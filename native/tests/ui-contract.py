"""Contract test: real Qt widgets driven by fake Plex responses, no credentials.

Tests pagination across all 156 albums, combining diacritics, detail drill-down,
music library selection, and queue construction. This does not prove real Plex
connectivity or actual audio playback.
"""
import os
import sys
from pathlib import Path
os.environ["QT_QPA_PLATFORM"]="offscreen"
os.environ["RESONADECK_NATIVE_SMOKE"]="1"
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/"native"))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from app import NativeWindow

app=QApplication([])
window=NativeWindow()
window.show()
app.processEvents()
window.bridge.online=True
albums=[{"ratingKey":str(i+1),"title":"Mo\u0308tley Cru\u0308e" if i==155 else f"Album {i}",
         "type":"album","artist":"Mara Voss","libraryRole":"music"} for i in range(156)]
calls=[]

def fake_request(method,args=None,ok=None,fail=None,**kw):
    args=list(args or [])
    calls.append((method,args))
    if method=="browse_cached":
        role,view,offset,limit,*_=args
        result={"success":True,"items":albums[offset:offset+limit],
                "total":156,"offset":offset,"hasMore":offset+limit<156}
    elif method=="get_children":
        result={"success":True,"tracks":[{"ratingKey":str(1000+i),"title":f"Track {i}",
             "type":"track","libraryRole":"music"} for i in range(8)]}
    elif method=="get_art_url":
        result={"success":True,"url":""}
    elif method=="get_libraries":
        result={"success":True,"libraries":[{"key":"1","role":"music","title":"Music"}]}
    elif method=="get_stream_url":
        result={"success":False,"message":"Fixture intentionally contains no audio"}
    else:
        result={"success":True}
    if ok: ok(result)
    return len(calls)

window.bridge.request=fake_request
window._libraries({"success":True,"libraries":[{"key":"1","title":"Music","role":"music"}]})
for i in range(5):
    app.processEvents()
    if window.library.grid.count()==156:
        break
    window.library._load_next()
assert window.library.grid.count()==156, f"Only {window.library.grid.count()} albums"
assert window.library.pager.total==156
last=window.library.grid.item(155)
assert last.data(Qt.ItemDataRole.UserRole)["item"]["title"]=="Mo\u0308tley Cru\u0308e", "Unicode title changed"
window.library.activate_item(last)
app.processEvents()
assert len(window.library.detail_tracks)==8, "Album tracks failed to load"
window.library.play_detail(window.library.detail_list.item(0))
assert len(window.audio.queue.tracks)==8, "Clicking Play did not build queue"
assert any(name=="browse_cached" and len(args)>6 and args[6]=="1" for name,args in calls), "Lost section key"
window.set_mode("expanded")
app.processEvents()
window.set_mode("mini")
window._quit=True
window.close()
app.quit()
print("PASS: 156 album grid + Unicode + Plex section + track drill-down + queue")
