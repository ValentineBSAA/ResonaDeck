"""Focused 0.9.4 backend checks using the real Music artwork resolver.
No live Plex server, credentials, or Steam Deck hardware is used.
"""
from __future__ import annotations

import asyncio
import importlib.util
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Minimal Decky shim so the real backend module can be imported in CI/chat.
decky = types.ModuleType("decky")
decky.DECKY_PLUGIN_VERSION = "0.9.8-test"
decky.DECKY_PLUGIN_RUNTIME_DIR = "/tmp/resonadeck-test-runtime"
decky.DECKY_PLUGIN_SETTINGS_DIR = "/tmp/resonadeck-test-settings"
decky.DECKY_PLUGIN_LOG_DIR = "/tmp/resonadeck-test-log"
decky.DECKY_USER_HOME = "/tmp"
decky.logger = __import__("logging").getLogger("resonadeck-test")
sys.modules["decky"] = decky

spec = importlib.util.spec_from_file_location("resonadeck_backend_v094", ROOT / "resonadeck_backend.py")
rb = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = rb
spec.loader.exec_module(rb)


def make_plugin(tmp: str):
    decky.DECKY_PLUGIN_RUNTIME_DIR = str(Path(tmp) / "runtime")
    decky.DECKY_PLUGIN_SETTINGS_DIR = str(Path(tmp) / "settings")
    decky.DECKY_PLUGIN_LOG_DIR = str(Path(tmp) / "log")
    p = rb.Plugin()
    p._server = rb.ServerState(base_url="http://plex.test", access_token="fixture", machine_id="server-1")
    p._session = object()
    p._db = None
    p._user_key = lambda: "user-1"
    p._record = lambda *_args, **_kwargs: None
    return p


async def resolver_checks():
    with tempfile.TemporaryDirectory() as tmp:
        p = make_plugin(tmp)
        album = {
            "type": "album", "ratingKey": "album", "parentRatingKey": "artist",
            "selfThumb": "/library/metadata/album/thumb/111",
            "thumb": "/library/metadata/album/thumb/111",
            "parentThumb": "/library/metadata/artist/thumb/333",
        }
        artist = {"type": "artist", "ratingKey": "artist", "thumb": "/library/metadata/artist/thumb/333"}
        children = [
            {"type": "track", "ratingKey": f"track-{i}", "parentRatingKey": "album", "parentThumb": "/library/metadata/album/thumb/222"}
            for i in range(4)
        ]

        async def metadata(key: str):
            return {"item": album if key == "album" else artist if key == "artist" else {}}

        async def child_sample(key: str, _limit: int = 8):
            return children if key == "album" else []

        p.get_metadata = metadata
        p._art_children_sample = child_sample

        # Real deep resolver: Album-owned cover and exact Album endpoint must beat Artist art.
        candidates = await p._resolve_art_candidates(album["thumb"], "album", "music", True)
        assert candidates[0] == "/library/metadata/album/thumb/111", candidates
        assert candidates.index("/library/metadata/album/thumb") < candidates.index("/library/metadata/artist/thumb/333"), candidates
        assert candidates.index("/library/metadata/album/thumb/222") < candidates.index("/library/metadata/artist/thumb/333"), candidates

        # Normal path stays lightweight and owner-specific rather than walking Artist metadata.
        p._art_candidate_cache.clear()
        normal = await p._resolve_art_candidates(album["thumb"], "album", "music", False)
        assert normal[:2] == ["/library/metadata/album/thumb/111", "/library/metadata/album/thumb"], normal

        # Album with no own thumb uses exact Album endpoint, then child parentThumb, before Artist fallback.
        p._art_candidate_cache.clear()
        no_own = {**album, "selfThumb": "", "thumb": "", "parentThumb": "/library/metadata/artist/thumb/333"}
        async def metadata_no_own(key: str):
            return {"item": no_own if key == "album" else artist if key == "artist" else {}}
        p.get_metadata = metadata_no_own
        repaired = await p._resolve_art_candidates("", "album", "music", True)
        assert repaired[0] == "/library/metadata/album/thumb", repaired
        assert repaired.index("/library/metadata/album/thumb/222") < repaired.index("/library/metadata/artist/thumb/333"), repaired

        # A Track still inherits its Album, proving the album-parent rule was not removed from tracks.
        p._art_candidate_cache.clear()
        track = {"type": "track", "ratingKey": "track", "parentRatingKey": "album", "thumb": "/library/metadata/track/thumb/1"}
        async def metadata_track(key: str):
            if key == "track": return {"item": track}
            if key == "album": return {"item": album}
            return {"item": artist}
        p.get_metadata = metadata_track
        p._art_children_sample = lambda *_args, **_kwargs: asyncio.sleep(0, result=[])
        track_candidates = await p._resolve_art_candidates(track["thumb"], "track", "music", True)
        album_positions = [i for i, c in enumerate(track_candidates) if p._art_path_owner_key(c) == "album"]
        track_positions = [i for i, c in enumerate(track_candidates) if p._art_path_owner_key(c) == "track"]
        assert album_positions and track_positions and min(album_positions) < min(track_positions), track_candidates


