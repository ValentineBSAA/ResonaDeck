"""Discover Jellyfin servers on the Steam Deck's local IPv4 networks.

Jellyfin's official UDP client discovery protocol uses port 7359 and the
broadcast question ``Who is JellyfinServer?``.  No passwords or access tokens
are ever sent during discovery.  No background polling or scanning is started.
"""
from __future__ import annotations

import contextlib
import ipaddress
import json
import socket
import time
import urllib.parse

DISCOVERY_QUESTION = b"Who is JellyfinServer?"
DISCOVERY_PORT = 7359


def broadcast_targets():
    """Include limited broadcast and all active Linux interface broadcasts."""
    found = {"255.255.255.255"}
    try:
        import fcntl  # SteamOS/Linux, not present on Windows
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            for _, name in socket.if_nameindex():
                if name.startswith(('lo', 'docker', 'veth')):
                    continue
                try:
                    request = name.encode('ascii')[:15].ljust(16, b'\0') + b'\0' * 24
                    result = fcntl.ioctl(sock.fileno(), 0x8919, request)  # SIOCGIFBRDADDR
                    address = socket.inet_ntoa(result[20:24])
                    if ipaddress.ip_address(address).is_multicast or address == '0.0.0.0':
                        continue
                    found.add(address)
                except (OSError, ValueError, UnicodeError):
                    pass
    except (ImportError, OSError):
        pass
    return sorted(found)


def _valid_server(row: dict, peer_ip: str):
    """Return a display-only server candidate; repair mistaken loopback advertisements."""
    if not isinstance(row, dict) or not isinstance(row.get('Name'), str):
        return None
    advertised = str(row.get('Address') or '').strip()
    parsed = urllib.parse.urlsplit(advertised)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        return None
    try:
        port = parsed.port  # reject malformed or out-of-range port numbers
    except (ValueError, TypeError):
        return None
    try:
        peer = ipaddress.ip_address(peer_ip)
        if peer.is_multicast or peer.is_unspecified:
            return None
        host = ipaddress.ip_address(parsed.hostname)
        if host.is_loopback or host.is_unspecified:
            port = port or (8920 if parsed.scheme == 'https' else 8096)
            advertised = urllib.parse.urlunsplit((parsed.scheme, f'{peer_ip}:{port}', parsed.path, '', ''))
    except ValueError:
        # Hostnames from the server's published URL are valid as-is.
        pass
    except (TypeError, OverflowError):
        return None
    if len(advertised) > 2048:
        return None
    ident = str(row.get('Id') or '')[:160]
    return {
        'id': ident,
        'name': str(row.get('Name') or 'Jellyfin Server')[:120],
        'url': advertised.rstrip('/'),
        'source': 'lan',
    }


def discover_jellyfin_servers(timeout_seconds: float = 2.4, *, targets=None, port: int = DISCOVERY_PORT):
    """Send UDP broadcast probes and gather matching JSON answers for a bounded time."""
    timeout_seconds = max(0.2, min(6.0, float(timeout_seconds)))
    targets = list(targets) if targets is not None else broadcast_targets()
    found = {}
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(('0.0.0.0', 0))
        sock.settimeout(0.18)
        for address in targets:
            with contextlib.suppress(OSError):
                sock.sendto(DISCOVERY_QUESTION, (address, port))
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            try:
                data, peer = sock.recvfrom(8192)
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                response = json.loads(data.decode('utf-8'))
                candidate = _valid_server(response, peer[0])
                if candidate:
                    found[(candidate['id'] or candidate['url'], candidate['url'])] = candidate
            except (ValueError, UnicodeDecodeError, TypeError, KeyError):
                continue
    # Multiple servers may share a hostname, but repeated broadcasts should not duplicate rows.
    return sorted(found.values(), key=lambda s: (s['name'].casefold(), s['url']))
