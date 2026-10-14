"""Run the 0.9.5 backend artwork worker methods with deterministic Plex/cache fixtures.
No live server, credentials, network, or Steam hardware is used.
"""
import ast
import asyncio
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

source = Path(__file__).resolve().parents[1] / 'resonadeck_backend.py'
tree = ast.parse(source.read_text())
names = {'start_artwork_hydration', '_artwork_hydration_worker', 'get_artwork_status'}
methods = [n for c in tree.body if isinstance(c, ast.ClassDef) for n in c.body if isinstance(n, ast.AsyncFunctionDef) and n.name in names]
assert len(methods) == 3
namespace = {'asyncio': asyncio, 'time': time, 'Any': Any, 'ARTWORK_HYDRATION_GENERATION': '0.9.9-library-refresh-v1', '_first': lambda *xs: next((x for x in xs if x), '')}
exec(compile(ast.fix_missing_locations(ast.Module(body=methods, type_ignores=[])), str(source), 'exec'), namespace)

async def run():
    with tempfile.TemporaryDirectory() as tmp:
        cover = Path(tmp) / 'cover'; cover.write_bytes(b'fixture')
        obj = SimpleNamespace(_art_hydration_task=None, _art_hydration_status={'state': 'idle'}, _server=SimpleNamespace(base_url='http://fixture', machine_id='fixture'), _session=object(), _art_registry={}, _art_registry_revision=0, _art_prefetch_tasks={}, _art_candidate_cache={}, _port=1, _loop_token='fixture')
        for name in names:
            setattr(obj, name, namespace[name].__get__(obj))
        saved = {}; obj._settings_get = lambda key, default: saved.get(key, default)
        obj._settings_set = lambda key, value: saved.__setitem__(key, value)
        obj._user_key = lambda: 'fixture-user'
        errors = []; obj._record = lambda *args: errors.append(args)
        fixtures = {'music': [{'ratingKey': str(i), 'title': f'Album {i}', 'thumb': f'/album/{i}', **({'artRegistryState':'ready','cachedArtUrl':'/cached/existing'} if i == 0 else {})} for i in range(144)], 'audiobooks': [{'ratingKey': 'book1', 'title': 'Working sibling', 'thumb': '/book1'}, {'ratingKey': 'book2', 'title': 'Synthetic missing metadata', 'thumb': ''}], 'podcasts': [], 'other': []}
        async def browse(role, view, offset, limit, *_):
            return {'success': True, 'total': len(fixtures[role]), 'items': fixtures[role][offset:offset+limit]}
        obj.browse_cached = browse
        async def resolve(path, key, role, repair):
            await asyncio.sleep(0)
            return [path] if path else []
        obj._resolve_art_candidates = resolve
        obj._remember_art_candidates = lambda candidates, **kw: kw['identity']
        obj._art_registry_identity = lambda path, key, role, mode: f'{role}|{key}|{mode}'
        def publish(identity, **fields):
            obj._art_registry_revision += 1
            rec = {'identity': identity, 'revision': obj._art_registry_revision, **fields}
            obj._art_registry[identity] = rec
            return rec
        obj._art_registry_publish = publish
        obj._art_cache_files = lambda key: (cover, cover)
        obj._validate_cached_art = lambda *args: (False, 'image/jpeg')
        active = maximum = 0; fetched = []
        async def fetch(key):
            nonlocal active, maximum
            active += 1; maximum = max(maximum, active)
            await asyncio.sleep(0)
            active -= 1; fetched.append(key)
            return cover, 'image/jpeg'
        obj._ensure_art_cached = fetch
        def ready(identity, key, role, mode, rating_key, *args):
            return publish(identity, state='ready', role=role, ratingKey=rating_key, url='/cached/'+key)
        obj._art_registry_ready_record = ready
        # Missing Plex session defers startup; restoring it starts the existing worker.
        # An old complete generation with failures must not suppress the 0.9.8 migration pass.
        saved['artworkHydrationState'] = {'generation':'0.8.3-artwork-v1','server':'fixture','user':'fixture-user','complete':True,'failed':9}
        obj._session = None
        assert (await obj.start_artwork_hydration(False))['state'] == 'waiting'
        assert obj._art_hydration_task is None
        obj._session = object()
        await obj.start_artwork_hydration(False)
        assert obj._art_hydration_task is not None
        await obj._art_hydration_task
        status = await obj.get_artwork_status()
        assert not errors, errors
        assert status['state'] == 'ready' and not status['active']
        assert status['done'] == 146 and status['cached'] == 145 and status['fallback'] == 1 and status['failed'] == 0
        assert maximum == 2 and '143|music' in fetched and '0|music' not in fetched
        assert obj._art_registry['audiobooks|book1|portrait-book-v85']['state'] == 'ready'
        assert obj._art_registry['audiobooks|book2|portrait-book-v85']['state'] == 'fallback' and obj._art_registry['audiobooks|book2|portrait-book-v85']['errorCode'] == 'NO_CANONICAL_ART'
        # Saved current-generation terminal fallback restores as healthy READY, not a transport failure.
        obj._art_hydration_status = {'state': 'idle'}; obj._art_hydration_task = None
        restored = await obj.start_artwork_hydration(False)
        assert restored['state'] == 'ready' and restored['fallback'] == 1 and restored['failed'] == 0
        assert obj._art_hydration_task is None
        print('PASS: 0.9.8 generation migration, READY-cache reuse, two-slot hydration, Book fallback outcomes, and saved terminal-fallback restore. Hardware NOT tested.')

asyncio.run(run())
