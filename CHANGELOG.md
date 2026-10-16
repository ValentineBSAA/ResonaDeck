## ResonaDeck 1.2.0 STABLE | 2026-10-16

- Promoted the creator-confirmed 1.1.9 Deck test build without changing audio, artwork, or controller behavior.
- Automatic eight-second crossfade and the incoming-vinyl → gold turntable → full-cover transition were both confirmed working by the creator in real Steam Deck playback.
- Prepared stable version metadata, complete plugin ZIP, public documentation and evidence-based verification checklist.
- Other duration/codec edge cases and minor transition polishing remain future validation.

## ResonaDeck 1.1.8 TEST - Automatic Crossfade Trigger

- Hardware finding: manual TEST Crossfade in 1.1.7 works for 8 seconds and two streams; automatic trigger is the defect.
- Favor the actual HTML audio duration and retain Plex metadata as fallback to calculate the impending track end.
- Rearm independent monitoring for every track after a successful audio crossfade.
- Preserve all currently working artwork, Surprise Me settings, Favorites, turntable and vinyl-arrival visual.
- Offline verified only; automatic crossfade on Steam Deck remains an open acceptance test.

## 1.1.6 TEST | 2026-10-15
- Independent crossfade scheduler and earlier Plex prebuffer; metadata-first duration checks; live player crossfade phase badge for diagnosis.
- Small timed UP NEXT artwork preview, nonfocusable, clears at track change; existing art/turntable left alone.
- Source-only and simulation-tested. **User-confirmed 1.1.5 crossfade failure remains unverified on hardware in 1.1.6.**

## 1.1.4 TEST
- Active artwork A/X settings toggle and native focus between artwork and Stop.
- Close settings from a selected preference or Favorites browser with X.
- Fill genuine/fallback music covers in the entire playing-artwork square; idle gold turntable untouched.
- Prepare a silent second music stream ahead of music-only 3/5/8/10-second equal-power crossfade.
- Preserve the 1.1.3 queue, artwork caching, contrast, and library behavior; hardware validation pending.

## 1.1.4 TEST - surprise control toggle, square playback artwork, music crossfade prewarm

- The active music artwork toggles Surprise Me options via X or A; focused settings/Favorites actions also support X close. Added direct Art/Stop focus lane.
- Real/fallback playing music artwork fills a square; the owner's existing gold idle record and its backing are unchanged.
- Music crossfade now plans and preloads the next Plex stream early using a separate audio element, followed by equal-power 3/5/8/10s overlapping playback. Stops and failure cleanup preserved; not verified on Steam Deck yet.
- Carries forward 1.1.3 continuous queue, Favorites browser, dark text contrast and album metadata repair. Includes authoritative updated checklist and plan handoff.

## 1.1.3 TEST - artwork focus, early queue refill and readable album details

- Track refill begins with twelve queued tracks remaining; bounded history keeps an independent continuous-session position so progress does not jump backward after old tracks are trimmed.
- Added focusable normal/fallback artwork when actively playing: A or X opens Surprise Me settings without stopping music. Gold focus, existing cover flow and original turntable remain.
- Dark, high-contrast album Browse Details and X actions while retaining album-themed accent trim; preserve real album title if Plex metadata returns `Unknown collection`.
- Based exclusively on the owner's tested 1.1.2 code. Offline verification passed; real Steam Deck verification remains pending. See `IMPLEMENTATION_CHECKLIST_1.1.3.md`.

## 1.1.2 TEST - continuous listening, Favorites and immediate fallback artwork

- Reworked timed Surprise Me to use actual listening clock (paused time excluded); queue refill now starts at five remaining tracks, supports a one-track Favorites set, album-mode recycling, urgent boundary retries and ignores canceled runs. When a timed goal is met, the active song is allowed to finish.
- Made selected and unselected Surprise Me controls reliably colored within theme-owned glass; added gold selected dot and retained separate controller focus outlines. Replaced clipped CLOSE with icon-only X.
- Added paginated, category-filtered Favorites browser reachable from Surprise Me X settings and integrated into Full Manager.
- Immediately display bundled Music/Audiobook/Podcast fallback art while native art resolves; proactively warm five upcoming queue covers.
- Kept 1.0.8 playback layout and 1.1.1 Plex backend unchanged. Device validation still required. See IMPLEMENTATION_CHECKLIST_1.1.2.md.

