#!/usr/bin/env python3
"""Conversation curator — turn chat context into selectable user options.

MIST ranks hospital sectors first, then mesh tools, then actions.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent
HOME = Path.home() / ".grok" / "mist-clones"
CURATE_DIR = HOME / "curation"
sys.path.insert(0, str(SCRIPTS))

import auto_router  # noqa: E402
import hive  # noqa: E402

# Action templates the user can pick (filled by conversation match)
ACTION_CATALOG: list[dict[str, Any]] = [
    {
        "id": "act-auto",
        "label": "Auto-route this need (MIST chooses specialist)",
        "kind": "action",
        "command": "auto",
        "keywords": ["auto", "route", "dispatch", "choose", "decide", "stuck", "help", "need"],
        "priority": 1,
    },
    {
        "id": "act-board",
        "label": "Open Swarm Ops board (live hive)",
        "kind": "action",
        "command": "board",
        "keywords": ["board", "view", "realtime", "dashboard", "watch", "ui", "servicenow"],
        "priority": 2,
    },
    {
        "id": "act-hive-feed",
        "label": "Show hive mind feed",
        "kind": "action",
        "command": "hive-feed",
        "keywords": ["hive", "harmony", "feed", "message", "connected"],
        "priority": 2,
    },
    {
        "id": "act-hospital-seed",
        "label": "Ensure hospital specialists are seeded",
        "kind": "action",
        "command": "seed-hospital",
        "keywords": ["hospital", "ehr", "seed", "nonprofit", "urban", "sector"],
        "priority": 1,
    },
    {
        "id": "act-delegate",
        "label": "Delegate a concrete task across the hive",
        "kind": "action",
        "command": "delegate",
        "keywords": ["delegate", "assign", "task", "handoff"],
        "priority": 3,
    },
    {
        "id": "act-absorb",
        "label": "Absorb ephemeral specialist (keep lessons, archive husk)",
        "kind": "action",
        "command": "absorb",
        "keywords": ["absorb", "recycle", "memory", "lesson", "done"],
        "priority": 3,
    },
    {
        "id": "act-create",
        "label": "Create a new specialist for a gap",
        "kind": "action",
        "command": "create",
        "keywords": ["create", "new", "specialist", "clone", "forge", "agent"],
        "priority": 3,
    },
    {
        "id": "act-curate-save",
        "label": "Save this curation as session options",
        "kind": "action",
        "command": "save",
        "keywords": ["curate", "options", "menu", "save", "session"],
        "priority": 4,
    },
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]{3,}", text.lower()))


def curate(conversation: str, *, limit: int = 12) -> dict[str, Any]:
    """Build ranked user options from free-text conversation."""
    text = (conversation or "").strip()
    if not text:
        return {
            "ok": False,
            "error": "empty conversation",
            "options": [],
            "ts": now(),
        }

    toks = _tokens(text)
    options: list[dict[str, Any]] = []

    # 1) Auto-route specialists (hospital-first)
    routes = auto_router.route(text, top_k=6)
    for i, r in enumerate(routes):
        options.append(
            {
                "id": f"spec-{r['id']}",
                "label": f"Work with {r['id']}",
                "subtitle": r.get("intent") or r.get("domain") or "",
                "kind": "specialist",
                "specialist": r["id"],
                "domain": r.get("domain"),
                "score": r.get("score", 0) + (6 - i) * 0.1,
                "why": f"Matched hospital/mesh routing (score {r.get('score')})",
                "action": {
                    "type": "auto_dispatch",
                    "task": text[:500],
                    "prefer": r["id"],
                },
            }
        )

    # 2) Action catalog
    for act in ACTION_CATALOG:
        hit = sum(1 for k in act["keywords"] if k in text.lower() or k in toks)
        if hit == 0 and act["id"] not in ("act-auto", "act-board"):
            # still offer auto + board lightly if hospital talk
            continue
        if hit == 0 and not any(
            h in text.lower()
            for h in ("hospital", "ehr", "hive", "agent", "mist", "board")
        ):
            continue
        score = hit * 1.5 + max(0, 5 - act["priority"]) * 0.3
        if act["id"] == "act-auto":
            score += 2.0  # always surface auto when curating
        if act["id"] == "act-hospital-seed" and any(
            k in text.lower() for k in ("hospital", "ehr", "nonprofit", "hipaa", "ed ")
        ):
            score += 2.5
        options.append(
            {
                "id": act["id"],
                "label": act["label"],
                "subtitle": f"Action · {act['command']}",
                "kind": "action",
                "command": act["command"],
                "score": score,
                "why": f"Conversation cues: {', '.join(act['keywords'][:4])}…",
                "action": {"type": act["command"], "context": text[:500]},
            }
        )

    # 3) Theme chips (for UI filters)
    themes = []
    theme_map = [
        ("hospital", ["hospital", "nonprofit", "urban", "clinical", "patient"]),
        ("ehr", ["ehr", "epic", "cerner", "fhir", "chart", "downtime"]),
        ("privacy", ["hipaa", "phi", "baa", "privacy", "breach"]),
        ("ed", ["ed", "emergency", "boarding", "triage"]),
        ("hive", ["hive", "mesh", "delegate", "harmony", "swarm"]),
        ("memory", ["absorb", "memory", "delete", "repo", "curate"]),
    ]
    low = text.lower()
    for name, kws in theme_map:
        if any(k in low for k in kws):
            themes.append(name)

    # de-dupe by id, sort
    best: dict[str, dict] = {}
    for o in options:
        prev = best.get(o["id"])
        if prev is None or o["score"] > prev["score"]:
            best[o["id"]] = o
    ranked = sorted(best.values(), key=lambda x: -x["score"])[:limit]

    # ensure auto is always option #1 when we have text
    auto_opt = next((o for o in ranked if o["id"] == "act-auto"), None)
    if auto_opt:
        ranked = [auto_opt] + [o for o in ranked if o["id"] != "act-auto"]

    result = {
        "ok": True,
        "ts": now(),
        "themes": themes,
        "summary": _summary(themes, ranked),
        "options": ranked,
        "hospital_first": True,
        "principle": "Curate from conversation · hospital sectors first · MIST can auto-dispatch",
    }
    return result


def _summary(themes: list[str], options: list[dict]) -> str:
    if not options:
        return "No strong matches — describe a hospital or mesh need."
    top = options[0]
    th = ", ".join(themes) if themes else "general"
    return f"Themes: {th}. Top option: {top['label']}."


def save_session(conversation: str, result: dict, label: str = "") -> Path:
    CURATE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    path = CURATE_DIR / f"session-{stamp}.json"
    payload = {
        "label": label or "conversation",
        "conversation": conversation[:8000],
        "result": result,
        "saved_at": now(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    # also latest pointer
    (CURATE_DIR / "latest.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    try:
        hive.post(
            "mist-prime",
            f"Curated {len(result.get('options', []))} options · themes={result.get('themes')}",
            kind="curation",
            meta={"path": str(path)},
        )
    except Exception:
        pass
    return path


def latest() -> dict[str, Any] | None:
    p = CURATE_DIR / "latest.json"
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Curate user options from conversation")
    ap.add_argument("text", nargs="?", help="Conversation / context text")
    ap.add_argument("--file", help="Read context from file")
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--latest", action="store_true")
    args = ap.parse_args()
    if args.latest:
        print(json.dumps(latest() or {"ok": False}, indent=2))
        return
    text = args.text or ""
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    if not text:
        ap.error("text or --file required")
    result = curate(text)
    if args.save:
        path = save_session(text, result)
        result["saved"] = str(path)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
