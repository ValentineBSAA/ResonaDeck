from __future__ import annotations
import asyncio, importlib.util, logging, sys, tempfile, types, xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
decky=types.ModuleType('decky')
decky.DECKY_PLUGIN_VERSION='0.9.10-test'
decky.DECKY_PLUGIN_RUNTIME_DIR='/tmp/resonadeck010-runtime'
decky.DECKY_PLUGIN_SETTINGS_DIR='/tmp/resonadeck010-settings'
decky.DECKY_PLUGIN_LOG_DIR='/tmp/resonadeck010-log'
decky.DECKY_USER_HOME='/tmp'
decky.logger=logging.getLogger('resonadeck010-test')
sys.modules['decky']=decky
spec=importlib.util.spec_from_file_location('resonadeck_backend_010',ROOT/'resonadeck_backend.py')
rb=importlib.util.module_from_spec(spec); assert spec and spec.loader
sys.modules[spec.name]=rb; spec.loader.exec_module(rb)

async def main():
    with tempfile.TemporaryDirectory() as tmp:
        decky.DECKY_PLUGIN_RUNTIME_DIR=str(Path(tmp)/'runtime')
        decky.DECKY_PLUGIN_SETTINGS_DIR=str(Path(tmp)/'settings')
        decky.DECKY_PLUGIN_LOG_DIR=str(Path(tmp)/'log')
        p=rb.Plugin(); p._db=None; p._record=lambda *_a,**_k:None
        async def meta(_key): return {'success':True,'item':{'ratingKey':'artist-1','title':'Vera Static','type':'artist'}}
        p.get_metadata=meta
        async def resolve(_role): return ('7','confirmed','Music')
        p._resolve_section_for_role=resolve
        async def xml(path,params=None,**_kw):
            if path.endswith('/library/metadata/artist-1/allLeaves'):
                # Plex artist tree only exposes one track.
                return ET.fromstring('''<MediaContainer>
                  <Track ratingKey="t1" type="track" title="Primary" grandparentRatingKey="artist-1" grandparentTitle="Vera Static" parentTitle="Album A" index="1" />
                </MediaContainer>''')
            if path.endswith('/library/sections/7/all'):
                # A second track lives under another filesystem branch and has
                # a different semantic parent id, but the same artist metadata.
                return ET.fromstring('''<MediaContainer>
                  <Track ratingKey="t1" type="track" title="Primary" grandparentRatingKey="artist-1" grandparentTitle="Vera Static" parentTitle="Album A" index="1" />
                  <Track ratingKey="t2" type="track" title="Alternate Folder Track" grandparentRatingKey="artist-shadow" grandparentTitle="Vera Static" parentTitle="Loose / Alt" index="1" />
                  <Track ratingKey="x1" type="track" title="Other" grandparentRatingKey="other" grandparentTitle="Other Artist" parentTitle="Other" index="1" />
                </MediaContainer>''')
            raise AssertionError(path)
        p._pms_xml=xml
        out=await p.get_artist_tracks('artist-1')
        assert out['success'], out
        ids=[x['ratingKey'] for x in out['tracks']]
        assert ids==['t1','t2'], ids
        assert out['count']==2 and out['artistTitle']=='Vera Static', out
        assert all(x['libraryRole']=='music' for x in out['tracks'])

        # Preserve 0.9.9 stale/re-added track recovery behavior.
        class Content:
            async def read(self,n=-1): return b'x'
        class Response:
            def __init__(self,status): self.status=status; self.content=Content()
            async def __aenter__(self): return self
            async def __aexit__(self,*_): return False
        class Session:
            def request(self,method,url,**kwargs): return Response(404 if 'old-part' in url else 206)
        p._session=Session(); p._server=rb.ServerState(base_url='http://plex.test',access_token='fixture',machine_id='server-1')
        async def stale_source(key,refresh=False):
            part='old-part' if str(key)=='old' else 'new-part'
            return {'url':f'http://plex.test/{part}','token':'fixture','partKey':f'/{part}','container':'mp3','codec':'mp3','bitrate':320,'size':1,'file':f'{part}.mp3','durationMs':1000,'updatedAt':2}
        p._media_source=stale_source
        async def search_xml(path,params=None,**_kw):
            return ET.fromstring('<MediaContainer><Track ratingKey="new" type="track" title="Pretty in Red" grandparentTitle="vampp" parentTitle="Pretty in Red - Single"><Media container="mp3"><Part key="/new-part" file="new.mp3"/></Media></Track></MediaContainer>')
        p._pms_xml=search_xml
        p._resolve_section_for_role=resolve
        p.refresh_music_state=lambda force=False: asyncio.sleep(0, result={'success':True})
        repaired=await p.resolve_fresh_track('old','Pretty in Red','vampp','Pretty in Red - Single')
        assert repaired['success'] and repaired['item']['ratingKey']=='new' and repaired['replaced'] and repaired['verifiedPart'], repaired
    print('PASS: 0.9.10 completes artist queues across filesystem branches and preserves stale/re-added Music track recovery.')

asyncio.run(main())
