"""Native Qt artwork retrieval and GPU-friendly painted vinyl transitions."""
from __future__ import annotations

import math
import sys
from pathlib import Path
from collections import OrderedDict
from PySide6.QtCore import QObject, QTimer, QRect, QRectF, Qt, Signal, QUrl
from PySide6.QtGui import QColor, QBrush, QConicalGradient, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import QWidget
from core import identity


class ArtworkStore(QObject):
    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.network = QNetworkAccessManager(self)
        self.cache = OrderedDict()
        self.waiting = {}
        self.inflight = 0
        self.todo = []

    def for_item(self, item: dict, callback, mode="square-card"):
        key = str(item.get("thumb") or item.get("parentThumb") or "") + "|" + identity(item) + "|" + mode
        if key in self.cache:
            self.cache.move_to_end(key)
            callback(self.cache[key])
            return
        self.waiting.setdefault(key, []).append(callback)
        if len(self.waiting[key]) > 1:
            return
        self.backend.request("get_art_url",
            [str(item.get("thumb") or item.get("parentThumb") or ""), mode, identity(item), False,
             str(item.get("libraryRole") or "music")],
            ok=lambda result, k=key: self._response(k, result),
            fail=lambda error, k=key: self._complete(k, QPixmap()))

    def _response(self, key, result):
        url = str(result.get("url") or "") if isinstance(result, dict) else ""
        if not url.startswith("http://127.0.0.1:"):
            self._complete(key, QPixmap())
            return
        self.todo.append((key, url))
        self._pump()

    def _pump(self):
        while self.todo and self.inflight < 5:
            key, url = self.todo.pop(0)
            self.inflight += 1
            request = QNetworkRequest(QUrl(url))
            request.setTransferTimeout(9000)
            reply = self.network.get(request)
            reply.finished.connect(lambda r=reply, k=key: self._downloaded(r, k))

    def _downloaded(self, reply, key):
        pix = QPixmap()
        if reply.error() == reply.NetworkError.NoError:
            body = bytes(reply.readAll())
            if len(body) < 12 * 1024 * 1024:
                pix.loadFromData(body)
        reply.deleteLater()
        self.inflight = max(0, self.inflight-1)
        self._complete(key, pix)
        self._pump()

    def _complete(self, key, pix):
        if not pix.isNull():
            self.cache[key] = pix
            self.cache.move_to_end(key)
            while len(self.cache) > 280:
                self.cache.popitem(last=False)
        listeners = self.waiting.pop(key, [])
        for callback in listeners:
            try:
                callback(pix)
            except RuntimeError:
                pass


class VinylArt(QWidget):
    """Painting only: no WebView, animations remain smooth while browsing."""
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.art = QPixmap()
        assets=Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parents[1]))/"assets"
        self.brand_art=QPixmap(str(assets/"resonadeck-glyph.webp"))
        self.angle = 0.0
        self.transition = 1.0
        self.playing = False
        self.setMinimumSize(116, 116)
        self.setToolTip("Double-click to open the library")
        self.timer = QTimer(self)
        self.timer.setInterval(42)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

    def set_art(self, art: QPixmap):
        self.art = art
        self.transition = 0.0
        self.update()

    def set_playing(self, playing: bool):
        self.playing = playing
        self.update()

    def _tick(self):
        if not self.isVisible():
            return
        if self.playing or self.art.isNull():
            self.angle = (self.angle + (0.75 if self.playing else 0.16)) % 360
        if self.transition < 1.0:
            self.transition = min(1.0, self.transition + 0.048)
        self.update()

    def mouseDoubleClickEvent(self, event):
        self.clicked.emit()
        super().mouseDoubleClickEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        side = min(self.width(), self.height()) - 8
        box = QRectF((self.width()-side)/2, (self.height()-side)/2, side, side)
        painter.setPen(QPen(QColor("#785e39"), 1.2))
        painter.setBrush(QBrush(QColor("#13151c")))
        painter.drawRoundedRect(box, 17, 17)
        cx, cy = box.center().x(), box.center().y()
        r = side * 0.44
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle)
        record = QRectF(-r, -r, 2*r, 2*r)
        gradient = QConicalGradient(0, 0, 45)
        for value, color in [(0,"#e4b864"),(.13,"#75511c"),(.26,"#ebc675"),(.41,"#302318"),(.55,"#e3b75b"),(.72,"#392d21"),(.88,"#c69543"),(1,"#e4b864")]:
            gradient.setColorAt(value, QColor(color))
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor("#f5d390"), 1))
        painter.drawEllipse(record)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for fraction in (0.67, .73, .79, .85, .92):
            rr = r * fraction
            painter.setPen(QPen(QColor(255, 233, 180, 70), 1))
            painter.drawEllipse(QRectF(-rr,-rr,rr*2,rr*2))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#1c2735"))
        painter.drawEllipse(QRectF(-r*.29,-r*.29,r*.58,r*.58))
        painter.setBrush(QColor("#dcb268"))
        painter.drawEllipse(QRectF(-r*.13,-r*.13,r*.26,r*.26))
        painter.setBrush(QColor("#111927"))
        painter.drawEllipse(QRectF(-3,-3,6,6))
        painter.restore()
        # The actual ResonaDeck emblem from the Deck version replaces a generic
        # dot at the heart of the record without changing the native rendering.
        if not self.brand_art.isNull():
            emblem=r*.30
            painter.drawPixmap(QRectF(cx-emblem/2,cy-emblem/2,emblem,emblem).toRect(),
                               self.brand_art,
                               QRect(0,0,self.brand_art.width(),self.brand_art.height()))
        # Floating tonearm: lightweight native painter strokes, no fake waveform.
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing,True)
        x0=box.right()-r*.15
        y0=box.top()+r*.25
        painter.setPen(QPen(QColor("#2b3543"),max(3.0,r*.052)))
        painter.drawLine(int(x0),int(y0),int(cx+r*.50),int(cy-r*.32))
        painter.setPen(QPen(QColor("#e8b968"),max(1.5,r*.024)))
        painter.drawLine(int(x0),int(y0),int(cx+r*.50),int(cy-r*.32))
        painter.setBrush(QColor("#111825"))
        painter.setPen(QPen(QColor("#d1a459"),1.5))
        painter.drawEllipse(QRectF(x0-r*.075,y0-r*.075,r*.15,r*.15))
        painter.restore()
        if not self.art.isNull():
            # On track changes the artwork grows over the gold disc.
            eased = 1 - pow(1-self.transition, 3)
            scaled = box.adjusted((1-eased)*r/2, (1-eased)*r/2,
                                  -(1-eased)*r/2, -(1-eased)*r/2)
            painter.setOpacity(eased)
            path = QPainterPath()
            path.addRoundedRect(scaled, 14, 14)
            painter.setClipPath(path)
            painter.drawPixmap(scaled.toRect(), self.art, QRect(0,0,self.art.width(),self.art.height()))
            painter.setClipping(False)
            painter.setOpacity(1.0)
