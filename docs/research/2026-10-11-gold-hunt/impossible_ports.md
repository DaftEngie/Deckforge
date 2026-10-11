# How studios make "impossible ports", and which of their tricks an outside tool can apply on a Steam Deck OLED

Research is current to 2026-10-11. Each finding carries its date.

**How to read the labels:**
- **[measured]** means the number comes from a frame-rate or resolution analysis, such as Digital Foundry or Phoronix.
- **[claimed]** means a developer or modder stated it.
- **[inference]** is my own reasoning.

**Source caveat:** Eurogamer/Digital Foundry pages are blocked to my fetch tool. Most DF findings below therefore come from accurate secondary summaries (Nintendo Life, NintendoEveryThing, PureXbox and others), not from the DF articles themselves.

**Overlap with existing project docs:** the Deck Forge project docs already cover forced VRS, the Wilds REFramework bundle and Space Marine 2's Tier-S limits (`claude/deckforge-research.md`, `claude/deckforge-native-quality-rethink.md`). The findings below agree with them and add the porting-technique catalog plus a few new levers, marked NEW.

---

## 1. What real low-end ports cut, port by port

### Takeaway
Every port cut internal resolution hard and then reconstructed the image. On Switch 2 in handheld mode, that means rendering at 360–540p and upscaling with DLSS.

On top of resolution, ports removed or reduced:
- ambient occlusion (AO), global illumination (GI), volumetrics and screen-space reflections (SSR);
- shadow quality;
- foliage, draw distance and textures.

