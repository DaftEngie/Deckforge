# Contracts for deckforge.settings.match_maps and read_settings (docs/specs/settings-read.md,
# S4-S7 and S10, with clarifier answers 1, 2, 4, 6, 7, 8, 10, 12-17, which win over S1-S10).
#
# match_maps(ini, file_name, maps) -> list[str]
#   Pre:  ini from read_ini; file_name is the settings file's base name; maps as load_maps.
#   Post: the ids of the maps whose whole fingerprint holds: file_name equal ignoring case,
#         every listed section present, every [section, key] pair present. Sections and keys
#         compare case-sensitively (answer 10). A snapshot's numbered name such as
#         "1_GameUserSettings.ini" is a different base name (answer 15). Order is not
#         specified, so ids are compared sorted.
#
# read_settings(card, maps) -> dict
#   Pre:  card is a discover scan card (all B4/C2-C7 fields) with installed true, of any
#         kind: spec item 19 keeps read_settings open to tool cards (only the CLI filters).
#   Post: keys exactly appid, name, engine, anticheat, status, maps, unmapped_files, issues
#         (answer 8). ASSUMED: answer 8's frozen "Game" key set, which includes status, is
#         what read_settings returns (S8 describes the CLI JSON as the S5 report "plus
#         status"; answer 8 freezes one game shape with status in it).
#   Post: engine and anticheat are copied verbatim from the card; a map's engine is never
#         checked against the card's engine.
#   Post: maps has one entry per (matching map, settings file): keys exactly map_id, file,
#         encoding, duplicates, knobs. file is the card's path string; duplicates is a list
#         of [section, key]. Several maps on one file give one entry each; one map on
#         several files gives one entry per file (answer 12).
#   Post: an entry lists every knob of its map: keys exactly id, label, section, key, type,
#         present, value, known, confidence. id/label/section/key/type/confidence are the
#         map knob's. Missing key: present false, value null, known false. Present key:
#         value is the string read; "key=" gives value "" and known false (answer 7).
#   Post: known. level/enum/bool: value in values, exactly and case-sensitively (answer 10).
#         percent: a plain integer string within min-max, so "100.000000" is not known
#         (answer 13). Item 20 makes that exact: the value must fully match -?[0-9]{1,9}
#         (ASCII digits, so "0010" is 10 and known, "+50", "5_0" and Arabic-Indic digits
#         are not), and a longer digit string is unknown, never an exception.
#         number: parses as a finite float within whichever bounds are given
#         (answer 1).
#   Post: a parsed file no map matched is in unmapped_files (S4, answer 16), entries read
#         as a path string or an object with "path" (shape unspecified).
#   Post: issues. Registry files (kind "reg" or "registry") are never opened and add exactly
#         {"code": "registry_not_read", "path"}. A file that fails S1 (too big, link,
#         folder, missing, or a UTF-16 BOM with bad UTF-16, answer 14) adds exactly
#         {"code": "settings_unreadable", "path", "why"} with a non-empty why, and gets no
#         map entry. One knob present with different values in two files of one map adds
#         {"code": "conflicting_files", "path": <first file in card order>, "map_id",
#         "knob": <knob id>} and neither value is chosen (answer 12). A file whose size or
#         mtime changed while it was read adds {"code": "changed_during_read", "path"}, and
#         its values are still reported (answer 17). Issue order is not specified.
#   Post: status, first rule that holds (answer 6): unreadable (at least one non-registry
#         file, all of them failed S1, no map matched); no_map (no file matched a map);
#         mapped_empty (maps matched, zero knobs present over all entries);
#         mapped_with_unknown_values (a present knob not known); mapped. A game with one
#         mapped file and one unmapped file is mapped, the other in unmapped_files.
#   Post: answer 4: the Wilds map reads only the sections it names; [RenderConfig] never
#         supplies a value, even when it disagrees with [Graphics].
#   Inv:  answer 17's trigger: the tests change the file (size and mtime) right after the
#         reader opens it and before it reads. ASSUMED: the "before" record is the lstat
#         taken before opening (S1's lstat-first check); a reader that records "before"
#         only after opening would not see this change.

import builtins
import io
import os
import pathlib
from pathlib import Path

import pytest
from test_discover_output import record_opens
from test_settings_support import (
    DD2_INI,
    DD2_KNOBS,
    GAME_KEYS,
    ISSUE_KEYS,
    KNOB_KEYS,
    MAP_ENTRY_KEYS,
    RE_APPOPTION,
    RE_GRAPHICS,
    REMATCH_GUS,
    REMATCH_VALUES,
    SPARKING_GUS,
    SPARKING_VALUES,
    UNREAL,
    UNREAL_KEYS,
    WILDS_INI,
    WILDS_KNOBS,
    MiB,
    as_pairs,
    builtin_map,
    by_key,
    entries_for,
    entry,
    issue_pairs,
    issues_of,
    knob,
    make_card,
    make_map,
    only_entry,
    sized,
    unmapped_paths,
    write,
)

from deckforge import settings

GUS = "GameUserSettings.ini"
SG = "ScalabilityGroups"


@pytest.fixture(scope="module")
def maps() -> list[dict]:
    return settings.load_maps()


def report_for(maps, files, **card_fields) -> dict:
    """files: (path, kind) pairs."""
    card = make_card([entry(path, kind) for path, kind in files], **card_fields)
    return settings.read_settings(card, maps)


