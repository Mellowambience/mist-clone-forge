# MIST for Hospital Systems

**Audience:** urban & regional **nonprofit hospital systems**, clinical IS, compliance, revenue cycle, nursing ops, and community benefit leaders.

MIST is a **specialist mesh** tuned for the work that keeps hospitals running—EHR friction, privacy, ED flow, care transitions, staffing, mission billing—not a generic chatbot and not a ServiceNow clone.

---

## What it is

| Layer | Role for a hospital |
| --- | --- |
| **Specialists** | Named vessels (EHR, HIPAA, ED, care coord, …) with clear intents |
| **Auto-router** | Routes a free-text need to the right specialist first |
| **Hive mind** | Shared presence, handoffs, and task delegation |
| **Command Center** | Live ops dashboard for the mesh |
| **Carrier** | PC mesh lock + optional phone-on-Wi‑Fi lock for rounding / on-call |

## What it is not

- Not an EHR replacement  
- Not a medical device or diagnostic system  
- Not clinical decision support for diagnosis/treatment  
- Not a license to invent PHI, labs, or chart content  
- Not a ticket warehouse  

**Operational intelligence only.** Clinicians remain accountable for care.

---

## Specialist map (hospital edition)

### Clinical systems & privacy

| ID | Focus |
| --- | --- |
| `mist-ehr` | EHR workflows, downtime, identity, interoperability |
| `mist-informatics` | Order sets, CDS, alert fatigue |
| `mist-hipaa` | Privacy, BAAs, minimum necessary, breach posture |
| `mist-cyber-health` | Ransomware readiness, device network safety |

### Care delivery ops

| ID | Focus |
| --- | --- |
| `mist-ed` | ED boarding, diversion, surge |
| `mist-behavioral` | BH boarding / holds **process ops** (not therapy) |
| `mist-care-coord` | Discharge, transitions, SDOH handoffs |
| `mist-quality` | Safety, infection metrics, RCA discipline |
| `mist-pharmacy` | Med safety interfaces, shortages |
| `mist-workforce` | Staffing, float pools, burnout-aware ops |

### Mission, access & money

| ID | Focus |
| --- | --- |
| `mist-access` | Language, ADA, coverage barriers at the door |
| `mist-community` | CHNA, community benefit, neighborhood trust |
| `mist-revenue` | RCM hygiene + **charity care / FAP** (mission-first) |
| `mist-grants` | Restricted funds, foundations, 990 discipline |
| `mist-pophealth` | Registries / analytics with de-ID-first posture |
| `mist-supply` | PPE, par levels, GPO / materials |
| `mist-facilities` | Plant, generators, environment of care |

### Mesh core (always on)

| ID | Focus |
| --- | --- |
| `mist-prime` | Genome / continuity |
| `mist-scavenger` | Verify before claim |
| `mist-sentinel` | Irreversible-harm gates |
| `mist-tinker` | Unstick broken tools |
| `mist-bridge` | Handoffs across teams/tools |

Definitions: [`roster/hospital_wave.json`](../roster/hospital_wave.json)

---

## Deploy for a hospital workstation

```bash
git clone https://github.com/Mellowambience/mist-clone-forge.git
cd mist-clone-forge

# One-shot hospital system seed
python scripts/seed_hospital_system.py

# Command Center (all interfaces — PC + phone on Wi‑Fi)
set MIST_HOST=0.0.0.0
python -u scripts/mist_serve.py
```

Windows: `scripts/START_MIST.bat` then open http://127.0.0.1:8766/

### Profile

Hospital defaults live in [`config/hospital_system.json`](../config/hospital_system.json).

Copy or merge into the runtime home if you customize:

```text
~/.grok/mist-clones/config/hospital_system.json
```

---

## Example auto-routes

| Need | Typical route |
| --- | --- |
| Epic downtime while ED boards | `mist-ehr` / `mist-ed` (+ HIPAA watch if PHI-ish) |
| BAA for analytics vendor | `mist-hipaa` |
| Charity care denial appeal | `mist-revenue` |
| Order-set alert fatigue / sepsis CDS | `mist-informatics` |
| Float pool / traveler ethics | `mist-workforce` |
| CHNA partnership language | `mist-community` |

```bash
python scripts/forge.py auto "Epic downtime while ED is boarding"
python scripts/forge.py auto --dry-run "HIPAA BAA for population health vendor"
```

---

## Security & compliance posture

1. **Local-first** — runtime under the operator’s machine (`~/.grok/mist-clones/`).  
2. **No PHI in git** — never commit charts, exports, or patient identifiers.  
3. **Minimum necessary** — prefer de-identified examples in demos.  
4. **Level-4 gates** — publish, export, and destructive actions require human approval.  
5. **Provenance** — specialists must not invent clinical facts.  
6. **Network** — phone access is same-LAN only; open firewall deliberately.

See also [`SECURITY.md`](../SECURITY.md).

---

## Suggested pilot (90 days)

| Phase | Outcome |
| --- | --- |
| **Week 1–2** | Seed hospital edition; IS + compliance review of intents |
| **Week 3–6** | Pilot: downtime, BAA checklist, ED boarding playbooks |
| **Week 7–10** | Expand: RCM FAP language, workforce, community benefit |
| **Week 11–12** | Measure: time-to-right-specialist, handoff quality, zero PHI leaks |

---

## Support path

- Issues: GitHub Issues on this repo  
- Product narrative: this document  
- Operator skill pack: `skill/SKILL.md`  

---

*Built for the hospitals that still believe care is a public good.*
