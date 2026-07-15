#!/usr/bin/env python3
"""Seed the Hospital Systems Edition of MIST (one command for health systems)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
FORGE = SCRIPTS / "forge.py"
CONFIG = ROOT / "config" / "hospital_system.json"
HOSPITAL_ROSTER = ROOT / "roster" / "hospital_wave.json"
RUNTIME = Path.home() / ".grok" / "mist-clones"


def run_forge(*args: str) -> None:
    r = subprocess.run(
        [sys.executable, str(FORGE), *args],
        capture_output=True,
        text=True,
    )
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    if out:
        print(out[:500])


def ensure_runtime_config() -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    (RUNTIME / "roster").mkdir(parents=True, exist_ok=True)
    (RUNTIME / "config").mkdir(parents=True, exist_ok=True)
    # copy hospital roster + config into runtime home
    if HOSPITAL_ROSTER.is_file():
        shutil.copy2(HOSPITAL_ROSTER, RUNTIME / "roster" / "hospital_wave.json")
    if CONFIG.is_file():
        shutil.copy2(CONFIG, RUNTIME / "config" / "hospital_system.json")
    emu = ROOT / "roster" / "emulator_wave.json"
    # intentionally NOT seeding GameCube for hospital edition
    print(f"Runtime home: {RUNTIME}")


def seed_core(cfg: dict) -> None:
    for s in cfg.get("mesh_core") or []:
        print(f"--- core {s['id']} ---")
        args = [
            "create",
            "--id",
            s["id"],
            "--intent",
            s["intent"],
            "--domain",
            s.get("domain", "general"),
            "--parent",
            s.get("parent", "mist-prime"),
            "--skills",
            ",".join(s.get("skills") or ["scavenger-mode"]),
            "--activate",
        ]
        run_forge(*args)


def seed_hospital_wave() -> None:
    print("\n=== hospital wave (EHR-first) ===")
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "seed_hospital.py")],
        cwd=str(ROOT),
    )
    if r.returncode != 0:
        print("seed_hospital.py reported errors (existing clones are OK)")


def main() -> None:
    print("MIST Hospital Systems Edition — seed\n")
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    print(f"Edition: {cfg.get('title')}")
    print(f"Audience: {cfg.get('audience')}\n")

    ensure_runtime_config()
    seed_core(cfg)
    seed_hospital_wave()

    print("\n=== hive join-all ===")
    run_forge("hive", "join-all")
    run_forge(
        "hive",
        "post",
        "--from",
        "mist-prime",
        "--kind",
        "harmony",
        "--body",
        "Hospital Systems Edition online. Auto-route prioritizes EHR, privacy, ED, care, mission revenue, and community benefit.",
    )

    print(
        """
Done.

Start Command Center:
  set MIST_HOST=0.0.0.0
  python -u scripts/mist_serve.py

  Windows: scripts\\START_MIST.bat
  Open:    http://127.0.0.1:8766/

Docs: docs/HOSPITAL_SYSTEMS.md
"""
    )


if __name__ == "__main__":
    main()
