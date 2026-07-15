# Security

## Scope

MIST Hospital Systems Edition is an **operational specialist mesh**. It does not process production PHI by default and must not be treated as a covered-entity system of record.

## Operator responsibilities

| Do | Do not |
| --- | --- |
| Keep runtime under a secured workstation | Commit patient identifiers or chart exports |
| Use de-identified examples in demos | Invent clinical facts for “realism” |
| Require human approval for publish/export | Expose the mesh to the public internet without controls |
| Review specialist intents with Compliance/IS | Use phone LAN access on untrusted networks |

## Network

- Default bind for hospital pilots: `0.0.0.0:8766` (LAN only).  
- Phone access requires same Wi‑Fi and an explicit firewall allow (private profile).  
- Do not port-forward to the public internet without a security review.

## Data at rest (local)

Runtime under `~/.grok/mist-clones/` may include:

- hive SQLite bus  
- clone journals (operator notes)  
- carrier beacons  

Treat that directory as **sensitive operational data**. Exclude it from backups that leave the facility unless encrypted and approved.

## Reporting

Report security issues privately to the repository owner via GitHub security advisories when available, or by private contact listed on the GitHub org profile.
