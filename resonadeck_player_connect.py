"""Experimental, LAN-only Plex Companion device discovery and controls.
ResonaDeck 1.5.8 TEST. Never send secrets or LAN addresses to the frontend.
No advertised-player receiver is implemented by this module.
"""
import asyncio
import ipaddress
import socket
import time
from urllib.parse import urlsplit

import aiohttp

_TTL = 18.0
_ACTIONS = {
    "play": "play", "pause": "pause", "toggle": "playPause",
    "next": "skipNext", "previous": "skipPrevious", "stop": "stop",
}
_TIMEOUT = aiohttp.ClientTimeout(total=2.8, connect=1.3, sock_read=1.8)


def _safe_connection(uri):
    """Allow only numeric private-network IPv4 addresses, never a proxy or WAN URL."""
    try:
        parsed = urlsplit(str(uri))
        ip = ipaddress.ip_address(parsed.hostname or "")
        # Strict RFC1918 host check: ipaddress.is_private also includes special
        # non-routable ranges that must never be usable as command targets.
        allowed = (ipaddress.ip_network("10.0.0.0/8"),
                   ipaddress.ip_network("172.16.0.0/12"),
                   ipaddress.ip_network("192.168.0.0/16"))
        if parsed.scheme != "http" or ip.version != 4 or not any(ip in n for n in allowed):
            return None
        if ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified:
            return None
        if str(ip) in {"192.0.0.8"}:
            return None
        port = parsed.port
        if not port or port < 1 or port > 65535 or parsed.username or parsed.password:
            return None
        return f"http://{ip}:{port}"
    except (ValueError, AttributeError):
        return None


def _discover_gdm_players():
    """Bounded broadcast lookup. The discovery response itself must declare a player."""
    found = []
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(0.20)
        for host in ("255.255.255.255", "239.0.0.250"):
            try:
                sock.sendto(b"M-SEARCH * HTTP/1.0\r\n\r\n", (host, 32414))
            except OSError:
                pass
        end = time.monotonic() + 0.9
        while time.monotonic() < end:
            try:
                blob, peer = sock.recvfrom(16000)
            except socket.timeout:
                continue
            except OSError:
                break
            fields = {}
            for row in blob.decode("utf-8", "replace").splitlines()[1:]:
                if ":" in row:
                    k, value = row.split(":", 1)
                    fields[k.strip().lower()] = value.strip()
            provides = fields.get("provides", "")
            if "player" not in provides.lower():
                continue
            try:
                port = int(fields.get("port") or "32500")
            except ValueError:
                continue
            base = _safe_connection(f"http://{peer[0]}:{port}")
            if base:
                found.append({
                    "id": fields.get("resource-identifier") or f"lan:{peer[0]}:{port}",
                    "name": fields.get("name") or fields.get("host") or "Plex Player",
                    "product": fields.get("product") or "Plex Companion",
                    "source": "LAN", "url": base,
                })
    finally:
        sock.close()
    return found


def _device_row(raw):
    device_id = str(raw.get("clientIdentifier") or raw.get("machineIdentifier") or "").strip()
    name = str(raw.get("name") or raw.get("product") or "Plex Player")[:96]
    product = str(raw.get("product") or "Plex")[:60]
    provides = str(raw.get("provides") or "").lower()
    if not device_id or "player" not in provides:
        return []
    out = []
    for entry in raw.get("connections") or []:
        if not isinstance(entry, dict) or not entry.get("local"):
            continue
        url = _safe_connection(entry.get("uri", ""))
        if url:
            out.append({"id": device_id, "name": name, "product": product,
                        "source": "Plex", "url": url})
    return out


