#!/usr/bin/env python3
"""GameCube play hub for MIST agents — Dolphin launch + input + vision hooks.

Legal: only plays dumps present in ../games/ that the user owns.
Enhancements: doctor, shot, wait-ready, SendInput, seed GCPad from controls.json.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOLPHIN_DIR = ROOT / "dolphin" / "Dolphin-x64"
DOLPHIN = DOLPHIN_DIR / "Dolphin.exe"
GAMES = ROOT / "games"
CATALOG = ROOT / "catalog.json"
CONTROLS = ROOT / "controls.json"
STATE = ROOT / "state.json"
SHOTS = ROOT / "screenshots"
SAVES = ROOT / "saves"
USER_CFG = DOLPHIN_DIR / "User" / "Config"
OWNED = GAMES / "OWNED.md"

# Virtual-key codes
VK: dict[str, int] = {
    "return": 0x0D,
    "enter": 0x0D,
    "escape": 0x1B,
    "space": 0x20,
    "up": 0x26,
    "down": 0x28,
    "left": 0x25,
    "right": 0x27,
    "shift": 0x10,
    "ctrl": 0x11,
    "alt": 0x12,
    "f1": 0x70,
    "f2": 0x71,
    "f3": 0x72,
    "f4": 0x73,
    "f5": 0x74,
    "f6": 0x75,
    "f7": 0x76,
    "f8": 0x77,
}
for i, ch in enumerate("abcdefghijklmnopqrstuvwxyz"):
    VK[ch] = 0x41 + i
for i in range(10):
    VK[str(i)] = 0x30 + i


def load_controls() -> dict:
    if CONTROLS.is_file():
        return json.loads(CONTROLS.read_text(encoding="utf-8")).get("map", {})
    return {}


def find_games() -> list[dict]:
    exts = {".iso", ".gcm", ".ciso", ".wbfs", ".rvz", ".gcz", ".wia", ".dol", ".elf"}
    games = []
    GAMES.mkdir(parents=True, exist_ok=True)
    for p in sorted(GAMES.rglob("*")):
        if p.is_file() and p.suffix.lower() in exts:
            games.append(
                {
                    "id": p.stem.lower().replace(" ", "-"),
                    "title": p.stem,
                    "path": str(p),
                    "size_mb": round(p.stat().st_size / (1024 * 1024), 1),
                }
            )
    cat: dict = {"version": 1, "library": games}
    if CATALOG.is_file():
        try:
            old = json.loads(CATALOG.read_text(encoding="utf-8"))
            old["library"] = games
            cat = old
        except Exception:
            pass
    CATALOG.write_text(json.dumps(cat, indent=2), encoding="utf-8")
    return games


def resolve_game(query: str) -> Path | None:
    q = query.lower().strip()
    for g in find_games():
        if q == g["id"] or q in g["title"].lower() or q in g["path"].lower():
            return Path(g["path"])
    p = Path(query)
    if p.is_file():
        return p
    return None


def save_state(**kwargs) -> None:
    st: dict = {}
    if STATE.is_file():
        try:
            st = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            st = {}
    st.update(kwargs)
    st["updated"] = time.time()
    STATE.write_text(json.dumps(st, indent=2), encoding="utf-8")


def hive_post(msg: str, kind: str = "play", meta: dict | None = None) -> None:
    try:
        sys.path.insert(0, str(Path.home() / ".grok" / "mist-clones" / "scripts"))
        import hive  # type: ignore

        hive.post("mist-gamecube", msg, kind=kind, meta=meta or {})
    except Exception:
        pass


# --- Dolphin User config seed (matches controls.json) ---

# Map our logical keys → Dolphin keyboard token names
_DOLPHIN_KEY = {
    "x": "X",
    "z": "Z",
    "c": "C",
    "s": "S",
    "d": "D",
    "q": "Q",
    "w": "W",
    "t": "T",
    "f": "F",
    "g": "G",
    "h": "H",
    "return": "RETURN",
    "enter": "RETURN",
    "up": "UP",
    "down": "DOWN",
    "left": "LEFT",
    "right": "RIGHT",
}


def seed_gcpad_config(force: bool = False) -> dict:
    """Write User/Config/GCPadNew.ini from controls.json so pad map is guaranteed."""
    USER_CFG.mkdir(parents=True, exist_ok=True)
    target = USER_CFG / "GCPadNew.ini"
    if target.is_file() and not force:
        return {"ok": True, "path": str(target), "skipped": True}

    cmap = load_controls()

    def k(btn: str, default: str) -> str:
        raw = (cmap.get(btn) or default).lower()
        return _DOLPHIN_KEY.get(raw, raw.upper())

    # Dolphin 5 / recent: DInput keyboard device name is common on Windows
    body = f"""# Seeded by gc_play.py from controls.json — do not hand-edit unless you also update controls.json
