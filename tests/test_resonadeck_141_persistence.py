import ast,os,json,asyncio,tempfile,types,contextlib,hashlib
from pathlib import Path
source=(Path(__file__).resolve().parent.parent / 'resonadeck_backend.py').read_text()
module=ast.parse(source)
cls=next(c for c in module.body if isinstance(c,ast.ClassDef) and any(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=='save_discovery_choice' for n in c.body))
wanted={'_discovery_file_v11','_discovery_choices_path_v141','_discovery_choices_v141','save_discovery_choice','get_discovery_state','save_discovery_state'}
methods=[n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in wanted]
exec_env={'Path':Path,'json':json,'hashlib':hashlib,'Any':object,'_safe_write':None}
def safe_write(path,value):
 path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value));os.replace(tmp,path)
exec_env['_safe_write']=safe_write
mod=ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='BackendTest',bases=[],keywords=[],body=methods,decorator_list=[])],type_ignores=[]))
exec(compile(mod,'rd141',mode='exec'),exec_env)
Backend=exec_env['BackendTest']
with tempfile.TemporaryDirectory() as tmp:
 def backend():
  b=Backend();b.settings_dir=Path(tmp);b._catalog_identity=lambda:('srv-one','user-one');return b
 b=backend()
 async def check():
  initial=await b.get_discovery_state();assert initial['state']['preferences']=={}
  # Migration: honor old per-account values until a new selection is saved.
  safe_write(b._discovery_file_v11(),{'preferences':{'sessionLength':'30m','crossfade':5}})
  state=await b.get_discovery_state();assert state['state']['preferences']['crossfade']==5
  assert (await b.save_discovery_choice('sessionLength','endless'))['success']
  assert (await b.save_discovery_choice('crossfade',8))['success']
  # Legacy async state save can arrive *after* latest choice; must not win.
  stale={'preferences':{'sessionLength':'20','crossfade':0,'category':'music'},'favorites':[],'sessions':[],'playlists':[],'recentIds':[]}
  assert (await b.save_discovery_state(stale))['success']
  b2=backend();r=await b2.get_discovery_state();p=r['state']['preferences']
  assert p['sessionLength']=='endless' and p['crossfade']==8,p
  # User changes and restarts, no 20-track / Crossfade OFF rollback.
  assert (await b2.save_discovery_choice('sessionLength','40'))['success']
  assert (await b2.save_discovery_choice('crossfade',10))['success']
  b3=backend();p=(await b3.get_discovery_state())['state']['preferences']
  assert (p['sessionLength'],p['crossfade'])==('40',10),p
  assert (await b3.save_discovery_choice('sessionLength','endless'))['success']
  assert not (await b3.save_discovery_choice('crossfade',20))['success']
  assert not (await b3.save_discovery_choice('bad','endless'))['success']
  b4=backend();p=(await b4.get_discovery_state())['state']['preferences']
  assert (p['sessionLength'],p['crossfade'])==('endless',10)
  # The preferences belong to app, not a transient Plex identity.
  b4._catalog_identity=lambda:('srv-two','other-user')
  p=(await b4.get_discovery_state())['state']['preferences']
  assert (p['sessionLength'],p['crossfade'])==('endless',10)
  print('PASS backend: migration, durable read-back, legacy save race, changing options, invalid values, re-login')
 asyncio.run(check())
