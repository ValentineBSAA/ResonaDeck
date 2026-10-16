# Source Code & Release Integrity

**ResonaDeck 1.2.0 Stable is publicly released, with its runtime source synchronized to this repository from the exact published ZIP.**

## Download the verified stable release

- **[ResonaDeck 1.2.0 Stable release](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.2.0)**
- **[ResonaDeck-1.2.0-Stable.zip](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.2.0/ResonaDeck-1.2.0-Stable.zip)**
- **SHA-256:** `66148bf5e02114282c964bf46f2d6f0f89934d6184e6eecd2ea8a4ac8d8b21f2`

The release ZIP contains a top-level `ResonaDeck/` plugin directory. Install this ZIP directly using Decky Loader.

## Browse the public implementation

- [Frontend source](src/index.js) and [installable compiled frontend](dist/index.js) are **byte-identical** in the verified stable ZIP.
- [Plex backend](resonadeck_backend.py) and [Decky entrypoint](main.py).
- [Manifest](plugin.json), [package dependencies](package.json) and [asset pack](assets/).
- [Tests](tests/), [mutagen metadata parser](mutagen/) and [third-party notices](THIRD-PARTY-NOTICES.md).
- [Changelog](CHANGELOG.md), [release notes](RELEASE_NOTES_1.2.0.md) and [feature verification](FEATURE_STATUS_1.2.0.md).

The checked-in source was imported via [the checksum-verifying GitHub Actions workflow](.github/workflows/import-v1-2-source.yml), which downloads the previously published archive, verifies its SHA-256, checks frontend parity and manifest versions, and copies files without recompiling the working audio engine.

## Reproducible integrity checks

```bash
sha256sum ResonaDeck-1.2.0-Stable.zip
```

Expected value: `66148bf5e02114282c964bf46f2d6f0f89934d6184e6eecd2ea8a4ac8d8b21f2`.

## Hardware verification

The project owner confirmed the **automatic eight-second crossfade**, native/fallback cover art, timed record-to-cover handoff, Surprise Me playback, Favorites browser, controller X toggles, and Keep Playing on Steam Deck. Other fade durations and edge cases need broader verification.

Older [ResonaDeck 1.0.0](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.0.0) remains available for historical reference.
