# Round 3 brief: second creative wave, aimed at the walls Round 2 exposed (2026-10-18)

Read `brief.md` in this folder first for the goal and rules:
`/tmp/claude-0/-home-claude/bafac712-f1ea-5f41-b2ba-592b27d3cd05/scratchpad/`

Round 1 produced about 40 ideas from 7 specialists (`round1/`). Round 2 sent 7 sceptics after them (`round2/`). Read the Round 2 file for your topic before inventing anything.

**The lesson of Round 2:** most Round 1 ideas were already shipped by Valve, already done inside the engine, or much smaller than claimed. A new idea that turns out to exist already is worth nothing. So check first.

## What Round 2 established (do not re-propose these as new)

**Already shipping on a stock Deck (gain over status quo ≈ 0):**
- Forced VRS. SteamOS's "Half Rate Shading" toggle uses `RADV_FORCE_VRS_CONFIG_FILE`, and `RADV_FORCE_VRS` is ignored. The forced rate skips:
  - mesh shaders, discarding shaders, FragCoord-reading shaders, and constant-W (UI and full-screen) draws;
  - all compute.
- Wine thread priorities. `* hard nice -8` is set.
- THP=always.
- amd-pstate active mode with EPP balance_performance. uclamp/schedutil hints do nothing in this mode.
- LAVD is an opt-in toggle.
- The CAPPED/UNCAPPED profiles are managed by steamos-manager.
- vkd3d-proton's per-game workarounds for MH Wilds (`no_upload_hvv`) and UE titles are on by default.
- UE5's Lumen surface cache already runs on fixed per-frame budgets.
- UE5 VSM shadows already cache.
- `r.VolumetricRenderTarget.Mode 2` already does 1/16-pixel temporal clouds.
- MH Wilds has in-game VRS and Distant Shadow Quality settings.
- XeSS DP4a already uses dot4 (`v_dot4_i32_i8`) on the Deck through vkd3d-proton. Its Performance mode sits at about 557×348 from 800p.

