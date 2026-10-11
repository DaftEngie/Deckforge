# Hidden and low-end rendering paths: RE Engine (Monster Hunter Wilds) and Swarm (Space Marine 2) on Steam Deck OLED handheld

Scope notes:
- This brief targets a locked **40 fps**. The repo's CLAUDE.md says the target is **45 fps (22.2 ms)**. Someone should decide which one is canonical.
- PCGamingWiki could not be reached. WebFetch errored and curl got a 403 from the egress proxy, so PCGW config paths and launch options are not included.
- Every date below is the source's publication date. "Claimed" means the author or a user asserted it with no method. "Measured" means numbers came from a stated test.

---

## 1. Wilds on consoles: DF findings, console-equivalent settings, and whether Series S goes below PC Lowest

### Takeaway
Series S runs Wilds at about 900p (dynamic, capped at 1080p) and 30 fps. It does not hold 30, and it drops SSR. No source maps it to PC settings or shows it going below PC Lowest. Series S has far more GPU and CPU than the Deck and still misses 30, which is a strong negative signal for a locked 40 on Deck.

### Cited Findings
- [Feb 2025, launch] Per DF, the PS5/Series performance mode targets about 900p dynamic. It sometimes hits 1080p and often falls to 720p. Balanced averages about 1224p at a 40 fps target, and Quality about 1656p. Output is upscaled to 4K with **FSR 1**. — [GamePro (DF summary)](https://www.gamepro.de/artikel/monster-hunter-wilds-performance-ps5-xbox-720p,3428384.html)
- [Mar 2025] ElAnalistaDeBits pixel counts:
  - PS5/XSX Resolution mode: dynamic 1800p (about 1620p typical), about 30 fps.
  - Balanced: dynamic 1440p (about 1224p), about 40 fps.
  - Performance: dynamic 1080p (about 900p), about 60 fps.
  - **Series S has one mode: dynamic 1080p (about 900p typical), about 30 fps, FSR.**
  - DF said Series S "needs adjustments" because it can't hold 30.
  - Source: [Vandal](https://vandal.elespanol.com/noticia-amp/1350778492/donde-se-ve-mejor-monster-hunter-wilds-comparativa-entre-ps5-xbox-series-ps5-pro-y-pc/)
- [Feb 2025] Per DF, Series S:
  - is capped at 1080p, targets 30 fps and often dips to about 25 fps;
  - has **no screen-space reflections**, "muddy" textures, and a UI that drops to 1080p;
  - gains very little from the unlocked VRR option.
  - Source: [Nintendo Life](https://nintendolife.com/news/2025/02/monster-hunter-wilds-tech-analysis-has-us-concerned-about-a-switch-2-port)
- [Dec 2024, Capcom official] Series X runs 1728p30 (graphics) or 1080p60 (framerate). Series S has a single 1080p30 mode. — [Pure Xbox](https://www.purexbox.com/news/2024/12/capcom-unveils-monster-hunter-wilds-performance-details-for-xbox-series-x-and-s)
- [Feb 2025] Per DF, PS5 is missing low framerate compensation (LFC), and VRR works better on XSX. — [Notebookcheck](https://www.notebookcheck.net/Monster-Hunter-Wilds-PS5-and-Xbox-performance-issues-detailed-in-Digital-Foundry-analysis.967046.0.html)

### Inferences
- The only feature Series S demonstrably drops is SSR, which PC can also switch off. On the evidence, Series S is a lower resolution plus fewer effects, not a hidden sub-Lowest preset.
- From general hardware knowledge (not sourced): Series S has an 8-core Zen 2 at about 3.6 GHz and a 4 TF RDNA2 GPU. The Deck has a 4-core Zen 2 and about 1.6 TF. Series S misses 30 fps at about 900p, so console settings are not a useful floor for Deck.

### Gaps
- I found no published "console-equivalent PC settings" for Wilds from DF or anyone else. The only console-vs-PC note is that PC and PS5 Pro have RT reflections and higher shadow and texture resolution ([Vandal](https://vandal.elespanol.com/noticia-amp/1350778492/donde-se-ve-mejor-monster-hunter-wilds-comparativa-entre-ps5-xbox-series-ps5-pro-y-pc/)).
- There is no post-patch (2026) DF console re-test of Series S.

---

## 2. Wilds config.ini keys beyond the menu

### Takeaway
Only a handful of off-menu keys are documented:
- `ParallelBuildProcessorCount`
- `RenderWorkerThreadPriorityAboveNormal`
- `StreamingVRAMSizeHigh` / `StreamingVRAMSizeHighest`
- `EnableSharpness` / `Sharpness`
- shadow caching and texture filtering keys (exact names not confirmed)
- the `Resoltuion` typo key

Every gain reported for them is anecdotal. The best-known Deck config pack is now marked obsolete by its author.

### Cited Findings
- [Mar 2025] Users changed the typo key `Resoltuion` to "Resolution", `ParallelBuildProcessorCount` from 8 to 16, and `RenderWorkerThreadPriorityAboveNormal` from false to true.
  - Reported gains include +10% (RTX 4090), about 45 to 60 fps, and "+30–40 fps".
  - Others saw no change. All of it is unverified.
  - Source: [The Game Post](https://thegamepost.com/monster-hunter-wilds-typo-configuration-file-pc-fps/)
- [Mar 2025] `ParallelBuildProcessorCount` should be set to the CPU's thread count or slightly lower. On one setup (7800X3D + 4080S, 3440×1440), camp went from 50–85 fps with stutter to 90–110 fps. Commenters had mixed results and some saw worse performance at high values. `EnableSharpness=True` plus `Sharpness` (0–1) unlocks the sharpening control. — [r/MonsterHunter guide](https://redlib.ssps.io/r/MonsterHunter/comments/1j5klpq/mhwilds_pc_optimization_guide)
- [Mar 2025] One user (R5 3600 + GTX 1060) set `ParallelBuildProcessorCount` to the logical core count (12) and made config.ini read-only so the game won't overwrite it. Combined with the REFramework mods, fps went from 10–15 to 30–40. This is self-reported. — [Steam thread](https://steamcommunity.com/app/2246340/discussions/0/599646765722946793)
- [v1.6, last updated 18 Dec 2025] "The Little Engine that Shouldn't" (Steam Deck OLED/LCD config):
  - Turns off shadow caching (v1.2), lowers texture filtering (v1.2) and texture quality (v1.1), and uses FSR Quality.
  - Sets `ParallelBuildProcessorCount` from 8 to **4** (v1.4.1). The author says it performs "about the same or slightly smoother" with lower CPU load.
  - Claimed result: about 30–45 fps at 1600×900 Balanced, 1280×800 Quality, or 1024×640 native.
  - **The page now says it is outdated and not needed after update 1.040.03.02. Delete the config so the game regenerates it.**
  - Source: [Nexus 183](https://nexusmods.com/monsterhunterwilds/mods/183)
- [Apr–May 2026] `StreamingVRAMSizeHigh` and `StreamingVRAMSizeHighest` are byte values (GB × 1,073,741,824). This is the older method. The newer mod uses a runtime `StreamingResidentTextureTargetSize`. — [Nexus 4269](https://www.nexusmods.com/monsterhunterwilds/mods/4269)
- [Mar 2025] A drop-in config.ini (Nexus 91) claims to:
  - enable multithreaded rendering, change thread count, and reduce rendering calculations;
  - turn off fog, SSR, SSS, and shadow caching;
  - lower water, wind, and shadow-map quality and use VRS;
  - strip film grain, lens distortion, god rays, and lens flare.
  - It claims "+10 fps" and 10–15% less CPU, with no benchmarks.
  - Source: [Nexus 91](https://nexusmods.com/monsterhunterwilds/mods/91)
- [May 2025] Deleting config.ini in the game root regenerates it, which is a useful reset path. — [Steam thread](https://steamcommunity.com/app/2246340/discussions/0/596274239105934228)

### Inferences
- Many "hidden" keys in older config packs are the same menu settings written below the menu floor, such as fog off and shadow cache off.
- After the Jan 2026 patch, Capcom regenerates and rewrites presets. Old read-only configs can conflict with the new option schema, which is probably why the Little Engine author says to delete them.
- On a 4-core/8-thread Deck, `ParallelBuildProcessorCount` of 4–8 is the only defensible range. Higher values hurt some users.

### Gaps
- I couldn't get the full current config.ini key list or the meaning of `ParallelBuildProcessorCount` from Capcom. PCGW was blocked.
- I found no LOD-bias or thread-count key measured on a Deck.

---

## 3. REFramework renderer parameters for RE Engine and Wilds

### Takeaway
REFramework's built-in Graphics panel has almost no performance controls. It covers ultrawide and FOV, GUI hiding, ForceRenderResToWindow, and ray/path-tracing tweaks. The low-end levers come from **Lua scripts that use the Lua API** (`sdk.get_managed_singleton` / `get_native_singleton`) to poke engine objects. Those scripts expose things the menu doesn't, including shadow resolution below Lowest.

### Cited Findings
- REFramework `Graphics.hpp` options:
  - `UltrawideFix`, FOV options, `DisableGUI`, and `ForceRenderResToWindow`.
  - Ray-tracing tweaks (`RayTraceType`: AO, hybrid or pure path tracing, etc.; `BounceCount`; `SamplesPerPixel`) for TDB ≥ 69.
  - RE4 scope tweaks (`ScopeImageQuality`).
  - **There are no built-in AO, fog, shadow, GI, or LOD controls.**
  - Source: [REFramework source](https://raw.githubusercontent.com/praydog/REFramework/master/src/mods/Graphics.hpp)
- The Lua API reaches engine objects through `sdk.get_managed_singleton` (C#-side, most exposed) and `sdk.get_native_singleton` (C++-side, least exposed). It also offers `on_pre_application_entry("BeginRendering")` hooks. ObjectExplorer is used to discover names. — [REFramework book](https://cursey.github.io/reframework-book/)
- [v2.0, 22 Apr 2026] "More graphics options" (Nexus 816) exposes:
  - environmental object culling (tall grass, shrubs and trees, rocks, decorations, decals, small lights, dust and leaf particles);
  - mesh LOD bias, including monsters;
  - foliage LOD bias and texture LOD bias;
  - disabling dynamic shadows;
  - **dynamic shadow resolution below the game's lowest preset**;
  - ambient and volumetric lighting quality;
  - particle density.
  - The author says the gains are "significant", with no numbers.
  - Source: [Nexus 816](https://nexusmods.com/monsterhunterwilds/mods/816)
- [Mar 2025] "Tweak In-Game Volumetric Fog(s)" exposes fog resolution, **including two hidden lower-quality options**, plus ambient-light rate, culling distance, and near fade. The author says it will "probably not improve FPS in any significant way". Requires REFramework ≥ build 01090. — [Nexus 455](https://nexusmods.com/monsterhunterwilds/mods/455)
- [v2.1.0, 6 Sep 2026] "Disable Post-Processing Effects" (TonWonton) toggles:
  - TAA/AA, sharpening, and color correction;
  - exposure (local and auto), contrast, and gamma;
  - volumetric fog, film grain, lens distortion, and vignette.
  - It ships Lua and C# (REFramework.NET + .NET 10) versions and makes no performance claim.
  - Source: [Nexus 221](https://nexusmods.com/monsterhunterwilds/mods/221)
- [Mar 2025] "Disable Ambient Lighting" turns off DPGI, the ambient lighting system. The author says it "should gain some FPS" and "looks pretty ugly in areas". Mod 2368 removes only the DPGI specular part. — [Nexus 331](https://www.nexusmods.com/monsterhunterwilds/mods/331)
- [Apr–May 2026] "MHWilds Graphics Enhancement" covers RTGI, RTAO, RT reflections, shadows, streaming budget, LOD, small-object culling, SSR, and SSAO/DFAO through the REFramework UI. It has no numbers. — [Nexus 4269](https://www.nexusmods.com/monsterhunterwilds/mods/4269)

### Inferences
- In Wilds, REFramework can set renderer parameters to values below the menu floor. The existence of "two hidden lower fog resolutions" and "shadow resolution below lowest" shows the engine accepts them.
- This is all Tier I: dinput8.dll injection.

### Gaps
- I didn't find a canonical list of RE Engine render-config fields (for example `via.render.*` properties) in official REFramework docs. Each field would have to be found with ObjectExplorer.
- Unverified (general knowledge): REFramework on Proton needs a `WINEDLLOVERRIDES="dinput8=n,b"` launch option.

---

## 4. Wilds community performance mods and what each measured

### Takeaway
Almost nothing was measured. The Deck-relevant mods are Lite Environment, More graphics options, Disable Ambient Lighting, wind simulation off, and the texture decompressor. All of them report "big" gains anecdotally. The one quantified Deck claim is the Little Engine author's "close to a solid 30 at 1024×640 without frame gen" with Lite Environment fully on (pre-2026 build).

### Cited Findings
- [Mar 2025] Little Engine author: about 30 fps at 1024×640 Quality or 800p Balanced with frame generation. With Lite Environment and all its options on, "close to a solid 30 at 1024×640 without frame generation". — [Destructoid](https://destructoid.com/steam-deck-users-enjoy-monster-hunter-wilds-at-sub-30-fps)
- Little Engine page: Lite Environment gives a "major performance uplift". The config plus Lite Environment plus 1024×640 is the biggest gain. — [Nexus 183](https://nexusmods.com/monsterhunterwilds/mods/183)
- [Mar 2025] One user said "Wind Simulation Disabler" turns off "minor physics effects applied to just about everything", for a large fps gain with little visible difference. Disable Ambient Lighting gave "a decent fps gain" at an image-quality cost. — [Steam thread](https://steamcommunity.com/app/2246340/discussions/0/599646765722946793)
- [2025] MHWS-TEX-Decompressor (eigeen, needs REFramework nightly) replaces GDeflate-compressed textures with uncompressed ones. Install size grows from about 24 to about 41 GB. **Measured:** reproducible camera-pan micro-stutter disappeared on an RTX 4060 8 GB. No fps figures. — [PCGH](https://www.pcgameshardware.de/Monster-Hunter-Wilds-Spiel-74697/News/Performance-Patch-Update-Community-Mod-1487048/)
- [Jan 2026] "Less DLC Checks" throttled per-frame DLC ownership checks. It is **obsolete since 1.040.03.01**. — [Nexus 3798](https://www.nexusmods.com/monsterhunterwilds/mods/3798)
- [Mar 2025] REFramework itself reportedly fixes stutters attributed to Capcom's anti-tamper. The evidence is a single frametime screenshot. — [DSOGaming](https://www.dsogaming.com/mods/monster-hunter-wilds-mod-fixes-stutters-caused-by-the-anti-tamper-tech/)
- [Mar 2025] An upgrade-guide mod claims "up to 30%" from presets, with no benchmarks. — [Nexus 249](https://nexusmods.com/monsterhunterwilds/mods/249)

### Inferences
- The likely biggest Tier I levers on Deck are CPU-relevant ones (wind simulation, environment and particle density, culling) and GPU-relevant ones (DPGI off, shadows below Lowest, LOD bias). They all need A/B testing on the 2026 build, because Capcom has since added its own CPU tab and LODs.

### Gaps
- I couldn't find the Lite Environment or Wind Simulation Disabler Nexus pages, so their exact toggles and current status are unknown.
- I found no frametime-captured Deck A/B for any mod.

---

## 5. Mods broken by Capcom's 2025–2026 patches, and what Capcom made official

### Takeaway
Each title update has broken REFramework until a new nightly ships. Capcom's Jan–Feb 2026 Steam patches made several mod levers official:
- a CPU tab;
- 5-level volumetric fog, with three new levels below the old Low;
- internal mesh LODs;
- the DLC-check fix.

The Little Engine and Less DLC Checks mods are explicitly obsolete. The game became **Steam Deck Verified around 20–21 Aug 2026**.

### Cited Findings
- [Dec 2025 roadmap]
  - TU4 (16 Dec): spreads player, monster, and UI CPU work across frames; fewer simultaneous effects; memory cuts.
  - Jan 2026 Steam patch: **new CPU and graphics options and presets**, plus shader, VRAM, and streaming fixes.
  - Feb 2026 Ver.1.041: **mesh LOD levels to reduce GPU load**.
  - Source: [AOL/roadmap](https://www.aol.com/articles/monster-hunter-wilds-sets-roadmap-122533949.html)
- [Capcom official, 28 Jan 2026, Ver.1.040.03.01, Steam]
  - New **CPU tab** "to adjust settings related to CPU load".
  - New graphics categories and new levels for existing options.
  - Presets adjusted.
  - **Volumetric Fog went from 2 to 5 levels.** The old Low became High, and Medium, Low, and Lowest are new.
  - VRS is forced off during upscaling, and shader warming outside the compile screen was cut.
  - Source: [Capcom patch notes](https://info.monsterhunter.com/wilds/update/en-us/Ver.1.040.03.01.html)
- [Jan 2026] The CPU tab's named options, as quoted by commenters, are "frame skips" and a cap on the number of smaller creatures. The tab doesn't affect visuals. Not confirmed from an official source. — [Reddit snapshot](https://reddit.sentinel-team.org/posts/1qpb0db/snapshots/2026-01-29T17%3A31%3A51.77496Z)
- [Capcom official, 18 Feb 2026, Ver.1.041] Added internal 3D-model LODs, optimized monster and endemic-life spawn processing, added effect caching for duplicate effects, and cut CPU/GPU rendering load. — [Capcom patch notes](https://info.monsterhunter.com/wilds/update/en-us/Ver.1.041.00.00.html)
- [Dec 2025, measured by DF] TU4 reduced GPU load about 8–9% at Medium/High (RTX 3070) and fixed High-texture streaming stutter. Some High textures look worse or load late. — [Notebookcheck DE](https://www.notebookcheck.com/Monster-Hunter-Wilds-Title-Update-4-bringt-zwar-mehr-FPS-und-behebt-Ruckler-hat-aber-auch-seinen-Preis.1190216.0.html)
- [Dec 2025, Capcom's own videos] TU3 to TU4 at 1080p Medium, no frame gen: +12–23% on an i5-10400 + 2060S and on an R5 5600X + RX 6600. — [DSOGaming](https://www.dsogaming.com/videotrailer-news/capcom-reveals-performance-improvements-for-monster-hunter-wilds-in-new-videos/)
- [Jan 2026] Average fps is "mostly similar" to TU4. Minimum fps is about +8% vs TU4 and about +20% vs TU3. Steam Deck is "roughly playable at ~30 fps" with FSR or XeSS. — [Notebookcheck](https://www.notebookcheck.net/Monster-Hunter-Wilds-fixes-DLC-bug-greatly-reduces-FPS-drops-and-runs-at-30-FPS-on-Steam-Deck.1215270.0.html)
- [Jan 2026, measured] Legion Go S (Z1 Extreme), Low preset, 1200p, XeSS/FSR3 Balanced: about 40 fps exploring and fighting, about **30 fps in CPU-heavy areas (Grand Hub)**. — [TechRadar](https://www.techradar.com/gaming/pc-gaming/its-not-a-myth-capcom-has-fixed-monster-hunter-wilds-and-i-even-tested-it-to-find-out)
- [Jan 2026] A Deck user reports large areas still around 25 fps or lower on the Lowest preset (previously 15–20). — [Reddit snapshot](https://reddit.sentinel-team.org/posts/1qq0psa/snapshots/2026-01-29T17%3A31%3A51.77496Z)
- [Feb 2026] A game update left REFramework unusable (mods not loading, black screen). The fix is expected in a nightly build, and the 18 Feb update might break it again. — [GitHub issue #1469](https://github.com/praydog/REFramework/issues/1469)
- [Jul 2026] On Deck at the lowest settings, the game averages about 30 fps with poor 1% and 0.1% lows. Verdict: "technically playable". — [Steam Deck HQ](https://steamdeckhq.com/news/monster-hunter-wilds-is-technically-playable/)
- [20–21 Aug 2026] Wilds is **Steam Deck Verified**, with Proton Experimental recommended.
  - At default settings it holds "30 FPS and above most of the time".
  - Visuals are "pixelated and blurry", with muddy textures and missing shadows.
  - Sources: [RPG Site](https://www.rpgsite.net/news/21151-monster-hunter-wilds-is-now-steam-deck-verified-by-valve), [Steam Deck HQ](https://steamdeckhq.com/news/monster-hunter-wilds-gets-steam-deck-verified/)
- [Feb 2025, launch, measured] Deck at 720p, FSR3 Ultra Performance, everything lowest: under 20 fps in the Scarlet Forest. — [RPG Site](https://www.rpgsite.net/feature/16917-monster-hunter-wilds-steam-deck-full-game-performance-final-build-rog-ally-settings-playstation-portal-streaming-ps5-mode)
- [Jul 2025] Capcom said its anti-cheat and anti-mod approach would change from TU1, with consequences mainly in ranked play. It has not officially supported mods. — [Mein-MMO](https://mein-mmo.de/monster-hunter-wilds-cheats-mods-trainer/)
- Discarded source: [Evetech, May 2026](https://evezone.evetech.co.za/gear-review/monster-hunter-wilds-on-steam-deck-performance-best-settings) lists setting names that don't exist in Wilds and an 18 W Deck TDP. It looks unreliable.

### Inferences
- The hidden low-end levels that mods found have partly become official (fog levels, CPU tab, LODs). The best Tier S baseline is now the **2026 in-game Lowest preset plus the CPU tab**, not old config packs.
- A Z1 Extreme (8-core Zen 4) still drops to about 30 fps in hubs. **On the evidence, a locked 40 fps on Deck in Wilds is not reachable. Report it as BLOCKED or UNSURE.** A locked 30, or 40 only in the field and not in hubs, is the realistic claim to test.

### Gaps
- There are no official names, ranges, or measured costs for the CPU-tab options.
- No source says which REFramework scripts survived 1.041 and later patches.

---

## 6. RE Engine on weak hardware (iPhone and Switch 2)

### Takeaway
Capcom's low-end RE Engine ports work mainly through **very low internal resolution plus a strong ML or temporal upscaler**:
- iPhone RE4: about 360p internal, MetalFX to 720p.
- Switch 2 SF6 and Requiem: 360p handheld and 540p docked, with DLSS.
- RE7 on Switch 2: about 432p handheld.

On top of that they cut or scale individual features:

| Feature | What the ports did |
|---|---|
| SSR | removed |
| Strand hair | replaced with cards |
| Volumetrics | lower resolution |
| AO | removed or reduced |
| Object shadows | fewer |
| Texture cache | at its lowest internal value |
| Particle physics, DoF | dropped |

### Cited Findings
- [2023] RE4 on iPhone 15 Pro:
  - About **360p internal**, MetalFX to 720p, locked 30 fps, and no graphics menu on iPhone (Mac exposes one).
  - Strand hair is absent.
  - The **texture cache is at its lowest internal value**.
  - **SSR is absent** (cube maps only), most objects cast no shadows, AO is lower, and **volumetrics are lower resolution**.
  - Source: [GSMArena](https://m.gsmarena.com/resident_evil_4_for_iphone_review-news-61067.php)
- [2023] RE Village on iPhone 15 Pro exposes a PC-like settings menu and MetalFX Quality or Performance. It runs up to 2796×1290, with "60 fps at 2340×1080" claimed by a YouTuber. — [Wccftech](https://wccftech.com/resident-evil-village-for-iphone-15-pro-offers-pc-graphics-settings/)
- [2026] RE7 on Switch 2 runs at about 720p docked and **about 432p handheld**, upscaled (likely DLSS), at 60 fps. Shadow cascades are less aggressive than PS4, volumetric resolution is reduced, and SSR suffers. Village on Switch 2 has similar resolution and drops to the 40s outdoors, with denser fog and faint snow. — [Nintendo Everything (DF)](https://nintendoeverything.com/resident-evil-7-and-village-frame-rate-and-resolution/)
- Village, Switch 2 vs Deck: Deck at defaults runs closer to 60 fps. The author recommends a 45 fps cap, or FSR 1 Quality to hold 60. — [Steam Deck HQ](https://steamdeckhq.com/news/resident-evil-village-nintendo-switch-2-steam-deck/)
- [2025] SF6 on Switch 2:
  - Fixed 540p to 1080p docked and **360p to 720p portable** with DLSS.
  - SSR, particle physics, and DoF are removed in battles.
  - **Portable also drops AO and volumetrics and uses lower lighting quality.**
  - Textures are close to base PS4.
  - Some characters at range animate at about 20 fps.
  - Source: [GoNintendo (DF)](https://www.gonintendo.com/contents/50394-digital-foundry-dives-into-street-fighter-6-on-switch-2-for-a-tech-analysis)
- [Feb 2026] RE Requiem on Switch 2:
  - 540p docked and **360p handheld** with DLSS.
  - Strand hair is replaced by cards (Series S also drops it), geometry is simplified, and textures are lower. Lighting and density are kept.
  - Docked is unlocked at 30–60 fps. Handheld drops to the mid-20s.
  - Series S runs native 720p at about 60 fps.
  - Sources: [PPE.pl (DF)](https://www.ppe.pl/news/401635/resident-evil-requiem-to-najlepsza-wizytowka-nintendo-switcha-2-gra-dziala-w-540p-ale-zaskakuje-jakoscia.html), [Pure Xbox](https://www.purexbox.com/news/2026/02/digital-foundry-compares-resident-evil-requiem-on-switch-2-and-xbox-series-s-with-mixed-results)

### Inferences
- The recipe that maps to Deck is about 360–540p internal plus the best available upscaler (FSR or XeSS; no DLSS or MetalFX on Deck), with SSR, AO, volumetrics, and DoF off and hair at its cheapest. That recipe depends on DLSS-class reconstruction. On Deck, FSR at those input resolutions will look much worse than the Switch 2 results.
- Capcom's handheld targets were 30 fps, or unlocked mid-20s to 30s for Requiem. The handheld-class ports give no evidence that Capcom can hold 40 in an open-world RE Engine game.

### Gaps
- There is no DF breakdown of GI or shadow-cascade settings for the iPhone ports.
- Wilds has no Switch 2 or mobile version, so there's no Capcom-made low-end Wilds profile to copy.

---

## 7. Are the mobile or Switch low-end modes reachable on PC?

### Takeaway
I found no evidence of a hidden mobile or Switch preset in PC builds, and no report of anyone forcing one. Below-menu values are reachable piecemeal: REFramework mods set shadow resolution below Lowest and use hidden fog resolutions, and Capcom later surfaced lower fog levels officially.

### Cited Findings
- REFramework scripts set shadow quality "below the game's lowest preset" and use culling and LOD bias. — [Nexus 816](https://nexusmods.com/monsterhunterwilds/mods/816)
- The fog tweak mod exposes "two hidden lower-quality" fog resolution options. — [Nexus 455](https://nexusmods.com/monsterhunterwilds/mods/455)
- Capcom later added Medium, Low, and Lowest fog below the old Low. — [Capcom](https://info.monsterhunter.com/wilds/update/en-us/Ver.1.040.03.01.html)

### Inferences
- The engine's scalability ranges extend below the PC menu. Reaching them on Wilds today is Tier I (REFramework), apart from whatever Capcom has since exposed.

### Gaps
- I found no datamine or REFramework ObjectExplorer dump that shows platform-specific (iOS or NX2) quality tables in PC builds.

---

## 8. Space Marine 2: consoles vs PC (DF)

### Takeaway
Consoles run 720–1080p (performance) or 1080–1440p (quality) with FSR2. Series S is 30 fps only, 720–1080p internal, with slightly lower shadows. It dips to about 26 fps. The limiting factor on every platform is **CPU load from enemy count**. PS5 falls below 40 fps with dozens of enemies.

### Cited Findings
- [Sep 2024, DF]
  - PS5/XSX Quality: 1080–1440p, FSR2 to 4K.
  - Performance: 720–1080p.
  - **Series S: one 30 fps preset, 720–1080p native, output 1440p, slightly lower shadows and "minor details".**
  - Performance mode can't hold 60. PS5 drops below 40 with dozens of enemies.
  - DF attributes the drops to **enemy count straining the CPU**.
  - Source: [Multiplayer.it](https://multiplayer.it/notizie/warhammer-40000-space-marine-2-analizzato-digital-foundry-tps5-xbox-series-x-chiaro-vincitore.html)
- [Sep 2024, DF] XSX averages 10–15 fps more than PS5 in performance mode. XSX's VRR window is 40–60 vs PS5's 48–60. Series S dips to about 26 fps. — [Pure Xbox](https://www.purexbox.com/news/2024/09/xbox-series-x-is-the-console-of-choice-for-warhammer-40k-space-marine-2-says-analysis); contradicted by [PPE.pl](https://www.ppe.pl/news/350901/warhammer-40-000-space-marine-2-pokazuje-moc-wspolczesnych-sprzetow-przetestowano-wersje-na-kazda-platforme.html), which says PS5 was better optimized. That summary looks garbled.
- [Aug 2024, official] XSX runs 4K30 or 1080p60, and XSS runs 1440p30. — [Pure Xbox](https://www.purexbox.com/news/2024/08/xbox-series-x-and-s-tech-specs-revealed-for-warhammer-40k-space-marine-2)
- [Sep 2024, PC, measured]
  - The horde battle is CPU-heavy. A 7800X3D caps at about 110 fps at 1080p.
  - High to Medium gives only 5–10%.
  - **A 4 GB GPU was broken even at Low and at 800×600: textures and enemies disappeared.**
  - Source: [TechSpot](https://www.techspot.com/review/2891-warhammer-space-marine-2-benchmark/)
- [Sep 2024] Swarm is derived from Saber's engine (World War Z hordes reach about 1,000) and is DX12-only. FSR1 pairs with TAA when render resolution is lowered, and some Tyranid swarms are rendered as particle emitters. Minimum spec is an R5 2600X with a GTX 1060 6 GB for 1080p30 at minimal settings. — [PCGH](https://www.pcgameshardware.de/Warhammer-40000-Space-Marine-2-Spiel-74358/Specials/Release-Test-Benchmarks-1454891/3/)

### Inferences
- Series S's cuts are small (shadows and minor details). There is no evidence of a console-only crowd reduction.
- An 8-core Zen 2 PS5 drops below 40 in big hordes, and the Deck has a 4-core Zen 2. **A locked 40 fps in SM2 hordes on Deck is almost certainly CPU-blocked**, whatever the GPU settings. This is inference, not measured on Deck.
- The 4 GB VRAM failure is relevant: Deck's VRAM allocation (shared memory) should be checked.

### Gaps
- I found no DF per-setting console-equivalent PC settings for SM2, and no DF re-test after 2024.

---

## 9. Space Marine 2: config file location, keys, and hidden settings under Proton

### Takeaway
The settings live in a per-user `storage` tree, but **users report the files are encoded or encrypted and keyed together**. Single-file edits or restores don't stick, and cloud sync reverts them. No hidden keys (horde density, AI rate, shadow distance) are documented. **The config-file route for SM2 looks blocked in practice.**

### Cited Findings
- Location: `%LOCALAPPDATA%\Saber\Space Marine 2\storage\steam\user\<id>\Main\config\`. — [Steam thread](https://steamcommunity.com/app/2183900/discussions/0/4763207778566041719)
- [2024] The folder has many `.cfg` files, including `user_defined_settings.cfg`, and possibly `platform/config/shared_user_settings.cfg`. The files look encoded or encrypted in Notepad.
  - One keybind change altered many files.
  - Restoring a single file fails, and cloud sync reverts to the last successful launch state.
  - Source: [Steam thread](https://steamcommunity.com/app/2183900/discussions/0/4763207599014733794)
- A user claims "the settings file is actually encrypted". On Steam Deck, Display Mode and Render Resolution reset on exit when DLSS is set to Dynamic. — [Steam thread](https://steamcommunity.com/app/2183900/discussions/0/4760956432755644947)
- The in-game menu covers:
  - render and display resolution, upscaler, and a Dynamic Resolution FPS Target;
  - textures, shadows, SSAO, SSR, volumetrics, effects, and details;
  - **Cloth Simulation**, motion blur, and an FPS limit.
  - Source: [The Backdash](https://www.thebackdash.com/tech/space-marine-2-steam-deck-settings)

### Inferences
- The Proton path should be `steamapps/compatdata/2183900/pfx/drive_c/users/steamuser/AppData/Local/Saber/Space Marine 2/storage/...`. That is App ID 2183900 plus the Windows path above. I haven't verified it on a Deck.
- If the files are encrypted, DeckForge can at most back up and restore the whole `storage` folder. Expect Steam Cloud to fight it.

### Gaps
- No hidden SM2 settings found (crowd density, AI tick, physics, shadow distance).
- I couldn't confirm the encryption from a primary or technical source; there are only two user claims.
- PCGW, which usually documents this, was unreachable.

---

## 10. Space Marine 2: what `SteamDeck=1` changes

### Takeaway
`SteamDeck=1` makes the game treat the PC as a Steam Deck. That restores online (EOS) on desktop Linux and **applies a Low preset with a 30 fps cap as the starting defaults**. Nothing documented points to a Deck-only quality tier below Low.

### Cited Findings
- [Dec 2024, patch 5.0] On desktop Linux, `SteamDeck=1 %command%` is needed for online play. Without it there's an EOS error and kicks for "mods detected". It **initially sets all graphics to Low with a 30 FPS limit**. One user said it blocked maxing settings over "insufficient VRAM". — [GamingOnLinux](https://www.gamingonlinux.com/2024/12/space-marine-2-adds-dlss3-fsr3-and-frame-generation-more-playable-on-steam-deck-needs-launch-option-for-desktop-linux/page=1/)
- [Oct 2024] The option forced very low defaults, and settings could be raised afterward. One commenter thinks the Deck "optimization" just reuses existing profiles at their lowest. — [GamingOnLinux](https://www.gamingonlinux.com/2024/10/space-marine-2-fixes-online-for-steam-deck-but-may-need-launch-option-on-desktop-linux/)

### Inferences
- From general knowledge (unsourced): on a real Deck, SteamOS already sets `SteamDeck=1`. Adding it gives no extra performance there. It only matters for testing on desktop Linux.

### Gaps
- It's unknown whether the Deck flag changes anything other than the default preset and EOS behavior, such as streaming budgets or VRAM limits.

---

## 11. Space Marine 2: measured Deck settings after the Dec 2024 FSR3 patch and later

### Takeaway
I found no measured Deck numbers after the FSR3 patch. Before it, Low with FSR2 at 15 W gave **20–30 fps, with low 20s in big fights**. After patch 5.0, FSR3 plus frame generation is "a lot more playable" by feel, but FG is not recommended below 60.

### Cited Findings
- [Sep 2024, pre-FSR3, measured]
  - Settings: Low or custom, FSR2, native render, SSR off, motion blur off, cloth simulation Low, FPS limit 30, TDP 15 W.
  - Result: **about 20–30 fps, low 20s in large battles**.
  - Source: [The Backdash](https://www.thebackdash.com/tech/space-marine-2-steam-deck-settings)
- [10 Dec 2024] Patch 5.0 "Obelisk" added FSR 3, DLSS 3, and FG. FSR3 looks better than FSR2 but "didn't improve performance much". FG "feels horrible" below 60. Before the patch the game hit 30+ at times and dropped below 30 in busy scenes. — [Steam Deck HQ](https://steamdeckhq.com/news/warhammer-40000-space-marine-2-gets-fsr-3/)
- [Dec 2024] Low plus FSR Performance plus FG was "a lot more playable", but FG is not recommended (poor image quality, unreadable small text). No fps numbers. — [GamingOnLinux](https://www.gamingonlinux.com/2024/12/space-marine-2-adds-dlss3-fsr3-and-frame-generation-more-playable-on-steam-deck-needs-launch-option-for-desktop-linux/page=1/)
- [Oct 2024] Hotfix 3.1 fixed the Deck and Linux launch issue, and some CPUs that caused heavy stutters. — [Steam Deck HQ](https://steamdeckhq.com/news/space-marine-2-gets-steam-deck-launch-fix/)

### Inferences
- Native performance in hordes is roughly 20–30 fps. A locked 40 native is not supported by any evidence. 30 fps with dynamic resolution is the plausible Tier S ceiling.

### Gaps
- No Deck measurements for 2025–2026 builds; patch 6 through 11.x notes I found mention no performance work.
- No r/SteamDeck thread with numbers turned up.

---

## 12. Space Marine 2: what can be done without touching EAC

### Takeaway
The Tier S options are:
- in-game menu settings, including Dynamic Resolution FPS Target, the upscaler, and Cloth Simulation;
- the `SteamDeck=1` default;
- Steam- and SteamOS-level controls (fps cap, refresh rate, TDP).

Config-file edits appear blocked by encryption. Saber's official Integration Studio mods produce a modded client. Since patch 5.0 that means private lobbies only, which falls outside Tier S.

### Cited Findings
- [Dec 2024] Since patch 5.0, mods are not allowed in public lobbies but are allowed in private ones, alongside EAC improvements. — [GamingOnLinux](https://www.gamingonlinux.com/2024/12/space-marine-2-adds-dlss3-fsr3-and-frame-generation-more-playable-on-steam-deck-needs-launch-option-for-desktop-linux/page=1/)
- [15 May 2025] Saber released Integration Studio, its internal editor, publicly. It covers AI behaviour trees, UI/HUD, and scenarios. — [Nexus Mods news](https://www.nexusmods.com/echo/news/15273)

### Inferences
- A "smaller horde" mod made with Integration Studio is technically conceivable. It would be a modded client, so per the CLAUDE.md product rule (SM2 gets Tier S only) DeckForge must not touch it.

### Gaps
- I couldn't confirm whether editing the encrypted user config triggers EAC or mod detection, as opposed to simply failing.

---

## 13. CPU-side settings in both games

### Takeaway
Wilds now has real CPU levers:
- the official CPU tab (frame skip and a small-creature cap, per community reports);
- Wind Simulation Quality and Grass/Tree Sway in the menu;
- `ParallelBuildProcessorCount` and `RenderWorkerThreadPriorityAboveNormal` in config.ini;
- Capcom's 1.041 spawn and effect-cache optimizations.

**SM2 exposes no crowd, AI, or physics density setting beyond Cloth Simulation.** Enemy count drives CPU load and the player can't change it.

### Cited Findings
- [Mar 2025] Wilds menu settings on Deck guides include **Wind Simulation Quality** and **Grass/Tree Sway (Disable)**, along with Shadow Quality Lowest, Volumetric Fog Low, VRS Performance, and more. — [Dot Esports](https://dotesports.com/monster-hunter/news/best-monster-hunter-wilds-steam-deck-settings)
- The Wilds CPU tab, CPU-related config keys, and 1.041 CPU work are cited in sections 2 and 5: [Capcom](https://info.monsterhunter.com/wilds/update/en-us/Ver.1.041.00.00.html), [Reddit snapshot](https://reddit.sentinel-team.org/posts/1qpb0db/snapshots/2026-01-29T17%3A31%3A51.77496Z).
- REFramework "particle effects density" and culling of small lights, particles, and decorations. — [Nexus 816](https://nexusmods.com/monsterhunterwilds/mods/816)
- In SM2, CPU load comes mainly from enemy count, per DF. — [Multiplayer.it](https://multiplayer.it/notizie/warhammer-40000-space-marine-2-analizzato-digital-foundry-tps5-xbox-series-x-chiaro-vincitore.html)
- TechSpot identified no SM2 setting that affects CPU load or enemy count. — [TechSpot](https://www.techspot.com/review/2891-warhammer-space-marine-2-benchmark/)

### Inferences
- On a 4-core Deck, the Wilds CPU tab is likely the highest-value new Tier S lever. It needs A/B testing in the Grand Hub and Base Camp, which is where the Z1E dropped to about 30.

### Gaps
- No measured cost for any CPU-tab option.
- SM2 2024 hotfixes ("optimized CPU behaviour") appeared only in search-result headlines. I didn't fetch them, so I haven't verified their scope.

---

## Candidate levers

| Lever | Route | Tier | Measured or claimed gain | Image cost | Game |
|---|---|---|---|---|---|
| 2026 Lowest preset (post-1.040.03.01 rebalanced presets) | In-game menu (writes config.ini) | S | Measured (on Deck): ~30 avg at lowest, poor 1%/0.1% lows (SDHQ Jul 2026); ~25 in large areas (user, Jan 2026) | "Pixelated, blurry", muddy textures | Wilds |
| Volumetric Fog = Lowest (new 5-level scale) | Menu / config.ini | S | Claimed (Capcom: load reduction); unmeasured | Lower-res or thinner fog | Wilds |
| CPU tab: frame skip, small-creature cap | Menu / config.ini | S | Claimed; option names unofficial; unmeasured | Distant animation judder; fewer small monsters | Wilds |
| `ParallelBuildProcessorCount` = 4 (Deck) | config.ini | S | Claimed: "same or slightly smoother, lower CPU" (Little Engine); desktop anecdotes +10% to +40%; some got worse | None | Wilds |
| `RenderWorkerThreadPriorityAboveNormal` = true | config.ini | S | Anecdotal only | None | Wilds |
| Shadow cache off, texture filtering lowest | config.ini (exact key names unconfirmed) | S | Claimed (Little Engine, pre-2026) | Shadow shimmer, blurrier oblique textures | Wilds |
| `StreamingVRAMSizeHigh` / `StreamingVRAMSizeHighest` | config.ini | S | Claimed stutter reduction; unmeasured | None if within budget | Wilds |
| Grass/Tree Sway off, Wind Simulation Low | Menu | S | Claimed | Static foliage and cloth | Wilds |
| Render ~1024×640 or 800p + FSR/XeSS Quality | Menu | S | Claimed ~30 fps (pre-2026, with Lite Environment) | Soft image; FSR at sub-720p input is poor | Wilds |
| Frame cap 40 + 40 Hz panel / TDP | SteamOS / gamescope | S | n/a (pacing only) | None | Both |
| "More graphics options": culling, mesh/foliage/texture LOD bias, shadows below Lowest, ambient lighting, particle density | REFramework Lua | I | Claimed "significant"; no numbers | Pop-in, missing clutter, flat lighting | Wilds |
| Lite Environment (all options) | REFramework | I | Claimed "major uplift"; ~30 at 1024×640 without FG (pre-2026) | Reduced environment detail (toggles unknown) | Wilds |
| Disable Ambient Lighting (DPGI off) | REFramework | I | Claimed "some FPS"; one user: "decent gain" | "Pretty ugly in areas" | Wilds |
| Wind Simulation Disabler | REFramework | I | Claimed "large fps boost" (one user) | Minor | Wilds |
| Disable Post-Processing (TAA, fog, film grain…) | REFramework | I | None claimed | Aliasing if TAA off | Wilds |
| Hidden low fog resolutions | REFramework | I | Author: "probably not significant"; partly superseded by official levels | Lower-res fog | Wilds |
| Texture decompressor (uncompressed textures) | Game-file replacement + REFramework nightly | I | Measured: micro-stutter removed (RTX 4060), no fps numbers | None; +~17 GB disk | Wilds |
| `SteamDeck=1` defaults (Low + 30 cap) | Launch option (automatic on Deck) | S | None beyond Low | n/a | SM2 |
| Low + FSR 3.1 Performance + Dynamic Resolution FPS Target | Menu | S | Measured pre-FSR3: 20–30 fps, low 20s in hordes (15 W); post-FSR3 "more playable", no numbers | Soft image | SM2 |
| Cloth Simulation Low, Volumetrics Low, SSR off, Effects/Details Low | Menu | S | Unmeasured per setting; PC High to Medium only 5–10% | Minor | SM2 |
| Direct user config edit | `storage/.../Main/config` | S in principle | **Blocked**: files reportedly encrypted and cross-keyed; cloud sync reverts | n/a | SM2 |
| Horde or AI reduction via Integration Studio | Official mod tool (modded client) | Forbidden (SM2 is Tier S only; modded = private lobbies) | None found | n/a | SM2 |

Bottom line for the spec:
- Evidence supports **BLOCKED or UNSURE for a native locked 40 fps** in both games on Deck. Wilds CPU-heavy hubs hit about 30 even on a Z1 Extreme. SM2 hordes push 8-core consoles below 40.
- Wilds' best Tier S package is the 2026 Lowest preset plus the CPU tab, Fog Lowest, `ParallelBuildProcessorCount` tuning and a sub-800p render with upscaling. It needs Deck A/B testing.
- SM2's Tier S options are the in-game menu and the frame cap only.

Worth saving to project memory:
- PCGamingWiki is blocked by this environment's egress proxy.
- Wilds became Steam Deck Verified around 20–21 Aug 2026.
- Wilds Jan/Feb 2026 patches added a CPU tab, 5-level fog and mesh LODs, which supersede the old Deck config packs.
- SM2 user config files are reportedly encrypted, so the Tier S config route for SM2 is likely unavailable.
- The target-fps inconsistency (40 in this brief vs 45 in CLAUDE.md) needs a decision.
