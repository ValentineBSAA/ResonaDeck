#!/usr/bin/env python3
"""Validate the exact maintainer-built 1.4.1 beta ZIP; no external dependencies."""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

VERSION = "1.4.1"
FILENAME = "ResonaDeck-1.4.1.zip"
ROOT = "ResonaDeck/"
SHA256 = "f865f9a8dcc5c167b0e15eb785492428a135c313abdd1a2c491254acb051500d"
EXPECTED_FILES = 84

def main() -> None:
    archive = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(FILENAME)
    if not archive.is_file():
        raise SystemExit(f"Missing beta archive: {archive}")
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    assert actual == SHA256, f"Unexpected ZIP checksum: {actual}"
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None, "Damaged ZIP entry"
        names = z.namelist()
        assert len(names) == EXPECTED_FILES, f"Expected {EXPECTED_FILES} entries, got {len(names)}"
        assert all(n.startswith(ROOT) and not n.startswith("/") and ".." not in Path(n).parts for n in names)
        for n in ("plugin.json", "package.json", "dist/index.js", "main.py"):
            assert ROOT + n in names, f"Missing {n}"
        for n in ("plugin.json", "package.json"):
            manifest = json.loads(z.read(ROOT + n))
            assert manifest["version"] == VERSION, f"Wrong version in {n}"
        js = z.read(ROOT + "dist/index.js").decode("utf-8")
        assert VERSION in js, "Frontend version marker missing"
    print(f"PASS: {FILENAME} 1.4.1, checksum, CRC, paths, metadata and frontend marker")

if __name__ == "__main__":
    main()
