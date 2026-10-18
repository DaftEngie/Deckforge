# Round 3: W5 (maintenance by a non-engineer), attacked from outside the software box

## Headline
1. **Proton tells every game it is not a handheld.** Microsoft's handheld program has publishers detect handhelds with one call, `RtlGetDeviceFamilyInfoEnum`. Wine and every Proton branch, bleeding-edge included, stub it to "Unknown". So no Xbox-handheld code path can ever run on a Deck. Fixing that is a one-function upstream change (Idea 1).
2. **Capcom is building a Deck-class Wilds right now.** The Switch 2 version ships 4 Dec 2026. Its handheld mode has a GPU close to the Deck's and roughly 0.4–0.5× the Deck's CPU (est.), so Capcom has to solve the plains CPU wall below Deck level. That makes Wilds the best publisher ask in this study (Idea 2).
3. **Upstream works through one table.** For D3D12 games, per-game Deck performance fixes land in vkd3d-proton's `device_workarounds.c`.
   - Wilds got `no_upload_hvv` five days after launch, with the commit message "Reported by users to help CPU perf a bit".
   - Mesa's RADV driconf (25 apps) and Proton's per-appid table hold correctness fixes only.
   - DeckForge as an "evidence lab" is a sound core loop. It is not a product DeckForge owns (Idea 3).
4. **New finding on the CFS case.** Valve's scheduler tunings have been undone by every CPU hotplug since 2022, under CFS too, not only since EEVDF. There is a two-write recipe that makes a value survive (Idea 3, case 1). A ready-to-file report is below.
5. **No accessory gives more GPU.** On the OLED the 1.6 GHz clock cap usually binds before power or heat do. The on-die blocks (encoder, display controller, audio DSP) are either already used or share the same 15 W budget.

---

## Idea 1: Proton says "handheld"
**Pitch.** Make Proton report the gaming-handheld device form on a Deck. Games that already contain an Xbox-handheld preset would then pick it up automatically.