def one_file(tmp_path, maps, data: bytes, file_name: str, **card_fields) -> tuple[dict, Path]:
    path = write(tmp_path / "Game" / file_name, data)
    return report_for(maps, [(path, "ini")], **card_fields), path


def ini_of(tmp_path, data: bytes, name: str):
    return settings.read_ini(write(tmp_path / "m" / name, data))


def gus(*lines: str) -> bytes:
    return ("[ScalabilityGroups]\r\n" + "".join(f"{line}\r\n" for line in lines)).encode()


def wilds_with(old: str, new: str) -> bytes:
    """WILDS_INI with one [Graphics] line replaced (old must occur once in [Graphics])."""
    head, tail = WILDS_INI.split(b"[Graphics/FSR3]\n")
    assert head.count(f"\n{old}\n".encode()) == 1
    head = head.replace(f"\n{old}\n".encode(), f"\n{new}\n".encode() if new else b"\n")
    return head + b"[Graphics/FSR3]\n" + tail


def unreal_knob(report: dict, key: str) -> dict:
    return by_key(only_entry(report, UNREAL))[(SG, key)]


# ---------------------------------------------------------------------------- S4 matching


@pytest.mark.parametrize(
    "data, name, expected",
    [
        (WILDS_INI, "config.ini", [RE_GRAPHICS]),
        (DD2_INI, "config.ini", [RE_APPOPTION]),
        (SPARKING_GUS, GUS, [UNREAL]),
        (REMATCH_GUS, GUS, [UNREAL]),
    ],
    ids=["wilds", "dd2", "sparking-zero", "rematch"],
)
def test_s4_s10_real_files_match_their_maps(tmp_path, maps, data, name, expected):
    assert settings.match_maps(ini_of(tmp_path, data, name), name, maps) == expected


@pytest.mark.parametrize(
    "name", ["gameusersettings.ini", "GAMEUSERSETTINGS.INI", "GameUserSettings.INI"]
)
def test_s4_file_name_matches_ignoring_case(tmp_path, maps, name):
    assert settings.match_maps(ini_of(tmp_path, REMATCH_GUS, name), name, maps) == [UNREAL]


def test_s4_config_ini_name_matches_ignoring_case(tmp_path, maps):
    assert settings.match_maps(ini_of(tmp_path, DD2_INI, "CONFIG.INI"), "CONFIG.INI", maps) == [
        RE_APPOPTION
    ]


@pytest.mark.parametrize(
    "name", ["Engine.ini", "1_GameUserSettings.ini", "GameUserSettings.ini.bak"]
)
def test_s4_a15_other_base_names_do_not_match(tmp_path, maps, name):
    assert settings.match_maps(ini_of(tmp_path, SPARKING_GUS, name), name, maps) == []


def test_s4_missing_section_does_not_match(tmp_path, maps):
    data = b"[/Script/Engine.GameUserSettings]\r\nbUseDesiredScreenHeight=False\r\n"
    assert settings.match_maps(ini_of(tmp_path, data, GUS), GUS, maps) == []


def test_s4_a10_section_case_must_match(tmp_path, maps):
    data = b"[scalabilitygroups]\r\nsg.ShadowQuality=1\r\n"
    assert settings.match_maps(ini_of(tmp_path, data, GUS), GUS, maps) == []


def test_s4_missing_fingerprint_key_does_not_match(tmp_path, maps):
    data = wilds_with("ShaderConvertVersion=Product:1.42.0.2,File:1.42.0.2", "")
    assert settings.match_maps(ini_of(tmp_path, data, "config.ini"), "config.ini", maps) == []


def test_s4_fingerprint_key_in_another_section_does_not_match(tmp_path, maps):
    data = b"[Graphics]\nShadowQuality=LOWEST\n[Render]\nShaderConvertVersion=1\n"
    assert settings.match_maps(ini_of(tmp_path, data, "config.ini"), "config.ini", maps) == []


def test_s4_a10_fingerprint_key_case_must_match(tmp_path, maps):
    data = b"[AppOption]\nupscalingalgorithm=FSR3\n"
    assert settings.match_maps(ini_of(tmp_path, data, "config.ini"), "config.ini", maps) == []


def test_s4_an_empty_file_matches_nothing(tmp_path, maps):
    assert settings.match_maps(ini_of(tmp_path, b"", "config.ini"), "config.ini", maps) == []


def test_s4_a_file_with_both_capcom_fingerprints_matches_both(tmp_path, maps):
    data = WILDS_INI + DD2_INI
    found = settings.match_maps(ini_of(tmp_path, data, "config.ini"), "config.ini", maps)
    assert sorted(found) == [RE_APPOPTION, RE_GRAPHICS]


def test_s4_several_custom_maps_all_match(tmp_path):
    custom = [
        make_map("m-one", knobs=[knob("shadow", "Shadow")]),
        make_map("m-two", keys=[["S", "Shadow"]], knobs=[knob("shadow", "Shadow")]),
        make_map("m-three", sections=["Other"], knobs=[knob("shadow", "Shadow")]),
    ]
    ini = ini_of(tmp_path, b"[S]\nShadow=a\n", "test.ini")
    assert sorted(settings.match_maps(ini, "test.ini", custom)) == ["m-one", "m-two"]


def test_s4_a_map_with_no_sections_or_keys_matches_on_the_file_name(tmp_path):
    custom = [make_map("by-name", sections=[], knobs=[knob("x", "x")])]
    assert settings.match_maps(ini_of(tmp_path, b"", "test.ini"), "test.ini", custom) == ["by-name"]


