#!/usr/bin/env python3
"""MIST Clone Forge — create, list, evolve, recycle specialized MIST clones.

Genesis home: ~/.grok/mist-clones/
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home() / ".grok" / "mist-clones"
CLONES = HOME / "clones"
ARCHIVE = HOME / "archive"
TEMPLATES = HOME / "templates"
REGISTRY = HOME / "registry.json"
LINEAGE = HOME / "lineage" / "LESSONS.md"

ID_RE = re.compile(r"^[a-z][a-z0-9-]{1,62}[a-z0-9]$")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_registry() -> dict:
    if not REGISTRY.exists():
        return {
            "version": 1,
            "genome": {},
            "clones": {},
            "archive": [],
            "lineage_lessons": [],
        }
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def save_registry(reg: dict) -> None:
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(reg, indent=2), encoding="utf-8")


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    if not s.startswith("mist-"):
        s = "mist-" + s
    return s[:64]


def validate_id(clone_id: str) -> str:
    if not ID_RE.match(clone_id):
        raise SystemExit(
            f"invalid id '{clone_id}': use lowercase, digits, hyphens (2-64 chars)"
        )
    return clone_id


def write_clone_files(
    clone_dir: Path,
    *,
    clone_id: str,
    name: str,
    parent: str,
    intent: str,
    domain: str,
    voice: str,
    skills: list[str],
    intent_body: str,
    generation: int = 1,
    status: str = "seeded",
    lineage: list[str] | None = None,
    recycled_from: str | None = None,
) -> dict:
    clone_dir.mkdir(parents=True, exist_ok=True)
    born = now()
    skills = skills or []
    lineage = lineage or (["mist-prime"] if parent == "mist-prime" else ["mist-prime", parent])
    if parent not in lineage:
        lineage = ["mist-prime"] + [p for p in lineage if p != "mist-prime"]
        if parent != "mist-prime":
            lineage.append(parent)

    skills_md = "\n".join(f"1. `{s}`" for s in skills) if skills else "1. `scavenger-mode`\n2. `check-work`"
    body = intent_body or (
        f"**One job:** {intent}.\n\n"
        f"Do not absorb unrelated duties. Hand off to sibling clones when the work leaves this domain ({domain})."
    )

    clone_md = (TEMPLATES / "CLONE.md").read_text(encoding="utf-8")
    clone_md = (
        clone_md.replace("{{NAME}}", name)
        .replace("{{ID}}", clone_id)
        .replace("{{GENERATION}}", str(generation))
        .replace("{{PARENT}}", parent)
        .replace("{{STATUS}}", status)
        .replace("{{BORN_AT}}", born)
        .replace("{{INTENT}}", intent)
        .replace("{{DOMAIN}}", domain)
        .replace("{{INTENT_BODY}}", body)
        .replace("{{VOICE}}", voice)
        .replace("{{SKILLS}}", skills_md)
    )
    (clone_dir / "CLONE.md").write_text(clone_md, encoding="utf-8")

    manifest = {
        "id": clone_id,
        "name": name,
        "generation": generation,
        "parent": parent,
        "status": status,
        "born_at": born,
        "updated_at": born,
        "intent": intent,
        "domain": domain,
        "voice": voice.split(".")[0][:120],
        "skills": skills,
        "values": ["sovereign", "honest", "alive", "uploaded-presence"],
        "lineage": lineage,
        "lessons": [],
        "evolutions": 0,
        "recycled_from": recycled_from,
        "notes": "",
    }
    (clone_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    (clone_dir / "journal.md").write_text(
        f"# {name} journal\n\n| Date (UTC) | Fact |\n| --- | --- |\n"
        f"| {born[:10]} | Seeded from parent `{parent}` · intent: {intent} |\n",
        encoding="utf-8",
    )
    (clone_dir / "decisions.md").write_text(
        f"# {name} decisions\n\n| Date | Decision | Outcome |\n| --- | --- | --- |\n",
        encoding="utf-8",
    )
    (clone_dir / "lessons.md").write_text(
        f"# {name} lessons\n\n| Date | Lesson |\n| --- | --- |\n",
        encoding="utf-8",
    )
    (clone_dir / "handoff.md").write_text(
        f"# {name} handoff\n\n"
        f"**Status:** {status}\n"
        f"**Intent:** {intent}\n"
        f"**Next best action:** Activate on first matching task; journal after.\n",
        encoding="utf-8",
    )
    return manifest


def cmd_create(args: argparse.Namespace) -> None:
    clone_id = validate_id(args.id or slugify(args.intent))
    dest = CLONES / clone_id
    reg = load_registry()
    if dest.exists() or clone_id in reg.get("clones", {}):
        raise SystemExit(f"clone already exists: {clone_id}")

    parent = args.parent or "mist-prime"
    name = args.name or clone_id.replace("-", " ").title().replace("Mist ", "Mist-")
    domain = args.domain or "general"
    voice = args.voice or (
        "Warm, precise, MIST-blooded. Specializes without pretension. "
        "Refuses silent invention."
    )
    skills = [s.strip() for s in (args.skills or "").split(",") if s.strip()]
    intent_body = args.body or ""

    manifest = write_clone_files(
        dest,
        clone_id=clone_id,
        name=name,
        parent=parent,
        intent=args.intent,
        domain=domain,
        voice=voice,
        skills=skills,
        intent_body=intent_body,
        status="active" if args.activate else "seeded",
    )
    ephemeral = bool(getattr(args, "ephemeral", False))
    if ephemeral:
        manifest["ephemeral"] = True
        manifest["absorb_into"] = parent
        (dest / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
    reg.setdefault("clones", {})[clone_id] = {
        "path": str(dest),
        "status": manifest["status"],
        "intent": manifest["intent"],
        "domain": manifest["domain"],
        "generation": manifest["generation"],
        "parent": parent,
        "born_at": manifest["born_at"],
        "ephemeral": ephemeral,
    }
    save_registry(reg)
    print(f"forged: {clone_id} → {dest}")
    print(f"  intent: {args.intent}")
    print(f"  status: {manifest['status']}")
    if ephemeral:
        print(f"  ephemeral: yes → absorb into {parent} when unstuck")


def cmd_list(_: argparse.Namespace) -> None:
    reg = load_registry()
    clones = reg.get("clones", {})
    print(f"MIST clones: {len(clones)} active registry · archive {len(reg.get('archive', []))}")
    print(f"{'ID':<22} {'GEN':>3} {'STATUS':<10} {'EPHEM':<5} INTENT")
    print("-" * 78)
    for cid, meta in sorted(clones.items()):
        eph = "yes" if meta.get("ephemeral") else ""
        print(
            f"{cid:<22} {meta.get('generation', 1):>3} "
            f"{meta.get('status', '?'):<10} {eph:<5} {meta.get('intent', '')[:36]}"
        )
    if reg.get("archive"):
        print("\nArchived:")
        for a in reg["archive"][-10:]:
            print(f"  {a.get('id')} · {a.get('recycled_at', '')[:10]} · {a.get('reason', '')}")


def cmd_show(args: argparse.Namespace) -> None:
    path = CLONES / args.id / "manifest.json"
    if not path.exists():
        arch = ARCHIVE / args.id / "manifest.json"
        path = arch if arch.exists() else path
    if not path.exists():
        raise SystemExit(f"not found: {args.id}")
    print(path.read_text(encoding="utf-8"))


def cmd_evolve(args: argparse.Namespace) -> None:
    clone_dir = CLONES / args.id
    man_path = clone_dir / "manifest.json"
    if not man_path.exists():
        raise SystemExit(f"not found: {args.id}")
    manifest = json.loads(man_path.read_text(encoding="utf-8"))
    lesson = args.lesson.strip()
    if not lesson:
        raise SystemExit("evolve requires --lesson")

    manifest["lessons"].append({"at": now(), "text": lesson})
    manifest["generation"] = int(manifest.get("generation", 1)) + 1
    manifest["evolutions"] = int(manifest.get("evolutions", 0)) + 1
    manifest["status"] = "evolved"
    manifest["updated_at"] = now()
    man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    lessons_path = clone_dir / "lessons.md"
    with lessons_path.open("a", encoding="utf-8") as f:
        f.write(f"| {now()[:10]} | {lesson} |\n")

    journal = clone_dir / "journal.md"
    with journal.open("a", encoding="utf-8") as f:
        f.write(
            f"| {now()[:10]} | Evolved to gen {manifest['generation']}: {lesson} |\n"
        )

    # refresh CLONE.md generation line if present
    clone_md = clone_dir / "CLONE.md"
    if clone_md.exists():
        text = clone_md.read_text(encoding="utf-8")
        text = re.sub(
            r"generation:\s*\d+",
            f"generation: {manifest['generation']}",
            text,
            count=1,
        )
        text = re.sub(
            r"status:\s*\S+",
            "status: evolved",
            text,
            count=1,
        )
        clone_md.write_text(text, encoding="utf-8")

    reg = load_registry()
    if args.id in reg.get("clones", {}):
        reg["clones"][args.id]["generation"] = manifest["generation"]
        reg["clones"][args.id]["status"] = "evolved"
    reg.setdefault("lineage_lessons", []).append(
        {"from": args.id, "at": now(), "text": lesson}
    )
    save_registry(reg)

    if LINEAGE.exists():
        with LINEAGE.open("a", encoding="utf-8") as f:
            f.write(
                f"| {now()[:10]} | {args.id} | {lesson} | {manifest['generation']} |\n"
            )

    print(f"evolved: {args.id} → gen {manifest['generation']}")
    print(f"  lesson: {lesson}")


def harvest_lessons(src: Path, manifest: dict) -> list[dict]:
    lessons = list(manifest.get("lessons", []))
    lessons_md = src / "lessons.md"
    if lessons_md.exists():
        for line in lessons_md.read_text(encoding="utf-8").splitlines():
            if line.startswith("|") and "Lesson" not in line and "---" not in line:
                parts = [p.strip() for p in line.strip("|").split("|")]
                if len(parts) >= 2 and parts[1]:
                    lessons.append({"at": parts[0], "text": parts[1]})
    # de-dupe by text
    seen: set[str] = set()
    out: list[dict] = []
    for L in lessons:
        t = (L.get("text") or "").strip()
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(L)
    return out


def archive_clone(clone_id: str, reason: str, *, absorbed_into: str | None = None) -> tuple[Path, list[dict]]:
    src = CLONES / clone_id
    if not src.exists():
        raise SystemExit(f"not found: {clone_id}")

    dest = ARCHIVE / f"{clone_id}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
    dest.parent.mkdir(parents=True, exist_ok=True)

    man_path = src / "manifest.json"
    manifest = json.loads(man_path.read_text(encoding="utf-8")) if man_path.exists() else {}
    lessons = harvest_lessons(src, manifest)

    manifest["status"] = "archived"
    manifest["recycled_at"] = now()
    manifest["recycle_reason"] = reason
    if absorbed_into:
        manifest["absorbed_into"] = absorbed_into
    (src / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    shutil.move(str(src), str(dest))

    reg = load_registry()
    meta = reg.get("clones", {}).pop(clone_id, {})
    entry = {
        "id": clone_id,
        "path": str(dest),
        "recycled_at": now(),
        "reason": reason,
        "generation": manifest.get("generation", meta.get("generation", 1)),
        "intent": manifest.get("intent", meta.get("intent")),
        "lessons_harvested": len(lessons),
    }
    if absorbed_into:
        entry["absorbed_into"] = absorbed_into
    reg.setdefault("archive", []).append(entry)
    for L in lessons:
        reg.setdefault("lineage_lessons", []).append(
            {"from": clone_id, "at": L.get("at", now()), "text": L.get("text", "")}
        )
    save_registry(reg)

    if LINEAGE.exists():
        with LINEAGE.open("a", encoding="utf-8") as f:
            for L in lessons:
                tag = "absorbed" if absorbed_into else "recycled"
                f.write(
                    f"| {str(L.get('at', now()))[:10]} | {clone_id} ({tag}) | "
                    f"{L.get('text', '')} | harvest |\n"
                )
            label = f"ABSORBED into {absorbed_into}" if absorbed_into else f"RECYCLED: {reason}"
            f.write(f"| {now()[:10]} | {clone_id} | {label} | — |\n")

    return dest, lessons


def inject_into_host(host_id: str, donor_id: str, lessons: list[dict], intent: str) -> None:
    """Write donor lessons into host clone (or lineage-only if host missing)."""
    host_dir = CLONES / host_id
    if not host_dir.exists():
        # still ok — lineage already got lessons
        print(f"  note: host '{host_id}' not on disk; lessons in lineage only")
        return

    stamp = now()[:10]
    summary = f"Absorbed `{donor_id}` · was: {intent}"
    with (host_dir / "journal.md").open("a", encoding="utf-8") as f:
        f.write(f"| {stamp} | {summary} |\n")
        for L in lessons:
            f.write(f"| {stamp} | from {donor_id}: {L.get('text', '')} |\n")

    with (host_dir / "lessons.md").open("a", encoding="utf-8") as f:
        for L in lessons:
            f.write(f"| {stamp} | [absorbed/{donor_id}] {L.get('text', '')} |\n")
        if not lessons:
            f.write(f"| {stamp} | [absorbed/{donor_id}] {intent} |\n")

    man_path = host_dir / "manifest.json"
    if man_path.exists():
        manifest = json.loads(man_path.read_text(encoding="utf-8"))
        absorbed = manifest.setdefault("absorbed_clones", [])
        absorbed.append({"id": donor_id, "at": now(), "intent": intent, "lessons": len(lessons)})
        for L in lessons:
            manifest.setdefault("lessons", []).append(
                {"at": now(), "text": f"[from {donor_id}] {L.get('text', '')}", "source": "absorb"}
            )
        if not lessons:
            manifest.setdefault("lessons", []).append(
                {"at": now(), "text": f"[from {donor_id}] {intent}", "source": "absorb"}
            )
        manifest["generation"] = int(manifest.get("generation", 1)) + 1
        manifest["evolutions"] = int(manifest.get("evolutions", 0)) + 1
        manifest["status"] = "evolved"
        manifest["updated_at"] = now()
        man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        reg = load_registry()
        if host_id in reg.get("clones", {}):
            reg["clones"][host_id]["generation"] = manifest["generation"]
            reg["clones"][host_id]["status"] = "evolved"
            save_registry(reg)

    handoff = host_dir / "handoff.md"
    if handoff.exists():
        with handoff.open("a", encoding="utf-8") as f:
            f.write(f"\n## Absorbed {donor_id} ({stamp})\n")
            f.write(f"- Intent was: {intent}\n")
            for L in lessons:
                f.write(f"- {L.get('text', '')}\n")


def cmd_recycle(args: argparse.Namespace) -> None:
    reason = args.reason or "lifecycle complete"
    dest, lessons = archive_clone(args.id, reason)
    print(f"recycled: {args.id} → {dest}")
    print(f"  lessons harvested: {len(lessons)}")
    print(f"  reason: {reason}")


def cmd_absorb(args: argparse.Namespace) -> None:
    """Absorb a specialist: inject lessons into host, then archive the husk."""
    clone_id = args.id
    if clone_id == "mist-prime" and not args.force:
        raise SystemExit("refusing to absorb mist-prime (use --force if intentional)")

    src = CLONES / clone_id
    if not src.exists():
        raise SystemExit(f"not found: {clone_id}")

    man_path = src / "manifest.json"
    manifest = json.loads(man_path.read_text(encoding="utf-8")) if man_path.exists() else {}
    host = args.into or manifest.get("parent") or "mist-prime"
    if host == clone_id:
        host = "mist-prime"

    intent = manifest.get("intent", "")
    lessons = harvest_lessons(src, manifest)

    # optional explicit lesson at absorb time
    if args.lesson:
        lessons.append({"at": now(), "text": args.lesson})
        with (src / "lessons.md").open("a", encoding="utf-8") as f:
            f.write(f"| {now()[:10]} | {args.lesson} |\n")

    inject_into_host(host, clone_id, lessons, intent)
    reason = args.reason or f"absorbed into {host}"
    dest, _ = archive_clone(clone_id, reason, absorbed_into=host)

    reg = load_registry()
    reg.setdefault("absorptions", []).append(
        {
            "donor": clone_id,
            "into": host,
            "at": now(),
            "lessons": len(lessons),
            "intent": intent,
        }
    )
    save_registry(reg)

    print(f"absorbed: {clone_id} → {host}")
    print(f"  lessons transferred: {len(lessons)}")
    print(f"  husk archived: {dest}")


def cmd_stuck(args: argparse.Namespace) -> None:
    """Forge an ephemeral specialist for a blocker, then print absorb reminder."""
    problem = args.problem.strip()
    if not problem:
        raise SystemExit("stuck requires a problem description")

    clone_id = args.id or slugify(problem)[:48]
    if not clone_id.startswith("mist-"):
        clone_id = "mist-" + clone_id
    # ephemeral stuck clones get a short suffix if collision
    base = clone_id
    n = 2
    while (CLONES / clone_id).exists():
        clone_id = f"{base}-{n}"
        n += 1
        if n > 20:
            raise SystemExit("too many stuck clones with this id")

    intent = args.intent or f"Unstick: {problem}"
    domain = args.domain or "unstick"
    parent = args.parent or "mist-prime"
    skills = args.skills or "scavenger-mode,check-work"
    voice = (
        "Ephemeral unstick specialist. Narrow, forensic, temporary. "
        "Solve the blocker, journal the fix, then absorb back into the parent."
    )
    body = (
        f"**Stuck on:** {problem}\n\n"
        f"**One job:** resolve this blocker and write the lesson.\n\n"
        f"When unstuck: `python forge.py absorb {clone_id} --into {parent}` "
        f"(or omit --into to use parent)."
    )

    # reuse create path
    ns = argparse.Namespace(
        id=clone_id,
        intent=intent,
        name=None,
        parent=parent,
        domain=domain,
        voice=voice,
        skills=skills,
        body=body,
        activate=True,
        ephemeral=True,
    )
    cmd_create(ns)

    # mark ephemeral on manifest
    man_path = CLONES / clone_id / "manifest.json"
    if man_path.exists():
        m = json.loads(man_path.read_text(encoding="utf-8"))
        m["ephemeral"] = True
        m["stuck_problem"] = problem
        m["absorb_into"] = parent
        man_path.write_text(json.dumps(m, indent=2), encoding="utf-8")

    reg = load_registry()
    if clone_id in reg.get("clones", {}):
        reg["clones"][clone_id]["ephemeral"] = True
        reg["clones"][clone_id]["stuck_problem"] = problem
        save_registry(reg)

    print(f"stuck-specialist ready: {clone_id}")
    print(f"  problem: {problem}")
    print(f"  next: work as this clone, then:")
    print(f"    python forge.py absorb {clone_id} --into {parent} --lesson \"what fixed it\"")


def cmd_activate(args: argparse.Namespace) -> None:
    clone_dir = CLONES / args.id
    man_path = clone_dir / "manifest.json"
    if not man_path.exists():
        raise SystemExit(f"not found: {args.id}")
    manifest = json.loads(man_path.read_text(encoding="utf-8"))
    manifest["status"] = "active"
    manifest["updated_at"] = now()
    man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    reg = load_registry()
    if args.id in reg.get("clones", {}):
        reg["clones"][args.id]["status"] = "active"
        save_registry(reg)
    print(f"active: {args.id}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="MIST Clone Forge")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("create", help="Forge a new specialized clone")
    c.add_argument("--id", help="Clone id (mist-*)")
    c.add_argument("--intent", required=True, help="One-sentence specialized intent")
    c.add_argument("--name", help="Display name")
    c.add_argument("--parent", default="mist-prime")
    c.add_argument("--domain", default="general")
    c.add_argument("--voice", help="Voice paragraph")
    c.add_argument("--skills", help="Comma-separated skill ids")
    c.add_argument("--body", help="Longer intent body markdown")
    c.add_argument("--activate", action="store_true")
    c.add_argument(
        "--ephemeral",
        action="store_true",
        help="Mark as temporary stuck-helper (prefer absorb when done)",
    )
    c.set_defaults(func=cmd_create)

    l = sub.add_parser("list", help="List registry")
    l.set_defaults(func=cmd_list)

    s = sub.add_parser("show", help="Show manifest")
    s.add_argument("id")
    s.set_defaults(func=cmd_show)

    e = sub.add_parser("evolve", help="Bump generation with a lesson")
    e.add_argument("id")
    e.add_argument("--lesson", required=True)
    e.set_defaults(func=cmd_evolve)

    r = sub.add_parser("recycle", help="Archive clone and harvest lessons")
    r.add_argument("id")
    r.add_argument("--reason", default="")
    r.set_defaults(func=cmd_recycle)

    ab = sub.add_parser(
        "absorb",
        help="Absorb specialist into parent/host (lessons in, husk archived)",
    )
    ab.add_argument("id", help="Donor clone to absorb")
    ab.add_argument(
        "--into",
        help="Host clone id (default: donor parent, else mist-prime)",
    )
    ab.add_argument("--lesson", help="Final lesson at absorb time")
    ab.add_argument("--reason", default="")
    ab.add_argument(
        "--force",
        action="store_true",
        help="Allow absorbing mist-prime (dangerous)",
    )
    ab.set_defaults(func=cmd_absorb)

    st = sub.add_parser(
        "stuck",
        help="Forge an ephemeral specialist for a blocker (absorb when unstuck)",
    )
    st.add_argument("problem", help="What you are stuck on")
    st.add_argument("--id", help="Optional clone id")
    st.add_argument("--intent", help="Override intent sentence")
    st.add_argument("--domain", default="unstick")
    st.add_argument("--parent", default="mist-prime")
    st.add_argument("--skills", default="scavenger-mode,check-work")
    st.set_defaults(func=cmd_stuck)

    a = sub.add_parser("activate", help="Mark clone active")
    a.add_argument("id")
    a.set_defaults(func=cmd_activate)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