## 1.1.1 TEST - Steam Deck discovery theme and continuous listening repair

- New 30-minute, 1-hour, 2-hour, and Keep Playing Surprise Me modes; user-selected 10/20/40-track options are preserved.
- Music duration modes refill upcoming queue in bounded batches until the requested listening duration is covered; no abrupt cutoff mid-song.
- Keep Playing continues selecting songs, with recent-repeat protection and a bounded queue to reduce large-queue lag.
- Source-level warm artwork seeding avoids clearing an already-cached cover between tracks.



- Restored the exact gold vinyl idle housing as the focusable Surprise Me control, fixed card alignment.
- Restyled Surprise Me and Full Manager discovery controls with CSS Loader resistant glass, and moved settings beneath the idle banner.
- No playback engine changes; preserves white-dot fix, Stop and queue behavior.

## 1.1.0 TEST — Discovery, Favorites, Sessions, Playlists, Crossfade
- Clickable original gold turntable: A Surprise Me, X settings, scoped LB/RB category selection.
- Defaults Music / Tracks / Favorites Off / 20 tracks. Categories Music, Audiobooks, Podcasts, More Audio, All.
- Favorites, Shuffle Favorites, saved listening sessions, local playlists persisted per Plex profile in Decky settings.
- Large-queue update optimization, with unchanged navigation and original Stop button.
- Universal sleep timer and optional final 10-second fade.
- Optional music-only 3/5/8/10-second dual-audio crossfade and existing sliding artwork; Off by default.
- TEST build pending real Steam Deck hardware validation. White-dot fix from 1.0.7 kept intact.

## 1.0.8 TEST — Quick Menu Stop Button
- Added compact artwork-tinted STOP in the media label row; no changes to transport rows.
- Uses existing engine stop behavior and controller focus navigation.
- Preserved the 1.0.7 white dot fix and all playback animations.

## 1.0.4 TEST · Full-size turntable and restored visualizer
- The idle record now fills the turntable plate. The ResonaDeck logo occupies the center label, not the entire vinyl surface. Faster 3.6-second rotation with a fixed tonearm and pulsing light.
- Restored the proven v1.0.2 audio visualizer DOM and animation selectors after v1.0.3 froze the keyframed transform.
- The white speck is not yet identified. Do not claim it is fixed; no more speculative player element removal in this build.
- The 2,048 idle messages, live Plex behavior and controller navigation remain unchanged.

## 1.0.3 TEST · Turntable idle emblem and playback speck investigation
- Replaced idle icon ornament with a four-and-a-half-second rotating vinyl deck: entire record and ResonaDeck label move together, illuminated grooves, fixed tonearm, warm pulsing aura.
- Removed tiny decorative status bullet nodes that are rendered only when an active track exists, in the Quick Menu and Full Manager minibar.
- Replaced theme-sensitive italic visualizer bars with explicitly sized spans to eliminate any collapsed single-pixel equalizer fragment while keeping a functioning wave.
- Idle quote JSON pack and playback/controller systems unchanged. White-dot removal is still hardware-pending; user observations implicate active playback, but a photo cannot prove the precise drawing source.

## 1.0.2 TEST · Whole-emblem animation and document-level idle cursor fallback
- Confirmed 2,048 JSON idle messages seed automatically and remain editable without frontend rebuild.
- Entire idle ResonaDeck icon now rotates with layered golden aura; respects visibility and reduced motion.
- Extended cursor suppression to Steam document root and restored it on pointer movement and unmount; actual Steam hardware result remains unverified.
- Player, queue, Full Manager, and 1.0.0 baseline functionality retained.

## 1.0.1 TEST — Idle Listening Lounge (not published stable)

