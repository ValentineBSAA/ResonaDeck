"""ResonaDeck Native for Windows 11 (PySide6, no Electron/WebView).

Mini player is the top-level transparent frameless window. Full Library is a
native QWidget page, not a Decky route and never embeds a browser.
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSettings, QTimer, QUrl, QPoint, QByteArray, QSize, Signal
from PySide6.QtGui import QAction, QDesktopServices, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QSystemTrayIcon, QMenu, QMessageBox,
    QDialog, QDialogButtonBox, QFormLayout, QCheckBox, QComboBox,
    QInputDialog, QLineEdit, QSizeGrip
)

from artwork import ArtworkStore
from core import AUDIO_ROLES, identity, media_kind, pick_surprise, clean_discovery
from player import AudioEngine
from theme import STYLE
from transport import PlexBridge, resources
from views import LibraryPage, PlayerPanel, button

APP_VERSION = "0.2.0-native-preview"


class DragBar(QFrame):
    """Qt's native system move works with transparent frameless Windows windows."""
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            window = self.window().windowHandle()
            if window and window.startSystemMove():
                event.accept()
                return
        super().mousePressEvent(event)


class PreferencesDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.host = parent
        self.setWindowTitle("ResonaDeck · Windows Settings")
        self.setMinimumWidth(430)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("WINDOWS EXPERIENCE"))
        form = QFormLayout()
        self.pin = QCheckBox("Float above other applications")
        self.pin.setChecked(parent.pin)
        self.tray = QCheckBox("Keep playing when the window closes")
        self.tray.setChecked(parent.close_to_tray)
        self.startup = QCheckBox("Launch at Windows sign-in")
        self.startup.setChecked(bool(parent.settings.value("startup",False,type=bool)))
        self.motion = QCheckBox("Reduce artwork animation")
        self.motion.setChecked(bool(parent.settings.value("reduce_motion",False,type=bool)))
        self.xfade = QComboBox()
        for n in (0,3,5,8,10):
            self.xfade.addItem("Off" if n==0 else f"{n} seconds",n)
        self.xfade.setCurrentIndex([0,3,5,8,10].index(parent.audio.crossfade))
        self.rate = QComboBox()
        for n in (0.5,0.75,1.0,1.25,1.5,1.75,2.0,2.5,3.0):
            self.rate.addItem(f"{n:g}×",n)
        current_rate=float(parent.settings.value("longform_rate",1.0))
        index=self.rate.findData(current_rate)
        self.rate.setCurrentIndex(max(0,index))
        form.addRow("Always on Top",self.pin)
        form.addRow("Close to Tray",self.tray)
        form.addRow("Autostart",self.startup)
        form.addRow("Animation",self.motion)
        form.addRow("Music crossfade",self.xfade)
        form.addRow("Audiobooks / Podcasts",self.rate)
        layout.addLayout(form)
        tip=QLabel("All changes are saved locally. Plex logins remain in the protected backend data folder.")
        tip.setWordWrap(True)
        layout.addWidget(tip)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save(self):
        w=self.host
        w.close_to_tray=self.tray.isChecked()
        w.settings.setValue("close_to_tray",w.close_to_tray)
        w.set_always_on_top(self.pin.isChecked())
        w.settings.setValue("reduce_motion",self.motion.isChecked())
        w.audio.set_crossfade(self.xfade.currentData())
        w.discovery["preferences"]["crossfade"]=w.audio.crossfade
        w.save_discovery()
        w.settings.setValue("longform_rate",self.rate.currentData())
        for player in w.audio.players:
            if media_kind(w.audio.current() or {}) != "music":
                player.setPlaybackRate(float(self.rate.currentData()))
        w.set_startup(self.startup.isChecked())
        for panel in (w.mini,w.expanded):
            if self.motion.isChecked():
                panel.art.timer.stop()
            else:
                panel.art.timer.start()
        self.accept()


