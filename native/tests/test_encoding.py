"""Reproduces the Windows cp1252 metadata failure reported in the first preview."""
import asyncio
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


class ProtocolTests(unittest.TestCase):
    def test_unicode_album_titles_survive_windows_charmap(self):
        # Use the actual production send() with a non-Unicode capable pipe,
        # precisely the old behavior on some Windows PyInstaller launch modes.
        root = Path(__file__).resolve().parents[2]
        sys.path.insert(0, str(root / "native"))
        with tempfile.TemporaryDirectory() as temp:
            os.environ["RESONADECK_WINDOWS_DATA_DIR"] = temp
            import bridge
            data = io.BytesIO()
            old = bridge.sys.stdout
            ascii_unsafe_pipe = io.TextIOWrapper(data, encoding="cp1252", errors="strict")
            try:
                bridge.sys.stdout = ascii_unsafe_pipe
                original = {"id": 1, "ok": True, "result": {
                    "total": 156, "items": [
                        {"title": "Mo\u0308tley Cru\u0308e", "artist": "Mara Voss"},
                        {"title": "夜に駆ける", "artist": "Vera Static"},
                        {"title": "Gold ✨", "artist": "ResonaDeck"}
                    ]}}
                asyncio.run(bridge.send(original))
                ascii_unsafe_pipe.flush()
                self.assertEqual(json.loads(data.getvalue().decode("ascii")), original)
            finally:
                bridge.sys.stdout = old
                ascii_unsafe_pipe.detach()


if __name__ == "__main__":
    unittest.main()
