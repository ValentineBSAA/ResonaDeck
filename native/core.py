"""Pure-Python queue, catalog paging and discovery rules for the native UI.

No Qt imports: these rules are exercised before building the Windows installer.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

ALLOWED_CROSSFADE = (0, 3, 5, 8, 10)
AUDIO_ROLES = ("music", "audiobooks", "podcasts", "other")
VIEWS = ("albums", "artists", "tracks")


def media_kind(item: dict) -> str:
    role = str(item.get("libraryRole") or "music").lower()
    return "audiobook" if role == "audiobooks" else "podcast" if role == "podcasts" else "music"


def playable(items: list[dict]) -> list[dict]:
    return [dict(item) for item in items if str(item.get("ratingKey") or "").strip()]


def identity(item: dict) -> str:
    return str(item.get("ratingKey") or item.get("key") or "")


def clean_discovery(raw=None):
    defaults = {"category": "music", "musicMode": "tracks", "favoritesOnly": False,
                "count": 20, "sessionLength": "20", "crossfade": 8, "sleepFade": False}
    value = {**defaults, **(raw if isinstance(raw, dict) else {})}
    if value["category"] not in (*AUDIO_ROLES, "all"):
        value["category"] = "music"
    if value["musicMode"] not in ("tracks", "albums", "rediscover"):
        value["musicMode"] = "tracks"
    try:
        value["crossfade"] = int(value["crossfade"])
    except (ValueError, TypeError):
        value["crossfade"] = 8
    if value["crossfade"] not in ALLOWED_CROSSFADE:
        value["crossfade"] = 8
    if str(value["sessionLength"]) not in ("10", "20", "40", "30m", "60m", "120m", "endless"):
        value["sessionLength"] = "20"
    value["favoritesOnly"] = bool(value["favoritesOnly"])
    return value


@dataclass
class Pager:
    role: str = "music"
    view: str = "albums"
    page_size: int = 48
    offset: int = 0
    total: int = 0
    has_more: bool = True
    busy: bool = False
    generation: int = 0
    rows: list[dict] = field(default_factory=list)

    def reset(self, role: str, view: str):
        self.role, self.view = role, view
        self.offset, self.total, self.has_more, self.busy = 0, 0, True, False
        self.generation += 1
        self.rows = []

    def start(self):
        if self.busy or not self.has_more:
            return None
        self.busy = True
        return self.generation, self.offset

    def receive(self, generation: int, response: dict) -> bool:
        if generation != self.generation:
            return False
        self.busy = False
        if response.get("success") is False:
            return False
        items = list(response.get("items") or [])
        seen = {identity(item) for item in self.rows}
        for row in items:
            if identity(row) and identity(row) not in seen:
                self.rows.append(dict(row))
                seen.add(identity(row))
        # Offset comes from Plex request position, not deduplicated visible count.
        self.offset = max(self.offset, int(response.get("offset") or self.offset) + len(items))
        self.total = max(0, int(response.get("total") or len(self.rows)))
        next_page = bool(response.get("hasMore", self.offset < self.total))
        self.has_more = next_page and bool(items) and self.offset < self.total
        return True


@dataclass
class Queue:
    tracks: list[dict] = field(default_factory=list)
    index: int = -1
    repeat: str = "off"
    shuffle: bool = False
    history: list[int] = field(default_factory=list)

    @property
    def current(self) -> dict | None:
        return self.tracks[self.index] if 0 <= self.index < len(self.tracks) else None

    def replace(self, tracks, index=0):
        self.tracks = playable(tracks)
        self.index = max(0, min(int(index), len(self.tracks) - 1)) if self.tracks else -1
        self.history.clear()
        return self.current

    def enqueue(self, tracks, next_up=False):
        rows = playable(tracks)
        if next_up and self.index >= 0:
            at = self.index + 1
            self.tracks[at:at] = rows
        else:
            self.tracks.extend(rows)
        if self.index < 0 and self.tracks:
            self.index = 0
        return len(rows)

    def candidate(self, manual=False, rng=None) -> int | None:
        if not self.tracks:
            return None
        if self.repeat == "one" and not manual:
            return self.index
        if self.shuffle and len(self.tracks) > 1:
            options = [i for i in range(len(self.tracks)) if i != self.index]
            # Avoid recently heard indices until the available pool is exhausted.
            fresh = [i for i in options if i not in self.history[-min(12, len(options)):]]
            return (rng or random).choice(fresh or options)
        candidate = self.index + 1
        if candidate < len(self.tracks):
            return candidate
        return 0 if self.repeat == "all" else None

    def advance(self, manual=False, rng=None):
        next_index = self.candidate(manual=manual, rng=rng)
        if next_index is None:
            return None
        if self.index >= 0 and self.index != next_index:
            self.history.append(self.index)
            self.history = self.history[-200:]
        self.index = next_index
        return self.current

    def previous(self):
        if self.history:
            self.index = self.history.pop()
        elif self.index > 0:
            self.index -= 1
        elif self.repeat == "all" and self.tracks:
            self.index = len(self.tracks) - 1
        return self.current

    def remove(self, position):
        if not 0 <= position < len(self.tracks):
            return False
        del self.tracks[position]
        if not self.tracks:
            self.index = -1
        elif position < self.index:
            self.index -= 1
        elif position == self.index:
            self.index = min(self.index, len(self.tracks) - 1)
        self.history.clear()
        return True


def pick_surprise(rows: list[dict], amount: int, recent=None, rng=None) -> list[dict]:
    rng = rng or random
    entries = playable(rows)
    recent = set(str(x) for x in (recent or []))
    fresh = [row for row in entries if identity(row) not in recent]
    candidates = fresh if len(fresh) >= min(amount, len(entries)) else entries
    k = min(max(1, int(amount)), len(candidates))
    return rng.sample(candidates, k) if k else []