# ---------------------------------------------------------------------------- S5 shapes


def test_a8_report_keys_are_frozen(tmp_path, maps):
    report, _ = one_file(tmp_path, maps, REMATCH_GUS, GUS)
    assert set(report) == GAME_KEYS
    assert len(report["maps"]) == 1
    assert set(report["maps"][0]) == MAP_ENTRY_KEYS
    for item in report["maps"][0]["knobs"]:
        assert set(item) == KNOB_KEYS


def test_s5_report_names_the_card(tmp_path, maps):
    report, _ = one_file(tmp_path, maps, REMATCH_GUS, GUS, appid=2138720, name="REMATCH")
    assert report["appid"] == 2138720
    assert report["name"] == "REMATCH"


@pytest.mark.parametrize("engine", ["unreal", "unknown", "ambiguous", "unity"])
def test_a8_engine_is_copied_and_never_checked_against_the_map(tmp_path, maps, engine):
    report, _ = one_file(tmp_path, maps, REMATCH_GUS, GUS, engine=engine)
    assert report["engine"] == engine
    assert [m["map_id"] for m in report["maps"]] == [UNREAL]


def test_s5_map_entry_file_encoding_and_no_duplicates(tmp_path, maps):
    report, path = one_file(tmp_path, maps, SPARKING_GUS, GUS)
    item = only_entry(report, UNREAL)
    assert item["file"] == str(path)
    assert item["encoding"].replace("_", "-").lower() in {"utf-8", "utf8"}
    assert as_pairs(item["duplicates"]) == []


def test_s5_map_entry_lists_duplicates_as_section_key_pairs(tmp_path, maps):
    data = gus("sg.ShadowQuality=1", "sg.TextureQuality=2", "sg.ShadowQuality=3")
    report, _ = one_file(tmp_path, maps, data, GUS)
    item = only_entry(report, UNREAL)
    assert as_pairs(item["duplicates"]) == [[SG, "sg.ShadowQuality"]]
    assert unreal_knob(report, "sg.ShadowQuality")["value"] == "1"


def test_s5_knob_fields_are_copied_from_the_map(tmp_path, maps):
    report, _ = one_file(tmp_path, maps, SPARKING_GUS, GUS)
    reported = by_key(only_entry(report, UNREAL))
    for map_knob_ in builtin_map(maps, UNREAL)["knobs"]:
        got = reported[(map_knob_["section"], map_knob_["key"])]
        for field in ("id", "label", "section", "key", "type", "confidence"):
            assert got[field] == map_knob_[field], field


def test_s5_absent_knob_is_not_present_with_null_value(tmp_path, maps):
    report, _ = one_file(tmp_path, maps, REMATCH_GUS, GUS)
    shadow = unreal_knob(report, "sg.ShadowQuality")
    assert shadow["present"] is False
    assert shadow["value"] is None
    assert shadow["known"] is False


def test_a7_empty_value_is_present_and_not_known(tmp_path, maps):
    report, _ = one_file(tmp_path, maps, gus("sg.ShadowQuality=", "sg.TextureQuality=2"), GUS)
    shadow = unreal_knob(report, "sg.ShadowQuality")
    assert (shadow["present"], shadow["value"], shadow["known"]) == (True, "", False)
    assert report["status"] == "mapped_with_unknown_values"


@pytest.mark.parametrize("kind", ["tool", "game"])
def test_i19_read_settings_accepts_any_card_kind(tmp_path, maps, kind):
    report, path = one_file(tmp_path, maps, REMATCH_GUS, GUS, kind=kind, name="Proton 9.0")
    assert set(report) == GAME_KEYS
    assert report["name"] == "Proton 9.0"
    assert [m["file"] for m in report["maps"]] == [str(path)]
    assert report["status"] == "mapped"


# ---------------------------------------------------------------------------- S10 real data


def test_s10_wilds_is_mapped_by_re_graphics_section(tmp_path, maps):
    report, path = one_file(tmp_path, maps, WILDS_INI, "config.ini", engine="re_engine")
    assert report["status"] == "mapped"
    assert [m["map_id"] for m in report["maps"]] == [RE_GRAPHICS]
    item = only_entry(report, RE_GRAPHICS)
    assert item["file"] == str(path)
    knobs = by_key(item)
    assert set(knobs) == set(WILDS_KNOBS)
    for pair, value in WILDS_KNOBS.items():
        assert (knobs[pair]["present"], knobs[pair]["value"], knobs[pair]["known"]) == (
            True,
            value,
            True,
        ), pair
    assert report["issues"] == []
    assert report["unmapped_files"] == []


def test_s10_dd2_is_mapped_by_re_appoption_section(tmp_path, maps):
    report, path = one_file(tmp_path, maps, DD2_INI, "config.ini", engine="re_engine")
    assert report["status"] == "mapped"
    assert [m["map_id"] for m in report["maps"]] == [RE_APPOPTION]
    knobs = by_key(only_entry(report, RE_APPOPTION))
    assert set(knobs) == {("AppOption", key) for key in DD2_KNOBS}
    for key, (_, _, value) in DD2_KNOBS.items():
        got = knobs[("AppOption", key)]
        assert (got["present"], got["value"], got["known"]) == (True, value, True), key
    assert report["issues"] == []
    assert report["unmapped_files"] == []


