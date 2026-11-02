import ast, asyncio, time, types, pathlib, inspect, contextlib
src = (pathlib.Path(__file__).resolve().parent.parent / 'resonadeck_backend.py').read_text()
root = ast.parse(src)
klass = next(n for n in root.body if isinstance(n,ast.ClassDef) and n.name=='Plugin')
methods = [n for n in klass.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='get_power_state']
assert len(methods)==1
n=methods[0]
lines=src.splitlines(); function='\n'.join(lines[n.lineno-1:n.end_lineno]); function='\n'.join(line[4:] if line.startswith('    ') else line for line in function.splitlines())
emitted=[]
class MockDecky:
 async def emit(self,name,payload):emitted.append((name,payload))
namespace={'time':time,'decky':MockDecky(),'contextlib':contextlib}
exec(function,namespace)
class Fake:
 _power_offset_v140=10.0
 _power_sleeping_v140=True
 _power_seq_v140=7
 _power_monitoring_v140=True
 _power_last_wake_v140=0.0
 offset=10.0
 def _power_offset_read_v140(self):return self.offset
async def run():
 e=Fake(); f=namespace['get_power_state']
 first=await f(e)
 assert first['seq']==7 and first['sleeping'] and not emitted
 e.offset=25.5; second=await f(e)
 assert second['seq']==8 and not second['sleeping']
 assert len(emitted)==1 and emitted[0][0]=='resonadeck_power_v140'
 third=await f(e)
 assert third['seq']==8 and len(emitted)==1
 print('PASS backend: Linux suspend clock detects missed wake exactly once, emits restartable state')
asyncio.run(run())
