"""Asynchronous IPC to the original Plex Python backend. No browser, no WebView."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from collections.abc import Callable

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, Signal, QStandardPaths


def resources() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


def user_data() -> Path:
    # Keep auth, SQLite cache and listening history separate from the Deck and
    # separate from the previous Electron experimental edition.
    value = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))
    value.mkdir(parents=True, exist_ok=True)
    return value


class PlexBridge(QObject):
    ready = Signal()
    stopped = Signal(str)
    failed = Signal(str)
    log = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        self.process.readyReadStandardOutput.connect(self._on_output)
        self.process.readyReadStandardError.connect(self._on_stderr)
        self.process.errorOccurred.connect(self._on_process_error)
        self.process.finished.connect(self._on_exit)
        self._buffer = bytearray()
        self._pending: dict[int, tuple[Callable | None, Callable | None, QTimer]] = {}
        self._seq = 0
        self.online = False
        self._closing = False

    def start(self):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            return
        self._closing = False
        root = Path(__file__).resolve().parents[1]
        if getattr(sys, "frozen", False):
            binary = Path(sys.executable).parent / "backend" / "ResonaDeckBackend" / "ResonaDeckBackend.exe"
            program, arguments = str(binary), []
        else:
            program, arguments = sys.executable, ["-u", str(root / "native" / "bridge.py")]
        env = QProcessEnvironment.systemEnvironment()
        env.insert("RESONADECK_WINDOWS_DATA_DIR", str(user_data()))
        env.insert("PYTHONIOENCODING", "utf-8")
        self.process.setProcessEnvironment(env)
        self.process.setWorkingDirectory(str(root if not getattr(sys, "frozen", False) else Path(program).parent))
        self.process.setProgram(program)
        self.process.setArguments(arguments)
        self.process.start()

    def request(self, method: str, args=None, ok=None, fail=None, timeout_ms=22000):
        if self.process.state() == QProcess.ProcessState.NotRunning:
            if fail:
                fail("Plex service is unavailable")
            else:
                self.failed.emit("Plex service is unavailable")
            return -1
        self._seq += 1
        seq = self._seq
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda ident=seq: self._timeout(ident))
        self._pending[seq] = (ok, fail, timer)
        timer.start(timeout_ms)
        try:
            content = json.dumps({"id": seq, "method": method, "args": list(args or [])},
                                 ensure_ascii=False).encode("utf-8") + b"\n"
            if len(content) > 1024 * 1024:
                raise ValueError("Plex request too large")
            self.process.write(content)
        except (ValueError, TypeError) as exc:
            self._finish(seq, False, str(exc))
        return seq

    def _timeout(self, seq):
        self._finish(seq, False, "Plex request timed out")

    def _finish(self, seq, success, payload):
        callback = self._pending.pop(seq, None)
        if not callback:
            return
        ok, fail, timer = callback
        timer.stop()
        timer.deleteLater()
        if success:
            if ok:
                ok(payload)
        elif fail:
            fail(str(payload))
        else:
            self.failed.emit(str(payload))

    def _on_output(self):
        self._buffer.extend(bytes(self.process.readAllStandardOutput()))
        if len(self._buffer) > 8 * 1024 * 1024:
            self._buffer.clear()
            self.failed.emit("Plex response exceeded safe size")
        while b"\n" in self._buffer:
            line, _, rest = self._buffer.partition(b"\n")
            self._buffer = bytearray(rest)
            try:
                payload = json.loads(line.decode("utf-8"))
            except (UnicodeError, ValueError):
                continue
            if payload.get("event") == "ready":
                self.online = True
                self.ready.emit()
            elif isinstance(payload.get("id"), int):
                self._finish(payload["id"], bool(payload.get("ok")),
                             payload.get("result") if payload.get("ok") else payload.get("error", "Unknown Plex error"))

    def _on_stderr(self):
        # Redacted backend diagnostics only; never log raw tokens or media URLs.
        self.log.emit(bytes(self.process.readAllStandardError()).decode("utf-8", "replace")[-400:])

    def _on_process_error(self, _error):
        if not self._closing:
            self.failed.emit("Could not start the Plex service. Check the installation and dependencies.")

    def _on_exit(self, code, _status):
        self.online = False
        for seq in list(self._pending):
            self._finish(seq, False, "Plex service stopped")
        if not self._closing:
            self.stopped.emit(f"Plex service exited (code {code})")

    def shutdown(self):
        if self.process.state() == QProcess.ProcessState.NotRunning:
            return
        self._closing = True
        self.process.write(b'{"event":"shutdown"}\n')
        self.process.waitForBytesWritten(250)
        if not self.process.waitForFinished(1800):
            self.process.terminate()
            if not self.process.waitForFinished(800):
                self.process.kill()
                self.process.waitForFinished(500)
