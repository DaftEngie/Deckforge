# DeckForge launch flow (design draft)

Status: **DRAFT for Fede's review**, 2026-10-11. No code yet.
This document proposes; it does not change `CLAUDE.md`, `docs/QUALITY_TARGET.md` or the
safety spec. Decisions it depends on are listed in
[STRATEGY_OPTIONS.md](STRATEGY_OPTIONS.md) as D1–D8. The evidence and its sources are
summarized in [the overnight report](../research/2026-10-11-overnight/REPORT.md).

Evidence: the overnight notes in `docs/research/2026-10-11-overnight/`, cited as
[platform §3], [levers: RE Engine], [shaders Q1], [latency §5], [upscaling Q7],
[alternatives §4], [prior art §5]. The notes carry the source links. Anything marked
**UNVERIFIED** must be checked on the Deck (or on a fixture copied from it) before code
depends on it.

## In one paragraph

DeckForge is a measure → search → apply loop. It first **reads** (never writes) the
Steam install and builds a "game card" for each game: engine, graphics API, upscalers
shipped, anti-cheat, where settings live, and which levers are safe. It then measures the
game while it runs, sorts the bottleneck into GPU, CPU, power or stutter, tries a small
set of levers with real runs on the Deck, and applies the winner through the safety
module. It never claims a result it did not measure. If no setting reaches a native
frame-rate lock, it says so and offers the next-best option: a lower lock, or cloud.

## The five stages

| # | Stage | What happens | Writes | Phase |
|---|---|---|---|---|
| 1 | Discover | Read-only scan → one game card per game | Nothing outside `~/deckforge` | 1 |
| 2 | Baseline | Game runs through the DeckForge launcher; frame times, power and versions logged | `~/deckforge/logs` only | 1–2 |
| 3 | Diagnose | Bottleneck class, stutter class; latency by phone camera (manual) | Nothing | 2 |
| 4 | Search | Candidate profiles from the lever map, run on the Deck, scored | `~/deckforge` only; game files only through `deckforge.safety` | 2–3 |
| 5 | Apply and watch | Winning profile applied; every launch checks for drift and game updates | Only through `deckforge.safety` | 1 (hand-made profiles), 3 (searched) |

## Stage 1 — Discover (read-only)

| What it looks for | Where | Why |
|---|---|---|
| Steam libraries (internal + SD card) | `~/.local/share/Steam/steamapps/libraryfolders.vdf` (path commonly known; **UNVERIFIED** in sources [platform §4]) | Find every install and every Proton prefix |
| Installed games and **build ID** | `steamapps/appmanifest_<appid>.acf` (`buildid`, `installdir`; field names **UNVERIFIED**) | Every profile and measurement is keyed to the build |
| Proton version per game | Steam `config/config.vdf` (compat tool mapping; **UNVERIFIED**) | Record only. Never switch automatically: a user reported a Denuvo lockout (24 h) after a Proton change [prior art §3] |
| Settings files in the prefix (Class P) | `steamapps/compatdata/<appid>/pfx/drive_c/users/steamuser/{AppData,Documents}`; Unity PlayerPrefs in `pfx/user.reg` [platform §4; levers: Unity] | Safest files to edit: Steam "verify" does not touch them |
| Settings files in the install folder (Class I) | `steamapps/common/<installdir>/` — e.g. **Wilds' `config.ini` lives here** [levers: RE Engine] | Verify and updates can revert them (for Wilds' `config.ini` this is untested, E15); anti-tamper may check them |
| Engine | File signatures: Unreal (`*/Binaries/Win64/*-Shipping.exe`), Unity (`UnityPlayer.dll`, `*_Data/boot.config`), RE Engine (`re_chunk_000.pak` + `config.ini`; the `.pak` name is **UNVERIFIED**, from general knowledge) | Chooses the lever template |
| Graphics API | A separate, unmeasured discovery run with translation-layer logging switched on (Proton turns DXVK and vkd3d-proton logs off by default [shaders Q5]); never on a measured run. Log paths are pointed at `~/deckforge/logs` (`DXVK_LOG_PATH` and the Proton and vkd3d-proton equivalents), so nothing lands in the game folder | D3D11 games get DXVK knobs; D3D12 games get vkd3d-proton knobs. (Wilds is believed to be D3D12-only; **UNVERIFIED** in the notes) |
| Upscalers shipped | DLLs in the install folder (DLSS, FSR 3.1, XeSS) | FSR 4 upgrade paths need FSR 3.1 or DLSS inputs [upscaling Q1, Q4] |
| Anti-cheat | `EasyAntiCheat*/`, `BattlEye/`, `GameGuard/` folders, plus a curated denylist (Helldivers 2, Space Marine 2) | Forces Tier S only. Also warns loudly if injector files are found in an anti-cheat game's folder |
| Steam Cloud | `userdata/<id>/<appid>/` cloud records (exact file **UNVERIFIED** [platform §4]) | A cloud-synced settings file can silently undo a change (safety spec Q7) |
| Shader cache | `steamapps/shadercache/<appid>/` present, and its size [shaders Q1] | Is Steam's pre-caching active for this game? |
| Tools the player installed | Decky Framegen (`~/fgmod`), lsfg-vk, OptiScaler files in the game folder [platform §5] | Orchestrate them; never bundle them (lsfg-vk is CC BY-NC-ND [prior art §3]) |
| Device and stack | Model (Galileo = OLED), SteamOS, kernel, Mesa, Proton build | Tag every measurement; never mix OLED and LCD data [platform §1] |

