# Precedents: reverse engineering, decompilation, recompilation and deep modding for better performance or weaker hardware (as of 12 Oct 2026)

Labels used below: **[measured]** means a third party benchmarked it. **[claimed]** means the author or vendor asserted it. **[inference]** is my own reasoning. Dates are publication or event dates.

---

## Q1. Fan decompilations and source ports

### Takeaway
Every successful fan decompilation or source port targets a small, old, fixed-platform game: N64, PS2/PC 2001–02, GameCube, or 1990s PC. Each took a community months to years. Matching decomps run from 21 months with dozens of people (OoT) to about 6 years (Melee). The gains go *upward*, meaning higher fps, resolution and widescreen on hardware far stronger than the original. Only one case went *downward* to run better on weak hardware: Kaze Emanuar's SM64 work on a real N64. It needed the finished decomp plus hundreds of hours from a world-class specialist. Nintendo has mostly gone after videos and listings, not the decomps themselves. Take-Two sued the re3 team, and the case was settled and dismissed in April 2023.

### Cited Findings
**Super Mario 64 (N64, 1996)**
- Fans decompiled the ROM to C in 2019. A Windows port followed in 2020 with "support for widescreen displays and 4K resolution". Later derivatives include Render96 and ports to 3DS, PS2, Vita, Dreamcast and Android. — [Wikipedia: Super Mario 64](https://en.wikipedia.org/wiki/Super_Mario_64)
- Legal: Nintendo "enlisted a law firm to remove videos of the port and its listings from various websites". Other fan projects were also struck (SM64 Online, a Unity SM64 HD remake). — [Wikipedia](https://en.wikipedia.org/wiki/Super_Mario_64)
- Ars Technica (May 2020) called the port the result of "a years-long effort to decompile the Super Mario 64 ROM into parsable C code". A commenter noted the game was built with optimization disabled, which made the machine code predictable. — [Slashdot summary of Ars](https://games.slashdot.org/story/20/05/07/0358239/beyond-emulation-the-massive-effort-to-reverse-engineer-n64-source-code?sdsrc=prev)
- The decomp repo is still public as of Oct 2026. It is a "full decompilation" of the JP/US/EU/Shindou/iQue versions, CC0 licensed, with no assets: users supply their own baserom. It has 8.8k stars. — [github.com/n64decomp/sm64](https://github.com/n64decomp/sm64)
- **Kaze Emanuar optimizing SM64 for real N64 hardware** is the only "make it run better on the weak original hardware" precedent.
  - [claimed] "Up to six times faster". Per-level frame rate roughly doubled. Rendering improved 70–90%. A "stable 30 FPS on N64 hardware" needs the RAM Expansion Pak.
  - Effort was "hundreds of hours", "over 100 hours" and "100,000 lines" read (the article gives inconsistent figures). Date: April 2022. — [eXputer](https://exputer.com/news/nintendo/modder-fix-super-mario-64-code/)
  - [claimed] In his later ROM hack, a spot that ran at "nine frames a second" now runs at 60 fps on hardware. Main techniques: cache-line alignment, plus the fact that the CPU and RCP share memory. He "basically reprogrammed the whole thing". — [SE Daily transcript, Mar 2024](https://softwareengineeringdaily.com/wp-content/uploads/2024/03/SED1666-Kaze_Emanuar.txt)

**Ocarina of Time (N64, 1998) → Ship of Harkinian; Majora's Mask (N64, 2000) → 2Ship2Harkinian**
- The OoT decomp was finished in November 2021 by the Zelda Reverse Engineering Team (ZRET) after "21 months of development". "Dozens of people helped". — [Wikipedia: Ship of Harkinian](https://en.wikipedia.org/wiki/Ship_of_Harkinian); [VGC, 27 Nov 2021](https://www.videogameschronicle.com/news/zelda-64-has-been-fully-decompiled-potentially-opening-the-door-for-mods-and-ports/)
- Ship of Harkinian (Harbour Masters) was first released on 22 March 2022.
  - Widescreen; 60 fps (May 2022); adjustable framerate up to 250 fps (July 2022).
  - Switch and Wii U homebrew ports.
  - No Nintendo legal action is reported.
  - — [Wikipedia](https://en.wikipedia.org/wiki/Ship_of_Harkinian)
- It is built on libultraship, which mimics the N64 libultra SDK on modern hardware. No assets are shipped; data is extracted from the user's ROM. — [GitHub Shipwright](https://github.com/HarbourMasters/Shipwright)
- Port legality, as reported: the SM64 port was DMCA'd because it bundled assets. SoH avoided this by keeping assets in an external archive dumped from the user's copy. "No clear court precedent". — [PC Gamer, Jan 2022](https://www.pcgamer.com/au/a-90-complete-fan-made-pc-port-of-zelda-ocarina-of-time-could-be-ready-by-april)
- 2Ship2Harkinian was released on 26 May 2024. Higher fps comes from Matrix Interpolation, and "the game logic still runs at 20 FPS, so this is all purely visual". — [GamingOnLinux, 27 May 2024](https://gamingonlinux.com/2024/05/2-ship-2-harkinian-another-unofficial-pc-port-of-zelda-majoras-mask-is-out-now); [Wikipedia](https://en.wikipedia.org/wiki/Ship_of_Harkinian)
- Harbour Masters has since shipped StarShip (Star Fox 64, Dec 2024), SpaghettiKart (Mario Kart 64, June 2025) and Ghostship (SM64, Jan 2026). Lighthouse (Banjo-Kazooie) is listed for July 2026. — [Wikipedia](https://en.wikipedia.org/wiki/Ship_of_Harkinian)

**Perfect Dark (N64, 2000)**
- The decomp was credited to Ryan Dwyer, essentially one person. On 17 Oct 2022 both NTSC versions were "fully decompiled", with about 97.4% byte-matching and the rest functionally equivalent. — [VGC](https://videogameschronicle.com/news/perfect-dark-has-been-fully-decompiled-making-pc-ports-and-mods-possible)
- The PC port by fgsfds (2023) adds 60 fps, widescreen and mouselook, and requires a "legally-sourced" ROM. — [Time Extension, Nov 2023](https://timeextension.com/news/2023/11/perfect-dark-has-got-a-fanmade-pc-port-which-adds-a-bunch-of-great-qol-features)

**re3/reVC (GTA III / Vice City, 2001/2002)**
- Take-Two DMCA'd the GitHub repos in 2021. A counternotice restored them.
- Sept 2021: Take-Two sued 4 named developers (Papenhoff, Morra, Orçunus, Graber) plus Does.
- Feb 2023: settlement in principle.
- 3 April 2023: claims against the 4 named developers were dismissed **with prejudice**, each side bearing its own costs, terms undisclosed. The Does were dismissed without prejudice. — [TorrentFreak](https://torrentfreak.com/take-two-dismisses-claims-against-lead-defendants-in-gta-mods-lawsuit-230405/)
- Related, 2025: "GTA Vice City Nextgen Edition" by Revolution Team ports Vice City content into the GTA IV engine, after about 2 years of work. Take-Two issued a takedown and the team's YouTube channel was removed. The team released it anyway in January 2025 as a standalone package. — [HotHardware, 28 Jan 2025](https://hothardware.com/news/gta-vice-city-nextgen-mod-released)

**Engine reimplementations and official source releases**
- **OpenMW** (Morrowind, 2002): started 2008; v0.50.0 released 7 Nov 2025. GPLv3; uses but doesn't include the original assets. The switch to OpenSceneGraph (v0.37) brought "significant performance improvements". — [Wikipedia: OpenMW](https://en.wikipedia.org/wiki/OpenMW)
- **OpenRCT2** (RCT2, 2002): started 2 April 2014; about 250 contributors. Adds HD resolutions, higher framerates, multiplayer and improved pathfinding. GPLv3; needs the original game. — [Wikipedia: OpenRCT2](https://en.wikipedia.org/wiki/OpenRCT2)
- **DevilutionX** (Diablo, 1996): a port derived from the earlier Devilution project. Widescreen; builds for Linux/macOS/Windows/Android/iOS/PS4/Xbox/Switch/Vita/3DS/Amiga. Needs DIABDAT.MPQ. Non-commercial license; "not associated with or endorsed by Blizzard". — [GitHub](https://github.com/diasurgical/DevilutionX)
- **OpenJK** (Jedi Academy/Outcast): a community continuation of Raven's code. Goals are stability, performance and ARM/Apple Silicon support. GPLv2. 3 leads and 14 significant contributors. — [GitHub](https://github.com/JACoders/OpenJK)
- **Doom** (1993): source released 23 Dec 1997, relicensed under GPL on 3 Oct 1999. "Hundreds" of source ports exist. Crispy Doom adds high resolution and uncapped fps. "Doom Ray Traced" (2022) adds RT and DLSS. — [Wikipedia: Doom source port](https://en.wikipedia.org/wiki/Doom_source_port)

**2025–2026 examples**
- **Dusk** (Twilight Princess, GC 2006): released around April–May 2026 by the TP decomp team and Twilit Realm. Up to 120 fps via skeleton interpolation, ultrawide, and builds for Windows/macOS/Linux/Android/iOS/Steam Deck. Own game files required. — [Time Extension, May 2026](https://timeextension.com/news/2026/05/the-legend-of-zelda-twilight-princess-has-unofficially-been-ported-to-the-pc)
- **Super Smash Bros. Melee** (GC 2001): "100% decompiled" per decomp.dev as of 8 Sep 2026, after about six years. No port yet. — [Android Authority, 8 Sep 2026](https://androidauthority.com/super-smash-bros-melee-decompiled-3708716)
- **P.T.** (PS4, 2014). This is the only PS4-era example found.
  - A solo developer (Lorean Xavier) reconstructed the game logic in C++ with a Vulkan renderer, loading assets from the user's own PS4 copy.
  - Adds FSR 3.1, DLSS 4.5, XeSS and frame generation, plus presets including "Original (PS4)" and RT effects. Builds for Windows, Linux and Steam Deck. MIT licensed.
  - v1.0.0 was announced on 7 Oct 2026. — [Insider Gaming, 8 Oct 2026](https://insider-gaming.com/p-t-gets-native-pc-port-with-a-bunch-of-improvements/)
  - P.T. was delisted in April 2015, so legitimate copies are rare. — [Held Games tracker, Oct 2026](https://heldgames.com/guides/recompiled-games-list)
- Tracker snapshot dated 7 Oct 2026: about 20 N64 recomp/decomp projects, 13 Xbox 360 projects, the Halo CE decomp, and GameCube/Wii projects. Its claims are not independently verified; treat it as secondary. — [Held Games](https://heldgames.com/guides/recompiled-games-list)

### Inferences
- [inference] Scale: the largest successful matching decomps cover single games with MB-scale code from the 1990s–2000s, built with old compilers. They needed dozens of contributors and 2–6 years. A modern AAA PC binary is far larger and built with modern optimizing toolchains (often with LTO and anti-tamper). It also gets patched every few weeks, which invalidates matching work. No precedent exists for a fan decomp of a PS5-era AAA game.
- [inference] Nearly every "60/120/250 fps" result in decomp ports is *render interpolation over fixed-rate logic* (2Ship, Dusk). Uncapping the logic is a separate and harder problem; see Bloodborne in Q3.
- [inference] The legal pattern is that projects survive when they ship no assets and require a user-owned copy (Nintendo N64 decomps). Publishers act when the work is commercially adjacent or the IP is still exploited (Take-Two on re3 and VC Nextgen, Sony on Bloodborne).

### Gaps
- I found no exact SM64 decomp start/finish dates or team size from a primary source; Ars Technica was blocked.
- I found no team sizes for SoH, 2Ship or Dusk, and no headcount for the re3 developers beyond the 4 named defendants.
- Whether re3 is still offline after the 2023 settlement is not confirmed in sources fetched; my understanding is that it is.
- I found no re3 performance or feature data.
- Original binary/ROM sizes were not sourced in this pass. [background, unverified here: SM64 is an 8 MB cartridge; OoT/MM are 32 MB.]

---

## Q2. Static recompilation

### Takeaway
Static recompilers lift a console binary's machine code (MIPS for N64, PowerPC for Xbox 360/Wii/PS3, MIPS R5900 for PS2) into C/C++, compile it natively, and pair it with a hand-built runtime and a new renderer. Per-game setup can take days (N64) or months (360) instead of the years a decomp takes. Every improvement comes from the new renderer and targeted patches, not from rewriting the game's algorithms. The technique solves *ISA translation for old consoles*. A modern PC game is already native x86-64, so recompilation offers it nothing by itself [inference]. AI involvement became visible in 2025–26 and is contested.

### Cited Findings
**N64Recomp / Zelda64Recomp (Majora's Mask, May 2024)**
- N64Recomp (by Wiseguy) converts N64 code into natively runnable code, avoiding per-instruction emulation overhead. The compiler can optimize the whole program.
- Getting another game running took Wiseguy "about two days"; he did Superman "in a couple days".
- [claimed] Majora's Mask runs at 60 fps on Steam Deck and runs fine on a dual-core Pentium with a GT 630. Widescreen comes via HUD patches.
- — [Read Only Memo interview, May 2024](https://www.readonlymemo.com/n64-recompiled-interview-majoras-mask-emulation-native-pc-port)
- Mapping is one original function to one output function. Overlays need manual identification. Decompilation is used only for the functions you want to change ("These are the functions I care about changing. And therefore, I'm going to decompile these").
- Widescreen "does require some hacks usually", such as removing draw-distance checks. Framebuffer effects worked unmodified through RT64.
- The team is two named developers: Wiseguy (recompiler and runtime) and Dario (RT64 renderer). No AI is mentioned.
- — [SE Daily transcript, Sept 2024](https://softwareengineeringdaily.com/wp-content/uploads/2024/09/SED1735-N64-Recomp.txt)

**XenonRecomp / Unleashed Recompiled (Sonic Unleashed, Xbox 360 2008; port released about March 2025)**
- How it works: Xbox 360 PowerPC is converted to C++ "directly", with CPU state passed to every function.
  - Byte-swapped loads/stores; VMX vector code mapped to x86 intrinsics (ARM64 via SIMDe).
  - Function boundaries come from `.pdata` plus branch scanning.
  - "No fully generic solution for handling jump tables". MMIO and exceptions are unimplemented.
  - "This project does not provide a runtime… Making the game work is your responsibility."
  - Per game: a TOML config, manual function boundaries, mid-asm hooks.
  - Optimizations cut the Unleashed executable "by around 20 MB" and frame times "by several milliseconds".
  - — [GitHub hedge-dev/XenonRecomp](https://github.com/hedge-dev/XenonRecomp)
- Unleashed Recompiled pairs XenonRecomp with XenosRecomp, which translates Xenos shaders to HLSL.
  - New D3D12/Vulkan multithreaded renderer and async shader compilation.
  - 60 fps default with unlockable higher targets; higher resolutions, extra MSAA, 21:9+ ultrawide.
  - Native Linux build works on Steam Deck. User must supply their own US/EU copy. 17 credited contributors; Skyth is the lead.
  - — [README](https://cdn.jsdelivr.net/gh/hedge-dev/unleashedrecomp@main/README.md)
- Co-creators Skyth and Sajid; Wiseguy assisted. — [Time Extension, Mar 2025](https://www.timeextension.com/news/2025/03/this-new-unofficial-pc-port-of-sonic-unleashed-could-be-the-best-version-of-the-game-yet)
- 2026 360 wave, per a secondary tracker:
  - The Darkness: D3D12, uncapped fps, up to 3× the console's 720p.
  - The Simpsons Game, tested on Steam Deck: [claimed] GPU frame time 14.6 → 8.1 ms.
  - Spider-Man: Edge of Time v1.0 (4 Oct 2026); Fable 2, Condemned 2, Ninja Gaiden II and others.
  - Mario Kart Wiicompiled is the first Wii static recomp (beta v0.2.32 in Sept 2026).
  - PSXRecomp produced Pepsiman, the first WebAssembly recomp (July 2026).
  - — [Held Games tracker, 7 Oct 2026](https://heldgames.com/guides/recompiled-games-list)

**PS2 / PS3 / Switch**
- PS2Recomp (ran-j, Brazil) statically recompiles PS2 ELFs to C++. As of 27 Jan 2026 it "doesn't yet work as intended". — [Time Extension](https://www.timeextension.com/news/2026/01/native-pc-ports-of-ps2-games-could-be-on-the-way-thanks-to-new-recompilation-experiment)
- ps3recomp (sp00nznet) is a toolkit that lifts PPU and SPU code with a runtime modelling PS3 memory, threads and syscalls. As of 15 June 2026: games reach initialization stages, "tens of thousands of lifted functions" exist, and there is basic geometry on screen. It is "not a general PS3-to-PC converter". — [GenerationAmiga](https://www.generationamiga.com/2026/06/15/ps3recomp-the-new-tool-bringing-native-playstation-3-ports-closer-to-pc/)
- Switch: I found no shipped Switch static recompilation.

**AI involvement**
- Chris Lewis, *Snowboard Kids 2* N64 decomp:
  - Nov 2025: workflow "still human-driven, with agents acting as research assistants". Failure modes: struct offset arithmetic, C89 rules, nested compiler-generated control flow. — [blog, 4 Nov 2025](https://blog.chrislewis.au/using-coding-agents-to-decompile-nintendo-64-games/)
  - Dec 2025: he switched to Claude Opus 4.5 in non-interactive "one-shot" mode, with a scorer feeding the simplest unmatched function next. [measured on decomp.dev chart] Matching went from about 25% to about 45% between 17 Nov and 2 Dec 2025, more progress in 3 weeks "than in the preceding three months".
  - Runs lasted "8+ hours" unattended. In a small test, Opus matched 5 of 7 functions Sonnet 4.5 had failed.
  - Output still needs cleanup: pointer arithmetic and gotos. "I don't see human experts becoming unnecessary any time soon."
  - — [blog](https://blog.chrislewis.au/the-unexpected-effectiveness-of-one-shot-decompilation-with-claude/); [Simon Willison, 6 Dec 2025](https://simonwillison.net/2025/Dec/6/one-shot-decompilation/)
- Mario Kart Wiicompiled (Patchzyy, solo): the FAQ discloses AI was used "to assist with code only". There was community backlash. — [Tom's Hardware, 17 Jul 2026](https://www.tomshardware.com/video-games/retro-gaming/mario-kart-wii-recompiled-for-pc-using-ai-with-4k-potential-and-uncapped-frame-rates-first-static-recompilation-of-a-wii-game-supports-over-200-tracks-thanks-to-retro-rewind-compatibility)
- Melee: one site claims OpenAI's "GPT-6 Astra" closed the final stretch "within days" after six years of human work, and that "'AI decompiled Melee' is not what happened". It cites no sources and does not quote the team. **Treat this as unverified.** — [Held Games, Sept 2026](https://heldgames.com/guides/melee-decompiled-ai-astra)
- The same site reports pushback from other projects: mGBA closes AI PRs, SDL banned them in April 2026, QEMU declines them on licensing grounds; the Petari (Galaxy) README denies AI use. Secondary and unverified. — [Held Games](https://heldgames.com/guides/melee-decompiled-ai-astra)

### Inferences
- [inference] Recomp's performance wins come from three things: removing emulation overhead, a modern multithreaded renderer, and running on hardware many times faster than the original console. None of these applies to a modern x86-64 PC game on a Steam Deck, which is GPU- and CPU-workload-bound, not ISA-bound.
- [inference] Even with recomp, every "better" feature (widescreen, interpolation, draw distance) needed targeted hand patches to specific functions. That per-feature, per-game effort is what DeckForge would have to pay for each title.
- [inference] AI is now proven to speed up the mechanical inner loop of *matching decomp of small MIPS C functions* (roughly 2× progress rate in one documented case). Nothing shows AI rebuilding a modern engine's renderer or content pipeline.

### Gaps
- Binary sizes of the recompiled originals (Unleashed XEX, MM code segment) were not found.
- Development duration for Unleashed Recompiled and for Zelda64Recomp's runtime was not found; Wiseguy only says the runtime "sat dormant for a while".
- I found no verified source on AI use in Melee.
- I found no fetched source on the original Xbox 360 Unleashed fps/resolution.

---

## Q3. Community performance patches for modern games (binary patching and hooking)

### Takeaway
Large community fps gains on modern games come from a few sources:
- **Fixing a specific bug.** The Monster Hunter Wilds DLC check: [claimed] minimum fps up 79%, average up 63%.
- **Removing a cap.** Elden Ring fps unlock; Bloodborne 30 → 60.
- **Flipping hidden engine switches.** Jedi Survivor animation interpolation.
- **Re-tuning expensive effects.** Ultra+, Special K global illumination.

The work is done by one or two highly skilled reverse engineers per game. It usually requires disabling anti-cheat, frequently breaks on updates, and is often absorbed into official patches. Uncapping frame rate on an engine with frame-coupled logic is costly; Bloodborne needed about 7 subsystems fixed and a cut to 720p. Prior work already covered vkd3d-proton, RenoDX, 3DMigoto and REFramework for MH Wilds; this section only adds to it.

### Cited Findings
- **Elden Ring FPS Unlocker and more** (uberhalit):
  - Hot-patches game memory at runtime ("does not modify any game files") to unlock fps, add widescreen and change FOV.
  - Requires "offline mode and the AntiCheat (EAC) isn't running". Claims it "should work with all future updates".
  - Last release v1.1.0.0 on 22 Mar 2022, with 65 open issues; it appears inactive.
  - — [GitHub](https://github.com/uberhalit/EldenRingFpsUnlockAndMore)
- **Bloodborne 60 fps** (Lance McDonald, Oct 2020, PS4 with modded firmware):
  - He backported the PS4 Pro 60 fps work from Dark Souls 3 (same engine).
  - Manually patched cloth physics, particles, wind, enemy patrol pathing, motion-blur sampling and elevator speed, so that logic scaled with delta-time.
  - Dropped resolution from 1080p to 720p to hold the frame rate.
  - — [Kotaku, 12 Oct 2020](https://kotaku.com/bloodborne-modder-will-release-60-fps-hack-if-sony-fail-1845352238)
- Sony then issued a DMCA notice, which McDonald says targeted the page because it used the trademark "Bloodborne". He says the patch is "100% code" and would not repost. Early 2025. — [Push Square, Jan 2025](https://www.pushsquare.com/news/2025/01/sony-issues-dmca-takedown-against-bloodborne-60fps-mod-four-years-after-release)
- shadPS4 (PS4 *emulator*, not recomp) runs Bloodborne at 80–100 fps on an RTX 4060 Ti, per footage. Setup "can be challenging". — [Notebookcheck, 29 Nov 2025](https://www.notebookcheck.net/ShadPS4-Bloodborne-emulator-shows-dramatic-PC-performance-gains-over-PS5-with-no-remaster-in-sight.1173307.0.html)
- **Monster Hunter Wilds**:
  - A Redditor found that a routine repeatedly re-checks DLC ownership, burning CPU and RAM. [claimed, modder's video] Bypassing it took minimum fps from 24 to 43 and average from 30 to 49. — [DSOGaming, 15 Jan 2026](https://www.dsogaming.com/?p=192404)
  - Capcom shipped a fix around late January 2026. [measured, Daniel Owen] Minimum fps rose 8% vs Title Update 4 and 20% vs TU3. Steam Deck reaches roughly 30 fps with FSR/XeSS. — [Notebookcheck, 30 Jan 2026](https://www.notebookcheck.net/Monster-Hunter-Wilds-fixes-DLC-bug-greatly-reduces-FPS-drops-and-runs-at-30-FPS-on-Steam-Deck.1215270.0.html)
- **Dragon's Dogma 2**: the developers said CPU load from "the thoughts of each NPC" and physics was the bottleneck, so lowering resolution barely helped. They reworked NPC thought processing and process order in the 17 Oct 2024 patch. — [Automaton, 18 Oct 2024](https://automaton-media.com/en/news/dragons-dogma-2-frame-rate-issues-were-largely-caused-by-the-npcs-thinking-developers-say/)
- **Star Wars Jedi Survivor**:
  - "May the Performance be with You" (Glumboi, May 2023) is a config preset mod. [claimed] Gains of 5–25 fps; the "Potato PC" preset took a GTX 1070 from about 30 to "60+". CPU-bound systems benefit less. — [Wccftech, 2 May 2023](https://wccftech.com/star-wars-jedi-survivor-performance-mod-reduces-stutters-increase-fps/amp/)
  - Feb 2026: a plug-in enables a hidden animation-interpolation setting found by Digital Foundry to lighten the main CPU thread. No fps numbers given. Compatible with Patch 9. — [DSOGaming, 25 Feb 2026](https://www.dsogaming.com/?p=193077)
- **Starfield**: "Vanilla Scripts Optimized" (Yeti, Oct 2023) replaces slow script functions and fixes queue thrashing. Only a "possible fps gain" is claimed. — [DSOGaming, 14 Oct 2023](https://www.dsogaming.com/?p=175055)
- **Special K** (Kaldaien) is a modding framework for "fixing and enhancing graphics" and "performance analysis and correction". — [Special K wiki](https://wiki.special-k.info/)
  - Its NieR: Automata mod FAR is loaded as `dxgi.dll`. It targets shaders by ID, lowers global illumination below the game's minimum ("major performance improvement"), fixes frame pacing, and cut load times from about 15 s to about 5 s.
  - It ran "for years" until Square Enix's 15 July 2021 update incorporated many of its fixes.
  - — [Special K wiki: FAR](https://wiki.special-k.info/SpecialK/Custom/FAR)
- **Ultra+ (Cyberpunk 2077)** by SammiLucia: uploaded 28 Oct 2023, v10.0.0.9 updated 11 Oct 2026, and covers "more than 80 games".
  - Uses Cyber Engine Tweaks plus a RED4ext plugin (UltraTool) and cvar changes.
  - [claimed] "PT20 Fast is 40% faster than vanilla PT". It targets *high-end* path tracing, not low-end hardware.
  - — [Nexus Mods](https://www.nexusmods.com/cyberpunk2077/mods/10490)
- **Alan Wake 2 without mesh shaders** was an *official* Remedy patch (1.0.16.1, March 2024), not a community hack. [measured, Digital Foundry, forest scene at 1080p FSR2 Quality] GTX 1060 +45%, 1070 +57%, 1080 +85%, 1080 Ti about +100%. — [ITC.ua citing DF](https://itc.ua/en/news/alan-wake-2-patch-should-improve-performance-with-nvidia-gtx-10-graphics-cards-gtx-1080-ti-may-double-the-number-of-frames/); [HotHardware, 6 Mar 2024](https://www.hothardware.com/news/performance-miracle-alan-wake-2-patch-delivers-a-huge-boost-on-older-geforce)
- **Stalker 2**: a Nexus "mod pack" (mod 60, Dec 2024) changes upscaling, anti-aliasing and streaming. [measured, MxBenchmarkPC, RTX 4080] 4K Epic DLSS-Q went from 55 to 70 fps (+27%), and 1440p from the mid-60s to the high-80s. It causes aggressive pop-in, with the smallest gains in CPU-bound camps. Whether it survives patch 1.01 was an open question. — [Club386, 3 Dec 2024](https://www.club386.com/stalker-2-modders-come-to-the-rescue-with-performance-tweaks)

### Inferences
- [inference] The biggest wins (MH Wilds, Dragon's Dogma 2, Alan Wake 2) were fixing a defect or adding a code path, and the studio either did it or adopted it within weeks. For DeckForge, the scalable version is detecting and reporting such defects, not maintaining binary patches.
- [inference] Every binary or hook approach that touches executable memory falls under DeckForge's Tier I. Elden Ring's unlocker literally requires EAC off. This matches the existing tier policy.
- [inference] Uncapping frame-coupled engines (FromSoftware, Bethesda) means auditing every time-dependent subsystem. Bloodborne needed about 7 manual fixes even with DS3's 60 fps code to borrow.

### Gaps
- I found no reliable sourced numbers for Hogwarts Legacy community CPU or stutter fixes, Dragon's Dogma 2 community CPU mods, or Black Myth Wukong binary-level mods.
- Special K's technical mechanism, anti-cheat guidance and per-game fps numbers were not on the pages fetched.
- How the Elden Ring unlocker locates code across patches (signature scanning) is suggested but not documented.
- I found no source quantifying how often these mods break per game update.

---

## Q4. "Potato" and ultra-low graphics mods

### Takeaway
Potato mods are mostly config files (Unreal `GameUserSettings`/`Engine.ini` scalability cvars, RE Engine configs through REFramework) or low-resolution texture swaps. They help only when the game is GPU- or VRAM-bound. Typical results on handhelds:
- Monster Hunter Wilds: [claimed] 30–45 fps on the Deck at 1024×640–1280×800.
- Clair Obscur: [claimed] 20–30 fps on the Deck.
- Jedi Survivor: [claimed] 30 to 60+ on a GTX 1070.

Image quality is often well below PS4 level: "more at home on a PlayStation 2" for Starfield's texture potato mod. This is the community's real form of "downporting", and it stays Tier S (config-level).

### Cited Findings
- **MH Wilds** "The Little Engine that Shouldn't" Steam Deck config (PFCacklefanny):
  - Uploaded 3 Mar 2025, updated 18 Dec 2025. It turns off wind simulation, global illumination and volumetric fog, using REFramework add-ons (Lite Environment, More Graphics Options), a texture decompressor (needs about 37 GB free) and DirectStorage tweaks.
  - [claimed] About 30–45 fps at 1600×900 Balanced, 1280×800 Quality or 1024×640 native, often paired with Lossless Scaling frame generation.
  - The author now says it is outdated, because after update 1.040.03.02 "the game works".
  - — [Nexus Mods 183](https://www.nexusmods.com/monsterhunterwilds/mods/183)
- **Black Myth Wukong** "Downgraded Wukong Visuals" (21 Aug 2024): lowers settings below the in-game minimum. The creator saw modest gains on a strong GPU, expects more on a GTX 1050-class card, and says CPU-limited systems "likely won't benefit". No numbers given. — [TroubleChute](https://hub.tcno.co/videos/low-end-gpu-fix-mod-optimized-low-end-graphics-black-myth-wukong/)
- **Silent Hill 2 Remake** "Optimization Config FPS Boost" (AlexLionel, May 2025, updated Mar 2026):
  - Edits GameUserSettings `sg.*` scalability and `sg.ResolutionQuality`. The author claims Engine.ini has "almost no impact on core performance".
  - The image "may look blurry". No fps numbers given.
  - — [Nexus Mods 336](https://www.nexusmods.com/silenthill2/mods/336)
- **Clair Obscur: Expedition 33** on Steam Deck LCD: launch options unlock hidden settings. [claimed] "Between 20 and 30 FPS in most situations". The guide deliberately avoids untrusted binary downloads. 31 May 2025, updated Jan 2026. — [Boiling Steam](https://boilingsteam.com/better-settings-for-clair-obscur-expedition-33-on-the-steam-deck/)
- **Starfield**:
  - "Potato Mode" (BulwarkHD, Sept 2023) squishes textures to "as low as 16 bits". It looks "more at home on a PlayStation 2" and "may not be enough to get it to boot on some PCs". No fps given. — [PCWorld, 6 Sep 2023](https://www.pcworld.com/article/2057465/starfield-potato-mode-mod-lets-this-years-hottest-game-run-on-a-toaster.html)
  - Erok's "Starfield Optimizations" has a Potato preset for handhelds. On the Deck, fps dips into the low 20s before the mod; no after figure is given. — [Sportskeeda](https://sportskeeda.com/esports/starfield-performance-mod-steam-deck-low-end-pcs)
  - On Xbox Series S, the "1280x720 Resolution" mod removes the 30 fps cap and drops internal resolution from 900p to 720p. [measured, Digital Foundry] Up to about 120 fps in small interiors, about 100 in combat, and just over 40 in the busiest areas. The image is "noticeably blurrier". — [TechRadar, 25 Jun 2024](https://www.techradar.com/gaming/starfield-can-reach-up-to-120fps-on-xbox-series-s-thanks-to-new-mods)
- **Jedi Survivor** Potato preset: see Q3 ([Wccftech](https://wccftech.com/star-wars-jedi-survivor-performance-mod-reduces-stutters-increase-fps/amp/)).

### Inferences
- [inference] The Starfield Series S case is the cleanest "PS5-era to lower tier" data point. It reaches 40 fps in the worst areas even at 720p on a console GPU stronger than the Deck's. That suggests CPU-heavy city scenes stay the limiting factor whatever the graphics settings, consistent with the Dragon's Dogma 2 and MH Wilds findings.
- [inference] Potato mods and DeckForge's Tier S already overlap almost entirely: config cvars, resolution, effect toggles. The community has not gone beyond this without the engine source.

### Gaps
- I found no sourced fps numbers for Hogwarts Legacy, Cyberpunk 2077 or Stalker 2 potato mods on low-end or Deck hardware; the Cyberpunk source page failed to load.
- I found no rigorous image-quality comparisons. Descriptions are qualitative ("blurry", "PS2-like").
- I found no Wukong potato fps figures.

---

## Q5. Official downports: what it costs *with* source code

### Takeaway
With full source, an experienced port studio and the platform vendor's SDK, bringing a PS4/PS5-era game to weaker hardware took about **12 months** (Witcher 3 on Switch). It ended at 30 fps and 540p handheld, after a first pass that ran at 10 fps and needed 50% more memory than the console had. Hogwarts Legacy needed a nearly 4-month delay and segmented its open world with 30–50 s loading screens. Elden Ring on Switch 2 needed about a year's delay and lands at 432p–864p handheld and 30–35 fps with the PS4 feature set. Cyberpunk on Switch 2 was "not a gigantic effort", but it had a "super small team" working "end-to-end with Nintendo", plus DLSS hardware. That is the cost floor for "PS5-era into PS4-era" *with* the source.

### Cited Findings
- **Witcher 3 on Switch** (Saber Interactive with CD Projekt Red guidance; launched 15 Oct 2019):
  - CDPR's producer: "around 12 months at this point"; "Geometry is the same". — [Nintendo Life, Aug 2019](https://www.nintendolife.com/news/2019/08/the_witcher_3_switch_port_started_development_just_12_months_ago)
  - Saber CEO Karch: the first pass ran at "10 frames per second", needed about 50% more memory than Switch has, and was about 20 GB larger than the biggest cartridge. "We worked tirelessly for a year to get the game running on Switch at 30 fps." — [GoNintendo](https://gonintendo.com/stories/350579-saber-interactive-says-their-first-pass-port-of-witcher-3-on-swit)
  - Final result: 720p docked and 540p handheld, blurrier textures, reduced draw distance with pop-in. Saber had prior PS4 Pro/Xbox One S work on the game and a partner studio. — [EGM](https://egmnow.com/the-switcher-how-saber-interactive-took-one-of-the-biggest-games-ever-portable/)
- **Hogwarts Legacy on Switch** (released 14 Nov 2023):
  - Delayed from 25 July 2023, nearly four months. — [HotHardware](https://hothardware.com/news/switch-hogwartslegacy-port-delayed)
  - Roughly 30 fps with aggressive FSR, reduced lighting and detail. The open world is segmented with new loading screens, 30–50 s per SwitchUp. — [Wccftech, 14 Nov 2023](https://wccftech.com/hogwarts-legacy-switch-looks-performs-well-caveats/amp/); [GGRecon](https://www.ggrecon.com/articles/hogwarts-legacy-switch-port-loses-open-world-capabilities/)
  - Note: Wccftech credits Avalanche Software. Search-result headlines describe Nintendo buying the "Hogwarts Legacy Switch studio" ([VGC headline](https://videogameschronicle.com/news/nintendo-agrees-deal-to-buy-hogwarts-legacy-mortal-kombat-switch-studio)); I did not fetch the article to confirm which studio.
- **Cyberpunk 2077 on Switch 2** (released 5 June 2025):
  - "Super small team working end-to-end with Nintendo". Talks began in summer 2023, before an SDK existed.
  - Handheld Performance mode is 720p at up to 40 fps; Quality mode is 1080p30. — [GoNintendo](https://gonintendo.com/contents/49122-cd-projekt-red-on-bringing-cyberpunk-2077-to-switch-2-when-development-started)
  - "Not a gigantic effort whatsoever" (Jan Rosner, CDPR). — [GoNintendo](https://gonintendo.com/contents/48152-getting-cyberpunk-2077-running-on-switch-2-was-not-a-gigantic-effort-cd-project-red)
- **Elden Ring: Tarnished Edition on Switch 2**:
  - Announced in 2025; delayed in Oct 2025 "for performance adjustments"; released 28 Aug 2026. — [VGC, 4 Jun 2026](https://www.videogameschronicle.com/news/elden-ring-tarnished-edition-on-switch-2-finally-has-a-confirmed-release-date/)
  - [measured, Digital Foundry] "A successful port" with the PS4 feature set and no current-gen features. Dynamic resolution is 720–1080p docked and 432–864p handheld. Capped at 40 fps but typically 30–35. The delay was "immensely beneficial". — [Nintendo Life, 5 Sep 2026](https://www.nintendolife.com/news/2026/09/video-digital-foundry-delivers-its-tech-review-for-elden-ring-on-switch-2)
- **Resident Evil Village on iPhone 15 Pro and M-series iPad** (Capcom, Oct 2023): adjustable resolution, MetalFX upscaling and frame-rate targets. It "runs better on the M1 iPad" and needs "some tweaking". — [TouchArcade](https://toucharcade.com/2023/10/26/resident-evil-village-iphone-15-pro-review-frame-rate-resolution-max-capcom/)
- **Star Wars Outlaws on Switch 2**: Digital Foundry called it technically demanding and "surprising", even "an impossible port" per headlines. I found no team or duration data. — [Nintenderos, Apr 2025](https://www.nintenderos.com/2025/04/un-port-imposible-asi-definen-star-wars-outlaws-para-nintendo-switch-2-desde-digital-foundry/)

### Inferences
- [inference] Even with source, studios reached "PS4-class" results by cutting resolution to 432–720p handheld, accepting 30–40 fps, segmenting worlds and re-authoring or compressing assets. They did not keep PS5 image quality at lower cost. DeckForge's 45 fps handheld target is *more* demanding than what these professional downports shipped (30–40 fps).
- [inference] Effort scales with how far the target sits below the game's original floor. Witcher 3 (PS4 to Switch 1, a large gap) took about a year from a specialist studio. Cyberpunk (PS5 to Switch 2 with DLSS) was described as small.
- [inference] Without source, there is no precedent for this degree of restructuring (segmenting worlds, rebuilding LODs, recompressing assets) in a modern AAA game. Rebuilding even one title by reverse engineering would cost a multiple of these source-code efforts, then break on each game patch, and it is legally exposed (re3, Bloodborne, VC Nextgen).

### Gaps
- I found no team headcounts for any official downport.
- Development duration is not public for Hogwarts on Switch, Elden Ring on Switch 2 or RE Village on iPhone.
- I found no source confirming which studio did Hogwarts Switch, nor any Digital Foundry figures for its resolution.
- The question of who ported Elden Ring to Switch 2 is unanswered.

---

## Summary table

| Project | Type | Original platform & age | Effort (people, years) | Performance / quality result | Legal outcome | AI involvement |
|---|---|---|---|---|---|---|
| SM64 decomp + PC port | decomp | N64, 1996 | Community; "years-long"; decomp 2019, port 2020 | Widescreen, 4K, many platform ports | Nintendo law firm removed videos and listings (2020); decomp repo still public (Oct 2026) | None reported |
| Kaze SM64 rewrite | decomp-based source optimization | N64, 1996 | 1 expert, "hundreds of hours" (2022) | [claimed] up to 6× faster; stable 30 fps on real N64 (Expansion Pak) | None reported | None |
| OoT decomp → Ship of Harkinian | decomp + source port | N64, 1998 | ZRET "dozens", 21 months (to Nov 2021); SoH released Mar 2022 | 60 fps → up to 250 fps (interpolated), widescreen, Switch/Wii U | No Nintendo action reported | None reported |
| 2Ship2Harkinian (MM) | decomp port | N64, 2000 | Harbour Masters; released May 2024 | High fps via interpolation (logic still 20 fps) | None reported | None reported |
| Zelda64Recomp (MM) | static recomp | N64, 2000 | 2 core devs; days per new game once tooling exists; May 2024 | [claimed] 60 fps on Deck, widescreen, runs on GT 630 | None reported | None |
| Perfect Dark port | decomp + port | N64, 2000 | Decomp mostly 1 person (to Oct 2022); port by 1 person (2023) | 60 fps, widescreen, mouselook | None reported | None reported |
| re3 / reVC | decomp / reimplementation | PS2/PC, 2001–02 | 4 named devs | Not verified here | DMCA 2021; sued Sep 2021; dismissed with prejudice Apr 2023, terms undisclosed | None |
| GTA VC Nextgen | content ported into GTA IV engine | PS2/PC, 2002 | Revolution Team, about 2 years | Visual remaster-level upgrade | Take-Two takedown; YouTube removed; released anyway Jan 2025 | None reported |
| OpenMW | engine reimplementation | PC, 2002 | Community since 2008 (17+ yrs) | OSG renderer "significant performance improvements" | GPLv3, original data needed; no action | None reported |
| OpenRCT2 | reimplementation | PC, 2002 | about 250 contributors since 2014 | HD resolution, higher fps, multiplayer | GPLv3, original needed; no action | None reported |
| DevilutionX | decomp-derived port | PC, 1996 | Community | Widescreen; about 11 platforms | Non-commercial license; not Blizzard-endorsed | None reported |
| OpenJK | official source release + community | PC, 2002–03 | 3 leads + 14 significant contributors | Stability, performance, ARM/Apple Silicon | GPLv2 | None |
| Doom source ports | official source release | PC, 1993 | Hundreds of ports since 1997 | High resolution, uncapped fps, RT + DLSS (2022) | Legal (GPL since 1999) | None |
| Unleashed Recompiled | static recomp (XenonRecomp) | Xbox 360, 2008 | 2 leads + 17 credited; released about Mar 2025 | 60 fps+/unlocked, high res, ultrawide, D3D12/Vulkan; "several ms" frame-time savings from recomp optimizations | No Sega action reported | None reported |
| 2026 360 recomps (Darkness, Simpsons Game, etc.) | static recomp | Xbox 360, 2007–08 | Mostly small teams, 2026 | [claimed] Simpsons Game GPU 14.6 → 8.1 ms on Deck; Darkness uncapped fps, up to 3× res | None reported | Not reported |
| Mario Kart Wiicompiled | static recomp | Wii, 2008 | 1 dev; beta Sept 2026 | Up to 4K, unlocked fps | None so far | AI coding disclosed; backlash |
| Dusk (Twilight Princess) | decomp port | GameCube, 2006 | TP decomp team + Twilit Realm; Apr–May 2026 | Up to 120 fps (interpolation), ultrawide, mobile | None reported | Not mentioned |
| Melee decomp | decomp | GameCube, 2001 | About 6 years to 100% (Sept 2026) | No port yet | None | Unverified claim of a "GPT-6 Astra" finish (single unsourced site) |
| Snowboard Kids 2 decomp | decomp | N64, 1999 | 1 lead + community, 2025 | Matching about 25% → 45% in 3 weeks | None | Claude Opus 4.5 one-shot loop, human-reviewed |
| PS2Recomp / ps3recomp | static recomp tools | PS2 / PS3 | 1-person projects, 2025–26 | PS2: not functional (Jan 2026); PS3: boots to init and basic geometry (Jun 2026) | None | Not mentioned |
| P.T. native PC | hand reimplementation (own C++/Vulkan, original assets) | PS4, 2014 | 1 dev; v1.0 7 Oct 2026 | DLSS/FSR/XeSS, RT, "Original (PS4)" preset, Deck build | Needs own PS4 copy (delisted 2015); no action yet | Real-ESRGAN texture upscaling; AI coding not mentioned |
| Bloodborne 60 fps patch | binary patch | PS4, 2015 | 1 expert (2020) | 30 → 60 fps but 1080p → 720p; about 7 subsystems fixed | Sony DMCA on the page (early 2025) | None |
| Elden Ring FPS Unlocker | runtime memory patch | PC, 2022 | 1 dev (last release Mar 2022) | Unlocked fps, widescreen, FOV; EAC must be off | None | None |
| MH Wilds DLC-check fix | runtime fix (unreleased) → official | PC, 2025 | 1 Redditor; Capcom fix about 2 weeks later (Jan 2026) | [claimed] min 24 → 43, avg 30 → 49; official fix: min +8–20% [measured] | None | None |
| Jedi Survivor mods | config preset / hidden cvar | PC, 2023 | Solo modders (2023, 2026) | [claimed] Potato preset GTX 1070 30 → 60+ | None | None |
| Special K / FAR | hooking framework | NieR: Automata PC, 2017 | 1 core dev | Load 15 → 5 s, GI cuts, frame pacing; Square Enix adopted fixes in 2021 | None | None |
| Ultra+ | config + RED4ext plugin | Cyberpunk PC, 2020 | 1 lead, Oct 2023–Oct 2026, 80+ games | [claimed] PT20 40% faster than vanilla path tracing (high-end focus) | None | None |
| Alan Wake 2 v1.0.16.1 | official patch (non-mesh-shader path) | PC, 2023 | Remedy | [measured, DF] GTX 1070 +57%, 1080 Ti about +100% | n/a | n/a |
| Stalker 2 mod pack | config mod | PC, 2024 | Community | [measured] +27% at 4K on RTX 4080; pop-in | None | None |
| Starfield potato / Series S 720p mod | mod (textures / config) | PC/Xbox, 2023 | Solo modders | "PS2-like" textures; Series S 720p: 40–120 fps [measured, DF] | None (Series S via official Creations) | None |
| MH Wilds Deck config | config + REFramework | PC, 2025 | 1 modder (2025) | [claimed] 30–45 fps at 1024×640–1280×800 | None | None |
| Witcher 3 Switch | official port | PS4/PC, 2015 | Saber + partner studio, about 12 months | First pass 10 fps → 30 fps; 540p handheld / 720p docked | n/a | n/a |
| Hogwarts Legacy Switch | official port | PS5/PS4/PC, 2023 | Studio unconfirmed; about 4-month delay | About 30 fps, aggressive FSR, segmented world with 30–50 s loads | n/a | n/a |
| Cyberpunk 2077 Switch 2 | official port | PS5/PC, 2020/23 | CDPR "super small team"; "not a gigantic effort" | 720p at up to 40 fps handheld Performance mode | n/a | n/a |
| Elden Ring Switch 2 | official port | PS5/PS4/PC, 2022 | FromSoftware/Bandai; delayed about 1 year | [measured, DF] 432–864p handheld, 30–35 fps, PS4 feature set | n/a | n/a |
| RE Village iPhone | official port | PS5/PC, 2021 | Capcom | MetalFX upscaling; needs tweaking; better on M1 iPad | n/a | n/a |

**Bottom line for DeckForge** [inference]:
- No one, fan or AI-assisted, has reverse engineered and rebuilt a PS5-era AAA game to run on weaker hardware.
- Every rebuild that worked:
  - targeted a game at least 10 years old with a small binary, no online anti-cheat and no further patches;
  - took a community months to years;
  - got its gains from much stronger target hardware plus a new renderer.
- The one PS4-era rebuild (P.T., Oct 2026) is a single-corridor demo.
- Studios with source needed about a year and still shipped 30–40 fps at sub-720p handheld.
- The community's practical "downport" is config-level potato tuning (Tier S) plus occasional targeted defect fixes, which publishers often adopt.
- AI has measurably sped up matching decomp of small 1990s C functions (about 2× in one case). It has not been shown to work at modern-engine scale.

### Persistent memory note (for the caller)
DeckForge decision input as of 12 Oct 2026: there is no precedent for reverse engineering or rebuilding PS5-era games for weaker hardware. The closest data points are official downports (about 12 months with source; 30–40 fps, sub-720p handheld) and community potato configs (Tier S). AI-assisted decomp is proven only on small N64 functions; the Claude Opus 4.5 case went from about 25% to 45% matched in 3 weeks.
