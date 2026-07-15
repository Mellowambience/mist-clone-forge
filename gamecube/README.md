# MIST GameCube Hub (Dolphin) — enhanced

Agent-playable **GameCube / Wii** via official **Dolphin** (portable 2606).

## Legal (required)

- **You** supply game dumps from discs **you own**.
- This hub does **not** ship copyrighted ISOs/ROMs.
- Do not ask the agent to download pirated games.

Place files in:

```text
games/
  YourGame.iso   # or .gcm .ciso .wbfs .rvz
```

See `games/OWNED.md` and **`games/TOP10.md`** (curated best-of — metadata only).

Machine-readable list: `catalog.json` → `top_ten_best_gamecube`.

## Doctor (run first)

```powershell
python $env:USERPROFILE\.grok\mist-clones\gamecube\scripts\gc_play.py doctor
python $env:USERPROFILE\.grok\mist-clones\gamecube\scripts\gc_play.py doctor --drop-archive
python $env:USERPROFILE\.grok\mist-clones\gamecube\scripts\gc_play.py doctor --reseed
```

Seeds `dolphin/Dolphin-x64/User/Config/GCPadNew.ini` + Hotkeys from `controls.json`.

## Play commands

```powershell
$gc = "$env:USERPROFILE\.grok\mist-clones\gamecube\scripts\gc_play.py"

python $gc list
python $gc status
python $gc launch "YourGame"          # waits for window (ready)
python $gc ready
python $gc focus
python $gc press A
python $gc hold LEFT --ms 500
python $gc combo "A,A,START"
python $gc stick --x 0.5 --y 0.8 --ms 200
python $gc shot
python $gc press SAVESTATE            # F5
python $gc press LOADSTATE            # F1
```

## Emulator

```text
dolphin\Dolphin-x64\Dolphin.exe
```

`portable.txt` enabled · User config under `dolphin\Dolphin-x64\User\`.

## Controls (default → GC)

| GC | Key |
| --- | --- |
| A | X |
| B | Z |
| X | C |
| Y | S |
| Z | D |
| Start | Enter |
| L / R | Q / W |
| D-Pad | Arrows |
| Main stick | T F G H |
| C-stick | I J K L |
| Save state | F5 |
| Load state | F1 |

Remap in Dolphin **and** `controls.json`, then `doctor --reseed`.

## Agent specialist

`mist-gamecube` — play/emulation tasks; hive posts on launch / input / shot.

## Modern presentation (owned dumps)

Configs live under portable `User/`:

- `User/Config/GFX.ini` — higher IR, 16:9, AA, async shaders  
- `User/GameSettings/GZLE01.ini` — Wind Waker USA  
- `modernize/README.md` — legal scope + Blizzard craft bar for **original** work  

```powershell
python $gc modern-status
python $gc launch wind_waker_usa
```

We do **not** remake Nintendo games. We modernize **how your dumps run**, and build original IP separately.