**Dead:**
- per-game neural upscaler (per-game training buys ≈0.1–0.3 dB over game-generic training; INT4 isn't reachable through Vulkan on stock Mesa);
- Low→High compositor filter (the differences between presets are non-local);
- blind Vulkan-layer pass skipping under vkd3d-proton (barriers carry no dataflow, descriptor copies are memcpy, skipping corrupts state);
- far-cascade division and exact memo;
- per-frame EPP predictor;
- watt arbitrage for fps;
- custom Mesa, gamescope or Proton builds as a product (anti-cheat risk, a new cache UUID loses Valve's pre-cache, and the read-only rootfs is overwritten by updates);
- Mesa SPIR-V replacement as Tier S (it is Tier I);
- distributing harvested lighting or per-game weights without a publisher licence.

**Survivors (modest):**
- **Perceptual price list (E).** UE cvars, the Half Rate toggle, the render scale × upscaler choice (XeSS at a lower internal resolution), motion blur and the temporal cvars all count as one umbrella, never added on top of each other.
  - About +8–12% vs the nearest preset.
  - About 0–5% vs the best human Deck guide.
- **Static "gaming CPU mode" plus scheduler fixes (C).**
  - `amd_pstate=guided`: at LPC 2026, on Civ VI, worst-1% frame time went from 70 to 47 ms.
  - A finding: Valve's CFS debugfs tunings are dead on EEVDF, leaving base_slice at 2.8 ms.
  - Critical-thread slices, SMT shielding, guided undervolt and throttle-bit logging.
  - About +0–8% average fps in CPU-bound scenes, and about +8% on 1% lows (central).
- **First-person rotation-warp reprojection inside gamescope (G2).** Presented fps and latency only, not native fps. It needs an upstream change at Valve.
- **Research-gated:** a generic Deck-budget INT8 temporal upscaler, frozen until AMD's RDNA2 FSR4 ships (early 2027; the Deck itself is not committed); a Tier I subgraph skip on one non-UE game; local per-user harvested GI.

## The honest gap (all est.; no High-preset run near 800p has ever been published for these games)

**Baselines** (measured Deck OLED/LCD points × measured PC preset ratios):

| Game | High-like fps (est.) | Notes |
|---|---|---|
| Wukong | ~18.5 | Measured OLED benchmark: Low/50% FSR 51 fps, Medium/50% FSR 32/28 fps |
| Stalker 2 | ~18.7 | |
| Wilds | ~15 | |
| Space Marine 2 | ~22 average, ~14 in hordes | Still under 30 fps even at a forced 640×400 |
| Alan Wake 2 | ~11 | |

**After Round 2's corrections,** the surviving stack is roughly +15–25% central, giving:
- Wukong: about 21–23 fps central, about 30 optimistic.
- The other games: below that.

**To reach 30 fps native with good 1% lows at a High-like look,** frame time must shrink about 1.6× for Wukong and Stalker 2, 2× for Wilds, and 2.7× for Alan Wake 2. Space Marine 2 is capped by CPU or fixed cost.

## Walls to attack (your assignment names one or more)

- **W1. The "High-like" definition.**
  - Nobody has measured whether Medium plus good reconstruction is perceived as High on this screen.
  - Wukong Medium/50% already measures 32 fps on the OLED.
  - Barten's SQRI puts about 42% of perceived quality in the 2–8 cpd band (shadows, AO, GI, tone), and about 10% in the finest octave.
  - How do we measure "perceived High" credibly? What would change the target?
- **W2. The fixed-cost GPU wall.**
  - The resolution-independent share is 34–66%; it was measured at 64% in one Wukong pair, so it is unresolved.
  - What large work in UE5, RE Engine and Northlight doesn't scale with pixels, and what Tier S lever reaches it?
- **W3. The CPU / fixed-cost wall.**
  - Space Marine 2 hordes run at 14 fps. Stalker 2 settlements and Wilds plains are also limited.
  - Is it really CPU, or a GPU fixed cost, or the translation layer's CPU overhead? What would tell us, and what lever exists at Tier S0/S1?
- **W4. The reconstruction wall.**
  - Without matrix cores, neural upscalers cost 3–5 ms and FSR2-class costs about 1.6–2 ms.
- **W5. The maintenance wall.**
  - The owner is a non-engineer.
  - Anything forked or custom (Mesa, gamescope, Proton, a Vulkan layer) is untenable unless it goes upstream to Valve, Mesa or Proton, or into publisher builds.
  - Config-only and upstream contributions are durable.

## Rules

**Tiers, refined by the Round 2 anti-cheat review:**
- **S0:** outside the game process, e.g. kernel, sysfs, scheduler, gamescope's own process, read-only hidraw.
- **S1:** stock Valve binaries changed only through documented environment variables or config files.
- **Tier I:** anything that replaces a binary or shader, injects a layer, or reads or writes game memory.

Anti-cheat titles (Space Marine 2 = EAC; Helldivers 2 = GameGuard, which relies on Valve's Proton Hotfix) get S0/S1 only. Never propose testing on a real account.

**Legal:**
- Captures and raw frames from games stay on the bench and never go to Claude, CI or the cloud.
- Bench work is the owner's personal, non-commercial use. In Mexico the private-copy exception (LFDA Art. 148 IV) covers only an individual.
- Distribution of anything derived from game output needs publisher permission.
- Note the Wukong EULA §8.3 definition of a cheat as "any program that operates externally to the software of the Game and which impacts operations during gameplay". That is a contract risk even for S0 tools on Wukong.

**Native rule:**
- No live streaming of frames from another machine.
- Offline precompute is allowed. The owner also has his own Windows gaming PC (GPU unknown) and an M3 Max MacBook Pro.
- Accessories are allowed but must be flagged.
- Frame generation and reprojection never count toward native fps. They count only toward smoothness and latency.

**Evidence:** cite URLs and file:line. Label estimates "(est.)". Check facts dated after June 2026.

## Deliverable

Return your final message only. Do not write files.

Give 3–5 ideas that are *new relative to the list above*. For each:
1. Name and pitch.
2. **An "already done?" check**, with a source showing nobody ships it.
3. Mechanism.
4. Tier (S0/S1/I).
5. Budget: pessimistic / central / optimistic, on the specific game(s) it targets, with the arithmetic shown.
6. **Self-red-team:** the strongest objection a Round 2 sceptic would raise, and your answer.
7. Maintenance story: who keeps it alive after game patches and SteamOS updates?
8. Falsification experiment: 2 weeks or less, on a bench Deck run by the owner, with a measurement judge and numeric pass/kill thresholds.

Then list 2–3 unknown unknowns. Keep it under about 2,000 words.

Ideas that are big and uncertain are welcome, if they are honestly labelled. Restating a survivor with a new name is not.
