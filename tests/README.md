# ResonaDeck regression tests

Legacy focused tests for artwork, Quick Access controls, queues, Surprise Me, crossfade and metadata remain in this directory. **Some historical tests intentionally pin an older release** and are not automatically valid for 1.4.1.

## New 1.4.1 tests
The following 1.4.1 tests were run successfully with the final source, after replacing developer-specific absolute paths with repository-relative paths:

| Test | Coverage |
| --- | --- |
| `test_resonadeck_141_persistence.py` | Choice migration, durable read-back, late writes, invalid values and reconnect. |
| `test_resonadeck_141_ui.cjs` | Keep Playing immediate queue refill, active Crossfade controls, async settings load. |
| `test_resonadeck_141_queue.cjs` | Rolling queue continuity and refill boundary logic. |
| `test_resonadeck_141_crossfade.cjs` | Prebuffered eight-second crossfade and interruption safeguards. |
| `test_resonadeck_141_sleep.cjs` | Sleep/wake, delayed resume and manual Pause precedence. |
| `test_resonadeck_141_power.py` | Suspend-aware Linux clock fallback. |
| `test_resonadeck_141_pcm.cjs` | Web Audio fallback and captured frequency telemetry. |
| `test_resonadeck_141_gtm_bridge.cjs` | Real GTM 4.1.2 bridge handshake, immediate visualizer OFF/ON; requires both repository trees. |

From repository root:
```bash
node --check dist/index.js
python3 -m py_compile main.py resonadeck_backend.py jellyfin_provider.py jellyfin_discovery.py
node tests/test_resonadeck_141_crossfade.cjs
node tests/test_resonadeck_141_pcm.cjs
node tests/test_resonadeck_141_queue.cjs
node tests/test_resonadeck_141_ui.cjs
node tests/test_resonadeck_141_sleep.cjs
python3 tests/test_resonadeck_141_persistence.py
python3 tests/test_resonadeck_141_power.py
node tests/test_resonadeck_141_gtm_bridge.cjs ../Game-Theme-Music .
```
The bridge test assumes the GTM checkout is `../Game-Theme-Music` and may be supplied an explicit alternative path. Separate hardware acceptance is documented in [FEATURE_STATUS_1.4.1.md](../FEATURE_STATUS_1.4.1.md). Automated success does not guarantee every SteamOS update, codec or Jellyfin server combination.
