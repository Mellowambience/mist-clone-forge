#!/usr/bin/env python3
"""Seed urban nonprofit hospital specialists (EHR-first) and link hive."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

FORGE = Path(__file__).resolve().parent / "forge.py"
ROSTER = Path(__file__).resolve().parent.parent / "roster" / "hospital_wave.json"


def main() -> None:
    specs = json.loads(ROSTER.read_text(encoding="utf-8"))
    # sort hospital priority
    specs = sorted(specs, key=lambda s: (int(s.get("priority", 5)), s["id"]))
    print(f"Seeding {len(specs)} hospital-sector specialists (priority order)…\n")
    for s in specs:
        args = [
            sys.executable,
            str(FORGE),
            "create",
            "--id",
            s["id"],
            "--intent",
            s["intent"],
            "--domain",
            s.get("domain", "hospital"),
            "--name",
            s.get("name", s["id"]),
            "--parent",
            s.get("parent", "mist-prime"),
            "--skills",
            ",".join(s.get("skills", [])),
            "--voice",
            s.get("voice", "Hospital-mission specialist."),
            "--body",
            s.get("body", s["intent"]),
            "--activate",
        ]
        print(f"--- {s['id']} (pri {s.get('priority')}) ---")
        r = subprocess.run(args, capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        if "already exists" in out:
            print("  exists — skip")
        else:
            print(out.strip()[:400])
    # hive link all
    print("\n=== hive join-all ===")
    subprocess.run([sys.executable, str(FORGE), "hive", "join-all"])
    # announce priority doctrine
    subprocess.run(
        [
            sys.executable,
            str(FORGE),
            "hive",
            "post",
            "--from",
            "mist-prime",
            "--kind",
            "harmony",
            "--body",
            "Doctrine: urban nonprofit hospital sectors first (EHR, HIPAA, ED, care, community). Auto-router chooses specialists — not manual ticket queues.",
        ]
    )
    print("\nHospital wave ready. Auto-route with:")
    print("  python auto_router.py --dispatch \"your hospital task\"")


if __name__ == "__main__":
    main()