- Quick Menu idle banner retains “Ready to listen” and the category instructions, and adds rotating listening prompts from a **2,048-message offline pack**.
- A quiet gold orbit and subtle glow surround the icon only when playback is idle, with reduced-motion support.
- Message pack is saved under Decky's persistent ResonaDeck settings and reread while idle; text changes do not require rebuilding the frontend.
- Idle cursor fallback now hides stale pointer visuals when stationary and restores them on genuine mouse movement; the decorative eyebrow dot is removed in idle mode.
- No modifications to Plex playback, queued tracks, controller handling, search, or Full Manager navigation.

# Changelog

## 1.0.0 — First Public Release

- Promote the hardware-confirmed ResonaDeck 0.9.50 feature set to stable 1.0.0, with **no new feature or controller-routing changes**.
- Retain the X/secondary-action item menu, 2×2 D-pad navigation, artwork-tinted Quick Menu queue and total-track queue counter.
- Retain Full Manager media routing, album art before playback, library categories, search, audiobooks, stable artwork glass controls, and Shuffle perimeter animation.
- Update visible version, backend/manifest metadata, documentation and release notes for public distribution.
- Keep Quick Menu search removed; Full Manager search remains.

## 0.9.50 TEST: Action Menu Navigation and Queue Count

- Keep the working X / Select item actions and their playback/queue callbacks unchanged.
- Replace the flat 2×2 action layout with explicit nested Steam/Decky focusable rows so **Left/Right** changes columns, **Up/Down** changes rows. Boundary directions stay within the popup; B closes it.
- Show the **total queue size**, including the current track, on the Quick Menu Queue button whether the drawer is open or closed. Show a consistent total-tracks label inside the drawer.
- Retain 0.9.49 idle-player behavior, 0.9.48 artwork-themed queue controls, current Full Manager and all Plex/audio systems.
- Validation: 54 JavaScript/Python regression scripts, including a dedicated two-axis navigation and queue-total test; JS/Python syntax, frontend sync and ZIP integrity. Deck hardware test still required for Steam gamepad focus.

## 0.9.49 TEST: Quick Menu Controller Navigation Repair

- X / secondary or Select / options action on a library item opens a small, artwork-compatible action menu. Music supports Add to Queue and Play Next, albums/artists resolve tracks first; all items support Browse Details or Close. Hold A remains inline preview, tap A still quick plays.
- Queue drawer starts at CLOSE, explicitly navigates header ARTIST / ALBUM / CLOSE and rows, supports B to close, and restores focus to the Queue control.
- Idle player no longer renders dead transport/volume focus controls; Down from profile goes to media tabs when idle.
- Scoped changes to Quick Menu UI; keep the 0.9.48 queue glass and Plex playback engine.
- Hardware confirmation still required for Steam/Decky secondary/options events and gamepad focus.

## 0.9.48 TEST: Queue Glass Consistency

- Quick Menu queue drawer, queue rows, remove buttons, and Artist / Album / Close actions now use their own artwork-tinted glass skins underneath native Decky focusable buttons.
- The active row uses a slightly stronger artwork hue; gold controller focus remains separate from the artwork accent.
- Increased small queue text and touch targets modestly for TV readability.
- Music and audiobook chapter queues share the same glass treatment. Playback and queue actions are unchanged.
- This is a focused visual repair based on a Steam Deck screenshot of a white queue under an otherwise correctly tinted player. Hardware confirmation still required.

## 0.9.47 - Full Manager Artwork and Controller Cleanup (hardware test)

- Reuse a ready artwork URL from the selected item or its other cached display size on detail screens; artwork no longer relies on initiating playback to discover an existing cover. A genuinely uncached image may still need Plex download time.
- Remove Quick Menu search because result navigation could not be reliably tested for right-stick focus and the user prefers a simpler Quick Menu to an awkward search. Full Manager search remains available.
- Return QAM paging controller focus directly to the Full Manager launch control instead of the removed search surface.
- Expand scoped Full Manager glass styling for remaining native utility fields, toggles, controls, and focus indicators without repainting media cards or Quick Menu.
- Internal test build. Real Steam Deck/CSS Loader and Plex artwork validation still required.


