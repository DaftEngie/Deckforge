# Which demanding 2022–2026 PC games a Steam Deck can run at 30 fps with near-High settings at native 800p (as of 11 Oct 2026)

> **Correction by the lead (2026-10-11):** the Lies of P result ("about 50 fps average" at default settings) was measured with FSR 2 set to Quality, not at native 800p. I checked the overkill.wtf article directly. Lies of P therefore belongs in class B, not A, and class A has 2 games (Elden Ring, Armored Core VI), about 6% of the 35 classified. Affected lines below are marked "[corrected]".

**How to read this.** In the notes, **[M]** means a tester reported numbers they saw on the Deck. **[C]** means a claim, a qualitative statement, a developer target or a prediction. Most "measured" Deck data are reviewers playing with an on-screen frame counter, not controlled benchmarks. Only a few sources report averages and lows: TechPowerUp (Spider-Man 2), SDHQ's analysis tool (Crimson Desert), SDHQ's Deck Dive (Hogwarts) and LevelUp's citation (Wukong). Most sources do not say whether they used an LCD or OLED Deck. The OLED is 2–9% faster ([Eurogamer via Overclockers.ru, cited in the DeckForge rethink note](https://overclockers.ru/blog/NOVO_GEEK/show/158278/Moe-mnenie-o-Steam-Deck-OLED-Eurogamer)).

**Search budget.** The shared per-turn web-search limit ran out near the end. The searches I could not run are listed under Gaps.

## Q1. What share of demanding 2022–2026 games reach 30 fps at High or near-High at native 800p?

### Takeaway
Of 35 classified games, only 2 (about 6%) clear the owner's bar of roughly High settings at native 800p and 30 fps: Elden Ring and Armored Core VI [corrected: Lies of P moved to B]. Both are 2022–23 games that also shipped on PS4.

