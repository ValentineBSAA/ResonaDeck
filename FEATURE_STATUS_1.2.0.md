# ResonaDeck 1.2.0 Stable — Feature Truth and Next Steps

Last updated: 2026-10-16. This document distinguishes hands-on Steam Deck evidence from source-level implementation and unverified permutations.

## Steam Deck confirmed by project owner

- [x] Surprise Me discovery launches playback.
- [x] Keep Playing replenishes music queues; queue history trimming no longer derails typical listening.
- [x] Favorites browser, themed selection states, and X/A settings open/close on artwork.
- [x] Native album art and full-square fallback artwork; existing idle gold turntable with white backing remains intact.
- [x] Manual crossfade successfully played two Plex streams at the same time.
- [x] **Natural automatic eight-second music crossfade** worked in 1.1.9 without clicking Test.
- [x] New incoming-record/turntable-to-cover artwork transition works on Deck, with minor remaining polish possibilities.

## Implemented and tested offline or only partially confirmed

- [ ] Listen through different 3-, 5-, and 10-second crossfade durations and verify actual audible overlap.
- [ ] Confirm repeated automatic fades across large mixed-format Plex music libraries.
- [ ] Confirm graceful crossfade recovery under network jitter, unavailable successor streams, pause, manual Next, Stop, and Repeat One.
- [ ] Confirm saved listening sessions, local playlists, sleep timer and resume across plugin restarts on current 1.2.0 package.
- [ ] Confirm longer-term stable behavior in Audiobooks, Podcasts and More Audio, including their intentional no-crossfade paths.
- [ ] Final visual tuning of record handoff timings, especially Steam themes or reduced motion.
- [ ] Independently install the exact renamed 1.2.0 stable ZIP and verify the displayed version.

## Important non-goals for the stable promotion

- Do not rewrite the dual-audio playback engine: the current eight-second automatic path is working on hardware.
- Do not change the A/X controller actions, Favorites, queue refill, artwork geometry, cover-flow animation, or protected idle turntable just for visual novelty.
- Do not treat offline tests as equivalent to real Steam Deck hearing tests.

## Next development candidates

Small bug-fix 1.2.1 after wider user testing; optional record-animation polish; compatibility checks against more Plex versions/codecs and CSS Loader themes; optional diagnostics export. No large new feature is required for this 1.2.0 milestone.

## Screenshot provenance and public documentation (2026-10-16)

- [x] Preserve nine original 1.0.0 GitHub-hosted image links for browsing, Full Manager, audiobooks and search, which have not been substantially redesigned.
- [x] Import four user-supplied 1.2.0 screenshots with descriptive names under `docs/screenshots/v1.2.0/`, sourced from the SHA-256 verified screenshot archive in the published GitHub release.
- [x] Separate new and retained imagery in `SCREENSHOTS.md`; link both galleries from the README.
- [x] Explain contextual X: Surprise Me turntable and active playback cover toggle discovery settings, while media tiles retain their existing actions.
- [x] Document the distinction between new 1.2.0 features and functionality retained from 1.0.0.
- [ ] Optional future screenshots: actual *in-motion* vinyl transition, additional settings further down the scrollable panel, and extended-time playback states. Not required for 1.2.0 Stable.

The older screenshots are intentionally preserved, not out-of-date claims that the entire 1.2.0 interface looks unchanged.
