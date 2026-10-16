# 🎧 ResonaDeck 1.2.0 Stable

**A bigger listening experience for your own Plex library, built for the Steam Deck.** This stable release promotes the creator-tested 1.1.9 implementation, preserving the same working audio engine, controller behavior, and artwork presentation.

## 🎲 NEW since 1.0.0: Surprise Me

Your music library can now pick the soundtrack for you.

**How to use it:**
1. Open ResonaDeck's **Quick Access Menu** and focus the **gold Surprise Me turntable**.
2. Press **X** to open **Surprise Me Settings**. Press X again to close them. Press **A** on the idle gold turntable to start Surprise Me.
3. Choose your media category, then for Music choose **Tracks**, **Albums**, or **Rediscover**. Optionally enable **Favorites only**.
4. Configure your music session (10/20/40 starting tracks, **30 minutes / 1 hour / 2 hours**, or **Keep Playing**) and select **crossfade Off / 3 / 5 / 8 / 10 seconds**.
5. While music is playing, highlight the **active album cover** or fallback artwork and press **X** to reopen or close these settings without stopping playback.

**Important:** X is contextual. On an ordinary album, artist, or track in your library, X still opens **Add to Queue**, **Play Next**, **Browse Details**, and similar media actions. Those original functions have not been replaced.

## 🔄 What changed between 1.0.0 and 1.2.0?

1.0.0 introduced the core Plex experience. **1.2.0 builds on it** with music discovery, continuous listening, and smoother transitions. It is not a replacement of the entire interface.

| Area | 1.0.0 Stable | 1.2.0 Stable |
| :--- | :--- | :--- |
| Finding something to play | Choose albums, artists, tracks and library sections manually | **Surprise Me** discovers music through Tracks, Albums, or Rediscover modes; optionally Favorites only |
| Starting discovery | Normal library selection and playback | Focus the **gold turntable**; **A starts Surprise Me**, **X opens/closes its settings** |
| Adjusting during playback | Standard playback and media actions | Focus the **playing cover or fallback art**; **X toggles Surprise Me settings** without stopping playback |
| Playing continuously | Normal manually managed queue, shuffle and repeat | **Keep Playing** prepares more tracks before the queue ends, with repeat protection and bounded history |
| Listening time | Standard track/queue playback | Choose **10 / 20 / 40 starting tracks**, **30 min / 1 hr / 2 hr** listening sessions, or Keep Playing |
| Track-to-track audio | Ordinary song transitions | **Two-stream music crossfade** with Off / 3 / 5 / 8 / 10 seconds; 8 seconds was confirmed on Steam Deck |
| Album artwork transitions | Artwork-reactive glass and the original gold turntable | Incoming record preview, record arrival and **vinyl-to-full-cover** transition, plus full-square fallback covers |
| Discovering saved favorites | Original library/queue tools | Favorites browsing and optional Favorites-only discovery, plus listening tools |
| Status visibility | Conventional playback/queue status | **Live XFADE** timing and states to show what the next transition is preparing to do |
| General library interface | Music, Audiobooks, Podcasts, More Audio; Full Manager, Search, album art, queue actions | **Retained:** these established sections and much of their original layout remain recognizable |

**X is contextual:** on the Surprise Me turntable or active playing cover it opens/closes discovery settings; on a normal library album, artist or track it still opens that item's action menu (**Add to Queue**, **Play Next**, **Browse Details**). No need to stop music to change Surprise Me settings.

**Why the screenshot collection includes 1.0.0 images:** 1.2.0 changed listening behavior far more than it changed standard library screens. The **4 new 1.2.0 screenshots** show the updated player and XFADE, albums, Surprise Me turntable and settings. The **9 original 1.0.0 screenshots** remain useful for browsing, searching, audiobooks and the Full Manager. [See all 13 images grouped by release](SCREENSHOTS.md).

## ✨ Other new or substantially expanded listening features

- **Keep Playing:** continuously replenishes the music queue before the end, avoids unwanted immediate repeats where possible, and maintains a bounded playback history.
- **Favorites:** mark tracks you enjoy, browse your Favorites list, and optionally build Surprise Me sessions from Favorites only.
- **Music crossfade:** two separate Plex audio streams overlap for a configurable duration; the automatic **eight-second crossfade has been confirmed working on the creator's Steam Deck**.
- **The incoming record animation:** an upcoming vinyl previews beside the player, moves through the familiar gold turntable, then expands to the next full-size album cover. The visual handoff follows audio playback rather than claiming a fade that hasn't started.
- **Live XFADE information:** reports countdown and states such as preparing, ready, starting, fading, complete, or why a fade could not begin.
- **Artwork reliability:** album covers, fallback images and upcoming-cover preparation were improved.
- **Personal listening tools:** saved sessions, local playlists, sleep timer, and themed selectable settings.

## 💙 What has NOT been redesigned

The **Music / Books / Podcasts / More** navigation, album/artist/track browsing, Full Manager shelves and search, audiobook chapters/resume, media action menu, general queue controls, controller navigation conventions, artwork-inspired glass colors, and the gold idle turntable remain recognizable.

This is why **nine screenshots from 1.0.0 are intentionally retained**. They are still useful representations of those parts of ResonaDeck. Four newer screenshots show the **1.2.0 player and XFADE status, album browsing, Surprise Me turntable, and its settings**. We did not manufacture new screenshots of screens that barely changed.

**[Browse all 13 screenshots, organized by version](https://github.com/ValentineBSAA/ResonaDeck/blob/main/SCREENSHOTS.md)**  
**[New screenshot files](https://github.com/ValentineBSAA/ResonaDeck/tree/main/docs/screenshots/v1.2.0)**

## ⬇️ Install or upgrade

Download **[ResonaDeck-1.2.0-Stable.zip](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.2.0/ResonaDeck-1.2.0-Stable.zip)** from this release's Assets.

In Decky Loader, open **Settings → Developer → Install Plugin ZIP**, choose the complete plugin ZIP, and sign in to your own reachable Plex Media Server. The ZIP is the full install, not a patch. ResonaDeck does not include copyrighted media.

## 🔬 Tested vs. still worth testing

Creator-confirmed on Steam Deck: Surprise Me playback, Keep Playing music, Favorites browsing, X-driven settings, full-square real/fallback artwork, **automatic eight-second crossfade**, and the record-to-cover animation.

Broader testing is still welcome for 3/5/10-second transitions, mixed codecs, intermittent networks, unusual queue controls, more Plex versions, and third-party Steam themes. Small visual timing imperfections may remain. See the **[feature verification checklist](https://github.com/ValentineBSAA/ResonaDeck/blob/main/FEATURE_STATUS_1.2.0.md)**.

Feedback, screenshots, and first-install reports are welcome in **[Issues](https://github.com/ValentineBSAA/ResonaDeck/issues)**. Please omit Plex credentials and server tokens.

Created by Valentine. Independent project, not affiliated with Plex, Valve, Steam, or Decky Loader.
