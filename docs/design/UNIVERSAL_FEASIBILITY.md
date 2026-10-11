# Is a universal DeckForge worth building?

Status: **PROPOSED decision document**, 2026-10-11. An independent verifier reviewed it twice
(PASS WITH FIXES both times), and this version addresses both rounds of findings.

It answers Fede's re-scoping message:

> *"This tool should be universal… used with multiple games… alongside anti-cheat games like Space
> Marine… My requirement for 30 fps is that visual quality will be on par with High settings. If we
> can't commit to that, we need to evaluate if this tool is even worth pursuing… 30 fps should be
> without the FSR and Lossless Scaling layers. That should be our tool standalone. Frame generation
> and FSR should help us get to 40+… compare to existing solutions."*

**Evidence.** Four new research notes in `docs/research/2026-10-11-universal/`:

| Cited as | File | Question |
|---|---|---|
| [sample] | `game_feasibility_sample.md` | Which of 35 demanding 2022–2026 games can a Deck run at High-like quality, native 800p, 30 fps? How much can smart settings gain? |
| [existing] | `existing_solutions.md` | What tools and services exist, and how close does each get to the bar? |
| [mechanics] | `universal_mechanics.md` | Can one tool work across engines and with anti-cheat? How would it measure? |
| [market] | `market_viability.md` | Who would use it, the RAM/GPU price crisis, money, platform risk, cloud |

