"""ResonaDeck Windows 11 palette, independent of CSS Loader/Steam."""
PALETTE = {
    "background": "#111724",
    "surface": "#1a2637",
    "surface_high": "#283b51",
    "text": "#f3f1f7",
    "muted": "#aab3c7",
    "wine": "#9b425c",
    "gold": "#e9b96c",
}

STYLE = """
QWidget{color:#f3f1f7;font-family:'Segoe UI',Arial,sans-serif;font-size:13px}
QFrame#Panel{background:#172338;border:1px solid #52718b;border-radius:18px}
QFrame#LibraryPanel{background:#101927;border:1px solid #36485f;border-radius:16px}
QFrame#Toolbar{background:transparent;border:none}
QLabel#Title{font-size:19px;font-weight:750;color:#faf5fc}
QLabel#SubTitle{font-size:12px;color:#b5c3d5}
QLabel#Eyebrow{font-size:10px;letter-spacing:2px;font-weight:bold;color:#e5b868}
QLabel#Status{font-size:11px;color:#9eb6cf}
QPushButton{background:#25364d;border:1px solid #516881;border-radius:9px;
    padding:7px 10px;color:#f3f3f8;font-weight:600}
QPushButton:hover{background:#344e67;border-color:#e9b96c}
QPushButton:pressed{background:#785265}
QPushButton:disabled{color:#788294;background:#152335}
QPushButton#Primary{background:#83415c;border:1px solid #dbac7f;font-weight:bold}
QPushButton#Primary:hover{background:#a15270}
QPushButton#Chrome{background:transparent;border:none;padding:3px;font-size:16px}
QPushButton#Chrome:hover{background:#ffffff26;border-radius:7px}
QPushButton#Transport{font-size:19px;background:transparent;border:0;padding:3px 8px}
QPushButton#Transport:hover{color:#eab867}
QPushButton#Tab:checked{background:#67384f;border:1px solid #e7b978}
QSlider::groove:horizontal{background:#41576d;border-radius:3px;height:5px}
QSlider::handle:horizontal{background:#e7b96c;border-radius:8px;width:15px;margin:-5px 0}
QSlider::sub-page:horizontal{background:#b5748a;border-radius:3px}
QComboBox,QLineEdit,QSpinBox{background:#19293e;border:1px solid #65738b;
    border-radius:7px;padding:7px;color:#eaf2fa;selection-background-color:#8e435e}
QComboBox QAbstractItemView{background:#202f45;color:#fff;selection-background-color:#7b4b62}
QListWidget{background:transparent;color:#f6f7fd;border:none;outline:0}
QListWidget::item{border-radius:12px;margin:3px;padding:7px}
QListWidget::item:hover{background:#334761}
QListWidget::item:selected{background:#76435a;border:1px solid #e7ba77}
QScrollBar:vertical{background:transparent;width:8px}
QScrollBar::handle:vertical{background:#647791;border-radius:4px;min-height:28px}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0px}
QMenu{background:#192538;color:#f4f6fc;border:1px solid #62768f;
    border-radius:7px;padding:6px}
QMenu::item{padding:8px 26px}
QMenu::item:selected{background:#79435c}
QCheckBox{spacing:8px}
QCheckBox::indicator{width:16px;height:16px}
QProgressBar{background:#18253a;border-radius:5px;text-align:center}
QProgressBar::chunk{background:#ba798f;border-radius:5px}
"""