async def hydration_generation_checks():
    with tempfile.TemporaryDirectory() as tmp:
        p = make_plugin(tmp)
        saved = {
            "artworkHydrationState": {
                "generation": "0.8.3-artwork-v1", "server": "server-1", "user": "user-1",
                "complete": True, "done": 144, "total": 144, "cached": 12, "failed": 132,
            }
        }
        p._settings_get = lambda key, default: saved.get(key, default)
        p._settings_set = lambda key, value: saved.__setitem__(key, value)
        ran = []
        async def worker(force=False):
            ran.append(force)
            p._art_hydration_status.update({"state": "ready", "generation": rb.ARTWORK_HYDRATION_GENERATION})
        p._artwork_hydration_worker = worker
        await p.start_artwork_hydration(False)
        assert p._art_hydration_task is not None, "old 0.8.3 completion incorrectly blocked 0.9.8 migration"
        await p._art_hydration_task
        assert ran == [False]

    with tempfile.TemporaryDirectory() as tmp:
        p = make_plugin(tmp)
        saved = {
            "artworkHydrationState": {
                "generation": rb.ARTWORK_HYDRATION_GENERATION, "server": "server-1", "user": "user-1",
                "complete": True, "done": 144, "total": 144, "cached": 140, "failed": 4,
                "roles": {"music": {"done": 144, "total": 144, "cached": 140, "failed": 4}},
            }
        }
        p._settings_get = lambda key, default: saved.get(key, default)
        p._settings_set = lambda key, value: saved.__setitem__(key, value)
        state = await p.start_artwork_hydration(False)
        assert state["state"] == "partial" and state["failed"] == 4, state
        assert p._art_hydration_task is None, "same-generation partial state should not rerun the full library forever"


async def valid_cache_reuse_check():
    with tempfile.TemporaryDirectory() as tmp:
        p = make_plugin(tmp)
        p._settings_set = lambda *_args: None
        fixtures = {
            "music": [{"ratingKey": "album", "title": "Cached Album", "thumb": "/library/metadata/album/thumb/1", "artRegistryState": "ready", "cachedArtUrl": "http://127.0.0.1/cached"}],
            "audiobooks": [], "podcasts": [], "other": [],
        }
        async def browse(role, _view, offset, limit, *_args):
            rows = fixtures[role]
            return {"success": True, "total": len(rows), "items": rows[offset:offset+limit]}
        p.browse_cached = browse
        async def forbidden(*_args, **_kwargs):
            raise AssertionError("validated READY artwork was unnecessarily re-resolved/redownloaded")
        p._resolve_art_candidates = forbidden
        p._ensure_art_cached = forbidden
        await p._artwork_hydration_worker(False)
        assert p._art_hydration_status["cached"] == 1
        assert p._art_hydration_status["failed"] == 0
        assert p._art_hydration_status["state"] == "ready"


async def main():
    assert rb.ARTWORK_HYDRATION_GENERATION == "0.9.9-library-refresh-v1"
    await resolver_checks()
    await hydration_generation_checks()
    await valid_cache_reuse_check()
    print("PASS: real Music resolver keeps Album ownership ahead of Artist art; track inheritance remains; old 0.8.3 completion triggers one migration; same-generation failures restore PARTIAL; valid READY cache is reused. Hardware NOT tested.")


asyncio.run(main())
