# How feasible is it to reverse engineer a AAA PC game so it renders 1.5–3× cheaper on a Steam Deck? (as of 12 Oct 2026)

Labels used throughout: **[measured]** means a source measured it, **[claimed]** means a source asserts it without data, **[inference]** is my own reasoning. All dates are publication dates. No files were written.

**Overall answer:** No. "Understanding everything" in a protected AAA executable is not feasible for agents plus one non-programmer.

- **What an agent can reach:**
  - the GPU shaders, through vkd3d-proton's dump and override switches;
  - the engine's own exposed parameters, through the RE Engine reflection system that REFramework uses;
  - the asset files.
- **Expected gain from those routes:**
  - About 1.2–1.5× in GPU-bound Wilds scenes, at a clearly "potato" visual cost.
  - About 1.0–1.15× in CPU-bound scenes.
  - None of these routes are allowed for Space Marine 2.
- **What 2–3× needs:** real downports got there with algorithm rewrites (Witcher 3's grass and shadows) and structural changes (Hogwarts on Switch cut the world into zones with loading screens). Those need source code or the developer.

---

## 1. Scale: binaries, engines, shaders, and what "understand everything" costs an LLM

### Takeaway
- Executables run to hundreds of MB, and much of that size can be protection code. Engine source runs to millions of lines.
- A single match of an Unreal Engine game compiles tens of thousands of GPU pipelines (compiled shader-plus-state objects) out of millions possible.
- Even with Claude's 1M-token context, one read-through of a decompiled engine is about 50–160 full context windows. Agentic analysis multiplies that many times over.
- So "understand everything" is the wrong goal. The only workable approach is "understand only the hot paths."

### Cited Findings
- **[measured, by the source's author]** Devil May Cry 5 (Capcom RE Engine): a Denuvo-free executable is about 128 MB, versus about 475 MB for the shipped protected one. The author says the gap exists because Denuvo's checking code "is woven throughout the game code." The page did not show a date. — [TechPowerUp](https://www.techpowerup.com/review/denuvo-performance-loss-test/)
- **[measured, SteamDB logs]** When Capcom removed Denuvo from Resident Evil 4 Remake, its executable became "422MB smaller." No absolute sizes were given. Published 3 Feb 2026. — [OC3D](https://overclock3d.net/news/software/capcom-removes-denuvo-from-its-resident-evil-4-remake/)
- **[measured, 2019]** Klocwork static analysis of Unreal Engine 4 covered 2,292,918 lines of code. — [Perforce, 22 Jul 2019](https://www.perforce.com/blog/kw/unreal-engine-and-static-analysis)
- **[claimed]** An empty Unreal Engine 5 project packages to over 321 MB. Debug symbols alone are 500 MB to over 2 GB. Neither figure is the executable on its own. — [StraySpark, 25 Mar 2026](https://www.strayspark.studio/blog/ue5-packaging-shipping-build-size-optimization)
- **[claimed by Epic]** Shader and pipeline counts in Unreal games:
  - Many Unreal games have "thousands of materials."
  - Covering every combination would mean compiling "millions" of pipelines.
  - One Fortnite Battle Royale match compiles about 30,000 pipelines and actually uses about 10,000.
  - Keeping all precompiled pipelines in memory would take over 1 GB.
  - Permutations multiply because:
    - each material spawns a different vertex shader for static, skinned and spline meshes;
    - vertex and pixel shaders pair in many ways;
    - render states (culling, blending, depth test) multiply the variants again.

  Source: [Epic tech blog, 4 Feb 2025](https://www.unrealengine.com/zh-CN/tech-blog/game-engines-and-shader-stuttering-unreal-engines-solution-to-the-problem)
- **[documented]** Current Claude API models and limits:

  | Model | Context window | Max output | Price per million tokens (input / output) |
  |---|---|---|---|
  | Fable 5.1 | 1M | 128K | $10 / $50 |
  | Opus 5.5 | 1M | 128K | $4 / $20 |
  | Sonnet 5.5 | 1M | 128K | $2 / $10 |
  | Haiku 5.5 | 1M | 128K | from $0.10 / $0.50 |

  Source: [Claude models overview, fetched 12 Oct 2026](https://platform.claude.com/docs/en/models/overview)
- **[measured, anecdotal]** In the River Raid experiment, Claude-to-Ghidra tool calls (Ghidra is a free disassembler and decompiler) took about 30 seconds each. — [Quesma, 23 Jan 2026](https://quesma.com/blog/ghidra-mcp-unlimited-lives/)
- **[claimed, self-reported, weak source]** One Claude Code modding pipeline had to split larger binaries into chunks to fit its API context. — [gerdennisai.com, 6 Oct 2026](https://gerdennisai.com/blog/claude-code-game-modding-agents)

### Inferences
- **Engine source in tokens [inference].**
  - At about 10 tokens per line of C++, UE4's 2.3M analysed lines are about 23M tokens, roughly 23 full 1M-token contexts.
  - UE5 is larger; I found no reliable count.
  - One read of that at Opus 5.5 input rates costs about $90. Agentic work re-reads code many times, so real cost is 10–100× that, or about $1k–$10k.
  - Even with the source, you cannot hold the engine in context. You can only search it.
- **A protected executable in tokens [inference].** Using an RE Engine binary of about 128 MB without Denuvo:
  - If half of it is code at about 4 bytes per x86-64 instruction, that is about 16M instructions, or roughly 100k–200k functions.
  - Disassembled, that is about 150M tokens; decompiled to C-like code, perhaps 50–100M tokens.
  - That is about 50–160 full 1M windows for a single read, and about $200–$640 of input at Opus 5.5 rates.
  - At about 30 seconds per decompilation call, pulling 150k functions one at a time would take about 50 days.
  - Decompiled output has no names or types, so "reading" it is not "understanding" it.
- **Shaders are the more tractable target [inference].** Each game has thousands of shaders, usually tens of thousands of pipelines. They reach the driver as plain D3D12 shader code, not protected x86 code, and vkd3d-proton can already dump and replace them by fingerprint (prior DeckForge research). The CPU-side logic that decides which passes run, and at what resolution, sits inside the protected executable.
- **Realistic goal [inference].** Profile first to find the 5–20 GPU passes and CPU systems that dominate the frame. Then reverse engineer only those, by behaviour (hooks plus measurement), not by reading the whole binary.

### Gaps
- **Wilds executable size:** not found. Check `MonsterHunterWilds.exe` locally or in SteamDB's depot history. Given RE4R's 422 MB shrink and DMC5's 475 MB, expect several hundred MB [inference].
- **Line counts:** no reliable figure for UE5. RE Engine and Saber's Swarm engine are closed source, so they have no public counts.
- **Wilds shader and pipeline counts:** no public number found. They can be measured by counting files from a vkd3d-proton dump on the Deck.
- **Long-context pricing:** the models page did not say whether the 1M-token window costs extra.

---

## 2. Protection: Denuvo, VMProtect-style virtualization, Capcom's anti-tamper, and how RE Engine modders work anyway

### Takeaway
- Wilds is reported to ship both Denuvo and Capcom's own anti-tamper. I found no evidence that either was removed by October 2026, although Capcom has stripped Denuvo from older titles during 2026.
- Protection makes full static decompilation impractical: checking code is woven through the game, and virtualization replaces real code with custom bytecode.
- RE Engine modders work around this, not through it:
  - **REFramework** loads at runtime as a stand-in DLL and calls the engine's own reflection system (a built-in catalogue of types, methods and fields, the "type database"). It lets scripts call engine methods and read or set fields by name.
  - **Asset mods** replace data files.
  - Neither decompiles engine algorithms.

### Cited Findings
- **[checked by the lead, 12 Oct 2026]** The Steam store page states "Incorporates 3rd-party DRM: Denuvo Anti-tamper". Press also reports a separate Capcom anti-tamper layer. [Lead's note: the original citation here was a news item about cracking the protection; it has been removed so this note links no circumvention reporting.] — [Steam store](https://store.steampowered.com/app/2246340/Monster_Hunter_Wilds/)
- **[claimed, user forum, no year shown]** A Steam thread, "Will the next update remove Denuvo?", assumes Denuvo is still present. Replies guess at removal "in 2 years." — [Steam discussion](https://steamcommunity.com/app/2246340/discussions/0/761806632715983858/)
- **Capcom's 2026 Denuvo removals:**
  - **[reported]** Resident Evil 4 Remake: Denuvo removed, 3 Feb 2026. — [OC3D](https://overclock3d.net/news/software/capcom-removes-denuvo-from-its-resident-evil-4-remake/)
  - **[reported, inferred from the store page]** Dragon's Dogma 2: Denuvo "appears" removed, 2 Sep 2026. The page says nothing about Wilds' DRM status. — [GamingOnLinux](https://www.gamingonlinux.com/2026/09/dragons-dogma-2-gets-a-big-upgrade-and-denuvo-drm-removed/)
- **[claimed, disputed, Mar 2025]** Community members disagree about which parts of Wilds' protection are Denuvo and which are Capcom's own anti-tamper. [Lead's note: internal component names from that thread were removed; they are not needed for this assessment.] — [Steam thread, 5 Mar 2025](https://steamcommunity.com/app/2246340/discussions/0/599646234919121475)
- **[claimed, with a frametime screenshot]** praydog's March 2025 REFramework update fixed Wilds stutters and crashes that he attributed to Capcom's anti-tamper. DSOGaming's author guesses the stutters were not caused by Denuvo. — [DSOGaming, 5 Mar 2025](https://dsogaming.com/?p=186512); [Lowyat, 6 Mar 2025](https://lowyat.net/2025/344742/modder-fix-stuttering-issue-in-mh-wilds)
- **[technical, 2021] How VMProtect 2 virtualization works:**
  - It turns native x86 code into a per-binary encrypted, stack-based bytecode, run by "handler" routines.
  - Branches become stack arithmetic, and arithmetic is obscured as NAND sequences.
  - Recovering the logic needs handler profiling, emulation, branch detection and lifting into an intermediate form.
  - Full conversion back to x86 is "not a job for a single person."

  Source: [back.engineering / aftermathlabs, 21 Jun 2021](https://aftermathlabs.net/blog/21/06/2021/)
- **[documented] How REFramework loads and what it exposes:**
  - It installs as `dinput8.dll` in the game folder. On Proton it needs `WINEDLLOVERRIDES="dinput8.dll=n,b"`.
  - It offers a Lua scripting and plugin API, an Object Explorer, and a list of supported RE Engine games that includes Wilds.
  - Stable releases and a separate nightly repository exist.

  Source: [REFramework README](https://github.com/praydog/REFramework)
- **[documented] What REFramework scripts can reach:**
  - Lua calls methods and reads or writes fields listed in the engine's type database ("only the TDB versions are fully supported").
  - It can fetch the engine's "managed" (C#-side) and native singleton objects.
  - Native plugins get per-frame callbacks and `BeginRendering`/`EndRendering` callbacks.
  - For some data edits, the book points to a separate tool, RE_RSZ.

  Source: [REFramework book](https://cursey.github.io/reframework-book/)
- **[reported] Asset modding in Wilds runs through REFramework's loose-file loader.** The MHWS-TEX-Decompressor mod swaps GPU-decompressed (GDeflate) textures for uncompressed ones. It needs REFramework Nightly and raises the install from about 24 GB to about 41 GB. — [PC Games Hardware, 23 Nov 2025](https://www.pcgameshardware.de/Monster-Hunter-Wilds-Spiel-74697/News/Performance-Patch-Update-Community-Mod-1487048/); [Gfinity, 20 Nov 2025](https://www.gfinityesports.com/article/monster-hunter-wilds-performance-fixed-on-pc-but-you-need-this-mod-first)

### Inferences
- **What protection blocks [inference].** It mostly blocks route (d), binary patching of engine algorithms:
  - Denuvo's checks are woven through the code, so patched bytes may trip integrity checks.
  - Virtualized regions are unreadable to decompilers, Claude's included.
  - Routes (a) assets, (b) reflection hooks and (c) shaders largely avoid the protected code.
- **The RE Engine type database is the key enabler [inference].** It lets REFramework address engine systems by type and method name instead of raw addresses. That is why a script ecosystem exists for Wilds without anyone decompiling the renderer.
- **Fluffy Mod Manager [inference].** Conceptually it is an asset and loose-file manager in the same family as route (a). I did not fetch a primary source.

### Gaps
- **Wilds' current Denuvo status:** no authoritative 2026 statement found for or against. Check the Steam store DRM notice or SteamDB.
- **What Capcom's anti-tamper does at runtime:** no primary source (Capcom says nothing).
- **Whether Wilds' render code is virtualized:** unknown.

---

## 3. Where frame time goes, what real downports changed, and which route reaches each lever

### Takeaway
- **Real downports changed all three areas: algorithms, content structure and CPU load.**
  - Witcher 3 on Switch replaced its sun-shadow technique and rewrote grass generation and rendering. It started at 10 fps.
  - Hogwarts Legacy on Switch broke the open world into loading-screen zones and dropped advanced lighting.
  - Cyberpunk 2077 on Switch 2 leaned on DLSS from 360–720p, PS4-level crowds and weaker outdoor shadows.
- **Of those levers, without source code:**
  - Resolution, LOD bias, culling, shadow resolution, GI and fog quality and particle density are reachable through Wilds' exposed engine parameters (REFramework).
  - Pass-internal costs (sample counts, ray-march steps) are reachable through shader replacement.
  - New algorithms, baked lighting, world restructuring and CPU-simulation rewrites need source code.
- **Lower-resolution textures save almost no GPU time** unless memory capacity is short.
- **Lower-poly meshes help mainly geometry-heavy passes:** shadow maps, the main geometry pass and foliage.

### Cited Findings
- **[developer interview, via aggregator] Witcher 3 on Switch (Saber):**
  - The first build ran at 10 fps, used more memory than the console had, and was over 50 GB.
  - The sun shadows were "prohibitively expensive." Saber replaced them with a static shadow map, a terrain lightmap and a dynamic shadow map.
  - Grass generation and rendering were rewritten, because foliage is about 50% of outdoor visuals.
  - LOD for trees, lighting and shadows was changed.
  - Cutting NPC counts "was not an option."

  Source: [Wccftech, 5 Dec 2019, citing GamesBeat's interview with Saber CEO Matthew Karch](https://wccftech.com/the-witcher-3-initial-switch-port-10-fps/amp/)
- **[observed] Hogwarts Legacy on original Switch:**
  - Much lower resolution with "fairly aggressive" FSR upscaling, at about 30 fps.
  - The world is "far less seamless," with added loading screens.
  - Lighting and environment are "dialed down."
  - Characters lose the advanced lighting and shaders.

  Source: [Wccftech, 14 Nov 2023](https://wccftech.com/hogwarts-legacy-switch-looks-performs-well-caveats/amp/)
- **[measured by Digital Foundry, via summary] Cyberpunk 2077 on Switch 2:**
  - Portable performance mode renders at 360–720p and DLSS reconstructs it to 720p.
  - NPC and vehicle density is on par with PS4.
  - Outdoor shadows are a step back from PS4.
  - Texture quality matches the PS5 setting.

  Source: [Nintendo Everything, 13 Jun 2025](https://nintendoeverything.com/cyberpunk-2077-switch-2-frame-rate-resolution/)
- **[developer quote] Cyberpunk 2077 on Switch 2:** CDPR's Tim Green said "We haven't had to fight with fitting into memory." Faster storage eased streaming. — [Gameranx, 28 Apr 2025](https://gameranx.com/updates/id/536521/article/cdpr-fixed-what-was-broken-in-cyberpunk-2077-on-ps4-xbox-one-in-the-switch-2/)
- **[reported, 2 Sep 2026]** Capcom's own RE Engine "downport levers" now appear as settings in Dragon's Dogma 2:
  - Volumetric Fog Resolution
  - Ray Tracing GI Quality
  - Foliage Density
  - CPU Saving Mode
  - NPC Culling
  - A commenter adds that an engine update brought new LODs [claimed].

  Source: [GamingOnLinux](https://www.gamingonlinux.com/2026/09/dragons-dogma-2-gets-a-big-upgrade-and-denuvo-drm-removed/)
- **[documented, mod page updated 22 Apr 2026] "More Graphics Options" (Wilds, REFramework script).** It exposes:
  - environmental culling toggles: tall grass, shrubs and some trees, rocks, decals, small lights, particles;
  - mesh LOD bias for monsters and objects;
  - foliage LOD bias;
  - texture LOD bias;
  - dynamic shadows on or off, and shadow resolution below the game's lowest setting;
  - ambient and volumetric lighting quality;
  - particle density.

  Gains are [claimed] "significant" for culling, with no benchmarks. Stated costs: low-poly monsters, pop-in, odd lighting in some areas. — [Nexus mod 816](https://nexusmods.com/monsterhunterwilds/mods/816); [Wccftech, 17 Mar 2025](https://wccftech.com/monster-hunter-wilds-new-graphics-options/amp/)
- **[documented] "Lite Environment" (REFramework)** disables wind simulation, global illumination and volumetric fog. It was used in the Deck bundle below. — [Nexus mod 183](https://www.nexusmods.com/monsterhunterwilds/mods/183)
- **[measured, old but direct]** In Witcher 3 at 1080p, texture quality's effect on fps was "unnoticeable." Ultra used under 300 MB more VRAM than Low. — [GamersNexus, 20 May 2015](https://gamersnexus.net/game-bench/1949-witcher-3-texture-quality-comparison-vram-and-fps)
- **[vendor guidance, mobile tile-based GPUs, not AMD]**
  - Triangles under about 32 pixels each hurt rasterization efficiency.
  - Many tiny triangles cost vertex-stage time and memory bandwidth.

  Source: [Imagination Technologies performance guide](https://docs.imgtec.com/performance-guides/graphics-recommendations/html/topics/triangle-size.html)

### Inferences
- **Which part of the pipeline must change for a "PS5 → PS4-era" downport [inference]:**
  - **Screen-space passes** (GI, volumetrics, post-processing, AO) scale with resolution and with constants inside the shaders. They are reachable via exposed parameters (b) and shader edits (c).
  - **Geometry passes** (shadow maps, the main geometry pass, foliage) scale with triangle and instance counts, which LOD bias and culling (b) control. That only works with the game's existing lower LODs.
  - **CPU-side cost** (animation, physics, NPC simulation, scene traversal, draw submission) is reachable only where the engine exposes a knob, like Dragon's Dogma 2's CPU Saving Mode or NPC culling. Otherwise it needs source code.
  - **Large structural changes need source code (e):** baked lighting replacing GI, a new grass renderer (Witcher 3), world partitioning with loading screens (Hogwarts). A binary patch (d) of an algorithm inside a Denuvo-protected executable is theoretically possible but practically out of reach for this team.
- **(a) Asset modification on a bandwidth-limited APU [inference]:**
  - Textures are filtered through mipmaps (pre-shrunk copies of each texture), so at 1280×800 the GPU rarely reads the top-resolution copy. Shrinking textures saves memory capacity and streaming work, not per-frame bandwidth. Expect about 0% GPU-time gain unless Wilds' working set overflows the Deck's shared 16 GB.
  - Regenerating low-poly meshes adds little over the LOD-bias knob, which already selects the game's own lower LODs. It only pays off where an asset has no cheap LOD.
  - It means rebuilding thousands of RE Engine mesh files and redoing them after every update. Its expected value is small for its cost.
- **(b) Engine-parameter hooking** has the best gain per unit of effort. The parameters Capcom itself exposed in Dragon's Dogma 2 point to which RE Engine knobs matter (fog resolution, GI quality, foliage density, CPU saving, NPC culling). Wilds' Jan 2026 patch added a CPU tab and five fog levels (prior DeckForge research), so some of this is now Tier S, in-game.
- **(c) Shader replacement** reaches costs inside each pass. Prior research estimates 5–10%. It cannot remove a pass or change its resolution, because the CPU side decides those.
- **The pattern across real downports** is that 2–3× comes from changing what is computed, not computing the same thing more cleverly. That is source-level work.

### Gaps
- **No public per-pass GPU timing breakdown of Wilds** (fog, GI and shadow cost in ms) on any hardware was found. Only a Deck RGP capture (Radeon GPU Profiler) can answer this.
- **No AMD/RDNA2-specific source** on the cost of small triangles was fetched. The Imagination guidance is for mobile tile-based GPUs.
- **No measured fps data** for any "More Graphics Options" knob.
- **Primary sources not fetched:** Digital Foundry's videos and the GamesBeat interview were seen only through aggregators.

---

## 4. Fragility: patch cadence, how hooks and patches survive updates, and the maintenance burden

### Takeaway
- Wilds shipped 28 PC updates in about 16 months (Apr 2025–Aug 2026): a major update every 2–4 months, each followed by 1–3 patches within weeks.
- REFramework and the mods built on it break at major updates, and users wait days or weeks for nightly fixes.
- Anything pinned to byte offsets or shader fingerprints should be expected to die on every major update. Name-based reflection hooks survive better.

### Cited Findings
- **[documented] Capcom's official Wilds update page** lists 28 Steam updates:
  - first listed: Ver.1.010.00.00 on 4 Apr 2025;
  - latest listed: Ver.1.042.00.02 on 14 Aug 2026;
  - major or title updates: 4 Apr 2025, 28 May 2025, 30 Jun 2025, 13 Aug 2025, 29 Sep 2025, 30 Oct 2025, 20 Nov 2025, 16 Dec 2025, 28 Jan 2026, 18 Feb 2026, 4 Aug 2026.

  Source: [Capcom Wilds update index](https://info.monsterhunter.com/wilds/update/en-us/)
- **[user reports]** After the February 2026 Wilds update, REFramework was "rendered obsolete." Users reported mods not loading, fps drops, black screens and possible data corruption. Commenters pointed to the nightly build. — [REFramework issue #1469](https://github.com/praydog/REFramework/issues/1469)
- **[documented]** The "Wilds Rehydrated" changelog shows fixes tied to Title Update 4 (tested on game 1.41.3.0). Mod page updated 8 Sep 2026. — [Nexus mod 50](https://nexusmods.com/monsterhunterwilds/mods/50)
- **[documented]** The "Little Engine that Shouldn't" Deck bundle is marked outdated after Ver.1.040.03.02. Its author tells users to delete its config. — [Nexus mod 183](https://www.nexusmods.com/monsterhunterwilds/mods/183)
- **[documented]** The REFramework book warns its API is "subject to change." Plugins declare the REFramework version they require. — [REFramework book](https://cursey.github.io/reframework-book/)
- **[reported] Space Marine 2 patch cadence:** Hotfix 12.3 (update 1.012.003) shipped 8 Apr 2026. — [MP1st](https://mp1st.com/title-updates-and-patches/space-marine-2-hotfix-12-3-update-1-012-003)
- **[reported] Space Marine 2 official modding:** Saber released its internal "Integration Studio" editor for mods on 15 May 2025: AI behaviour trees, UI and HUD, scenarios, no cutscene animation tools. Rendering modding and Easy Anti-Cheat interaction are not addressed. — [Nexus news, 15 May 2025](https://www.nexusmods.com/rust/news/15273)

### Inferences
- **How each route survives an update [inference]:**
  - **Raw byte patches** in a protected executable break on every rebuild. The whole executable is regenerated and checks are re-woven.
  - **Pattern-scan hooks** survive minor patches.
  - **Reflection-name hooks** (REFramework scripts calling the type database by name) survive unless Capcom renames or refactors the type. So far, breakage clusters at REFramework's own internals, which are fixed centrally by one maintainer.
  - **Shader overrides** die whenever a shader is recompiled. Prior research found vkd3d-proton moving its own workarounds from fingerprints to entry-point names because fingerprints churn.
- **Burden on DeckForge [inference].** Expect a re-validation cycle every 2–4 weeks around Wilds updates, plus a dependency on praydog's release timing for any route (b) feature.
- **Space Marine 2 [inference].** It patched about 12 major versions in the roughly 19 months from Sept 2024 to Apr 2026. Combined with Easy Anti-Cheat, it is a poor target for anything beyond Tier S.

### Gaps
- **Wilds after Aug 2026:** no updates were listed after 14 Aug 2026. I did not check whether one arrived in September or October.
- **Space Marine 2 patch dates:** no full patch list found.
- **REFramework fix latency:** no measured typical delay between a Wilds update and a working nightly.

---

## 5. What Claude and Claude Code can and cannot contribute

### Takeaway
- **Public evidence shows Claude is a real accelerator for small, checkable reverse-engineering tasks.** Examples:
  - an 8 KB ROM patch (with human help);
  - N64 decompilation, where a compiler checks every match automatically;
  - single-player content and gameplay mods.
- **I found no public case of Claude making a modern AAA game meaningfully cheaper to render.**
- **Where Claude helps:**
  - REFramework Lua scripts against the type database;
  - shader edits (sample counts and step counts in decompiled shaders);
  - test harnesses and image-comparison pipelines;
  - triaging decompiled functions found through profiling.
- **What Claude cannot do:**
  - judge visual correctness without measured image metrics and a human A/B;
  - run on the Deck;
  - hold a whole engine in context;
  - read virtualized code.

### Cited Findings
- **[case study, 23 Jan 2026] River Raid (Quesma):**
  - Claude with Ghidra found and patched the lives counter in an 8 KB Atari ROM (one instruction changed).
  - It wrongly identified the game as Centipede: "confidence and accuracy are orthogonal."
  - The human had to rebase the binary twice and apply the patch.
  - Tool calls took about 30 seconds.

  Source: [Quesma](https://quesma.com/blog/ghidra-mcp-unlimited-lives/)
- **[case study, 4 Nov 2025] Agentic N64 decompilation (Chris Lewis):**
  - The workflow was "human-driven, with agents acting as research assistants," verified by compiling candidate C and diffing it against the original binary.
  - Agents "stumble on basic arithmetic and bookkeeping" (for example, struct offsets).
  - They struggle with compiler-generated control flow and often ignore context they are force-fed.

  Source: [blog.chrislewis.au](https://blog.chrislewis.au/using-coding-agents-to-decompile-nintendo-64-games/)
- **[result, 17 May 2026]** Snowboard Kids 2 is 100% decompiled, after almost two years. Coding agents (Claude, GLM, Codex) "greatly accelerated" it, but human community members finished the last ten functions. A 100% match "doesn't mean the code is fully understood." — [blog.chrislewis.au](https://blog.chrislewis.au/snowboard-kids-2-is-100-decompiled/)
- **[project page, 2026] universal-modder ("Point Claude at any game").**
  - Its reverse-engineering skill lists Ghidra, IDA (a commercial disassembler) through a connector, Frida (a runtime instrumentation tool) and RenderDoc (a GPU frame debugger).
  - Demos: Terraria content, an Age of Empires II civilization, Minecraft composited into GTA V.
  - No performance mods. It refuses online anti-cheat games and DRM bypass.
  - The fork has 0 stars, so evidence of real use is weak.

  Source: [GitHub Jagou/universal-modder](https://github.com/Jagou/universal-modder)
- **[self-reported, unverified, 6 Oct 2026]** One person's Claude Code pipeline on an unnamed legacy game found 12 places to hook in, generated a texture-format converter, and ran nightly automated tests. No performance work. Two of seven generated scripts had potential vulnerabilities. — [gerdennisai.com](https://gerdennisai.com/blog/claude-code-game-modding-agents)
- **[documented]** REFramework's Lua API, the scripting surface Claude would write against, calls type-database methods and reads and writes fields. — [REFramework book](https://cursey.github.io/reframework-book/)

### Inferences
- **The successful cases share one feature: an automatic checker** (a ROM runs, a compiler output matches byte for byte) [inference]. DeckForge's equivalent is a deterministic capture on the Deck plus frame-time and image metrics, which is the R2 harness. Without it, Claude's "this is faster and looks the same" is worthless; prior research found AI-claimed speedups shrinking below 1× under strict checks.
- **Ranked contributions, best first [inference]:**
  1. Writing and maintaining REFramework scripts that wrap the parameters "More Graphics Options" already exposes, and re-checking them after each Wilds update.
  2. Building the measurement harness.
  3. Shader constant edits through vkd3d-proton's override switch.
  4. Explaining decompiled functions reached from a profiler hotspot, a few at a time.
  5. Generating LOD meshes: low value, high churn.
- **Fede's role as a non-programmer [inference]** is the visual judge in blind A/B tests and the approver of the tier rules. He cannot vet decompiled code, so Tier I work must stay inside automatically measured loops.

### Gaps
- **No public, verified case** of an LLM agent modifying a modern x86-64 AAA renderer (decompile, patch, measure).
- **No public data** on Claude's accuracy at naming or explaining functions in stripped, optimized x86-64 C++ at scale.
- **Not reviewed:** Simon Willison's Dec 2025 "one-shot decompilation" post appeared in search, but I did not read it.

---

## 6. Realistic upper bound for Wilds on the Deck with a dedicated modder plus AI

### Takeaway
- **GPU-bound field scenes:** stacking every reachable lever plausibly yields about 1.2–1.5× [inference]. The levers are resolution down to about 1024×640, GI and volumetric fog off, mesh and foliage LOD bias with culling, shadows below the lowest setting, and 5–10% from shader constants.
- **CPU-bound scenes** (the Grand Hub, busy fights): about 1.0–1.15× [inference].
- **Visual cost:** a "potato" look (flat lighting, pop-in, low-poly monsters, cutscene breakage), arguably below a PS4-era presentation.
- **The best documented community result,** with all tweaks, claimed only "around 30–45 fps," partly with frame generation. It is now deprecated because Capcom's patches made it unnecessary.
- **The target of 1.5–3× at similar visual quality is not reachable without source-level changes [inference].**

### Cited Findings
- **[claimed, Deck] "The Little Engine that Shouldn't" (updated 18 Dec 2025):**
  - Its full stack was a config edit (lower textures, no shadow caching), 1024×640 or upscaled 800p/900p, a 1600 MHz GPU clock, Lite Environment (GI, fog and wind off), and foliage LOD bias 2 / leaf LOD 3, with Lossless Scaling optional.
  - It claimed "around 30–45fps," with no baseline.
  - Costs: pop-in, artifacts from Lossless Scaling's "Smooth" mode, and missing textures from premade decompression files.
  - Status: "outdated" after Ver.1.040.03.02.

  Source: [Nexus mod 183](https://www.nexusmods.com/monsterhunterwilds/mods/183)
- **[claimed, via prior DeckForge research, not re-fetched here]** Lite Environment's GI and fog cuts broke cutscenes until the mod learned to switch them back on during cinematics. — [Nexus mod 234](https://www.nexusmods.com/monsterhunterwilds/mods/234)
- **[claimed, no benchmarks]** "More Graphics Options" culling and foliage LOD give a "significant" or "considerable" framerate gain, and lower ambient lighting "significantly improves" it. — [Nexus mod 816](https://nexusmods.com/monsterhunterwilds/mods/816)
- **[measured, Legion Go S with Z1 Extreme, a faster handheld than the Deck; via prior DeckForge research]** About 40 fps exploring and fighting, but about 30 in CPU-heavy areas such as the Grand Hub. Published 29 Jan 2026. — [TechRadar](https://www.techradar.com/gaming/pc-gaming/its-not-a-myth-capcom-has-fixed-monster-hunter-wilds-and-i-even-tested-it-to-find-out)
- **[reported]** The texture-decompressor asset mod removes texture-streaming microstutter on 8 GB GPUs but gives no fps numbers. On the Deck it costs about 37–41 GB of storage. — [PC Games Hardware, 23 Nov 2025](https://www.pcgameshardware.de/Monster-Hunter-Wilds-Spiel-74697/News/Performance-Patch-Update-Community-Mod-1487048/); [Nexus mod 183](https://www.nexusmods.com/monsterhunterwilds/mods/183)

### Inferences
- **Arithmetic for GPU-bound scenes [inference]:**
  - 1280×800 is 1.02M pixels; 1024×640 is 0.66M, which is 1.56× fewer. Resolution-dependent passes therefore gain at most about 1.3–1.5×, less once fixed costs are counted.
  - Prior estimates, all speculative: fog and GI cuts 5–20%, shadows 2–8%, VRS 0–8%, shader constants 5–10%.
  - These overlap with resolution, since GI and fog are also screen-space, so they do not simply multiply.
  - A realistic total is about 1.2–1.5× over today's lowest-plus-upscaling baseline of about 30 fps, so about 36–45 fps in the field.
  - That matches the community's "30–45" claim and the faster Z1 Extreme's ~40.
- **CPU-bound scenes [inference].** Rendering levers barely help. Only engine knobs such as NPC and object culling or Capcom's CPU tab help, so gains are about 1.0–1.15×. The CPU, not shaders, is likely the binding limit for a locked 40 or 45 in Wilds.
- **"PS4-era quality" [inference].** What these levers produce is not a PS4-style downport. A PS4-era game was authored with baked or cheaper lighting tuned to look good without GI. Switching GI off in a game built around GI looks flat and broken in places, the cutscene problem being one example. Similar-quality 2–3× needs re-authored lighting and LODs, which only the developer can do.
- **Where AI helps most [inference]** is speed and coverage: re-deriving these mod settings after each patch, testing parameter combinations automatically on the Deck, and finding the knee of the quality/fps curve per scene. It does not raise the upper bound.

### Gaps
- **No measured Deck before/after fps** exists for any single REFramework lever.
- **No Deck GPU profile of Wilds** splitting the frame into passes and into CPU vs GPU time. This is the decisive missing measurement (prior DeckForge test X1).
- **Space Marine 2:** no evidence of any rendering lever beyond the in-game menu (including its dynamic-resolution target). Easy Anti-Cheat excludes routes (b)–(d).

### Lever table (Wilds unless noted; gains are vs. the current lowest-plus-upscaling baseline on the Deck)

| Lever | Route | Expected gain on Deck | Visual cost | Effort | Fragility | Allowed for anti-cheat games (e.g. Space Marine 2)? |
|---|---|---|---|---|---|---|
| Lower internal resolution (e.g. 1024×640) + FSR/XeSS upscaling | Tier S (in-game / gamescope) | Up to ~1.3–1.5× on resolution-bound passes [inference]; ~0 when CPU-bound | Softer image on a 7" screen | Very low | Low | Yes |
| Fog at its lowest of the 5 in-game levels; CPU tab | Tier S (in-game since Jan 2026) | Small, unmeasured [gap] | Minor | Very low | Low | Yes (in-game equivalents only) |
| GI and volumetric fog off (Lite Environment) | Engine-parameter hook (REFramework) | 5–20% [prior estimate, speculative] | Flat lighting; cutscene breakage unless handled | Low (existing mod) | Breaks at major updates until REFramework is fixed | No |
| Mesh and foliage LOD bias + object culling (grass, decals, small lights, particles) | Hook (REFramework "More Graphics Options") | ~5–15% in foliage-heavy fields [inference; "significant" claimed, unmeasured] | Pop-in, low-poly monsters, missing grass and clutter | Low | Same as above | No |
| Shadows below lowest / dynamic shadows off | Hook | 2–8% [prior estimate] | Missing or blocky shadows | Low | Same as above | No |
| Particle density down | Hook | Small on average; helps worst-case dips [claimed] | Weaker effects | Low | Same as above | No |
| Texture LOD bias / smaller textures | Hook or asset | ~0% GPU time unless memory-capacity-bound [GamersNexus, inference] | Blur | Low | Asset repacks redone every update | No |
| Uncompressed-texture asset swap (stutter, not average fps) | Asset + REFramework loose-file loader | Smoother frame times on 8 GB GPUs; Deck effect unmeasured | None visible; +~17 GB disk | Low–medium | Redone after asset-changing updates | No |
| Newly generated low-poly LOD meshes | Asset | Small beyond LOD bias, since existing LODs are already selectable [inference] | Varies by asset | High (thousands of meshes, proprietary format) | Very high | No |
| Constants in hot shaders (sample counts, ray-march steps) | Shader replacement (vkd3d-proton override) | 5–10% [prior estimate] | Subtle to moderate (noise, banding) | Medium–high (needs RGP profiling and image metrics) | Dies when a shader recompiles; unsafe across Proton updates unless pinned | No (Tier I) |
| Cheaper pass algorithms (e.g. a different GI or shadow technique, Witcher-style grass rewrite) | Binary patch + new shaders, realistically source only | Potentially large (1.3–2× on the affected passes) [inference from downports] | Re-tuned to look similar, as real ports did | Very high; protected executable | Extreme | No |
| CPU reductions: NPC, animation and physics LOD, crowd density | Hook where knobs exist; otherwise binary patch or source | ~1.0–1.15× in CPU-bound hubs and fights [inference] | Fewer or stiffer NPCs and ambient life | Medium (hook) to very high (patch) | High | No |
| Re-authored baked lighting, world zoning, content re-optimization (the PS5 → PS4-class port) | Source only (developer) | The 2–3× real ports reach [inference] | Comparable quality by design | Studio-scale | n/a | n/a |
| Frame generation (Lossless Scaling / lsfg-vk) | Tracked separately, never counted toward the native target | — | — | — | — | — |

**Bottom line for the owner [inference]:**
- **Wilds:** the reachable ceiling is roughly 36–45 fps in GPU-bound field scenes at a visible "potato" cost, and about 30–35 in CPU-bound areas.
- **Space Marine 2:** only the Tier S rows apply.
- **What to build:** the measured REFramework-parameter route and the hot-shader-constant route, each inside the R2 measurement harness. Do not attempt binary reverse engineering of the engine.
- **Memory:** nothing in this report needs saving to memory beyond what is already in the DeckForge project docs.
