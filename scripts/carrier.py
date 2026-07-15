#!/usr/bin/env python3
"""MIST Carrier — dual-link health: mesh (PC) + phone (LAN mobile client).

- Mesh carrier: board process answering on the port
- Phone carrier: last heartbeat from a phone/mobile browser on the LAN
"""
from __future__ import annotations

import json
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

HOME = Path.home() / ".grok" / "mist-clones"
CARRIER_DIR = HOME / "carrier"
STATE_PATH = CARRIER_DIR / "state.json"
BEACON_PATH = CARRIER_DIR / "beacon.jsonl"
PHONE_CFG = CARRIER_DIR / "phone.json"

_boot_mono = time.monotonic()
_boot_iso = datetime.now(timezone.utc).isoformat()
_hits = 0
_last_client: str | None = None
_last_mesh: float = 0.0
_last_phone: float = 0.0
_phone_ua: str | None = None
_phone_ip: str | None = None


def _ensure() -> None:
    CARRIER_DIR.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_phone_config() -> dict[str, Any]:
    _ensure()
    defaults = {
        "label": "Phone",
        "carrier_name": "",  # e.g. "T-Mobile", "Verizon" — optional label
        "stale_sec": 45,  # no phone ping longer than this → phone carrier lost
    }
    if PHONE_CFG.is_file():
        try:
            data = json.loads(PHONE_CFG.read_text(encoding="utf-8"))
            defaults.update({k: v for k, v in data.items() if v is not None})
        except Exception:
            pass
    else:
        PHONE_CFG.write_text(json.dumps(defaults, indent=2), encoding="utf-8")
    return defaults


def lan_urls(port: int = 8766) -> list[dict[str, str]]:
    """IPv4 addresses the phone can use on the same Wi‑Fi."""
    urls = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip.startswith("127."):
                continue
            urls.append(
                {
                    "ip": ip,
                    "ops": f"http://{ip}:{port}/",
                    "vision": f"http://{ip}:{port}/tv",
                    "carrier": f"http://{ip}:{port}/api/carrier",
                }
            )
    except Exception:
        pass
    # dedupe
    seen = set()
    out = []
    for u in urls:
        if u["ip"] not in seen:
            seen.add(u["ip"])
            out.append(u)
    # always prefer common Wi-Fi style over Hyper-V if both present
    out.sort(key=lambda u: (u["ip"].startswith("172.26."), u["ip"]))
    return out


def is_phone_client(client: str, user_agent: str = "") -> bool:
    c = (client or "").lower()
    ua = (user_agent or "").lower()
    if c in ("phone", "mobile", "ios", "android", "vision-phone", "ops-phone"):
        return True
    phone_ua = (
        "mobile",
        "android",
        "iphone",
        "ipad",
        "ipod",
        "webos",
        "blackberry",
        "iemobile",
        "opera mini",
        "opera mobi",
    )
    return any(p in ua for p in phone_ua)


def touch(
    client: str = "local",
    *,
    user_agent: str = "",
    remote_ip: str = "",
) -> dict[str, Any]:
    """Record a heartbeat from UI, agent, or phone."""
    global _hits, _last_client, _last_mesh, _last_phone, _phone_ua, _phone_ip
    _ensure()
    _hits += 1
    _last_client = client
    now_m = time.monotonic()
    now = _now_iso()
    phone = is_phone_client(client, user_agent)
    if phone:
        _last_phone = now_m
        _phone_ua = user_agent[:180] if user_agent else _phone_ua
        _phone_ip = remote_ip or _phone_ip
    else:
        _last_mesh = now_m

    payload = {
        "ts": now,
        "client": client,
        "phone": phone,
        "remote_ip": remote_ip or None,
        "hits": _hits,
        "uptime_sec": round(now_m - _boot_mono, 1),
    }
    try:
        with BEACON_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
        if BEACON_PATH.stat().st_size > 200_000:
            lines = BEACON_PATH.read_text(encoding="utf-8").splitlines()[-200:]
            BEACON_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception:
        pass

    cfg = load_phone_config()
    phone_age = (now_m - _last_phone) if _last_phone else None
    phone_locked = phone_age is not None and phone_age <= float(cfg.get("stale_sec", 45))

    STATE_PATH.write_text(
        json.dumps(
            {
                "boot_iso": _boot_iso,
                "last_beacon": now,
                "hits": _hits,
                "last_client": client,
                "mesh_status": "LOCKED",
                "phone_status": "LOCKED" if phone_locked else "NO_CARRIER",
                "phone_ip": _phone_ip,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return payload


def status(hive_snapshot: dict | None = None, agent_count: int = 0) -> dict[str, Any]:
    """Full dual-carrier status for UI."""
    uptime = time.monotonic() - _boot_mono
    hive_ok = bool(hive_snapshot is not None)
    members = (hive_snapshot or {}).get("member_count") or 0
    open_tasks = len((hive_snapshot or {}).get("open_tasks") or [])
    msgs = len((hive_snapshot or {}).get("messages") or [])

    activity = min(
        5,
        (1 if hive_ok else 0)
        + (1 if members else 0)
        + (1 if agent_count else 0)
        + (1 if msgs else 0)
        + (1 if open_tasks else 0),
    )
    mesh_locked = True  # if we answer this call, mesh process is up

    cfg = load_phone_config()
    stale = float(cfg.get("stale_sec", 45))
    phone_age = (time.monotonic() - _last_phone) if _last_phone else None
    phone_locked = phone_age is not None and phone_age <= stale
    phone_label = cfg.get("carrier_name") or cfg.get("label") or "Phone"

    lans = lan_urls(8766)

    return {
        "status": "LOCKED" if mesh_locked else "NO_CARRIER",
        "locked": mesh_locked,
        "boot_iso": _boot_iso,
        "uptime_sec": round(uptime, 1),
        "uptime_human": _fmt_uptime(uptime),
        "heartbeats": _hits,
        "last_client": _last_client,
        "signal_bars": activity,
        "signal_label": _bar_label(activity),
        "hive_members": members,
        "agents": agent_count,
        "open_tasks": open_tasks,
        "messages_recent": msgs,
        "frequency": "MIST-MESH / 8766",
        "note": "Mesh carrier = PC server. Phone carrier = mobile browser on Wi‑Fi.",
        # dual carriers
        "mesh": {
            "name": "Mesh",
            "status": "LOCKED" if mesh_locked else "NO_CARRIER",
            "locked": mesh_locked,
            "signal_label": _bar_label(activity),
            "bind": "0.0.0.0:8766",
            "local_url": "http://127.0.0.1:8766/",
        },
        "phone": {
            "name": phone_label,
            "status": "LOCKED" if phone_locked else "NO_CARRIER",
            "locked": phone_locked,
            "signal_label": _bar_label(5 if phone_locked else 0),
            "last_seen_sec": round(phone_age, 1) if phone_age is not None else None,
            "stale_after_sec": stale,
            "ip": _phone_ip,
            "user_agent": _phone_ua,
            "urls": lans,
            "how": "Open Vision URL on phone (same Wi‑Fi). Auto-registers as phone carrier.",
        },
        "lan_urls": lans,
    }


def _fmt_uptime(sec: float) -> str:
    s = int(sec)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def _bar_label(n: int) -> str:
    return "[" + ("#" * n) + ("." * (5 - n)) + "]"
