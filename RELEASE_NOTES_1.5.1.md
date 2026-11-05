# ResonaDeck 1.5.1 | Long-Track Crossfade Fix and Precision Countdown

**Stable release • November 5, 2026 • Developer: Valentine**

**Installable asset:** [ResonaDeck-1.5.1.zip](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.5.1/ResonaDeck-1.5.1.zip) · [SHA-256](RELEASE_ASSET_SHA256_1.5.1.txt)

ResonaDeck 1.5.1 is a focused stability update built on the 1.4.9 Plex/Jellyfin, Keep Playing and Game Theme Music integration release. It combines the long-duration playback fix proven in the private 1.5.0 test with a precise hours/minutes/seconds crossfade counter.

## Fixed: long tracks skipping or ending prematurely

An earlier crossfade path rejected track durations of two hours or more and guessed units based on numeric magnitude. A three-hour track, **10,800 seconds**, could be misinterpreted as **10.8 seconds**. Short browser media-segment information could also incorrectly suggest the track was at its end.

- Treat Plex seconds and explicitly labeled millisecond durations according to their actual units.
- Allow multi-hour track lengths in crossfade scheduling.
- Use the full track duration when the browser exposes only a short segment.
- If a long stream reports a premature end (such as 1.5 seconds into a three-hour track), attempt to recover **the same track** instead of silently advancing the queue.
- If recovery fails, surface an error rather than repeatedly skipping without explanation.

The maintainer confirmed successful playback of the previously failing three-hour recording on physical Steam Deck hardware.

## New: crossfade time remaining in hours, minutes and seconds

The crossfade countdown now retains the seconds component through every hour and minute:

| Actual time remaining | On-screen value |
| --- | --- |
| Three hours | `3h 00m 00s` |
| Two hours, 59 minutes, eight seconds | `2h 59m 08s` |
| One hour, one minute, one second | `1h 01m 01s` |
| Three minutes, eight seconds | `3m 08s` |
| Eight seconds | `8s` |

The formatter is shared by **Quick Access**, **Full Manager**, and crossfade timing diagnostics/history. Only the displayed time format changed in 1.5.1; the crossfade overlap setting remains **3, 5, 8 or 10 seconds**, plus Off.

## Preserved from 1.4.9

- Plex and Jellyfin authentication and premium source artwork.
- Keyboard-safe Full Manager Jellyfin sign-in and controller navigation.
- Surprise Me, Keep Playing and rolling music queue replenishment.
- Optional Game Theme Music (GTM 4.5.8) two-way visualizer ON/OFF integration.
- Sleep/wake playback handling and crossfade controls.
- Existing premium glass interface and media browsing features.

## Validation and limits

- Release ZIP size: **1,780,736 bytes**.
- SHA-256: `ab6b862a27ed6354fd7b4ad0a3d2e93934b22f18720c741d1bd7f06d090b4400`.
- The ZIP passed archive integrity, JavaScript syntax, and Python parsing checks. Key source files in Git are copied from this exact published ZIP.
- The maintainer confirmed the long-track fix and accepted 1.5.1 on physical hardware. This does **not** claim universal compatibility across every Plex stream, format or network environment.

## Install or update

Under this GitHub release's **Assets**, download **ResonaDeck-1.5.1.zip**. Install with Decky Loader's manual ZIP installation option. Do not install GitHub's automatically generated "Source code" ZIP; it is not the prepared Decky installer. Keep backups of settings before upgrading or downgrading.

Support and reproducible bug reports: [GitHub Issues](https://github.com/ValentineBSAA/ResonaDeck/issues).

Thank you for listening, testing and helping ResonaDeck improve. ❤️

**Developed and maintained by Valentine.**
