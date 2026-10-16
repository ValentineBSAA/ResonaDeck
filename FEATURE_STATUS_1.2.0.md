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
