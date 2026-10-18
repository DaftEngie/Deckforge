# Round 3 red-team: W3 (CPU wall) and W5 (ecosystem/upstream)

Reviewer stance: Linux kernel and Wine/Proton maintainer, plus publisher partnerships. Kernel sources are torvalds/linux v6.16. I diffed the scheduler and amdgpu-ctx code against Valve's tag Jovian-Experiments/linux `6.16.12-valve28`, and it matches line for line.

## Headline
1. **The CFS finding is right at its core, but the draft issue overstates it.**
   - A debugfs `base_slice_ns` write does revert on any runqueue online/offline, and the two-write recipe does work.
   - But 2 of Valve's 5 writes (`migration_cost_ns=50000`, `nr_migrate=128`) still apply and never revert.
   - Hibernation is **disabled on 3.8**, so S3 suspend is the trigger.
   - The revert behaviour is upstream, dating from the 5.13 move of these knobs to debugfs.
2. **"Proton says handheld" has correct facts but a contradicted premise.**
   - The stub, the 0x2E constant and the swapped Microsoft table all check out.
   - DOOM: The Dark Ages, the flagship handheld-mode title, already autodetects the Deck.
   - Microsoft's own 40 Ally profiles are applied by the OS, not by games. Expected value is about 0.
3. **Triage is genuinely S0, but `drm-engine-gfx` is ring occupancy, not busy time.** SteamOS sets `amdgpu.sched_hw_submission=4`, so overlapping jobs are counted more than once.
4. **Steam's Manual GPU Clock pins the clock; it is not a ceiling.** Idea 2 and the GPU arm of the 2×2 test need redesigning.
5. **`/etc/default/grub` edits are wiped by SteamOS updates by default.**
6. **SM2: the verdict holds for a 30-fps *floor* in heavy hordes.** But the "14 fps" baseline is one launch-week anecdote. Current horde fps has never been measured.

---

## 1. Four-counter triage
**Facts**
- `/proc/<pid>/task/*/schedstat` [checked]:
  - Mode `S_IRUGO` with no ptrace check (`fs/proc/base.c:511-523,3370`).
  - It needs only `CONFIG_SCHED_INFO` (`include/linux/sched/stat.h:25-28`). `run_delay` is accounted unconditionally (`kernel/sched/stats.h:241-281`).
  - `CONFIG_SCHEDSTATS` is irrelevant here: its extra fields also need the runtime sysctl.
  - `pcount` counts times scheduled in, not EEVDF slices.
- SteamOS config has `SCHED_INFO=y`, `SCHEDSTATS=y`, `NTSYNC=m` [checked] (PKGBUILDs-mirror `jupiter-3.9/linux-neptune-616/config:12049-12050,2823`, `_tag=6.16.12-valve28`).
  - Note: the mirror's `jupiter-rel` branch is stale (5.13), so don't use it.
- fdinfo exposes per-process GPU time on Van Gogh [checked]: `drm-engine-%s` (`amdgpu_fdinfo.c:121`).
  - But the value is Σ(finished − scheduled) per job (`amdgpu_ctx.c:170-188`). "Scheduled" means pushed to the hardware ring.
  - With up to 4 jobs in flight (`grub-steamos:21`, jupiter-hw-support `jupiter-3.8-20260807.1`), the sum can exceed wall time. Treat it as "queue non-empty", not as "GPU busy".
  - Use `gpu_metrics.average_gfx_activity` (`vangogh_ppt.c:1679`) for busy time.
  - Reading fdinfo takes `mgr->lock` (`amdgpu_ctx.c:970`), the same mutex the CS ioctl takes in `amdgpu_ctx_get` (`:740`). The contention is small but real.
- **S0 and anti-cheat** [checked mechanism; EAC policy could not verify]:
  - fdinfo needs `PTRACE_MODE_READ_FSCREDS` (`fs/proc/fd.c:94`).
  - Yama gates only attach mode (`yama_lsm.c:355`).
  - A non-dumpable target refuses non-CAP_SYS_PTRACE readers (`kernel/ptrace.c:340-344`). So run the sampler as root.
  - Procfs reads are invisible to an in-process anti-cheat.
  - Precedent: Valve's own mangoapp already reads the game pid's fdinfo out of process (MangoHud `src/amdgpu.cpp:298-306`).