- **Current-gen-only games (26 classified):** none reach class A. Most need Low settings plus heavy upscaling to hold about 30 (class C, 12 games) or miss 30 even then (class D, 8 games).
- **What "Verified" means:** Valve's Verified badge requires only 30 fps at the game's *default* settings ([Steamworks via DeckForge rethink note](https://partner.steamgames.com/doc/steamhardware/compat)). Many 2025–26 Verified games reach it with locked low presets that reviewers call blurry.

### Cited Findings

**Class A: about 30 fps at High or near-High, native 800p**
- **Elden Ring** (overkill.wtf, undated, about 2024, Shadow of the Erdtree era) [C]
  - Settings: 1280×800 custom, no upscaler mentioned, ray tracing off, 30 fps cap.
    - High: textures, AA, shadows, grass, water.
    - Medium: SSAO, depth of field, lighting, effects, volumetrics, GI.
    - Low: reflections, shader quality.
  - Result: fps "regularly dips into the mid-30s", so a 30 lock is safe. For 40 fps, lower Effects, Volumetrics and Grass. Limgrave is the heaviest area. [overkill.wtf](https://overkill.wtf/elden-ring-shadow-of-the-erdtree-best-settings-steam-deck)
  - SDHQ review (undated) [M]: a mixed High/Medium/Low build at 9 W TDP stays above 30, with 1–2 frame dips in six areas. [SDHQ](https://steamdeckhq.com/ja/game-reviews/elden-ring/)
  - The base game is Steam Deck Verified. [RPGSite](https://www.rpgsite.net/feature/17521-elden-ring-nightreign-steam-deck-impressions-recommended-settings-pc-port-features-rog-ally-performance)
- **Armored Core VI** (overkill.wtf, about Aug–Sep 2023) [M/C]
  - High preset at 1280×800 with a 30 lock is "near-flawless". Default settings uncapped ran about 34–50 fps.
  - Late bosses dip into the 30s. With dynamic resolution off there are short dips to 28.
  - [overkill.wtf](https://overkill.wtf/armored-core-vi-fires-of-rubicon-best-steam-deck-settings/)
- **Lies of P** (overkill.wtf, 15 Sep 2023) [M] [corrected: belongs in class B; the source's ~50 fps default result used FSR 2 Quality]
  - Default settings at native 800p: about 50 fps average, dipping into the 40s.
  - Lowering Visibility from High to Medium: about +12 fps. Lowering Shadows from Medium to Low: about +14 fps.
  - Recommended build: FSR 2 Quality plus a Medium/High mix, aiming toward 60 fps.
  - [overkill.wtf](https://overkill.wtf/lies-of-p-performance-review-best-settings-steam-deck)

**Class B: about 30 at Medium native, or at High only with an upscaler**
- **Elden Ring Nightreign** (RPGSite, 28 May 2025) [M]
  - Medium preset with Low shadows, 720p or 800p, no upscaler available: "mostly solid 30" with some drops.
  - Low preset at 720p: mostly above 30, mid-20s in particle-heavy moments. Closer to Shadow of the Erdtree than to the base game. [RPGSite](https://www.rpgsite.net/feature/17521-elden-ring-nightreign-steam-deck-impressions-recommended-settings-pc-port-features-rog-ally-performance)
  - Rated Playable, not Verified, at launch. [Icy Veins, 31 May 2025](https://wp-prod.icy-veins.com/best-elden-ring-nightreign-steam-deck-settings-for-performance/)
- **Kingdom Come: Deliverance II** (overkill.wtf, 3 Feb 2025) [M]
  - Low preset, 800p, no upscaling: 35–45 fps.
  - Recommended 30-cap build at native resolution with SMAA 2TX: textures High; objects, GI, shaders, vegetation and characters Medium; everything else Low. [overkill.wtf](https://overkill.wtf/kingdom-come-deliverance-2-best-settings-steam-deck)
  - RPGSite (4 Feb 2025, pre-release build plus day-one patch) [M]: Low settings, FSR Native AA at 800p, steady 30 cap. A 40 fps target needs FSR Balanced. [RPGSite](https://www.rpgsite.net/feature/16808-kingdom-come-deliverance-ii-steam-deck-recommended-settings-pc-features-rog-ally-impressions-review)
- **Hogwarts Legacy** (SDHQ Deck Dive, 21 Apr 2023, worst-case route from Hogsmeade to the Forbidden Forest) [M]
  - High stock: about 20 fps average. High with FSR 2 and tweaks: "almost 30". Low stock: just under 40.
  - Most results were in chart images I could not read. [SDHQ](https://steamdeckhq.com/news/hogwarts-legacys-performance-deck-dive/)
  - SDHQ review (7 Feb 2023) [M]: Low plus FSR 2 Quality gives a mostly steady 30. "Medium looked nearly the same as Low." Ultra hit 30 in many areas but halved when casting Lumos. The game is Verified. [SDHQ](https://steamdeckhq.com/game-reviews/hogwarts-legacy/)
- **Ghost of Tsushima** (overkill.wtf, about May–June 2024, OLED) [C]
  - Settings: 1280×800, FSR 3 Quality (the article also says Balanced), dynamic resolution off, 30 cap.
    - High: textures, level of detail.
    - Medium: shadows, terrain, volumetric fog.
    - Low: SSR, screen-space shadows.
    - Ambient occlusion: SSAO Performance.
  - Result: a 40 fps baseline is "possible"; cutscenes fall to the mid-20s. No measured numbers. [overkill.wtf](https://overkill.wtf/ghost-of-tsushima-performance-and-best-settings-for-steam-deck)
- **Resident Evil 4 remake**
  - Dexerto (24 Mar 2023) [M]: Low plus FSR 2 Balanced or Quality at 720p gives 40–60 fps with VRR; a locked 30 is recommended. [Dexerto](https://www.dexerto.com/tech/can-you-play-resident-evil-4-remake-on-steam-deck-2082782/)
  - GamePretty (29 Mar 2023) [C, unmeasured]: a 30 fps "Prettier" build at 800p with FSR 2 Quality.
    - High: textures (2 GB), mesh, particle lighting, rain.
    - Medium: shadows, volumetrics.
    - On: SSR, SSAO, contact shadows.
    - Needs CryoUtilities (a community Deck memory tweak) and 4 GB of VRAM. [GamePretty](https://gamepretty.com/resident-evil-4-remake-settings-for-30-or-40-fps-on-steam-deck/)

**Class B/C (my label): 30+ with an upscaler and headroom, but native Medium or High at 30 not measured**
- **God of War Ragnarök**
  - SDHQ (19 Sep 2024) [M]: FSR 3 Balanced gives 39–60 fps and "never went below 30". The settings preset is not named. [SDHQ](https://steamdeckhq.com/news/god-of-war-ragnarok-fantastic-on-steam-deck)
  - The Backdash (20 Sep 2024) [C]: mostly Low with Medium textures and FSR 3.1 Performance "mostly" hits 40, with dips to the low 30s. [Backdash](https://www.thebackdash.com/tech/god-of-war-ragnarok-steam-deck-settings)
- **007 First Light** (SDHQ, 26 May 2026) [M]
  - Default (all lowest) with FSR Performance: 50–70 fps, 40–50 in NPC-heavy areas.
  - Textures High; terrain, shadows and reflections Medium; volumetrics Low; FSR Quality: 32–40 fps.
  - The Deck's 45 fps limiter added input lag. [SDHQ](https://steamdeckhq.com/news/007-first-light-steam-deck-first-impressions/)
  - Steam Deck Verified in July 2026, per a GamingOnLinux headline I did not open. [GoL](https://www.gamingonlinux.com/2026/07/007-first-light-is-now-steam-deck-steam-machine-verified/page=1/)
- **Resident Evil Requiem** (SDHQ, 25 Feb 2026, OLED) [M]
  - Lowest preset with 16x anisotropic filtering and FSR 3.1.5 Balanced or Quality, targeting 45 fps at 90 Hz. Indoors exceeds 60; uncapped indoors about 80 fps. The default is FSR 1 with a 30 cap. [SDHQ](https://steamdeckhq.com/news/resident-evil-requiem-is-surprisingly-playable-on-steam-deck-so-far-early-impressions/)
  - Rated Unsupported despite running well. [Notebookcheck, 5 Mar 2026](https://www.notebookcheck.net/Resident-Evil-Requiem-receives-Unsupported-rating-on-Steam-Deck-even-though-it-runs-well.1242272.0.html)
- **Pragmata**
  - SDHQ (undated, about Apr 2026) [M]: default settings with FSR 3 hold a stable ~40 fps; uncapped reaches 60 in most of the game. The Switch 2 in handheld mode fluctuates into the 20s in open areas. [SDHQ](https://steamdeckhq.com/ja/news/pragmata-nintendo-switch-2-vs-steam-deck/)
  - Verified at launch. [RPGSite, 17 Apr 2026](https://www.rpgsite.net/news/20148-pragmata-steam-deck-verified-valve-rating-performance)

**Class C: about 30 only at Low with upscaling (or a locked Deck preset)**
- **Monster Hunter Wilds**
  - SDHQ (28 Jan 2026, after the PC performance patch) [M]: lowest settings give a stable 30 in quiet or indoor areas, mid-20s in Scarlet Forest, below 20 near the Windward Plains watering hole, and high teens to low 20s in large open areas. [SDHQ](https://steamdeckhq.com/news/monster-hunter-wilds-1040-performance/)
  - Notebookcheck (30 Jan 2026), citing Daniel Owen and Deck Wizard: "roughly 30" with FSR or XeSS and no frame generation. [Notebookcheck](https://www.notebookcheck.net/Monster-Hunter-Wilds-fixes-DLC-bug-greatly-reduces-FPS-drops-and-runs-at-30-FPS-on-Steam-Deck.1215270.0.html)
  - Verified on 20 Aug 2026. [RPGSite](https://www.rpgsite.net/news/21151-monster-hunter-wilds-is-now-steam-deck-verified-by-valve)
  - PC Guide (25 Aug 2026) [C]: default settings "generally stayed at 30 or above", but the image is "extremely blurry and pixelated". [PC Guide](https://www.pcguide.com/news/monster-hunter-wilds-is-now-officially-steam-deck-verified-but-its-still-just-a-blurry-pixelated-mess/)
  - I class it C after the August 2026 Verified update; it was class D through January 2026.
- **Helldivers 2** (SDHQ review, 15 Feb 2024, LCD) [M]
  - 1280×800 with Render Scale Balanced (upscaled), 30 cap, no TDP limit.
  - Settings: textures Ultra; shadows, object detail and terrain Medium; most else Low; SSGI and AO off.
  - Mostly a steady 30, up to about 40 when calm, brief dips to the low 20s in swarms and extraction. Rated Deck Playable. [SDHQ](https://steamdeckhq.com/game-reviews/helldivers-2/)
- **Cyberpunk 2077 2.0 + Phantom Liberty** (SDHQ, 23 Sep 2023, patch 2.0) [M]
  - A modified Steam Deck preset with shadows and SSR lowered, plus FSR 2.1 Balanced: mostly a stable 30, including combat.
  - The burning-city first mission: 21–23 fps (26–27 at lowest). Dogtown driving: 19–25 fps, which the author blames on prop density and pop-in. [SDHQ](https://steamdeckhq.com/news/cyberpunk-2077-phantom-liberty-runs-on-steam-deck/)
- **Black Myth: Wukong**
  - Unnamed tester cited by LevelUp (20 Aug 2024) [M]: 1280×800 medium-low averages 35 fps with a 26 fps minimum; upscaler not stated. [LevelUp](https://www.levelup.com/noticias/prueban-black-myth-wukong-con-43-tarjetas-graficas-diferentes-para-ver-cuales-lo-pueden-correr-sin-problemas-tambien-lo-testearon-en-la-steam-deck-y-la-asus-rog-ally/)
  - Destructoid (29 Aug 2024) [C]: Low preset, FSR at super resolution 50 and frame generation on gives about 45 fps, but only with frame generation. [Destructoid](https://destructoid.com/best-steam-deck-settings-for-black-myth-wukong)
- **Doom: The Dark Ages**
  - SDHQ (11 May 2025, launch) [M]: Low at 720p with XeSS Quality runs in the low 20s with enemies on screen; 30 fps needed 960×540. Ray tracing is forced. [SDHQ](https://steamdeckhq.com/news/how-doom-the-dark-ages-runs-on-the-steam-deck)
  - GamingOnLinux (16 Oct 2025) [C]: a handheld update made it Verified, with a developer target of "720p @ ~30FPS". [GoL](https://www.gamingonlinux.com/2025/10/doom-the-dark-ages-gets-a-major-performance-upgrade-for-handhelds-now-steam-deck-verified/page=1/)
- **Final Fantasy XVI** (PCGamesN, demo, undated, OLED) [M]
  - Lowest settings, 800p borderless, FSR 3 with dynamic resolution: 31 fps average. Dynamic resolution off with FSR Quality: 26 fps. [PCGamesN](https://www.pcgamesn.com/steam-deck/final-fantasy-xvi-demo-performance)
  - Verified on 6 Oct 2026. [Final Weapon](https://finalweapon.net/2026/10/06/final-fantasy-xvi-steam-deck-verified/)
- **Final Fantasy VII Rebirth** (Noticias3D, 23 Jan 2025, citing Wccftech) [M]: minimum settings with upscaling and a heavily reduced resolution give about 30, dipping to 25 and lower. Verified at launch. [Noticias3D](https://www.noticias3d.com/noticia/96693/final-fantasy-vii-rebirth-rendimiento-steam-deck.html)
- **Assassin's Creed Shadows**
  - Verified at launch (14 Mar 2025), with graphics settings locked on the Deck except upscaling. No fps measured. [SDHQ](https://steamdeckhq.com/news/assassins-creed-shadows-steam-deck-verified/)
  - RPGSite's Switch 2 review (about Dec 2025): on its own screen the Deck looks sharper than Switch 2, and its 30 cap is better implemented, but it drops below Switch 2 in some portions. [RPGSite](https://dev.rpgsite.net/review/19212-assassins-creed-shadows-nintendo-switch-2-review-vs-steam-deck-ps5)
- **Clair Obscur: Expedition 33** (RPGSite, 12 Dec 2025) [M]
  - The locked default Deck preset with TSR gives 30–45 fps.
  - Custom settings with TSR at its Low scaling mode: 30–35 outdoors, minimum 28–29, brief drops to 25–26.
  - Unsupported at launch, now Verified. The author calls the locked preset's downgrades "too much". [RPGSite](https://www.rpgsite.net/feature/17274-clair-obscur-expedition-33-steam-deck-impressions-pc-port-features-performance-rog-ally-and-more)
  - Boiling Steam (May 2025, LCD): "20–30 in most situations". [Boiling Steam](https://boilingsteam.com/better-settings-for-clair-obscur-expedition-33-on-the-steam-deck/)
- **Silent Hill 2 remake** (SDHQ, 6 Oct 2024) [M]
  - Forest at lowest settings dips to 18 fps; at 50% resolution scale about 30, but "very blurry".
  - Town with a Medium/Low mix at 66% scale: 30–35, dipping to 28. [SDHQ](https://steamdeckhq.com/news/silent-hill-2-may-be-playable-on-steam-deck-first-impressions/)
  - Patch 1.04 (22 Oct 2024) added Deck optimizations, but no figures were published. [PCGH](https://www.pcgameshardware.de/Silent-Hill-2-Spiel-33019/News/Performance-Update-Steam-Deck-1458139/)
- **Death Stranding 2** (PC release 19 Mar 2026, with a "Portable" preset; listed as Verified) [GoL](https://www.gamingonlinux.com/2026/02/death-stranding-2-pc-specs-have-been-revealed-along-with-a-portable-preset-for-handhelds/page=1/)
  - Launch (SDHQ, 19 Mar 2026) [M]: Portable preset with PICO upscaling on Performance gives 19–25 fps, down to 10 in combat and sandstorms. [SDHQ](https://steamdeckhq.com/news/death-stranding-2-not-playable-on-steam-deck/)
  - After Patch 1.2 (games.gg, 9 Jun 2026) [M]: Portable preset holds 30–35 in the open world and nearly 50 indoors. [games.gg](https://games.gg/de/news/death-stranding-2-patch-12-verbessert-steam-deck-performance/)
- **Onimusha: Way of the Sword** (SDHQ benchmark tool, 14 Jul 2026) [M]: on Lowest (the default), combat stays mostly above 30. The Low preset drops below 30 far more often. [SDHQ](https://steamdeckhq.com/news/onimusha-way-of-the-sword-benchmark-tool-steam-deck/)

**Class D: below 30 even at the lowest settings with upscaling**
- **Warhammer 40K: Space Marine 2** (The Backdash, 6 Sep 2024) [M]
  - Custom Low settings, FSR 2, SSR off, 15 W, 30 cap: 20–30 fps, low 20s in large battles. [Backdash](https://www.thebackdash.com/tech/space-marine-2-steam-deck-settings)
  - FSR 3 was added on 10 Dec 2024 "without adding much performance"; no new measurement. [SDHQ](https://steamdeckhq.com/news/warhammer-40000-space-marine-2-gets-fsr-3/)
- **Starfield** (GGRecon, 6 Sep 2023, launch patch, player reports) [C]: 720p, all Low, FSR 2 with dynamic resolution and VRS, 30 cap gives 20–30 fps, about 20 in fights. Not Verified at the time. [GGRecon](https://www.ggrecon.com/guides/starfield-steam-deck-verified-performance-best-settings/)
- **Alan Wake 2** (SDHQ, 28 Oct 2023) [C]: lowest settings with Proton GE and workarounds "regularly" drop below 30. [SDHQ](https://steamdeckhq.com/tips-and-guides/alan-wake-2-on-steam-deck/)
- **Dragon's Dogma 2** (RPGSite, 20 Mar 2024, launch) [M]: below 15 fps at the lowest settings with heavy stutter, using 13 GB of RAM and 5 GB of VRAM. [RPGSite](https://www.rpgsite.net/feature/15623-dragons-dogma-2-an-amazing-game-but-you-wont-be-running-it-on-steam-deck)
- **Stalker 2**
  - GamingOnLinux (20 Nov 2024) [M]: Low at 1280×800 runs about 15 fps native and about 23 with FSR Ultra Performance; some areas fall below 10. Valve rated it Unsupported. [GoL](https://www.gamingonlinux.com/2024/11/stalker-2-heart-of-chornobyl-review-works-on-linux-desktop-with-proton-but-poorly-on-steam-deck/page=1/)
  - Update 2.0 (Unreal Engine 5.5.4), via Rock Paper Shotgun and TweakTown (21 Aug 2026) [M]: "roughly 30 FPS on average" with aggressive FSR, but still no consistent 30 minimum. [TweakTown](https://www.tweaktown.com/news/113170/stalker-2-receives-massive-performance-boost-with-new-2-0-update-game-gets-upgraded-to-unreal-engine-5-5-4/index.html)
- **Indiana Jones and the Great Circle** (SDHQ, 6 Dec 2024) [M]: lowest settings give 18–28 fps outdoors and 30–40 in the museum. Ray tracing is forced and cannot be turned off. [SDHQ](https://steamdeckhq.com/news/indiana-jones-should-not-be-played-on-steam-deck/)
- **Marvel's Spider-Man 2** (TechPowerUp via Notebookcheck, 5 Feb 2025) [M]: at 720p, Very Low averages 26 fps with a 12.8 minimum; Low averages 21.1. [Notebookcheck](https://www.notebookcheck.net/Unplayable-on-Steam-Deck-Marvel-s-Spider-Man-2-tested-with-gaming-handhelds-ROG-Ally-manages-playable-frame-rates-despite-hiccups.956463.0.html)
  - Valve pulled the Verified badge, then a later patch restored it. No post-patch fps were found. [SDHQ](https://steamdeckhq.com/ja/news/marvels-spider-man-2-performance-improvements-steam-deck/)
- **Horizon Forbidden West** (the sources conflict)
  - Digital Foundry, via Multiplayer.it (29 Mar 2024): the Deck "struggles to hold 30 fps even at the lowest settings with the scaler enabled". [Multiplayer.it](https://multiplayer.it/notizies/horizon-forbidden-west-pc-vs-ps5-impostazioni-suggerite-da-digital-foundry.html)
  - overkill.wtf (about May 2024) [C]: dynamic resolution scaling with a 30 target, XeSS, shadows Very Low and LOD Low give a "fairly stable 30", dipping to the low 20s. [overkill.wtf](https://overkill.wtf/horizon-forbidden-west-best-settings-for-steam-deck)
  - I class it D, conservatively.
- **Crimson Desert** (SDHQ, 13 Aug 2026) [M]
  - Lowest settings with FSR Ultra Performance cannot hold 30 in normal play.
  - An 8-enemy fight measured with an analysis tool: 29.8 fps average, 14.9 at 1% low, 11.5 at 0.1% low. Patches did not meaningfully help.
  - Verified anyway; SDHQ disputes the badge. [SDHQ](https://steamdeckhq.com/news/crimson-desert-steam-deck-verified-badge/)

**Class X: does not run**
- **Battlefield 6:** EA's Javelin anti-cheat blocks Linux and SteamOS, with "no workaround". [GoL, 10 Oct 2025](https://www.gamingonlinux.com/2025/10/battlefield-6-releases-today-and-it-will-not-be-playable-on-any-linux-steamos-system/page=1/) An EA job listing (Mar 2026) mentions a future Linux/Proton path, with no timeline. [Notebookcheck](https://www.notebookcheck.net/Battlefield-6-and-Madden-NFL-to-come-to-SteamOS-and-ARM-PCs.1243276.0.html)
- **Marathon:** uses BattlEye, and Bungie has not enabled Linux support. "Most likely unplayable" on SteamOS (pre-launch prediction, 20 Jan 2026; no confirmation after launch found). [GoL](https://gamingonlinux.com/2026/01/marathon-from-bungie-is-out-march-5th-likely-unplayable-on-steamos-linux)

**Not classified (no measured data found)**
- **Baldur's Gate 3:** Verified. A native Steam Deck build shipped on 23–24 Sep 2025. Larian claims it lowers "CPU usage and memory consumption" and reduces frame-rate spikes in Act 3's Lower City. No fps figures were found. [GoL](https://gamingonlinux.com/2025/09/baldurs-gate-3-gets-a-native-linux-version-to-improve-it-on-steam-deck); [KitGuru](https://www.kitguru.net/page/65/!https:/www.kitguru.net/desktop-pc/mustafa-mahmoud/baldurs-gate-3-gets-surprise-steam-deck-optimisation-update/)
- **Phantom Blade Zero** (Sep 2026): developers promise good performance on low-end hardware; no Deck test was found.

**Hardware reference**
- Deck: 4-core/8-thread Zen 2 at 2.4–3.5 GHz; an 8-compute-unit RDNA 2 GPU of about 1.6 TFLOPS; 88 GB/s memory bandwidth (LCD) or 102.4 GB/s (OLED); 1280×800 at 215 ppi (LCD) or 204 ppi (OLED). [Wikipedia](https://en.wikipedia.org/wiki/Steam_Deck)
- Series S: 20 compute units, 4.0 TFLOPS, 8-core Zen 2 at 3.6 GHz (one core reserved), 224 GB/s on its 8 GB graphics pool. [Wikipedia](https://en.wikipedia.org/wiki/Xbox_Series_X_and_Series_S)

### Inferences
- **The bar is met only by games built for PS4-class hardware.**
  - Both class A games are cross-gen titles from 2022–23 [corrected]. The PS4 platform lists come from my background knowledge; I did not source them in this pass.
  - Cross-gen games with a PS4 version: 9 classified, of which A = 2, B = 5, B/C = 1, D = 1 (Horizon Forbidden West) [corrected].
  - Current-gen-only games: 26 classified, of which A = 0, B = 1 (Kingdom Come: Deliverance II), B/C = 3, C = 12, D = 8, X = 2.
- **Verified does not mean High.** At least five 2025–26 Verified games (Monster Hunter Wilds, Crimson Desert, Assassin's Creed Shadows, Clair Obscur, Doom: The Dark Ages) reach the badge with locked or lowest presets plus upscaling.
- **Most class C and D games are upscaling from far below 800p.** Typical render scales are 50–67%, or FSR Performance and Ultra Performance. Native 800p needs about 1.5–4x more pixels, which no settings tool can make up.
- **Patches move games but rarely past one class.** Death Stranding 2 went from D to C, Stalker 2 from D to borderline C/D, Doom: The Dark Ages from D to C, and Monster Hunter Wilds from D to C. None reached B.

### Gaps
- **Searches blocked by the budget:** measured Baldur's Gate 3 Deck fps, especially Act 3 on the native build; Indiana Jones, Dragon's Dogma 2, Starfield and Alan Wake 2 after their later patches; Space Marine 2 after the FSR 3 patch; Phantom Blade Zero.
- **Deck status not confirmed this pass:** Space Marine 2, Alan Wake 2, Wukong, Dragon's Dogma 2, God of War Ragnarök, Kingdom Come II, Silent Hill 2, Ghost of Tsushima, Horizon Forbidden West, RE4, Lies of P, Armored Core VI and Cyberpunk.
- **Old data:** the Elden Ring, Ghost of Tsushima and Horizon Forbidden West pages are undated. Results for Starfield, Alan Wake 2, Cyberpunk (patch 2.0), Hogwarts and RE4 come from 2023 patches.
- **No Digital Foundry Deck analyses were found with numbers** for these games.

## Q2. How much can a "perceptual" settings optimizer gain over the game's High preset?

### Takeaway
Published optimized settings usually beat Ultra by 20–80%, but beat High by only about 5–25%. Some "quality-optimized" builds are even slower than High while looking better. For most demanding games the Deck sits 1.5–2x or more below 30 fps at native High. A perceptual optimizer can therefore improve the look *within* the 30 fps budget, but it can rarely move a game into class A.

### Cited Findings
- **TechSpot / Hardware Unboxed, Starfield** (8 Sep 2023; RTX 3070, 1440p native) [M]
  - The "Quality" optimized build beats Ultra by +19% in New Atlantis and +39% in the forest. The "Performance" build: +35% and +64%. The High preset alone: +14% and +29% over Ultra.
  - The Quality build is "slightly more efficient than High".
  - Per-setting costs:
    - Shadows Ultra→High: +9% (city), +26% (forest); High "holds up well". High→Medium adds pop-in.
    - Volumetric lighting Ultra→Medium: +2–3%, differences "hard to spot".
    - GTAO Ultra→High: +2%, subtle.
    - Contact shadows at Low: about +4%, very subtle.
    - Particles High→Medium: about +2% on 1% lows, no visible difference.
    - Depth of field off: about +3%. Motion blur off: about +2%.
    - Indirect lighting: no measurable cost.
  - Not worth cutting: grass at Low gains only 2%; reflections at Low gain 4% with a visible loss.
  - [TechSpot](https://www.techspot.com/guides/2732-starfield-optimization/)
- **TechSpot, Black Myth: Wukong** (23 Aug 2024; RTX 4070 Super, 1440p, DLSS Quality) [M]
  - The Quality-optimized build is at least 50% faster than Cinematic but about 8% *slower* than High. The Performance-optimized build is over 80% faster than Cinematic and about 10% faster than High. High alone is 70% faster than Cinematic.
  - Per-setting costs:
    - Shadows Cinematic→High: 28% (Nvidia) or 36% (AMD); "one of the most influential settings".
    - GI: 13% at High, 22% at Medium; scene-dependent and sometimes minimal, but Low "completely alters" the look.
    - Hair at Medium: about 7% average and 23% on 1% lows in a boss fight; still acceptable.
    - View distance at Medium: about 3%, mainly distant foliage.
    - Vegetation: 3–5%, with visible density loss.
    - Reflections: 7–8% in reflective areas, visible.
  - [TechSpot](https://www.techspot.com/guides/2884-wukong-optimization/)
- **TechSpot, "Ultra vs High"** (5 Oct 2021; RTX 3080, 4K, 9 games) [M]
  - Going from Ultra to High gains 5–47%, "typically 15 to 25 percent".
  - The visual impact is "small" in most games, with draw distance and distant AO the least visible. Days Gone was the exception: High removed visible shadows and AO.
  - [TechSpot](https://www.techspot.com/article/2338-ultra-vs-high-settings/)
- **TechSpot, Stalker 2** (23 Nov 2024; RTX 4090): Epic→High gains 12–18%; Epic→Medium gains 21–28%. CPU-limited at 1080p. [TechSpot](https://www.techspot.com/review/2926-stalker-2-benchmark/)
- **TechSpot, Space Marine 2** (12 Sep 2024): Medium beats High by only 5–10% at 1080p. [TechSpot](https://www.techspot.com/review/2891-warhammer-space-marine-2-benchmark/)
- **Digital Foundry optimized settings mostly mirror console presets, and no percentage gains were retrievable.**
  - Horizon Forbidden West: the optimized build "largely mirrors" PS5 presets, usually High (29 Mar 2024). [Multiplayer.it](https://multiplayer.it/notizie/horizon-forbidden-west-pc-vs-ps5-impostazioni-suggerite-da-digital-foundry.html)
  - Avatar: Frontiers of Pandora: the build is meant to look like PS5 Performance mode (21 Dec 2023). [Vandal](https://vandal.elespanol.com/noticia/1350767894/digital-foundry-explica-como-optimizar-el-pc-para-avatar-frontiers-of-pandora/)
  - Assassin's Creed Shadows tiers (31 Mar 2025) [Multiplayer.it](https://psapp.multiplayer.it/notizie/come-gira-assassins-creed-shadows-su-pc-analisi-di-digital-foundry.html) and Dragon Age: The Veilguard (30 Oct 2024) [Multiplayer.it](https://multiplayer.it/notizie/dragon-age-the-veilguard-pc-promosso-digital-foundry-impostazioni-grafiche-consigliate.html): no percentages reported.
- **Setting costs measured on the Deck itself**
  - Lies of P: Visibility High→Medium about +12 fps, Shadows Medium→Low about +14 fps, from roughly 50 fps (about +24% and +28%). [overkill.wtf](https://overkill.wtf/lies-of-p-performance-review-best-settings-steam-deck)
  - Ghost of Tsushima: SSAO Performance saves an estimated 2–4 fps. [overkill.wtf](https://overkill.wtf/ghost-of-tsushima-performance-and-best-settings-for-steam-deck)
  - Space Marine 2: SSR is "very GPU heavy" on the Deck and should stay off. [Backdash](https://www.thebackdash.com/tech/space-marine-2-steam-deck-settings)
  - Hogwarts: an overclock plus undervolt raised averages about 33% on Low but only about 7% on High. The FSR tweaks on High are cited at about 15%. The Deck "simply can't get enough VRAM", causing asset-streaming stutter. [SDHQ Deck Dive](https://steamdeckhq.com/news/hogwarts-legacys-performance-deck-dive/)
- **What reviewers say is visible on the 800p screen**
  - Hogwarts: Medium "looked nearly the same as Low". [SDHQ](https://steamdeckhq.com/game-reviews/hogwarts-legacy/)
  - Clair Obscur: the lowest shadows make close-up conversation scenes look poor. [Boiling Steam](https://boilingsteam.com/better-settings-for-clair-obscur-expedition-33-on-the-steam-deck/)
  - Kingdom Come II: reviewers preferred native resolution over FSR for clarity and because upscaling hurts UI text. [overkill.wtf](https://overkill.wtf/kingdom-come-deliverance-2-best-settings-steam-deck); [RPGSite](https://www.rpgsite.net/feature/16808-kingdom-come-deliverance-ii-steam-deck-recommended-settings-pc-features-rog-ally-impressions-review)
  - Monster Hunter Wilds' Verified preset is "extremely blurry and pixelated", with muddy textures. [PC Guide](https://www.pcguide.com/news/monster-hunter-wilds-is-now-officially-steam-deck-verified-but-its-still-just-a-blurry-pixelated-mess/)
  - Crimson Desert at its lowest settings looks "blocky, blurry". [SDHQ](https://steamdeckhq.com/news/crimson-desert-steam-deck-verified-badge/)
  - Silent Hill 2 at 50% scale is "very blurry". [SDHQ](https://steamdeckhq.com/news/silent-hill-2-may-be-playable-on-steam-deck-first-impressions/)

### Inferences
- **Typical gain at a High-equivalent look is about +5–25% over the High preset.** Computed from TechSpot's Starfield figures, the Quality build is about +4% (city) and +8% (forest) over High; the Performance build is about +18% and +27%. Wukong's Performance build is about +10%.
- **Cheap-to-cut, hard-to-see at low resolution:**
  - volumetric quality
  - AO quality steps above the first "on" level
  - contact shadows
  - particle quality
  - hair quality
  - distant view distance and LOD
  - depth of field and motion blur
  - the shadow step from Ultra to High
- **Expensive and visible, so a perceptual optimizer must not cut them:**
  - shadows from High down to Low
  - GI at Low
  - reflections where surfaces are wet or metallic
  - vegetation density
  - render resolution and upscaler mode, the most visible on the Deck per the reviewer statements above
- **Screen math (my calculation, not sourced).** 20/20 acuity resolves about 1 arcminute: roughly 291 ppi at 30 cm and 218 ppi at 40 cm. The Deck's 204–215 ppi sits at that limit at a typical 30–40 cm, so whole-pixel blur from upscaling is visible. Detail below one pixel contributes less: shadow-map resolution beyond about one texel per pixel, AO sample count, and distant foliage density.
- **The ceiling for an optimizer.** It can deliver class A only where High at native already runs at about 24–28 fps. On current evidence that means at most a handful of cross-gen titles that are already A or close to it. Nightreign at Medium about 30, and Ghost of Tsushima and RE4 at near-High with FSR Quality, are the plausible candidates; none is measured.
- **Where the gap is too big.** Hogwarts runs about 20 fps at High native, so it needs about +50%. Upscaled class C games need 1.5–4x. No perceptual tuning closes those gaps.

### Gaps
- No Digital Foundry or Hardware Unboxed optimized-settings figures were retrieved for Cyberpunk 2.x, Alan Wake 2, Monster Hunter Wilds, Indiana Jones or Hogwarts. The search budget ran out.
- No formal study was found on what is visible at 800p on a 7-inch screen. The acuity calculation above is my own.
- Per-setting costs measured *on the Deck* exist only for Lies of P, plus estimates for Ghost of Tsushima and Elden Ring.

## Q3. How do Series S, Switch 2 and PS4 versions compare? Is "High at 800p" possible?

### Takeaway
Where the developers' own Series S version runs at 720p–1080p and 30 fps on reduced settings, the Deck measures C or D. The one exception is Kingdom Come II, whose Series S version renders 1080p native without upscaling and which measures B on the Deck. On the handheld side, the Switch 2 and the Deck land in roughly the same class. The data does not support "High at 30" on the Deck for any current-gen-only title.

### Cited Findings
- **Alan Wake 2:** Series S runs 720p in one quality mode at "mostly stable" 30 fps (Digital Foundry, via PPE.pl, Nov 2023). Deck: D. [PPE.pl](https://www.ppe.pl/news/329586/alan-wake-2-dziala-doskonale-na-xboksie-series-x-rozgrywka-na-ps5-porownana-do-wersji-na-xboksa-series-s.html)
- **Monster Hunter Wilds:** Series S is capped at 1080p, targets 30, often falls below 30 to about 25, has no SSR and muddy textures. Unlocking the frame rate adds little (Digital Foundry, via Nintendo Life, Feb 2025). Deck: D, then C. [Nintendo Life](https://nintendolife.com/news/2025/02/monster-hunter-wilds-tech-analysis-has-us-concerned-about-a-switch-2-port)
- **Space Marine 2:** Series S runs 1440p at 30 with no performance mode (official specs, Aug 2024). Deck: D. [Pure Xbox](https://www.purexbox.com/news/2024/08/xbox-series-x-and-s-tech-specs-revealed-for-warhammer-40k-space-marine-2)
- **Starfield:** Series S renders 900p internally, FSR 2 to about 1440p, locked 30; it dips only in two cities (Digital Foundry via Pure Xbox, Sep 2023). Deck: D. [Pure Xbox](https://www.purexbox.com/news/2023/09/starfield-is-a-solid-day-one-experience-on-xbox-according-to-digital-foundry)
- **Kingdom Come: Deliverance II:** Series S runs "straight 1080p, 30FPS" with no upscaling (official specs, Dec 2024). Deck: B. [Pure Xbox](https://purexbox.com/news/2024/12/kingdom-come-deliverance-2-full-xbox-tech-specs-revealed)
- **Black Myth: Wukong:** Series S performance mode holds a "steady 60" (21 Aug 2025; tester not named). Deck: C. [TweakTown](https://www.tweaktown.com/news/107235/black-myth-wukong-runs-at-60fps-on-xbox-series-s-after-all/index.html)
- **Indiana Jones:** Series S runs 60 fps at lower resolution and with reduced textures (Pure Xbox, Dec 2024). Deck: D, at 18–28 fps on the lowest settings. [Pure Xbox](https://purexbox.com/news/2024/12/video-indiana-jones-comparison-shows-difference-between-xbox-series-x-and-s-versions)
- **Assassin's Creed Shadows:** Series S and Switch 2 both drop strand hair and ray-traced GI. Switch 2 also cuts SSAO, foliage, textures and shadows, and swaps SSR for cube maps (Digital Foundry via Pure Xbox, Dec 2025). [Pure Xbox](https://www.purexbox.com/news/2025/12/digital-foundry-compares-xbox-series-s-and-switch-2-in-new-assassins-creed-shadows-analysis)
- **Switch 2 vs Deck, Cyberpunk** (Digital Foundry, Jul 2025)
  - Switch 2 handheld targets 30 at a higher resolution than the Deck, with "slightly more instability" in the Kabuki run.
  - Power draw: Deck 24.5 W, Switch 2 8.9 W. Capped to Switch 2's power draw, the Deck ran 9–13 fps.
  - [Nintendo Life](https://www.nintendolife.com/news/2025/07/video-switch-2-and-steam-deck-face-off-in-cyberpunk-2077-benchmark-test); [Notebookcheck](https://www.notebookcheck.net/Steam-Deck-and-Switch-2-performance-compared-in-Cyberpunk-2077-with-one-handheld-thriving-when-docked.1055095.0.html)
- **Elden Ring on Switch 2** (Digital Foundry, 5 Sep 2026): the PS4 feature set; handheld at 432p–864p; docked typically 30–35 fps. [Nintendo Life](https://www.nintendolife.com/news/2026/09/video-digital-foundry-delivers-its-tech-review-for-elden-ring-on-switch-2)
- **Hogwarts:** Switch 2 holds a stable 30; the Deck's Verified default at 720p matches it (LOS40, Aug 2025). [LOS40](https://los40.com.mx/2025/06/18/hogwarts-legacy-analisis-en-nintendo-switch-2-vs-rog-ally-vs-steam-deck/) Digital Foundry's overall verdict on Switch 2 vs Deck: "no clear winner". [Multiplayer.it](https://multiplayer.it/notizie/nintendo-switch-2-contro-steam-deck-nel-confronto-definitivo-di-digital-foundry.html)
- **Pragmata:** the Deck holds about 40 with FSR 3; Switch 2 handheld falls into the 20s in open areas. [SDHQ](https://steamdeckhq.com/ja/news/pragmata-nintendo-switch-2-vs-steam-deck/)

### Inferences
- **FLOPS per pixel at 30 fps.**
  - Deck: about 1.6 TFLOPS ÷ 1.02 MP = about 1.56 TF per megapixel.
  - Series S at 1080p30: about 1.93, so the Deck has about 80% of the per-pixel budget. That fits Kingdom Come II landing in B.
  - Series S at 900p30: about 2.78, so the Deck has about 56%. Starfield lands in D.
  - Series S at 720p30: about 4.35, so the Deck has about 36%. Alan Wake 2 lands in D.
  - The Deck also has about 40–45% of the Series S's memory bandwidth and half its CPU cores. These ratios are therefore an *optimistic* upper bound.
- **Rule of thumb for DeckForge.** If the developer's Series S version renders at 900p or below internally at 30 fps, the Deck cannot reach console settings at native 800p and 30. Expect C or D, and report BLOCKED or "Low + upscaler".
- **The FLOPS math overstates the Deck in some games.** Series S runs Indiana Jones at 60 fps, which would predict a playable Deck at 30, yet it measures under 30 at the lowest settings. Ray-tracing-required and heavy UE5 or id Tech titles underperform the FLOPS ratio, plausibly due to RT throughput, bandwidth or translation overhead. This is unmeasured.
- **Switch 2 as a sibling, not a ceiling.** A Switch 2 port at about 30 handheld implies Deck Low/Medium plus upscaling at about 30, not High.
- **PS4 comparison (indirect).** Games that shipped on PS4 cluster in A and B on the Deck (see Q1). No direct Deck-vs-PS4 measurements were found.

### Gaps
- No direct Deck-vs-PS4 tests were found. The search budget ran out before targeted queries.
- No Series S data for Doom: The Dark Ages, Stalker 2, Clair Obscur, Silent Hill 2 or Crimson Desert.
- The Space Marine 2 Series S resolution is the official target, not a measured figure. A Pure Xbox headline, which I did not open, reports a player claiming the Series S information was misleading.

## Q4. Which games are CPU-bound on the Deck's 4-core Zen 2?

### Takeaway
CPU limits are documented in crowds, hordes and dense hubs: Space Marine 2 battles, Stalker 2 settlements, Dragon's Dogma 2 towns, BG3's Lower City, Starfield's cities, and Hogwarts once FSR is on. Measured CPU diagnosis on the Deck itself exists only for Hogwarts. The rest is inferred from desktop CPU limits plus Deck dips that settings do not fix.

### Cited Findings
- **Hogwarts (on Deck)** [M]: after FSR, CPU load "rose substantially and became a candidate bottleneck". GPU use fell to 60–75%. Pinning the GPU at 1400 MHz helped "because the CPU was the limiting factor". VRAM shortage causes streaming stutter. [SDHQ Deck Dive](https://steamdeckhq.com/news/hogwarts-legacys-performance-deck-dive/)
- **Space Marine 2:** the Swarm Engine battle is "particularly CPU heavy". A Ryzen 7800X3D caps at about 110 fps at 1080p. [TechSpot](https://www.techspot.com/review/2891-warhammer-space-marine-2-benchmark/) On the Deck, large battles fall to the low 20s even on Low with FSR 2. [Backdash](https://www.thebackdash.com/tech/space-marine-2-steam-deck-settings)
- **Stalker 2:** towns are "especially CPU-heavy", and lowering quality "has little effect on CPU load" there. [TechSpot](https://www.techspot.com/review/2926-stalker-2-benchmark/) The Deck still has no consistent 30 minimum after update 2.0. [TweakTown](https://www.tweaktown.com/news/113170/stalker-2-receives-massive-performance-boost-with-new-2-0-update-game-gets-upgraded-to-unreal-engine-5-5-4/index.html)
- **Dragon's Dogma 2:** towns are CPU-bottlenecked even on an RTX 4090 with a Ryzen 7700X, at about 60 fps and about 50 in Vernworth. The Deck runs below 15 at the lowest settings. [RPGSite](https://www.rpgsite.net/feature/15623-dragons-dogma-2-an-amazing-game-but-you-wont-be-running-it-on-steam-deck)
- **Baldur's Gate 3:** Larian's native Deck build targets "CPU usage" and the Lower City frame-rate spikes. [KitGuru](https://www.kitguru.net/page/65/!https:/www.kitguru.net/desktop-pc/mustafa-mahmoud/baldurs-gate-3-gets-surprise-steam-deck-optimisation-update/); [GoL](https://gamingonlinux.com/2025/09/baldurs-gate-3-gets-a-native-linux-version-to-improve-it-on-steam-deck)
- **Starfield:** even the 8-core Series S dips only in cities. [Pure Xbox](https://www.purexbox.com/news/2023/09/starfield-is-a-solid-day-one-experience-on-xbox-according-to-digital-foundry)
- **Cyberpunk:** Dogtown driving runs 19–25 fps, attributed to prop density and pop-in (streaming). [SDHQ](https://steamdeckhq.com/news/cyberpunk-2077-phantom-liberty-runs-on-steam-deck/)
- **007 First Light:** NPC-heavy areas run 40–50 against 50–70 elsewhere, even at the lowest settings. [SDHQ](https://steamdeckhq.com/news/007-first-light-steam-deck-first-impressions/)
- **Helldivers 2:** swarms and extraction dip to the low 20s. [SDHQ](https://steamdeckhq.com/game-reviews/helldivers-2/)
- **Kingdom Come II:** Kuttenberg's dense NPCs serve as the stress test, though the source does not attribute the load to the CPU. [overkill.wtf](https://overkill.wtf/kingdom-come-deliverance-2-best-settings-steam-deck)

### Inferences
- **Likely CPU-bound in hubs or hordes on the Deck**, where graphics settings will not save the minimums: Space Marine 2, Stalker 2, Dragon's Dogma 2, Baldur's Gate 3 Act 3, Starfield cities, Monster Hunter Wilds open areas, Helldivers 2 swarms, Hogwarts (after FSR), and Kingdom Come II's Kuttenberg.
  - Monster Hunter Wilds: the earlier DeckForge note lists it as CPU- and GPU-heavy, and the Deck dips below 20 near the watering hole.
  - Kingdom Come II's Kuttenberg is plausible but unverified.
- **Suggested DeckForge diagnostic.** If lowering the render scale or preset does not raise the 1% lows, label the scene CPU-bound and report it, rather than searching settings.
- **Crimson Desert's frame-time spread** (14.9 fps 1% lows against a 29.8 average) suggests streaming or CPU limits. This is unverified.

### Gaps
- No Deck CPU-versus-GPU utilization traces exist for any game except Hogwarts.
- Digital Foundry's Monster Hunter Wilds CPU analysis was not retrieved.
- No Deck fps for Baldur's Gate 3 Act 3.

---

## Per-game table

| Game | PC year | Engine¹ | Deck result (settings, resolution, upscaler, fps) | Source / date / M or C | Deck status | Class | CPU-bound? |
|---|---|---|---|---|---|---|---|
| Elden Ring | 2022 | FromSoftware | Custom High/Medium mix, 1280×800 native, no upscaler, 30 cap; dips to mid-30s uncapped | overkill.wtf (~2024) C; SDHQ review M | Verified | **A** | No |
| Armored Core VI | 2023 | FromSoftware | High preset, 800p native, 30 lock "near-flawless"; uncapped 34–50, late bosses to 28 | overkill.wtf (~Sep 2023) M/C | ? | **A** | No |
| Lies of P | 2023 | UE4 | Default (Medium/High mix) with FSR 2 Quality, ~50 avg [corrected: not native] | overkill.wtf 15 Sep 2023 M | ? | **B** [corrected] | No |
| Elden Ring Nightreign | 2025 | FromSoftware | Medium + Low shadows, 720/800p, no upscaler, mostly 30 with drops | RPGSite 28 May 2025 M | Playable at launch | **B** | ? |
| Kingdom Come II | 2025 | CryEngine | Low preset, 800p native: 35–45; Low/Med mix at 30 cap | overkill.wtf 3 Feb 2025 M; RPGSite 4 Feb 2025 M | ? | **B** | Possible (Kuttenberg) |
| Hogwarts Legacy | 2023 | UE4 | High native ~20; High + FSR 2 ~30; Low ~40 (worst-case route) | SDHQ 21 Apr 2023 M | Verified | **B** (borderline) | Yes (after FSR; VRAM) |
| Ghost of Tsushima | 2024 | Sucker Punch | High textures/LOD, Medium shadows, FSR 3 Quality, 30 cap; "40 possible" | overkill.wtf (~mid-2024) C | ? | **B** | ? |
| RE4 remake | 2023 | RE Engine | Low + FSR 2 at 720p: 40–60 fps; Med/High mix + FSR 2 Quality at 30 (claimed) | Dexerto 24 Mar 2023 M; GamePretty 29 Mar 2023 C | ? | **B** | ? |
| God of War Ragnarök | 2024 | Santa Monica | FSR 3 Balanced: 39–60 (preset unnamed); mostly Low + FSR Performance ~40 | SDHQ 19 Sep 2024 M; Backdash 20 Sep 2024 C | ? | **B/C** | ? |
| 007 First Light | 2026 | Glacier | Mostly Medium + FSR Quality: 32–40; lowest + FSR Performance: 50–70 | SDHQ 26 May 2026 M | Verified (Jul 2026) | **B/C** | Possible (NPC areas) |
| RE Requiem | 2026 | RE Engine | Lowest + FSR 3.1.5 Balanced/Quality: 45 target held, indoors >60 (OLED) | SDHQ 25 Feb 2026 M | Unsupported | **B/C** | ? |
| Pragmata | 2026 | RE Engine | Default + FSR 3: stable ~40; uncapped up to 60 | SDHQ (~Apr 2026) M | Verified | **B/C** | ? |
| Monster Hunter Wilds | 2025 | RE Engine | Lowest: high teens–30 (Jan 2026); Verified default "generally ≥30", very blurry (Aug 2026) | SDHQ 28 Jan 2026 M; PC Guide 25 Aug 2026 C | Verified (Aug 2026) | **C** (was D) | Likely |
| Helldivers 2 | 2024 | Stingray | Render scale Balanced, mostly Low: steady 30, swarms low 20s | SDHQ 15 Feb 2024 M | Playable | **C** | Likely (swarms) |
| Cyberpunk 2077 2.0 + PL | 2023 | REDengine 4 | Modified Deck preset + FSR 2.1 Balanced: mostly 30; 21–25 in burning city / Dogtown | SDHQ 23 Sep 2023 M | not confirmed | **C** | Partly (Dogtown) |
| Black Myth: Wukong | 2024 | UE5 | Medium-low 800p: 35 avg / 26 min; Low + FSR 50 + frame gen ≈45 | LevelUp 20 Aug 2024 M; Destructoid 29 Aug 2024 C | ? | **C** | ? |
| Doom: The Dark Ages | 2025 | id Tech 8 | Launch: Low 720p XeSS Q low 20s, 540p for 30; post-patch target "720p ~30" | SDHQ 11 May 2025 M; GoL 16 Oct 2025 C | Verified (Oct 2025) | **C** (was D) | No |
| Final Fantasy XVI | 2024 | Square Enix | Lowest + FSR 3 + dynamic resolution, 800p: 31 avg; without DRS: 26 | PCGamesN (demo, undated) M | Verified (Oct 2026) | **C** | ? |
| FF VII Rebirth | 2025 | UE4 | Minimum + upscaler, much-reduced resolution: ~30, dips ≤25 | Noticias3D/Wccftech 23 Jan 2025 M | Verified | **C** | ? |
| AC Shadows | 2025 | Anvil | Locked Deck preset + upscaler, 30 cap; drops in places | SDHQ 14 Mar 2025 C; RPGSite (~Dec 2025) C | Verified | **C** | ? |
| Clair Obscur: E33 | 2025 | UE5 | Locked preset + TSR: 30–45; custom TSR Low: 30–35, min 28 | RPGSite 12 Dec 2025 M | Verified (Dec 2025) | **C** | ? |
| Silent Hill 2 | 2024 | UE5 | Forest lowest: 18 (30 at 50% scale); town Med/Low at 66%: 30–35 | SDHQ 6 Oct 2024 M | ? | **C** | ? |
| Death Stranding 2 | 2026 | Decima | Portable preset + PICO Performance: 19–25 at launch → 30–35 after patch 1.2 | SDHQ 19 Mar 2026 M; games.gg 9 Jun 2026 M | Verified (per GoL) | **C** (was D) | ? |
| Onimusha: Way of the Sword | 2026 | RE Engine | Lowest: mostly >30 in combat; Low: often <30 | SDHQ 14 Jul 2026 M (benchmark tool) | ? | **C** | ? |
| Space Marine 2 | 2024 | Swarm Engine | Low + FSR 2, 15 W: 20–30, low 20s in battles | Backdash 6 Sep 2024 M | ? | **D** | **Yes** (hordes) |
| Starfield | 2023 | Creation 2 | 720p Low + FSR 2 dynamic res: 20–30 | GGRecon 6 Sep 2023 C (launch patch) | Not Verified (2023) | **D** | Yes (cities) |
| Alan Wake 2 | 2023 | Northlight | Lowest + workarounds: "regularly below 30" | SDHQ 28 Oct 2023 C | ? | **D** | No |
| Dragon's Dogma 2 | 2024 | RE Engine | Lowest: <15 fps, heavy stutter | RPGSite 20 Mar 2024 M (launch) | ? | **D** | **Yes** (towns) |
| Stalker 2 | 2024 | UE5 | Low 800p: 15 native / 23 FSR Ultra Performance; v2.0: ~30 avg with aggressive FSR, no stable minimum | GoL 20 Nov 2024 M; RPS/TweakTown 21 Aug 2026 M | Unsupported (launch) | **D** (borderline C after 2.0) | **Yes** (settlements) |
| Indiana Jones | 2024 | id Tech 7 | Lowest: 18–28 outdoors (forced RT) | SDHQ 6 Dec 2024 M | ? | **D** | ? |
| Spider-Man 2 | 2025 | Insomniac | 720p Very Low: 26 avg / 12.8 min; Low: 21.1 | TechPowerUp via Notebookcheck 5 Feb 2025 M | Verified (restored) | **D** (launch data) | ? |
| Horizon Forbidden West | 2024 | Decima | Lowest + upscaler "struggles to hold 30" (DF); tuned XeSS DRS "fairly stable 30", dips low 20s | DF via Multiplayer.it 29 Mar 2024; overkill.wtf (~May 2024) C | ? | **D** (conflict; C/D) | ? |
| Crimson Desert | 2026 | BlackSpace | Lowest + FSR Ultra Performance: 29.8 avg, 1% low 14.9 | SDHQ 13 Aug 2026 M | Verified (disputed) | **D** | Likely (lows) |
| Battlefield 6 | 2025 | Frostbite | Javelin anti-cheat blocks Linux | GoL 10 Oct 2025 | n/a | **X** | n/a |
| Marathon | 2026 | Bungie | BattlEye Linux support not enabled; "likely unplayable" | GoL 20 Jan 2026 C (pre-launch) | n/a | **X** (predicted) | n/a |
| Baldur's Gate 3 | 2023 | Divinity 4.0 | Native Deck build (Sep 2025); no fps figures found | GoL / KitGuru Sep 2025 C | Verified | **unclassified** | **Yes** (Act 3 Lower City) |
| Phantom Blade Zero | 2026 | UE5 | No Deck test found | none | ? | **unclassified** | ? |

¹ Engine names and the PS4/cross-gen platform lists are background knowledge, not sourced in this pass. Exceptions: Swarm Engine (TechSpot) and Stalker 2's Unreal Engine 5.5.4 (TweakTown).

## Count per class (35 classified games, 2 more unclassified)

| Class | Count | Share | Games |
|---|---|---|---|
| A | 2 | 6% | Elden Ring, Armored Core VI [corrected] |
| B | 6 | 17% | Nightreign, Kingdom Come II, Hogwarts (borderline), Ghost of Tsushima (claimed), RE4 (claimed), Lies of P [corrected] |
| B/C | 4 | 11% | God of War Ragnarök, 007 First Light, RE Requiem, Pragmata |
| C | 12 | 34% | Monster Hunter Wilds, Helldivers 2, Cyberpunk, Wukong, Doom: The Dark Ages, FF XVI, FF VII Rebirth, AC Shadows, Clair Obscur, Silent Hill 2, Death Stranding 2, Onimusha |
| D | 9 | 26% | Space Marine 2, Starfield, Alan Wake 2, Dragon's Dogma 2, Stalker 2, Indiana Jones, Spider-Man 2, Horizon Forbidden West, Crimson Desert |
| X | 2 | 6% | Battlefield 6, Marathon |
| Unclassified | 2 | — | Baldur's Gate 3, Phantom Blade Zero |

- **Cross-gen (PS4 version exists), 9 games:** A 2, B 5, B/C 1, D 1 [corrected].
- **Current-gen-only, 26 classified games:** A 0, B 1, B/C 3, C 12, D 8, X 2.

## Optimized settings: gains versus High

| Source / date | Game, test rig | Config | vs Ultra / Max | vs High | Visual claim |
|---|---|---|---|---|---|
| TechSpot / HUB, 8 Sep 2023 | Starfield, RTX 3070, 1440p native | "Quality" optimized | +19% city / +39% forest | ≈ +4% / +8% (my calc; High is +14% / +29% vs Ultra) | Little difference from Ultra |
| same | Starfield | "Performance" optimized | +35% / +64% | ≈ +18% / +27% (my calc) | Closer to Medium |
| TechSpot / HUB, 23 Aug 2024 | Wukong, RTX 4070S, 1440p DLSS Q | Quality optimized | ≥ +50% vs Cinematic | **−8%** (slower, denser world) | Lighting like High, better density |
| same | Wukong | Performance optimized | > +80% vs Cinematic | ≈ +10% | "High is a great balance" |
| TechSpot, 5 Oct 2021 | 9 games, RTX 3080, 4K | High preset | Ultra→High +5–47% (typically 15–25%; mean ~21%) | — | "Small" visual impact in most games |
| TechSpot, 23 Nov 2024 | Stalker 2, RTX 4090 | High / Medium | +12–18% / +21–28% vs Epic | Medium ≈ +8% over High | Not assessed |
| TechSpot, 12 Sep 2024 | Space Marine 2, 1080p | Medium | — | +5–10% | — |
| overkill.wtf, 15 Sep 2023 | Lies of P on **Deck**, 800p | Visibility High→Med; Shadows Med→Low | — | about +12 fps and +14 fps each, from ~50 (≈ +24% / +28%) | Recommended for the Deck |
| SDHQ, 21 Apr 2023 | Hogwarts on **Deck** | FSR 2 + tweaks on High; overclock + undervolt | — | ~+15% (cited); OC/UV +7% on High, +33% on Low | VRAM-limited stutter remains |
| Digital Foundry, 2023–2025 | Horizon FW, Avatar, AC Shadows, Veilguard | Optimized ≈ console presets (PS5 High or Performance) | no percentages retrieved | no percentages retrieved | Equals the console look |

**Bottom line for DeckForge.** A perceptual optimizer is worth about 5–25% over a game's High preset at the same look. The Deck's gap to native High at 30 is 0–25% only for the two class A games [corrected] and possibly two or three class B cross-gen titles. For the other roughly 30 demanding games the gap is about 1.5–4x. The honest product verdict for most current-gen-only titles is therefore "best look at about 30 fps with an upscaler", or BLOCKED.

**Worth remembering for the DeckForge project:** in a sample of 35 demanding PC games from 2022–2026 (as of Oct 2026), only 2 met "High at native 800p and 30 fps" on the Deck: Elden Ring and Armored Core VI, both cross-gen PS4 titles [corrected]. No current-gen-only title did.
