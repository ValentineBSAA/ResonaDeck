"""0.9.7 terminal fallback, folder suppression, persistence and revision checks."""
from __future__ import annotations
import asyncio, importlib.util, logging, sys, tempfile, types
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
decky=types.ModuleType('decky')
decky.DECKY_PLUGIN_VERSION='0.9.8-test'
decky.DECKY_PLUGIN_RUNTIME_DIR='/tmp/resonadeck097-runtime'
decky.DECKY_PLUGIN_SETTINGS_DIR='/tmp/resonadeck097-settings'
decky.DECKY_PLUGIN_LOG_DIR='/tmp/resonadeck097-log'
decky.DECKY_USER_HOME='/tmp'
decky.logger=logging.getLogger('resonadeck097-test')
sys.modules['decky']=decky
spec=importlib.util.spec_from_file_location('resonadeck_backend_097',ROOT/'resonadeck_backend.py')
rb=importlib.util.module_from_spec(spec); assert spec and spec.loader
sys.modules[spec.name]=rb; spec.loader.exec_module(rb)

def make_plugin(tmp: str):
    decky.DECKY_PLUGIN_RUNTIME_DIR=str(Path(tmp)/'runtime')
    decky.DECKY_PLUGIN_SETTINGS_DIR=str(Path(tmp)/'settings')
    decky.DECKY_PLUGIN_LOG_DIR=str(Path(tmp)/'log')
    p=rb.Plugin(); p._server=rb.ServerState(base_url='http://plex.test',access_token='fixture',machine_id='server-1')
    p._session=object(); p._db=None; p._user_key=lambda:'user-1'; p._record=lambda *_a,**_k:None
    return p

async def main():
    assert rb.ARTWORK_HYDRATION_GENERATION=='0.9.9-library-refresh-v1'
    with tempfile.TemporaryDirectory() as tmp:
        p=make_plugin(tmp)
        # Latest hardware evidence: both candidate routes returned 404. That is
        # a terminal native-art miss, not a transient transport failure.
        p._art_sources['k']={'lastCandidateErrors':[
            {'kind':'plex-thumbnail','message':'Plex artwork HTTP 404 (plex-thumbnail)'},
            {'kind':'original-fallback','message':'Plex artwork HTTP 404 (original-fallback)'},
        ]}
        state,code,errs=p._art_failure_state('k')
        assert (state,code)==('fallback','PLEX_ART_NOT_FOUND') and len(errs)==2
        p._art_sources['k2']={'lastCandidateErrors':[{'kind':'plex-thumbnail','message':'Plex artwork HTTP 500'}]}
        assert p._art_failure_state('k2')[:2]==('failed','PLEX_IMAGE_FAILED')

        # 0.9.8 no longer guesses from names. Only Plex semantic Album rows
        # belong in the normal Music Albums catalog.
        assert p._is_semantic_music_album({'title':'Real Album','plexType':'album','semanticType':'album'})
        assert not p._is_semantic_music_album({'title':'Music ds','plexType':'folder','semanticType':'filesystem-directory'})
        assert not p._is_semantic_music_album({'title':'Garden Alt','plexType':'directory','semanticType':'filesystem-directory'})

        # Per-record revision must never be inflated to the global cursor. This
        # was the mounted-QAM stale-art mechanism seen after 0.9.6 hydration.
        p._art_registry_revision=99
        response=p._art_record_response({'identity':'music|a|square-card','state':'downloading','revision':7})
        assert response['revision']==7 and response['latestRevision']==99

        # Saved terminal fallbacks are restored without scheduling another full
        # hydration pass or refetching Plex just to rediscover the same 404.
        saved={'artworkHydrationState':{
            'generation':rb.ARTWORK_HYDRATION_GENERATION,'server':'server-1','user':'user-1','complete':True,
            'done':1,'total':1,'cached':0,'fallback':1,'failed':0,
            'roles':{'music':{'done':1,'total':1,'cached':0,'fallback':1,'failed':0}},
            'terminalFallbacks':[{'identity':'music|missing|square-card','role':'music','mode':'square-card','ratingKey':'missing','title':'Missing Album','sourceHint':'/library/metadata/missing/thumb','errorCode':'PLEX_ART_NOT_FOUND','candidateErrors':[{'message':'Plex artwork HTTP 404'}]}]
        }}
        p._settings_get=lambda key,default:saved.get(key,default)
        p._settings_set=lambda key,value:saved.__setitem__(key,value)
        status=await p.start_artwork_hydration(False)
        assert status['state']=='ready' and status['fallback']==1 and status['failed']==0
        assert p._art_hydration_task is None
        rec=p._art_registry.get('music|missing|square-card')
        assert rec and rec['state']=='fallback' and rec['errorCode']=='PLEX_ART_NOT_FOUND'

    print('PASS: terminal Plex 404 fallbacks, semantic Music album gating, per-record revisions, and fallback restore remain intact in 0.9.8. Hardware NOT tested.')

asyncio.run(main())
