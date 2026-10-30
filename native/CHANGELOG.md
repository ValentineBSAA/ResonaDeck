# ResonaDeck Native for Windows 11

## 0.2.1 Development Preview (unverified)

### Windows creator-test regressions fixed in source
- Fix Unicode `charmap` failures for Plex album and artist titles containing combining diacritics by making the backend IPC stream locale-independent and ASCII-safe.
- Provide first-run Plex library classification, Music/Audiobook/Podcast/Other mapping, the ability to edit roles later, and selection of multiple Music sections.
- Stop representing a connected Plex account as proof of a loaded music catalog; show loaded counts, meaningful empty states and failures.
- Remove the extra expanded-player Windows chrome, reduce the oversized turntable, use the actual ResonaDeck emblem on the record, and replace unsupported transport glyphs with legible text.
- Add real Qt widget integration tests: 156 albums, Unicode metadata, Plex section selection, album track drill-down, native playback queue population.

### Security / verification status
- The portable executable remains unsigned. Windows Security may warn, and no virus-free claim is made. Do not disable Defender to test this build.
- Real-world Plex, audio decoder, crossfade, audiobooks, and device testing have not passed creator acceptance.
- This remains a draft PR; Steam Deck Stable 1.2.1 is unchanged.

## 0.2.0 Preview (superseded)
Initial PySide6 prototype. Failed real creator review: Plex library not browseable after authentication, Unicode stream error and inadequate desktop layout. Not suitable for release.
