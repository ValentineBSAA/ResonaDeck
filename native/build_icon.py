"""Convert the existing licensed project artwork into a multi-resolution Windows icon."""
from pathlib import Path
from PIL import Image
root = Path(__file__).resolve().parents[1]
with Image.open(root / "assets" / "resonadeck-icon.webp") as image:
    image.convert("RGBA").save(root / "native" / "resonadeck.ico",
        format="ICO", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print("Created native/resonadeck.ico")