[GCPad1]
Device = DInput/0/Keyboard Mouse
Buttons/A = `{k("A", "x")}`
Buttons/B = `{k("B", "z")}`
Buttons/X = `{k("X", "c")}`
Buttons/Y = `{k("Y", "s")}`
Buttons/Z = `{k("Z", "d")}`
Buttons/Start = `{k("START", "return")}`
Main Stick/Up = `{k("STICK_UP", "t")}`
Main Stick/Down = `{k("STICK_DOWN", "g")}`
Main Stick/Left = `{k("STICK_LEFT", "f")}`
Main Stick/Right = `{k("STICK_RIGHT", "h")}`
Main Stick/Modifier = `Shift`
Main Stick/Calibration = 100.00 100.00 100.00 100.00 100.00 100.00 100.00 100.00
C-Stick/Up = `I`
C-Stick/Down = `K`
C-Stick/Left = `J`
C-Stick/Right = `L`
C-Stick/Modifier = `Ctrl`
C-Stick/Calibration = 100.00 100.00 100.00 100.00 100.00 100.00 100.00 100.00
Triggers/L = `{k("L", "q")}`
Triggers/R = `{k("R", "w")}`
D-Pad/Up = `{k("UP", "up")}`
D-Pad/Down = `{k("DOWN", "down")}`
D-Pad/Left = `{k("LEFT", "left")}`
D-Pad/Right = `{k("RIGHT", "right")}`
"""
    target.write_text(body, encoding="utf-8")

    # Hotkeys: F1 load / F5 save slot 1 (agent savestate)
    hk = USER_CFG / "Hotkeys.ini"
    if force or not hk.is_file():
        hk.write_text(
            """# Seeded by gc_play.py
[Hotkeys]
Device = DInput/0/Keyboard Mouse
General/Open = `Ctrl`+`O`
General/Toggle Pause = `F10`
Save State/Save to selected slot = `F5`
Load State/Load from selected slot = `F1`
Load State/Load State Slot 1 = `F1`
Save State/Save State Slot 1 = `F5`
""",
            encoding="utf-8",
        )

    # Minimal Dolphin.ini: confirm on stop off, keep window
    dini = USER_CFG / "Dolphin.ini"
    if force or not dini.is_file():
        dini.write_text(
            """[General]
ShowLag = False
[Interface]
ConfirmStop = False
PauseOnFocusLost = False
[Core]
WiimoteContinuousScanning = False
""",
            encoding="utf-8",
        )

    return {"ok": True, "path": str(target), "hotkeys": str(hk), "skipped": False}


def ensure_owned_md() -> None:
    GAMES.mkdir(parents=True, exist_ok=True)
    if not OWNED.is_file():
        OWNED.write_text(
            """# Owned dumps only

Place **your own** GameCube/Wii dumps here (`.iso` `.gcm` `.rvz` `.wbfs` …).

