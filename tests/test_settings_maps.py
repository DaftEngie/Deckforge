# Contracts for deckforge.settings.load_maps and the built-in maps (docs/specs/settings-read.md,
# S2 and S3, with clarifier answers 1, 2, 3, 5, 9 and 13, which win over S2/S3).
#
# load_maps() -> list[dict]
#   Pre:  none. Answer 9: the maps are the *.json files of the `maps` folder next to
#         settings.py. No path constant is named by the spec, so these tests never patch the
#         module. To give load_maps other maps they copy src/deckforge into tmp_path with a
#         `maps` folder of their own and call load_maps in a child Python whose
#         settings.__file__ is checked to be the copy.
#   Post: the maps, sorted by "id" (not by file name). Files not named *.json are ignored.
#   Post: zero maps (empty folder, missing folder, or no *.json file) -> SettingsError.
#   Post: every map is validated. SettingsError, whose message names the file and the
#         problem, for: a missing field (map: id, engine, label, match, knobs; match:
#         file_name, sections, keys; knob: id, label, section, key, type, confidence,
#         source); an unknown type or confidence; an empty source; a level/enum/bool knob
#         without values (missing or empty list); a percent knob without min <= max (min or
#         max missing, or min > max); duplicate knob ids in one map; duplicate map ids.
#         ASSUMED (the spec gives no wording): "names the problem" means the message holds
#         the offending field name, value or id; "names the file" means it holds the file's
#         base name.
#   Post: types are level, percent, enum, bool and number (answer 1: float with optional
#         min/max, no values needed). min == max is valid for percent.
#
# Built-in maps, S3 with answers 1, 2, 3, 5, 13
#   Inv:  the files unreal-scalability.json, re-graphics-section.json and
#         re-appoption-section.json in src/deckforge/maps exist, each file's "id" is its
#         base name, and load_maps returns exactly these three.
#   Inv:  unreal-scalability: match GameUserSettings.ini, sections [ScalabilityGroups], no
#         keys. One knob per sg.* key of S3 in [ScalabilityGroups]. sg.ResolutionQuality is
#         percent 10-100; the other ten are level "0"-"4" (answer 13 adds 4 = Cinematic).
#         documented for PostProcess, Shadow, Texture, Effects; likely for the rest.
#   Inv:  re-graphics-section: match config.ini, sections [Graphics], keys
#         [[Graphics, ShaderConvertVersion]]. Knobs: exactly the matched and likely rows of
#         docs/research/wilds-settings-map.md, one per concrete key (answer 3: SpeedTreeWind_*
#         is Branch, Global, Leaf; Bloom and VolumetricFogControl are two keys each). No
#         AOSetting knob. Confidence copied from the doc. [Graphics/FSR3] Sharpness is number
#         without bounds; ImageQualityRate is enum ["1"] (answer 1). Values only as seen:
#         an enum lists the fixture value and nothing beyond the doc's other sightings; a
#         bool is one of the pairs False/True, false/true, OFF/ON (false first) holding the
#         seen value (answer 2). No level type (answer 2: level only for Unreal).
#   Inv:  re-appoption-section: match config.ini, sections [AppOption], keys
#         [[AppOption, UpscalingAlgorithm]]. Exactly the eight keys of answer 5 with that
#         table's types and values, all likely, source exactly the answer-5 note.
#   Inv:  in every map: knob ids unique, no wildcard in a key, every source non-empty,
#         a single-valued knob is never level (answer 2).

import json
import re

import pytest
from test_settings_support import (
    BOOL_PAIRS,
    BUILTIN_IDS,
    DD2_KNOBS,
    DD2_SOURCE,
    MAPS_DIR,
    RE_APPOPTION,
    RE_GRAPHICS,
    UNREAL,
    UNREAL_DOCUMENTED,
    UNREAL_KEYS,
    UNREAL_LEVEL_KEYS,
    WILDS_ALSO_SEEN,
    WILDS_KNOBS,
    WILDS_MATCHED,
    builtin_map,
    copy_package,
    knob,
    load_maps_in,
    make_map,
    map_knob,
)

from deckforge import settings

TYPES = {"level", "percent", "enum", "bool", "number"}
CONFIDENCES = {"documented", "matched", "likely"}


def valid_map(map_id: str = "test-map") -> dict:
    return make_map(
        map_id,
        keys=[["S", "lvl"]],
        knobs=[
            knob("lvl", "lvl", "level", values=["0", "1"]),
            knob("pct", "pct", "percent", min=10, max=100),
            knob("en", "en", "enum", values=["a"]),
            knob("bo", "bo", "bool", values=["False", "True"]),
            knob("num", "num", "number"),
            knob("numb", "numb", "number", min=0, max=1),
        ],
    )


