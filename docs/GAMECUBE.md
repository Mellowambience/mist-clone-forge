# GameCube agent play (optional)

## Legal

Supply dumps from discs **you own**. This project never ships copyrighted games or Dolphin binaries.

## Setup

1. Install [Dolphin](https://dolphin-emu.org/download/) (or extract portable build to `~/.grok/mist-clones/gamecube/dolphin/Dolphin-x64/`).  
2. Place owned dumps in `~/.grok/mist-clones/gamecube/games/`.  
3. Run:

```bash
python gamecube/scripts/gc_play.py list
python gamecube/scripts/gc_play.py launch "title"
python gamecube/scripts/gc_play.py press A
```

Specialist: `mist-gamecube` (see `roster/emulator_wave.json`).