def test_s10_sparking_zero_is_mapped_by_unreal_with_all_eleven_keys(tmp_path, maps):
    report, _ = one_file(tmp_path, maps, SPARKING_GUS, GUS, engine="unreal")
    assert report["status"] == "mapped"
    knobs = by_key(only_entry(report, UNREAL))
    assert set(knobs) == {(SG, key) for key in UNREAL_KEYS}
    for key, value in SPARKING_VALUES.items():
        assert (knobs[(SG, key)]["present"], knobs[(SG, key)]["value"]) == (True, value), key
        assert knobs[(SG, key)]["known"] is True, key
    assert report["issues"] == []


def test_s10_rematch_reports_two_present_keys_and_the_rest_absent(tmp_path, maps):
    report, _ = one_file(tmp_path, maps, REMATCH_GUS, GUS, engine="unreal")
    assert report["status"] == "mapped"
    knobs = by_key(only_entry(report, UNREAL))
    assert set(knobs) == {(SG, key) for key in UNREAL_KEYS}
    for key in UNREAL_KEYS:
        got = knobs[(SG, key)]
        if key in REMATCH_VALUES:
            assert (got["present"], got["value"], got["known"]) == (True, REMATCH_VALUES[key], True)
        else:
            assert (got["present"], got["value"]) == (False, None), key
    assert report["issues"] == []


# ---------------------------------------------------------------------------- answer 4


def test_a4_render_config_never_supplies_a_value(tmp_path, maps):
    head, tail = WILDS_INI.split(b"[RenderConfig]\n")
    assert tail.count(b"ShadowQuality=LOWEST\n") == 1
    data = (
        head
        + b"[RenderConfig]\n"
        + tail.replace(b"ShadowQuality=LOWEST\n", b"ShadowQuality=HIGH\n")
    )
    report, _ = one_file(tmp_path, maps, data, "config.ini")
    shadow = by_key(only_entry(report, RE_GRAPHICS))[("Graphics", "ShadowQuality")]
    assert (shadow["value"], shadow["known"]) == ("LOWEST", True)
    assert report["status"] == "mapped"


def test_a4_a_key_only_in_render_config_is_not_present(tmp_path, maps):
    report, _ = one_file(tmp_path, maps, wilds_with("ShadowQuality=LOWEST", ""), "config.ini")
    shadow = by_key(only_entry(report, RE_GRAPHICS))[("Graphics", "ShadowQuality")]
    assert (shadow["present"], shadow["value"]) == (False, None)
    assert report["status"] == "mapped"


def test_a4_ray_tracing_section_quality_is_not_graphics_quality(tmp_path, maps):
    report, _ = one_file(tmp_path, maps, WILDS_INI, "config.ini")
    knobs = by_key(only_entry(report, RE_GRAPHICS))
    assert knobs[("Graphics", "Quality")]["value"] == "Balanced"
    assert knobs[("Graphics/RayTracing", "Enable")]["value"] == "False"


# ---------------------------------------------------------------------------- known values


@pytest.mark.parametrize(
    "value, known",
    [
        ("10", True),
        ("55", True),
        ("87", True),
        ("100", True),
        ("9", False),
        ("0", False),
        ("101", False),
        ("-50", False),
        ("100.000000", False),
        ("87.5", False),
        ("abc", False),
    ],
)
def test_a13_resolution_quality_known_only_as_integer_10_to_100(tmp_path, maps, value, known):
    report, _ = one_file(tmp_path, maps, gus(f"sg.ResolutionQuality={value}"), GUS)
    got = unreal_knob(report, "sg.ResolutionQuality")
    assert (got["present"], got["value"], got["known"]) == (True, value, known)
    assert report["status"] == ("mapped" if known else "mapped_with_unknown_values")


@pytest.mark.parametrize(
    "value, known",
    [
        ("1" * 4301, False),
        ("1" * 10, False),
        ("0000000050", False),
        ("-" + "9" * 4301, False),
        ("000000050", True),
        ("0010", True),
        ("0100", True),
        ("-5", False),
        ("-050", False),
        ("+50", False),
        ("\u0665\u0660", False),
        ("5_0", False),
        ("50 ", True),
    ],
    ids=[
        "4301-digits",
        "10-digits",
        "10-digits-in-range",
        "negative-4301-digits",
        "9-digits-in-range",
        "leading-zeros-10",
        "leading-zeros-100",
        "minus-5",
        "minus-050",
        "plus-50",
        "arabic-indic-50",
        "underscore",
        "trailing-space-stripped",
    ],
)
def test_i20_percent_known_only_for_up_to_9_ascii_digits_in_range(tmp_path, maps, value, known):
    report, _ = one_file(tmp_path, maps, gus(f"sg.ResolutionQuality={value}"), GUS)
    got = unreal_knob(report, "sg.ResolutionQuality")
    assert (got["present"], got["value"], got["known"]) == (True, value.strip(), known)
    assert report["status"] == ("mapped" if known else "mapped_with_unknown_values")


@pytest.mark.parametrize(
    "value, known",
    [
        ("0", True),
        ("1", True),
        ("2", True),
        ("3", True),
        ("4", True),
        ("5", False),
        ("-1", False),
        ("3.0", False),
        ("High", False),
    ],
)
def test_a13_unreal_level_known_from_0_to_4(tmp_path, maps, value, known):
    report, _ = one_file(tmp_path, maps, gus(f"sg.ShadowQuality={value}"), GUS)
    got = unreal_knob(report, "sg.ShadowQuality")
    assert (got["value"], got["known"]) == (value, known)
    assert report["status"] == ("mapped" if known else "mapped_with_unknown_values")