- Dump discs you physically own.
- Do **not** ask the agent to download pirated ROMs.
- After adding files: `python scripts/gc_play.py list` then `launch <name>`.
""",
            encoding="utf-8",
        )


# --- Window / input ---

def _enum_dolphin_hwnds() -> list:
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        found: list = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        def enum_cb(hwnd, _):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
                if "dolphin" in title.lower():
                    found.append((hwnd, title))
            return True

        user32.EnumWindows(enum_cb, 0)
        return found
    except Exception:
        return []


def focus_dolphin() -> bool:
    try:
        import ctypes

        user32 = ctypes.windll.user32
        found = _enum_dolphin_hwnds()
        if not found:
            return False
        hwnd = found[0][0]
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False


def wait_ready(timeout_s: float = 20.0) -> dict:
    """Poll until Dolphin window exists and optional PID still alive."""
    st = {}
    if STATE.is_file():
        try:
            st = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    pid = st.get("pid")
    deadline = time.time() + timeout_s
    last_titles: list[str] = []
    while time.time() < deadline:
        wins = _enum_dolphin_hwnds()
        last_titles = [t for _, t in wins]
        alive = True
        if pid:
            try:
                import ctypes

                # OpenProcess + wait 0
                k32 = ctypes.windll.kernel32
                handle = k32.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
                if handle:
                    exit_code = ctypes.c_ulong()
                    k32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
                    k32.CloseHandle(handle)
                    alive = exit_code.value == 259  # STILL_ACTIVE
                else:
                    alive = False
            except Exception:
                pass
        if wins and alive:
            focus_dolphin()
            save_state(ready=True, window_title=last_titles[0] if last_titles else None)
            return {
                "ok": True,
                "ready": True,
                "titles": last_titles,
                "pid": pid,
                "focused": True,
            }
        time.sleep(0.4)
    save_state(ready=False)
    return {
        "ok": False,
        "ready": False,
        "titles": last_titles,
        "pid": pid,
        "error": "timeout waiting for Dolphin window",
    }


def send_key(vk: int, down: bool) -> None:
    """Prefer SendInput; fall back to keybd_event."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_EXTENDEDKEY = 0x0001

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    class INPUT(ctypes.Structure):
        class _I(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT)]

        _anonymous_ = ("i",)
        _fields_ = [("type", wintypes.DWORD), ("i", _I)]

    flags = 0 if down else KEYEVENTF_KEYUP
    if vk in (0x25, 0x26, 0x27, 0x28):
        flags |= KEYEVENTF_EXTENDEDKEY

    try:
        inp = INPUT(type=INPUT_KEYBOARD)
        inp.ki = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=flags, time=0, dwExtraInfo=None)
        n = user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        if n == 1:
            return
    except Exception:
        pass
    # fallback
    user32.keybd_event(vk, 0, flags, 0)


def press(button: str, *, ms: int = 80) -> dict:
    cmap = load_controls()
    name = button.strip().upper().replace("-", "_")
    # savestate helpers
    if name in ("SAVESTATE", "SAVE"):
        return press_key_name("f5", ms=ms, label="SAVESTATE")
    if name in ("LOADSTATE", "LOAD"):
        return press_key_name("f1", ms=ms, label="LOADSTATE")
    key = cmap.get(name) or cmap.get(button.strip()) or button.strip().lower()
    vk = VK.get(key.lower()) if isinstance(key, str) else None
    if vk is None:
        return {"ok": False, "error": f"unknown button/key: {button} → {key}"}
    focus_dolphin()
    time.sleep(0.05)
    send_key(vk, True)
    time.sleep(max(ms, 20) / 1000.0)
    send_key(vk, False)
    hive_post(f"input {name} ({ms}ms)", kind="play")
    return {"ok": True, "button": name, "key": key, "ms": ms}


def press_key_name(key: str, *, ms: int = 80, label: str | None = None) -> dict:
    vk = VK.get(key.lower())
    if vk is None:
        return {"ok": False, "error": f"unknown key {key}"}
    focus_dolphin()
    time.sleep(0.05)
    send_key(vk, True)
    time.sleep(max(ms, 20) / 1000.0)
    send_key(vk, False)
    lab = label or key
    hive_post(f"input {lab}", kind="play")
    return {"ok": True, "button": lab, "key": key, "ms": ms}


def hold(button: str, ms: int = 500) -> dict:
    return press(button, ms=ms)


