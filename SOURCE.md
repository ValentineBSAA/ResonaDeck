# ResonaDeck 1.4.1 • Source and integrity

**Next maintainer-tested beta:** 1.4.1. **Last published stable:** [1.2.1](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.2.1). The beta asset will be uploaded and published separately.

GitHub's main-branch installed runtime files were synchronized from the **exact ResonaDeck-1.4.1.zip**:
- [Compiled frontend](dist/index.js) and [matching JS source snapshot](src/index.js)
- [Decky entrypoint](main.py), [Plex backend](resonadeck_backend.py), [Jellyfin provider](jellyfin_provider.py), [Jellyfin discovery](jellyfin_discovery.py)
- [Package metadata](package.json), [Decky manifest](plugin.json) and [1.4.1 regression tests](tests/).

Selected Git blob hashes (verified against ZIP bytes):
- dist/index.js and src/index.js: `c93a2b09f53bdcede9cbf63ebff9d44366f2c085`
- resonadeck_backend.py: `2fbe984219179bccfff91888bfd714ab92d0c1a6`
- main.py: `2b8f7513aa47497b2ba1593435423b5649fddc4b`
- package.json: `5837312dd15ad9b1a7c0ec7eb8978c22dab4da05`
- plugin.json: `1bd319545bfcc7b19ebf48527c424f49a949c516`

**Installable ZIP SHA-256:** `f865f9a8dcc5c167b0e15eb785492428a135c313abdd1a2c491254acb051500d` (6,350,824 bytes).

Historical [1.2.1 release](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.2.1) remains available. GitHub's automatically generated “Source code” ZIP is **not** an installable Decky plugin. Download the named release asset after the maintainer uploads it.

The repository includes a compiled frontend snapshot, not the original fully reproducible TypeScript/React source project. License: [GPL-3.0-only](LICENSE) and third-party [notices](THIRD-PARTY-NOTICES.md).
