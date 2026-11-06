from pathlib import Path
from PIL import Image

repo = Path(__file__).resolve().parents[2]
source = repo / "assets" / "resonadeck-icon.webp"
target = repo / "windows" / "icon.ico"
with Image.open(source) as artwork:
    artwork.convert("RGBA").save(target, format="ICO",
                                 sizes=[(16, 16), (24, 24), (32, 32),
                                        (48, 48), (64, 64), (128, 128), (256, 256)])
print(target)
