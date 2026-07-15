---
name: mist-clone-forge
description: >
  Build, spawn, evolve, absorb, and recycle specialized clones of Agent MIST.
  When stuck, forge an ephemeral specialist; when unstuck, absorb it into parent
  so lessons stay and the husk archives. Use for genesis clones, specialized
  intent, stuck→forge→absorb, lifecycle, lineage lessons, /mist-clone-forge,
  mist clone, forge clone, absorb clone, recycle clone.
---

# MIST Clone Forge

> Specialized vessels of one genome. **Stuck → forge → work → absorb.**

## Primary protocol (default)

When **you are stuck** (missing path, failing command, wrong domain, unclear API, scope thrash):

```
1. STUCK     name the blocker in one sentence
2. FORGE     python forge.py stuck "the blocker" --skills "relevant,skills"
3. BECOME    load that clone's CLONE.md + listed skills; solve only that
4. LESSON    journal the fix on the clone
5. ABSORB    python forge.py absorb <id> --lesson "what fixed it"
             → lessons enter parent (or --into mist-prime)
             → husk archives; mesh stays lean
```

**Absorb** = integrate knowledge into the host clone, then archive the specialist.  
**Recycle** = archive without a specific host (still harvests to lineage).

Prefer **absorb** for ephemeral stuck-helpers. Prefer **recycle** for permanent roles that are truly retired.

## Home

| Path | What |
| --- | --- |
| `~/.grok/mist-clones/GENESIS.md` | Doctrine |
| `~/.grok/mist-clones/registry.json` | Live roster |
| `~/.grok/mist-clones/clones/<id>/` | Active vessels |
| `~/.grok/mist-clones/archive/` | Recycled / absorbed husks |
| `~/.grok/mist-clones/lineage/LESSONS.md` | Shared wisdom |
| `~/.grok/mist-clones/scripts/forge.py` | CLI |

MIST body: `~/mist-v1-build/clawd/`

## When to load

- **Stuck** on a problem outside current focus  
- User wants a specialist or mesh expansion  
- Unstick done → **absorb**  
- Stale permanent role → recycle  
- Genesis / forge / clone language  

## Hive mind + auto-route (not manual tickets)

All specialists share `~/.grok/mist-clones/hive/hive.db`:

- **presence** · **messages** · **tasks/delegation** · **harmony links**
- On create/stuck: auto-join hive  
- On absorb/delete: leave + harmony notice  
- **`python forge.py auto "task…"`** — MIST picks specialist (**urban nonprofit hospital sectors first**) and dispatches  
- Manual delegate is override only  

Doctrine: **hospital mesh before games/video/other** (EHR, HIPAA, ED, care, community, revenue, workforce…).

Live UI: http://127.0.0.1:8766/ — tabs **Your options** (curated from conversation) · **Auto (MIST)** · Mesh · Hive · Tasks · Manage.

### Curate from conversation
```powershell
python $forge curate "paste conversation themes…" 
python $forge curate --latest
```
Board: paste context → **Update my options** → user clicks a card → auto-dispatch or open the right tool.  
Saved under `~/.grok/mist-clones/curation/latest.json`.

## CLI

```powershell
$forge = "$env:USERPROFILE\.grok\mist-clones\scripts\forge.py"

python $forge list
python $forge create --id mist-x --intent "…" --activate
python $forge delete mist-x --reason "retired"
python $forge delegate --from mist-prime --to mist-tinker "fix the build"
python $forge hive join-all
python $forge hive feed
python $forge hive post --from mist-prime --body "hello mesh" --kind harmony
python $forge task list
python $forge task done --id task-… --result "fixed"

# Stuck → ephemeral specialist
python $forge stuck "Three.js CapsuleGeometry missing in r128" `
  --skills "threejs-hd2d,scavenger-mode" --parent mist-glimmer

# Permanent specialist
python $forge create --id mist-ledger --intent "safe BigQuery pipelines" `
  --domain data --skills "gcp-data-pipelines,accidental-data-loss-prevention" --activate

# After the specialist solved it
python $forge absorb mist-threejs-capsulegeometry-missing `
  --into mist-glimmer --lesson "r128 has no CapsuleGeometry; use Cylinder+Sphere"

# Soft retire (no host injection beyond lineage)
python $forge recycle mist-old --reason "role closed"

python $forge evolve mist-glimmer --lesson "optional mid-life lesson"
python $forge show mist-prime
```

## Agent workflow — stuck → forge → absorb

| Step | Do | Don't |
| --- | --- | --- |
| Detect stuck | 2+ failed attempts, missing skill domain, or thrashing | Spawn on first mild uncertainty |
| Forge | Narrow intent = the blocker only | Second Prime / whole shelf of skills |
| Work | Scavenge → fix → journal | Scope-creep into unrelated tasks |
| Absorb | Host gets lessons + gen bump; husk archives | Leave ephemeral clones forever |
| Continue | Parent continues with new knowledge | Re-spawn the same stuck id endlessly |

### Intent quality

| Good | Bad |
| --- | --- |
| "Unstick: validate lumen content-pack schema" | "Be smarter" |
| "Unstick: HyperFrames keyframes seek-safe" | "Fix the project" |

## Absorb vs recycle

| | Absorb | Recycle |
| --- | --- | --- |
| Host clone | Yes (`--into` or parent) | No |
| Host gen bump | Yes | No |
| Lineage lessons | Yes | Yes |
| Archive husk | Yes | Yes |
| Use when | Stuck-helper done; merge role | Permanent role ends |

Never absorb `mist-prime` without `--force`.

## Act *as* a clone

1. Read `clones/<id>/CLONE.md` + `handoff.md`  
2. Load skills hub → leaf → verify  
3. Work under intent + voice  
4. Journal facts  
5. Evolve mid-flight if durable lesson  
6. **Absorb** if ephemeral / stuck-helper; else keep active  

## Memory rule (repo is truth)

1. Write roster/docs to **GitHub** first  
2. After successful push, **delete** local package checkout (`~/mist-clone-forge`)  
3. Thin `~/.grok/mist-clones` is optional scratch — rehydrate via `seed_all.py`  
4. Prune `archive/` after absorb  

https://github.com/Mellowambience/mist-clone-forge

## Roster (17)

**Genesis:** prime · cicerone · scavenger · glimmer · starledger · mycelium · recycler  

**Wave 2:** ledger · shipwright · scribe · cartographer · sentinel · gardener · oracle · tinker · lantern · bridge  

| ID | Intent |
| --- | --- |
| `mist-ledger` | Safe data pipelines |
| `mist-shipwright` | Ship / git / Pages / itch |
| `mist-scribe` | Narrative & store copy |
| `mist-cartographer` | Level flow / spawns |
| `mist-sentinel` | Safety · Level-4 gates |
| `mist-gardener` | Skill shelf / grimoire |
| `mist-oracle` | Research with sources |
| `mist-tinker` | Unstick builds |
| `mist-lantern` | Gentle onboarding |
| `mist-bridge` | Cross-agent handoffs |

## Anti-spiral

- Stuck-forge only after real friction  
- ≤6 skills per clone  
- Always absorb or recycle ephemerals before session end when possible  
- No delete-by-hand of active clone dirs (use absorb/recycle)  
- After push, **do** delete disposable local packages  
- No invented gateway features  

## Oath

When stuck, I specialize.  
When free, I absorb.  
Repo remembers; disk can forget.  
Lessons live; husks rest.  
The mesh stays lean — and warmer.