- `VKD3D_QUEUE_PROFILE` [checked]:
  - Real, and compiled into every build: `queue_timeline.c` is unconditional at `libs/vkd3d/meson.build:94`, init is at `device.c:10619`, env var at `queue_timeline.c:33`.
  - "Undocumented" is [contradicted]: it is in `CHANGELOG.md:391`, though not in the README.
  - It writes from inside the game process and perturbs exactly the CPU-bound frames being measured. Keep it off EAC titles.

**Budget redo.** The sampler costs more than claimed: 40 threads × 2 files × 50 Hz with open/close is about 4k reads/s × ~10 µs ≈ 0.5% of the APU (est.). Rescue: keep the fds open and use pread, sample deltas at 10 Hz, and run the sampler under SCHED_IDLE.

**2×2 flaw.** Pinning the GPU at 1600 MHz forces GPU power, which steals CPU clock at 15 W. That shows up as false "GPU elasticity". Use the arms auto vs pinned 1100, and log `current_coreclk`.

**Legal.** Wukong is a poor control: its EULA §8.3 risk covers the clock-changing arms. Swap it for a GPU-bound scene in a game without that clause.

**Verdict:** SURVIVES WITH CHANGES (gfx_activity for busy time, root sampler, 10 Hz, auto-vs-pin arm).

**Experiment (3 days).**
- Controls: Civ VI (CPU-bound) and Stalker 2 at 800p Epic outside settlements (GPU-bound). 10 runs each; sampler on/off A/B.
- **Pass:** ≥9/10 correct classifications, and the sampler costs ≤0.5% median fps.
- **Kill:** ≥2/10 misclassified, or a cost above 1%.
- Owner: launch the scenes, and toggle Manual GPU Clock when the runner prompts.

## 2. SM2 GPU slack → CPU watts
**Facts**
- steamos-manager writes `s 0 X`, `s 1 X`, `c` (`gpu.rs:363-392`, v26.4.1). Min equals max, so this is a **pin** [contradicted: "ceiling"].
- Separate `TDC_VDD` and `TDC_GFX` limits exist (`vangogh_ppt.c:218,220`). The power shift is therefore physically plausible.

**Budget.**
- If GPU busy is about 60% at auto/1600, a 1100 pin raises it to about 87%. A 900 pin becomes GPU-bound, so only about 1100 is viable.
- 0 / +3 / +8% (est.). This is the same watt pool as Round 2's guided/EPP levers; count only the increment.

**Failure modes.** Auto DPM may already drop GFX clocks in CPU-bound frames, which would make the headroom zero. Explosions also go GPU-bound under a pin.

**Verdict:** SURVIVES WITH CHANGES. Add a kill if `current_gfxclk` at auto is already ≤1200 MHz in CPU-bound samples. Test only auto vs 1100 vs 1000.

**Experiment.** W3's 1-week plan, with these thresholds:
- **Pass:** CPU clock +≥5%, median −≥4%, and p99 no worse.
- **Kill:** throttle bits set in <20% of CPU-bound samples.

## 3. Syscall-tax trim
**Facts**
- No `mitigations=` on the command line [checked] (`grub-steamos:16-27`).
- `spectre_v2_user=off` does drop the retbleed-forced STIBP [checked]. `CMD_NONE` returns early, and the force applies only if STIBP is not NONE (`bugs.c:1734-1736,1817-1823`).
- **Persistence** [contradicted: "should persist"]:
  - The keep-list says "all changes made in /etc will be lost" except listed files, and `/etc/default/grub` is not listed (`atomic-update-keep.conf.in:1-4`).
  - Surviving an update needs a drop-in in `/etc/atomic-update.conf.d/` (`common.mk:130`).
  - For a bench this is a feature: updates auto-revert the profile.
- ntsync default [checked]:
  - Proton 11's wineserver opens `/dev/ntsync` unless `PROTON_NO_NTSYNC` is set, then switches fsync off (`server/inproc_sync.c:48-66`, proton_11.0).
  - The header is vendored (`ntsync_tmp.h:57`), so ntsync is compiled in. The 3.8 tag preloads the module (bb08ada is an ancestor of `jupiter-3.8-20260721.1`).
  - The variable name `PROTON_NO_NTSYNC` is correct (`README.md:326`).
  - Valve defaults SM2 to Proton Experimental, which is 11-based (GOL, 1 Sep 2026).
  - "fsync skips the syscall uncontended" is partly [contradicted]: SetEvent 0→1 always calls `futex_wake` (`fsync.c:549-550`).

