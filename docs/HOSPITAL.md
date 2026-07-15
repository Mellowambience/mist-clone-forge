# Hospital-first specialists

Urban nonprofit hospital systems are prioritized by the auto-router.

## Priority sectors

| ID | Domain |
| --- | --- |
| mist-ehr | Electronic health records |
| mist-informatics | Order sets, CDS, alert fatigue |
| mist-hipaa | Privacy, BAA, breach discipline |
| mist-cyber-health | Healthcare cybersecurity |
| mist-ed | Emergency department flow |
| mist-behavioral | Behavioral health boarding (ops) |
| mist-care-coord | Transitions, SDOH handoffs |
| mist-community | Community benefit / CHNA |
| mist-access | Language, ADA, equity at the door |
| mist-quality | Safety, infection, RCA |
| mist-workforce | Staffing, burnout |
| mist-revenue | RCM + charity care (mission-first) |
| mist-grants | Nonprofit grants / 990 |
| mist-pharmacy | Med safety / shortages |
| mist-supply | Materials / PPE / GPO |
| mist-pophealth | Population analytics (de-ID first) |
| mist-facilities | Plant / EOC / utilities |

Definitions: `roster/hospital_wave.json`  
Seed: `python scripts/seed_hospital.py`

## Safety posture

- Operational and systems guidance only.  
- No invented patient data, labs, or chart content.  
- PHI-adjacent tasks may auto-notify `mist-hipaa`.
