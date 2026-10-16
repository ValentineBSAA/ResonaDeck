"""Functional offline checks for persistent discovery profiles (no Plex connection)."""
import asyncio, importlib.util, logging, sys, tempfile, types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if 'decky' not in sys.modules:
    stub=types.ModuleType('decky');stub.DECKY_PLUGIN_VERSION='1.1.0';stub.DECKY_PLUGIN_RUNTIME_DIR='/tmp/rd-v110-runtime';stub.DECKY_PLUGIN_SETTINGS_DIR='/tmp/rd-v110-settings';stub.DECKY_PLUGIN_LOG_DIR='/tmp/rd-v110-logs';stub.logger=logging.getLogger('rd-v110');sys.modules['decky']=stub
spec=importlib.util.spec_from_file_location('rd_v110_backend',ROOT/'resonadeck_backend.py')
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
async def main():
    with tempfile.TemporaryDirectory() as tmp:
        p=module.Plugin();p.settings_dir=Path(tmp);p._catalog_identity=lambda:('server-1','person-A')
        original={'preferences':{'category':'music','count':20,'musicMode':'tracks','favoritesOnly':False,'crossfade':5},'favorites':[{'ratingKey':'19','title':'Favorite','libraryRole':'music','accessToken':'NEVER_STORE'}],'sessions':[{'id':'s1','name':'Sunday Mix','items':[{'ratingKey':'19','title':'Song','url':'http://sensitive?token=secret'}],'index':0,'position':8.2}],'playlists':[],'recentIds':['19']}
        assert (await p.save_discovery_state(original))['success']
        raw=next(Path(tmp).glob('discovery*.json')).read_text()
        assert 'NEVER_STORE' not in raw and 'sensitive' not in raw and 'secret' not in raw,raw
        got=(await p.get_discovery_state())['state']
        assert got['preferences']['category']=='music' and got['preferences']['count']==20
        assert got['sessions'][0]['items'][0]['title']=='Song'
        p._catalog_identity=lambda:('server-1','person-B')
        other=(await p.get_discovery_state())['state']
        assert not other['favorites'] and not other['sessions'],'plex profiles must remain isolated'
        p._catalog_identity=lambda:('server-1','person-A')
        assert (await p.get_discovery_state())['state']['favorites'][0]['title']=='Favorite','data lost after identity switch'
        nextfile=p._discovery_file_v11();nextfile.write_text('bad json')
        assert (await p.get_discovery_state())['success'] is True,'malformed preferences must recover'
        assert not (await p.save_discovery_state('not a dictionary'))['success']
        print('PASS: 1.1 per-user durable storage, favorites, sessions, sanitize stream URLs/tokens, corruption recovery')
asyncio.run(main())
