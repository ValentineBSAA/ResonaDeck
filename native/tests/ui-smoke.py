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
window._quit=True;window.close();app.quit()
print("Qt mini/expanded/full library UI smoke PASS")
