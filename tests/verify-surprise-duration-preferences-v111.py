"""Persistent timed Surprise Me profile settings, scoped per Plex user."""
import asyncio, importlib.util, logging, sys, tempfile, types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if 'decky' not in sys.modules:
    stub=types.ModuleType('decky'); stub.DECKY_PLUGIN_VERSION='1.1.1'
    stub.DECKY_PLUGIN_RUNTIME_DIR='/tmp/rd-v111-runtime'
    stub.DECKY_PLUGIN_SETTINGS_DIR='/tmp/rd-v111-settings'
    stub.DECKY_PLUGIN_LOG_DIR='/tmp/rd-v111-logs'
    stub.logger=logging.getLogger('rd-v111')
    sys.modules['decky']=stub
spec=importlib.util.spec_from_file_location('rd111_backend',ROOT/'resonadeck_backend.py')
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
async def main():
    with tempfile.TemporaryDirectory() as tmp:
        plugin=module.Plugin();plugin.settings_dir=Path(tmp);plugin._catalog_identity=lambda:('server-1','user-1')
        for length in ('10','20','40','30m','60m','120m','endless'):
            result=await plugin.save_discovery_state({'preferences':{'category':'music','sessionLength':length,'count':20}})
            assert result['success'], result
            loaded=await plugin.get_discovery_state()
            assert loaded['state']['preferences']['sessionLength']==length, (length,loaded)
        bad=await plugin.save_discovery_state({'preferences':{'category':'music','sessionLength':'forever;rm -rf','count':20}})
        assert bad['success']
        loaded=await plugin.get_discovery_state()
        assert loaded['state']['preferences']['sessionLength']=='20'
        await plugin.save_discovery_state({'preferences':{'category':'music','sessionLength':'60m','count':20}})
        plugin._catalog_identity=lambda:('server-1','user-2')
        other=(await plugin.get_discovery_state())['state']
        assert not other['preferences'] and not other['favorites']
        plugin._catalog_identity=lambda:('server-1','user-1')
        assert (await plugin.get_discovery_state())['state']['preferences']['sessionLength']=='60m'
    print('PASS: 7 timed/track/endless preferences persist; malformed selection sanitized; Plex account isolation')
asyncio.run(main())
