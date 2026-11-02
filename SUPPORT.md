# ResonaDeck support and troubleshooting

The creator-tested beta candidate is **ResonaDeck 1.4.1**. The maintainer will upload its full plugin ZIP to [GitHub Releases](https://github.com/ValentineBSAA/ResonaDeck/releases). [1.2.1 stable](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.2.1) remains the last published stable release until that happens.

## Install/update
Open Decky Loader's **Settings → General → Developer Mode**, then **Developer → Install Plugin from ZIP**. Choose the **named `ResonaDeck-1.4.1.zip` release asset** after it is published. GitHub's automatic Source code archives are not installers. Keep your existing saved settings.

Direct Updater is an optional independent Decky add-on; search for `ValentineBSAA/ResonaDeck`. The user has not separately verified the 1.4.1 upgrade through Direct Updater.

## Common fixes
- **No libraries:** verify Plex account permissions, reachable server and chosen libraries. Jellyfin support is included but has not been exhaustively hardware-verified in this beta.
- **Music starts slowly:** check server transcoding and network availability; remote libraries may need buffering.
- **Keep Playing resets to 20 tracks:** update to 1.4.1, enable Keep Playing in Surprise Me settings, close/reopen, then restart. The creator confirmed that selection survived a full restart.
- **Keep Playing queue ends:** 1.4.1's rolling queue replenishes before the former 55-track endpoint; enabling it during playback requests an immediate refill, with fallback for temporary discovery failures.
- **Crossfade preference:** Surprise Me provides Off/3/5/8/10 seconds. Preference persistence is covered by offline regression tests; 8-second playback overlap was confirmed on Deck during development.
- **After sleep the player stays silent:** Full ResonaDeck → Account/Profile → Settings → Sleep & Wake; enable resume and set delay (5–60 seconds, default 12). It only auto-resumes a track that was playing before sleep. **Automatic Plex playback after a complete Deck reboot is not required or verified.**
- **GTM visualizer toggle:** below **Open Full ResonaDeck** in Quick Access. OFF immediately stops external GTM visualizer data while Plex continues to play; GTM 4.1.2 is the paired version.
- **Decky gets stuck on “Downloading any external binaries”:** the slim 1.4.1 installer does not require an external binary download; restart a stuck Decky installer before retrying. Do not erase saved settings.

## Reporting issues
Use [GitHub Issues](https://github.com/ValentineBSAA/ResonaDeck/issues) with your SteamOS/Decky versions, which player controls you used, expected vs actual behavior, and steps to reproduce. **Never upload Plex tokens, private server addresses, or account credentials.**

[Release notes](RELEASE_NOTES_1.4.1.md) · [Validation](FEATURE_STATUS_1.4.1.md) · [Source integrity](SOURCE.md)
