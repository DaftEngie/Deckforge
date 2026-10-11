# DeckForge market case: SteamOS handhelds and low-spec PCs (as of 11 Oct 2026)

Labels: **[M]** measured (I pulled it directly from a primary data source), **[R]** reported (from a press or analyst report), **[E]** estimate (a third party's or mine, as stated). Dates are publication or data dates.

---

## 1. Install base

### Takeaway
There are roughly 4.5 to 5.5M Steam Decks in use. That base has nearly stopped growing since Valve's May 2026 price rise. Other SteamOS devices add only a few hundred thousand units, and Bazzite adds tens of thousands. In the Steam survey, SteamOS devices are about 0.5 to 0.9% of respondents, against about 95% Windows. The low-spec Windows pool is far larger: at least 37% of respondents have 8 GB VRAM or less, and at least 44% have 16 GB RAM or less. But that pool already has free per-game optimizers from NVIDIA, HP and Microsoft.

### Cited Findings
- **Steam Deck cumulative sales.** About 3.7M by end-2024 (IDC via The Verge) and about 4M by February 2025. Valve has never published an official figure. [R, page dated Aug–Sep 2026] — [ShaneTheGamer handheld report](https://www.shanethegamer.com/research/handheld-gaming-pc-report/); [overkill.wtf, Feb 2025](https://overkill.wtf/steam-deck-sold-4-million-units)
- **Steam Deck weekly sales.**
  - Before the price rise: about 11k–18k per week.
  - After it: about 1.4k–3k per week in mid-2026, a drop of roughly 80%. The Deck fell from 4th–5th to 10th–15th on Steam's Top Sellers chart.
  - Boiling Steam derived this from chart position and calls it "back-of-the-napkin." Regional stockouts may skew it. [E, 22 Jul 2026] — [PC Gamer](https://www.pcgamer.com/hardware/handheld-gaming-pcs/steam-deck-sales-are-estimated-to-have-plummeted-by-around-80-percent-since-the-massive-price-hikes-earlier-this-year-back-of-the-napkin-maths-suggests/)
- **Steam Deck price rise and LCD model.** On 27 May 2026 the OLED 512 GB went from $549 to $789, and the OLED 1 TB from $649 to $949. The LCD model is discontinued. Valve's statement: prices "reflect the current state of component costs and other global logistical challenges." [R] — [Game Informer](https://www.gameinformer.com/2026/05/27/valve-just-raised-the-price-of-the-steam-deck-by-hundreds-of-dollars)
  - Notebookcheck says the LCD was discontinued in late 2025 and the OLED was out of stock in many countries because of memory shortages. [R, 19 Feb 2026] — [Notebookcheck](https://www.notebookcheck.net/Asus-ROG-Xbox-Ally-sales-stall-with-Steam-Deck-still-the-preferred-handheld-gaming-PC.1230155.0.html)
  - PC Gamer describes the rise as "54%". That does not match Game Informer's figures, which work out to +44% and +46%.
- **Steam survey, July 2026.** Linux 4.01%, Windows 93.67%, macOS 2.32%. Shares within Linux: SteamOS Holo 22.24%, CachyOS 14.31%, Bazzite 7.73%. [M via R, 2 Aug 2026] — [GamingOnLinux](https://www.gamingonlinux.com/2026/08/linux-back-over-4-percent-in-the-july-2026-steam-survey/)
- **Steam survey, September 2026.** Linux 3.05% (−0.85), Windows 95.03%. Within Linux: SteamOS Holo 17.37% (−3.70), Bazzite 6.97%. [M via R, 2 Oct 2026] — [GamingOnLinux](https://www.gamingonlinux.com/2026/10/steam-survey-for-september-2026-shows-a-drop-in-linux-with-simplified-chinese-rising/)
  - The same month, Simplified Chinese respondents rose 7.42 points to 31.39%. That points to a change in who answered the survey, not a real fall in Linux use. [R, 6 Oct 2026] — [Digital Citizen](https://www.digitalcitizen.life/32gb-ram-overtakes-16gb-steam-hardware-survey-september-2026/)
- **Steam Machine.** Launched 25 June 2026 in the US with a lottery for early orders.
  - Prices: $1,049 (512 GB), $1,349 (2 TB), $1,128 or $1,428 bundled with the controller.
  - Specs: 6-core Zen 4, RDNA3 GPU with **8 GB VRAM**, **16 GB DDR5**. [R, 22 Jun 2026] — [PCWorld](https://pcworld.com/article/3172143/the-steam-machine-finally-has-a-price-and-date-1049-june-25th.html)
- **Steam Machine sales.** Boiling Steam estimates about 12k–15k units per week in the launch window (8.7k–15.6k across its scenarios). It projects 600k–750k over 12 months, with a 20–30% weekly decline after launch. [E, 18 Jul 2026] — [Boiling Steam](https://boilingsteam.com/steam-machine-between-10k-and-15k-sold-per-week/)
- **Legion Go S (SteamOS).**
  - Z2 Go 16 GB/512 GB: launched at $599.99; Best Buy listed it at $989.99.
  - Z1 Extreme 32 GB/1 TB: launched at about $829.99; Best Buy listed it at $1,579.99.
  - Lenovo.com showed it as "temporarily unavailable." No sales data is public. [R, 21 Apr 2026] — [GamingOnLinux](https://www.gamingonlinux.com/2026/04/lenovo-legion-go-s-sees-a-massive-price-jump/)
- **Legion Go 2 (SteamOS).** From $1,199, due June 2026. That is $150 more than the $1,049 Windows version. [R, 6 Jan 2026] — [Android Authority](https://www.androidauthority.com/lenovo-legion-go-2-steamos-launched-3628420)
- **Steam Frame.** Pre-orders opened mid-September 2026: $1,059 (256 GB) and $1,299 (1 TB). It streams games from a PC, Deck or Steam Machine, and also runs standalone. [R, 15 Sep 2026] — [80.lv](https://80.lv/articles/steam-frame-vr-headset-price-disclosed-by-valve)
- **Bazzite users.** About 50k active users over the 2025 holiday season, up about 16k since mid-November. The figure comes from Universal Blue's "countme" graphs. [R, about Dec 2025–Jan 2026] — [Lemmy post linking ublue-os/countme](https://peachpie.theatl.social/c/linux/p/175193/bazzite-has-seen-a-massive-jolt-in-growth-over-the-holiday-season-surpassing-5); [ublue-os/countme](https://github.com/ublue-os/countme)
- **Windows handheld market.**
  - IDC shipments for Steam Deck, ROG Ally, Legion Go and MSI Claw combined: 1.62M (2022), 2.87M (2023), 1.49M (2024), about 1.93M (2025, estimate). Steam Deck was about 48% of 2024 shipments.
  - Omdia: 2.3M PC handhelds in 2025 (+32%), projected 4.7M in 2029. Omdia's 2024 base conflicts with IDC's. [R/E, Aug–Sep 2026] — [ShaneTheGamer](https://www.shanethegamer.com/research/handheld-gaming-pc-report/)
  - Prices: ROG Xbox Ally $599, Ally X $999 (October 2025); MSI Claw A8 £850; Legion Go 2 about $1,049–1,099. [R] — same source
- **ROG Xbox Ally sales.** Circana's Matt Piscatella said sales were strong in the first month and then "dropped significantly." Japanese retailers raised the Z2 Extreme model's price by more than 20%. ASUS projected up to $160M in Q4 2025 handheld sales. [R, 19 Feb 2026] — [Notebookcheck](https://www.notebookcheck.net/Asus-ROG-Xbox-Ally-sales-stall-with-Steam-Deck-still-the-preferred-handheld-gaming-PC.1230155.0.html)
- **Low-spec share, September 2026 survey.**
  - VRAM: 16 GB 27.21%, 8 GB 26.71%, 12 GB 13.06%, 6 GB 5.12%, 4 GB 5.13%.
  - Top GPUs: RTX 5070 5.86%, RTX 5060 4.20%, RTX 5060 Ti 3.87%, RTX 4060 3.72%, RTX 3060 3.54%, RTX 4060 Laptop 3.35%.
  - [M via R, 4 Oct 2026] — [Digital Citizen GPU](https://www.digitalcitizen.life/nvidia-rtx-5070-most-popular-gpu-steam-hardware-survey-september-2026/)
  - RAM: 32 GB 42.22%, 16 GB 37.82%, 8 GB 6.47%. [M via R, 6 Oct 2026] — [Digital Citizen RAM](https://www.digitalcitizen.life/32gb-ram-overtakes-16gb-steam-hardware-survey-september-2026/)

### Inferences
- **SteamOS share of Steam.** SteamOS Holo was about 0.89% of all survey respondents in July 2026 (22.24% × 4.01%) and about 0.53% in September (17.37% × 3.05%). The September drop is mostly the change in survey pool. Bazzite was about 0.21–0.31%. Together, SteamOS-style devices are about 1% of Steam.
- **Steam Deck installed base (my estimate).** About 4M in February 2025, plus about 0.7–1.2M sold before the price rise, plus about 30–60k since. That gives **about 4.5–5.2M units by October 2026**. Stockouts push toward the low end.
- **Steam Machine (my estimate).** About 120k–230k units by October 2026. It is a "low-spec" box by the brief's own definition (8 GB VRAM, 16 GB RAM).
- **Shape of the market.** New SteamOS handhelds now cost $789–$1,580. The DeckForge market is therefore mainly the existing, aging Deck base, not a growing one. Owners have more reason to get more out of the hardware they already have, but few new buyers are coming in.
- **Low-spec Windows PCs.** At least 37% of respondents have 8 GB VRAM or less, and at least 44% have 16 GB RAM or less (buckets under 4 GB are excluded). That is a far bigger pool than SteamOS. Reaching it means competing on Windows (see question 5).

### Gaps
- Valve publishes no official unit figures for Steam Deck, Steam Machine or Legion Go S SteamOS sales.
- I found no 2026 Bazzite user count. The countme badge values did not render, and the newest figure I have is about 50k from around December 2025.
- I could not turn survey shares into user counts. I found no 2026 Steam monthly active user figure.
- I found no direct survey share for "GPUs below RTX 3060 / RX 6600 class". The cards outside the top list (8.82% "Other", GTX cards, iGPUs, Steam Deck GPU entries) did not appear in the sources I fetched.
- I found no Steam Frame shipping date and no sales data.

---

## 2. DRAM, NAND and GPU prices, 2025–2026

### Takeaway
AI-server demand set off the worst memory price spike in years. DRAM contract prices rose by up to 98% in Q1 2026 and another 58–63% (forecast) in Q2. Increases are slowing but still positive in Q3. The effect reached GPUs, laptops and every SteamOS device; the Steam Deck rose about 45%. Most forecasters expect high prices well into 2027, and some say 2028. Surveys and shipment data show gamers putting off upgrades.

### Cited Findings
- **DRAM contract prices.** TrendForce: up to +98% in Q1 2026, and a forecast +58–63% in Q2 2026. [R, 2 Jun 2026, via The Register] — [AI Weekly](https://aiweekly.co/alerts/trendforce-dram-prices-to-jump-63-again-in-q2)
- **Q3 2026 forecast.** TrendForce: conventional DRAM +13–18% quarter on quarter, NAND +10–15%. The market "will remain extremely tight in the third quarter." The slowdown is partly because consumers cannot pay more. [R, primary, 3 Jul 2026] — [TrendForce](https://www.trendforce.com/presscenter/news/20260703-13134.html); [Igor's Lab](https://www.igorslab.de/en/dram-and-nand-remain-more-expensive-trendforce-sees-slowing-but-still-rising-memory-prices-q3-2026/)
- **Conflicting forecast.** Jefferies forecasts memory prices +40–50% in Q3 2026, +30–40% in Q4 2026 and about +40–45% in 2027, with possible relief only in 2028. [E, 29 Jun 2026] — [TweakTown](https://tweaktown.com/news/112389/analysts-predict-another-massive-memory-price-increase-in-q3-2026-and-another-in-q4/index.html)
- **PC prices and shipments.** IDC: OEMs preparing price rises of up to 8%. 2026 PC shipments forecast −4.9%, or −8.9% if the shortage worsens. Shortages to "continue well into 2027." [R, 22 Dec 2025] — [TechSpot](https://www.techspot.com/news/110679-memory-shortages-raise-pc-smartphone-prices-8-2026.html)
- **What PC makers say.**
  - ASUS: cumulative PC price rises of about 30% since Q4 2025, with about 5% more in Q3 2026.
  - Lenovo: another round of rises in July.
  - Acer: no meaningful declines expected; prices stay high for the rest of 2026.
  - Guru3D's conclusion: buyers face high prices "well into 2027." [R, 24 Jun 2026] — [Guru3D](https://www.guru3d.com/story/asus-expects-pc-price-increase-cumulative-increase-since-q4-2025-is/)
- **GPU prices.**
  - Board partners face supply-price increases of 10–15%.
  - RTX 50 cards with 16 GB+ rose about 15–20%; RX 9000 channel prices rose about 10–18% in Europe and China.
  - NVIDIA is shifting supply toward the **RTX 5060 8 GB** and cutting 16 GB SKUs.
  - Prices are expected to stay high "through late 2027 or even early 2028." [R, 20 Jan 2026] — [TrendForce News](https://www.trendforce.com/news/2026/01/20/news-vram-shortage-reportedly-drives-nvidias-rtx-50-price-hikes-at-taiwans-gpu-card-makers-this-month/)
- **Handheld and console prices.** Steam Deck +$240/+$300 (May 2026); Legion Go S SteamOS +65–90% at Best Buy (April 2026); Steam Machine at $1,049 (see question 1). PCWorld notes Valve's 2026 hardware launch was delayed by the market and that consoles have raised prices amid the "RAM crisis." [R] — [PCWorld](https://pcworld.com/article/3172143/the-steam-machine-finally-has-a-price-and-date-1049-june-25th.html)
- **Gamers delaying upgrades.**
  - A Tom's Hardware survey of 1,500 found 60% have no plans to build a new PC in the next two years.
  - The same article reports SSD prices +147% in Q1 2026.
  - Memory makers expect the shortage to last until at least 2028. [R, 17 May 2026] — [Tech4Gamers](https://tech4gamers.com/60-gamers-wont-build-new-pc/)
- **Shipment data.** Futuresource, Q1 2026: gaming DRAM sell-in −36% quarter on quarter and −52% year on year. Gaming SSD units −28% quarter on quarter. Consumers are "extending upgrade cycles… or delaying gaming PC builds altogether." [R, 21 Aug 2026] — [Futuresource](https://www.futuresource-consulting.com/the-source/industry-pulse/rising-prices-force-consumers-to-delay-gaming-pc-upgrades/)
- **Valve's own successor.** Pierre-Loup Griffais (Valve) says a Steam Deck 2 is probably years away. Valve won't ship "20 or 30 or even 50% more performance," and no suitable chip exists yet. [R, 14 Nov 2025] — [Tom's Hardware via Yahoo](https://tech.yahoo.com/gaming/articles/valve-waiting-create-steam-deck-100000632.html)

### Inferences
- The pressure to "get more from the hardware you have" is real and documented, and will probably last through 2027.
- Supply is tilting toward 8 GB cards and there is no Deck 2, so the installed base of constrained hardware will keep growing relative to game requirements. That strengthens the problem DeckForge solves.
- The same shock shrinks the inflow of new Deck owners. It is good for the need, but neutral to negative for growth in the SteamOS audience.

### Gaps
- I found no TrendForce Q4 2025 figure and no consumer DDR5 kit retail price series. Analysts disagree on Q3/Q4 2026 (TrendForce +13–18% vs Jefferies +40–50%).
- I found no data specific to handheld owners (for example, people keeping a Deck LCD instead of upgrading).

---

## 3. Willingness to pay and how similar tools make money

### Takeaway
There is one strong precedent: Lossless Scaling, a $6.99 tool sold on Steam, has about 2–3M+ sales and roughly $15–20M gross. It proves that people will pay a small one-time price for "make games run or feel better." The open-source tools in this space (OptiScaler, Decky plugins, Special K) live on donations, and I found no public evidence that any of them earns a meaningful income. The surrounding media business (Steam Deck HQ) runs on ads plus Patreon. I found no explicit Valve rule against selling a settings-tuning tool. Injection-style tools carry a documented ban risk.

### Cited Findings
- **Lossless Scaling reviews.** 39,460 total reviews, 35,710 positive (90.5%), "Very Positive." [M, Steam appreviews API, 11 Oct 2026] — [Steam API](https://store.steampowered.com/appreviews/993090?json=1&language=all&purchase_type=all&num_per_page=0)
- **Lossless Scaling store page.** $6.99. Released 28 Dec 2018. Developer is THS. Described as an "All-in-one gaming utility for frame generation and scaling." Frame generation (LSFG 3) is part of the base product, not paid DLC. [M, 11 Oct 2026] — [Steam store](https://store.steampowered.com/app/993090/Lossless_Scaling/)
- **Lossless Scaling sales estimates.**
  - VaporLens: about 2,725,947 sales and about $19.05M gross revenue. [E, 9 Mar 2026] — [VaporLens](https://vaporlens.app/app/993090/lossless_scaling/stats/details)
  - SteamSpy: 2M–5M owners, about 5,667 concurrent players. [E, fetched 11 Oct 2026] — [SteamSpy API](https://steamspy.com/api.php?request=appdetails&appid=993090)
- **Steam Deck HQ.** Ads through Mediavine ("extremely generous" RPM) plus direct ad sales. Patreon tiers: $1, $3 (ad-free), $6.50 and $10 (Discord role, early access). The team was expanding into HandheldHQ. No revenue or patron numbers are disclosed. [R, 4 Jan 2024] — [SDHQ](https://steamdeckhq.com/news/sdhq-update-patreon-disabling-ads-rewards/)
- **Hone (hone.gg).** A Windows game-optimizer with a freemium "Premium" subscription: premium game presets, custom game modes, no ads. Price varies by region. [M, Oct 2026] — [Hone Premium](https://hone.gg/pl/premium)
- **Ban risk precedent.** In October 2023, AMD's own Anti-Lag+ caused VAC bans in Counter-Strike 2 because it hooked engine DLLs. Valve said "DO NOT ENABLE ANTI-LAG/+" and blamed AMD. Bans were also reported in Apex Legends and CoD. [R, 16 Oct 2023] — [PCWorld](https://www.pcworld.com/article/2106874/amd-anti-lag-is-causing-player-bans-in-counter-strike-2-apex-legends.html)
- **Steam Subscriber Agreement.** It bars users from reverse engineering or modifying Valve's content "without the prior consent, in writing, of Valve." It concerns Valve's content, not third-party games' config files. [R] — [ConductAtlas excerpt](https://conductatlas.com/platform/steam/steam-subscriber-agreement/provision/CA-P-029805/prohibition-on-reverse-engineering-and-modification/)

### Inferences
- **Lossless Scaling's real income.** Valve takes 20–30%, and regional pricing and refunds reduce it further. Lifetime net to the developer is plausibly about $9–13M. Most of it likely came after frame generation was added in 2023–2025, but I did not verify the timeline.
- **Ceiling for a SteamOS-only paid tool.** Lossless Scaling sells to the about 95% of Steam on Windows. A SteamOS-only tool addresses about 1% of Steam. Even with much higher conversion among enthusiast Deck owners, a rough ceiling is in the **low hundreds of thousands of dollars lifetime gross**. That is my order-of-magnitude estimate, not data.
- **Donations.** Donation income for open-source tools of this kind is usually small and is almost never disclosed. An "open source + income" plan probably needs one of three things: a paid Steam build of the open-source code (the Lossless Scaling model, since Steam is a proven storefront for utilities), paid convenience features, or content/media income (the SDHQ model).
- **Legal risk by tier.** Editing settings files and launch options (Tier S) has no ban precedent that I found. DLL or Vulkan-layer injection (Tier I) does, even when the vendor is AMD. That supports keeping anti-cheat games to Tier S only.

### Gaps
- I could not retrieve Patreon, Ko-fi or GitHub Sponsors figures for Special K (Kaldaien), OptiScaler or Decky plugin authors. The Patreon fetch failed, and GitHub API access was not enabled in this session.
- I could not retrieve Process Lasso pricing (the bitsum.com fetch failed). I did not research Razer Cortex's model.
- I found no explicit Steamworks rule on selling software that modifies other games' settings files. The only evidence that it is allowed is that Lossless Scaling has been on sale since 2018.
- I found no legal analysis of distributing per-game settings profiles. My assumption is that settings values are factual and low risk, while bundling game files or DLLs is not. That needs a legal check.
- **Unreliable funding record:** a "Hone $30M Series B (2022, Sequoia, YC)" record appears to belong to a different company (the Hone manager-training startup), not hone.gg. I could not verify hone.gg's funding.

---

## 4. How fast official fixes arrive

### Takeaway
Official Deck fixes are slow and partial, and the bar they meet is lower than DeckForge's. Monster Hunter Wilds took about 18 months to earn Verified, and it was then running at about 30 fps with "muddy" visuals. New AAA releases in 2026 are increasingly Unsupported on the Deck while Verified on the Steam Machine. About a quarter of rated games are Verified, and most are only "Playable," which means manual tweaking. That leaves a long window where tuning adds value. The catch: for the heaviest games, no tuning gets a 2022 APU to 45 fps.

### Cited Findings
- **Verified counts (via SteamDB).** 8,939 Verified, 21,067 Playable, 6,848 Unsupported, 31,265 "SteamOS Compatible." The article has no data on ratings at launch. [M via R, 31 Aug 2026] — [GamingOnLinux](https://www.gamingonlinux.com/2026/08/steam-deck-steamos-hit-over-30-000-verified-playable-games/)
- **Earlier milestone.** 25,000 Verified or Playable in January 2026. [R] — [GamingOnLinux](https://www.gamingonlinux.com/2026/01/steam-deck-hits-25000-games-valve-have-rated-playable-or-verified)
- **Top 1,000 Steam games (Boiling Steam).**
  - 25.0% Verified, 46.0% Playable, 19.8% Unsupported, 9.2% unrated, so about 71% work.
  - Stable since January 2024. "The current process cannot keep up" with turnover in the top list.
  - Few 2024 releases had reached Verified. [M via R, 6 Aug 2024] — [Boiling Steam](https://boilingsteam.com/top-1000-steam-games-71-percent-work-on-the-steam-deck-august-2024/)
- **Monster Hunter Wilds.** Verified on 21 August 2026. At default settings it holds 30 fps "most of the time." [R] — [SDHQ](https://steamdeckhq.com/news/monster-hunter-wilds-gets-steam-deck-verified/)
  - Visuals described as "muddy," "soft and pixelated." [R, 23 Aug 2026] — [Digital Citizen](https://www.digitalcitizen.life/monster-hunter-wilds-is-now-steam-deck-verified-but-visual-quality-remains-a-major-compromise/)
- **CONTROL Resonant (Remedy).** Launched Unsupported on the Deck for "poor performance," while Verified on the Steam Machine. Remedy quietly removed Deck support from its FAQ before release. [R, 24 Sep 2026] — [GamingOnLinux](https://www.gamingonlinux.com/2026/09/control-resonant-launches-works-on-steamos-but-unsupported-on-steam-deck/)
- **2025–26 games on the Deck (Noobfeed).**
  - Run at about 30–40 fps with heavy compromises: Expedition 33, Monster Hunter Wilds, Black Myth: Wukong, and Indiana Jones (even though Indiana Jones is Verified).
  - Broken by anti-cheat: Battlefield 6 (EA Javelin), Call of Duty: Black Ops 7 (Ricochet) and Fortnite.
  - [R, 15 Mar 2026] — [Noobfeed](https://www.noobfeed.com/hardware/steam-deck-modern-games-issues)

### Inferences
- **Size of the window.** Monster Hunter Wilds launched 28 February 2025. That date is from my general knowledge; the fetched pages don't state it. The launch-to-Verified window was therefore about 18 months, and even then the target was about 30 fps.
- **DeckForge's target is above Valve's bar.** A locked 45 fps with the best visuals is above what Verified certifies. Official Verified status does not close DeckForge's niche, so the window is effectively open-ended for "Playable" and borderline titles.
- **Where the value lies.** The roughly 21k "Playable" games are the clearest pool: by definition they need manual configuration.
- **Where tuning cannot help.** Unsupported AAA titles, such as anything that needs the Steam Machine, and anti-cheat-blocked games cannot reach 45 fps on a Deck. DeckForge should say so clearly instead of promising it.

### Gaps
- I found no Valve or Boiling Steam statistic for the share of top-selling new releases that are Verified or Playable at launch versus later. The Boiling Steam top-1,000 data is from 2024.
- I found no systematic data on the median lag from launch to a Deck-specific patch.
- I could not fetch an up-to-date count of anti-cheat titles that are broken on Linux. A headline claims "640 games still broken," but the page blocked fetching ([Switchblade Gaming](https://www.switchbladegaming.com/handheld-gaming/anti-cheat-steam-deck-linux-2026/)). Treat that number as unverified.

---

## 5. Risk from platform owners and other competitors

### Takeaway
The risk is real and growing. Valve's SDK 1.65 (July 2026) adds per-hardware default settings and reporting of settings and resolution alongside opt-in frame-rate data. That is the first step toward an official version of DeckForge's core feature. Microsoft (Default Game Profiles) and HP (OMEN AI) already ship per-game automatic tuning on Windows. The mitigation is that Valve's API only covers games rebuilt on the new SDK, so the existing back catalogue stays open for at least a few years.

### Cited Findings
- **Valve, Steamworks SDK 1.65.**
  - `GetSteamHardwareDefaultConfig()` helps developers choose default video settings tuned per Steam hardware, and change them for future hardware "without recompiling."
  - `SetGamePerformanceSetting()` and `SetGameRenderResolution()` report a player's settings and resolution to Steam, included with opt-in anonymous frame-rate data.
  - The Deck-only check is removed in favour of `IsRunningOnSteamHardware()`.
  - [R, 24 Jul 2026] — [GamingOnLinux](https://gamingonlinux.com/2026/07/valves-steamworks-sdk-v1-65-brings-changes-for-steam-machine-steam-frame-and-steam-deck)
  - A reader comment notes it applies only to games built with the new SDK, which is not mandatory. [R] — same source
- **Microsoft, Default Game Profiles.**
  - Preview on the ROG Xbox Ally. Hand-crafted per-game TDP and FPS caps, 40 games at launch, battery power only.
  - Microsoft: "Spend more time playing and less time fine-tuning."
  - Auto SR (AI upscaling) is planned for the Ally X. [R, 25 Nov 2025] — [ElevenForum / Xbox Wire](https://www.elevenforum.com/t/new-rog-xbox-ally-updates-default-game-profiles-available-in-preview.42380/latest)
  - The Xbox full-screen experience is available on all Windows handhelds (headline). [R] — [PCWorld](https://www.pcworld.com/article/2981446/xbox-fullscreen-experience-now-available-on-all-windows-handhelds.html)
- **HP, OMEN AI (beta).** "Personalized settings tailored to your unique hardware and games," one click, trained on OMEN Gaming Hub performance data. 17 games available (CS2, Fortnite, Valorant, Battlefield 6, ARC Raiders and others), with CoD and GTA V coming. [M, Oct 2026] — [HP](https://www.hp.com/us-en/gaming-pc/omen-ai.html)
- **Hone.gg.** Paid "premium game presets" optimizer on Windows (see question 3). [M] — [Hone](https://hone.gg/pl/premium)

### Inferences
- **Valve has built the data loop:** per-hardware defaults plus telemetry on settings versus fps. That is exactly DeckForge's "best settings that hold the target" engine.
- **Adoption will be gradual.** Developers must adopt the new SDK and choose to tune the defaults. The roughly 30k-game back catalogue, and games that never update, remain DeckForge's territory. New AAA games that adopt it will gradually need DeckForge less.
- **Valve's defaults aim at Valve's bar.** Defaults are likely tuned for a "Verified" experience (about 30 fps), not a locked 45 fps with the best visuals. DeckForge's target is a defensible difference, if it is shown clearly.
- **On Windows, the space is crowded and free** (OEM and platform tools). DeckForge's clearest open space is SteamOS and Linux, which none of these Windows tools serve.

### Gaps
- I did not verify NVIDIA app "Optimize" or AMD Adrenalin per-game auto-tuning features for 2026.
- I found no venture-funded startup doing cross-device per-game settings optimization for SteamOS. Hone.gg's funding could not be verified, and BetterFPS appeared in search results but was not checked.
- I found nothing showing whether Valve intends to expose community or telemetry-based "recommended settings" to players directly.

---

## 6. Cloud gaming as a substitute

### Takeaway
Cloud gaming is a partial substitute that got worse in 2026. GeForce NOW added a 100-hour monthly cap in January 2026. Xbox will cap cloud play at 5–15 hours a month from November 2026, after raising Game Pass Ultimate to $29.99 in October 2025. GeForce NOW works natively on the Deck and is available in Mexico, but Mexico is served from US data centres. For heavy players and for players in LatAm, local play stays important.

### Cited Findings
- **GeForce NOW cap.**
  - From 1 January 2026: 100 hours a month on Performance and Ultimate; Founders plans exempt.
  - Up to 15 unused hours roll over. Extra blocks of 15 hours cost $2.99 (Performance) or $5.99 (Ultimate).
  - NVIDIA estimated fewer than 6% of users are affected. [R, 23 Dec 2025] — [9to5Google](https://9to5google.com/2025/12/23/nvidia-geforce-now-100-hour-limit-2026/)
- **Native GeForce NOW app for the Deck.** Up to 4K/60 when docked, and NVIDIA claims "up to 50% longer battery life" than playing natively. [R, 29 May 2025] — [NVIDIA blog](https://blogs.nvidia.com/blog/geforce-now-thursday-steam-deck-geforce-now)
- **GeForce NOW in Mexico.**
  - Official launch reported June 2024: Priority MXN 149/month, Ultimate MXN 299/month. [R] — [LevelUp](https://www.levelup.com/noticias/geforce-now-llega-oficialmente-a-mexico-juega-tus-titulos-de-pc-desde-la-nube-con-la-mayor-calidad/)
  - By November 2025, Ultimate with RTX 5080 cost MXN 439/month or MXN 4,399/year. Mexico is served "directamente desde Estados Unidos." [R, 25 Nov 2025] — [Xataka México](https://www.xataka.com.mx/videojuegos/nvidia-geforce-now-se-actualiza-ahora-podemos-contamos-rendimiento-rtx-5080-a-5k-120-fps-suscripcion-ultimate-mexico)
  - Mexico was the only LatAm country to get the Blackwell upgrade (September 2025). NVIDIA claims under 30 ms network latency for "most" users in supported regions. [R, 23 Aug 2025] — [TechRadar MX](https://global.techradar.com/es-mx/gaming/mexico-primer-pais-de-latam-en-recibir-geforce-now-con-arquitectura-blackwell)
- **Game Pass prices.** From 1 October 2025: Ultimate $29.99/month (+50%), Premium $14.99, Essential $9.99, PC Game Pass $16.49. [R] — [Pure Xbox](https://purexbox.com/news/2025/10/heres-a-breakdown-of-all-the-new-prices-for-xbox-game-pass-as-of-october-2025)
- **Xbox Cloud Gaming caps.**
  - From November 2026: Ultimate 15 hours/month, Premium 10, Essential 5. Extra hours can be bought.
  - Non-subscribers can buy cloud hours to stream games they own. Microsoft says about 4% of subscribers are affected.
  - [R, 5 Sep 2026, two outlets] — [Club386](https://www.club386.com/?p=155777); [ETV Bharat](https://www.etvbharat.com/en/technology/xbox-to-limit-free-cloud-gaming-hours-from-november-enn26090502585)

### Inferences
- **Who cloud still suits.** Casual players (under 15–100 hours a month) can treat cloud as a real substitute for heavy AAA titles on a Deck, especially ones a Deck can't run at all.
- **Who it doesn't.** Heavy players, offline or travel play, and games not on GeForce NOW or Xbox Cloud remain local, which is DeckForge's audience.
- **Pricing.** GeForce NOW Ultimate in Mexico costs about MXN 5,268/year at the monthly rate, versus a one-time tool. With caps and a 30–50% Game Pass price rise, cloud is a weaker substitute in 2026 than in 2024.
- **Mexico latency.** Because Mexico runs from US servers, latency from CDMX is probably noticeably higher than for US users. I have no measurement for this.

### Gaps
- I found no 2026 subscriber or user counts for GeForce NOW or Xbox Cloud, and no data on cloud use by handheld owners specifically.
- I found no measured GeForce NOW or Xbox Cloud latency from CDMX or other LatAm cities, and no confirmed US data-centre location for Mexican users.
- Xbox's cloud-hour pricing and which regions get it (including Mexico) were "to be shared in November."

---

## Summary table

| Factor | Evidence (dated) | Implication for DeckForge |
|---|---|---|
| Steam Deck installed base | About 4M by Feb 2025 [R]; about 4.5–5.2M by Oct 2026 [my E]; weekly sales −80% after May 2026 price rise [E] | **Neutral.** A large, aging base that needs help, but it has almost stopped growing |
| SteamOS share of Steam | SteamOS Holo about 0.5–0.9% of survey; Linux 3.05–4.01% (Jul–Sep 2026) [M] | **Weakens** income potential: about 1% of Steam |
| Other SteamOS devices | Steam Machine $1,049, est. 12–15k/wk at launch [E]; Legion Go S up to $990–1,580; Legion Go 2 SteamOS $1,199; Bazzite about 50k (Dec 2025) | **Supports, slightly.** Steam Machine (8 GB VRAM/16 GB RAM) is a new low-spec target, but volumes are small |
| Low-spec Windows PCs | 8 GB VRAM or less: at least 37%; 16 GB RAM or less: at least 44% (Sep 2026) [M] | **Supports the need, but the market is Windows**, where free OEM/platform tools already compete |
| Memory and GPU price shock | DRAM up to +98% in Q1 and +58–63% (forecast) in Q2 2026; PCs +30% cumulative; GPUs +10–20%; expected into 2027–28 [R] | **Supports.** Strong "keep your hardware longer" pressure |
| Upgrade delays | 60% of 1,500 surveyed won't build a PC within 2 years; gaming DRAM sell-in −52% year on year [R] | **Supports** |
| No Steam Deck 2 | Valve: "years away," no suitable chip [R, Nov 2025] | **Supports.** The Deck base keeps aging |
| Willingness to pay (paid tool) | Lossless Scaling $6.99, 39,460 reviews [M], about 2.7M sales and about $19M gross [E] | **Supports** paying for a cheap utility on Steam. That success is mostly a Windows audience |
| Donation model | No public figures for OptiScaler, Special K or Decky; SDHQ uses ads plus Patreon [R] | **Weakens** "open source as income" unless paired with a paid Steam build or content |
| Selling on Steam | Lossless Scaling on Steam since 2018 [M]; no explicit Valve rule found | **Neutral to supports** (precedent exists; the policy text was not found) |
| Anti-cheat and injection risk | CS2 VAC bans from AMD Anti-Lag+ (2023) [R]; BF6, BO7 and Fortnite broken on SteamOS [R] | **Weakens** the "works with anti-cheat games" claim. Settings-only (Tier S) is viable there; injection is not |
| Speed of official fixes | Monster Hunter Wilds Verified about 18 months after launch, still about 30 fps and blurry [R]; Control Resonant Unsupported on Deck (Sep 2026) [R]; about 25% Verified vs 57% Playable [M] | **Supports.** The window is long, and DeckForge's 45 fps target is above Valve's bar |
| Valve SDK 1.65 | Per-hardware default config plus settings and resolution reported with frame-rate data (Jul 2026) [R] | **Weakens over the long term** for new games; the back catalogue is unaffected |
| Microsoft, HP and others on Windows | Default Game Profiles (40 games, TDP/FPS) [R]; OMEN AI per-game settings beta [M]; Hone premium presets [M] | **Weakens** the Windows expansion. Neutral for SteamOS, which they don't serve |
| Cloud as substitute | GeForce NOW 100-hour cap (Jan 2026); Xbox Cloud 5–15 hour caps (Nov 2026); Game Pass Ultimate $29.99; Mexico served from US [R] | **Supports.** Cloud became a weaker substitute in 2026, especially for heavy users and LatAm |

**Overall:** the need is strong and well documented: aging hardware, a price shock lasting into 2027–28, slow and low-bar official fixes, and weaker cloud. The income case is weak if DeckForge stays SteamOS-only (about 1% of Steam, slow donations). It is contested if it moves to Windows (free platform and OEM tools). Valve's SDK 1.65 is the main long-term threat.

**Most viable path (my inference):** an open-source SteamOS tool focused on the "Playable" back catalogue and the 45 fps target that Valve doesn't certify, with Tier S only for anti-cheat games. Treat income as secondary: a low-priced paid Steam build or content and sponsorships, sized at hundreds of thousands of dollars lifetime at best, not millions.

*Note: one fetched page (a Lemmy mirror) contained unrelated injected text. I ignored it, and it does not affect the findings.*
