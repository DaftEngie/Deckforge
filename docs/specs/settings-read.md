# Spec: `deckforge.settings`, read a game's graphics settings through engine maps (read-only)

Status: draft, 2026-10-22. This is step 2 of the build order Fede approved: the settings
maps. A later spec, `tune`, writes settings through `deckforge.safety`. This one only
reads.

## Goal (one sentence, user-visible)

For each installed game, DeckForge says which of its graphics settings it understands
and what they are set to now, using one map per engine family, not per game. For games
it doesn't understand it says plainly "no map, change these in the game's menu". It
changes nothing.

## Why maps are per engine family, not per game

Evidence from Fede's 2026-10-21 snapshot:

- **Unreal Engine games** store quality levels in `GameUserSettings.ini`, section
  `[ScalabilityGroups]`, keys `sg.*`.
  - Dragon Ball Sparking! Zero has 11 such keys.
  - REMATCH has only 2 (`sg.ResolutionQuality`, `sg.ShadingQuality`).
  - Epic documents the levels as 0 = Low through 3 = Epic
    ([Scalability Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/scalability-reference-for-unreal-engine)).
  - So one map covers every UE game, and a game simply exposes fewer or more keys.
- **RE Engine games do not share one format.**
  - Wilds uses `config.ini` with a `[Graphics]` section (and `ShaderConvertVersion`).
  - Dragon's Dogma 2 uses `config.ini` with an `[AppOption]` section and different key
    names.
  - So RE Engine needs one map per **format family**, recognized by a fingerprint. A new
    Capcom game reuses a map when its fingerprint matches.
- **Menu names are not needed by the tool.** They appear only as labels in reports.

## Delivery

- One PR, based on `main`.
- Standard library only (R8).
- Maps are JSON data files shipped in the package, so adding an engine family means
  adding a data file, not code.

## Interface

- `load_maps() -> list[dict]`: the built-in maps from `src/deckforge/maps/*.json`, sorted
  by `id`.
- `read_ini(path) -> Ini`:
  - `Ini` is a frozen dataclass with `sections: dict[str, dict[str, str]]` (first value
    wins), `duplicates: list[tuple[str, str]]` and `encoding: str`.
- `match_maps(ini, file_name, maps) -> list[str]`: the ids of maps whose fingerprint
  matches.
- `read_settings(card, maps) -> dict`: the report for one scan card (S5).
- `class SettingsError(Exception)`
- `main(argv=None) -> int`:
  - `--steam-root` (required);
  - `--appid` (int, optional; repeatable);
  - `--json`.
  - It runs `deckforge.discover.scan` and reports every installed game, or only the
    listed appids.

## Map format (S2)

```json
{
  "id": "unreal-scalability",
  "engine": "unreal",
  "label": "Unreal Engine scalability groups",
  "match": {"file_name": "GameUserSettings.ini", "sections": ["ScalabilityGroups"], "keys": []},
  "knobs": [
    {"id": "shadows", "label": "Shadow quality", "section": "ScalabilityGroups",
     "key": "sg.ShadowQuality", "type": "level", "values": ["0", "1", "2", "3"],
     "confidence": "documented", "source": "<url or note>"}
  ]
}
```

- **`match`:**
  - `file_name` is compared case-insensitively with the settings file's base name.
  - Every name in `sections` must exist.
  - Every `[section, key]` pair in `keys` must exist.
- **`type`** is one of:
  - `level`: ordered `values`, lowest first;
  - `percent`: integer with `min`/`max` instead of `values`;
  - `enum`: unordered `values`;
  - `bool`: `values` holds exactly the two spellings seen, false first.
- **`confidence`** is one of:
  - `documented`: a vendor document says so;
  - `matched`: the menu and the file agree, and only one key could be it;
  - `likely`: names and values agree, but this is not proven.
- **`source`** is required and non-empty: a URL, or a note naming the evidence.
- **`values`** may list only values that are documented, or were seen in a real file.
  Never invented ladders.

## Built-in maps (S3)