@pytest.mark.parametrize(
    "old, new, pair, known",
    [
        ("Bloom_Enable=True", "Bloom_Enable=False", ("Graphics", "Bloom_Enable"), True),
        ("SSR_Enable=False", "SSR_Enable=True", ("Graphics", "SSR_Enable"), True),
        ("Bloom_Enable=True", "Bloom_Enable=true", ("Graphics", "Bloom_Enable"), False),
        ("Bloom_Enable=True", "Bloom_Enable=TRUE", ("Graphics", "Bloom_Enable"), False),
        ("ShadowQuality=LOWEST", "ShadowQuality=lowest", ("Graphics", "ShadowQuality"), False),
        ("ShadowQuality=LOWEST", "ShadowQuality=HIGH", ("Graphics", "ShadowQuality"), False),
        ("Quality=Balanced", "Quality=balanced", ("Graphics", "Quality"), False),
        ("ImageQualityRate=1", "ImageQualityRate=2", ("Graphics", "ImageQualityRate"), False),
    ],
    ids=[
        "bool-unseen-spelling-allowed",
        "bool-unseen-true-allowed",
        "bool-lowercase",
        "bool-uppercase",
        "enum-lowercase",
        "enum-unseen-value",
        "enum-case",
        "enum-image-quality-rate",
    ],
)
def test_a2_a10_wilds_values_outside_the_list_are_unknown(tmp_path, maps, old, new, pair, known):
    report, _ = one_file(tmp_path, maps, wilds_with(old, new), "config.ini")
    got = by_key(only_entry(report, RE_GRAPHICS))[pair]
    assert (got["value"], got["known"]) == (new.split("=", 1)[1], known)
    assert report["status"] == ("mapped" if known else "mapped_with_unknown_values")


@pytest.mark.parametrize(
    "old, new, known",
    [
        ("VSync=ON", "VSync=OFF", True),
        ("FSR3_FrameGeneraion=OFF", "FSR3_FrameGeneraion=ON", True),
        ("VSync=ON", "VSync=on", False),
        ("VSync=ON", "VSync=Off", False),
        ("TextureQuality=High", "TextureQuality=Low", False),
        ("UpscalingSharpness=7", "UpscalingSharpness=0.5", True),
        ("UpscalingSharpness=7", "UpscalingSharpness=sharp", False),
    ],
)
def test_a2_a5_dd2_values(tmp_path, maps, old, new, known):
    assert DD2_INI.count(f"\n{old}\n".encode()) == 1
    data = DD2_INI.replace(f"\n{old}\n".encode(), f"\n{new}\n".encode())
    report, _ = one_file(tmp_path, maps, data, "config.ini")
    key, value = new.split("=", 1)
    got = by_key(only_entry(report, RE_APPOPTION))[("AppOption", key)]
    assert (got["value"], got["known"]) == (value, known)
    assert report["status"] == ("mapped" if known else "mapped_with_unknown_values")


NUMBER_MAP = make_map(
    "number-map",
    knobs=[
        knob("free", "free", "number"),
        knob("bounded", "bounded", "number", min=0, max=1),
        knob("low_only", "low_only", "number", min=0),
    ],
)


@pytest.mark.parametrize(
    "key, value, known",
    [
        ("free", "7", True),
        ("free", "0.65", True),
        ("free", "-3.5", True),
        ("free", "1e3", True),
        ("free", "nan", False),
        ("free", "inf", False),
        ("free", "-inf", False),
        ("free", "abc", False),
        ("free", "1,5", False),
        ("free", "", False),
        ("bounded", "0", True),
        ("bounded", "1", True),
        ("bounded", "0.5", True),
        ("bounded", "1.5", False),
        ("bounded", "-0.1", False),
        ("bounded", "nan", False),
        ("low_only", "1000000", True),
        ("low_only", "-1", False),
    ],
)
def test_a1_number_known_when_finite_and_within_given_bounds(tmp_path, key, value, known):
    report, _ = one_file(tmp_path, [NUMBER_MAP], f"[S]\n{key}={value}\n".encode(), "test.ini")
    got = by_key(only_entry(report, "number-map"))[("S", key)]
    assert (got["present"], got["value"], got["known"]) == (True, value, known)


# ---------------------------------------------------------------------------- S4 reporting


def test_s4_a_file_matched_by_two_maps_gets_one_entry_per_map(tmp_path, maps):
    report, path = one_file(tmp_path, maps, WILDS_INI + DD2_INI, "config.ini")
    assert sorted(m["map_id"] for m in report["maps"]) == [RE_APPOPTION, RE_GRAPHICS]
    assert {m["file"] for m in report["maps"]} == {str(path)}
    assert by_key(only_entry(report, RE_APPOPTION))[("AppOption", "VSync")]["value"] == "ON"
    graphics = by_key(only_entry(report, RE_GRAPHICS))
    assert graphics[("Graphics", "ShadowQuality")]["value"] == "LOWEST"
    assert report["status"] == "mapped"


