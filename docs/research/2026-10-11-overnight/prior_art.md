# Prior art: automatic game-settings optimization and per-game tuning tools (as of October 2026)

*Compiled 2026-10-11. Builds on /mnt/user-data/uploads/deckforge-research.md (compendium of 2026-09-28) and does not repeat its shader, VRS or Vulkan-layer material. "Evidence" means independent testing or primary documentation. "Marketing" means vendor claims. The web-search budget ran out before every lead was closed, so the Gaps sections list what is still unverified. GitHub's API was blocked in this session, so repo stats come from rendered pages or mirrors and are approximate.*

## 1. Automatic settings optimizers: vendors, platforms and academic work

### Takeaway
Every vendor "optimal settings" feature is a lookup table built offline: lab-tested (NVIDIA), mined from users (AMD Raptr, 2013) or a fixed bundle of driver toggles (AMD HYPR-RX). None of them measures the user's own frames and image quality and then iterates. Enthusiasts largely ignore or distrust these features. Academic work supplies the parts DeckForge needs (perceptual metrics, Pareto search, budget allocation), but I found no published system that closes the loop of measuring, searching and verifying graphics settings on a real game.

### Cited Findings
**NVIDIA GeForce Experience / NVIDIA App**
- **Method in 2012:** NVIDIA tested most top titles before release. A dedicated team set target quality levels and wrote scripts that play through demanding areas. Results fed server farms running "a complex algorithm", and the client queried those servers for each recommendation. The stated goal was the highest settings the CPU, GPU and memory allow while staying at **40 fps or higher**. This comes from a vendor demo, not independent testing. — [LaptopMag/Fox News, 2012-12-06](https://www.foxnews.com/tech/nvidia-geforce-experience-software-optimizes-your-game-settings.amp)
- **Method in 2013:** Labs in Moscow, Santa Clara and Shenzhen. Human testers decide which settings matter for gameplay and which mostly cost performance; NVIDIA's James Wang called this "a subjective call." The testers' priority list goes into a server-side algorithm that is run against many PC configurations. NVIDIA tests every GPU it ships but not every CPU. Coverage grew from about 30 games to 130. — [TechRadar, 2013-12-30](https://www.techradar.com/news/software/applications/in-the-pursuit-of-fps-how-amd-and-nvidia-are-tackling-pc-gaming-optimization-1210970/2)
- **AMD's competing approach in 2013:** AMD Gaming Evolved (Raptr) crowdsourced settings mined from users' systems and covered 65 games. NVIDIA's Wang criticized it as a privacy risk and argued that popular settings are just "the lowest common denominator of defaults." TechRadar concluded that neither approach was perfect. — [TechRadar, 2013-12-30](https://www.techradar.com/news/software/applications/in-the-pursuit-of-fps-how-amd-and-nvidia-are-tackling-pc-gaming-optimization-1210970/2)
- **NVIDIA App today:** The Graphics tab shows each game's current settings next to recommended ones, with a slider that leans toward performance or toward quality. TechPowerUp called this tab the app's main strength. Its review does not explain how the recommendations are generated (review date not clearly shown, around the v1.0 release). — [TechPowerUp NVIDIA App v1.0 review](https://techpowerup.com/review/nvidia-app-v1-0/3.html)
- **Reception (anecdotal):** In a June 2025 ComputerBase forum thread, a user reported crashes every time the NVIDIA App auto-optimized new games. Most replies said the feature "never helped" and recommended tuning by hand, using sites such as Hardware Unboxed as a guide. — [ComputerBase forum, 2025-06-08 to 06-11](https://www.computerbase.de/forum/threads/automatische-optimierung-mit-nvidia-app-bringt-probleme.2242763/latest)
- **Project G-Assist:** Announced at Computex 2024 as a tech demo that needed developer customization per game. Its optimization features were promised but not demonstrated ([Tom's Guide, 2024-06-04](https://tomsguide.com/ai/nvidia-g-assist-is-the-game-changing-ai-assistant-i-didnt-know-i-needed-heres-what-it-does)). It shipped in the NVIDIA App on 2025-03-25 and can "monitor game performance" and "adjust performance settings"; PCWorld's article contains no hands-on testing ([PCWorld, 2025-03-25](https://www.pcworld.com/article/2648083/nvidias-g-assist-ai-arrives-to-optimize-your-rtx-gaming-pc.html)). I found no independent evaluation of whether it picks better settings.

**AMD**
- **HYPR-RX (marketing page):** A one-click bundle of Anti-Lag, AFMF 2.1 (driver frame generation), RSR, Radeon Boost and FSR. "HYPR-RX Eco" bundles AFMF with Radeon Chill instead.
  - It changes in-game settings only for about 60 "HYPR-Tune optimized" titles. In those it turns on FSR Quality, or enables RSR and drops in-game resolution one step.
  - It requires RDNA 3 or newer, so it does not support the Deck's RDNA 2 GPU.
  - The headline "up to 2.3X" and the charts compare native rendering against upscaling plus frame generation. One footnote compares a 2023 configuration with a 2025 one, so these are not clean on/off tests. — [AMD HYPR-RX page](https://www.amd.com/en/products/software/adrenalin/hypr-rx.html)
- **Anti-Lag+ and Counter-Strike 2 (cautionary precedent):** Adrenalin 23.10.1 enabled Anti-Lag+ in CS2 by "detouring engine dll functions." Valve warned that "any tampering with CS code will result in a VAC ban" and told players "DO NOT ENABLE ANTI-LAG/+". — [Guru3D, 2023-10-14](https://www.guru3d.com/story/amd-in-counterstrike-2-can-result-in-vac-ban). Valve later began reversing those bans — [KitGuru (headline)](https://www.kitguru.net/page/226/!https:/www.kitguru.net/gaming/matthew-wilson/valve-begins-reversing-vac-bans-for-radeon-anti-lag-users/).

**Intel**
- **Intel Graphics Command Center (2019):** Offered "1-click game optimizations" for 30+ titles. The option silently disappeared when the hardware was below a game's minimum spec. Intel did not say how the settings were derived. The reviewer flagged data-collection consent terms with no opt-out. — [LegitReviews, 2019](https://www.legitreviews.com/?p=211069)

**Consoles and Windows handhelds**
- **PS5 Game Presets (2020):** A system-wide preference for Performance mode or Resolution mode, plus difficulty and camera settings. It applies only in games that support it, and "selected settings will be applied differently depending on the game." The platform states a preference; it does not tune anything. — [Android Central, 2020-11-11](https://www.androidcentral.com/how-setup-preferred-game-presets-ps5)
- **Xbox Handheld Compatibility Program (launched October 2025 with the ROG Xbox Ally):** Four labels: Handheld optimized ("good to go without any tweaks or settings changes"), Mostly compatible ("minor adjustments might be required"), Unsupported and Not tested. It gives no per-game recommended settings. PCWorld criticized poor discoverability, a broken filter and unclear coverage across chip variants. — [PCWorld, 2025-10-31](https://www.pcworld.com/article/2959020/xboxs-handheld-compatibility-program-needs-serious-work.html)
- **Xbox performance labels:** "Should perform well" means 30 fps or more and "should perform great" means 60 fps or more. Asus Armoury Crate offers device-wide Silent, Performance and Turbo modes. — [Notebookcheck, 2025-08-21](https://www.notebookcheck.com/Asus-ROG-Xbox-Ally-X-Microsoft-enthuellt-Performance-Modi-und-Windows-Optimierungen-a-la-Steam-Deck.1093121.0.html)

**Mobile (closed-loop, but built into the game engine)**
- **Android ADPF with MediaTek MAGT:** Automatically adjusts in-game quality and performance to hold a steady frame rate as heat builds. Games must integrate it through the Performance Hint API. Vendor-reported results for one game: frame-time jitter down about 17%, peak current down about 6%, average fps unchanged at 30. — [MediaTek blog, 2025-05-19](https://www.mediatek.com/tek-talk-blogs/mediatek-and-google-collaborate-to-usher-in-a-new-era-of-smartphone-game-performance-tuning)
- **Samsung Game Optimizing Service (GOS), the trust failure:**
  - What happened: GOS throttled CPU and GPU in more than a thousand apps but not in popular benchmarks, and at first it could not be turned off (early 2022).
  - The lawsuit: 1,882 consumers filed a class action in Korea. A court ordered compensation in February 2026 after appeal and failed mediation. — [SamMobile, 2026-03-20](https://www.sammobile.com/news/gos-controversy-ends-samsung-ordered-to-pay-galaxy-s22-users/)
  - Conflicting record: earlier coverage reported a court tossing the case — [Korea JoongAng Daily (headline)](https://www.koreajoongangdaily.com/korea/court-tosses-class-action-against-samsung-alleging-performance-throttling-in-galaxy-s22/12464724); [Android Authority (headline)](https://www.androidauthority.com/samsung-galaxy-s22-throttling-gos-court-win-3566892/). This was likely the first-instance ruling that SamMobile says was overturned.

**Academic work**
- **Piórkowski, Mantiuk & Wernikowski, *Scientific Reports* 14:27830 (2024-11-13):**
  - A CNN compares ultra-quality references with low, medium and high texture, shadow and anti-aliasing settings across 8 games, and predicts whether a human would notice the difference.
  - It matched human judgments better than SSIM, MS-SSIM and S-CIELAB, and was close to Wolski et al.'s CNN metric.
  - In a prototype renderer it suggested MSAA 4x could replace 8x with no visible loss.
  - Limits: still images only (temporal effects are future work), and it is not a general settings selector. — [Nature/Sci Rep](https://www.nature.com/articles/s41598-024-78254-0)
- **Jindal, Wolski, Myszkowski & Mantiuk, "ALSaRR" (SIGGRAPH Asia 2021, ACM TOG 40(6)):** Given a fixed rendering budget, the method picks a refresh rate and a VRS shading-rate map using a perceptual model of judder, aliasing and blur. It ships as a game-engine plugin, and users preferred it over fixed resolution and refresh rate. Code: gfxdisp/ALSaRR. — [Cambridge project page](https://www.cl.cam.ac.uk/research/rainbow/projects/alsarr/)
- **Intel CGVQM+D (2025-06-13):**
  - A full-reference video quality metric and dataset for rendering distortions, including neural supersampling, frame interpolation, VRS, path tracing and denoising.
  - Existing full-reference metrics reach at most 0.78 Pearson correlation with human ratings on these distortions. Intel says CGVQM "significantly outperforms" them but gives no number.
  - Code: github.com/IntelLabs/CGVQM. — [Intel](https://www.intel.com/content/www/us/en/developer/articles/technical/cgvqm-d-computer-graphics-video-quality.html); [arXiv 2506.11546](https://arxiv.org/pdf/2506.11546)
- **Kim & Hakak, SSRN preprint (2026-02-18, not peer-reviewed):**
  - A "Perceptual Quality-Aware Optimization Framework" that uses Pareto multi-objective optimization over graphics configurations.
  - Tested on StarCraft II, Black Myth: Wukong and Overwatch 2, using RTX 4070 Ti Super, 4080 Super and 5090 GPUs.
  - Claims up to 107% gains in CPU-bound scenes, and that optimal settings converge across hardware tiers at a given resolution. — [SSRN 6259844](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6259844)
- **Older subjective study:** "Frame Rate vs Resolution: A Subjective Evaluation of Spatiotemporal Perceived Quality Under Varying Computational Budgets" studies the same trade-off DeckForge faces. I only saw the title; the full text could not be fetched. — [ResearchGate](https://www.researchgate.net/publication/320094532_Frame_Rate_vs_Resolution_A_Subjective_Evaluation_of_Spatiotemporal_Perceived_Quality_Under_Varying_Computational_Budgets)
- **Bayesian optimization in games:** Searches found BO applied to game-testing agents ([arXiv 2508.13121](https://arxiv.org/pdf/2508.13121)) and to designing engaging games ([CU Boulder](https://experts.colorado.edu/display/pubid_139429)). Neither applies BO to graphics settings scored on frame time plus image quality.
- **A search-result false positive:** arXiv 2306.14011 ("ML-driven autotuning…") is about GPU CFD kernel scheduling, not game settings. — [arXiv](https://arxiv.org/abs/2306.14011)

### Inferences
- NVIDIA's original recipe still makes sense for DeckForge: scripted runs through demanding areas, human judgment of which settings are visible, and a fixed fps floor. On the Deck, "the lab" and "the user" are the same hardware, so every DeckForge run is effectively a lab run. This avoids the noise of AMD's 2013 crowdsourcing, which mixed heterogeneous PCs.
- Vendor tools never measure image quality on the user's own machine; quality is a human prior baked into the table. DeckForge's plan to score candidates with a perceptual metric (FLIP or SSIM in the compendium) would be new for a consumer tool. CGVQM looks better suited than FLIP or SSIM for upscaler, frame-gen and VRS artifacts, which are temporal. Its compute cost on or off the Deck is unknown.
- Two trust lessons for any automatic per-game tuner:
  - Samsung GOS: tuning must be visible, reversible and possible to switch off.
  - AMD Anti-Lag+: even a signed vendor feature gets bans if it hooks game code in an anti-cheat title. This supports DeckForge's Tier S/Tier I split.
- The Kim & Hakak claim that optimal settings converge across hardware tiers, if it holds, supports DeckForge's premise that one Deck's results transfer to every Deck. But it is an unreviewed preprint tested only on high-end NVIDIA GPUs.

### Gaps
- I found no published accuracy data for GFE or NVIDIA App recommendations (for example, how often the recommended settings actually hit the target fps), and no NVIDIA documentation of the 2024–2026 method.
- I found no independent hands-on review of G-Assist's settings optimization.
- I did not find a peer-reviewed paper that runs Bayesian or bandit search over real game settings with a perceptual-quality objective. This looks like an open niche, but the search budget ran out before I could confirm it.
- I could not find the CGVQM license or runtime cost.

## 2. The Steam Deck landscape: Valve, SteamOS, community sites, Decky plugins and distros

### Takeaway
As of October 2026, Valve does not ship or recommend per-game settings. Verified only requires a 30 fps playable default configuration, and Valve's guidance tells developers to ship their own hardware-specific defaults. In 2026 Valve started collecting opt-in framerate data from Decks and showing it to developers, and client code hints at a future crowd-based estimate of fps for a given hardware configuration. None of this records settings or image quality. The community layer splits into curated human guides (Steam Deck HQ), settings-sharing sites (ShareDeck, the DeckSettings app), compatibility reports (ProtonDB), knob plugins (SimpleDeckyTDP, PowerTools) and injector installers (Decky Framegen, decky-lsfg-vk). None of them measures and searches automatically.

### Cited Findings
**Valve: Verified criteria and developer guidance**
- **Verified criteria:** Games must ship a default configuration that gives a playable framerate: **30 fps at 800p on Deck** and **30 fps at 1080p on Steam Machine**.
  - Verified on Deck guarantees Verified on Machine.
  - Valve re-reviews automatically on events such as new Proton releases.
  - Unsupported can result from anti-cheat or other middleware.
  - Comfort, battery and performance advice lives in a separate, non-blocking recommendations document. — [Steamworks: Steam hardware compatibility review](https://partner.steamgames.com/doc/steamhardware/compat)
- **Valve's guidance to developers:**
  - "providing default graphics options for specific hardware (like Steam Deck) is fine"
  - "we do not recommend making some settings unavailable dependent on hardware"
  - "Graphics settings should be set and saved on a per-device basis"
  - Don't sync config such as resolution across devices.
  - Valve is "working on updated APIs to help game developers detect the type of hardware". — [Steamworks: recommendations](https://partner.steamgames.com/doc/steamhardware/recommendations)
- **Steam Machine Verified:** 30 fps at 1080p in the default configuration. No minimum frame-time, percentile, preset or upscaler/frame-gen requirements are documented, and Valve publishes no official recommended settings. — [Igor's Lab, 2026-07-12](https://www.igorslab.de/en/steam-machine-verified-valve-sets-30-fps-at-1080p-as-the-minimum-standard/)

**Valve: 2026 performance data**
- **February 2026:** Valve added an option to send anonymous performance data and to attach PC specs to reviews.
- **April 2026:**
  - For Verified titles, developers get a trailing-30-day average framerate chart from opted-in Deck users, plus a post-play survey asking whether players agree with the rating.
  - Valve says agreement is above 95% and plans to add variance data and extend this to Playable games.
  - A reader asked how the data accounts for different graphics settings, mods and lsfg-vk; the article does not say. — [GamingOnLinux, 2026-04-23](https://www.gamingonlinux.com/2026/04/valve-make-steps-to-improve-steam-deck-verification-giving-developers-more-performance-data/page=1/)
- **October 2026:** Valve added a framerate-distribution chart to the partner dashboard, still limited to Verified titles. The article mentions no settings, launch-option or frame-gen attribution and no recommended-settings feature. — [GamingOnLinux, 2026-10-05](https://www.gamingonlinux.com/2026/10/valve-give-game-developers-more-steam-deck-framerate-data/page=1/)
- **Possible crowd fps estimator (unconfirmed):**
  - Steam client code contains: "Select an App and a PC config to get a chart of estimated frame rates, based on the frame rates of other users."
  - A beta on SteamOS devices already logs frame rates and system configurations in the background, detached from identity.
  - There is no confirmation that it records graphics settings or presets, and it is unknown whether it will reach Windows Steam. — [TechSpot, 2026-04-04](https://www.techspot.com/news/111951-steam-could-soon-show-estimated-fps-based-crowd.html)

**SteamOS per-game controls**
- **Per-game profiles:** Introduced in May 2022. The Deck "will remember how settings have been configured for each game." — [NME, 2022-05-12](https://www.nme.com/news/steam-deck-now-has-per-game-performance-profiles-3224024)
- **Quick-access performance knobs:** framerate limit, refresh rate, allow tearing, half-rate shading (VRS), TDP limit (3–15 W), manual GPU clock, scaling filter (Linear, Nearest, Integer, FSR 1) and the per-game profile toggle. — [Steam Deck HQ "Performance Settings Encyclopedia", 2023-01-07](https://steamdeckhq.com/tips-and-guides/the-sdhq-performance-settings-encyclopedia/)
- **SteamOS 3.8 stable (2026-06-17):**
  - Fixed per-app performance settings that "would intermittently fail to apply when launching a game."
  - Fixed FPS limits not applying when a game is downscaled.
  - Kernel 6.16, the LAVD CPU scheduler via `steamosctl`, initial Steam Machine support, and Wayland by default in Desktop Mode. — [Steam Deck HQ](https://steamdeckhq.com/news/steamoss-3-8-has-been-released-with-new-kernel-graphics-driver-and-initial-steam-machine-support/)

**Developer-shipped Deck presets**
- **Example:** Assassin's Creed Mirage (patch of 2024-10-29) detects the Deck and applies Deck-specific defaults. Ubisoft gave no target fps. — [Notebookcheck, 2024-10-28](https://www.notebookcheck.net/Assassin-s-Creed-Mirage-update-adds-built-in-Steam-Deck-support-with-automatic-optimisation.910077.0.html)
- **Typical case:** Community comments say most games just use their normal defaults, with some guessing from VRAM. — [Lemmy thread, about 2023](https://lemmy.linuxuserspace.show/post/7132)

**Curated guides: Steam Deck HQ**
- **"There's no such thing as best settings":**
  - Priorities differ (battery at 30 fps, stable 60, or visuals), so SDHQ publishes multiple profiles.
  - Fixed hardware makes settings shareable across units.
  - Long games can't be fully tested at launch, and settings tested early may stop holding later in the game. — [SDHQ opinion by Noah Kupetsky, 2023-08-05](https://steamdeckhq.com/news/theres-no-such-thing-as-best-settings)
- **"The Verified system needs to change":** Verified games ran poorly at their defaults:
  - Remnant 2 dropped to 17–19 fps when aiming.
  - Chernobylite ran at 6–7 fps on its default Ultra settings.
  - Ninja Gaiden Sigma 2 defaulted to 4K. — [SDHQ, 2023-07-26](https://steamdeckhq.com/news/the-steam-deck-verified-system-needs-to-change/)

**Settings-sharing sites and apps**
- **DeckSettings app (2025):** A free iOS and Android app by a developer named Felix (also the creator of DeckFilter). It aggregates SDHQ reviews, ShareDeck reports and YouTube results, and links to ProtonDB and How Long to Beat. No license or API is mentioned. — [Steam Deck HQ](https://steamdeckhq.com/news/check-recommended-steam-deck-settings-on-iphone-easily-with-the-new-decksettings-app/)
- **Older DeckSettings Decky plugin:** Reportedly removed from the Decky store for lack of maintenance, with a new version said to be in the works. ShareDeck, SDHQ, ProtonDB and the "Show Great on Deck" browser extension were the community's usual answers to "where do people share settings and fps?" — [Lemmy thread](https://lemmy.linuxuserspace.show/post/7132)

**Decky plugins and Linux tools**
- **SimpleDeckyTDP:**
  - About 290 stars, 764 commits and 18 open issues.
  - Features: per-game TDP profiles (separate AC profiles optional), GPU controls, SMT, EPP, governor and CPU boost.
  - Supports Steam Deck, Legion Go and Go S, and ROG Ally and Ally X; tested on SteamOS, ChimeraOS, Nobara, SteamFork and Bazzite.
  - SteamOS 3.7.5's switch to `amd-pstate-epp` broke EPP and boost controls for existing installs. The documented fix deletes the settings file, which also wipes per-game profiles. — [GitHub](https://github.com/aarron-lee/SimpleDeckyTDP)
- **PowerTools (NGnius, May 2022):** CPU threads, boost, CPU frequency, GPU power and fan. Labeled "at your own risk." The developer treated auto-loading settings per game as a feature request. — [GamingOnLinux, 2022-05-03](https://www.gamingonlinux.com/2022/05/powertools-is-a-steam-deck-plugin-for-power-users)
- **Decky Framegen:**
  - About 1.3k stars and 80 open issues.
  - Many pre-releases from March to June 2026. It bundles OptiScaler 0.9.x and an experimental "RDNA2 FSR 4.1.1" path that uses a Valve `amdxcffx64.dll`.
  - v0.15.6 was a "hotfix release for the latest Steam UI layout change."
  - v0.15.2 dropped its bundled `nvngx.dll`, which "caused export-not-found failures on Proton." — [GitHub releases](https://github.com/xXJSONDeruloXx/Decky-Framegen/releases)
  - Setup uses the per-game launch option `~/fgmod/fgmod %command%` and then enabling DLSS in the game. GamingOnLinux called it "a bit of a hack though and completely unsupported" (2025-09-17). — [GamingOnLinux](https://www.gamingonlinux.com/2025/09/steam-deck-plugin-adds-amd-fsr4-support-to-improve-visuals/page=1/)
- **decky-lsfg-vk:** About 1.9k stars, 185 issues, last push around September 2026. — [GitTrend](https://gittrend.io/repo/xXJSONDeruloXx/decky-lsfg-vk)
- **lsfg-vk 2.0 (2026-09-07):**
  - New features: per-game matching by Linux binary, Windows exe or Steam App ID, and an `lsfg-vk-cli` with `benchmark`, `validate` and `healthcheck`.
  - Claims 2–3x speed on 2:1 FP16 hardware.
  - You still need to own Lossless Scaling. — [GamingOnLinux](https://gamingonlinux.com/2026/09/lossless-scalings-frame-generation-for-linux-lsfg-vk-2-0-is-out-now)
  - SDHQ found the 2.0 Decky plugin "exactly the same" on Deck apart from a ghosting fix, with input lag remaining. — [SDHQ, 2026-08-07](https://steamdeckhq.com/lossless-scaling-2-0-doesnt-improve-frame-gen/)
- **CryoUtilities:**
  - About 3.5k stars, GPL-3.0, 63 open issues.
  - Changes: swap-file resize, swappiness, HugePages, compaction proactiveness, page-lock unfairness and shmem. It offers one-click "recommended" settings, one-click revert to stock, and a VRAM tab that explains the UMA buffer size.
  - Warning: resizing swap on a full drive can trigger a SteamOS boot-loop bug.
  - The author says support beyond the Deck is "best effort" and that the project is not full-time. — [GitHub](https://github.com/CryoByte33/steam-deck-utilities)
- **Bazzite:** Its Steam Deck documentation is thin. It covers BIOS updates via `ujust enable-deck-bios-firmware-updates` and lists OLED issues, including that MangoHud may not report GPU clocks. — [Bazzite docs](https://docs.bazzite.gg/fr/Handheld_and_HTPC_edition/Handheld_Wiki/Steam_Deck/)

### Inferences
- Valve is building the measurement half of DeckForge's idea (opt-in fps telemetry from identical hardware) but not the settings half. Its data cannot say which settings produced a given fps, which is exactly the confound the GamingOnLinux commenter raised. DeckForge's niche is settings-attributed measurements. Valve could move into this later, so DeckForge should not depend on Valve staying out of it.
- The Verified bar (30 fps at defaults, no frame-time percentile) sits well below DeckForge's target of a locked 45 fps (22.2 ms). The Verified badge is therefore a weak prior for DeckForge, and frame-time distributions are the real gap.
- SteamOS's per-game profile is the safest place to apply TDP, fps cap and refresh rate (all Tier S). It was unreliable until 3.8 (June 2026), so DeckForge should check after every launch that the profile actually applied.
- The "RDNA2 FSR 4.1.1" path depends on a Valve DLL and an unofficial FSR 4 build, so it is fragile. Treat it as Tier I and experimental.

### Gaps
- **PowerTools:** current maintenance status and last commit. The GitHub fetch was refused in this session.
- **CheatDeck, Lutris, ChimeraOS:** not researched; I ran out of search budget. Lutris's community install scripts and umu-protonfixes' per-game fix database are likely useful precedents and should be checked.
- **Valve 2026 features:** I found no evidence of any Valve plan for an "optimal settings" feature or for sharing graphics settings in the Steam community. Absence is not confirmation.
- **Steam Deck HQ reviews:** their exact structure (fields such as TDP, GPU clock, projected battery and in-game settings) was not fetched directly in this session.
- **ShareDeck:** structure, owner, data fields and license not found.

## 3. What happened to similar projects: adoption, maintenance, breakage, trust, legal and anti-cheat

### Takeaway
The recurring failure modes are:
- **Breakage from platform updates:** Steam client UI changes break Decky, kernel and driver changes break power plugins, and Proton exports break DLL injectors.
- **Volunteer bus factor:** many key tools are one-person projects.
- **Recommendations that are wrong or unattributed:** these erode trust, as with the lsfg-vk plugin, GFE "optimal" settings and Verified games that run poorly.
- **Opaque automatic tuning:** Samsung GOS ended in court.

Anti-cheat risk is concentrated in tools that hook game code (Anti-Lag+, OptiScaler) and in games that block Linux. Bans on Linux are rare and usually reversed for non-cheaters.

### Cited Findings
**Breakage on updates**
- **Decky after the April 2026 Steam client update:** Decky Loader stopped working after the April 2026 stable Steam client update (around April 28). PCGames.de says similar breakage followed several earlier SteamOS updates and that Decky fixes usually came quickly. — [PCGames.de, 2026-04-29](https://www.pcgames.de/Steam-Deck-Hardware-277668/News/Neues-Update-Decky-Loader-1529736/)
- **Decky in 2022:** Decky needed fixes for newer SteamOS as early as October 2022. — [GamingOnLinux, 2022-10](https://www.gamingonlinux.com/2022/10/decky-loader-for-steam-deck-plugin-loader-gets-fixed-up-for-newer-steamos/page=1/)
- **SimpleDeckyTDP:** SteamOS 3.7.5's switch to the amd-pstate-epp driver broke its EPP and boost controls, and the fix wipes per-game profiles. — [SimpleDeckyTDP README](https://github.com/aarron-lee/SimpleDeckyTDP)
- **Decky Framegen:** It needed a hotfix for a Steam UI layout change and removed a bundled DLL that failed under Proton. — [Decky Framegen releases](https://github.com/xXJSONDeruloXx/Decky-Framegen/releases)
- **SteamOS itself:** Its per-game performance settings intermittently failed to apply until the 3.8 fix (June 2026). — [SDHQ](https://steamdeckhq.com/news/steamoss-3-8-has-been-released-with-new-kernel-graphics-driver-and-initial-steam-machine-support/)

**Maintenance and bus factor**
- **CryoUtilities:** The author says the project is not full-time and support beyond the Deck is "best effort." — [CryoUtilities README](https://github.com/CryoByte33/steam-deck-utilities)
- **DeckSettings plugin:** Delisted from the Decky store for lack of maintenance. — [Lemmy thread](https://lemmy.linuxuserspace.show/post/7132)
- **lsfg-vk leaves GitHub (2026-08-28):**
  - It moved off GitHub to self-hosting at git.lsfg-vk.dev.
  - The license went from MIT, to GPLv3 for the next major version, to **CC BY-NC-ND 4.0** (source-available, not open source).
  - The developer said over 87% of forks (excluding v1 and plain mirrors) were AI-generated, mostly abandoned after a few commits, and sometimes meant to mislead or monetize. — [GamingOnLinux](https://www.gamingonlinux.com/2026/08/lossless-scaling-frame-generation-on-linux-lsfg-vk-moves-away-from-github-changes-license-due-to-ai-slop-forks/)

**Trust failures from wrong or unattributed recommendations**
- **Decky lsfg-vk plugin launch (July 2025):**
  - It was released against the upstream author's request to wait.
  - It claimed a collaboration the author denied.
  - It recommended settings the author said give poor results (30% flow scale with no performance mode, versus his advice of 85–100% with performance mode).
  - Outcome: the labeling was fixed after discussion, but the plugin stayed unofficial. — [SDHQ, 2025-07-14](https://steamdeckhq.com/the-lossless-scaling-fg-plugin-has-released-to-controversy/)
- **lsfg-vk 2.0 plugin (August 2026):** SDHQ raised the possibility of AI-generated code, citing the lsfg-vk creator, who said some claims on GitHub were fabricated. SDHQ did not confirm it. — [SDHQ, 2026-08-07](https://steamdeckhq.com/lossless-scaling-2-0-doesnt-improve-frame-gen/)
- **Verified ratings:**
  - Steam Deck HQ documented Verified games that run poorly at their defaults — [SDHQ, 2023-07-26](https://steamdeckhq.com/news/the-steam-deck-verified-system-needs-to-change/)
  - A GamingOnLinux commenter called Verified "completely worthless", while Valve cites more than 95% agreement — [GamingOnLinux, 2026-04-23](https://www.gamingonlinux.com/2026/04/valve-make-steps-to-improve-steam-deck-verification-giving-developers-more-performance-data/page=1/)
- **Automatic optimizers in general:**
  - NVIDIA App auto-optimization blamed for crashes and widely avoided by enthusiasts (anecdotal) — [ComputerBase forum, 2025-06](https://www.computerbase.de/forum/threads/automatische-optimierung-mit-nvidia-app-bringt-probleme.2242763/latest)
  - Samsung GOS ended in court — [SamMobile, 2026-03-20](https://www.sammobile.com/news/gos-controversy-ends-samsung-ordered-to-pay-galaxy-s22-users/)

**Legal, EULA and anti-cheat**
- **AMD Anti-Lag+ in CS2 (October 2023):** VAC bans because the feature detoured game DLL functions; Valve said the bans would be reversed. — [Guru3D, 2023-10-14](https://www.guru3d.com/story/amd-in-counterstrike-2-can-result-in-vac-ban)
- **OptiScaler:** Games with Easy Anti-Cheat, BattlEye or Vanguard are unsupported, and online use "may lead to account bans." TechSpot lists v0.9.4, updated 2026-10-09, and calls it "Freeware"; I could not verify the license against the GitHub repo. — [TechSpot downloads](https://www.techspot.com/downloads/7843-optiscaler.html)
- **Linux anti-cheat guide (published 2026-05-21, updated 2026-06-23):**
  - Anti-cheat on Linux is user-mode; kernel anti-cheat "is not a thing."
  - Fortnite, Valorant and Warzone "absolutely will not work."
  - Some games allow SteamOS but block desktop distros.
  - Bans of Linux players are rare and usually reversed for non-cheaters. The guide warns that bypassing anti-cheat risks account bans.
  - In the comments, an admin corrected a reader's claim about **Denuvo locking players out after a Proton version change** to a 24-hour lockout. — [GamingOnLinux](https://www.gamingonlinux.com/guides/view/anticheat-check-which-competitive-games-actually-work-on-linux-steamos/)
- **Valve's rules:** Anti-cheat middleware can make a game Unsupported on Deck. — [Steamworks compat](https://partner.steamgames.com/doc/steamhardware/compat)

### Inferences
- **Keep the core off Decky.** DeckForge's core (measure, search, apply) should not depend on Decky or on Steam's internal UI. Use stable surfaces: per-game launch options, game config files, `steamosctl` and sysfs, and SteamOS per-game profiles. A Decky front end can be an optional, replaceable layer.
- **Version-gate and re-validate after updates.** Applied profiles should record the SteamOS, Steam client, Mesa and Proton versions and the game's build ID, and should re-validate after any of them changes.
- **Reversibility is a selling point.** CryoUtilities' one-click revert is good practice; SimpleDeckyTDP's "delete settings to fix" is the anti-pattern. This supports R10 (backup, manifest, verify).
- **Proton version is a risky knob.** The Denuvo lockout report implies switching Proton versions can trip DRM activation limits. Exclude it from automatic search for Denuvo titles, or gate it behind explicit opt-in.
- **Don't vendor lsfg-vk.** Its CC BY-NC-ND license means DeckForge can only detect and orchestrate a user-installed copy, and cannot bundle or modify it. Its license churn shows that a dependency's terms can change suddenly.
- **Expect scrutiny as an AI-built project.** DeckForge is built with AI agents and will arrive in a community primed to suspect "AI slop" (the lsfg-vk forks, the 2.0 plugin). The best defense is evidence: reproducible benchmark logs, CI links and visible human review. That matches R1 and R2.
- **Engage upstream before shipping recommendations.** The lsfg-vk plugin row came from recommending settings without upstream input. DeckForge should cite where each recommendation comes from and talk to tool authors first.

### Gaps
- I found no documented case of a ban caused specifically by MangoHud, vkBasalt, gamescope or Lossless Scaling on Linux. Not found is not proof of safety.
- I found no legal analysis of editing game config files or launch options under game EULAs. This is probably benign (Tier S), but it was not researched.
- Exact adoption numbers (installs, active users) for any Decky plugin were not found. Stars are a weak proxy.

## 4. Community data sets that could seed DeckForge

### Takeaway
ProtonDB is the only large, openly licensed data set (ODbL, monthly dumps). It records compatibility, not performance or settings: free-text tinker notes, no structured fps data, and messy fields. Steam Deck HQ, ShareDeck and DeckSettings hold the settings-level data DeckForge wants, but I found no published license or API for them, so use them only as hand-entered priors or through partnership. Valve's new framerate data is visible only to developers.

### Cited Findings
- **ProtonDB:** Announced "Report data now available under ODbL" (the page is rendered in JavaScript, so I could not extract the date or details). — [ProtonDB news](https://protondb.com/news/report-exports-odbl)
  - Dumps are published monthly in the bdefore/protondb-data GitHub repo as tarballs containing `reports_piiremoved.json`. A "result" field was dropped starting December 2019. — [protondb-data-analyzer README](https://github.com/hellsworth/protondb-data-analyzer)
  - Fields visible in early dumps: game title, rating (for example Platinum), Linux distro, GPU, CPU and Proton version. There were 29,823 reports as of early 2019.
  - Quality problems: distro strings are messy, reports aren't tied to unique users, and ratings are inconsistent (Platinum reports that required tweaks). — [GamingOnLinux, 2019-02-03](https://gamingonlinux.com/2019/02/a-quick-run-over-some-details-from-the-recent-protondb-data)
- **Valve's Deck framerate data:** An average and a distribution chart, Verified titles only, visible only to developers in the partner dashboard. Not public. — [GamingOnLinux, 2026-04-23](https://www.gamingonlinux.com/2026/04/valve-make-steps-to-improve-steam-deck-verification-giving-developers-more-performance-data/page=1/); [GamingOnLinux, 2026-10-05](https://www.gamingonlinux.com/2026/10/valve-give-game-developers-more-steam-deck-framerate-data/page=1/)
- **DeckSettings app:** Aggregates SDHQ reviews, ShareDeck reports and YouTube results. No license, open-source status or API is stated. — [SDHQ](https://steamdeckhq.com/news/check-recommended-steam-deck-settings-on-iphone-easily-with-the-new-decksettings-app/)
- **Steam Deck HQ:** Settings are produced by editorial testing, with multiple profiles per game, and are only published after the tester has played enough to cover the major areas. — [SDHQ, 2023-08-05](https://steamdeckhq.com/news/theres-no-such-thing-as-best-settings)
- **Image-quality calibration data:**
  - Intel CGVQD (rendering-distortion videos with human ratings; code at IntelLabs/CGVQM) — [Intel](https://www.intel.com/content/www/us/en/developer/articles/technical/cgvqm-d-computer-graphics-video-quality.html)
  - The Sci Rep 2024 visibility data set (8 games, 720 human difference masks) — [Sci Rep](https://www.nature.com/articles/s41598-024-78254-0)

### Inferences
- **ODbL obligations.** Under ODbL, a derivative database that DeckForge distributes (for example ProtonDB merged with its own measurements) would have to stay under ODbL, and outputs need attribution. Keeping DeckForge's own measurement database separate from ProtonDB-derived tables avoids share-alike contamination. This is from general knowledge of ODbL, not something I verified in this session; check the license text before relying on it.
- **Use ProtonDB for safety and compatibility priors,** such as which Proton version or launch options make a game work and which games need tinkering. It cannot supply performance or quality priors.
- **DeckForge's own data would be the first open, structured data set** linking settings, frame-time distribution and image-quality score on identical hardware. A clear license chosen early (for example ODbL or CC BY for the data, separate from the code license) would make it reusable by SDHQ, DeckSettings, or Valve's estimator.

### Gaps
- **DeckSettings license:** The brief says GPL. I could not verify a GPL license for any DeckSettings project. The 2025 mobile app states none, and the older Decky plugin's repo was not found. Confirm directly before relying on it.
- **ShareDeck:** schema, owner, license and API not found.
- **ProtonDB today:** current field list (for example, whether Steam Deck-specific fields or structured launch options exist), dump cadence in 2026 and exact attribution terms were not extracted.
- **CGVQD:** license not stated on Intel's page.

## 5. Gaps DeckForge could own

### Takeaway
No existing tool, from vendors, Valve or the community, closes the loop of measuring this game on this exact hardware, searching the knobs, scoring frame-time stability and image quality, applying a reversible profile, and re-checking after updates. The defensible niche is a closed-loop, evidence-first, Tier S-first optimizer whose results are tagged with versions and settings and shared as an open data set. Injection features and frame generation should stay optional and be orchestrated, not owned.

### Cited Findings
- **Every vendor optimizer uses a precomputed table.** NVIDIA uses lab tests and server recommendations; AMD's HYPR-RX is a fixed bundle that changes in-game settings for only about 60 titles and needs RDNA 3 or newer, so not the Deck; Intel's 1-click covered 30+ titles. — [TechRadar 2013](https://www.techradar.com/news/software/applications/in-the-pursuit-of-fps-how-amd-and-nvidia-are-tackling-pc-gaming-optimization-1210970/2); [AMD](https://www.amd.com/en/products/software/adrenalin/hypr-rx.html); [LegitReviews](https://www.legitreviews.com/?p=211069)
- **Valve's bar and data stop short of settings.** Verified needs only 30 fps at defaults, with no frame-time percentiles. Valve's 2026 telemetry has no settings attribution and is visible only to developers. — [Steamworks compat](https://partner.steamgames.com/doc/steamhardware/compat); [Igor's Lab](https://www.igorslab.de/en/steam-machine-verified-valve-sets-30-fps-at-1080p-as-the-minimum-standard/); [GamingOnLinux, Oct 2026](https://www.gamingonlinux.com/2026/10/valve-give-game-developers-more-steam-deck-framerate-data/page=1/)
- **Community settings go stale.** Settings are human-tested, may not hold later in a game, and there is no single "best"; users have different goals. — [SDHQ](https://steamdeckhq.com/news/theres-no-such-thing-as-best-settings)
- **Knob plugins set what you choose; they don't search.** SimpleDeckyTDP stores per-game TDP and GPU profiles, and SteamOS stores per-game profiles. — [SimpleDeckyTDP](https://github.com/aarron-lee/SimpleDeckyTDP); [SDHQ encyclopedia](https://steamdeckhq.com/tips-and-guides/the-sdhq-performance-settings-encyclopedia/)
- **Perceptual metrics exist but are unused by consumer tools.** CGVQM covers supersampling, interpolation and VRS distortions — [Intel](https://www.intel.com/content/www/us/en/developer/articles/technical/cgvqm-d-computer-graphics-video-quality.html); the visibility-prediction CNN covers textures, shadows and AA — [Sci Rep 2024](https://www.nature.com/articles/s41598-024-78254-0); budget-aware refresh-rate and VRS selection — [ALSaRR](https://www.cl.cam.ac.uk/research/rainbow/projects/alsarr/)
- **Even upstream tools are only now adding benchmark and validate commands.** lsfg-vk 2.0 added a CLI with `benchmark`, `validate` and `healthcheck`, and per-App-ID matching. — [GamingOnLinux, 2026-09-07](https://gamingonlinux.com/2026/09/lossless-scalings-frame-generation-for-linux-lsfg-vk-2-0-is-out-now)

### Inferences
Each item below is a candidate niche for DeckForge, framed as inference from the findings above:
1. **Closed-loop search on fixed hardware.** Measure frame-time percentiles (not average fps) against the 22.2 ms budget, search Tier S knobs, then verify. Nobody does this on the Deck. Present a small Pareto front (for example "45 locked, best quality" versus "45 locked, best battery"), not one "best": SDHQ's critique of "best settings" and NVIDIA App's performance/quality slider both point this way.
2. **Image quality measured, not assumed.** Score candidates with a temporal metric (CGVQM, or FLIP over short clips) against a reference, so the recommendation is backed by "quality loss X versus reference." No consumer tool does this.
3. **Settings-attributed, versioned results.** Tag every result with the game build ID, Proton, SteamOS, Mesa, LCD or OLED model, and whether frame gen was on (frame gen kept separate from native fps, per CLAUDE.md). This answers the question Valve's telemetry can't and addresses SDHQ's staleness problem. Automatic re-validation after updates is something no community source offers.
4. **Trust by design, where GOS, GFE and the lsfg-vk plugin failed:**
   - every change visible and reversible with one action;
   - an evidence bundle (MangoHud CSV plus screenshots or clips) for each recommendation;
   - no silent automatic changes;
   - upstream tools credited and their recommended settings respected.
5. **An anti-cheat- and DRM-aware search space.** Denylist anti-cheat titles for Tier I, as CLAUDE.md already plans. Also treat the Proton version as a knob that can trigger Denuvo lockouts. No existing tool exposes this kind of safety model.
6. **An open data set.** Publish opted-in results under a clear data license. This could seed SDHQ, DeckSettings or ShareDeck as partners rather than competitors, and stays useful even if Valve ships its own fps estimator.
7. **Platform risk to watch.** Valve already has the telemetry pipeline and the client hook (the estimated-fps code). If Valve adds settings attribution, DeckForge's data advantage shrinks, but the search, image-quality scoring and reversible application would still be differentiators.

### Gaps
- I did not confirm that no GitHub project already does automatic search of in-game settings on Deck or Linux. The search budget ran out before a targeted GitHub search; this is the most important open check.
- I did not check Handheld Companion or Handheld Daemon (HHD) features such as any "AutoTDP" closed-loop TDP control. These are likely the closest prior art for closed-loop TDP control on handhelds.
- I have no measurements of CGVQM or FLIP runtime cost on the Deck, or of whether scoring has to run offline on a PC.
- I did not find out whether Valve's "estimated frame rates" feature has shipped since April 2026.