1. **`unreal-scalability`**
   - Knobs: `sg.ResolutionQuality` (percent, 10–100) and the level keys
     `sg.ViewDistanceQuality`, `sg.AntiAliasingQuality`, `sg.ShadowQuality`,
     `sg.GlobalIlluminationQuality`, `sg.ReflectionQuality`, `sg.PostProcessQuality`,
     `sg.TextureQuality`, `sg.EffectsQuality`, `sg.FoliageQuality` and
     `sg.ShadingQuality`, with values `"0"`–`"3"`.
   - Confidence: `documented` for the four groups Epic's page names (PostProcess,
     Shadow, Texture, Effects). `likely` for the rest, which were seen in Fede's files
     with the same 0–3 range.
2. **`re-graphics-section`** (Wilds format)
   - Fingerprint: `config.ini` with section `Graphics` and key `[Graphics]
     ShaderConvertVersion`.
   - Knobs: every `matched` and `likely` row of `docs/research/wilds-settings-map.md`,
     with only the values seen in Fede's files.
   - `AOSetting` is **excluded**: the menu and the file disagree.
3. **`re-appoption-section`** (Dragon's Dogma 2 format)
   - Fingerprint: `config.ini` with section `AppOption` and key `[AppOption]
     UpscalingAlgorithm`.
   - Knobs: upscaler, upscaling quality, sharpness, frame generation, texture quality,
     shadow quality, frame rate cap and VSync. All are `likely`, with the values seen in
     Fede's file.
   - Source: "inferred from Fede's DD2 config.ini, 2026-10-21; key names match the
     English menu".

## Acceptance criteria

**S1 INI reading.**
- Settings files are read as text with a size cap of 1 MiB. They are checked with
  `lstat` first and must be regular files; links are refused.
- **Encoding:** a UTF-16 BOM means UTF-16, a UTF-8 BOM is stripped, and otherwise the
  file is read as UTF-8. If decoding fails, the file is read as Latin-1 and that is
  recorded in `encoding`.
- **Line handling:**
  - CRLF is accepted.
  - `[name]` starts a section; the name is stored without brackets, case preserved.
  - `key=value` splits at the first `=`, with whitespace stripped around the key and
    value.
  - Lines starting with `;` or `#`, blank lines, and lines with no `=` are ignored.
  - Keys starting with `+`, `-`, `.` or `!` are ignored (UE array syntax).
  - Keys before any section go into section `""`.
- A repeated key within the same section keeps its **first** value and is recorded in
  `duplicates`.
- An oversized file, a non-regular file, or a link → `SettingsError`.

**S2 Map validation.**
- `load_maps()` validates every map against the format above.
- `SettingsError` names the file and the problem for:
  - a missing field;
  - an unknown `type` or `confidence`;
  - an empty `source`;
  - a `level`/`enum`/`bool` knob with no `values`;
  - a `percent` knob without `min` ≤ `max`;
  - duplicate knob ids within a map, or duplicate map ids.

**S3 Built-in maps** exist as described, and pass S2.

**S4 Matching.**
- A map matches a settings file when every fingerprint condition holds.
- Several maps may match; all of them are used, and knob ids from different maps are
  reported separately under their map id.
- No match leaves the file in `unmapped_files`.

**S5 Report per game.** `read_settings(card, maps)` returns
`{"appid", "name", "engine", "anticheat", "maps": [...], "unmapped_files": [...], "issues": [...]}`.
- Each entry in `maps` is `{"map_id", "file", "knobs": [...]}`.
- **Each knob is:** `{"id", "label", "section", "key", "present", "value", "known",
  "confidence"}`.
  - `present` is false when the key is missing, and then `value` is `null`.
  - `known` is true when the value is in `values` (level, enum or bool), or is an
    integer within `min`–`max` (percent).
- **Settings files the card doesn't cover:**
  - files of kind `reg`/`registry` are never opened, and add the issue
    `{"code": "registry_not_read", "path"}`;
  - files that fail S1 add `{"code": "settings_unreadable", "path", "why"}`.
- Cards with `installed: false` are skipped.

**S6 Plain verdict per game.** Each game gets `status`:
- `"mapped"`: at least one map matched and all present knobs are `known`.
- `"mapped_with_unknown_values"`: a present knob has a value the map doesn't know. The
  tool must not touch that knob later.
- `"no_map"`: no settings file matched any map. The text output says "no map: change
  graphics settings in the game's menu".

**S7 Anti-cheat.** Games whose card lists anti-cheat are read and reported like any
other game, with `"anticheat"` copied from the card. The text output adds "settings
files only; DeckForge will never inject into this game". Reading a settings file is
Tier S.

**S8 CLI.**
- Text output: one block per game, showing the name, status, map id and each present
  knob as `label: value` (plus `(?)` when it is not known).
- `--json`: a list of S5 reports plus `status`, sorted by appid, using
  `json.dumps(indent=2, sort_keys=True)` with a trailing newline.
- Exit codes:
  - 0 on success;
  - 2 on `SettingsError` or `DiscoverError`, with one stderr line;
  - other exceptions propagate (R12).
- An `--appid` that isn't installed → an exit-2 error naming it.

**S9 Read-only.**
- Nothing is created, changed or deleted.
- A run over a fixture Steam tree leaves it byte-for-byte unchanged, mtimes included.
- No logging handlers are added.

**S10 Real-data fixtures.** Tests include trimmed copies of the relevant sections of
Fede's real files:
- Wilds `config.ini`, `[Graphics]` and `[Graphics/FSR3]` only;
- DD2 `[AppOption]`;
- Sparking! Zero `[ScalabilityGroups]`;
- REMATCH `[ScalabilityGroups]`.

These contain no personal data. Expected results:
- Wilds → `re-graphics-section`, `mapped`;
- DD2 → `re-appoption-section`, `mapped`;
- both UE files → `unreal-scalability`. REMATCH reports only its two present keys, with
  the other knobs `present: false`.

## Out of scope

- Writing settings, presets and profiles. Those come with `tune` and `deckforge.safety`.
- Cost and visibility ranking of knobs. That comes with `tune` and its measurements.
- Engines other than Unreal and RE Engine.
- Reading settings from a snapshot zip.

## Files and interfaces involved

- New:
  - `src/deckforge/settings.py`;
  - `src/deckforge/maps/{unreal-scalability,re-graphics-section,re-appoption-section}.json`;
  - `tests/test_settings_*.py`.
- Reused: `deckforge.discover.scan`.
- `pyproject.toml` must already include package data. If it doesn't, the maps are found
  by path next to `settings.py`; nothing is added to `pyproject.toml` (R5).

## Safety

- **Reads:** settings files listed on scan cards, plus the scan's own reads.
- **Writes:** none.
- Registry files are never opened.

## End-to-end check Fede will run on the Deck

`cd ~/deckforge-repo && git pull && PYTHONPATH=src python3 -m deckforge.settings --steam-root ~/.local/share/Steam`

Expected:
- Wilds and Dragon's Dogma 2 are `mapped`.
- Sparking! Zero and REMATCH are mapped by `unreal-scalability`.
- The other games are `no_map`, or mapped where they use Unreal.

## Clarifier questions and answers (filled before tests are written)
Reviewed 2026-10-22 by the clarifier. These answers are binding and win over S1–S10.

1. **New type `number`.** A float, with optional `min` and `max`. It is `known` when the
   value parses as a finite float and lies within whichever bounds are given.
   - Wilds `[Graphics/FSR3] Sharpness` and DD2 `UpscalingSharpness` are `number` with no
     bounds.
   - Wilds `ImageQualityRate` is `enum ["1"]`.
2. **Seen values and types.**
   - A knob with only one value seen is `enum`, not `level`.
   - A `bool` lists both spellings of a matching pair: `True`/`False`, `true`/`false` or
     `ON`/`OFF`. The spelling that was not seen is still allowed.
   - `level` is used only where the order is documented: Unreal, values `"0"`–`"4"`.
   - Tests must include a value outside the list, giving `mapped_with_unknown_values`.
3. **One knob per concrete key.** No wildcards. When one menu option covers several
   keys, the label is repeated on each knob (for example "Bloom (enable)" and
   "Bloom (level)").
4. **Wilds fixture.**
   - It includes `[Graphics]`, `[Graphics/FSR3]`, `[Graphics/RayTracing]` and
     `[RenderConfig]`.
   - The map reads only the sections it names. `[RenderConfig]` is never used; the test
     proves it by giving `[RenderConfig]` a different value for a key that also exists
     in `[Graphics]`.
   - The spec records that which section the game honours is **unconfirmed**.
5. **DD2 knobs, exact keys in `[AppOption]`.**

   | Key | Type | Values |
   |---|---|---|
   | `UpscalingAlgorithm` | enum | `FSR3` |
   | `UpscalingQuality` | enum | `Balanced` |
   | `UpscalingSharpness` | number | |
   | `FSR3_FrameGeneraion` (sic) | bool | `OFF`/`ON` |
   | `TextureQuality` | enum | `High` |
   | `ShadowQuality` | enum | `Low` |
   | `FrameRate` | enum | `Max60` |
   | `VSync` | bool | `OFF`/`ON` |

   Source note: "key names only, no menu evidence; Fede's DD2 config.ini 2026-10-21".
6. **Status, checked in this order:**
   1. `unreadable`: there was at least one non-registry settings file, every one failed
      S1, and no map matched.
   2. `no_map`: no settings file matched a map. This includes no settings files at all,
      or only registry files.
   3. `mapped_empty`: maps matched, but zero knobs are present.
   4. `mapped_with_unknown_values`: a present knob is not `known`.
   5. `mapped`: otherwise.

   Mixed games, where one file is mapped and another is not (`Engine.ini`), get the
   mapped status, with the other file listed in `unmapped_files`.
7. **Empty value.** `key=` gives `present: true, value: "", known: false`.
8. **Frozen key sets.**
   - **Game:** `appid, name, engine, anticheat, status, maps, unmapped_files, issues`.
     `engine` and `anticheat` are copied verbatim from the card. "Lists anti-cheat"
     means a non-empty `anticheat` list. A map's `engine` is a label only and is not
     checked against the card.
   - **Map entry:** `map_id, file, encoding, duplicates, knobs`. `duplicates` is a list
     of `[section, key]`.
   - **Knob:** `id, label, section, key, type, present, value, known, confidence`.
   - **Issue:** `code, path`, plus `why`, `map_id` or `knob` where a code uses them.
9. **Locating maps.** Maps are found by path: the `maps` folder next to `settings.py`.
   Finding zero maps raises `SettingsError`.
10. **Case.** Sections, keys and values are compared case-sensitively and exactly. Only
    `file_name` matching ignores case.
11. **Repeated section header.** Its keys merge into the first occurrence, and the first
    value wins. Each repeated key is recorded in `duplicates`.
12. **Several files matching the same map.** Each is reported separately with its
    `file`. If the same knob is present with different values in two of them, the
    issue `{"code": "conflicting_files", "path": <first file>, "map_id", "knob"}` is
    added. Neither file is chosen.
13. **Unreal values.**
    - Level values are `"0"`–`"4"`, where 4 is Cinematic, documented by Epic.
    - `sg.ResolutionQuality` is known only as a plain integer string from 10 to 100.
      `"100.000000"` is **not** known.
14. **Encodings.**
    - A UTF-16 BOM with a decode failure → the issue `settings_unreadable`. There is no
      Latin-1 fallback for UTF-16.
    - Files without a BOM: UTF-8, then Latin-1, as in S1.
15. **File names.** Fixtures use the real base names (`config.ini`,
    `GameUserSettings.ini`), not the snapshot's numbered names.
16. **Other kinds.** Unity `boot.config` and any other non-registry file are parsed and
    land in `unmapped_files`.
17. **Read while the game runs.** Size and mtime (ns) are recorded before and after
    reading. If either differs, the issue `changed_during_read` is added and the
    values are still reported.
18. **Reuse (R13).** Opening files reuses the existing lstat + `O_NOFOLLOW` approach in
    `snapshot.py` / `measure.py`. Shared code is factored only if it can be done
    without changing those modules' behaviour; otherwise it follows the same pattern,
    and the PR says why.