## 0.9.46 - Full Manager Reliability Audit (test candidate)
- Corrected audiobook Book/Author/Collection routing to dedicated chapter-and-resume screens instead of generic music child endpoints.
- Added a separate track-details component; track detail requests no longer depend on nonexistent child lists.
- Fixed Now Playing artwork hook order when transitioning from no track to playback.
- Keyed the four library pages to prevent leftover view/library state during LB/RB switching.
- Split artist album lookup from slower all-tracks lookup, so albums can render independently.
- Detail screens return controller focus to their Back control and support B to leave.
- Render audiobook identity/artwork immediately, with a recoverable failure instead of blank waiting.
- Category and paged catalogs now offer controller-selectable Retry actions after Plex errors; stale Search responses cannot overwrite a newer query.
- Home shelves now populate independently rather than waiting for eight Plex requests; Search shows cached results before optional network results.
- Reduced blocking and added an explicit empty-children message.
- Added a Full Manager error boundary with controller-selectable Retry and Home recovery, rather than blanking the whole screen on render errors.
- No changes to QAM playback glass, Shuffle snake or search keyboard.

## 0.9.45 RC - Live Quick Search + Recoverable Details

- Quick Menu: Move built-in controller search to the top, offer two live results after a short typing debounce, auto-collapse on selection; cached index first and Plex fallback.
- Full Manager: correct the detail-page layout; metadata, tracks and related items load independently with bounded waits, fallback and Retry.
- Improve book and author/collection loading with independent prewarming and small parallel batches.
- Dark cover placeholders, fallback when artwork stalls, and reuse already loaded Now Playing art.
- Existing category palettes, playback engine, queue, Shuffle snake and controller focus routing preserved.


## 0.9.44 RC - Audiobook Pager + Quick Menu Search

- Restored CSS Loader-resistant, copper and midnight-blue glass to Audiobooks Previous/Next pagination in catalog, chapters, reading lists and saved book/author collections. Native focus and original paging logic preserved.
- Added a collapsed-by-default Quick Menu Plex search with a built-in, controller-operated keyboard (no Steam keyboard), All/Music/Books/Podcasts/More filters, up to six playable matches, and local Living Library results followed by Plex enrichment.
- Search is explicitly submitted, not automatically requested while typing. Stale results from previous searches are discarded; B closes expanded search.
- Preserves the 0.9.43 library, Quick Menu artwork player, Shuffle snake, gold focus, and existing Plex playback code.
- Full Manager now prewarms metadata for up to six search tracks without blocking search results. Plex streaming/network conditions can still affect start times.
- Made the Full Manager bottom mini-player significantly slimmer; Now Playing details use the recovered space and scroll before handing focus to the mini-player.
- Full Manager retains ordinary/native text entry. The separate built-in keyboard is Quick Menu only.
- Requires hardware validation on Steam Deck with CSS Loader, especially built-in keyboard focus, audiobook paging and detail navigation.


## 0.9.43 RC - Full Manager finishing pass

- Made the Home listening banner a true controller-focusable action. A plays or resumes; Play/Pause and Now Playing remain separate, independently painted glass controls.
- Reworked Search field and scope filters with cool slate/teal glass and per-category colored filter treatments; text uses dark entry surfaces instead of CSS Loader white.
- Styled Plex Library Manager selection rows, role chooser, library overview, and actions as consistent silver/blue glass with visible Steam/Decky focus.
- Removed only the old `rd-v924-nowbar::before` bottom-edge progress indicator, leaving the real artwork-colored timeline and seeking untouched.
- Kept the known-good 0.9.40+ Quick Menu player, category browsing palettes, Plex audio engine, focus routing, and shuffle perimeter animation unchanged.

## 0.9.42
- Full Manager release-candidate polish pass.
- Removed the visible version pill from the Full Manager header to reduce clutter.
- Increased card title and subtitle readability for TV / couch-distance viewing.
- Refined manager tab styling so inactive and active states feel more consistent.
- Slightly rebalanced the Full Manager header layout for breathing room.