The biggest original-hardware wins came from **rewriting algorithms** (Witcher 3's grass and sun-shadow systems) and from **quarter-resolution transparency and depth-of-field** (Doom 2016). Neither is a settings change.

### Cited Findings

**Doom 2016 on Switch (Panic Button), DF, 2017, [measured]**
- Adaptive resolution, typically about 600p docked; portable can drop to about 576p or lower — [NintendoEveryThing summary of DF](http://nintendoeverything.com/doom-switch-tech-analysis/)
- **The depth-of-field buffer and alpha (transparent) effects render at quarter resolution** — [same](http://nintendoeverything.com/doom-switch-tech-analysis/)
- Reduced texture quality, toned-down lighting and AO, no SSR — [same](http://nintendoeverything.com/doom-switch-tech-analysis/)
- Frame rate falls as enemy count rises, which points to CPU or draw-call limits — [same](http://nintendoeverything.com/doom-switch-tech-analysis/)

**Doom Eternal on Switch, DF, January 2021, [measured]**
- Dynamic resolution: 720p down to 540p docked, 612p down to 360p handheld; "near locked 30 fps" — [My Nintendo News summary of DF](https://mynintendonews.com/2021/01/17/digital-foundry-doom-eternal-docked-is-720p-540p-handheld-612p-360p-and-30fps/)
- The port "exhibits many of the same sacrifices as its prior ports" (the Wolfenstein II port, for example) — [same](https://mynintendonews.com/2021/01/17/digital-foundry-doom-eternal-docked-is-720p-540p-handheld-612p-360p-and-30fps/)
- Panic Button lead engineer Travis Archer said cutscenes run at **20 fps so they can use a higher resolution**, because "it doesn't impact your ability to fluidly move around" — [Nintendo Life](https://www.nintendolife.com/news/2021/02/panic_button_explains_why_doom_eternals_cutscenes_run_at_20fps_on_switch)
- I found no Wolfenstein II-specific numbers.

**The Witcher 3 on Switch (Saber Interactive, which also built Space Marine 2's Swarm engine), interview December 2019, [claimed]**
- The first pass ran at **10 fps**, used **150% of the Switch's RAM**, and was **20 GB over the largest cartridge size** — [Destructoid, reporting the GamesBeat interview](https://www.destructoid.com/the-witcher-3s-switch-port-started-in-super-rough-shape/)
- First Saber tried settings cuts: removed dynamic shadowed lights and SSAO and **cut NPC count 30%**. The game "felt too empty", so they reverted those cuts and optimized elsewhere — [same](https://www.destructoid.com/the-witcher-3s-switch-port-started-in-super-rough-shape/)
- Structural fixes: they changed how the engine computes **sun shadows**. Foliage is about 50% of the visuals, and Saber "rewrote the algorithm for how grass is generated and rendered" — [same](https://www.destructoid.com/the-witcher-3s-switch-port-started-in-super-rough-shape/)
- The shipped game runs at 720p docked and 540p handheld, with blurrier textures, reduced draw distance and visible pop-in. Decapitations, dynamic lighting and water ripples were kept — [EGM](https://egmnow.com/the-switcher-how-saber-interactive-took-one-of-the-biggest-games-ever-portable/)

**Hogwarts Legacy on Switch 1, DF, November 2023, [measured]**
- 720p docked, 576p handheld; 30 fps peak, frequent drops to the low or mid 20s — [GoNintendo summary of DF](https://gonintendo.com/contents/28866-digital-foundry-dives-deep-into-hogwarts-legacy-on-switch)
- AO and other real-time lighting removed; outdoor shadows reduced
- Fewer trees, shorter draw distance, many environment objects simplified or removed
- **Outdoor NPC animations reduced**
- **Loading screens added** inside the open world: about 15 s in some areas, up to about 40 s in others

**Hogwarts Legacy on Switch 2, DF, May 2025, pre-release build**
- Locked 30 fps with DLSS (reported output 1440p docked, 1080p handheld; internal resolution lower)
- Assets less detailed than on Series S; level layouts more open than last-gen but less than current-gen — [Multiplayer.it summary of DF](https://multiplayer.it/notizie/hogwarts-legacy-analizzato-in-video-su-nintendo-switch-2-a-confronto-con-switch-1-xbox-series-s-e-ps4.html)

**Cyberpunk 2077 on Switch 2, DF, 2025, [measured]**
- Resolution ranges, all with DLSS:

  | Mode | Docked | Portable |
  |---|---|---|
  | Quality | 720p–1080p | 450p–810p |
  | Performance | 540p–1080p, targeting 40 fps | 360p–720p |

  Source: [NintendoEveryThing summary of DF](https://nintendoeverything.com/cyberpunk-2077-switch-2-frame-rate-resolution/)
- Texture quality matches PS5. NPC and vehicle density matches PS4. Outdoor shadows are a step back. Mirror reflections lose clarity in Performance mode — [same](https://nintendoeverything.com/cyberpunk-2077-switch-2-frame-rate-resolution/)
- CDPR [claimed]: engine-level changes were needed and shaders were converted from HLSL to GLSL. Fast storage, more RAM and DLSS are what put it above PS4. The target is "30fps everywhere" — [GamingBolt](https://gamingbolt.com/cd-projekt-red-vp-of-technology-believes-switch-2s-faster-storage-ram-and-dlss-make-it-better-than-ps4-xbox-one)

**Capcom RE Engine on Switch 2, [measured]**
- **Street Fighter 6** (2025): 960×540 internal docked and **640×360 handheld**, both with DLSS; 60 fps in fights; World Tour unlocked between 30 and 60 fps — [NintendoEveryThing summary of DF](https://nintendoeverything.com/street-fighter-6-frame-rate-resolution/). Cut versus PS5 and Series S:
  - subsurface scattering, muscle deformation, depth of field;
  - the optional "crowded" NPC density (standard density only);
  - shadow quality reduced;
  - physics particles no longer interactive;
  - SSR removed;
  - in handheld only: AO dropped, lower lighting quality, volumetric haze and fog removed.
- **Resident Evil Requiem** (February 2026): 540p native docked and **360p handheld** with DLSS, unlocked frame rate (about 30 docked, 20s handheld). No ray tracing; lower-quality hair; less detailed character models than Series S — [PureXbox](https://www.purexbox.com/news/2026/02/digital-foundry-compares-resident-evil-requiem-on-switch-2-and-xbox-series-s-with-mixed-results); [Nintendo Wire](https://nintendowire.com/news/2026/02/26/resident-evil-requiem-one-of-the-best-ports-on-the-switch-2-says-digital-foundry/)

**RE Engine on iPhone 15 Pro: RE Village, October 2023, [claimed or reviewer-measured]**
- The game exposes PC-like graphics settings plus MetalFX Quality and Performance modes
- About 60 fps at 2340×1080 output; it shows about 6 GB of available video memory — [Wccftech](https://wccftech.com/resident-evil-village-for-iphone-15-pro-offers-pc-graphics-settings/)

**Death Stranding on iPhone 15 Pro, DF, February 2024, [measured]**
- Dynamic resolution averaging **about 400p**, no MetalFX, 30 fps target with drops — [Multiplayer.it summary of DF](https://multiplayer.it/notizie/death-stranding-iphone-15-pro-analisi-digital-foundry-video-confronto.html)

**Assassin's Creed Mirage on iPhone, June 2024**
- Ubisoft gave no technical specifics beyond "Metal API & MetalFX upscaling are core technologies" — [TouchArcade interview](https://toucharcade.com/2024/06/24/assassins-creed-mirage-iphone-interview-ubisoft-sofia-producer-controller-support-touch-controls-uncapped-frame-rate-ipad-m1-metalfx/)

**Xbox Series S, January 2026**
- In AC Shadows, ray-traced GI was removed on lower-spec versions apart from one hideout zone. Ubisoft's Nicolas Lopez: "we were very short on memory" — [PureXbox, citing DF](https://purexbox.com/news/2026/01/assassins-creed-shadows-almost-had-full-ray-tracing-on-xbox-series-s-but-its-ram-caused-issues)

### Inferences
- The common pattern has three steps:
  1. Internal resolution at roughly 25–45% of the output's pixel count, plus temporal reconstruction.
  2. Remove the "second-order" lighting: AO, GI, volumetrics, SSR, subsurface scattering, depth of field.
  3. Trim shadows, foliage, draw distance and textures.

  Steps 1 and 2 map well onto menu settings in modern PC builds. Step 3's best wins (Saber's grass and shadow rewrites, id's quarter-res alpha) are engine work, route (e).
- Witcher 3 is the clearest evidence that density cuts alone degrade the game noticeably: Saber undid a 30% NPC cut because the world felt empty. For crowd-heavy games, a tool should treat density as a last resort.
- Switch 2 handheld ports ship at **360p internal** in RE Engine titles. That suggests the Deck's 800p output can tolerate an internal resolution of about 400–530p, which is FSR Performance to Quality territory. The catch: DF judged DLSS at 540p better than Series S at native 720p, so the reconstruction method matters as much as the pixel count.

### Gaps
- I could not read DF's Eurogamer articles (blocked), DF's Panic Button/id interviews (2017 and 2021), or any GDC Vault talk about the Doom Switch port. I found no evidence such a GDC talk exists.
- No per-technique frame-time costs (in milliseconds) were found for any port. All the "what was cut" lists are qualitative.
- No technical detail for AC Mirage on iPhone. No Wolfenstein II specifics. Death Stranding's specific cuts are not listed.
- No CEDEC or WWDC RE Engine talk text was retrieved.

---

## 2. Which techniques gave the biggest wins, with numbers

### Takeaway
The few hard numbers that exist are these:
- Witcher 3 went from 10 fps to about 30 fps through algorithm rewrites plus memory and storage work, not settings.
- On RDNA2, forced 2×2 variable-rate shading (VRS: shading fewer pixels and reusing the result for neighbors) gave "upwards of 30%" in some games on desktop GPUs.
- Monster Hunter Wilds' January 2026 PC patch raised minimum fps about 8–20%.

The ports' other big wins are resolution and lighting removal, but no source gives their cost in milliseconds.

### Cited Findings
- Witcher 3 Switch: 10 fps first pass → shipped at 30 fps (EGM says Saber's "key concern" was "a solid frame rate") after rewriting the grass and sun-shadow systems [claimed] — [Destructoid](https://www.destructoid.com/the-witcher-3s-switch-port-started-in-super-rough-shape/); [EGM](https://egmnow.com/the-switcher-how-saber-interactive-took-one-of-the-biggest-games-ever-portable/)
- Mesa's RADV driver (the Deck's Vulkan driver) `RADV_FORCE_VRS=2x2` gave "upwards of 30%" on RDNA2 [measured on desktop RX 6000 cards, April 2021] — [Phoronix](https://www.phoronix.com/news/RADV-Render-Less)
  - Phoronix's benchmark review saw "little quality loss" at 2×2 (games tested: Batman, DiRT Rally 2, F1 2017, Hitman 2, Tomb Raider, Talos Principle, Total War) — [Phoronix review](https://www.phoronix.com/review/radeon-radv-vrs)
- Marek Olšák (Valve) reworked RADV's VRS code for Mesa 26.2 (August 2026). It "can double performance" in some cases, "mainly benefits VKD3D" (DirectX 12 games under Proton), and needs flat-shading fragment shaders [claimed, edge cases] — [Phoronix, July 2026](https://phoronix.com/news/Marek-Double-VRS-RADV-Perf)
- Monster Hunter Wilds' January 2026 PC patch (shader-compilation and texture-streaming optimizations) [measured by Daniel Owen, desktop]:
  - minimum fps about +8% versus Title Update 4, about +20% versus Title Update 3;
  - on the Deck, "roughly playable at ~30 FPS" with FSR or XeSS upscaling.

  Source: [Notebookcheck](https://www.notebookcheck.net/Monster-Hunter-Wilds-fixes-DLC-bug-greatly-reduces-FPS-drops-and-runs-at-30-FPS-on-Steam-Deck.1215270.0.html)
- Wilds Deck mod bundle [claimed, unmeasured]: for the community "Lite Environment - OGU" mod, the bundle author says turning off GI and volumetric fog gives "significant gains" and turning off wind simulation is "likely a few frames". Foliage LOD 2–3 gives "a couple more frames". The whole bundle gives 30–45 fps at reduced resolution — [Nexus mod 183](https://nexusmods.com/monsterhunterwilds/mods/183)

### Inferences
- The likely ranking by gain is: internal resolution > removing GI, volumetrics and AO > coarse shading (VRS) > shadows > foliage and LOD > textures (mostly a memory issue) > animation and physics rate. The last two matter only when the game is CPU-bound. This ranking is an inference from the port cut-lists, not a measurement.
- On the Deck's shared 102 GB/s memory bus, techniques that cut bandwidth (lower-resolution render targets, lower texture mips, fewer full-screen passes) probably beat techniques that cut shader math alone (inference).

### Gaps
- No Deck-specific measurement of forced VRS in Wilds or Space Marine 2. Experiment E2 in `deckforge-research.md` is still open.
- No published per-setting millisecond costs for RE Engine or the Swarm engine.

---

## 3. Steam Deck optimization patches and Valve guidance: what is user-reachable

### Takeaway
Most Deck patches do two things:
1. Add or adjust a **Deck default preset** and new low-end settings. These land as ordinary menu or config settings, route (a).
2. Fix memory, crash and engine issues, route (e).

Valve's guidance allows hardware-specific defaults but discourages locking settings to hardware. **NEW:** Steamworks SDK 1.65 (July 2026) adds a per-hardware default-config mechanism. **NEW:** Space Marine 2 reads the `SteamDeck=1` environment variable to force Low settings and a 30 fps cap.

### Cited Findings
- Valve: "providing default graphics options for specific hardware (like Steam Deck) is fine", but "we recommend against restricting access to settings based on specific hardware". Settings should be saved per device and not synced through the cloud. Valve recommends Vulkan for performance and battery, and notes Proton's DirectX-to-Vulkan translation may beat a custom Vulkan path — [Steamworks hardware recommendations](https://partner.steamgames.com/doc/steamhardware/recommendations)
- **Steamworks SDK 1.65 (24 July 2026)** — [GamingOnLinux](https://www.gamingonlinux.com/2026/07/valves-steamworks-sdk-v1-65-brings-changes-for-steam-machine-steam-frame-and-steam-deck/page=1/):
  - Removes `ISteamUtils::IsRunningOnSteamDeck()`.
  - Adds `IsRunningOnSteamHardware()` (for analytics only) and `IsRunningUnderProton()`.
  - Adds `GetSteamHardwareDefaultConfig()` to "help choose default game settings (video and other) that you have tuned for specific Steam hardware". It "enables changing your default game settings on future Steam hardware without needing to recompile".
  - Adds `SetGamePerformanceSetting()` and `SetGameRenderResolution()` so games can report their settings to Steam.
- **Space Marine 2** (Update 5.0, December 2024):
  - Desktop Linux players need the launch option `SteamDeck=1 %command%` for online play. It "forces Low settings and a 30 FPS limit".
  - Update 5.0 added FSR 3.1 and frame generation; no Deck-specific preset from Saber is described.

  Source: [GamingOnLinux](https://www.gamingonlinux.com/2024/12/space-marine-2-adds-dlss3-fsr3-and-frame-generation-more-playable-on-steam-deck-needs-launch-option-for-desktop-linux/page=1/)
- **Space Marine 2 community Deck settings** (September 2024): 800p with FSR 2; Low textures, shadows, volumetrics, effects, details and cloth; SSR off ("very GPU heavy"); 30 fps cap at 15 W; about 20–30 fps, low 20s in big battles [reviewer-measured] — [The Backdash](https://www.thebackdash.com/tech/space-marine-2-steam-deck-settings)
- **The Last of Us Part I** Deck-Verified patch (June 2023) — [GamingOnLinux](https://www.gamingonlinux.com/2023/06/the-last-of-us-part-i-upgraded-and-now-steam-deck-verified/page=1/):
  - added a **Very Low preset**, an **AI quality** setting and a **dynamic light quality** setting;
  - Effects Density now defaults to Very Low;
  - fixed a memory leak;
  - RAM spikes to about 14.1 GB remained in some areas.
- **Cyberpunk 2077 Steam Deck preset** (March 2022) shipped broken: it behaved like Ultra or whatever preset was last selected, with FSR Balanced. CDPR fixed it in September 2022 — [GamingOnLinux](https://www.gamingonlinux.com/2022/03/cyberpunk-2077-gets-an-official-steam-deck-setting-but-seems-broken)
- **Marvel's Spider-Man 2** (May 2025): Nixxes changed rendering and the default preset for the Deck and regained Verified status. No settings detail was published in the summary — [SteamDeckHQ](https://steamdeckhq.com/news/marvels-spider-man-2-performance-improvements-steam-deck/)
- **Satisfactory 1.1.1.7** (November 2025): Deck-only default presets (Quality and Performance), larger UI defaults, and a spline-collision refactor that cuts RAM use — [GamingOnLinux](https://gamingonlinux.com/2025/11/satisfactory-gets-optimizations-and-improved-steam-deck-support-in-patch-1-1-1-7)

### Inferences
- **Reachable by a user or tool:**
  - Anything a Deck preset sets lands in the game's settings file, route (a).
  - The `SteamDeck=1` variable is set by SteamOS on a Deck and can be set manually as a launch option, route (d). DeckForge can treat "what the game does on a Deck by default" as a baseline and read it from the settings file after first launch.
- **Not reachable:** Deck-only rendering changes (Spider-Man 2), memory-leak fixes and new settings that don't exist in the binary. These are route (e).
- `GetSteamHardwareDefaultConfig` suggests per-hardware defaults may live outside the game binary. Whether a user can read or override them is unknown; the wording is Valve's and no format is documented.

### Gaps
- Whether Monster Hunter Wilds checks for the Deck (through the environment variable or Steam's API) and applies Deck defaults is undocumented.
- The data format and user visibility of `GetSteamHardwareDefaultConfig` are unknown.
- I did not fetch Valve's Deck-compatibility review criteria page in this pass. The project doc cites "30 fps at 800p on default settings" from it.

---

## 4. Animation and simulation rate reduction for distant objects

### Takeaway
In Unreal Engine this is real and documented. There is per-component **Update Rate Optimizations (URO)** and the **Animation Budget Allocator** with `a.Budget.*` console variables. But the budget allocator only works if the game shipped with the plugin and budgeted components. I found **no equivalent knob for RE Engine or the Swarm engine**.

Hogwarts Legacy on Switch is a port that visibly reduced NPC animation.

### Cited Findings
- **UE Animation Budget Allocator** — [Epic docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-budget-allocator-in-unreal-engine):
  - It lowers update rate and interpolates for less significant skeletal meshes and can stop them ticking. Key variables:
    - `a.Budget.Enabled`
    - `a.Budget.BudgetMs` (default 1.0 ms)
    - `a.Budget.MaxTickRate` (default 10)
    - `a.Budget.InterpolationMaxRate` (default 6)
    - `a.Budget.Debug.Force` / `.Force.Rate` / `.Force.Interp`
    - `a.Budget.MinQuality`
  - Projects can scale `a.Budget.BudgetMs` per View Distance Quality level in `DefaultScalability.ini` (1.0 / 1.5 / 2.0 / 2.5).
  - **It is opt-in:** the plugin must be enabled, characters must use `USkeletalMeshComponentBudgeted`, and Blueprints must call Enable Animation Budget. Registering a mesh disables URO for that mesh.
- **UE URO** — [Unreal forum](https://forums.unrealengine.com/t/animation-frameskip-skeletalmesh/432638); [Epic API docs](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/FAnimUpdateRateParameters):
  - Turned on per component with `bEnableUpdateRateOptimizations`.
  - `FAnimUpdateRateParameters` sets screen-size thresholds for frame skipping (`BaseVisibleDistanceFactorThesholds`), the off-screen rate (`BaseNonRenderedUpdateRate`, for example 4) and `MaxEvalRateForInterpolation`.
- Hogwarts Legacy on Switch 1 reduced outdoor NPC animation [measured, qualitative] — [GoNintendo summary of DF](https://gonintendo.com/contents/28866-digital-foundry-dives-deep-into-hogwarts-legacy-on-switch)
- Wilds: the Lite Environment OGU mod can disable **wind simulation**; Space Marine 2 exposes a **cloth simulation** setting in its menu — [Nexus mod 183](https://nexusmods.com/monsterhunterwilds/mods/183); [The Backdash](https://www.thebackdash.com/tech/space-marine-2-steam-deck-settings)
- Saber's Swarm engine: developers tested 100,000 animated simple AIs and shipped "hundreds, if not thousands" of Tyranids. **No public description of its animation level-of-detail scheme** — [Creative Bloq](https://www.creativebloq.com/3d/video-game-design/warhammer-40-000-space-marine-2-almost-had-100k-enemies-on-screen); [TheGamer](https://www.thegamer.com/warhammer-40k-space-marine-2-lots-of-enemies-on-screen/)

### Inferences
- In UE games, `a.Budget.*` variables set through `Engine.ini` only help titles that already use the allocator. For other UE titles, URO frame skipping depends on per-component flags the game author set. A third party can sometimes force a rate (`a.Budget.Debug.Force.Rate`, route b), but only if the game uses the allocator.
- From memory of UE source code, `a.URO.ForceAnimRate`, `a.URO.ForceInterpolation`, `a.URO.Enable` and `a.URO.Draw` exist as console variables. I could not verify them in any public doc, so treat them as unverified.
- In RE Engine, a REFramework script could in principle throttle motion or physics components (route b, Wilds only). I found **no precedent** for this. Space Marine 2's horde animation is route (e): engine source plus anti-cheat.

### Gaps
- No public `a.URO.*` documentation was found.
- No RE Engine animation-LOD setting or REFramework animation-throttle script was found.
- No Swarm-engine technical talk was found.

---

## 5. Overdraw and particles at reduced resolution: is there precedent for forcing it externally?

### Takeaway
Ports do this. Doom 2016 on Switch renders alpha effects and depth of field at **quarter resolution**. Externally, the only documented route is UE's console variable `r.SeparateTranslucencyScreenPercentage`, route (b), and it causes known artifacts.

A general "render particles at half resolution" Vulkan layer has **no precedent** that I found. The closest practical external levers are driver-forced coarse shading (RADV VRS), which lowers shading cost but not overdraw or blending bandwidth, and texture LOD bias (DXVK, D3D9/11 games only).

### Cited Findings
- Doom 2016 on Switch: depth-of-field buffer and alpha effects at quarter resolution [measured] — [NintendoEveryThing summary of DF](http://nintendoeverything.com/doom-switch-tech-analysis/)
- UE `r.SeparateTranslucencyScreenPercentage` renders separate translucency into a downsampled buffer (a 50% repro shown). Known artifacts: materials using world-position UVs "swim", and depth-fade behaves differently (UE 4.11 era, bug UE-30267) — [Unreal forum](https://forums.unrealengine.com/t/r-separatetranslucencyscreenpercentage-bug-with-worldposition-as-uvs/355046)
- UE scalability groups also expose `r.DetailMode`, `r.RefractionQuality`, `r.SSR`, `r.TranslucencyLightingVolumeDim` (Effects), `foliage.DensityScale` / `grass.DensityScale` (Foliage), `r.Shadow.CSM.MaxCascades` / `r.Shadow.MaxResolution` (Shadows), `r.Streaming.MipBias` / `r.Streaming.PoolSize` (Textures), `r.ViewDistanceScale` and `r.SkeletalMeshLODBias` — [Epic scalability reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/scalability-reference-for-unreal-engine)
- RADV `RADV_FORCE_VRS`:
  - forces per-pipeline VRS rates (2x2, 1x2, 2x1, 1x1) on RDNA2 and newer;
  - is "only forced for pipelines that don't explicitly use VRS or flat shading" and is documented as "Only for testing purposes".

  `RADV_FORCE_VRS_CONFIG_FILE` does the same from a file and "only affects GFX10.3 APUs", which is the Deck's chip class. Source: [Mesa envvars.rst](https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/docs/envvars.rst). The file variant applies changes immediately and was written by Valve's Samuel Pitoiset for Deck power savings (Mesa 22.1, 2022) — [Phoronix](https://www.phoronix.com/news/RADV-Dynamic-VRS-Lands)
- RADV `RADV_TEX_ANISO` forces anisotropic filtering, up to 16 — [Mesa envvars.rst](https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/docs/envvars.rst)
- **NEW, DXVK** (DirectX 9–11 only):
  - `d3d11.samplerLodBias` / `d3d9.samplerLodBias` add an offset from −2.0 to 1.0 to every sampler's mip bias ("Positive values will reduce texture detail");
  - `clampNegativeLodBias` and `samplerAnisotropy` are also available;
  - `forceSampleRateShading` works in the opposite direction (more cost).

  Source: [dxvk.conf](https://raw.githubusercontent.com/doitsujin/dxvk/master/dxvk.conf)
- **NEW, vkd3d-proton** (DirectX 12): the README lists **no sampler LOD-bias or anisotropy override**. Relevant knobs are:
  - `VKD3D_CONFIG=single_queue` ("Do not use asynchronous compute or transfer queues"), which effectively turns async compute off from outside;
  - `VKD3D_FRAME_RATE` (a frame limiter);
  - `VKD3D_SWAPCHAIN_PRESENT_MODE`.

  Source: [vkd3d-proton README](https://raw.githubusercontent.com/HansKristian-Work/vkd3d-proton/master/README.md)
- **NEW, Space Marine 2 is DirectX 12-only** ("DirectX: Version 12"), so it runs through vkd3d-proton — [Saber support](https://support.saber.games/hc/en/warhammer-40-000-space-marine-2/articles/warhammer-40-000-space-marine-2-pc-system-requirements-3)

### Inferences
- A true external half-res particle pass would mean finding the particle draws, redirecting them to a smaller render target with a downsampled depth buffer, then upsampling and compositing. That is fragile across game patches and is Tier I (injection). No precedent was found.
- Per-pass VRS, set only on particle, volumetric and blur pipelines through a Vulkan layer, is the practical substitute. It cuts shading work but not blending or render-target bandwidth.
- Both test games use DirectX 12, so neither DXVK's LOD bias nor its anisotropy override applies. A sampler LOD bias for Wilds would need a Vulkan layer that adds `mipLodBias` when samplers are created, which is Tier I and not allowed for Space Marine 2.
- `RADV_FORCE_VRS` set as a launch-option variable changes the driver's behavior without loading any module into the game. That makes it plausibly anti-cheat-safe for Space Marine 2, but no Easy Anti-Cheat statement confirms it.
- Forced VRS also hits HUD and text pipelines, so image scoring must include the UI.

### Gaps
- No measurements of forced VRS on the Deck for these two games.
- No tool found that does per-pass VRS or per-pass render-target scaling.
- No RE Engine equivalent of a translucency screen-percentage setting was found.

---

## 6. Classification and applicability notes for the two test games

### Takeaway
**Monster Hunter Wilds** (RE Engine, DirectX 12, no online anti-cheat; REFramework works) can reach routes (a), (b), (d) and, with Tier I opt-in, (c). Its notable route (a) and (b) knobs:
- in-menu upscalers;
- `config.ini` lines for CPU worker threads, shadow cache and DirectStorage;
- REFramework toggles for GI, volumetric fog, wind and foliage LOD.

**Space Marine 2** (Swarm engine, DirectX 12, Easy Anti-Cheat) is limited to route (a) menu settings, the `SteamDeck=1` Low/30 fps preset, and route (d): gamescope resolution and FSR1 upscaling, frame caps, TDP, and possibly a RADV environment variable. Its expensive parts — hordes, animation, physics — are route (e).

### Cited Findings
- Wilds `config.ini` levers from the Deck guide [claimed, unmeasured]:
  - `ParallelBuildProcessorCount` 8→4: "same if not a bit smoother", lower CPU load;
  - shadow cache disabled;
  - texture filtering reduced;
  - FSR Quality;
  - DirectStorage `StagingBufferSize=32`.

  The same guide forces 1024×640 in Gaming Mode and calls it its biggest single jump. Source: [Nexus mod 183](https://nexusmods.com/monsterhunterwilds/mods/183)
- Viral Wilds `config.ini` tweaks are unmeasured — [Icy Veins](https://www.icy-veins.com/monster-hunter-wilds/news/monster-hunter-wilds-performance-optimization-fps-boost/):
  - `RenderWorkerThreadPriorityAboveNormal=Enable`;
  - fixing the misspelled "Resoltuion" key, which "might change nothing".
- A REFramework post-processing mod for Wilds controls TAA, sharpening, volumetric fog, film grain and similar. Only lens distortion and volumetric fog actually worked — [Nexus mod 221](https://nexusmods.com/monsterhunterwilds/mods/221)

### Inferences
- `ParallelBuildProcessorCount` is the only CPU job-system knob found in either game.
- Wilds' in-menu settings already cover most of the "port cuts" list: resolution and upscaler, shadows, volumetrics, AO, textures, mesh quality. Because RE Engine on Switch 2 dropped AO, volumetrics, SSR, depth of field and subsurface scattering in handheld, those same menu items are the priority search space for DeckForge in Wilds.

### Gaps
- I could not confirm the full list of Wilds `config.ini` keys or whether an NPC or crowd density setting exists.
- I could not confirm where Space Marine 2 stores its graphics-settings file (for route a outside the menu) or whether editing it is safe under Easy Anti-Cheat.

---

## Ranked technique table

The ranking is by expected gain on the Deck times feasibility. **"Typical gain" figures come from other hardware unless marked; none were measured on a Deck OLED for these two games.**

| # | Technique (port precedent) | Typical gain (source quality) | Route(s) | Monster Hunter Wilds (RE Engine, no anti-cheat) | Space Marine 2 (Swarm, Easy Anti-Cheat) |
|---|---|---|---|---|---|
| 1 | Lower internal resolution plus temporal reconstruction (Switch 2 handheld at 360–540p with DLSS; Death Stranding iPhone ~400p; all Switch ports) | Largest single lever; ports go to 25–45% of output pixels [measured resolutions; no ms costs] | a (in-game upscaler/resolution), d (gamescope resolution + FSR1/NIS), b/c-Tier I (OptiScaler for FSR4) | **Yes**: in-game FSR/XeSS; 1024×640 forced was the "largest jump" [claimed]; OptiScaler possible (Tier I) | **Yes (a, d)**: in-game FSR 3.1; gamescope. No OptiScaler (anti-cheat) |
| 2 | Remove second-order lighting: GI, volumetrics, AO, SSR, subsurface scattering, depth of field (SF6 and Hogwarts on Switch; AC Shadows Series S RTGI; Doom Switch no SSR) | "Significant" for Wilds GI + fog [claimed]; SM2 SSR "very GPU heavy" [claimed] | a (menu), b (REFramework) | **Yes**: menu items + REFramework GI/fog off (cutscene breakage was reported and later fixed in the mod) | **Partial (a)**: SSR off, volumetrics Low, AO setting; GI not exposed |
| 3 | Forced coarse shading, VRS 2×2 (Valve's Deck power-saving work) | "Upwards of 30%" on desktop RDNA2, little quality loss [measured 2021]; some cases ~2× with Mesa 26.2 [claimed] | d (`RADV_FORCE_VRS` / config file); c (per-pass layer, Tier I) | **Yes (d), test it**; per-pass layer possible (Tier I) | **Probably (d)**: driver variable, no module injected (inference; no anti-cheat confirmation); layer not allowed |
| 4 | Shadow cuts: resolution, cascades, distance, sun-shadow method (Witcher 3 sun-shadow rewrite; Hogwarts, Cyberpunk, SF6 reduced shadows) | Unquantified [qualitative] | a; b (UE `r.Shadow.*`); e (method rewrite) | **Yes (a)**: shadow quality; shadow cache toggle in `config.ini` | **Yes (a)**: Low shadows |
| 5 | Foliage density and LOD (Witcher grass rewrite ~50% of visuals; Hogwarts fewer trees) | "Couple more frames" in Wilds [claimed] | a; b (UE `foliage.DensityScale`; Wilds More Graphics Options mod); e (algorithm) | **Yes (b)**: foliage LOD 2–3 via mod | **Limited (a)**: "details" setting only |
| 6 | Draw distance and mesh LOD bias (Witcher, Hogwarts) | Unquantified | a; b (UE `r.ViewDistanceScale`, `r.SkeletalMeshLODBias`) | **Partial (a/b)**: mesh quality in menu; mods | **Limited (a)** |
| 7 | Textures, mips, streaming pool (Switch ports; Series S memory pressure) | Mostly memory and bandwidth; fps gain unquantified | a; c (DXVK `samplerLodBias`, D3D9/11 only; custom Vulkan layer for D3D12, Tier I) | **Yes (a)**; LOD-bias layer possible (Tier I) | **Yes (a)** only |
| 8 | Frame cap, refresh pacing, cutscene trade (Doom Eternal cutscenes at 20 fps for higher resolution) | Pacing and latency, not throughput | a, d (gamescope; `VKD3D_FRAME_RATE`) | Yes | Yes |
| 9 | CPU worker-thread and job tuning (Witcher; Doom enemy-count drops) | "Same if not a bit smoother" [claimed] | a (`ParallelBuildProcessorCount`) | **Yes (a)** | No knob found (e) |
| 10 | Crowd, NPC and AI density (Witcher −30% NPCs reverted; SF6 standard density; Cyberpunk PS4-level density; TLOU AI quality setting) | CPU relief; risks an "empty world" [claimed] | a where exposed; e | Unknown (gap) | **No**: horde size is gameplay (e) |
| 11 | Distant-character animation rate (Hogwarts Switch reduced NPC animation; UE URO and budget allocator) | Unquantified; CPU-bound scenes only | b (UE `a.Budget.*` if the game uses it); e | No knob found; REFramework is theoretical (no precedent) | **No (e)** |
| 12 | Physics, cloth and wind simulation rate | "A few frames" for Wilds wind [claimed] | a, b | **Yes (b)**: wind off via mod | **Yes (a)**: cloth simulation Low |
| 13 | Half- or quarter-res particles and depth of field (Doom Switch) | Unquantified; overdraw-heavy scenes | b (UE `r.SeparateTranslucencyScreenPercentage`); c (no precedent); e | **No external route found** (e); per-pass VRS is the stand-in (c) | **No (e)** |
| 14 | Streaming and loading changes (Hogwarts Switch loading screens; Cyberpunk fast storage) | Fewer hitches; not fps | a (Wilds DirectStorage staging buffer [claimed]); e | Partial (a) | No (e) |
| 15 | Async compute on/off | Direction unknown on the Deck | c/d (`VKD3D_CONFIG=single_queue`) | Testable | Testable (environment variable; inference that it is anti-cheat-safe) |
| 16 | FP16 or lower shader precision; baked replacing dynamic lighting | Unquantified | e (a SPIR-V rewrite layer is speculative) | No | No |
| 17 | Deck-specific default preset (TLOU Very Low, Spider-Man 2, Satisfactory; SDK 1.65 hardware defaults) | Baseline only | a; d (`SteamDeck=1`) | Unknown whether Wilds reads the Deck flag | **Yes**: `SteamDeck=1` forces Low + 30 fps cap [reported] |

**Key memory-worthy facts for the main session:**
- Space Marine 2 is DirectX 12-only and honors `SteamDeck=1` (Low preset plus 30 fps cap).
- vkd3d-proton has no LOD-bias or anisotropy override, unlike DXVK.
- Steamworks SDK 1.65 (July 2026) added `GetSteamHardwareDefaultConfig()` and removed `IsRunningOnSteamDeck()`.
- Doom 2016 on Switch used quarter-res alpha effects and depth of field.
- RE Engine on Switch 2 handheld runs at 360p internal (SF6, Requiem).
