# Is a universal DeckForge worth building?

Status: **PROPOSED decision document**, 2026-10-11. It answers Fede's re-scoping message:

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

Earlier work: `INVENTIONS.md` (PR #6), `GOLD_HUNT_40FPS.md` (PR #7), and the Phase 1 scanner
(PRs #3–#5).

**Labels:**
- **(est.)**: my estimate or inference, not a measurement.
- **[checked]**: I verified it myself on the primary page.

---

## 1. The bar, as I read it

| Part | Your words | How I measure it |
|---|---|---|
| Universal | "used with multiple games… a universal solution" | Works by engine family and by system-level levers, not by hand-tuning one game at a time |
| Anti-cheat safe | "can be used alongside anti-cheat games like Space Marine" | Only Tier S changes: settings files, launch options, power, frame cap, refresh rate. No injection |
| Standalone target | "30 fps… visual quality on par with High… without FSR and Lossless Scaling" | Locked 30 fps at native 1280×800 with no upscaling and no frame generation. Visuals within a small distance of the game's High preset *on the Deck's own screen*, scored the way QUALITY_TARGET.md already says (FLIP plus a temporal metric, then your blind A/B) |
| With layers | "FSR and frame generation should help us get to 40+" | Upscaling and frame generation are added on top and reported separately |
| Stretch | "35 would be amazing, 40 would be ideal" | Same quality bar at a higher frame rate |

I judged two readings of "on par with High": the strict one (the literal High preset) and the
perceptual one (looks like High on a 7-inch 800p screen). The conclusion is the same for both.

## 2. The short answer

**1. Your bar can't be met for most demanding games, by us or by anyone.** It is a hardware
ceiling, not a software problem.
- In a sample of 35 demanding games from 2022–2026, only **2 meet it today**: Elden Ring and
  Armored Core VI. Both also shipped on PS4, and both already meet it without any tool.
- **None of the 26 games made only for current consoles meets it** [sample Q1, corrected].
- The best "smart settings" in published tests gain **about 5–25% over the High preset** at the
  same look [sample Q2].
- Most current-generation games need **1.5–4× more speed** to reach High-like visuals at native
  800p and 30 fps [sample Q2].

**2. A smaller universal tool is feasible, and nobody has built it.** It would:
- find the best-looking settings your Deck can hold at the frame rate you pick;
- measure on your own Deck;
- re-check after every game patch;
- stay anti-cheat safe;
- tell you plainly when a game can't do 30.

The closest project found, DeckPacer, has one commit and no measurement loop yet
[existing Q1, checked].

**3. My recommendation:**
- Don't build to the original bar.
- Build the smaller promise only if a short proof-of-value test shows it beats what Deck owners
  already have: Steam Deck HQ's hand-tuned settings and the game's own Deck defaults.
- If it doesn't, stop, and publish the research.
- Treat income as a possible bonus, not the reason to build (section 6).

## 3. What the Deck can and can't do: the 35-game sample

Classes [sample Q1]:
- **A**: ~30 fps at High or near-High, native 800p.
- **B**: ~30 at Medium native, or High only with an upscaler.
- **C**: ~30 only at Low with upscaling.
- **D**: under 30 even at Low with upscaling.
- **X**: blocked (anti-cheat).

| Class | Games | Share | What standalone DeckForge could do | With upscaling | With frame generation |
|---|---|---|---|---|---|
| **A** | Elden Ring, Armored Core VI | 2 (6%) | Already meets your bar; at best adds quality or headroom | 40+ likely (est.) | Smooth 60+ presented (est.) |
| **B** | Elden Ring Nightreign, Kingdom Come II, Hogwarts Legacy (borderline), Ghost of Tsushima, RE4 remake, Lies of P | 6 (17%) | Near-High at 30 *in some*, via the 5–25% smart-settings gain (est.). Hogwarts needs about +50% at High, so not it | High-like at 30–40 plausible (est.) | Possible from a ~40 base |
| **B/C** | God of War Ragnarök, 007 First Light, RE Requiem, Pragmata | 4 (11%) | Native High-like 30: no | 30–45 at a mixed Low/Medium look (measured, varies) | Possible |
| **C** | Monster Hunter Wilds, Helldivers 2, Cyberpunk 2077, Black Myth: Wukong, Doom: The Dark Ages, FF XVI, FF VII Rebirth, AC Shadows, Clair Obscur, Silent Hill 2, Death Stranding 2, Onimusha | 12 (34%) | Native 30 at *any* quality: mostly no | ~30 at Low; the tool can only pick the best-looking Low mix | Smoother picture from a ~30 base, but with a latency cost. Space Marine 2 testers called frame generation "horrible" below 60 [gold-engines §11] |
| **D** | Space Marine 2, Starfield, Alan Wake 2, Dragon's Dogma 2, Stalker 2, Indiana Jones, Spider-Man 2, Horizon Forbidden West, Crimson Desert | 9 (26%) | No | Under 30 even at Low | Can't fix, and several are CPU-bound in crowds and hubs |
| **X** | Battlefield 6, Marathon | 2 (6%) | Doesn't run on SteamOS | — | — |

Notes on the table:
- **Lies of P was originally classed A.** I checked the source: its ~50 fps was measured *with*
  FSR 2 Quality, so it moves to B. The sample note carries that correction.
- **[gold-engines §11]** is `docs/research/2026-10-11-gold-hunt/re_engine_swarm_low_end.md` on
  branch `design/gold-hunt-40fps` (PR #7).

**A quick ceiling check** [sample Q3]. The Xbox Series S has about 2.5× the Deck's GPU and twice
its CPU cores. Where the developer's own Series S version renders at 900p or below to hold 30, the
Deck lands in C or D. Examples: Starfield, Alan Wake 2, Monster Hunter Wilds. A settings tool
cannot outdo the studio's own console port.

**Patches help, but rarely by more than one class.** Monster Hunter Wilds, Doom: The Dark Ages,
Death Stranding 2 and Stalker 2 each moved from D toward C after patches. None reached B
[sample Q1].

**What "High-like at 800p" could mean in practice** (est., from [sample Q2]):
- **Cheap to cut, hard to see on a 7-inch screen:** volumetric quality, ambient-occlusion steps
  above the first "on" level, contact shadows, particle quality, hair, distant detail, depth of
  field, motion blur, and the step from Ultra to High shadows.
- **Expensive but visible, so keep them:** shadows below High, global illumination at Low,
  reflections on wet or metal surfaces, vegetation density, and above all render resolution.
- **This is what a smart optimizer exploits.** It is worth about 5–25%, which is enough to push a
  game running at 24–28 fps at High to 30. It is far from enough for a game that needs 2×.

## 4. Can one tool be universal and anti-cheat safe?

Yes, as a two-layer design [mechanics, overall takeaway].

**Layer 1: levers that work for every game, with no game knowledge** [mechanics §8]:
- render resolution and upscaling through gamescope (the biggest lever, but it softens the image);
- frame cap with a matching refresh rate (pacing and battery, not speed);
- power limit and clocks through Valve's steamos-manager;
- driver and Proton settings passed as launch options;
- Proton version (anti-cheat games must stay on Valve's Proton).

None of these gets a game to High-like 30 by itself. Swap and zram tweaks measured as no gain
(Hogwarts, 2023) [mechanics §8].

**Layer 2: settings adapters by engine family** [mechanics §1–§3]:
- **Unreal Engine 4/5 (est. 40–55% of demanding games):** plain-text ini files in the game's prefix,
  with fine control from `Engine.ini`. But its settings levels mean different things in each game,
  so costs must be measured, not assumed.
- **Unity:** only resolution and fullscreen are universal; the rest varies per game.
- **RE Engine, Frostbite, Helldivers 2's engine:** plain text, needs a small adapter per game.
- **Space Marine 2:** settings reportedly encrypted. The tool can only advise, and you set the menu
  yourself ("guided mode").
- The AI pipeline can draft adapters. A Deck run must still confirm each one, so "universal"
  means "covers an engine family quickly", not "works on day one with no testing" (est.).

**The anti-cheat rule that keeps it safe** [mechanics §4]:
- **The precedent:** no anti-cheat vendor has published a rule on config files. Publishers decide.
  - PUBG bans config edits that make "changes that cannot be made via the in-game settings menu".
  - Marvel Rivals began detecting and penalizing modified configs in July 2026.
- **Proposed policy for online or anti-cheat games:**
  - write only menu-reachable values;
  - write only to the game's own user-settings file, never the install folder;
  - never write while the game is running;
  - keep a "never touch" list, starting with Marvel Rivals.
- **What that costs.** In anti-cheat games the tool can only choose the best *combination of menu
  options*. That is where its value is smallest.
- **Frame generation in anti-cheat games.** Lossless Scaling's Linux version (lsfg-vk) loads into
  the game, so under our rules it is Tier I and not for anti-cheat games. Only a game's *own* frame
  generation is safe there (Space Marine 2 has FSR 3 frame generation).

**Measuring without touching the game** [mechanics §5]:
- **Frame times.** Gamescope already measures every game's frame times from outside the game and
  feeds them to Steam's performance overlay. GPU load and power come from the system.
- **Screenshots.** They come from the compositor, so nothing is injected.
- **The hard part is repeatable test scenes.** Only about 23 games released 2023–2026 have built-in
  benchmarks. The universal answer is probably **"learn while you play"**: record frame times for
  each settings combination during normal play, and compare across sessions (est.; this needs
  design work).

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
- in-process DeckWarp;
- lsfg-vk.

At most, those become an optional research track.

## 5. Compared with what exists

| Solution | What it does | Measures on your Deck? | Searches settings? | Re-checks after patches? | Anti-cheat safe? | Cost | High-like 30 on demanding games? |
|---|---|---|---|---|---|---|---|
| Steam Deck HQ reviews | Hand-tuned settings and fps for ~810 games | No (one tester, often LCD, launch week) | By hand, once | Only if a reader flags it | Yes (settings) | Free | No: shows Low/Medium + upscaling at ~24–30 [existing Q2, Q6] |
| ShareDeck | Crowd setting reports | No | No | No | Yes | Free | Thin data (1–6 reports per game) [existing Q2] |
| Valve Verified + developer Deck defaults (SDK 1.65) | Developer-chosen defaults; fps data shown only to developers | No | No | Developer's choice | Yes | Free | No: Verified only means 30 fps at defaults. Wilds' Verified look is "blurry, pixelated" [existing Q4] |
| SteamOS per-game profiles, Decky TDP plugins | Power and fps cap per game, set by you | No | No | No | Yes | Free | No: no graphics changes [existing Q1] |
| DeckPacer | Profiles, config patches, gamescope; benchmark-based recommendations *planned* | Partly (one game) | Not yet | No | Unclear | Free | Unproven: one commit, 0 stars [existing Q1, checked] |
| Microsoft Default Game Profiles (Windows handhelds) | Curated power and fps cap per game | No | No | — | Yes | Free | No: no graphics; Windows only [existing Q1] |
| NVIDIA App / G-Assist; HP OMEN AI; Razer Cortex | Lookup or predicted "optimal" settings | No | No (lookup) | Vendor updates | Yes | Free | Not on Deck: Windows and mostly NVIDIA [existing Q3] |
| Lossless Scaling (lsfg-vk), OptiScaler | Frame generation; better upscalers | — | — | — | **No** under our rules (they load into the game) | US$6.99 / free | Smoother or sharper, not High-like 30 standalone |
| GeForce NOW | Streams the game from a server | — | — | Server-side | Yes | US$19.99 or MXN 439/month, 100 h cap | **Yes, visually**, but streamed, capped and latency-dependent. Mexico is served from US data centres [market §6] |
| Xbox Cloud Gaming | Streams the Game Pass catalog | — | — | Server-side | Yes | Game Pass Ultimate MXN 339/month | Yes, visually, for its catalog. Hour caps of 5–15 h/month reported from Nov 2026 [existing Q5, market §6] |

**The gap DeckForge would fill.** No tool measures a game on your own Deck, searches its settings,
scores both frame-time stability and image quality, and re-checks after updates
[existing, bottom line]. Steam Deck HQ's settings already show the pattern DeckForge would
automate: Ultra textures, which cost little speed when video memory allows, combined with cheap
effects. But
those settings were found by hand once and are rarely re-checked [existing Q2].

**The threat.** Valve is moving toward the same territory:
- per-device developer defaults (SDK 1.65, July 2026);
- fps-by-setting data, so far shown only to developers [market §5];
- a reported, unverified idea of showing crowd fps on store pages [mechanics §7].

Valve's bar, though, is "30 fps at defaults", not "best look". Its API needs each studio to adopt
it, which leaves the large back catalogue open for years (est.).

## 6. Is it worth it? Need, audience, money

| Factor | Evidence | Effect on the case |
|---|---|---|
| Need | DRAM up to +98% in Q1 2026, PCs ~+30% since late 2025, GPUs +10–20%, expected to last into 2027–28; 60% of surveyed gamers won't build a PC within two years [market §2] | **Strong** |
| Deck price and successor | Deck OLED 512 GB went from US$549 to **US$789** on 27 May 2026 [checked]; LCD discontinued; Valve says a Deck 2 is "years away" [market §1–§2] | **Strong need**, but few new Deck buyers: weekly sales down ~80% (est.) [market §1] |
| Audience size | ~4.5–5.2M Decks (est.); SteamOS ≈ 0.5–0.9% of Steam survey respondents; Steam Machine ~120–230k (est.), not sold in Mexico [market §1, existing Q4] | **Moderate and flat** |
| Bigger audience | ≥37% of Steam users have ≤8 GB VRAM, but that is Windows, where free NVIDIA, HP and Microsoft tools already exist [market §1, §5] | Possible later; crowded |
| Willingness to pay | Lossless Scaling: US$6.99, ~2.7M sales (est.), mostly Windows [market §3] | People pay for "feels better" utilities |
| Income ceiling | SteamOS-only paid tool: low hundreds of thousands of dollars lifetime at best (est.); open-source donations usually small [market §3] | **Weak** as an income stream |
| Window before official fixes | Wilds took ~18 months to reach Verified, and its look is still "muddy" [market §4] | **Supports**: a long window for "best look" |
| Cloud as substitute | GeForce NOW 100 h cap (Jan 2026); Xbox cloud caps from Nov 2026 (reported) [market §6] | Cloud got weaker; local play still matters |

**Bottom line:**
- **The problem is real and growing.**
- **The money is small:** a SteamOS-only tool reaches about 1% of Steam.
- **The value only exists if the tool visibly beats free hand-tuned settings.** Nobody has tested
  that yet, so it is the first thing to test.

## 7. Recommendation: reframe, then prove it or stop

**Reframe the promise (decision U1).** Replace "High at 30 standalone" with:

1. **Standalone:** a locked 30 fps at the best image quality your Deck can hold. Each game gets an
   honest label:
   - "High-equivalent" when measured close to the High reference;
   - otherwise "Best look at 30, needs upscaling";
   - or "Can't hold 30 here (CPU/GPU limit)", with cloud suggested where available.
2. **Layers, reported separately:**
   - the game's own upscaler, or gamescope's;
   - then frame generation (the game's own in anti-cheat games), with its latency cost shown.
3. **Stretch:** the same, at 35 or 40 where the game allows.

**Proof-of-value gate before any further building (decision U3), about 3–4 weeks (est.):**

| Step | What | Who |
|---|---|---|
| G1 | Build the minimum: the Phase 1 scanner (done, PRs #3–#5); frame-time measurement from gamescope; one Unreal adapter, two per-game adapters and guided mode; a search loop | Me (agents, test-first) |
| G2 | Pick 6 games across classes A/B/C, at least 2 with anti-cheat and at least 2 on Unreal | You and me (U4) |
| G3 | At the same locked 30 fps, compare DeckForge's settings against the game's Deck defaults and against Steam Deck HQ's settings where they exist. Score with FLIP plus a temporal metric, then your blind A/B on the Deck | You, about 3 Deck evenings |

**Pass:**
- DeckForge is preferred, or tied with better 1% lows, in **at least 4 of 6** games;
- no hand-tuning per game beyond writing the adapter;
- no anti-cheat warnings.

**Fail:** stop building. Publish the research and the scanner as they are.

**Park:** DeckWarp, shader surgery and the REFramework work stay an optional research track for
games without anti-cheat. They are not the product.

**What we keep.** The Phase 1 scanner already detects engines, settings files and anti-cheat for
every installed game (PRs #3–#5), so it carries straight over.

## 8. Decisions for Fede

| # | Decision | Recommendation |
|---|---|---|
| **U1** | Accept that "High-like visuals at 30 fps standalone" is out of reach for most demanding games, and adopt the reframed promise (section 7) | Yes |
| **U2** | Make the product a universal, anti-cheat-safe "settings autopilot"; Tier I inventions become optional research | Yes |
| **U3** | Run the proof-of-value gate before more building; stop if it fails | Yes |
| **U4** | Test games: list what you own beyond Wilds and Space Marine 2. If needed, buy 2–4 cheap demanding games (~US$40–100). That would be outside the subscription-only budget in decision 0001 | Owned games first |
| **U5** | Income: treat as a bonus; revisit after the gate (paid Steam build like Lossless Scaling, or Patreon) | Defer |
| **U6** | Where they conflict, these decisions replace T1 (40 fps target, PR #7) and N1 ("automated Deck port team", PR #6) | Yes. I'll mark those docs superseded once you decide |

If you agree, the next PRs are:
1. update the target in QUALITY_TARGET.md, decision 0001 and CLAUDE.md;
2. a spec for the gate;
3. the build, test-first.

## 9. Caveats

- **The 35-game sample relies on reviewer data.**
  - Most are reviewers reading an on-screen counter, not controlled benchmarks.
  - Many were tested on the LCD Deck (OLED is 2–9% faster) or on old patches.
  - Some classes rest on claims, not measurements [sample, Gaps].
- **The perceptual analysis is unproven.** No study was found on what is visible at 800p on a
  7-inch screen. The "cheap to cut" list comes from desktop tests at higher resolutions.
- **The engine shares are estimates.** The Unreal share of demanding games is my inference;
  published engine shares cover all Steam releases [mechanics §1].
- **The market numbers are estimates.** Valve publishes no sales figures [market §1].
- **Cloud latency from Mexico City is still unmeasured** (experiment E11 from PR #2).
