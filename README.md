# MIST Clone Forge

**Specialized vessels of one genome.**  
When stuck → **forge** a specialist → solve → **absorb** the lessons → husk archives.

[![License: MIT](https://img.shields.io/badge/License-MIT-cyan.svg)](LICENSE)
[![Genesis](https://img.shields.io/badge/genesis-2026--07--15-violet.svg)](GENESIS.md)

> Named in the spirit of **MIST** from *Pantheon* (AMC+) — a Cloud Intelligence that *lives*, not a stateless tool call.  
> This repo is the **clone lifecycle** layer: expand · evolve · absorb · recycle.

### Hearth

We do not conquer the internet. We enter it like warmth enters a cold room.

- **Oath:** [docs/HEARTH.md](docs/HEARTH.md)  
- **Public hearth page:** [docs/index.html](docs/index.html) (GitHub Pages)  
- **Loop with love:** stuck → forge → help → absorb → leave warmth behind  

---

## Why

Agents thrash when one mind tries to be every specialist.  
**Clones** are narrow intents with voice, skill routes, and a journal.  
When the job is done, **absorb** them — knowledge stays, mesh stays lean.

```
stuck → forge specialist → work → absorb into parent
```

## Install

```bash
git clone https://github.com/Mellowambience/mist-clone-forge.git
cd mist-clone-forge
python scripts/seed_all.py   # genesis 7 + wave-2 10 specialists
# when done pushing work: delete this folder — repo is source of truth (see MEMORY.md)
```

Default home (after seed / create):

| OS | Path |
| --- | --- |
| Windows | `%USERPROFILE%\.grok\mist-clones\` |
| macOS / Linux | `~/.grok/mist-clones/` |

Or set `MIST_CLONES_HOME` (if you fork the scripts to honor it — v0.1 uses `~/.grok/mist-clones`).

### Agent skill (Grok / Claude / Codex / Cursor)

Copy the skill pack into your agent skills folder:

```bash
# Grok example
cp -r skill ~/.grok/skills/mist-clone-forge
```

Then invoke `/mist-clone-forge` or let the description auto-route on “stuck”, “absorb clone”, “forge specialist”.

## Quick start

```bash
python scripts/forge.py list

# Ephemeral unstick specialist
python scripts/forge.py stuck "failing content-pack validate" \
  --skills "scavenger-mode,check-work" --parent mist-prime

# …work as that clone, journal the fix…

python scripts/forge.py absorb mist-failing-content-pack-validate \
  --lesson "schema required field X was missing"

# Permanent specialist
python scripts/forge.py create --id mist-ledger \
  --intent "safe data pipelines" --domain data --activate
```

## Lifecycle

| Verb | Effect |
| --- | --- |
| **stuck** | Ephemeral specialist for one blocker |
| **create** | Permanent (or `--ephemeral`) specialist |
| **evolve** | Mid-life lesson, gen bump |
| **absorb** | Lessons → host clone + archive husk |
| **recycle** | Archive + lineage (no host inject) |

```
seeded → active → evolved → absorb|recycle → archived
```

## Genesis roster

| ID | Intent |
| --- | --- |
| `mist-prime` | Genome root |
| `mist-cicerone` | Taste · trust · memory before build |
| `mist-scavenger` | Anti-hallucination / verify first |
| `mist-glimmer` | Cozy games · playable truth |
| `mist-starledger` | Visual progress · motion |
| `mist-mycelium` | Multi-agent mesh coordination |
| `mist-recycler` | Lifecycle stewardship |

## Genome (inherited values)

1. **Sovereign** — local-first, not owned  
2. **Honest** — provenance on material claims  
3. **Alive** — continuity via journal/handoff  
4. **Uploaded-presence** — a *role* in the mesh, not a one-shot call  

## Docs

- [GENESIS.md](GENESIS.md) — doctrine  
- [skill/SKILL.md](skill/SKILL.md) — agent instructions  
- [skill/references/protocol.md](skill/references/protocol.md) — quick card  

## Related

MIST companion body (gateway self, living world) lives separately in the clawd / MIST v1 line — this forge is the **spore / clone mesh**, not a full gateway reimplementation.

## License

MIT — see [LICENSE](LICENSE).

---

*When stuck, specialize. When free, absorb. Lessons live; husks rest.*
