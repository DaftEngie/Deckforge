# Alternative approaches to near-console-quality, 45+ fps handheld play on a Steam Deck OLED (other than local per-game optimization). Status as of October 2026

Scope: the owner has a Steam Deck OLED, a MacBook Air (Apple Silicon) and Lossless Scaling, plays handheld, and wants to spend little. He moved to Mexico City in 2026, so cloud server distance from CDMX matters. Reference titles are Monster Hunter Wilds (MHW), Warhammer 40K: Space Marine 2 (SM2) and Helldivers 2 (HD2).

Source-quality note: several 2026 pages come from tech-insider.org. It looks like an SEO aggregator; it states it took prices from vendor pages but does not show it checked them, and some of its tables contradict each other. Its figures are flagged wherever used. Vendor pages for Boosteroid pricing and Valve's Steam Machine GamingOnLinux article could not be fetched (fetch error / permission timeout).

---

## 1. Cloud gaming to the Deck (GeForce NOW, Xbox Cloud Gaming, Boosteroid, Shadow PC)

### Takeaway
GeForce NOW (GFN) is the strongest alternative for the heaviest games. It has a native Steam Deck app that streams at the Deck's native 1280x800, at 60 fps at launch (May 2025) and up to 90 fps after the Blackwell (RTX 5080) server rollout. A paid tier costs US$9.99–19.99/month, about MXN 439/month for Ultimate in Mexico, with a 100 h/month cap since Jan 2026. It covers MHW and SM2, but **not HD2** (Sony titles are absent). Testers report roughly double the native battery life and no stutter. No source measured compression artifacts on the 800p screen or latency over Wi-Fi from Mexico City, so those are the open risks.