def combo(seq: str, gap_ms: int = 120) -> dict:
    parts = [p.strip() for p in seq.replace("+", ",").split(",") if p.strip()]
    results = []
    for p in parts:
        results.append(press(p))
        time.sleep(gap_ms / 1000.0)
    return {"ok": all(r.get("ok") for r in results), "steps": results}


def stick(x: float, y: float, ms: int = 200) -> dict:
    """Approximate main stick via opposing keys (keyboard limitation).

    x,y in [-1,1]; +y = up, +x = right (GC stick space).
    """
    x = max(-1.0, min(1.0, float(x)))
    y = max(-1.0, min(1.0, float(y)))
    cmap = load_controls()
    keys_down: list[int] = []

    def add_btn(btn: str, amount: float) -> None:
        if abs(amount) < 0.25:
            return
        key = (cmap.get(btn) or "").lower()
        vk = VK.get(key)
        if vk:
            keys_down.append(vk)

    if y > 0:
        add_btn("STICK_UP", y)
    if y < 0:
        add_btn("STICK_DOWN", -y)
    if x < 0:
        add_btn("STICK_LEFT", -x)
    if x > 0:
        add_btn("STICK_RIGHT", x)

    if not keys_down:
        return {"ok": True, "x": x, "y": y, "ms": 0, "note": "deadzone"}

    focus_dolphin()
    time.sleep(0.05)
    for vk in keys_down:
        send_key(vk, True)
    time.sleep(max(ms, 20) / 1000.0)
    for vk in keys_down:
        send_key(vk, False)
    hive_post(f"stick x={x:.2f} y={y:.2f} {ms}ms", kind="play")
    return {"ok": True, "x": x, "y": y, "ms": ms, "keys": len(keys_down)}


def launch(game_query: str, *, batch: bool = True, wait: float = 15.0) -> dict:
    seed_gcpad_config(force=False)
    ensure_owned_md()
    if not DOLPHIN.is_file():
        return {"ok": False, "error": f"Dolphin not found at {DOLPHIN}"}
    game = resolve_game(game_query)
    if not game:
        return {
            "ok": False,
            "error": "game not found — put owned dumps in games/",
            "library": find_games(),
        }
    args = [str(DOLPHIN), "-e", str(game)]
    if batch:
        args.insert(1, "-b")
    proc = subprocess.Popen(args, cwd=str(DOLPHIN_DIR))
    save_state(game=str(game), pid=proc.pid, title=game.stem, ready=False)
    hive_post(
        f"Launching GC title: {game.stem}",
        kind="play",
        meta={"path": str(game), "pid": proc.pid},
    )
    ready = wait_ready(timeout_s=wait) if wait > 0 else {"ok": None, "ready": False}
    return {
        "ok": True,
        "pid": proc.pid,
        "game": str(game),
        "title": game.stem,
        "ready": ready,
    }


