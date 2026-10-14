"""0.9.8 semantic Music catalog checks against the real backend methods."""
from __future__ import annotations
import asyncio, importlib.util, logging, sys, tempfile, types, xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
decky=types.ModuleType('decky')
decky.DECKY_PLUGIN_VERSION='0.9.8-test'
decky.DECKY_PLUGIN_RUNTIME_DIR='/tmp/resonadeck098-runtime'
decky.DECKY_PLUGIN_SETTINGS_DIR='/tmp/resonadeck098-settings'
decky.DECKY_PLUGIN_LOG_DIR='/tmp/resonadeck098-log'
decky.DECKY_USER_HOME='/tmp'
decky.logger=logging.getLogger('resonadeck098-test')
sys.modules['decky']=decky
spec=importlib.util.spec_from_file_location('resonadeck_backend_098',ROOT/'resonadeck_backend.py')
rb=importlib.util.module_from_spec(spec); assert spec and spec.loader
sys.modules[spec.name]=rb; spec.loader.exec_module(rb)

def make_plugin(tmp):
    decky.DECKY_PLUGIN_RUNTIME_DIR=str(Path(tmp)/'runtime')
    decky.DECKY_PLUGIN_SETTINGS_DIR=str(Path(tmp)/'settings')
    decky.DECKY_PLUGIN_LOG_DIR=str(Path(tmp)/'log')
    p=rb.Plugin(); p._server=rb.ServerState(base_url='http://plex.test',access_token='fixture',machine_id='server-1')
    p._session=object(); p._db=None; p._user_key=lambda:'user-1'; p._record=lambda *_a,**_k:None; p._role=lambda _s:'music'
    return p

async def main():
    assert rb.CATALOG_CACHE_GENERATION=='0.9.9-refresh-v1'
    assert rb.ARTWORK_HYDRATION_GENERATION=='0.9.9-library-refresh-v1'
    with tempfile.TemporaryDirectory() as tmp:
        p=make_plugin(tmp)
        calls=[]
        async def fake_xml(path, params=None, **_kw):
            calls.append((path,dict(params or {})))
            return ET.fromstring('''<MediaContainer size="3" totalSize="3" offset="0">
              <Directory ratingKey="album-1" type="album" title="Very Static" thumb="/library/metadata/album-1/thumb/1" />
              <Directory ratingKey="folder-1" type="folder" title="Music ds" />
              <Directory ratingKey="dir-2" type="directory" title="Garden Alt" />
            </MediaContainer>''')
        p._pms_xml=fake_xml
        r=await p.browse_section('7','albums','',0,40,'title','music')
        assert r['success'] and [x['title'] for x in r['items']]==['Very Static','Music ds','Garden Alt'], r
        assert calls[0][0].endswith('/library/sections/7/all'), calls
        assert calls[0][1].get('type')==9, calls
        assert p._is_semantic_music_album(r['items'][0])
        assert not p._is_semantic_music_album(r['items'][1]) and not p._is_semantic_music_album(r['items'][2])
        album=r['items'][0]
        assert album['plexType']=='album' and p._eli_classify_item(album,'music','albums')['semanticType']=='album'
        ghost=p._eli_classify_item({'title':'Music ds','type':'folder','plexType':'folder'},'music','albums')
        assert ghost['semanticType']=='filesystem-directory', ghost

        # Track retrieval is semantic type=10 and therefore independent of how
        # deeply the file sits under Artist/Album/Alt/per-track folders.
        calls.clear()
        async def track_xml(path, params=None, **_kw):
            calls.append((path,dict(params or {})))
            return ET.fromstring('''<MediaContainer size="2" totalSize="2" offset="0">
              <Track ratingKey="t1" type="track" title="Bury Me in the Light" parentTitle="The Light"><Media container="flac"><Part key="/library/parts/1" file="/Music ds/Vera Static/004 The Light/01 - Bury Me in the Light/song.flac" /></Media></Track>
              <Track ratingKey="t2" type="track" title="Alt Mix" parentTitle="The Garden Has Teeth"><Media container="flac"><Part key="/library/parts/2" file="/Music ds/Vera Static/003 The Garden Has Teeth/Garden Alt/Alt Mix.flac" /></Media></Track>
            </MediaContainer>''')
        p._pms_xml=track_xml
        t=await p.browse_section('7','tracks','',0,40,'title','music')
        assert len(t['items'])==2 and calls[0][1].get('type')==10, (t,calls)
        assert all(x['type']=='track' for x in t['items'])

    print('PASS: 0.9.8 Music Albums use Plex type=9, raw directories are not albums, and nested/alternate tracks remain visible through type=10. Hardware NOT tested.')

asyncio.run(main())
