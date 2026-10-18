# Shared brief for all DeckForge "clean slate" agents (2026-10-17)

## Goal (deliberately abstract)
Make demanding current-generation games (PS5-era: e.g. Monster Hunter Wilds, Black Myth: Wukong,
Alan Wake 2, Space Marine 2, Stalker 2) play well **natively** on a Steam Deck OLED.

"Play well" =
- a stable frame-time target: ≥30 fps with good 1% lows as the floor; 40–60 presented fps is better;
- image quality approaching the game's High preset *as perceived on the Deck's own 7" 1280×800
  screen at hand-held distance* (scored with perceptual metrics such as FLIP/ColorVideoVDP against a
  max-settings reference, then a blind human A/B);
- input latency comparable to a console game.

## Rules
1. **Be ambitious. Hardware limits are design constraints to engineer around, never a reason to
   stop.** If you hit a wall, say how you would go around, under, or through it.
2. **Native** means the game runs on the Deck. No live streaming of rendered frames from another
   machine. Allowed:
   - work precomputed offline on big computers and shipped to the Deck as data (models, caches,
     baked data);
   - anything running on the Deck itself;
   - local accessories (flag them clearly as "accessory").
3. **Legal and safety lines (non-negotiable):**
   - no circumventing DRM or anti-tamper;
   - no bypassing anti-cheat;
   - no redistributing game code or assets.

   Tiers:
   - **Tier S:** settings, launch options, system/compositor/driver-level changes that load nothing
     into the game. Allowed for anti-cheat games.
   - **Tier I:** in-process layers, mods and hooks. Only for games without anti-cheat, user opt-in.
4. **Start from raw evidence**, not settings guides: GPU frame captures and per-pass timings, chip
   documentation, open-source driver/Proton/Mesa code, perception research, academic papers.
   Use the web to check facts and prior art; cite URLs.
5. Separate **measured** facts from **estimates**. Label estimates "(est.)".

## Raw facts about the device
- **Steam Deck OLED APU ("Sephiroth", 6 nm):**
  - CPU: 4-core/8-thread Zen 2, 2.4–3.5 GHz, 4 MB L3.
  - GPU: RDNA2, 8 CUs at up to 1.6 GHz, ~1.6 TFLOPS FP32 (~3.2 TFLOPS packed FP16). INT8 dot
    products (no matrix/tensor cores), 1 MB L2, no Infinity Cache.
  - Memory: 16 GB LPDDR5-6400 shared by CPU and GPU, ~102 GB/s.
  - Power: APU power limit ~15 W (configurable 3–15 W).
- **Screen:** 7.4" OLED, 1280×800, 45–90 Hz (no VRR), HDR.
- **I/O:** one USB-C port (USB 3.2 Gen 2 + DisplayPort alt mode; no Thunderbolt/USB4 PCIe
  tunneling); microSD; Wi-Fi 6E.
- **Software:** SteamOS 3.8 (Arch-based Linux), gamescope compositor, Proton (Wine + DXVK for
  D3D9–11, vkd3d-proton for D3D12), Mesa RADV Vulkan driver with the ACO shader compiler, open
  source end to end below the game.

## Deliverable from you
Your final message only; do not write files (a hook blocks subagent file writes). Give 5–8 ideas,
ranked by your belief in them. For each:
- **Name + one-line pitch.**
- **Mechanism:** how it works, concretely.
- **Why it could beat the wall:** what physical or perceptual asymmetry it exploits.
- **Budget math:** ms per frame saved or added, memory, power. Show the arithmetic.
- **Specific tools/tech it would use:** existing projects, papers, APIs.
- **Prior art:** who has done something similar, anywhere, and the result (with URLs).
- **Tier** (S or I) and which kinds of games it can apply to.
- **Cheapest falsification experiment:** what to build or measure in ≤2 weeks to prove it wrong,
  and what *measurement* (not opinion) would judge it.
- **Biggest risk.**

Finish with "Unknown unknowns": 3–5 things nobody on a typical team would think to check.
Keep it under ~2,000 words. Quality over quantity: one genuinely new mechanism beats five
restatements of "lower the settings" or "use FSR/frame generation".
