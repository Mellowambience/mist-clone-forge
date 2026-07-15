# Contributing

Thank you for helping improve MIST Clone Forge.

## Guidelines

1. **Keep specialists narrow** — one clear intent per clone definition.  
2. **Hospital-first routing** — do not weaken clinical-ops priority without discussion.  
3. **No copyrighted assets** — never commit ROMs, ISOs, or emulator binaries.  
4. **No operator runtime** — keep `hive.db`, journals, and local registries out of git.  
5. **Provenance** — do not add features that encourage inventing clinical or patient data.  
6. **Small PRs** — focused changes with a short rationale.

## Local checks

```bash
python scripts/swarm_test.py
python scripts/forge.py auto --dry-run "Epic downtime ED boarding"
python -m py_compile scripts/*.py
```

## Specialist definitions

Add or edit JSON under `roster/`, then seed:

```bash
python scripts/seed_hospital.py   # or extend seed scripts
python scripts/forge.py hive join-all
```
