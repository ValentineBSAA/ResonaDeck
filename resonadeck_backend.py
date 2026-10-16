"""ResonaDeck 0.9.30 DEV QAM listening experience backend.

Plex-first Decky audio client backend for music, audiobooks, podcasts and other audio.
Responsibilities:
- Plex authentication (JWT PIN when cryptography is available, legacy PIN fallback)
- Plex Home member switching including PIN-protected users
- Plex server/resource resolution plus best-effort LAN discovery
- Music/audiobook library role management
- Metadata, search, queue helpers, playback reporting, resume checkpoints
- Token-hiding loopback proxy for audio and artwork
- M4B/M4A embedded chapter parsing via bundled Mutagen
- Redacted diagnostics and health data

The browser/React side never receives Plex account/server tokens.
"""
from __future__ import annotations

import asyncio
import base64
import contextlib
import datetime as _dt
import hashlib
import io
import json
import logging
import os
import re
import secrets
import shutil
import socket
import sqlite3
import ssl
import struct
import sys
import time
import urllib.parse
import urllib.request
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

# Decky may import main.py from a sandbox without adding the plugin root to sys.path.
# Add it explicitly so bundled modules (for example Mutagen) are always importable.
_PLUGIN_ROOT = str(Path(__file__).resolve().parent)
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

import aiohttp
from aiohttp import web
try:
    import certifi
except Exception:  # Decky/SteamOS may already provide a system CA store
    certifi = None
import decky

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    _HAS_ED25519 = True
except Exception:  # pragma: no cover - Decky image may omit cryptography
    serialization = None
    Ed25519PrivateKey = None
    _HAS_ED25519 = False

try:
    from mutagen.mp4 import MP4
except Exception:  # pragma: no cover
    MP4 = None
try:
    from mutagen.id3 import ID3
except Exception:  # pragma: no cover
    ID3 = None

logger = getattr(decky, "logger", logging.getLogger(__name__))
logging.basicConfig(level=logging.INFO)

PLUGIN_VERSION = getattr(decky, "DECKY_PLUGIN_VERSION", "1.1.1")
PRODUCT = "ResonaDeck"
ARTWORK_HYDRATION_GENERATION = "0.9.9-library-refresh-v1"
CATALOG_CACHE_GENERATION = "0.9.9-refresh-v1"
PLATFORM = "Steam Deck"
DEVICE = "Steam Deck"
DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=12, connect=4, sock_read=10)
ART_MAX_BYTES = 12 * 1024 * 1024
PROXY_SESSION_TTL = 24 * 60 * 60
SENSITIVE_RE = re.compile(r"(token|secret|password|authorization|cookie|private|pin)", re.I)
URL_TOKEN_RE = re.compile(r"([?&](?:X-Plex-Token|token|authToken)=)[^&\s]+", re.I)


