# ResonaDeck focused tests

These are deterministic development checks. They do not replace Steam Deck hardware testing.

- `verify-artwork-queue.cjs` — frontend artwork queue, retries, revision/cursor behavior and cache identity.
- `verify-artwork-worker.py` — backend hydration generation/status/cache-reuse behavior.
- `verify-music-artwork-activation.py` — 0.9.4 real Music candidate ordering and migration fixtures.
- `verify-targeted-qam.cjs` — controller spatial routing, Decky top-boundary handoff and targeted QAM regressions.
- `verify-mini-player.cjs` — mini-player component/layout checks. Set `RD_SKIP_BROWSER=1` when Playwright is unavailable.

## 0.9.7 targeted checks

- `verify-fallback-artwork-097.py` — terminal Plex 404 fallback classification, Music source-folder ghost detection, per-record revision preservation, and persisted fallback restore.
- `verify-fallback-assets-097.py` — validates the locked Music/Audiobook/Podcast fallback PNGs and 512px WebP runtime copies.
- `verify-fallback-ui-097.cjs` — verifies the approved runtime WebPs are embedded byte-for-byte, fallback state renders, mounted artwork polling is kicked by backend revision changes, retry query strings never corrupt `data:` assets, and `src/dist` stay identical.

## 0.9.12 targeted checks
- `verify-music-queue-coverflow-012.cjs`: Repeat Off/All/One, Play Next/Add Queue, persisted mode hooks, Up Next drawer/navigation hooks, persistent Shuffle glow, and directional two-cover transitions.
- Existing 0.9.6–0.9.11 regression tests remain required before packaging.

## 0.9.13 targeted checks
- `verify-qam-motion-active-013.cjs`: masked spatial cover handoff, coordinated copy/visualizer motion, living amber Shuffle radiance, Repeat active styling, reduced-motion protection, and no animation on mode toggles.


## 0.9.14 targeted checks
- `verify-qam-motion-active-013.cjs`: widened Cover Flow motion, theme-aware Shuffle tracer, reduced-motion protection, and no animation on mode toggles.


## 0.9.15 targeted checks
- `verify-shuffle-border-tracer-015.cjs`: true rounded-rectangle SVG border path, themed head/mid/tail dash motion, no conic spinner, no breathing aura, reduced-motion behavior, and preservation of the 0.9.14 strong Cover Flow.


## 0.9.16 targeted checks
- `verify-cover-rest-position-016.cjs`: verifies viewport-inset compensation, corrected resting artwork anchor, preserved large Cover Flow travel, and preserved 0.9.15 border tracer.

## 0.9.17 targeted checks
- `verify-repeat-boundary-shuffle-label-017.cjs`: visible themed Shuffle label, explicit Repeat OFF/ALL/ONE labels, no-wrap Repeat Off, Repeat All boundary wrapping, Repeat One natural-only repeat, and native audio loop disabled.


## 0.9.18 targeted checks
- `verify-shuffle-contrast-label-018.cjs`: explicit OFF/ON labels, forced readable foreground, neutral active button surface, contrast-corrected theme accent tracer, and retained Repeat/Cover Flow/cover-position repairs.


## 0.9.19 targeted checks
- `verify-qam-idle-cursor-019.cjs`: QAM-only idle pointer suppression, pointer reveal/re-arm hooks, cleanup, and preservation of Shuffle/Repeat/Cover Flow repairs.


## 0.9.20 targeted checks
- `verify-hardware-truth-repair-020.cjs`: Decky-native Shuffle OFF/ON label path, separate border tracer overlay, document-level transparent idle cursor suppression, and preservation of Repeat/Cover Flow/cover position.


## 0.9.21 targeted checks
- `verify-shuffle-cursor-021.cjs`: confirms the failed 0.9.21 sibling-label/cursor-parking approach stays retired while locked player behavior remains.


## 0.9.22 targeted checks
- `verify-native-shuffle-cursor-022.cjs`: direct native Shuffle button text, CSS rounded-perimeter motion tracer with fallback, Steam browser-native idle cursor hiding, and retirement of failed 0.9.21 wrapper/parking paths.

## 1.1.6 focused tests
- `node tests/verify-crossfade-v116.cjs`: two-player timing and independent pulse tests.
- `node tests/verify-next-peek-v116.cjs`: correct temporary album preview, no focus stealing.
- `node tests/verify-surprise-continuity-v116.cjs`: queue progression and persistent discovery.
These are synthetic tests, not proof of Steam Deck audio output. Older version-pinned tests in this directory may fail their version assertion on a newer build.

## 1.2.1 Direct Updater compatibility checks

- Run `python3 tests/verify-direct-updater-v121.py ResonaDeck-1.2.1-Stable.zip` to validate a complete download before publication.
- Checks archive paths and CRC, the single `ResonaDeck/` folder, required files, matching `1.2.1` version identifiers, and the canonical GitHub repository association.
- **Offline archive checks do not establish that an actual Decky Direct Updater installation succeeds on Steam Deck.**