def test_s4_the_same_knob_id_in_two_maps_is_reported_under_each_map(tmp_path):
    custom = [
        make_map("m-one", knobs=[knob("shadow", "Shadow", values=["a"])]),
        make_map("m-two", knobs=[knob("shadow", "Shadow", values=["b"])]),
    ]
    report, _ = one_file(tmp_path, custom, b"[S]\nShadow=a\n", "test.ini")
    one = only_entry(report, "m-one")["knobs"]
    two = only_entry(report, "m-two")["knobs"]
    assert [(k["id"], k["value"], k["known"]) for k in one] == [("shadow", "a", True)]
    assert [(k["id"], k["value"], k["known"]) for k in two] == [("shadow", "a", False)]
    assert report["status"] == "mapped_with_unknown_values"


def test_s4_a_file_no_map_matches_is_in_unmapped_files(tmp_path, maps):
    report, path = one_file(tmp_path, maps, b"[Core.System]\r\nPaths=x\r\n", "Engine.ini")
    assert unmapped_paths(report) == [str(path)]
    assert report["maps"] == []
    assert report["status"] == "no_map"


def test_a16_unity_boot_config_is_parsed_and_unmapped(tmp_path, maps):
    boot = write(tmp_path / "Game_Data" / "boot.config", b"gfx-enable-gfx-jobs=1\nvr=0\n")
    report = report_for(maps, [(boot, "boot_config")], engine="unity")
    assert unmapped_paths(report) == [str(boot)]
    assert report["issues"] == []
    assert report["status"] == "no_map"


def test_a6_mixed_game_is_mapped_with_engine_ini_unmapped(tmp_path, maps):
    config = tmp_path / "pfx" / "Saved" / "Config" / "Windows"
    engine_ini = write(config / "Engine.ini", b"[SystemSettings]\r\nr.X=1\r\n")
    gus_path = write(config / GUS, SPARKING_GUS)
    report = report_for(maps, [(engine_ini, "ini"), (gus_path, "ini")], engine="unreal")
    assert report["status"] == "mapped"
    assert unmapped_paths(report) == [str(engine_ini)]
    assert [m["file"] for m in report["maps"]] == [str(gus_path)]


# ---------------------------------------------------------------------------- registry


@pytest.mark.parametrize("kind", ["registry", "reg"])
def test_s5_registry_files_are_never_opened_and_add_an_issue(tmp_path, maps, monkeypatch, kind):
    reg = write(tmp_path / "pfx" / "user.reg", b"WINE REGISTRY Version 2\n[Software\\\\Game]\n")
    boot = write(tmp_path / "Game_Data" / "boot.config", b"a=1\n")
    with monkeypatch.context() as patch:
        seen = record_opens(patch)
        report = report_for(maps, [(reg, kind), (boot, "boot_config")])
    opened = {
        os.path.realpath(os.fsdecode(file))
        for _, file, _ in seen
        if isinstance(file, str | bytes | os.PathLike)
    }
    assert os.path.realpath(reg) not in opened
    assert os.path.realpath(boot) in opened, "the recorder saw no open of the other file"
    assert issues_of(report, "registry_not_read") == [
        {"code": "registry_not_read", "path": str(reg)}
    ]
    assert report["status"] == "no_map"


def test_s5_registry_file_that_does_not_exist_still_gets_only_the_issue(tmp_path, maps):
    reg = tmp_path / "pfx" / "user.reg"
    report = report_for(maps, [(reg, "registry")])
    assert report["issues"] == [{"code": "registry_not_read", "path": str(reg)}]
    assert report["status"] == "no_map"


# ---------------------------------------------------------------------------- unreadable


def bad_file(tmp_path: Path, how: str) -> Path:
    path = tmp_path / "Game" / GUS
    if how == "oversized":
        sized(path, MiB + 1, head=b"[ScalabilityGroups]\r\nsg.ShadowQuality=1\r\n")
    elif how == "link":
        target = write(tmp_path / "real" / GUS, SPARKING_GUS)
        path.parent.mkdir(parents=True)
        path.symlink_to(target)
    elif how == "folder":
        path.mkdir(parents=True)
    elif how == "missing":
        path.parent.mkdir(parents=True)
    elif how == "utf16-lone-surrogate":
        write(path, b"\xff\xfe" + "[ScalabilityGroups]\r\n".encode("utf-16-le") + b"\x00\xd8A\x00")
    elif how == "utf16-odd-length":
        write(
            path,
            b"\xff\xfe"
            + "[ScalabilityGroups]\r\nsg.ShadowQuality=1\r\n".encode("utf-16-le")
            + b"A",
        )
    elif how == "utf16-be-lone-surrogate":
        write(path, b"\xfe\xff" + "[ScalabilityGroups]\r\n".encode("utf-16-be") + b"\xdc\x00\x00A")
    else:
        raise AssertionError(how)
    return path


UNREADABLE = [
    "oversized",
    "link",
    "folder",
    "missing",
    "utf16-lone-surrogate",
    "utf16-odd-length",
    "utf16-be-lone-surrogate",
]


@pytest.mark.parametrize("how", UNREADABLE)
def test_s5_a6_a14_a_file_failing_s1_is_unreadable(tmp_path, maps, how):
    path = bad_file(tmp_path, how)
    report = report_for(maps, [(path, "ini")], engine="unreal")
    found = issues_of(report, "settings_unreadable")
    assert len(found) == 1
    assert set(found[0]) == ISSUE_KEYS["settings_unreadable"]
    assert found[0]["path"] == str(path)
    assert isinstance(found[0]["why"], str) and found[0]["why"].strip()
    assert report["maps"] == []
    assert report["status"] == "unreadable"