def load_one(tmp_path, content) -> dict:
    pkg = copy_package(tmp_path, {"bad-map.json": content})
    return load_maps_in(pkg, tmp_path)


def assert_error(result: dict, *names: str) -> None:
    assert "error" in result, f"load_maps accepted the map: {result.get('ids')}"
    message = result["error"]
    for name in names:
        assert name in message, f"{name!r} not named in {message!r}"


def drop(obj: dict, path: tuple) -> dict:
    target = obj
    for step in path[:-1]:
        target = target[step]
    del target[path[-1]]
    return obj


def put_value(obj: dict, path: tuple, value) -> dict:
    target = obj
    for step in path[:-1]:
        target = target[step]
    target[path[-1]] = value
    return obj


# ---------------------------------------------------------------------------- S2 / answer 9


def test_s2_a9_valid_maps_load_sorted_by_id_and_other_files_are_ignored(tmp_path):
    maps = {
        "a.json": valid_map("b-map"),
        "z.json": valid_map("a-map"),
        "notes.txt": "not json {",
        "draft.json.bak": "not json {",
    }
    result = load_maps_in(copy_package(tmp_path, maps), tmp_path)
    assert result.get("ids") == ["a-map", "b-map"], result


def test_s2_percent_with_min_equal_to_max_is_valid(tmp_path):
    content = make_map(knobs=[knob("pct", "pct", "percent", min=50, max=50)])
    assert load_one(tmp_path, content).get("ids") == ["test-map"]


@pytest.mark.parametrize(
    "path",
    [
        ("id",),
        ("engine",),
        ("label",),
        ("match",),
        ("knobs",),
        ("match", "file_name"),
        ("match", "sections"),
        ("match", "keys"),
        ("knobs", 0, "id"),
        ("knobs", 0, "label"),
        ("knobs", 0, "section"),
        ("knobs", 0, "key"),
        ("knobs", 0, "type"),
        ("knobs", 0, "confidence"),
        ("knobs", 0, "source"),
    ],
    ids=lambda path: ".".join(str(step) for step in path),
)
def test_s2_missing_field_is_named_with_the_file(tmp_path, path):
    result = load_one(tmp_path, drop(valid_map(), path))
    assert_error(result, "bad-map.json", str(path[-1]))


def test_s2_unknown_type_is_named_with_the_file(tmp_path):
    result = load_one(tmp_path, put_value(valid_map(), ("knobs", 2, "type"), "slider"))
    assert_error(result, "bad-map.json", "slider")


def test_s2_unknown_confidence_is_named_with_the_file(tmp_path):
    result = load_one(tmp_path, put_value(valid_map(), ("knobs", 1, "confidence"), "guessed"))
    assert_error(result, "bad-map.json", "guessed")


def test_s2_empty_source_is_named_with_the_file(tmp_path):
    result = load_one(tmp_path, put_value(valid_map(), ("knobs", 3, "source"), ""))
    assert_error(result, "bad-map.json", "source")


@pytest.mark.parametrize("knob_type", ["level", "enum", "bool"])
@pytest.mark.parametrize("how", ["missing", "empty"])
def test_s2_level_enum_bool_without_values_is_named_with_the_file(tmp_path, knob_type, how):
    bad = knob("novals", "novals", knob_type, values=["x", "y"])
    if how == "missing":
        del bad["values"]
    else:
        bad["values"] = []
    content = valid_map()
    content["knobs"].append(bad)
    assert_error(load_one(tmp_path, content), "bad-map.json", "values")


@pytest.mark.parametrize(
    "bounds",
    [{"min": 100, "max": 10}, {"max": 100}, {"min": 10}, {}],
    ids=["min-above-max", "no-min", "no-max", "no-bounds"],
)
def test_s2_percent_without_min_le_max_is_named_with_the_file(tmp_path, bounds):
    bad = knob("pct2", "pct2", "percent", **bounds)
    content = valid_map()
    content["knobs"].append(bad)
    result = load_one(tmp_path, content)
    assert "error" in result, result
    assert "bad-map.json" in result["error"]
    assert "min" in result["error"] or "max" in result["error"], result["error"]


def test_s2_duplicate_knob_ids_in_one_map_are_named_with_the_file(tmp_path):
    content = valid_map()
    content["knobs"].append(knob("dup-knob", "k1"))
    content["knobs"].append(knob("dup-knob", "k2"))
    assert_error(load_one(tmp_path, content), "bad-map.json", "dup-knob")


def test_s2_duplicate_map_ids_across_files_are_named(tmp_path):
    maps = {"first.json": valid_map("same-id"), "second.json": valid_map("same-id")}
    result = load_maps_in(copy_package(tmp_path, maps), tmp_path)
    assert "error" in result, result
    assert "same-id" in result["error"]
    assert "first.json" in result["error"] or "second.json" in result["error"]