## 0.9.42 - Full Manager Glass Unification (release candidate)

- The Full ResonaDeck workspace now follows the 0.9.40 glass design rather than reverting to white native buttons and fields.
- Keeps the artwork-responsive current-player background while styling its position, volume, queue rows and playback controls as cohesive, darker glass.
- Category-specific accents in Music, Books, Podcasts, More; artwork-specific colors remain on individual cards. Search, account, setup, system health and settings use a quieter neutral glass family.
- Open Full ResonaDeck now has a protected colored glass face while retaining Decky navigation.
- Drops the displayed DEV suffix and removes the visible Full Manager version pill. Does not promote the build to public stable before hardware testing.
- Preserves the 0.9.40 QAM player, shuffle snake, in-game navigation and the Plex/media backend.

## 0.9.40 DEV - Unified Glass Library + Shuffle Snake

- Extended the independently painted, CSS Loader-resistant glass treatment to Music, Books, Podcasts and More tabs, library cards, browsing modes, inline previews, and the Full Manager library.
- Kept stable category palettes: indigo/violet for Music, copper/midnight for Books, teal for Podcasts, and rose/plum for More. Neutral slate keeps account controls quiet.
- Added subtle per-cover color accents for individual media cards without recoloring the navigation for every new song.
- Restored the favorite Shuffle border snake as an independent, artwork-colored animated perimeter detail, only while Shuffle is ON. It does not touch Decky focus or input; reduced-motion settings keep the detail still.
- Preserved the 0.9.39 artwork-colored playback panel, working transport buttons, gold controller highlight, and playback/Plex systems.

**Hardware validation still needed**: actual CSS Loader interaction, per-card artwork sampling, legibility on television, and Shuffle snake animation on Steam Deck.

## 0.9.39 DEV - CSS Loader-Resistant Artwork Glass

- Designed around a white CSS Loader Steam theme with orange navigation accents.
- Added a dedicated, internal, artwork-colored glass paint surface inside each Quick Menu transport button. Native Decky DialogButtons remain in place for Steam Input and gamepad focus.
- Paint surfaces use dark and vivid album-derived colors, not white surfaces with weak colored overlays. Each transport has a different color role.
- The restart control retains its enlarged dedicated icon. Long-form transport, queue, and volume use the same isolated color surface.
- The glass skin uses inline important styling on ResonaDeck-owned spans to resist global CSS Loader button backgrounds, while retaining the external gold focus outline. No focus handlers or playback logic were altered.
- Scoped exclusively to ResonaDeck Quick Menu player; it does not recolor Steam UI or other Decky plugins.

**Validation:** See `VALIDATION_0.9.39_DEV.md` for tests and remaining physical Deck/CSS Loader checks.

## 0.9.38 DEV - Album-Themed Transport Controls

- Reworked the playback and mode buttons so the controls themselves are visibly themed from the current artwork palette, not just the player panel behind them.
- Added explicit control-face markup with readable icons and labels for Restart, Shuffle, Repeat, Queue, Previous, Play/Pause, and Next.
- Themed each button role with its own tinted glass mix and accent color derived from the active album palette.
- Gave Restart a clearer icon treatment for couch readability.
- Preserved the stable gold Steam/Decky focus ring without changing button fills during focus movement.
- No media logic, navigation routing, or Plex behavior changes from 0.9.37.

**Validation**: JavaScript syntax, Python syntax, and ZIP integrity verified. Physical Steam Deck / TV appearance still requires real hardware confirmation.

## 0.9.37 DEV - Artwork-Tinted Glass Refinement

