# Quality target (handheld mode)

Decided 2026-10-08. Handheld mode on a Steam Deck OLED is the baseline. TV play is
handled by streaming (Steam Link), not by DeckForge.

## Objective (revised 2026-10-21, docs/decisions/0002-experience-target.md)
1. **Constraint, on what the player sees (frame generation allowed):**
   - **Gold:** locked 35 fps at 70 Hz.
   - **Good enough:** steady 30-35 fps, 1% low >= 28 fps, and real frames' 1% low
     >= 14 fps.
2. **Maximize:** image quality above Fede's quality floors. The defaults are textures
   High, upscaler Performance or better, and frame generation on. Cuts go least
   visible first.
3. **Always reported separately:** real (native) fps. Never call a result native
   when frame generation produced it.

The original objective (locked 45 fps native, frame generation as a separate track)
was dropped after the first real Wilds measurement: 24.8 fps average, GPU-bound.
Sections below describe the longer-term image-scoring and lever plan. Where they
mention 45 fps, read the current constraint above.

## How image quality is scored
- **Reference:** the same scene rendered on the Deck itself at maximum settings and
  native 1280x800, however slowly. "Close to console" = close to that reference.
- **Screen:** per-frame FLIP against the reference.
- **Promotion:** a temporal (video) metric on short clips, because per-frame metrics
  miss upscaler ghosting and flicker.
- **Final call:** Fede's blind A/B on the Deck's own screen. His early verdicts
  calibrate the metric thresholds.

## Why this is plausible (back-of-envelope, to be tested)
PS5 performance mode draws roughly 5-8x more pixels per second than the Deck needs
at ~600p internal / 45 fps, and its GPU is ~6x stronger, so GPU-bound games get a
comparable per-pixel budget. Breaks for CPU-bound games, fixed per-frame costs
(shadow maps, simulation) and heavy ray tracing.

## Levers, in expected order of visual payoff
1. Better reconstruction: FSR 4 INT8 / XeSS from ~540-600p (OptiScaler or
   PROTON_FSR4_UPGRADE). Tier I where injection is needed.
2. Spend on what a 7" screen shows (textures, LOD, draw distance, AA); cut what it
   doesn't (volumetric/shadow resolution, SSR, DOF, motion blur).
3. Frame pacing: 45 fps lock (OLED 90 Hz refresh, 2x frame gen optional).
4. Shader-cache warming to remove stutter.
5. Later: per-pass budget reallocation in the Vulkan layer.

## Test games
| Game | Anti-cheat | Allowed tiers | Role |
|---|---|---|---|
| Monster Hunter Wilds | None (DRM/anti-tamper) | S + I | Full-stack test, heavy CPU+GPU |
| Space Marine 2 | Easy Anti-Cheat | S only | Safe-tier test (owned) |
| Helldivers 2 | nProtect GameGuard (kernel) | S only | Later; mod/injection = ban risk |
