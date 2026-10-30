"""Construct actual PySide6 window offscreen and switch all three views."""
import os,sys
from pathlib import Path
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
os.environ["RESONADECK_NATIVE_SMOKE"]="1"
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from app import NativeWindow
app=QApplication([])
window=NativeWindow()
window.show()
app.processEvents()
assert window._mode=="mini"
window.set_mode("expanded");app.processEvents()
assert window.stack.currentIndex()==1
window.set_mode("library");app.processEvents()
assert window.stack.currentIndex()==2
window.set_mode("mini");app.processEvents()
assert window.stack.currentIndex()==0
# Exercise the actual Qt album browser against a four-page 156-album fixture.
window.bridge.online=True
albums=[{"ratingKey":str(i),"title":f"Album {i}","thumb":"",
         "type":"album","libraryRole":"music"} for i in range(156)]
def fake_request(method,args=None,ok=None,fail=None,timeout_ms=22000):
    if method=="browse_cached":
        offset,size=args[2],args[3]
        data=albums[offset:offset+size]
        if ok:
            ok({"success":True,"items":data,"total":len(albums),"offset":offset,
                "hasMore":offset+len(data)<len(albums)})
    elif method=="get_art_url":
        if ok:
            ok({"success":True,"url":""})
    return 1
window.bridge.request=fake_request
window.set_mode("library")
window.library.browse()
for _ in range(4):
    if window.library.pager.has_more:
        window.library._load_next()
    app.processEvents()
assert window.library.grid.count()==156,window.library.grid.count()
assert window.library.pager.offset==156
assert not window.library.pager.has_more
window.library.grid.setCurrentRow(155)
assert window.library.grid.currentItem().data(256)["item"]["ratingKey"]=="155"
window.set_mode("mini");app.processEvents()
window._quit=True;window.close();app.quit()
print("Qt mini/expanded/full library UI smoke PASS")