def screenshot(name: str | None = None) -> dict:
    """Capture Dolphin window (or primary screen fallback) to screenshots/."""
    SHOTS.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out = SHOTS / (name or f"shot_{ts}.png")
    focus_dolphin()
    time.sleep(0.1)

    # Try BitBlt of foreground window via ctypes + PIL if available; else PowerShell
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        hwnd = user32.GetForegroundWindow()
        wins = _enum_dolphin_hwnds()
        if wins:
            hwnd = wins[0][0]
        rect = wintypes.RECT()
        user32.GetClientRect(hwnd, ctypes.byref(rect))
        w, h = rect.right - rect.left, rect.bottom - rect.top
        if w < 16 or h < 16:
            raise RuntimeError("client too small")

        hwndDC = user32.GetDC(hwnd)
        mfcDC = gdi32.CreateCompatibleDC(hwndDC)
        saveBit = gdi32.CreateCompatibleBitmap(hwndDC, w, h)
        gdi32.SelectObject(mfcDC, saveBit)
        # PrintWindow often works better than BitBlt for GPU windows
        PW_RENDERFULLCONTENT = 2
        user32.PrintWindow(hwnd, mfcDC, PW_RENDERFULLCONTENT)

        # Save via PIL if present
        try:
            from PIL import Image  # type: ignore

            bmpinfo = {
                "bmType": 0,
                "bmWidth": w,
                "bmHeight": h,
                "bmWidthBytes": ((w * 32 + 31) // 32) * 4,
                "bmPlanes": 1,
                "bmBitsPixel": 32,
                "bmBits": None,
            }
            # Use GetDIBits
            class BITMAPINFOHEADER(ctypes.Structure):
                _fields_ = [
                    ("biSize", wintypes.DWORD),
                    ("biWidth", ctypes.c_long),
                    ("biHeight", ctypes.c_long),
                    ("biPlanes", wintypes.WORD),
                    ("biBitCount", wintypes.WORD),
                    ("biCompression", wintypes.DWORD),
                    ("biSizeImage", wintypes.DWORD),
                    ("biXPelsPerMeter", ctypes.c_long),
                    ("biYPelsPerMeter", ctypes.c_long),
                    ("biClrUsed", wintypes.DWORD),
                    ("biClrImportant", wintypes.DWORD),
                ]

            class BITMAPINFO(ctypes.Structure):
                _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]

            bmi = BITMAPINFO()
            bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmi.bmiHeader.biWidth = w
            bmi.bmiHeader.biHeight = -h  # top-down
            bmi.bmiHeader.biPlanes = 1
            bmi.bmiHeader.biBitCount = 32
            bmi.bmiHeader.biCompression = 0
            buf_len = w * h * 4
            buf = ctypes.create_string_buffer(buf_len)
            gdi32.GetDIBits(mfcDC, saveBit, 0, h, buf, ctypes.byref(bmi), 0)
            img = Image.frombuffer("RGB", (w, h), buf, "raw", "BGRX", 0, 1)
            img.save(out)
            ok = True
        except Exception:
            ok = False

        gdi32.DeleteObject(saveBit)
        gdi32.DeleteDC(mfcDC)
        user32.ReleaseDC(hwnd, hwndDC)
        if ok and out.is_file():
            save_state(last_shot=str(out))
            hive_post(f"screenshot {out.name}", kind="play", meta={"path": str(out)})
            return {"ok": True, "path": str(out), "method": "PrintWindow+PIL"}
    except Exception as e:
        last_err = str(e)
    else:
        last_err = "bitblt failed"

    # PowerShell fallback — full primary screen
    try:
        ps = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
