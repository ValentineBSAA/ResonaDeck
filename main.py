"""ResonaDeck 0.9.30 Decky bootstrap.

This file is intentionally tiny. It guarantees Decky can register a Python
backend and answer `ping` even if an optional/heavy ResonaDeck dependency fails
to import on a particular SteamOS/Decky build. The full implementation lives in
resonadeck_backend.py and is loaded behind a guarded boundary.
"""
from __future__ import annotations

import asyncio
import importlib
import logging
import sys
from pathlib import Path
from typing import Any

import decky

PLUGIN_VERSION = getattr(decky, "DECKY_PLUGIN_VERSION", "1.0.0")
logger = getattr(decky, "logger", logging.getLogger(__name__))

_ROOT = str(Path(__file__).resolve().parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


class Plugin:
    def __init__(self):
        self._impl = None
        self._bootstrap_error = ""
        self._bootstrap_ready = False

    async def _main(self):
        logger.info("ResonaDeck bootstrap starting %s", PLUGIN_VERSION)
        try:
            module = importlib.import_module("resonadeck_backend")
            impl_cls = getattr(module, "Plugin")
            self._impl = impl_cls()
            await self._impl._main()
            self._bootstrap_ready = True
            logger.info("ResonaDeck bootstrap attached full backend")
        except Exception as error:
            self._impl = None
            self._bootstrap_ready = False
            self._bootstrap_error = f"{type(error).__name__}: {error}"
            logger.exception("ResonaDeck backend bootstrap failed")

    async def _unload(self):
        if self._impl is not None:
            try:
                await self._impl._unload()
            except Exception:
                logger.exception("ResonaDeck backend unload failed")
        self._impl = None

    async def ping(self):
        if self._impl is None:
            return {
                "ok": False,
                "version": str(PLUGIN_VERSION),
                "bootstrapReady": False,
                "bootstrapError": self._bootstrap_error or "Full backend has not attached yet",
                "errors": [],
            }
        try:
            result = await self._impl.ping()
            if not isinstance(result, dict):
                result = {"ok": True}
            result["bootstrapReady"] = True
            result["bootstrapError"] = ""
            return result
        except Exception as error:
            return {
                "ok": False,
                "version": str(PLUGIN_VERSION),
                "bootstrapReady": True,
                "bootstrapError": f"{type(error).__name__}: {error}",
                "errors": [],
            }

    async def _forward(self, method: str, *args: Any):
        if self._impl is None:
            raise RuntimeError(self._bootstrap_error or "ResonaDeck full backend is unavailable")
        fn = getattr(self._impl, method, None)
        if fn is None:
            raise AttributeError(f"ResonaDeck backend method not found: {method}")
        result = fn(*args)
        if asyncio.iscoroutine(result):
            return await result
        return result

    async def begin_plex_auth(self): return await self._forward("begin_plex_auth")
    async def poll_plex_auth(self): return await self._forward("poll_plex_auth")
    async def sign_out(self): return await self._forward("sign_out")
    async def get_auth_state(self): return await self._forward("get_auth_state")
    async def get_home_users(self): return await self._forward("get_home_users")
    async def switch_home_user(self, user_id: str, pin: str = ""): return await self._forward("switch_home_user", user_id, pin)
    async def discover_servers(self): return await self._forward("discover_servers")
    async def select_server(self, machine_id: str): return await self._forward("select_server", machine_id)
    async def recover_connection(self): return await self._forward("recover_connection")
    async def get_libraries(self): return await self._forward("get_libraries")
    async def inspect_library(self, section_key: str): return await self._forward("inspect_library", section_key)
    async def set_library_role(self, section_key: str, title: str, role: str): return await self._forward("set_library_role", section_key, title, role)
    async def browse_library(self, role: str, view: str = "home", query: str = "", offset: int = 0, limit: int = 60): return await self._forward("browse_library", role, view, query, offset, limit)
    async def browse_section(self, section_key: str, view: str = "albums", query: str = "", offset: int = 0, limit: int = 36, sort: str = "title"): return await self._forward("browse_section", section_key, view, query, offset, limit, sort)
    async def browse_cached(self, role: str, view: str = "albums", offset: int = 0, limit: int = 40, sort: str = "title", refresh: bool = False, section_key: str = ""): return await self._forward("browse_cached", role, view, offset, limit, sort, refresh, section_key)
    async def get_sync_status(self): return await self._forward("get_sync_status")
    async def refresh_library_cache(self, role: str, view: str = "albums"): return await self._forward("refresh_library_cache", role, view)
    async def refresh_music_state(self, force: bool = False): return await self._forward("refresh_music_state", force)
    async def get_continue_listening(self, role: str = "audiobooks", limit: int = 12): return await self._forward("get_continue_listening", role, limit)
    async def get_children(self, rating_key: str): return await self._forward("get_children", rating_key)
    async def get_artist_tracks(self, rating_key: str): return await self._forward("get_artist_tracks", rating_key)
    async def resolve_fresh_track(self, rating_key: str, title: str = "", artist: str = "", album: str = ""): return await self._forward("resolve_fresh_track", rating_key, title, artist, album)
    async def get_metadata(self, rating_key: str): return await self._forward("get_metadata", rating_key)
    async def get_genres(self, role: str = "music"): return await self._forward("get_genres", role)
    async def get_genre_tracks(self, genre_key: str, role: str = "music"): return await self._forward("get_genre_tracks", genre_key, role)
    async def get_playlists(self): return await self._forward("get_playlists")
    async def get_playlist_items(self, rating_key: str): return await self._forward("get_playlist_items", rating_key)
    async def search(self, query: str, scope: str = "everything"): return await self._forward("search", query, scope)
    async def search_cached(self, query: str, scope: str = "everything", limit: int = 80): return await self._forward("search_cached", query, scope, limit)
    async def get_stream_url(self, rating_key: str, capabilities: Any = None, force_transcode: bool = False, offset_seconds: float = 0.0, kind: str = ""): return await self._forward("get_stream_url", rating_key, capabilities, force_transcode, offset_seconds, kind)
    async def get_art_url(self, path: str, mode: str = "square", rating_key: str = "", repair: bool = False, role: str = ""): return await self._forward("get_art_url", path, mode, rating_key, repair, role)
    async def get_artwork_record(self, path: str, mode: str = "square", rating_key: str = "", repair: bool = False, role: str = "", title: str = ""): return await self._forward("get_artwork_record", path, mode, rating_key, repair, role, title)
    async def get_artwork_updates(self, since_revision: int = 0): return await self._forward("get_artwork_updates", since_revision)
    async def prefetch_artwork(self, entries): return await self._forward("prefetch_artwork", entries)
    async def get_artwork_status(self): return await self._forward("get_artwork_status")
    async def start_artwork_hydration(self, force: bool = False, rescan: bool = False): return await self._forward("start_artwork_hydration", force, rescan)
    async def eli_classify(self, rating_key: str, role: str = ""): return await self._forward("eli_classify", rating_key, role)
    async def get_book_manifest(self, book_rating_key: str, refresh: bool = False): return await self._forward("get_book_manifest", book_rating_key, refresh)
    async def resolve_book_position(self, book_rating_key: str, position_ms: int): return await self._forward("resolve_book_position", book_rating_key, position_ms)
    async def prepare_media(self, entries): return await self._forward("prepare_media", entries)
    async def prepare_playback(self, rating_key: str, capabilities: Any = None, kind: str = "music", offset_seconds: float = 0.0): return await self._forward("prepare_playback", rating_key, capabilities, kind, offset_seconds)
    async def record_playback_event(self, rating_key: str, session_id: str, event: str, elapsed_ms: int = 0, detail: Any = None): return await self._forward("record_playback_event", rating_key, session_id, event, elapsed_ms, detail)
    async def get_playback_diagnostics(self, limit: int = 80): return await self._forward("get_playback_diagnostics", limit)
    async def report_book_progress(self, book_rating_key: str, track_rating_key: str, state: str, global_position_ms: int, local_position_ms: int, duration_ms: int, chapter_index: int = -1): return await self._forward("report_book_progress", book_rating_key, track_rating_key, state, global_position_ms, local_position_ms, duration_ms, chapter_index)
    async def add_bookmark(self, book_rating_key: str, position_ms: int, title: str = ""): return await self._forward("add_bookmark", book_rating_key, position_ms, title)
    async def get_bookmarks(self, book_rating_key: str): return await self._forward("get_bookmarks", book_rating_key)
    async def delete_bookmark(self, book_rating_key: str, bookmark_id: str): return await self._forward("delete_bookmark", book_rating_key, bookmark_id)
    async def get_book_history(self, book_rating_key: str, limit: int = 30): return await self._forward("get_book_history", book_rating_key, limit)
    async def set_reading_list(self, book_rating_key: str, enabled: bool = True, item: Any = None): return await self._forward("set_reading_list", book_rating_key, enabled, item)
    async def is_in_reading_list(self, book_rating_key: str): return await self._forward("is_in_reading_list", book_rating_key)
    async def get_reading_list(self, limit: int = 200): return await self._forward("get_reading_list", limit)
    async def get_book_chapters(self, rating_key: str): return await self._forward("get_book_chapters", rating_key)
    async def save_resume(self, rating_key: str, kind: str, position_ms: int, duration_ms: int, chapter_index: int = -1): return await self._forward("save_resume", rating_key, kind, position_ms, duration_ms, chapter_index)
    async def get_resume(self, rating_key: str): return await self._forward("get_resume", rating_key)
    async def report_progress(self, rating_key: str, state: str, position_ms: int, duration_ms: int, kind: str = "music", chapter_index: int = -1): return await self._forward("report_progress", rating_key, state, position_ms, duration_ms, kind, chapter_index)
    async def get_preferences(self): return await self._forward("get_preferences")
    async def set_preference(self, key: str, value: Any): return await self._forward("set_preference", key, value)
    async def get_health(self, deep: bool = False): return await self._forward("get_health", deep)
    async def export_hardware_evidence(self, frontend_state: Any = None): return await self._forward("export_hardware_evidence", frontend_state)
    async def export_diagnostics(self): return await self._forward("export_diagnostics")
