"""0.9.29 functional regression: Plex startup restoration, role isolation, and music sections."""
from __future__ import annotations
import asyncio, importlib.util, logging, sys, tempfile, types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
decky=types.ModuleType('decky')
decky.DECKY_PLUGIN_VERSION='0.9.29-test'
decky.DECKY_PLUGIN_RUNTIME_DIR='/tmp/rd929-runtime'
decky.DECKY_PLUGIN_SETTINGS_DIR='/tmp/rd929-settings'
decky.DECKY_PLUGIN_LOG_DIR='/tmp/rd929-logs'
decky.DECKY_USER_HOME='/tmp'
decky.logger=logging.getLogger('rd929')
sys.modules['decky']=decky
spec=importlib.util.spec_from_file_location('rd929_backend',ROOT/'resonadeck_backend.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
class Settings:
 def __init__(self):self.values={'selected_server':{'machineId':'server-A','name':'Living Library'}}
 def getSetting(self,k,default=None):return self.values.get(k,default)
 def setSetting(self,k,value):self.values[k]=value
async def test():
 with tempfile.TemporaryDirectory() as tmp:
  decky.DECKY_PLUGIN_RUNTIME_DIR=tmp+'/runtime';decky.DECKY_PLUGIN_SETTINGS_DIR=tmp+'/settings';decky.DECKY_PLUGIN_LOG_DIR=tmp+'/logs'
  p=m.Plugin();p.auth_path.parent.mkdir(parents=True,exist_ok=True);p.settings=Settings();p._active_user_token='home-token';p._account_token='account';p._record=lambda *a,**kw:None
  async def probe(uri,token,machine):return (uri=='http://plex.local:32400' and token=='server-token',12)
  p._probe_connection=probe
  p._last_server_connection={'machineId':'server-A','name':'Living Library','uri':'http://plex.local:32400','token':'server-token','local':True,'relay':False,'userFingerprint':p._server_user_fingerprint()}
  async def offline(*args):raise ConnectionError('Plex cloud offline')
  p._resources=offline
  assert await p._restore_server(), 'remembered endpoint must restore while cloud discovery is offline'
  assert p._server.machine_id=='server-A' and p._restore_state=='connected'
  assert 'token' not in str(p._server_public()) and 'token' not in str(await p.get_auth_state()), 'never reveal tokens over RPC'
  # User changes cannot reuse the previous Plex Home profile server token.
  p._active_user_token='other-user-token'
  assert not await p._restore_server(), 'old profile credentials must not be used'
  assert not p._server_public()['connected']
  p._active_user_token='home-token'
  p._last_server_connection={}
  async def resources(*args):return [
   {'clientIdentifier':'server-B','name':'Not Selected','accessToken':'token-B','connections':[{'uri':'http://other','local':True}]},
  ]
  p._resources=resources
  p._probe_connection=lambda *args: offline() # No probe should happen when preferred server is absent.
  assert not await p._restore_server(), 'must not silently switch to a different server'
  assert not p._server_public()['connected']
  # Cloud outage must not block manual selection of a server found over LAN GDM.
  p._resources=offline
  p._discover_gdm_sync=lambda:[{'machineId':'server-A','name':'Living Library','uri':'http://plex.local:32400','local':True}]
  async def accept(resource):
   assert resource['clientIdentifier']=='server-A' and resource['accessToken']=='home-token', resource
   return True
  p._select_resource=accept
  picked=await p.select_server('server-A')
  assert picked['success'], picked
  # Section picker must only allow an available section explicitly assigned/suggested as Music.
  p._server=m.ServerState(machine_id='server-A',name='Living Library',base_url='http://plex.local:32400',access_token='secret')
  async def role(_role):return ('7','confirmed','Primary')
  p._resolve_section_for_role=role
  async def libraries():return {'success':True,'libraries':[
   {'key':'7','role':'music','title':'Primary'},
   {'key':'8','role':'music','title':'Alternate Mixes'},
   {'key':'9','role':'audiobooks','title':'Audiobooks'},
  ]}
  p.get_libraries=libraries
  visited=[]
  def cache(section,view,sort,offset,limit):
   visited.append(section)
   return ([{'ratingKey':'a8','type':'album','title':'Alternate Album'}],{'complete':True,'total':1,'indexed':1,'updated_at':10**12})
  p._read_catalog_cache=cache
  p._restore_ready_art_for_item=lambda item,role,mode:item
  async def section(*args):raise AssertionError('fresh network query not needed for valid complete cached page')
  p.browse_section=section
  r=await p.browse_cached('music','albums',0,20,'title',False,'8')
  assert r['success'] and r['section']=='8' and visited[0]=='8',r
  forbidden=await p.browse_cached('music','albums',0,20,'title',False,'9')
  assert forbidden['success'] is False and all(x=='8' for x in visited), (forbidden, visited)
  # Don't regress long-form use of the same section resolver.
  assert 'section_key' not in m.Plugin.get_continue_listening.__code__.co_varnames
 print('PASS 0.9.29 backend: offline remembered-server restore, per-user isolation, preferred-server integrity, music-section scoping, long-form isolation')
asyncio.run(test())