def _utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _json_b64(value: dict[str, Any]) -> str:
    return _b64url(json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def _safe_write(path: Path, value: Any, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    with contextlib.suppress(Exception):
        os.chmod(path, mode)


def _xml_unescape(value: str) -> str:
    # Plex responses are attribute-centric. Decode the XML entity set locally
    # so Decky runtimes that omit the stdlib xml package still work.
    text = str(value or "")
    named = {"amp": "&", "quot": '"', "apos": "'", "lt": "<", "gt": ">"}

    def repl(match):
        token = match.group(1)
        if token in named:
            return named[token]
        try:
            if token.startswith(("#x", "#X")):
                return chr(int(token[2:], 16))
            if token.startswith("#"):
                return chr(int(token[1:], 10))
        except Exception:
            pass
        return match.group(0)

    return re.sub(r"&([^;]+);", repl, text)


class _PlexElement:
    __slots__ = ("tag", "attrib", "children")

    def __init__(self, tag: str, attrib: dict[str, str] | None = None):
        self.tag = str(tag)
        self.attrib = dict(attrib or {})
        self.children: list[_PlexElement] = []

    def find(self, tag: str):
        name = str(tag).split("}")[-1]
        for child in self.children:
            if child.tag.split("}")[-1] == name:
                return child
        return None

    def findall(self, path: str):
        path = str(path or "")
        deep = path.startswith(".//")
        name = (path[3:] if deep else path).split("}")[-1]
        if not deep:
            return [c for c in self.children if c.tag.split("}")[-1] == name]
        out = []
        stack = list(reversed(self.children))
        while stack:
            node = stack.pop()
            if node.tag.split("}")[-1] == name:
                out.append(node)
            if node.children:
                stack.extend(reversed(node.children))
        return out


_XML_ATTR_RE = re.compile(r'''([A-Za-z_:][\w:.-]*)\s*=\s*(["'])(.*?)\2''', re.S)
_XML_TAG_RE = re.compile(r"<([^<>]+)>", re.S)


def _parse_plex_xml(data: bytes | str) -> _PlexElement:
    # Minimal stack parser for Plex XML. Text nodes are intentionally ignored.
    text = data.decode("utf-8", "replace") if isinstance(data, (bytes, bytearray)) else str(data)
    root = None
    stack: list[_PlexElement] = []
    for match in _XML_TAG_RE.finditer(text):
        raw = match.group(1).strip()
        if not raw or raw.startswith(("?", "!")):
            continue
        if raw.startswith("/"):
            if stack:
                stack.pop()
            continue
        self_closing = raw.endswith("/")
        if self_closing:
            raw = raw[:-1].rstrip()
        parts = raw.split(None, 1)
        tag = parts[0]
        attr_text = parts[1] if len(parts) > 1 else ""
        attrs = {m.group(1): _xml_unescape(m.group(3)) for m in _XML_ATTR_RE.finditer(attr_text)}
        node = _PlexElement(tag, attrs)
        if stack:
            stack[-1].children.append(node)
        elif root is None:
            root = node
        if not self_closing:
            stack.append(node)
    if root is None:
        raise RuntimeError("Plex returned an empty or unreadable XML response")
    return root


def _xml_attrs(node: _PlexElement) -> dict[str, Any]:
    return {str(k): v for k, v in node.attrib.items()}


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _as_bool(value: Any) -> bool:
    return str(value).lower() in ("1", "true", "yes", "on")


def _first(*values: Any) -> str:
    for value in values:
        if value is not None and str(value).strip():
            return str(value)
    return ""

_PLACEHOLDER_TITLES = {"", "untitled", "unknown", "unknown track", "track", "audio", "plex audio"}

def _meaningful_title(*values: Any, fallback: str = "") -> str:
    for value in values:
        text = str(value or "").strip()
        if text and text.lower() not in _PLACEHOLDER_TITLES:
            return text
    return str(fallback or "")


def _split_title_path(path: str) -> tuple[str, str, str]:
    try:
        parts = [p for p in urllib.parse.unquote(path).replace("\\", "/").split("/") if p]
        if len(parts) >= 3:
            filename = os.path.splitext(parts[-1])[0]
            # Common audiobook/music files start with disc/track numbers. Keep
            # those useful for ordering in metadata, but do not expose them as
            # the recovered display title when Plex itself only says Untitled.
            cleaned = re.sub(r"^\s*(?:cd\s*\d+[._ -]*)?(?:\d{1,3}[._ -]+)+", "", filename, flags=re.I).strip()
            album = parts[-2]
            artist = parts[-3]
            if album.lower().startswith(artist.lower() + " - "):
                album = album[len(artist) + 3:].strip() or album
            return artist, album, cleaned or filename
    except Exception:
        pass
    return "Unknown Artist", "Unknown Album", "Unknown Track"


@dataclass
class ServerState:
    machine_id: str = ""
    name: str = ""
    base_url: str = ""
    access_token: str = ""
    source: str = ""
    local: bool = False
    relay: bool = False
    secure: bool = False
    latency_ms: int = 0


class HTTPRangeReader(io.RawIOBase):
    """Small seekable HTTP reader for metadata parsers.

    Each read issues a Range request. It is intentionally metadata-only; the
    actual media stream goes through the aiohttp loopback proxy.
    """

    def __init__(self, url: str, headers: dict[str, str], timeout: float = 8.0):
        self.url = url
        self.headers = dict(headers)
        self.timeout = timeout
        self.pos = 0
        self.length = self._size()

    def _request(self, start: int | None = None, end: int | None = None, method: str = "GET"):
        headers = dict(self.headers)
        if start is not None:
            headers["Range"] = f"bytes={start}-{'' if end is None else end}"
        req = urllib.request.Request(self.url, headers=headers, method=method)
        context = ssl.create_default_context(cafile=certifi.where())
        return urllib.request.urlopen(req, timeout=self.timeout, context=context)

    def _size(self) -> int:
        try:
            with self._request(method="HEAD") as r:
                n = r.headers.get("Content-Length")
                if n:
                    return int(n)
        except Exception:
            pass
        with self._request(0, 0) as r:
            cr = r.headers.get("Content-Range", "")
            m = re.search(r"/(\d+)$", cr)
            if m:
                return int(m.group(1))
            data = r.read()
            return len(data)

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            nxt = offset
        elif whence == io.SEEK_CUR:
            nxt = self.pos + offset
        elif whence == io.SEEK_END:
            nxt = self.length + offset
        else:
            raise ValueError("invalid whence")
        self.pos = max(0, min(self.length, int(nxt)))
        return self.pos

    def read(self, size: int = -1) -> bytes:
        if self.pos >= self.length:
            return b""
        if size is None or size < 0:
            end = self.length - 1
        else:
            end = min(self.length - 1, self.pos + max(0, size) - 1)
        if end < self.pos:
            return b""
        with self._request(self.pos, end) as r:
            data = r.read()
        self.pos += len(data)
        return data


class JsonSettings:
    """Tiny plugin-local settings store.

    ResonaDeck intentionally does not depend on Decky Loader's private
    `settings` helper module. Some Loader/sandbox combinations expose it and
    others do not. Keeping this six-method JSON store in our own backend makes
    startup deterministic while still writing only inside
    DECKY_PLUGIN_SETTINGS_DIR.
    """

    def __init__(self, name: str, settings_directory: str):
        self.path = Path(settings_directory) / f"{name}.json"
        self.data: dict[str, Any] = {}
        self.read()

    def read(self):
        try:
            if self.path.exists():
                value = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(value, dict):
                    self.data = value
        except Exception:
            self.data = {}
        return dict(self.data)

    def getSetting(self, key: str, default: Any = None):
        return self.data.get(key, default)

    def setSetting(self, key: str, value: Any):
        self.data[key] = value
        _safe_write(self.path, self.data)
        return value


def _make_ssl_context() -> ssl.SSLContext:
    try:
        if certifi is not None:
            return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass
    return ssl.create_default_context()


class Plugin:
    def __init__(self):
        self.ssl_context = _make_ssl_context()
        self.settings: JsonSettings | None = None
        self.runtime_dir = Path(decky.DECKY_PLUGIN_RUNTIME_DIR)
        self.settings_dir = Path(decky.DECKY_PLUGIN_SETTINGS_DIR)
        self.log_dir = Path(getattr(decky, "DECKY_PLUGIN_LOG_DIR", decky.DECKY_PLUGIN_RUNTIME_DIR))
        # The Living Library and artwork cache are user data, not executable
        # plugin runtime. Keep them in Decky's persistent settings directory so
        # plugin upgrades do not make ResonaDeck relearn the entire Plex server.
        self.legacy_db_path = self.runtime_dir / "resonadeck.sqlite3"
        self.db_path = self.settings_dir / "resonadeck.sqlite3"
        self.identity_path = self.settings_dir / "device-identity.json"
        # Editable idle quotes live in persistent settings across plugin upgrades.
        self.idle_messages_path = self.settings_dir / "idle-messages.json"
        self._idle_messages_cached = None
        self._idle_messages_stat = None
        self.auth_path = self.settings_dir / "plex-auth.json"
        # Keep the loopback identity in persistent settings. Reusing the same
        # token/port across upgrades keeps already-rendered localhost artwork URLs
        # valid whenever the port can be rebound after a backend restart.
        self.legacy_endpoint_path = self.runtime_dir / "loopback.json"
        self.endpoint_path = self.settings_dir / "loopback.json"
        self.diagnostics_dir = self.runtime_dir / "diagnostics"
        self.legacy_artwork_dir = self.runtime_dir / "artwork-cache"
        self.artwork_dir = self.settings_dir / "artwork-cache"
        self._db: sqlite3.Connection | None = None
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None
        self._port = 0
        self._loop_token = secrets.token_urlsafe(24)
        self._session: aiohttp.ClientSession | None = None
        self._errors: list[dict[str, str]] = []
        self._proxy_sources: dict[str, dict[str, Any]] = {}
        # 0.9.0A hardware-truth transport telemetry. Bounded and token-free.
        self._http_range_events: list[dict[str, Any]] = []
        self._art_sources: dict[str, dict[str, Any]] = {}
        self._art_locks: dict[str, asyncio.Lock] = {}
        self._art_resolve_locks: dict[str, asyncio.Lock] = {}
        # Artwork work is deliberately bounded so a slower NAS never gets
        # swamped by every card mounted in a Steam UI grid at once.
        self._art_fetch_semaphore = asyncio.Semaphore(4)
        self._art_prefetch_tasks: dict[str, asyncio.Task] = {}
        self._art_hydration_task: asyncio.Task | None = None
        self._art_rescan_pending = False
        self._art_hydration_status: dict[str, Any] = {
            "state": "idle", "generation": ARTWORK_HYDRATION_GENERATION,
            "done": 0, "total": 0, "cached": 0, "failed": 0,
            "currentRole": "", "currentTitle": "", "startedAt": 0.0, "updatedAt": time.time(),
        }
        self._art_identity_cache: dict[str, tuple[float, str]] = {}
        self._art_candidate_cache: dict[str, tuple[float, list[str]]] = {}
        # 0.8.1 central Artwork Registry. Frontend surfaces subscribe to one
        # identity/state stream instead of independently swapping unresolved URLs.
        self._art_registry_revision = 0
        self._art_registry: dict[str, dict[str, Any]] = {}
        self._media_source_cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._book_manifest_locks: dict[str, asyncio.Lock] = {}
        self._sync_tasks: dict[str, asyncio.Task] = {}
        self._auth_pending: dict[str, Any] = {}
        self._server = ServerState()
        self._last_server_connection: dict[str, Any] = {}
        self._restore_state = "starting"
        self._restore_last_error = ""
        self._account_token = ""
        self._active_user_token = ""
        self._client_id = ""
        self._jwt_private = None
        self._jwt_kid = ""
        self._lock = asyncio.Lock()
        self._music_refresh_lock = asyncio.Lock()
        self._server_restore_lock = asyncio.Lock()
        self._startup_task: asyncio.Task | None = None
        self._startup_complete = False
        self._startup_started_at = time.time()

    def _migrate_persistent_cache(self) -> None:
        """Best-effort migration from the pre-0.5 runtime cache location.

        Runtime files are disposable during Decky/plugin replacement; settings
        storage is persistent. Never overwrite newer persistent cache entries.
        """
        try:
            if not self.db_path.exists() and self.legacy_db_path.exists() and self.legacy_db_path != self.db_path:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.legacy_db_path, self.db_path)
        except Exception as error:
            self._record("cache-migrate-db", error)
        try:
            if self.legacy_artwork_dir.exists() and self.legacy_artwork_dir != self.artwork_dir:
                self.artwork_dir.mkdir(parents=True, exist_ok=True)
                for source in self.legacy_artwork_dir.iterdir():
                    if not source.is_file() or source.suffix.lower() not in (".bin", ".json"):
                        continue
                    target = self.artwork_dir / source.name
                    if not target.exists():
                        try:
                            shutil.copy2(source, target)
                        except Exception:
                            pass
        except Exception as error:
            self._record("cache-migrate-artwork", error)
        try:
            if not self.endpoint_path.exists() and self.legacy_endpoint_path.exists():
                self.endpoint_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.legacy_endpoint_path, self.endpoint_path)
        except Exception as error:
            self._record("cache-migrate-loopback", error)

    async def _main(self):
        logger.info("Starting ResonaDeck %s", PLUGIN_VERSION)
        # Critical 0.1.2 rule: _main must return quickly. Decky does not need to
        # wait on loopback/network/Plex recovery before exposing RPC methods to
        # the frontend. Local persistence is initialized synchronously; all
        # potentially blocking work continues in a background task.
        for directory in (self.runtime_dir, self.settings_dir, self.diagnostics_dir, self.artwork_dir):
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception as error:
                self._record("startup-directory", error)
        self._migrate_persistent_cache()
        # Seed the editable library once. Never overwrite a listener's changes.
        try:
            if not self.idle_messages_path.exists():
                shutil.copy2(Path(__file__).resolve().parent / "assets" / "idle-messages.json", self.idle_messages_path)
        except Exception as error:
            self._record("idle-messages-seed", error)
        try:
            self.settings = JsonSettings(name="config", settings_directory=decky.DECKY_PLUGIN_SETTINGS_DIR)
        except Exception as error:
            self.settings = None
            self._record("startup-settings", error)
        for area, fn in (("identity", self._init_identity), ("database", self._init_db),
                         ("auth", self._load_auth), ("loopback-state", self._load_loopback_state)):
            try:
                fn()
            except Exception as error:
                self._record(f"startup-{area}", error)
        try:
            self._session = aiohttp.ClientSession(timeout=DEFAULT_TIMEOUT)
        except Exception as error:
            self._session = None
            self._record("startup-http", error)
        self._startup_task = asyncio.create_task(self._finish_startup())
        logger.info("ResonaDeck RPC backend registered; background startup scheduled")

    async def _finish_startup(self):
        try:
            try:
                await asyncio.wait_for(self._start_loopback(), timeout=4.0)
            except Exception as error:
                self._record("startup-loopback", error)
            try:
                await asyncio.wait_for(self._refresh_jwt_if_needed(), timeout=6.0)
            except Exception as error:
                self._record("startup-jwt", error)
            try:
                async with self._server_restore_lock:
                    await asyncio.wait_for(self._restore_server(), timeout=10.0)
            except Exception as error:
                self._restore_state = "offline"
                self._restore_last_error = self._sanitize(str(error))
                self._record("restore", error)
        finally:
            self._startup_complete = True
            logger.info("ResonaDeck background startup complete; loopback port=%s", self._port)

    async def ping(self):
        """Tiny frontend/backend handshake that never touches Plex or the network."""
        return {
            "ok": True,
            "version": str(PLUGIN_VERSION),
            "startupComplete": bool(self._startup_complete),
            "serverRestoreState": self._restore_state,
            "startupAgeMs": int(max(0.0, time.time() - self._startup_started_at) * 1000),
            "loopbackPort": int(self._port or 0),
            "errors": list(self._errors[-8:]),
        }

    async def _unload(self):
        if self._startup_task and not self._startup_task.done():
            self._startup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await self._startup_task
        self._startup_task = None
        if self._runner:
            with contextlib.suppress(Exception):
                await self._runner.cleanup()
        self._runner = None
        self._site = None
        for task in list(self._sync_tasks.values()):
            if task and not task.done():
                task.cancel()
        self._sync_tasks.clear()
        if self._art_hydration_task and not self._art_hydration_task.done():
            self._art_hydration_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await self._art_hydration_task
        self._art_hydration_task = None
        if self._session:
            with contextlib.suppress(Exception):
                await self._session.close()
        self._session = None
        if self._db:
            with contextlib.suppress(Exception):
                self._db.close()
        self._db = None

    # ------------------------------------------------------------------
    # Persistence / security
    # ------------------------------------------------------------------
    def _record(self, area: str, error: Exception | str) -> None:
        text = self._sanitize(str(error))[:800]
        self._errors.append({"time": _utc(), "area": area, "message": text})
        self._errors = self._errors[-80:]
        logger.warning("ResonaDeck %s: %s", area, text)

    def _sanitize(self, text: str) -> str:
        text = URL_TOKEN_RE.sub(r"\1<redacted>", str(text))
        if self._account_token:
            text = text.replace(self._account_token, "<redacted-account-token>")
        if self._active_user_token:
            text = text.replace(self._active_user_token, "<redacted-user-token>")
        if self._server.access_token:
            text = text.replace(self._server.access_token, "<redacted-server-token>")
        if self._loop_token:
            text = text.replace(self._loop_token, "<redacted-loop-token>")
        return text

    def _sanitize_value(self, value: Any) -> Any:
        if isinstance(value, dict):
            out = {}
            for k, v in value.items():
                out[k] = "<redacted>" if SENSITIVE_RE.search(str(k)) else self._sanitize_value(v)
            return out
        if isinstance(value, list):
            return [self._sanitize_value(v) for v in value]
        if isinstance(value, str):
            return self._sanitize(value)
        return value

    def _init_identity(self) -> None:
        raw: dict[str, Any] = {}
        try:
            raw = json.loads(self.identity_path.read_text("utf-8"))
        except Exception:
            pass
        self._client_id = str(raw.get("client_id") or uuid.uuid4())
        self._jwt_kid = str(raw.get("kid") or uuid.uuid4())
        private_b64 = str(raw.get("ed25519_private") or "")
        public_b64 = str(raw.get("ed25519_public") or "")
        if _HAS_ED25519:
            try:
                if private_b64:
                    key_bytes = base64.b64decode(private_b64)
                    self._jwt_private = Ed25519PrivateKey.from_private_bytes(key_bytes)
                else:
                    self._jwt_private = Ed25519PrivateKey.generate()
                    priv = self._jwt_private.private_bytes(
                        serialization.Encoding.Raw,
                        serialization.PrivateFormat.Raw,
                        serialization.NoEncryption(),
                    )
                    pub = self._jwt_private.public_key().public_bytes(
                        serialization.Encoding.Raw,
                        serialization.PublicFormat.Raw,
                    )
                    private_b64 = base64.b64encode(priv).decode("ascii")
                    public_b64 = base64.b64encode(pub).decode("ascii")
            except Exception as error:
                self._jwt_private = None
                self._record("identity-ed25519", error)
        _safe_write(self.identity_path, {
            "client_id": self._client_id,
            "kid": self._jwt_kid,
            "ed25519_private": private_b64,
            "ed25519_public": public_b64,
        })

    def _load_auth(self) -> None:
        try:
            raw = json.loads(self.auth_path.read_text("utf-8"))
        except Exception:
            raw = {}
        self._account_token = str(raw.get("account_token") or "")
        self._active_user_token = str(raw.get("active_user_token") or self._account_token)
        self._auth_pending = dict(raw.get("pending") or {})
        self._last_server_connection = dict(raw.get("server_connection") or {})

    def _save_auth(self) -> None:
        _safe_write(self.auth_path, {
            "account_token": self._account_token,
            "active_user_token": self._active_user_token,
            "pending": self._auth_pending,
            "server_connection": self._last_server_connection,
            "updated_at": _utc(),
        })

    def _settings_get(self, key: str, default: Any = None) -> Any:
        if not self.settings:
            return default
        return self.settings.getSetting(key, default)

    def _settings_set(self, key: str, value: Any) -> None:
        if self.settings:
            self.settings.setSetting(key, value)

    def _init_db(self) -> None:
        self._db = sqlite3.connect(self.db_path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS library_roles(
          server_id TEXT NOT NULL, section_key TEXT NOT NULL,
          title TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'unassigned',
          updated_at REAL NOT NULL, PRIMARY KEY(server_id, section_key));
        CREATE TABLE IF NOT EXISTS resume(
          user_id TEXT NOT NULL, rating_key TEXT NOT NULL,
          kind TEXT NOT NULL, position_ms INTEGER NOT NULL DEFAULT 0,
          duration_ms INTEGER NOT NULL DEFAULT 0, chapter_index INTEGER NOT NULL DEFAULT -1,
          updated_at REAL NOT NULL, PRIMARY KEY(user_id, rating_key));
        CREATE TABLE IF NOT EXISTS chapter_cache(
          server_id TEXT NOT NULL, rating_key TEXT NOT NULL,
          fingerprint TEXT NOT NULL, payload TEXT NOT NULL, updated_at REAL NOT NULL,
          PRIMARY KEY(server_id, rating_key));
        CREATE TABLE IF NOT EXISTS endpoint_health(
          server_id TEXT NOT NULL, uri TEXT NOT NULL, latency_ms INTEGER NOT NULL,
          ok INTEGER NOT NULL, last_seen REAL NOT NULL,
          PRIMARY KEY(server_id, uri));
        CREATE TABLE IF NOT EXISTS catalog_cache(
          server_id TEXT NOT NULL, user_id TEXT NOT NULL, section_key TEXT NOT NULL,
          view TEXT NOT NULL, rating_key TEXT NOT NULL, sort_index INTEGER NOT NULL DEFAULT 0,
          role TEXT NOT NULL DEFAULT '', payload TEXT NOT NULL, plex_updated_at INTEGER NOT NULL DEFAULT 0,
          cached_at REAL NOT NULL, PRIMARY KEY(server_id,user_id,section_key,view,rating_key));
        CREATE INDEX IF NOT EXISTS idx_catalog_cache_page
          ON catalog_cache(server_id,user_id,section_key,view,sort_index);
        CREATE TABLE IF NOT EXISTS catalog_sync(
          server_id TEXT NOT NULL, user_id TEXT NOT NULL, section_key TEXT NOT NULL, view TEXT NOT NULL,
          total INTEGER NOT NULL DEFAULT 0, indexed INTEGER NOT NULL DEFAULT 0, complete INTEGER NOT NULL DEFAULT 0,
          last_error TEXT NOT NULL DEFAULT '', updated_at REAL NOT NULL,
          PRIMARY KEY(server_id,user_id,section_key,view));
        CREATE TABLE IF NOT EXISTS media_index(
          server_id TEXT NOT NULL, user_id TEXT NOT NULL, rating_key TEXT NOT NULL,
          role TEXT NOT NULL DEFAULT '', semantic_type TEXT NOT NULL DEFAULT '', parent_rating_key TEXT NOT NULL DEFAULT '',
          confidence REAL NOT NULL DEFAULT 0, reason TEXT NOT NULL DEFAULT '', payload TEXT NOT NULL DEFAULT '{}',
          source_updated_at INTEGER NOT NULL DEFAULT 0, indexed_at REAL NOT NULL,
          PRIMARY KEY(server_id,user_id,rating_key));
        CREATE INDEX IF NOT EXISTS idx_media_index_role ON media_index(server_id,user_id,role,semantic_type);
        CREATE TABLE IF NOT EXISTS canonical_art(
          server_id TEXT NOT NULL, user_id TEXT NOT NULL, rating_key TEXT NOT NULL,
          role TEXT NOT NULL DEFAULT '', mode TEXT NOT NULL DEFAULT '', candidates TEXT NOT NULL DEFAULT '[]',
          selected_path TEXT NOT NULL DEFAULT '', updated_at REAL NOT NULL,
          PRIMARY KEY(server_id,user_id,rating_key,role,mode));
        CREATE TABLE IF NOT EXISTS book_manifest(
          server_id TEXT NOT NULL, user_id TEXT NOT NULL, book_rating_key TEXT NOT NULL,
          fingerprint TEXT NOT NULL, payload TEXT NOT NULL, updated_at REAL NOT NULL,
          PRIMARY KEY(server_id,user_id,book_rating_key));
        CREATE TABLE IF NOT EXISTS playback_events(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, rating_key TEXT NOT NULL DEFAULT '',
          session_id TEXT NOT NULL DEFAULT '', event TEXT NOT NULL, elapsed_ms INTEGER NOT NULL DEFAULT 0,
          detail TEXT NOT NULL DEFAULT '', created_at REAL NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_playback_events_recent ON playback_events(user_id,created_at DESC);
        CREATE TABLE IF NOT EXISTS book_bookmarks(
          user_id TEXT NOT NULL, book_rating_key TEXT NOT NULL, bookmark_id TEXT NOT NULL,
          position_ms INTEGER NOT NULL DEFAULT 0, title TEXT NOT NULL DEFAULT '', created_at REAL NOT NULL,
          PRIMARY KEY(user_id,book_rating_key,bookmark_id));
        CREATE TABLE IF NOT EXISTS book_history(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, book_rating_key TEXT NOT NULL,
          position_ms INTEGER NOT NULL DEFAULT 0, state TEXT NOT NULL DEFAULT '', created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS book_reading_list(
          user_id TEXT NOT NULL, book_rating_key TEXT NOT NULL, payload TEXT NOT NULL DEFAULT '{}',
          added_at REAL NOT NULL, PRIMARY KEY(user_id,book_rating_key));
        """)
        self._db.commit()

    def _load_loopback_state(self) -> None:
        try:
            raw = json.loads(self.endpoint_path.read_text("utf-8"))
            token = str(raw.get("token") or "")
            port = _as_int(raw.get("port"))
            if re.fullmatch(r"[A-Za-z0-9_-]{16,128}", token):
                self._loop_token = token
            self._port = port if 1024 <= port <= 65535 else 0
        except Exception:
            pass

    def _save_loopback_state(self) -> None:
        _safe_write(self.endpoint_path, {"token": self._loop_token, "port": self._port})

    # ------------------------------------------------------------------
    # HTTP helpers / Plex headers
    # ------------------------------------------------------------------
    def _plex_headers(self, token: str = "", json_accept: bool = True) -> dict[str, str]:
        h = {
            "X-Plex-Product": PRODUCT,
            "X-Plex-Version": str(PLUGIN_VERSION),
            "X-Plex-Client-Identifier": self._client_id,
            "X-Plex-Platform": PLATFORM,
            "X-Plex-Device": DEVICE,
            "X-Plex-Device-Name": PRODUCT,
            "Accept": "application/json" if json_accept else "application/xml",
        }
        if token:
            h["X-Plex-Token"] = token
        return h

    async def _request(self, method: str, url: str, *, token: str = "", params: dict[str, Any] | None = None,
                       json_body: Any = None, data: Any = None, timeout: aiohttp.ClientTimeout | None = None,
                       json_accept: bool = True) -> aiohttp.ClientResponse:
        if not self._session:
            raise RuntimeError("HTTP session is not ready")
        return await self._session.request(
            method, url, headers=self._plex_headers(token, json_accept), params=params,
            json=json_body, data=data, ssl=self.ssl_context, timeout=timeout or DEFAULT_TIMEOUT,
        )

    async def _json(self, method: str, url: str, **kwargs) -> Any:
        async with await self._request(method, url, **kwargs) as r:
            text = await r.text()
            if r.status >= 400:
                raise RuntimeError(f"HTTP {r.status} from {urllib.parse.urlsplit(url).netloc}: {text[:180]}")
            if not text.strip():
                return {}
            try:
                return json.loads(text)
            except Exception:
                # Some Plex endpoints ignore Accept and return XML.
                return {"_xml": text}

    async def _xml(self, method: str, url: str, **kwargs) -> _PlexElement:
        kwargs["json_accept"] = False
        async with await self._request(method, url, **kwargs) as r:
            data = await r.read()
            if r.status >= 400:
                raise RuntimeError(f"HTTP {r.status} from {urllib.parse.urlsplit(url).netloc}: {data[:180]!r}")
            return _parse_plex_xml(data)

    # ------------------------------------------------------------------
    # JWT / Plex sign-in
    # ------------------------------------------------------------------
    def _public_jwk(self) -> dict[str, str] | None:
        if not self._jwt_private or not serialization:
            return None
        pub = self._jwt_private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        return {"kty": "OKP", "crv": "Ed25519", "x": _b64url(pub), "kid": self._jwt_kid, "alg": "EdDSA", "use": "sig"}

    def _device_jwt(self, extra: dict[str, Any]) -> str:
        if not self._jwt_private:
            raise RuntimeError("Ed25519 is unavailable")
        now = int(time.time())
        header = {"kid": self._jwt_kid, "alg": "EdDSA", "typ": "JWT"}
        payload = {"aud": "plex.tv", "iss": self._client_id, "iat": now, "exp": now + 300, **extra}
        signing = f"{_json_b64(header)}.{_json_b64(payload)}".encode("ascii")
        sig = self._jwt_private.sign(signing)
        return signing.decode("ascii") + "." + _b64url(sig)

    def _jwt_exp(self, token: str) -> int:
        try:
            part = token.split(".")[1]
            part += "=" * ((4 - len(part) % 4) % 4)
            return int(json.loads(base64.urlsafe_b64decode(part))["exp"])
        except Exception:
            return 0

    async def _refresh_jwt_if_needed(self) -> bool:
        if not self._account_token or self._account_token.count(".") != 2 or not self._jwt_private:
            return False
        exp = self._jwt_exp(self._account_token)
        if exp and exp - time.time() > 24 * 3600:
            return True
        try:
            nonce_data = await self._json("GET", "https://clients.plex.tv/api/v2/auth/nonce")
            nonce = str(nonce_data.get("nonce") or "")
            if not nonce:
                return False
            device_jwt = self._device_jwt({"nonce": nonce, "scope": "username,email,friendly_name,restricted,anonymous"})
            data = await self._json("POST", "https://clients.plex.tv/api/v2/auth/token", json_body={"jwt": device_jwt})
            token = _first(data.get("auth_token"), data.get("authToken"))
            if not token:
                return False
            old = self._account_token
            self._account_token = token
            if self._active_user_token == old:
                self._active_user_token = token
            self._save_auth()
            return True
        except Exception as error:
            self._record("jwt-refresh", error)
            return False

    async def begin_plex_auth(self):
        """Start Plex PIN authentication and return a browser-friendly URL.

        Prefer Plex's current JWK/JWT-capable PIN endpoint when Ed25519 is
        available, but automatically fall back to the long-lived PIN flow if
        a server/account rollout does not accept the newer request yet.
        """
        async with self._lock:
            last_error: Exception | None = None
            for mode in (("jwt", "legacy") if self._public_jwk() else ("legacy",)):
                try:
                    if mode == "jwt":
                        data = await self._json(
                            "POST", "https://clients.plex.tv/api/v2/pins",
                            json_body={"jwk": self._public_jwk(), "strong": True},
                        )
                    else:
                        data = await self._json("POST", "https://plex.tv/api/v2/pins", params={"strong": "true"})
                    pin_id = _as_int(data.get("id"))
                    code = str(data.get("code") or "")
                    if not pin_id or not code:
                        raise RuntimeError("Plex did not return a PIN")
                    query = urllib.parse.urlencode({
                        "clientID": self._client_id,
                        "code": code,
                        "context[device][product]": PRODUCT,
                        "context[device][deviceName]": DEVICE,
                    })
                    auth_url = f"https://app.plex.tv/auth#?{query}"
                    self._auth_pending = {"id": pin_id, "code": code, "mode": mode, "started": time.time(), "url": auth_url}
                    self._save_auth()
                    return {"success": True, "mode": mode, "pinId": pin_id, "code": code, "url": auth_url}
                except Exception as error:
                    last_error = error
                    self._record(f"auth-begin-{mode}", error)
            return {"success": False, "message": self._sanitize(str(last_error or "Plex sign-in could not start"))}

    async def poll_plex_auth(self):
        pending = dict(self._auth_pending or {})
        pin_id = _as_int(pending.get("id"))
        if not pin_id:
            return {"success": False, "pending": False, "message": "No Plex sign-in is pending"}
        try:
            if pending.get("mode") == "jwt" and self._jwt_private:
                device_jwt = self._device_jwt({"scope": "username,email,friendly_name,restricted,anonymous"})
                data = await self._json("GET", f"https://clients.plex.tv/api/v2/pins/{pin_id}", params={"deviceJWT": device_jwt})
            else:
                data = await self._json("GET", f"https://plex.tv/api/v2/pins/{pin_id}")
            token = _first(data.get("authToken"), data.get("auth_token"), data.get("authenticationToken"))
            if not token:
                return {"success": True, "pending": True, "message": "Waiting for Plex approval"}
            self._account_token = token
            self._active_user_token = token
            self._last_server_connection = {}
            self._server = ServerState()
            self._auth_pending = {}
            self._save_auth()
            await self._restore_server(force=True)
            return {"success": True, "pending": False, "authenticated": True}
        except Exception as error:
            self._record("auth-poll", error)
            return {"success": False, "pending": True, "message": self._sanitize(str(error))}

    async def sign_out(self):
        self._account_token = ""
        self._active_user_token = ""
        self._auth_pending = {}
        self._last_server_connection = {}
        self._server = ServerState()
        self._restore_state = "signed-out"
        self._save_auth()
        self._settings_set("active_home_user", {})
        self._settings_set("selected_server", {})
        return {"success": True}

    async def get_auth_state(self):
        return {
            "authenticated": bool(self._account_token),
            "pending": bool(self._auth_pending),
            "authMode": "jwt" if self._account_token.count(".") == 2 else ("legacy" if self._account_token else "none"),
            "clientId": self._client_id,
            "activeUser": self._settings_get("active_home_user", {}),
            "server": self._server_public(),
            "serverRestoring": bool(self._active_user_token and not self._startup_complete and not self._server.base_url),
            "serverRestoreState": self._restore_state,
        }

    # ------------------------------------------------------------------
    # Plex Home users
    # ------------------------------------------------------------------
    async def get_home_users(self):
        if not self._account_token:
            return {"success": False, "users": [], "message": "Connect Plex first"}
        users: list[dict[str, Any]] = []
        try:
            # v2 endpoint is JSON on current Plex. Fall back to the long-lived XML endpoint.
            data = await self._json("GET", "https://clients.plex.tv/api/v2/home/users", token=self._account_token)
            candidates = data.get("users") if isinstance(data, dict) else data
            if isinstance(candidates, dict):
                candidates = candidates.get("items") or candidates.get("users") or []
            if isinstance(candidates, list):
                for u in candidates:
                    if not isinstance(u, dict):
                        continue
                    users.append(self._normalize_home_user(u))
            if not users:
                raise ValueError("v2 did not provide users")
        except Exception:
            root = await self._xml("GET", "https://plex.tv/api/home/users", token=self._account_token)
            for node in list(root):
                if node.tag.lower().endswith("user"):
                    users.append(self._normalize_home_user(_xml_attrs(node)))
        # Stable unique users only.
        seen = set()
        out = []
        for u in users:
            key = str(u.get("id") or u.get("uuid") or u.get("title"))
            if key and key not in seen:
                seen.add(key); out.append(u)
        return {"success": True, "users": out, "active": self._settings_get("active_home_user", {})}

    def _normalize_home_user(self, raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(raw.get("id") or raw.get("uuid") or raw.get("userID") or raw.get("userId") or ""),
            "uuid": str(raw.get("uuid") or ""),
            "title": _first(raw.get("title"), raw.get("friendlyName"), raw.get("username"), "Plex User"),
            "username": _first(raw.get("username"), raw.get("title")),
            "thumb": _first(raw.get("thumb"), raw.get("avatar")),
            "protected": _as_bool(raw.get("protected") or raw.get("pin")),
            "restricted": _as_bool(raw.get("restricted")),
            "admin": _as_bool(raw.get("admin")),
        }

    async def switch_home_user(self, user_id: str, pin: str = ""):
        if not self._account_token:
            return {"success": False, "message": "Connect Plex first"}
        user_id = str(user_id or "").strip()
        pin = str(pin or "").strip()
        if not user_id:
            return {"success": False, "message": "Choose a Plex Home user"}
        try:
            token = ""
            # Current clients endpoint first.
            try:
                data = await self._json(
                    "POST", f"https://clients.plex.tv/api/v2/home/users/{urllib.parse.quote(user_id)}/switch",
                    token=self._account_token, params={"pin": pin} if pin else None,
                )
                token = _first(data.get("authToken"), data.get("auth_token"), data.get("authenticationToken"))
            except Exception:
                root = await self._xml(
                    "POST", f"https://plex.tv/api/home/users/{urllib.parse.quote(user_id)}/switch",
                    token=self._account_token, params={"pin": pin} if pin else None,
                )
                token = _first(root.attrib.get("authenticationToken"), root.attrib.get("authToken"), root.attrib.get("token"))
                if not token:
                    for node in root.iter():
                        token = _first(node.attrib.get("authenticationToken"), node.attrib.get("authToken"), node.attrib.get("token"))
                        if token: break
            if not token:
                raise RuntimeError("Plex did not return a user token. Check the PIN.")
            users = await self.get_home_users()
            selected = next((u for u in users.get("users", []) if str(u.get("id")) == user_id or str(u.get("uuid")) == user_id), {"id": user_id, "title": "Plex User"})
            self._active_user_token = token
            self._last_server_connection = {}  # Server credentials belong to the selected Plex Home user.
            self._server = ServerState()
            self._settings_set("active_home_user", selected)
            self._save_auth()
            await self._restore_server(force=True)
            return {"success": True, "user": selected, "server": self._server_public()}
        except Exception as error:
            self._record("home-switch", error)
            msg = str(error)
            if "401" in msg or "403" in msg:
                msg = "PIN rejected or this user cannot be switched to"
            return {"success": False, "message": self._sanitize(msg)}

    # ------------------------------------------------------------------
    # Server discovery / selection
    # ------------------------------------------------------------------
    async def _resources(self, token: str) -> list[dict[str, Any]]:
        data = await self._json(
            "GET", "https://clients.plex.tv/api/v2/resources", token=token,
            params={"includeHttps": "1", "includeRelay": "1", "includeIPv6": "1"},
        )
        rows = data if isinstance(data, list) else data.get("resources", []) if isinstance(data, dict) else []
        return [r for r in rows if isinstance(r, dict) and "server" in str(r.get("provides", ""))]

    def _discover_gdm_sync(self) -> list[dict[str, Any]]:
        payload = b"M-SEARCH * HTTP/1.0\r\n\r\n"
        found: dict[str, dict[str, Any]] = {}
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(0.35)
        try:
            for addr in (("255.255.255.255", 32414), ("239.0.0.250", 32414)):
                with contextlib.suppress(Exception): sock.sendto(payload, addr)
            deadline = time.time() + 1.15
            while time.time() < deadline:
                try:
                    data, peer = sock.recvfrom(65535)
                except socket.timeout:
                    continue
                text = data.decode("utf-8", "replace")
                headers = {}
                for line in text.splitlines()[1:]:
                    if ":" in line:
                        k, v = line.split(":", 1); headers[k.strip().lower()] = v.strip()
                port = _as_int(headers.get("port"), 32400)
                machine = headers.get("resource-identifier", "")
                uri = f"http://{peer[0]}:{port}"
                found[machine or uri] = {"machineId": machine, "name": headers.get("name") or headers.get("host") or peer[0], "uri": uri, "local": True, "source": "lan"}
        finally:
            sock.close()
        return list(found.values())

    async def discover_servers(self):
        resources: list[dict[str, Any]] = []
        if self._active_user_token:
            try:
                resources = await self._resources(self._active_user_token)
            except Exception as error:
                self._record("resources", error)
        gdm = []
        try:
            gdm = await asyncio.to_thread(self._discover_gdm_sync)
        except Exception as error:
            self._record("gdm", error)
        rows = []
        for r in resources:
            connections = r.get("connections") or []
            rows.append({
                "machineId": str(r.get("clientIdentifier") or r.get("machineIdentifier") or ""),
                "name": str(r.get("name") or "Plex Media Server"),
                "owned": bool(r.get("owned", True)),
                "accessToken": "<hidden>" if r.get("accessToken") else "",
                "connections": [
                    {"uri": c.get("uri"), "local": bool(c.get("local")), "relay": bool(c.get("relay")), "protocol": c.get("protocol")}
                    for c in connections if isinstance(c, dict)
                ],
                "source": "account",
            })
        # Only tokenless discovery details leave Python.
        existing = {x.get("machineId") for x in rows if x.get("machineId")}
        for x in gdm:
            if x.get("machineId") not in existing:
                rows.append(x)
        return {"success": True, "servers": rows, "selected": self._server_public()}

    async def _probe_connection(self, uri: str, token: str, server_id: str = "") -> tuple[bool, int]:
        started = time.monotonic()
        try:
            async with await self._request("GET", uri.rstrip("/") + "/identity", token=token,
                                           timeout=aiohttp.ClientTimeout(total=2.4, connect=1.5), json_accept=False) as r:
                await r.read()
                ok = r.status < 400
        except Exception:
            ok = False
        ms = int((time.monotonic() - started) * 1000)
        if self._db and server_id:
            with contextlib.suppress(Exception):
                self._db.execute("INSERT OR REPLACE INTO endpoint_health(server_id,uri,latency_ms,ok,last_seen) VALUES(?,?,?,?,?)",
                                 (server_id, uri, ms, 1 if ok else 0, time.time()))
                self._db.commit()
        return ok, ms

    def _server_user_fingerprint(self) -> str:
        # A remembered server token cannot be shared between Plex Home users.
        return hashlib.sha256(self._active_user_token.encode("utf-8")).hexdigest() if self._active_user_token else ""

    async def _restore_cached_server(self) -> bool:
        saved = dict(self._last_server_connection or {})
        chosen = self._settings_get("selected_server", {}) or {}
        uri = str(saved.get("uri") or "")
        token = str(saved.get("token") or "")
        machine_id = str(saved.get("machineId") or "")
        if not (uri.startswith(("https://", "http://")) and token and machine_id):
            return False
        if saved.get("userFingerprint") != self._server_user_fingerprint():
            return False
        if chosen.get("machineId") and str(chosen["machineId"]) != machine_id:
            return False
        ok, latency = await self._probe_connection(uri, token, machine_id)
        if not ok:
            return False
        self._server = ServerState(
            machine_id=machine_id, name=str(saved.get("name") or chosen.get("name") or "Plex Media Server"),
            base_url=uri, access_token=token, source="remembered", local=bool(saved.get("local")),
            relay=bool(saved.get("relay")), secure=uri.startswith("https://"), latency_ms=latency,
        )
        return True

    async def _restore_server(self, force: bool = False):
        if not self._active_user_token:
            self._restore_state = "signed-out"
            return False
        self._restore_state = "restoring"
        self._restore_last_error = ""
        # Restore the last successful endpoint without requiring Plex's cloud
        # discovery service to be online as the Steam Deck wakes from sleep.
        if await self._restore_cached_server():
            self._restore_state = "connected"
            return True
        selected = self._settings_get("selected_server", {}) or {}
        wanted = str(selected.get("machineId") or "")
        try:
            resources = await self._resources(self._active_user_token)
            if resources:
                ordered = [r for r in resources if str(r.get("clientIdentifier") or "") == wanted] if wanted else resources
                for resource in ordered:
                    if await self._select_resource(resource):
                        self._restore_state = "connected"
                        return True
        except Exception as error:
            self._restore_last_error = self._sanitize(str(error))
            self._record("restore-discovery", error)
        # Do not pretend a stale in-memory connection is an online server.
        self._server = ServerState()
        self._restore_state = "offline"
        return False

    async def select_server(self, machine_id: str):
        if not self._active_user_token:
            return {"success": False, "message": "Choose a Plex user first"}
        try:
            try:
                resources = await self._resources(self._active_user_token)
            except Exception as error:
                self._record("select-server-cloud", error)
                resources = []
            resource = next((r for r in resources if str(r.get("clientIdentifier") or "") == str(machine_id)), None)
            if not resource:
                # A sleeping Deck can still find Plex over GDM when Plex's cloud
                # service cannot be reached. Allow the selected LAN advertisement
                # to be probed with the active Plex Home user token.
                discovered = await asyncio.to_thread(self._discover_gdm_sync)
                lan = next((r for r in discovered if str(r.get("machineId") or "") == str(machine_id) and machine_id), None)
                if lan:
                    uri = str(lan.get("uri") or "")
                    resource = {
                        "clientIdentifier": machine_id,
                        "name": str(lan.get("name") or "Plex Media Server"),
                        "accessToken": self._active_user_token,
                        "connections": [{"uri": uri, "local": True, "relay": False, "protocol": "http"}],
                    }
            if not resource:
                return {"success": False, "message": "That server is not currently available"}
            ok = await self._select_resource(resource)
            return {"success": bool(ok), "server": self._server_public(), "message": "Connected" if ok else "No working connection found"}
        except Exception as error:
            self._record("select-server", error)
            return {"success": False, "message": self._sanitize(str(error))}

    async def _select_resource(self, resource: dict[str, Any]) -> bool:
        machine_id = str(resource.get("clientIdentifier") or resource.get("machineIdentifier") or "")
        token = str(resource.get("accessToken") or self._active_user_token or "")
        name = str(resource.get("name") or "Plex Media Server")
        connections = [c for c in (resource.get("connections") or []) if isinstance(c, dict) and c.get("uri")]
        # local HTTPS, local HTTP, remote HTTPS, remote HTTP, relay last.
        def score(c):
            local = bool(c.get("local")); relay = bool(c.get("relay")); https = str(c.get("protocol") or "").lower() == "https" or str(c.get("uri")).startswith("https:")
            if relay: return 50
            if local and https: return 0
            if local: return 10
            if https: return 20
            return 30
        connections.sort(key=score)
        for c in connections:
            uri = str(c.get("uri") or "").rstrip("/")
            ok, ms = await self._probe_connection(uri, token, machine_id)
            if ok:
                self._server = ServerState(
                    machine_id=machine_id, name=name, base_url=uri, access_token=token,
                    source="account", local=bool(c.get("local")), relay=bool(c.get("relay")),
                    secure=uri.startswith("https:"), latency_ms=ms,
                )
                self._settings_set("selected_server", {"machineId": machine_id, "name": name})
                # Credentials stay in the chmod-0600 authentication file, never
                # in ordinary plugin preferences or frontend RPC responses.
                self._last_server_connection = {
                    "machineId": machine_id, "name": name, "uri": uri, "token": token,
                    "local": bool(c.get("local")), "relay": bool(c.get("relay")),
                    "userFingerprint": self._server_user_fingerprint(),
                }
                self._save_auth()
                self._restore_state = "connected"
                return True
        return False

    def _server_public(self) -> dict[str, Any]:
        s = self._server
        return {"machineId": s.machine_id, "name": s.name, "url": s.base_url, "source": s.source,
                "local": s.local, "relay": s.relay, "secure": s.secure, "latencyMs": s.latency_ms,
                "connected": bool(s.base_url and s.access_token), "restoreState": self._restore_state}

    # ------------------------------------------------------------------
    # Library / metadata helpers
    # ------------------------------------------------------------------
    async def _pms_xml(self, path: str, *, params: dict[str, Any] | None = None) -> _PlexElement:
        if not self._server.base_url or not self._server.access_token:
            async with self._server_restore_lock:
                if not self._server.base_url or not self._server.access_token:
                    if not await self._restore_server(force=True):
                        raise RuntimeError("No Plex server connection is available")
        try:
            return await self._xml("GET", self._server.base_url.rstrip("/") + path, token=self._server.access_token, params=params)
        except Exception as first_error:
            self._record("pms-read-recover", first_error)
            async with self._server_restore_lock:
                recovered = await self._restore_server(force=True)
            if not recovered:
                raise
            return await self._xml("GET", self._server.base_url.rstrip("/") + path, token=self._server.access_token, params=params)

    async def recover_connection(self):
        # Re-resolve the selected Plex resource and report the public state.
        if not self._active_user_token:
            return {"success": False, "server": self._server_public(), "message": "Choose a Plex user first"}
        try:
            async with self._server_restore_lock:
                ok = await self._restore_server(force=True)
            return {"success": bool(ok), "server": self._server_public(), "message": "Connected" if ok else "No working Plex endpoint found"}
        except Exception as error:
            self._record("recover-connection", error)
            return {"success": False, "server": self._server_public(), "message": self._sanitize(str(error))}

    def _role(self, section_key: str) -> str:
        if not self._db or not self._server.machine_id:
            return "unassigned"
        row = self._db.execute("SELECT role FROM library_roles WHERE server_id=? AND section_key=?", (self._server.machine_id, str(section_key))).fetchone()
        return str(row[0]) if row else "unassigned"

    async def get_libraries(self):
        try:
            root = await self._pms_xml("/library/sections")
            libraries = []
            for n in root.findall(".//Directory"):
                typ = str(n.attrib.get("type") or "")
                if typ not in ("artist", "music"):
                    continue
                key = str(n.attrib.get("key") or "")
                title = str(n.attrib.get("title") or "Audio")
                libraries.append({"key": key, "title": title, "type": typ, "role": self._role(key), "uuid": n.attrib.get("uuid", "")})
            # Sensible suggestions only when not assigned yet.
            for lib in libraries:
                if lib["role"] == "unassigned":
                    low = lib["title"].lower()
                    if any(k in low for k in ("audio book", "audiobook", "audio books", "books", "book")):
                        lib["suggestedRole"] = "audiobooks"
                    elif any(k in low for k in ("podcast", "podcasts")):
                        lib["suggestedRole"] = "podcasts"
                    elif any(k in low for k in ("music", "songs", "albums")):
                        lib["suggestedRole"] = "music"
                    else:
                        # Plex exposes many spoken/ambient libraries through the same
                        # music-style hierarchy. Keep them playable without pretending
                        # they are albums or books. The user can always override this.
                        lib["suggestedRole"] = "other"
            return {"success": True, "libraries": libraries}
        except Exception as error:
            self._record("libraries", error)
            return {"success": False, "libraries": [], "message": self._sanitize(str(error))}


    async def inspect_library(self, section_key: str):
        """Inspect a Plex audio section without requiring a ResonaDeck role.

        Library setup needs to answer "what is actually in here?" before the
        user classifies a section.  This intentionally addresses Plex by
        section key rather than through the role mapping.
        """
        key = str(section_key or "").strip()
        if not key:
            return {"success": False, "message": "Missing Plex library section"}
        try:
            # Refresh the canonical section title from /library/sections so the
            # UI never has to treat an internal section number as a title.
            sections_root = await self._pms_xml("/library/sections")
            section_node = None
            for node in sections_root.findall(".//Directory"):
                if str(node.attrib.get("key") or "") == key:
                    section_node = node
                    break
            title = str((section_node.attrib.get("title") if section_node else "") or f"Plex Audio {key}")
            typ = str((section_node.attrib.get("type") if section_node else "") or "artist")

            async def fetch(plex_type: int, size: int = 8, sort: str = "addedAt:desc"):
                root = await self._pms_xml(
                    f"/library/sections/{urllib.parse.quote(key)}/all",
                    params={"type": plex_type, "sort": sort, "X-Plex-Container-Start": 0, "X-Plex-Container-Size": size},
                )
                nodes = root.findall(".//Track") if plex_type == 10 else root.findall(".//Directory")
                total = _as_int(root.attrib.get("totalSize") or root.attrib.get("size"), len(nodes))
                mapper = self._artist if plex_type == 8 else self._album if plex_type == 9 else self._track
                return total, [mapper(n) for n in nodes]

            (artist_count, artists), (album_count, albums), (track_count, tracks) = await asyncio.gather(
                fetch(8, 10, "titleSort:asc"),
                fetch(9, 12, "addedAt:desc"),
                fetch(10, 1, "addedAt:desc"),
            )
            if albums:
                weak = [i for i, row in enumerate(albums[:12]) if (not row.get("thumb") or str(row.get("title") or "").strip().lower() in _PLACEHOLDER_TITLES or str(row.get("title") or "").startswith("Unknown collection"))]
                if weak:
                    enriched = await asyncio.gather(*(self._enrich_collection_item(albums[i]) for i in weak))
                    for i, row in zip(weak, enriched):
                        albums[i] = row
            # Inspector previews are unique album/book-level items only. Tracks are
            # never mixed into this strip because several chapters from one book
            # legitimately share one cover and made the old 8-item sample view look
            # like duplicates. The full catalog is exposed by browse_section().
            samples = albums[:6]
            hero = next((x for x in samples if x.get("thumb")), None)
            role = self._role(key)
            suggested = "other"
            low = title.lower()
            if any(k in low for k in ("audio book", "audiobook", "audio books", "books", "book")):
                suggested = "audiobooks"
            elif "podcast" in low:
                suggested = "podcasts"
            elif any(k in low for k in ("music", "songs", "albums")):
                suggested = "music"
            return {
                "success": True, "library": {
                    "key": key, "title": title, "type": typ, "role": role, "suggestedRole": suggested,
                    "counts": {"artists": artist_count, "albums": album_count, "tracks": track_count},
                    "samples": samples, "heroThumb": (hero or {}).get("thumb", ""),
                }
            }
        except Exception as error:
            self._record("library-inspect", error)
            return {"success": False, "message": self._sanitize(str(error))}

    async def set_library_role(self, section_key: str, title: str, role: str):
        if role not in ("music", "audiobooks", "podcasts", "other", "ignore", "unassigned"):
            return {"success": False, "message": "Invalid library role"}
        if not self._db or not self._server.machine_id:
            return {"success": False, "message": "No Plex server selected"}
        self._db.execute("INSERT OR REPLACE INTO library_roles(server_id,section_key,title,role,updated_at) VALUES(?,?,?,?,?)",
                         (self._server.machine_id, str(section_key), str(title), role, time.time()))
        self._db.commit()
        return {"success": True}

    def _section_for_role(self, role: str) -> str:
        if not self._db or not self._server.machine_id:
            return ""
        row = self._db.execute("SELECT section_key FROM library_roles WHERE server_id=? AND role=? ORDER BY updated_at DESC LIMIT 1",
                               (self._server.machine_id, role)).fetchone()
        return str(row[0]) if row else ""

    async def _resolve_section_for_role(self, role: str) -> tuple[str, str, str]:
        """Resolve a playable Plex section for a ResonaDeck role.

        Confirmed role assignments always win. During first-run setup, however,
        the full-screen entertainment pages should not look empty merely because
        the user has not pressed Confirm yet. If exactly one unassigned Plex
        section has a safe suggestion for the requested role, use it as a
        temporary preview route. Nothing is persisted until set_library_role().
        """
        confirmed = self._section_for_role(role)
        if confirmed:
            return confirmed, "confirmed", ""
        result = await self.get_libraries()
        libraries = result.get("libraries", []) if isinstance(result, dict) else []
        candidates = [
            lib for lib in libraries
            if str(lib.get("role") or "unassigned") == "unassigned"
            and str(lib.get("suggestedRole") or "") == str(role)
        ]
        if len(candidates) == 1:
            lib = candidates[0]
            return str(lib.get("key") or ""), "suggested", str(lib.get("title") or "")
        return "", "missing", ""

    def _track(self, n: _PlexElement) -> dict[str, Any]:
        a = n.attrib
        media = n.find("Media")
        part = media.find("Part") if media is not None else None
        part_path = part.attrib.get("file", "") if part is not None else ""
        f_artist, f_album, f_title = _split_title_path(part_path)
        duration = _as_int(a.get("duration"))
        return {
            "ratingKey": str(a.get("ratingKey") or a.get("key") or ""),
            "key": str(a.get("key") or ""),
            "title": _meaningful_title(a.get("title"), f_title, fallback="Unknown track"),
            "artist": _first(a.get("grandparentTitle"), a.get("originalTitle"), f_artist),
            "album": _first(a.get("parentTitle"), f_album),
            "duration": duration / 1000.0,
            "durationMs": duration,
            "thumb": _first(a.get("thumb"), a.get("parentThumb"), a.get("grandparentThumb"), a.get("art")),
            "selfThumb": str(a.get("thumb") or ""),
            "parentThumb": str(a.get("parentThumb") or ""),
            "year": _as_int(a.get("year")),
            "index": _as_int(a.get("index")),
            "parentRatingKey": str(a.get("parentRatingKey") or ""),
            "grandparentRatingKey": str(a.get("grandparentRatingKey") or ""),
            "viewOffset": _as_int(a.get("viewOffset")),
            "lastViewedAt": _as_int(a.get("lastViewedAt")),
            "addedAt": _as_int(a.get("addedAt")),
            "updatedAt": _as_int(a.get("updatedAt")),
            "viewCount": _as_int(a.get("viewCount")),
            "guid": str(a.get("guid") or ""),
            "container": str(media.attrib.get("container") if media is not None else ""),
            "audioCodec": str(media.attrib.get("audioCodec") if media is not None else ""),
            "bitrate": _as_int(media.attrib.get("bitrate") if media is not None else 0),
            "partKey": str(part.attrib.get("key") if part is not None else ""),
            "file": str(part.attrib.get("file") if part is not None else ""),
            "size": _as_int(part.attrib.get("size") if part is not None else 0),
            "type": "track",
            "mediaType": "track",
            "plexType": str(a.get("type") or "track"),
            "art": _first(a.get("art"), a.get("parentArt"), a.get("grandparentArt")),
            "selfArt": str(a.get("art") or ""),
            "parentArt": str(a.get("parentArt") or ""),
            "grandparentThumb": str(a.get("grandparentThumb") or ""),
            "grandparentArt": str(a.get("grandparentArt") or ""),
        }

    @staticmethod
    def _is_semantic_music_album(item: dict[str, Any]) -> bool:
        """Return True only for a Plex semantic Album object.

        0.9.7 used a title heuristic to hide obvious source-folder ghosts. Real
        libraries proved that filesystem depth/name cannot tell us whether a
        directory represents an artist, album, alternate version, track folder,
        notes folder, or a source root. The normal Music catalog therefore uses
        Plex's semantic type only; folder descendants remain discoverable through
        Plex's Artist/Album/Track endpoints and are never discarded by path.
        """
        row = dict(item or {})
        raw = str(row.get("plexType") or row.get("type") or row.get("mediaType") or "").lower().strip()
        semantic = str(row.get("semanticType") or "").lower().strip()
        if raw in {"folder", "directory", "container", "artist", "track", "audio", "playlist", "collection"}:
            return False
        if raw == "album":
            return True
        return not raw and semantic == "album"

    def _album(self, n: _PlexElement) -> dict[str, Any]:
        a = n.attrib
        plex_type = str(a.get("type") or "")
        return {
            "ratingKey": str(a.get("ratingKey") or a.get("key") or ""),
            "key": str(a.get("key") or ""),
            "title": _meaningful_title(a.get("title"), fallback="Unknown collection"),
            "artist": _first(a.get("parentTitle"), a.get("grandparentTitle"), a.get("originalTitle")),
            "year": _as_int(a.get("year")),
            "thumb": _first(a.get("thumb"), a.get("parentThumb"), a.get("grandparentThumb"), a.get("art")),
            "selfThumb": str(a.get("thumb") or ""),
            "summary": str(a.get("summary") or ""),
            "addedAt": _as_int(a.get("addedAt")),
            "viewOffset": _as_int(a.get("viewOffset")),
            "duration": _as_int(a.get("duration")) / 1000.0,
            "leafCount": _as_int(a.get("leafCount")),
            "viewCount": _as_int(a.get("viewCount")),
            "lastViewedAt": _as_int(a.get("lastViewedAt")),
            "updatedAt": _as_int(a.get("updatedAt")),
            "guid": str(a.get("guid") or ""),
            "originallyAvailableAt": str(a.get("originallyAvailableAt") or ""),
            "type": plex_type or "album",
            "mediaType": plex_type or "album",
            "plexType": plex_type,
            "art": _first(a.get("art"), a.get("parentArt"), a.get("grandparentArt")),
            "selfArt": str(a.get("art") or ""),
            "parentThumb": str(a.get("parentThumb") or ""),
            "grandparentThumb": str(a.get("grandparentThumb") or ""),
            "parentArt": str(a.get("parentArt") or ""),
            "grandparentArt": str(a.get("grandparentArt") or ""),
            "parentRatingKey": str(a.get("parentRatingKey") or ""),
        }

    def _collection(self, n: _PlexElement) -> dict[str, Any]:
        a = n.attrib
        return {
            "ratingKey": str(a.get("ratingKey") or a.get("key") or ""),
            "key": str(a.get("key") or ""),
            "title": _meaningful_title(a.get("title"), fallback="Untitled collection"),
            "thumb": _first(a.get("thumb"), a.get("art")),
            "selfThumb": str(a.get("thumb") or ""),
            "selfArt": str(a.get("art") or ""),
            "summary": str(a.get("summary") or ""),
            "childCount": _as_int(a.get("childCount") or a.get("leafCount")),
            "addedAt": _as_int(a.get("addedAt")),
            "updatedAt": _as_int(a.get("updatedAt")),
            "type": "collection",
        }

    def _artist(self, n: _PlexElement) -> dict[str, Any]:
        a = n.attrib
        return {"ratingKey": str(a.get("ratingKey") or a.get("key") or ""), "title": _first(a.get("title"), "Unknown"),
                "thumb": _first(a.get("thumb"), a.get("art")), "selfThumb": str(a.get("thumb") or ""),
                "summary": str(a.get("summary") or ""), "type": "artist", "mediaType": "artist",
                "plexType": str(a.get("type") or "artist"),
                "art": str(a.get("art") or ""), "selfArt": str(a.get("art") or "")}

    # ------------------------------------------------------------------
    # Eli media intelligence
    # ------------------------------------------------------------------
    def _eli_classify_item(self, item: dict[str, Any], role: str = "", view: str = "") -> dict[str, Any]:
        """Classify Plex's music-style hierarchy into ResonaDeck media semantics.

        A confirmed Library Manager role is authoritative. Eli then interprets
        the hierarchy inside that role so a Directory can be a book/podcast
        show/album and a Track can be a chapter/episode/song. If no role is
        known, conservative file/duration/title heuristics are used and the
        confidence stays below a confirmed role.
        """
        row = dict(item or {})
        role = str(role or row.get("libraryRole") or "").lower()
        view = str(view or "").lower()
        plex_type = str(row.get("plexType") or row.get("type") or row.get("mediaType") or "").lower()
        is_track = plex_type in ("track", "audio", "episode") or bool(row.get("partKey"))
        is_artist = plex_type == "artist" or view in ("artists", "authors")
        is_directory = plex_type in ("folder", "directory", "container")
        duration = max(0.0, float(row.get("duration") or 0.0))
        container = str(row.get("container") or "").lower().lstrip(".")
        text = " ".join(str(row.get(k) or "") for k in ("title", "album", "artist", "guid", "file")).lower()
        semantic = "other-audio"
        confidence = 0.55
        reason = "generic audio fallback"
        if is_directory:
            semantic = "filesystem-directory"
            confidence = 1.0; reason = "raw Plex filesystem directory"
        elif role == "audiobooks":
            semantic = "audiobook-file" if is_track else ("author" if is_artist else "book")
            confidence = 1.0; reason = "confirmed audiobook library role"
        elif role == "podcasts":
            semantic = "episode" if is_track else ("podcast-author" if is_artist else "podcast-show")
            confidence = 1.0; reason = "confirmed podcast library role"
        elif role == "music":
            if is_track:
                semantic = "song"
            elif is_artist:
                semantic = "artist"
            elif plex_type == "album" or (not plex_type and view == "albums"):
                semantic = "album"
            else:
                semantic = "music-container"
            confidence = 1.0; reason = "confirmed music library role + Plex semantic type"
        elif role == "other":
            semantic = "other-track" if is_track else "other-collection"
            confidence = 1.0; reason = "confirmed other-audio library role"
        else:
            if container in ("m4b",) or "audiobook" in text or "audio book" in text:
                semantic = "audiobook-file" if is_track else "book"
                confidence = 0.88; reason = "M4B/audiobook metadata heuristic"
            elif "podcast" in text or (is_track and duration >= 12 * 60 and any(x in text for x in ("episode", " ep ", "show"))):
                semantic = "episode" if is_track else "podcast-show"
                confidence = 0.78; reason = "podcast title/duration heuristic"
            elif is_artist:
                semantic = "artist"; confidence = 0.62; reason = "Plex artist hierarchy"
            elif is_track and duration and duration <= 20 * 60:
                semantic = "song"; confidence = 0.64; reason = "short-form Plex track heuristic"
            elif is_track and duration >= 45 * 60:
                semantic = "audiobook-file"; confidence = 0.58; reason = "long-form track heuristic"
            elif not is_track:
                semantic = "album"; confidence = 0.60; reason = "Plex album hierarchy"
        row["semanticType"] = semantic
        row["eliConfidence"] = round(float(confidence), 3)
        row["eliReason"] = reason
        return row

    def _index_media_item(self, item: dict[str, Any], role: str = "", view: str = "") -> dict[str, Any]:
        row = self._eli_classify_item(item, role, view)
        if not self._db:
            return row
        rating_key = str(row.get("ratingKey") or row.get("key") or "")
        if not rating_key:
            return row
        server_id, user_id = self._catalog_identity()
        try:
            self._db.execute("""
                INSERT OR REPLACE INTO media_index
                (server_id,user_id,rating_key,role,semantic_type,parent_rating_key,confidence,reason,payload,source_updated_at,indexed_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """, (server_id, user_id, rating_key, str(role or row.get("libraryRole") or ""),
                  str(row.get("semanticType") or ""), str(row.get("parentRatingKey") or ""),
                  float(row.get("eliConfidence") or 0), str(row.get("eliReason") or ""),
                  json.dumps(row, ensure_ascii=False, separators=(",", ":")), _as_int(row.get("updatedAt")), time.time()))
        except Exception as error:
            self._record("eli-index", error)
        return row

    async def eli_classify(self, rating_key: str, role: str = ""):
        """Public diagnostic/classification endpoint used by System Health and tests."""
        try:
            meta = await self.get_metadata(str(rating_key))
            item = dict(meta.get("item") or {}) if isinstance(meta, dict) else {}
            if not item:
                return {"success": False, "message": "Media item was not found"}
            row = self._index_media_item(item, role, "")
            if self._db:
                self._db.commit()
            return {"success": True, "item": row}
        except Exception as error:
            self._record("eli-classify", error)
            return {"success": False, "message": self._sanitize(str(error))}

    async def _enrich_collection_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Recover weak Plex collection metadata from its first playable child.

        Some music-style Plex libraries expose an album/book Directory with an
        empty/placeholder title or no thumb even though the child Track has
        correct parentTitle, file-path metadata, and artwork.  Do this only for
        weak rows so ordinary well-tagged libraries stay fast.
        """
        row = dict(item or {})
        weak_title = str(row.get("title") or "").strip().lower() in _PLACEHOLDER_TITLES or str(row.get("title") or "").startswith("Unknown collection")
        if not weak_title and row.get("thumb"):
            return row
        rating_key = str(row.get("ratingKey") or "").strip()
        if not rating_key:
            return row
        try:
            root = await self._pms_xml(f"/library/metadata/{urllib.parse.quote(rating_key)}/children", params={"X-Plex-Container-Start": 0, "X-Plex-Container-Size": 3})
            node = next(iter(root.findall(".//Track")), None)
            if node is None:
                return row
            track = self._track(node)
            if weak_title:
                row["title"] = _meaningful_title(track.get("album"), track.get("title"), row.get("title"), fallback="Unknown collection")
            if not row.get("artist"):
                row["artist"] = str(track.get("artist") or "")
            if not row.get("thumb"):
                row["thumb"] = _first(track.get("parentThumb"), track.get("thumb"))
            return row
        except Exception as error:
            self._record("collection-enrich", error)
            return row

    # ------------------------------------------------------------------
    # Living Library cache / progressive Plex synchronization
    # ------------------------------------------------------------------
    def _catalog_identity(self) -> tuple[str, str]:
        server_id = str(self._server.machine_id or self._server.name or self._server.base_url or "server")
        return server_id, self._user_key()

    def _catalog_view_key(self, view: str, sort: str = "title") -> str:
        # 0.9.8 deliberately invalidates the 0.9.7 catalog cache. The previous
        # Music/Albums cache came from Plex's /albums directory-style endpoint
        # and could contain filesystem containers beside semantic Albums.
        return f"{CATALOG_CACHE_GENERATION}:{str(view or 'albums').lower()}:{str(sort or 'title').lower()}"

    def _cache_catalog_page(self, section: str, role: str, view: str, sort: str,
                            offset: int, items: list[dict[str, Any]], total: int,
                            complete: bool = False, error: str = "") -> None:
        if not self._db:
            return
        server_id, user_id = self._catalog_identity()
        view_key = self._catalog_view_key(view, sort)
        now = time.time()
        rows = []
        for i, item in enumerate(items or []):
            rating_key = str(item.get("ratingKey") or item.get("key") or f"row-{offset+i}")
            payload = self._index_media_item(dict(item), role, view)
            payload["libraryRole"] = role
            payload["sectionKey"] = str(section)
            rows.append((server_id, user_id, str(section), view_key, rating_key, int(offset+i), str(role),
                         json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                         _as_int(item.get("updatedAt")), now))
        if rows:
            # Replace the visible sort-index window atomically. Without this, a
            # resorted Plex library can leave an older rating key occupying the
            # same page position beside the new row, which makes stale metadata
            # and artwork appear to "belong" to the wrong card.
            self._db.execute(
                "DELETE FROM catalog_cache WHERE server_id=? AND user_id=? AND section_key=? AND view=? AND sort_index>=? AND sort_index<?",
                (server_id, user_id, str(section), view_key, int(offset), int(offset)+len(rows)),
            )
            self._db.executemany("""
                INSERT OR REPLACE INTO catalog_cache
                (server_id,user_id,section_key,view,rating_key,sort_index,role,payload,plex_updated_at,cached_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)
            """, rows)
        indexed = int(offset) + len(items or [])
        previous = self._db.execute(
            "SELECT indexed,complete FROM catalog_sync WHERE server_id=? AND user_id=? AND section_key=? AND view=?",
            (server_id, user_id, str(section), view_key),
        ).fetchone()
        indexed = max(indexed, int(previous["indexed"] if previous else 0))
        complete_flag = 1 if complete else int(previous["complete"] if previous else 0)
        self._db.execute("""
            INSERT OR REPLACE INTO catalog_sync
            (server_id,user_id,section_key,view,total,indexed,complete,last_error,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?)
        """, (server_id, user_id, str(section), view_key, max(0, int(total)), indexed,
              complete_flag, str(error or "")[:500], now))
        if complete and total >= 0:
            self._db.execute("""
                DELETE FROM catalog_cache WHERE server_id=? AND user_id=? AND section_key=? AND view=? AND sort_index>=?
            """, (server_id, user_id, str(section), view_key, int(total)))
        self._db.commit()

    def _read_catalog_cache(self, section: str, view: str, sort: str, offset: int, limit: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        if not self._db:
            return [], {}
        server_id, user_id = self._catalog_identity()
        view_key = self._catalog_view_key(view, sort)
        rows = self._db.execute("""
            SELECT payload FROM catalog_cache
            WHERE server_id=? AND user_id=? AND section_key=? AND view=? AND sort_index>=?
            ORDER BY sort_index ASC LIMIT ?
        """, (server_id, user_id, str(section), view_key, max(0, int(offset)), max(1, int(limit)))).fetchall()
        items = []
        for row in rows:
            try:
                items.append(json.loads(row["payload"]))
            except Exception:
                pass
        state_row = self._db.execute("""
            SELECT total,indexed,complete,last_error,updated_at FROM catalog_sync
            WHERE server_id=? AND user_id=? AND section_key=? AND view=?
        """, (server_id, user_id, str(section), view_key)).fetchone()
        return items, dict(state_row) if state_row else {}

    async def _sync_catalog_worker(self, section: str, role: str, view: str, sort: str, start: int = 0):
        task_key = f"{self._catalog_identity()[0]}:{self._user_key()}:{section}:{view}:{sort}"
        offset = max(0, int(start))
        page_size = 40
        try:
            while True:
                result = await self.browse_section(section, view, "", offset, page_size, sort, role)
                if not result.get("success"):
                    self._cache_catalog_page(section, role, view, sort, offset, [], int(result.get("total") or 0), False, str(result.get("message") or "Plex sync failed"))
                    break
                items = list(result.get("items") or [])
                total = int(result.get("total") or 0)
                has_more = bool(result.get("hasMore"))
                self._cache_catalog_page(section, role, view, sort, offset, items, total, not has_more)
                # Prime artwork metadata without fetching all image bytes up front.
                for item in items[:12]:
                    thumb = str(item.get("thumb") or item.get("parentThumb") or "")
                    if thumb:
                        self._remember_art_source(thumb, "portrait" if role == "audiobooks" else "square")
                if not has_more or not items:
                    break
                offset += len(items)
                # DS418-friendly pacing: never turn background indexing into a NAS benchmark.
                await asyncio.sleep(0.28)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            self._record("catalog-sync", error)
            self._cache_catalog_page(section, role, view, sort, offset, [], 0, False, self._sanitize(str(error)))
        finally:
            self._sync_tasks.pop(task_key, None)

    def _schedule_catalog_sync(self, section: str, role: str, view: str, sort: str, start: int = 0) -> None:
        task_key = f"{self._catalog_identity()[0]}:{self._user_key()}:{section}:{view}:{sort}"
        current = self._sync_tasks.get(task_key)
        if current and not current.done():
            return
        try:
            self._sync_tasks[task_key] = asyncio.create_task(self._sync_catalog_worker(section, role, view, sort, start))
        except Exception as error:
            self._record("catalog-sync-schedule", error)

    def _restore_ready_art_for_item(self, item: dict[str, Any], role: str, mode: str) -> dict[str, Any]:
        """Reattach persistent artwork cache state to a catalog row.

        The Artwork Registry is intentionally in-memory, while the actual image
        cache and canonical candidate index are persistent. A QAM reopen or
        Decky reload must therefore be able to reconstruct READY state without
        redownloading the library or waiting for a new hydration pass.
        """
        if not isinstance(item, dict):
            return item
        rating_key = str(item.get("ratingKey") or item.get("key") or "")
        if not rating_key:
            return item
        role = str(role or item.get("libraryRole") or "").lower()
        mode = str(mode or ("portrait-book-v85" if role == "audiobooks" else "square-card")).lower()
        path = _first(item.get("thumb"), item.get("parentThumb"), item.get("grandparentThumb"), item.get("art"))
        identity = self._art_registry_identity(str(path or ""), rating_key, role, mode)

        existing = dict(self._art_registry.get(identity) or {})
        # A Plex artwork edit can retain the same album ratingKey while changing
        # the versioned thumb path. Do not glue an old READY Music cover back onto
        # a freshly scanned catalog row whose current source hint has changed.
        if role == "music" and path and str(existing.get("sourceHint") or "") and str(existing.get("sourceHint")) != str(path):
            existing = {}
        if existing.get("state") == "ready":
            key = str(existing.get("cacheKey") or "")
            ready = self._art_registry_ready_record(
                identity, key, role, mode, rating_key,
                str(item.get("title") or ""), str(existing.get("resolvedPath") or ""),
                str(path or ""), int(existing.get("candidateCount") or 0),
            ) if key else None
            if ready:
                item["cachedArtUrl"] = str(ready.get("url") or "")
                item["artRegistryState"] = "ready"
                item["artRegistryIdentity"] = identity
                return item

        if not self._db:
            return item
        try:
            server_id, user_id = self._catalog_identity()
            row = self._db.execute(
                """SELECT candidates,selected_path FROM canonical_art
                   WHERE server_id=? AND user_id=? AND rating_key=? AND role=?
                   ORDER BY CASE WHEN mode=? THEN 0 WHEN mode='resolved-v5' THEN 1 ELSE 2 END, updated_at DESC
                   LIMIT 1""",
                (server_id, user_id, rating_key, role, mode),
            ).fetchone()
            if not row:
                return item
            candidates = json.loads(row["candidates"] or "[]")
            candidates = [str(x) for x in candidates if str(x or "").strip()]
            if not candidates:
                return item
            if role == "music" and path and str(path) not in candidates:
                # Same semantic album, new Plex artwork version. Let hydration
                # resolve the new candidates instead of resurrecting the old file.
                return item
            key = self._remember_art_candidates(
                candidates, mode=mode, identity=f"{rating_key}|{role or 'auto'}", role=role
            )
            if not key:
                return item
            ready = self._art_registry_ready_record(
                identity, key, role, mode, rating_key, str(item.get("title") or ""),
                str(row["selected_path"] or candidates[0]), str(path or ""), len(candidates),
            )
            if ready:
                item["cachedArtUrl"] = str(ready.get("url") or "")
                item["artRegistryState"] = "ready"
                item["artRegistryIdentity"] = identity
        except Exception as error:
            self._record("artwork-restore-ready", error)
        return item

    async def browse_cached(self, role: str, view: str = "albums", offset: int = 0, limit: int = 40,
                            sort: str = "title", refresh: bool = False, section_key: str = ""):
        """Fast catalog API: SQLite first, Plex only for cache misses/stale refreshes.

        The visible page is always prioritized. Once it is available, the rest of
        that view continues indexing in the background so returning to the page is
        progressively faster without blocking the UI on the NAS.
        """
        section, mapping_source, section_title = await self._resolve_section_for_role(role)
        if role == "music" and str(section_key or "").strip():
            libraries = (await self.get_libraries()).get("libraries", [])
            selected = next((lib for lib in libraries if str(lib.get("key")) == str(section_key)
                and (lib.get("role") == "music" or (lib.get("role") == "unassigned" and lib.get("suggestedRole") == "music"))), None)
            if not selected:
                return {"success": False, "items": [], "message": "That Plex music library is not available"}
            section, mapping_source, section_title = str(selected["key"]), "selected", str(selected.get("title") or "")
        if not section:
            return {"success": False, "items": [], "message": f"No {role} library is available", "mappingSource": mapping_source}
        start = max(0, int(offset)); size = max(1, min(100, int(limit)))
        cached, state = self._read_catalog_cache(section, view, sort, start, size)
        enough = len(cached) >= size or (state.get("complete") and start + len(cached) >= int(state.get("total") or 0))
        stale = not state or (time.time() - float(state.get("updated_at") or 0) > 20 * 60)
        network_result = None
        if refresh or not enough or (start == 0 and stale):
            network_result = await self.browse_section(section, view, "", start, size, sort, role)
            if network_result.get("success"):
                rows = list(network_result.get("items") or [])
                self._cache_catalog_page(section, role, view, sort, start, rows, int(network_result.get("total") or len(rows)), not bool(network_result.get("hasMore")))
                cached, state = self._read_catalog_cache(section, view, sort, start, size)
            elif not cached:
                return {**network_result, "mappingSource": mapping_source, "sectionTitle": section_title, "cached": False}
        total = int(state.get("total") or (network_result or {}).get("total") or len(cached))
        indexed = int(state.get("indexed") or len(cached))
        complete = bool(state.get("complete"))
        if not complete:
            self._schedule_catalog_sync(section, role, view, sort, max(indexed, start + len(cached)))
        # 0.9.8 safety gate: Music/Albums is sourced from Plex type=9, then
        # additionally rejects any raw Directory/container object that still
        # leaks through. No title/path heuristic is used and descendants are
        # untouched because Tracks/Artists come from their own semantic APIs.
        if str(role).lower() == "music" and str(view).lower() == "albums" and complete:
            all_rows, _display_state = self._read_catalog_cache(section, view, sort, 0, max(1, int(state.get("total") or total or 1)))
            logical_rows = [dict(row) for row in all_rows if self._is_semantic_music_album(dict(row))]
            cached = logical_rows[start:start + size]
            total = len(logical_rows)
            indexed = total
            complete = True
        art_mode = "portrait-book-v85" if str(role).lower() == "audiobooks" else "square-card"
        cached = [self._restore_ready_art_for_item(dict(item), role, art_mode) for item in cached]
        return {
            "success": True, "items": cached, "total": total, "offset": start, "limit": size,
            "hasMore": start + len(cached) < total, "indexed": indexed, "complete": complete,
            "syncing": not complete, "lastError": str(state.get("last_error") or ""),
            "section": section, "sectionTitle": section_title, "role": role, "view": view,
            "mappingSource": mapping_source, "cached": bool(cached and network_result is None),
        }

    async def get_sync_status(self):
        if not self._db:
            return {"success": True, "views": []}
        server_id, user_id = self._catalog_identity()
        rows = self._db.execute("""
            SELECT section_key,view,total,indexed,complete,last_error,updated_at
            FROM catalog_sync WHERE server_id=? AND user_id=? ORDER BY updated_at DESC
        """, (server_id, user_id)).fetchall()
        return {"success": True, "views": [dict(r) for r in rows], "active": len([t for t in self._sync_tasks.values() if t and not t.done()])}

    async def refresh_library_cache(self, role: str, view: str = "albums"):
        section, _source, _title = await self._resolve_section_for_role(role)
        if not section:
            return {"success": False, "message": f"No {role} library is available"}
        sort = "title"
        server_id, user_id = self._catalog_identity()
        if self._db:
            key = self._catalog_view_key(view, sort)
            self._db.execute("DELETE FROM catalog_cache WHERE server_id=? AND user_id=? AND section_key=? AND view=?", (server_id,user_id,section,key))
            self._db.execute("DELETE FROM catalog_sync WHERE server_id=? AND user_id=? AND section_key=? AND view=?", (server_id,user_id,section,key))
            self._db.commit()
        result = await self.browse_cached(role, view, 0, 40, sort, True)
        return {"success": bool(result.get("success")), "message": result.get("message", "Refresh started"), "result": result}

    async def _music_section_revision(self) -> dict[str, Any]:
        section, _source, title = await self._resolve_section_for_role("music")
        if not section:
            return {"success": False, "section": "", "revision": "", "title": title, "message": "No music library is available"}
        try:
            root = await self._pms_xml("/library/sections")
            node = next((n for n in root.findall(".//Directory") if str(n.attrib.get("key") or "") == str(section)), None)
            revision = ""
            if node is not None:
                revision = ":".join([str(node.attrib.get("updatedAt") or ""), str(node.attrib.get("scannedAt") or ""), str(node.attrib.get("contentChangedAt") or "")])
                title = str(node.attrib.get("title") or title or "Music")
            return {"success": True, "section": str(section), "revision": revision, "title": title or "Music"}
        except Exception as error:
            self._record("music-section-revision", error)
            return {"success": False, "section": str(section), "revision": "", "title": title or "Music", "message": self._sanitize(str(error))}

    async def refresh_music_state(self, force: bool = False):
        """Refresh semantic Music catalog/media identities and artwork after Plex changes.

        A cheap section revision check makes normal calls effectively free. Forced calls
        are used by the manager button and stale-track recovery. The lock prevents QAM
        and Full Manager from launching duplicate rescans at the same time.
        """
        async with self._music_refresh_lock:
            rev = await self._music_section_revision()
            if not rev.get("section"):
                return rev
            section = str(rev.get("section"))
            current = str(rev.get("revision") or "")
            key = f"musicLibraryRevision:{self._catalog_identity()[0]}:{self._user_key()}:{section}"
            previous = str(self._settings_get(key, "") or "")
            changed = bool(force or not previous or (current and current != previous))
            if not changed:
                return {"success": True, "changed": False, "section": section, "revision": current, "message": "Music library is current"}
            # Any Plex rescan can replace Part keys even when a ratingKey survives.
            prefix = f"{self._server.machine_id}:"
            self._media_source_cache = {k:v for k,v in self._media_source_cache.items() if not str(k).startswith(prefix)}
            if self._db:
                server_id, user_id = self._catalog_identity()
                self._db.execute("DELETE FROM catalog_cache WHERE server_id=? AND user_id=? AND section_key=? AND role='music'", (server_id,user_id,section))
                self._db.execute("DELETE FROM catalog_sync WHERE server_id=? AND user_id=? AND section_key=?", (server_id,user_id,section))
                self._db.commit()
            results = {}
            for view in ("albums","artists","tracks"):
                results[view] = await self.browse_cached("music", view, 0, 40, "title", True)
            self._settings_set(key, current or str(time.time()))
            # Valid READY files are reused. Missing/changed identities are reconsidered.
            await self.start_artwork_hydration(False, True)
            counts = {}
            try:
                inspected = await self.inspect_library(section)
                counts = dict((inspected.get("library") or {}).get("counts") or {}) if inspected.get("success") else {}
            except Exception:
                pass
            return {"success": True, "changed": True, "section": section, "revision": current, "counts": counts, "message": "Music library and artwork refresh started", "views": {k: bool(v.get("success")) for k,v in results.items()}}

    async def resolve_fresh_track(self, rating_key: str, title: str = "", artist: str = "", album: str = ""):
        """Resolve a Music track after Plex metadata/file changes.

        A remove/re-add may preserve the visible title while replacing either the
        ratingKey or the Media/Part key. Verify the actual current Part with a
        one-byte range request before reusing it, then fall back to semantic track
        search. This endpoint runs only after a playback-source failure.
        """
        old_key = str(rating_key or "").strip()

        async def reachable(key: str) -> tuple[bool, dict[str, Any] | None]:
            key = str(key or "").strip()
            if not key or not self._session:
                return False, None
            try:
                source = await self._media_source(key, refresh=True)
                headers = self._plex_headers(str(source.get("token") or ""), json_accept=False)
                headers["Range"] = "bytes=0-0"
                async with self._session.request(
                    "GET", str(source.get("url") or ""), headers=headers, ssl=self.ssl_context,
                    timeout=aiohttp.ClientTimeout(total=6, connect=3, sock_read=4),
                ) as response:
                    # 200 is valid for servers/sources that ignore Range; 206 is
                    # the normal bounded response. Do not consume the whole body.
                    if int(response.status) >= 400:
                        return False, source
                    await response.content.read(1)
                    return True, source
            except Exception:
                return False, None

        if old_key:
            self._media_source_cache.pop(f"{self._server.machine_id}:{old_key}", None)
            ok, _source = await reachable(old_key)
            if ok:
                try:
                    meta = await self.get_metadata(old_key)
                    if meta.get("success") and str((meta.get("item") or {}).get("type") or "") == "track":
                        item = dict(meta.get("item") or {})
                        item["libraryRole"] = "music"
                        return {"success": True, "item": item, "replaced": False, "verifiedPart": True}
                except Exception:
                    pass

        section, _source, _section_title = await self._resolve_section_for_role("music")
        if not section:
            return {"success": False, "message": "Music library is unavailable"}

        def norm(v):
            return " ".join(str(v or "").strip().lower().split())
        want_t, want_a, want_al = norm(title), norm(artist), norm(album)

        def score(x):
            st = 100 if want_t and norm(x.get("title")) == want_t else 0
            if want_a and norm(x.get("artist")) == want_a:
                st += 20
            if want_al and norm(x.get("album")) == want_al:
                st += 10
            if old_key and str(x.get("ratingKey") or "") == old_key:
                st += 5
            return st

        try:
            async def query(params: dict[str, Any]) -> list[dict[str, Any]]:
                root = await self._pms_xml(
                    f"/library/sections/{urllib.parse.quote(str(section))}/all", params=params
                )
                return [self._track(n) for n in root.findall(".//Track")]

            params = {"type": 10, "X-Plex-Container-Start": 0, "X-Plex-Container-Size": 160}
            if title:
                params["title"] = str(title)
            rows = await query(params)
            rows.sort(key=score, reverse=True)
            # Some PMS builds do not honor title filtering consistently. A stale
            # track is exceptional, so an exhaustive semantic fallback is worth
            # the extra request and is much safer than guessing a filesystem path.
            if not rows or score(rows[0]) < (100 if want_t else 1):
                rows = await query({"type": 10, "X-Plex-Container-Start": 0, "X-Plex-Container-Size": 5000})
                rows.sort(key=score, reverse=True)
            candidates = [x for x in rows if score(x) >= (100 if want_t else 1)][:12]
            for candidate in candidates:
                key = str(candidate.get("ratingKey") or "")
                ok, _source = await reachable(key)
                if not ok:
                    continue
                item = dict(candidate)
                item["libraryRole"] = "music"
                self._media_source_cache.pop(f"{self._server.machine_id}:{key}", None)
                # Every surface should converge after a successful stale-item repair.
                try:
                    asyncio.create_task(self.refresh_music_state(True))
                except Exception:
                    pass
                return {
                    "success": True, "item": item,
                    "replaced": key != old_key, "verifiedPart": True,
                }
            return {"success": False, "message": "Plex no longer exposes a playable matching track"}
        except Exception as error:
            self._record("resolve-fresh-track", error)
            return {"success": False, "message": self._sanitize(str(error))}

    async def browse_section(self, section_key: str, view: str = "albums", query: str = "", offset: int = 0, limit: int = 36, sort: str = "title", role_hint: str = ""):
        """Browse one Plex audio section directly with real pagination.

        This is the catalog primitive used by the full-screen manager. It never
        caps a library to a decorative sample set. Albums/books are unique
        top-level Directory items; tracks/chapters only appear in their own view
        or after opening a parent item.
        """
        section = str(section_key or "").strip()
        if not section:
            return {"success": False, "items": [], "message": "Missing Plex library section"}
        try:
            size = max(1, min(120, int(limit)))
            start = max(0, int(offset))
            view = str(view or "albums").lower()
            sort_key = str(sort or "title").lower()
            sort_value = sort if ":" in str(sort) else ("addedAt:desc" if sort_key in ("newest", "recent", "added") else "titleSort:asc")
            params: dict[str, Any] = {"X-Plex-Container-Start": start, "X-Plex-Container-Size": size, "sort": sort_value}
            if query:
                params["title"] = str(query)

            semantic_role = str(role_hint or self._role(section) or "").lower()
            mapper = self._album
            path = f"/library/sections/{urllib.parse.quote(section)}/albums"
            node_tag = "Directory"
            if view in ("artists", "authors"):
                path = f"/library/sections/{urllib.parse.quote(section)}/all"
                params["type"] = 8
                mapper = self._artist
            elif view in ("tracks", "chapters", "recently_played"):
                path = f"/library/sections/{urllib.parse.quote(section)}/all"
                params["type"] = 10
                if view == "recently_played":
                    params["sort"] = "lastViewedAt:desc"
                mapper = self._track
                node_tag = "Track"
            elif view == "collections":
                path = f"/library/sections/{urllib.parse.quote(section)}/collections"
                mapper = self._collection
            elif view in ("albums", "books", "home", "recently_added"):
                # Music Albums must come from Plex's semantic type=9 catalog,
                # never the filesystem/folder-oriented /albums hierarchy.
                if view == "albums" and semantic_role == "music":
                    path = f"/library/sections/{urllib.parse.quote(section)}/all"
                    params["type"] = 9
                elif view in ("home", "recently_added"):
                    params["sort"] = "addedAt:desc"
            else:
                path = f"/library/sections/{urllib.parse.quote(section)}/all"
                params["type"] = 9

            root = await self._pms_xml(path, params=params)
            nodes = root.findall(f".//{node_tag}")
            if mapper == self._track and not nodes:
                nodes = root.findall(".//Video")
            items = [mapper(n) for n in nodes]
            if mapper == self._album and items:
                weak_indexes = [i for i,row in enumerate(items[:24]) if (not row.get("thumb") or str(row.get("title") or "").strip().lower() in _PLACEHOLDER_TITLES or str(row.get("title") or "").startswith("Unknown collection"))]
                if weak_indexes:
                    enriched = await asyncio.gather(*(self._enrich_collection_item(items[i]) for i in weak_indexes))
                    for i,row in zip(weak_indexes,enriched):
                        items[i]=row
            total = _as_int(root.attrib.get("totalSize"), -1)
            if total < 0:
                total = _as_int(root.attrib.get("size"), len(items))
            returned_offset = _as_int(root.attrib.get("offset"), start)
            has_more = returned_offset + len(items) < total
            return {"success": True, "items": items, "total": total, "offset": returned_offset, "limit": size, "hasMore": has_more, "section": section, "view": view, "semanticRole": semantic_role}
        except Exception as error:
            self._record("browse-section", error)
            return {"success": False, "items": [], "message": self._sanitize(str(error)), "section": section, "view": view}

    async def browse_library(self, role: str, view: str = "home", query: str = "", offset: int = 0, limit: int = 60):
        section, mapping_source, section_title = await self._resolve_section_for_role(role)
        if not section:
            return {"success": False, "items": [], "message": f"Confirm a {role} library in Library Manager first", "mappingSource": mapping_source}
        try:
            size = max(1, min(200, int(limit)))
            start = max(0, int(offset))
            params: dict[str, Any] = {"X-Plex-Container-Start": start, "X-Plex-Container-Size": size}
            if view in ("artists", "authors"):
                path = f"/library/sections/{section}/all"; params.update({"type": 8, "sort": "titleSort:asc"}); mapper = self._artist
            elif view in ("albums", "books", "recently_added"):
                if role == "music" and view == "albums":
                    path = f"/library/sections/{section}/all"; params.update({"type": 9, "sort": "titleSort:asc"}); mapper = self._album
                else:
                    path = f"/library/sections/{section}/albums"; params.update({"sort": "addedAt:desc" if view == "recently_added" else "titleSort:asc"}); mapper = self._album
            elif view in ("tracks", "chapters"):
                path = f"/library/sections/{section}/all"; params.update({"type": 10, "sort": "titleSort:asc"}); mapper = self._track
            elif view == "recently_played":
                path = f"/library/sections/{section}/all"; params.update({"type": 10, "sort": "lastViewedAt:desc"}); mapper = self._track
            else:
                path = f"/library/sections/{section}/all"; params.update({"type": 9, "sort": "addedAt:desc"}); mapper = self._album
            if query:
                params["title"] = query
            root = await self._pms_xml(path, params=params)
            nodes = root.findall(".//Directory") if mapper != self._track else root.findall(".//Track")
            if mapper == self._track and not nodes:
                nodes = root.findall(".//Video")
            items = [mapper(n) for n in nodes]
            if role == "music" and view == "albums":
                items = [row for row in items if self._is_semantic_music_album(row)]
            if mapper == self._album and items:
                # Only rows with missing/placeholder metadata need child reads.
                weak_indexes = [i for i, row in enumerate(items[:24]) if (not row.get("thumb") or str(row.get("title") or "").strip().lower() in _PLACEHOLDER_TITLES or str(row.get("title") or "").startswith("Unknown collection"))]
                if weak_indexes:
                    enriched = await asyncio.gather(*(self._enrich_collection_item(items[i]) for i in weak_indexes))
                    for i, row in zip(weak_indexes, enriched):
                        items[i] = row
            total = _as_int(root.attrib.get("totalSize") or root.attrib.get("size"), len(items))
            return {"success": True, "items": items, "total": total, "section": section, "sectionTitle": section_title, "role": role, "view": view, "mappingSource": mapping_source}
        except Exception as error:
            self._record("browse", error)
            return {"success": False, "items": [], "message": self._sanitize(str(error))}

    async def get_continue_listening(self, role: str = "audiobooks", limit: int = 12):
        """Return distinct parent books/albums with in-progress Plex tracks.

        Plex stores long-form progress primarily on track items. ResonaDeck
        groups those tracks by parentRatingKey so the UI can present one book
        card per story instead of one card per chapter/file.
        """
        section, mapping_source, section_title = await self._resolve_section_for_role(role)
        if not section:
            return {"success": False, "items": [], "message": f"No {role} library is available", "mappingSource": mapping_source}
        try:
            wanted = max(1, min(200, int(limit)))
            root = await self._pms_xml(
                f"/library/sections/{section}/all",
                params={"type": 10, "sort": "lastViewedAt:desc", "X-Plex-Container-Start": 0, "X-Plex-Container-Size": 300},
            )
            tracks = [self._track(n) for n in root.findall(".//Track")]
            candidates = []
            seen = set()
            for track in tracks:
                offset = _as_int(track.get("viewOffset"))
                duration_ms = int(float(track.get("duration") or 0) * 1000)
                parent = str(track.get("parentRatingKey") or "")
                if not parent or parent in seen or offset <= 0:
                    continue
                if duration_ms > 0 and offset >= max(0, duration_ms - 5000):
                    continue
                seen.add(parent)
                candidates.append((parent, track))
                if len(candidates) >= wanted:
                    break

            async def parent_item(parent_key: str, track: dict[str, Any]):
                try:
                    meta = await self.get_metadata(parent_key)
                    item = dict(meta.get("item") or {}) if meta.get("success") else {}
                except Exception:
                    item = {}
                if not item:
                    item = {
                        "ratingKey": parent_key,
                        "title": _meaningful_title(track.get("album"), track.get("title"), fallback="Audiobook"),
                        "artist": str(track.get("artist") or ""),
                        "thumb": _first(track.get("parentThumb"), track.get("thumb")),
                    }
                item["resumeTrackRatingKey"] = str(track.get("ratingKey") or "")
                item["resumeOffsetMs"] = _as_int(track.get("viewOffset"))
                item["resumeTrackDurationMs"] = int(float(track.get("duration") or 0) * 1000)
                item["lastViewedAt"] = _as_int(track.get("lastViewedAt"))
                return item

            items = await asyncio.gather(*(parent_item(parent, track) for parent, track in candidates)) if candidates else []
            return {"success": True, "items": items, "section": section, "sectionTitle": section_title, "mappingSource": mapping_source}
        except Exception as error:
            self._record("continue-listening", error)
            return {"success": False, "items": [], "message": self._sanitize(str(error))}

    async def get_children(self, rating_key: str):
        try:
            root = await self._pms_xml(f"/library/metadata/{urllib.parse.quote(str(rating_key))}/children",
                                       params={"X-Plex-Container-Size": 1000})
            tracks = [self._track(n) for n in root.findall(".//Track")]
            dirs = [self._album(n) for n in root.findall(".//Directory")]
            return {"success": True, "tracks": tracks, "items": dirs}
        except Exception as error:
            self._record("children", error)
            return {"success": False, "tracks": [], "items": [], "message": self._sanitize(str(error))}

    async def get_artist_tracks(self, rating_key: str):
        """Return every playable track belonging to an Artist, independent of folder layout.

        Plex /allLeaves is normally sufficient, but hardware testing showed that
        a track stored in a separate filesystem branch can be omitted even while
        it carries the same semantic artist metadata. 0.9.10 therefore unions
        allLeaves with the Music section's semantic Track objects and matches by
        artist rating key first, then exact normalized artist title.
        """
        key = str(rating_key or "").strip()
        if not key:
            return {"success": False, "tracks": [], "message": "Missing artist rating key"}

        def norm(value: Any) -> str:
            return " ".join(str(value or "").casefold().split())

        artist_title = ""
        try:
            meta = await self.get_metadata(key)
            if meta.get("success"):
                artist_title = str((meta.get("item") or {}).get("title") or "")
        except Exception:
            artist_title = ""

        candidates: list[dict[str, Any]] = []
        try:
            leaves = await self._pms_xml(
                f"/library/metadata/{urllib.parse.quote(key)}/allLeaves",
                params={
                    "X-Plex-Container-Start": 0,
                    "X-Plex-Container-Size": 5000,
                    "sort": "parentIndex:asc,index:asc,titleSort:asc",
                },
            )
            candidates.extend(self._track(n) for n in leaves.findall(".//Track"))
        except Exception as error:
            self._record("artist-tracks-allleaves", error)

        try:
            section, _, _ = await self._resolve_section_for_role("music")
            if section:
                section_root = await self._pms_xml(
                    f"/library/sections/{section}/all",
                    params={
                        "type": 10,
                        "X-Plex-Container-Start": 0,
                        "X-Plex-Container-Size": 20000,
                        "sort": "parentIndex:asc,index:asc,titleSort:asc",
                    },
                )
                wanted_title = norm(artist_title)
                for node in section_root.findall(".//Track"):
                    track = self._track(node)
                    same_key = str(track.get("grandparentRatingKey") or "") == key
                    same_title = bool(wanted_title and norm(track.get("artist")) == wanted_title)
                    if same_key or same_title:
                        candidates.append(track)
        except Exception as error:
            self._record("artist-tracks-section", error)

        # Last compatibility fallback for unusual PMS builds.
        if not candidates:
            try:
                children = await self.get_children(key)
                albums = list(children.get("items") or [])
                groups = await asyncio.gather(*(
                    self.get_children(str(a.get("ratingKey") or ""))
                    for a in albums if a.get("ratingKey")
                ))
                for group in groups:
                    candidates.extend(group.get("tracks") or [])
            except Exception as error:
                self._record("artist-tracks-children", error)

        seen, tracks = set(), []
        for track in candidates:
            ident = str(track.get("ratingKey") or track.get("partKey") or track.get("file") or "")
            if not ident or ident in seen:
                continue
            seen.add(ident)
            track["libraryRole"] = "music"
            tracks.append(track)
        tracks.sort(key=lambda t: (
            str(t.get("album") or "").casefold(),
            int(t.get("index") or 0),
            str(t.get("title") or "").casefold(),
        ))
        return {
            "success": True,
            "tracks": tracks,
            "artistRatingKey": key,
            "artistTitle": artist_title,
            "count": len(tracks),
        }

    async def get_metadata(self, rating_key: str):
        try:
            root = await self._pms_xml(f"/library/metadata/{urllib.parse.quote(str(rating_key))}")
            node = root.children[0] if getattr(root, "children", None) else None
            if node is None:
                return {"success": False, "message": "Plex metadata was empty"}
            if node.tag.lower() in ("track", "video"):
                item = self._track(node); typ = "track"
            elif node.attrib.get("type") == "artist":
                item = self._artist(node); typ = "artist"
            else:
                item = self._album(node); typ = node.attrib.get("type", "album")
            item["summary"] = str(node.attrib.get("summary") or item.get("summary") or "")
            item["type"] = typ
            return {"success": True, "item": item}
        except Exception as error:
            self._record("metadata", error)
            return {"success": False, "message": self._sanitize(str(error))}

    async def get_genres(self, role: str = "music"):
        section, mapping_source, section_title = await self._resolve_section_for_role(role)
        if not section:
            return {"success": False, "genres": [], "message": f"Confirm a {role} library first", "mappingSource": mapping_source}
        try:
            root = await self._pms_xml(f"/library/sections/{section}/genre", params={"type": 10, "X-Plex-Container-Size": 500})
            genres = []
            for n in root.findall(".//Directory"):
                genres.append({"key": str(n.attrib.get("key") or n.attrib.get("id") or ""), "title": str(n.attrib.get("title") or "Genre")})
            return {"success": True, "genres": genres, "section": section, "sectionTitle": section_title, "mappingSource": mapping_source}
        except Exception as error:
            self._record("genres", error)
            return {"success": False, "genres": [], "message": self._sanitize(str(error))}

    async def get_genre_tracks(self, genre_key: str, role: str = "music"):
        section, mapping_source, section_title = await self._resolve_section_for_role(role)
        if not section:
            return {"success": False, "tracks": [], "message": f"Confirm a {role} library first", "mappingSource": mapping_source}
        try:
            # Plex agents may attach genre at track, album, or artist level.
            # Try the direct track relation first, then relational fallbacks.
            for relation in ("genre", "album.genre", "artist.genre"):
                root = await self._pms_xml(
                    f"/library/sections/{section}/all",
                    params={"type": 10, relation: str(genre_key), "X-Plex-Container-Size": 1000},
                )
                tracks = [self._track(n) for n in root.findall(".//Track")]
                if tracks:
                    return {"success": True, "tracks": tracks}
            return {"success": True, "tracks": []}
        except Exception as error:
            self._record("genre-tracks", error)
            return {"success": False, "tracks": [], "message": self._sanitize(str(error))}

    async def get_playlists(self):
        try:
            root = await self._pms_xml("/playlists", params={"playlistType": "audio", "X-Plex-Container-Size": 200})
            out = []
            for n in root.findall(".//Playlist"):
                a = n.attrib
                out.append({"ratingKey": str(a.get("ratingKey") or a.get("key") or ""), "title": str(a.get("title") or "Playlist"),
                            "thumb": _first(a.get("thumb"), a.get("composite")), "leafCount": _as_int(a.get("leafCount")),
                            "duration": _as_int(a.get("duration")) / 1000.0})
            return {"success": True, "playlists": out}
        except Exception as error:
            self._record("playlists", error)
            return {"success": False, "playlists": [], "message": self._sanitize(str(error))}

    async def get_playlist_items(self, rating_key: str):
        try:
            root = await self._pms_xml(f"/playlists/{urllib.parse.quote(str(rating_key))}/items", params={"X-Plex-Container-Size": 2000})
            return {"success": True, "tracks": [self._track(n) for n in root.findall(".//Track")]}
        except Exception as error:
            self._record("playlist-items", error)
            return {"success": False, "tracks": [], "message": self._sanitize(str(error))}

    async def search_cached(self, query: str, scope: str = "everything", limit: int = 80):
        """Search the already-indexed Living Library before waking Plex."""
        q = str(query or "").strip()
        if not q or not self._db:
            return {"success": True, "artists": [], "albums": [], "tracks": [], "cached": True}
        roles = ["music", "audiobooks", "podcasts", "other"] if scope == "everything" else ([scope] if scope in ("music", "audiobooks", "podcasts", "other") else ["music", "audiobooks", "podcasts", "other"])
        server_id = self._catalog_identity()[0]
        user_id = self._user_key()
        needle = f"%{q.lower()}%"
        cap = max(12, min(160, int(limit)))
        artists, albums, tracks, seen = [], [], [], set()
        try:
            placeholders = ','.join('?' for _ in roles)
            sql = f"SELECT role, view, payload FROM catalog_cache WHERE server_id=? AND user_id=? AND role IN ({placeholders}) AND lower(payload) LIKE ? ORDER BY cached_at DESC LIMIT ?"
            rows = self._db.execute(sql, (server_id, user_id, *roles, needle, cap * 4)).fetchall()
            for row in rows:
                try:
                    item = json.loads(row["payload"])
                    role = str(row["role"] or "")
                    view = str(row["view"] or "").split(":", 1)[0]
                except Exception:
                    continue
                key = (role, str(item.get("ratingKey") or item.get("key") or ""), str(item.get("title") or ""))
                if key in seen:
                    continue
                seen.add(key)
                item["libraryRole"] = role
                if view in ("artists", "authors"):
                    artists.append(item)
                elif view in ("tracks", "chapters", "recently_played"):
                    tracks.append(item)
                else:
                    albums.append(item)
                if len(artists) + len(albums) + len(tracks) >= cap:
                    break
            return {"success": True, "artists": artists[:cap], "albums": albums[:cap], "tracks": tracks[:cap], "cached": True}
        except Exception as error:
            self._record("search-cache", error)
            return {"success": False, "artists": [], "albums": [], "tracks": [], "cached": True, "message": self._sanitize(str(error))}

    async def search(self, query: str, scope: str = "everything"):
        query = str(query or "").strip()
        if not query:
            return {"success": True, "artists": [], "albums": [], "tracks": []}
        try:
            # Section-scoped search avoids audiobook/music crossover.
            roles = ["music", "audiobooks", "podcasts", "other"] if scope == "everything" else ([scope] if scope in ("music", "audiobooks", "podcasts", "other") else ["music", "audiobooks", "podcasts", "other"])
            artists: list[dict[str, Any]] = []; albums: list[dict[str, Any]] = []; tracks: list[dict[str, Any]] = []
            for role in roles:
                section, _mapping_source, _section_title = await self._resolve_section_for_role(role)
                if not section: continue
                for typ, target, mapper in ((8, artists, self._artist), (9, albums, self._album), (10, tracks, self._track)):
                    root = await self._pms_xml(f"/library/sections/{section}/all", params={"type": typ, "title": query, "X-Plex-Container-Size": 40})
                    nodes = root.findall(".//Track") if typ == 10 else root.findall(".//Directory")
                    for n in nodes:
                        item = mapper(n); item["libraryRole"] = role; target.append(item)
            return {"success": True, "artists": artists[:60], "albums": albums[:60], "tracks": tracks[:100]}
        except Exception as error:
            self._record("search", error)
            return {"success": False, "artists": [], "albums": [], "tracks": [], "message": self._sanitize(str(error))}

    # ------------------------------------------------------------------
    # Proxy / stream / artwork
    # ------------------------------------------------------------------
    async def _start_loopback(self):
        app = web.Application()
        app.router.add_route("GET", "/media/{token}/{sid}", self._proxy_media)
        app.router.add_route("HEAD", "/media/{token}/{sid}", self._proxy_media)
        app.router.add_route("GET", "/art/{token}/{sid}", self._proxy_art)
        app.router.add_route("GET", "/art-cache/{token}/{key}", self._serve_cached_art)
        self._runner = web.AppRunner(app, access_log=None)
        await self._runner.setup()
        ports = [self._port] if self._port else []
        ports += [0]
        last = None
        for p in ports:
            try:
                self._site = web.TCPSite(self._runner, "127.0.0.1", p)
                await self._site.start()
                sockets = getattr(self._site, "_server", None).sockets
                self._port = int(sockets[0].getsockname()[1]) if sockets else p
                self._save_loopback_state()
                return
            except Exception as e:
                last = e
        raise RuntimeError(f"Could not start loopback proxy: {last}")

    def _prune_proxy(self):
        cutoff = time.time() - PROXY_SESSION_TTL
        for sid in list(self._proxy_sources):
            if self._proxy_sources[sid].get("created", 0) < cutoff:
                self._proxy_sources.pop(sid, None)

    def _register_proxy(self, kind: str, url: str, token: str, content_type: str = "", allow_range: bool = True) -> str:
        self._prune_proxy()
        sid = secrets.token_urlsafe(14)
        self._proxy_sources[sid] = {"kind": kind, "url": url, "token": token, "contentType": content_type, "allowRange": bool(allow_range), "created": time.time()}
        return f"http://127.0.0.1:{self._port}/{kind}/{self._loop_token}/{sid}"

    async def _media_source(self, rating_key: str, refresh: bool = False) -> dict[str, Any]:
        cache_key = f"{self._server.machine_id}:{str(rating_key)}"
        cached = self._media_source_cache.get(cache_key)
        if not refresh and cached and time.time() - float(cached[0]) < 15 * 60:
            return dict(cached[1])
        root = await self._pms_xml(f"/library/metadata/{urllib.parse.quote(str(rating_key))}")
        node = root.children[0] if getattr(root, "children", None) else None
        if node is None:
            raise RuntimeError("Track metadata not found")
        media = node.find("Media")
        part = media.find("Part") if media is not None else None
        if part is None or not part.attrib.get("key"):
            raise RuntimeError("Plex did not expose a playable media part")
        part_key = str(part.attrib["key"])
        url = self._server.base_url.rstrip("/") + part_key
        result = {"url": url, "token": self._server.access_token, "partKey": part_key,
                "container": str(media.attrib.get("container") if media is not None else ""),
                "codec": str(media.attrib.get("audioCodec") if media is not None else ""),
                "bitrate": _as_int(media.attrib.get("bitrate") if media is not None else 0),
                "size": _as_int(part.attrib.get("size")), "file": str(part.attrib.get("file") or ""),
                "durationMs": _as_int(node.attrib.get("duration")), "updatedAt": _as_int(node.attrib.get("updatedAt"))}
        self._media_source_cache[cache_key] = (time.time(), dict(result))
        return result

    def _browser_can_direct_play(self, source: dict[str, Any], capabilities: dict[str, Any] | None) -> tuple[bool, str]:
        """Choose Direct Play only when the Steam/CEF frontend reported support.

        HTML media support varies with the Chromium build shipped by SteamOS.
        ResonaDeck therefore treats the frontend canPlayType() probe as the
        authoritative capability signal rather than assuming a file extension
        is safe. Unknown formats transcode up front instead of failing first.
        """
        caps = capabilities if isinstance(capabilities, dict) else {}
        container = str(source.get("container") or "").lower().lstrip(".")
        codec = str(source.get("codec") or "").lower()
        file_name = str(source.get("file") or "").lower()
        if not container and "." in file_name:
            container = file_name.rsplit(".", 1)[-1]
        names: list[str] = []
        if codec in ("mp3", "mpeg", "mpga") or container == "mp3": names = ["mp3"]
        elif codec in ("aac", "mp4a") or container in ("aac",): names = ["aac"]
        elif container in ("m4a", "mp4") and codec in ("aac", "mp4a", ""): names = ["m4a", "aac"]
        elif codec == "flac" or container == "flac": names = ["flac"]
        elif codec == "opus": names = ["opus"]
        elif codec in ("vorbis", "ogg") or container in ("ogg", "oga"): names = ["ogg"]
        elif codec in ("wav", "pcm", "pcm_s16le", "pcm_s24le") or container in ("wav", "wave"): names = ["wav"]
        elif codec == "alac": names = ["alac"]
        for name in names:
            value = caps.get(name)
            if value is True or str(value).lower() in ("maybe", "probably", "true", "1"):
                return True, f"Steam browser reports {name} support"
        if not caps and (codec in ("mp3", "aac", "mp4a") or container in ("mp3", "m4a", "mp4")):
            # Compatibility fallback for older frontend bundles that do not yet
            # pass a capability map. New 0.6 frontends always do.
            return True, "legacy common-format fallback"
        label = codec or container or "unknown format"
        return False, f"Steam browser did not report support for {label}"

    def _music_transcode_url(self, rating_key: str, bitrate: int = 320, offset_seconds: float = 0.0,
                             audio_boost: int = 100, normalize_loudness: bool = False) -> tuple[str, str]:
        session_id = str(uuid.uuid4())
        # Tell Plex exactly what the Deck browser target is. The Generic profile
        # plus an explicit music transcode target avoids the old behavior where
        # we handed Chromium an incompatible file and waited for MEDIA_ERR_SRC_NOT_SUPPORTED.
        profile_extra = "+".join([
            "add-transcode-target(type=musicProfile&context=streaming&protocol=http&container=mp3&audioCodec=mp3&replace=true)",
            "add-direct-play-profile(type=musicProfile&container=mp3&audioCodec=mp3)",
        ])
        params = {
            "path": f"/library/metadata/{rating_key}",
            "mediaIndex": 0,
            "partIndex": 0,
            "protocol": "http",
            "musicBitrate": max(96, min(320, int(bitrate or 320))),
            "audioBoost": max(50, min(200, int(audio_boost or 100))),
            "normalizeLoudness": 1 if normalize_loudness else 0,
            "offset": max(0.0, float(offset_seconds or 0.0)),
            "directPlay": 0,
            "directStream": 0,
            "transcodeSessionId": session_id,
            "X-Plex-Client-Identifier": self._client_id,
            "X-Plex-Session-Identifier": session_id,
            "X-Plex-Client-Profile-Name": "generic",
            "X-Plex-Client-Profile-Extra": profile_extra,
            "X-Plex-Product": PRODUCT,
            "X-Plex-Version": str(PLUGIN_VERSION),
            "X-Plex-Platform": "Chrome",
            "X-Plex-Device": DEVICE,
        }
        url = self._server.base_url.rstrip("/") + "/music/:/transcode/universal/start.mp3?" + urllib.parse.urlencode(params)
        return url, session_id

    async def _probe_music_transcode_decision(self, start_url: str, token: str) -> tuple[bool, str]:
        """Ask Plex whether a prepared audio transcode profile is acceptable.

        The universal transcoder can reject a start request on some PMS builds
        even though the same source is otherwise playable. 0.8.5 treats
        server-side loudness as optional: probe the matching decision endpoint
        before relying on an enhanced profile, then gracefully degrade.
        """
        try:
            parsed = urllib.parse.urlsplit(str(start_url or ""))
            if not parsed.scheme or not parsed.netloc:
                return False, "invalid transcode URL"
            path = parsed.path
            if "/start." in path:
                path = path[:path.rfind("/start.")] + "/decision"
            elif path.endswith("/start"):
                path = path[:-6] + "/decision"
            else:
                return False, "unsupported transcode start path"
            decision_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, ""))
            async with await self._request(
                "GET", decision_url, token=token,
                timeout=aiohttp.ClientTimeout(total=8), json_accept=True,
            ) as response:
                body = await response.text()
                if response.status >= 400:
                    return False, f"decision HTTP {response.status}"
                try:
                    payload = json.loads(body) if body.strip() else {}
                    container = payload.get("MediaContainer") if isinstance(payload, dict) else None
                    if isinstance(container, dict):
                        codes = [container.get("generalDecisionCode"), container.get("transcodeDecisionCode")]
                        for raw in codes:
                            try:
                                code = int(raw)
                            except Exception:
                                continue
                            if code >= 2000:
                                text = str(container.get("generalDecisionText") or container.get("transcodeDecisionText") or "Plex rejected transcode")
                                return False, self._sanitize(text)
                except Exception:
                    # A 200 response is sufficient if this PMS returned XML/text
                    # despite the JSON Accept header.
                    pass
                return True, "Plex transcode decision accepted"
        except Exception as error:
            self._record("transcode-decision", error)
            return False, self._sanitize(str(error))

    async def _select_music_transcode_profile(self, rating_key: str, source: dict[str, Any], offset_seconds: float,
                                              boost_percent: int, normalize_loudness: bool,
                                              preflight: bool = False) -> tuple[str, str, int, bool, bool, str]:
        """Choose the strongest Plex MP3 profile the current server accepts.

        Return (url, session_id, boost, normalize, decision_ready, note).
        A normal Direct Play plan does not preflight its dormant fallback. The
        recovery call does, keeping the A-button path fast while making the
        fallback materially more reliable when it is actually needed.
        """
        variants: list[tuple[int, bool, str]] = []
        requested_boost = max(100, min(200, int(boost_percent or 100)))
        requested_norm = bool(normalize_loudness)
        variants.append((requested_boost, requested_norm, "requested"))
        if requested_norm:
            variants.append((requested_boost, False, "boost-only"))
        if requested_boost != 100:
            variants.append((100, False, "plain-mp3"))
        dedup: list[tuple[int, bool, str]] = []
        seen = set()
        for boost, norm, label in variants:
            key = (boost, norm)
            if key not in seen:
                seen.add(key); dedup.append((boost, norm, label))

        last_url = ""; last_session = ""; last_note = "not preflighted"
        for boost, norm, label in dedup:
            url, session_id = self._music_transcode_url(
                rating_key, 320, offset_seconds, audio_boost=boost, normalize_loudness=norm
            )
            last_url, last_session = url, session_id
            if not preflight:
                return url, session_id, boost, norm, False, "deferred Plex transcode fallback"
            accepted, note = await self._probe_music_transcode_decision(url, str(source.get("token") or ""))
            last_note = note
            if accepted:
                return url, session_id, boost, norm, True, f"{label}: {note}"
        # Keep a final plain MP3 URL available even if a PMS does not expose a
        # useful decision response. The frontend still has Direct Play recovery
        # when the source format is browser-compatible.
        return last_url, last_session, 100, False, False, last_note

    async def get_stream_url(self, rating_key: str, capabilities: dict[str, Any] | None = None, force_transcode: bool = False, offset_seconds: float = 0.0, kind: str = ""):
        """Return a resilient transport plan.

        0.8.3 restores the hardware-proven rule: if Steam Chromium can Direct
        Play the source, Direct Play is the primary transport. Plex loudness
        transcoding remains available as a recovery/optional path, but it may
        never make a previously playable audiobook or podcast unplayable.

        Every transcode plan carries a Direct Play recovery URL when the source
        is browser-compatible. Every Direct Play plan carries an MP3 recovery
        URL. The frontend can therefore recover in either direction without
        recursively selecting the same broken transport.
        """
        try:
            kind = str(kind or "").lower()
            # Music metadata is cheap to refresh and is the surface most likely to
            # change underneath a running Deck session after a tag/art edit or a
            # remove/re-add in Plex. Never hand the browser a 15-minute-old Part
            # key for Music. Long-form media keeps the warm source cache.
            source = await self._media_source(rating_key, refresh=(kind == "music"))
            can_direct, decision_reason = self._browser_can_direct_play(source, capabilities)
            direct_url = self._register_proxy("media", source["url"], source["token"], allow_range=True)
            offset_seconds = max(0.0, float(offset_seconds or 0.0))
            prefs = await self.get_preferences()
            is_audiobook = kind in ("audiobook", "audiobooks")
            is_podcast = kind in ("podcast", "podcasts")
            long_form = bool(is_audiobook or is_podcast)
            # Hardware evidence: Podcasts are already loud enough on Direct Play.
            # Only audiobooks get an automatic source-level boost, and normalization
            # is deliberately off by default because some PMS builds reject it.
            boost_percent = max(100, min(200, int(prefs.get("audiobookBoostPercent", 170) or 170))) if is_audiobook else 100
            normalize_loudness = False

            # Audiobooks may choose a preflighted boost-only Plex MP3 stream when
            # the server explicitly accepts it. If not, Direct Play remains the
            # immediate safe path. Podcasts and Music stay Direct Play-first.
            prefer_boosted_book = bool(is_audiobook and can_direct and not force_transcode and boost_percent > 100)
            if prefer_boosted_book:
                transcode, _session_id, selected_boost, selected_norm, decision_ready, decision_note = await self._select_music_transcode_profile(
                    rating_key, source, offset_seconds, boost_percent, False, preflight=True
                )
                use_direct = not bool(decision_ready and selected_boost > 100)
            else:
                use_direct = bool(can_direct and not force_transcode)
                transcode, _session_id, selected_boost, selected_norm, decision_ready, decision_note = await self._select_music_transcode_profile(
                    rating_key, source, offset_seconds, boost_percent, False, preflight=not use_direct
                )
            transcode_url = self._register_proxy("media", transcode, source["token"], "audio/mpeg", allow_range=False)
            primary = direct_url if use_direct else transcode_url
            fallback_url = transcode_url if use_direct else (direct_url if can_direct else "")
            fallback_direct = bool((not use_direct) and can_direct)

            if use_direct:
                selected = "direct"
                reason = decision_reason
            else:
                selected = "transcode"
                if (force_transcode or prefer_boosted_book) and is_audiobook and boost_percent > 100:
                    reason = f"Plex MP3 audiobook loudness profile {selected_boost}%"
                elif force_transcode:
                    reason = "forced Plex MP3 recovery"
                else:
                    reason = decision_reason or "Steam browser requires Plex MP3"

            return {
                "success": True,
                "url": primary,
                "fallbackUrl": fallback_url,
                "fallbackDirectPlay": fallback_direct,
                "fallbackSelected": "direct" if fallback_direct else ("transcode" if fallback_url else ""),
                "directPlay": use_direct,
                "transcoded": not use_direct,
                "selected": selected,
                "decisionReason": reason,
                "audioBoostPercent": selected_boost if not use_direct else 100,
                "normalizeLoudness": bool(selected_norm and not use_direct),
                "transcodeDecisionReady": bool(decision_ready),
                "transcodeDecisionNote": str(decision_note or ""),
                "outputMime": "" if use_direct else "audio/mpeg",
                "fallbackCodec": "mp3" if use_direct else str(source.get("codec") or ""),
                "fallbackBitrate": 320 if use_direct else int(source.get("bitrate") or 0),
                "offsetSeconds": offset_seconds if not use_direct else 0.0,
                "container": source["container"],
                "codec": source["codec"],
                "bitrate": source["bitrate"],
                "size": source["size"],
            }
        except Exception as error:
            self._record("stream-url", error)
            return {"success": False, "message": self._sanitize(str(error))}

    def _art_cache_key(self, path: str, mode: str) -> str:
        server = str(self._server.machine_id or self._server.base_url or "plex")
        # 0.7.8 intentionally keeps the v5 disk namespace so already-correct book,
        # podcast and More artwork remains warm. Candidate signatures still
        # invalidate individual entries when ordering/source evidence changes.
        return hashlib.sha256(f"{server}|thumb-v5|{str(mode or 'square').lower()}|{path}".encode("utf-8", "ignore")).hexdigest()[:40]

    def _art_source_url(self, path: str, mode: str) -> str:
        """Return the original Plex artwork resource, not /photo/:/transcode.

        The Deck can scale cached images cheaply. Asking a DS418 to transcode
        every cover while the user scrolls is both slower and less reliable.
        """
        if path.startswith("http://") or path.startswith("https://"):
            return path
        source = path if path.startswith("/") else "/" + path
        return self._server.base_url.rstrip("/") + source

    def _art_fallback_url(self, path: str, mode: str = "square") -> str:
        """Return a bounded Plex thumbnail URL sized for the actual UI surface.

        On Steam Deck, small normalized Plex thumbnails are substantially more
        predictable than arbitrary original cover files. 0.7.4 therefore uses
        this as the primary card/detail source and keeps the original only as a
        fallback.
        """
        base = self._server.base_url.rstrip("/")
        raw = str(path or "")
        if not base or not raw:
            return ""
        if raw.startswith("http://") or raw.startswith("https://"):
            if not raw.startswith(base):
                return ""
            parsed = urllib.parse.urlsplit(raw)
            raw = parsed.path + (("?" + parsed.query) if parsed.query else "")
        if not raw.startswith("/"):
            raw = "/" + raw
        m = str(mode or "square").lower()
        if "portrait-card" in m or "portrait-book" in m:
            width, height = (720, 1080) if "detail" in m else (360, 540)
        elif "square-card" in m:
            width, height = 360, 360
        elif "portrait" in m:
            width, height = 720, 1080
        else:
            width, height = 720, 720
        params = {
            "width": width,
            "height": height,
            "minSize": 0,
            "upscale": 0,
            "url": raw,
        }
        return base + "/photo/:/transcode?" + urllib.parse.urlencode(params)

    def _remember_art_source(self, path: str, mode: str = "square") -> str:
        return self._remember_art_candidates([path], mode=mode, identity=str(path or ""))

    def _remember_art_candidates(self, paths, mode: str = "square", identity: str = "", role: str = "") -> str:
        """Register one canonical artwork identity with ordered Plex candidates.

        0.7.5 makes the cache identity belong to the media item/role/surface, not
        whichever transient thumb string happened to reach React first. Every
        Plex candidate is attempted as a bounded thumbnail before any original.
        """
        mode = str(mode or "square").lower()
        role = str(role or "").lower()
        clean = []
        for raw in (paths or []):
            value = str(raw or "").strip()
            if value and value not in clean:
                clean.append(value)
        if not clean or not self._server.base_url:
            return ""
        stable = str(identity or clean[0])
        candidate_signature = hashlib.sha256("\n".join(clean).encode("utf-8", "ignore")).hexdigest()[:16]
        key = self._art_cache_key(f"{role}|{stable}|src:{candidate_signature}", mode)
        candidates = []
        # Try every small normalized cover before touching any potentially huge
        # original. This keeps QAM responsive even when one Plex source image
        # is pathological.
        for candidate in clean:
            normalized = self._art_fallback_url(candidate, mode)
            if normalized:
                candidates.append({"kind": "plex-thumbnail", "url": normalized, "path": candidate, "timeout": 7})
        for candidate in clean:
            normalized = self._art_fallback_url(candidate, mode)
            original = self._art_source_url(candidate, mode)
            if original and original != normalized:
                candidates.append({"kind": "original-fallback", "url": original, "path": candidate, "timeout": 6})
        self._art_sources[key] = {
            "candidates": candidates, "token": self._server.access_token,
            "path": clean[0], "paths": clean, "mode": mode, "role": role,
            "identity": stable, "candidateSignature": candidate_signature, "seen": time.time(),
        }
        return key

    def _art_cache_files(self, key: str) -> tuple[Path, Path]:
        safe = re.sub(r"[^a-fA-F0-9]", "", str(key))[:64]
        return self.artwork_dir / f"{safe}.bin", self.artwork_dir / f"{safe}.json"

    def _art_registry_identity(self, path: str = "", rating_key: str = "", role: str = "", mode: str = "square") -> str:
        owner = str(rating_key or path or "unknown")
        return f"{str(role or 'auto').lower()}|{owner}|{str(mode or 'square').lower()}"

    def _art_registry_publish(self, identity: str, **fields: Any) -> dict[str, Any]:
        identity = str(identity or "")
        if not identity:
            return {}
        previous = dict(self._art_registry.get(identity) or {})
        candidate = {**previous, **fields, "identity": identity, "updatedAt": time.time()}
        # Do not churn the revision counter for timestamp-only repeats.
        meaningful = {k: v for k, v in candidate.items() if k not in ("revision", "updatedAt")}
        old_meaningful = {k: v for k, v in previous.items() if k not in ("revision", "updatedAt")}
        if meaningful != old_meaningful:
            self._art_registry_revision += 1
            candidate["revision"] = self._art_registry_revision
        else:
            candidate["revision"] = int(previous.get("revision") or self._art_registry_revision)
        self._art_registry[identity] = candidate
        if len(self._art_registry) > 1200:
            oldest = sorted(self._art_registry.items(), key=lambda kv: float(kv[1].get("updatedAt") or 0))[:200]
            for key, _ in oldest:
                self._art_registry.pop(key, None)
        return dict(candidate)

    def _art_registry_ready_record(self, identity: str, key: str, role: str, mode: str, rating_key: str, title: str = "", resolved_path: str = "", source_hint: str = "", candidate_count: int = 0) -> dict[str, Any] | None:
        data_path, meta_path = self._art_cache_files(key)
        valid, _ = self._validate_cached_art(data_path, meta_path)
        if not valid:
            return None
        try:
            stat = data_path.stat(); version = f"{int(stat.st_mtime_ns)}-{int(stat.st_size)}"
        except Exception:
            version = "cached"
        url = f"http://127.0.0.1:{self._port}/art-cache/{self._loop_token}/{key}?v={version}"
        return self._art_registry_publish(identity, state="ready", url=url, cacheKey=key, role=role, mode=mode,
                                          ratingKey=rating_key, title=title, resolvedPath=resolved_path,
                                          sourceHint=str(source_hint or ""), candidateCount=int(candidate_count or 0),
                                          errorCode="", candidateErrors=[])

    def _art_record_response(self, record: dict[str, Any]) -> dict[str, Any]:
        """Return one registry record without inflating its per-record revision.

        Older builds overwrote ``record.revision`` with the registry's global
        revision on single-item RPC responses. The frontend correctly rejects
        older per-identity updates, so an inflated revision could make a mounted
        QAM card ignore the later READY record until the page remounted. Keep the
        identity revision intact and expose the global cursor separately.
        """
        return {"success": True, **dict(record or {}), "latestRevision": self._art_registry_revision}

    async def get_artwork_record(self, path: str, mode: str = "square", rating_key: str = "", repair: bool = False, role: str = "", title: str = ""):
        mode = str(mode or "square").lower(); role = str(role or "").lower(); path = str(path or ""); rating_key = str(rating_key or "")
        identity = self._art_registry_identity(path, rating_key, role, mode)
        existing = dict(self._art_registry.get(identity) or {})
        # 0.8.2: a validated READY record is authoritative for a rating-key
        # identity. Never downgrade a good cached cover to RESOLVING merely
        # because another consumer supplied a different/stale thumb hint.
        if existing.get("state") == "ready" and not repair:
            key = str(existing.get("cacheKey") or "")
            if key:
                ready = self._art_registry_ready_record(
                    identity, key, role, mode, rating_key,
                    title or str(existing.get("title") or ""),
                    str(existing.get("resolvedPath") or ""),
                    path or str(existing.get("sourceHint") or ""),
                    int(existing.get("candidateCount") or 0),
                )
                if ready:
                    return self._art_record_response(ready)
        if existing.get("state") == "fallback" and not repair:
            return self._art_record_response(existing)
        self._art_registry_publish(identity, state="resolving", url=str(existing.get("url") or ""), role=role, mode=mode,
                                   ratingKey=rating_key, title=title, sourceHint=path, errorCode="")
        try:
            candidates = await self._resolve_art_candidates(path, rating_key, role, bool(repair))
        except Exception as error:
            self._record("artwork-registry-resolve", error)
            record = self._art_registry_publish(identity, state="failed", url=str(existing.get("url") or ""), role=role, mode=mode,
                                                ratingKey=rating_key, title=title, sourceHint=path, errorCode="PLEX_METADATA_FAILED")
            return self._art_record_response(record)
        if not candidates:
            record = self._art_registry_publish(identity, state="fallback", url="", role=role, mode=mode,
                                                ratingKey=rating_key, title=title, sourceHint=path, errorCode="NO_CANONICAL_ART", candidateErrors=[])
            return self._art_record_response(record)
        if not self._server.base_url:
            record = self._art_registry_publish(identity, state="failed", url=str(existing.get("url") or ""), role=role, mode=mode,
                                                ratingKey=rating_key, title=title, sourceHint=path, errorCode="PLEX_OFFLINE")
            return self._art_record_response(record)
        key = self._remember_art_candidates(candidates, mode=mode, identity=f"{rating_key or candidates[0]}|{role or 'auto'}", role=role)
        if not key:
            record = self._art_registry_publish(identity, state="failed", url=str(existing.get("url") or ""), role=role, mode=mode,
                                                ratingKey=rating_key, title=title, sourceHint=path, resolvedPath=candidates[0], errorCode="CACHE_KEY_FAILED")
            return self._art_record_response(record)
        ready = self._art_registry_ready_record(identity, key, role, mode, rating_key, title, candidates[0], path, len(candidates))
        if ready:
            return self._art_record_response(ready)
        downloading = self._art_registry_publish(identity, state="downloading", url=str(existing.get("url") or ""), cacheKey=key,
                                                  role=role, mode=mode, ratingKey=rating_key, title=title, sourceHint=path,
                                                  resolvedPath=candidates[0], candidateCount=len(candidates), errorCode="")
        running = self._art_prefetch_tasks.get(key)
        if not running or running.done():
            async def warm():
                try:
                    cached_path, _ = await self._ensure_art_cached(key)
                    if cached_path and cached_path.is_file():
                        self._art_registry_ready_record(identity, key, role, mode, rating_key, title, candidates[0], path, len(candidates))
                    else:
                        failure_state, failure_code, candidate_errors = self._art_failure_state(key)
                        self._art_registry_publish(identity, state=failure_state, url="" if failure_state == "fallback" else str(existing.get("url") or ""), cacheKey=key,
                                                   role=role, mode=mode, ratingKey=rating_key, title=title, sourceHint=path,
                                                   resolvedPath=candidates[0], errorCode=failure_code,
                                                   candidateErrors=candidate_errors)
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    self._record("artwork-registry-fetch", error)
                    self._art_registry_publish(identity, state="failed", url=str(existing.get("url") or ""), cacheKey=key,
                                               role=role, mode=mode, ratingKey=rating_key, title=title, sourceHint=path,
                                               resolvedPath=candidates[0], errorCode="CACHE_WRITE_FAILED")
                finally:
                    self._art_prefetch_tasks.pop(key, None)
            self._art_prefetch_tasks[key] = asyncio.create_task(warm())
        return self._art_record_response(downloading)

    async def get_artwork_updates(self, since_revision: int = 0):
        """Return registry updates without skipping early records.

        0.8.1 returned the newest 300 records but advanced the client cursor to
        the global latest revision. A cold QAM could therefore permanently miss
        Music records created early in a large hydration run. 0.8.2 pages from
        the oldest unseen revision and advances only to the last record actually
        returned.
        """
        since = max(0, int(since_revision or 0))
        records = [dict(v) for v in self._art_registry.values() if int(v.get("revision") or 0) > since]
        records.sort(key=lambda r: int(r.get("revision") or 0))
        page = records[:300]
        delivered_revision = max([since] + [int(r.get("revision") or 0) for r in page])
        return {
            "success": True,
            "revision": delivered_revision,
            "latestRevision": self._art_registry_revision,
            "hasMore": bool(records[300:]),
            "records": page,
        }

    def _prune_art_cache(self) -> None:
        try:
            prefs = self._settings_get("preferences", {}) or {}
            max_bytes = max(64, min(2048, int(prefs.get("artCacheMaxMb", 384) or 384))) * 1024 * 1024
            files = [p for p in self.artwork_dir.glob("*.bin") if p.is_file()]
            total = sum(p.stat().st_size for p in files)
            if total <= max_bytes:
                return
            files.sort(key=lambda p: p.stat().st_mtime)
            target = int(max_bytes * 0.88)
            for path in files:
                if total <= target:
                    break
                try:
                    size = path.stat().st_size
                    meta = path.with_suffix(".json")
                    path.unlink(missing_ok=True); meta.unlink(missing_ok=True)
                    total -= size
                except Exception:
                    pass
        except Exception as error:
            self._record("art-cache-prune", error)

    @staticmethod
    def _sniff_image_type(data: bytes, declared: str = "") -> str:
        if not data or len(data) < 64:
            return ""
        head = data[:32]
        if head.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if head.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if head.startswith((b"GIF87a", b"GIF89a")):
            return "image/gif"
        if len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WEBP":
            return "image/webp"
        if head.startswith(b"BM"):
            return "image/bmp"
        declared = str(declared or "").split(";", 1)[0].strip().lower()
        if declared.startswith("image/") and not data.lstrip().startswith((b"<", b"{", b"[")):
            return declared
        return ""

    @staticmethod
    async def _read_artwork_stream(stream: Any, limit: int = ART_MAX_BYTES) -> bytes:
        """Read an artwork response all the way to EOF without trusting one read().

        aiohttp StreamReader.read(n) means *up to* n bytes. On Steam Deck/Plex,
        a single read() commonly returned only the currently buffered 16 KiB or
        32 KiB even when Content-Length advertised a much larger valid image.
        0.9.5 treated that normal partial read as a truncated transfer. Repeated
        reads are required until EOF. Keep one byte of headroom so callers can
        still enforce ART_MAX_BYTES without buffering an unbounded response.
        """
        cap = max(1, int(limit)) + 1
        parts: list[bytes] = []
        size = 0
        while size < cap:
            chunk = await stream.read(min(64 * 1024, cap - size))
            if not chunk:
                break
            parts.append(bytes(chunk))
            size += len(chunk)
        return b"".join(parts)

    @staticmethod
    def _image_payload_complete(data: bytes, content_type: str) -> bool:
        """Validate a complete image without requiring its terminator at EOF.

        Plex can return perfectly valid covers with harmless trailing bytes.
        0.9.4 only searched the last 64 bytes for JPEG/PNG terminators, which
        rejected many real Music covers after a successful HTTP transfer. This
        validator remains dependency-free but accepts trailing data while still
        rejecting obviously truncated payloads.
        """
        if not data or len(data) < 64:
            return False
        kind = str(content_type or "").split(";", 1)[0].strip().lower()
        if kind == "image/jpeg":
            if not data.startswith(b"\xff\xd8\xff"):
                return False
            # JPEG entropy data byte-stuffs literal 0xFF values, so an FF D9
            # marker after SOI is a reliable lightweight end-of-image signal.
            return data.rfind(b"\xff\xd9", 3) >= 3
        if kind == "image/png":
            if not data.startswith(b"\x89PNG\r\n\x1a\n"):
                return False
            # Walk PNG chunks so an incidental 'IEND' byte sequence inside IDAT
            # cannot masquerade as a complete image. Trailing bytes after the
            # real zero-length IEND chunk are intentionally tolerated.
            pos = 8
            size = len(data)
            while pos + 12 <= size:
                length = int.from_bytes(data[pos:pos+4], "big", signed=False)
                chunk_type = data[pos+4:pos+8]
                end = pos + 12 + length
                if end > size:
                    return False
                if chunk_type == b"IEND":
                    return length == 0
                pos = end
            return False
        if kind == "image/gif":
            if not data.startswith((b"GIF87a", b"GIF89a")):
                return False
            # A valid GIF terminates with 0x3B. Permit metadata/padding after it
            # because transfer completion is checked separately via HTTP length.
            return data.rfind(b"\x3b", 13) >= 13
        if kind == "image/webp":
            if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
                return False
            declared_size = int.from_bytes(data[4:8], "little", signed=False) + 8
            return declared_size >= 12 and len(data) >= declared_size
        if kind == "image/bmp":
            if len(data) < 6 or not data.startswith(b"BM"):
                return False
            declared_size = int.from_bytes(data[2:6], "little", signed=False)
            return declared_size <= len(data) if declared_size else True
        # For less common image/* types, successful transfer + non-trivial body
        # is safer than permanently rejecting Plex artwork we cannot parse here.
        return len(data) >= 1024

    def _validate_cached_art(self, data_path: Path, meta_path: Path) -> tuple[bool, str]:
        if not data_path.is_file():
            return False, ""
        declared = ""
        try:
            declared = str(json.loads(meta_path.read_text("utf-8")).get("contentType") or "")
        except Exception:
            pass
        try:
            data = data_path.read_bytes()
            detected = self._sniff_image_type(data, declared)
            if detected and self._image_payload_complete(data, detected):
                return True, detected
        except Exception:
            pass
        try:
            data_path.unlink(missing_ok=True); meta_path.unlink(missing_ok=True)
        except Exception:
            pass
        return False, ""

    @staticmethod
    def _art_candidate_errors_are_not_found(errors: Any) -> bool:
        rows = [dict(x) for x in (errors or []) if isinstance(x, dict)]
        if not rows:
            return False
        return all("http 404" in str(row.get("message") or "").lower() for row in rows)

    def _art_failure_state(self, key: str) -> tuple[str, str, list[dict[str, Any]]]:
        errors = list((self._art_sources.get(str(key or "")) or {}).get("lastCandidateErrors") or [])
        if self._art_candidate_errors_are_not_found(errors):
            return "fallback", "PLEX_ART_NOT_FOUND", errors
        return "failed", "PLEX_IMAGE_FAILED", errors

    async def _ensure_art_cached(self, key: str) -> tuple[Path | None, str]:
        """Fetch one cover into the local disk cache with retries and a hard
        concurrency ceiling. A failure is temporary, never a permanent grey
        card: requesting the same stable loopback URL later retries Plex.
        """
        key = str(key or "")
        source = self._art_sources.get(key)
        data_path, meta_path = self._art_cache_files(key)
        valid, content_type = self._validate_cached_art(data_path, meta_path)
        expected_signature = str((source or {}).get("candidateSignature") or "")
        if valid and expected_signature:
            try:
                cached_meta = json.loads(meta_path.read_text("utf-8"))
                if str(cached_meta.get("candidateSignature") or "") != expected_signature:
                    data_path.unlink(missing_ok=True); meta_path.unlink(missing_ok=True); valid = False
            except Exception:
                data_path.unlink(missing_ok=True); meta_path.unlink(missing_ok=True); valid = False
        if valid:
            return data_path, content_type
        if not source or not self._session:
            return None, "image/jpeg"
        lock = self._art_locks.setdefault(key, asyncio.Lock())
        async with lock:
            valid, content_type = self._validate_cached_art(data_path, meta_path)
            if valid:
                return data_path, content_type
            last_error = None
            candidate_errors = []
            registered = list(source.get("candidates") or [])
            if not registered:
                primary_url = str(source.get("url") or "")
                fallback_url = str(source.get("fallbackUrl") or "")
                registered = [{"kind":"plex-thumbnail", "url":primary_url, "path":str(source.get("path") or ""), "timeout":7}]
                if fallback_url and fallback_url != primary_url:
                    registered.append({"kind":"original-fallback", "url":fallback_url, "path":str(source.get("path") or ""), "timeout":6})
            async with self._art_fetch_semaphore:
                for candidate in registered:
                    source_kind = str(candidate.get("kind") or "artwork")
                    art_url = str(candidate.get("url") or "")
                    total_timeout = max(4, min(12, _as_int(candidate.get("timeout"), 7)))
                    if not art_url:
                        continue
                    try:
                        timeout = aiohttp.ClientTimeout(total=total_timeout, connect=3, sock_read=max(5, total_timeout - 2))
                        # Never leak a Plex access token to third-party absolute artwork URLs.
                        token = str(source.get("token") or "") if art_url.startswith(self._server.base_url.rstrip("/")) else ""
                        headers = self._plex_headers(token, False) if token else {"User-Agent": f"{PRODUCT}/{PLUGIN_VERSION}"}
                        async with self._session.get(art_url, headers=headers, ssl=self.ssl_context, timeout=timeout) as r:
                            if r.status >= 400:
                                raise RuntimeError(f"Plex artwork HTTP {r.status} ({source_kind})")
                            declared_size = _as_int(r.headers.get("Content-Length"))
                            if declared_size > ART_MAX_BYTES:
                                raise RuntimeError(f"Artwork declared {declared_size} bytes, above the {ART_MAX_BYTES} byte cache limit ({source_kind})")
                            # IMPORTANT: StreamReader.read(n) returns *up to* n bytes;
                            # it is not a read-exactly/until-EOF API. 0.9.5 performed
                            # one read and therefore mistook normal 16/32 KiB buffer
                            # fills for truncated Plex images. Drain to EOF first.
                            data = await self._read_artwork_stream(r.content, ART_MAX_BYTES)
                            if len(data) > ART_MAX_BYTES:
                                raise RuntimeError(f"Artwork exceeded {ART_MAX_BYTES} bytes ({source_kind})")
                            # Only compare Content-Length after EOF has been reached.
                            # aiohttp usually raises ClientPayloadError for a genuinely
                            # short body; this explicit check remains as a second guard.
                            content_encoding = str(r.headers.get("Content-Encoding") or "").strip().lower()
                            if declared_size > 0 and not content_encoding and len(data) < declared_size:
                                raise RuntimeError(f"Artwork body shorter than Content-Length ({len(data)}/{declared_size}, {source_kind})")
                            declared_type = r.headers.get("Content-Type", "")
                            content_type = self._sniff_image_type(data, declared_type)
                            if not content_type:
                                raise RuntimeError(f"Artwork response was not a valid image ({declared_type or 'unknown content type'}, {source_kind})")
                            if not self._image_payload_complete(data, content_type):
                                raise RuntimeError(f"Artwork download was incomplete or truncated ({source_kind})")
                        self.artwork_dir.mkdir(parents=True, exist_ok=True)
                        tmp = data_path.with_suffix(".tmp")
                        tmp.write_bytes(data)
                        os.replace(tmp, data_path)
                        _safe_write(meta_path, {
                            "contentType": content_type,
                            "source": str(candidate.get("path") or source.get("path") or ""),
                            "mode": str(source.get("mode") or ""),
                            "role": str(source.get("role") or ""),
                            "identity": str(source.get("identity") or ""),
                            "candidateSignature": str(source.get("candidateSignature") or ""),
                            "sourceKind": source_kind,
                            "cachedAt": _utc(),
                        })
                        self._prune_art_cache()
                        source["lastCandidateErrors"] = []
                        return data_path, content_type
                    except asyncio.CancelledError:
                        raise
                    except Exception as error:
                        last_error = error
                        candidate_errors.append({"kind": source_kind, "message": self._sanitize(str(error))[:240]})
                        if source_kind.startswith("plex-thumbnail") and len(registered) > 1:
                            await asyncio.sleep(0.08)
            self._art_sources.get(key, {})["lastCandidateErrors"] = candidate_errors[-8:]
            if last_error and not self._art_candidate_errors_are_not_found(candidate_errors):
                summary = "; ".join(f"{row.get('kind')}: {row.get('message')}" for row in candidate_errors[-4:])
                self._record("artwork-fetch", summary or last_error)
            return None, "image/jpeg"

    async def _serve_cached_art(self, request: web.Request):
        if request.match_info.get("token") != self._loop_token:
            raise web.HTTPForbidden()
        key = str(request.match_info.get("key") or "")
        data_path, content_type = await self._ensure_art_cached(key)
        if not data_path or not data_path.is_file():
            raise web.HTTPBadGateway(text="Plex artwork is temporarily unavailable")
        try:
            os.utime(data_path, None)
        except Exception:
            pass
        return web.FileResponse(data_path, headers={
            "Content-Type": content_type,
            "Cache-Control": "private, max-age=31536000, immutable",
            "Access-Control-Allow-Origin": "*",
        })

    @staticmethod
    def _art_paths_from_item(item: dict[str, Any], role: str = "") -> list[str]:
        """Return cover candidates in semantic ownership order.

        Plex music-style libraries expose several artwork fields whose meaning
        changes with hierarchy level. A Track's parentThumb is usually the album
        or book cover, while a Directory/Album's own thumb is authoritative.
        0.7.5 flattened those fields too aggressively, allowing a stale child or
        artist image to outrank the actual media owner.
        """
        if not isinstance(item, dict):
            return []
        role = str(role or item.get("libraryRole") or "").lower()
        typ = str(item.get("semanticType") or item.get("type") or item.get("mediaType") or "").lower()
        is_track = typ in ("track", "audio", "episode", "song", "audiobook-file") or bool(item.get("partKey"))
        own_thumb = str(item.get("selfThumb") or "").strip()
        merged_thumb = str(item.get("thumb") or "").strip()
        parent_thumb = str(item.get("parentThumb") or "").strip()
        grand_thumb = str(item.get("grandparentThumb") or "").strip()
        own_art = str(item.get("selfArt") or "").strip()
        merged_art = str(item.get("art") or "").strip()
        parent_art = str(item.get("parentArt") or "").strip()
        grand_art = str(item.get("grandparentArt") or "").strip()

        if role == "music" and is_track:
            ordered = (parent_thumb, own_thumb, merged_thumb, grand_thumb, parent_art, own_art, merged_art, grand_art)
        elif role == "audiobooks" and is_track:
            ordered = (parent_thumb, own_thumb, merged_thumb, grand_thumb, parent_art, own_art, merged_art, grand_art)
        elif role == "podcasts" and is_track:
            # Keep episode-specific art when Plex exposes it, then inherit show art.
            ordered = (own_thumb, merged_thumb, parent_thumb, grand_thumb, own_art, parent_art, merged_art, grand_art)
        else:
            # Albums/books/shows/artists own their direct thumbnail. Backdrops are
            # only fallbacks and never outrank a poster/cover.
            ordered = (own_thumb, merged_thumb, parent_thumb, grand_thumb, own_art, merged_art, parent_art, grand_art)
        out: list[str] = []
        for value in ordered:
            value = str(value or "").strip()
            if value and value not in out:
                out.append(value)
        return out

    @staticmethod
    def _art_path_owner_key(path: str) -> str:
        """Extract the Plex metadata owner encoded in common thumb URLs."""
        raw = urllib.parse.unquote(str(path or ""))
        match = re.search(r"/library/metadata/([^/?]+)/thumb(?:/|\?|$)", raw)
        return str(match.group(1)) if match else ""

    async def _art_children_sample(self, rating_key: str, limit: int = 8) -> list[dict[str, Any]]:
        """Fetch a tiny child sample for semantic artwork ownership.

        Artwork should never require reading a 1000-track album just to learn
        what cover its children point back to. A bounded sample is enough to
        establish parentThumb consensus while remaining DS418-friendly.
        """
        rating_key = str(rating_key or "").strip()
        if not rating_key:
            return []
        try:
            root = await self._pms_xml(
                f"/library/metadata/{urllib.parse.quote(rating_key)}/children",
                params={"X-Plex-Container-Start": 0, "X-Plex-Container-Size": max(1, min(12, int(limit)))},
            )
            rows: list[dict[str, Any]] = []
            rows.extend(self._track(n) for n in root.findall(".//Track"))
            rows.extend(self._album(n) for n in root.findall(".//Directory"))
            return rows[: max(1, min(12, int(limit)))]
        except Exception as error:
            self._record("artwork-child-sample", error)
            return []

    @staticmethod
    def _parent_cover_consensus(rows: list[dict[str, Any]], rating_key: str) -> list[str]:
        """Return child-declared parent covers ordered by consensus.

        This is deliberately stronger evidence than an album/book row's stale
        own thumb. It mirrors what a child track says its parent actually uses
        and fixes cases where Plex exposes the right book title/ratingKey beside
        an obsolete poster on the parent row.
        """
        wanted = str(rating_key or "").strip()
        counts: dict[str, int] = {}
        order: list[str] = []
        for child in rows or []:
            parent_key = str(child.get("parentRatingKey") or "").strip()
            if wanted and parent_key and parent_key != wanted:
                continue
            # parentThumb is cover/poster ownership. parentArt is commonly a
            # backdrop/fanart image and must never win a card-cover consensus.
            candidate = str(child.get("parentThumb") or "").strip()
            if not candidate:
                continue
            if candidate not in counts:
                counts[candidate] = 0; order.append(candidate)
            counts[candidate] += 1
        return sorted(order, key=lambda x: (-counts.get(x, 0), order.index(x)))

    async def _resolve_art_candidates(self, path: str = "", rating_key: str = "", role: str = "", repair: bool = False) -> list[str]:
        supplied = str(path or "").strip()
        rating_key = str(rating_key or "").strip()
        role = str(role or "").lower()
        server_id = str(self._server.machine_id or self._server.base_url or "plex")
        user_id = self._user_key()
        cache_key = f"v7:{server_id}:{user_id}:{rating_key}:{role}"

        cached = self._art_candidate_cache.get(cache_key)
        if cached and not repair and time.time() - float(cached[0]) < 900:
            result = list(cached[1] or [])
            if supplied and supplied not in result:
                result.append(supplied)
            return result

        # 0.9.4 Music fast path: most callers already pass the canonical Album
        # owner ratingKey. Try an owner-matching catalog thumb and Plex's exact
        # album thumb endpoint before doing deep metadata/child traversal. A
        # failed image request retries with repair=True and reaches the semantic
        # resolver below.
        if rating_key and not repair and role == "music":
            synthetic = f"/library/metadata/{urllib.parse.quote(rating_key)}/thumb"
            quick_music: list[str] = []
            supplied_owner = self._art_path_owner_key(supplied) if supplied else ""
            if supplied and supplied_owner == rating_key:
                quick_music.append(supplied)
            if synthetic not in quick_music:
                quick_music.append(synthetic)
            # Unknown/opaque supplied paths are a final lightweight fallback;
            # known other-owner paths (normally Artist art) wait for deep repair.
            if supplied and not supplied_owner and supplied not in quick_music:
                quick_music.append(supplied)
            self._art_candidate_cache[cache_key] = (time.time(), list(quick_music))
            return quick_music

        # Podcasts/Other can similarly use their exact owner endpoint without
        # a hierarchy walk on the normal path.
        if rating_key and not repair and role in ("podcasts", "other"):
            synthetic = f"/library/metadata/{urllib.parse.quote(rating_key)}/thumb"
            quick: list[str] = []
            supplied_owner = self._art_path_owner_key(supplied) if supplied else ""
            if supplied and supplied_owner == rating_key:
                quick.append(supplied)
            if synthetic not in quick:
                quick.append(synthetic)
            if supplied and supplied not in quick:
                quick.append(supplied)
            self._art_candidate_cache[cache_key] = (time.time(), list(quick))
            return quick

        # A visible audiobook card already tells us the book rating key and its
        # catalog cover. Skip a redundant parent metadata read and ask only a
        # small child sample for authoritative parentThumb consensus.
        if rating_key and not repair and role == "audiobooks" and supplied:
            resolve_lock = self._art_resolve_locks.setdefault(cache_key, asyncio.Lock())
            async with resolve_lock:
                again = self._art_candidate_cache.get(cache_key)
                if again and time.time() - float(again[0]) < 900:
                    result = list(again[1] or [])
                    if supplied and supplied not in result:
                        result.append(supplied)
                    return result
                rows = await self._art_children_sample(rating_key, 8)
                consensus = self._parent_cover_consensus(rows, rating_key)
                quick_book: list[str] = []
                # 0.9.0A: the Book/Album owner is canonical. A child parentThumb
                # may corroborate/fill a missing owner cover, but no longer
                # automatically outranks the supplied book row or exact owner endpoint.
                if supplied:
                    quick_book.append(supplied)
                synthetic = f"/library/metadata/{urllib.parse.quote(rating_key)}/thumb"
                if synthetic not in quick_book:
                    quick_book.append(synthetic)
                for candidate in consensus:
                    if candidate and candidate not in quick_book:
                        quick_book.append(candidate)
                self._art_candidate_cache[cache_key] = (time.time(), list(quick_book))
                return quick_book

        candidates: list[str] = []
        meta_item: dict[str, Any] = {}
        if rating_key:
            try:
                meta = await self.get_metadata(rating_key)
                meta_item = dict(meta.get("item") or {}) if isinstance(meta, dict) else {}
                for candidate in self._art_paths_from_item(meta_item, role):
                    if candidate not in candidates:
                        candidates.append(candidate)
            except Exception as error:
                self._record("artwork-candidates-metadata", error)

            meta_type = str(meta_item.get("type") or meta_item.get("mediaType") or "").lower()
            is_track_meta = meta_type in ("track", "audio", "episode") or bool(meta_item.get("partKey"))

            # Only an actual track/file may promote its semantic parent. A Music
            # Album's parentRatingKey is normally the Artist and must never be
            # inserted ahead of that Album's cover.
            parent_key = str(meta_item.get("parentRatingKey") or "").strip()
            if is_track_meta and parent_key and role in ("music", "audiobooks", "podcasts"):
                try:
                    parent_meta = await self.get_metadata(parent_key)
                    parent_item = dict(parent_meta.get("item") or {}) if isinstance(parent_meta, dict) else {}
                    parent_paths = self._art_paths_from_item(parent_item, role)
                    if role in ("music", "audiobooks"):
                        # Parent-owned album/book art outranks a track-local fallback.
                        for candidate in reversed(parent_paths):
                            if candidate in candidates:
                                candidates.remove(candidate)
                            candidates.insert(0, candidate)
                    else:
                        for candidate in parent_paths:
                            if candidate not in candidates:
                                candidates.append(candidate)
                except Exception as error:
                    self._record("artwork-candidates-parent", error)

            # Container covers may use a tiny child sample as corroboration. For
            # Music Albums, keep the owner hierarchy explicit: own thumb, exact
            # Album endpoint, child parentThumb consensus, then inherited/artist
            # fallbacks. Books retain their proven 0.9.0A ordering.
            rows: list[dict[str, Any]] = []
            if not is_track_meta and role in ("music", "audiobooks", "podcasts"):
                rows = await self._art_children_sample(rating_key, 8)
                parent_consensus = self._parent_cover_consensus(rows, rating_key)
                if role == "audiobooks":
                    for candidate in parent_consensus:
                        if candidate and candidate not in candidates:
                            candidates.append(candidate)
                elif role == "music":
                    prior = list(candidates)
                    ordered_music: list[str] = []
                    self_thumb = str(meta_item.get("selfThumb") or "").strip()
                    merged_thumb = str(meta_item.get("thumb") or "").strip()
                    supplied_owner = self._art_path_owner_key(supplied) if supplied else ""
                    for candidate in (self_thumb,):
                        if candidate and candidate not in ordered_music:
                            ordered_music.append(candidate)
                    if merged_thumb and self._art_path_owner_key(merged_thumb) == rating_key and merged_thumb not in ordered_music:
                        ordered_music.append(merged_thumb)
                    if supplied and supplied_owner == rating_key and supplied not in ordered_music:
                        ordered_music.append(supplied)
                    synthetic_album = f"/library/metadata/{urllib.parse.quote(rating_key)}/thumb"
                    if synthetic_album not in ordered_music:
                        ordered_music.append(synthetic_album)
                    for candidate in parent_consensus:
                        if candidate and candidate not in ordered_music:
                            ordered_music.append(candidate)
                    for candidate in prior:
                        if candidate and candidate not in ordered_music:
                            ordered_music.append(candidate)
                    candidates = ordered_music
                else:
                    for candidate in reversed(parent_consensus):
                        if candidate in candidates:
                            candidates.remove(candidate)
                        candidates.insert(0, candidate)
            elif (not candidates or repair) and rating_key:
                rows = await self._art_children_sample(rating_key, 6)

            # A direct metadata thumb endpoint is also useful when Plex omits the
            # thumb attribute but can still render artwork for the rating key.
            # Keep it after child-parent consensus for containers, because the
            # latter is stronger evidence in stale-parent cases such as Warship.
            if rating_key:
                synthetic = f"/library/metadata/{urllib.parse.quote(rating_key)}/thumb"
                if synthetic not in candidates:
                    # Episode/Other-Audio tracks may have a rating-key thumbnail
                    # even when Plex omitted selfThumb and supplied only inherited
                    # parent art. Try that exact track identity before repeating the
                    # same parent poster across every row. Music/audiobook tracks
                    # intentionally keep semantic parent artwork first.
                    if is_track_meta and role in ("podcasts", "other") and not str(meta_item.get("selfThumb") or "").strip():
                        candidates.insert(0, synthetic)
                    elif candidates:
                        candidates.append(synthetic)
                    else:
                        candidates.insert(0, synthetic)

            # Add child-local fallbacks after semantic parent evidence. These help
            # podcast/other-style rows where the child really owns distinct art.
            if rows:
                for child in rows[:8]:
                    for candidate in self._art_paths_from_item(child, role):
                        if candidate and candidate not in candidates:
                            candidates.append(candidate)
                            if len(candidates) >= 12:
                                break
                    if len(candidates) >= 12:
                        break

        # Rank metadata-addressed Plex paths by ownership. A book/album card whose
        # thumb URL literally names another rating key is suspicious and must not
        # outrank a path owned by the requested item (or, for a track, its parent).
        expected_owner = rating_key
        meta_type = str(meta_item.get("type") or meta_item.get("mediaType") or "").lower()
        if (meta_type in ("track", "audio", "episode") or meta_item.get("partKey")) and role in ("music", "audiobooks"):
            expected_owner = str(meta_item.get("parentRatingKey") or rating_key)
        if candidates and expected_owner:
            indexed = list(enumerate(candidates))
            def owner_rank(pair):
                i, candidate = pair
                owner = self._art_path_owner_key(candidate)
                if owner == expected_owner:
                    bucket = 0
                elif not owner:
                    bucket = 1
                elif owner == rating_key:
                    bucket = 1
                else:
                    bucket = 2
                return (bucket, i)
            candidates = [candidate for _, candidate in sorted(indexed, key=owner_rank)]

        # Supplied catalog art is intentionally last. It keeps offline/stale-cache
        # resilience without letting an old association beat fresh Plex metadata.
        if supplied and supplied not in candidates:
            candidates.append(supplied)
        candidates = [c for c in candidates if c]
        if rating_key:
            self._art_candidate_cache[cache_key] = (time.time(), list(candidates))
            if self._db:
                try:
                    self._db.execute(
                        "INSERT OR REPLACE INTO canonical_art(server_id,user_id,rating_key,role,mode,candidates,selected_path,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                        (server_id,user_id,rating_key,role,"resolved-v5",json.dumps(candidates,ensure_ascii=False,separators=(",",":")),candidates[0] if candidates else "",time.time()),
                    )
                    self._db.commit()
                except Exception as error:
                    self._record("canonical-art-index", error)
        return candidates

    async def _resolve_art_identity(self, path: str = "", rating_key: str = "", repair: bool = False) -> str:
        candidates = await self._resolve_art_candidates(path, rating_key, "", repair)
        return candidates[0] if candidates else str(path or "")

    async def get_art_url(self, path: str, mode: str = "square", rating_key: str = "", repair: bool = False, role: str = ""):
        mode = str(mode or "square").lower()
        role = str(role or "").lower()
        candidates = await self._resolve_art_candidates(path, rating_key, role, bool(repair))
        if not candidates or not self._server.base_url:
            return {"success": True, "url": "", "cached": False, "resolvedPath": "", "candidateCount": 0}
        identity = f"{rating_key or candidates[0]}|{role or 'auto'}"
        key = self._remember_art_candidates(candidates, mode=mode, identity=identity, role=role)
        if self._db and rating_key:
            try:
                server_id, user_id = self._catalog_identity()
                self._db.execute(
                    "INSERT OR REPLACE INTO canonical_art(server_id,user_id,rating_key,role,mode,candidates,selected_path,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                    (server_id,user_id,rating_key,role,mode,json.dumps(candidates,ensure_ascii=False,separators=(",",":")),candidates[0] if candidates else "",time.time()),
                )
                self._db.commit()
            except Exception as error:
                self._record("canonical-art-surface", error)
        if not key:
            return {"success": True, "url": "", "cached": False, "resolvedPath": candidates[0], "candidateCount": len(candidates)}
        data_path, meta_path = self._art_cache_files(key)
        valid, _content_type = self._validate_cached_art(data_path, meta_path)
        version = "miss"
        if valid:
            try:
                stat = data_path.stat(); version = f"{int(stat.st_mtime_ns)}-{int(stat.st_size)}"
            except Exception:
                version = "cached"
        return {"success": True, "url": f"http://127.0.0.1:{self._port}/art-cache/{self._loop_token}/{key}?v={version}",
                "cached": valid, "cacheKey": key, "resolvedPath": candidates[0], "candidateCount": len(candidates), "role": role}

    async def prefetch_artwork(self, entries):
        """Queue visible artwork through the central 0.8.1 Artwork Registry."""
        rows = [raw for raw in (entries if isinstance(entries, list) else [])[:20] if isinstance(raw, dict)]
        sem = asyncio.Semaphore(4)
        async def one(raw: dict[str, Any]):
            async with sem:
                return await self.get_artwork_record(
                    str(raw.get("path") or ""), str(raw.get("mode") or "square"),
                    str(raw.get("ratingKey") or raw.get("rating_key") or ""), bool(raw.get("repair")),
                    str(raw.get("role") or raw.get("libraryRole") or ""), str(raw.get("title") or ""),
                )
        results = await asyncio.gather(*(one(dict(raw)) for raw in rows)) if rows else []
        return {"success": True, "queued": len([r for r in results if isinstance(r, dict) and r.get("state") in ("resolving","downloading")]),
                "resolved": len(results), "ready": len([r for r in results if isinstance(r, dict) and r.get("state") == "ready"]),
                "records": results}

    async def get_artwork_status(self):
        status = dict(self._art_hydration_status or {})
        status["active"] = bool(self._art_hydration_task and not self._art_hydration_task.done())
        status["queued"] = len([t for t in self._art_prefetch_tasks.values() if t and not t.done()])
        registry_counts: dict[str, dict[str, int]] = {}
        failure_reasons: dict[str, dict[str, int]] = {}
        recent_failures = []
        for rec in self._art_registry.values():
            role = str(rec.get("role") or "auto")
            state = str(rec.get("state") or "unknown")
            bucket = registry_counts.setdefault(role, {"ready":0,"fallback":0,"downloading":0,"resolving":0,"failed":0})
            if state in bucket:
                bucket[state] += 1
            if state in ("failed", "fallback"):
                code = str(rec.get("errorCode") or "UNKNOWN")
                by_role = failure_reasons.setdefault(role, {})
                by_role[code] = int(by_role.get(code, 0)) + 1
                if len(recent_failures) < 12:
                    recent_failures.append({"role":role,"ratingKey":str(rec.get("ratingKey") or ""),"title":str(rec.get("title") or ""),"errorCode":code})
        status["registryRevision"] = self._art_registry_revision
        status["registryCounts"] = registry_counts
        status["failureReasons"] = failure_reasons
        status["recentFailures"] = recent_failures
        return {"success": True, **status}

    async def start_artwork_hydration(self, force: bool = False, rescan: bool = False):
        if self._art_hydration_task and not self._art_hydration_task.done():
            if rescan:
                self._art_rescan_pending = True
            return await self.get_artwork_status()
        if not self._server.base_url or not self._session:
            self._art_hydration_status.update({"state":"waiting", "generation":ARTWORK_HYDRATION_GENERATION, "updatedAt":time.time()})
            return await self.get_artwork_status()

        generation = ARTWORK_HYDRATION_GENERATION
        current_state = str(self._art_hydration_status.get("state") or "")
        current_generation = str(self._art_hydration_status.get("generation") or "")
        if not force and not rescan and current_generation == generation and current_state in ("ready", "partial"):
            return await self.get_artwork_status()

        if not force and not rescan:
            saved = self._settings_get("artworkHydrationState", {}) or {}
            server_key = str(self._server.machine_id or self._server.base_url or "")
            if (
                str(saved.get("generation") or "") == generation
                and str(saved.get("server") or "") == server_key
                and str(saved.get("user") or "") == self._user_key()
                and bool(saved.get("complete"))
            ):
                failed = int(saved.get("failed") or 0)
                self._art_hydration_status.update({
                    "state": "partial" if failed > 0 else "ready",
                    "generation": generation,
                    "done": int(saved.get("done") or 0),
                    "total": int(saved.get("total") or 0),
                    "cached": int(saved.get("cached") or 0),
                    "fallback": int(saved.get("fallback") or 0),
                    "failed": failed,
                    "roles": dict(saved.get("roles") or {}),
                    "currentRole": "", "currentTitle": "", "currentRatingKey": "", "currentArtUrl": "",
                    "previewRole": str(saved.get("previewRole") or ""),
                    "previewTitle": str(saved.get("previewTitle") or ""),
                    "previewArtUrl": str(saved.get("previewArtUrl") or ""),
                    "terminalFallbacks": list(saved.get("terminalFallbacks") or [])[:512],
                    "updatedAt": time.time(),
                })
                for fallback_rec in list(saved.get("terminalFallbacks") or [])[:512]:
                    if not isinstance(fallback_rec, dict) or not str(fallback_rec.get("identity") or ""):
                        continue
                    fields = {k: fallback_rec.get(k) for k in ("role","mode","ratingKey","title","sourceHint","resolvedPath","cacheKey","errorCode","candidateErrors")}
                    self._art_registry_publish(str(fallback_rec.get("identity")), state="fallback", url="", **fields)
                return await self.get_artwork_status()

        # A generation mismatch (including 0.8.3-artwork-v1) intentionally runs
        # one migration pass. Valid READY cache entries are reused by the worker.
        if force or rescan:
            self._art_candidate_cache.clear()
        # rescan=True re-walks the catalog while still allowing validated READY
        # files to be reused. force=True remains the deep repair/redownload path.
        self._art_hydration_task = asyncio.create_task(self._artwork_hydration_worker(bool(force)))
        return await self.get_artwork_status()

    async def _artwork_hydration_worker(self, force: bool = False):
        roles = [("music","albums"),("audiobooks","books"),("podcasts","artists"),("other","tracks")]
        status = {"state":"indexing","generation":ARTWORK_HYDRATION_GENERATION,"done":0,"total":0,"cached":0,"fallback":0,"failed":0,"currentRole":"","currentTitle":"","currentRatingKey":"","currentArtUrl":"","previewRole":"","previewTitle":"","previewArtUrl":"","roles":{},"terminalFallbacks":[],"startedAt":time.time(),"updatedAt":time.time()}
        self._art_hydration_status = status
        try:
            plans: list[tuple[str,str,int]] = []
            for role, view in roles:
                first = await self.browse_cached(role, view, 0, 1, "title", False)
                if not first.get("success"):
                    continue
                total = max(0, int(first.get("total") or len(first.get("items") or [])))
                plans.append((role,view,total))
                status["roles"][role] = {"done":0,"total":total,"cached":0,"fallback":0,"failed":0}
                status["total"] += total
                status["updatedAt"] = time.time()
            status["state"] = "downloading"
            # Music is intentionally first because it is the remaining hardware failure.
            for role, view, total in plans:
                status["currentRole"] = role
                offset = 0
                while offset < total:
                    page = await self.browse_cached(role, view, offset, min(24, total-offset), "title", False)
                    rows = list(page.get("items") or [])
                    if not rows:
                        break
                    sem = asyncio.Semaphore(2)
                    async def hydrate(item: dict[str, Any]):
                        async with sem:
                            rating_key = str(item.get("ratingKey") or item.get("key") or "")
                            title = str(item.get("title") or "Untitled")
                            status["currentTitle"] = title
                            path = _first(item.get("thumb"), item.get("parentThumb"), item.get("grandparentThumb"), item.get("art"))
                            mode = "portrait-book-v85" if role == "audiobooks" else "square-card"
                            try:
                                # browse_cached() restores validated persistent READY artwork.
                                # Reuse it during a normal generation migration instead of
                                # re-resolving/redownloading every healthy album on the NAS.
                                if not force and str(item.get("artRegistryState") or "") == "ready" and str(item.get("cachedArtUrl") or ""):
                                    status["cached"] += 1
                                    status["roles"][role]["cached"] += 1
                                    status["previewRole"] = role
                                    status["previewTitle"] = title
                                    status["previewArtUrl"] = str(item.get("cachedArtUrl") or "")
                                    return
                                # Normal hydration uses the lightweight canonical path first.
                                # repair=True is reserved for explicit/failed-item recovery.
                                candidates = await self._resolve_art_candidates(str(path or ""), rating_key, role, bool(force))
                                if not candidates:
                                    registry_identity = self._art_registry_identity(str(path or ""), rating_key, role, mode)
                                    rec = self._art_registry_publish(registry_identity, state="fallback", url="", role=role, mode=mode, ratingKey=rating_key, title=title, sourceHint=str(path or ""), errorCode="NO_CANONICAL_ART", candidateErrors=[])
                                    status["fallback"] += 1
                                    status["roles"][role]["fallback"] += 1
                                    if len(status["terminalFallbacks"]) < 512:
                                        status["terminalFallbacks"].append({k: rec.get(k) for k in ("identity","role","mode","ratingKey","title","sourceHint","resolvedPath","cacheKey","errorCode","candidateErrors")})
                                    return
                                key = self._remember_art_candidates(candidates, mode=mode, identity=f"{rating_key or candidates[0]}|{role}", role=role)
                                registry_identity = self._art_registry_identity(str(path or ""), rating_key, role, mode)
                                self._art_registry_publish(registry_identity, state="downloading", url="", cacheKey=key or "", role=role, mode=mode, ratingKey=rating_key, title=title, resolvedPath=candidates[0], errorCode="")
                                status["currentRatingKey"] = rating_key
                                status["currentArtUrl"] = ""
                                status["updatedAt"] = time.time()
                                if not key:
                                    status["failed"] += 1
                                    status["roles"][role]["failed"] += 1
                                    return
                                data_path, meta_path = self._art_cache_files(key)
                                valid, _ = self._validate_cached_art(data_path, meta_path)
                                if valid:
                                    status["cached"] += 1
                                    status["roles"][role]["cached"] += 1
                                    try:
                                        stat = data_path.stat(); art_version = f"{int(stat.st_mtime_ns)}-{int(stat.st_size)}"
                                    except Exception:
                                        art_version = "cached"
                                    status["previewRole"] = role
                                    status["previewTitle"] = title
                                    status["previewArtUrl"] = f"http://127.0.0.1:{self._port}/art-cache/{self._loop_token}/{key}?v={art_version}"
                                    self._art_registry_ready_record(registry_identity, key, role, mode, rating_key, title, candidates[0], str(path or ""), len(candidates))
                                    return
                                cached_path, _ = await self._ensure_art_cached(key)
                                # 0.9.4: only a lightweight Music miss escalates to
                                # the expensive metadata/child resolver. This gives
                                # albums with missing/stale direct thumbs one bounded
                                # repair attempt without deep-resolving all 144 albums.
                                if (not cached_path or not cached_path.is_file()) and role == "music" and not force:
                                    repair_candidates = await self._resolve_art_candidates(str(path or ""), rating_key, role, True)
                                    if repair_candidates:
                                        repair_key = self._remember_art_candidates(repair_candidates, mode=mode, identity=f"{rating_key or repair_candidates[0]}|{role}", role=role)
                                        if repair_key:
                                            key = repair_key
                                            candidates = repair_candidates
                                            self._art_registry_publish(registry_identity, state="downloading", url="", cacheKey=key, role=role, mode=mode, ratingKey=rating_key, title=title, resolvedPath=candidates[0], errorCode="")
                                            data_path, meta_path = self._art_cache_files(key)
                                            valid, _ = self._validate_cached_art(data_path, meta_path)
                                            if valid:
                                                cached_path = data_path
                                            else:
                                                cached_path, _ = await self._ensure_art_cached(key)
                                if cached_path and cached_path.is_file():
                                    status["cached"] += 1
                                    status["roles"][role]["cached"] += 1
                                    try:
                                        stat = cached_path.stat(); art_version = f"{int(stat.st_mtime_ns)}-{int(stat.st_size)}"
                                    except Exception:
                                        art_version = "cached"
                                    status["previewRole"] = role
                                    status["previewTitle"] = title
                                    status["previewArtUrl"] = f"http://127.0.0.1:{self._port}/art-cache/{self._loop_token}/{key}?v={art_version}"
                                    self._art_registry_ready_record(registry_identity, key, role, mode, rating_key, title, candidates[0], str(path or ""), len(candidates))
                                else:
                                    failure_state, failure_code, candidate_errors = self._art_failure_state(key)
                                    self._art_registry_publish(registry_identity, state=failure_state, url="", cacheKey=key, role=role, mode=mode, ratingKey=rating_key, title=title, resolvedPath=candidates[0], errorCode=failure_code, candidateErrors=candidate_errors)
                                    if failure_state == "fallback":
                                        status["fallback"] += 1
                                        status["roles"][role]["fallback"] += 1
                                        if len(status["terminalFallbacks"]) < 512:
                                            current = dict(self._art_registry.get(registry_identity) or {})
                                            status["terminalFallbacks"].append({k: current.get(k) for k in ("identity","role","mode","ratingKey","title","sourceHint","resolvedPath","cacheKey","errorCode","candidateErrors")})
                                    else:
                                        status["failed"] += 1
                                        status["roles"][role]["failed"] += 1
                            except asyncio.CancelledError:
                                raise
                            except Exception as error:
                                status["failed"] += 1
                                status["roles"][role]["failed"] += 1
                                self._record("artwork-hydration", error)
                            finally:
                                status["done"] += 1
                                status["roles"][role]["done"] += 1
                                status["updatedAt"] = time.time()
                    await asyncio.gather(*(hydrate(dict(item)) for item in rows))
                    offset += len(rows)
                    await asyncio.sleep(0.04)
            status["state"] = "partial" if int(status.get("failed") or 0) > 0 else "ready"
            status["currentRole"] = ""
            status["currentTitle"] = ""
            status["currentRatingKey"] = ""
            status["currentArtUrl"] = ""
            status["updatedAt"] = time.time()
            self._settings_set("artworkHydrationState", {
                "generation": ARTWORK_HYDRATION_GENERATION,
                "server": str(self._server.machine_id or self._server.base_url or ""),
                "user": self._user_key(),
                "complete": True,
                "done": int(status.get("done") or 0),
                "total": int(status.get("total") or 0),
                "cached": int(status.get("cached") or 0),
                "fallback": int(status.get("fallback") or 0),
                "failed": int(status.get("failed") or 0),
                "roles": dict(status.get("roles") or {}),
                "previewRole": str(status.get("previewRole") or ""),
                "previewTitle": str(status.get("previewTitle") or ""),
                "previewArtUrl": str(status.get("previewArtUrl") or ""),
                "terminalFallbacks": list(status.get("terminalFallbacks") or [])[:512],
                "completedAt": time.time(),
            })
        except asyncio.CancelledError:
            status["state"] = "paused"
            status["updatedAt"] = time.time()
            raise
        except Exception as error:
            status["state"] = "error"
            status["updatedAt"] = time.time()
            self._record("artwork-hydration-worker", error)
        finally:
            # A Plex library revision can arrive while hydration is already in
            # flight. Remember one soft rerun instead of losing the new/changed
            # item until the user manually refreshes again.
            if bool(getattr(self, "_art_rescan_pending", False)) and getattr(self, "_session", None) and getattr(getattr(self, "_server", None), "base_url", ""):
                self._art_rescan_pending = False
                self._art_candidate_cache.clear()
                try:
                    self._art_hydration_task = asyncio.create_task(self._artwork_hydration_worker(False))
                except Exception:
                    pass

    def _append_http_range_event(self, row: dict[str, Any]) -> None:
        self._http_range_events.append(self._sanitize_value(dict(row or {})))
        if len(self._http_range_events) > 220:
            del self._http_range_events[:-220]

    async def _proxy_media(self, request: web.Request):
        started = time.time()
        sid = str(request.match_info.get("sid", ""))
        source_hash = hashlib.sha256(sid.encode("utf-8")).hexdigest()[:16] if sid else ""
        range_request = str(request.headers.get("Range") or "")
        if request.match_info.get("token") != self._loop_token:
            raise web.HTTPForbidden()
        src = self._proxy_sources.get(sid)
        if not src or src.get("kind") != "media":
            raise web.HTTPNotFound()
        headers = self._plex_headers(str(src.get("token") or ""), json_accept=False)
        if src.get("allowRange", True) and range_request:
            headers["Range"] = range_request
        if not self._session:
            raise web.HTTPServiceUnavailable()
        try:
            async with self._session.request(request.method, src["url"], headers=headers, ssl=self.ssl_context,
                                             timeout=aiohttp.ClientTimeout(total=None, connect=5, sock_read=45)) as upstream:
                passthrough = {}
                for key in ("Content-Type", "Content-Length", "Content-Range", "Accept-Ranges", "ETag", "Last-Modified"):
                    if upstream.headers.get(key): passthrough[key] = upstream.headers[key]
                if not passthrough.get("Content-Type") and src.get("contentType"):
                    passthrough["Content-Type"] = str(src.get("contentType"))
                passthrough["Access-Control-Allow-Origin"] = "*"
                self._append_http_range_event({
                    "timestamp": _utc(), "sourceIdHash": source_hash, "method": str(request.method),
                    "rangeRequest": range_request, "upstreamStatus": int(upstream.status),
                    "contentType": str(upstream.headers.get("Content-Type") or src.get("contentType") or ""),
                    "contentLength": str(upstream.headers.get("Content-Length") or ""),
                    "contentRange": str(upstream.headers.get("Content-Range") or ""),
                    "acceptRanges": str(upstream.headers.get("Accept-Ranges") or ""),
                    "elapsedMs": int((time.time()-started)*1000), "error": ""
                })
                if request.method == "HEAD":
                    return web.Response(status=upstream.status, headers=passthrough)
                response = web.StreamResponse(status=upstream.status, headers=passthrough)
                await response.prepare(request)
                async for chunk in upstream.content.iter_chunked(256 * 1024):
                    await response.write(chunk)
                await response.write_eof()
                return response
        except Exception as error:
            self._append_http_range_event({
                "timestamp": _utc(), "sourceIdHash": source_hash, "method": str(request.method),
                "rangeRequest": range_request, "upstreamStatus": 0, "contentType": str(src.get("contentType") or ""),
                "contentLength": "", "contentRange": "", "acceptRanges": "",
                "elapsedMs": int((time.time()-started)*1000), "error": self._sanitize(str(error))
            })
            raise

    async def _proxy_art(self, request: web.Request):
        if request.match_info.get("token") != self._loop_token:
            raise web.HTTPForbidden()
        src = self._proxy_sources.get(request.match_info.get("sid", ""))
        if not src or src.get("kind") != "art":
            raise web.HTTPNotFound()
        if not self._session:
            raise web.HTTPServiceUnavailable()
        async with self._session.get(src["url"], headers=self._plex_headers(str(src.get("token") or ""), False), ssl=self.ssl_context) as r:
            # Keep the legacy direct-art proxy on the same proven stream-to-EOF
            # contract as the artwork cache. One StreamReader.read(n) may expose
            # only a 16/32 KiB buffered chunk on Deck/Plex.
            data = await self._read_artwork_stream(r.content, ART_MAX_BYTES)
            if len(data) > ART_MAX_BYTES:
                raise web.HTTPRequestEntityTooLarge(max_size=ART_MAX_BYTES, actual_size=len(data))
            return web.Response(body=data, status=r.status, headers={"Content-Type": r.headers.get("Content-Type", "image/jpeg"), "Cache-Control": "private, max-age=3600"})

    # ------------------------------------------------------------------
    # Audiobooks / chapters / progress
    # ------------------------------------------------------------------
    def _user_key(self) -> str:
        u = self._settings_get("active_home_user", {}) or {}
        return str(u.get("id") or u.get("uuid") or u.get("title") or "default")

    def _book_manifest_fingerprint(self, book: dict[str, Any], tracks: list[dict[str, Any]]) -> str:
        basis = {
            "book": [str(book.get("ratingKey") or ""), _as_int(book.get("updatedAt")), str(book.get("thumb") or "")],
            "tracks": [[str(t.get("ratingKey") or ""), _as_int(t.get("updatedAt")), _as_int(t.get("durationMs")),
                        str(t.get("container") or ""), str(t.get("partKey") or ""), _as_int(t.get("size"))] for t in tracks],
            "version": 3,
        }
        return hashlib.sha256(json.dumps(basis, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    def _book_resume_overlay(self, manifest: dict[str, Any]) -> dict[str, Any]:
        result = dict(manifest or {})
        files = list(result.get("files") or [])
        total_ms = max(0, int(result.get("durationMs") or 0))
        resume = None
        if self._db:
            row = self._db.execute(
                "SELECT kind,position_ms,duration_ms,chapter_index,updated_at FROM resume WHERE user_id=? AND rating_key=?",
                (self._user_key(), str(result.get("ratingKey") or "")),
            ).fetchone()
            if row:
                resume = dict(row)
        # Plex may be updated by another client after ResonaDeck saved a local
        # bookmark. Respect the newest timestamp instead of always preferring
        # the local row. When Plex has no timestamp, preserve the local progress.
        candidates = []
        for f in files:
            offset = _as_int(f.get("viewOffset"))
            if offset <= 0:
                continue
            dur = _as_int(f.get("durationMs"))
            if dur > 0 and offset >= max(0, dur - 5000):
                continue
            candidates.append((_as_int(f.get("lastViewedAt")), f, offset))
        if candidates:
            stamp, f, local_ms = max(candidates, key=lambda x: x[0])
            if not resume or (stamp > 0 and float(stamp) >= float(resume.get("updated_at") or 0)):
                resume = {
                    "kind": "audiobook",
                    "position_ms": _as_int(f.get("globalStartMs")) + local_ms,
                    "duration_ms": total_ms,
                    "chapter_index": -1,
                    "updated_at": float(stamp or 0),
                    "source": "plex-track",
                }
        global_ms = max(0, min(total_ms if total_ms > 0 else 2**63 - 1, _as_int((resume or {}).get("position_ms"))))
        active_file = None
        local_ms = 0
        for f in files:
            start = _as_int(f.get("globalStartMs")); end = _as_int(f.get("globalEndMs"))
            if global_ms < end or f is files[-1]:
                active_file = f; local_ms = max(0, global_ms - start); break
        chapters = list(result.get("chapters") or [])
        chapter_index = -1
        chapter_title = ""
        for i, ch in enumerate(chapters):
            if global_ms < _as_int(ch.get("globalEndMs")) or i == len(chapters) - 1:
                if global_ms >= _as_int(ch.get("globalStartMs")):
                    chapter_index = i; chapter_title = str(ch.get("title") or f"Chapter {i+1}")
                break
        result["resume"] = {
            "positionMs": global_ms,
            "durationMs": total_ms,
            "remainingMs": max(0, total_ms - global_ms),
            "percent": round((global_ms / total_ms * 100.0), 2) if total_ms else 0.0,
            "trackRatingKey": str((active_file or {}).get("ratingKey") or ""),
            "fileIndex": _as_int((active_file or {}).get("index"), -1),
            "localPositionMs": local_ms,
            "chapterIndex": chapter_index,
            "chapterTitle": chapter_title,
            "source": str((resume or {}).get("source") or ("resonadeck" if resume else "none")),
        }
        return result

    async def get_book_manifest(self, book_rating_key: str, refresh: bool = False):
        """Build one book-level timeline across every Plex child file.

        Embedded chapters are flattened across M4B/M4A/MP4 and ID3-capable MP3
        files. Files without embedded chapters become one logical chapter. The
        resulting global timeline is independent of Plex's physical file split.
        """
        book_key = str(book_rating_key or "").strip()
        if not book_key:
            return {"success": False, "message": "Missing book rating key"}
        lock = self._book_manifest_locks.setdefault(book_key, asyncio.Lock())
        async with lock:
            try:
                meta, children = await asyncio.gather(self.get_metadata(book_key), self.get_children(book_key))
                book = dict(meta.get("item") or {}) if isinstance(meta, dict) else {}
                tracks = [dict(x) for x in (children.get("tracks") or [])] if isinstance(children, dict) else []
                tracks.sort(key=lambda t: (_as_int(t.get("index"), 10**9), str(t.get("title") or "")))
                if not tracks and str(book.get("type") or "").lower() == "track":
                    tracks = [dict(book)]
                if not tracks:
                    return {"success": False, "message": "Plex did not expose playable audiobook files"}
                fingerprint = self._book_manifest_fingerprint(book, tracks)
                server_id, user_id = self._catalog_identity()
                if self._db and not refresh:
                    row = self._db.execute(
                        "SELECT fingerprint,payload FROM book_manifest WHERE server_id=? AND user_id=? AND book_rating_key=?",
                        (server_id, user_id, book_key),
                    ).fetchone()
                    if row and str(row["fingerprint"]) == fingerprint:
                        payload = json.loads(row["payload"])
                        return {"success": True, "manifest": self._book_resume_overlay(payload), "cached": True}

                chapter_sem = asyncio.Semaphore(2)
                async def inspect_track(i: int, track: dict[str, Any]):
                    t = dict(track); t["libraryRole"] = "audiobooks"; t["index"] = i
                    container = str(t.get("container") or "").lower().lstrip(".")
                    file_name = str(t.get("file") or "").lower()
                    ext = file_name.rsplit(".", 1)[-1] if "." in file_name else container
                    chapters = []
                    if ext in ("m4b", "m4a", "mp4", "mp3") or container in ("m4b", "m4a", "mp4", "mp3"):
                        async with chapter_sem:
                            info = await self.get_book_chapters(str(t.get("ratingKey") or ""))
                        chapters = list(info.get("chapters") or []) if isinstance(info, dict) else []
                    return t, chapters

                inspected = await asyncio.gather(*(inspect_track(i, t) for i, t in enumerate(tracks)))
                files = []
                chapters_out = []
                cursor_ms = 0
                for file_index, (track, embedded) in enumerate(inspected):
                    duration_ms = _as_int(track.get("durationMs")) or int(max(0.0, float(track.get("duration") or 0)) * 1000)
                    start_ms = cursor_ms
                    end_ms = start_ms + duration_ms
                    file_row = {
                        **track,
                        "index": file_index,
                        "globalStartMs": start_ms,
                        "globalEndMs": end_ms,
                        "durationMs": duration_ms,
                        "chapterCount": len(embedded),
                    }
                    files.append(file_row)
                    valid_embedded = []
                    for ch in embedded:
                        local_start = max(0, int(float(ch.get("start") or 0) * 1000))
                        local_end = max(local_start, int(float(ch.get("end") or 0) * 1000))
                        if duration_ms and (local_start > duration_ms + 2000 or local_end < local_start):
                            continue
                        local_end = min(duration_ms, local_end) if duration_ms else local_end
                        valid_embedded.append((ch, local_start, local_end))
                    if valid_embedded:
                        for ch, local_start, local_end in valid_embedded:
                            chapters_out.append({
                                "index": len(chapters_out),
                                "fileIndex": file_index,
                                "fileRatingKey": str(track.get("ratingKey") or ""),
                                "title": _meaningful_title(ch.get("title"), fallback=f"Chapter {len(chapters_out)+1}"),
                                "localStartMs": local_start,
                                "localEndMs": local_end,
                                "globalStartMs": start_ms + local_start,
                                "globalEndMs": start_ms + local_end,
                                "durationMs": max(0, local_end - local_start),
                                "source": "embedded",
                            })
                    else:
                        chapters_out.append({
                            "index": len(chapters_out),
                            "fileIndex": file_index,
                            "fileRatingKey": str(track.get("ratingKey") or ""),
                            "title": _meaningful_title(track.get("title"), fallback=("Full audiobook" if len(tracks) == 1 else f"Part {file_index+1}")),
                            "localStartMs": 0,
                            "localEndMs": duration_ms,
                            "globalStartMs": start_ms,
                            "globalEndMs": end_ms,
                            "durationMs": duration_ms,
                            "source": "file",
                        })
                    cursor_ms = end_ms
                # 0.8.5: physical audiobook tracks are the strongest evidence for
                # their parent book cover. A parent book row may legally carry an
                # author/collection poster, so child.parentThumb consensus wins.
                parent_cover_counts: dict[str, int] = {}
                parent_cover_order: list[str] = []
                for f in files:
                    if str(f.get("parentRatingKey") or "") not in ("", book_key):
                        continue
                    candidate = str(f.get("parentThumb") or "").strip()
                    if not candidate:
                        continue
                    if candidate not in parent_cover_counts:
                        parent_cover_counts[candidate] = 0; parent_cover_order.append(candidate)
                    parent_cover_counts[candidate] += 1
                consensus_cover = ""
                if parent_cover_order:
                    consensus_cover = sorted(parent_cover_order, key=lambda x: (-parent_cover_counts.get(x, 0), parent_cover_order.index(x)))[0]
                art_path = _first(consensus_cover, book.get("selfThumb"), book.get("thumb"), *(f.get("thumb") for f in files), book.get("parentThumb"))
                total_size = sum(max(0, _as_int(f.get("size"))) for f in files)
                weighted_bits = sum(max(0, _as_int(f.get("bitrate"))) * max(0, _as_int(f.get("durationMs"))) for f in files)
                weighted_ms = sum(max(0, _as_int(f.get("durationMs"))) for f in files if _as_int(f.get("bitrate")) > 0)
                avg_bitrate = int(round(weighted_bits / weighted_ms)) if weighted_ms else 0
                containers = sorted({str(f.get("container") or "").upper() for f in files if str(f.get("container") or "").strip()})
                manifest = {
                    "ratingKey": book_key,
                    "title": _meaningful_title(book.get("title"), tracks[0].get("album"), fallback="Audiobook"),
                    "author": _first(book.get("artist"), tracks[0].get("artist")),
                    "summary": str(book.get("summary") or ""),
                    "thumb": art_path,
                    "durationMs": cursor_ms,
                    "totalSizeBytes": total_size,
                    "averageBitrateKbps": avg_bitrate,
                    "containers": containers,
                    "fileCount": len(files),
                    "chapterCount": len(chapters_out),
                    "files": files,
                    "chapters": chapters_out,
                    "semanticType": "book",
                    "eliConfidence": 1.0,
                    "fingerprint": fingerprint,
                    "generatedAt": _utc(),
                }
                if self._db:
                    self._db.execute(
                        "INSERT OR REPLACE INTO book_manifest(server_id,user_id,book_rating_key,fingerprint,payload,updated_at) VALUES(?,?,?,?,?,?)",
                        (server_id, user_id, book_key, fingerprint, json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), time.time()),
                    )
                    self._db.commit()
                return {"success": True, "manifest": self._book_resume_overlay(manifest), "cached": False}
            except Exception as error:
                self._record("book-manifest", error)
                return {"success": False, "message": self._sanitize(str(error))}

    async def resolve_book_position(self, book_rating_key: str, position_ms: int):
        result = await self.get_book_manifest(book_rating_key, False)
        if not result.get("success"):
            return result
        manifest = result.get("manifest") or {}
        total = _as_int(manifest.get("durationMs"))
        pos = max(0, min(total if total else 2**63 - 1, int(position_ms or 0)))
        target = None
        for f in manifest.get("files") or []:
            if pos < _as_int(f.get("globalEndMs")) or f is (manifest.get("files") or [])[-1]:
                target = f; break
        if not target:
            return {"success": False, "message": "Book has no playable target"}
        local_ms = max(0, pos - _as_int(target.get("globalStartMs")))
        chapter_index = -1
        for i, ch in enumerate(manifest.get("chapters") or []):
            if pos >= _as_int(ch.get("globalStartMs")) and (pos < _as_int(ch.get("globalEndMs")) or i == len(manifest.get("chapters") or []) - 1):
                chapter_index = i; break
        return {"success": True, "bookRatingKey": str(book_rating_key), "globalPositionMs": pos,
                "track": target, "trackRatingKey": str(target.get("ratingKey") or ""),
                "localPositionMs": local_ms, "chapterIndex": chapter_index, "manifest": manifest}

    async def prepare_media(self, entries):
        """Pre-resolve media part metadata for near-viewport items.

        This moves Plex metadata discovery out of the A-button critical path.
        Parent books are intentionally not chapter-scanned here; their manifest
        is prepared when the user opens the book detail screen.
        """
        rows = entries if isinstance(entries, list) else []
        keys = []
        for raw in rows[:12]:
            if isinstance(raw, dict):
                key = str(raw.get("ratingKey") or raw.get("rating_key") or "")
                semantic = str(raw.get("semanticType") or "")
                if key and semantic not in ("book", "album", "podcast-show", "artist", "author"):
                    keys.append(key)
            elif raw:
                keys.append(str(raw))
        sem = asyncio.Semaphore(3)
        async def one(key: str):
            async with sem:
                try:
                    source = await self._media_source(key)
                    return {"ratingKey": key, "ready": True, "container": source.get("container", ""), "codec": source.get("codec", "")}
                except Exception as error:
                    return {"ratingKey": key, "ready": False, "message": self._sanitize(str(error))}
        prepared = await asyncio.gather(*(one(k) for k in dict.fromkeys(keys))) if keys else []
        return {"success": True, "prepared": prepared}

    async def prepare_playback(self, rating_key: str, capabilities: Any = None, kind: str = "music", offset_seconds: float = 0.0):
        """Prepare a complete transport plan before the user presses A.

        This is intentionally the same plan get_stream_url would produce, but
        the media-source lookup is already cached and the result carries an
        expiry hint so the frontend can use it only while it is fresh.
        """
        key = str(rating_key or "")
        kind = str(kind or "music").lower()
        if not key:
            return {"success": False, "message": "Missing Plex rating key"}
        try:
            source = await self._media_source(key)
            container = str(source.get("container") or "").lower().lstrip(".")
            # Hardware evidence from 0.8.2 showed that forcing all Books and
            # Podcasts into Plex MP3 could regress media that Direct Played
            # correctly. Prepare the normal negotiated transport first; the
            # audio engine owns recovery if that path later stalls or errors.
            plan = await self.get_stream_url(key, capabilities, False, max(0.0, float(offset_seconds or 0.0)), kind)
            if plan.get("success"):
                plan["prepared"] = True
                plan["preparedAt"] = time.time()
                plan["expiresAt"] = time.time() + 90
                plan["kind"] = kind
                plan["sourceContainer"] = container
            return plan
        except Exception as error:
            self._record("prepare-playback", error)
            return {"success": False, "message": self._sanitize(str(error))}

    async def record_playback_event(self, rating_key: str, session_id: str, event: str, elapsed_ms: int = 0, detail: Any = None):
        if self._db:
            try:
                safe_detail = json.dumps(self._sanitize_value(detail if detail is not None else {}), ensure_ascii=False, separators=(",", ":"))[:4000]
                self._db.execute(
                    "INSERT INTO playback_events(user_id,rating_key,session_id,event,elapsed_ms,detail,created_at) VALUES(?,?,?,?,?,?,?)",
                    (self._user_key(), str(rating_key or ""), str(session_id or "")[:80], str(event or "")[:80], max(0, int(elapsed_ms or 0)), safe_detail, time.time()),
                )
                # Keep this diagnostic ledger bounded.
                self._db.execute("DELETE FROM playback_events WHERE id NOT IN (SELECT id FROM playback_events ORDER BY id DESC LIMIT 1200)")
                self._db.commit()
            except Exception as error:
                self._record("playback-event", error)
        return {"success": True}

    async def get_playback_diagnostics(self, limit: int = 80):
        if not self._db:
            return {"success": True, "events": []}
        rows = self._db.execute(
            "SELECT rating_key,session_id,event,elapsed_ms,detail,created_at FROM playback_events WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (self._user_key(), max(1, min(300, int(limit or 80)))),
        ).fetchall()
        out = []
        for row in rows:
            d = dict(row)
            try: d["detail"] = json.loads(d.get("detail") or "{}")
            except Exception: pass
            out.append(d)
        return {"success": True, "events": out}

    async def report_book_progress(self, book_rating_key: str, track_rating_key: str, state: str,
                                   global_position_ms: int, local_position_ms: int, duration_ms: int,
                                   chapter_index: int = -1):
        book_key = str(book_rating_key or "")
        track_key = str(track_rating_key or "")
        await self.save_resume(book_key, "audiobook", int(global_position_ms or 0), int(duration_ms or 0), int(chapter_index or -1))
        if self._db and state in ("paused", "stopped"):
            try:
                self._db.execute("INSERT INTO book_history(user_id,book_rating_key,position_ms,state,created_at) VALUES(?,?,?,?,?)",
                                 (self._user_key(), book_key, max(0, int(global_position_ms or 0)), str(state), time.time()))
                self._db.execute("DELETE FROM book_history WHERE id NOT IN (SELECT id FROM book_history ORDER BY id DESC LIMIT 600)")
                self._db.commit()
            except Exception as error:
                self._record("book-history", error)
        if track_key:
            # Plex wants the physical child track's local time, while ResonaDeck
            # keeps a separate book-level global timeline.
            return await self.report_progress(track_key, state, int(local_position_ms or 0),
                                              _as_int((await self._media_source(track_key)).get("durationMs")), "audiobook", chapter_index)
        return {"success": True, "reported": False}

    async def add_bookmark(self, book_rating_key: str, position_ms: int, title: str = ""):
        if not self._db:
            return {"success": False, "message": "Database unavailable"}
        bookmark_id = uuid.uuid4().hex[:16]
        self._db.execute("INSERT INTO book_bookmarks(user_id,book_rating_key,bookmark_id,position_ms,title,created_at) VALUES(?,?,?,?,?,?)",
                         (self._user_key(), str(book_rating_key), bookmark_id, max(0, int(position_ms or 0)), str(title or ""), time.time()))
        self._db.commit()
        return {"success": True, "bookmarkId": bookmark_id}

    async def get_bookmarks(self, book_rating_key: str):
        if not self._db:
            return {"success": True, "bookmarks": []}
        rows = self._db.execute("SELECT bookmark_id,position_ms,title,created_at FROM book_bookmarks WHERE user_id=? AND book_rating_key=? ORDER BY position_ms ASC",
                                (self._user_key(), str(book_rating_key))).fetchall()
        return {"success": True, "bookmarks": [dict(r) for r in rows]}

    async def delete_bookmark(self, book_rating_key: str, bookmark_id: str):
        if self._db:
            self._db.execute("DELETE FROM book_bookmarks WHERE user_id=? AND book_rating_key=? AND bookmark_id=?",
                             (self._user_key(), str(book_rating_key), str(bookmark_id)))
            self._db.commit()
        return {"success": True}

    async def get_book_history(self, book_rating_key: str, limit: int = 30):
        if not self._db:
            return {"success": True, "history": []}
        rows = self._db.execute("SELECT position_ms,state,created_at FROM book_history WHERE user_id=? AND book_rating_key=? ORDER BY id DESC LIMIT ?",
                                (self._user_key(), str(book_rating_key), max(1, min(100, int(limit or 30))))).fetchall()
        return {"success": True, "history": [dict(r) for r in rows]}

    async def set_reading_list(self, book_rating_key: str, enabled: bool = True, item: Any = None):
        """Persist a local Prologue-style Reading List without mutating Plex."""
        if not self._db:
            return {"success": False, "message": "Database unavailable"}
        key = str(book_rating_key or "").strip()
        if not key:
            return {"success": False, "message": "Missing book rating key"}
        user_id = self._user_key()
        if not bool(enabled):
            self._db.execute("DELETE FROM book_reading_list WHERE user_id=? AND book_rating_key=?", (user_id, key))
            self._db.commit()
            return {"success": True, "inReadingList": False}
        payload = dict(item) if isinstance(item, dict) else {}
        payload["ratingKey"] = key
        payload["libraryRole"] = "audiobooks"
        payload["semanticType"] = "book"
        if not payload.get("title") or not payload.get("thumb"):
            try:
                result = await self.get_book_manifest(key, False)
                manifest = (result.get("manifest") or {}) if isinstance(result, dict) else {}
                payload.setdefault("title", manifest.get("title") or "Audiobook")
                payload.setdefault("artist", manifest.get("author") or "")
                payload.setdefault("thumb", manifest.get("thumb") or "")
                payload.setdefault("durationMs", _as_int(manifest.get("durationMs")))
            except Exception:
                pass
        self._db.execute(
            "INSERT OR REPLACE INTO book_reading_list(user_id,book_rating_key,payload,added_at) VALUES(?,?,?,?)",
            (user_id, key, json.dumps(self._sanitize_value(payload), ensure_ascii=False, separators=(",", ":")), time.time()),
        )
        self._db.commit()
        return {"success": True, "inReadingList": True}

    async def is_in_reading_list(self, book_rating_key: str):
        if not self._db:
            return {"success": True, "inReadingList": False}
        row = self._db.execute("SELECT 1 FROM book_reading_list WHERE user_id=? AND book_rating_key=?",
                               (self._user_key(), str(book_rating_key or ""))).fetchone()
        return {"success": True, "inReadingList": bool(row)}

    async def get_reading_list(self, limit: int = 200):
        if not self._db:
            return {"success": True, "items": []}
        rows = self._db.execute(
            "SELECT book_rating_key,payload,added_at FROM book_reading_list WHERE user_id=? ORDER BY added_at DESC LIMIT ?",
            (self._user_key(), max(1, min(500, int(limit or 200)))),
        ).fetchall()
        items = []
        for row in rows:
            try:
                item = json.loads(row["payload"] or "{}")
            except Exception:
                item = {}
            item["ratingKey"] = str(item.get("ratingKey") or row["book_rating_key"] or "")
            item["libraryRole"] = "audiobooks"
            item["semanticType"] = "book"
            item["readingListAddedAt"] = float(row["added_at"] or 0)
            items.append(item)
        return {"success": True, "items": items, "total": len(items)}

    async def get_book_chapters(self, rating_key: str):
        """Return embedded chapters from MP4/M4B or ID3 CHAP frames when available."""
        try:
            source = await self._media_source(rating_key)
            fingerprint = f"v2:{source.get('size',0)}:{source.get('partKey','')}:{source.get('updatedAt',0)}"
            if self._db and self._server.machine_id:
                row = self._db.execute("SELECT fingerprint,payload FROM chapter_cache WHERE server_id=? AND rating_key=?",
                                       (self._server.machine_id, str(rating_key))).fetchone()
                if row and row[0] == fingerprint:
                    return {"success": True, "chapters": json.loads(row[1]), "source": "cache"}
            headers = self._plex_headers(source["token"], json_accept=False)
            container = str(source.get("container") or "").lower().lstrip(".")
            file_name = str(source.get("file") or "").lower()
            ext = file_name.rsplit(".", 1)[-1] if "." in file_name else container
            chapters = []
            source_name = "none"
            if ext in ("m4b", "m4a", "mp4") or container in ("m4b", "m4a", "mp4"):
                if MP4 is not None:
                    chapters = await asyncio.to_thread(self._read_mp4_chapters, source["url"], headers)
                    source_name = "mp4"
            elif ext == "mp3" or container == "mp3":
                if ID3 is not None:
                    chapters = await asyncio.to_thread(self._read_id3_chapters, source["url"], headers, float(source.get("durationMs") or 0) / 1000.0)
                    source_name = "id3"
            clean = []
            for i, ch in enumerate(chapters or []):
                try:
                    start_s = max(0.0, float(ch.get("start") or 0))
                    end_s = max(start_s, float(ch.get("end") or 0))
                except Exception:
                    continue
                if not (start_s < 10**9 and end_s < 10**9):
                    continue
                clean.append({"index": len(clean), "title": _meaningful_title(ch.get("title"), fallback=f"Chapter {len(clean)+1}"), "start": start_s, "end": end_s})
            if self._db and self._server.machine_id:
                self._db.execute("INSERT OR REPLACE INTO chapter_cache(server_id,rating_key,fingerprint,payload,updated_at) VALUES(?,?,?,?,?)",
                                 (self._server.machine_id, str(rating_key), fingerprint, json.dumps(clean), time.time()))
                self._db.commit()
            return {"success": True, "chapters": clean, "source": source_name if clean else "none"}
        except Exception as error:
            self._record("audio-chapters", error)
            return {"success": True, "chapters": [], "source": "failed", "message": self._sanitize(str(error))}

    def _read_mp4_chapters(self, url: str, headers: dict[str, str]) -> list[dict[str, Any]]:
        if MP4 is None:
            return []
        reader = HTTPRangeReader(url, headers)
        mp4 = MP4(reader)
        out = []
        ch = getattr(mp4, "chapters", None)
        if ch:
            entries = list(ch)
            length = float(getattr(getattr(mp4, "info", None), "length", 0) or 0)
            for i, c in enumerate(entries):
                start = float(getattr(c, "start", 0) or 0)
                title = str(getattr(c, "title", "") or f"Chapter {i + 1}")
                end = float(getattr(entries[i + 1], "start", length) or length) if i + 1 < len(entries) else length
                if start < 0 or end < start:
                    continue
                out.append({"index": i, "title": title, "start": start, "end": max(start, end)})
        return out

    def _read_id3_chapters(self, url: str, headers: dict[str, str], length: float = 0.0) -> list[dict[str, Any]]:
        if ID3 is None:
            return []
        reader = HTTPRangeReader(url, headers)
        tags = ID3(fileobj=reader)
        rows = []
        for frame in tags.getall("CHAP"):
            try:
                start = max(0.0, float(getattr(frame, "start_time", 0) or 0) / 1000.0)
                raw_end = float(getattr(frame, "end_time", 0) or 0) / 1000.0
                end = max(start, raw_end if raw_end > 0 else float(length or start))
                title = ""
                sub = getattr(frame, "sub_frames", {}) or {}
                tit2 = sub.get("TIT2") if hasattr(sub, "get") else None
                if tit2 is not None:
                    title = str(tit2)
                rows.append({"title": title or f"Chapter {len(rows)+1}", "start": start, "end": end})
            except Exception:
                continue
        rows.sort(key=lambda x: float(x.get("start") or 0))
        for i, row in enumerate(rows):
            if (not row.get("end") or float(row.get("end") or 0) <= float(row.get("start") or 0)) and i + 1 < len(rows):
                row["end"] = float(rows[i + 1].get("start") or row.get("start") or 0)
            row["index"] = i
        return rows

    async def save_resume(self, rating_key: str, kind: str, position_ms: int, duration_ms: int, chapter_index: int = -1):
        if self._db:
            self._db.execute("INSERT OR REPLACE INTO resume(user_id,rating_key,kind,position_ms,duration_ms,chapter_index,updated_at) VALUES(?,?,?,?,?,?,?)",
                             (self._user_key(), str(rating_key), str(kind), max(0, int(position_ms)), max(0, int(duration_ms)), int(chapter_index), time.time()))
            self._db.commit()
        return {"success": True}

    async def get_resume(self, rating_key: str):
        if not self._db:
            return {"success": True, "resume": None}
        row = self._db.execute("SELECT kind,position_ms,duration_ms,chapter_index,updated_at FROM resume WHERE user_id=? AND rating_key=?",
                               (self._user_key(), str(rating_key))).fetchone()
        return {"success": True, "resume": dict(row) if row else None}

    async def report_progress(self, rating_key: str, state: str, position_ms: int, duration_ms: int, kind: str = "music", chapter_index: int = -1):
        await self.save_resume(rating_key, kind, position_ms, duration_ms, chapter_index)
        prefs = await self.get_preferences()
        if prefs.get("reportPlayback") is False:
            return {"success": True, "reported": False}
        if not self._server.base_url:
            return {"success": False}
        try:
            params = {
                "ratingKey": str(rating_key), "key": f"/library/metadata/{rating_key}", "state": str(state),
                "time": max(0, int(position_ms)), "duration": max(0, int(duration_ms)),
                "X-Plex-Client-Identifier": self._client_id,
            }
            async with await self._request("GET", self._server.base_url.rstrip("/") + "/:/timeline",
                                           token=self._server.access_token, params=params, json_accept=False,
                                           timeout=aiohttp.ClientTimeout(total=4, connect=2)) as r:
                await r.read()
            return {"success": True}
        except Exception as error:
            self._record("timeline", error)
            return {"success": False, "message": self._sanitize(str(error))}

    # ------------------------------------------------------------------
    # Settings / health / diagnostics
    # ------------------------------------------------------------------
    async def get_idle_messages(self):
        """Read user-editable idle quotes without touching Plex or audio playback.

        Cached by file timestamp for efficiency. Invalid edits return a safe
        fallback; no arbitrary code, HTML, or remote scripts are executed.
        """
        path = self.idle_messages_path
        try:
            stat = path.stat()
            stamp = (stat.st_mtime_ns, stat.st_size)
            if stat.st_size > 1024 * 1024:
                raise ValueError("Idle message file exceeds the 1 MB limit")
            if self._idle_messages_cached is not None and self._idle_messages_stat == stamp:
                return self._idle_messages_cached
            parsed = json.loads(path.read_text(encoding="utf-8"))
            raw = parsed.get("messages") if isinstance(parsed, dict) else parsed
            if not isinstance(raw, list):
                raise ValueError("Expected a JSON messages array")
            values = []
            seen = set()
            for value in raw[:4096]:
                if not isinstance(value, str):
                    continue
                line = " ".join(value.split())[:150]
                if not 12 <= len(line) <= 150 or line in seen:
                    continue
                seen.add(line)
                values.append(line)
            if not values:
                raise ValueError("No valid idle messages")
            result = {"ok": True, "messages": values, "count": len(values), "editableFile": str(path)}
            self._idle_messages_cached = result
            self._idle_messages_stat = stamp
            return result
        except Exception as error:
            return {"ok": False, "count": 3, "messages": [
                "There's always something wonderful waiting in your library.",
                "Your next great listening adventure is one button away.",
                "Take your time. The perfect soundtrack is worth finding."
            ], "error": str(error)[:120]}

    def _discovery_file_v11(self) -> Path:
        # Use opaque account/server identity; never store Plex auth tokens.
        try:
            server_id, user_id = self._catalog_identity()
            identity = f"{server_id}|{user_id}"
        except Exception:
            identity = "local-unconfigured"
        digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
        return self.settings_dir / f"discovery-{digest}.json"

    async def get_discovery_state(self):
        path = self._discovery_file_v11()
        try:
            value = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        except (ValueError, OSError):
            value = {}
        if not isinstance(value, dict):
            value = {}
        return {"success": True, "state": {
            "preferences": value.get("preferences", {}) if isinstance(value.get("preferences"), dict) else {},
            "favorites": value.get("favorites", []) if isinstance(value.get("favorites"), list) else [],
            "sessions": value.get("sessions", []) if isinstance(value.get("sessions"), list) else [],
            "playlists": value.get("playlists", []) if isinstance(value.get("playlists"), list) else [],
            "recentIds": value.get("recentIds", []) if isinstance(value.get("recentIds"), list) else [],
        }}

    async def save_discovery_state(self, value: Any):
        if not isinstance(value, dict):
            return {"success": False, "message": "Invalid discovery state"}
        # Allowlisted fields, bounded lists and track metadata, no stream URLs or credentials.
        fields = ("ratingKey", "title", "artist", "album", "thumb", "parentThumb", "libraryRole", "duration", "type", "kind", "grandparentRatingKey", "parentRatingKey")
        def item(row):
            if not isinstance(row, dict):
                return None
            result = {key: row[key] for key in fields if key in row and isinstance(row[key], (str, int, float)) and len(str(row[key])) <= 1024}
            return result if result.get("ratingKey") else None
        prefs = value.get("preferences") if isinstance(value.get("preferences"), dict) else {}
        safe_prefs = {
            "category": str(prefs.get("category", "music")) if prefs.get("category") in ("music", "audiobooks", "podcasts", "other", "all") else "music",
            "musicMode": str(prefs.get("musicMode", "tracks")) if prefs.get("musicMode") in ("tracks", "albums", "rediscover") else "tracks",
            "favoritesOnly": bool(prefs.get("favoritesOnly", False)),
            "count": int(prefs.get("count", 20)) if str(prefs.get("count", 20)) in ("10", "20", "40") else 20,
            "sessionLength": str(prefs.get("sessionLength", prefs.get("count", 20))) if str(prefs.get("sessionLength", prefs.get("count", 20))) in ("10", "20", "40", "30m", "60m", "120m", "endless") else "20",
            "crossfade": int(prefs.get("crossfade", 0)) if str(prefs.get("crossfade", 0)) in ("0", "3", "5", "8", "10") else 0,
            "sleepFade": bool(prefs.get("sleepFade", False)),
        }
        def collection(key, cap):
            result = []
            for row in value.get(key, [])[:cap] if isinstance(value.get(key), list) else []:
                if key == "favorites":
                    clean = item(row)
                else:
                    clean = None
                    if isinstance(row, dict):
                        tracks = [x for x in (item(x) for x in (row.get("items") or [])[:500]) if x]
                        if tracks:
                            clean = {"id": str(row.get("id", ""))[:48], "name": str(row.get("name", "Untitled"))[:90],
                                     "items": tracks, "index": min(max(0, int(row.get("index", 0))), len(tracks)-1),
                                     "position": max(0, float(row.get("position", 0))),
                                     "bookRatingKey": str(row.get("bookRatingKey", ""))[:100],
                                     "globalPosition": max(0, float(row.get("globalPosition", 0))),
                                     "shuffle": bool(row.get("shuffle", False)), "repeatMode": str(row.get("repeatMode", "off"))[:8]}
                if clean: result.append(clean)
            return result
        clean = {"preferences": safe_prefs, "favorites": collection("favorites", 5000),
                 "sessions": collection("sessions", 30), "playlists": collection("playlists", 100),
                 "recentIds": [str(x)[:64] for x in (value.get("recentIds", []) or [])[-300:] if isinstance(x, (str, int))]}
        try:
            _safe_write(self._discovery_file_v11(), clean)
            return {"success": True}
        except OSError as error:
            return {"success": False, "message": str(error)}

    async def get_preferences(self):
        defaults = {
            "notifyTrackChange": True,
            "reportPlayback": True,
            "audiobookSkipSeconds": 30,
            "audiobookSpeed": 1.0,
            "artworkTheme": True,
            "autoSignInLastUser": True,
            "appearanceMode": "auto",
            "playerVolume": 1.0,
            "audioBoostDb": 0.0,
            "audiobookBoostPercent": 170,
            "longFormAudioBoostPercent": 150,
            "normalizeLongFormLoudness": False,
            "artCacheMaxMb": 384,
            "catalogPageSize": 36,
            "preferDirectPlay": True,
        }
        saved = self._settings_get("preferences", {}) or {}
        # Only expose current standalone preferences. This intentionally drops
        # legacy experimental cross-plugin audio ownership keys if they exist.
        return {key: saved.get(key, value) for key, value in defaults.items()}

    async def set_preference(self, key: str, value: Any):
        prefs = await self.get_preferences()
        if key not in prefs:
            return {"success": False, "message": "Unknown preference"}
        prefs[key] = value
        self._settings_set("preferences", prefs)
        return {"success": True, "preferences": prefs}

    async def get_health(self, deep: bool = False):
        auth = await self.get_auth_state()
        libs = await self.get_libraries() if self._server.base_url else {"libraries": []}
        semantic_music = None
        if deep and self._server.base_url:
            try:
                section, _source, _title = await self._resolve_section_for_role("music")
                if section:
                    inspected = await self.inspect_library(section)
                    semantic_music = dict((inspected.get("library") or {}).get("counts") or {}) if inspected.get("success") else None
            except Exception as error:
                self._record("semantic-music-health", error)
        media_count = book_count = art_count = 0
        if self._db:
            try:
                media_count = int(self._db.execute("SELECT COUNT(*) FROM media_index WHERE user_id=?", (self._user_key(),)).fetchone()[0])
                book_count = int(self._db.execute("SELECT COUNT(*) FROM book_manifest WHERE user_id=?", (self._user_key(),)).fetchone()[0])
                art_count = int(self._db.execute("SELECT COUNT(*) FROM canonical_art WHERE user_id=?", (self._user_key(),)).fetchone()[0])
            except Exception:
                pass
        checks = [
            {"id": "decky", "label": "Decky backend", "status": "ok", "message": f"ResonaDeck {PLUGIN_VERSION}"},
            {"id": "readiness", "label": "1.0 readiness core", "status": "ok" if self._startup_complete and self._port and self._db else "warning", "message": "Core services ready" if self._startup_complete and self._port and self._db else "One or more core services are still starting"},
            {"id": "plex-auth", "label": "Plex account", "status": "ok" if auth["authenticated"] else "warning", "message": "Authenticated" if auth["authenticated"] else "Not connected"},
            {"id": "plex-server", "label": "Plex server", "status": "ok" if self._server.base_url else "warning", "message": self._server.name if self._server.base_url else "No active server"},
            {"id": "connection", "label": "Connection", "status": "ok" if self._server.base_url else "warning", "message": ("Local" if self._server.local else "Remote") + (" HTTPS" if self._server.secure else " HTTP") if self._server.base_url else "Unavailable"},
            {"id": "proxy", "label": "Audio proxy", "status": "ok" if self._port else "error", "message": f"127.0.0.1:{self._port}" if self._port else "Stopped"},
            {"id": "chapters", "label": "M4B chapter reader", "status": "ok" if MP4 is not None else "warning", "message": "Mutagen ready" if MP4 is not None else "Unavailable"},
            {"id": "library-cache", "label": "Living Library index", "status": "ok" if self._db else "warning", "message": f"{len([t for t in self._sync_tasks.values() if t and not t.done()])} background sync task(s)" if self._db else "Unavailable"},
            {"id": "eli-index", "label": "Eli Media Index", "status": "ok" if self._db else "warning", "message": f"{media_count} classified item(s)" if self._db else "Unavailable"},
            {"id": "book-manifests", "label": "Book Manifest Engine", "status": "ok" if self._db else "warning", "message": f"{book_count} prepared book(s)" if self._db else "Unavailable"},
            {"id": "canonical-art", "label": "Canonical Artwork Index", "status": "ok" if self._db else "warning", "message": f"{art_count} indexed artwork identity/identities" if self._db else "Unavailable"},
            {"id": "semantic-music", "label": "Semantic Music catalog", "status": "ok" if semantic_music else "warning" if deep else "ok", "message": (f"{int(semantic_music.get('artists') or 0)} artists · {int(semantic_music.get('albums') or 0)} albums · {int(semantic_music.get('tracks') or 0)} tracks" if semantic_music else "Run Checks to verify Plex Artist / Album / Track counts")},
            {"id": "playback-telemetry", "label": "Playback telemetry", "status": "ok" if self._db else "warning", "message": "Timing ledger active" if self._db else "Unavailable"},
            {"id": "art-cache", "label": "Artwork cache", "status": "ok" if self.artwork_dir.exists() else "warning", "message": f"{sum(p.stat().st_size for p in self.artwork_dir.glob('*.bin') if p.is_file()) // (1024*1024)} MB cached" if self.artwork_dir.exists() else "Unavailable"},
            {"id": "jwt", "label": "Plex auth security", "status": "ok" if _HAS_ED25519 else "warning", "message": "Ed25519/JWT capable" if _HAS_ED25519 else "Legacy PIN fallback"},
        ]
        return {"version": PLUGIN_VERSION, "generatedAt": _utc(), "checks": checks, "server": self._server_public(),
                "activeUser": self._settings_get("active_home_user", {}), "libraries": libs.get("libraries", []),
                "errors": self._errors[-10:], "proxySessions": len(self._proxy_sources)}

    async def export_hardware_evidence(self, frontend_state: Any = None):
        """Export one token-redacted bundle describing real Deck runtime behavior."""
        frontend = self._sanitize_value(frontend_state if isinstance(frontend_state, dict) else {})
        health = await self.get_health(False)
        prefs = await self.get_preferences()
        artwork_status = await self.get_artwork_status()
        semantic_music = None
        try:
            section, _source, _title = await self._resolve_section_for_role("music")
            if section:
                semantic_music = await self.inspect_library(section)
        except Exception as error:
            self._record("semantic-music-evidence", error)
        filename = f"ResonaDeck-Hardware-Evidence-{time.strftime('%Y%m%d-%H%M%S')}.zip"
        out = self.diagnostics_dir / filename

        def short_hash(value: Any) -> str:
            text = str(value or "")
            return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16] if text else ""

        auth_user = self._settings_get("active_home_user", {}) or {}
        manifest = {
            "resonadeckVersion": str(PLUGIN_VERSION),
            "buildId": "0.9.30-listening-experience",
            "timestamp": _utc(),
            "serverMachineIdHash": short_hash(self._server.machine_id or self._server.base_url),
            "userIdHash": short_hash(auth_user.get("id") or auth_user.get("uuid") or self._user_key()),
            "steamGameRunning": None,
            "notes": "token-redacted hardware evidence",
        }
        app_state = {
            "health": {"generatedAt": health.get("generatedAt", ""), "checks": health.get("checks", []), "proxySessions": health.get("proxySessions", 0)},
            "preferences": prefs,
            "artworkHydration": dict(self._art_hydration_status),
            "artworkStatus": artwork_status,
            "artworkRegistryRevision": int(self._art_registry_revision),
            "proxySessionCount": len(self._proxy_sources),
            "frontendVersion": frontend.get("frontendVersion", ""),
            "recordingStartedAt": frontend.get("startedAt", ""),
            "semanticMusicCounts": dict(((semantic_music or {}).get("library") or {}).get("counts") or {}),
        }
        selected_media = list(frontend.get("selectedMedia") or [])[:12]
        bindings = []
        for raw in list(frontend.get("artworkBindings") or [])[:80]:
            row = dict(raw or {})
            ident = str(row.get("registryIdentity") or row.get("frontendArtworkIdentity") or "")
            reg = dict(self._art_registry.get(ident) or {})
            cache_key = str(row.get("cacheKey") or reg.get("cacheKey") or "")
            if reg:
                row["registryState"] = str(reg.get("state") or row.get("registryState") or "")
                row["registryUrl"] = self._sanitize(str(reg.get("url") or row.get("registryUrl") or ""))
                row["selectedSourcePath"] = str(reg.get("resolvedPath") or row.get("selectedSourcePath") or "")
                row["cacheKey"] = cache_key
                row["bindingVersion"] = int(reg.get("revision") or row.get("bindingVersion") or 0)
            if cache_key:
                data_path, meta_path = self._art_cache_files(cache_key)
                valid, reason = self._validate_cached_art(data_path, meta_path)
                row["cacheFileExists"] = bool(data_path.is_file())
                try: row["cacheFileSize"] = int(data_path.stat().st_size) if data_path.is_file() else 0
                except Exception: row["cacheFileSize"] = 0
                row["cacheValidation"] = "valid" if valid else str(reason or "invalid")
            bindings.append(self._sanitize_value(row))
        registry_events = sorted((dict(v) for v in self._art_registry.values()), key=lambda r: int(r.get("revision") or 0))[-220:]
        artwork_events = list(frontend.get("artworkEvents") or [])[-220:] + [{
            "timestamp": _utc(), "event": "backend-registry", "identity": r.get("identity", ""),
            "role": r.get("role", ""), "state": r.get("state", ""), "ratingKey": r.get("ratingKey", ""),
            "resolvedPath": r.get("resolvedPath", ""), "cacheKey": r.get("cacheKey", ""),
            "error": r.get("errorCode", ""), "candidateErrors": r.get("candidateErrors", [])
        } for r in registry_events]
        recent_errors = list(frontend.get("recentErrors") or [])[-80:] + [
            {"timestamp": e.get("time", "") or e.get("at", ""), "subsystem": e.get("area", "backend"), "code": "BACKEND_ERROR", "message": e.get("message", ""), "context": {}}
            for e in self._errors[-80:]
        ]
        payloads = {
            "manifest.json": manifest,
            "app-state.json": app_state,
            "catalog-semantics.json": self._sanitize_value(semantic_music or {"success": False, "message": "Music library unavailable"}),
            "selected-media.json": selected_media,
            "artwork-bindings.json": bindings,
            "artwork-events.json": artwork_events[-320:],
            "playback.json": frontend.get("playback") or {},
            "seek-events.json": list(frontend.get("seekEvents") or [])[-140:],
            "http-range-events.json": list(self._http_range_events)[-180:],
            "focus-events.json": list(frontend.get("focusEvents") or [])[-180:],
            "navigation.json": frontend.get("navigation") or {},
            "gtm-focus.json": frontend.get("gtmFocus") or {},
            "recent-errors.json": recent_errors[-120:],
        }
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for name, payload in payloads.items():
                z.writestr(name, json.dumps(self._sanitize_value(payload), ensure_ascii=False, indent=2))
        desktop_path = ""
        desktop = Path(getattr(decky, "DECKY_USER_HOME", "")) / "Desktop"
        if desktop.is_dir():
            try:
                copy = desktop / filename
                shutil.copy2(out, copy)
                desktop_path = str(copy)
            except Exception as error:
                self._record("hardware-evidence-copy", error)
        return {"success": True, "path": str(out), "desktopPath": desktop_path, "filename": filename}

    async def export_diagnostics(self):
        health = await self.get_health(False)
        filename = f"ResonaDeck-Diagnostics-{time.strftime('%Y%m%d-%H%M%S')}.zip"
        out = self.diagnostics_dir / filename
        prefs = await self.get_preferences()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("health.json", json.dumps(self._sanitize_value(health), indent=2))
            z.writestr("preferences.json", json.dumps(self._sanitize_value(prefs), indent=2))
            z.writestr("errors.json", json.dumps(self._sanitize_value(self._errors), indent=2))
            playback = await self.get_playback_diagnostics(160)
            z.writestr("playback-events.json", json.dumps(self._sanitize_value(playback), indent=2))
            artwork_status = await self.get_artwork_status()
            z.writestr("artwork-status.json", json.dumps(self._sanitize_value(artwork_status), indent=2))
            # Keep a bounded registry snapshot so future hardware failures can be
            # separated into resolver, cache, delivery, and frontend-decode layers.
            registry_snapshot = sorted((dict(v) for v in self._art_registry.values()), key=lambda r: int(r.get("revision") or 0))[-400:]
            z.writestr("artwork-registry.json", json.dumps(self._sanitize_value(registry_snapshot), indent=2))
            if self._db:
                counts = {}
                for table in ("media_index", "book_manifest", "canonical_art", "book_bookmarks", "book_history"):
                    try: counts[table] = int(self._db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                    except Exception: counts[table] = -1
                z.writestr("media-core-counts.json", json.dumps(counts, indent=2))
            z.writestr("README.txt", "ResonaDeck diagnostics are redacted. Plex tokens, PINs, and device private keys are excluded. Playback timing plus Artwork Registry status are included so slow startup and missing covers can be traced without guessing.\n")
        desktop_path = ""
        desktop = Path(getattr(decky, "DECKY_USER_HOME", "")) / "Desktop"
        if desktop.is_dir():
            try:
                import shutil
                copy = desktop / filename
                shutil.copy2(out, copy)
                desktop_path = str(copy)
            except Exception as error:
                self._record("diagnostics-copy", error)
        return {"success": True, "path": str(out), "desktopPath": desktop_path, "filename": filename}
