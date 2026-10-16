# 1.2.0 release completion checklist

This branch stages documentation only until the **complete 1.2.0 source** has been synchronized with the **creator-tested 1.1.9** stable package.

- [x] Stable ZIP built locally and archive integrity verified.
- [x] Manifest identifiers switched to 1.2.0; src and dist kept byte-identical.
- [x] Release notes, README copy, evidence-based feature checklist prepared.
- [ ] Synchronize actual updated plugin source, compiled frontend, backend, assets, tests and public docs with this branch. Do not merge or tag while main still contains the earlier 1.0.0 implementation.
- [ ] Verify GitHub source exactly corresponds to the full 1.2.0 stable ZIP.
- [ ] Create GitHub release/tag `1.2.0` pointing to the synchronized commit.
- [ ] Upload `ResonaDeck-1.2.0-Stable.zip` as a **Release asset**, not merely an attachment in an issue.
- [ ] Verify release asset SHA-256: `e65c10c0fccfa0f3e4128afd7ee0d846ef4df89a3049f83269005a0be32b1c37`.
- [ ] Confirm public README install/download links work.
- [ ] Keep 1.0.0 release intact; it is an independent previous release.

**Connector limitation:** This integration can create/update repository files and PRs, but currently lacks a Release creation and binary asset-upload action. A browser/Work session or authorized workflow is required to finish those GitHub release steps. Avoid claiming the release is live beforehand.
