<div align="center">

# 🎧 ResonaDeck
### Your Plex audio library, right where you play.

**Premium, controller-first Plex audio for Steam Deck.**  
Music · Audiobooks · Podcasts · More Audio

[![Release](https://img.shields.io/badge/Download-ResonaDeck%201.2.0-2554a2?style=for-the-badge&logo=github)](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.2.0/ResonaDeck-1.2.0-Stable.zip)
[![Platform](https://img.shields.io/badge/Steam%20Deck-Decky%20Loader-183b59?style=for-the-badge)](https://github.com/SteamDeckHomebrew/decky-loader)

<a href="https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.2.0"><img src="https://github.com/user-attachments/assets/304629b8-1b41-4ac8-b820-10b6e9f3e7a0" width="820" alt="ResonaDeck Quick Menu player with cover-art-tinted glass controls"></a>

*Artwork-colored playback controls, directly in your Quick Access Menu.*

**[Download v1.2.0](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.2.0) · [View all screenshots](SCREENSHOTS.md) · [Share feedback](https://github.com/ValentineBSAA/ResonaDeck/discussions/3) · [Report a problem](https://github.com/ValentineBSAA/ResonaDeck/issues)**

</div>

---

## 🎵 What is ResonaDeck?

**ResonaDeck** is a Decky Loader plugin that brings **your own Plex audio libraries** into Steam Deck's **Quick Access Menu** and a larger **Full Manager**. Browse covers, play music while gaming, pick up an audiobook, or manage a queue without switching to a separate music application.

It's designed around the Steam Deck controller, with colorful frosted-glass controls that follow the artwork you're listening to.

## ✨ Highlights

| | |
| :--- | :--- |
| **Surprise Me discovery** | Generate themed listening sessions across Plex music and other audio libraries, with Favorites-only options. |
| **Keep Playing** | Automatic music queue refill, repeat protection, and optional 30-minute, 1-hour, or 2-hour listening sessions. |
| **Automatic music crossfade** | Dual-stream overlap with Off, 3, 5, 8, and 10-second choices. Automatic **8-second fades are Steam Deck-confirmed**. |
| **Vinyl record transition** | Incoming record arrives beside the cover, transitions through the gold turntable, and expands into full-square album art. |
| **Favorites and listening tools** | Favorites browser, saved sessions, local playlists, sleep timer, and artwork prefetch/fallbacks. |
| **Live XFADE feedback** | Countdown, preparation, fade progress, completion, and error/blocker states. |
| **Quick Menu player** | Play and control your audio while using Steam and games. |
| **Artwork-colored glass** | Player buttons, queue, and visual accents adapt to the current cover art. |
| **Four library identities** | Music in blue-violet, Audiobooks in slate/copper, Podcasts in teal, and More Audio in plum. |
| **Full ResonaDeck** | Home shelves, Music, Audiobooks, Podcasts, More Audio, Search, and library management. |
| **Queue that works with a controller** | Add to Queue, Play Next, total track count, queue drawer, and remove actions. |
| **Long-form listening** | Audiobook chapters, resume, podcast browsing, and relevant playback controls. |
| **Designed for Steam themes** | Glass control layers that resist white-background CSS Loader overrides. |

## 🎧 What's new in 1.2.0 Stable

ResonaDeck 1.2.0 is the promotion of the **1.1.9 hardware-tested build**, bringing discovery and proper music transitions together without replacing the working player architecture. The creator confirmed **automatic eight-second crossfades** and the incoming-vinyl-to-album-cover sequence on a real Steam Deck.

The crossfade status shows when the next stream is preparing, when a fade is expected, and when both tracks are actually playing. Music can continue through automatically replenished queues. The gold idle turntable, its white backing, focus navigation, and artwork-reactive glass remain intact.

**[Read 1.2.0 release notes](RELEASE_NOTES_1.2.0.md) · [Feature verification checklist](FEATURE_STATUS_1.2.0.md)**

## 📸 See ResonaDeck in action

### New in 1.2.0 · Surprise Me and active playback

<table>
<tr>
<td align="center" width="50%"><a href="docs/screenshots/v1.2.0/03-surprise-me-turntable.jpg"><img src="docs/screenshots/v1.2.0/03-surprise-me-turntable.jpg" width="100%" alt="Gold Surprise Me turntable and ready-to-listen screen"></a><br><b>Surprise Me</b><br><sub>Choose the gold record. A starts listening; X opens or closes settings.</sub></td>
<td align="center" width="50%"><a href="docs/screenshots/v1.2.0/04-surprise-me-settings.jpg"><img src="docs/screenshots/v1.2.0/04-surprise-me-settings.jpg" width="100%" alt="ResonaDeck 1.2.0 Surprise Me Settings"></a><br><b>Surprise Me Settings</b><br><sub>Choose discovery mode, favorites, session length, and music crossfade.</sub></td>
</tr>
<tr>
<td align="center" width="50%"><a href="docs/screenshots/v1.2.0/01-player-crossfade-status.jpg"><img src="docs/screenshots/v1.2.0/01-player-crossfade-status.jpg" width="100%" alt="Now Playing screen with XFADE status"></a><br><b>Now Playing + XFADE</b><br><sub>Live crossfade countdown and queue controls in the Quick Menu.</sub></td>
<td align="center" width="50%"><a href="docs/screenshots/v1.2.0/02-music-albums.jpg"><img src="docs/screenshots/v1.2.0/02-music-albums.jpg" width="100%" alt="Music Albums browser in ResonaDeck 1.2.0"></a><br><b>Music albums</b><br><sub>Still familiar: album browsing keeps its controller-first layout.</sub></td>
</tr>
</table>

<div align="center">

**[Explore all 13 screenshots: 1.2.0 new features + 1.0.0 preserved interface →](SCREENSHOTS.md)**

<sub>The nine original screenshots remain intentionally in the gallery. Most library browsing, Full Manager, audiobook and search screens have not undergone major redesigns; the 1.2.0 changes primarily expand listening and playback.</sub>

</div>

## 🚀 Install

1. Install **[Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader)** on your Steam Deck.
2. **[Download ResonaDeck-1.2.0-Stable.zip](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.2.0/ResonaDeck-1.2.0-Stable.zip)** from the official GitHub release.
3. Open Decky Loader → **Settings → Developer → Install Plugin ZIP**.
4. Select the ZIP, open ResonaDeck from the Quick Access Menu, and sign in to your Plex account.
5. Select a reachable Plex server and the audio libraries you want to browse.

> **Requires:** Steam Deck, Decky Loader, and access to a Plex Media Server containing your audio. ResonaDeck supplies no media content.

## 🎲 Surprise Me · Quick start

1. Open ResonaDeck in the Steam Deck Quick Access Menu and locate the **gold Surprise Me turntable**.
2. Focus the turntable. Press **X** for **Surprise Me Settings**, choosing your category, music mode (**Tracks, Albums, Rediscover**), and Favorites-only preference.
3. Choose a track count or a timed session (**30 minutes, 1 hour or 2 hours**); select **Keep Playing** for continuously replenished music.
4. For music, choose a **crossfade** setting (Off, 3, 5, 8 or 10 seconds). The automatic **8-second overlap** was tested on a real Steam Deck.
5. Press **A** on Surprise Me to start listening. Once music starts, focus the **playing album cover** and press **X** to reopen or close the same settings without stopping the music.

**X depends on what is focused.** On ordinary Albums / Artists / Tracks it still opens the familiar media actions menu, including **Add to Queue**, **Play Next**, and **Browse Details**. The new Surprise Me behavior does not replace those older controls.

## 🔄 What Changed Between 1.0.0 and 1.2.0?

| Introduced or substantially expanded in 1.2.0 | Kept from the established 1.0.0 experience |
| :--- | :--- |
| Surprise Me discovery, selectable gold turntable, themed settings | Music/Books/Podcasts/More categories and controller-first library browsing |
| Tracks, Albums, Rediscover, Favorites-only discovery | Album art cards, queues, search and the Full Manager |
| Keep Playing, refill-before-end, timed sessions, Favorites browser | Standard media actions: X → Add to Queue, Play Next, Browse Details |
| Automatic music crossfade, XFADE countdown and diagnostic status | Artwork-reactive glass, library colors, and existing playback buttons |
| Incoming vinyl → gold turntable → full-cover animated transition | Audiobook chapters/resume and podcast library navigation |
| Refined artwork loading/fallback, personal listening tools | The original idle gold turntable and white backing |

**Why older screenshots remain:** these longstanding screens still represent current functionality. We photographed the four new 1.2.0 views where the features visibly changed, rather than replacing accurate screenshots just to change their version label. [See the two release galleries](SCREENSHOTS.md).

## 🎮 Controller guide

| Button | Action |
| :--- | :--- |
| **A** | Play or resume |
| **Hold A** | Preview supported media |
| **X** | On Surprise Me turntable / active cover: open or close discovery settings. On a library item: open its normal media actions. |
| **D-pad ← / →** | Move across action menu columns |
| **D-pad ↑ / ↓** | Move between action menu rows |
| **B** | Back / close the menu or queue |
| **LB / RB** | Switch Full Manager sections |

**Where is search?** Search lives in **Full ResonaDeck**. Quick Menu search was intentionally removed to keep controller navigation smooth.

## 🔊 Two listening experiences

**Quick Access Menu:** Compact playback with artwork-reactive glass, an animated Shuffle highlight, the track queue, volume, and album/artist navigation.

**Full Manager:** A more spacious Plex audio library with shelves, artwork, track details, search, audiobook chapters, player settings, and library tools.

## 🧩 Open source

Browse the **[frontend source](src/index.js)**, **[Python Plex backend](resonadeck_backend.py)**, **[tests](tests/)**, and **[assets](assets/)** directly in this repository. The runtime source has been synchronized from the checksum-verified 1.2.0 Stable ZIP; see **[Source & Integrity](SOURCE.md)** for the checksum and tag details.

## ℹ️ About 1.2.0 Stable

**1.2.0 preserves the working 1.1.9 crossfade, discovery, and controller implementation.** The automatic eight-second crossfade and record handoff were confirmed in the creator's Steam Deck testing. Other fade durations, formats, network edge cases, and alternative themes may need additional compatibility testing. Playback speed depends partly on Plex server availability, network conditions, and server transcoding. Steam and Decky updates may affect controller or theme behavior.

## 💬 Share your experience or report a problem

**Already installed ResonaDeck 1.2.0? We'd love to hear how it went.** Whether Surprise Me picked the right songs, crossfade worked on your Plex setup, or you just want to say hello, you can leave a note in the **[1.2.0 release discussion](https://github.com/ValentineBSAA/ResonaDeck/discussions/3)**. Short impressions and questions are welcome. You don't need to write a full bug report.

If something actually breaks, use **[GitHub Issues](https://github.com/ValentineBSAA/ResonaDeck/issues)** so it's easier to reproduce and track. Include SteamOS, Decky, and Plex server details where helpful, but **never post Plex tokens, passwords, or private server links**.



**[Official release page](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.2.0)** · **[Full screenshot gallery](SCREENSHOTS.md)** · **[1.2.0 Release Notes](RELEASE_NOTES_1.2.0.md)** · **[Support](SUPPORT.md)** · **[Source & Integrity](SOURCE.md)** · **[Credits and Third-Party Notices](THIRD-PARTY-NOTICES.md)**

---

<div align="center">

Created by **Valentine** · **[GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.en.html)**

*Independent project, not affiliated with Plex, Valve, Steam, or Decky Loader.*

</div>
