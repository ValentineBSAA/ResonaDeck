# ResonaDeck 1.5.7 | Hardware and release verification

**Published stable:** [ResonaDeck 1.5.7](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.5.7) · November 6, 2026 · Maintainer: Valentine.

## Published asset and package checks

| Item | Observation |
| --- | --- |
| Installer | **ResonaDeck-1.5.7.zip** (1,789,639 bytes) |
| SHA-256 | `55f24398e5461cda6de732935a15fc11d9f47da550ba03b43aa4bac34975d03f` |
| GitHub release asset digest | **Matches local SHA-256** |
| JavaScript syntax, Python parsing, ZIP integrity | **PASS** during build preparation |
| Every provider, SteamOS/Decky version, CSS theme | **Not universally verified** |

## Maintainer's Steam Deck tests

| Check | Result |
| --- | --- |
| Quick Access artwork, controls and styling after restoring correct CSS scope | **PASS** |
| Player controls and music continue working after Quick Menu corrections | **PASS** in maintainer observations |
| Enabled visualizers stay hidden when no eligible music plays | **PASS** |
| Visualizers can appear with music playback | **PASS** |
| Music-frequency response to ResonaDeck audio in GTM | **PASS after toggling GTM Visualizers OFF/ON in ResonaDeck** |
| Automatic first-time capture handshake after every hot update/reboot | **Not established as universally reliable** |
| GTM Store Music respects ongoing ResonaDeck playback | **PASS** |
| Cash App button/icon/link removed from 1.5.7 ZIP | **Confirmed in package preparation** |
| Three-hour Plex track duration handling, precision crossfade countdown | **Maintainer-confirmed on 1.5.1 hardware**, preserved in later builds; not a new exhaustive 1.5.7 codec test |

## The distinction between visualizer visibility and music reactivity

A visualizer appearing when music starts only establishes that the playback signal is recognized. True music-reactive behavior additionally requires frequency/PCM delivery. The maintainer initially reported visualizers appearing without reacting, then confirmed they responded after switching **GTM Visualizers OFF then ON** in ResonaDeck. This is a successful manual recovery observation, **not** proof that the first handshake always succeeds on every Deck restart.

Diagnostics (when available): **Full ResonaDeck → Settings → GTM Visualizers · Live Control**. Check Live PCM, audio context state, analyzer RMS, packet counts and GTM acknowledgments; values may retain historical readings after the link is disabled.

## Earlier verification

See [1.5.1 long-track acceptance](FEATURE_STATUS_1.5.1.md) and [1.4.1 hardware acceptance](FEATURE_STATUS_1.4.1.md) for prior features. They remain historical observations, not a claim to have rerun every test in 1.5.7.

[Release notes](RELEASE_NOTES_1.5.7.md) · [Support](SUPPORT.md) · [SHA-256](RELEASE_ASSET_SHA256_1.5.7.txt) · [Source and packaging](SOURCE.md)
