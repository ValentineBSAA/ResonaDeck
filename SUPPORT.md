# ResonaDeck support and troubleshooting

**Current published stable:** [ResonaDeck 1.5.7](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.5.7) · [Download ZIP](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.5.7/ResonaDeck-1.5.7.zip) · [Release notes](RELEASE_NOTES_1.5.7.md).

### GTM music-reactive visualizer looks static

If your music plays and a GTM visualizer is visible but **doesn't react to the music**, open **Quick Access → ResonaDeck → GTM Visualizers** and switch sharing **OFF, then ON** once. The maintainer reproduced an initially unreactive link and found this refresh restored frequency response. A reliable cold-start handshake in every SteamOS/Decky session is not universally verified.

For further details, visit **Full ResonaDeck → Settings → GTM Visualizers · Live Control**. Useful diagnostics include **Live PCM**, **audio context**, **analyzer RMS**, **capture tracks**, **packets sent** and **GTM acknowledgment**. These report different parts of the bridge; a running audio context or old packet count alone does not prove fresh frequency frames are reaching GTM. Do not change the safe Web Audio fallback unless normal reconnection fails and you understand it may take effect on the next track.

The visualizer toggle controls visuals, **not** audio playback. Enabled visuals should remain hidden with no eligible music playing, then may appear while compatible music plays. [GTM 4.6.7](https://github.com/ValentineBSAA/Game-Theme-Music/releases/tag/V4.6.7) is the recommended pair.

### Quick Menu styling after an update

If the artwork expands, text overlaps or controls look unstyled, update to **1.5.7**, close/reopen Quick Access and retry. The stylesheet-scope issue from an intermediate 1.5.x build was corrected. A full Deck restart is normally unnecessary; restart **Steam** only if old UI hooks remain after a hot update.


## Jellyfin sign-in and Steam keyboard

When Jellyfin is signed out, open **Full ResonaDeck Manager** from Quick Access. Choose the Jellyfin server/address, username and password fields with the controller. The compact field editor stays above Steam's native keyboard, and the **Nothing Playing** banner is omitted during sign-in. Press Back/Done to return to the next field. If Steam's keyboard does not appear automatically, focus the editor and use Steam + X.

Keep credentials private when sharing screenshots or logs. The appearance of Steam's keyboard is controlled by SteamOS, not by the ResonaDeck theme.

## Install/update
Open Decky Loader's **Settings → General → Developer Mode**, then **Developer → Install Plugin from ZIP**. Choose the published **[ResonaDeck-1.5.7.zip](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.5.7/ResonaDeck-1.5.7.zip)** release asset. GitHub's automatic Source code archives are not installers. Keep your existing saved settings.

Direct Updater is an optional independent Decky add-on; search for `ValentineBSAA/ResonaDeck`. A direct updater's behavior depends on the updater and Decky version; the official 1.5.7 release ZIP remains the verified installation asset.

## Common fixes
- **No libraries:** verify Plex account permissions, reachable server and chosen libraries. Jellyfin support is included, although every provider/device combination has not been exhaustively hardware-verified.
- **Music starts slowly:** check server transcoding and network availability; remote libraries may need buffering.
- **Keep Playing resets to 20 tracks:** update to 1.5.7, enable Keep Playing in Surprise Me settings, close/reopen, then restart. The creator confirmed that selection survived a full restart.
- **Keep Playing queue ends:** ResonaDeck's rolling queue replenishes before the former 55-track endpoint; enabling it during playback requests an immediate refill, with fallback for temporary discovery failures.
- **Crossfade preference:** Surprise Me provides Off/3/5/8/10 seconds. Fade overlap is different from the **time until fade** shown as `3h 00m 00s`, `2h 59m 08s`, `3m 08s` or `8s`. 
- **Long track skips after one or two seconds:** update to 1.5.7. Earlier code could read 10,800 seconds as 10.8, reject durations above two hours, or misinterpret a prematurely ended stream. Version 1.5.1 fixes duration units, removes the cutoff and attempts same-track recovery. If the issue remains, report the Plex item duration, codec, and whether the server is transcoding. **Never send private URLs or tokens.**
- **After sleep the player stays silent:** Full ResonaDeck → Account/Profile → Settings → Sleep & Wake; enable resume and set delay (5–60 seconds, default 12). It only auto-resumes a track that was playing before sleep. **Automatic Plex playback after a complete Deck reboot is not required or verified.**
- **GTM visualizer toggle:** below **Open Full ResonaDeck** in Quick Access. OFF immediately stops external GTM visualizer data while Plex continues to play; GTM 4.6.7 is the recommended pairing; compatible earlier bridge implementations can also work.
- **Decky gets stuck on “Downloading any external binaries”:** the 1.5.7 installer does not require an external binary download; restart a stuck Decky installer before retrying. Do not erase saved settings.

## Reporting issues
Use [GitHub Issues](https://github.com/ValentineBSAA/ResonaDeck/issues) with your SteamOS/Decky versions, which player controls you used, expected vs actual behavior, and steps to reproduce. **Never upload Plex tokens, private server addresses, or account credentials.**

[Release notes](RELEASE_NOTES_1.5.7.md) · [Current validation](FEATURE_STATUS_1.5.7.md) · [Source integrity](SOURCE.md)
