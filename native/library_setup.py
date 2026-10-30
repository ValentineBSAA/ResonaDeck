"""Explicit Windows-native Plex library classification for first-run onboarding."""
from __future__ import annotations
from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox, QDialogButtonBox

ROLE_OPTIONS = (
    ("Music", "music"),
    ("Audiobooks", "audiobooks"),
    ("Podcasts", "podcasts"),
    ("Other audio", "other"),
    ("Ignore this library", "ignore"),
)

def suggested_assignment(library: dict, is_only: bool = False) -> str:
    role = str(library.get("role") or "").lower()
    if role in {value for _label, value in ROLE_OPTIONS}:
        return role
    suggested = str(library.get("suggestedRole") or "").lower()
    if suggested in ("music", "audiobooks", "podcasts"):
        return suggested
    # An unlabeled single Plex audio library should default to Music; more
    # ambiguous collections remain Other until the listener explicitly chooses.
    return "music" if is_only else "other"


class LibrarySetupDialog(QDialog):
    def __init__(self, libraries: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("ResonaDeck · Your Plex Libraries")
        self.setMinimumWidth(510)
        self.libraries = [dict(x) for x in libraries if x.get("key")]
        self.choices = []
        layout = QVBoxLayout(self)
        header = QLabel("CONNECT YOUR MUSIC")
        header.setObjectName("Eyebrow")
        layout.addWidget(header)
        intro = QLabel(
            "Plex is connected. Choose what each Plex audio library contains. "
            "Your Steam Deck settings are stored separately, so Windows needs "
            "this one-time setup. Nothing inside Plex will be modified."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        form = QFormLayout()
        for lib in self.libraries:
            choice = QComboBox()
            for title, value in ROLE_OPTIONS:
                choice.addItem(title, value)
            selected = suggested_assignment(lib, is_only=len(self.libraries) == 1)
            choice.setCurrentIndex(max(0, choice.findData(selected)))
            self.choices.append(choice)
            label = str(lib.get("title") or f"Library {lib.get('key')}")
            form.addRow(label, choice)
        layout.addLayout(form)
        footer = QLabel("After saving, ResonaDeck will load the selected music, books, "
                        "podcasts and other audio using their real Plex catalogs.")
        footer.setWordWrap(True)
        layout.addWidget(footer)
        actions = QDialogButtonBox(QDialogButtonBox.StandardButton.Save
                                   | QDialogButtonBox.StandardButton.Cancel)
        actions.accepted.connect(self.accept)
        actions.rejected.connect(self.reject)
        layout.addWidget(actions)

    def assignments(self) -> list[tuple[str,str,str]]:
        return [(str(lib["key"]), str(lib.get("title") or "Audio"),
                 str(choice.currentData()))
                for lib, choice in zip(self.libraries, self.choices)]
