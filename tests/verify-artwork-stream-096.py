"""0.9.6 real artwork stream completion regression checks."""
from __future__ import annotations
import asyncio, importlib.util, logging, sys, types
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
decky=types.ModuleType("decky")
decky.DECKY_PLUGIN_VERSION="0.9.8-test"
decky.DECKY_PLUGIN_RUNTIME_DIR="/tmp/resonadeck096-runtime"
decky.DECKY_PLUGIN_SETTINGS_DIR="/tmp/resonadeck096-settings"
decky.DECKY_PLUGIN_LOG_DIR="/tmp/resonadeck096-log"
decky.DECKY_USER_HOME="/tmp"
decky.logger=logging.getLogger("resonadeck096-test")
sys.modules["decky"]=decky
spec=importlib.util.spec_from_file_location("resonadeck_backend_096",ROOT/"resonadeck_backend.py")
rb=importlib.util.module_from_spec(spec); assert spec and spec.loader
sys.modules[spec.name]=rb; spec.loader.exec_module(rb)

class FragmentedStream:
    """Mimic Deck/Plex where read(big_n) exposes only current 16/32 KiB buffers."""
    def __init__(self, payload: bytes, pattern=(16384,32768)):
        self.payload=payload; self.pos=0; self.pattern=pattern; self.i=0; self.calls=[]
    async def read(self, n: int) -> bytes:
        self.calls.append(n)
        if self.pos >= len(self.payload): return b""
        natural=self.pattern[self.i % len(self.pattern)]; self.i += 1
        take=min(n,natural,len(self.payload)-self.pos)
        out=self.payload[self.pos:self.pos+take]; self.pos += take
        await asyncio.sleep(0)
        return out

async def main():
    # Reproduce the hardware symptom: first read is 16 KiB despite an 86+ KiB body.
    jpeg=b"\xff\xd8\xff\xe0" + b"A"*100_000 + b"\xff\xd9" + b"tail"*100
    stream=FragmentedStream(jpeg)
    got=await rb.Plugin._read_artwork_stream(stream, rb.ART_MAX_BYTES)
    assert got==jpeg, (len(got),len(jpeg))
    assert len(stream.calls) >= 4, "test did not actually fragment the body"
    assert rb.Plugin._sniff_image_type(got,"image/jpeg")=="image/jpeg"
    assert rb.Plugin._image_payload_complete(got,"image/jpeg")

    # One call would reproduce 0.9.5's failure exactly.
    one=FragmentedStream(jpeg)
    first=await one.read(rb.ART_MAX_BYTES+1)
    assert len(first)==16384 and len(first) < len(jpeg)

    # Reader remains bounded: it returns at most limit+1 so the caller can reject it.
    small_limit=100_000
    huge=b"Z"*(small_limit+50_000)
    bounded=await rb.Plugin._read_artwork_stream(FragmentedStream(huge,(32768,)), small_limit)
    assert len(bounded)==small_limit+1

    assert rb.ARTWORK_HYDRATION_GENERATION=="0.9.9-library-refresh-v1"
    print("PASS: 0.9.6 drains fragmented 16/32 KiB artwork reads to EOF and remains size-bounded. Hardware NOT tested.")

asyncio.run(main())