The game card is a small JSON file in `~/deckforge/cards/<appid>.json`, for example:

```json
{"appid": 2246340, "name": "Monster Hunter Wilds", "build": "<from manifest>",
 "engine": "RE Engine", "api": "d3d12", "anticheat": "none known",
 "settings_files": [{"path": "<install>/config.ini", "class": "I"}],
 "upscalers_shipped": ["DLSS", "FSR", "XeSS"], "tiers_allowed": ["S", "I"],
 "levers": ["menu", "launch_env", "qam", "optiscaler?", "reframework?"]}
```

(The Wilds upscaler list above is an example shape, not a verified inventory.)

**Finding that changes the safety spec.** Wilds keeps its settings file in the install
folder. Under safety-spec Q1's recommended default ("never write `steamapps/common`"),
DeckForge could not edit Wilds' settings at all; Tier S for Wilds would shrink to
"recommend menu settings, the player sets them". See decision **D3**.

## Stage 2 — Baseline: the launcher

**One launch option per game, pasted once.** The player sets the game's launch option
to `~/deckforge/bin/df-run %command%`. This is the pattern Decky Framegen
(`~/fgmod/fgmod %command%`) and lsfg-vk already use [platform §5]. From then on,
DeckForge changes that game's environment variables by editing **its own** profile file
in `~/deckforge/profiles/`. It never edits Steam's `localconfig.vdf`, which Steam owns
and rewrites (safety spec Q2). See decision **D4**.

If the game already has a launch option, DeckForge shows it and records it first:
- Plain variables such as `FOO=1 %command%` move into the DeckForge profile.
- Other wrappers chain after `df-run`, for example
  `~/deckforge/bin/df-run ~/fgmod/fgmod %command%`.
- Exception: for anti-cheat games, `df-run` refuses to chain known injector wrappers
  (`~/fgmod/fgmod`, `~/lsfg`). Anything they add happens after `df-run` hands over, out
  of its control. DeckForge records them and asks the player instead.

Nothing the player had is silently dropped.

What `df-run` does, in order:

1. Read `~/deckforge/profiles/<appid>.json`. No profile → launch the game unchanged.
2. Check the game's build ID and the hashes of files DeckForge manages. On a mismatch,
   mark the profile **STALE**, launch with no file-dependent settings, and tell the
   player next time DeckForge opens.
