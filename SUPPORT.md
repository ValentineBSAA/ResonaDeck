# Support & Troubleshooting

## First-time setup

Install ResonaDeck from its ZIP using **Decky Loader → Settings → Developer → Install Plugin ZIP**. Start the plugin from the Quick Access Menu and authorize Plex.

Make sure your Deck can reach the Plex server over your network or configured remote connection, and that your account has access to audio libraries.

## Common questions

### Nothing appears in my library
Confirm Plex connectivity and select the appropriate Music / Audiobook / Podcast / Other library sections. Reopen the plugin if you've just changed your Plex library permissions.

### Playback is slow or buffers
Check Plex server status, your network connection, and whether the server is transcoding the chosen media. A slow server can delay first playback.

### Where is Quick Menu search?
It was removed from v1.0.0 after testing showed the embedded controller search was too awkward. Use **Full Manager → Search**.

### How do I add a track to my queue?
Highlight a supported music item and press **X**. Select **Add to Queue** or **Play Next**. **Left/Right** changes columns; **Up/Down** changes rows. Use **B** to back out.

### Why are my colors different from the screenshots?
ResonaDeck chooses player colors based on artwork, and can coexist with Steam/CSS Loader themes. Exact appearance depends on the current track and theme.

### What if controller focus gets stuck?
Try **B** to close a drawer/menu, then reopen the page. If the problem is repeatable, file an issue with the exact screen, button sequence, SteamOS/Decky versions, and whether a CSS Loader theme is active.

## Reporting bugs

Please use [GitHub Issues](https://github.com/ValentineBSAA/ResonaDeck/issues) and include:

- ResonaDeck version (e.g. **1.0.0**) and SteamOS/Decky versions
- Quick Menu or Full Manager screen name
- Expected behavior and actual behavior
- Button sequence to reproduce
- Logs or screenshots if helpful, **with private server details and tokens removed**

This is a community project without guaranteed support response times.

## Security and privacy

Do **not** post Plex authentication tokens, private server URLs, passwords, or local account credentials in public issues or screenshots. ResonaDeck does not host or sell your media.
