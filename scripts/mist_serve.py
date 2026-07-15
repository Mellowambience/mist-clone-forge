#!/usr/bin/env python3
"""Persistent MIST mesh server entrypoint.

Runs swarm_board forever with logging. Prefer launching via mist_serve.vbs
so the process survives parent shells closing.
"""
from __future__ import annotations

import os
import sys
import time
import traceback
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
LOG = SCRIPTS / "mist_serve.log"
os.chdir(SCRIPTS)
sys.path.insert(0, str(SCRIPTS))


def log(msg: str) -> None:
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n"
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
    try:
        sys.stdout.write(line)
        sys.stdout.flush()
    except Exception:
        pass


def main() -> None:
    # 0.0.0.0 so phone on same Wi‑Fi can join (phone carrier)
    host = os.environ.get("MIST_HOST", "0.0.0.0")
    port = int(os.environ.get("MIST_PORT", "8766"))
    log(f"mist_serve boot host={host} port={port} py={sys.executable}")

    # Import after chdir
    import swarm_board

    while True:
        try:
            log("starting ThreadingHTTPServer…")
            # Inline serve so we control restarts
            from http.server import ThreadingHTTPServer
            import carrier
            import hive
            import threading

            hive.init_db()
            carrier.touch("mist_serve")
            try:
                hive.join_all_from_disk()
            except Exception as e:
                log(f"hive join warn: {e}")

            threading.Thread(target=swarm_board.watch_loop, daemon=True).start()
            httpd = ThreadingHTTPServer((host, port), swarm_board.Handler)
            log(f"MESH CARRIER LISTENING on {host}:{port}")
            log(f"  local  http://127.0.0.1:{port}/tv")
            try:
                for u in carrier.lan_urls(port):
                    log(f"  phone  {u['vision']}")
            except Exception:
                pass
            httpd.serve_forever()
        except OSError as e:
            log(f"bind/serve OSError: {e} — retry in 3s")
            time.sleep(3)
        except KeyboardInterrupt:
            log("keyboard interrupt — exit")
            break
        except Exception:
            log("crash:\n" + traceback.format_exc())
            time.sleep(3)


if __name__ == "__main__":
    main()
