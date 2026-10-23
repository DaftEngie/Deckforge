# Monster Hunter Wilds: graphics menu → `config.ini` map (draft)

Date: 2026-10-22.

## Sources

- Fede's three photos of the in-game Graphics menu (pages 1–3), taken on his Steam Deck
  OLED in Game Mode.
- His `config.ini` from the 2026-10-21 snapshot
  (`steamapps/common/MonsterHunterWilds/config.ini`, game build 24705561). That snapshot
  had the same upscaler, frame generation, mode and sharpness as the photos.

Line numbers refer to that file. Section `[Graphics]` runs from the top of the file to
about line 116. `[Graphics/FSR3]` is around line 136, and `[Graphics/RayTracing]` around
lines 138–141. A second, older-style section (`[RenderConfig]`, around lines 320–400)
repeats some keys.

## Confidence levels

- **matched:** the menu value and the key value agree, and no other key could be the
  match.
- **likely:** the names and values agree, but more than one key could be involved.
- **unknown:** no confident match yet.
- **conflict:** the menu and the file disagree.

Nothing here has been tested by changing a value. Before DeckForge writes any key, it
must be confirmed by changing that one option in the menu and diffing the file. That is
step 2's spec.

## Page 1

| Menu option | Menu value | Key (line) | File value | Confidence |
|---|---|---|---|---|
| Upscaling | AMD FSR | `Algorithm` (6) | FSR3 | matched |
| Frame Generation | Disable | `AlgorithmFG` (7) | NONE | matched (in the 2026-10-21 18:56 snapshot it was FSR3 while frame gen was on) |
| Upscaling Mode | Balanced | `Quality` (71) | Balanced | matched |
| Upscaling Sharpness | 0.65 | `[Graphics/FSR3] Sharpness` (136) | 0.65 | matched |
| Anti-Aliasing | Off (greyed out by FSR) | `AntiAliasing` (9) | NONE | likely |
| Render Scaling | 100 (greyed out) | `ImageQualityRate` (51) | 1 | likely (1 = 100%) |
| Ray Tracing | Off | `[Graphics/RayTracing] Enable` (139) | False | likely |
| Texture Quality | High | `StreamingTextureQuality` (100) | HIGH | likely (several texture-streaming keys exist) |
| Texture Filtering Quality | Lowest (Bilinear) | `SamplerQuality` (78) | Bilinear | matched |
| Mesh Quality | High | `MeshCullingSetting` (59) or `ResourceOption` (72) | HIGH / High | unknown: two candidates |
| Fur Quality | High | `UseLowShellFur` (105) | False | likely |
| Graphics Settings | Custom | not found | | unknown |
| Cutscene Graphics | Do Not Adjust Separately | not found | | unknown |

## Page 2

| Menu option | Menu value | Key (line) | File value | Confidence |
|---|---|---|---|---|
| Sky/Cloud Quality | Low | not found | | unknown |
| Grass/Tree Quality | Low | not found | | unknown |
| Grass/Tree Sway | Disable | `SpeedTreeWind_Branch` (91), `_Global` (92), `_Leaf` (93) | 0 | likely |
| Foliage Density | Lowest | not found (perhaps `GlobalDensity` or `DensityCulling*`) | | unknown |
| Foliage and Snow Collision | Off | `GrassPushCollision` (43) | False | likely |
| Wind Simulation Quality | Off | `WindSimulationQuality` (115) | OFF | matched |
| Surface Quality | High | `GroundQuality` (44) | HIGH | likely |
| Sand/Snow Quality | High | not found | | unknown |
| Water Effects | Disable | `UseLowWaterSimulation` (106) | True | likely |
| Distortion Effects | Enable | not found | | unknown |
| Render Distance | Low | not found | | unknown |
| Shadow Quality | Lowest | `ShadowQuality` (85) | LOWEST | matched |
| Distant Shadow Quality | Low | not found | | unknown |
| Shadow Distance | Medium | `ShadowCastDistanceType` (81) | MIDDLE | likely |

## Page 3

| Menu option | Menu value | Key (line) | File value | Confidence |
|---|---|---|---|---|
| Ambient Light Quality | Low | `GIQuality` (37) | LOW | likely |
| Contact Shadows | Disable | `ContactShadowSetting` (20) | OFF | matched |
| Ambient Occlusion | **High** | `AOSetting` (5) | **LOW** | **conflict**: the menu says High, the file says LOW. AO may live elsewhere; to resolve. |
| Bloom | Low | `Bloom_Enable` (12) + `Bloom_ReductionLevel` (13) | True / 2 | likely |
| Motion Blur | On | `MotionBlur_Enable` (63) | True | matched |
| Vignette Effect | On | not found | | unknown |
| Screen Space Reflection | Off | `SSR_Enable` (76) | False | matched |
| SSSS Scattering | Off | `SSSSS_Enable` (77) | False | matched |
| Depth of Field | On | `DOF_Enable` (21) | True | matched |
| Volumetric Fog | Lowest | `VolumetricFogControl_*` (111, 113) | True / W54xH30xD32 | likely |
| Variable Rate Shading | Off (greyed out) | `VRSSetting` (108) | Off | matched |

## Totals

13 matched, 13 likely, 11 unknown, 1 conflict (38 menu options).

## Notes for the profile work

- **VRAM:** the menu estimates 3.99 of 6.00 GB, so textures at High are affordable.
- **Settings still above Low:**
  - Ambient Occlusion High;
  - Mesh, Fur, Surface and Sand/Snow High;
  - Shadow Distance Medium;
  - Motion Blur, Depth of Field, Vignette and Distortion on.

  These are the first candidates for "least visible first" cuts, once each one's cost is
  measured.
- **Variable Rate Shading is greyed out** with FSR on. It is probably unavailable with
  this upscaler, so run B's "turn on VRS" may not be possible as planned.
