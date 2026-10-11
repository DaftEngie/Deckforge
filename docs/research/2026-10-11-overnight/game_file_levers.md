# Game-file and config-file levers, engine by engine (Steam Deck / Proton handheld, as of Oct 2026)

*Researched 2026-10-11. Scope: what can be changed in a game's own files and configs, with no source code, to save frame time on Steam Deck OLED handheld (target: locked 45 fps = 22.2 ms) without visible cost. This does not repeat the 2026-09-28 compendium, which covers tools and layers (OptiScaler, vkd3d-proton, RADV VRS, lsfg-vk, GFXReconstruct).*

*Evidence labels used throughout:*
- **[Measured]**: an A/B test with numbers or a described method.
- **[Author-tested]**: the author says they tested it, but published no data.
- **[Claim]**: an assertion with no test behind it.
- **[Prescriptive]**: a recommendation with no data.
- **[Anecdotal]**: forum or user reports.

*Access limits this session:*
- PCGamingWiki, GitHub raw files and Epic's documentation site could not be fetched. Their permission prompts went unanswered, or the page needed JavaScript.
- The web search budget ran out before Steam Cloud, Unity registry details and several secondary engines could be researched.
- Items that could not be sourced are listed under Gaps, marked "unverified." Where useful, they include my prior-knowledge expectation so someone can verify them later.

---

## Unreal Engine 4/5: where the inis live, which CVars move GPU cost, which only affect stutter, which are placebo, and how games lock files

### Takeaway
- **Biggest lever:** the GI/reflection method, meaning Lumen on or off, which on Deck is worth roughly 5–10 fps in one author-tested case, plus internal resolution (`r.ScreenPercentage`/TSR).
- **Stutter:** PSO precaching is set by the developer at project level. A player-side Engine.ini edit is unlikely to fix shader stutter.
- **Placebo:** Digital Foundry's A/B test found the popular "Ultimate Engine Tweaks" ini pack does nothing measurable in Oblivion Remastered.
- **Fragility:** ini edits can be overwritten by the game's own settings menu or by updates. Modders commonly lock them read-only.

### Cited Findings

