#!/usr/bin/env python3
"""Seed genesis + wave-2 specialists into ~/.grok/mist-clones from roster."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

FORGE = Path(__file__).resolve().parent / "forge.py"
ROSTER = Path(__file__).resolve().parents[1] / "roster" / "wave2.json"
GENESIS = Path(__file__).resolve().parent / "seed_genesis.py"


def run(args: list[str]) -> int:
    r = subprocess.run(
        [sys.executable, str(FORGE), *args],
        capture_output=True,
        text=True,
    )
    if r.stdout:
        print(r.stdout, end="")
    if r.returncode != 0 and "already exists" not in (r.stderr + r.stdout):
        print(r.stderr, end="", file=sys.stderr)
        return r.returncode
    if "already exists" in (r.stderr + r.stdout):
        print(f"  skip (exists): {args[args.index('--id')+1] if '--id' in args else '?'}")
    return 0


def main() -> None:
    print("=== genesis ===")
    subprocess.run([sys.executable, str(GENESIS)], check=False)

    specs = json.loads(ROSTER.read_text(encoding="utf-8"))
    print("\n=== wave 2 ===")
    for s in specs:
        print(f"--- {s['id']} ---")
        args = [
            "create",
            "--id",
            s["id"],
            "--intent",
            s["intent"],
            "--domain",
            s.get("domain", "general"),
            "--name",
            s.get("name", s["id"]),
            "--parent",
            s.get("parent", "mist-prime"),
            "--skills",
            ",".join(s.get("skills", [])),
            "--voice",
            s.get("voice", "MIST-blooded specialist. Warm, precise, honest."),
            "--body",
            s.get("body", s["intent"]),
            "--activate",
        ]
        run(args)

    print("\n=== roster ===")
    run(["list"])
    print("\nDone. Local clones live under ~/.grok/mist-clones/")
    print("Repo remains source of truth — delete working copies after push.")


if __name__ == "__main__":
    main()
