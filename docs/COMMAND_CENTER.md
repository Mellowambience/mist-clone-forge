# Command Center

## Surfaces

| Path | Description |
| --- | --- |
| `/` | Command Center dashboard |
| `/tv` | Agentic Vision (live cognition) |
| `/ops` | Multi-tab classic ops UI |
| `/api/carrier` | Dual carrier status (mesh + phone) |
| `/api/board` | Full mesh snapshot |
| `/api/auto` | Auto-route + dispatch |
| `/api/curate` | Conversation → options |

## Start

```bash
set MIST_HOST=0.0.0.0
python -u scripts/mist_serve.py
```

Windows: `scripts/START_MIST.bat`

## Phone carrier

1. PC and phone on the same Wi‑Fi.  
2. Open `http://<PC-LAN-IP>:8766/` on the phone.  
3. If connection refused from phone only, allow firewall: `ALLOW_PHONE_FIREWALL.bat` (Admin).  
4. Optional label in `~/.grok/mist-clones/carrier/phone.json`.
