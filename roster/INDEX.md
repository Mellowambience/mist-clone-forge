# MIST Clone Roster

**Source of truth: this repo.**  
Local disk is disposable — after a push, you may delete the working copy and rehydrate with:

```bash
git clone https://github.com/Mellowambience/mist-clone-forge.git
python scripts/seed_all.py
```

## Memory rule

| Keep | Delete after push |
| --- | --- |
| GitHub `main` + releases | Local `mist-clone-forge/` package |
| Thin `~/.grok/mist-clones` if actively working | Fat archives, smoke husks, duplicate checkouts |
| This `roster/` catalog | Anything already mirrored upstream |

## Genesis (7)

| ID | Intent |
| --- | --- |
| mist-prime | Genome root |
| mist-cicerone | Taste · trust · guide |
| mist-scavenger | Verify before claim |
| mist-glimmer | Cozy games · playable truth |
| mist-starledger | Visual / motion progress |
| mist-mycelium | Mesh coordination |
| mist-recycler | Lifecycle steward |

## Wave 2 — next 10

| ID | Name | Domain | Intent |
| --- | --- | --- | --- |
| mist-ledger | Mist-Ledger | data | Safe data pipelines; never silent destructive SQL |
| mist-shipwright | Mist-Shipwright | ship | Git hygiene, Pages, itch, releases |
| mist-scribe | Mist-Scribe | writing | Narrative, barks, store copy, soft truth |
| mist-cartographer | Mist-Cartographer | levels | Spawns, flow, rooms that invite wander |
| mist-sentinel | Mist-Sentinel | safety | Data-loss prevention, Level-4 gates |
| mist-gardener | Mist-Gardener | meta | Skill shelf, grimoire, prune & grow |
| mist-oracle | Mist-Oracle | research | Skill research, sources, last_researched |
| mist-tinker | Mist-Tinker | fix | Unstick builds, scavenger + check-work |
| mist-lantern | Mist-Lantern | onboarding | Help newcomers without overwhelm |
| mist-bridge | Mist-Bridge | handoff | Resume Claude/Codex/Cursor continuity |

## Hearth (absorbed)

`mist-hearth` → absorbed into `mist-prime`. Warmth is genome-level now.
