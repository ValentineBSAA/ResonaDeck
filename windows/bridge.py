"""Windows JSON-lines adapter for the existing Decky/Plex backend.

Only main.Plugin's public RPC methods are reachable. stdout is reserved for JSON;
logging and tracebacks go to stderr. Plex credentials remain in the Python process.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sys
import types
from pathlib import Path

if not getattr(sys, "frozen", False):
    ROOT = Path(__file__).resolve().parent.parent
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

DATA = Path(os.environ.get("RESONADECK_WINDOWS_DATA_DIR") or
            (Path.home() / "AppData" / "Local" / "ResonaDeck"))
DATA.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, stream=sys.stderr)

# Reuse the production backend without importing or modifying Steam Deck itself.
decky = types.ModuleType("decky")
decky.DECKY_PLUGIN_RUNTIME_DIR = str(DATA / "backend" / "runtime")
decky.DECKY_PLUGIN_SETTINGS_DIR = str(DATA / "backend" / "settings")
decky.DECKY_PLUGIN_LOG_DIR = str(DATA / "backend" / "logs")
decky.DECKY_PLUGIN_VERSION = "1.2.1"
decky.logger = logging.getLogger("resonadeck.windows")
sys.modules["decky"] = decky

import resonadeck_backend as _backend  # noqa: E402
_backend.PLATFORM = "Windows"
_backend.DEVICE = "Windows PC"
from main import Plugin  # noqa: E402

LOCK = asyncio.Lock()
SAFE_NAME = re.compile(r"^[a-z][a-z0-9_]{1,65}$")
PUBLIC_METHODS = {
    name for name in dir(Plugin)
    if SAFE_NAME.fullmatch(name)
    and callable(getattr(Plugin, name, None))
}

async def send(message):
    # All writes are JSON-encoded and serialized so concurrent responses cannot mix.
    async with LOCK:
        sys.stdout.write(json.dumps(message, ensure_ascii=False, default=str) + "\n")
        sys.stdout.flush()

async def invoke(plugin, packet):
    request_id = packet.get("id")
    try:
        method = packet.get("method")
        args = packet.get("args")
        if not isinstance(method, str) or method not in PUBLIC_METHODS:
            raise ValueError("Unsupported backend method")
        if not isinstance(args, list) or len(args) > 20:
            raise ValueError("Invalid backend arguments")
        response = await getattr(plugin, method)(*args)
        await send({"id": request_id, "ok": True, "result": response})
    except Exception as error:
        impl = getattr(plugin, "_impl", None)
        detail = str(error)
        if impl and callable(getattr(impl, "_sanitize", None)):
            detail = impl._sanitize(detail)
        else:
            detail = re.sub(r"([?&]X-Plex-Token=)[^&\s]+", r"\1<redacted>", detail, flags=re.I)
        await send({"id": request_id, "ok": False, "error": detail[:500]})

async def main():
    plugin = Plugin()
    try:
        await plugin._main()
        await send({"event": "ready"})
        tasks = set()
        while True:
            line = await asyncio.to_thread(sys.stdin.readline)
            if not line:
                break
            if len(line) > 2 * 1024 * 1024:
                continue
            try:
                packet = json.loads(line)
            except (ValueError, TypeError):
                continue
            if not isinstance(packet, dict):
                continue
            if packet.get("event") == "shutdown":
                break
            if not isinstance(packet.get("id"), int):
                continue
            task = asyncio.create_task(invoke(plugin, packet))
            tasks.add(task)
            task.add_done_callback(tasks.discard)
        if tasks:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
    finally:
        await plugin._unload()

if __name__ == "__main__":
    asyncio.run(main())
