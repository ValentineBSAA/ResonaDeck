# ResonaDeck 1.2.0 Stable

**Promoted from the creator-tested 1.1.9 build.** The underlying music playback, audio crossfade, artwork-transition, queue, Favorites, and controller functionality is preserved. This release changes version metadata, packaging, and public documentation only.

### Highlights

- **Surprise Me:** themed discovery and configurable listening from Plex Music, Audiobooks, Podcasts, and other audio libraries.
- **Keep Playing:** continuous queues refill automatically, with bounded history and recent-repeat protection. Timed session options are also included.
- **Automatic music crossfade:** a two-stream 8-second overlap confirmed working audibly on an actual Steam Deck. Off/3/5/8/10-second choices are included; only the 8-second automatic transition is specifically confirmed in this release.
- **Vinyl-to-artwork handoff:** incoming record previews and a synchronized gold-turntable transition into full-square real or fallback album art. Minor animation timing polish may still be useful.
- **Personalization and management:** Favorites, saved sessions, local playlists, sleep timer, themed browsing and controller-friendly X/A actions.
- **Status feedback:** XFADE preparation, countdown, start, fade and completion information.

### What's not claimed

This stable promotion is based on creator hardware testing of primary listening functionality. It is **not** a complete QA certification across every Plex server, codec, crossfade duration, audio format, external theme, or long-form resume scenario. See `FEATURE_STATUS_1.2.0.md`.

### Install / update

Download **ResonaDeck-1.2.0-Stable.zip** from this release's Assets and install through **Decky Loader → Settings → Developer → Install Plugin ZIP**. The ZIP contains the entire plugin, not just a patch. ResonaDeck requires media on your own reachable Plex server.

Thanks to everyone testing the early builds and reporting real Steam Deck behavior. The breakthrough came when the manual two-stream crossfade was confirmed and automatic scheduling could be debugged independently.

Created by Valentine. Unofficial Plex client; not affiliated with Plex, Valve, or Decky Loader.
