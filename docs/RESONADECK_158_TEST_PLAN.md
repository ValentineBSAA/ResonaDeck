# ResonaDeck 1.5.8 TEST | Player Connect experiment
**Not a stable release.** Separate experimental branch. Do not merge into main or overwrite 1.5.7.

## Why this exists
GitHub Discussion #13 by brianx87 asks to use ResonaDeck to select other local Plex players
(iPod touch / iOS / Android attached to speakers), control playback and queues from the Steam
Deck, and eventually advertise the Steam Deck itself as a Plex player.

## What this test actually implements
- A controller- and touchscreen-accessible **Player Connect** disclosure in the QAM.
- On-demand LAN Plex Companion GDM search and Plex account resource discovery.
- Select, probe, pause, play, previous, next, stop and experimental send-current-track.
- No network scan until Player Connect is opened; remote requests are 2.8 seconds maximum.
- Only sends commands to numeric private IPv4 endpoints discovered via Plex/GDM.
- Warm-state Quick Menu: when a connected player has previously reached Ready,
  reopening can show controls without an initial full-screen Loading state.
- Original Deck music playback, artwork, visualizers, crossfade and queue remain locally owned.

## Not yet implemented
- Automatic remote playback ownership across all existing Now Playing controls.
- Synchronized full remote queue editor, seeking, progress, repeat, shuffle, or volume.
- Deck advertising itself as a Plex Companion receiver.
- Jellyfin remote control.
- Guaranteed compatibility with recent iOS Plex or Plexamp clients. Devices can appear
  even when their Companion HTTP listener is unreachable or newer APIs differ.
- Remote handoff of audiobook and podcast state.

**Do not mark Discussion #13 complete on this test.** The next test depends on actual
iPhone probe and playback results. A 2xx API response alone does not verify sound output.

## Steam Deck + iPhone hardware checklist
1. Keep ResonaDeck 1.5.7 original installer safe. Install this ZIP only in your TEST environment.
2. Use the same local Wi-Fi on Deck and iPhone. Disable VPN or guest-network isolation.
3. Install or open Plexamp on iPhone. Sign into the Plex account whose music library the Deck uses.
4. In Plexamp's Playback / Remote Control settings, enable incoming remote control, if offered.
   Keep Plexamp in foreground for the first test; connect iPhone to Bluetooth speakers.
5. On Steam Deck: open Quick Access > ResonaDeck. Measure first opening and second opening.
   Check that Plex artwork and normal playback work unchanged.
6. Expand Player Connect by tapping or D-pad + A; press Refresh. Note whether iPhone appears.
7. Select the phone (A or touch), observe the probe status. If it fails, note error + Plexamp version.
8. Start music directly on iPhone. From Deck try **Pause**, **Play**, **Next**, **Previous**.
   Confirm the PHONE changes and the Deck's local music does not accidentally change.
9. From Deck start a music track locally. Tap **Send Current Track** to the phone.
   Confirm whether the iPhone actually starts that song, not just an API acknowledgement.
   Normal ResonaDeck play/queue buttons still act locally in this build.
10. Leave the QAM, start a game, reopen QAM, and compare opening speed; then retry remote control.
11. Repeat using touchscreen and D-pad, A, B, LB/RB; try PS4 Bluetooth controller if available.
12. Suspend/resume the Deck once. Confirm GTM reactivity, local crossfade, library browsing,
    and playback still work. Remote reachability after wake may require manual Refresh.

## Report back
- **Found device:** yes/no; display name; Plex vs Plexamp app/version; iOS version.
- **Probe:** success / HTTP status / unreachable.
- **Play / Pause / Next / Previous:** which actions changed actual iPhone audio?
- **Send current track:** started correct music / returned success but silent / failed.
- **Quick Menu:** first open, second open, reopen during game, seconds until controls useful.
- **Input:** touchscreen, built-in controls and external controller.
- **Regressions:** Plex, Jellyfin, artwork, 3-hour track, crossfade, GTM visualizer state.

## Maintainer rules
- Build is patched from **exactly** the 1.5.7 release ZIP downloaded by GitHub Actions.
- SHA-256 of input installer MUST match:
  55f24398e5461cda6de732935a15fc11d9f47da550ba03b43aa4bac34975d03f
- ZIP contents must report 1.5.7 before patch; mismatches abort build.
- This is a Plex Companion feasibility test. Device list alone is NOT feature completion.