**Earlier work:**
- `INVENTIONS.md` (PR #6);
- `GOLD_HUNT_40FPS.md` (PR #7);
- `STRATEGY_OPTIONS.md` (PR #2);
- the Phase 1 scanner (PRs #3–#5, written and in review, not merged; #4 and #5 show a failing
  dependency-review check because the repo's Dependency graph setting is off).

**Labels:**
- **(est.)**: my estimate or inference, not a measurement.
- **[checked]**: I verified it myself on the primary page. The verifier's environment could not
  reach web pages, so these rest on my check alone.

---

## 1. The bar, as I read it

| Part | Your words | How I'd measure it |
|---|---|---|
| Universal | "used with multiple games… a universal solution" | Works by engine family and by system-level levers, not by hand-tuning one game at a time |
| Anti-cheat safe | "can be used alongside anti-cheat games like Space Marine" | Only Tier S changes, and in anti-cheat games only a short allowed list of them (section 4) |
| Standalone target | "30 fps… visual quality on par with High… without FSR and Lossless Scaling" | Locked 30 fps at native 1280×800, with no upscaling and no frame generation, and image quality on par with High (scoring below) |
| With layers | "FSR and frame generation should help us get to 40+" | Upscaling and frame generation added on top, reported separately |
| Stretch | "35 would be amazing, 40 would be ideal" | Same quality bar at a higher frame rate |

**How "on par with High" is scored.**
- QUALITY_TARGET.md already scores every setup against a reference: the same scene at *maximum*
  settings at native 800p. It uses per-frame (FLIP) and temporal metrics, then your blind A/B on
  the Deck.
- I'd define **"High-equivalent"** (decision U7) this way:
  - at native 800p, with no upscaling and no frame generation;
  - it scores at least as close to that reference as the game's own High preset does, within a
    tolerance fixed in advance and over repeat captures;
  - your blind A/B makes the final call, as QUALITY_TARGET.md already says.

**Two readings:**
- **Strict:** the literal High preset at native 800p.
- **Perceptual:** looks like High on the 7-inch screen.

The headline holds under both. 23 of the 35 sampled games (66%) need upscaling just to reach
about 30 fps at *Low* (class C), can't reach 30 even then (class D), or don't run (class X). No reading of "High at native 800p" rescues those.

## 2. The short answer

**1. Your bar can't be met for most demanding games by any tool running on the Deck.** It is a
hardware ceiling. Patches move games a little, and cloud streaming sidesteps the ceiling by not
rendering on the Deck.
- In a sample of 35 demanding games from 2022–2026, **at most 2 are shown to meet it today**:
  Elden Ring and Armored Core VI.
  - Under the strict reading the count is 0–1. Elden Ring's result uses a mixed High/Medium/Low
    build, and Armored Core VI's may rely on dynamic resolution.
  - Both also shipped on PS4. Under the perceptual reading, both reach it without any tool
    [sample Q1, corrected].
- **None of the 26 games made only for current consoles is shown to meet it** [sample Q1].
- **Smart settings gain about −8% to +8% over the High preset at the same look.** They gain 10–27%
  if you accept a near-Medium look. This is my reading of the two desktop games in [sample Q2];
  that note's own 5–25% summary mixes both kinds of build, so treat it as an estimate.
- **What C and D games need.** Most need at least **~2–4× more speed just to drop the upscaler at
  Low**, and more again to reach High (est.). This is from the 50–67% render scales in
  [sample Q1]; that note's "1.5–4×" figure is a pixel ratio. Several games are limited by the CPU
  in crowds and hubs, where fewer pixels don't help [sample Q4].

**2. A smaller universal tool is feasible in parts, and we found no one who has built it.** It
would:
- find the best-looking settings your Deck can hold at the frame rate you pick;
- measure on your own Deck;
- re-check after every game patch;
- stay anti-cheat safe;
- tell you plainly when a game can't do 30.

The closest project found, DeckPacer, has one commit and no measurement loop yet [existing Q1,
checked]. Two parts are unproven: measuring without repeatable test scenes, and whether the tuned
settings look better than what people already use.

**3. My recommendation:**
- Don't build to the original bar.
- First run a **cheap manual test** (no code, about 3–4 Deck evenings). It checks whether carefully
  tuned settings visibly beat what Deck owners already have: the game's Deck defaults and Steam
  Deck HQ's hand-tuned settings.
- Build only if that test passes. If it fails, stop and publish the research.
- Treat income as a possible bonus, not the reason to build (section 6).

## 3. What the Deck can and can't do: the 35-game sample

Classes [sample Q1]:
- **A**: ~30 fps at High or near-High, native 800p.
- **B**: ~30 at Medium native, or High only with an upscaler.
- **C**: ~30 only at Low with upscaling.
- **D**: under 30 even at Low with upscaling.
- **X**: blocked (anti-cheat).

| Class | Games | Share | What standalone DeckForge could do (est.) | With upscaling | With frame generation |
|---|---|---|---|---|---|
| **A** | Elden Ring, Armored Core VI | 2 (6%) | Already meets the perceptual bar; at best adds a little quality or headroom | 40+ likely (est.) | Smooth 60+ presented (est.) |
| **B** | Elden Ring Nightreign, Kingdom Come II, Hogwarts Legacy (borderline), Ghost of Tsushima, RE4 remake, Lies of P | 6 (17%) | A same-look gain of up to ~8% only helps a game already near 28 fps at High. Hogwarts needs about +50%, so not it | High-like at 30–40 plausible (est.) | Possible from a ~40 base |
| **B/C** | God of War Ragnarök, 007 First Light, RE Requiem, Pragmata | 4 (11%) | Native High-like 30 **not measured**; unlikely (est.) | 30–60+ at a mixed look (measured, varies; Pragmata ~60 uncapped with FSR 3) | Possible |
| **C** | Monster Hunter Wilds, Helldivers 2, Cyberpunk 2077, Black Myth: Wukong, Doom: The Dark Ages, FF XVI, FF VII Rebirth, AC Shadows, Clair Obscur, Silent Hill 2, Death Stranding 2, Onimusha | 12 (34%) | Native 30 at *any* quality: mostly no | ~30 at Low; the tool can only pick the best-looking Low mix | A smoother picture from a ~30 base, with a latency cost (see below) |
| **D** | Space Marine 2, Starfield, Alan Wake 2, Dragon's Dogma 2, Stalker 2, Indiana Jones, Spider-Man 2, Horizon Forbidden West, Crimson Desert | 9 (26%) | No | Under 30 even at Low | Can't fix it, and several are CPU-bound in crowds and hubs |
| **X** | Battlefield 6, Marathon | 2 (6%) | Doesn't run on SteamOS | — | — |

**Notes on the table:**
- **Lies of P was originally classed A.** I checked the source: its ~50 fps was measured *with* FSR
  2 Quality, so it moves to B. The sample note carries "[corrected]" markers wherever this
  changed a count.
- **Frame generation from a ~30 fps base.** Steam Deck HQ said frame generation "feels horrible"
  below 60 in Space Marine 2 [gold-engines §11]. That file is
  `docs/research/2026-10-11-gold-hunt/re_engine_swarm_low_end.md` on branch
  `design/gold-hunt-40fps` (PR #7).

**A quick ceiling check** [sample Q3]. The Xbox Series S has about 2.5× the Deck's GPU and twice
its CPU cores.
- Where the developer's own Series S version renders at 900p or below to hold 30, the Deck lands in
  C or D. Examples: Starfield at 900p, Alan Wake 2 at 720p.
- Monster Hunter Wilds on Series S is capped at 1080p and still often falls below 30.

A settings tool cannot outdo the studio's own console port.

**Patches help, but rarely by more than one class.** Monster Hunter Wilds, Doom: The Dark Ages,
Death Stranding 2 and Stalker 2 each moved from D toward C after patches. None reached B
[sample Q1].

**What a smart optimizer can and can't exploit** (est., from desktop tests in [sample Q2]):
- **Cheap to cut, hard to see:** volumetric quality, ambient-occlusion steps above the first "on"
  level, contact shadows, particle quality, hair, distant detail, depth of field, motion blur, and
  the Ultra-to-High shadow step.
- **Expensive and visible:** shadows below High, global illumination at Low, reflections on wet or
  metal surfaces, vegetation density, and above all render resolution.
- **Same-look builds gain little over High** (Starfield +4% / +8%; Black Myth: Wukong −8%). The
  bigger gains come from builds that look closer to Medium.

## 4. Can one tool be universal and anti-cheat safe?

Partly. The design would have two layers [mechanics, overall takeaway].

**Layer 1: levers that work for every game, with no game knowledge** [mechanics §8]:
- render resolution and upscaling through gamescope (the biggest lever, but it softens the image);
- a frame cap with a matching refresh rate (pacing and battery, not speed);
- power limit and clocks through Valve's steamos-manager;
- driver and Proton settings passed as launch options;
- Proton version (anti-cheat games must stay on Valve's Proton).

None of these gets a game to High-like 30 on its own. Swap and zram tweaks measured as no gain
(Hogwarts, 2023) [mechanics §8].

**Layer 2: settings adapters by engine family** [mechanics §1–§3]:
- **Unreal Engine 4/5.**
  - It covers 7 of our 35 sampled games (20%). The researcher's 40–55% guess for all demanding
    games is unverified [mechanics §1].
  - Settings are plain-text ini files, with fine control from `Engine.ini`. But settings levels mean
    different things in each game, so costs must be measured, not assumed.
  - In anti-cheat games, `Engine.ini` edits are off-limits (below), so one Unreal adapter covers
    less than it seems.
- **Unity:** only resolution and fullscreen are universal; the rest varies per game.
- **RE Engine, Frostbite, Helldivers 2's engine:** plain text, needs a small adapter per game.
- **Space Marine 2:** settings reportedly encrypted. The tool can only advise, and you set the menu
  yourself ("guided mode").
- **Adapters still need a real test.** The AI pipeline can draft adapters, but each one must be
  confirmed on a Deck. "Universal" therefore means "covers an engine family quickly", not "works on
  day one untested" (est.).
- **Current scanner coverage.** The Phase 1 scanner, in review, recognises Unreal, Unity and RE
  Engine. Other engines, including Space Marine 2's and Helldivers 2's, show as "unknown"
  (verifier, `feat/discover-detect:src/deckforge/detect.py` lines 309–323).

**The anti-cheat rule that keeps it safe** [mechanics §4]:
- **No vendor rule exists; publishers decide.** No anti-cheat vendor has published a rule on config
  files.
  - PUBG bans config edits that make "changes that cannot be made via the in-game settings menu".
  - Marvel Rivals began detecting and penalizing modified configs in July 2026.
  - Penalties can arrive in later waves, and a ban on your account may be permanent.
- **Proposed policy for online or anti-cheat games** (decision U8):
  - write only menu-reachable values;
  - write only to the game's own user-settings file, never the install folder, and never while the
    game runs;
  - no `Engine.ini` or console-style settings;
  - keep a "never touch" list, starting with Marvel Rivals;
  - launch options from a **short allowed list only**: frame cap, resolution, and driver settings.
    I propose each entry with a stated reason it loads nothing into the game, and you approve the
    list.
  - **Never** launch options that load anything into the game: Vulkan layers such as lsfg-vk,
    DLL-upgrade switches such as `PROTON_FSR4_UPGRADE`, or engine-settings switches.
  - CLAUDE.md lists all launch options as Tier S today. This proposal narrows that.
- **What that costs.** In anti-cheat games the tool can only choose the best *combination of menu
  options*, which is where it adds the least.
- **Frame generation in anti-cheat games.** lsfg-vk, the unofficial community port of Lossless
  Scaling's frame generation to Linux, loads into the game. PR #2 already classed it Tier I, so it
  is not for anti-cheat games. There, only a game's *own* frame generation is safe; Space Marine 2
  has FSR 3 frame generation.

**Measuring without touching the game** [mechanics §5]:
- Gamescope already measures every game's frame times from outside the game and feeds them to
  Steam's performance overlay. GPU load and power come from the system. Screenshots come from the
  compositor.
- Using those numbers needs a change to the SteamOS session settings, and gamescope's stats-file
  format is undocumented.
- **The hard part is repeatable test scenes.** Only about 23 games released 2023–2026 have built-in
  benchmarks. The universal answer is probably **"learn while you play"**: record frame times for
  each settings combination during normal play and compare across sessions. That is unproven and
  needs design work (est.).

**"Integrated into SteamOS," realistically** [mechanics §6]:
- Only Valve can build it into SteamOS itself.
- The practical form is a background service plus an optional Decky panel in the quick-access
  menu. Decky broke several times in 2026, so the core must not depend on it.
- Valve accepts outside contributions to gamescope (NVIDIA's, for example). Small upstream pieces
  are plausible; a whole tuner is not.

**What does *not* belong in the universal tool.** Everything from INVENTIONS and the gold hunt that
loads into the game is per-game, opt-in, and never for anti-cheat games:
- shader surgery;
- REFramework cuts;
- in-process DeckWarp-D;
- lsfg-vk.

At most these become an optional research track. **DeckWarp-C**, the compositor version, stays
undecided under INVENTIONS N5; this document does not settle it.

## 5. Compared with what exists

| Solution | What it does | Measures on your Deck? | Searches settings? | Re-checks after patches? | Anti-cheat safe? | Cost | High-like 30 on demanding games? |
|---|---|---|---|---|---|---|---|
| Steam Deck HQ reviews | Hand-tuned settings and fps for ~810 games | No (one tester, often LCD, launch week) | By hand, once | Only if a reader flags it | Yes (settings) | Free | No: shows Low/Medium + upscaling at ~24–30 [existing Q2, Q6] |
| ShareDeck | Crowd setting reports | No | No | No | Yes | Free | Thin data (1–6 reports per game) [existing Q2] |
| Valve Verified + developer Deck defaults (SDK 1.65) | Developer-chosen defaults; fps data shown only to developers | No | No | Developer's choice | Yes | Free | No. Verified only means 30 fps at defaults [existing Q4]; Monster Hunter Wilds' Verified look is "blurry, pixelated" [existing Q6] |
| SteamOS per-game profiles, Decky power plugins | Power and fps cap per game, set by you | No | No | No | Yes | Free | No: no graphics changes [existing Q1] |
| DeckPacer | Profiles, config patches, gamescope; benchmark-based recommendations *planned* | Partly (one game) | Not yet | No | Unclear | Free (MIT) | Unproven: one commit, 0 stars, dates unknown [existing Q1, checked] |
| Microsoft Default Game Profiles (Windows handhelds) | Curated power and fps cap per game | No | No | — | Yes | Free | No: no graphics changes; Windows only [existing Q1] |
| NVIDIA App / G-Assist; HP OMEN AI; Razer Cortex | Lookup or predicted "optimal" settings | No | No (lookup) | Vendor updates | Yes | Free | Not on Deck: Windows, mostly NVIDIA [existing Q3] |
| lsfg-vk, OptiScaler | Frame generation; better upscalers | — | — | — | **No** under our rules (they load into the game) | Lossless Scaling US$6.99 / free | Smoother or sharper, not High-like 30 standalone |
| GeForce NOW | Streams the game from a server | — | — | Server-side | Yes | Ultimate MXN 439/month in Mexico [market §6] (US$19.99 per PR #2); 100 h cap | **Yes, visually**, but streamed, capped and latency-dependent. Mexico is served from US data centres [market §6] |
| Xbox Cloud Gaming | Streams the Game Pass catalog | — | — | Server-side | Yes | Game Pass Ultimate MXN 339/month [existing Q5] | Yes, visually, for its catalog. Hour caps of 5–15 h/month reported from Nov 2026 [market §6] |

**The gap DeckForge would fill.** We found no tool that measures a game on your own Deck, searches
its settings, scores both frame-time stability and image quality, and re-checks after updates
[existing, bottom line]. Some of the research searches were cut short, so "found no" is not proof
of absence.

Steam Deck HQ's settings already show the pattern DeckForge would automate: Ultra textures (cheap
when video memory allows) combined with cheaper effects. But those settings were found by hand
once and are rarely re-checked [existing Q2].

**Two cheaper alternatives to building our own:**
- **Contribute to DeckPacer**, which already has profiles and adapters and plans the
  recommendation step [existing Q1].
- **Publish verified settings guides** made with the same method, without a tool. That is closer
  to Steam Deck HQ's model.

**The threat.** Valve is moving into the same territory:
- per-device developer defaults (SDK 1.65, July 2026);
- fps-by-setting data, so far shown only to developers [market §5];
- a reported, unverified idea of showing crowd fps on store pages [mechanics §7].

Valve's bar, though, is "30 fps at defaults", not "best look". Its API needs each studio to adopt
it, which leaves the large back catalogue open for years (est.).

## 6. Is it worth it? Need, audience, money

| Factor | Evidence | Effect on the case |
|---|---|---|
| Need | DRAM contract prices up to +98% in Q1 2026, expected high into 2027–28. PC price rises: up to 8% per IDC; ASUS reports ~30% cumulative for its own PCs. GPUs +10–20%. 60% of surveyed gamers won't build a PC within two years [market §2] | **Strong** |
| Deck price and successor | Deck OLED 512 GB went from US$549 to **US$789** on 27 May 2026 [checked]. LCD model discontinued. Valve says a Deck 2 is "years away" [market §1–§2] | **Strong need**, but few new Deck buyers: weekly sales down ~80% (est.) [market §1] |
| Audience size | ~4.5–5.2M Decks (est.). SteamOS ≈ 0.5–0.9% of Steam survey respondents. Steam Machine ~120–230k (est.), not sold in Mexico [market §1, existing Q4] | **Moderate and flat** |
| Bigger audience | ≥37% of Steam users have ≤8 GB VRAM. That audience is on Windows, where free NVIDIA, HP and Microsoft tools already exist [market §1, §5] | Possible later; crowded |
| Willingness to pay | Lossless Scaling: US$6.99, ~2.7M sales (est.), mostly on Windows [market §3] | People pay for utilities that make games feel better |
| Income ceiling | A SteamOS-only paid tool probably makes low hundreds of thousands of dollars lifetime (est., wide uncertainty). Open-source donations are usually small [market §3] | **Weak** as an income stream |
| Window before official fixes | Monster Hunter Wilds took ~18 months to reach Verified, and its look is still "muddy" [market §4] | **Supports**: a long window for "best look" |
| Cloud as substitute | GeForce NOW 100 h cap (Jan 2026); Xbox cloud caps from Nov 2026 (reported) [market §6] | Cloud got weaker; local play still matters |
| Your time | Each test means Deck evenings, and each decision means reviews. Agents do the technical work | The real cost to you; keep the first test small |

**Bottom line:**
- **The problem is real and growing.**
- **The money is small:** a SteamOS-only tool reaches about 1% of Steam.
- **The value exists only if tuned settings visibly beat what people already use for free.** Nobody
  has tested that, so it is the first thing to test.

## 7. Recommendation: reframe, test cheaply, then decide

**Reframe the promise (decision U1).** Replace "High at 30 standalone" with:

1. **Standalone:** a locked 30 fps at the best image quality your Deck can hold. Each game gets an
   honest label:
   - "High-equivalent" when it meets the U7 score;
   - otherwise "Best look at 30, needs upscaling";
   - or "Can't hold 30 here (CPU/GPU limit)", with cloud suggested where available.
2. **Layers, reported separately:**
   - the game's own upscaler, or gamescope's;
   - then frame generation (the game's own in anti-cheat games), with its latency cost shown.
3. **Stretch:** the same, at 35 or 40 where the game allows.

**Step 0, a manual test before any building (decision U3).** About 2–3 weeks of calendar time and
about 3–4 Deck evenings for you (est.).

**What it tests.** Whether careful tuning visibly beats what Deck owners already have.
- Step 0 uses menu values only and a handful of variants, with no automated search.
- A fail is therefore strong evidence, not proof: if careful hand-tuning can't win, an automated
  tool is unlikely to (est.).

**Ground rules:**
- **No new code and no automated writes.** You change settings yourself in each game's menu, as any
  player does, so there is no anti-cheat risk beyond normal play.
- **Preference games:** 3 games you own that can hold a locked 30, upscaled if needed (classes B
  and C; Monster Hunter Wilds counts as C). Class A games are left out because the expected result
  is a tie.

**For each preference game I prepare three settings sets, all locked at 30 fps:**
1. the game's Deck default;
2. Steam Deck HQ's settings, where they exist;
3. a tuned set from the research, plus 1–2 variants in case the first doesn't hold 30.

**How the comparison works:**
- **Source-blind labels.** I label the sets with random letters. You see the values while entering
  them, but not which source made each one; the key is revealed only after you score.
- **Stability check.** With Steam's performance overlay showing the frame-time graph, count hitches
  (spikes above 50 ms) over 2 minutes in each scene. The tuned set must have no more hitches than
  the default.
- **Repeats.** Compare twice per game, in two different scenes.

**Pass rule, fixed before testing:**
- In at least **2 of 3** games, you **clearly** prefer the tuned set over both the default and
  Steam Deck HQ's set, in both scenes.
- In no game is the tuned set clearly worse.
- "Slightly better" counts as a tie, and ties count as fails.

**Separate check (not part of the pass rule): Space Marine 2 and other class D games.**
- Is the honest label right? That is, does the game really fail to hold 30 in hordes?
- Do tuned settings give fewer hitches at its best stable frame rate?
- This tests the "tell you plainly" half of the promise.

**If Step 0 passes: build the minimum (Step 1).** That needs, in this order:
1. **The safety module** (backups, atomic writes, manifest). Its spec in PR #1 is waiting for your
   answers, and CLAUDE.md R10 requires it before any write outside the repo.
2. **A Deck test path you approve.**
   - CLAUDE.md R7 says only the bench runner drives the Deck.
   - R5 bars agents from `bench/`, so agents don't write the code that grades them.
   - The options are an explicit exception you approve, recorded in `docs/ENFORCEMENT.md` and
     checked by the verifier, or a human author for that part.
3. **The gamescope session change** for frame-time capture, backed up and reversible.
4. **The adapters and search loop:** one Unreal adapter, two per-game adapters, guided mode, and
   the search loop, built test-first.

That is roughly 4–8 weeks of agent work plus several Deck evenings (est.). The scanner work in PRs
#3–#5 carries over once merged.

**If Step 0 fails:** stop building, and publish the research as it is.

**Park:** shader surgery, REFramework work and in-process DeckWarp stay an optional research track
for games without anti-cheat. They are not the product.

## 8. Decisions for Fede

| # | Decision | Recommendation |
|---|---|---|
| **U1** | Accept that "High-like visuals at 30 fps standalone" is out of reach for most demanding games, and adopt the reframed promise (section 7). This replaces decision 0001's "locked 45 fps native" target with "locked 30 at best quality, with labels". The target files (CLAUDE.md, decision 0001, QUALITY_TARGET.md) keep saying 45 fps until they are updated after Step 0 | Yes |
| **U2** | Make the product a universal, anti-cheat-safe "settings autopilot"; in-process inventions become optional research | Yes |
| **U3** | Run Step 0 (the manual test) before building; build only if it passes, stop if it fails | Yes |
| **U4** | Tell me which games you own beyond Wilds and Space Marine 2, so I can pick 2 more class B or C games for Step 0. Buying games would be outside the subscription-only budget in decision 0001 | Owned games first |
| **U5** | Income: treat as a bonus; revisit after Step 0 (paid Steam build like Lossless Scaling, or Patreon) | Defer |
| **U6** | Where they conflict, these decisions replace T1 (40 fps target, PR #7) and N1 ("automated Deck port team", PR #6) | Yes. I'll mark those docs superseded once you decide |
| **U7** | "High-equivalent" = native 800p with no upscaling or frame generation, scoring at least as close to the maximum-settings reference as the game's own High preset, within a preset tolerance over repeat captures, with your blind A/B as the final call (section 1) | Yes |
| **U8** | Anti-cheat policy: menu-reachable values only, user-settings file only, an allowed list of launch options, a never-touch list. This narrows CLAUDE.md's "launch options are Tier S" | Yes |
| **U9** | Alternative to building: contribute to DeckPacer, or publish guides, if Step 0 shows value but you'd rather not run a project | Decide after Step 0 |

If you agree, the next steps are:
1. the Step 0 plan, with settings cards for your games;
2. after it passes, update the target in QUALITY_TARGET.md, decision 0001 and CLAUDE.md, and write
   the specs for the safety module and the Deck test path.

## 9. Caveats

- **The 35-game sample relies on reviewer data.**
  - Most are reviewers reading an on-screen counter, not controlled benchmarks.
  - Many were tested on the LCD Deck (OLED is 2–9% faster) or on old patches.
  - Some classes rest on claims [sample, Gaps].
  - One misclassification was found and fixed (Lies of P); others may exist.
- **The same-look gain is thin evidence.** It comes from two desktop games at 1440p, none tested on
  a Deck. No study was found on what is visible at 800p on a 7-inch screen.
- **The Unreal share is uncertain.** It is 20% in our sample; the 40–55% figure is an unverified
  guess.
- **The market numbers are estimates.** Valve publishes no sales figures [market §1].
- **The verifier could not reach web pages**, so web-sourced facts rest on the researchers and on my
  own checks.
- **Cloud latency from Mexico City is still unmeasured** (experiment E11 from PR #2).
