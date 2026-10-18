# ResonaDeck 1.2.1 Stable · Feature and Update Validation

Updated 2026-10-18. Distinguishes checks performed offline from testing on real hardware.

## Verified in the published 1.2.1 package

- [x] Official `ResonaDeck-1.2.1-Stable.zip` matches SHA-256 `165fbfe15e21d01ae6cf9ac7042d3efad8cb100bb89e1fc2cf18cc6fe71a4493`.
- [x] Consistent version `1.2.1` in `package.json`, `plugin.json`, frontend display and backend fallback.
- [x] Canonical source `ValentineBSAA/ResonaDeck` declared in package metadata.
- [x] ZIP contains one top-level `ResonaDeck/` directory and all required Decky runtime files.
- [x] The Plex backend, crossfade scheduler, controller behavior, Surprise Me, and artwork engine were not redesigned in this maintenance release.

## Creator-confirmed on Steam Deck in 1.2.0

- [x] Automatic eight-second music crossfade without pressing a manual test button.
- [x] Surprise Me, Keep Playing, Favorites and contextual A/X controller actions.
- [x] Native/fallback covers, idle gold turntable and incoming vinyl-to-cover animation.

See [the original 1.2.0 hardware verification](FEATURE_STATUS_1.2.0.md) for detail.

## Still needs real hardware acceptance

- [ ] Install ResonaDeck using Direct Updater on a Steam Deck.
- [ ] Update a 1.2.0 installation to 1.2.1 and confirm the displayed version.
- [ ] Confirm Plex sign-in and saved preferences survive this specific update path.
- [ ] Verify a later official GitHub stable release appears without silent installation.
- [ ] Expand crossfade tests to 3/5/10-second options and mixed formats, and test external themes.

**Do not report the Direct Updater path as Steam Deck-confirmed until those checks are completed.**