3. Build the environment from the profile: `DXVK_CONFIG`, `VKD3D_CONFIG` (appended to,
   never replaced, because Proton adds to it too [shaders Q5]), `RADV_*`, and drirc
   options as variables. On measured runs it also switches MangoHud on (`MANGOHUD=1` plus
   `MANGOHUD_CONFIGFILE`; the switch name is from general knowledge, **UNVERIFIED**),
   except in anti-cheat games (see below). A run counts as "measured" only when the bench
   runner has written a one-shot run ticket for that App ID into
   `~/deckforge/runs/`. `df-run` consumes the ticket, so normal play is never mistaken
   for a measured run.
4. For anti-cheat games, strip anything Tier I (for example DLL overrides or an
   injected layer's enable variable), whatever the profile says. Stripping variables may
   not be enough: lsfg-vk 2.0 can switch itself on by App ID in its own config
   [prior art §2]. Discover therefore also checks that config, and warns if an
   anti-cheat game is listed there.
5. Replace itself with the game process, using an argument list and no shell (R11).

Design rules for `df-run`:

- **Fail open for play, fail closed for measurement.**
  - In normal play, a problem with DeckForge's own files makes `df-run` log the
    traceback with `logging.exception` to `~/deckforge/logs/df-run.log`, write a status
    file the UI shows, and launch the game with the **original arguments and the
    untouched inherited environment**. Its own log and status-file writes are
    best-effort: if they fail (for example, on a full disk), the game still launches.
  - On a **measured run**, the same problem aborts the run and records it as FAILED.
    A fallback launch would log frame times against a profile that was never applied:
    a wrong "done" (R1).
- **What fail-open cannot cover:** a missing or too-old system Python after a SteamOS
  update, an import error, or a lost execute bit. The recovery is to delete the launch
  option, and the UI and docs must say so. Before Milestone 1 closes, confirm `df-run`
  runs on the system Python of the oldest SteamOS version DeckForge supports (version
  **UNVERIFIED**).
- **Lint and review gates:**
  - The logic lives in a `.py` module under `src/`, so `ruff` and the tamper check apply.
    `bin/df-run` is a two-line shell stub that only `exec`s that module with `"$@"`. It
    must contain no Python logic: `ruff check .` skips files without a `.py` extension.
  - The project's lint flags every `os.exec*` call (ruff S606), and adding `# noqa` is
    blocked. That one module therefore needs a per-file ignore in `pyproject.toml`, a
    protected file only Fede can change (decision **D4**).
  - The top-level handler touches R12 and needs Fede's and the verifier's sign-off.
- **Off switch:** delete the launch option, empty the profile, or set `DECKFORGE_OFF=1`.
- **Small and boring:** standard-library Python only.

**MangoHud and anti-cheat.** MangoHud also loads into the game as a Vulkan layer, the
same reason lsfg-vk counts as Tier I. No MangoHud ban was found, but "not found" is not
proof of safety [prior art §3]. Until Fede decides (**D8**), anti-cheat games (Space
Marine 2, Helldivers 2) get no MangoHud on measured runs. Their frame times must come
from outside the game process. Whether Steam's own performance overlay (mangoapp) can
log without loading into the game is **UNVERIFIED** (E17).

The baseline to beat is the game's own Deck defaults. Steamworks SDK 1.65 lets
developers ship hardware-specific defaults [platform §6]. Valve's notes frame these
around future devices, and they could change without a new build ID. So the baseline is
re-measured when the build ID changes **and** whenever discover sees the game's
settings file change without DeckForge having written it.

Baseline protocol:
- Game Mode only, since Desktop Mode has known performance gaps [platform §2].
- Plugged in.
- Fixed scene: the Wilds Benchmark app for Wilds. It may not include the game's 2026
  performance patches, so its numbers are checked against an in-game scene before they
  are trusted. A Space Marine 2 scene is still to be chosen.
- The first (cold) run is kept, but only to classify shader stutter (Stage 3). It is
  excluded from frame-time statistics.

## Stage 3 — Diagnose

| Class | Signal (MangoHud + amdgpu `gpu_metrics`) | What it means for the search |
|---|---|---|
| GPU-bound | GPU busy near 100%; frame time moves with resolution | Resolution, upscaler, VRS, GPU-heavy settings |
| CPU-bound | GPU idle gaps; frame time ignores resolution | CPU-side settings (crowds, simulation, draw distance), scheduler. FSR 4 is a pure loss here [upscaling Q7] |
| Power-bound | `power1_average` at the cap, clocks below max, throttle bits set | Move watts from CPU to GPU (SMT off, lower CPU boost) inside the shared 15 W [platform §1, §3] |
| Shader stutter | Spikes over 44 ms (2× budget) that disappear on the warm run | Cache warming, not settings [shaders Q1] |
| Streaming stutter | Spikes that remain on the warm run | Texture and streaming settings; often not fixable |

The stutter metric is frames over 44.4 ms per minute plus the worst frame. Percentile
lows blur a few 200 ms hitches into a small number [shaders Q1].

Latency is measured by phone camera at 240 fps: at least 10–20 trials per configuration,
median and spread reported, and an uncapped baseline in the same session [latency §5].
This is manual in Phases 1–2.

## Stage 4 — Search

### Lever map

| Lever | How it is applied | Tier | Note |
|---|---|---|---|
| In-game settings | Settings file (Class P), or the player sets the menu | S | Usually the largest effect |
| Internal resolution + upscaler choice | In-game | S | Grid {400, 470, 533, 600, 640, 800}p [upscaling Q7] |
| FSR 4 INT8 via OptiScaler / Decky Framegen | DLLs in the game folder | I | ~4.5 ms at 800p (one user's figure; ~6 ms plausible). Must be measured (E9). Pin versions and check hashes [upscaling Q4] |
| FSR 4 via the Proton-CachyOS upgrade (FSR 3.1 games) | Non-stock Proton (`FSR4_UPGRADE`; `PROTON_FSR4_UPGRADE` now only requests a version, see REPORT.md) | I until proven otherwise | A Proton change reportedly can trigger a Denuvo lockout; check the game's DRM first |
| Sharpening | Steam/gamescope filter (S); OptiScaler RCAS (I) | S/I | Start at RCAS 0.2–0.4 or gamescope 2–5 [upscaling Q6] |
| Texture LOD (mip) bias | `DXVK_CONFIG` `d3d11.samplerLodBias` (D3D9/11); OptiScaler override | S/I | A negative bias sharpens but costs bandwidth |
| Anisotropic filtering | `RADV_TEX_ANISO` or DXVK `samplerAnisotropy` | S | Quality up, bandwidth cost |
| Variable rate shading | `RADV_FORCE_VRS` / VRS config file (built by Valve for the Deck's GPU) | S | Needs an image-quality check (compendium E2) |
| Render-queue depth | `dxgi.maxFrameLatency=1` (D3D9/10/11 via DXVK) | S | Latency lever; no documented equivalent for D3D12 [latency §1] |
| Frame cap + refresh | Steam per-game profile (Quick Access Menu) | S | 45@90 Hz, 40@80 Hz or 30@90 Hz. Always set the two together [platform §2] |
| TDP, GPU clock, governor, scheduler (LAVD) | `steamosctl` (Valve's steamos-manager) | S | Steam's per-game profile may override at launch [platform §3] → Phase 1: recommend; the player sets it |
| SMT off | sysfs, root needed; `steamosctl` has no SMT command [platform §3] | S | Deferred: needs a root decision from Fede, not just an experiment |
| CPU boost | `steamosctl` | S | Whether it works without a password is E16 |
| Shader compiler threads | `dxvk.numCompilerThreads` | S | Hitch-severity lever; untested [shaders Q1] |
| Unreal ini CVars | `Saved/Config/Windows/Engine.ini` (Class P) | S | Small curated set; every CVar unverified until measured; tweak packs are placebo by default [levers: Unreal] |
| Unity PlayerPrefs | Prefix `user.reg` (Class P) | S | Encoding **UNVERIFIED** [levers: Unity] |
| REFramework scripts (Wilds) | Injected mod | I | Strongest below-menu Wilds levers (GI, fog, LOD), with visible costs [levers: RE Engine] |
| Reflex-style limiter (low_latency_layer) | Implicit Vulkan layer | I | Conflicts with the FSR 4 GPU spoof [latency §2] |
| Frame generation (lsfg-vk, FSR 3.1 FG) | Tools the player installed | Separate track; lsfg-vk is Tier I (it loads into the game as a Vulkan layer) | Never counted as native; shown as "motion smoothing" with its measured latency cost |

### How candidates are scored

1. **Hard constraints:** median frame time within the target lock, p99 within that game's
   guard, stutter count within limit and, once measured, latency no worse than the
   native best + 5 ms [latency §6].
2. **Then maximize image quality:** FLIP to screen candidates, a temporal metric
   (ColorVideoVDP, which runs on CPU, slowly) to promote them, and Fede's blind A/B on
   the Deck as the final call.
3. **Shader-affecting knobs** (VRS, wave size, shader overrides, some drirc options) miss
   Steam's precompiled cache. Score them on the warm second run and report the
   first-run cost separately [shaders Q1].
4. **Prune using the diagnosis:** for example, skip FSR 4 for CPU-bound games. A night
   allows roughly 100 runs of 2–3 minutes each (estimate).
5. **Output a small set of profiles, not one "best":** for example "45 locked, best
   quality", "45 locked, best battery", "40@80 best quality" [prior art §5].

### Verdict per game

`NATIVE-45 MET` · `BEST NATIVE LOCK = 40@80` or `30@90` · `ROUTE TO CLOUD` (if the game is
on GeForce NOW and local play misses the floor Fede sets in D1) · `BLOCKED: <reason>`.
Each verdict ships with its evidence: MangoHud CSVs, screenshots or clips, versions.

## Stage 5 — Apply and watch

- **Game files:** only through `deckforge.safety` (preview, backup, atomic write,
  manifest, byte-identical restore).
- **Environment variables:** only in DeckForge's own profile file, read by `df-run`.
- **Quick Access Menu settings** (TDP, fps cap, refresh): Phase 1 prints them for the
  player to set. Reading them back after launch is **UNVERIFIED** (E16).
- **Drift:** on each launch `df-run` compares hashes of the files it manages. If the
  game's menu, a patch, a verify or Steam Cloud changed a file, it does **not** silently
  re-apply. It marks the profile STALE and asks. A new build ID makes the profile STALE
  until it is re-measured; 2025 Wilds community configs became harmful after the 2026
  patches [levers: RE Engine, Risks].
- **Never** makes files read-only. That freezes the game's own menu [levers: Risks].

## How DeckForge handles shaders

What it does:

1. Keeps Steam's shader pre-caching on and lets it finish.
2. Measures every configuration cold and warm, and calls a spike "shader stutter" only
   if the warm run removes it.
3. Avoids knobs that invalidate Steam's precompiled cache unless their warm-run gain
   pays for a one-time compile.
4. Tests capping DXVK compiler threads for hitch severity (D3D11 games).
5. Uses variable rate shading as the "shade fewer pixels" lever, with no shader edits.

What it does **not** do in Phases 1–3:

- Rewrite shaders. The only official replacement hook is a debug feature of vkd3d-proton
  (D3D12) that is tied to the exact translator version. D3D11 would need DeckForge's own
  Vulkan layer. Generic SPIR-V optimizers mostly repeat what Mesa's compiler already does.
  Real gains need risky edits (lower precision, fewer samples) that must be re-checked on
  every game patch [shaders Q2].
- Run `fossilize-replay` on Steam's caches, or delete caches. Both touch the real Steam
  install (R7).

Shader rewriting stays a research track. It is justified only if compendium E1 (a GPU
profile of Wilds) finds one pass that dominates the frame, and E7 (one hand edit) shows
the gain is worth the upkeep.

## Latency budget

- **Rule:** "native feel" means the median camera-measured latency is no worse than the
  same game at native frame rate with its best non-frame-gen settings, plus 5 ms (camera
  noise). Anything adding 20 ms or more (about one 45 fps frame) is "not native". Frame
  gen is always reported separately, and never with a base under 30 fps [latency §6].
- **Expected chain at native 45 fps on the OLED:** roughly 55–90 ms (estimate). Measured
  OLED baselines are 51–65 ms in games running faster than 45 fps [latency §6].
- **Biggest levers:**
  1. Limiter choice. In 2022 the Steam limiter added 44–87 ms over uncapped; an in-game
     cap added about nothing. That predates the OLED and current SteamOS, so it is
     **UNVERIFIED today** (E8).
  2. Render-queue depth: `maxFrameLatency=1`, or a Reflex-style limiter (Tier I).
  3. 90 Hz refresh.
- **Limiter policy until E8 is run:** use the Steam per-game cap (exact 2:1 pacing at
  45@90) and label the result "latency not measured". E8 then decides the default.

## Getting more out of the hardware

- **One shared 15 W budget.** In GPU-bound games, watts saved on the CPU can go to the
  GPU, hence the "power-bound" class and the CPU-side knobs [platform §1, §3].
- **45@90 Hz is the natural lock:** each frame shows on exactly two refreshes.
  40 fps needs 80 Hz; 30 fps sits on 90 Hz with three refreshes per frame.
- **GPU clock tops out at 1600 MHz** on the OLED without risky hacks. A BIOS undervolt
  (Valve firmware) mostly saves power at the same fps [alternatives §4]. It stays a
  manual step for the player, never automated: stable values vary by unit, some units
  freeze, and per the notes a CMOS reset no longer clears it.
- **Scheduler:** A/B test LAVD in CPU-bound scenes. One reversible `steamosctl` call.
- **Bandwidth:** if E1 shows bandwidth-bound passes, try positive LOD bias or lower
  texture settings first.
- **Realistic total from the knobs DeckForge would use: about 0–4%**
  [alternatives §4, §6]. The 5–9% figures need overclocking, which is rejected. Settings
  and reconstruction move far more.

## Where things run

- **Mac:** agents, analysis, image-quality metrics. ColorVideoVDP runs on CPU (slow);
  whether CGVQM runs without CUDA is **UNVERIFIED**.
- **Deck:** `df-run`, logging, and later the bench runner. No agent or LLM runs on the
  Deck during measurement (ARCHITECTURE.md).

## Packages (adds one to ARCHITECTURE.md)

| Package | Purpose | Phase |
|---|---|---|
| `deckforge.discover` (**new**) | Read-only scan → game cards | 1 |
| `deckforge.safety` | Preview, backup, atomic write, restore | 1 |
| `deckforge.profiles` + `df-run` | Profile files and the launcher | 1 |
| `deckforge.diagnose` | MangoHud and `gpu_metrics` parsing, bottleneck class, stutter metric | 2 |
| `bench/` | Deck runner and protocol | 2–3 |
| `deckforge.search` | Candidate generation and scoring | 3 |
| `layer/` | Vulkan layer (timing, then interventions) | 4 |

## Proposed Milestone 1 scope

Discover + safety + `df-run` + hand-made profiles for Wilds and Space Marine 2 + baseline
logging for Wilds. The Space Marine 2 baseline waits on D8 / E17 (measuring it without
an in-process layer). Search comes after the first baselines exist.

Order of specs: `discover` (read-only, so lowest risk; it can be built and tested against
fixtures while Fede answers Q1–Q7), then `safety`, then `df-run`.

## Open items to verify before coding

- Steam file names and fields (library list, manifest, compat tool mapping, cloud
  records).
  - **Fede** copies by hand only `libraryfolders.vdf`, two `.acf` files and the
    `CompatToolMapping` block. No agent connects to the Deck (R7).
  - Steam account IDs and user names are replaced before anything is committed; the
    repo is public, and gitleaks does not catch Steam IDs.
  - Fede reviews the files before they are committed.
- Whether `steamosctl` works as the `deck` user without a password, and whether Steam's
  per-game profile overrides it (E16).
- Unity `user.reg` encoding.
- The current names of shader-cache subfolders.
- Whether the Steam limiter latency penalty still exists (E8).