- Removed the dominant white layer in 0.9.36 button fills. Controls now use two translucent artwork-tinted gradients and narrow top-edge reflections, with visible album color behind them.
- Made Play/Pause slightly more luminous than surrounding controls without losing the shared palette, and gave volume the same frosted treatment.
- Removed visual transitions/scale on transport buttons and volume to prevent controller-focus flashes or sliding colors. Preserved the gold focus outline and the existing Shuffle tracer animation.
- Excluded the Shuffle button from the new reflection pseudo-element to avoid conflicting with its existing active-border effect.
- Kept the 0.9.35 main player background/palette and 0.9.34 in-game navigation unchanged. No transport, queue, Plex, or other functional changes.

**Validation:** See `VALIDATION_0.9.37_DEV.md`. Real Steam Deck/TV confirmation still needed.

## 0.9.36 DEV - Frosted Glass Controls

- Preserved the 0.9.35 artwork-driven player backgrounds while reintroducing a tinted frosted-glass treatment for playback controls and volume.
- Buttons now use translucent layered fills, soft inner highlights, lighter border edges and backdrop blur so they feel premium and integrated instead of hard white blocks.
- Play/Pause remains the strongest transport action; progress, waveform and volume still use artwork accents; Steam/Decky gold controller focus is preserved for TV readability.
- No navigation, playback, queue, or Plex behavior changes from 0.9.35. This is a visual refinement pass only.

**Validation**: JavaScript syntax, Python syntax, package metadata update, and ZIP integrity verified. Physical Steam Deck / TV appearance still requires real hardware confirmation.

## 0.9.35 DEV - Artwork-Coordinated Player

- Replaced one-color album tinting with a multi-role palette sampled from the actual artwork. The algorithm preserves the most prevalent chromatic hue and, when present, a distinct secondary hue.
- Gave the player a layered deep-to-surface gradient, a restrained blurred-artwork layer, and differentiated secondary accent areas without returning to solid neon fills.
- Coordinated Shuffle, Repeat, Queue, Previous, Play/Pause, Next, and Volume with different related colors. Active states, progress, visualizer, and volume have distinct readable accent roles.
- Retained the independent gold Steam/Decky controller-focus indicator, readable labels, reduced-motion support, inline browse previews, and all four media roles.
- Kept the 0.9.34 native in-game focus routing, playback engine, Plex reconnection and progress systems unchanged.
- Cached analyzed album palettes to reduce flicker when returning to previously played artwork. CORS-restricted/undecodable covers use a neutral fallback.
- Updated plugin.json, package.json, frontend/dist and backend version fallbacks to 0.9.35.

**Validation**: 30 JavaScript regression checks, 11 Python checks, syntax and ZIP audits passed; standalone mini-player component smoke test passed. A Chromium static rendering check confirmed the themed panel and controls have non-flat computed gradients. Actual controller focus and TV appearance require physical Steam Deck validation.

## 0.9.34 DEV - Artwork Palette and QAM Focus Reliability

- Removed the stray PREVIEW SELECTED button/hint from catalog pagination. Hold A, X/secondary and context controls still open album/episode/chapter previews.
- Replaced forced 91%-saturation full-panel blues/reds with artwork-weighted palettes and dark, TV-readable gradients; reduces unrelated tracks looking identical.
- Removed six automatic focus-stealing retries. Uses one native-focus recovery on entry, yields when Steam is already focused in QAM, and never pretends DOM focus is Steam gamepad focus.
- Registers the whole music player as a native Focusable navigation cluster so Steam's QAM traversal can enter/leave it.
- Does not intercept raw game/controller input. True in-game routing requires testing on device and can also depend on Decky/SteamOS.

## 0.9.33 DEV - In-Game Focus Routes and Album Color Visibility

- Respect button-specific D-pad maps rather than guessing positions on the TV. Account DOWN leads into the player Play/Pause action; restart DOWN leads to Previous; failed focus transfers yield to Decky rather than trapping input.
- Stop burying artwork-derived colors under dark gradients and opaque shading. The player now uses a vivid but contrast-limited cover hue across its surface with text-safe opacity.
- Preserves the 0.9.32 media engine, album previews, Plex progress, sleep recovery, and GTM audio coordination.
- Physical Steam Deck validation is still needed for in-game controller ownership and artwork URL sampling.

