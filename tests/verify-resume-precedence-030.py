"""0.9.30: an updated Plex audiobook bookmark outranks a stale local bookmark."""
import importlib.util, logging, sqlite3, sys, types
from pathlib import Path
root=Path(__file__).resolve().parents[1]
decky=types.ModuleType('decky'); decky.logger=logging.getLogger('rd930');decky.DECKY_PLUGIN_VERSION='0.9.30-test'
sys.modules['decky']=decky
spec=importlib.util.spec_from_file_location('resonadeck_v930',root/'resonadeck_backend.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
p=m.Plugin.__new__(m.Plugin)
conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
conn.execute('CREATE TABLE resume(user_id TEXT,rating_key TEXT,kind TEXT,position_ms INTEGER,duration_ms INTEGER,chapter_index INTEGER,updated_at REAL)')
p._db=conn;p._user_key=lambda:'home-user'
conn.execute("INSERT INTO resume VALUES ('home-user','book','audiobook',50000,1200000,-1,100)")
manifest={'ratingKey':'book','durationMs':1200000,'files':[
 {'ratingKey':'file1','index':0,'globalStartMs':0,'globalEndMs':600000,'viewOffset':0,'durationMs':600000},
 {'ratingKey':'file2','index':1,'globalStartMs':600000,'globalEndMs':1200000,'viewOffset':45000,'durationMs':600000,'lastViewedAt':200}],
 'chapters':[{'title':'First','globalStartMs':0,'globalEndMs':600000},{'title':'Second','globalStartMs':600000,'globalEndMs':1200000}]}
res=p._book_resume_overlay(manifest)
assert res['resume']['positionMs']==645000,res['resume']
assert res['resume']['fileIndex']==1,res['resume']
assert res['resume']['chapterTitle']=='Second',res['resume']
assert res['resume']['source']=='plex-track',res['resume']
conn.execute("UPDATE resume SET position_ms=720000,updated_at=300 WHERE rating_key='book'")
res=p._book_resume_overlay(manifest)
assert res['resume']['positionMs']==720000,res['resume']
assert res['resume']['source']=='resonadeck',res['resume']
# A Plex file lacking playback timestamps cannot silently overwrite a known local bookmark.
manifest['files'][1]['lastViewedAt']=0
res=p._book_resume_overlay(manifest)
assert res['resume']['positionMs']==720000,res['resume']
conn.close()
print('PASS 0.9.30 audiobook resume precedence: newer Plex track, newer local checkpoint, missing Plex timestamp')
