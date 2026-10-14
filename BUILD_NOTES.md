# ResonaDeck 0.8.4 DEV — Playback Recovery + Live Artwork Binding + GTM Audio Focus

Hardware-unverified. Built from the 0.8.2 hardware evidence on the locked 0.7 GTM Shell / Eli Media Core lineage.

Primary targets:
- recover Books/Podcasts from the 0.8.2 transcode regression;
- bind already-cached and newly-ready Music artwork into visible QAM cards;
- prevent stale cross-media mini-player artwork;
- reuse completed artwork hydration instead of restarting it on every QAM open;
- improve in-game QAM focus continuity;
- add premium Aincrad playback telemetry without reintroducing Web Audio;
- cooperate with Game Theme Music 3.6.8 audio focus without modifying GTM.

Locked behavior preserved:
- Page X of Y;
- horizontal Previous ↔ Next;
- four QAM cards per page;
- categories browse inside QAM;
- plain persistent HTMLAudioElement playback;
- Book Manifests and global audiobook timeline;
- global controller interception remains LB/RB-only.

See `PLAYBACK_ARTWORK_GTM_FOCUS_0.8.4.md` and `VALIDATION_0.8.4_DEV.md`.
