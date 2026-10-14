# ResonaDeck 1.0.0 release validation

- Baseline: 0.9.50, reported working on Steam Deck by the user.
- Runtime code delta: version constant only in frontend (`src/index.js`, `dist/index.js`) and backend (`main.py`, `resonadeck_backend.py`). No new playback, controller, queue, UI layout, or network logic.
- Release metadata: `plugin.json` and `package.json` updated to 1.0.0.
- Frontend source/package synchronization: identical.
- Test run: 53 JavaScript/Python regression scripts passed, plus one mini-player component test (`RD_SKIP_BROWSER=1`).
- JavaScript syntax: `node --check` for source and distribution; Python syntax: `py_compile` for backend and plugin.
- Unit/component checks do not replace deployment smoke tests on a Steam Deck running the target Steam Client / CSS Loader theme and Plex server.
- Package excludes local `test-output` screenshots, `.pyc` files, and `__pycache__` directories.
