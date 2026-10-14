"""0.9.6 artwork payload compatibility checks against the real backend validator."""
from __future__ import annotations
import importlib.util, logging, sys, tempfile, types, zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
decky=types.ModuleType("decky")
decky.DECKY_PLUGIN_VERSION="0.9.8-test"
decky.DECKY_PLUGIN_RUNTIME_DIR="/tmp/resonadeck095-runtime"
decky.DECKY_PLUGIN_SETTINGS_DIR="/tmp/resonadeck095-settings"
decky.DECKY_PLUGIN_LOG_DIR="/tmp/resonadeck095-log"
decky.DECKY_USER_HOME="/tmp"
decky.logger=logging.getLogger("resonadeck095-test")
sys.modules["decky"]=decky
spec=importlib.util.spec_from_file_location("resonadeck_backend_095",ROOT/"resonadeck_backend.py")
rb=importlib.util.module_from_spec(spec); assert spec and spec.loader
sys.modules[spec.name]=rb; spec.loader.exec_module(rb)

check=rb.Plugin._image_payload_complete
sniff=rb.Plugin._sniff_image_type

# JPEG: 0.9.4 rejected this because EOI is more than 64 bytes from EOF.
jpeg=b"\xff\xd8\xff\xe0"+b"J"*200+b"\xff\xd9"+b"TRAILING-METADATA"*10
assert sniff(jpeg,"image/jpeg")=="image/jpeg"
assert check(jpeg,"image/jpeg"), "valid JPEG with trailing bytes must be accepted"
assert not check(b"\xff\xd8\xff\xe0"+b"J"*300,"image/jpeg"), "JPEG without EOI must fail"

# Minimal structurally valid PNG with trailing bytes.
def chunk(kind: bytes, payload: bytes=b""):
    body=kind+payload
    return len(payload).to_bytes(4,"big")+body+(zlib.crc32(body)&0xffffffff).to_bytes(4,"big")
png=b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00")+chunk(b"IEND")+b"tail"*30
assert check(png,"image/png"), "PNG with real IEND plus trailing bytes must be accepted"
assert not check(png[:png.find(b"IEND")-4],"image/png"), "PNG truncated before IEND must fail"

# WebP RIFF declared length may be followed by harmless trailing bytes.
webp_payload=b"WEBP"+b"VP8 "+(4).to_bytes(4,"little")+b"DATA"
webp=b"RIFF"+len(webp_payload).to_bytes(4,"little")+webp_payload+b"extra"*20
assert check(webp,"image/webp")

# Cached validation must preserve a now-valid trailing-byte JPEG instead of deleting it.
with tempfile.TemporaryDirectory() as td:
    data=Path(td)/"a.bin"; meta=Path(td)/"a.json"
    data.write_bytes(jpeg); meta.write_text('{"contentType":"image/jpeg"}')
    obj=object.__new__(rb.Plugin)
    valid,typ=rb.Plugin._validate_cached_art(obj,data,meta)
    assert valid and typ=="image/jpeg" and data.exists()

assert rb.ARTWORK_HYDRATION_GENERATION=="0.9.9-library-refresh-v1"
print("PASS: 0.9.6 accepts complete JPEG/PNG/WebP payloads with trailing bytes, rejects obvious truncation, and preserves compatible cached art. Hardware NOT tested.")
