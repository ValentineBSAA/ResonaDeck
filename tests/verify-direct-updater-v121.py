#!/usr/bin/env python3
"""Offline validation for the ResonaDeck 1.2.1 install ZIP (not a hardware test)."""
import json
import stat
import sys
import zipfile
from pathlib import Path

EXPECTED = "ResonaDeck-1.2.1-Stable.zip"
REPO = "https://github.com/ValentineBSAA/ResonaDeck.git"


def check(path: Path):
    assert path.name == EXPECTED, "Unexpected release asset filename"
    with zipfile.ZipFile(path) as archive:
        items = archive.infolist()
        names = [item.filename for item in items]
        assert items and len(items) <= 30000
        assert len(names) == len({n.casefold() for n in names}), "Case-colliding ZIP paths"
        assert {n.split("/")[0] for n in names} == {"ResonaDeck"}, "Wrong root folder"
        assert sum(i.file_size for i in items) < 2 * 1024 ** 3
        for item in items:
            name = item.filename
            assert name and not name.startswith("/") and "\\" not in name
            assert all(p not in ("", ".", "..") and ":" not in p for p in name.rstrip("/").split("/"))
            assert not item.flag_bits & 1
            assert stat.S_IFMT(item.external_attr >> 16) in (0, stat.S_IFREG, stat.S_IFDIR)
        for file in ("plugin.json", "package.json", "dist/index.js", "main.py"):
            assert f"ResonaDeck/{file}" in names
        plugin = json.loads(archive.read("ResonaDeck/plugin.json"))
        package = json.loads(archive.read("ResonaDeck/package.json"))
        assert plugin["name"] == "ResonaDeck"
        assert package["name"] == "resonadeck"
        assert package["version"] == plugin["version"] == "1.2.1"
        assert package["repository"]["url"] == REPO
        assert package["homepage"] == "https://github.com/ValentineBSAA/ResonaDeck"
        assert package["bugs"]["url"] == "https://github.com/ValentineBSAA/ResonaDeck/issues"
        frontend = archive.read("ResonaDeck/dist/index.js")
        assert b"const RD_VERSION = '1.2.1';" in frontend
        assert frontend == archive.read("ResonaDeck/src/index.js")
        assert archive.getinfo("ResonaDeck/dist/index.js").file_size > 0
        assert archive.testzip() is None, "ZIP CRC failure"
    print("PASS: 1.2.1 ZIP metadata, structure, versions and integrity")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(f"Usage: {sys.argv[0]} {EXPECTED}")
    check(Path(sys.argv[1]))
