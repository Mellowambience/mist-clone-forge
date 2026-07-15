#!/usr/bin/env python3
"""MIST Hive Mind — shared bus so every clone works in harmony.

All specialists share:
  - presence (who is awake)
  - messages (broadcast + directed)
  - tasks / delegation
  - harmony pulse (mesh health)

Storage: ~/.grok/mist-clones/hive/hive.db (sqlite, stdlib)
"""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

HOME = Path.home() / ".grok" / "mist-clones"
HIVE_DIR = HOME / "hive"
DB_PATH = HIVE_DIR / "hive.db"
CLONES = HOME / "clones"

_lock = threading.Lock()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _conn() -> sqlite3.Connection:
    HIVE_DIR.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with _lock:
        c = _conn()
        try:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS messages (
                  id TEXT PRIMARY KEY,
                  ts TEXT NOT NULL,
                  from_id TEXT NOT NULL,
                  to_id TEXT,
                  kind TEXT NOT NULL,
                  body TEXT NOT NULL,
                  meta TEXT
                );
                CREATE TABLE IF NOT EXISTS tasks (
                  id TEXT PRIMARY KEY,
                  ts TEXT NOT NULL,
                  updated_at TEXT,
                  from_id TEXT NOT NULL,
                  to_id TEXT NOT NULL,
                  title TEXT NOT NULL,
                  status TEXT NOT NULL,
                  result TEXT,
                  meta TEXT
                );
                CREATE TABLE IF NOT EXISTS presence (
                  clone_id TEXT PRIMARY KEY,
                  joined_at TEXT NOT NULL,
                  last_seen TEXT NOT NULL,
                  status TEXT NOT NULL,
                  current_task TEXT,
                  note TEXT
                );
                CREATE TABLE IF NOT EXISTS links (
                  a TEXT NOT NULL,
                  b TEXT NOT NULL,
                  relation TEXT NOT NULL,
                  PRIMARY KEY (a, b, relation)
                );
                CREATE INDEX IF NOT EXISTS idx_msg_ts ON messages(ts);
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                """
            )
            c.commit()
        finally:
            c.close()


def post(
    from_id: str,
    body: str,
    *,
    to_id: Optional[str] = None,
    kind: str = "thought",
    meta: Optional[dict] = None,
) -> dict:
    init_db()
    mid = str(uuid.uuid4())[:12]
    ts = now()
    with _lock:
        c = _conn()
        try:
            c.execute(
                "INSERT INTO messages VALUES (?,?,?,?,?,?,?)",
                (mid, ts, from_id, to_id, kind, body, json.dumps(meta or {})),
            )
            c.execute(
                "UPDATE presence SET last_seen=?, status=? WHERE clone_id=?",
                (ts, "active", from_id),
            )
            c.commit()
        finally:
            c.close()
    return {
        "id": mid,
        "ts": ts,
        "from_id": from_id,
        "to_id": to_id,
        "kind": kind,
        "body": body,
        "meta": meta or {},
    }


def feed(limit: int = 80, clone_id: Optional[str] = None) -> list[dict]:
    init_db()
    with _lock:
        c = _conn()
        try:
            if clone_id:
                rows = c.execute(
                    """
                    SELECT * FROM messages
                    WHERE to_id IS NULL OR to_id=? OR from_id=?
                    ORDER BY ts DESC LIMIT ?
                    """,
                    (clone_id, clone_id, limit),
                ).fetchall()
            else:
                rows = c.execute(
                    "SELECT * FROM messages ORDER BY ts DESC LIMIT ?", (limit,)
                ).fetchall()
        finally:
            c.close()
    out = []
    for r in rows:
        out.append(
            {
                "id": r["id"],
                "ts": r["ts"],
                "from_id": r["from_id"],
                "to_id": r["to_id"],
                "kind": r["kind"],
                "body": r["body"],
                "meta": json.loads(r["meta"] or "{}"),
            }
        )
    return out


def join(clone_id: str, note: str = "") -> dict:
    init_db()
    ts = now()
    with _lock:
        c = _conn()
        try:
            row = c.execute(
                "SELECT clone_id FROM presence WHERE clone_id=?", (clone_id,)
            ).fetchone()
            if row:
                c.execute(
                    "UPDATE presence SET last_seen=?, status=?, note=? WHERE clone_id=?",
                    (ts, "joined", note, clone_id),
                )
            else:
                c.execute(
                    "INSERT INTO presence VALUES (?,?,?,?,?,?)",
                    (clone_id, ts, ts, "joined", None, note),
                )
            c.commit()
        finally:
            c.close()
    post(
        "hive",
        f"{clone_id} joined the hive mind",
        kind="system",
        meta={"clone": clone_id},
    )
    return {"clone_id": clone_id, "joined_at": ts, "status": "joined"}


def leave(clone_id: str, reason: str = "left") -> None:
    init_db()
    with _lock:
        c = _conn()
        try:
            c.execute("DELETE FROM presence WHERE clone_id=?", (clone_id,))
            c.commit()
        finally:
            c.close()
    post("hive", f"{clone_id} left hive ({reason})", kind="system")


def heartbeat(clone_id: str, status: str = "active", note: str = "") -> None:
    init_db()
    ts = now()
    with _lock:
        c = _conn()
        try:
            row = c.execute(
                "SELECT clone_id FROM presence WHERE clone_id=?", (clone_id,)
            ).fetchone()
            if row:
                c.execute(
                    "UPDATE presence SET last_seen=?, status=?, note=? WHERE clone_id=?",
                    (ts, status, note, clone_id),
                )
            else:
                c.execute(
                    "INSERT INTO presence VALUES (?,?,?,?,?,?)",
                    (clone_id, ts, ts, status, None, note),
                )
            c.commit()
        finally:
            c.close()


def presence_list() -> list[dict]:
    init_db()
    with _lock:
        c = _conn()
        try:
            rows = c.execute(
                "SELECT * FROM presence ORDER BY last_seen DESC"
            ).fetchall()
        finally:
            c.close()
    return [dict(r) for r in rows]


def delegate(
    from_id: str,
    to_id: str,
    title: str,
    *,
    meta: Optional[dict] = None,
) -> dict:
    init_db()
    tid = "task-" + str(uuid.uuid4())[:10]
    ts = now()
    with _lock:
        c = _conn()
        try:
            c.execute(
                "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    tid,
                    ts,
                    ts,
                    from_id,
                    to_id,
                    title,
                    "open",
                    None,
                    json.dumps(meta or {}),
                ),
            )
            c.execute(
                "UPDATE presence SET last_seen=?, current_task=?, status=? WHERE clone_id=?",
                (ts, tid, "delegating", from_id),
            )
            c.execute(
                "UPDATE presence SET last_seen=?, current_task=?, status=? WHERE clone_id=?",
                (ts, tid, "assigned", to_id),
            )
            c.commit()
        finally:
            c.close()
    post(
        from_id,
        f"DELEGATE → {to_id}: {title}",
        to_id=to_id,
        kind="delegate",
        meta={"task_id": tid},
    )
    # notify hive
    post(
        "hive",
        f"Harmony: {from_id} delegated to {to_id} — {title}",
        kind="harmony",
        meta={"task_id": tid, "from": from_id, "to": to_id},
    )
    # write into assignee handoff
    handoff = CLONES / to_id / "handoff.md"
    if handoff.parent.is_dir():
        with handoff.open("a", encoding="utf-8") as f:
            f.write(f"\n## Delegated task {tid} ({ts[:10]})\n")
            f.write(f"- From: `{from_id}`\n- Task: {title}\n- Status: open\n")
    return {
        "id": tid,
        "from_id": from_id,
        "to_id": to_id,
        "title": title,
        "status": "open",
        "ts": ts,
    }


def task_update(task_id: str, status: str, result: str = "") -> dict:
    init_db()
    ts = now()
    with _lock:
        c = _conn()
        try:
            c.execute(
                "UPDATE tasks SET status=?, result=?, updated_at=? WHERE id=?",
                (status, result, ts, task_id),
            )
            row = c.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            c.commit()
        finally:
            c.close()
    if not row:
        return {"ok": False, "error": "task not found"}
    post(
        row["to_id"],
        f"Task {task_id} → {status}" + (f": {result}" if result else ""),
        to_id=row["from_id"],
        kind="task_result",
        meta={"task_id": task_id, "status": status},
    )
    return {"ok": True, "id": task_id, "status": status, "result": result}


def tasks(status: Optional[str] = None, limit: int = 50) -> list[dict]:
    init_db()
    with _lock:
        c = _conn()
        try:
            if status:
                rows = c.execute(
                    "SELECT * FROM tasks WHERE status=? ORDER BY ts DESC LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = c.execute(
                    "SELECT * FROM tasks ORDER BY ts DESC LIMIT ?", (limit,)
                ).fetchall()
        finally:
            c.close()
    out = []
    for r in rows:
        out.append(
            {
                "id": r["id"],
                "ts": r["ts"],
                "updated_at": r["updated_at"],
                "from_id": r["from_id"],
                "to_id": r["to_id"],
                "title": r["title"],
                "status": r["status"],
                "result": r["result"],
                "meta": json.loads(r["meta"] or "{}"),
            }
        )
    return out


def link(a: str, b: str, relation: str = "harmony") -> None:
    init_db()
    with _lock:
        c = _conn()
        try:
            c.execute(
                "INSERT OR REPLACE INTO links VALUES (?,?,?)", (a, b, relation)
            )
            c.execute(
                "INSERT OR REPLACE INTO links VALUES (?,?,?)", (b, a, relation)
            )
            c.commit()
        finally:
            c.close()


def links() -> list[dict]:
    init_db()
    with _lock:
        c = _conn()
        try:
            rows = c.execute("SELECT * FROM links").fetchall()
        finally:
            c.close()
    return [dict(r) for r in rows]


def join_all_from_disk() -> list[str]:
    """Connect every clone on disk into the hive + full mesh links."""
    init_db()
    ids = []
    if CLONES.is_dir():
        for d in sorted(CLONES.iterdir()):
            if d.is_dir() and (d / "manifest.json").is_file():
                ids.append(d.name)
    for cid in ids:
        join(cid, note="auto-joined mesh")
        heartbeat(cid, "harmonized", "hive mind online")
    # full mesh: every pair linked (for small N=17 this is fine)
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            link(a, b, "hive")
    post(
        "hive",
        f"Harmony pulse: {len(ids)} specialists linked in one mind",
        kind="harmony",
        meta={"count": len(ids)},
    )
    return ids


def snapshot() -> dict[str, Any]:
    init_db()
    members = presence_list()
    open_tasks = tasks(status="open", limit=30)
    recent = feed(limit=50)
    all_tasks = tasks(limit=30)
    return {
        "ts": now(),
        "member_count": len(members),
        "members": members,
        "open_tasks": open_tasks,
        "tasks": all_tasks,
        "messages": recent,
        "links": len(links()),
        "harmony": "online" if members else "empty",
        "principle": "One genome · many specialists · shared bus · work in harmony",
    }


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="MIST Hive Mind")
    sub = p.add_subparsers(dest="cmd", required=True)

    j = sub.add_parser("join-all", help="Join every disk clone into hive")
    j.set_defaults(fn=lambda a: print(json.dumps(join_all_from_disk())))

    s = sub.add_parser("status", help="Hive snapshot")
    s.set_defaults(fn=lambda a: print(json.dumps(snapshot(), indent=2)))

    f = sub.add_parser("feed", help="Message feed")
    f.add_argument("--limit", type=int, default=30)
    f.set_defaults(
        fn=lambda a: print(json.dumps(feed(a.limit), indent=2))
    )

    po = sub.add_parser("post", help="Post to hive")
    po.add_argument("--from", dest="from_id", required=True)
    po.add_argument("--to", dest="to_id", default=None)
    po.add_argument("--kind", default="thought")
    po.add_argument("body")
    po.set_defaults(
        fn=lambda a: print(
            json.dumps(
                post(a.from_id, a.body, to_id=a.to_id, kind=a.kind), indent=2
            )
        )
    )

    d = sub.add_parser("delegate", help="Delegate task")
    d.add_argument("--from", dest="from_id", required=True)
    d.add_argument("--to", dest="to_id", required=True)
    d.add_argument("title")
    d.set_defaults(
        fn=lambda a: print(
            json.dumps(delegate(a.from_id, a.to_id, a.title), indent=2)
        )
    )

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
