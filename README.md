# MIST — Hospital Systems Edition

**Specialist agent mesh for hospital operations**  
Urban & regional nonprofit health systems · EHR · privacy · ED · care · mission

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Edition](https://img.shields.io/badge/edition-hospital%20systems-0ea5e9.svg)](docs/HOSPITAL_SYSTEMS.md)

MIST is not a ticket queue and not a generic chatbot.  
It is a **hive of operational specialists** that auto-route hospital work—downtime, BAAs, boarding, charity care, staffing—so the right mind answers first.

> **Operational intelligence only.** Not clinical decision support for diagnosis or treatment. Never invent patient data.

---

## Why hospitals use it

| Pain | MIST response |
| --- | --- |
| Issues bounce across IS, nursing, compliance, RCM | **Auto-route** to EHR / ED / HIPAA / revenue specialists |
| Knowledge dies in tickets | **Hive handoffs** + absorb lessons into the mesh |
| Generic AI invents chart facts | **Provenance posture** + HIPAA watcher on PHI-ish tasks |
| Tools feel like ServiceNow sludge | **Command Center** — one screen, live mesh, no approval theater |

Full offering: **[docs/HOSPITAL_SYSTEMS.md](docs/HOSPITAL_SYSTEMS.md)**

---

## Hospital specialist mesh (included)

| Clinical systems | Care ops | Mission & access |
| --- | --- | --- |
| EHR · Informatics | ED · Behavioral ops | Access · Community |
| HIPAA · Cyber-health | Care coord · Quality | Revenue (FAP) · Grants |
| | Pharmacy · Workforce | Pop health · Supply · Facilities |

Plus mesh core: Prime · Scavenger · Sentinel · Tinker · Bridge.

---

## Deploy (hospital workstation)

```bash
git clone https://github.com/Mellowambience/mist-clone-forge.git
cd mist-clone-forge

# One command: hospital edition seed
python scripts/seed_hospital_system.py

# Command Center (PC + phone on same Wi‑Fi)
set MIST_HOST=0.0.0.0
python -u scripts/mist_serve.py
```

**Windows:** double‑click `scripts/START_MIST.bat`

| Surface | URL |
| --- | --- |
| **Hospital Command Center** | http://127.0.0.1:8766/ |
| **Agentic Vision** | http://127.0.0.1:8766/tv |
| **Carrier status** | http://127.0.0.1:8766/api/carrier |

Phone (same Wi‑Fi): `http://<PC-LAN-IP>:8766/`  
Firewall helper (Admin once): `scripts/ALLOW_PHONE_FIREWALL.bat`

---

## Day-one commands

```bash
# MIST chooses the specialist (hospital-first)
python scripts/forge.py auto "Epic downtime while ED is boarding"
python scripts/forge.py auto "HIPAA BAA for population health vendor"
python scripts/forge.py auto "charity care financial assistance denial"

# Preview only
python scripts/forge.py auto --dry-run "order set alert fatigue sepsis"

# Hive
python scripts/forge.py hive feed
python scripts/forge.py task list
```

---

## Configuration

Hospital profile: [`config/hospital_system.json`](config/hospital_system.json)  
Specialist definitions: [`roster/hospital_wave.json`](roster/hospital_wave.json)

Runtime (local, not in git): `~/.grok/mist-clones/`

---

## Security

See **[SECURITY.md](SECURITY.md)**.

- Local-first runtime  
- No PHI in the repository  
- Human approval for irreversible / public actions  
- Not a medical device  

---

## Optional modules

| Module | Docs |
| --- | --- |
| Command Center details | [docs/COMMAND_CENTER.md](docs/COMMAND_CENTER.md) |
| Hospital specialist map | [docs/HOSPITAL.md](docs/HOSPITAL.md) · [docs/HOSPITAL_SYSTEMS.md](docs/HOSPITAL_SYSTEMS.md) |
| GameCube agent play (lab only) | [docs/GAMECUBE.md](docs/GAMECUBE.md) — owned dumps only; not part of hospital seed |

---

## Project layout

```text
config/                 Hospital Systems profile
roster/                 Specialist definitions (hospital + optional)
scripts/                Forge, hive, carrier, server, seed, UI
skill/                  Agent skill pack for IDE copilots
docs/                   Hospital offering & operator guides
templates/              Clone templates
```

---

## License

MIT — see [LICENSE](LICENSE).

---

*Built for hospital systems that still treat care as a public good.*
