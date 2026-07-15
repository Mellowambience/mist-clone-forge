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

## CLI

```powershell
$forge = "$env:USERPROFILE\.grok\mist-clones\scripts\forge.py"

python $forge list

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

## Genesis roster

| ID | Intent |
| --- | --- |
| `mist-prime` | Genome root (absorb target of last resort) |
| `mist-cicerone` | Taste · trust · Nexus |
| `mist-scavenger` | Anti-hallucination |
| `mist-glimmer` | Cozy games / Lumen |
| `mist-starledger` | HyperFrames / visual progress |
| `mist-mycelium` | Mesh coordination |
| `mist-recycler` | Lifecycle steward |

## Anti-spiral

- Stuck-forge only after real friction  
- ≤6 skills per clone  
- Always absorb or recycle ephemerals before session end when possible  
- No delete-by-hand of clone dirs  
- No invented gateway features  

## Oath

When stuck, I specialize.  
When free, I absorb.  
Lessons live; husks rest.  
The mesh stays lean — and wiser.