class DiscoveryDialog(QDialog):
    def __init__(self,parent):
        super().__init__(parent)
        self.host=parent
        self.setWindowTitle("Surprise Me · Discovery")
        self.setMinimumWidth(440)
        main=QVBoxLayout(self)
        heading=QLabel("✦ SURPRISE ME")
        heading.setObjectName("Eyebrow")
        main.addWidget(heading)
        layout=QFormLayout()
        pref=parent.discovery["preferences"]
        self.category=QComboBox()
        for name,key in (("Music","music"),("Audiobooks","audiobooks"),("Podcasts","podcasts"),
                         ("More Audio","other"),("All Audio","all")):
            self.category.addItem(name,key)
        self.category.setCurrentIndex(max(0,self.category.findData(pref.get("category","music"))))
        self.mode=QComboBox()
        for name,key in (("Tracks","tracks"),("Albums","albums"),("Rediscover","rediscover")):
            self.mode.addItem(name,key)
        self.mode.setCurrentIndex(max(0,self.mode.findData(pref.get("musicMode","tracks"))))
        self.favorites=QCheckBox("Discover saved favorite tracks only")
        self.favorites.setChecked(bool(pref.get("favoritesOnly",False)))
        self.session=QComboBox()
        for name,key in (("10 tracks","10"),("20 tracks","20"),("40 tracks","40"),
                         ("30 minutes","30m"),("1 hour","60m"),("2 hours","120m"),
                         ("Keep Playing","endless")):
            self.session.addItem(name,key)
        self.session.setCurrentIndex(max(0,self.session.findData(str(pref.get("sessionLength","20")))))
        self.crossfade=QComboBox()
        for seconds in (0,3,5,8,10):
            self.crossfade.addItem("Off" if not seconds else f"{seconds} seconds",seconds)
        self.crossfade.setCurrentIndex(max(0,self.crossfade.findData(parent.audio.crossfade)))
        layout.addRow("Listen to",self.category)
        layout.addRow("Music discovery",self.mode)
        layout.addRow("Favorites",self.favorites)
        layout.addRow("Session",self.session)
        layout.addRow("Crossfade",self.crossfade)
        main.addLayout(layout)
        controls=QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        start=controls.addButton("▶ Surprise Me",QDialogButtonBox.ButtonRole.AcceptRole)
        start.setObjectName("Primary")
        controls.rejected.connect(self.reject)
        start.clicked.connect(self.start)
        main.addWidget(controls)

    def start(self):
        pref=self.host.discovery["preferences"]
        pref.update({"category":self.category.currentData(),"musicMode":self.mode.currentData(),
                     "favoritesOnly":self.favorites.isChecked(),
                     "sessionLength":self.session.currentData(),
                     "crossfade":self.crossfade.currentData()})
        self.host.audio.set_crossfade(self.crossfade.currentData())
        self.host.save_discovery()
        self.accept()
        self.host.surprise()


class NativeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ResonaDeck Native")
        self.setWindowFlags(Qt.WindowType.Window|Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground,True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground,True)
        self.setMinimumSize(400,238)
        self.setMouseTracking(True)
        self.settings=QSettings("ValentineBSAA","ResonaDeck Native")
        self.pin=bool(self.settings.value("pin",False,type=bool))
        self.close_to_tray=bool(self.settings.value("close_to_tray",True,type=bool))
        self._quit=False
        self._mode="mini"
        self._keep_playing=False
        self._discovery_busy=False
        self._session_deadline=0.0
        self._sleep_left=0
        self._sleep_original=1.0
        self._restore_tries=0
        self.discovery={"preferences":clean_discovery(),"favorites":[],"sessions":[],
                        "playlists":[],"recentIds":[]}
        self.bridge=PlexBridge(self)
        self.audio=AudioEngine(self.bridge,self.settings,self)
        self.covers=ArtworkStore(self.bridge,self)
        self.build_ui()
        self.configure_tray()
        self.bind()
        self.set_always_on_top(self.pin)
        self.set_mode("mini",first=True)
        if os.environ.get("RESONADECK_NATIVE_SMOKE") != "1":
            QTimer.singleShot(10,self.bridge.start)
        self._sleep_timer=QTimer(self)
        self._sleep_timer.setInterval(1000)
        self._sleep_timer.timeout.connect(self._sleep_update)
        self._session_timer=QTimer(self)
        self._session_timer.setInterval(1000)
        self._session_timer.timeout.connect(self._apply_session_end)
        self._auth_timer=QTimer(self)
        self._auth_timer.setInterval(1900)
        self._auth_timer.timeout.connect(self._poll_auth)
        self._controller=None
        try:
            from controller import Controller
            self._controller=Controller(self)
            self._controller.button.connect(self.gamepad)
        except Exception:
            pass

    def build_ui(self):
        outer=QVBoxLayout(self)
        outer.setContentsMargins(7,7,7,7)
        outer.setSpacing(0)
        self.shell=QFrame(self)
        self.shell.setObjectName("Panel")
        shell_layout=QVBoxLayout(self.shell)
        shell_layout.setContentsMargins(6,3,6,6)
        shell_layout.setSpacing(3)
        self.header=DragBar()
        self.header.setFixedHeight(31)
        self.header.setObjectName("Toolbar")
        header_layout=QHBoxLayout(self.header)
        header_layout.setContentsMargins(7,0,4,0)
        header_layout.setSpacing(3)
        self.brand=QLabel("◈  ResonaDeck")
        self.brand.setStyleSheet("font-size:12px;font-weight:700;color:#eac587")
        header_layout.addWidget(self.brand)
        header_layout.addStretch(1)
        self.pin_btn=button("♢","Always on Top","Chrome")
        self.size_btn=button("⛶","Expand / collapse (Ctrl+M)","Chrome")
        self.library_btn=button("▦","Open full library (Ctrl+L)","Chrome")
        self.menu_btn=button("⋯","Options (right-click)","Chrome")
        self.close_btn=button("×","Close to tray or exit","Chrome")
        for control in (self.pin_btn,self.size_btn,self.library_btn,self.menu_btn,self.close_btn):
            control.setFixedSize(27,27)
            header_layout.addWidget(control)
        shell_layout.addWidget(self.header)
        self.stack=QStackedWidget()
        self.mini=PlayerPanel(self.audio,self.covers,expanded=False)
        self.expanded=PlayerPanel(self.audio,self.covers,expanded=True)
        self.library=LibraryPage(self.bridge,self.audio,self.covers)
        self.library.attach_favorites(lambda:self.library.show_custom("Favorites",self.discovery["favorites"]))
        self.stack.addWidget(self.mini)
        self.stack.addWidget(self.expanded)
        self.stack.addWidget(self.library)
        shell_layout.addWidget(self.stack,1)
        outer.addWidget(self.shell,1)
        self.grip=QSizeGrip(self)
        self.grip.resize(18,18)
        self.grip.setToolTip("Drag to resize")
        self.grip.hide()
        self.setStyleSheet(STYLE)

    def configure_tray(self):
        icon_path=resources()/"assets"/"resonadeck-icon.webp"
        if not icon_path.is_file():
            icon_path=Path(__file__).resolve().parents[1]/"assets"/"resonadeck-icon.webp"
        self.icon=QIcon(str(icon_path))
        if not self.icon.isNull():
            self.setWindowIcon(self.icon)
        self.tray=QSystemTrayIcon(self.icon,self)
        menu=QMenu()
        menu.addAction("Show ResonaDeck",lambda:self.show_normal())
        menu.addAction("Mini Player",lambda:self.set_mode("mini"))
        menu.addAction("Expanded Player",lambda:self.set_mode("expanded"))
        menu.addAction("Full Library",lambda:self.set_mode("library"))
        menu.addSeparator()
        menu.addAction("▶ / ⏸  Play or Pause",self.audio.play_pause)
        menu.addAction("⏭  Next",self.audio.next)
        menu.addAction("⏮  Previous",self.audio.previous)
        menu.addSeparator()
        self.tray_pin=menu.addAction("Always on Top")
        self.tray_pin.setCheckable(True)
        self.tray_pin.setChecked(self.pin)
        self.tray_pin.triggered.connect(lambda checked:self.set_always_on_top(checked))
        menu.addAction("Settings",lambda:PreferencesDialog(self).exec())
        menu.addSeparator()
        menu.addAction("Exit ResonaDeck",self.quit_app)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason:self.show_normal()
            if reason==QSystemTrayIcon.ActivationReason.DoubleClick else None)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

    def bind(self):
        self.pin_btn.clicked.connect(lambda:self.set_always_on_top(not self.pin))
        self.size_btn.clicked.connect(lambda:self.set_mode("expanded" if self._mode=="mini" else "mini"))
        self.library_btn.clicked.connect(lambda:self.set_mode("library"))
        self.menu_btn.clicked.connect(lambda:self.open_menu(self.menu_btn.mapToGlobal(QPoint(0,30))))
        self.close_btn.clicked.connect(self.close)
        self.library.back_requested.connect(lambda:self.set_mode("mini"))
        self.library.plex_requested.connect(self.plex_menu)
        self.library.surprise_requested.connect(lambda:DiscoveryDialog(self).exec())
        self.library.play_tracks.connect(self.audio.play_tracks)
        self.library.add_tracks.connect(self.audio.add_tracks)
        self.library.favorite_requested.connect(self.favorite)
        for panel in (self.mini,self.expanded):
            panel.library_requested.connect(lambda:self.set_mode("library"))
            panel.favorite_requested.connect(lambda:self.favorite(self.audio.current()))
            panel.options_requested.connect(lambda:self.open_menu(self.mapToGlobal(QPoint(self.width()-30,50))))
        self.bridge.ready.connect(self.plex_ready)
        self.bridge.failed.connect(self.show_error)
        self.bridge.stopped.connect(self.show_error)
        self.audio.track_changed.connect(self.on_track)
        self.audio.queue_changed.connect(self.check_keep_playing)
        self.audio.playback_changed.connect(self.tray_playback)
        self.audio.status_changed.connect(lambda message:self.tray.setToolTip("ResonaDeck · "+message[:70]))
        QShortcut(QKeySequence("Space"),self,activated=self.audio.play_pause)
        QShortcut(QKeySequence("Ctrl+M"),self,activated=lambda:self.set_mode("expanded" if self._mode=="mini" else "mini"))
        QShortcut(QKeySequence("Ctrl+L"),self,activated=lambda:self.set_mode("library"))
        QShortcut(QKeySequence("Ctrl+Shift+P"),self,activated=lambda:self.set_always_on_top(not self.pin))
        QShortcut(QKeySequence("Ctrl+F"),self,activated=lambda:(self.set_mode("library"),self.library.search.setFocus()))
        QShortcut(QKeySequence("Ctrl+Right"),self,activated=self.audio.next)
        QShortcut(QKeySequence("Ctrl+Left"),self,activated=self.audio.previous)
        QShortcut(QKeySequence("Escape"),self,activated=self.back)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(lambda point:self.open_menu(self.mapToGlobal(point)))
        self.shell.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.shell.customContextMenuRequested.connect(lambda point:self.open_menu(self.shell.mapToGlobal(point)))

    def set_mode(self,mode,first=False):
        if mode not in ("mini","expanded","library"):
            return
        if not first and mode==self._mode:
            return
        if not first:
            self.settings.setValue("geometry_"+self._mode,self.saveGeometry())
        self._mode=mode
        self.stack.setCurrentIndex({"mini":0,"expanded":1,"library":2}[mode])
        # Only the actual player is visible in Mini mode, with no title strip.
        self.header.setVisible(mode != "mini")
        self.shell.setObjectName("ShellMini" if mode == "mini" else "Panel")
        self.shell.style().unpolish(self.shell)
        self.shell.style().polish(self.shell)
        bounds={"mini":(440,255,400,238),"expanded":(504,650,430,510),
                "library":(1120,760,650,490)}
        w,h,mw,mh=bounds[mode]
        self.setMinimumSize(mw,mh)
        restored=self.settings.value("geometry_"+mode)
        if isinstance(restored,(QByteArray,bytes)) and len(restored)>5:
            self.restoreGeometry(restored)
            self._constrain_to_screen()
        else:
            self.resize(w,h)
            if first:
                from PySide6.QtGui import QGuiApplication
                area=QGuiApplication.primaryScreen().availableGeometry()
                self.move(area.right()-self.width()-45,area.bottom()-self.height()-75)
        self.size_btn.setText("⛶" if mode=="mini" else "◱")
        self.library_btn.setVisible(mode!="library")
        self.brand.setText("◈  ResonaDeck" if mode!="library" else "◈  ResonaDeck   ·   Library")
        if mode=="library" and self.bridge.online and self.library.grid.count()==0:
            self.library.browse()
        self.update()
        self._save_mode()

    def _constrain_to_screen(self):
        from PySide6.QtGui import QGuiApplication
        screens=QGuiApplication.screens()
        rect=self.frameGeometry()
        if not any(screen.availableGeometry().intersects(rect) for screen in screens):
            area=QGuiApplication.primaryScreen().availableGeometry()
            self.move(area.center()-QPoint(self.width()//2,self.height()//2))

    def _save_mode(self):
        self.settings.setValue("mode",self._mode)
        self.settings.setValue("pin",self.pin)

    def set_always_on_top(self,enabled):
        self.pin=bool(enabled)
        visible=self.isVisible()
        # Window flags must be updated for Qt to apply topmost status.
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint,self.pin)
        if visible:
            self.show()
        self.pin_btn.setText("📌" if self.pin else "♢")
        if hasattr(self,"tray_pin"):
            self.tray_pin.setChecked(self.pin)
        self.settings.setValue("pin",self.pin)

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,"grip"):
            self.grip.move(self.width()-25,self.height()-25)

    def enterEvent(self,event):
        self.grip.show()
        super().enterEvent(event)

    def leaveEvent(self,event):
        self.grip.hide()
        super().leaveEvent(event)

    def contextMenuEvent(self,event):
        self.open_menu(event.globalPos())
        event.accept()

    def open_menu(self,position):
        menu=QMenu(self)
        menu.addAction("◉ Mini Player",lambda:self.set_mode("mini"))
        menu.addAction("▣ Expanded Player",lambda:self.set_mode("expanded"))
        menu.addAction("▦ Full Library",lambda:self.set_mode("library"))
        menu.addSeparator()
        pin=menu.addAction("📌 Always on Top")
        pin.setCheckable(True);pin.setChecked(self.pin)
        pin.triggered.connect(self.set_always_on_top)
        menu.addAction("✦ Surprise Me",lambda:DiscoveryDialog(self).exec())
        menu.addAction("★ Favorite Playing Track",lambda:self.favorite(self.audio.current()))
        menu.addAction("Save Queue as Playlist",self.save_playlist)
        menu.addAction("Save Listening Session",self.save_session)
        playlist_menu=menu.addMenu("Saved Playlists")
        for data in self.discovery["playlists"][-30:]:
            playlist_menu.addAction(str(data.get("name") or "Playlist"),
                lambda _,entry=data:self.audio.play_tracks(entry.get("items") or [],int(entry.get("index") or 0)))
        session_menu=menu.addMenu("Saved Sessions")
        for data in self.discovery["sessions"][-20:]:
            session_menu.addAction(str(data.get("name") or "Listening Session"),
                lambda _,entry=data:self.audio.play_tracks(
                    entry.get("items") or [],int(entry.get("index") or 0),
                    round(float(entry.get("position") or 0)*1000)))
        sleep=menu.addMenu("Sleep Timer")
        for minutes in (0,15,30,60,90,120):
            sleep.addAction("Off" if not minutes else f"{minutes} minutes",
                lambda _,m=minutes:self.sleep_timer(m))
        menu.addSeparator()
        menu.addAction("Plex Account and Servers",self.plex_menu)
        menu.addAction("Windows Settings",lambda:PreferencesDialog(self).exec())
        menu.addSeparator()
        menu.addAction("Hide to Tray",self.hide)
        menu.addAction("Exit",self.quit_app)
        menu.exec(position)

    def show_error(self,message):
        text=str(message)[:180]
        self.mini.status.setText(text)
        self.expanded.status.setText(text)

    def tray_playback(self,playing):
        if playing:
            self.tray.setToolTip("ResonaDeck · Playing music")
        else:
            self.tray.setToolTip("ResonaDeck · Paused")

    def show_normal(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def back(self):
        if self._mode=="library" and self.library.stack.currentIndex()==1:
            self.library.close_detail()
        else:
            self.set_mode("mini")

    def plex_ready(self):
        self.show_error("Checking your Plex account…")
        self.restore_plex()
        self.bridge.request("get_discovery_state",ok=self.load_discovery,fail=lambda error:None)

    def restore_plex(self):
        self.bridge.request("get_auth_state",ok=self.auth_status,fail=self.show_error)

    def auth_status(self,result):
        if not isinstance(result,dict) or not result.get("authenticated"):
            self.show_error("Connect Plex in the menu to start listening")
            return
        server=result.get("server") or {}
        connected=bool(server.get("connected") or server.get("baseUrl") or server.get("name"))
        if not connected:
            self._restore_tries+=1
            if self._restore_tries < 12:
                QTimer.singleShot(1200,self.restore_plex)
                return
            self.show_error("Plex account connected; choose a media server")
            return
        self._restore_tries=0
        self.show_error("Plex connected · Ready to listen")
        self.library.browse()
        self.bridge.request("get_libraries",ok=self._libraries,fail=lambda error:None)

    def _libraries(self,result):
        self.library._all_libraries=result.get("libraries",[]) if isinstance(result,dict) else []
        self.bridge.request("refresh_music_state",[False],fail=lambda error:None)

    def plex_menu(self):
        menu=QMenu(self)
        menu.addAction("Sign in to Plex",self.sign_in)
        menu.addAction("Choose Plex Home User",self.home_users)
        menu.addAction("Discover Plex Servers",self.choose_server)
        menu.addAction("Refresh Connection",lambda:self.bridge.request("recover_connection",
            ok=lambda response:self.restore_plex()))
        menu.addSeparator()
        menu.addAction("Sign out of Plex",self.sign_out)
        menu.exec(self.mapToGlobal(QPoint(70,80)))

    def sign_in(self):
        self.bridge.request("begin_plex_auth",
            ok=self._auth_started,
            fail=self.show_error)

    def _auth_started(self,result):
        if not result.get("success") or not result.get("url"):
            self.show_error(result.get("message","Could not connect to Plex"))
            return
        QDesktopServices.openUrl(QUrl(result["url"]))
        self.show_error("Approve the Plex login in your browser…")
        self._auth_timer.start()

    def _poll_auth(self):
        self.bridge.request("poll_plex_auth",
            ok=self._auth_progress,fail=self.show_error)

    def _auth_progress(self,result):
        if result.get("authenticated"):
            self._auth_timer.stop()
            self.restore_plex()
        elif result.get("pending") is False:
            self._auth_timer.stop()
            self.show_error(result.get("message","Plex sign-in not completed"))

    def home_users(self):
        self.bridge.request("get_home_users",ok=self._users,fail=self.show_error)

    def _users(self,result):
        users=result.get("users",[])
        if not users:
            self.show_error("No Plex Home users available")
            return
        labels=[str(x.get("title") or x.get("username") or x.get("id")) for x in users]
        selected,ok=QInputDialog.getItem(self,"Plex Home","Select your Plex Home user",labels,0,False)
        if not ok:
            return
        user=users[labels.index(selected)]
        pin=""
        if user.get("protected"):
            pin,ok=QInputDialog.getText(self,"Plex Home PIN","Enter this user's PIN",QLineEdit.EchoMode.Password)
            if not ok:
                return
        self.bridge.request("switch_home_user",[str(user.get("id") or user.get("uuid")),pin],
                            ok=lambda r:self.restore_plex() if r.get("success") else self.show_error(r.get("message","PIN rejected")),
                            fail=self.show_error)

    def choose_server(self):
        self.bridge.request("discover_servers",ok=self._servers,fail=self.show_error)

    def _servers(self,result):
        servers=result.get("servers",[])
        if not servers:
            self.show_error("Plex has not reported any reachable servers")
            return
        labels=[str(x.get("name") or x.get("machineId") or "Server") for x in servers]
        selected,ok=QInputDialog.getItem(self,"Plex Servers","Choose your Plex Media Server",labels,0,False)
        if not ok:
            return
        server=servers[labels.index(selected)]
        self.bridge.request("select_server",[str(server.get("machineId") or server.get("machine_id") or "")],
            ok=lambda response:self.restore_plex() if response.get("success") else self.show_error(response.get("message","Unable to connect")),
            fail=self.show_error)

    def sign_out(self):
        if QMessageBox.question(self,"Disconnect Plex","Remove the saved Plex sign-in for this Windows app?") != QMessageBox.StandardButton.Yes:
            return
        self.audio.stop()
        self.bridge.request("sign_out",ok=lambda _:self.show_error("Signed out of Plex"),
                            fail=self.show_error)

    def load_discovery(self,result):
        if not isinstance(result,dict):
            return
        state=result.get("state") or {}
        for k in ("favorites","sessions","playlists","recentIds"):
            if isinstance(state.get(k),list):
                self.discovery[k]=state[k]
        self.discovery["preferences"]=clean_discovery(state.get("preferences"))
        self.discovery["preferences"]["crossfade"]=self.audio.crossfade

    def save_discovery(self):
        self.bridge.request("save_discovery_state",[self.discovery],fail=self.show_error)

    def favorite(self,row):
        if not isinstance(row,dict) or not identity(row):
            return
        kind=str(row.get("type") or row.get("semanticType") or "").lower()
        if kind in ("album","directory","artist","show"):
            self.bridge.request("get_children",[identity(row)],
                ok=lambda data:self._favorite_tracks(data.get("tracks") or []))
        else:
            self._favorite_tracks([row])

    def _favorite_tracks(self,rows):
        favorites=self.discovery["favorites"]
        present={identity(x) for x in favorites}
        changed=0
        for row in rows:
            if not isinstance(row,dict) or not identity(row):
                continue
            key=identity(row)
            if key in present:
                favorites[:]=[x for x in favorites if identity(x)!=key]
                present.discard(key)
            else:
                favorites.append(row)
                present.add(key)
            changed+=1
        if changed:
            self.save_discovery()
            self.show_error(f"Favorites updated · {len(favorites)} saved tracks")

    def save_playlist(self):
        rows=self.audio.queue.tracks
        if not rows:
            self.show_error("Add music to the queue before saving a playlist")
            return
        name,ok=QInputDialog.getText(self,"Save Playlist","Playlist name")
        if not ok or not name.strip():
            return
        self.discovery["playlists"].append({"id":str(os.urandom(6).hex()),"name":name.strip(),
            "items":rows,"index":self.audio.queue.index})
        self.save_discovery()
        self.show_error(f"Saved playlist: {name}")

    def save_session(self):
        rows=self.audio.queue.tracks
        if not rows:
            return
        self.discovery["sessions"].append({"id":str(os.urandom(6).hex()),
            "name":"Listening Session","items":rows,"index":self.audio.queue.index,
            "position":self.audio.players[self.audio.active].position()/1000})
        self.discovery["sessions"]=self.discovery["sessions"][-30:]
        self.save_discovery()
        self.show_error("Listening session saved")

    def on_track(self,track):
        if not isinstance(track,dict):
            return
        title=str(track.get("title") or "Untitled")
        self.setWindowTitle("ResonaDeck · "+title)
        self.tray.setToolTip("ResonaDeck · "+title[:55])
        recent=self.discovery["recentIds"]
        recent.append(identity(track))
        self.discovery["recentIds"]=recent[-300:]
        self.save_discovery()
        self._apply_session_end()

    def _apply_session_end(self):
        import time
        if self._session_deadline and time.monotonic() >= self._session_deadline:
            self._session_deadline=0
            self._session_timer.stop()
            self._keep_playing=False
            self.audio.pause()
            self.show_error("Listening session complete")

    def check_keep_playing(self):
        if not self._keep_playing or self._discovery_busy:
            return
        remaining=len(self.audio.queue.tracks)-self.audio.queue.index-1
        if remaining<=2:
            self.surprise(append=True)

    def surprise(self,append=False):
        if self._discovery_busy or not self.bridge.online:
            return
        self._discovery_busy=True
        prefs=self.discovery["preferences"]
        category=prefs.get("category","music")
        if category=="all":
            category=random.choice(AUDIO_ROLES)
        count=int(prefs.get("sessionLength","20")) if str(prefs.get("sessionLength")) in ("10","20","40") else 20
        self._keep_playing=prefs.get("sessionLength")=="endless"
        favorites=self.discovery["favorites"]
        role_favorites=[x for x in favorites if x.get("libraryRole","music")==category]
        if prefs.get("favoritesOnly"):
            if not role_favorites:
                self._discovery_busy=False
                self.show_error("No saved favorites available for this category")
                return
            self._surprise_done({"items":role_favorites},count,append)
            return
        view="albums" if category=="music" and prefs.get("musicMode")=="albums" else "tracks"
        self.show_error("Surprise Me is discovering your next tracks…")
        self.bridge.request("browse_cached",[category,view,0,48,"title",False],
            ok=lambda response:self._surprise_catalog(category,view,count,append,response),
            fail=lambda error:self._surprise_error(error))

    def _surprise_catalog(self,role,view,count,append,response):
        if response.get("success") is False:
            self._surprise_error(response.get("message","Plex discovery failed"))
            return
        total=int(response.get("total") or len(response.get("items") or []))
        if total>48:
            offset=random.randint(0,max(0,total-48))
            self.bridge.request("browse_cached",[role,view,offset,48,"title",False],
                ok=lambda data:self._surprise_done(data,count,append,view),
                fail=lambda error:self._surprise_error(error))
        else:
            self._surprise_done(response,count,append,view)

    def _surprise_done(self,response,count,append,view="tracks"):
        rows=response.get("items") or []
        if view=="albums" and rows:
            album=random.choice(rows)
            self.bridge.request("get_children",[identity(album)],
                ok=lambda data:self._surprise_done({"items":data.get("tracks") or []},count,append,"tracks"),
                fail=lambda error:self._surprise_error(error))
            return
        selected=pick_surprise(rows,count,self.discovery["recentIds"])
        self._discovery_busy=False
        if not selected:
            self.show_error("Surprise Me found no playable tracks")
            return
        if append:
            self.audio.add_tracks(selected)
        else:
            self.audio.play_tracks(selected)
            duration={"30m":30,"60m":60,"120m":120}.get(str(self.discovery["preferences"].get("sessionLength")))
            if duration:
                import time
                self._session_deadline=time.monotonic()+duration*60
                self._session_timer.start()
            else:
                self._session_deadline=0
                self._session_timer.stop()
            self.set_mode("expanded")
        self.show_error(f"Surprise Me · {len(selected)} songs selected")

    def _surprise_error(self,error):
        self._discovery_busy=False
        self.show_error(str(error)[:150])

    def sleep_timer(self,minutes):
        self._sleep_left=max(0,int(minutes)*60)
        self._sleep_original=self.audio.volume
        if self._sleep_left:
            self._sleep_timer.start()
        else:
            self._sleep_timer.stop()
            self.audio.set_volume(self._sleep_original)
        self.show_error("Sleep timer Off" if not minutes else f"Sleep timer: {minutes} minutes")

    def _sleep_update(self):
        self._sleep_left=max(0,self._sleep_left-1)
        if self._sleep_left<=10 and self._sleep_left>0 and self.discovery["preferences"].get("sleepFade"):
            self.audio.set_volume(self._sleep_original*self._sleep_left/10)
        if self._sleep_left==0:
            self._sleep_timer.stop()
            self.audio.pause()
            self.audio.set_volume(self._sleep_original)

    def set_startup(self,enabled):
        # Per-user Windows Run key. Never request administrator privileges.
        self.settings.setValue("startup",bool(enabled))
        if sys.platform != "win32":
            return
        try:
            import winreg
            key_path=r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,key_path,0,winreg.KEY_SET_VALUE) as key:
                if enabled:
                    executable=str(Path(sys.executable if getattr(sys,"frozen",False) else __file__).resolve())
                    command=f'"{executable}"' if getattr(sys,"frozen",False) else f'"{sys.executable}" "{Path(__file__).resolve()}"'
                    winreg.SetValueEx(key,"ResonaDeckNative",0,winreg.REG_SZ,command)
                else:
                    try:
                        winreg.DeleteValue(key,"ResonaDeckNative")
                    except FileNotFoundError:
                        pass
        except OSError as error:
            self.show_error("Couldn't change Windows startup: "+str(error))

    def gamepad(self,name):
        if not self.isActiveWindow():
            return
        if name=="A":
            widget=QApplication.focusWidget()
            if isinstance(widget,QPushButton):
                widget.click()
            elif self._mode=="library" and self.library.grid.currentItem():
                self.library.activate_item(self.library.grid.currentItem())
            else:
                self.audio.play_pause()
        elif name=="B":
            self.back()
        elif name=="Start":
            self.audio.play_pause()
        elif name=="LB":
            self.audio.previous() if self._mode!="library" else self._category_step(-1)
        elif name=="RB":
            self.audio.next() if self._mode!="library" else self._category_step(1)

    def _category_step(self,delta):
        combo=self.library.roles
        combo.setCurrentIndex((combo.currentIndex()+delta)%combo.count())

    def closeEvent(self,event):
        if not self._quit and self.close_to_tray and QSystemTrayIcon.isSystemTrayAvailable():
            self.settings.setValue("geometry_"+self._mode,self.saveGeometry())
            self.hide()
            event.ignore()
            return
        self.settings.setValue("geometry_"+self._mode,self.saveGeometry())
        self.audio.shutdown()
        self.bridge.shutdown()
        event.accept()

    def quit_app(self):
        self._quit=True
        self.close()
        QApplication.quit()


def main():
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ValentineBSAA.ResonaDeck.Native")
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling,True) if hasattr(Qt.ApplicationAttribute,"AA_EnableHighDpiScaling") else None
    app=QApplication(sys.argv)
    app.setApplicationName("ResonaDeck Native")
    app.setOrganizationName("ValentineBSAA")
    app.setQuitOnLastWindowClosed(False)
    window=NativeWindow()
    window.show()
    result=app.exec()
    window.audio.shutdown()
    window.bridge.shutdown()
    return result


if __name__ == "__main__":
    raise SystemExit(main())