@pytest.mark.parametrize(
    "maps",
    [{}, None, {"readme.txt": "maps go here"}],
    ids=["empty-folder", "no-folder", "no-json-file"],
)
def test_a9_zero_maps_raises_settings_error(tmp_path, maps):
    result = load_maps_in(copy_package(tmp_path, maps), tmp_path)
    assert "error" in result, result


def test_a9_the_copied_package_with_the_shipped_maps_loads_them(tmp_path):
    shipped = {path.name: path.read_text(encoding="utf-8") for path in MAPS_DIR.glob("*.json")}
    result = load_maps_in(copy_package(tmp_path, shipped), tmp_path)
    assert result.get("ids") == BUILTIN_IDS, result


# ---------------------------------------------------------------------------- S3 general


def test_s3_the_three_map_files_exist_with_their_ids():
    for map_id in BUILTIN_IDS:
        path = MAPS_DIR / f"{map_id}.json"
        assert path.is_file(), path
        assert json.loads(path.read_text(encoding="utf-8"))["id"] == map_id


def test_s3_load_maps_returns_exactly_the_builtin_maps_sorted_by_id():
    maps = settings.load_maps()
    assert isinstance(maps, list)
    assert all(isinstance(m, dict) for m in maps)
    assert [m["id"] for m in maps] == BUILTIN_IDS


def test_s3_a2_a3_every_builtin_knob_is_well_formed():
    for map_dict in settings.load_maps():
        ids = [k["id"] for k in map_dict["knobs"]]
        assert len(ids) == len(set(ids)), map_dict["id"]
        pairs = [(k["section"], k["key"]) for k in map_dict["knobs"]]
        assert len(pairs) == len(set(pairs)), f"{map_dict['id']}: one key, two knobs"
        for k in map_dict["knobs"]:
            where = f"{map_dict['id']}/{k['id']}"
            assert k["type"] in TYPES, where
            assert k["confidence"] in CONFIDENCES, where
            assert isinstance(k["source"], str) and k["source"].strip(), where
            assert isinstance(k["label"], str) and k["label"].strip(), where
            assert "*" not in k["key"] and "?" not in k["key"], where
            if k["type"] in ("level", "enum", "bool"):
                assert k["values"], where
                assert all(isinstance(v, str) for v in k["values"]), where
            if k["type"] == "level":
                assert len(k["values"]) > 1, f"{where}: one seen value is enum (answer 2)"
            if k["type"] == "bool":
                assert k["values"] in BOOL_PAIRS, where
            if k["type"] == "percent":
                assert k["min"] <= k["max"], where


def test_a2_level_type_is_used_only_by_the_unreal_map():
    for map_dict in settings.load_maps():
        if map_dict["id"] != UNREAL:
            assert [k["key"] for k in map_dict["knobs"] if k["type"] == "level"] == []


# ---------------------------------------------------------------------------- unreal


def test_s3_unreal_fingerprint():
    unreal = builtin_map(settings.load_maps(), UNREAL)
    assert unreal["match"] == {
        "file_name": "GameUserSettings.ini",
        "sections": ["ScalabilityGroups"],
        "keys": [],
    }
    assert unreal["engine"] == "unreal"


def test_s3_unreal_has_one_knob_per_scalability_key():
    unreal = builtin_map(settings.load_maps(), UNREAL)
    assert sorted((k["section"], k["key"]) for k in unreal["knobs"]) == sorted(
        ("ScalabilityGroups", key) for key in UNREAL_KEYS
    )


def test_s3_a13_unreal_resolution_quality_is_percent_10_to_100():
    k = map_knob(
        builtin_map(settings.load_maps(), UNREAL), "ScalabilityGroups", "sg.ResolutionQuality"
    )
    assert k["type"] == "percent"
    assert (k["min"], k["max"]) == (10, 100)


@pytest.mark.parametrize("key", UNREAL_LEVEL_KEYS)
def test_s3_a13_unreal_level_keys_have_values_0_to_4(key):
    k = map_knob(builtin_map(settings.load_maps(), UNREAL), "ScalabilityGroups", key)
    assert k["type"] == "level"
    assert k["values"] == ["0", "1", "2", "3", "4"]


@pytest.mark.parametrize("key", UNREAL_KEYS)
def test_s3_unreal_confidence_documented_only_for_the_four_epic_groups(key):
    k = map_knob(builtin_map(settings.load_maps(), UNREAL), "ScalabilityGroups", key)
    assert k["confidence"] == ("documented" if key in UNREAL_DOCUMENTED else "likely")


# ---------------------------------------------------------------------------- Wilds