def test_a6_unreadable_ignores_registry_files(tmp_path, maps):
    path = bad_file(tmp_path, "oversized")
    reg = write(tmp_path / "pfx" / "user.reg", b"WINE\n")
    report = report_for(maps, [(path, "ini"), (reg, "registry")])
    assert issue_pairs(report) == sorted(
        [("registry_not_read", str(reg)), ("settings_unreadable", str(path))]
    )
    assert report["status"] == "unreadable"


def test_a6_one_failed_file_and_one_unmapped_file_is_no_map(tmp_path, maps):
    path = bad_file(tmp_path, "oversized")
    engine_ini = write(tmp_path / "Game" / "Engine.ini", b"[Core.System]\r\nPaths=x\r\n")
    report = report_for(maps, [(path, "ini"), (engine_ini, "ini")])
    assert report["status"] == "no_map"
    assert unmapped_paths(report) == [str(engine_ini)]
    assert issue_pairs(report) == [("settings_unreadable", str(path))]


def test_a6_a_mapped_file_wins_over_an_unreadable_one(tmp_path, maps):
    path = bad_file(tmp_path, "oversized")
    good = write(tmp_path / "Other" / GUS, SPARKING_GUS)
    report = report_for(maps, [(path, "ini"), (good, "ini")])
    assert report["status"] == "mapped"
    assert issue_pairs(report) == [("settings_unreadable", str(path))]
    assert [m["file"] for m in report["maps"]] == [str(good)]


# ---------------------------------------------------------------------------- status order


def test_a6_no_settings_files_is_no_map(maps):
    report = settings.read_settings(make_card([]), maps)
    assert report["status"] == "no_map"
    assert (report["maps"], report["unmapped_files"], report["issues"]) == ([], [], [])


def test_a6_only_registry_files_is_no_map(tmp_path, maps):
    reg = write(tmp_path / "pfx" / "user.reg", b"WINE\n")
    report = report_for(maps, [(reg, "registry")])
    assert report["status"] == "no_map"


@pytest.mark.parametrize(
    "data",
    [gus(), gus("sg.SomethingElse=1"), b"[ScalabilityGroups]\r\n"],
    ids=["empty-section", "no-mapped-key", "header-only"],
)
def test_a6_mapped_with_zero_present_knobs_is_mapped_empty(tmp_path, maps, data):
    report, _ = one_file(tmp_path, maps, data, GUS)
    assert [m["map_id"] for m in report["maps"]] == [UNREAL]
    assert report["status"] == "mapped_empty"


def test_a6_mapped_empty_counts_knobs_over_every_entry(tmp_path, maps):
    empty = write(tmp_path / "a" / GUS, gus())
    bad = write(tmp_path / "b" / GUS, gus("sg.ShadowQuality=9"))
    good = write(tmp_path / "c" / GUS, gus("sg.ShadowQuality=1"))
    assert report_for(maps, [(empty, "ini"), (bad, "ini")])["status"] == (
        "mapped_with_unknown_values"
    )
    assert report_for(maps, [(empty, "ini"), (good, "ini")])["status"] == "mapped"


def test_a2_a6_a_value_outside_the_list_gives_mapped_with_unknown_values(tmp_path, maps):
    report, _ = one_file(tmp_path, maps, gus("sg.ShadowQuality=9", "sg.TextureQuality=2"), GUS)
    assert unreal_knob(report, "sg.ShadowQuality")["known"] is False
    assert unreal_knob(report, "sg.TextureQuality")["known"] is True
    assert report["status"] == "mapped_with_unknown_values"


def test_s6_all_present_knobs_known_is_mapped(tmp_path, maps):
    report, _ = one_file(tmp_path, maps, gus("sg.ShadowQuality=2"), GUS)
    assert report["status"] == "mapped"


# ---------------------------------------------------------------------------- answer 12


def test_a12_conflicting_files_names_the_first_file_map_and_knob(tmp_path, maps):
    first = write(tmp_path / "a" / GUS, gus("sg.ShadowQuality=1", "sg.TextureQuality=3"))
    second = write(tmp_path / "b" / GUS, gus("sg.ShadowQuality=2", "sg.TextureQuality=3"))
    report = report_for(maps, [(second, "ini"), (first, "ini")])
    entries = entries_for(report, UNREAL)
    assert sorted(m["file"] for m in entries) == [str(first), str(second)]
    values = {m["file"]: by_key(m)[(SG, "sg.ShadowQuality")]["value"] for m in entries}
    assert values == {str(first): "1", str(second): "2"}
    shadow_id = unreal_knob_id(maps, "sg.ShadowQuality")
    assert issues_of(report, "conflicting_files") == [
        {"code": "conflicting_files", "path": str(first), "map_id": UNREAL, "knob": shadow_id}
    ]
    assert report["status"] == "mapped"


def test_a12_one_issue_per_conflicting_knob(tmp_path, maps):
    first = write(tmp_path / "a" / GUS, gus("sg.ShadowQuality=1", "sg.TextureQuality=3"))
    second = write(tmp_path / "b" / GUS, gus("sg.ShadowQuality=2", "sg.TextureQuality=0"))
    report = report_for(maps, [(first, "ini"), (second, "ini")])
    found = issues_of(report, "conflicting_files")
    assert sorted(issue["knob"] for issue in found) == sorted(
        [unreal_knob_id(maps, "sg.ShadowQuality"), unreal_knob_id(maps, "sg.TextureQuality")]
    )
    assert {issue["path"] for issue in found} == {str(first)}