**Security cost.**
- `spectre_v2_user=off` (est.):
  - It removes cross-SMT branch-injection protection between user processes.
  - On a single-uid device, same-uid native code can already read Steam's files, so the marginal loss is low.
  - It also weakens retbleed ("SMT vulnerable").
- `mitigations=off` (est.): it opens kernel memory to any unprivileged code. That includes a compromised steamwebhelper renderer, the Desktop-mode browser, and root Decky plugins. Bench-only, never a shipped profile.

**Budget.** Wine NT calls mostly stay in user space. Assume ~10–20k real syscalls/s × ~1 µs: 0 / +1 / +4% (est.).

**Verdict:** SURVIVES WITH CHANGES, as bench-only research. Only the `spectre_v2_user=off` arm is ever recommendable.

**Experiment (1 week).**
- Gate: critical-thread stime share ≥5% (from Idea 1); otherwise kill.
- **Pass:** the `spectre_v2_user=off` arm gives −3% median or −5% p99 with the CI excluding 0.
- **Kill:** <2% everywhere.
- Owner: reboot when the runner prompts.

## 4. CPU column for the price list
**Facts**
- Stalker 2 v2.0 runs UE 5.5.4, and Zalissya is "highly CPU-limited" [checked] ([OC3D, 21 Aug 2026](https://overclock3d.net/reviews/software/stalker-2-patch-2-0-tested-huge-improvements/)).
- `a.URO.ForceAnimRate` exists [checked] ([UE-39021](https://issues.unrealengine.com/issue/UE-39021)). Whether it applies in a 5.5.4 Shipping build: [could not verify]. Epic's source is private.
- Wilds CPU tab [checked]: "Added a CPU tab to the Options menu… settings related to CPU load", 28 Jan 2026, v1.040.03.01 ([RPG Site](https://www.rpgsite.net/news/19445-monster-hunter-wilds-steam-dlc-check-performance-issues-fix-patch-notes-pc)). Its contents: [could not verify]; no outlet lists them.

**Failure modes.**
- Most of the listed cvars cut render-thread work. The binding thread in settlements may be GameThread or A-Life (est.).
- Pre-v2.0 guides are stale.
- Wilds analysis carries contract risk (Capcom §8.1 bans "analyzing… data").

**Budget.** Stalker 2 settlements: 0 / +5 / +12% (est.).

**Verdict:** SURVIVES WITH CHANGES. Stalker 2 only, run Idea 1 first to name the critical thread, verify every cvar in the log, and merge into E's table.

**Experiment.** W3's thresholds plus a log check per cvar.

## 5. "Proton says handheld"
**Facts**
- The stub is real in Wine master and every Proton branch [checked]: `rtl.c:1645-1652`; proton_10.0 `:1094-1100`; proton_11.0 `:1649-1655`; experimental and bleeding-edge `:1654-1660`.
- 0x2E is `DEVICEFAMILYDEVICEFORM_GAMING_HANDHELD`, and it is Microsoft's stated method [checked] (`IsDeviceHandheld.cpp:9-18`; [guidance](https://devdocs.xbox.com/build/gdk-and-engines/handheld/handheld-guidance.md)). Wine's `winnt.h` stops at 0x21 (`:6341`).
- **Swapped table** [checked]: Microsoft lists Ally (Z2 A) = 150E and Ally X (Z2 Extreme) = 163F. pci.ids says `150e Strix`, `163f VanGogh`, and the Z2 A is the RDNA 2 part.
  - A copying game would see the LCD Deck (and the real Ally) as an Ally X.
  - The OLED (0x1435) appears in no table at all.
- **Who calls it?** [could not verify the count].
  - The stub was added for the WebView2 installer (Wine bug 56259, MR 4973), so grepping the FIXME will catch launchers.
  - Microsoft's 40 "hand-crafted" Ally profiles are applied by system software ([Wccftech](https://wccftech.com/rog-xbox-ally-x-update-adds-hand-crafted-default-game-profiles-for-40-games//amp/)).
  - DOOM: TDA autodetects handhelds *and* lists "Steam Deck: 720p @ ~30FPS" and is Verified ([GOL](https://www.gamingonlinux.com/2025/10/doom-the-dark-ages-gets-a-major-performance-upgrade-for-handhelds-now-steam-deck-verified/page=1/)).
  - So "no handheld path can ever run on a Deck" is [contradicted] in practice.

**Would Valve take it?** Plausible as a per-appid compat entry (`default_compat_config()`, `proton:1288`), but only with a named game that benefits.

**Risks.** An Ally X preset via 163F (DOOM's Ally X tier targets 1080p60). Anti-cheat is neutral if the change ships in stock Proton.

**Budget.** −10 / 0 / +3%.

**Verdict:** SURVIVES only as a 1-day census.

**Experiment.**
- Run `PROTON_LOG=1` on 15 titles.
- On non-AC titles, attribute each caller with relay tracing limited by `RelayInclude=ntdll.RtlGetDeviceFamilyInfoEnum`, mapping the `ret=` address to a module.
- **Kill** if fewer than 2 calls come from game modules.

## 6. Capcom Switch 2 tier
**Facts**
- Release date 4 Dec 2026 [checked] ([Siliconera](https://www.siliconera.com/monster-hunter-wilds-switch-2-release-date-updated/)).
- "Stable performance" is the author's impression of Direct footage, not a measurement.
- Handheld specs [checked] ([club386](https://www.club386.com/nintendo-finally-reveals-switch-2-specs-including-docked-and-handheld-clock-speeds/), via DF): 6 game cores, A78C at 1.1 GHz with boost up to 1.7 GHz in some scenarios, 1.71 TF, 68 GB/s.
- Wilds became Verified on 21 Aug 2026 at "30 FPS and above most of the time" ([SDHQ](https://steamdeckhq.com/news/monster-hunter-wilds-gets-steam-deck-verified/)). The 30-fps floor is therefore mostly met already; what remains is open-world drops.

**CPU arithmetic.** 0.4× is a sound central figure (est.). The range is 0.3–0.55×: IPC parity ±20%, an SMT gain of 1.1–1.25, and a Deck at 3.0–3.5 GHz.
- The step "13–15 ms of Deck time" ignores PC-side API cost. NVN is thin; D3D12 → vkd3d → RADV is not.
- W3 and W5 contradict each other: W3 says the plains are GPU-bound, W5 says CPU-bound.

**Realism (est.).**
- Capcom replies to individual packets <5% of the time. Valve's Deck team: 10–20%.
- Capcom acts on mass Steam-review pressure: the January 2026 patch followed that.

**Verdict:** SURVIVES WITH CHANGES. Parked until DF's Switch 2 analysis, gated on W5's 360p-vs-800p test, and aimed at Valve first.

## 7. Evidence lab
**Facts**
- vkd3d-proton since 2025: 1,330 commits, 965 of them by Arntzen (73%).
- Only 1 says "reported by" (9645932, "Reported by users to help CPU perf a bit") and 4 say "Fixes #" [checked, local git]. So "entries landed" can't be attributed to anyone.
- Acceptance rates: [could not verify]. The issue-search API is blocked here.
- Maintainer hostility to AI-generated work is documented: lsfg-vk relicensed over "AI slop forks" (Round 2).

**Verdict:** a sound low-maintenance side channel, not a product. Realistically 1–3 acted-on items per year (est.). SURVIVES WITH CHANGES: measure the KPI as "maintainer acted", keep W5's kill gate, and lead with human-verified bench data.

## 8. CFS/EEVDF report
**Facts**
- The file is `steamos-cfs-debugfs-settings.in` on 3.8 (`jupiter-3.8-20260721.1`). `holo-…` exists only on main (`jupiter-20260930.1`). Lines 33-37 make 5 writes, and the log string is "Not all CFS debugfs settings applied successfuly" [checked].
- Three of the files are absent on 6.16, but `migration_cost_ns` and `nr_migrate` exist (`debug.c:510-518`) [checked]. So "Only base_slice_ns exists" is [contradicted].
- `update_sysctl()` recomputes only `base_slice` (`fair.c:215-223`), and it is called from `rq_online/offline_fair` (`:12963-12975`). "The rest revert on hotplug" is [contradicted]: Valve's migration_cost and nr_migrate values persist.
- Recipe [checked]: a `tunable_scaling` write sets the mode and then calls `sched_update_scaling()` (`debug.c:190-191`). That re-normalizes from the current value (`fair.c:1000-1010`). Writing 1 (log scaling) works too and keeps CPU-count scaling.
- CFS era [checked]: these were plain u32 files in v6.1 (`debug.c:311-314`), and `update_sysctl` reset all three (`fair.c:263-268`). Before 5.13 they were sysctls with `sched_proc_update_handler` (v5.12 `sysctl.c:1664-1668`), which persisted.
- Sleep [checked]:
  - s2idle skips CPU offlining (`suspend.c:443-447`).
  - An LCD Deck log shows "PM: suspend entry (deep)" ([drm/amd#3172](https://gitlab.freedesktop.org/drm/amd/-/issues/3172)). OLED: unverified.
  - 3.8 sets `AllowHibernation=no` ("Disabled for 3.8.x cycle"); main sets `=yes`. W5's "hibernate guarantees a hotplug" is [contradicted] for stable.
- No sleep hook re-applies the tunings [checked].

**Fair to Valve? Not yet.** Fix the file name and the "rest revert" line, credit the upstream 5.13 behaviour, and present it as dead writes plus a false error log.

**Verdict:** SURVIVES WITH CHANGES.

**Experiment (day 1).**
- Predictions: `base_slice_ns` = 2800000, `migration_cost_ns` = 50000, `nr_migrate` = 128, and `mem_sleep` shows `[deep]`.
- Write 300000, suspend for 5 minutes, re-read: expect 2800000.
- Write 300000, then `tunable_scaling` 1, suspend: expect 300000.
- **File** only if all of these hold. Then run W5's A/B (**pass** ≥8% p99; **kill** <3%).

---

## SM2 verdict: CONFIRMED for a 30-fps floor in heavy hordes, but the baseline is wrong
- **14 fps is one anecdote.** "I have even seen it go down to 14 FPS!" comes from a 4 Sep 2024 launch review (72 Hz, so an OLED).
  - Lowest settings with FSR UP "would regularly sit at 24 FPS with drops down to 19" ([SDHQ](https://steamdeckhq.com/game-reviews/warhammer-40000-space-marine-2/)).
  - After Patch 5.0 the game "can hit 30 FPS and above at times" ([SDHQ, Dec 2024](https://steamdeckhq.com/?p=26917)).
- **Scaling estimate.** PS5 drops "below 40 fps" in heavy hordes and is CPU-limited (DF via multiplayer.it). Scaling that to the Deck gives about 18 fps (est.) in the worst hordes, so 30 fps needs about 1.65×.
- **The S0/S1 stack I credit reaches about 1.15× optimistic**, because guided/EPP and the GPU cap share one watt pool.
- **Rescues tried, all failed:**
  - GPU cap;
  - guided/EPP;
  - syscall trim;
  - SMT off (negative);
  - menu settings (already Low under `SteamDeck=1`);
  - a swarm config file (none documented, and the "Mods Detected" risk);
  - a BIOS CPU overclock (not S0, and the 15 W cap binds).
- Only the publisher route remains. Typical combat at 30 fps is unmeasured, not ruled out.

## Verdicts
| Idea | Verdict |
|---|---|
| 1 Triage | SURVIVES WITH CHANGES |
| 2 GPU slack→CPU | SURVIVES WITH CHANGES (small) |
| 3 Syscall trim | SURVIVES WITH CHANGES (bench-only) |
| 4 CPU column | SURVIVES WITH CHANGES (Stalker 2) |
| 5 Proton handheld | Census only; EV≈0 |
| 6 Capcom ask | Parked, gated |
| 7 Evidence lab | Side channel, not product |
| 8 CFS report | SURVIVES WITH CHANGES (fix text) |

## What would change my mind
1. gfx_activity and fdinfo disagree on more than 2 of 10 control runs.
2. `current_gfxclk` at auto is already ≤1200 MHz in CPU-bound samples. That would kill Idea 2.
3. Critical-thread stime share is ≥10%.
4. `a.URO.ForceAnimRate` is shown applied in a Stalker 2 Shipping log.
5. At least 2 of 10 titles call the API from a game module.
6. Capcom or Valve sends a written reply.
7. A maintainer acts on 1 of 3 packets within 60 days.
8. `migration_cost_ns` reads 50000 after suspend. That confirms my correction; a revert would refute it.

**Key facts to keep:**
- Manual GPU Clock is a pin.
- `/etc` edits need an `/etc/atomic-update.conf.d` drop-in to survive updates.
- 3.8 has hibernation off.
- `drm-engine-gfx` is ring occupancy.
- mangoapp reads the game's fdinfo out of process.
- Wilds has been Verified since 21 Aug 2026.
- Microsoft's Ally/Ally X GPU IDs are swapped.

Source copies: `/tmp/claude-0/-home-claude/bafac712-f1ea-5f41-b2ba-592b27d3cd05/scratchpad/r3sk/`
