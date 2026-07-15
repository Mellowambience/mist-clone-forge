#!/usr/bin/env python3
"""Local MIST swarm smoke test — census, parallel read, stuck trio, absorb."""
from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HOME = Path.home() / ".grok" / "mist-clones"
FORGE = HOME / "scripts" / "forge.py"
CLONES = HOME / "clones"


def forge(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(FORGE), *args],
        capture_output=True,
        text=True,
    )


def ok(label: str, cond: bool, detail: str = "") -> None:
    mark = "PASS" if cond else "FAIL"
    print(f"[{mark}] {label}" + (f" — {detail}" if detail else ""))
    if not cond:
        raise SystemExit(1)


def main() -> None:
    print("=== MIST SWARM TEST ===\n")
    ok("forge exists", FORGE.is_file(), str(FORGE))
    ok("registry exists", (HOME / "registry.json").is_file())

    r = forge("list")
    ok("forge list", r.returncode == 0, r.stdout.splitlines()[0] if r.stdout else "")
    print(r.stdout)

    manifests = list(CLONES.glob("*/manifest.json"))
    ok("clone dirs", len(manifests) >= 17, f"found {len(manifests)}")

    def load(p: Path):
        return json.loads(p.read_text(encoding="utf-8"))

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(load, p): p for p in manifests}
        for fut in as_completed(futs):
            m = fut.result()
            assert m.get("id") and m.get("intent"), futs[fut]

    ok("parallel manifest read", True, f"{len(manifests)} ok")

    # ephemeral swarm trio
    trio = [
        ("mist-swarm-test-a", "mist-tinker", "path missing"),
        ("mist-swarm-test-b", "mist-scavenger", "schema invalid"),
        ("mist-swarm-test-c", "mist-bridge", "handoff lost"),
    ]
    for cid, parent, problem in trio:
        # clean if leftover
        if (CLONES / cid).exists():
            forge("recycle", cid, "--reason", "prior swarm leftover")
        r = forge(
            "stuck",
            problem,
            "--id",
            cid,
            "--parent",
            parent,
            "--skills",
            "scavenger-mode",
        )
        ok(f"forge stuck {cid}", r.returncode == 0, r.stdout.strip().splitlines()[-1] if r.stdout else "")
        forge("evolve", cid, "--lesson", f"swarm: fixed {problem}")
        r = forge("absorb", cid, "--into", parent, "--lesson", f"swarm PASS {cid}")
        ok(f"absorb {cid} → {parent}", r.returncode == 0)

    # hosts gained generation
    for parent in ("mist-tinker", "mist-scavenger", "mist-bridge"):
        m = load(CLONES / parent / "manifest.json")
        ok(f"{parent} evolved", m.get("status") in ("evolved", "active"), f"gen {m.get('generation')}")

    r = forge("list")
    print("\n=== FINAL LIST ===")
    print(r.stdout)
    print("=== SWARM TEST COMPLETE ===")


if __name__ == "__main__":
    main()