def test_s3_wilds_fingerprint():
    wilds = builtin_map(settings.load_maps(), RE_GRAPHICS)
    assert wilds["match"]["file_name"].lower() == "config.ini"
    assert wilds["match"]["sections"] == ["Graphics"]
    assert [list(pair) for pair in wilds["match"]["keys"]] == [["Graphics", "ShaderConvertVersion"]]


def test_s3_a3_wilds_knobs_are_exactly_the_matched_and_likely_rows():
    wilds = builtin_map(settings.load_maps(), RE_GRAPHICS)
    assert sorted((k["section"], k["key"]) for k in wilds["knobs"]) == sorted(WILDS_KNOBS)


def test_s3_wilds_ao_setting_is_excluded():
    wilds = builtin_map(settings.load_maps(), RE_GRAPHICS)
    assert [k for k in wilds["knobs"] if k["key"] == "AOSetting"] == []


def test_s3_wilds_reads_only_sections_it_names_and_never_render_config():
    wilds = builtin_map(settings.load_maps(), RE_GRAPHICS)
    sections = {k["section"] for k in wilds["knobs"]}
    assert sections == {"Graphics", "Graphics/FSR3", "Graphics/RayTracing"}


def test_s3_wilds_confidence_follows_the_research_doc():
    wilds = builtin_map(settings.load_maps(), RE_GRAPHICS)
    for k in wilds["knobs"]:
        pair = (k["section"], k["key"])
        assert k["confidence"] == ("matched" if pair in WILDS_MATCHED else "likely"), pair


def test_a1_wilds_sharpness_is_number_without_bounds():
    k = map_knob(builtin_map(settings.load_maps(), RE_GRAPHICS), "Graphics/FSR3", "Sharpness")
    assert k["type"] == "number"
    assert k.get("min") is None
    assert k.get("max") is None


def test_a1_wilds_image_quality_rate_is_enum_1():
    k = map_knob(builtin_map(settings.load_maps(), RE_GRAPHICS), "Graphics", "ImageQualityRate")
    assert k["type"] == "enum"
    assert k["values"] == ["1"]


def test_s3_a2_wilds_values_are_only_values_seen():
    wilds = builtin_map(settings.load_maps(), RE_GRAPHICS)
    for k in wilds["knobs"]:
        pair = (k["section"], k["key"])
        seen = WILDS_KNOBS[pair]
        if k["type"] == "number":
            continue
        assert seen in k["values"], pair
        if k["type"] == "enum":
            assert set(k["values"]) <= {seen} | WILDS_ALSO_SEEN.get(pair, set()), pair
        else:
            assert k["type"] == "bool", pair
            assert k["values"] in BOOL_PAIRS, pair


def test_a3_wilds_bloom_label_is_repeated_on_both_keys():
    wilds = builtin_map(settings.load_maps(), RE_GRAPHICS)
    for key in ("Bloom_Enable", "Bloom_ReductionLevel"):
        assert "Bloom" in map_knob(wilds, "Graphics", key)["label"]


# ---------------------------------------------------------------------------- DD2


def test_s3_dd2_fingerprint():
    dd2 = builtin_map(settings.load_maps(), RE_APPOPTION)
    assert dd2["match"]["file_name"].lower() == "config.ini"
    assert dd2["match"]["sections"] == ["AppOption"]
    assert [list(pair) for pair in dd2["match"]["keys"]] == [["AppOption", "UpscalingAlgorithm"]]


def test_s3_a5_dd2_knobs_are_exactly_the_eight_keys():
    dd2 = builtin_map(settings.load_maps(), RE_APPOPTION)
    assert sorted((k["section"], k["key"]) for k in dd2["knobs"]) == sorted(
        ("AppOption", key) for key in DD2_KNOBS
    )


@pytest.mark.parametrize("key", sorted(DD2_KNOBS))
def test_a5_dd2_knob_type_values_confidence_and_source(key):
    knob_type, values, _ = DD2_KNOBS[key]
    k = map_knob(builtin_map(settings.load_maps(), RE_APPOPTION), "AppOption", key)
    assert k["type"] == knob_type
    if values is None:
        assert k.get("values") in (None, [])
        assert k.get("min") is None
        assert k.get("max") is None
    else:
        assert k["values"] == values
    assert k["confidence"] == "likely"
    assert k["source"] == DD2_SOURCE


@pytest.mark.parametrize(
    "key, line",
    [("SpeedTreeWind_Branch", 91), ("SpeedTreeWind_Global", 92), ("SpeedTreeWind_Leaf", 93)],
)
def test_i20_wilds_speedtreewind_sources_cite_their_real_line(key, line):
    source = map_knob(builtin_map(settings.load_maps(), RE_GRAPHICS), "Graphics", key)["source"]
    assert re.search(rf"(?<!\d){line}(?!\d)", source), source
