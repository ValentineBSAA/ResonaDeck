# ResonaDeck 1.4.1 | Validation snapshot

**Date:** 2026-11-02. Maintainer's physical Steam Deck observations, plus offline regression evidence.

| Test | Status |
| --- | --- |
| Plex resumes after real sleep/wake | **Hardware pass** (same listening session resumed) |
| Keep Playing selection persists after device restart | **Hardware pass** |
| GTM 4.1.2 and ResonaDeck coexist | **Hardware pass**, maintainer confirmation |
| Quick GTM Visualizers toggle | **Hardware accepted** after 1.3.7 compatibility fix |
| Prebuffered 8-second music crossfade | **Hardware accepted** during prior versions; automated regression preserved |
| Queue continues past 55 and past 130 with simulated failures | **Automated pass**, hardware marathon not separately confirmed |
| Crossfade selection persistence after restart | **Automated pass**; physical restart retention not independently singled out |
| Manually paused before sleep stays paused | **Automated pass**; not separately confirmed on hardware |
| Plex automatically resumes after **full reboot** | **Not verified / not promised** |
| Every Plex/Jellyfin server and SteamOS channel | **Not tested** |

Exact SteamOS and Decky Loader builds were not recorded. No universal compatibility, precise wake timing or uninterrupted infinite-playback guarantee is claimed.

**Release status:** 1.4.1 is prepared as a beta candidate; maintainer will upload the ZIP and publish the GitHub release separately.
