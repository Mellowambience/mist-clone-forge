#!/usr/bin/env python3
"""MIST Auto-Router — specialists are chosen by the hive, not by hand.

Priority: urban nonprofit hospital sectors first (EHR, compliance, ED, …),
then general mesh (tinker, scavenger, …).

Usage:
  python auto_router.py "Epic downtime procedure for ED boarding"
  python auto_router.py --dispatch "HIPAA BAA for new analytics vendor"
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

SCRIPTS = Path(__file__).resolve().parent
HOME = Path.home() / ".grok" / "mist-clones"
CLONES = HOME / "clones"
ROSTER_DIR = HOME / "roster"
# package/repo roster (scripts/../roster)
PACK_ROSTER = SCRIPTS.parent / "roster"

sys.path.insert(0, str(SCRIPTS))
import hive  # noqa: E402

# Fallback keyword map if roster files missing (hospital-first order)
FALLBACK: list[dict[str, Any]] = [
    {
        "id": "mist-ehr",
        "priority": 1,
        "keywords": ["ehr", "emr", "epic", "cerner", "fhir", "hl7", "cpoe", "mar", "chart"],
    },
    {
        "id": "mist-hipaa",
        "priority": 1,
        "keywords": ["hipaa", "phi", "baa", "breach", "privacy", "ocr"],
    },
    {
        "id": "mist-ed",
        "priority": 1,
        "keywords": ["emergency", "ed", "er", "boarding", "triage", "diversion"],
    },
    {
        "id": "mist-scavenger",
        "priority": 9,
        "keywords": ["verify", "truth", "hallucination", "check"],
    },
    {
        "id": "mist-tinker",
        "priority": 9,
        "keywords": ["broken", "fix", "bug", "error", "fail"],
    },
]


def _load_route_table() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    candidates_dirs = [
        ROSTER_DIR,
        PACK_ROSTER,
        SCRIPTS.parent / "roster",
    ]
    for base in candidates_dirs:
        if not base.is_dir():
            continue
        for name in ("hospital_wave.json", "wave2.json", "emulator_wave.json"):
            p = base / name
            if not p.is_file():
                continue
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                for item in data:
                    rows.append(
                        {
                            "id": item["id"],
                            "priority": int(item.get("priority", 5)),
                            "keywords": [k.lower() for k in item.get("keywords", [])],
                            "domain": item.get("domain", ""),
                            "intent": item.get("intent", ""),
                        }
                    )
            except Exception:
                pass
    # disk manifests (general clones) — lower priority
    if CLONES.is_dir():
        for d in CLONES.iterdir():
            man = d / "manifest.json"
            if not man.is_file():
                continue
            try:
                m = json.loads(man.read_text(encoding="utf-8"))
            except Exception:
                continue
            cid = m.get("id", d.name)
            if any(r["id"] == cid for r in rows):
                continue
            intent = (m.get("intent") or "").lower()
            domain = (m.get("domain") or "").lower()
            # extract keyword-ish tokens from intent
            tokens = re.findall(r"[a-z]{4,}", intent + " " + domain)
            rows.append(
                {
                    "id": cid,
                    "priority": 8 if not domain.startswith("hospital") else 2,
                    "keywords": list(set(tokens))[:40],
                    "domain": domain,
                    "intent": m.get("intent", ""),
                }
            )
    if not rows:
        rows = FALLBACK
    # de-dupe by id keeping lowest priority number
    best: dict[str, dict] = {}
    for r in rows:
        prev = best.get(r["id"])
        if prev is None or r["priority"] < prev["priority"]:
            best[r["id"]] = r
    return list(best.values())


def score(text: str, row: dict[str, Any]) -> float:
    t = text.lower()
    score = 0.0
    for kw in row.get("keywords") or []:
        if kw in t:
            # longer keywords weigh more
            score += 1.0 + min(len(kw), 24) / 24.0
    # hard compliance spikes
    rid = row.get("id", "")
    if rid == "mist-hipaa" and any(k in t for k in ("hipaa", "baa", "phi", "breach", "ocr")):
        score += 3.0
    if rid == "mist-ehr" and any(k in t for k in ("epic", "cerner", "ehr", "emr", "fhir", "downtime")):
        score += 1.5
    # priority: hospital first (lower number = more important boost)
    pri = int(row.get("priority", 5))
    score += max(0, 6 - pri) * 0.15
    # hospital domain always outranks game/video fluff for mixed text
    if str(row.get("domain", "")).startswith("hospital"):
        score += 0.5
    # exist on disk bonus
    if (CLONES / row["id"]).is_dir():
        score += 0.25
    return score


def route(task: str, *, top_k: int = 3) -> list[dict[str, Any]]:
    table = _load_route_table()
    ranked = []
    for row in table:
        s = score(task, row)
        if s > 0:
            ranked.append({**row, "score": round(s, 3)})
    ranked.sort(key=lambda x: (-x["score"], x["priority"], x["id"]))
    if not ranked:
        # default hospital-safe fallbacks
        for fid in ("mist-ehr", "mist-scavenger", "mist-tinker", "mist-prime"):
            if (CLONES / fid).is_dir() or fid == "mist-prime":
                ranked.append(
                    {
                        "id": fid,
                        "score": 0.1,
                        "priority": 9,
                        "keywords": [],
                        "domain": "fallback",
                        "intent": "fallback router",
                    }
                )
                break
    return ranked[:top_k]


def dispatch(
    task: str,
    *,
    from_id: str = "mist-prime",
    auto_create_hint: bool = False,
) -> dict[str, Any]:
    """Pick best specialist and delegate via hive — no manual selection."""
    hive.init_db()
    ranked = route(task, top_k=5)
    if not ranked:
        return {"ok": False, "error": "no route"}

    chosen = ranked[0]
    # if specialist not on disk, try ehr/hospital still message hive
    to_id = chosen["id"]
    if not (CLONES / to_id).is_dir():
        # fall through ranked until one exists
        for r in ranked:
            if (CLONES / r["id"]).is_dir():
                chosen = r
                to_id = r["id"]
                break
        else:
            to_id = "mist-prime"
            chosen = {"id": to_id, "score": 0, "domain": "identity", "intent": "prime"}

    # ensure presence
    try:
        hive.join(to_id, note="auto-route target")
        hive.heartbeat(from_id, "routing", task[:80])
    except Exception:
        pass

    task_rec = hive.delegate(from_id, to_id, task, meta={"auto": True, "scores": ranked[:5]})
    hive.post(
        "hive",
        f"AUTO-ROUTE → {to_id} ({chosen.get('domain','')}) score={chosen.get('score')} · {task[:120]}",
        kind="harmony",
        meta={"to": to_id, "task_id": task_rec["id"], "auto": True},
    )
    # secondary watchers (hospital harmony): always notify hipaa if phi-ish
    watchers = []
    low = task.lower()
    if any(k in low for k in ("phi", "patient", "hipaa", "chart", "ehr", "mrn")):
        if to_id != "mist-hipaa" and (CLONES / "mist-hipaa").is_dir():
            watchers.append("mist-hipaa")
            hive.post(
                "mist-hipaa",
                f"Watching auto-route for PHI risk: {task[:160]}",
                to_id=to_id,
                kind="watch",
                meta={"task_id": task_rec["id"]},
            )
    if any(k in low for k in ("ed", "emergency", "boarding")) and to_id != "mist-ed":
        if (CLONES / "mist-ed").is_dir():
            watchers.append("mist-ed")

    return {
        "ok": True,
        "auto": True,
        "task": task_rec,
        "chosen": {
            "id": to_id,
            "domain": chosen.get("domain"),
            "score": chosen.get("score"),
            "intent": chosen.get("intent"),
        },
        "alternatives": ranked[1:4],
        "watchers": watchers,
        "principle": "Hospital sectors first · MIST chooses · humans override only when needed",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="MIST auto-router (hospital-first)")
    ap.add_argument("task", nargs="?", help="Task text to route")
    ap.add_argument("--dispatch", action="store_true", help="Delegate via hive")
    ap.add_argument("--from", dest="from_id", default="mist-prime")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if not args.task:
        ap.error("task text required")
    if args.dispatch:
        result = dispatch(args.task, from_id=args.from_id)
    else:
        result = {"ok": True, "routes": route(args.task), "auto": False}
    if args.json or args.dispatch:
        print(json.dumps(result, indent=2))
    else:
        for i, r in enumerate(result.get("routes") or [], 1):
            print(f"{i}. {r['id']:22} score={r['score']:<6} pri={r['priority']}  {r.get('domain','')}")


if __name__ == "__main__":
    main()
