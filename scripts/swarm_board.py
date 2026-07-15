#!/usr/bin/env python3
"""MIST Swarm Ops — management, hive mind, delegation, live mesh.

  python swarm_board.py --port 8766
  http://127.0.0.1:8766/
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HOME = Path.home() / ".grok" / "mist-clones"
CLONES = HOME / "clones"
FORGE = HOME / "scripts" / "forge.py"
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import carrier  # noqa: E402
import hive  # noqa: E402

_events: list[dict] = []
_lock = threading.Lock()
_snapshots: dict[str, float] = {}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def push_event(ev: dict) -> None:
    with _lock:
        _events.append(ev)
        if len(_events) > 400:
            del _events[:-400]


def _clone_from_path(p: Path) -> str:
    try:
        parts = p.relative_to(HOME).parts
        if len(parts) >= 2 and parts[0] == "clones":
            return parts[1]
    except Exception:
        pass
    return "?"


def _tail_md(path: Path, n: int = 6) -> list[str]:
    if not path.is_file():
        return []
    lines = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("|") and "---" not in line and "Date" not in line:
            lines.append(line.strip())
    return lines[-n:]


def run_forge(*args: str) -> dict:
    r = subprocess.run(
        [sys.executable, str(FORGE), *args],
        capture_output=True,
        text=True,
        timeout=90,
    )
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    push_event(
        {
            "ts": now(),
            "kind": "forge",
            "clone": args[1] if len(args) > 1 else "forge",
            "path": " ".join(args)[:140],
            "ok": r.returncode == 0,
        }
    )
    return {"ok": r.returncode == 0, "code": r.returncode, "output": out}


def snapshot_agents() -> list[dict]:
    agents = []
    if not CLONES.is_dir():
        return agents
    presence = {p["clone_id"]: p for p in hive.presence_list()}
    for d in sorted(CLONES.iterdir()):
        if not d.is_dir() or not (d / "manifest.json").is_file():
            continue
        try:
            man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        except Exception:
            man = {"id": d.name, "status": "corrupt"}
        times = []
        for name in ("manifest.json", "journal.md", "handoff.md", "lessons.md"):
            p = d / name
            if p.is_file():
                times.append((p.stat().st_mtime, name))
        times.sort(reverse=True)
        last_mtime, last_file = times[0] if times else (0.0, "")
        age = time.time() - last_mtime if last_mtime else None
        pulse = (
            "hot"
            if age is not None and age < 120
            else "warm"
            if age is not None and age < 3600
            else "idle"
        )
        pr = presence.get(man.get("id", d.name), {})
        agents.append(
            {
                "id": man.get("id", d.name),
                "name": man.get("name", d.name),
                "domain": man.get("domain", "general"),
                "intent": man.get("intent", ""),
                "status": man.get("status", "?"),
                "generation": man.get("generation", 1),
                "parent": man.get("parent"),
                "skills": man.get("skills") or [],
                "voice": man.get("voice", ""),
                "ephemeral": bool(man.get("ephemeral")),
                "last_file": last_file,
                "age_sec": round(age, 1) if age is not None else None,
                "pulse": pulse,
                "hive_status": pr.get("status", "offline"),
                "hive_task": pr.get("current_task"),
                "hive_seen": pr.get("last_seen"),
                "absorbed_count": len(man.get("absorbed_clones") or []),
                "lesson_count": len(man.get("lessons") or []),
                "journal_tail": _tail_md(d / "journal.md"),
                "lessons_tail": _tail_md(d / "lessons.md"),
            }
        )
    return agents


def snapshot_board() -> dict:
    agents = snapshot_agents()
    domains: dict[str, int] = {}
    for a in agents:
        domains[a["domain"]] = domains.get(a["domain"], 0) + 1
    with _lock:
        events = list(_events[-100:])
    hs = hive.snapshot()
    car = carrier.status(hs, agent_count=len(agents))
    return {
        "ts": now(),
        "agent_count": len(agents),
        "hot": sum(1 for a in agents if a["pulse"] == "hot"),
        "warm": sum(1 for a in agents if a["pulse"] == "warm"),
        "idle": sum(1 for a in agents if a["pulse"] == "idle"),
        "domains": domains,
        "agents": agents,
        "events": events,
        "hive": hs,
        "carrier": car,
        "tagline": "One genome · many specialists · hive mind · harmony",
        "loop": "stuck → forge → delegate → help → absorb",
    }


def _ambient_thoughts(agent_id: str, intent: str, domain: str) -> list[str]:
    """Simulated inner monologue grounded in specialist role (not clinical advice)."""
    templates = [
        f"// {agent_id} · scanning hive bus…",
        f"intent locked: {intent[:90]}…" if intent else f"// {agent_id} idle hum",
        f"domain={domain} · hospital-first doctrine active"
        if str(domain).startswith("hospital")
        else f"domain={domain} · standing by for auto-route",
        "cross-checking provenance · no invented facts",
        "harmony link: mist-prime ↔ mesh · OK",
    ]
    if "ehr" in agent_id or "ehr" in domain:
        templates += [
            "EHR path: downtime runbook · identity match · never fabricate chart data",
            "listening for ADT / order / note friction…",
        ]
    if "hipaa" in agent_id:
        templates += [
            "PHI guard: minimum necessary · BAA surface · no casual export",
        ]
    if "ed" in agent_id:
        templates += ["ED flow vectors: boarding · diversion · surge…"]
    return templates


def tv_snapshot(channel: str | None = None) -> dict:
    """Compose CRT channel feed from hive + agent presence + ambient think."""
    agents = snapshot_agents()
    # hospital channels first for channel guide
    agents_sorted = sorted(
        agents,
        key=lambda a: (
            0 if str(a.get("domain", "")).startswith("hospital") else 1,
            a.get("id", ""),
        ),
    )
    hs = hive.snapshot()
    thoughts: list[dict] = []

    # Real hive messages → "thinking out loud"
    for m in (hs.get("messages") or [])[:40]:
        fr = m.get("from_id") or "?"
        if channel and channel not in ("ALL", "all", "") and fr not in (
            channel,
            "hive",
            "mist-prime",
        ):
            # still show if directed to channel
            if m.get("to_id") != channel:
                continue
        kind = m.get("kind") or "thought"
        body = m.get("body") or ""
        thoughts.append(
            {
                "id": m.get("id"),
                "ts": m.get("ts"),
                "channel": fr,
                "kind": kind,
                "text": f"«{kind}» {body}",
            }
        )

    # Open tasks as active thinking
    for t in (hs.get("open_tasks") or hs.get("tasks") or [])[:15]:
        if t.get("status") not in (None, "open", "accepted", "assigned"):
            if t.get("status") not in ("open", "accepted"):
                continue
        to_id = t.get("to_id")
        if channel and channel not in ("ALL", "all", "") and to_id != channel:
            continue
        thoughts.append(
            {
                "id": t.get("id"),
                "ts": t.get("ts"),
                "channel": to_id,
                "kind": "think",
                "text": f"TASK[{t.get('status')}]: {t.get('title', '')[:140]}",
            }
        )

    # Ambient role thoughts for selected channel
    if channel and channel not in ("ALL", "all", ""):
        ag = next((a for a in agents if a["id"] == channel), None)
        if ag:
            for line in _ambient_thoughts(
                ag["id"], ag.get("intent", ""), ag.get("domain", "")
            )[:3]:
                thoughts.append(
                    {
                        "id": f"amb-{channel}-{hash(line) % 99999}",
                        "ts": now(),
                        "channel": channel,
                        "kind": "think",
                        "text": line,
                    }
                )
            for j in (ag.get("journal_tail") or [])[-2:]:
                thoughts.append(
                    {
                        "id": f"j-{hash(j) % 99999}",
                        "ts": now(),
                        "channel": channel,
                        "kind": "dim",
                        "text": f"journal⟩ {j[:120]}",
                    }
                )

    with _lock:
        for e in list(_events)[-20:]:
            thoughts.append(
                {
                    "id": f"ev-{e.get('ts')}-{e.get('path')}",
                    "ts": e.get("ts"),
                    "channel": e.get("clone") or "?",
                    "kind": e.get("kind") or "write",
                    "text": f"pulse/{e.get('kind')}: {e.get('path', '')[:100]}",
                }
            )

    car = carrier.status(hs, agent_count=len(agents))
    return {
        "ts": now(),
        "live": True,
        "signal": "AGENTIC-VISION",
        "carrier": car,
        "member_count": hs.get("member_count") or len(agents),
        "channel": channel or "ALL",
        "agents": [{"id": a["id"], "domain": a.get("domain"), "pulse": a.get("pulse")} for a in agents_sorted],
        "thoughts": thoughts[-50:],
        "note": "Thoughts = hive messages + tasks + role ambient monologue (not private model weights).",
    }


def watch_loop(interval: float = 0.5) -> None:
    global _snapshots
    while True:
        try:
            current: dict[str, float] = {}
            if CLONES.is_dir():
                for p in CLONES.rglob("*"):
                    if not p.is_file() or p.suffix not in {".json", ".md"}:
                        continue
                    key = str(p.relative_to(HOME)).replace("\\", "/")
                    mt = p.stat().st_mtime
                    current[key] = mt
                    prev = _snapshots.get(key)
                    if prev is not None and mt > prev:
                        push_event(
                            {
                                "ts": now(),
                                "kind": "write",
                                "path": key,
                                "clone": _clone_from_path(p),
                            }
                        )
            _snapshots = current
        except Exception as e:
            push_event({"ts": now(), "kind": "watch_error", "path": str(e), "clone": "—"})
        time.sleep(interval)


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>MIST Swarm Ops — Hive</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet"/>
<style>
:root{--bg:#060b14;--card:rgba(12,22,38,.72);--ink:#e8f2ff;--mute:#8ba3c4;--cyan:#7dd3fc;--violet:#c4b5fd;--pink:#f0abfc;--amber:#fde68a;--green:#a5f3fc;--line:rgba(148,180,220,.16);--hot:#f0abfc;--warm:#7dd3fc;--fog:rgba(186,230,253,.08)}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"IBM Plex Mono",monospace;background:radial-gradient(1000px 600px at 15% -5%,rgba(125,211,252,.14),transparent 50%),radial-gradient(900px 500px at 90% 10%,rgba(196,181,253,.12),transparent 48%),radial-gradient(700px 400px at 50% 100%,rgba(240,171,252,.06),transparent 42%),var(--bg);color:var(--ink);min-height:100vh}
body::before{content:"";pointer-events:none;position:fixed;inset:0;background:radial-gradient(ellipse 50% 40% at 30% 40%,rgba(186,230,253,.05),transparent),radial-gradient(ellipse 40% 35% at 75% 55%,rgba(196,181,253,.04),transparent);z-index:0;animation:fog 20s ease-in-out infinite alternate}
@keyframes fog{from{opacity:.6;transform:translate(0,0)}to{opacity:1;transform:translate(1.5%,-1%)}}
.top,.tabs,.panel{position:relative;z-index:1}
.top{position:sticky;top:0;z-index:30;backdrop-filter:blur(16px);background:rgba(6,11,20,.78);border-bottom:1px solid var(--line);padding:.75rem 1.1rem;display:flex;flex-wrap:wrap;gap:.7rem;align-items:center;justify-content:space-between}
.brand h1{font-family:"Cormorant Garamond",serif;font-size:1.4rem;letter-spacing:.04em;text-shadow:0 0 24px rgba(125,211,252,.25)}
.brand .sub{font-size:.65rem;color:var(--mute)}
.dot{width:10px;height:10px;border-radius:50%;background:var(--cyan);box-shadow:0 0 16px rgba(125,211,252,.7);display:inline-block;margin-right:8px;animation:p 1.8s infinite}
@keyframes p{50%{opacity:.35}}
.kpis{display:flex;gap:.4rem;flex-wrap:wrap}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:999px;padding:.3rem .7rem;font-size:.68rem;color:var(--mute);backdrop-filter:blur(8px)}
.kpi b{color:var(--ink)}
.kpi.hot b{color:var(--hot)}.kpi.hive b{color:var(--green)}
.tabs{display:flex;gap:.35rem;padding:.7rem 1.1rem 0;flex-wrap:wrap}
.tab{background:rgba(12,22,38,.4);border:1px solid var(--line);color:var(--mute);font:inherit;font-size:.72rem;padding:.4rem .8rem;border-radius:999px;cursor:pointer}
.tab.active{border-color:rgba(125,211,252,.5);color:var(--cyan);background:rgba(125,211,252,.12);box-shadow:0 0 20px rgba(56,189,248,.1)}
.panel{display:none;padding:1rem 1.1rem 2rem}
.panel.active{display:block}
.hero{display:flex;flex-wrap:wrap;justify-content:space-between;gap:1rem;padding:1rem;border:1px solid var(--line);border-radius:16px;margin-bottom:1rem;background:linear-gradient(135deg,rgba(125,211,252,.1),rgba(196,181,253,.1) 50%,rgba(240,171,252,.05));backdrop-filter:blur(10px);box-shadow:0 8px 40px rgba(0,0,0,.2)}
.hero h2{font-family:"Cormorant Garamond",serif;font-size:1.45rem;font-weight:600}
.hero p{color:var(--mute);font-size:.72rem;margin-top:.3rem;max-width:50ch}
.actions{display:flex;flex-wrap:wrap;gap:.4rem}
.btn{border:1px solid rgba(125,211,252,.4);background:rgba(12,22,38,.5);color:var(--cyan);font:inherit;font-size:.7rem;padding:.45rem .8rem;border-radius:999px;cursor:pointer}
.btn:hover{background:rgba(125,211,252,.12);box-shadow:0 0 16px rgba(56,189,248,.15)}
.btn.solid{background:linear-gradient(135deg,#0e7490,#5b21b6 60%,#7c3aed);border:0;color:#fff;box-shadow:0 4px 24px rgba(91,33,182,.3)}
.btn.danger{border-color:rgba(240,171,252,.45);color:var(--pink)}
.btn.ghost{border-color:var(--line);color:var(--mute)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:.65rem}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:.85rem;cursor:pointer;position:relative;overflow:hidden;backdrop-filter:blur(8px)}
.card::before{content:"";position:absolute;left:0;right:0;top:0;height:2px;background:var(--mute);opacity:.4}
.card.hot::before{background:linear-gradient(90deg,var(--pink),var(--violet),var(--cyan));opacity:1}
.card.warm::before{background:linear-gradient(90deg,var(--cyan),var(--violet));opacity:1}
.card:hover{border-color:rgba(125,211,252,.4);transform:translateY(-2px);box-shadow:0 12px 40px rgba(14,30,50,.45)}
.card.selected{border-color:var(--cyan);box-shadow:0 0 0 1px rgba(125,211,252,.25),0 0 28px rgba(56,189,248,.12)}
.badge{font-size:.58rem;text-transform:uppercase;letter-spacing:.06em;padding:2px 6px;border-radius:999px}
.badge.hot{background:rgba(240,171,252,.18);color:var(--hot)}
.badge.warm{background:rgba(125,211,252,.14);color:var(--warm)}
.badge.idle{background:rgba(100,116,139,.25);color:var(--mute)}
.badge.hive{background:rgba(165,243,252,.12);color:var(--green)}
.id{color:var(--cyan);font-size:.85rem;margin:.35rem 0 .2rem;text-shadow:0 0 12px rgba(125,211,252,.25)}
.intent{font-size:.66rem;color:var(--mute);line-height:1.4;min-height:2.6em;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.meta{display:flex;justify-content:space-between;font-size:.6rem;color:var(--mute);margin-top:.45rem}
.skill{font-size:.55rem;color:var(--violet);background:rgba(196,181,253,.12);padding:1px 5px;border-radius:4px;margin:2px 2px 0 0;display:inline-block}
.layout{display:grid;grid-template-columns:1fr 320px;gap:1rem}
@media(max-width:960px){.layout{grid-template-columns:1fr}}
.rail{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:.85rem;max-height:75vh;overflow:auto;backdrop-filter:blur(8px)}
.rail h3{font-size:.62rem;text-transform:uppercase;letter-spacing:.1em;color:var(--mute);margin:.6rem 0 .4rem}
.ev{font-size:.65rem;color:var(--mute);padding:.35rem 0;border-bottom:1px solid var(--line);line-height:1.35}
.ev b{color:var(--ink)}.ev .k{color:var(--cyan)}
.form{display:grid;gap:.55rem;max-width:520px}
label{font-size:.65rem;color:var(--mute)}
input,select,textarea{width:100%;background:rgba(6,12,22,.55);border:1px solid var(--line);border-radius:10px;color:var(--ink);font:inherit;font-size:.75rem;padding:.5rem .6rem}
textarea{min-height:72px;resize:vertical}
.table{width:100%;border-collapse:collapse;font-size:.68rem}
.table th,.table td{text-align:left;padding:.4rem .35rem;border-bottom:1px solid var(--line);color:var(--mute)}
.table th{color:var(--ink);font-weight:500}
.table tr:hover td{color:var(--ink)}
.toast{position:fixed;bottom:1rem;right:1rem;background:rgba(12,22,38,.95);border:1px solid rgba(125,211,252,.4);padding:.65rem .9rem;border-radius:12px;font-size:.72rem;opacity:0;transition:opacity .2s;max-width:360px;z-index:50;box-shadow:0 8px 32px rgba(0,0,0,.4)}
.toast.show{opacity:1}
.search{width:100%;max-width:280px;margin-bottom:.7rem}
.split{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
@media(max-width:800px){.split{grid-template-columns:1fr}}
.tail{font-size:.6rem;color:var(--mute);background:rgba(6,12,22,.45);border-radius:10px;padding:.45rem;white-space:pre-wrap;max-height:100px;overflow:auto}
.harmony{font-family:"Cormorant Garamond",serif;font-size:1.05rem;color:var(--cyan);text-shadow:0 0 20px rgba(125,211,252,.3)}
</style>
</head>
<body>
<header class="top">
  <div class="brand">
    <div><span class="dot"></span><h1 style="display:inline">MIST Swarm Ops</h1>
    <div class="sub" id="tagline">Hive mind · management · harmony</div></div>
  </div>
  <div class="kpis">
    <div class="kpi hive"><b id="k-hive">○</b> hive</div>
    <div class="kpi" id="kpi-carrier" style="border-color:rgba(52,211,153,.45)"><b id="k-carrier">MESH</b> <span id="k-bars"></span></div>
    <div class="kpi" id="kpi-phone" style="border-color:rgba(244,114,182,.4)"><b id="k-phone">PHONE</b> <span id="k-phone-bars"></span></div>
    <div class="kpi"><b id="k-up">—</b> up</div>
    <div class="kpi" id="kpi-phone-url" style="max-width:280px;overflow:hidden;text-overflow:ellipsis" title="Open on phone"><b id="k-phone-url">—</b></div>
    <div class="kpi"><b id="k-n">0</b> agents</div>
    <div class="kpi hot"><b id="k-hot">0</b> hot</div>
    <div class="kpi"><b id="k-tasks">0</b> open tasks</div>
    <div class="kpi"><b id="k-msg">0</b> hive msgs</div>
    <div class="kpi"><b id="k-lat">—</b> ms</div>
  </div>
</header>
<nav class="tabs">
  <button class="tab active" data-tab="options">Your options</button>
  <button class="tab" data-tab="auto">Auto (MIST)</button>
  <button class="tab" data-tab="mesh">Mesh</button>
  <button class="tab" data-tab="hive">Hive Mind</button>
  <button class="tab" data-tab="tasks">Tasks</button>
  <button class="tab" data-tab="manage">Manage</button>
  <a class="tab" href="/tv" style="text-decoration:none;display:inline-block">Agentic Vision</a>
  <button class="tab" data-tab="gc">GameCube</button>
</nav>

<section class="panel" id="tab-gc">
  <div class="hero">
    <div>
      <h2>GameCube · Dolphin</h2>
      <p>Agent play hub. Drop owned dumps in games folder — no piracy. mist-gamecube launches + presses buttons.</p>
      <div class="harmony">legal dumps only · hive play log · misty CRT narrates</div>
    </div>
    <div class="actions">
      <button class="btn solid" onclick="gcList()">Refresh library</button>
      <button class="btn" onclick="gcStatus()">Status</button>
    </div>
  </div>
  <pre class="tail" id="gc-out" style="max-height:320px;font-size:.7rem">Loading…</pre>
  <div class="form" style="max-width:520px;margin-top:1rem">
    <label>Launch game (name contains…)</label>
    <input id="gc-game" placeholder="e.g. melee or full path"/>
    <div class="actions">
      <button class="btn solid" onclick="gcLaunch()">Launch in Dolphin</button>
      <button class="btn" onclick="gcPress('A')">Press A</button>
      <button class="btn" onclick="gcPress('START')">Start</button>
      <button class="btn" onclick="gcPress('LEFT')">←</button>
      <button class="btn" onclick="gcPress('RIGHT')">→</button>
    </div>
  </div>
  <p style="font-size:.68rem;color:var(--mute);margin-top:1rem">Folder: <code>~/.grok/mist-clones/gamecube/games/</code></p>
</section>

<section class="panel active" id="tab-options">
  <div class="hero">
    <div>
      <h2>Curated for you</h2>
      <p>Options from this conversation — hospital-first. Click one; MIST can dispatch without manual ticket picking.</p>
      <div class="harmony" id="cur-summary">Paste or refresh conversation context below.</div>
    </div>
    <div class="actions">
      <button class="btn solid" onclick="curateNow()">Curate from text</button>
      <button class="btn" onclick="loadLatestCurate()">Load latest</button>
    </div>
  </div>
  <form class="form" style="max-width:720px" onsubmit="return curateNow(event)">
    <label>Conversation / context (what you've been working on)</label>
    <textarea id="cur-text" rows="5" placeholder="Paste chat themes or describe what you care about right now…"></textarea>
    <div class="actions">
      <button class="btn solid" type="submit">Update my options</button>
    </div>
  </form>
  <div id="cur-themes" style="margin:.75rem 0;display:flex;flex-wrap:wrap;gap:.35rem"></div>
  <div class="grid" id="cur-options"></div>
</section>

<section class="panel" id="tab-auto">
  <div class="hero">
    <div>
      <h2>MIST decides</h2>
      <p>Urban nonprofit hospital sectors first (EHR, HIPAA, ED, care, community…). No manual ticket queue — describe the need; the hive routes.</p>
      <div class="harmony">hospital-first · auto-route · hive harmony</div>
    </div>
  </div>
  <form class="form" style="max-width:640px" onsubmit="return doAuto(event)">
    <label>What does the hospital / mission need?</label>
    <textarea id="auto-task" required placeholder="e.g. Epic downtime plan while ED is boarding behavioral health patients"></textarea>
    <div class="actions">
      <button class="btn solid" type="submit">Auto-route &amp; dispatch</button>
      <button class="btn" type="button" onclick="doAutoDry()">Preview only</button>
    </div>
  </form>
  <pre class="tail" id="auto-out" style="margin-top:1rem;max-height:240px;font-size:.68rem">Awaiting task…</pre>
</section>

<section class="panel" id="tab-mesh">
  <div class="hero">
    <div>
      <h2 id="hero-t">Mesh</h2>
      <p id="hero-s">Hospital specialists first in roster · hive status on each card</p>
      <div class="harmony" id="loop"></div>
    </div>
    <div class="actions">
      <button class="btn solid" onclick="openTab('auto')">Auto-route</button>
      <button class="btn" onclick="openTab('manage')">Manage</button>
      <button class="btn" onclick="joinAll()">Re-link hive</button>
      <button class="btn ghost" onclick="load()">Refresh</button>
    </div>
  </div>
  <input class="search" id="q" placeholder="Search  /" oninput="renderMesh()"/>
  <div class="layout">
    <div class="grid" id="grid"></div>
    <aside class="rail">
      <h3>Selected</h3>
      <div id="sel-empty" style="color:var(--mute);font-size:.72rem">Click a specialist</div>
      <div id="sel-body" style="display:none">
        <div class="id" id="s-id"></div>
        <div class="intent" id="s-intent" style="min-height:0"></div>
        <div class="meta" id="s-meta"></div>
        <div id="s-skills" style="margin:.4rem 0"></div>
        <h3>Journal</h3><div class="tail" id="s-j"></div>
        <h3>Lessons</h3><div class="tail" id="s-l"></div>
        <div class="actions" style="margin-top:.5rem">
          <button class="btn" onclick="doEvolve()">Evolve</button>
          <button class="btn" onclick="prefillDelegate()">Delegate from…</button>
          <button class="btn danger" onclick="doDelete()">Delete</button>
        </div>
      </div>
      <h3>File pulse</h3>
      <div id="file-feed"></div>
    </aside>
  </div>
</section>

<section class="panel" id="tab-hive">
  <div class="hero">
    <div>
      <h2>Hive Mind</h2>
      <p>Shared bus — every specialist hears harmony messages, presence, and handoffs.</p>
    </div>
    <div class="actions">
      <button class="btn solid" onclick="joinAll()">Join all to hive</button>
      <button class="btn" onclick="broadcastThought()">Broadcast</button>
    </div>
  </div>
  <div class="split">
    <div>
      <h3 style="font-size:.65rem;color:var(--mute);margin-bottom:.5rem">PRESENCE</h3>
      <table class="table" id="presence-table"><thead><tr><th>Agent</th><th>Status</th><th>Task</th><th>Seen</th></tr></thead><tbody></tbody></table>
    </div>
    <div>
      <h3 style="font-size:.65rem;color:var(--mute);margin-bottom:.5rem">HIVE FEED</h3>
      <div class="rail" id="hive-feed" style="max-height:55vh"></div>
      <div class="form" style="margin-top:.7rem">
        <label>Post to hive</label>
        <div style="display:flex;gap:.4rem">
          <select id="hive-from" style="flex:0 0 140px"></select>
          <input id="hive-body" placeholder="Thought for the mesh…" style="flex:1"/>
          <button class="btn solid" onclick="hivePost()">Send</button>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="panel" id="tab-tasks">
  <div class="hero">
    <div>
      <h2>Delegation</h2>
      <p>Assign work across the hive. Assignee gets handoff + hive notify.</p>
    </div>
  </div>
  <div class="split">
    <form class="form" onsubmit="return doDelegate(event)">
      <label>From</label><select id="d-from" required></select>
      <label>To</label><select id="d-to" required></select>
      <label>Task</label><textarea id="d-task" required placeholder="What should they do?"></textarea>
      <div class="actions"><button class="btn solid" type="submit">Delegate</button></div>
    </form>
    <div>
      <h3 style="font-size:.65rem;color:var(--mute);margin-bottom:.5rem">OPEN TASKS</h3>
      <table class="table" id="task-table"><thead><tr><th>ID</th><th>From→To</th><th>Title</th><th></th></tr></thead><tbody></tbody></table>
    </div>
  </div>
</section>

<section class="panel" id="tab-manage">
  <div class="hero">
    <div>
      <h2>Create &amp; manage</h2>
      <p>Birth specialists into the hive. Delete retires (archives) them.</p>
    </div>
  </div>
  <div class="split">
    <form class="form" onsubmit="return doCreate(event)">
      <label>ID (mist-…)</label><input id="c-id" placeholder="mist-example" pattern="[a-z][a-z0-9-]{1,62}[a-z0-9]"/>
      <label>Intent (one sentence)</label><textarea id="c-intent" required placeholder="What is this specialist for?"></textarea>
      <label>Domain</label>
      <select id="c-domain">
        <option>general</option><option>game</option><option>data</option><option>ship</option>
        <option>writing</option><option>truth</option><option>fix</option><option>mesh</option>
        <option>identity</option><option>video</option><option>safety</option><option>meta</option>
      </select>
      <label>Parent</label><select id="c-parent"></select>
      <label>Skills (comma-separated)</label><input id="c-skills" value="scavenger-mode"/>
      <label><input type="checkbox" id="c-ephemeral"/> Ephemeral (absorb when done)</label>
      <div class="actions"><button class="btn solid" type="submit">Create &amp; join hive</button></div>
    </form>
    <div>
      <h3 style="font-size:.65rem;color:var(--mute);margin-bottom:.5rem">UNSTICK (quick forge)</h3>
      <form class="form" onsubmit="return doStuck(event)">
        <label>Blocker</label><textarea id="u-problem" required></textarea>
        <label>Parent host</label><select id="u-parent"></select>
        <label>Skills</label><input id="u-skills" value="scavenger-mode,check-work"/>
        <button class="btn solid" type="submit">Forge unstick specialist</button>
      </form>
      <h3 style="font-size:.65rem;color:var(--mute);margin:1rem 0 .5rem">DANGER ZONE</h3>
      <p style="font-size:.68rem;color:var(--mute);margin-bottom:.4rem">Select agent on Mesh tab, or type id:</p>
      <div class="actions">
        <input id="del-id" placeholder="mist-…" style="max-width:180px"/>
        <button class="btn danger" onclick="doDeleteInput()">Delete / archive</button>
      </div>
    </div>
  </div>
</section>

<div class="toast" id="toast"></div>
<script>
const S = { board:null, selected:null, tab:'options', curation:null };
const $ = id => document.getElementById(id);
function toast(m){const t=$('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),3200)}
function esc(s){return String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function age(sec){if(sec==null)return'—';if(sec<60)return Math.round(sec)+'s';if(sec<3600)return Math.round(sec/60)+'m';return Math.round(sec/3600)+'h'}

function openTab(name){
  S.tab=name;
  document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t.dataset.tab===name));
  document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('active',p.id==='tab-'+name));
}
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>openTab(t.dataset.tab));

async function api(path, opts){
  const r = await fetch(path, opts);
  const j = await r.json().catch(()=>({}));
  if(!r.ok && !j.ok) throw new Error(j.error||j.output||r.statusText);
  return j;
}

async function load(){
  const t0=performance.now();
  try{
    S.board = await api('/api/board?t='+Date.now());
    $('k-lat').textContent = Math.round(performance.now()-t0);
    $('k-live') && ($('k-live').textContent='●');
    render();
  }catch(e){
    toast('NO CARRIER: '+e.message+' — run start_carrier.bat');
    if($('k-hive')) $('k-hive').textContent='○';
    if($('k-live')) $('k-live').textContent='○';
    if($('k-carrier')) $('k-carrier').textContent='NO CARRIER';
    if($('k-bars')) $('k-bars').textContent='░░░░░';
    if($('k-up')) $('k-up').textContent='offline';
    const kc=$('kpi-carrier'); if(kc) kc.style.borderColor='rgba(244,114,182,.55)';
  }
}

function fillSelects(){
  const agents = (S.board&&S.board.agents)||[];
  ['d-from','d-to','c-parent','u-parent','hive-from'].forEach(id=>{
    const el=$(id); if(!el) return;
    const cur=el.value;
    el.innerHTML = agents.map(a=>`<option value="${esc(a.id)}">${esc(a.id)}</option>`).join('');
    if(cur) el.value=cur;
    if(id==='d-from'||id==='c-parent'||id==='hive-from') el.value = agents.find(a=>a.id==='mist-prime')? 'mist-prime' : (agents[0]&&agents[0].id);
    if(id==='d-to'||id==='u-parent') el.value = agents.find(a=>a.id==='mist-tinker')? 'mist-tinker' : (agents[1]&&agents[1].id)||el.value;
  });
}

function render(){
  const b=S.board; if(!b) return;
  $('k-n').textContent=b.agent_count;
  $('k-hot').textContent=b.hot;
  $('k-tasks').textContent=(b.hive.open_tasks||[]).length;
  $('k-msg').textContent=(b.hive.messages||[]).length;
  $('k-hive').textContent = b.hive.harmony==='online' ? '●' : '○';
  const car=b.carrier||{};
  const mesh=car.mesh||{};
  const phone=car.phone||{};
  const locked=mesh.locked!==false && car.locked!==false;
  $('k-carrier').textContent = locked ? 'MESH LOCK' : 'MESH DOWN';
  $('k-bars').textContent = mesh.signal_label||car.signal_label||'';
  $('k-up').textContent = car.uptime_human||'—';
  const plock=!!phone.locked;
  if($('k-phone')) $('k-phone').textContent = plock ? ((phone.name||'PHONE')+' LOCK') : ((phone.name||'PHONE')+' …');
  if($('k-phone-bars')) $('k-phone-bars').textContent = phone.signal_label||'[.....]';
  const purl=(phone.urls&&phone.urls[0]&&phone.urls[0].vision)||'';
  if($('k-phone-url')) $('k-phone-url').textContent = purl || 'Wi‑Fi URL…';
  const kc=$('kpi-carrier');
  if(kc){ kc.style.borderColor = locked ? 'rgba(52,211,153,.45)' : 'rgba(244,114,182,.5)'; }
  const kp=$('kpi-phone');
  if(kp){ kp.style.borderColor = plock ? 'rgba(52,211,153,.45)' : 'rgba(244,114,182,.4)'; }
  $('tagline').textContent=b.tagline||'';
  $('loop').textContent=b.loop||'';
  $('hero-t').textContent = b.hot? `${b.hot} hot · ${b.agent_count} in mesh` : `${b.agent_count} specialists · hive ${b.hive.harmony}`;
  fillSelects();
  renderMesh();
  renderHive();
  renderTasks();
  if(S.selected) select(S.selected,false);
  fetch('/api/carrier/ping?client=ops').catch(()=>{});
}

function renderMesh(){
  const q=($('q').value||'').toLowerCase();
  const list=((S.board&&S.board.agents)||[]).filter(a=>{
    if(!q) return true;
    return (a.id+' '+a.intent+' '+a.domain+' '+(a.skills||[]).join(' ')).toLowerCase().includes(q);
  });
  $('grid').innerHTML = list.map(a=>`
    <article class="card ${a.pulse} ${S.selected===a.id?'selected':''}" data-id="${esc(a.id)}">
      <span class="badge ${a.pulse}">${a.pulse}</span>
      <span class="badge hive">${esc(a.hive_status||'offline')}</span>
      <div class="id">${esc(a.id)}</div>
      <div class="intent">${esc(a.intent)}</div>
      <div>${(a.skills||[]).slice(0,3).map(s=>`<span class="skill">${esc(s)}</span>`).join('')}</div>
      <div class="meta"><span>${esc(a.domain)} · g${a.generation}</span><span>${age(a.age_sec)}</span></div>
    </article>`).join('');
  document.querySelectorAll('#grid .card').forEach(c=>c.onclick=()=>select(c.dataset.id,true));
  $('file-feed').innerHTML = ((S.board.events)||[]).slice().reverse().slice(0,40).map(e=>
    `<div class="ev"><b>${esc(e.clone)}</b> <span class="k">${esc(e.kind)}</span> ${esc(e.path||'')}</div>`
  ).join('') || '<div class="ev">No file pulses yet</div>';
}

function select(id, _){
  S.selected=id;
  const a=((S.board&&S.board.agents)||[]).find(x=>x.id===id);
  document.querySelectorAll('#grid .card').forEach(c=>c.classList.toggle('selected',c.dataset.id===id));
  if(!a){ $('sel-empty').style.display='block'; $('sel-body').style.display='none'; return; }
  $('sel-empty').style.display='none'; $('sel-body').style.display='block';
  $('s-id').textContent=a.name||a.id;
  $('s-intent').textContent=a.intent;
  $('s-meta').textContent=`${a.domain} · gen ${a.generation} · ${a.status} · hive:${a.hive_status} · parent ${a.parent||'—'}`;
  $('s-skills').innerHTML=(a.skills||[]).map(s=>`<span class="skill">${esc(s)}</span>`).join('');
  $('s-j').textContent=(a.journal_tail||[]).join('\n')||'—';
  $('s-l').textContent=(a.lessons_tail||[]).join('\n')||'—';
  $('del-id').value=a.id;
}

function renderHive(){
  const h=S.board.hive||{};
  const tb=$('presence-table').querySelector('tbody');
  tb.innerHTML=(h.members||[]).map(m=>`<tr>
    <td>${esc(m.clone_id)}</td><td>${esc(m.status)}</td>
    <td>${esc(m.current_task||'—')}</td><td>${esc((m.last_seen||'').slice(11,19))}</td>
  </tr>`).join('')||'<tr><td colspan=4>No presence — Join all</td></tr>';
  $('hive-feed').innerHTML=(h.messages||[]).map(m=>`<div class="ev">
    <b>${esc(m.from_id)}</b>→${esc(m.to_id||'*')} <span class="k">${esc(m.kind)}</span><br/>${esc(m.body)}
  </div>`).join('')||'<div class="ev">Silent hive</div>';
}

function renderTasks(){
  const tasks=(S.board.hive&&S.board.hive.tasks)||[];
  $('task-table').querySelector('tbody').innerHTML = tasks.map(t=>`<tr>
    <td>${esc(t.id.slice(0,12))}</td>
    <td>${esc(t.from_id)}→${esc(t.to_id)}</td>
    <td>${esc(t.title)} <span class="badge ${t.status==='open'?'hot':'idle'}">${esc(t.status)}</span></td>
    <td>${t.status==='open'?`<button class="btn" onclick="taskDone('${esc(t.id)}')">Done</button>`:''}</td>
  </tr>`).join('')||'<tr><td colspan=4>No tasks</td></tr>';
}

async function joinAll(){
  toast('Linking hive…');
  const j=await api('/api/hive/join-all',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
  toast(`Hive: ${j.count||0} linked`); await load();
}
function doAuto(e){
  e.preventDefault();
  const task=$('auto-task').value.trim(); if(!task) return false;
  $('auto-out').textContent='Routing…';
  api('/api/auto',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task})})
    .then(async j=>{
      $('auto-out').textContent=JSON.stringify(j,null,2);
      toast(j.ok?`Auto → ${j.chosen&&j.chosen.id}`:'Route failed');
      await load(); openTab('tasks');
    }).catch(err=>{ $('auto-out').textContent=String(err); toast(err.message); });
  return false;
}
function doAutoDry(){
  const task=$('auto-task').value.trim(); if(!task) return toast('Enter a task');
  api('/api/auto',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task,dry_run:true})})
    .then(j=>{ $('auto-out').textContent=JSON.stringify(j,null,2); toast('Preview only'); });
}
function renderCuration(){
  const c=S.curation; if(!c||!c.options){ $('cur-options').innerHTML='<div class="intent">No curation yet — paste conversation context.</div>'; return; }
  $('cur-summary').textContent=c.summary||'';
  $('cur-themes').innerHTML=(c.themes||[]).map(t=>`<span class="skill">${esc(t)}</span>`).join('');
  $('cur-options').innerHTML=c.options.map((o,i)=>`
    <article class="card ${i===0?'hot':'warm'}" data-idx="${i}">
      <span class="badge ${o.kind==='specialist'?'hive':'hot'}">${esc(o.kind)}</span>
      <div class="id">${esc(o.label)}</div>
      <div class="intent">${esc(o.subtitle||o.why||'')}</div>
      <div class="meta"><span>score ${Number(o.score).toFixed(1)}</span><span>${esc(o.domain||o.command||'')}</span></div>
      <div class="actions" style="margin-top:.5rem">
        <button class="btn solid pick-btn" data-idx="${i}">Choose</button>
      </div>
    </article>`).join('');
  document.querySelectorAll('.pick-btn').forEach(b=>b.onclick=()=>pickOption(Number(b.dataset.idx)));
}
function curateNow(e){
  if(e&&e.preventDefault) e.preventDefault();
  const text=$('cur-text').value.trim();
  if(!text){ toast('Add conversation context'); return false; }
  api('/api/curate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,save:true})})
    .then(j=>{ S.curation=j; renderCuration(); toast('Options updated'); })
    .catch(err=>toast(err.message));
  return false;
}
function loadLatestCurate(){
  api('/api/curate/latest').then(j=>{
    if(j&&j.result){ S.curation=j.result; if(j.conversation)$('cur-text').value=j.conversation; renderCuration(); toast('Loaded latest'); }
    else toast('No saved curation');
  }).catch(()=>toast('No latest'));
}
function pickOption(idx){
  const o=(S.curation&&S.curation.options&&S.curation.options[idx]);
  if(!o) return toast('Missing option');
  const a=o.action||{};
  if(a.type==='auto'||a.type==='auto_dispatch'){
    const task=a.task||a.context||$('cur-text').value;
    $('auto-task').value=task;
    openTab('auto');
    api('/api/auto',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task})})
      .then(j=>{ $('auto-out').textContent=JSON.stringify(j,null,2); toast('Dispatched → '+(j.chosen&&j.chosen.id)); load(); });
    return;
  }
  if(a.type==='board'){ openTab('mesh'); toast('Mesh board'); return; }
  if(a.type==='hive-feed'){ openTab('hive'); toast('Hive mind'); return; }
  if(a.type==='delegate'){ openTab('tasks'); toast('Prefer Auto — or pick from/to'); return; }
  if(a.type==='create'){ openTab('manage'); toast('Create specialist'); return; }
  if(a.type==='seed-hospital'){ toast('Re-linking hospital hive…'); joinAll(); return; }
  if(a.type==='absorb'){ openTab('manage'); toast('Use delete/absorb on ephemeral agents'); return; }
  if(o.specialist){
    const task='Engage '+o.specialist+': '+($('cur-text').value||o.subtitle||o.label);
    $('auto-task').value=task;
    openTab('auto');
    api('/api/auto',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task})})
      .then(j=>{ $('auto-out').textContent=JSON.stringify(j,null,2); toast('→ '+(j.chosen&&j.chosen.id)); load(); });
    return;
  }
  toast('Selected: '+o.label);
}
// boot: load latest curation if any
fetch('/api/curate/latest').then(r=>r.json()).then(j=>{
  if(j&&j.result){ S.curation=j.result; if(j.conversation)$('cur-text').value=j.conversation; renderCuration(); }
}).catch(()=>{});
function gcList(){ api('/api/gc/list').then(j=>{ $('gc-out').textContent=JSON.stringify(j,null,2); toast((j.library||[]).length+' games'); }).catch(e=>toast(e.message)); }
function gcStatus(){ api('/api/gc/status').then(j=>{ $('gc-out').textContent=JSON.stringify(j,null,2); }).catch(e=>toast(e.message)); }
function gcLaunch(){
  const game=$('gc-game').value.trim(); if(!game) return toast('Enter game name');
  api('/api/gc/launch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({game})})
    .then(j=>{ $('gc-out').textContent=JSON.stringify(j,null,2); toast(j.ok?'Launched':'Need owned dump in games/'); });
}
function gcPress(btn){
  api('/api/gc/press',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({button:btn})})
    .then(j=>{ toast(j.ok?'Pressed '+btn:j.error); });
}
// lazy load when tab clicked
document.querySelectorAll('.tab').forEach(t=>{
  const prev=t.onclick;
  t.addEventListener('click',()=>{ if(t.dataset.tab==='gc') gcList(); });
});
async function hivePost(){
  const body=$('hive-body').value.trim(); if(!body) return toast('Empty message');
  await api('/api/hive/post',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({from:$('hive-from').value,body,kind:'thought'})});
  $('hive-body').value=''; toast('Posted to hive'); await load();
}
async function broadcastThought(){
  const body=prompt('Broadcast to entire hive:'); if(!body) return;
  await api('/api/hive/post',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({from:'mist-prime',body,kind:'harmony'})});
  toast('Broadcast sent'); await load();
}
function doDelegate(e){
  e.preventDefault();
  api('/api/delegate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
    from:$('d-from').value, to:$('d-to').value, task:$('d-task').value
  })}).then(async j=>{ toast(j.ok!==false?'Delegated':'Failed'); $('d-task').value=''; await load(); }).catch(err=>toast(err.message));
  return false;
}
function prefillDelegate(){
  if(S.selected){ $('d-from').value=S.selected; openTab('tasks'); }
}
async function taskDone(id){
  const result=prompt('Result note (optional):')||'done';
  await api('/api/task/done',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,result})});
  toast('Task done'); await load();
}
function doCreate(e){
  e.preventDefault();
  const body={
    id:$('c-id').value.trim()||undefined,
    intent:$('c-intent').value.trim(),
    domain:$('c-domain').value,
    parent:$('c-parent').value,
    skills:$('c-skills').value,
    ephemeral:$('c-ephemeral').checked
  };
  api('/api/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
    .then(async j=>{ toast(j.ok?'Created & joined hive':'Failed: '+(j.output||'')); if(j.ok){ $('c-intent').value=''; $('c-id').value='';} await load(); openTab('mesh'); })
    .catch(err=>toast(err.message));
  return false;
}
function doStuck(e){
  e.preventDefault();
  api('/api/stuck',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
    problem:$('u-problem').value, parent:$('u-parent').value, skills:$('u-skills').value
  })}).then(async j=>{ toast(j.ok?'Unstick specialist forged':'Failed'); await load(); openTab('mesh'); })
    .catch(err=>toast(err.message));
  return false;
}
async function doEvolve(){
  if(!S.selected) return;
  const lesson=prompt('Lesson for '+S.selected); if(!lesson) return;
  await api('/api/evolve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:S.selected,lesson})});
  toast('Evolved'); await load();
}
async function doDelete(){
  const id=S.selected||$('del-id').value.trim(); if(!id) return toast('No agent selected');
  if(!confirm('Delete/archive '+id+'?')) return;
  await api('/api/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,reason:'deleted from Swarm Ops'})});
  S.selected=null; toast('Deleted (archived)'); await load();
}
function doDeleteInput(){ S.selected=$('del-id').value.trim(); doDelete(); }

document.addEventListener('keydown',e=>{
  if(e.key==='/' && !['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){ e.preventDefault(); $('q').focus(); }
});
load(); setInterval(load, 2000);
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _json(self, code: int, obj: dict) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            return {}

    def _client_meta(self) -> tuple[str, str]:
        ua = self.headers.get("User-Agent") or ""
        ip = self.client_address[0] if self.client_address else ""
        return ua, ip

    def _touch(self, client: str) -> dict:
        ua, ip = self._client_meta()
        # auto-tag phones
        if carrier.is_phone_client(client, ua) or carrier.is_phone_client("auto", ua):
            if not client.startswith("phone"):
                client = "phone-" + (client or "web")
        return carrier.touch(client, user_agent=ua, remote_ip=ip)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _send_file(self, path: Path, fallback: bytes = b"missing") -> None:
        body = path.read_bytes() if path.is_file() else fallback
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        # Command Center is home
        if path in ("/", "/index.html", "/command", "/command/", "/cc"):
            self._send_file(SCRIPTS / "tv_static" / "command.html", b"<h1>Command Center missing</h1>")
            return
        if path in ("/ops", "/ops/", "/ops/index.html"):
            body = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path in ("/tv", "/tv/", "/tv/index.html", "/vision"):
            self._send_file(SCRIPTS / "tv_static" / "tv.html", b"<h1>Vision missing</h1>")
            return
        if path == "/api/board":
            self._touch("ops")
            self._json(200, snapshot_board())
            return
        if path == "/api/carrier":
            self._touch("carrier-poll")
            agents = snapshot_agents()
            hs = hive.snapshot()
            self._json(200, carrier.status(hs, agent_count=len(agents)))
            return
        if path == "/api/carrier/ping":
            qs = parse_qs(urlparse(self.path).query)
            client = (qs.get("client") or ["ping"])[0]
            self._json(200, {"ok": True, **self._touch(client)})
            return
        if path == "/api/carrier/debug":
            agents = snapshot_agents()
            hs = hive.snapshot()
            st = carrier.status(hs, agent_count=len(agents))
            self._json(
                200,
                {
                    "ok": True,
                    "carrier": st,
                    "listening": True,
                    "home": str(HOME),
                    "clones_dir_exists": CLONES.is_dir(),
                    "hive_db_exists": (HOME / "hive" / "hive.db").is_file(),
                    "python": sys.executable,
                    "phone_urls": st.get("lan_urls") or [],
                    "tip": "On phone (same Wi‑Fi): open vision URL. Phone carrier locks when UA is mobile.",
                },
            )
            return
        if path == "/api/hive":
            self._json(200, hive.snapshot())
            return
        if path == "/api/tv":
            self._touch("vision")
            qs = parse_qs(urlparse(self.path).query)
            ch = (qs.get("channel") or ["ALL"])[0]
            self._json(200, tv_snapshot(None if ch in ("ALL", "all", "") else ch))
            return
        if path == "/api/tv/ambient":
            qs = parse_qs(urlparse(self.path).query)
            ch = (qs.get("channel") or ["ALL"])[0]
            if ch in ("ALL", "all", ""):
                thoughts = [
                    {
                        "text": "// mux scan · " + (a["id"] or "?"),
                        "kind": "think",
                        "channel": a["id"],
                    }
                    for a in snapshot_agents()[:3]
                ]
            else:
                ag = next((a for a in snapshot_agents() if a["id"] == ch), None)
                thoughts = []
                if ag:
                    for line in _ambient_thoughts(
                        ag["id"], ag.get("intent", ""), ag.get("domain", "")
                    ):
                        thoughts.append(
                            {"text": line, "kind": "think", "channel": ch}
                        )
            self._json(200, {"thoughts": thoughts})
            return
        if path == "/api/curate/latest":
            import curator

            latest = curator.latest()
            self._json(200, latest or {"ok": False, "error": "none"})
            return
        if path in ("/api/gc/list", "/api/gc/status"):
            gc_scripts = HOME / "gamecube" / "scripts"
            if str(gc_scripts) not in sys.path:
                sys.path.insert(0, str(gc_scripts))
            import gc_play  # type: ignore

            if path.endswith("list"):
                self._json(200, {"ok": True, "library": gc_play.find_games()})
            else:
                self._json(200, {"ok": True, **gc_play.status()})
            return
        self.send_error(404)

    def do_POST(self):
        path = urlparse(self.path).path
        data = self._read_json()

        if path == "/api/create":
            intent = (data.get("intent") or "").strip()
            if not intent:
                self._json(400, {"ok": False, "error": "intent required"})
                return
            args = ["create", "--intent", intent, "--activate"]
            if data.get("id"):
                args += ["--id", str(data["id"]).strip()]
            if data.get("domain"):
                args += ["--domain", str(data["domain"])]
            if data.get("parent"):
                args += ["--parent", str(data["parent"])]
            if data.get("skills"):
                args += ["--skills", str(data["skills"])]
            if data.get("ephemeral"):
                args += ["--ephemeral"]
            result = run_forge(*args)
            self._json(200 if result["ok"] else 500, result)
            return

        if path == "/api/delete":
            cid = (data.get("id") or "").strip()
            if not cid:
                self._json(400, {"ok": False, "error": "id required"})
                return
            args = ["delete", cid, "--reason", data.get("reason") or "ui delete"]
            if data.get("force"):
                args.append("--force")
            result = run_forge(*args)
            self._json(200 if result["ok"] else 500, result)
            return

        if path == "/api/stuck":
            problem = (data.get("problem") or "").strip()
            if not problem:
                self._json(400, {"ok": False, "error": "problem required"})
                return
            result = run_forge(
                "stuck",
                problem,
                "--parent",
                data.get("parent") or "mist-tinker",
                "--skills",
                data.get("skills") or "scavenger-mode",
            )
            self._json(200 if result["ok"] else 500, result)
            return

        if path == "/api/evolve":
            result = run_forge(
                "evolve",
                (data.get("id") or "").strip(),
                "--lesson",
                (data.get("lesson") or "").strip(),
            )
            self._json(200 if result["ok"] else 500, result)
            return

        if path == "/api/absorb":
            args = ["absorb", (data.get("id") or "").strip()]
            if data.get("into"):
                args += ["--into", data["into"]]
            if data.get("lesson"):
                args += ["--lesson", data["lesson"]]
            result = run_forge(*args)
            self._json(200 if result["ok"] else 500, result)
            return

        if path == "/api/delegate":
            frm = (data.get("from") or "").strip()
            to = (data.get("to") or "").strip()
            task = (data.get("task") or "").strip()
            if not frm or not to or not task:
                self._json(400, {"ok": False, "error": "from, to, task required"})
                return
            try:
                t = hive.delegate(frm, to, task)
                push_event(
                    {
                        "ts": now(),
                        "kind": "delegate",
                        "clone": frm,
                        "path": f"→ {to}: {task[:80]}",
                    }
                )
                self._json(200, {"ok": True, "task": t})
            except Exception as e:
                self._json(500, {"ok": False, "error": str(e)})
            return

        if path == "/api/task/done":
            tid = (data.get("id") or "").strip()
            result = hive.task_update(tid, "done", data.get("result") or "")
            self._json(200, result)
            return

        if path == "/api/hive/join-all":
            ids = hive.join_all_from_disk()
            self._json(200, {"ok": True, "count": len(ids), "ids": ids})
            return

        if path == "/api/hive/post":
            msg = hive.post(
                (data.get("from") or "mist-prime").strip(),
                (data.get("body") or "").strip(),
                to_id=(data.get("to") or None),
                kind=(data.get("kind") or "thought"),
            )
            push_event(
                {
                    "ts": now(),
                    "kind": "hive",
                    "clone": msg["from_id"],
                    "path": msg["body"][:100],
                }
            )
            self._json(200, {"ok": True, "message": msg})
            return

        if path == "/api/auto":
            # MIST decides — hospital sectors first
            import auto_router

            task = (data.get("task") or data.get("problem") or "").strip()
            if not task:
                self._json(400, {"ok": False, "error": "task required"})
                return
            dry = bool(data.get("dry_run"))
            if dry:
                self._json(200, {"ok": True, "routes": auto_router.route(task)})
                return
            result = auto_router.dispatch(
                task, from_id=(data.get("from") or "mist-prime").strip()
            )
            push_event(
                {
                    "ts": now(),
                    "kind": "auto",
                    "clone": result.get("chosen", {}).get("id", "—"),
                    "path": task[:120],
                }
            )
            self._json(200, result)
            return

        if path == "/api/curate":
            import curator

            text = (data.get("text") or data.get("conversation") or "").strip()
            if not text:
                self._json(400, {"ok": False, "error": "text required"})
                return
            result = curator.curate(text, limit=int(data.get("limit") or 12))
            if data.get("save", True):
                path_saved = curator.save_session(
                    text, result, label=data.get("label") or "board"
                )
                result["saved"] = str(path_saved)
            push_event(
                {
                    "ts": now(),
                    "kind": "curate",
                    "clone": "mist-prime",
                    "path": f"{len(result.get('options', []))} options",
                }
            )
            self._json(200, result)
            return

        if path.startswith("/api/gc/"):
            gc_scripts = HOME / "gamecube" / "scripts"
            if str(gc_scripts) not in sys.path:
                sys.path.insert(0, str(gc_scripts))
            import gc_play  # type: ignore

            if path == "/api/gc/list":
                self._json(200, {"ok": True, "library": gc_play.find_games()})
                return
            if path == "/api/gc/status":
                self._json(200, {"ok": True, **gc_play.status()})
                return
            if path == "/api/gc/launch":
                game = (data.get("game") or "").strip()
                self._json(200, gc_play.launch(game))
                return
            if path == "/api/gc/press":
                self._json(
                    200,
                    gc_play.press(
                        (data.get("button") or "A").strip(),
                        ms=int(data.get("ms") or 80),
                    ),
                )
                return
            if path == "/api/gc/combo":
                self._json(
                    200,
                    gc_play.combo((data.get("seq") or "A").strip()),
                )
                return

        self._json(404, {"ok": False, "error": "unknown endpoint"})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()

    hive.init_db()
    carrier.touch("boot")
    # ensure mesh linked on boot
    try:
        hive.join_all_from_disk()
    except Exception as e:
        print(f"hive bootstrap: {e}")

    threading.Thread(target=watch_loop, daemon=True).start()
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"MIST Swarm Ops (Hive) → http://{args.host}:{args.port}/")
    print(f"Agentic Vision → http://{args.host}:{args.port}/tv")
    print(f"Carrier API → http://{args.host}:{args.port}/api/carrier")
    print("CARRIER LOCK when board answers. Use carrier_watch.ps1 to hold the link.")
    print("Leave this window open. Ctrl+C stops.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