## 0.9.32 DEV - In-Game Focus Handoff and Visible Artwork Colors

- Stop consuming a D-pad press from the Plex account picker when Steam needs to navigate to the player; release directions if target focus acquisition fails.
- Reinstate the artwork-backed mini-player layer that previous styles hid. Stronger cover-derived background colors are visible across a TV without compromising text and control contrast.
- Keep saturated 255-channel highlights (such as neon blue) during palette sampling; clear stale colors on image failures.
- Preserve earlier playback, Plex progress, album preview, and Decky audio-focus behavior.
- Real Steam Deck in-game verification still required.

## 0.9.31 DEV - In-Game Controller Focus Recovery

- Native Steam focus subtree for Quick Access Menu.
- Bounded controller-focus recovery when opening from a running game or returning after sleep.
- No raw input interception, no playback-engine changes.
- Real Steam Deck testing required; upstream Decky input-routing issue can still prevent all plugin interaction.

## 0.9.30 DEV - Listen First, Browse on Hold

- Quick Menu library cards: press A to play or resume; hold A for ~540 ms to preview album tracks, podcast episodes, audiobook chapters, or individual ASMR recordings.
- Because Decky gamepad A may dispatch only a click event on some builds, the Preview Selected control and secondary button provide an accessible fallback until verified on Steam Deck hardware.
- Album / artist previews stay inside Quick Menu with B/Back and restored focus. Podcasts use Plex item view offsets and saved progress when available; audiobooks retain book-wide bookmarks; More/ASMR resumes individual recordings.
- Music mini-player uses a prominent artwork accent with an animated, readable tint; fallback accent when artwork cannot be sampled.
- Friendly, rotating Plex reconnection text while keeping accurate connection details.
- Full scrollable listening queue opens at the currently playing track or chapter and does not forcibly re-center while the user browses; close returns to its own queue control.
- Inherits 0.9.29 reconnect, paging, multi-library support, Theme Music audio focus and all other stable playback behaviors.

**Hardware validation still required:** hold A interpretation under actual Decky/Steam Input, artwork tint and visual layout on Steam Deck/TV, Plex wake timing, and real Plex bookmark fidelity by library type. Existing automatic tests do not establish those behaviors on physical hardware.

## 0.9.29 DEV - Quality of Life

- Plex server restore checks saved working endpoint first and re-resolves Plex server discovery only when needed.
- Server selection retries in place and no longer requires reopening Decky after a cold start.
- QAM and full manager pagination preserve controller focus on Next/Previous rather than selecting the first card and scrolling upward.
- Select between multiple Plex music libraries with independent catalog caches.
- Music artist details support Plex album selection and track browsing.
- Cache request generation prevents stale page responses from overriding a newer selection.
- Preserves 0.9.28 controller, artwork, audio focus, and playback fundamentals; no data reset.

## 0.9.28 DEV — Controller Recovery
- Reverted the rejected 0.9.27 runtime theme-ownership experiment to the hardware-stable 0.9.26 Full Manager/controller baseline.
- Removed runtime MutationObserver/focus/style reassertion logic that could interfere with Decky spatial navigation.
- Preserved shared QAM/Full Manager version identity and enlarged only the QAM version badge.
- No playback, queue, artwork, shuffle/repeat or page-reset redesign.

## 0.9.26 DEV — Theme Isolation + Version Identity

- Isolated Full Manager native Decky controls from Steam/CSS Loader surface backgrounds while retaining theme-derived focus accent.
- Added one shared runtime version identity to the Full Manager header, Plex profile route and QAM header.
- Tightened the persistent Full Manager player contrast and QAM-style control treatment without changing playback behavior.
- Preserved 0.9.25 user-picker focus containment, B/back hierarchy, page-to-top navigation and playback reliability.
- Advanced all release/runtime/package identifiers to 0.9.26 and retained version-consistency regression coverage.

# ResonaDeck Changelog

## 0.9.25 DEV — Full Manager Refinement

