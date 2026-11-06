# ResonaDeck 1.5.1 • Source and release integrity

**Current stable:** [ResonaDeck 1.5.1](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.5.1), published November 5, 2026.

**Installable ZIP:** [ResonaDeck-1.5.1.zip](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.5.1/ResonaDeck-1.5.1.zip) (1,780,736 bytes).

**SHA-256:** `ab6b862a27ed6354fd7b4ad0a3d2e93934b22f18720c741d1bd7f06d090b4400`.

The published ZIP's checksum was compared with the creator's tested 1.5.1 package. The repository runtime is synchronized from that **exact uploaded archive**: `dist/index.js`, a matching `src/index.js` compiled snapshot, `main.py`, `resonadeck_backend.py`, Jellyfin provider/discovery, `plugin.json`, `package.json`, and relevant artwork. Archive integrity, JavaScript syntax and Python parsing were checked.

This repository contains compiled frontend code, not a fully reproducible original React/TypeScript project. Bundled third-party Python components live in the published installer. To install via Decky Loader, use the specifically named **ResonaDeck-1.5.1.zip**, **not** GitHub's automatic "Source code" archive.

## Tested scope and remaining limitations

- The previously failing three-hour audio track now plays correctly on a physical Steam Deck. The maintainer accepted 1.5.1 after verifying the new countdown behavior.
- Multi-hour duration handling and crossfade display changes received targeted checks. This does not guarantee every Plex codec or stream will be interruption-free.
- GTM 4.5.8 visualizer integration, Keep Playing, and Jellyfin input fixes are preserved.
- The former stable [1.4.9 release](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.4.9), [1.4.1 beta](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.4.1) and historical releases remain available and unchanged.

[1.5.1 release notes](RELEASE_NOTES_1.5.1.md) · [Changelog](CHANGELOG.md) · [Checksum manifest](RELEASE_ASSET_SHA256_1.5.1.txt) · [Support](SUPPORT.md).

License: [GPL-3.0-only](LICENSE). Third-party license acknowledgments: [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
