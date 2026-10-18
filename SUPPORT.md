# Support & Troubleshooting

## First-time setup and updates

Install the official [1.2.1 Stable ZIP](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.2.1/ResonaDeck-1.2.1-Stable.zip) using **Decky Settings → General → Developer Mode**, then **Developer → Install Plugin from ZIP**.

Alternatively, use the independent [Decky Direct Updater](https://deckyup.nukeador.com/) and search for **`ValentineBSAA/ResonaDeck`**. Confirm the official source when prompted. Older 1.2.0 installations may require a one-time source confirmation. Updates are never silently installed.

Connect to a Plex Media Server that is reachable from the Deck and grant your account access to the audio libraries you want to browse.

## Common questions

### Nothing appears in my library
Confirm Plex connectivity and select the appropriate Music / Audiobook / Podcast / Other library sections. Reopen the plugin if you've just changed your Plex library permissions.

### Playback is slow or buffers
Check Plex server status, your network connection, and whether the server is transcoding the chosen media. A slow server can delay first playback.

### Does ResonaDeck support music crossfade?
Yes. In Surprise Me settings, select Off, 3, 5, 8, or 10 seconds. Automatic eight-second crossfades were confirmed on the creator's Steam Deck. Different Plex formats and network conditions can affect buffering. The XFADE status shows whether the incoming stream is buffering, ready, fading, or unable to transition. Crossfade is a music feature and should not overlap audiobook/podcast speech.

### How do I reopen or close Surprise Me settings?
Focus the active album artwork or idle turntable and press X. Press X again to close the settings panel. The artwork and fallback cover remain selectable.

### Where is Quick Menu search?
It was removed from v1.0.0 after testing showed the embedded controller search was too awkward. Use **Full Manager → Search**.

### How do I add a track to my queue?
Highlight a supported music item and press **X**. Select **Add to Queue** or **Play Next**. **Left/Right** changes columns; **Up/Down** changes rows. Use **B** to back out.

### Why are my colors different from the screenshots?
ResonaDeck chooses player colors based on artwork, and can coexist with Steam/CSS Loader themes. Exact appearance depends on the current track and theme.

### What if controller focus gets stuck?
Try **B** to close a drawer/menu, then reopen the page. If the problem is repeatable, file an issue with the exact screen, button sequence, SteamOS/Decky versions, and whether a CSS Loader theme is active.

### Direct Updater doesn't recognize ResonaDeck

Check that the source is **`ValentineBSAA/ResonaDeck`**. Use **Find source** in Direct Updater to verify the correct repository. If it cannot offer a release, download the official manual ZIP from [GitHub Releases](https://github.com/ValentineBSAA/ResonaDeck/releases/latest).

### Will my Plex settings survive the updater?

The 1.2.1 maintenance package doesn't change saved-settings code. However, preservation through an actual Direct Updater-based Steam Deck upgrade hasn't been verified. Back up important settings before upgrading.

## Reporting bugs

Please use [GitHub Issues](https://github.com/ValentineBSAA/ResonaDeck/issues) and include:

- ResonaDeck version (currently **1.2.1**) and SteamOS/Decky versions
- Installation method (Direct Updater or manual ZIP), and whether this was an upgrade
- Quick Menu or Full Manager screen name
- Expected behavior and actual behavior
- Button sequence to reproduce
- Logs or screenshots if helpful, **with private server details and tokens removed**

This is a community project without guaranteed support response times.

## Security and privacy

Do **not** post Plex authentication tokens, private server URLs, passwords, or local account credentials in public issues or screenshots. ResonaDeck does not host or sell your media.
