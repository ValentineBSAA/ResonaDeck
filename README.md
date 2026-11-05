<div align="center">

# 🎧 ResonaDeck
### Premium Plex & Jellyfin audio in Steam Deck Gaming Mode

**1.4.9 • Stable release • Physically tested on Steam Deck**

[⬇ Download ResonaDeck 1.4.9](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.4.9/ResonaDeck-1.4.9.zip) · [Release notes](RELEASE_NOTES_1.4.9.md) · [Previous hardware results](FEATURE_STATUS_1.4.1.md) · [Source integrity](SOURCE.md)

</div>

> **Release status:** [1.4.9 is the current stable GitHub release](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.4.9). [1.4.1](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.4.1) is an earlier beta. Install the **named 1.4.9 ZIP asset**, not GitHub's automatic source archive.

Music · Audiobooks · Podcasts · More Audio · Plex, with Jellyfin integration included.

## Highlights

| Feature | Experience |
| --- | --- |
| **Controller-first Quick Access player** | Frosted artwork-colored player with album art, queues, favorites and Full ResonaDeck manager. |
| **Surprise Me + Keep Playing** | Endless music discovery with rolling queue replenishment, including when selecting a single music track, rather than stopping at a 55-track boundary. Temporary discovery failures can reuse known music. |
| **Persistent choices** | Keep Playing and Crossfade choices save independently, so the menu no longer falls back to 20 tracks on restart. |
| **Immediate queue refill** | Enabling Keep Playing during existing music playback requests more tracks right away; it does not start an idle player. |
| **Crossfade** | Off / 3 / 5 / **8** / 10-second options; the eight-second fade was verified during earlier Steam Deck development. |
| **Sleep & Wake recovery** | Optional auto-resume of a previously playing Plex track after wake, **12-second default delay**, adjustable 5–60 seconds. A manually paused track stays paused. |
| **GTM 4.5.8 visualizers** | Music-frequency bridge and **bidirectional live visualizer ON/OFF state** with compatible GTM versions; either plugin can change the live state. |
| **Premium provider selector** | Premium Plex/Jellyfin source artwork and source-switching; Jellyfin sign-in uses the keyboard-safe Full Manager editor. |

ResonaDeck and GTM coordinate audio ownership, so GTM Home Ambient should yield to Plex music.

## What Steam Deck testing establishes (including earlier 1.4.1 results)
- **PASS (1.4.1 hardware):** ResonaDeck resumes Plex music after sleep/wake, approximately following the configured delay.
- **PASS:** Surprise Me **Keep Playing remained selected after a full Steam Deck restart**.
- **PASS (earlier hardware acceptance):** Plex music, GTM visualizers, Quick Access visualizer ON/OFF and eight-second music crossfade worked.
- **Not claimed:** Automatic Plex playback after a full system restart. It is *not* required for 1.4.1.
- **Offline tested, not separately established by the final hardware report:** each Crossfade option surviving a reboot, every Jellyfin provider workflow, every possible queue/codec edge case.

- **PASS (1.4.9 hardware):** Jellyfin Full Manager credential fields remain visible with Steam's native keyboard; the controller can move between fields and return to the form.
- **PASS (4.5.8 integration):** GTM and ResonaDeck can both control the live visualizer ON/OFF state.
- **Diagnostic-only:** Plex buffering interruptions can be recorded; they are not claimed to be universally fixed.

Details: [1.4.9 release notes](RELEASE_NOTES_1.4.9.md) and [historical 1.4.1 testing](FEATURE_STATUS_1.4.1.md).

## What's new in 1.4.9

- Premium Plex/Jellyfin source icons and glass-style Account controls.
- Controller-friendly Jellyfin sign-in through Full Manager, with the active input visible above Steam's native keyboard.
- Quick Access sign-in notice routes to Full Manager, and the Nothing Playing footer is hidden during sign-in.
- Single-track Keep Playing queue continuation and synchronized GTM visualizer controls.

[Read the complete 1.4.9 changelog](CHANGELOG.md) · [Release checksum](RELEASE_ASSET_SHA256_1.4.9.txt)

## Installation & setup
Download **[ResonaDeck-1.4.9.zip](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.4.9/ResonaDeck-1.4.9.zip)** from the published release. Install through Decky Loader's manual ZIP installer. Keep existing settings. Sign in to Plex, choose your library, and open **Full ResonaDeck**.

- **Surprise Me:** choose **Keep Playing** and optionally an 8-second crossfade; choices should persist when reopened and after restart.
- **Sleep protection:** **Full ResonaDeck → Account/Profile → Settings → Sleep & Wake**; wake delay defaults to twelve seconds.
- **GTM sharing:** Quick Access → **GTM Visualizers** in the music controls (when compatible GTM is installed). OFF stops visualizer data without pausing Plex.
- **Up Next:** enabling Keep Playing during current music should immediately ask for more tracks.

[Full screenshot gallery](SCREENSHOTS.md) · [Support](SUPPORT.md) · [Changelog](CHANGELOG.md) · [1.4.9 release notes](RELEASE_NOTES_1.4.9.md)

This repository contains the installed compiled JavaScript bundle and Python sources, not an original fully reproducible frontend project. It does **not** include copyrighted media. Maintained by Valentine with real Steam Deck testing and maintainer-directed AI-assisted development.
