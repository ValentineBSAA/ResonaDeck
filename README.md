<div align="center">

# 🎧 ResonaDeck
### Premium Plex & Jellyfin audio in Steam Deck Gaming Mode

**1.5.1 • Stable release • Physically tested on Steam Deck**

[⬇ Download ResonaDeck 1.5.1](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.5.1/ResonaDeck-1.5.1.zip) · [Release notes](RELEASE_NOTES_1.5.1.md) · [Previous hardware results](FEATURE_STATUS_1.4.1.md) · [Source integrity](SOURCE.md)

</div>

> **Release status:** [1.5.1 is the current stable GitHub release](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.5.1). [1.4.9](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.4.9) is the previous stable release. Install the **named 1.5.1 ZIP asset**, not GitHub's automatic source archive.

Music · Audiobooks · Podcasts · More Audio · Plex, with Jellyfin integration included.

## Highlights

| Feature | Experience |
| --- | --- |
| **Controller-first Quick Access player** | Frosted artwork-colored player with album art, queues, favorites and Full ResonaDeck manager. |
| **Surprise Me + Keep Playing** | Endless music discovery with rolling queue replenishment, including when selecting a single music track, rather than stopping at a 55-track boundary. Temporary discovery failures can reuse known music. |
| **Persistent choices** | Keep Playing and Crossfade choices save independently, so the menu no longer falls back to 20 tracks on restart. |
| **Immediate queue refill** | Enabling Keep Playing during existing music playback requests more tracks right away; it does not start an idle player. |
| **Crossfade and long tracks** | Off / 3 / 5 / **8** / 10-second fade settings; corrected multi-hour timing and a live countdown with hours, minutes and seconds (`2h 59m 08s`). |
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

Details: [1.5.1 release notes](RELEASE_NOTES_1.5.1.md) and [historical 1.4.1 testing](FEATURE_STATUS_1.4.1.md).

## What's new in 1.5.1

- **Multi-hour audio reliability:** Plex duration values now use explicit seconds or milliseconds, rather than guessing from their magnitude. The two-hour crossfade cutoff is gone.
- **Premature-end protection:** if a lengthy stream stops unexpectedly near the beginning, ResonaDeck tries to recover the same track rather than silently skipping it.
- **Precise crossfade countdown:** Quick Access, Full Manager and timing diagnostics show `3h 00m 00s`, `2h 59m 08s`, `3m 08s` or `8s`, as appropriate.
- **Hardware verification:** the maintainer confirmed three-hour playback and the 1.5.1 experience on a physical Steam Deck.
- **Everything else preserved:** Plex/Jellyfin sign-in, Keep Playing, crossfade overlap selection and Game Theme Music 4.5.8 visualizer synchronization.

[Complete 1.5.1 release notes](RELEASE_NOTES_1.5.1.md) · [Changelog](CHANGELOG.md) · [ZIP SHA-256](RELEASE_ASSET_SHA256_1.5.1.txt)

## Installation & setup
Download **[ResonaDeck-1.5.1.zip](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.5.1/ResonaDeck-1.5.1.zip)** from the published release. Install through Decky Loader's manual ZIP installer. Keep existing settings. Sign in to Plex, choose your library, and open **Full ResonaDeck**.

- **Surprise Me:** choose **Keep Playing** and optionally an 8-second crossfade; choices should persist when reopened and after restart.
- **Sleep protection:** **Full ResonaDeck → Account/Profile → Settings → Sleep & Wake**; wake delay defaults to twelve seconds.
- **GTM sharing:** Quick Access → **GTM Visualizers** in the music controls (when compatible GTM is installed). OFF stops visualizer data without pausing Plex.
- **Up Next:** enabling Keep Playing during current music should immediately ask for more tracks.

[Full screenshot gallery](SCREENSHOTS.md) · [Support](SUPPORT.md) · [Changelog](CHANGELOG.md) · [1.5.1 release notes](RELEASE_NOTES_1.5.1.md)

## ❤️ A little note from me

I originally made ResonaDeck because I wanted a proper way to listen to my Plex music on the Steam Deck. I kept noticing little things I wanted to fix or improve, and somehow that small idea turned into a whole music player with Jellyfin, crossfade, discovery, and a lot more. I've genuinely enjoyed making it.

If ResonaDeck is something you enjoy using, and you'd like to help me keep working on it, I've added an optional Cash App donation link below. **Please don't feel like you have to donate.** ResonaDeck stays free, with no locked features or special treatment for donations. Downloading it, telling somebody about it, or helping me find a bug already means a lot.

I'm just one developer who keeps finding things I want to make better. Thank you for giving ResonaDeck a place on your Steam Deck. ❤️

<p align="center">
  <a href="https://cash.app/$jilvalentinebsaa" title="Optional Cash App donation to support ResonaDeck development"><img src="assets/donate-support.webp" alt="Green Donate and Support badge for Valentine's Cash App" width="150"></a>
  <br>
  <strong><a href="https://cash.app/$jilvalentinebsaa">Support my development on Cash App · $jilvalentinebsaa</a></strong>
  <br>
  <sub>Always optional. The music stays free. ❤️</sub>
</p>

This repository contains the installed compiled JavaScript bundle and Python sources, not an original fully reproducible frontend project. It does **not** include copyrighted media. Maintained by Valentine with real Steam Deck testing and maintainer-directed AI-assisted development.