**Placebo evidence (most important for DeckForge's search space)**
- **[Measured]** Digital Foundry A/B-tested the "Ultimate Engine Tweaks" (UET) Engine.ini mod in Oblivion Remastered (DF Direct, reported 6 May 2025).
  - Runs with the mod were "essentially a mirror run" of runs without it. Battaglia: "it runs the same." DF judged it placebo.
  - DF also tested the BSA Uncompressor mod and found a 1.9% difference, within run-to-run variance.
  - DF said many .ini mods are placebo, "though some may work." Neither the article nor DF identified which individual CVars, if any, had an effect. — [VideoGamer, 6 May 2025](https://www.videogamer.com/?p=1162217)
- UET is sold and distributed as a generic pack "for Unreal Engine 4/5+ Games" (Patreon "techoptimized"), with per-game Nexus versions. — [Patreon UET page](https://www.patreon.com/techoptimized/posts/ultimate-engine-133743054); [Nexus example](https://www.nexusmods.com/hellisus/mods/19)
- **[Claim]** Placebo config "fixes" also exist outside UE. CD Projekt Red removed Cyberpunk 2077's `memory_pool_budgets.csv`, calling it "leftover clutter from development that had no connection to the main game." CDPR said reported gains "may have been related to restarting the game." No measurements backed the original claims. — [PCGamesN, 6 Jan 2021](https://www.pcgamesn.com/cyberpunk-2077/config-file-fix)

**GPU-cost CVars with Deck-specific evidence**
- **[Author-tested]** Oblivion Remastered on Steam Deck: disabling Lumen with the Engine.ini lines below gained "between 5 and 10 FPS, depending on the scene." The comparison data appears only as screenshots.
  ```
  [/Script/Engine.RendererSettings]
  r.Lumen.DiffuseIndirect.Allow=0
  [ConsoleVariables]
  r.Lumen.DiffuseIndirect.Allow=0
  ```
  - **Visual cost:** "more grounded and possibly slightly darker," with less detail loss than the author expected.
  - **Overwrite risk:** changing Lumen settings in the in-game menu "may overwrite this parameter."
  - **Other menu settings:** lowering Foliage or View Distance causes pop-in and a duller scene. Turning off SSR "saves little" and changes the look noticeably.
  - **Shadows:** the P40L0X UET config caused "slight shadow degradation."
  - **Recommended menu settings:** Lumen HW RT off, Lumen SW RT Quality Low, Global Illumination Medium, XeSS Balanced, 1280x800, 30 fps cap. — [overkill.wtf Oblivion Remastered Deck settings (undated, 2025)](https://overkill.wtf/elder-scrolls-oblivion-remastered-best-settings-steam-deck)
- **[Claim]** Krupar101's script installs an optimized Engine.ini plus the "Lumen Begone" mod, with "performance" and "visuals" presets.
  - It claims a "stable 30 FPS" on Deck but gives no before/after numbers and doesn't list its CVars.
  - The author says to re-run it if "a game update overwrites the settings." — [overkill.wtf, 2 May 2025](https://overkill.wtf/steam-deck-oblivion-remaster-automatic-optimization)
- **[Prescriptive, developer-side]** A UE5 studio blog's Steam Deck profile:
  - Scalability groups: `sg.ResolutionQuality=80`, `sg.ViewDistanceQuality=2`, `sg.AntiAliasingQuality=2`, `sg.ShadowQuality=2`, `sg.GlobalIlluminationQuality=1`, `sg.ReflectionQuality=1`, `sg.PostProcessQuality=2`, `sg.TextureQuality=2`, `sg.EffectsQuality=2`, `sg.FoliageQuality=1`, `sg.ShadingQuality=2`.
  - Upscaling: `r.TemporalAA.Upscaler=1`, `r.ScreenPercentage=75`.
  - Dynamic resolution: `r.DynamicRes.OperationMode=1`, `MinScreenPercentage=60`, `MaxScreenPercentage=85`, `TargetedMS=16.0`.
  - It states "Lumen's ray tracing is too expensive for this hardware class." It recommends 2 shadow cascades instead of 4 and a 5000–8000-unit shadow distance.
  - No benchmarks were published. — [StraySpark, 1 Apr 2026](https://www.strayspark.studio/blog/shipping-60fps-ue5-steam-deck)
- **[Measured, rough]** Digital Foundry (Leadbetter) ran UE5 on a Deck under Windows. The Valley of the Ancients and Matrix demos "performed very poorly." Fortnite with Lumen (forced to the hardware-RT path by a bug), Nanite and Virtual Shadow Maps got "close to 30 FPS." No per-feature cost was isolated. — [Steam Deck HQ, 6 Jan 2023](https://steamdeckhq.com/news/unreal-engine-5-can-run-on-the-steam-deck/)

**Hidden features unlocked through Engine.ini**
- **[Author-tested]** In Metal Gear Solid Delta (UE5), Engine.ini lines reportedly enable hardware Lumen, Ray Reconstruction and DLSS frame generation.
  - Frame generation clearly worked.
  - Whether hardware Lumen was active could not be confirmed ("very slight" visual difference).
  - Tested on an RTX 5090, not Deck-relevant hardware. — [PC Gamer via Yahoo Tech, 1 Sep 2025](https://tech.yahoo.com/gaming/articles/ive-tested-simple-config-file-144501797.html)

**Stutter (PSO) versus GPU cost**
- Epic's explanation: shader compilation stutter happens when the engine discovers it needs a new shader right before a draw.
  - Unreal Engine 5.2 added PSO precaching, which "prevents most kinds of shader compilation stutters" but has coverage gaps.
  - Earlier bundled PSO caches needed automated level fly-throughs.
  - Drivers can save PSOs, which speeds up later sessions.
  - The fixes Epic describes are developer-side. No user-side fix is offered. — [GamingOnLinux summarizing Epic, 5 Feb 2025](https://www.gamingonlinux.com/2025/02/epic-games-devs-talk-about-solutions-to-the-unreal-engine-stuttering-issues-in-games/)
- **[Prescriptive]** The precaching CVars are `r.PSOPrecaching=1`, `r.PSOPrecache.Components=1`, `r.PSOPrecache.Resources=1` and `r.PSOPrecache.ProxyMaterial=1`.
  - They are shown in the project-level `DefaultEngine.ini`. Manual cache-recording CVar names "vary by engine version (5.2 through 5.7)."
  - One PSO compile costs "a couple of milliseconds to tens of milliseconds," and a runtime compile drops one frame. — [StraySpark, 18 Jun 2026](https://www.strayspark.studio/blog/ue5-shader-stutter-pso-precaching-playbook)

**File locations and locking**
- **Prefix layout:** Proton prefixes live under `~/.local/share/Steam/steamapps/compatdata/<APPID>/`. The Windows user folder is `pfx/drive_c/users/steamuser/`, with `AppData/Local/`, `AppData/Roaming/` and, for some games, `Documents`. — [GamingOnLinux guide, updated 24 Sep 2026](https://www.gamingonlinux.com/guides/view/how-to-find-where-steam-stores-proton-game-files/)
- **Concrete Deck path (UE5, Oblivion Remastered):** `/home/deck/.local/share/Steam/steamapps/compatdata/2623190/pfx/drive_c/users/steamuser/Documents/My Games/Oblivion Remastered/Saved/Config/Windows/`. — [overkill.wtf](https://overkill.wtf/elder-scrolls-oblivion-remastered-best-settings-steam-deck)
- **Read-only locking:** modders commonly tell users to set Engine.ini to read-only after editing, for example in DocDoBig's "Ultimate Engine.ini for Smooth 60 FPS" (Oblivion Remastered). That guide gives no measurements. — [Nexus article 81, 30 Apr 2025](https://www.nexusmods.com/oblivionremastered/articles/81)
- **Why edits don't apply (dedicated-server guide):** something else (a panel or launcher) rewrites the file; the wrong file or section was edited; the key isn't read by that build ("there is no complete supported key list"); Linux path case-sensitivity. — [Supercraft wiki (VEIN), 24 Sep 2026](https://supercraft.host/wiki/vein/fixing_game_ini_settings_not_applying/)
- **Universal Unreal Unlocker:** PC Gamer describes it as a mod that "adds an incredible photo mode to almost any UE4 game." Its console-unlock capabilities and Proton compatibility were not verified this session. — [PC Gamer](https://www.pcgamer.com/uk/universal-unreal-unlocker-photo-mode-mod/)

### Inferences
- **Where UE frame time comes from:** on Deck, most of the measurable GPU savings come from a few heavy systems: GI/reflection method (Lumen vs SSGI/none), internal resolution and upscaler, shadow method and cascade count, and foliage/view distance. The long tail of "tweak pack" CVars is mostly noise (DF's UET result). DeckForge should search a small, curated CVar set and measure every candidate, not apply packs.
- **Treat every CVar as unverified until measured:** if a CVar has no effect in a shipping build, the game behaves exactly as without it. That is what a placebo looks like (DF/UET; MGS Delta's HW Lumen ambiguity). DeckForge needs a per-game "did this CVar take effect?" check, such as a frame-time delta plus a pass-count or image diff, before crediting it.
- **Precedence:** the in-game menu can rewrite the same keys (overkill.wtf's Lumen warning). DeckForge must define which wins: the menu, GameUserSettings.ini, or the `[ConsoleVariables]`/`[SystemSettings]` sections of Engine.ini. It should re-check after each launch rather than rely on read-only flags, which block legitimate menu changes.
- **Stutter is not a frame-time problem:** shader stutter in UE is mostly a developer-side PSO-coverage issue. Player-side levers are the driver/Proton pipeline cache (Steam shader pre-caching, DXVK/vkd3d caches), not Engine.ini. DeckForge should report stutter separately from average frame time and not promise an ini fix.
- **Lumen as a quality lever:** turning Lumen off is a quality-for-performance trade with a visible but modest cost at 800p. That fits DeckForge's "budget reallocation" thesis. A "Lumen off + SSGI/AO on" profile is a candidate default to test on UE5 titles.

### Gaps
- **No official per-CVar cost numbers:** Epic's Lumen performance guide and scalability reference (dev.epicgames.com) would not render, so I have no official ms costs for Lumen, Virtual Shadow Maps, volumetric fog or SkyAtmosphere. No Deck-specific measured cost per feature was found for `r.Shadow.Virtual.Enable=0` (VSM to cascaded shadow maps), `r.VolumetricFog=0`, `r.SkyAtmosphere`, post-process quality or `r.Streaming.PoolSize`.
- **Unverified prior knowledge (needs checking):**
  - `r.DynamicGlobalIlluminationMethod` (0 none / 1 Lumen / 2 SSGI) and `r.ReflectionMethod` (0 / 1 Lumen / 2 SSR) are the cleaner Lumen switches.
  - UE4 games usually write to `.../Saved/Config/WindowsNoEditor/` and UE5 games to `.../Saved/Config/Windows/`. Most games use `AppData/Local/<Project>/Saved/Config/...`, not Documents.
  - CVars flagged as cheats are compiled out of shipping builds, so some ini lines silently do nothing.
  - Some games re-create or overwrite Engine.ini at launch.
- **Unverified prior knowledge, continued:**
  - Universal Unreal Unlocker (Frans Bouma, paid) can open the UE console and set CVars live. Whether it injects cleanly under Proton was not verified.
  - It is DLL injection, so it belongs in DeckForge Tier I.
- **No individually measured UET CVars:** no source broke down which UET CVars (if any) are effective. DF tested the package as a whole.
- **No Deck A/B of `r.ScreenPercentage` vs TSR vs FSR** in a UE5 game was found.

---

## Unity: boot.config, PlayerPrefs in the Proton registry, quality levels

### Takeaway
Unity exposes two file-level surfaces:
- **`boot.config`** in the game's `_Data` folder (engine flags such as graphics jobs). Steam "verify" resets it, and Easy Anti-Cheat can reject it.
- **PlayerPrefs** in the Windows registry under `HKCU\Software\<Company>\<Product>`. Under Proton this is the prefix's registry, so resolution, quality level and per-game settings can be edited without touching game files.

Measured evidence is thin.

### Cited Findings
- **PlayerPrefs location:** Windows standalone players store PlayerPrefs at `HKEY_CURRENT_USER\Software\<CompanyName>\<ProductName>`, with names from Player Settings. Native Linux players use `~/.config/unity3d/<Company>/<Product>`.
  - The docs page (as extracted) describes hashed key names (e.g., `DeckBase_h3232628825`) in the context of Windows editor Play mode.
  - Page version: Unity 6.6. — [Unity ScriptReference: PlayerPrefs](https://docs.unity3d.com/ScriptReference/PlayerPrefs.html)
- **Registry files in the prefix:** a Proton prefix contains the "Windows registry files" alongside drive_c. — [GamingOnLinux guide, 24 Sep 2026](https://www.gamingonlinux.com/guides/view/how-to-find-where-steam-stores-proton-game-files/)
- **[Anecdotal] boot.config graphics jobs (7 Days to Die, Unity):** adding `gfx-enable-native-gfx-jobs` to boot.config reportedly gave about 20% more fps on some hardware. One server operator reported 10+ fps.
  - Steam "validate local files" resets boot.config to defaults.
  - The change fails client-side EAC verification, so it only works offline or with EAC off.
  - It must be reapplied after every update. — [The Fun Pimps forums, 2020–2021](https://community.thefunpimps.com/threads/gfx-enable-native-gfx-jobs-flag-performance-increase.18407)
- Unity's issue tracker documents "force gfx jobs" as an engine-level setting that interacts with profiling. This confirms the flag family exists but says nothing about performance. — [Unity Issue Tracker](https://issuetracker.unity3d.com/issues/patch-gpu-profiler-is-disabled-even-when-force-gfx-jobs-is-set-to-off)

### Inferences
- **Under Proton**, Unity PlayerPrefs for a Windows build live in `compatdata/<APPID>/pfx/user.reg` under `[Software\\<Company>\\<Product>]`. They are text-editable with no change to the game's install files, so they survive "verify files." That makes them a Tier S lever. I could not fetch documentation confirming the exact user.reg encoding.
- **boot.config** is an install-dir file, so verify and updates revert it, and EAC games treat it as integrity-checked. DeckForge should treat it as Tier I (or "offline-only") whenever the game ships EAC.
- **Coverage:** Unity games vary widely (URP/HDRP/built-in, custom settings menus), so there's no universal CVar surface like UE's. The practical per-game levers are the quality-level index, resolution and any game-specific keys in PlayerPrefs.

### Gaps
- **Unverified registry details:**
  - user.reg value encoding for Unity PlayerPrefs (DWORD vs hex(3) binary for strings/floats).
  - Whether the `_h<hash>` key suffix also applies to standalone players. Prior knowledge says yes: classic keys look like `Screenmanager Resolution Width_h182942802`. This conflicts with the summarized docs reading and needs verification.
- **No Deck A/B found** for `gfx-enable-gfx-jobs` / `gfx-enable-native-gfx-jobs` under DXVK/vkd3d-proton. Graphics jobs may behave differently on translated D3D11/D3D12.
- **No source found** on editing `QualitySettings` assets in shipped builds (would need asset editing tools, e.g., UABE). Feasibility and legality were not researched.

---

## RE Engine (Monster Hunter Wilds): config.ini beyond the menu, REFramework capabilities, and what the Deck community found

### Takeaway
- **config.ini** in Wilds' install folder does contain settings beyond the menu, but the famous "fixes" are anecdotal and partly debunked.
- **REFramework scripts** gave the Deck community real levers: GI, volumetric fog, wind sim, post-process, mesh/foliage LOD bias, dynamic shadows, texture streaming. The best Deck config claimed ~30–45 fps with heavy visual cuts.
- **Patches changed the picture:** Capcom's 2025–26 patches made the community Deck config unnecessary by the author's own account. The game now reaches about 30 fps on Deck with upscaling.

### Cited Findings

**config.ini**
- **Location:** config.ini is in the install folder `steamapps\common\MonsterHunterWilds`.
- **"Resoltuion" typo:** fixing it went viral in March 2025. Results ranged from "no difference" to "30–40 fps," all anecdotal, mostly on high-end PCs.
- **Other edits users made:** `ParallelBuildProcessorCount` (8 → 16) and `RenderWorkerThreadPriorityAboveNormal=Enable`. — [The Game Post, 2 Mar 2025](https://thegamepost.com/monster-hunter-wilds-typo-configuration-file-pc-fps/)
- **Typo debunk:** further investigation suggested the typo also exists in the game's code, so fixing it "may change nothing." No gains were quantified for any of the edits. — [Icy Veins, 2 Mar 2025](https://www.icy-veins.com/monster-hunter-wilds/news/monster-hunter-wilds-performance-optimization-fps-boost/)

**"The Little Engine that Shouldn't" (Deck-specific config + mod bundle; author PFCacklefanny, v1.6, 3 Mar 2025 – 18 Dec 2025)**
- **config.ini changes:**
  - Texture quality below the menu minimum.
  - Shadow-caching and texture-filtering lines.
  - `ParallelBuildProcessorCount=4` (match physical cores).
  - The `[Render/Adapter]` section is machine-specific and must be copied from a game-generated file.
- **Locking:** after install, set the config read-only to stop the game overwriting it. In-game setting changes then don't persist.
- **REFramework scripts:**
  - OGU Lite Environment: disables wind sim, with GI and volumetric fog adjustments.
  - More Graphics Options: foliage LOD bias 2, leaf LOD 3.
- **Also used:**
  - Texture Decompressor (about 37 GB free space needed).
  - DirectStorageOption with `StagingBufferSize=32`.
  - Forced 1024x640 output, 90 Hz on OLED (60 Hz on LCD) and a GPU clock of 1600 MHz.
  - Launch option `WINEDLLOVERRIDES="dinput8.dll=n,b"`.
- **[Claim]** About 30–45 fps at 1600x900 Balanced, 1280x800 Quality or 1024x640 Native.
- **Now obsolete:** the author says "There is no need to follow this guide anymore" after update 1.040.03.02. Users should delete it and let the game regenerate config.ini.
- **Updates add lines:** v1.5 notes that game updates added config lines. — [Nexus mod 183](https://www.nexusmods.com/monsterhunterwilds/mods/183)
- **[Claim/Anecdotal] Contemporaneous coverage:**
  - The mod creator said ~30 fps with frame gen at 1024×640 Quality or 800p Balanced, and "close to a solid 30" without frame gen using Lite Environment with all options.
  - One Reddit user reported "locked 10 fps." — [Destructoid, 17 Mar 2025](https://destructoid.com/steam-deck-users-enjoy-monster-hunter-wilds-at-sub-30-fps)

**REFramework-based mods**
- **Lite Environment – OGU** (HolographicWings, v2.2.2, end of support, last updated 16 Dec 2025):
  - REFramework script that toggles off wind simulation, GI and volumetric fog.
  - **[Claim]** "Up to +15 FPS" on a GTX 1080 Ti with frame gen.
  - Disabling GI/VF broke cutscenes. Later versions re-enable them during cutscenes by default. — [Nexus mod 234](https://www.nexusmods.com/monsterhunterwilds/mods/234)
- **More Graphics Options** (Aiyke): mesh LOD bias, foliage LOD offset/bias, disable texture streaming, disable dynamic shadows, small-object culling ratio.
  - **[Claim]** "Can also improve the game's performance," with "considerable" visual impact. — [Wccftech, 17 Mar 2025](https://wccftech.com/monster-hunter-wilds-new-graphics-options/amp/)
- **Disable Post-Processing Effects** (TonWonton, v2.1.0, updated 6 Sep 2026):
  - Toggles AA/TAA, color correction, vignette, sharpening, exposure/local/auto exposure, contrast/gamma, volumetric fog, film grain and lens distortion.
  - Comes in a Lua version and a C# version (REFramework C# API + .NET 10 runtime).
  - Disabling TAA has no effect when DLSS or another upscaler is active. No fps claims. — [Nexus mod 221](https://nexusmods.com/monsterhunterwilds/mods/221)

**REFramework itself**
- Lua scripting API and plugin system, Object Explorer, FOV slider, vignette disabler, ultrawide fixes.
- Supports DX11 and DX12, and lists Monster Hunter Wilds.
- **Proton install:** put `dinput8.dll` in the game folder plus the launch option `WINEDLLOVERRIDES="dinput8.dll=n,b" %command%`. — [REFramework GitHub README](https://github.com/praydog/REFramework)
- **[Claim]** In March 2025, REFramework (praydog) was reported to reduce Wilds stutter that the article attributes to Capcom's proprietary anti-tamper (not Denuvo). Capcom did not confirm, and no independent numbers were given. — [Multiplayer.it, 12 Mar 2025](https://multiplayer.it/notizie/una-mod-migliora-la-fluidita-di-monster-hunter-wilds-su-pc-contrastando-la-tecnologia-anti-tamper-di-capcom.html)

**Texture decompression mod and official patches**
- **[Measured, second-hand]** Digital Foundry, via Gfinity, on a texture mod that replaces GDeflate-compressed assets with uncompressed ones (installed through REFramework's loose file loader):
  - Frame-time spikes "simply vanished" on an 8 GB GPU.
  - Install size grew from ~24 GB to ~41 GB.
  - Framed as temporary until Title Update 4. — [Gfinity, 20 Nov 2025](https://www.gfinityesports.com/article/monster-hunter-wilds-performance-fixed-on-pc-but-you-need-this-mod-first)
- **[Measured, second-hand]** January 2026 PC performance patch: per Daniel Owen, minimum fps rose about 8% over Title Update 4 and about 20% over Title Update 3.
  - Wilds is "roughly playable" at about 30 fps on Deck without frame gen, with FSR/XeSS upscaling. The exact Deck settings weren't given. — [Notebookcheck, 30 Jan 2026](https://www.notebookcheck.net/Monster-Hunter-Wilds-fixes-DLC-bug-greatly-reduces-FPS-drops-and-runs-at-30-FPS-on-Steam-Deck.1215270.0.html)
- **[Claim, internally inconsistent]** EveZone (12 Feb 2026, modified 23 May 2026) claims a "stable 40FPS" on Deck at 40 Hz with a 4 GB UMA buffer, FSR 3 Balanced/Performance and mostly Low settings. Its FAQ contradicts its body (FSR 2, 720p, TDP 7–10 W). No measurements. — [EveZone](https://evezone.evetech.co.za/performance-pulse/steam-deck-40fps-settings-mh-wilds)
- **[Anecdotal]** A Deck user reported "around 40+ FPS" with REFramework plus mods 221, 331 (Disable Ambient Lighting), 234 and 183. Another user's Steam "verify" flagged two modified files for redownload. — [Steam discussion, Apr 2025](https://steamcommunity.com/app/2246340/discussions/0/596271270005369411)

### Inferences
- **Wilds' lever map, by cost:**
  - **config.ini (Tier S):** texture quality, shadow caching, thread counts. Install-dir file, so updates and verify can rewrite it.
  - **REFramework scripts (Tier I):** GI off, volumetric fog off, wind sim off, post-process toggles, mesh/foliage LOD bias, dynamic shadows off. These are the strongest below-menu GPU levers, with visible costs (darker or flatter lighting, pop-in, broken cutscenes).
  - **Asset swap:** texture decompression. Costs disk space, fixes CPU-side streaming stutter.
- **Re-baseline before reusing community configs:** official patches made 2025 community configs obsolete or harmful (author says delete). DeckForge must key every Wilds recommendation to the game build number and re-baseline after each title update.
- **Read-only config conflicts with DeckForge's model:** a read-only config.ini blocks in-game changes. Better: write the file through `deckforge.safety`, re-apply on launch if the game reverted it, and never chmod it.
- **No source supports the "fixes":** neither the "Resoltuion" typo nor `RenderWorkerThreadPriorityAboveNormal` has measured support. Exclude them from defaults unless DeckForge's own bench shows an effect.
- **Fit with DeckForge's target:** 45 fps native on Deck in Wilds is beyond anything reported, even with mods. The best credible native results are ~30 fps; "40+" claims are unmeasured or use heavy cuts. Wilds is a "problem (b)" game (built for much stronger hardware) per the compendium, so the honest target there may be 30–40 native.

### Gaps
- **No measured Deck frame-time breakdown** (GI vs fog vs shadows) for the REFramework toggles. The compendium's E1 (RGP capture) would answer this.
- **Anti-tamper status unconfirmed:** whether Wilds' anti-tamper or any online integrity check reacts to REFramework or config edits. The game has online co-op, and I found no Capcom statement.
- **Coverage of the Disable Ambient Lighting mod (331)** and of current config.ini keys after the 2026 patches was not checked.
- **REFramework docs not read:** the wiki (refdocs.praydog.com) was not fetched, so there's no list of the engine-level render parameters scripts can reach (e.g., via.render settings).

---

## Swarm engine (Space Marine 2, Saber Interactive): config locations, hidden settings, EAC constraints

### Takeaway
- **Files:** Space Marine 2 stores user data under `AppData/Local/Saber/Space Marine 2/storage/steam/user/<SteamID>`, which under Proton is inside `compatdata/2183900`. It ships Easy Anti-Cheat (EOS).
- **No hidden settings found:** I found no documented hidden render settings and no measured file tweaks.
- **Practical levers:** the in-menu settings (FSR, Low textures and shadows, SSR off, volumetrics Low) plus the frame-gen/upscaler support added in a December 2024 patch.

### Cited Findings
- **Save/user data path:** `C:/Users/<user>/AppData/Local/Saber/Space Marine 2/storage/steam/user/<STEAM ID>`. The article names no config file and no editable hidden settings. — [Prima Games, 6 Sep 2024 (mod. 15 Nov 2024)](https://primagames.com/?p=279357)
- **IDs and anti-cheat:** the Steam App ID is 2183900, and the game uses `EasyAntiCheat_EOS`. A Windows BSOD workaround thread tells users to delete EAC driver files. The executable is `Warhammer 40000 Space Marine 2 - Retail.exe` under `client_pc\root\bin\pc`. — [Steam discussion, Sep 2024](https://steamcommunity.com/app/2183900/discussions/0/4763207778563513263)
- **[Author-tested, no data] Deck settings at launch:**
  - Output 1280×800, FSR 2, 30 fps cap, TDP 15 W.
  - Textures Low (the "4 GB VRAM" preset), Shadows Low, SSR off, Volumetrics Low, Effects/Details/Cloth Low.
  - Reported roughly 20–30 fps, with drops into the low 20s in big battles. No config edits mentioned. — [The Backdash, 6 Sep 2024](https://www.thebackdash.com/tech/space-marine-2-steam-deck-settings)
- **December 2024 patch:** a GamingOnLinux headline states it "adds DLSS3, FSR3 and frame generation, more playable on Steam Deck, needs launch option for desktop Linux." Only the headline was retrieved, not the article body. — [GamingOnLinux, Dec 2024](https://www.gamingonlinux.com/2024/12/space-marine-2-adds-dlss3-fsr3-and-frame-generation-more-playable-on-steam-deck-needs-launch-option-for-desktop-linux/page=1/)

### Inferences
- **Proton path (inferred):** `~/.local/share/Steam/steamapps/compatdata/2183900/pfx/drive_c/users/steamuser/AppData/Local/Saber/Space Marine 2/storage/steam/user/<SteamID>/`. This combines the Prima path with GamingOnLinux's prefix layout.
- **Tier S only:** with EAC (EOS) and online co-op, DeckForge's existing rule gives Space Marine 2 Tier S only. Any file it touches should be a user-profile settings file in the prefix, never an install-dir or packed-asset file, because EAC integrity checks typically cover the install directory. That's an inference; no Saber/EAC statement was found.
- **Low upside:** with no documented hidden settings, DeckForge's search for Space Marine 2 is the menu space (upscaler, resolution, per-setting Low/Medium) plus OS-level knobs. Expect "BLOCKED at ~30 fps native in hordes" as the honest result.

### Gaps
- **No authoritative source** on the exact settings file name, its format or whether it holds keys beyond the menu (prior knowledge suggests a text config inside the per-user folder; unverified). PCGamingWiki's Space Marine 2 page was not reachable.
- **No source** on whether EAC validates user-folder config files or only install files, or whether Space Marine 2 is Steam Cloud-synced for settings.
- **No measured Deck results** after the Dec 2024 FSR 3 / frame-gen patch or later 2025–26 patches.

---

## Other engines (Frostbite, id Tech, Decima, Creation, Snowdrop, Anvil, REDengine): which allow meaningful tweaks

### Takeaway
Only fragments were sourced this session:
- **Frostbite (Battlefield 6):** `user.cfg` still exists, but at least some valid console commands reportedly don't apply through it. BF6 isn't a Deck target anyway because of anti-cheat (unverified).
- **REDengine (Cyberpunk 2077):** the most famous config "fix" was placebo.

Everything else is listed as an unverified gap.

### Cited Findings
- **[Anecdotal] Frostbite, Battlefield 6:** a player reports that commands that work in the in-game console do not apply via `User.cfg`. Examples: `PostProcess.DofMethod 0`, `WorldRender.MotionBlurEnable 0`, `Thread.ProcessorCount 16`. DOF stayed on, and `Thread.ProcessorCount` printed -1. No EA/DICE reply. — [EA Forums, ~Sep 2026](https://forums.ea.com/discussions/battlefield-6-technical-issues-en/valid-game-console-commands-do-not-apply-through-user-cfg/13668511)
- Community "user.cfg" packs for BF6 continue to circulate with claims of fixing FPS drops and stutter. Titles only; contents not verified. — [EA Forums](https://forums.ea.com/discussions/battlefield-6-technical-issues-en/battlefield-6-%e2%80%93-raw-core-user-cfg-v2-6-fixes-fps-drops--stutter/12914570); [Mein-MMO](https://mein-mmo.de/battlefield-6-user-cfg-profsave_profile-aendern/)
- **REDengine, Cyberpunk 2077:** the `memory_pool_budgets.csv` edit was unmeasured. CDPR removed the file as dev clutter and attributed gains to restarting the game. — [PCGamesN, Jan 2021](https://www.pcgamesn.com/cyberpunk-2077/config-file-fix)
- Cyberpunk has Nexus mods that ship engine config overrides (e.g., mod 1642's docs tab). Contents not retrieved. — [Nexus mod 1642](https://www.nexusmods.com/cyberpunk2077/mods/1642/?tab=docs)

### Inferences
- **Treat community config packs as placebo by default:** two famous config-file "performance fixes" (Cyberpunk's CSV, UE's UET) were placebo or dev clutter. This is strong evidence for that default, with DeckForge's bench as the only arbiter.
- **Frostbite user.cfg is partly honored:** at least some commands are ignored. DeckForge would need a readback check (the console prints the value) per command per build, which is impractical without in-process access. Low priority, especially since most Frostbite multiplayer titles carry anti-cheat.

### Gaps (unverified prior knowledge; verify before use)
- **id Tech (DOOM 2016/Eternal/The Dark Ages, Indiana Jones):**
  - Some console variables can be set via launch options (`+cvar value`), with limited documented performance levers.
  - Newer id Tech titles require ray-tracing-capable GPUs, so Deck viability depends on RADV RT. Not researched.
- **Decima (Horizon, Death Stranding PC ports):** no known user config surface beyond the menu (prior knowledge). Not verified.
- **Creation Engine (Skyrim/Fallout 4/Starfield):** extensive `*Custom.ini`/`*Prefs.ini` files in `Documents/My Games/<Game>/`, with many real render toggles (shadow distance and resolution, grass, LOD fade, volumetrics). Long, well-known tweak tradition. Not sourced this session.
- **Snowdrop (Avatar, Star Wars Outlaws, The Division 2):** settings files in `Documents/My Games/<Game>/`. Avatar/Outlaws reportedly have hidden "Unobtanium"-type settings unlocked by launch flag. Not sourced.
- **Anvil (Assassin's Creed):** `ACX.ini`-style files in `Documents/Assassin's Creed <title>/` with mostly menu-equivalent keys. Not sourced.
- **REDengine 4, Cyberpunk:** user settings in `AppData/Local/CD Projekt Red/Cyberpunk 2077/UserSettings.json`. Engine overrides via `engine/config/platform/pc/*.ini` in the install dir (install dir, so reverted by verify/updates). Not sourced.
- **Overall:** a per-engine "meaningful tweak" ranking cannot be stated with evidence from this session. PCGamingWiki per-game pages are the right next source.

---

## Asset-level options: lower-res texture packs, LOD bias via DXVK/driver, "potato" mods (realistic and legal?)

### Takeaway
Asset-level cost reduction is real but game-specific:
- **Wilds:** the strongest documented examples are mesh/foliage LOD bias, disabled dynamic shadows and below-menu texture quality (all REFramework/config), plus uncompressed textures, which trade disk for stutter.
- **DXVK `samplerLodBias`** exists for D3D9/D3D11. I couldn't fetch its documentation, and found no Deck measurements of LOD-bias savings.

### Cited Findings
- **Wilds below-menu reductions:**
  - Mesh LOD bias, foliage LOD bias, small-object culling ratio, disabling dynamic shadows and disabling texture streaming are exposed by the More Graphics Options REFramework mod, with "considerable" visual impact. — [Wccftech, 17 Mar 2025](https://wccftech.com/monster-hunter-wilds-new-graphics-options/amp/)
  - The Deck config uses foliage LOD bias 2 / leaf LOD 3 and texture quality below the menu floor. — [Nexus mod 183](https://www.nexusmods.com/monsterhunterwilds/mods/183)
- **Texture decompression (Wilds):**
  - Removing GDeflate compression eliminated frame-time spikes (DF, second-hand), at +17 GB disk. — [Gfinity, Nov 2025](https://www.gfinityesports.com/article/monster-hunter-wilds-performance-fixed-on-pc-but-you-need-this-mod-first)
  - The Deck guide warns against premade "Texture Decompression Removal" files, which cause missing textures. It recommends the decompressor tool instead (~37 GB free needed). — [Nexus mod 183](https://www.nexusmods.com/monsterhunterwilds/mods/183)
- **Low texture setting as a VRAM lever:** Space Marine 2's Deck recommendation uses Low textures (the "4 GB VRAM" preset). — [The Backdash, Sep 2024](https://www.thebackdash.com/tech/space-marine-2-steam-deck-settings)
- **DXVK release notes:** DXVK 2.1 added `dxgi.enableHDR`, `d3d9.forceSampleRateShading` and `d3d11.forceSampleRateShading`. That release's notes do not mention LOD bias, so `samplerLodBias` was added in a different version. — [newreleases.io DXVK v2.1](https://newreleases.io/project/github/doitsujin/dxvk/release/v2.1)

### Inferences
- **LOD bias is a bandwidth lever:** a positive texture LOD bias (blurrier mips) mainly saves memory bandwidth, which the compendium flags as the Deck's real limiter. Mesh/foliage LOD bias saves vertex work and draw calls, a CPU and geometry lever. These are different knobs and should be measured separately.
- **Asset swaps are Tier I:** texture packs and decompression change install-dir game data, so verify and updates revert them. They can also trigger integrity checks. They belong in Tier I (opt-in, offline or no anti-cheat).
- **Legality:** I found no source on EULA or legality. Practically, these mods are distributed openly on Nexus for single-player use. DeckForge should orchestrate user-installed mods, not redistribute game assets.

### Gaps
- **dxvk.conf documentation not fetched** (GitHub and Debian sources needed permission or JavaScript). Unverified prior knowledge:
  - `d3d11.samplerLodBias` / `d3d9.samplerLodBias` (float) and `d3d11.clampNegativeLodBias` / `d3d9.clampNegativeLodBias` exist. The clamp is useful for undoing a game's negative TAA/upscaler bias.
  - `d3d11.samplerAnisotropy` / `d3d9.samplerAnisotropy` exist.
  - dxvk.conf is read from the game's working directory or from `DXVK_CONFIG_FILE`. Newer versions also accept a `DXVK_CONFIG` environment string.
  - Must verify the exact names and versions before DeckForge writes any dxvk.conf (R14).
- **vkd3d-proton (D3D12):** whether it has an equivalent LOD-bias option is unknown. Prior knowledge says no general one. D3D12 games would then need the compendium's `vkCreateSampler` layer hook instead.
- **No measured Deck data** for sampler LOD bias, anisotropy reduction or low-res texture packs.
- **Lower-resolution texture packs** as official DLC (e.g., optional "high-res" packs that can be uninstalled) were not researched.

---

## Risks: anti-cheat integrity checks, Steam "verify files", updates overwriting configs, Steam Cloud syncing

### Takeaway
- **Install-dir edits are fragile:** edits to install-directory files (boot.config, RE Engine config.ini, packed assets) are reverted by Steam verify or updates and can fail anti-cheat integrity checks.
- **Prefix edits are safer, but not safe:** edits to user-profile files in the Proton prefix (UE Saved/Config, Unity registry, Saber user folder) survive verify. The game's own menu or a patch can still overwrite them.
- **Steam Cloud not researched:** whether it syncs config files between Deck and PC wasn't covered, so it's an open risk.

### Cited Findings
- **Verify reverts install-dir edits; EAC rejects them:** Steam "validate local files" resets Unity boot.config edits, and the edit fails client-side EAC verification. — [The Fun Pimps forums, 2020–21](https://community.thefunpimps.com/threads/gfx-enable-native-gfx-jobs-flag-performance-increase.18407)
- **Verify flags modded files:** a Wilds user's Steam verify flagged two modified files for redownload. — [Steam discussion, Apr 2025](https://steamcommunity.com/app/2246340/discussions/0/596271270005369411)
- **Game updates change config files:**
  - The Wilds Deck config changelog notes "Added lines brought with TU4." After a later update the author says to delete the custom config entirely. — [Nexus mod 183](https://www.nexusmods.com/monsterhunterwilds/mods/183)
  - The Oblivion Remastered Deck script must be re-run if "a game update overwrites the settings." — [overkill.wtf, May 2025](https://overkill.wtf/steam-deck-oblivion-remaster-automatic-optimization)
- **The in-game menu overwrites ini edits:** changing Lumen in Oblivion Remastered's menu "may overwrite" the Engine.ini Lumen line. — [overkill.wtf](https://overkill.wtf/elder-scrolls-oblivion-remastered-best-settings-steam-deck)
- **Read-only locking is the common community workaround,** but in-game settings then stop persisting. — [Nexus mod 183](https://www.nexusmods.com/monsterhunterwilds/mods/183); [Nexus Oblivion article 81](https://www.nexusmods.com/oblivionremastered/articles/81)
- **Anti-cheat and mods:** Space Marine 2 ships EAC EOS. — [Steam discussion](https://steamcommunity.com/app/2183900/discussions/0/4763207778563513263)
- **Wilds' anti-tamper and REFramework:** REFramework was reported to work around stutter attributed to Capcom's anti-tamper. This shows Wilds has anti-tamper code that DLL injection interacts with. Capcom has not confirmed. — [Multiplayer.it, Mar 2025](https://multiplayer.it/notizie/una-mod-migliora-la-fluidita-di-monster-hunter-wilds-su-pc-contrastando-la-tecnologia-anti-tamper-di-capcom.html)

### Inferences
- **Two classes of files, different rules:**
  - **Class P (prefix user files):** UE `Saved/Config/*`, Unity registry, Saber user folder, `Documents/My Games/*`. They survive verify, are usually not integrity-checked, but can be rewritten by the game's menu and by patches. This is the natural home for Tier S edits.
  - **Class I (install-dir files):** RE Engine config.ini, Unity boot.config, dxvk.conf placed beside the exe, mods, asset packs. Verify and updates revert them, and they're the likeliest to be integrity-checked. Tier I unless proven otherwise per game.
- **Drift detection instead of read-only flags:** DeckForge should record a content hash of every file it writes (the R10 manifest). On each launch it should detect drift (menu change, patch, verify, cloud sync) and re-validate against the current game build before re-applying. That's safer than chmod read-only, which silently freezes the menu.
- **Gate on build number:** game updates can invalidate a tuned profile (Wilds' 2025 configs became harmful after the 2026 patches). Every stored profile should carry the game's Steam build ID and be re-benchmarked when it changes.
- **Wilds' config.ini is install-dir:** DeckForge's Tier S definition ("in-game settings files") should be refined. Some games store settings in the install directory, where verify and updates (and potentially anti-tamper) touch them.

### Gaps
- **Steam Cloud:** no source found on which games sync config/ini files via Steam Cloud, or how a Deck-tuned config interacts with a desktop PC through cloud sync. Search budget was exhausted. PCGamingWiki lists Steam Cloud coverage per game (including whether config is synced). That is the source to consult per title.
- **No primary EAC/BattlEye documentation** on what is integrity-checked (install directory only vs user folders, or config file hashes). The evidence here is anecdotal (7 Days to Die boot.config).
- **No source** on whether vkd3d-proton/DXVK config files (dxvk.conf in the game folder) trip anti-cheat. Prior knowledge: DXVK itself is used under Proton regardless, so a config file beside the exe is unlikely to matter, but this is unverified.
- **No data on SD-card installs:** for games on an SD card, the compatdata prefix lives in that library's `steamapps/compatdata`. That's prior knowledge, unverified; DeckForge's path resolver must handle multiple library folders.
