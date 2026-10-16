# ResonaDeck 1.2.0 feature verification

Evidence is split between hardware-confirmed behavior and implemented options that still merit testing.

## Confirmed on the creator's Steam Deck

- Surprise Me discovery plays and Keep Playing replenishes music.
- Favorites browsing, thematic settings, X/A open/close from cover artwork, and controller navigation.
- Native cover art and bundled full-square fallback art. Idle gold turntable and white backing retained.
- Manual dual-stream eight-second crossfade and **automatic eight-second crossfade** during normal playback in 1.1.9.
- Incoming vinyl → gold turntable → full-cover visual transition in the real player.

## Implemented, broader hardware testing still recommended

- Three-, five-, and ten-second fades; repeat/skip/stop during a fade; codec compatibility and adverse Plex network conditions.
- Saved sessions/local playlists and sleep timer across installation upgrades/restarts.
- Longer-term audiobook, podcast, and other-audio behavior with no speech overlap.
- Fine visual choreography on different Steam/CSS Loader themes.
- Confirm the final 1.2.0 ZIP version on a fresh/updated Steam Deck installation.

## Do not regress

The 1.1.9 dual-stream engine, Favorites, continuous queue timing, cover geometry, artwork fallback, A/X focus, 2x2 D-pad menu, and the original idle gold turntable.
