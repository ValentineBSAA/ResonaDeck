# ResonaDeck 1.5.7 | Source and release integrity

**Current stable:** [ResonaDeck 1.5.7](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.5.7), published November 6, 2026.  
**Installable ZIP:** [ResonaDeck-1.5.7.zip](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.5.7/ResonaDeck-1.5.7.zip) (**1,789,639 bytes**).  
**SHA-256:** `55f24398e5461cda6de732935a15fc11d9f47da550ba03b43aa4bac34975d03f`.

The hash matches **GitHub's published release-asset digest** and the locally packaged file. See [checksum manifest](RELEASE_ASSET_SHA256_1.5.7.txt).

## Release ZIP vs GitHub source tree

**The published 1.5.7 ZIP is the supported installer**, not GitHub's auto-generated Source code ZIP. The repository contains a compiled frontend snapshot and Python sources, but **main-branch runtime files currently correspond to an older release (1.5.1)**. Updating these documentation pages does not automatically synchronize `dist/index.js`, backend modules or plugin metadata to the 1.5.7 ZIP. Do not claim the default-branch files reproduce the newer published installer until a separate source-sync and parity verification is performed.

The repository does not provide a fully reproducible original React/TypeScript frontend project. Third-party Python components in the release ZIP may not be present in a GitHub source archive.

## Maintainer verification and limitations

The physical Steam Deck tests confirmed restored Quick Menu styling, expected visualizer visibility and a working frequency-reactive GTM link **after a manual OFF/ON refresh**. Audio priority with GTM Store Music also worked. The automatic visualizer audio-capture first-connection is not universally verified. The previous three-hour Plex track fix and precision crossfade counter were established in earlier 1.5.1 testing, preserved in 1.5.7.

[Release notes](RELEASE_NOTES_1.5.7.md) · [Hardware test record](FEATURE_STATUS_1.5.7.md) · [Support](SUPPORT.md) · [Changelog](CHANGELOG.md) · [License](LICENSE) · [Third-party notices](THIRD-PARTY-NOTICES.md)
