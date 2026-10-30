"""Optional XInput controller navigation, scoped to the focused app."""
import ctypes
import sys
from PySide6.QtCore import QObject, QTimer, Signal
if sys.platform == "win32":
    from ctypes import wintypes
    class Gamepad(ctypes.Structure):
        _fields_=[("wButtons",wintypes.WORD),("bLeftTrigger",ctypes.c_ubyte),
                  ("bRightTrigger",ctypes.c_ubyte),("sThumbLX",ctypes.c_short),
                  ("sThumbLY",ctypes.c_short),("sThumbRX",ctypes.c_short),
                  ("sThumbRY",ctypes.c_short)]
    class State(ctypes.Structure):
        _fields_=[("dwPacketNumber",wintypes.DWORD),("Gamepad",Gamepad)]
class Controller(QObject):
    button=Signal(str)
    BUTTONS={0x1000:"A",0x2000:"B",0x0010:"Start",0x0100:"LB",0x0200:"RB"}
    def __init__(self,parent=None):
        super().__init__(parent)
        self._xinput=None
        self._last=0
        if sys.platform=="win32":
            for candidate in ("xinput1_4.dll","xinput9_1_0.dll","xinput1_3.dll"):
                try:
                    self._xinput=ctypes.WinDLL(candidate)
                    self._xinput.XInputGetState.argtypes=[ctypes.c_ulong,ctypes.POINTER(State)]
                    self._xinput.XInputGetState.restype=ctypes.c_ulong
                    break
                except OSError:
                    pass
        self.timer=QTimer(self)
        self.timer.setInterval(90)
        self.timer.timeout.connect(self.poll)
        if self._xinput:
            self.timer.start()
    def poll(self):
        if not self._xinput:
            return
        state=State()
        if self._xinput.XInputGetState(0,ctypes.byref(state))!=0:
            self._last=0
            return
        pressed=int(state.Gamepad.wButtons)
        for mask,name in self.BUTTONS.items():
            if pressed&mask and not self._last&mask:
                self.button.emit(name)
        self._last=pressed
