"""Pure Qt Widgets views: Windows-first, never reproduces Decky's QAM."""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap, QFont
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMenu, QPushButton, QSlider, QStackedWidget, QVBoxLayout, QWidget, QSizePolicy
)
from artwork import VinylArt
from core import Pager, identity


def button(label, tip="", name=""):
    obj = QPushButton(label)
    if tip:
        obj.setToolTip(tip)
    if name:
        obj.setObjectName(name)
    obj.setCursor(Qt.CursorShape.PointingHandCursor)
    return obj


def readable_time(ms):
    t = max(0, int(ms) // 1000)
    return f"{t//3600}:{(t//60)%60:02d}:{t%60:02d}" if t >= 3600 else f"{t//60}:{t%60:02d}"


def placeholder(text, size=142):
    pix = QPixmap(size, size)
    pix.fill(QColor("#273a54"))
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor("#d4ad76"))
    font = QFont("Segoe UI", 36, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, (text or "♪")[:1].upper())
    painter.end()
    return pix


class PlayerPanel(QFrame):
    """Minimal by default. Same audio engine, different native layout."""
    full_requested = Signal()
    library_requested = Signal()
    options_requested = Signal()
    surprise_requested = Signal()
    favorite_requested = Signal()
    stop_requested = Signal()

    def __init__(self, engine, covers, expanded=False, parent=None):
        super().__init__(parent)
        self.engine, self.covers, self.expanded = engine, covers, expanded
        self.setObjectName("Panel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.art = VinylArt(self)
        self.art.clicked.connect(self.library_requested)
        self.title = QLabel("Ready to listen")
        self.title.setObjectName("Title")
        self.title.setWordWrap(True)
        self.artist = QLabel("Your Plex library. Your listening room.")
        self.artist.setObjectName("SubTitle")
        self.artist.setWordWrap(True)
        self.eyebrow = QLabel("RESONADECK   /   PLEX AUDIO")
        self.eyebrow.setObjectName("Eyebrow")
        self.position = QLabel("0:00")
        self.duration = QLabel("0:00")
        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.seek.setRange(0,1000)
        self.seek.setTracking(False)
        self.seek.sliderReleased.connect(lambda: self.engine.seek(self.seek.value()))
        # Use reliable Segoe UI/ASCII labels instead of the Steam glyphs that
        # rendered as tiny replacement squares on the creator's Windows PC.
        self.prev = button("PREV", "Previous track", "Transport")
        self.play = button("PLAY", "Play / Pause (Space)", "Transport")
        self.next = button("NEXT", "Next track", "Transport")
        self.favorite = button("FAV", "Favorite current track", "Transport")
        self.options = button("MORE", "Player options", "Transport")
        self.options.clicked.connect(self.options_requested)
        self.shuffle = button("SHUFFLE", "Shuffle", "Transport")
        self.repeat = button("REPEAT", "Repeat", "Transport")
        self.queue = button("QUEUE", "Open queue")
        self.browse = button("Browse Music", "Open your Plex library", "Primary")
        self.surprise = button("Surprise Me", "Play something unexpected", "Primary")
        self.browse.clicked.connect(self.library_requested)
        self.surprise.clicked.connect(self.surprise_requested)
        self.vol = QSlider(Qt.Orientation.Horizontal)
        self.vol.setRange(0,100)
        self.vol.setValue(round(engine.volume*100))
        self.vol.setFixedWidth(120)
        self.vol.valueChanged.connect(lambda value: self.engine.set_volume(value/100))
        self.prev.clicked.connect(engine.previous)
        self.play.clicked.connect(engine.play_pause)
        self.next.clicked.connect(engine.next)
        self.favorite.clicked.connect(self.favorite_requested)
        self.shuffle.clicked.connect(engine.toggle_shuffle)
        self.repeat.clicked.connect(engine.cycle_repeat)
        self.queue.clicked.connect(self.library_requested)
        self.status = QLabel("Connect Plex to begin. Use Browse Music or More > Plex Account.")
        self.status.setObjectName("Status")
        self.status.setWordWrap(True)

        def transport():
            row = QHBoxLayout()
            row.setSpacing(4)
            row.setContentsMargins(0,0,0,0)
            for widget in (self.prev,self.play,self.next,self.favorite,self.options):
                row.addWidget(widget)
            row.addStretch(1)
            return row

        def seekbar():
            row = QHBoxLayout()
            row.setSpacing(5)
            row.setContentsMargins(0,0,0,0)
            row.addWidget(self.position)
            row.addWidget(self.seek,1)
            row.addWidget(self.duration)
            return row

        main = QVBoxLayout(self)
        main.setSpacing(7)
        if not expanded:
            main.setContentsMargins(14, 13, 14, 12)
            body = QHBoxLayout()
            body.setSpacing(12)
            self.art.setFixedSize(138,138)
            body.addWidget(self.art)
            right = QVBoxLayout()
            right.setSpacing(4)
            right.addWidget(self.eyebrow)
            right.addWidget(self.title)
            right.addWidget(self.artist)
            right.addStretch(1)
            right.addLayout(seekbar())
            right.addLayout(transport())
            body.addLayout(right, 1)
            main.addLayout(body,1)
            main.addWidget(self.status)
        else:
            main.setContentsMargins(19,16,19,15)
            main.addWidget(self.eyebrow)
            self.art.setFixedSize(224,224)
            main.addWidget(self.art,0,Qt.AlignmentFlag.AlignHCenter)
            main.addWidget(self.title)
            main.addWidget(self.artist)
            main.addLayout(seekbar())
            main.addLayout(transport())
            extras = QHBoxLayout()
            extras.addWidget(self.shuffle)
            extras.addWidget(self.repeat)
            extras.addWidget(self.queue)
            extras.addStretch(1)
            extras.addWidget(QLabel("VOL"))
            extras.addWidget(self.vol)
            main.addLayout(extras)
            discovery = QHBoxLayout()
            discovery.addWidget(self.browse, 1)
            discovery.addWidget(self.surprise, 1)
            main.addLayout(discovery)
            main.addWidget(self.status)
            main.addStretch(1)
        engine.track_changed.connect(self.on_track)
        engine.progress_changed.connect(self.on_position)
        engine.playback_changed.connect(self.on_playing)
        engine.status_changed.connect(self.status.setText)
        engine.crossfade_changed.connect(self.status.setText)
        engine.queue_changed.connect(self._update_modes)
        self._update_modes()

    def mousePressEvent(self, event):
        # The actual player is the draggable window: no mini title bar.
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.window().windowHandle()
            if handle and handle.startSystemMove():
                event.accept()
                return
        super().mousePressEvent(event)

    def on_track(self, track):
        if not isinstance(track,dict):
            return
        self.title.setText(str(track.get("title") or "Untitled"))
        self.artist.setText(str(track.get("artist") or track.get("grandparentTitle") or track.get("album") or "Plex Audio"))
        self.eyebrow.setText(str(track.get("libraryRole") or "MUSIC").upper() + " · NOW PLAYING")
        self.art.set_art(QPixmap())
        key=identity(track)
        self.covers.for_item(track, lambda pix, target=key: self._accept_art(pix,target), mode="square")

    def _accept_art(self,pix,key):
        if self.engine.current() and identity(self.engine.current()) == key:
            self.art.set_art(pix)

    def on_position(self, position, duration):
        if not self.seek.isSliderDown():
            self.seek.setRange(0,max(1,int(duration)))
            self.seek.setValue(max(0,int(position)))
        self.position.setText(readable_time(position))
        self.duration.setText(readable_time(duration))

    def on_playing(self, playing):
        self.play.setText("PAUSE" if playing else "PLAY")
        self.art.set_playing(playing)

    def _update_modes(self):
        self.shuffle.setText("SHUFFLE ON" if self.engine.queue.shuffle else "SHUFFLE OFF")
        self.repeat.setText("REPEAT " + self.engine.queue.repeat.upper())
        self.queue.setText(f"QUEUE {len(self.engine.queue.tracks)}")


class LibraryPage(QFrame):
    """Real Plex browse with unbounded paging, mouse scroll, double-click and queue."""
    back_requested = Signal()
    play_tracks = Signal(object, int)
    add_tracks = Signal(object, bool)
    favorite_requested = Signal(object)
    surprise_requested = Signal()
    plex_requested = Signal()

    def __init__(self, backend, engine, covers, parent=None):
        super().__init__(parent)
        self.setObjectName("LibraryPanel")
        self.backend, self.engine, self.covers = backend, engine, covers
        self.pager = Pager(page_size=48)
        self.context_rows = []
        self.detail_tracks = []
        self.root_view = "albums"
        self._custom_mode = ""
        self._active_item = None
        self._loading = False
        self._search_generation = 0
        self._all_libraries = []
        self._selected_sections=[]

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16,15,16,14)
        outer.setSpacing(10)
        header = QHBoxLayout()
        self.back = button("‹ Player", "Return to floating player")
        self.brand = QLabel("RESONADECK   /   LIBRARY")
        self.brand.setObjectName("Eyebrow")
        self.plex = button("⚙ Plex", "Connect or change Plex server")
        self.surprise = button("✦ Surprise Me", "Start a discovery session", "Primary")
        header.addWidget(self.back)
        header.addWidget(self.brand)
        header.addStretch(1)
        header.addWidget(self.surprise)
        header.addWidget(self.plex)
        outer.addLayout(header)
        filters = QHBoxLayout()
        self.roles = QComboBox()
        for title,role in (("Music","music"),("Audiobooks","audiobooks"),("Podcasts","podcasts"),("More Audio","other")):
            self.roles.addItem(title,role)
        self.sections=QComboBox()
        self.sections.setToolTip("Choose a Plex Music library, including multiple Music sections")
        self.sections.setVisible(False)
        self.view = QComboBox()
        for title,view in (("Albums","albums"),("Artists","artists"),("Tracks","tracks")):
            self.view.addItem(title,view)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search artists, albums and tracks…")
        self.search.setClearButtonEnabled(True)
        self.search.returnPressed.connect(self.perform_search)
        self.refresh = button("⟳", "Refresh current category")
        self.queue_button = button("☷ Queue")
        self.favorites_button = button("★ Favorites")
        self.playlists_button = button("▤ Playlists")
        filters.addWidget(self.roles)
        filters.addWidget(self.sections)
        filters.addWidget(self.view)
        filters.addWidget(self.search,1)
        filters.addWidget(self.refresh)
        filters.addWidget(self.favorites_button)
        filters.addWidget(self.playlists_button)
        filters.addWidget(self.queue_button)
        outer.addLayout(filters)
        self.heading = QLabel("Music · Albums")
        self.heading.setObjectName("Title")
        self.counter = QLabel("Connecting…")
        self.counter.setObjectName("Status")
        topline = QHBoxLayout()
        topline.addWidget(self.heading)
        topline.addStretch(1)
        topline.addWidget(self.counter)
        outer.addLayout(topline)
        self.stack = QStackedWidget()
        self.grid = QListWidget()
        self.grid.setUniformItemSizes(True)
        self.grid.setViewMode(QListWidget.ViewMode.IconMode)
        self.grid.setIconSize(QSize(145,145))
        self.grid.setGridSize(QSize(190,211))
        self.grid.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.grid.setMovement(QListWidget.Movement.Static)
        self.grid.setFlow(QListWidget.Flow.LeftToRight)
        self.grid.setWordWrap(True)
        self.grid.setSpacing(5)
        self.grid.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.grid.itemDoubleClicked.connect(self.activate_item)
        self.grid.itemClicked.connect(self.click_item)
        self.grid.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.grid.customContextMenuRequested.connect(self._context_menu)
        self.grid.verticalScrollBar().valueChanged.connect(self._on_scroll)
        self.stack.addWidget(self.grid)
        detail_wrapper = QWidget()
        d_layout = QVBoxLayout(detail_wrapper)
        self.detail_back = button("‹ All albums")
        self.detail_title = QLabel("Album")
        self.detail_title.setObjectName("Title")
        self.detail_meta = QLabel("")
        self.detail_meta.setObjectName("SubTitle")
        self.detail_list = QListWidget()
        self.detail_list.setAlternatingRowColors(False)
        self.detail_list.itemDoubleClicked.connect(self.play_detail)
        self.detail_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.detail_list.customContextMenuRequested.connect(self._detail_context)
        d_actions = QHBoxLayout()
        self.detail_play = button("▶ Play All", name="Primary")
        self.detail_shuffle = button("⇄ Shuffle")
        self.detail_add = button("+ Add to Queue")
        d_actions.addWidget(self.detail_back)
        d_actions.addWidget(self.detail_play)
        d_actions.addWidget(self.detail_shuffle)
        d_actions.addWidget(self.detail_add)
        d_actions.addStretch(1)
        d_layout.addWidget(self.detail_title)
        d_layout.addWidget(self.detail_meta)
        d_layout.addLayout(d_actions)
        d_layout.addWidget(self.detail_list,1)
        self.stack.addWidget(detail_wrapper)
        outer.addWidget(self.stack,1)
        footer = QHBoxLayout()
        self.load_more = button("Load more albums", "Load next Plex page")
        self.info = QLabel("Double-click a cover to open an album. Use the mouse wheel to browse.")
        self.info.setObjectName("Status")
        footer.addWidget(self.info,1)
        footer.addWidget(self.load_more)
        outer.addLayout(footer)

        self.back.clicked.connect(self.back_requested)
        self.plex.clicked.connect(self.plex_requested)
        self.surprise.clicked.connect(self.surprise_requested)
        self.roles.currentIndexChanged.connect(self._role_changed)
        self.sections.currentIndexChanged.connect(lambda: self.browse(reset=True))
        self.view.currentIndexChanged.connect(lambda: self.browse(reset=True))
        self.refresh.clicked.connect(lambda: self.browse(reset=True,refresh=True))
        self.load_more.clicked.connect(self._load_next)
        self.detail_back.clicked.connect(self.close_detail)
        self.detail_play.clicked.connect(lambda: self.play_tracks.emit(self.detail_tracks,0))
        self.detail_shuffle.clicked.connect(self._shuffle_detail)
        self.detail_add.clicked.connect(lambda: self.add_tracks.emit(self.detail_tracks,False))
        self.queue_button.clicked.connect(self.show_queue)
        self.favorites_button.clicked.connect(lambda: self.plex_requested.emit() if not hasattr(self,"show_favorites") else self.show_favorites())
        self.playlists_button.clicked.connect(self.show_playlists)
        self.setMinimumSize(640,480)

    def attach_favorites(self, provider):
        self.show_favorites = provider

    def current_role(self):
        return str(self.roles.currentData() or "music")

    def current_view(self):
        return str(self.view.currentData() or "albums")

    def _role_changed(self):
        self.update_sections(self._all_libraries)
        self.browse(reset=True)

    def update_sections(self,libraries):
        self._all_libraries=list(libraries)
        chosen=self.sections.currentData()
        role=self.current_role()
        self.sections.blockSignals(True)
        self.sections.clear()
        choices=[lib for lib in self._all_libraries if
                 lib.get("role")==role or (lib.get("role")=="unassigned" and lib.get("suggestedRole")==role)]
        for lib in choices:
            self.sections.addItem(str(lib.get("title") or "Plex Library"),str(lib.get("key") or ""))
        i=self.sections.findData(chosen)
        if i>=0:
            self.sections.setCurrentIndex(i)
        self.sections.setVisible(role=="music" and len(choices)>1)
        self.sections.blockSignals(False)

    def browse(self,reset=True,refresh=False):
        if not self.backend.online:
            self.counter.setText("Connect to Plex to browse")
            return
        self._custom_mode = ""
        self.stack.setCurrentIndex(0)
        self.load_more.show()
        role, view = self.current_role(), self.current_view()
        if reset:
            self.pager.reset(role,view)
            self.grid.clear()
            self.search.clear()
        self.heading.setText(f"{self.roles.currentText()} · {self.view.currentText()}")
        self._load_next(refresh=refresh)

    def _load_next(self,refresh=False):
        token=self.pager.start()
        if token is None:
            self.load_more.setEnabled(False)
            return
        generation,offset=token
        self.load_more.setEnabled(False)
        self.counter.setText("Loading Plex catalog…")
        self.backend.request("browse_cached",
            [self.pager.role,self.pager.view,offset,self.pager.page_size,"title",refresh,
             str(self.sections.currentData() or "") if self.pager.role=="music" else ""],
            ok=lambda payload,gen=generation:self._received(gen,payload),
            fail=lambda error,gen=generation:self._browse_error(gen,error))

    def _browse_error(self,generation,error):
        if generation!=self.pager.generation:
            return
        self.pager.busy=False
        self.counter.setText("Unable to load Plex catalog")
        self.info.setText(str(error)[:180] + " · Check Plex > Manage Libraries")
        self.load_more.setEnabled(True)

    def _received(self,generation,payload):
        if not self.pager.receive(generation,payload):
            self._browse_error(generation,str(payload.get("message") or "Could not read Plex catalog"))
            return
        old=self.grid.count()
        for row in self.pager.rows[old:]:
            self._add_row(row, row.get("type","album"))
        self.counter.setText(f"{self.pager.total:,} items · {len(self.pager.rows):,} loaded")
        self.info.setText("Scroll for more. Double-click to play or open a collection.")
        self.load_more.setEnabled(self.pager.has_more)
        self.load_more.setVisible(self.pager.has_more)

    def _add_row(self,row,kind="album"):
        if not isinstance(row,dict):
            return
        role=row.get("libraryRole") or self.current_role()
        row={**row,"libraryRole":role}
        name=str(row.get("title") or "Untitled")
        subtitle=str(row.get("artist") or row.get("parentTitle") or row.get("grandparentTitle") or "")
        label=name[:37] + ("…" if len(name)>37 else "")
        if subtitle:
            label+="\n"+subtitle[:27]
        item=QListWidgetItem(QIcon(placeholder(name)),label)
        item.setData(Qt.ItemDataRole.UserRole, {"item":row,"kind":kind})
        item.setToolTip((name+"\n"+subtitle).strip())
        self.grid.addItem(item)
        uid=identity(row)
        self.covers.for_item(row,
            lambda pix,owner=item,key=uid: self._apply_icon(owner,pix,key))

    def _apply_icon(self,owner,pix,key):
        if pix.isNull() or owner.listWidget() != self.grid:
            return
        row=owner.data(Qt.ItemDataRole.UserRole) or {}
        if identity(row.get("item") or {}) != key:
            return
        owner.setIcon(QIcon(pix.scaled(145,145,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation)))

    def _on_scroll(self,value):
        if self.stack.currentIndex()!=0 or self._custom_mode or not self.pager.has_more:
            return
        bar=self.grid.verticalScrollBar()
        if value >= bar.maximum()-100:
            self._load_next()

    def click_item(self,item):
        data=item.data(Qt.ItemDataRole.UserRole) or {}
        row=data.get("item") or {}
        self.info.setText(f"{row.get('title','Untitled')} · Double-click to open or play")

    def activate_item(self,item):
        data=item.data(Qt.ItemDataRole.UserRole) or {}
        row=data.get("item") or {}
        kind=str(data.get("kind") or self.current_view()).lower()
        if kind in ("tracks","track","audio","song","episode"):
            self.play_tracks.emit([row],0)
            return
        if kind in ("artists","artist","author"):
            method="get_artist_tracks"
        elif kind in ("playlist","playlists"):
            method="get_playlist_items"
        else:
            method="get_children"
        self._active_item=row
        self.counter.setText("Opening "+str(row.get("title") or "collection")+"…")
        self.backend.request(method,[identity(row)],
            ok=lambda response:self._open_detail(row,response),
            fail=lambda error:self.info.setText(str(error)[:150]))

    def _open_detail(self,row,response):
        if not isinstance(response,dict) or response.get("success") is False:
            self.info.setText(str(response.get("message","Could not open collection"))[:180])
            return
        tracks=response.get("tracks") or response.get("items") or []
        self.detail_tracks=[{**r,"libraryRole":r.get("libraryRole") or row.get("libraryRole") or self.current_role()}
                            for r in tracks if isinstance(r,dict) and identity(r)]
        self.detail_title.setText(str(row.get("title") or "Collection"))
        self.detail_meta.setText(f"{len(self.detail_tracks)} playable tracks")
        self.detail_list.clear()
        for index,track in enumerate(self.detail_tracks):
            title=str(track.get("title") or "Untitled")
            item=QListWidgetItem(f"{index+1:02d}   {title}   ·   {readable_time(float(track.get('duration') or 0)*1000)}")
            item.setData(Qt.ItemDataRole.UserRole,index)
            self.detail_list.addItem(item)
        self.stack.setCurrentIndex(1)
        self.load_more.hide()
        self.info.setText("Double-click a track to play. Play All preserves album track order.")
        self.detail_play.setEnabled(bool(self.detail_tracks))

    def close_detail(self):
        self.stack.setCurrentIndex(0)
        self.load_more.setVisible(self.pager.has_more)
        self.info.setText("Scroll for more albums or click a collection.")
        if self._custom_mode:
            self.heading.setText(self._custom_mode.title())

    def play_detail(self,item):
        index=item.data(Qt.ItemDataRole.UserRole)
        if 0<=index<len(self.detail_tracks):
            self.play_tracks.emit(self.detail_tracks,index)

    def _shuffle_detail(self):
        import random
        rows=self.detail_tracks[:]
        random.shuffle(rows)
        self.play_tracks.emit(rows,0)

    def _context_menu(self,point):
        selected=self.grid.itemAt(point)
        if not selected:
            return
        row=(selected.data(Qt.ItemDataRole.UserRole) or {}).get("item") or {}
        menu=QMenu(self)
        open_action=menu.addAction("Open / Play")
        add_action=menu.addAction("Add to Queue")
        next_action=menu.addAction("Play Next")
        star_action=menu.addAction("★ Toggle Favorite")
        choice=menu.exec(self.grid.mapToGlobal(point))
        if choice==open_action:
            self.activate_item(selected)
        elif choice==star_action:
            self.favorite_requested.emit(row)
        elif choice in (add_action,next_action):
            kind=(selected.data(Qt.ItemDataRole.UserRole) or {}).get("kind","")
            if str(kind).lower() in ("tracks","track","audio"):
                self.add_tracks.emit([row],choice==next_action)
            else:
                self.backend.request("get_children",[identity(row)],
                    ok=lambda data:self.add_tracks.emit(data.get("tracks") or [],choice==next_action))

    def _detail_context(self,point):
        selected=self.detail_list.itemAt(point)
        if not selected:
            return
        index=selected.data(Qt.ItemDataRole.UserRole)
        menu=QMenu(self)
        play=menu.addAction("Play from Here")
        nxt=menu.addAction("Play Next")
        add=menu.addAction("Add to Queue")
        star=menu.addAction("★ Toggle Favorite")
        choice=menu.exec(self.detail_list.mapToGlobal(point))
        if choice==play:
            self.play_tracks.emit(self.detail_tracks,index)
        elif choice==nxt:
            self.add_tracks.emit([self.detail_tracks[index]],True)
        elif choice==add:
            self.add_tracks.emit([self.detail_tracks[index]],False)
        elif choice==star:
            self.favorite_requested.emit(self.detail_tracks[index])

    def perform_search(self):
        query=self.search.text().strip()
        if not query:
            self.browse()
            return
        self._search_generation+=1
        generation=self._search_generation
        self._custom_mode="search"
        self.stack.setCurrentIndex(0)
        self.grid.clear()
        self.heading.setText("Search · "+query)
        self.load_more.hide()
        self.counter.setText("Searching Plex…")
        self.backend.request("search",[query,"everything"],
            ok=lambda response,generation=generation:self._search_done(response,generation),
            fail=lambda error:self.counter.setText(str(error)[:120]))

    def _search_done(self,response,generation):
        if generation!=self._search_generation or self._custom_mode!="search":
            return
        self.grid.clear()
        for kind in ("artists","albums","tracks"):
            for row in response.get(kind,[]) or []:
                self._add_row(row,kind)
        self.counter.setText(f"{self.grid.count()} matches")

    def show_queue(self):
        rows=self.engine.queue.tracks
        self._custom_mode="queue"
        self.heading.setText("Up Next · Queue")
        self.grid.clear()
        for row in rows:
            self._add_row(row,"track")
        self.counter.setText(f"{len(rows)} tracks")
        self.load_more.hide()
        self.stack.setCurrentIndex(0)

    def show_custom(self,title,rows):
        self._custom_mode=title
        self.heading.setText(title)
        self.grid.clear()
        for row in rows:
            self._add_row(row,"track")
        self.counter.setText(f"{self.grid.count()} tracks")
        self.load_more.hide()
        self.stack.setCurrentIndex(0)

    def show_playlists(self):
        self._custom_mode="playlists"
        self.grid.clear()
        self.heading.setText("Plex Playlists")
        self.counter.setText("Loading playlists…")
        self.load_more.hide()
        self.backend.request("get_playlists",[],
            ok=lambda data:self._playlists(data),
            fail=lambda error:self.counter.setText(str(error)[:120]))

    def _playlists(self,data):
        for row in data.get("playlists") or []:
            self._add_row(row,"playlist")
        self.counter.setText(f"{self.grid.count()} Plex playlists")
