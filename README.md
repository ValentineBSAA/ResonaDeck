> **Release preparation:** ResonaDeck 1.4.9 is a tested candidate with a prepared Decky installer. See [1.4.9 release notes](RELEASE_NOTES_1.4.9.md) and [asset checksum](RELEASE_ASSET_SHA256_1.4.9.txt). Existing public releases remain unchanged **until the 1.4.9 runtime and ZIP asset are published**.

<div align="center">

# 🎧 ResonaDeck
### Premium Plex audio in Steam Deck Gaming Mode

**1.4.1 • Published, creator-tested beta**

[⬇ Download ResonaDeck 1.4.1](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.4.1/ResonaDeck-1.4.1.zip) · [Beta notes](RELEASE_NOTES_1.4.1.md) · [Hardware results](FEATURE_STATUS_1.4.1.md) · [Source integrity](SOURCE.md)

</div>

> **Release status:** [1.4.1 is published as a GitHub prerelease](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.4.1), with the exact checksum-verified ZIP. [1.2.1](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.2.1) remains the previous stable release. Install the **named asset ZIP**, not GitHub's automatic source archive.

Music · Audiobooks · Podcasts · More Audio · Plex, with Jellyfin integration included.

## Highlights

| Feature | Experience |
| --- | --- |
| **Controller-first Quick Access player** | Frosted artwork-colored player with album art, queues, favorites and Full ResonaDeck manager. |
| **Surprise Me + Keep Playing** | Endless music discovery with rolling queue replenishment, rather than stopping at a 55-track boundary. Temporary discovery failures can reuse known music. |
| **Persistent choices** | Keep Playing and Crossfade choices save independently, so the menu no longer falls back to 20 tracks on restart. |
| **Immediate queue refill** | Enabling Keep Playing during existing music playback requests more tracks right away; it does not start an idle player. |
| **Crossfade** | Off / 3 / 5 / **8** / 10-second options; the eight-second fade was verified during earlier Steam Deck development. |
| **Sleep & Wake recovery** | Optional auto-resume of a previously playing Plex track after wake, **12-second default delay**, adjustable 5–60 seconds. A manually paused track stays paused. |
| **GTM 4.1.2 visualizers** | Opt-in read-only music frequency bridge, track-change visualizer shuffle, plus an immediate ON/OFF switch directly below **Open Full ResonaDeck**. |
| **Premium provider selector** | Dark Plex/Jellyfin account and server selection; Web Audio fallback preserves output for reactive visualization. |

ResonaDeck and GTM coordinate audio ownership, so GTM Home Ambient should yield to Plex music.

## What the Steam Deck testing establishes
- **PASS:** ResonaDeck 1.4.1 resumes Plex music after sleep/wake, approximately following the configured delay.
- **PASS:** Surprise Me **Keep Playing remained selected after a full Steam Deck restart**.
- **PASS (earlier hardware acceptance):** Plex music, GTM visualizers, Quick Access visualizer ON/OFF and eight-second music crossfade worked.
- **Not claimed:** Automatic Plex playback after a full system restart. It is *not* required for 1.4.1.
- **Offline tested, not separately established by the final hardware report:** each Crossfade option surviving a reboot, every Jellyfin provider workflow, every possible queue/codec edge case.

Details: [1.4.1 hardware and regression status](FEATURE_STATUS_1.4.1.md).

## Installation & setup
Download **[ResonaDeck-1.4.1.zip](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.4.1/ResonaDeck-1.4.1.zip)** from the published release. Install through Decky Loader's manual ZIP installer. Keep existing settings. Sign in to Plex, choose your library, and open **Full ResonaDeck**.

- **Surprise Me:** choose **Keep Playing** and optionally an 8-second crossfade; choices should persist when reopened and after restart.
- **Sleep protection:** **Full ResonaDeck → Account/Profile → Settings → Sleep & Wake**; wake delay defaults to twelve seconds.
- **GTM sharing:** Quick Access → **GTM Visualizers** below **Open Full ResonaDeck**. OFF stops visualizer data without pausing Plex.
- **Up Next:** enabling Keep Playing during current music should immediately ask for more tracks.

[Full screenshot gallery](SCREENSHOTS.md) · [Support](SUPPORT.md) · [Changelog](CHANGELOG.md) · [1.4.1 release notes](RELEASE_NOTES_1.4.1.md)

This repository contains the installed compiled JavaScript bundle and Python sources, not an original fully reproducible frontend project. It does **not** include copyrighted media. Maintained by Valentine with real Steam Deck testing and maintainer-directed AI-assisted development.
