# Source Code & Release Integrity

**ResonaDeck 1.0.0 is open source, and its actual plugin code is browsable in this repository.**

## Browse the code

- **[src/index.js](src/index.js):** original frontend source, including the controller-first Quick Menu and Full Manager.
- **[dist/index.js](dist/index.js):** installable frontend bundled with Decky Loader. This matches the published frontend source byte-for-byte.
- **[resonadeck_backend.py](resonadeck_backend.py):** Python Plex integration and playback backend.
- **[main.py](main.py):** Decky Loader bootstrap.
- **[package.json](package.json)** and **[plugin.json](plugin.json):** dependencies, version and plugin metadata.
- **[assets/](assets/):** icon, fallback art and interface assets.
- **[tests/](tests/):** automated regression tests.
- **[mutagen/](mutagen/)** and **[third_party/](third_party/):** included metadata parser and accompanying third-party licensing material.
- **[CHANGELOG.md](CHANGELOG.md)** and **[RELEASE_VALIDATION_1.0.0.md](RELEASE_VALIDATION_1.0.0.md):** development history and validation record.

The code was imported directly from the exact public **ResonaDeck 1.0.0** installation archive after checking its SHA-256. The important GitHub blobs were cross-checked against the local original and match.

## Install the plugin

Download the named **[ResonaDeck-1.0.0.zip](https://github.com/ValentineBSAA/ResonaDeck/releases/download/1.0.0/ResonaDeck-1.0.0.zip)** release asset.

For installation use the named plugin ZIP, **not** GitHub's automatically generated repository snapshots.

> Historical note: the **1.0.0 Git tag** was created before the source tree was imported onto `main`. GitHub's automatically generated **Source code (zip/tar.gz)** archives for that particular tag reflect its earlier, documentation-only commit. The complete browsable source is now on `main`, and the named 1.0.0 release asset contains the exact corresponding plugin files. We have not rewritten the already-published tag.

## Release integrity

**Named release asset:** `ResonaDeck-1.0.0.zip`

**SHA-256:**

```text
e09416573796a432ec2fc093f613108d79929134677dbad6cba5efb37675dd7a
```

See [the 1.0.0 release](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.0.0), [release notes](RELEASE_NOTES_1.0.0.md), [license](LICENSE), and [third-party notices](THIRD-PARTY-NOTICES.md).

ResonaDeck is an independent project, not affiliated with Plex, Valve, Steam, or Decky Loader.
