"""Native QtMultimedia two-deck audio engine.

Plex tokens and URLs stay inside QProcess/Qt. No HTMLAudioElement, browser,
SteamClient, or Decky interfaces exist in this module.
"""
from __future__ import annotations

import uuid
from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from core import Queue, identity, media_kind

# Qt Multimedia on Windows selects its FFmpeg backend when available.
CAPABILITIES = {
    "mp3": True, "aac": True, "m4a": True, "flac": True,
    "ogg": True, "opus": True, "wav": True, "alac": True
}


class AudioEngine(QObject):
    track_changed = Signal(object)
    status_changed = Signal(str)
    playback_changed = Signal(bool)
    progress_changed = Signal(int, int)
    queue_changed = Signal()
    crossfade_changed = Signal(str)

    def __init__(self, backend, prefs, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.prefs = prefs
        self.queue = Queue()
        self.players = [QMediaPlayer(self), QMediaPlayer(self)]
        self.outputs = [QAudioOutput(self), QAudioOutput(self)]
        for i in range(2):
            self.players[i].setAudioOutput(self.outputs[i])
            self.players[i].positionChanged.connect(lambda ms, deck=i: self._position(deck, ms))
            self.players[i].durationChanged.connect(lambda ms, deck=i: self._duration(deck, ms))
            self.players[i].mediaStatusChanged.connect(lambda status, deck=i: self._media_status(deck, status))
            self.players[i].playbackStateChanged.connect(lambda status, deck=i: self._playback_state(deck, status))
            self.players[i].errorOccurred.connect(lambda error, details, deck=i: self._error(deck, details))
        self.active = 0
        self.fade_active = False
        self.fade_begin = 0
        self.fade_ms = 0
        self.pending_load = False
        self.prepared_index = None
        self.prepared_url = ""
        self.play_request = 0
        self.preload_request = 0
        self.plan: dict[int, dict] = {}
        self.recovered: set[tuple[int, str]] = set()
        self._seek_restore_ms = 0
        self._session = str(uuid.uuid4())
        self.volume = float(prefs.value("volume", 0.85))
        self.volume = max(0.0, min(1.0, self.volume))
        self.crossfade = int(prefs.value("crossfade", 8))
        if self.crossfade not in (0, 3, 5, 8, 10):
            self.crossfade = 8
        self._tick = QTimer(self)
        self._tick.setInterval(80)
        self._tick.timeout.connect(self._update)
        self._tick.start()
        self._progress_tick = QTimer(self)
        self._progress_tick.setInterval(20000)
        self._progress_tick.timeout.connect(self._checkpoint)
        self._progress_tick.start()
        self._apply_volumes()

    def current(self):
        return self.queue.current

    def set_volume(self, value):
        self.volume = max(0.0, min(1.0, float(value)))
        self.prefs.setValue("volume", self.volume)
        self._apply_volumes()

    def set_crossfade(self, seconds):
        seconds = int(seconds)
        if seconds not in (0, 3, 5, 8, 10):
            return
        self.crossfade = seconds
        self.prefs.setValue("crossfade", seconds)

    def _apply_volumes(self, fraction=None):
        fraction = fraction if fraction is not None else (0.0 if self.fade_active else 1.0)
        if self.fade_active:
            self.outputs[self.active].setVolume(self.volume * max(0, 1 - fraction))
            self.outputs[1-self.active].setVolume(self.volume * max(0, fraction))
        else:
            self.outputs[self.active].setVolume(self.volume)
            self.outputs[1-self.active].setVolume(0)

    def play_tracks(self, tracks, index=0):
        self._checkpoint()
        if not self.queue.replace(tracks, index):
            self.status_changed.emit("Nothing playable in this selection")
            return
        self.queue_changed.emit()
        self._start_current()

    def add_tracks(self, tracks, next_up=False):
        self.queue.enqueue(tracks, next_up=next_up)
        self.queue_changed.emit()
        if self.players[self.active].source().isEmpty() and self.queue.current:
            self._start_current()

    def _start_current(self, requested_ms=0):
        item = self.queue.current
        if not item:
            return
        self.play_request += 1
        request_id = self.play_request
        self.preload_request += 1
        self.pending_load = False
        self.prepared_index = None
        self.fade_active = False
        self.players[0].stop()
        self.players[1].stop()
        self.active = 0
        self._apply_volumes()
        self.track_changed.emit(item)
        self.status_changed.emit("Connecting to Plex…")
        self.backend.request(
            "get_stream_url",
            [identity(item), CAPABILITIES, False, float(requested_ms)/1000, media_kind(item)],
            ok=lambda plan, stamp=request_id, start=requested_ms: self._open(plan, stamp, start),
            fail=lambda error: self.status_changed.emit("Stream unavailable: " + error)
        )
        if not requested_ms and media_kind(item) != "music":
            self.backend.request("get_resume", [identity(item)],
                ok=lambda info, stamp=request_id: self._accept_resume(info, stamp),
                fail=lambda error: None)

    def _accept_resume(self, info, stamp):
        if stamp != self.play_request or not isinstance(info, dict):
            return
        ms = info.get("positionMs", info.get("position_ms", 0))
        if not ms and isinstance(info.get("resume"), dict):
            ms = info["resume"].get("positionMs", info["resume"].get("position_ms", 0))
        try:
            ms = int(ms)
        except (ValueError, TypeError):
            ms = 0
        if ms > 5000:
            self._seek_restore_ms = ms
            if self.players[self.active].isSeekable():
                self.players[self.active].setPosition(ms)

    def _open(self, plan, stamp, requested_ms):
        if stamp != self.play_request:
            return
        if not isinstance(plan, dict) or not plan.get("success") or not plan.get("url"):
            self.status_changed.emit("Plex couldn't prepare the audio stream")
            return
        self.plan[self.active] = plan
        self._seek_restore_ms = requested_ms or self._seek_restore_ms
        self.players[self.active].setSource(QUrl(plan["url"]))
        if media_kind(self.queue.current or {}) != "music":
            rate = float(self.prefs.value("longform_rate", 1.0))
            self.players[self.active].setPlaybackRate(max(0.5, min(3.0, rate)))
        self.players[self.active].play()
        self.status_changed.emit("Playing · " + ("Direct" if plan.get("directPlay") else "Plex transcode"))
        self._session = str(uuid.uuid4())
        self.backend.request("record_playback_event",
                             [identity(self.queue.current), self._session, "play", 0, {"platform": "Windows Native"}],
                             fail=lambda error: None)

    def play_pause(self):
        player = self.players[self.active]
        if self.queue.current is None:
            self.status_changed.emit("Choose music from the library or Surprise Me")
        elif player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            if self.fade_active:
                self.players[1-self.active].pause()
            player.pause()
            self._checkpoint()
        elif player.source().isEmpty():
            self._start_current()
        else:
            if self.fade_active:
                self.players[1-self.active].play()
            player.play()

    def pause(self):
        if self.queue.current:
            self.players[self.active].pause()
            if self.fade_active:
                self.players[1-self.active].pause()
            self._checkpoint()

    def stop(self):
        self._checkpoint()
        self.players[0].stop()
        self.players[1].stop()
        self.fade_active = False
        self.prepared_index = None
        self.status_changed.emit("Stopped")

    def next(self):
        self._checkpoint()
        if self.queue.advance(manual=True):
            self.queue_changed.emit()
            self._start_current()
        else:
            self.stop()

    def previous(self):
        if self.players[self.active].position() > 3000:
            self.seek(0)
            return
        self._checkpoint()
        if self.queue.previous():
            self.queue_changed.emit()
            self._start_current()

    def seek(self, ms):
        self.fade_active = False
        self.players[1-self.active].stop()
        self.prepared_index = None
        self.pending_load = False
        self.preload_request += 1
        self.players[self.active].setPosition(max(0, int(ms)))
        self._apply_volumes()

    def toggle_shuffle(self):
        self.queue.shuffle = not self.queue.shuffle
        self.queue_changed.emit()

    def cycle_repeat(self):
        self.queue.repeat = {"off":"all", "all":"one", "one":"off"}[self.queue.repeat]
        self.queue_changed.emit()

    def _position(self, deck, position):
        if deck != self.active:
            return
        duration = self.players[deck].duration()
        self.progress_changed.emit(position, duration)

    def _duration(self, deck, duration):
        if deck == self.active:
            self.progress_changed.emit(self.players[deck].position(), duration)

    def _playback_state(self, deck, state):
        if deck == self.active:
            self.playback_changed.emit(state == QMediaPlayer.PlaybackState.PlayingState)

    def _media_status(self, deck, status):
        if deck == self.active and self._seek_restore_ms and status in (
            QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia):
            if self.players[deck].isSeekable():
                self.players[deck].setPosition(self._seek_restore_ms)
                self._seek_restore_ms = 0
        if deck != self.active or status != QMediaPlayer.MediaStatus.EndOfMedia:
            return
        if self.fade_active:
            return
        self._checkpoint()
        if self.queue.advance():
            self.queue_changed.emit()
            self._start_current()
        else:
            self.status_changed.emit("Queue finished")
            self.playback_changed.emit(False)

    def _error(self, deck, details):
        if not self.queue.current:
            return
        key = (deck, identity(self.queue.current))
        plan = self.plan.get(deck) or {}
        if deck == self.active and key not in self.recovered and plan.get("fallbackUrl"):
            self.recovered.add(key)
            player = self.players[deck]
            player.setSource(QUrl(plan["fallbackUrl"]))
            player.play()
            self.status_changed.emit("Recovering audio with Plex fallback…")
        elif deck == self.active:
            self.status_changed.emit("Audio error: " + str(details or "Unknown codec/network error")[:150])

    def _update(self):
        if not self.queue.current:
            return
        current = self.players[self.active]
        if self.fade_active:
            other = self.players[1-self.active]
            # A timer elapsed is independent of the decoder's position reporting.
            elapsed = max(0, self._clock.elapsed() if hasattr(self, "_clock") else 0)
            progress = min(1.0, elapsed / max(1, self.fade_ms))
            self._apply_volumes(progress)
            self.crossfade_changed.emit(f"Crossfade {round(progress*100)}%")
            if progress >= 1:
                old = self.active
                self.active = 1-old
                self.players[old].stop()
                self.fade_active = False
                self._apply_volumes()
                if self.queue.advance():
                    self.queue_changed.emit()
                    self.track_changed.emit(self.queue.current)
                    self._session = str(uuid.uuid4())
                self.prepared_index = None
                self.plan[self.active] = self.plan.get(self.active, {})
                self.playback_changed.emit(True)
            return
        if self.crossfade <= 0 or media_kind(self.queue.current) != "music":
            return
        duration, position = current.duration(), current.position()
        if duration <= self.crossfade * 1000 + 2500 or position <= 0:
            return
        remaining = duration - position
        candidate = self.queue.candidate()
        if candidate is None or candidate == self.queue.index:
            return
        if remaining <= max(25000, self.crossfade*1000+11000) and self.prepared_index != candidate and not self.pending_load:
            self.pending_load = True
            self.preload_request += 1
            req = self.preload_request
            next_track = self.queue.tracks[candidate]
            self.backend.request("get_stream_url",
                [identity(next_track), CAPABILITIES, False, 0.0, "music"],
                ok=lambda plan, gen=req, idx=candidate: self._prepared(plan, gen, idx),
                fail=lambda error: self._prepare_failed(error, req))
        if remaining <= self.crossfade * 1000 and self.prepared_index == candidate and self.prepared_url:
            # Start both players together. Crossfade finalization is atomic.
            import time
            from PySide6.QtCore import QElapsedTimer
            self.fade_active = True
            self.fade_ms = self.crossfade * 1000
            self._clock = QElapsedTimer()
            self._clock.start()
            standby = 1-self.active
            self.outputs[standby].setVolume(0)
            self.players[standby].play()
            self.crossfade_changed.emit(f"Crossfading {self.crossfade}s")

    def _prepared(self, plan, generation, index):
        if generation != self.preload_request:
            return
        self.pending_load = False
        if not isinstance(plan, dict) or not plan.get("success") or not plan.get("url"):
            return
        self.prepared_index = index
        self.prepared_url = plan["url"]
        standby = 1-self.active
        self.plan[standby] = plan
        self.players[standby].setSource(QUrl(plan["url"]))

    def _prepare_failed(self, _error, generation):
        if generation == self.preload_request:
            self.pending_load = False

    def _checkpoint(self):
        item = self.queue.current
        if not item:
            return
        ms = int(self.players[self.active].position())
        duration = int(self.players[self.active].duration())
        kind = media_kind(item)
        if kind in ("audiobook", "podcast") and ms > 0:
            self.backend.request("save_resume", [identity(item), kind, ms, duration, -1],
                                 fail=lambda error: None)
            self.backend.request("report_progress", [identity(item), "paused", ms, duration, kind, -1],
                                 fail=lambda error: None)
        else:
            self.backend.request("record_playback_event",
                [identity(item), self._session, "progress", ms, {"duration_ms": duration}],
                fail=lambda error: None)

    def shutdown(self):
        self._checkpoint()
        self.players[0].stop()
        self.players[1].stop()
        self._tick.stop()
        self._progress_tick.stop()