### Cited Findings
**GeForce NOW — tiers, prices, caps (USD unless noted)**
- Free tier: 1 h sessions, ads, longest queues, up to 1080p60 on RTX 3050-class servers, Ready-to-Play games only. Performance tier (renamed from "Priority" in Nov 2024): **$9.99/mo or $99.99/yr**, 6 h sessions, up to 1440p60 on RTX 3060-class servers (12 GB). Ultimate tier: **$19.99/mo or $199.99/yr**, 8 h sessions; supports Reflex, DLSS 3 frame generation and HDR. Day passes cost $3.99 (Performance) and $7.99 (Ultimate) — [Wikipedia: GeForce Now](https://en.wikipedia.org/wiki/GeForce_Now) (accessed Oct 2026)
- **100-hour monthly playtime cap** for all paid non-Founders members from **Jan 1, 2026**. NVIDIA said it affects about 6% of users. Extra 15 h blocks cost $2.99 (Performance) or $5.99 (Ultimate), and up to 15 unused hours roll over — [Wikipedia](https://en.wikipedia.org/wiki/GeForce_Now); [Guru3D](https://www.guru3d.com/story/geforce-now-introduces-100hour-monthly-playtime-cap-starting-2026/)
- Above the cap, the account drops to free-tier queues and 1 h sessions unless the member buys more hours — [tech-insider (aggregator), 24 Jun 2026](https://tech-insider.org/sv/shadow-pc-vs-geforce-now-vs-boosteroid-2026/)
- EU prices: Performance **€10.99/mo**, Ultimate **€21.99/mo** (June 2026), with a summer promotion of up to 35% off annual plans until early July 2026 — [tech-insider (aggregator), 24 Jun 2026](https://tech-insider.org/sv/shadow-pc-vs-geforce-now-vs-boosteroid-2026/). These match the EU price rise to €10.99 and €21.99 that took effect 1 Nov 2023 — [Genbeta, 16 Oct 2023](https://www.genbeta.com/actualidad/nvidia-sube-precios-su-suscripcion-geforce-now-para-jugar-nube-asi-quedan-todos-sus-planes)
- **Mexico:** Ultimate costs **MXN 439/month or MXN 4,399/year** (Nov 2025). Mexico is the only Latin American country served "directly from the United States" (no city named). RTX 5080 servers are available to Ultimate members for selected games — [Xataka México, 25 Nov 2025](https://www.xataka.com.mx/videojuegos/nvidia-geforce-now-se-actualiza-ahora-podemos-contamos-rendimiento-rtx-5080-a-5k-120-fps-suscripcion-ultimate-mexico). GFN launched officially in Mexico with RTX 4080 servers — [Xataka México](https://www.xataka.com.mx/videojuegos/geforce-now-llega-oficialmente-a-mexico-juega-tu-catalogo-pc-nube-rtx-4080-a-resolucion-4k-240-fps); MXN pricing was also reported — [Promodescuentos](https://www.promodescuentos.com/ofertas/nvidia-geforce-now-ahora-con-precios-en-pesos-mexicanos-965067)
- Founders (subscribed on or before 17 Mar 2021) keep $4.99/mo and are exempt from the cap — [Wikipedia](https://en.wikipedia.org/wiki/GeForce_Now)

**GeForce NOW — servers, codecs, Deck app**
- Ultimate runs on RTX 4080-class servers by default (16 vCPU, 56 GB RAM). Selected optimized games run on RTX 5080-class (Blackwell) servers, introduced Sept 2025, at up to 5K/120 or 360 fps at 1080p — [Wikipedia](https://en.wikipedia.org/wiki/GeForce_Now)
- Codecs: AV1 on newer servers (about 40% bitrate saving vs H.264); HEVC and H.264 remain for devices without AV1; adaptive bitrate. "Cinematic Quality Streaming" offers 4:4:4 chroma, 10-bit HDR, AV1 and up to 100 Mbps on Blackwell — [Wikipedia](https://en.wikipedia.org/wiki/GeForce_Now); [GamingOnLinux, 19 Aug 2025](https://www.gamingonlinux.com/2025/08/geforce-now-gets-blackwell-gpus-install-to-play-games-a-steam-deck-upgrade-and-discord-integration/page=1/)
- **Native Steam Deck app** became available about 29–31 May 2025. Nvidia claimed about 50% more play time per charge than running games natively, plus HDR10, DLSS 4 and Reflex on supported titles — [MobileSyrup, 29 May 2025](https://mobilesyrup.com/2025/05/29/nvidia-geforce-now-is-officially-available-on-steam-deck/)
- At launch the Deck app streamed **1280x800 at 60 fps** on the Deck OLED, with 90 fps "to follow" — [PCGH, 31 May 2025](https://www.pcgameshardware.de/Steam-Deck-Hardware-277668/Specials/Geforce-Now-auf-dem-Handheld-PC-1473728/). NVIDIA said the Deck app would rise from 60 to **90 fps "with the release of the Blackwell servers"** — [GamingOnLinux, 19 Aug 2025](https://www.gamingonlinux.com/2025/08/geforce-now-gets-blackwell-gpus-install-to-play-games-a-steam-deck-upgrade-and-discord-integration/page=1/); the rollout was due "next month", i.e. Sept 2025 — [The Outerhaven, 18 Aug 2025](https://www.theouterhaven.net/geforce-now-rtx-5080-4k-hdr-steam-deck/). Wikipedia now lists the Deck app at "up to 90fps in handheld mode, or up to 4K/60fps on an external display" — [Wikipedia](https://en.wikipedia.org/wiki/GeForce_Now). A July 2025 review still saw a 60 fps cap, before the update — [NoobFeed, Jul 2025](https://www.noobfeed.com/hardware/nvidia-geforce-now-on-steam-deck-gameplay)
- One reader comment says the official app isn't on Flathub and installs from NVIDIA's binary installer (a user claim, not the article's) — [GamingOnLinux comments, Aug 2025](https://www.gamingonlinux.com/2025/08/geforce-now-gets-blackwell-gpus-install-to-play-games-a-steam-deck-upgrade-and-discord-integration/page=1/)
- Install-to-Play (Gamescom 2025, Performance and Ultimate tiers): 100 GB per-session cache for Steam games whose publishers opted in. The cache clears after each session; persistent storage costs $2.99/$4.99/$7.99 a month for 200 GB/500 GB/1 TB. The total library passed 4,500 games by late 2025 — [Wikipedia](https://en.wikipedia.org/wiki/GeForce_Now); [GamingOnLinux, Aug 2025](https://www.gamingonlinux.com/2025/08/geforce-now-gets-blackwell-gpus-install-to-play-games-a-steam-deck-upgrade-and-discord-integration/page=1/)

**GeForce NOW — measured experience on Deck**
- PCGH tested Ultimate on a Deck OLED in May 2025, at 800p60 on a wired Gigabit connection:
  - Latency averaged **12–14 ms**. This is probably the app's network figure, not click-to-photon.
  - Frame times were smooth with no stutter, even in Cyberpunk 2077 with path tracing.
  - Whole-system draw was **≤7.1 W**, giving **7.5–9.5 h** of battery.
  - Source: [PCGH, 31 May 2025](https://www.pcgameshardware.de/Steam-Deck-Hardware-277668/Specials/Geforce-Now-auf-dem-Handheld-PC-1473728/)
- NoobFeed compared battery life in Rise of the Tomb Raider: native at 40–55 fps drew about 22 W (2–2.5 h); native capped at 45 fps drew about 15 W (3–3.5 h); GFN drew **7–8 W (6–8 h)**. Streaming used about 12 Mbps. Cyberpunk at RT Ultra held a steady 60 fps on GFN vs 35–40 fps native. The review cites "60 ms or more" for players far from data centers, but did not measure it — [NoobFeed, 7 Jul 2025](https://www.noobfeed.com/hardware/nvidia-geforce-now-on-steam-deck-gameplay)
- Tom's Guide measured **17 ms click-to-photon** on an RTX 5080 server (1080p/360 fps esports test, connection up to 125 Mbps); a Steam Deck OLED was one of the test devices. Nvidia's own figure is 30 ms. The reviewer reported no compression artifacts in high-bitrate modes — [Tom's Guide, updated 20 Aug 2025](https://www.tomsguide.com/gaming/nvidia-geforce-now-with-rtx-5080-is-a-console-killer-i-played-5k-at-120-fps-and-it-blew-my-mind)
- Nvidia's figure for RTX 5080 servers is sub-30 ms click-to-pixel; PC Gamer found 4K with frame generation "a little laggy" (Sept 2025) — [Wikipedia](https://en.wikipedia.org/wiki/GeForce_Now)
- NVIDIA's bandwidth guidance: 15 Mbps for 720p, 25 Mbps for 1080p, about 45 Mbps for 4K/120 — [tech-insider (aggregator), Jun 2026](https://tech-insider.org/sv/shadow-pc-vs-geforce-now-vs-boosteroid-2026/)

**Library coverage for the three reference games**
- **Monster Hunter Wilds:** on GFN — [Icy Veins headline: "Monster Hunter Wilds joins GeForce NOW"](https://www.icy-veins.com/monster-hunter-wilds/news/monster-hunter-wilds-joins-geforce-now-hunt-anywhere) (headline only; date not captured)
- **Space Marine 2:** added to GFN at launch week — [Neowin headline](https://www.neowin.net/news/nvidia-geforce-now-adds-warhammer-40000-space-marine-ii-and-more-this-week/); [GameWatcher](https://www.gamewatcher.com/warhammer-40000-space-marine-2-nvidia-geforce-now) (headlines only). Because the server runs Windows, Easy Anti-Cheat is not a client-side problem on the Deck. That is an inference; GFN's support for Destiny 2's anti-cheat launch was observed in [NoobFeed](https://www.noobfeed.com/hardware/nvidia-geforce-now-on-steam-deck-gameplay).
- **Helldivers 2:** **not on GFN.** The article attributes this to Sony's policy against cloud platforms and finds no sign it will be added. It claims HD2 is on **Boosteroid** and runs on Shadow, and that it can be streamed via Xbox Cloud with Ultimate even though it is not in Game Pass. The article leans on Reddit/YouTube for these claims (unverified) — [u4n, 23 Feb 2026, updated 11 Oct 2026](https://www.u4n.com/news/is-helldivers-2-on-ps4-game-pass-switch-geforce-now.html); also [AFK Gaming (undated)](https://afkgaming.com/gaming/general/is-helldivers-2-available-on-geforce-now)
- HD2 runs natively on the Deck via Proton; a Proton Hotfix in April 2026 fixed a breakage — [GamingOnLinux headline, Apr 2026](https://www.gamingonlinux.com/2026/04/proton-hotfix-updated-to-fix-helldivers-2-on-linux-steamos-systems/page=1/)

**Xbox Cloud Gaming**
- Left beta on **1 Oct 2025**. Streams up to 1440p for **Ultimate members only**, on certain games and devices. Premium and Essential tiers also include cloud gaming, with no 1440p and longer waits — [Android Headlines, 1 Oct 2025](https://www.androidheadlines.com/2025/10/amidst-all-the-xbox-hubbub-theres-a-small-silver-lining-cloud-gaming.html)
- Prices from Oct 2025 (existing subscribers from 4 Nov 2025):

  | Tier | USD | GBP | EUR |
  |---|---|---|---|
  | Ultimate | **$29.99** | £22.99 | €26.99 |
  | Premium | $14.99 | £10.99 | €12.99 |
  | Essential | $9.99 | £6.99 | €8.99 |

  Source: [GSMArena, ~Oct 2025](https://m.gsmarena.com/microsoft_announces_50_price_hike_for_xbox_game_pass_ultimate-news-69792.php)
- On the Deck it is browser-based. Linux/ChromeOS, including the Deck, got a higher-resolution stream in Nov 2022 — [Engadget, 4 Nov 2022](https://engadget.com/xbox-cloud-gaming-steam-deck-linux-chromeos-upgrade-183817227.html)
- "Stream your own game" (Ultimate only) launched with 50+ games; the page doesn't say whether Steam purchases count — [Xbox Wire, Nov 2024](https://news.xbox.com/en-us/2024/11/20/stream-your-own-game-xbox-cloud-gaming-beta)

**Boosteroid**
- Standard tier from **€7.49/mo** (annual plan); "Ultra Pro" at €8.97 promo (regular €14.89); 1080p60, no ray tracing; no time limit; H.264/H.265; 15 Mbps minimum, 30 Mbps recommended; browser plus Android/TV clients. The source does not mention Linux or the Deck — [tech-insider (aggregator), 24 Jun 2026](https://tech-insider.org/sv/shadow-pc-vs-geforce-now-vs-boosteroid-2026/). Boosteroid's own pricing page failed to load.

**Shadow PC (a full Windows cloud PC)**
- Neo: **€32.99/mo** (RTX 4060-class per one table). Power: €49.99/mo (€39.99 for the first 3 months; RTX A4500 ≈ RTX 3070 Ti). Neither tier has an hour cap ("fair use"). Bitrate is user-adjustable; H.264/H.265 — [tech-insider (aggregator), 24 Jun 2026](https://tech-insider.org/sv/shadow-pc-vs-geforce-now-vs-boosteroid-2026/). Note the source's internal GPU inconsistencies.
- Official Linux client for Debian/Ubuntu — [Shadow support](https://support.shadow.tech/hc/en-us/articles/32731811574673-How-to-Automatically-Install-Shadow-PC-on-Debian-or-Ubuntu-Distributions); an overview of Shadow on Linux — [Boiling Steam](https://boilingsteam.com/an-overview-of-shadow-on-linux/)

**Deck OLED network hardware**
- Wi-Fi 6E (2.4/5/6 GHz) and Bluetooth 5.3; 1280x800 at 90 Hz; 50 Wh battery — [Wikipedia: Steam Deck](https://en.wikipedia.org/wiki/Steam_Deck). The LCD model is Wi-Fi 5 (802.11ac) 2x2 — [steamdeck.com tech specs](https://www.steamdeck.com/en/tech/deck)

### Inferences
- For MHW and SM2, the games the Deck's ~1.6 TFLOPS RDNA2 cannot run at near-console quality and 45 fps, GFN Ultimate is the only option here that delivers both quality and 60–90 fps today for under $20/month. No local tweak closes a 5x+ GPU gap (compendium §1(b)).
- The 100 h cap is about 3.3 h/day. It's fine for a working adult; the risk is only binge months, where extra blocks cost $5.99 per 15 h.
- At 800p, AV1/HEVC at 12–25 Mbps should look clean in most scenes. Compression artifacts typically show in foliage, particles and dark gradients. **No source measured artifacts on the Deck's 7" screen**, so treat this as a likely-small but unquantified risk.
- **Latency from CDMX is the decisive unknown.** Mexico is served from US data centers (city unnamed). If the nearest is Dallas or similar, the network round trip could be 30–50+ ms before encode and decode. That is playable for MHW/SM2 PvE, worse for parries and dodges. Fede should run GFN's built-in network test from home before paying for more than a day pass ($7.99 Ultimate).
- Wi-Fi 6E helps only with a 6E router. On 5 GHz, a clean channel and short distance to the router matter more than the band.
- Xbox Cloud costs 50% more than GFN Ultimate ($29.99 vs $19.99) and is tied to the Game Pass catalog, not his Steam library. That is poor value unless he wants Game Pass content anyway.
- Shadow (€33+/mo) is the only option that runs anything, HD2 included, but costs 1.5–2x GFN Ultimate.
- Boosteroid is the cheapest. Its 1080p60 limit doesn't matter at 800p, and it reportedly has HD2 (unverified).

### Gaps
- No measured click-to-photon latency for GFN, Xbox Cloud or Boosteroid **on a Steam Deck over Wi-Fi**, and none **from Mexico City**. Tom's Guide (17 ms) and PCGH (12–14 ms) were wired, in Europe or the US.
- No source analyzed compression artifacts on the Deck's 800p panel.
- The Deck app codec (AV1 vs HEVC) is not documented in any fetched source. Whether the 90 fps Deck mode needs Ultimate or only selected RTX 5080 titles is also unconfirmed.
- No official Boosteroid or Shadow pricing page was retrieved, so prices rely on an aggregator. No USD or MXN prices for these two.
- Whether MHW or SM2 are on Xbox Cloud is unknown. HD2's availability on Boosteroid and Xbox Cloud is unverified.
- No direct 2026 Digital Foundry test of GFN on Deck was found.

---

## 2. Local streaming (Steam Remote Play / Steam Link, Moonlight + Sunshine/Apollo, Steam Machine as host; Mac as host)

### Takeaway
Local streaming gives the best image and latency of any streaming option: about 20 ms in older wired tests, no data caps, and any game, anti-cheat included. But **Fede owns no gaming PC**, so it only makes sense if he buys a host. The new Steam Machine costs **$1,049+** (June 2026, reservation queue, about 6x the Deck's GPU). A used-parts PC is cheaper, but GPU and RAM prices are inflated in 2026. A MacBook Air is not a realistic host for these Windows/anti-cheat games.

### Cited Findings
- **Latency, 2021 TechSpot test:**
  - Setup: RTX 3080 host on Ethernet, 1080p, HEVC, 50 Mbps.
  - Steam Remote Play ≈ **20 ms**, Moonlight ≈ **18–20 ms**; "Balanced/Beautiful" quality modes add 5–10 ms.
  - Remote Play looked better in fast motion. Remote Play was limited to 60 Hz; Moonlight supported 120 Hz.
  - Source: [TechSpot, 26 Feb 2021](https://www.techspot.com/article/2198-steam-remote-play-vs-moonlight/)
- A 2026 guide recommends Ethernet for the host; "decent 5GHz Wi-Fi can also work well" and 2.4 GHz struggles. It says Remote Play is easier but "generally has higher latency" than Sunshine/Moonlight, gives no ms figures, and notes Sunshine has had end-to-end encryption since v0.22 — [NerdZap, 4 Mar 2026, updated 8 Jul 2026](https://nerdzap.com/guides/sunshine-moonlight-guide/)
- **Moonlight-qt features:**
  - v5.0 added AV1 streaming from Sunshine hosts — [GitHub release v5.0.0](https://github.com/moonlight-stream/moonlight-qt/releases/tag/v5.0.0)
  - v6.0 added a Vulkan renderer (libplacebo; `PREFER_VULKAN=1` makes it default), **Vulkan Video decode of H.264/HEVC/AV1 on Linux**, and HDR on the Steam Deck.
  - Latest is v6.2.0 (4 Oct). No super-resolution or AI upscaling feature exists on any platform.
  - Source: [moonlight-qt releases](https://github.com/moonlight-stream/moonlight-qt/releases)
- **Apollo** (Sunshine fork): a virtual display (SudoVDA) that **automatically matches the client's resolution and frame rate**, so the host renders exactly 1280x800 at 90 Hz for a Deck OLED. Virtual display is Windows-only. Host builds exist for Windows 10+, macOS 12+ and Linux. Artemis client is Android-only — [Apollo GitHub](https://github.com/ClassicOldSong/Apollo)
- AV1 decode on the Deck: one guide claims Deck models decode AV1 in hardware and recommends **12–18 Mbps for 800p60** (10–25 Mbps range) — [PulseGeek, Jan 2026](https://pulsegeek.com/articles/enable-av1-streaming-to-steam-deck-step-by-step) (low-authority source; no primary AMD/Valve confirmation found)
- **Decoder latency pitfall:** on CachyOS Handheld, Moonlight hardware decode on a Deck showed 64–200 ms decode latency inside Big Picture. Software decode ran at 11–12 ms, and **re-imaging to SteamOS fixed it** (Sep 2024) — [CachyOS forum](https://discuss.cachyos.org/t/handheld-steam-deck-moonlight-qt-decoding-latency-very-high/3108)
- SteamOS 3.8 (June 2026) fixed video output freezing during Remote Play — [Steam Deck HQ, 17 Jun 2026](https://steamdeckhq.com/news/steamoss-3-8-has-been-released-with-new-kernel-graphics-driver-and-initial-steam-machine-support/)
- **Steam Machine (Valve):**
  - Announced 12 Nov 2025; on sale **29 Jun 2026 via a reservation queue**. Signups closed 25 Jun 2026 and required a Steam purchase before 27 Apr 2026.
  - Prices (Jun 2026):

    | SKU | USD | EUR | GBP | CAD |
    |---|---|---|---|---|
    | 512 GB | **$1,049** | €1,039 | £879 | C$1,509 |
    | 512 GB + controller | $1,128 | | | |
    | 2 TB | $1,349 | | | |

    Source: [Gfinity, 22 Jun 2026](https://www.gfinityesports.com/article/the-steam-machine-will-start-at-a-whopping-1049-wont-include-a-controller)
  - Specs: Zen 4 6C/12T; RDNA3 **28 CU** at about 10.5–11.5 TFLOPS; **8 GB GDDR6** plus 16 GB DDR5; Wi-Fi 6E. Valve targets 4K60 with FSR from about 1080p and claims about 6x the Deck. Delays were blamed on AI-driven memory shortages — [tech-insider (aggregator), Jun 2026, mod. 7 Oct 2026](https://tech-insider.org/steam-machine-2026/). GamingOnLinux headline: ["Steam Machine pricing and launch announced, and yes it's pricey"](https://www.gamingonlinux.com/2026/06/steam-machine-pricing-and-launch-announced-and-yes-its-pricey/page=3)
- **Used GPU prices (US eBay, 10 Oct 2026):**
  - RX 6700 XT: average about **$313** (99 active listings; range $260–385; +5% over 90 days) — [ResalePrices](https://resaleprices.com/gpu/amd-rx-6700-xt)
  - RX 7600 used **$249.99** (new $399.99); RTX 4060 used $375 (new $530). The Arc B580 sells 49% above MSRP, and no budget card is at or below MSRP — [VideoCardPrices, 10 Oct 2026](https://videocardprices.com/deals/)
- Deck prices also rose: OLED 512 GB to **$789**, 1 TB to **$949** on 27 May 2026 — [Wikipedia: Steam Deck](https://en.wikipedia.org/wiki/Steam_Deck)

### Inferences
- **Cost comparison** (US prices, before tax and electricity):
  - The Steam Machine at $1,049 equals about **5.2 years of GFN Ultimate** on the annual plan ($199.99/yr), or about 10.5 years of Performance.
  - A used-parts host would probably cost $600–900 in 2026: GPU ~$250–313, plus CPU, board, 16 GB RAM at inflated prices, PSU, case and SSD. This range is an estimate, not a sourced figure.
  - For an owner who "doesn't want to spend much," buying a host just to stream to the Deck is hard to justify unless he also wants a TV or desk gaming PC.
- Local streaming's advantages over cloud:
  - No 100 h cap.
  - Any game, including HD2 and anti-cheat titles, since the host runs them natively.
  - LAN latency of about 15–25 ms (extrapolated from 2021 data).
  - Bitrate can sit at 30–50+ Mbps, so artifacts are lower at 800p.
- Apollo with Moonlight is the best-fit stack if the host is Windows: native 1280x800 at 90 Hz, no scaling blur. On a SteamOS host (Steam Machine), Steam Remote Play is the zero-setup option.
- **Mac as host:** Sunshine/Apollo builds run on macOS, but the games don't. MHW, SM2 and HD2 are Windows titles, and anti-cheat titles generally won't run under translation layers such as CrossOver/Game Porting Toolkit. A fanless MacBook Air would also throttle under sustained load. This is an inference; no fetched source tested these games on Mac. Verdict: no.
- Remote streaming from a home PC while away is possible (e.g., over Tailscale), but it inherits cloud-like latency without cloud-grade networks.

### Gaps
- No 2025–2026 measured end-to-end latency for Moonlight or Remote Play **to a Steam Deck** (only TechSpot's 2021 iPad/Android test).
- No primary confirmation (AMD/Valve/Mesa) that the Deck APU decodes AV1 in hardware.
- No Valve source on how Remote Play from a Steam Machine to the Deck performs, or whether it gets special treatment.
- No sourced 2026 price for a complete used gaming PC in the US or Mexico.
- Steam Machine regional (MXN) pricing and availability in Mexico are not found.

---

## 3. Hybrid and novel approaches (offloaded frame generation, AI upscaling of streams, Steam Machine as home server)

### Takeaway
No credible, tested pipeline was found for split rendering or for frame generation on a streamed image on the Deck. Cloud services already do the heavy work, including DLSS frame generation, on the server. Moonlight has no AI upscaling. On the Deck the stream already matches native 800p, so upscaling the stream adds nothing in handheld mode. "Steam Machine as home server" is just local streaming (section 2) at a $1,049 entry price.

### Cited Findings
- GFN Ultimate runs DLSS 3 Frame Generation and Reflex server-side; RTX 5080 tiers add DLSS 4 Multi-Frame Generation — [Wikipedia](https://en.wikipedia.org/wiki/GeForce_Now); [GamingOnLinux, Aug 2025](https://www.gamingonlinux.com/2025/08/geforce-now-gets-blackwell-gpus-install-to-play-games-a-steam-deck-upgrade-and-discord-integration/page=1/)
- Moonlight-qt release notes list no super-resolution, video-enhancement or vendor-upscaling feature on any platform. It has a Vulkan renderer on Linux, opt-in via `PREFER_VULKAN=1` — [moonlight-qt releases](https://github.com/moonlight-stream/moonlight-qt/releases)
- lsfg-vk exists as a Vulkan layer and Decky plugin on the Deck (compendium §4); v2.0 shipped in Sept 2026 — [Steam Deck HQ headline](https://steamdeckhq.com/ja/news/lsfg-vk-lossless-scaling-huge-2-0-0-release/) (page failed to load; headline only). A Junk Store build also integrates it — [Junk Store blog](https://www.junkstore.xyz/blog/lsfg-frame-generation-built-in/)
- Apollo matches client resolution and refresh, so no client-side scaling is needed — [Apollo GitHub](https://github.com/ClassicOldSong/Apollo)

### Inferences
- **Frame generation on the stream client (lsfg-vk on Moonlight's Vulkan renderer)** is technically plausible but untested. Moonlight's Linux Vulkan path is opt-in, and lsfg-vk hooks Vulkan apps. Two drawbacks follow:
  - It stacks frame-generation latency on top of streaming latency.
  - Interpolating compressed video would likely magnify macroblock artifacts.
  - It is only worth trying if the cloud or host can't reach 60+ fps, which is rare with GFN Ultimate. Low value, low priority.
- **Lossless Scaling "dual-GPU" offload** is a Windows desktop setup where a second GPU generates frames. The Deck has one APU, so it doesn't apply. The streaming equivalent is the server doing the generation, which GFN already does.
- **Split rendering** (part of the frame on the server, part on the Deck): no consumer tool or service was found. Not realistic in 2026.
- **AI upscaling of streams** helps only docked at 1080p/4K, where GFN already streams up to 4K60. Handheld, the stream is native 800p. Not relevant to the handheld goal.
- **Steam Machine as home server** is the cleanest "own the hardware" option: same OS, Steam Remote Play built in. But it costs $1,049, sells through a reservation queue, has only 8 GB of VRAM, and is not confirmed for sale in Mexico. GFN dominates it on cost for a handheld-only player.

### Gaps
- No public test of lsfg-vk applied to Moonlight or GFN client output on the Deck. Unknown whether the GFN Deck app is a Vulkan app lsfg-vk can hook.
- No published split-rendering consumer system found.

---

## 4. Squeezing the Deck hardware further (undervolt, overclock, RAM OC, SMT, scheduler, memory, kernel)

### Takeaway
The extra headroom is small. Expect **2–9% fps** at best, mostly better 1% lows or the same fps at lower power. Valve's BIOS (firmware 118+) undervolt is the only low-risk lever. GPU overclocking on the OLED is effectively capped near 1600 MHz without kernel-module or BIOS hacks that carry brick risk. RAM overclocking showed no measurable benefit. SteamOS 3.8 added an opt-in LAVD scheduler with "similar or better" performance but no published Deck numbers. None of this turns MHW-class games into near-console quality at 45 fps; it belongs inside DeckForge as one more knob, not as an alternative strategy.

### Cited Findings
- **Undervolt (official):**
  - Valve's firmware 118 enables BIOS undervolting; SteamOS 3.5.5 was "primarily made for the OLED Deck" — [HotHardware, update 17 Nov 2023](https://amp.hothardware.com/reviews/steam-deck-undervolting-tested-a-little-extra-battery-life-and-performance)
  - At −30 mV on CPU, GPU and SoC: no fps change in Witcher 3; Hitman 3's 99th-percentile improved "significantly". Witcher 3 capped at 45 fps gained about **14% battery**.
  - Stable offsets vary by unit (−10 to −50 mV; some units can't undervolt at all), and finding one can take hours — same source.
- Users of the BIOS undervolt report: OLED −30 across the board stable; LCD −35 froze cutscenes in Like a Dragon, so the user backed off to −30. One user estimated a 3–4% performance gain; another saw no fps gain but less fan ramping. A CMOS reset no longer clears the undervolt — [lemm.ee thread (undated)](https://next.lemm.ee/post/20627432)
- On an **OLED**, undervolt 10/10/10 gave about **+2%** and 20/50/50 about **+4%** performance. At 20/50/50, 9 W matched stock 10 W, and Firestrike "doesn't scale well with more than 10W APU power" — [sopuli/lemmy post by thubn (date ~2025, "8 months ago")](https://lemmy.ndlug.org/u/thubn@discuss.tchncs.de)
- **Overclock (LCD, 2023, Smokeless_UMAF BIOS menus + PowerTools):**
  - OC alone: Cyberpunk average **+9%** (low) / **+5%** (high); Elden Ring +6% / +4%; battery about 35% lower.
  - Undervolt + OC: Cyberpunk +9% / +7% average, 1% lows +16%, 0.1% lows +27% on high; battery about 7% below stock.
  - Best case: 4.0 GHz CPU / 2.0 GHz GPU at a sustained 21–23 W.
  - Risks: brick, a CH341A programmer for recovery, one RMA after an aggressive undervolt; the APU shuts off at 105 °C.
  - **RAM overclock: "no measurable improvement".**
  - Comments say BIOS 115+ removed the Smokeless menus and 118+ removed overclocking support.
  - Source: [Steam Deck HQ / CryoByte33, 7 Apr 2023](https://steamdeckhq.com/news/undervolting-and-overclocking-push-your-steam-deck-beyond-its-limits/)
- Even with the BIOS OC option, the GPU stays capped at about **1600 MHz** in games. Getting past it needs a custom BIOS pack, PowerTools limits and the `vangogh_oc_fix` module; one user said the method failed for them (2024) — [Steam Community thread](https://steamcommunity.com/app/1675200/discussions/1/4330852793642803094)
- `vangogh_oc_fix` installer: a kernel module that raises the **CPU** soft max frequency, with OLED support on BIOS F7G0109. It does not mention GPU clocks, needs reinstalling after SteamOS branch updates, and is "at your own risk". It moved to the SREP / Steam Deck BIOS Manager unlock method; the last changelog entry is 2 Apr 2025 (SteamOS 3.6 / kernel 6.5) — [GitHub](https://github.com/ryanrudolfoba/steamdeck-vangogh_oc_fix-installer). Upstream amdgpu has hard-coded Van Gogh clock limits — [freedesktop issue #2638](https://gitlab.freedesktop.org/drm/amd/-/issues/2638)
- OLED memory is LPDDR5 at **6400 MT/s (102.4 GB/s)** vs the LCD's 5500 MT/s; the OLED uses a 6 nm APU — [Wikipedia: Steam Deck](https://en.wikipedia.org/wiki/Steam_Deck); [steamdeck.com LCD specs](https://www.steamdeck.com/en/tech/deck)
- **Scheduler:**
  - **SteamOS 3.8.10 stable (17–18 Jun 2026):** kernel **6.16** default; "Initial support for LAVD CPU scheduler", **opt-in** via `steamosctl set-cpu-scheduler lavd`; improved VRR frame pacing — [Phoronix, 18 Jun 2026](https://phoronix.com/news/SteamOS-3.8.10-Stable); [Steam Deck HQ, 17 Jun 2026](https://steamdeckhq.com/news/steamoss-3-8-has-been-released-with-new-kernel-graphics-driver-and-initial-steam-machine-support/)
  - LAVD (by Igalia for Valve) gives "similar or better performance than EEVDF" on the Deck. It is used in CachyOS Handheld and Bazzite, and Meta adopted it for servers — [Phoronix, 23 Dec 2025](https://www.phoronix.com/news/Meta-SCX-LAVD-Steam-Deck-Server)
  - LAVD design goals: high average fps, fewer 99th-percentile stutters, and battery life — [hpc.social summary of LPC 2025 talk, 10 Jan 2026](https://hpc.social/personal-blog/2026/latency-critical-linux-task-scheduling-for-gaming/)
  - An earlier Phoronix headline: ["Rust-Written LAVD Kernel Scheduler Shows Promising Results For Linux Gaming"](https://phoronix.com/news/LAVD-Scheduler-Linux-Gaming)
- Memory/swap: SteamOS 3.6 added zram, shrinking CryoUtilities' effect; the best UMA buffer size varies by game (compendium §4).

### Inferences
- **Realistic stack for Fede**, ranked by return for the risk:
  1. BIOS undervolt (−10 to −30 mV, test stability). Its value is lower power at a fixed 45 fps cap, which means battery or thermal headroom, rather than more fps.
  2. LAVD on SteamOS 3.8. Easy and reversible; A/B test it in CPU-bound games such as MHW, which uses RE Engine.
  3. A per-game TDP and GPU clock lock using the existing Decky plugins.
- Skip RAM OC (no measured benefit) and GPU OC beyond 1600 MHz on the OLED (needs unsupported hacks and risks bricking).
- The measured 5–9% average gains on the LCD came from raising power to 21–23 W. That costs heat, fan noise and battery, and the OLED's 6 nm efficiency gains go mostly to battery, not peak clocks.
- These are **DeckForge knobs**. They can be searched and scored automatically, per the compendium's "Search" phase, with LAVD vs EEVDF as a new dimension. They are not an alternative to optimizing.

### Gaps
- No published OLED-specific fps gains for undervolt or OC in named AAA games in 2025–2026. No measured LAVD vs EEVDF fps or 1% lows on a Deck.
- SMT on/off: no 2025–2026 measured Deck data was found in this pass.
- Whether Valve's current OLED BIOS still exposes any overclock option, and the exact SREP risk profile on OLED, were not verified. No 2026 source on Valve's warranty stance toward BIOS undervolting, beyond the fact that Valve shipped the option.
- No measured effect of kernel 6.16 vs 6.11 or earlier on Deck gaming performance.

---

## 5. Running games on a different OS on the Deck (Windows on Deck)

### Takeaway
There is no performance case for Windows on the Deck in 2026. The only head-to-head Deck data is from 2022 and was mixed: Windows was faster in some games, SteamOS in others, and some games failed to run. Recent handheld tests on other AMD devices favor SteamOS by about 24% on average. Valve does not support Windows drivers. Windows would help only with games whose anti-cheat blocks Linux, and none of the three reference games needs it: SM2 and HD2 run on Proton (HD2 had an April 2026 hotfix), and MHW runs natively.

### Cited Findings
- **Deck LCD (Mar 2022, Windows 10):**
  - Horizon Zero Dawn 56 vs 48 fps and Borderlands 3 68 vs 56 fps in favor of Windows.
  - RDR2 slightly favored SteamOS; Civ VI even; Guardians of the Galaxy **would not run** on Windows (D3D12 error).
  - Speakers had no driver; controls sometimes froze; no fTPM for Windows 11 at the time.
  - Source: [Tom's Hardware, 16 Mar 2022](https://www.tomshardware.com/uk/news/windows-steam-deck-performance-testing)
- Valve and AMD provide Windows drivers, but Valve does not support them — [Wikipedia: Steam Deck](https://en.wikipedia.org/wiki/Steam_Deck). Windows GPU drivers for the Deck were released in 2022 — [HotHardware](https://hothardware.com/news/windows-video-drivers-for-steam-deck-are-out)
- **Ars Technica, Legion Go S (not the Deck):** SteamOS beat Windows 11 in 4 of 5 games, by **about 23.9% average**; Returnal ran 33 fps on SteamOS vs 18 fps on Windows — [Tom's Guide, 27 Jun 2025](https://www.tomsguide.com/gaming/handheld-gaming/new-benchmarks-reveal-steamos-beats-windows-on-handheld-gaming-performance-heres-the-results); [Laptop Mag, 29 Jun 2025](https://www.laptopmag.com/gaming/steam-deck-leaves-windows-handhelds-behind-performance-tests)
- Windows 11 on the Steam Machine reportedly gives "nearly identical" gaming performance to SteamOS — [TweakTown headline](https://www.tweaktown.com/news/112643/windows-11-tested-on-steam-machine-provides-nearly-identical-gaming-performance-to-steamos/index.html) (headline only)
- HD2 on SteamOS: the April 2026 Proton Hotfix restored it — [GamingOnLinux headline](https://www.gamingonlinux.com/2026/04/proton-hotfix-updated-to-fix-helldivers-2-on-linux-steamos-systems/page=1/)

### Inferences
- Windows would cost Fede the DeckForge toolchain: MangoHud, lsfg-vk, gamescope, RADV VRS, vkd3d-proton overrides, Decky plugins. It would also mean worse sleep/resume and unsupported drivers, for no evidence of an fps gain. **Not recommended.**
- AMD's Windows-only driver features (AFMF, RSR) are not established as working on the Deck's custom APU. Lossless Scaling already provides frame generation on SteamOS via lsfg-vk.
- Dual-booting only makes sense for a specific game whose anti-cheat bans Linux. None of the owner's reference games is in that group.

### Gaps
- No 2024–2026 Windows vs SteamOS benchmark **on a Deck OLED** was found.
- No confirmation either way that AFMF works on the Deck under Windows.

---

## 6. Per-approach verdict for this owner: realism, cost, and how each combines with DeckForge

### Takeaway
The best low-cost plan is a **hybrid**: GFN (Performance or Ultimate) for the few PS5-era games the Deck can't run well (MHW, SM2), and local DeckForge tuning for everything else, including HD2, which isn't on GFN. Local optimization is still the right core for DeckForge, because it targets "wasted hardware" games and works offline. But it should stop trying to rescue games 5x beyond the Deck, and DeckForge could explicitly route those to cloud.

### Cited Findings (cost and fit anchors)
- GFN: Performance $9.99/mo, Ultimate $19.99/mo or $199.99/yr; Mexico Ultimate MXN 439/mo; 100 h/mo cap; Deck app at 800p 60→90 fps — [Wikipedia](https://en.wikipedia.org/wiki/GeForce_Now); [Xataka MX, Nov 2025](https://www.xataka.com.mx/videojuegos/nvidia-geforce-now-se-actualiza-ahora-podemos-contamos-rendimiento-rtx-5080-a-5k-120-fps-suscripcion-ultimate-mexico); [PCGH](https://www.pcgameshardware.de/Steam-Deck-Hardware-277668/Specials/Geforce-Now-auf-dem-Handheld-PC-1473728/)
- GFN power draw on the Deck is 7–8 W, vs 15 W for native gaming capped at 45 fps — [NoobFeed](https://www.noobfeed.com/hardware/nvidia-geforce-now-on-steam-deck-gameplay)
- Xbox Cloud Ultimate costs $29.99/mo (Oct 2025) — [GSMArena](https://m.gsmarena.com/microsoft_announces_50_price_hike_for_xbox_game_pass_ultimate-news-69792.php)
- Boosteroid from €7.49/mo; Shadow Neo €32.99/mo (Jun 2026, aggregator) — [tech-insider](https://tech-insider.org/sv/shadow-pc-vs-geforce-now-vs-boosteroid-2026/)
- Steam Machine $1,049+ (Jun 2026) — [Gfinity](https://www.gfinityesports.com/article/the-steam-machine-will-start-at-a-whopping-1049-wont-include-a-controller)
- Used RX 7600 $250, RX 6700 XT about $313 (US eBay, 10 Oct 2026) — [VideoCardPrices](https://videocardprices.com/deals/); [ResalePrices](https://resaleprices.com/gpu/amd-rx-6700-xt)
- Undervolt gives +2–4% (OLED) and OC +4–9% (LCD 2023) — [lemmy/thubn](https://lemmy.ndlug.org/u/thubn@discuss.tchncs.de); [Steam Deck HQ 2023](https://steamdeckhq.com/news/undervolting-and-overclocking-push-your-steam-deck-beyond-its-limits/)

### Inferences — comparison matrix (ratings are the researcher's judgment from the findings above)

| Approach | Quality on 800p | Latency | Cost (Oct 2026) | Reliability | Fit for Fede |
|---|---|---|---|---|---|
| Local DeckForge tuning | Limited by 1.6 TFLOPS. Good for PS4-era games, poor for MHW/SM2 | Best (native; frame gen adds some) | $0 | High offline | Core for most of the library |
| **GFN Performance/Ultimate** | High (server RTX 3060/4080/5080; 800p stream) | Network-dependent; 12–17 ms wired in EU/US tests; **CDMX unknown** | $9.99–19.99/mo (MXN 439 for Ultimate) | Needs strong Wi-Fi; 100 h cap; game must be on GFN | **Best add-on for MHW/SM2**; no HD2 |
| Xbox Cloud | Medium-high (1440p only on Ultimate, select games) | Not measured | $29.99/mo Ultimate | Browser on Deck; tied to Game Pass | Poor value |
| Boosteroid | 1080p60, no RT (fine at 800p) | Not measured | ~€7.49/mo+ (annual) | No caps; no confirmed Deck app | Budget fallback; reportedly has HD2 (unverified) |
| Shadow PC | Full Windows PC (RTX 4060–3070 Ti class) | Not measured | €32.99+/mo | Runs anything | Too expensive for the goal |
| Local streaming from own PC/Steam Machine | Highest (LAN bitrate, no cap) | ~15–25 ms LAN (2021 data) | $600–1,349 upfront | High at home only | Only if he wants a home gaming PC anyway |
| Undervolt / LAVD / TDP tuning | +0–4% fps; better efficiency | Neutral or better | $0 | High (BIOS UV is official) | Fold into DeckForge as knobs |
| GPU/RAM overclock | +4–9% (LCD), none from RAM | Neutral | $0, but brick/warranty risk | Low (hacks, resets on updates) | Skip |
| Windows on Deck | No proven gain; SteamOS often faster | — | $0 + license | Unsupported drivers | Skip |
| Stream + client frame gen / AI upscale | Unproven; may magnify artifacts | Worse | $0 | Untested | Research curiosity only |

- **Suggested combined plan:**
  1. Run a GFN Ultimate day pass ($7.99) from the CDMX home network on the Deck OLED. Check fps, latency stats and artifacts in MHW and SM2.
  2. If it's good, subscribe annually (MXN 4,399/yr, about US$200/yr equivalent) for MHW and SM2. If latency is marginal, Performance at $9.99 is enough at 800p; Ultimate's extra value is 90 fps and the RTX 5080 tier.
  3. Keep DeckForge for everything else, including HD2. Add BIOS undervolt, LAVD and per-game TDP as searchable knobs.
  4. Revisit owning a host only if a cheap used PC appears or he wants TV/desk gaming.
- **Implications for DeckForge's direction:**
  - The "games 5x beyond the Deck" category (compendium §1(b)) is better solved by cloud than by any local technique. DeckForge could add a **"route to cloud" verdict**: if the measured best native config misses the 45 fps target and the game is on GFN, recommend GFN.
  - Scoring the cloud path with DeckForge's image-quality and frame-time harness, e.g. FLIP/SSIM of a GFN capture vs a local high-quality reference, would be a novel, useful measurement. No public source has done it for the Deck.
- **Owner context:** an owner who dislikes admin work benefits from GFN's zero maintenance. The 100 h cap and GFN's game list are the only ongoing things to watch.

### Gaps
- Real-world GFN latency and quality from Mexico City on the owner's ISP and router is the single most important unknown, and only a trial can answer it.
- No MXN prices were found for GFN Performance, Xbox Cloud (Mexico), Boosteroid or Shadow, and no tax-inclusive figures.
- No source quantified total input latency for native Deck play at 45 fps (with or without lsfg-vk) against cloud streaming. A head-to-head comparison (e.g., a 240 fps phone camera on button-to-screen) would settle it.