**Already done?** No.
- Microsoft's sample is literally `RtlGetDeviceFamilyInfoEnum(nullptr, nullptr, &deviceForm); return deviceForm == 0x2E` ([IsDeviceHandheld.cpp:13-18](https://github.com/microsoft/Xbox-GDK-Samples/blob/main/Samples/Handheld/Snippets/IsDeviceHandheld.cpp)). It is the detection method on [Microsoft's handheld guidance page](https://devdocs.xbox.com/build/gdk-and-engines/handheld/handheld-guidance.md).
- Wine master `dlls/ntdll/rtl.c:1645-1652`, Proton `proton_10.0` `rtl.c:1094-1101`, and `proton_11.0`, `experimental_11.0` and `bleeding-edge` `rtl.c:1649-1661` all contain `FIXME(...stub)` and `*form = DEVICEFAMILYDEVICEFORM_UNKNOWN`.

**Mechanism.**
- When `SteamDeck=1` is set, ntdll returns form 0x2E and keeps the family as Desktop.
- Valve would turn it on per game through the `appid in [...]` lists in `default_compat_config()` (proton script, from line 1193), and only where evidence shows the handheld path helps.

**Tier.** S1 once it is in stock Proton. A local patched Proton is Tier I: bench use only, never on anti-cheat games.

**Budget.**
- None of the five targets is on Xbox's [launch list](https://news.xbox.com/en-us/2025/10/15/rog-xbox-ally-handhelds-games-list-handheld-optimized/). Later list additions not checked.
- Pessimistic: −10%. A game sees "handheld" plus an unknown GPU and picks an Ally X-class preset (16 CU) (est.).
- Central: 0 on the five targets; about +5% at defaults on games that call the API (est.).
- Optimistic: +20%, where the handheld path has content cuts the menus don't expose. DOOM: The Dark Ages' handheld mode adds "optimized SFX and VFX" ([GOL, Oct 2025](https://www.gamingonlinux.com/2025/10/doom-the-dark-ages-gets-a-major-performance-upgrade-for-handhelds-now-steam-deck-verified/page=1/)) (est.).

**Self-red-team: "It's a launcher flag; the targets don't call it."** Probably true for the targets. The value is platform-wide and grows with every title that joins the Xbox program. The falsification test measures it at no risk.
- A second hazard: Microsoft's own ID table lists GPU 0x163F under the "ROG XBOX Ally X" ([handheld-performance](https://devdocs.xbox.com/build/gdk-and-engines/handheld/handheld-performance)). But 0x163F is Van Gogh, the LCD Deck's ID, which vkd3d-proton uses to detect a Deck (`device_workarounds.c:1000-1005`, 0x163f/0x1435). The table looks swapped (est.).
- A game that copied it would treat an LCD Deck as an Ally X. That is why per-app gating is mandatory.

**Maintenance.** Valve's Proton team after merge. DeckForge supplies per-game evidence only.

**Falsification (1 week).**
- Days 1–3: run the five targets plus 10 Handheld Optimized titles with `PROTON_LOG=1`, then grep `fixme:ntdll:RtlGetDeviceFamilyInfoEnum`.
  - Kill if fewer than 2 of the 10 call it.
- Days 4–7: on non-anti-cheat callers only, bench build with the patch, then A/B against each game's best menu preset. Judge: gamescope frame times plus ColorVideoVDP on the Deck display model.
  - Pass: at least one game with ≥10% lower frame time at ≤0.1 JOD loss.
  - Kill: every handheld preset is no better than the menu presets.

## Idea 2: Ride Capcom's Switch 2 tier for Wilds
**Pitch.** Ask Capcom to expose the Wilds Switch 2 content tier on PC, behind the `SteamDeck` env var, as one "handheld" preset that covers Deck, Z2 A and Frame.

**Already done?** No.
- Wilds for Switch 2 was announced 5 Jun 2026 ([VGC](https://www.videogameschronicle.com/news/monster-hunter-wilds-announced-for-nintendo-switch-2/)) and dated 4 Dec 2026 ([Nintendo Wire, 9 Sep 2026](https://nintendowire.com/news/2026/09/09/monster-hunter-wilds-lands-on-switch-2-this-december/)): "surprisingly stable performance, although incredibly low-resolution visuals".
- On PC nothing sits below Lowest. Wilds is Deck Verified at "30 and above most of the time" ([SDHQ](https://steamdeckhq.com/news/monster-hunter-wilds-gets-steam-deck-verified/)), but the plains still run below 20 fps.

**Why Switch 2 is the right proxy.**
- Handheld mode ([club386](https://www.club386.com/nintendo-finally-reveals-switch-2-specs-including-docked-and-handheld-clock-speeds/)):
  - 6 game cores, A78C at 1.1 GHz;
  - 1.71 TFLOPS GPU;
  - 68 GB/s memory bandwidth.
- Deck: 4C/8T Zen 2 at up to 3.5 GHz, ~1.6 TFLOPS, 102 GB/s.
- Series S, by contrast, has about 2.5× the Deck's GPU. Its Wilds mode is 1080p30 ([Pure Xbox](https://www.purexbox.com/news/2024/12/capcom-unveils-monster-hunter-wilds-performance-details-for-xbox-series-x-and-s)), so it is not Deck-class.

**Mechanism.** Send an evidence packet to Capcom's PC feedback channel and Valve's compatibility team (Valve aims for review results "within a week of submission", [FAQ](https://partner.steamgames.com/doc/steamhardware/steamdeck/faq)). It contains:
- bench frame-time distributions in the format of Valve's new dashboard;
- proof that the plains are CPU-bound;
- the CPU-side knobs the Switch 2 build must have changed (from Digital Foundry-style analysis after 4 Dec).

**Tier.** S1. The publisher ships it; the user changes nothing.

**Budget (est.).**
- CPU arithmetic:
  - Switch 2: 6 × 1.1 = 6.6 core-GHz.
  - Deck: 4 × 3.5 × ~1.2 for SMT ≈ 17.
  - So Switch 2 ≈ 0.4× the Deck, assuming similar IPC.
  - If the Switch 2 build holds 30 fps, its CPU frame is about 33 × 0.4 ≈ 13–15 ms of Deck time. The Deck plains frame today is over 50 ms.
- Pessimistic: 0. The tier isn't shipped, or its cuts are mostly resolution and DLSS.
- Central: plains <20 → ~25 fps (+25–35%), now GPU-bound.
- Optimistic: ~30 fps (+50%).
- This raises the 30-fps floor at a below-High look. It does nothing for "High-like".

**Self-red-team: "Publishers fix their own platform, not Proton. Wilds is already Verified, so Capcom has no reason."** Two answers.
- Valve's new dashboard shows the framerate distribution only for Verified titles ([GOL, 5 Oct 2026](https://gamingonlinux.com/2026/10/valve-give-game-developers-more-steam-deck-framerate-data)). Wilds is exactly the game where Capcom sees its plains numbers.
- Microsoft asks for a 720p30 minimum on the Z2 A Ally, which is the same silicon class. One tier serves three devices.

**Precedents (verified):**
- FF7 Rebirth forces Low on first Deck launch ([Feb 2025](https://www.gamingonlinux.com/2025/02/final-fantasy-vii-rebirth-gets-stability-fixes-and-a-steam-deck-graphics-setting-tweak/page=1/)).
- Satisfactory 1.1.1.7 has Deck-only default presets, explicitly aimed at Verified ([Nov 2025](https://gamingonlinux.com/2025/11/satisfactory-gets-optimizations-and-improved-steam-deck-support-in-patch-1-1-1-7)).
- DOOM: The Dark Ages lists Steam Deck and Z2 A devices side by side at "720p @ ~30FPS" (Oct 2025).
- Death Stranding 2 shipped Deck performance optimizations ([Apr 2026](https://www.gamingonlinux.com/2026/04/death-stranding-2-gets-better-performance-for-steam-deck-along-with-other-general-improvements/page=1/)).
- Space Marine 2 has `SteamDeck=1`.
- Valve-side: vkd3d-proton hides ray tracing on Deck/Frame for Persona 3 Reload, Hellblade, Tracing Decay and PARANOID (`device_workarounds.c:97-125`; flag at `:1024-1029`).
- **Honest finding:** none of these credited community measurements. Each was tied to Verified status or a handheld launch. The lever is Valve's review and dashboard, not petitions.

**Maintenance.** Capcom.

**Falsification (≤2 weeks, bench Deck).**
- Confirm the target wall: Windward Plains at Lowest, internal resolution 360p vs 800p, 10 runs each.
  - Pass (CPU-bound, send the packet): frame time changes less than 10%.
  - Kill: change above 25%. The plains are GPU-bound, and Lowest already covers the GPU side.
- Judge for the ask: a written reply from Capcom or Valve within 30 days. No reply means parked.

## Idea 3: DeckForge as the upstream evidence lab
**Verdict.** Yes as the core loop; no as a product DeckForge owns. Hans-Kristian Arntzen wrote 208 of about 310 commits to vkd3d-proton's workaround files since January 2025. DeckForge produces evidence, and its KPI is entries landed. It is the only route in this study whose maintenance cost for Fede trends to zero.

**Channel map** (checked in source):

| Channel | What lands | How | Speed / evidence |
|---|---|---|---|
| vkd3d-proton `device_workarounds.c` | Per-exe performance and Deck flags. These are keyed on the exe name, so they also apply to Alan Wake 2 on Epic. | GitHub issue or PR | Wilds: launch → commit 9645932 in 5 days (2025-03-05), "Reported by users". Proton Experimental takes the "latest development versions" (Proton changelog, line 75). |
| Mesa `src/amd/vulkan/00-radv-defaults.conf` | 25 apps, all correctness fixes. The engine-wide `vkd3d` block is at lines 16-22. | freedesktop.org GitLab merge request (unreachable from here, speed not measured) | **New:** since vkd3d-proton commit 512364b (2026-09-08), the game's engine is forwarded to the driver, so RADV can key entries on "UE5 under D3D12" for the first time. |
| Proton `default_compat_config()` | Correctness per appid | ValveSoftware/Proton issue | Stable releases 10.0-2 to 11.0-2 across 2025–26 |
| SteamOS | Defaults and system services | Issues only. The source is visible only through Jovian mirrors. | 3.8.15 fixed a composition performance regression after social-media reports ([GOL, Jul 2026](https://www.gamingonlinux.com/2026/07/steamos-3-8-15-brings-a-performance-fix-and-steamos-3-8-23-beta-is-out-too/page=1/)) |
| gamescope | Compositor | GitHub pull requests | n/a |
| Kernel | amd-pstate | LKML | epp_boost is still an RFC (Jul 2026). Months at best. |

**Evidence format maintainers built for themselves.** vkd3d-proton has a per-PSO timestamp profiler (commit 76a5c48: "picking out PSOs which are suspiciously slow on a certain GPU/driver").
- Enable it with `VKD3D_TIMESTAMP_PROFILE=<path>`. It writes CSV rows of PSO hash, shader hashes, time and invocations (`timestamp_profiler.c:312,376`).
- It is compiled only into profiling builds (`meson.build:119-120`). So it is a bench-only, Tier I tool for games without anti-cheat.
- The output contains no assets, so it may leave the bench under the legal rule.

**Case 1: the CFS report** (my additions to the Round 2 finding):
- `holo-cfs-debugfs-settings.in:33-37` writes five files. Three of them no longer exist on 6.16 (`debug.c:510-518`), which trips the `IS_ERR` branch, so `logger` reports a failure on every boot (`:39-40`).
- The surviving writes, and any `base_slice_ns` write, are also undone by CPU hotplug: `rq_online_fair` and `rq_offline_fair` call `update_sysctl()`, which recomputes the slice from its normalized value (`fair.c` v6.16 `:215-223`, `:12963-12972`).
- CFS did the same thing (v6.1 `:259-267`, `:11439-11449`). Valve's 2022 values therefore lasted only until the first hotplug.
- SteamOS's suspend-then-hibernate setting (`HibernateDelaySec=20min`, steamos-customizations master) guarantees a hotplug. Plain suspend also hotplugs CPUs only if `/sys/power/mem_sleep` is `deep` (unverified).
- **Persistent recipe:** write `base_slice_ns` first, then `tunable_scaling=0`. That runs `sched_update_scaling()`, which stores the written value as the normalized one with factor 1 (`fair.c:1000-1010`, `debug.c:171-196`), so later hotplugs keep it.

**Draft issue** for github.com/ValveSoftware/SteamOS:
> **holo-cfs-debugfs-tunings: 3 of 5 writes target files removed in Linux 6.6; the rest revert on CPU hotplug.**
> **Repro (stock SteamOS 3.8, kernel 6.16):**
> - `journalctl -b | grep "Not all CFS debugfs"` shows the failure line.
> - `cat /sys/kernel/debug/sched/base_slice_ns` returns 2800000.
>
> **Cause:**
> - `latency_ns`, `min_granularity_ns` and `wakeup_granularity_ns` were removed with EEVDF. Only `base_slice_ns` exists (kernel/sched/debug.c:510).
> - Debugfs writes are recomputed by `update_sysctl()` on rq online/offline, i.e. on hibernate and suspend-to-RAM. This was true under CFS too.
>
> **Options:**
> 1. Drop the dead writes.
> 2. Map the min_granularity intent to `base_slice_ns=300000`, followed by `tunable_scaling=0`, so it survives hotplug.
> 3. Decide using the attached A/B data.
>
> **Data:** p99 frame times at stock / 0.7 ms / 0.3 ms in three CPU-bound scenes (to follow).

**Budget for case 1 (est.).**
- A critical thread can wait up to one slice behind a competitor on its CPU: 2.8 ms now vs 0.3 ms.
- One such wait in a p99 frame of a 71 ms horde is about −3.5%.
- Pessimistic / central / optimistic: 0 / −2–4% / −8% on p99.
- Cost: about 9× more preemptions × ~3–5 µs each ≈ 1–1.5% CPU.

**Self-red-team: "Maintainers ignore outsiders, and a few ms is not worth their time."** Lead with plain bugs (dead code, a false error log), which are cheap to accept. Send tuning opinions only after the A/B.
- Kill the lab model if none of 3 packets is acted on within 60 days.

**Falsification (≤2 weeks).**
- Day 1:
  - read-only checks (journal line, current `base_slice_ns`, `mem_sleep`);
  - write 300000, suspend 25 minutes on battery, re-read;
  - expect a revert, then check that the persistent recipe survives.
  - File the issue the same day.
- Days 2–10: Round 2's harness with arms stock / 0.7 ms / 0.3 ms persistent.
  - Pass: p99 at least 8% better in ≥2 CPU-bound scenes, with average fps no worse than −1% in GPU-bound scenes.
  - Kill: under 3% everywhere.

---

## Question 2: the owner's PC as an offline "oven"
**Shader binaries.**
- Mesa's amdgpu drm-shim (`AMDGPU_GPU_ID=vangogh`, `src/amd/common/amdgpu_devices.c:1672`; the shim's default ID is set at `amdgpu_noop_drm_shim.c:229`) runs RADV with no AMD GPU.
- The cache UUID is the RADV binary's build-id (`radv_physical_device.c:316-345`). So the PC must run SteamOS's exact `libvulkan_radeon.so`: through WSL2 on the Windows PC; the Mac only under x86 emulation.
- Uses:
  - pre-compile caches for Alan Wake 2 on Epic, which gets no Valve pre-cache;
  - run Cluster F's compile-only search at PC speed.
- Gain: stutter and 1% lows only; native fps ≈0. For Steam games this is already done by Valve's pre-cache.

**Harvested GI and local models: the contract binds, not copyright.**
- Wukong §8.2(4) bans "creating any derivative works of data released into any terminal memory with regard to the Games".
- §2.2(4) bans derivative works, and §2.2 applies "(including for both for-profit and non-profit purposes)" ([EULA](https://store.steampowered.com/eula/2358720_eula_0)).
- Capcom §8.1 bans "analyzing… data" (per the prior legal doc).
- So purely private harvesting still breaches the licence on Wukong and Wilds. The remaining candidates are Stalker 2 and Alan Wake 2, whose EULAs are unverified.

**Correction to Round 2.**
- LFDA Art. 78 limits *exploitation* ("sólo podrán ser explotadas"), not private creation. Art. 148 IV still covers only an individual.
- US: Galoob's alternative holding treated private home use as fair use; Micro Star concerned distribution.
- Net: copyright risk for strictly personal data is low; contract risk decides, game by game. I am not a lawyer.

**Limit.** The PC cannot time Deck work. It can only render the reference frames that stay on the bench.

## Question 4: hardware outside the APU budget

| Block | Finding | Verdict |
|---|---|---|
| Video encoder (VCN) motion vectors | On-die, so it shares the 15 W. Linux exposes only frame-level `mv_x_frame/mv_y_frame` (`ac_vcn_enc.h:627-642`); there are no per-block vectors in Vulkan Video or VA-API. | Dead for native fps. At most a global-motion signal for Cluster A's gating, at an encode's power cost. |
| Display controller (DCN) | gamescope already drives the full plane colour pipeline (degamma, CTM, shaper, 3D LUT, blend, HDR multiplier) and KMS plane scaling via libliftoff (`DRMBackend.cpp:2336,2922`). | Already done |
| Audio DSP (ACP) | The OLED runs Sound Open Firmware on it ([LKML](https://lkml.iu.edu/hypermail/linux/kernel/2402.2/05615.html)). Game audio is mixed inside the game process, so offloading would be Tier I and save under 0.3 W (est.). | Dead |
| Ambient light sensor | It is an input to E's display model (ambient lux). | Fold into E; not new |
| Clip-on cooler | The OLED fan reaches only 22–25 dBA at 100% load vs 30–33 dBA on the LCD ([GamersNexus](https://gamersnexus.net/handheld-pcs/valve-goes-hard-steam-deck-oled-review-benchmarks-vs-asus-rog-ally-z1-extreme-deck-lcd)). Valve's LCD-era fan curve saturates near 90 °C (7,300 rpm). So the fan has headroom (est.). | Leakage gain only, ≤1–3% (est.). Gate on the throttle bits. |
| More GPU via an accessory | No PCIe over USB-C (USB 3.2 Gen 2 ≈1 GB/s vs 102 GB/s); DP alt-mode is output-only; power is BIOS-capped and the 1.6 GHz clock cap binds first; a second machine is streaming. | None honest |

## Unknown unknowns
1. **PCI IDs collide across devices.** 0x163F means "Deck" to vkd3d-proton and "Ally X" in Microsoft's table. Any preset keyed on a GPU ID is ambiguous, and Linux on an Ally would also receive Deck workarounds.
2. **Hotplug resets more than Steam does.** Kernel tunables revert after hibernate even when Steam touches nothing. Round 2's X2 override test should log values across a 25-minute battery suspend.
3. **Engine forwarding (Sep 2026) is an unclaimed channel.** Nobody knows yet what RADV maintainers will accept as engine-wide entries for UE5 or RE Engine running under vkd3d-proton.

**Post-June-2026 claims checked:** Valve's dashboard (5 Oct 2026, Verified titles only); Wilds on Switch 2 (4 Dec 2026); SteamOS 3.8.15 (Jul 2026); vkd3d-proton commits from Aug–Sep 2026 (local git).
**Could not verify:**
- an Unreal Engine Steam Deck device profile;
- Steamworks Deck-only launch options;
- whether Deck suspend uses S3;
- Mesa's merge speed (gitlab.freedesktop.org is blocked here).

**Key facts to keep:**
- Wine and Proton stub `RtlGetDeviceFamilyInfoEnum` to "Unknown".
- Wilds ships on Switch 2 on 4 Dec 2026.
- Valve's dashboard covers Verified titles only.
- vkd3d-proton has a Deck/Frame "no default ray tracing" mechanism.
- Debugfs scheduler writes revert on CPU hotplug; the fix is `base_slice_ns`, then `tunable_scaling=0`.
- Wukong EULA §2.2 applies to non-profit use too.

**Files.** Source copies are in `/tmp/claude-0/-home-claude/bafac712-f1ea-5f41-b2ba-592b27d3cd05/scratchpad/r3up/`: `device_workarounds.c`, `radv.conf`, `debug_v616.c`, `fair_v61.c`, `wine_rtl.c`, `pw_*.c`, `gdk/`, `vcn/`, `proton_script`, `pwiki/`, plus the `vkd3d` and `mesam` clones. I wrote no report files.
