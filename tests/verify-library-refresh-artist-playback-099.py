"""Focused 0.9.9 backend checks using the real methods with bounded fixtures."""
from __future__ import annotations
import asyncio, importlib.util, logging, sys, tempfile, types, xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
decky=types.ModuleType('decky')
decky.DECKY_PLUGIN_VERSION='0.9.9-test'
decky.DECKY_PLUGIN_RUNTIME_DIR='/tmp/resonadeck099-runtime'
decky.DECKY_PLUGIN_SETTINGS_DIR='/tmp/resonadeck099-settings'
decky.DECKY_PLUGIN_LOG_DIR='/tmp/resonadeck099-log'
decky.DECKY_USER_HOME='/tmp'
decky.logger=logging.getLogger('resonadeck099-test')
sys.modules['decky']=decky
spec=importlib.util.spec_from_file_location('resonadeck_backend_099',ROOT/'resonadeck_backend.py')
rb=importlib.util.module_from_spec(spec); assert spec and spec.loader
sys.modules[spec.name]=rb; spec.loader.exec_module(rb)

class Content:
    async def read(self,n=-1): return b'x'
class Response:
    def __init__(self,status): self.status=status; self.content=Content()
    async def __aenter__(self): return self
    async def __aexit__(self,*_): return False
class Session:
    def request(self,method,url,**kwargs):
        return Response(404 if 'old-part' in url else 206)

async def main():
    assert rb.CATALOG_CACHE_GENERATION=='0.9.9-refresh-v1'
    assert rb.ARTWORK_HYDRATION_GENERATION=='0.9.9-library-refresh-v1'
    with tempfile.TemporaryDirectory() as tmp:
        decky.DECKY_PLUGIN_RUNTIME_DIR=str(Path(tmp)/'runtime')
        decky.DECKY_PLUGIN_SETTINGS_DIR=str(Path(tmp)/'settings')
        decky.DECKY_PLUGIN_LOG_DIR=str(Path(tmp)/'log')
        p=rb.Plugin(); p._server=rb.ServerState(base_url='http://plex.test',access_token='fixture',machine_id='server-1')
        p._session=Session(); p._db=None; p._record=lambda *_a,**_k:None; p._role=lambda _s:'music'; p._user_key=lambda:'user-1'

        # Music transport must bypass the 15-minute Media/Part cache.
        refresh_flags=[]
        async def source(key,refresh=False):
            refresh_flags.append(bool(refresh)); return {'url':'http://plex.test/new-part','token':'fixture','partKey':'/new-part','container':'mp3','codec':'mp3','bitrate':320,'size':1,'file':'x.mp3','durationMs':1000,'updatedAt':1}
        p._media_source=source
        p._register_proxy=lambda kind,url,token,content_type='',allow_range=True: f'http://127.0.0.1/{kind}/fixture'
        async def prefs(): return {'audiobookBoostPercent':170}
        p.get_preferences=prefs
        async def trans(*_a,**_k): return ('http://plex.test/trans.mp3','sid',100,False,True,'ok')
        p._select_music_transcode_profile=trans
        plan=await p.get_stream_url('track-1',{'mp3':True},False,0,'music')
        assert plan['success'] and refresh_flags==[True], (plan,refresh_flags)

        # Artist playback uses the semantic allLeaves path.
        calls=[]
        async def artist_xml(path,params=None,**_kw):
            calls.append(path)
            return ET.fromstring('<MediaContainer><Track ratingKey="t1" type="track" title="One" grandparentTitle="Artist"/><Track ratingKey="t2" type="track" title="Two" grandparentTitle="Artist"/></MediaContainer>')
        p._pms_xml=artist_xml
        artists=await p.get_artist_tracks('artist-1')
        assert artists['success'] and len(artists['tracks'])==2 and any(x.endswith('/library/metadata/artist-1/allLeaves') for x in calls), (artists,calls)

        # Stale source: old key validates to HTTP 404, semantic search returns a
        # new key whose Part validates. The queue can therefore be repaired.
        async def stale_source(key,refresh=False):
            part='old-part' if str(key)=='old' else 'new-part'
            return {'url':f'http://plex.test/{part}','token':'fixture','partKey':f'/{part}','container':'mp3','codec':'mp3','bitrate':320,'size':1,'file':f'{part}.mp3','durationMs':1000,'updatedAt':2}
        p._media_source=stale_source
        async def search_xml(path,params=None,**_kw):
            return ET.fromstring('<MediaContainer><Track ratingKey="new" type="track" title="Pretty in Red" grandparentTitle="vampp" parentTitle="Pretty in Red - Single"><Media container="mp3"><Part key="/new-part" file="new.mp3"/></Media></Track></MediaContainer>')
        p._pms_xml=search_xml
        async def resolve_role(_role): return ('7','fixture','Music')
        p._resolve_section_for_role=resolve_role
        p.refresh_music_state=lambda force=False: asyncio.sleep(0, result={'success':True})
        repaired=await p.resolve_fresh_track('old','Pretty in Red','vampp','Pretty in Red - Single')
        assert repaired['success'] and repaired['item']['ratingKey']=='new' and repaired['replaced'] and repaired['verifiedPart'], repaired

    print('PASS: 0.9.9 refreshes Music Media/Part identity, loads artist allLeaves, and repairs a stale 404 track with a verified semantic replacement. Hardware NOT tested.')

asyncio.run(main())
