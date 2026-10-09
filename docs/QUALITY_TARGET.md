# Quality target (handheld mode)

Decided 2026-10-08. Handheld mode on a Steam Deck OLED is the baseline. TV play is
handled by streaming (Steam Link), not by DeckForge.

## Objective
1. **Constraint:** median frame time <= 22.2 ms (45 fps), with a 99th-percentile
   guard set per game after its first profile.
2. **Maximize:** image quality within that budget.
3. **Separate track:** frame generation (lsfg-vk / Lossless Scaling, owned) from a
   45 fps base to 90 Hz on OLED. Logged as "presented fps"; never counted as native.

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