$bmp.Save('{str(out).replace("'", "''")}')
$g.Dispose(); $bmp.Dispose()
"""
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if out.is_file() and out.stat().st_size > 0:
            save_state(last_shot=str(out))
            hive_post(f"screenshot {out.name} (screen)", kind="play")
            return {
                "ok": True,
                "path": str(out),
                "method": "powershell-screen",
                "note": "full primary screen — focus Dolphin first",
                "ps_code": r.returncode,
            }
        return {"ok": False, "error": last_err, "ps": r.stderr}
    except Exception as e2:
        return {"ok": False, "error": f"{last_err}; fallback {e2}"}


def modern_status() -> dict:
    """Report modernization layer files + library enhancement readiness."""
    gfx = USER_CFG / "GFX.ini"
    dini = USER_CFG / "Dolphin.ini"
    ww = DOLPHIN_DIR / "User" / "GameSettings" / "GZLE01.ini"
    tex = DOLPHIN_DIR / "User" / "Load" / "Textures"
    games = find_games()
    return {
        "ok": gfx.is_file() and dini.is_file(),
        "gfx_ini": str(gfx),
        "gfx_exists": gfx.is_file(),
        "dolphin_ini": str(dini),
        "wind_waker_profile": str(ww),
        "wind_waker_profile_exists": ww.is_file(),
        "hires_texture_dir": str(tex),
        "library": games,
        "enhanced_titles": [
            {
                "title": "The Legend of Zelda: The Wind Waker (USA)",
                "status": "modern_presentation",
                "in_library": any("wind" in g["id"] for g in games),
                "game_ini": "GZLE01",
            }
        ],
        "cannot_remaster": "Nintendo IP remakes out of scope — presentation + original spiritual successors only",
        "docs": str(ROOT / "modernize" / "README.md"),
    }


def ensure_modern_layer() -> dict:
    """Idempotent: ensure modernize docs path exists; configs written by seed files."""
    (ROOT / "modernize").mkdir(parents=True, exist_ok=True)
    (DOLPHIN_DIR / "User" / "Load" / "Textures").mkdir(parents=True, exist_ok=True)
    (DOLPHIN_DIR / "User" / "GameSettings").mkdir(parents=True, exist_ok=True)
    return modern_status()


def doctor(*, drop_archive: bool = False) -> dict:
    """Health check for the hub."""
    ensure_owned_md()
    seed = seed_gcpad_config(force=False)
    games = find_games()
    checks = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    add("dolphin_exe", DOLPHIN.is_file(), str(DOLPHIN))
    add("portable_txt", (DOLPHIN_DIR / "portable.txt").is_file())
    add("games_dir", GAMES.is_dir(), str(GAMES))
    add("owned_md", OWNED.is_file())
    add("gcpad_ini", (USER_CFG / "GCPadNew.ini").is_file(), str(USER_CFG / "GCPadNew.ini"))
    add("controls_json", CONTROLS.is_file())
    add("library_nonempty", len(games) > 0, f"{len(games)} games")
    add("scripts_gc_play", Path(__file__).is_file())
    add("modern_gfx", (USER_CFG / "GFX.ini").is_file(), str(USER_CFG / "GFX.ini"))
    add(
        "wind_waker_ini",
        (DOLPHIN_DIR / "User" / "GameSettings" / "GZLE01.ini").is_file(),
    )

    archive = ROOT / "dolphin-2606-x64.7z"
    if archive.is_file():
        if drop_archive and DOLPHIN.is_file():
            try:
                archive.unlink()
                add("archive_7z", True, "deleted after verify")
            except Exception as e:
                add("archive_7z", False, f"delete failed: {e}")
        else:
            add(
                "archive_7z",
                True,
                f"present ({archive.stat().st_size // (1024*1024)} MB) — optional drop with --drop-archive",
            )
    else:
        add("archive_7z", True, "absent (ok)")

    # focus probe (may fail if Dolphin not running — warn only)
    focused = focus_dolphin()
    add("focus_probe", True, "focused" if focused else "Dolphin not running (ok if idle)")

    ok = all(
        c["ok"]
        for c in checks
        if c["name"] not in ("library_nonempty", "focus_probe")
    )
    # library empty is warning not hard fail
    result = {
        "ok": ok,
        "checks": checks,
        "seed": seed,
        "library_count": len(games),
        "next": (
            "Add an owned dump to games/ then: python scripts/gc_play.py launch <name>"
            if not games
            else "python scripts/gc_play.py launch <id> then shot / press A"
        ),
    }
    save_state(doctor=result)
    return result


def status() -> dict:
    st = {}
    if STATE.is_file():
        st = json.loads(STATE.read_text(encoding="utf-8"))
    return {
        "dolphin": str(DOLPHIN),
        "dolphin_exists": DOLPHIN.is_file(),
        "library": find_games(),
        "state": st,
        "gcpad": str(USER_CFG / "GCPadNew.ini"),
        "windows": [t for _, t in _enum_dolphin_hwnds()],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="MIST GameCube / Dolphin agent player")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List games in library")
    sub.add_parser("top10", help="Print curated top 10 GC titles (metadata only)")
    sub.add_parser("status", help="Hub status")
    doc = sub.add_parser("doctor", help="Health check + seed config")
    doc.add_argument(
        "--drop-archive",
        action="store_true",
        help="Delete dolphin-2606-x64.7z after verifying exe exists",
    )
    doc.add_argument("--reseed", action="store_true", help="Force rewrite GCPad/Hotkeys ini")

    la = sub.add_parser("launch", help="Launch a game by name/path")
    la.add_argument("game")
    la.add_argument("--ui", action="store_true", help="Show Dolphin UI (no -b)")
    la.add_argument("--wait", type=float, default=15.0, help="Seconds to wait for window")

    sub.add_parser("ready", help="Wait until Dolphin window is ready")
    rd = sub.add_parser("wait-ready", help="Alias for ready")
    rd.add_argument("--timeout", type=float, default=20.0)

    pr = sub.add_parser("press", help="Tap a button (or SAVESTATE/LOADSTATE)")
    pr.add_argument("button")
    pr.add_argument("--ms", type=int, default=80)

    ho = sub.add_parser("hold", help="Hold a button")
    ho.add_argument("button")
    ho.add_argument("--ms", type=int, default=500)

    co = sub.add_parser("combo", help="Sequence e.g. A,A,START")
    co.add_argument("seq")
    co.add_argument("--gap", type=int, default=120)

    stc = sub.add_parser("stick", help="Main stick vector -1..1")
    stc.add_argument("--x", type=float, default=0.0)
    stc.add_argument("--y", type=float, default=0.0)
    stc.add_argument("--ms", type=int, default=200)

    sh = sub.add_parser("shot", help="Screenshot Dolphin (or screen fallback)")
    sh.add_argument("--name", default=None, help="Output filename")

    sub.add_parser("focus", help="Focus Dolphin window")
    sub.add_parser("seed", help="Force seed GCPad from controls.json")
    sub.add_parser("modern-status", help="Modernization layer status (Gfx/WW profile)")
    sub.add_parser("ensure-modern", help="Ensure modern dirs/profile status")

    args = ap.parse_args()

    if args.cmd == "list":
        games = find_games()
        if not games:
            print("Library empty. Copy owned .iso/.gcm/.rvz into:")
            print(f"  {GAMES}")
            print(f"See {OWNED}")
        for g in games:
            print(f"{g['id']:30} {g['size_mb']:>8} MB  {g['title']}")
        return
    if args.cmd == "top10":
        if CATALOG.is_file():
            cat = json.loads(CATALOG.read_text(encoding="utf-8"))
            for row in cat.get("top_ten_best_gamecube", []):
                print(f"{row.get('rank', '?'):>2}. {row.get('title')}  [{row.get('id_hint')}]")
                print(f"    {row.get('why', '')}")
            print("---")
            print("Legal: dump discs you own into games/. No ROMs ship with this hub.")
        else:
            print("catalog.json missing")
        return
    if args.cmd == "status":
        print(json.dumps(status(), indent=2))
        return
    if args.cmd == "doctor":
        if args.reseed:
            print(json.dumps(seed_gcpad_config(force=True), indent=2))
        print(json.dumps(doctor(drop_archive=args.drop_archive), indent=2))
        return
    if args.cmd == "seed":
        print(json.dumps(seed_gcpad_config(force=True), indent=2))
        return
    if args.cmd == "launch":
        print(json.dumps(launch(args.game, batch=not args.ui, wait=args.wait), indent=2))
        return
    if args.cmd in ("ready", "wait-ready"):
        t = getattr(args, "timeout", 20.0)
        print(json.dumps(wait_ready(timeout_s=t), indent=2))
        return
    if args.cmd == "press":
        print(json.dumps(press(args.button, ms=args.ms), indent=2))
        return
    if args.cmd == "hold":
        print(json.dumps(hold(args.button, ms=args.ms), indent=2))
        return
    if args.cmd == "combo":
        print(json.dumps(combo(args.seq, gap_ms=args.gap), indent=2))
        return
    if args.cmd == "stick":
        print(json.dumps(stick(args.x, args.y, ms=args.ms), indent=2))
        return
    if args.cmd == "shot":
        print(json.dumps(screenshot(args.name), indent=2))
        return
    if args.cmd == "focus":
        print(json.dumps({"ok": focus_dolphin(), "windows": [t for _, t in _enum_dolphin_hwnds()]}))
        return
    if args.cmd == "modern-status":
        print(json.dumps(modern_status(), indent=2))
        return
    if args.cmd == "ensure-modern":
        print(json.dumps(ensure_modern_layer(), indent=2))
        return


if __name__ == "__main__":
    main()