def install(cls):
    if getattr(cls, "_rd158_player_connect_installed", False):
        return

    async def _get_player_connect_devices(self, force=False):
        if getattr(self, "_media_provider", "plex") != "plex":
            return {"success": False, "devices": [], "message": "Player Connect currently supports Plex only."}
        now = time.monotonic()
        cached = getattr(self, "_rd158_devices", {})
        if not force and now - getattr(self, "_rd158_scanned", 0) < _TTL:
            return {"success": True, "devices": _public(cached), "cached": True}
        token = str(getattr(self, "_active_user_token", "") or getattr(self, "_account_token", "") or "")
        rows = []
        if token:
            try:
                payload = await asyncio.wait_for(self._json(
                    "GET", "https://clients.plex.tv/api/v2/resources",
                    token=token, params={"includeHttps": "1", "includeRelay": "0"}), timeout=3.5)
                resources = payload if isinstance(payload, list) else payload.get("resources", []) if isinstance(payload, dict) else []
                for item in resources:
                    if isinstance(item, dict):
                        rows.extend(_device_row(item))
            except Exception:
                pass  # LAN discovery must still work when Plex cloud is offline.
        try:
            rows.extend(await asyncio.wait_for(asyncio.to_thread(_discover_gdm_players), timeout=1.5))
        except Exception:
            pass
        devices = {}
        local_id = str(getattr(self, "_client_id", ""))
        for row in rows:
            if not row["id"] or row["id"] == local_id:
                continue
            key = row["id"]
            if key not in devices or (row["source"] == "LAN" and devices[key]["source"] != "LAN"):
                devices[key] = row
        self._rd158_devices = devices
        self._rd158_scanned = time.monotonic()
        return {"success": True, "devices": _public(devices), "cached": False,
                "message": "Open Plexamp and enable Remote Control if your phone is missing." if not devices else ""}

    async def _player_connect_command(self, player_id, action, rating_key=""):
        if getattr(self, "_media_provider", "plex") != "plex":
            return {"success": False, "message": "Switch to Plex to use Player Connect."}
        action = str(action)
        if action not in {*_ACTIONS, "probe", "sendTrack"}:
            return {"success": False, "message": "Unsupported remote command."}
        cached = getattr(self, "_rd158_devices", {})
        target = cached.get(str(player_id))
        if not target or not _safe_connection(target.get("url")):
            return {"success": False, "message": "Refresh devices before sending a command."}
        if not getattr(self, "_session", None):
            return {"success": False, "message": "ResonaDeck network service is not ready."}
        command_id = getattr(self, "_rd158_command_id", 0) + 1
        self._rd158_command_id = command_id
        path = "/resources" if action == "probe" else "/player/playback/" + _ACTIONS.get(action, "playMedia")
        params = {} if action == "probe" else {"commandID": command_id}
        if action == "sendTrack":
            key = str(rating_key or "").strip()
            if not key.isdigit():
                return {"success": False, "message": "Choose a Plex music track before sending playback."}
            server = getattr(self, "_server", None)
            server_uri = urlsplit(str(getattr(server, "base_url", "") or ""))
            machine = str(getattr(server, "machine_id", "") or "")
            if not machine or not server_uri.hostname or not server_uri.port:
                return {"success": False, "message": "A connected Plex server is required."}
            params.update({
                "key": f"/library/metadata/{key}", "machineIdentifier": machine,
                "address": server_uri.hostname, "port": server_uri.port,
                "protocol": server_uri.scheme,
            })
        try:
            token = str(getattr(self, "_active_user_token", "") or getattr(self, "_account_token", "") or "")
            headers = self._plex_headers(token, False)
            headers["X-Plex-Target-Client-Identifier"] = str(target["id"])
            async with self._session.get(
                target["url"] + path, headers=headers, params=params,
                timeout=_TIMEOUT, allow_redirects=False) as response:
                await response.read()
                if response.status in (200, 201, 202, 204):
                    return {"success": True, "message": "Player responded."}
                return {"success": False, "message": f"Player returned HTTP {response.status}."}
        except (asyncio.TimeoutError, aiohttp.ClientError, OSError):
            return {"success": False, "message": "The player is unreachable. Check Plexamp Remote Control and Wi-Fi."}

    def _public(rows):
        return [{"id": row["id"], "name": row["name"], "product": row["product"],
                 "source": row["source"], "reachable": "unknown"}
                for row in rows.values()]

    cls.get_player_connect_devices = _get_player_connect_devices
    cls.player_connect_command = _player_connect_command
    cls._rd158_player_connect_installed = True