@pytest.mark.parametrize(
    "second_lines",
    [("sg.ShadowQuality=1",), ("sg.TextureQuality=2",), ()],
    ids=["same-value", "knob-absent-in-one", "empty-second-file"],
)
def test_a12_no_conflict_without_two_different_present_values(tmp_path, maps, second_lines):
    first = write(tmp_path / "a" / GUS, gus("sg.ShadowQuality=1"))
    second = write(tmp_path / "b" / GUS, gus(*second_lines))
    report = report_for(maps, [(first, "ini"), (second, "ini")])
    assert issues_of(report, "conflicting_files") == []
    assert len(entries_for(report, UNREAL)) == 2


def unreal_knob_id(maps: list[dict], key: str) -> str:
    return next(k["id"] for k in builtin_map(maps, UNREAL)["knobs"] if k["key"] == key)


# ---------------------------------------------------------------------------- answer 17


def change_on_open(monkeypatch: pytest.MonkeyPatch, target: Path) -> list[bool]:
    """Right after the first open of `target` (any route), grow it by one comment line and
    move its mtime 5 s on, as a running game rewriting its settings would."""
    fired: list[bool] = []
    real_os_open, real_open, real_path_open = os.open, builtins.open, pathlib.Path.open
    wanted = os.path.realpath(target)

    def is_target(file: object) -> bool:
        if not isinstance(file, str | bytes | os.PathLike):
            return False
        return os.path.realpath(os.fsdecode(file)) == wanted

    def change() -> None:
        if fired:
            return
        fired.append(True)
        before = target.lstat()
        fd = real_os_open(target, os.O_WRONLY | os.O_APPEND)
        try:
            os.write(fd, b"; rewritten by the game\r\n")
        finally:
            os.close(fd)
        later = before.st_mtime_ns + 5_000_000_000
        os.utime(target, ns=(before.st_atime_ns, later))

    def fake_os_open(path, flags, *args, **kwargs):
        result = real_os_open(path, flags, *args, **kwargs)
        if is_target(path):
            change()
        return result

    def fake_open(file, *args, **kwargs):
        result = real_open(file, *args, **kwargs)
        if is_target(file):
            change()
        return result

    def fake_path_open(self, *args, **kwargs):
        result = real_path_open(self, *args, **kwargs)
        if is_target(self):
            change()
        return result

    monkeypatch.setattr(os, "open", fake_os_open)
    monkeypatch.setattr(builtins, "open", fake_open)
    monkeypatch.setattr(io, "open", fake_open)
    monkeypatch.setattr(pathlib.Path, "open", fake_path_open)
    return fired


def test_a17_a_file_changed_while_read_adds_an_issue_and_keeps_its_values(
    tmp_path, maps, monkeypatch
):
    path = write(tmp_path / "Game" / GUS, REMATCH_GUS)
    with monkeypatch.context() as patch:
        fired = change_on_open(patch, path)
        report = report_for(maps, [(path, "ini")])
    assert fired == [True], "the reader never opened the file"
    assert issues_of(report, "changed_during_read") == [
        {"code": "changed_during_read", "path": str(path)}
    ]
    knobs = by_key(only_entry(report, UNREAL))
    for key, value in REMATCH_VALUES.items():
        assert (knobs[(SG, key)]["present"], knobs[(SG, key)]["value"]) == (True, value)
    assert report["status"] == "mapped"


def test_a17_an_unchanged_file_has_no_changed_during_read_issue(tmp_path, maps):
    report, _ = one_file(tmp_path, maps, WILDS_INI, "config.ini")
    assert issues_of(report, "changed_during_read") == []


# ---------------------------------------------------------------------------- S7


def test_s7_anticheat_games_are_read_and_anticheat_is_copied_verbatim(tmp_path, maps):
    anticheat = [
        {"system": "battleye", "evidence": ["BattlEye"]},
        {"system": "easyanticheat", "evidence": ["(curated)", "EasyAntiCheat"]},
    ]
    report, _ = one_file(tmp_path, maps, SPARKING_GUS, GUS, anticheat=anticheat)
    assert report["anticheat"] == anticheat
    assert [m["map_id"] for m in report["maps"]] == [UNREAL]
    assert report["status"] == "mapped"


def test_s7_no_anticheat_is_an_empty_list(tmp_path, maps):
    report, _ = one_file(tmp_path, maps, SPARKING_GUS, GUS)
    assert report["anticheat"] == []


# ---------------------------------------------------------------------------- issue shapes


def test_a8_issue_key_sets(tmp_path, maps):
    reg = write(tmp_path / "pfx" / "user.reg", b"WINE\n")
    big = bad_file(tmp_path, "oversized")
    first = write(tmp_path / "a" / GUS, gus("sg.ShadowQuality=1"))
    second = write(tmp_path / "b" / GUS, gus("sg.ShadowQuality=2"))
    report = report_for(maps, [(reg, "registry"), (big, "ini"), (first, "ini"), (second, "ini")])
    codes = sorted(issue["code"] for issue in report["issues"])
    assert codes == ["conflicting_files", "registry_not_read", "settings_unreadable"]
    for issue in report["issues"]:
        assert set(issue) == ISSUE_KEYS[issue["code"]], issue["code"]
