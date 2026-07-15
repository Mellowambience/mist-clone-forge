# Memory discipline

## Rule

**Repo is memory. Disk is scratch.**

1. Write specialists, docs, and lessons **to GitHub** (`roster/`, `docs/`, releases).  
2. After a successful `git push`, **delete** the local working copy if you need space.  
3. Rehydrate only when working:

```bash
git clone https://github.com/Mellowambience/mist-clone-forge.git
cd mist-clone-forge
python scripts/seed_all.py   # optional: thin clones under ~/.grok/mist-clones
```

4. Prefer **absorb** over keeping ephemeral stuck-clones forever.  
5. Prune `~/.grok/mist-clones/archive/` smoke tests occasionally.

## What not to keep locally

- Duplicate checkouts of this repo  
- Huge `node_modules` unrelated to active work  
- Absorbed clone husks once lessons are in lineage + remote  

## Operator home (thin)

`~/.grok/mist-clones/` may hold active manifests while you work.  
It is **not** the archive of record — the public repo + releases are.
