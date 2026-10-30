# ResonaDeck for Windows · 0.1 Preview

This is the **Windows desktop adaptation** of the existing ResonaDeck 1.2.1 Steam Deck code. It is developed on a separate branch and does not change the stable Decky plugin. **Not yet hardware-accepted:** Windows audio playback, Plex authentication, crossfades, tray behavior, gamepad operation and the installer require real Windows testing.

## What is shared

The actual Deck frontend source is bundled into the Electron renderer during the build. Its Plex menus, Surprise Me, Keep Playing, queue, player engine, timed crossfade, vinyl animation and audiobook/podcast UI remain in one place, not copied or reimplemented. The Python JSON-RPC bridge loads the real Decky backend with Windows-local storage directories. The Decky-specific UI primitives and route navigation are replaced by a compact browser shim.

## Windows-specific features

- Frameless, resizable window with draggable custom title bar, Minimize and Close buttons.
- Mini player and full manager, with Ctrl+M to switch and Escape to return.
- Always on Top toggle in the title bar and system tray; Ctrl+Shift+P shortcut.
- Close to tray, restoring from tray, independent windows for mini/full layouts.
- Last window size, screen position and pin/tray preferences persisted.
- Single instance, Windows user-data separation from your Steam Deck, mouse/text input, optional controller shoulder bridge.
- Background throttling disabled so the active audio engine can run while minimized.
- App uses secure preload IPC: Node integration disabled, context isolation and sandbox enabled. The Python process owns all Plex tokens.

## Development launch on Windows

Requires Windows 10/11, Node.js and Python 3.11+.

From the repository root, in PowerShell:

    python -m pip install -r windows/requirements.txt
    cd windows
    npm install
    npm run check
    npm run dev

If Python is not available as \`python\`, set \`RESONADECK_PYTHON\` to the interpreter path before launching. The first run stores settings under Electron's per-user data directory; Plex tokens are **not** written to project source. The app works with a reachable Plex server; it does not ship audio or media.

## Create Windows installer locally

From repo root:

    python windows/scripts/build_icon.py
    python -m PyInstaller --noconfirm --clean --onedir --name ResonaDeckBackend --distpath windows/backend-dist --workpath windows/.pyinstaller-build --specpath windows/.pyinstaller-build --hidden-import resonadeck_backend --collect-submodules mutagen --add-data "assets;assets" --paths . windows/bridge.py
    cd windows
    npm install
    npm run package:win

Installer output: \`windows/release/\`. Alternatively use the Windows Preview GitHub Actions workflow artifact. This is **not yet** a stable downloadable release. Do not label it 1.2.1 Stable for Windows.

## Manual acceptance checklist

1. Launch from Windows 11 without Steam or Decky installed.
2. Sign in to Plex and confirm your server, Music, Audiobooks, Podcasts and Other Audio libraries.
3. Play, pause, seek, change volume, play next, queue, shuffle/repeat, save preferences.
4. Run Surprise Me, Keep Playing, session duration and the automatic 8-second crossfade, including a mixed-codec boundary.
5. Watch the gold turntable/crossfade cover handoff and validate artwork fallback.
6. Hide in tray while playing, restore, toggle Always on Top, drag/resize, exit without an orphan Python process.
7. Test full/mini transitions, mouse, keyboard, and controller input, with sleep/resume and Plex connection loss.
8. Reinstall preview and confirm settings survive. Then regression-test the Steam Deck build separately.

Important: The Steam Deck UI depends on native Steam focus behaviors. Mouse and keyboard use the Windows adapter. Standard gamepad shoulder events are translated, but full Deck controller parity is still a testing target, not a completed claim.
