# ResonaDeck 1.4.1 | Beta release notes

**Status:** [Published 1.4.1 beta](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.4.1), accepted on a physical Steam Deck. **1.2.1 remains the previous stable release.**

## What's new since 1.2.1

- **Keep Playing:** a rolling queue with early replenishment rather than a fixed 55-track endpoint; previously discovered tracks can bridge temporary Plex discovery failures. Ordinary playlists and timed sessions still end normally. Enabling Keep Playing during active music refreshes the queue immediately; selecting it while idle does not unexpectedly start playback.
- **Surprise Me preferences persist:** Keep Playing versus track-count/timed choices no longer silently fall back to 20 after a restart. Crossfade Off / 3 / 5 / 8 / 10 seconds is saved and restored separately from large discovery-state saves, and changes apply during playback.
- **Steam Deck sleep/wake recovery:** resume the same Plex track after an adjustable wake delay (5–60 seconds, default 12) if it was playing before sleep; do not auto-resume a manually paused track. Protect pending recovery from the orphan-player watchdog, and restore Web Audio output when necessary. **Automatic Plex playback after a full Steam Deck restart is not a verified feature.**
- **GTM visualizers:** opt-in audio telemetry to Game Theme Music 4.1.2, with an easily reached **GTM Visualizers** toggle directly below **Open Full ResonaDeck** in Quick Access. OFF clears the external visualization promptly without muting Plex; ON restores samples without restarting music.
- **Plex/Jellyfin provider picker:** premium dark account/server selection, controller focus and persistent preferences. Jellyfin compatibility varies by server/setup and is not claimed as comprehensively hardware-tested.
- **Existing player retained:** artwork-tinted controller-first Quick Menu, Full Manager, library browsing and search, gold turntable transitions, and prebuffered automatic crossfade (including the 8-second mode tested on Steam Deck).
- **Lean installer:** reduced unnecessary development/duplicate files compared with earlier packages; bundled Python dependencies. No package-specific external-binary download step.

## Verified on a real Steam Deck

The maintainer confirmed that **ResonaDeck resumes Plex music after actual sleep/wake**, and that **Keep Playing remained selected after a full restart**. Crossfade, audio-focus cooperation and the GTM visualizer toggle were accepted during the preceding beta fixes. This does **not** mean Plex automatically resumes after a full system restart.

## Testing and release guidance

Automated tests previously covered preference restart/restore, queue replenishment past track 130 including simulated lookup failures, manually paused sleep sessions, wake timers, eight-second crossfade, Web Audio output recovery and the GTM telemetry handshake. See [validation notes](FEATURE_STATUS_1.4.1.md).

Install the published **[ResonaDeck-1.4.1.zip](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.4.1/ResonaDeck-1.4.1.zip)** through Decky Loader. GitHub's generated source archive is not the plugin installer. Report issues through GitHub Issues; suggestions do not guarantee implementation.