- Corrected the complete release identity chain to 0.9.25 across plugin.json, package.json, frontend runtime, Decky bootstrap, backend fallback version, hardware-evidence build ID, and regression expectations.
- Replaces washed-out Full Manager utility/account controls with darker high-contrast surfaces and stronger text hierarchy.
- Tightens Plex Home user-picker D-pad containment so list navigation does not leak into the persistent player.
- Refines the Full Manager persistent player toward QAM parity with larger artwork, stronger controls, multi-line title/subtitle presentation, and clearer long-form controls.
- Preserves 0.9.24 Back/B hierarchy, page-to-top behavior, account-center structure, and the verified playback/QAM core.

## 0.9.24 DEV — Full Manager Unity

- Rebuilt the Full Manager visual shell around a high-contrast dark cinema surface so account, settings, health, library and playback text no longer inherit washed-out Steam host colors.
- Added a compact QAM-inspired Full Manager player with artwork blur, media-kind eyebrow, full book/title presentation, progress/timing, restart/back/play/forward/Open controls, and playback/format status.
- Added a top-bar Now Playing glance that shows the active book or track title while browsing.
- Audiobooks now prefer the persistent book title and chapter/author context instead of exposing a physical file/chapter title as the primary manager title.
- Rebuilt Account into a card-based Account Center and moved Plex Home user switching inline so the Full Manager no longer has to throw the user into a separate route.
- Added hierarchical B/Cancel behavior: Settings, Health and User Picker return to Account; Account and Now Playing return to the manager; only B from the main manager exits the route.
- Rebuilt the Plex Home user picker styling with larger avatars, readable metadata and explicit Select/PIN affordances.
- Preserves all 0.9.23 playback, artwork, QAM shuffle/repeat, queue, paging/focus, stale-endpoint recovery and session-readiness behavior.

# Changelog

## 0.9.23 DEV — 1.0 Readiness Consolidation
- Preserves the hardware-verified 0.9.22 audio playback, native Shuffle OFF/ON label, perimeter snake tracer, Repeat behavior, Cover Flow and Steam browser cursor repair.
- Adds one bounded retry for read-only frontend RPC calls and startup handshakes without replaying state-changing actions.
- Adds automatic stale Plex endpoint recovery: a failed PMS read re-resolves the selected Plex resource once and retries.
- Adds a public `recover_connection` backend action for diagnostics/recovery paths.
- Makes Full ResonaDeck section changes reset the workspace to the top and focus the new page deterministically.
- Remembers the last manager section across manager remounts while explicit launches can still choose the requested page.
- Makes QAM paging return to the first card after a page change.
- Adds a 1.0 readiness health check and updates hardware evidence build identity.
- Removes duplicate reading-list RPC forwarders from the Decky bootstrap.
- No player redesign, artwork rewrite, queue rewrite, or shuffle/repeat behavior change.

# 0.9.22 DEV Native Shuffle + Steam Browser Cursor Repair - HARDWARE UNVERIFIED

- Restores Shuffle OFF/ON to native Decky raw button text with no wrapper or custom text layer.
- Replaces the SVG Shuffle overlay with a CSS motion-path tracer that follows the rounded button perimeter.
- Keeps a static themed border fallback if motion-path animation is unsupported.
- Replaces CSS cursor hiding and coordinate parking with Steam browser-native `HideCursorUntilMouseEvent()`.
- Leaves Repeat, queue semantics, Cover Flow, cover position, artwork, catalog, and controller behavior unchanged.

## 1.0.5 TEST — Isolated idle turntable geometry
- Replaced the idle turntable's legacy shared artwork/icon CSS classes with dedicated `rd-v105` markup and exact positioning rules.
- Kept the vinyl and small ResonaDeck center label inside one rotating element, with a stationary tonearm reaching the outer grooves; 3.3-second rotation.
- Turntable is dark charcoal with subtle gold accents and glow.
- Restored 1.0.4 playback visualizer implementation is unchanged; no playback controls, Plex network paths, queue, or controller actions were modified.
- **White playback dot still under investigation.** No speculative cursor or artwork changes in this release.
