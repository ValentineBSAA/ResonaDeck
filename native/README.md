# ResonaDeck Native for Windows 11 | 0.2.0 Preview

This is a complete **new native Windows application**, not Electron and not
a clone of the Steam Deck quick access menu. Built using PySide6 Qt Widgets
and Qt Multimedia, with the existing ResonaDeck 1.2.1 Plex backend. It has
a transparent frameless top-level window whose visible surface is the player.

This branch is independent of both the Steam Deck Stable version and the
experimental Electron Windows branch. No old binaries were overwritten.
All Windows-specific functionality must pass hands-on testing before a
Stable release.

## Implemented in code

- Rounded frameless resizable Mini Player (default 440 x 255), animated
  gold vinyl/album art, hover resize grip, window dragging, right-click menu.
- Expanded Player (504 x 650), Full native Library (1120 x 760), with
  remembered separate window geometry and optional Always on Top.
- Qt album grid with actual offset/total/hasMore pagination, load-more,
  mouse wheel and double-click. Artists, albums, tracks, playlists, search,
  album details, queue, Play All, Play Next and Add to Queue.
- Native Qt Multimedia dual-player crossfade, seek, pause, next/previous,
  volume, shuffle/repeat and Plex stream fallback.
- Plex auth with default browser, Plex Home user PINs, server discovery,
  art caching, local account preferences, Favorites and saved sessions.
- Surprise Me / Keep Playing, 8-second default music crossfade, sleep timer,
  controller shoulder buttons, keyboard commands and tray controls.
- Native autostart opt-in, close-to-tray opt-in, per-mode window positions,
  reduce motion, audiobook/podcast speed and resume.

## Download and start

Open GitHub Actions > ResonaDeck Native Windows Preview > latest successful
run. Under Artifacts download ResonaDeck-Native-Windows-0.2.0-Preview.
Unzip both layers and run ResonaDeckNative/ResonaDeckNative.exe. Keep the
whole directory intact, particularly its backend and Qt libraries.
This is a *portable ZIP Preview*, not a signed Windows installer.

For development on Windows:

    python -m pip install -r native/requirements.txt
    python -m unittest discover -s native/tests -p "test_*.py" -v
    python native/tests/backend-smoke.py
    python native/app.py

First run: right-click the player > Plex Account and Servers > Sign in.
Approve Plex in your browser. The app saves its *own* Windows backend
settings under AppLocalData, not in source code or Steam Deck settings.

## Shortcuts

Space = play/pause. Ctrl+M = mini/expanded. Ctrl+L = library.
Ctrl+F = search. Ctrl+Shift+P = pin. Ctrl+Left/Right = previous/next.
Escape = back. Right-click = Windows menu and advanced tools.
XInput A/B/Start/LB/RB work while the window has focus.

## Acceptance: do not claim more than tested

- Automated: 156-album pagination model; queue/shuffle/repeat and discovery
  rules; source and frozen Plex backend handshakes; Qt offscreen widget startup;
  Windows portable executable packaging.
- Real Windows verification still required: login with actual Plex account,
  complete album scrolling, album art downloads, seamless crossfade audible
  quality, direct/transcoded codecs, lost network recovery, tray playback,
  DPI and multi-monitor positions, Windows startup and XInput hardware.
- Not fully ported: original per-chapter audiobook UI; global Windows
  System Media Transport Controls (SMTC); full Steam Deck Saved Sessions
  UI; installer code signing. These must remain on the known-gaps list.
- Keep main.py, resonadeck_backend.py, the old plugin frontend, and Deck
  release metadata unchanged.

The source is GPL-3.0-only as in the original repository. Qt/PySide6 is
distributed subject to its applicable LGPL/commercial terms; bundle all
necessary Qt license notices when publishing installers.
