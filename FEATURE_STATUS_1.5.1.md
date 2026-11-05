# ResonaDeck 1.5.1 verification and release scope

**Release:** [1.5.1 stable](https://github.com/ValentineBSAA/ResonaDeck/releases/tag/1.5.1) (November 5, 2026).

| Check | Result |
| --- | --- |
| Published installer and local candidate SHA-256 | Identical: `ab6b862a27ed6354fd7b4ad0a3d2e93934b22f18720c741d1bd7f06d090b4400` |
| ZIP entry integrity | Pass |
| JavaScript parsing (`node --check`) | Pass |
| Python `ast.parse` for entrypoint, backend and Jellyfin modules | Pass |
| `plugin.json` / `package.json` and compiled version | 1.5.1 |
| Formerly failing three-hour track on Steam Deck | Maintainer-confirmed pass |
| 1.5.1 counter readability | Maintainer accepted 1.5.1 on hardware |
| Every Plex codec / all SteamOS versions | Not universally verified |

**Scope:** The three-hour track problem was caused by unit confusion and long-duration rejection. ResonaDeck now uses explicit time units and has premature-end recovery. The 1.5.1 user-facing change preserves seconds in crossfade countdowns above one minute or one hour. Keep Playing, source authentication, and GTM integration remain separate, preserved features.

**Important:** Automated syntax and archive validation do not constitute full end-to-end streaming coverage. If another media format skips unexpectedly, capture the Plex duration, approximate playback time, and safe-to-share codec/transcoding details without disclosing tokens or private server addresses.

[Release notes](RELEASE_NOTES_1.5.1.md) · [Checksum](RELEASE_ASSET_SHA256_1.5.1.txt) · [Support](SUPPORT.md)
