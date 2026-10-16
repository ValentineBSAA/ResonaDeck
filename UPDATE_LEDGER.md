## 0.9.29 DEV (2026-10-12)
See QUALITY_OF_LIFE_0.9.29.md and VALIDATION_0.9.29_DEV.md for scope and verification.

## 0.9.28 DEV — Controller Recovery
- Reverted the rejected 0.9.27 runtime theme-ownership experiment to the hardware-stable 0.9.26 Full Manager/controller baseline.
- Removed runtime MutationObserver/focus/style reassertion logic that could interfere with Decky spatial navigation.
- Preserved shared QAM/Full Manager version identity and enlarged only the QAM version badge.
- No playback, queue, artwork, shuffle/repeat or page-reset redesign.

## 0.9.26 DEV — Theme Isolation + Version Identity

**Focus:** stop Steam/CSS Loader themes from painting Full Manager control surfaces, expose the running version everywhere testers need it, and keep the persistent player visually coherent with QAM.

- Full Manager controls now own their base surface/background; external themes may still influence ResonaDeck's sampled focus accent.
- Shared version badge derives from `RD_VERSION`, avoiding separate hard-coded QAM/Manager labels.
- QAM shows version beside Plex connection state; Full Manager shows it beside the ResonaDeck brand.
- Persistent player keeps the 0.9.25 audiobook/title improvements and uses isolated dark controls.

# ResonaDeck Update Ledger

## 0.9.25 DEV — Full Manager Refinement

**Hardware input:** 0.9.24 confirmed the new Full Manager structure, page-to-top behavior, and B/back hierarchy, but utility/account controls remained washed out and Plex Home list focus could fall into the persistent player.

**Locked:** playback engine, QAM player, shuffle tracer, repeat, artwork, Cover Flow, queue behavior, page reset, and 0.9.24 account hierarchy.

**0.9.25 focus:** Full Manager contrast, persistent-player parity, user-picker focus containment, and complete release-version consistency.

## 0.9.24 DEV — Full Manager Unity

**Hardware input:** 0.9.23 playback works, Shuffle OFF/ON and perimeter tracer work, Full Manager page changes return to the top. Remaining hardware complaint was the Full Manager's washed-out visual hierarchy, incomplete title presentation, mini-player inconsistency, and B escaping the manager from Account/Settings.

**Locked from 0.9.23:** audio transport, QAM player behavior, native shuffle label/tracer, repeat states, Cover Flow, artwork system, paging reset, Plex stale-endpoint retry, and session reliability.

**0.9.24 focus:** one cohesive Full Manager redesign and controller-back repair without touching the verified QAM core.

## 0.9.23 DEV — 1.0 Readiness Consolidation
**Baseline:** 0.9.22 hardware-confirmed for audio playback and Shuffle OFF/ON + snake tracer.

**Locked / preserved**
- QAM mini-player visual design and transport layout
- Native Shuffle OFF/ON label + perimeter tracer
- Repeat Off / All / One behavior
- Cover Flow and cover positioning
- Artwork ownership, hydration and fallback architecture
- Music queue / Play Next / Add to Queue
- Existing controller spatial navigation model and top-boundary handoff

**Consolidated for RC readiness**
- Read-only RPC retry
- Plex endpoint self-recovery
- Manager top/focus reset on section changes
- Manager section continuity
- QAM page-to-first-card reset
- Readiness diagnostics
- Bootstrap duplicate cleanup

**Next gate**
- If this consolidated build behaves normally in ordinary use, promote the branch to 1.0.0 RC rather than continuing feature churn in 0.9.x.

## 0.9.22 DEV - Native Shuffle + Steam Browser Cursor Repair
- Two-fix-only hardware follow-up.
- Native Decky Shuffle OFF/ON text, no wrapper/sibling label.
- CSS motion-path perimeter tracer with static border fallback.
- Steam browser-native cursor hiding via `HideCursorUntilMouseEvent()`.
- Repeat, queue, Cover Flow, cover position, artwork and navigation locked.
