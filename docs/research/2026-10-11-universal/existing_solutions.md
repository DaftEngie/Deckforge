# Tools and services for running demanding PC games on a Steam Deck (as of 11 Oct 2026)

Method note: I used about 75 tool calls. The web-search budget for this turn ran out near the end, so a few questions were only partly checked; they are listed under Gaps. GitHub API access was blocked for the relevant repos, so I read the public pages instead. Each finding is tagged **[measured]** (someone tested it), **[claimed]** (vendor or marketing statement) or **[aggregator]** (secondary site of uneven quality).

---

## Q1. Handheld Daemon, Handheld Companion, Bazzite, ChimeraOS and SteamOS-adjacent "optimization" features

### Takeaway
None of these tools picks in-game graphics settings, measures frame times, or uses crowd data. At most they store per-game profiles of system knobs (TDP, fps cap) that the user sets by hand. The closest thing to DeckForge is a new, essentially unused project called **DeckPacer**: per-game profiles, edits to engine config files, and a planned benchmark-driven recommender.

### Cited Findings
- **Handheld Daemon (hhd)**
  - Latest version 4.1.12, released 10 Jul 2026. Features: TDP and fan-curve controls, controller emulation (gyro, back buttons), RGB, and a gamescope overlay. — [PyPI hhd](https://pypi.org/project/hhd)
  - The supported-device list covers Legion Go, ROG Ally, GPD, OneXPlayer, MSI, Ayaneo and others. **It does not list the Steam Deck.** — [PyPI hhd](https://pypi.org/project/hhd)
  - No per-game profiles, automatic game settings, crowd data or fps-based tuning are described. The GitHub repo has about 403 stars. — [GitHub hhd-dev/hhd](https://github.com/hhd-dev/hhd)
- **Handheld Companion**
  - Built for 64-bit Windows 10/11 only. Supports "Steam Deck (all models)" and the Steam Machine, but only when they run Windows. — [GitHub Valkirie/HandheldCompanion](https://github.com/Valkirie/HandheldCompanion)
  - Profiles are applied automatically when the game is detected. They include TDP (global and per profile), motion and controller settings. No crowd-sourced or shared profiles. — [GitHub](https://github.com/Valkirie/HandheldCompanion)
  - Latest release 0.32.2.0, dated "24 Jul" (year not shown; probably 2026). Recent releases are profile and TDP bug fixes. Nothing on fps limiter, upscaling or automatic settings. — [Releases](https://github.com/Valkirie/HandheldCompanion/releases)
- **Microsoft Default Game Profiles (Windows/Xbox handhelds; relevant for comparison)**
  - These are per-game TDP and FPS-limit profiles for Xbox Store PC games on the ROG Xbox Ally and Ally X.
  - They launched in Nov 2025 with 40 games, and "more than two dozen" were added on 4 May 2026.
  - An Xbox service distributes them and ASUS software applies them. **No graphics presets or resolution are included.** — [Microsoft Game Dev, 4 May 2026](https://developer.microsoft.com/en-us/games/articles/2026/05/improving-default-game-profile-support/)
- **Bazzite**
  - Latest stable release 44.20260914 (14 Sep 2026). Has a Deck edition with Steam Gaming Mode preinstalled. — [Wikipedia](https://en.wikipedia.org/wiki/Bazzite_(operating_system))
  - Its docs mention only the gamescope framerate cap and resolution scaling. Nothing is applied automatically per game. — [Bazzite docs](https://docs.bazzite.gg/Handheld_and_HTPC_edition/Steam_Gaming_Mode/)
- **ChimeraOS**
  - Latest release is 49-1, dated **27 Jul 2025**. No 2026 release was found, so the project looks dormant.
  - It has had per-game, per-power-state (docked/undocked) performance profiles in OpenGamepadUI since v44 (Sep 2023), Steam Deck TDP control since v46, and the PowerStation backend. — [ChimeraOS release notes](https://github.com/ChimeraOS/chimeraos/wiki/Release-Notes)
- **SteamOS 3.8 (stable 18 Jun 2026)**
  - Fixes per-app performance settings that sometimes failed to apply at launch.
  - Fixes FPS limits failing to apply when a game is downscaled.
  - Adds TDP control for the ROG Xbox Ally. **No automatic per-game settings.** — [GamingOnLinux, 18 Jun 2026](https://www.gamingonlinux.com/2026/06/steamos-3-8-is-out-with-initial-steam-machine-support-desktop-mode-upgrades-new-graphics-drivers/page=1/)
- **Decky Loader (update to prior research)**
  - As of 29 Apr 2026, no fix had been released for the April 2026 breakage. — [PC Games, 29 Apr 2026](https://www.pcgames.de/Steam-Deck-Hardware-277668/News/Neues-Update-Decky-Loader-1529736/)
  - I could not confirm when it was fixed.
- **DeckPacer (new find, closest to DeckForge's concept)**
  - Describes itself as a "Steam Deck FPS optimizer for Proton games, Decky Loader, and gamescope profiles." Has global and per-game profiles with fps targets (45/60/90).
  - Writes DXVK/VKD3D settings and patches engine config keys for Unreal, Unity, Source and Path of Exile 2, with backups.
  - Logs MangoHud benchmark data, but only for PoE2.
  - **Planned, not built:** "benchmark-driven profile recommendation" and an "anti-cheat database with Safe Mode fallback."
  - Repo state: 0 stars, a single commit, MIT license. — [GitHub basuev/deck-pacer](https://github.com/basuev/deck-pacer)

### Inferences
- The "handheld OS companion" category on SteamOS is done and has become a commodity, but it only covers system knobs. Nobody searches in-game settings on the user's own device.
- hhd is not a Deck tool; the Deck uses Valve's own stack. Handheld Companion is Windows-only, so it doesn't apply to a SteamOS Deck.
- DeckPacer shows that at least one other developer is going after the same idea. With 0 stars, one commit and no measurement loop yet, it is not a real competitor today. It is worth watching and possibly contributing to rather than duplicating.

### Gaps
- DeckPacer's creation and last-commit dates were not shown.
- Handheld Companion's release year was not shown.
- Bazzite's handheld-specific docs page was not reachable; it may list more tools such as preinstalled Decky.

---

## Q2. Crowd-sourced Deck settings databases

### Takeaway
Steam Deck HQ has the richest per-game settings (about 810 Deck reviews with exact settings and observed fps). But the reviews come from a single launch-era test and are re-tested only when a reader flags them. ShareDeck is thin (1–6 reports on recently updated games). ProtonDB is about compatibility, not settings and fps. **No database tracks game patches systematically.**

### Cited Findings
- **Steam Deck HQ, size:** the "Steam Deck" filter lists 810 games across 41 pages (listing updated 2 Oct 2026). — [SDHQ game reviews](https://steamdeckhq.com/game-reviews/)
- **SDHQ example, Helldivers 2 [measured]**
  - Settings: 30 fps cap, no TDP limit, native 1280×800 with in-game Render Scale "Balanced", Ultra textures, Medium shadows, most other settings Low/Medium.
  - Result: mostly 30 fps with dips into the low 20s; about 80 min battery at 15–25 W; tested on the **LCD** model ("OLED coming soon").
  - Review dated 15 Feb 2024. Page metadata shows it modified 24 Sep 2026, but the body has no patch notes. — [SDHQ Helldivers 2](https://steamdeckhq.com/game-reviews/helldivers-2/)
- **SDHQ example, Space Marine 2 [measured]**
  - Settings: Low preset with FSR 2 Performance.
  - Result: about 24 fps, dropping to about 14 fps in open areas; 21–24 W; about 2.5 h battery; Deck score 2/5.
  - Review dated 4 Sep 2024, tested at launch. Metadata modified 13 Sep 2026 with no described changes. — [SDHQ Space Marine 2](https://steamdeckhq.com/game-reviews/warhammer-40000-space-marine-2/)
- **SDHQ example, Monster Hunter Wilds**
  - The review page was **tested on an ROG Ally X and a PC, not a Deck** (24 Feb 2025). Page modified 8 May 2026.
  - Each review has a "Flag this review" box: if a patch or Proton update changes performance, SDHQ "will re-test it." — [SDHQ MH Wilds](https://steamdeckhq.com/game-reviews/monster-hunter-wilds/)
- **ShareDeck**
  - Self-description: "An unofficial site to find and share Steam Deck performance configurations." Built by one developer (Nick), funded through Ko-fi.
  - The "Recently updated games" list shows 1–6 reports per title.
  - No totals, dates, API or export are visible; report details load dynamically. — [sharedeck.games](https://sharedeck.games/)
- **DeckSettings (iOS app, Oct/Nov 2025)** combines SDHQ reviews, ShareDeck reports, YouTube search, and ProtonDB and Deck Verified badges. Made by Felix, the developer of DeckFilter. — [SDHQ, 6 Oct 2025](https://steamdeckhq.com/news/check-recommended-steam-deck-settings-on-iphone-easily-with-the-new-decksettings-app/)
- **ProtonDB**
  - Data exports are published under the ODbL license (repo has 201 stars). — [GitHub bdefore/protondb-data](https://github.com/bdefore/protondb-data)
  - Deck-specific reports have been possible since at least Oct 2024. — [SDHQ, 20 Oct 2024](https://steamdeckhq.com/news/you-can-rate-how-well-the-steam-deck-runs-on-steam-deck-on-protondb/)
- **Steam reviews (new, 13 Feb 2026):** users can attach their PC hardware specs to a review. No fps or settings are included. — [Multiplayer.it](https://multiplayer.it/notizie/ora-steam-permette-di-aggiungere-la-propria-configurazione-hardware-alle-recensioni.html)

### Inferences
- The best community data is a snapshot from launch week, from one tester, on one model (often LCD). Patches, Proton changes and OLED vs LCD differences are mostly not captured. That is exactly the staleness problem DeckForge's re-check-after-update loop would address.
- The SDHQ Helldivers 2 settings already use the pattern DeckForge would automate: Ultra textures (free on VRAM) combined with Low/Medium on the expensive effects. But it was found by hand once and never re-validated.

### Gaps
- ShareDeck's report schema (fps, TDP, GPU clock, Proton/SteamOS version, game version) could not be verified because the page renders dynamically.
- ProtonDB's report field schema could not be read (the dump folder is blocked by robots.txt).
- I could not search for other databases (for example PCGamingWiki Deck sections or newer 2026 sites) because the search budget ran out.

---

## Q3. Automated or AI settings optimizers on PC (2026)

### Takeaway
Every vendor optimizer is either an NVIDIA-only lookup (NVIDIA App / G-Assist), a Windows tool for a handful of competitive games (Razer Cortex, HP OMEN AI), or a Microsoft handheld program that sets **only TDP and fps caps** for Xbox Store games. None runs on SteamOS or AMD Deck hardware, and none measures and searches settings on the user's device.

### Cited Findings
- **NVIDIA G-Assist**
  - Asking it to "optimize graphics for [game]" applies NVIDIA's recommended settings, the same lookup as the NVIDIA App.
  - Requirements: GeForce RTX 20–50 or RTX PRO with ≥6 GB VRAM (lowered from 12 GB at Gamescom on 18 Aug 2026, which also added laptops); Windows 10/11.
  - **AMD GPUs are not supported.** Sep 2026 added mod.io plugin integration. — [PromptQuorum review, 12 Sep 2026](https://www.promptquorum.com/ko/power-local-llm/nvidia-g-assist-review)
- **NVIDIA App accuracy criticism:** only anecdotal. In one r/nvidia thread, the poster says the optimizer ties higher settings to "specs." Replies advise ignoring the app and tuning by hand. — [r/nvidia mirror](https://reddit.birdcat.cafe/r/nvidia/comments/1jtfmte/nvidia_optimizer_wrong)
  - A Sep 2026 roundup of NVIDIA App problems (performance hits, overlay bugs, memory leaks) does not mention optimal-settings accuracy. — [BGR](https://www.bgr.com/2267633/nvidia-app-major-problems-explained/)
- **Razer Cortex Booster Prime [claimed]**
  - Uses ML-chosen settings for about 7 named games (Cyberpunk 2077, Fortnite, PUBG, Valorant, Apex, LoL, CoD MW).
  - Modes: Competitive / High Quality / High Performance / Balance, with a target fps setting.
  - It **predicts** fps rather than measuring it. Windows 10/11. — [Razer](https://www.razer.com/cortex/booster-prime)
- **HP OMEN AI [claimed]**
  - Part of OMEN Gaming Hub. Supports 8 esports titles. Claims ML trained on "millions of data points" and "up to 35% FPS" gains.
  - Mainly for OMEN/Victus PCs. The page's dates are inconsistent (Jul 2025 byline, 2026 metadata). — [HP](https://www.hp.com/us-en/shop/tech-takes/omen-ai-gaming-optimization)
- **"AI picks my settings" journalism:** one May 2026 article does not name its tool and has no measurements. Low quality. — [Tech4Gamers, 18 May 2026](https://tech4gamers.com/i-let-an-ai-algorithm-decide-my-graphics-settings-for-a-week/)
- **Microsoft "Handheld Optimized" / "Handheld Compatible" labels**
  - 40 games were added on 18 Jul 2026 (18 optimized, 22 compatible).
  - "Optimized" means "best experience with minimal configuration" with "recommended performance settings." No fps or resolution target is stated. — [Windows Report](https://windowsreport.com/40-more-games-join-the-xbox-handheld-compatibility-list/)
- **Advanced Shader Delivery**
  - Ships precompiled shaders. Launched Oct 2025 on the ROG Xbox Ally and expanded to more AMD devices in May 2026; 45 titles listed as of 11 Jun 2026.
  - Claims "up to 95%" shorter launch times **[claimed]**. Delivered through the Xbox Partner Center, with no Steam mention. — [Microsoft Game Dev, 11 Jun 2026](https://developer.microsoft.com/en-us/games/articles/2026/06/expanding-advanced-shader-delivery-support/)
- **Automatic Super Resolution (Auto SR) preview, 30 Apr 2026**
  - OS-level, NPU-based upscaler for DX10+ games. Preview only, for Xbox Insiders on the ROG Xbox Ally X, docked only. Adds "a frame of latency."
  - Single-game vendor claim: Forza Horizon 5 gets ">30% FPS" over native 1440p at "similar visual quality." — [DirectX blog](https://devblogs.microsoft.com/directx/autosrpreview/)
- **Xbox Full Screen Experience:** available on all Windows 11 handhelds from 21 Nov 2025. No per-game settings. — [PCWorld](https://www.pcworld.com/article/2981446/xbox-fullscreen-experience-now-available-on-all-windows-handhelds.html)
- **DeckPacer** (see Q1) is the only open-source Deck project found that is aiming at automated per-game tuning.

### Inferences
- Confirmed: NVIDIA's tools do not work on AMD or Deck.
- Microsoft's handheld default profiles are the nearest commercial analogue, but they are curated, Xbox-Store-only and limited to TDP/fps. That validates the "per-game defaults for handhelds" need without competing on graphics-settings search.
- Auto SR is an OS-level upscaler. For DeckForge's bar it counts as upscaling, and it doesn't exist on SteamOS.

### Gaps
- I could not search further for 2025–2026 AI startups or academic auto-tuning projects (search budget exhausted). None was found in the searches that did run.
- No independent accuracy study of NVIDIA's optimal settings was found.

---

## Q4. Valve's direction

### Takeaway
Valve is pushing the job onto **developers**: shipping per-device defaults through `GetSteamHardwareDefaultConfig`, and reporting the settings and resolution used alongside fps telemetry. Valve has made no statement about automatic per-game tuning on the player side. The Steam Machine launched in June 2026, and Valve set its Verified bar at "1080p30 without changing settings" on hardware about 6× a Deck. **No named game adopting the new API was found.**

### Cited Findings
- **Steamworks SDK 1.65 (article 24 Jul 2026): updates to prior research**
  - `GetSteamHardwareDefaultConfig` loads "developer prepared default settings for specific hardware." Valve can change which configuration is selected for future devices without a new game release.
  - It replaces `IsRunningOnSteamDeck`. `IsRunningOnSteamHardware` is meant for analytics and diagnostics.
  - `SetGamePerformanceSetting` and `SetGameRenderResolution` attach the active setting and render resolution to opt-in fps sharing. — [Digital Citizen](https://www.digitalcitizen.life/steamworks-sdk-1-65-helps-developers-optimise-games-for-steam-deck-steam-machine-and-steam-frame/)
- **Source conflict on the API:**
  - Valve's public recommendations page does not name the API and says Valve is "working on updated APIs." The same page says hardware-specific defaults are "fine," advises against restricting settings by hardware, and says settings should be saved per device rather than cloud-synced. — [Steamworks docs](https://partner.steamgames.com/doc/steamhardware/recommendations)
  - A 30 Jul 2026 article says developers can now see hardware, chosen preset, average fps and Proton vs native. It names no adopters; AC Black Flag Resynced and Chronos appear only as hypothetical examples. — [Noobfeed](https://noobfeed.com/hardware/steam-hardware-developer-support)
- **Steam Machine**
  - Announced 23 Jun 2026; reservation randomization 25 Jun; purchase emails from 29 Jun; released 30 Jun.
  - Prices: 512 GB US$1,049; 2 TB US$1,349; controller bundles US$1,128 / US$1,428.
  - Regions: US, Canada, UK, EU and Australia through Steam; Japan, Taiwan and Hong Kong through Komodo. **No Mexico or LatAm.** — [GamingOnLinux](https://www.gamingonlinux.com/2026/06/steam-machine-pricing-and-launch-announced-and-yes-its-pricey/); [AUTOMATON, 23 Jun 2026](https://automaton-media.com/en/news/steam-machine-aims-to-run-compatibility-verified-games-at-a-comfortable-1080p-30fps-without-settings-tweaks-we-talk-to-the-developers/)
  - Valve says it is about 6× Steam Deck performance, with no 60 fps hard cap. FSR 4 is "coming." BattlEye and EAC need developer opt-in; kernel anti-cheat is still hard. — [AUTOMATON](https://automaton-media.com/en/news/steam-machine-aims-to-run-compatibility-verified-games-at-a-comfortable-1080p-30fps-without-settings-tweaks-we-talk-to-the-developers/)
- **Steam Machine Verified**
  - Valve quote: games "must be able to hit 1080p at 30 FPS without customers having to change their settings at all." — [AUTOMATON](https://automaton-media.com/en/news/steam-machine-aims-to-run-compatibility-verified-games-at-a-comfortable-1080p-30fps-without-settings-tweaks-we-talk-to-the-developers/)
  - The GDC 2026 report says "native 1080p" and "stable 30 fps." The AUTOMATON quote does not say "native" — minor conflict. — [tbreak, 12 Mar 2026](https://tbreak.com/steam-machine-verified-requirements-gdc-2026/)
  - Lawrence Yang: the program has "fewer constraints" than Deck Verified, and "if your title is Verified on Steam Deck, it will be Verified on Steam Machine." — [PCGamesN](https://www.pcgamesn.com/steam-machine/verified)
- **Valve statements on automatic per-game settings for players:** none found. Steam Frame docs only include "Suggesting default user settings for your game" for VR preferences. — [Steamworks hardware docs](https://partner.steamgames.com/doc/steamhardware)
- **Time from launch to Deck Verified, or to a Deck default/preset**
  - **Monster Hunter Wilds:** Verified 21 Aug 2026. At defaults it holds "30 FPS and above most of the time," with "muddy textures, lack of shadows." — [SDHQ, 21 Aug 2026](https://steamdeckhq.com/news/monster-hunter-wilds-gets-steam-deck-verified/); [Digital Citizen, 23 Aug 2026](https://www.digitalcitizen.life/monster-hunter-wilds-is-now-steam-deck-verified-but-visual-quality-remains-a-major-compromise/)
  - **Final Fantasy VII Rebirth:** PC launch 23 Jan 2025. Patch 1.001 (by 3 Feb 2025) "fixed the graphics preset to be set to 'Low' when launching for the first time on Steam Deck." Now Verified. — [GamingOnLinux](https://www.gamingonlinux.com/2025/02/final-fantasy-vii-rebirth-gets-stability-fixes-and-a-steam-deck-graphics-setting-tweak/page=1/)
  - **Death Stranding 2:** PC launch 19 Mar 2026 and Verified. Got further Deck optimizations on 23 Apr 2026. — [GamingOnLinux](https://www.gamingonlinux.com/2026/04/death-stranding-2-gets-better-performance-for-steam-deck-along-with-other-general-improvements/page=1/)
  - **The Last of Us Part I:** Naughty Dog announced "now Steam Deck Verified" on 13 Jun 2023, about 2.5 months after the PC launch. The launch date (28 Mar 2023) is from background knowledge, not re-checked. The patch added a "Very Low" preset. — [Xarkas blog](https://blog.xarkas.com/the-last-of-us-part-i-is-now-steam-deck-verified-with-v1-1-0-update/)
  - **Cyberpunk 2077:** got "an official Steam Deck setting but seems broken" in Mar 2022, about 15 months after its Dec 2020 launch. — [GamingOnLinux headline (not fetched)](https://www.gamingonlinux.com/2022/03/cyberpunk-2077-gets-an-official-steam-deck-setting-but-seems-broken/page=2)

### Inferences
- The lag runs from days (FF7 Rebirth, Death Stranding 2: publishers who planned for the Deck) to 15–18 months (Cyberpunk, MH Wilds).
- Even when a game is Verified, the developer's Deck default targets "30 fps, playable," not "High-equivalent." MH Wilds is the clearest example.
- `GetSteamHardwareDefaultConfig` could eventually make developer Deck presets universal. In practice it inherits the same developer-chosen, low-visual-quality defaults and depends on each studio adopting it.
- Valve's Steam Machine bar (1080p30 out of the box on about 6× Deck hardware) shows how demanding the owner's "High at 30 fps on a Deck" bar is.

### Gaps
- No primary Valve changelog confirming the `GetSteamHardwareDefaultConfig` name was reachable; only one secondary source names it.
- No count of Steam Machine Verified titles was found.
- Space Marine 2's current Deck rating was not found.

---

## Q5. Cloud alternatives besides GeForce NOW

### Takeaway
In Mexico, Xbox Cloud Gaming is the cheapest legitimate option (Game Pass Ultimate **MXN 339/month** since Apr 2026), but it only covers the Game Pass catalog and runs in a browser on the Deck. Boosteroid has no Mexican data center. PlayStation cloud on the Deck exists only through unofficial third-party apps that require PS Plus Premium, which Mexico historically does not sell.

### Cited Findings
- **Xbox Cloud Gaming: prices**
  - Mexico (21 Apr 2026): Ultimate **MXN 339** (down from 449), Premium 219, Essential 169. Cloud is included in all three. PC Game Pass (209) has no cloud. — [Xataka MX](https://www.xataka.com.mx/videojuegos/xbox-game-pass-ultimate-baja-precio-mexico-cambio-importante-adios-a-call-of-duty-dia-uno)
  - US: Ultimate cut from US$29.99 to **US$22.99** on 21 Apr 2026. Future Call of Duty games are no longer on day one. — [Pure Xbox](https://www.purexbox.com/news/2026/04/xbox-announces-price-reductions-for-game-pass-ultimate-and-pc-game-pass)
- **Xbox Cloud Gaming: quality and access [aggregator]**
  - Ultimate streams up to 1440p60; lower tiers are "standard."
  - Essential and Premium include streaming of "select" owned games; Steam and Epic libraries can't be linked.
  - Starter Edition with Discord Nitro gives 10 h/month. — [CloudLoadout, Jun 2026](https://cloudloadout.com/xbox-game-pass-update/)
- **Xbox Cloud Gaming on the Deck:** runs through Microsoft Edge in kiosk mode added as a Steam shortcut. The guide gives no resolution or latency data. — [NerdZap, 4 Mar 2026](https://nerdzap.com/guides/xbox-cloud-steamdeck/)
  - The DeckZap script sets up Xbox Cloud, GFN and Boosteroid the same way through Edge. — [NerdZap, 3 May 2026](https://nerdzap.com/guides/steam-deck-cloud-gaming-deckzap/)
- **Boosteroid**
  - Prices: from €7.49/month on an annual plan; "Ultra Pro" €11.22/month (promo, down from €16.89). No session limits.
  - Linux browser and desktop app (Ubuntu, Mint, Debian, Fedora). "Hundreds of titles." — [boosteroid.com](https://boosteroid.com/)
  - Data centers named in its expansion post: Brazil, Czechia, Romania, Italy and Spain, plus a planned US site. **No Mexico.** It states a 4K120 goal. — [Boosteroid blog](https://boosteroid.com/blog/2025/02/10/boosteroid-infrastructure-expansion-plans-to-meet-the-growing-demand/)
- **PlayStation**
  - Sony's official PC cloud streaming of PS5 games is not confirmed. — [Notebookcheck, 13 Jan 2026](https://www.notebookcheck.net/New-Steam-app-cloud-streams-owned-PS5-games-without-console-mimicking-PS-Portal-feature.1203591.0.html)
  - **PSStream:** third-party, US$4.99 on Steam, up to 1080p60 HDR. It "appears to access PSN accounts without the company's consent," which raises security concerns. — [Notebookcheck](https://www.notebookcheck.net/New-Steam-app-cloud-streams-owned-PS5-games-without-console-mimicking-PS-Portal-feature.1203591.0.html)
  - **Asobi:** third-party, Steam Playtest (11 Aug 2026), requires **PS Plus Premium**. Free tier 1080p30; paid tier 60 fps. — [MP1st](https://mp1st.com/news/ps-plus-cloud-gaming-is-now-possible-on-steam-deck-without-a-playstation-thanks-to-asobi)
  - Mexico's PS Plus tiers were Essential, Extra and **Deluxe** (no Premium, no cloud streaming listed) at about MXN 166/270/285. That source is from 2022. — [Xataka MX, 13 Jun 2022](https://www.xataka.com.mx/videojuegos/ps-plus-esta-disponible-mexico-precios-planes-como-contratar-nuevo-servicio-playstation)
- **GeForce NOW:** the Oct 2026 roundup lists Linux app 2.0.89 (surround-sound fix) and about 18 new games. It mentions no price or cap changes. — [GamingOnLinux, 2 Oct 2026](https://www.gamingonlinux.com/2026/10/heres-whats-coming-to-nvidia-geforce-now-during-october-2026/)

### Inferences
- In Mexico, the realistic cloud options for a Deck are GFN (owned Steam games, 100 h cap) and Xbox Cloud (Game Pass catalog only, browser). PS cloud is effectively unavailable in Mexico (Premium not sold, apps unofficial). Boosteroid would be routed to US servers, so expect higher latency.
- Cloud gets around the Deck's GPU limit and covers anti-cheat games where the catalog allows. But it adds compression artifacts and input latency, and needs a strong connection. It also covers only part of any given library.

### Gaps
- No measured latency or image-quality comparison for any of these services from Mexico City was found.
- Whether PS Plus Premium cloud is now sold in Mexico in 2026 is unknown.
- Xbox Cloud's 1440p figure comes from an aggregator, not Microsoft.

---

## Q6. What quality and fps these solutions actually deliver vs. the owner's bar ("30 fps at High-equivalent, no upscaling")

### Takeaway
For demanding 2024–2026 AAA games, the measured Deck reality is **Low/Medium settings, usually with upscaling, at about 24–30 fps with dips**. No local tool or official Deck preset found comes near "High-equivalent at 30 fps with no upscaling." Only cloud streaming delivers High-class visuals at 30+ fps, and only by not rendering on the Deck at all.

### Cited Findings
- **Monster Hunter Wilds (Verified defaults) [measured]:** "30 FPS and above most of the time," but visually "blurry, pixelated, and stripped of detail," with muddy textures and limited shadows. — [SDHQ](https://steamdeckhq.com/news/monster-hunter-wilds-gets-steam-deck-verified/); [Digital Citizen](https://www.digitalcitizen.life/monster-hunter-wilds-is-now-steam-deck-verified-but-visual-quality-remains-a-major-compromise/)
- **Space Marine 2 [measured, 2024]:** Low + FSR 2 Performance gives about 24 fps, down to about 14 fps in open areas. — [SDHQ](https://steamdeckhq.com/game-reviews/warhammer-40000-space-marine-2/)
- **Helldivers 2 [measured, 2024, LCD]:** mostly Low/Medium with Ultra textures and Render Scale Balanced (upscaled). 30 fps with dips into the low 20s. — [SDHQ](https://steamdeckhq.com/game-reviews/helldivers-2/)
- **FF7 Rebirth [anecdotal reader comment]:** about 30 fps on OLED "with a mix of settings," up to 45 in some scenes. The developer forced a Low preset on Deck first launch. — [GamingOnLinux](https://www.gamingonlinux.com/2025/02/final-fantasy-vii-rebirth-gets-stability-fixes-and-a-steam-deck-graphics-setting-tweak/page=1/)
- **Valve's own bar for hardware about 6× the Deck:** 1080p30 out of the box. — [AUTOMATON](https://automaton-media.com/en/news/steam-machine-aims-to-run-compatibility-verified-games-at-a-comfortable-1080p-30fps-without-settings-tweaks-we-talk-to-the-developers/)
- **Cloud [claimed]:** Xbox Ultimate streams up to 1440p60 ([CloudLoadout, aggregator](https://cloudloadout.com/xbox-game-pass-update/)). GFN reaches up to 90 fps handheld (prior research).

### Inferences
- For the hardest current titles (MH Wilds, Space Marine 2, Helldivers 2), "High-equivalent at 30 fps without upscaling" is probably beyond what settings can achieve on Deck hardware. Even developers' tuned Deck defaults trade large visual losses for about 30 fps.
- DeckForge's realistic standalone advantage is not reaching "High." It is the **best image quality per millisecond** at a locked 30 (or 45): for example, keeping cheap-but-visible settings like Ultra textures while cutting expensive ones, as in SDHQ's Helldivers 2 settings. It would also re-validate those settings after patches.
- The bar likely needs to be per-game or tiered (for example "High-equivalent where physically possible, otherwise the best quality at a locked 30"), or limited to games that are less demanding than these.

### Gaps
- No independent image-quality scoring (SSIM/FLIP-style) of Deck presets against High was found for any game.
- No measured Deck results for these games on the OLED model in 2026, after patches, were found.

---

## Comparison table

| Solution | What it automates | Universal? | Anti-cheat safe? | Per-game settings search on user's device? | Tracks game patches? | Cost | How close to "30 fps at High-equivalent, no upscaling" for demanding games |
|---|---|---|---|---|---|---|---|
| SteamOS 3.8 per-game QAM profiles | Applies user-set TDP/fps/refresh per game | Yes (all games) | Yes (system level) | No | No | Free | Far: no graphics changes |
| Handheld Daemon (hhd) | TDP, fans, controller; no per-game profiles described | Many non-Deck handhelds; **Deck not listed** | Yes | No | No | Free | N/A on Deck |
| Handheld Companion | Auto-applied per-game profiles (TDP, controller) | Windows only | Yes | No | No | Free | N/A on SteamOS |
| Bazzite (Deck edition) | gamescope fps cap/scaling; Gaming Mode | Yes | Yes | No | No | Free | Far |
| ChimeraOS / OpenGamepadUI | Per-game, per-power-state TDP/fps profiles | Yes; last release Jul 2025 | Yes | No | No | Free | Far |
| DeckPacer (GitHub) | Per-game fps-target profiles; DXVK/VKD3D and engine config patches; benchmark recommender *planned* | Engine adapters (UE/Unity/Source/PoE2) | Probably, since it edits config files; anti-cheat database only planned | Not yet (MangoHud logging for PoE2 only) | No | Free (MIT) | Unproven: 0 stars, 1 commit |
| Steam Deck HQ reviews | Human-tested settings, fps, battery | About 810 games | Settings are Tier S | No (one tester, often LCD or even non-Deck) | Only if a reader flags it | Free | Shows the reality: Low/Med + upscaling, about 24–30 fps |
| ShareDeck | Crowd configuration reports | Thin (1–6 reports on recent games) | Settings are Tier S | No | Not visible | Free | Not measured |
| DeckSettings (iOS) | Aggregates SDHQ, ShareDeck, YouTube | Same as sources | — | No | No | Not stated | Same as sources |
| ProtonDB | Compatibility reports, ODbL dumps | Very broad | — | No | No | Free | Compatibility only |
| Deck Verified + dev Deck presets / `GetSteamHardwareDefaultConfig` | Developer-shipped per-device defaults; opt-in telemetry | Only games that adopt it; no named adopters | Yes | No (lab-chosen by developer) | Developer can update; Valve can remap for new devices | Free | Far: e.g. MH Wilds about 30 fps, "blurry, muddy" |
| Steam Machine Verified | Certification: 1080p30 with no tweaks | Steam Machine, not Deck | — | No | — | Machine from US$1,049; not sold in Mexico | Analogous bar on about 6× the hardware |
| NVIDIA App / G-Assist | Lookup-table "optimal" settings, voice/LLM front end | NVIDIA RTX Windows only; **not AMD/Deck** | Yes (settings) | No | NVIDIA updates the table | Free (RTX ≥6 GB) | N/A on Deck |
| Razer Cortex Booster Prime | ML-chosen settings; predicts fps | About 7 named games, Windows | Yes | No (predicts) | Unknown | Free download | N/A |
| HP OMEN AI | ML system and game tuning | 8 esports titles; mainly OMEN PCs | Claims compatibility | No | Unknown | Free with OMEN Hub | N/A |
| Microsoft Default Game Profiles (Xbox Ally) | TDP + fps cap per game | About 40 + 24 Xbox Store games, Ally only | Yes | No (curated) | Unknown | Free with device | Far: no graphics changes |
| Handheld Optimized labels | Label: "minimal configuration needed" | Xbox PC games | — | No | — | Free | Label only |
| Advanced Shader Delivery | Precompiled shaders (load and stutter) | 45 titles, Xbox app, AMD devices | Yes | No | Developer-uploaded | Free | Fixes stutter, not quality |
| Auto SR | OS/NPU upscaling | DX10+ games; Ally X docked preview only | Unclear | No | — | Free (Windows) | Counts as upscaling; not on SteamOS |
| GeForce NOW Ultimate | Remote rendering | Owned games on the list (Helldivers 2 not included) | Handled server-side | No | Yes, server-side | US$19.99 / MXN 439; 100 h cap | Closest visually (High+ at 60–90 fps) but streamed |
| Xbox Cloud Gaming | Remote rendering | Game Pass catalog plus some owned games | Server-side | No | Yes | Ultimate US$22.99 / **MXN 339** (Essential MXN 169) | High-class visuals streamed, up to 1440p60 on Ultimate (aggregator figure) |
| Boosteroid | Remote rendering | "Hundreds" of titles | Server-side | No | Yes | From €7.49/month (annual) | No Mexico data center; latency unknown |
| PS Plus cloud via Asobi / PSStream | Unofficial streaming clients | PS Plus catalog | Server-side; ToS and security risk | No | Yes | PS Plus Premium (not sold in Mexico per 2022 source) + app | 1080p30 free / 60 paid; not legitimately usable in Mexico |

**Bottom line:** No existing product or project measures a game on the user's own Deck, searches its settings, scores frame-time stability and image quality, and re-checks after patches. DeckPacer is aiming at part of this but is barely started. Microsoft and Valve are converging on per-device defaults chosen by developers or curators, not measured on the device. The "High-equivalent at 30 fps, no upscaling" bar does not appear achievable for the current hardest AAA games by any local method found. Cloud is the only route to High-class visuals, and it is streamed rather than rendered on the Deck.

**Worth remembering for the DeckForge project (for the main session to save if useful):**
- DeckPacer (github.com/basuev/deck-pacer) is a nascent near-competitor.
- Steam Machine launched 30 Jun 2026 at US$1,049, with a Verified bar of 1080p30 out of the box; not sold in Mexico.
- Game Pass Ultimate in Mexico is now MXN 339.
- SDK 1.65 lets Valve remap developer hardware defaults for future devices; no named adopters yet.
- SDHQ reviews are snapshots from launch, re-tested only when a reader flags them.
