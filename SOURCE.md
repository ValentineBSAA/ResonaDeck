# Source Code & Release Integrity

**Current stable release:** [ResonaDeck 1.2.1](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.2.1). The published release's SHA-256 matches the package built for this maintenance update.

## Official download and checksum

- [ResonaDeck-1.2.1-Stable.zip](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.2.1/ResonaDeck-1.2.1-Stable.zip)
- **SHA-256:** `165fbfe15e21d01ae6cf9ac7042d3efad8cb100bb89e1fc2cf18cc6fe71a4493`
- **Layout:** one `ResonaDeck/` folder with `plugin.json`, `package.json`, `dist/index.js`, `main.py` and other runtime assets.

You can verify a downloaded file with `sha256sum ResonaDeck-1.2.1-Stable.zip` or a graphical checksum checker.

## Source and compatibility

- [Frontend](src/index.js) / [installed compiled bundle](dist/index.js)
- [Plex backend](resonadeck_backend.py) / [Decky entrypoint](main.py)
- [Package and GitHub source metadata](package.json) / [Decky manifest](plugin.json)
- [Tests](tests/) / [artwork assets](assets/) / [third-party notices](THIRD-PARTY-NOTICES.md)
- [1.2.1 release notes](RELEASE_NOTES_1.2.1.md) / [verification status](FEATURE_STATUS_1.2.1.md)

The 1.2.1 ZIP introduces canonical GitHub repository metadata and synchronized version identifiers. The only compiled frontend change is its displayed version; the Plex backend and existing audio, animation, and controller logic are unchanged.

## Historical 1.2.0 evidence

The previous [1.2.0 Stable release notes](RELEASE_NOTES_1.2.0.md) had SHA-256 `66148bf5e02114282c964bf46f2d6f0f89934d6184e6eecd2ea8a4ac8d8b21f2`. Its [hardware test record](FEATURE_STATUS_1.2.0.md) confirms automatic eight-second crossfade, Surprise Me, Keep Playing, Favorites and the vinyl handoff on Steam Deck. The earlier source-import process remains recorded in Git history.

**Still unverified:** a real 1.2.0 → 1.2.1 update through Decky Direct Updater and persistence of settings after that update.
