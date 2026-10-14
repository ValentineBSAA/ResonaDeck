<div align="center">

# 🎧 ResonaDeck
### Your Plex audio library, right where you play.

**Premium, controller-first Plex audio for Steam Deck.**  
Music · Audiobooks · Podcasts · More Audio

[![Release](https://img.shields.io/badge/Download-ResonaDeck%201.0.0-2554a2?style=for-the-badge&logo=github)](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.0.0/ResonaDeck-1.0.0.zip)
[![Platform](https://img.shields.io/badge/Steam%20Deck-Decky%20Loader-183b59?style=for-the-badge)](https://github.com/SteamDeckHomebrew/decky-loader)

<a href="https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.0.0"><img src="https://github.com/user-attachments/assets/304629b8-1b41-4ac8-b820-10b6e9f3e7a0" width="820" alt="ResonaDeck Quick Menu player with cover-art-tinted glass controls"></a>

*Artwork-colored playback controls, directly in your Quick Access Menu.*

**[Download v1.0.0](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.0.0) · [View all screenshots](SCREENSHOTS.md) · [Report a problem](https://github.com/ValentineBSAA/ResonaDeck/issues)**

</div>

---

## 🎵 What is ResonaDeck?

**ResonaDeck** is a Decky Loader plugin that brings **your own Plex audio libraries** into Steam Deck's **Quick Access Menu** and a larger **Full Manager**. Browse covers, play music while gaming, pick up an audiobook, or manage a queue without switching to a separate music application.

It's designed around the Steam Deck controller, with colorful frosted-glass controls that follow the artwork you're listening to.

## ✨ Highlights

| | |
| :--- | :--- |
| **Quick Menu player** | Play and control your audio while using Steam and games. |
| **Artwork-colored glass** | Player buttons, queue, and visual accents adapt to the current cover art. |
| **Four library identities** | Music in blue-violet, Audiobooks in slate/copper, Podcasts in teal, and More Audio in plum. |
| **Full ResonaDeck** | Home shelves, Music, Audiobooks, Podcasts, More Audio, Search, and library management. |
| **Queue that works with a controller** | Add to Queue, Play Next, total track count, queue drawer, and remove actions. |
| **Long-form listening** | Audiobook chapters, resume, podcast browsing, and relevant playback controls. |
| **Designed for Steam themes** | Glass control layers that resist white-background CSS Loader overrides. |

## 📸 See ResonaDeck in action

<table>
<tr>
<td align="center" width="50%"><a href="https://github.com/user-attachments/assets/9db6c2f8-acd3-4bec-99d1-37e9622890fc"><img src="https://github.com/user-attachments/assets/9db6c2f8-acd3-4bec-99d1-37e9622890fc" width="100%" alt="ResonaDeck Music albums in the Steam Quick Menu"></a><br><b>Quick Menu · Music</b><br><sub>Browse your albums without leaving Steam.</sub></td>
<td align="center" width="50%"><a href="https://github.com/user-attachments/assets/f4451eb8-b4fe-462d-8e83-6981046eca41"><img src="https://github.com/user-attachments/assets/f4451eb8-b4fe-462d-8e83-6981046eca41" width="100%" alt="ResonaDeck Full Manager Music category"></a><br><b>Full Manager · Music</b><br><sub>A cover-driven music library made for a controller.</sub></td>
</tr>
<tr>
<td align="center" width="50%"><a href="https://github.com/user-attachments/assets/75712b32-0898-4b6e-9b0a-f5b8d347167d"><img src="https://github.com/user-attachments/assets/75712b32-0898-4b6e-9b0a-f5b8d347167d" width="100%" alt="ResonaDeck audiobook browsing"></a><br><b>Audiobooks</b><br><sub>Find and resume long-form audio.</sub></td>
<td align="center" width="50%"><a href="https://github.com/user-attachments/assets/03a84d73-3308-4a83-bd39-cb628e59939a"><img src="https://github.com/user-attachments/assets/03a84d73-3308-4a83-bd39-cb628e59939a" width="100%" alt="ResonaDeck Full Manager Plex search results"></a><br><b>Full Manager · Search</b><br><sub>Find tracks across your connected Plex library.</sub></td>
</tr>
</table>

<div align="center">

**[Explore all 9 screenshots →](SCREENSHOTS.md)**

<sub>Captured on a real Steam Deck with a personalized CSS Loader theme. Your own Plex artwork and colors will vary.</sub>

</div>

## 🚀 Install

1. Install **[Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader)** on your Steam Deck.
2. **[Download ResonaDeck-1.0.0.zip](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.0.0/ResonaDeck-1.0.0.zip)** from the official GitHub release.
3. Open Decky Loader → **Settings → Developer → Install Plugin ZIP**.
4. Select the ZIP, open ResonaDeck from the Quick Access Menu, and sign in to your Plex account.
5. Select a reachable Plex server and the audio libraries you want to browse.

> **Requires:** Steam Deck, Decky Loader, and access to a Plex Media Server containing your audio. ResonaDeck supplies no media content.

## 🎮 Controller guide

| Button | Action |
| :--- | :--- |
| **A** | Play or resume |
| **Hold A** | Preview supported media |
| **X** | Open media actions: Add to Queue, Play Next, Browse Details, and more |
| **D-pad ← / →** | Move across action menu columns |
| **D-pad ↑ / ↓** | Move between action menu rows |
| **B** | Back / close the menu or queue |
| **LB / RB** | Switch Full Manager sections |

**Where is search?** Search lives in **Full ResonaDeck**. Quick Menu search was intentionally removed to keep controller navigation smooth.

## 🔊 Two listening experiences

**Quick Access Menu:** Compact playback with artwork-reactive glass, an animated Shuffle highlight, the track queue, volume, and album/artist navigation.

**Full Manager:** A more spacious Plex audio library with shelves, artwork, track details, search, audiobook chapters, player settings, and library tools.

## 🧩 Open source

Browse the **[frontend source](src/index.js)**, **[Python Plex backend](resonadeck_backend.py)**, **[tests](tests/)**, and **[assets](assets/)** directly in this repository. The source matches the verified 1.0.0 installation ZIP; see **[Source & Integrity](SOURCE.md)** for the checksum and tag details.

## ℹ️ About 1.0.0

**1.0.0 preserves the hardware-tested 0.9.50 baseline** rather than introducing another feature overhaul. Playback speed depends partly on Plex server availability, network conditions, and server transcoding. Steam and Decky updates may affect controller or theme behavior.

## 💬 Issues & feedback

Bugs, feature suggestions, and compatibility reports are welcome in **[Issues](https://github.com/ValentineBSAA/ResonaDeck/issues)**. Include your SteamOS / Decky versions, the affected screen, and reproduction steps. **Please don't post Plex tokens, passwords, or private server links.**

**[Official release page](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.0.0)** · **[Full screenshot gallery](SCREENSHOTS.md)** · **[1.0.0 Release Notes](RELEASE_NOTES_1.0.0.md)** · **[Support](SUPPORT.md)** · **[Source & Integrity](SOURCE.md)** · **[Credits and Third-Party Notices](THIRD-PARTY-NOTICES.md)**

---

<div align="center">

Created by **Valentine** · **[GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.en.html)**

*Independent project, not affiliated with Plex, Valve, Steam, or Decky Loader.*

</div>
