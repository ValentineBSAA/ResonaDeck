# ResonaDeck 1.0.0 · First Stable Release

**Your Plex audio library, at home on Steam Deck.**

ResonaDeck 1.0.0 is the first stable milestone of this independent Decky Loader plugin. It carries forward the user-tested **0.9.50** implementation without changing its playback and controller behavior.

## What's in 1.0.0

- **Quick Access Menu playback** for Plex Music, Audiobooks, Podcasts, and More Audio.
- **Full ResonaDeck manager** with Home shelves, category browsing, Search, media details, and Plex library tools.
- **Artwork-reactive frosted glass** for player buttons, queue, and album/track artwork; individual category palettes.
- **Controller-first navigation**, including X action menu, Add to Queue, Play Next, and a 2×2 D-pad action layout.
- **Queue drawer** with artwork-derived glass, working close/back navigation, and a **live total-track count**.
- **Audiobook chapter, resume, and long-form playback** controls.
- **Stable artwork display** that can reuse cached covers before Play.
- **Full Manager loading/error recovery** and preserved controller focus routing.
- **Shuffle perimeter animation** and an idle player that does not waste D-pad navigation on unavailable controls.

## Install

1. Download the **ResonaDeck-1.0.0.zip** asset from the GitHub Release when published.
2. On Steam Deck, open **Decky Loader → Settings → Developer → Install Plugin ZIP**.
3. Install the archive, open ResonaDeck, and authorize your Plex account and reachable media server.

## Upgrade from 0.9.50

The version number and public-facing packaging changed; the approved **0.9.50 audio, focus, queue, and visual behavior is intentionally preserved**.

## Compatibility and scope

ResonaDeck needs a Plex Media Server and your own audio media. It doesn't supply audio content. Network/server status and transcode needs can affect startup. SteamOS, Steam Client, Decky Loader, and CSS Loader changes may require later compatibility fixes.

**Quick Menu Search is intentionally absent.** Search is available in Full ResonaDeck.

## Feedback

Please report reproducible issues through **[GitHub Issues](https://github.com/ValentineBSAA/ResonaDeck/issues)**. Include Decky/SteamOS version, affected screen, and controller steps. Avoid sharing Plex tokens or credentials.

**Author:** Valentine · **License:** GPL-3.0-only

ResonaDeck is not affiliated with Plex, Valve, Steam, or Decky Loader.
