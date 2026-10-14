"""Verify the exact approved fallback assets are packaged and usable."""
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
for role in ('music','audiobooks','podcasts'):
    png=ROOT/'assets'/f'fallback-{role}.png'
    webp=ROOT/'assets'/f'fallback-{role}.webp'
    assert png.is_file() and png.stat().st_size>500_000, png
    assert webp.is_file() and webp.stat().st_size>20_000, webp
    with Image.open(png) as im: assert im.width==im.height and im.width>=1200, (role,im.size)
    with Image.open(webp) as im: assert im.size==(512,512), (role,im.size)
print('PASS: user-approved Music/Audiobook/Podcast fallback PNGs and 512px WebP runtime copies are packaged and valid.')
