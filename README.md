# MIST Clone Forge

**Specialized agent vessels · hospital-first routing · hive mind · command center**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

MIST is a **mesh of specialists**, not a ticket queue.  
Describe a need — the hive **auto-routes** (urban nonprofit hospital sectors first).  
Expand · evolve · absorb · recycle.

---

## Features

| Area | What you get |
| --- | --- |
| **Clone lifecycle** | Create, evolve, absorb, delete specialists |
| **Hive mind** | Shared presence, messages, delegation |
| **Auto-router** | Hospital-first scoring (EHR, HIPAA, ED, care, …) |
| **Command Center** | Live dashboard at `:8766` |
| **Agentic Vision** | Live cognition stream for the mesh |
| **Dual carrier** | Mesh (PC) + Phone (LAN Wi‑Fi) |
| **Curator** | Options ranked from conversation context |
| **GameCube hub** | Dolphin launcher + agent inputs (*owned dumps only*) |

---

## Quick start

### Requirements

- Windows 10/11 (primary target) or any OS with Python 3.10+
- Python on `PATH`

### Install

```bash
git clone https://github.com/Mellowambience/mist-clone-forge.git
cd mist-clone-forge
```

Runtime home (created on first seed):

```text
~/.grok/mist-clones/
```

### Seed specialists

```bash
# Genesis + general mesh
python scripts/seed_genesis.py

# Urban nonprofit hospital wave (EHR-first)
python scripts/seed_hospital.py

# Link everyone into the hive
python scripts/forge.py hive join-all
```

### Command Center

```bash
# Windows: bind all interfaces (PC + phone on Wi‑Fi)
set MIST_HOST=0.0.0.0
python -u scripts/mist_serve.py
```

Or double‑click **`scripts/START_MIST.bat`**.

| Surface | URL |
| --- | --- |
| **Command Center** | http://127.0.0.1:8766/ |
| **Agentic Vision** | http://127.0.0.1:8766/tv |
| **Classic Ops** | http://127.0.0.1:8766/ops |
| **Carrier API** | http://127.0.0.1:8766/api/carrier |

**Phone (same Wi‑Fi):** `http://<your-lan-ip>:8766/`  
If the phone cannot connect, run **`scripts/ALLOW_PHONE_FIREWALL.bat`** once as Administrator.

---

## CLI

```bash
python scripts/forge.py list
python scripts/forge.py auto "Epic downtime while ED is boarding"
python scripts/forge.py auto --dry-run "HIPAA BAA for vendor"
python scripts/forge.py curate "conversation themes…"
python scripts/forge.py hive feed
python scripts/forge.py delegate --from mist-prime --to mist-tinker "fix the build"
python scripts/forge.py create --id mist-example --intent "one job" --activate
python scripts/forge.py delete mist-example --reason "retired"
```

---

## Hospital-first doctrine

Auto-routing **prefers urban nonprofit hospital sectors** before general/game skills:

EHR · Informatics · HIPAA · Cyber · ED · Behavioral ops · Care coordination · Community benefit · Access · Quality · Workforce · Revenue (mission-first) · Grants · Pharmacy · Supply · Pop health · Facilities

These are **operational specialists** (workflows, compliance, coordination)—not clinical decision engines. Never invent patient data.

---

## GameCube / Dolphin (optional)

```bash
# Install Dolphin yourself (not bundled):
# https://dolphin-emu.org/download/

# Place legally owned dumps in:
#   ~/.grok/mist-clones/gamecube/games/

python gamecube/scripts/gc_play.py list
python gamecube/scripts/gc_play.py launch "game-name"
python gamecube/scripts/gc_play.py press A
```

This repository **does not** ship emulators or copyrighted game images.

---

## Project layout

```text
scripts/           # forge, hive, carrier, router, server, UI assets
roster/            # hospital + emulator specialist definitions
templates/         # clone templates
skill/             # agent skill pack (Grok / Claude / Codex style)
gamecube/          # play hub (no binaries, no ISOs)
docs/              # additional documentation
```

---

## Design principles

1. **Specialists, not tickets** — one intent per vessel  
2. **Hospital sectors first** when the text matches clinical ops  
3. **Hive harmony** — shared bus, not isolated chatbots  
4. **Absorb lessons** — keep wisdom, archive husks  
5. **Provenance** — no silent invention  
6. **Repo is memory** — runtime state stays local under `~/.grok/mist-clones/`

---

## License

MIT — see [LICENSE](LICENSE).

---

*When stuck, specialize. When free, absorb. Mesh locked · phone optional · work becoming real.*
