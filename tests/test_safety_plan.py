# Contracts for deckforge.safety.plan, Change and preview (docs/specs/safety-module.md:
# AC1, AC4, AC7 and clarifier answers A1-A4, A6, A10). Written before the implementation:
# src/deckforge/safety.py does not exist yet. Fixtures: test_safety_support.py.
#
# plan(card, target_path, new_bytes) -> Change
#   Pre:  card has discover's shape; target_path is a str; new_bytes is bytes.
#   Post: returns a frozen dataclass Change whose first four fields are, in order,
#         appid, path, old_sha256, new_bytes (A4): appid == card["appid"], path ==
#         target_path, old_sha256 == sha256 hex of the file's bytes at plan time,
#         new_bytes == new_bytes. Assigning a field raises FrozenInstanceError.
#   Post: refusals raise SafetyError with .code, and nothing on disk changes (AC4: "before
#         anything is touched"; checked with the B9 lstat detector):
#           bad_path              "", a relative path, a path holding a ".." part (even
#                                 when the card lists exactly that string)
#           not_a_settings_file   not equal, as a string, to a card entry's path (A3):
#                                 game program/data files, saves, Steam's config/*.vdf and
#                                 userdata/**/localconfig.vdf, "//" or "/./" spellings,
#                                 another letter case
#           registry_file         an entry of kind "registry" (user.reg)
#           kind_not_writable     any kind other than "ini" (boot_config, unknown) (A1)
#           engine_ini_anticheat  Engine.ini, any letter case, unless the card's
#                                 tier_i_eligible is True (A2); always on a card that
#                                 lists anti-cheat
#           symlink               the last part is a link (to a file, or dangling)
#           outside_game          realpath(target) is outside realpath(install_path) and
#                                 realpath(prefix_path) (a parent-folder link leading
#                                 out, or a forged entry); links in parent folders that
#                                 stay inside are allowed (A3)
#           file_missing          the target does not exist; the message holds "launch
#                                 the game once, then retry"; nothing is created (AC7)
#           too_large             the target or new_bytes is over 1 MiB (exactly 1 MiB is
#                                 still accepted, A10)
#         A target that is a folder is refused (some SafetyError).
#   Inv:  GameUserSettings.ini and config.ini are allowed on a card with anti-cheat (Q1).
#   Inv:  Steam's own files never appear in detect's settings_files, even when copies of
#         config.vdf / localconfig.vdf sit inside the install and Saved/Config folders.
#   Pre:  hard links (A6) are refused (hard_link) by plan or apply.
#
# preview(changes) -> list[dict]
#   Post: one dict per Change, in order, with exactly the keys path, diff, old_sha256,
#         new_sha256, warnings. Hashes are sha256 hex of the file now and of new_bytes.
#   Post: diff is a unified diff ("---", "+++", "@@" lines) of the decoded texts: a BOM
#         picks UTF-8 or UTF-16 (LE/BE) and is not shown; otherwise strict UTF-8. If either
#         side fails to decode, diff is None and warnings holds "not_text" (A10).
#   Inv:  writes nothing (AC1): the B9 lstat detector shows no change anywhere, and no
#         file is opened for writing.
#   (Cloud warnings, AC11, are in test_safety_guards.py.)

import dataclasses
import os

import pytest
from test_discover_output import record_opens
from test_discover_output import snapshot as tree_state
from test_safety_support import (
    APPID,
    CONFIG_INI,
    CONFIG_NEW,
    ENGINE_NEW,
    FILE_MISSING_TEXT,
    GUS_NEW,
    MiB,
    backup_folders,
    make_deck,
    refusal,
    refused_at_plan_or_apply,
    sha,
    warning_codes,
    with_anticheat,
    with_entry,
)

from deckforge import detect, safety

WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND


# ---------------------------------------------------------------------------- accepted


@pytest.mark.parametrize(
    ("key", "new"), [("config", CONFIG_NEW), ("gus", GUS_NEW), ("engine", ENGINE_NEW)]
)
def test_ac4_plan_accepts_each_ini_settings_file_of_the_card(tmp_path, key, new):
    deck = make_deck(tmp_path)
    target = deck.files[key]
    change = safety.plan(deck.card, str(target), new)
    assert change.appid == APPID
    assert change.path == str(target)
    assert change.old_sha256 == sha(target.read_bytes())
    assert change.new_bytes == new


def test_a4_change_is_a_frozen_dataclass_with_the_four_fields_in_order(tmp_path):
    deck = make_deck(tmp_path)
    change = safety.plan(deck.card, str(deck.config), CONFIG_NEW)
    assert dataclasses.is_dataclass(change)
    names = [item.name for item in dataclasses.fields(change)]
    assert names[:4] == ["appid", "path", "old_sha256", "new_bytes"]
    with pytest.raises(dataclasses.FrozenInstanceError):
        change.new_bytes = b"other"


def test_a4_old_sha256_is_taken_from_the_file_at_plan_time(tmp_path):
    deck = make_deck(tmp_path)
    first = safety.plan(deck.card, str(deck.config), CONFIG_NEW)
    deck.config.write_bytes(b"[Render]\r\nUpscaler=XeSS\r\n")
    second = safety.plan(deck.card, str(deck.config), CONFIG_NEW)
    assert first.old_sha256 == sha(CONFIG_INI)
    assert second.old_sha256 == sha(b"[Render]\r\nUpscaler=XeSS\r\n")


@pytest.mark.parametrize("key", ["config", "gus"])
def test_q1_game_settings_files_are_allowed_on_a_card_with_anticheat(tmp_path, key):
    deck = make_deck(tmp_path)
    change = safety.plan(with_anticheat(deck.card), str(deck.files[key]), b"[S]\nA=1\n")
    assert change.path == str(deck.files[key])


def test_a3_a_link_in_a_parent_folder_is_allowed(tmp_path):
    deck = make_deck(tmp_path, layout="linked")
    assert deck.library.is_symlink()
    change = safety.plan(deck.card, str(deck.config), CONFIG_NEW)
    assert change.path == str(deck.config)


@pytest.mark.parametrize("layout", ["sd", "flatpak"])
def test_unusual_setup_sd_card_and_flatpak_paths_come_from_the_card(tmp_path, layout):
    deck = make_deck(tmp_path, layout=layout)
    for path in deck.writable:
        assert safety.plan(deck.card, str(path), b"x=1\n").path == str(path)


def test_a10_new_bytes_of_exactly_one_mib_are_accepted(tmp_path):
    deck = make_deck(tmp_path)
    change = safety.plan(deck.card, str(deck.config), b"a" * MiB)
    assert len(change.new_bytes) == MiB


def test_ac4_plan_touches_nothing_when_it_accepts(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    before = tree_state(deck.base)
    opens = record_opens(monkeypatch)
    safety.plan(deck.card, str(deck.config), CONFIG_NEW)
    monkeypatch.undo()
    assert tree_state(deck.base) == before
    assert not _write_opens(opens)


# ---------------------------------------------------------------------------- refusals


@pytest.mark.parametrize("key", ["exe", "pak", "shipping", "save", "sysreg"])
def test_ac4_game_program_data_and_save_files_are_not_settings_files(tmp_path, key):
    deck = make_deck(tmp_path)
    before = tree_state(deck.base)
    with pytest.raises(safety.SafetyError) as info:
        safety.plan(deck.card, str(deck.files[key]), b"x")
    allowed = {"not_a_settings_file"} | ({"registry_file"} if key == "sysreg" else set())
    assert info.value.code in allowed
    assert tree_state(deck.base) == before


@pytest.mark.parametrize("key", ["configvdf", "localconfig", "remotecache"])
def test_ac4_steam_own_files_are_refused_as_not_a_settings_file(tmp_path, key):
    deck = make_deck(tmp_path)
    before = tree_state(deck.base)
    refusal("not_a_settings_file", safety.plan, deck.card, str(deck.files[key]), b"x")
    assert tree_state(deck.base) == before


def test_ac4_steam_own_files_never_appear_in_settings_files(tmp_path):
    deck = make_deck(tmp_path)
    saved_config = deck.gus.parent
    for folder in (deck.install, saved_config, deck.prefix):
        (folder / "config.vdf").write_bytes(deck.files["configvdf"].read_bytes())
        (folder / "localconfig.vdf").write_bytes(deck.files["localconfig"].read_bytes())
    fields, _notes = detect.card_fields(
        APPID,
        kind="game",
        state_flags=4,
        install_path=deck.card["install_path"],
        prefix_path=deck.card["prefix_path"],
    )
    paths = [entry["path"] for entry in fields["settings_files"]]
    assert paths, "the fixture must still list settings files"
    assert not [path for path in paths if path.lower().endswith(".vdf")]
    card = {**deck.card, **fields}
    for folder in (deck.install, saved_config):
        for name in ("config.vdf", "localconfig.vdf"):
            refusal("not_a_settings_file", safety.plan, card, str(folder / name), b"x")


def test_ac4_the_registry_entry_is_refused_as_registry_file(tmp_path):
    deck = make_deck(tmp_path)
    before = tree_state(deck.base)
    refusal("registry_file", safety.plan, deck.card, str(deck.files["userreg"]), b"x")
    assert tree_state(deck.base) == before


def test_a1_unity_boot_config_is_kind_not_writable(tmp_path):
    deck = make_deck(tmp_path)
    before = tree_state(deck.base)
    refusal("kind_not_writable", safety.plan, deck.card, str(deck.files["boot"]), b"x=1\n")
    assert tree_state(deck.base) == before


def test_a1_an_unknown_kind_is_kind_not_writable(tmp_path):
    deck = make_deck(tmp_path)
    other = deck.install / "settings.json"
    other.write_bytes(b"{}")
    card = with_entry(deck.card, other, kind="json")
    refusal("kind_not_writable", safety.plan, card, str(other), b"{}")


def test_ac4_engine_ini_on_a_card_with_anticheat_is_refused(tmp_path):
    deck = make_deck(tmp_path)
    before = tree_state(deck.base)
    card = with_anticheat(deck.card)
    refusal("engine_ini_anticheat", safety.plan, card, str(deck.engine), ENGINE_NEW)
    assert tree_state(deck.base) == before


@pytest.mark.parametrize("eligible", [False, None, 1, "true", "missing"])
def test_a2_engine_ini_needs_tier_i_eligible_exactly_true(tmp_path, eligible):
    deck = make_deck(tmp_path)
    card = {**deck.card, "anticheat": []}
    if eligible == "missing":
        del card["tier_i_eligible"]
    else:
        card["tier_i_eligible"] = eligible
    refusal("engine_ini_anticheat", safety.plan, card, str(deck.engine), ENGINE_NEW)


@pytest.mark.parametrize("name", ["ENGINE.INI", "engine.ini", "Engine.INI"])
def test_ac4_engine_ini_check_ignores_letter_case(tmp_path, name):
    deck = make_deck(tmp_path)
    other = deck.engine.parent / name
    other.write_bytes(b"[SystemSettings]\n")
    card = with_entry(deck.card, other)
    card["settings_files"][-1]["class"] = "P"
    refusal("engine_ini_anticheat", safety.plan, with_anticheat(card), str(other), b"x")
    refusal(
        "engine_ini_anticheat",
        safety.plan,
        {**card, "tier_i_eligible": False},
        str(other),
        b"x",
    )
    assert safety.plan(card, str(other), b"[S]\n").path == str(other)


def test_ac4_bad_path_empty(tmp_path):
    deck = make_deck(tmp_path)
    refusal("bad_path", safety.plan, with_entry(deck.card, ""), "", b"x")


def test_ac4_bad_path_relative_even_when_the_card_lists_it(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    monkeypatch.chdir(deck.install)
    refusal("bad_path", safety.plan, with_entry(deck.card, "config.ini"), "config.ini", b"x")


def test_ac4_bad_path_dot_dot_even_when_the_card_lists_it(tmp_path):
    deck = make_deck(tmp_path)
    dotted = f"{deck.install}/FakeGame_Data/../config.ini"
    before = tree_state(deck.base)
    refusal("bad_path", safety.plan, with_entry(deck.card, dotted), dotted, CONFIG_NEW)
    assert tree_state(deck.base) == before


@pytest.mark.parametrize("spelling", ["double_slash", "dot", "trailing_slash", "case"])
def test_a3_target_must_equal_the_card_entry_string_exactly(tmp_path, spelling):
    deck = make_deck(tmp_path)
    text = str(deck.config)
    variant = {
        "double_slash": text.replace("/Fake Game/", "/Fake Game//"),
        "dot": text.replace("/Fake Game/", "/Fake Game/./"),
        "trailing_slash": text + "/",
        "case": text.replace("config.ini", "Config.ini"),
    }[spelling]
    assert variant != text
    with pytest.raises(safety.SafetyError) as info:
        safety.plan(deck.card, variant, CONFIG_NEW)
    assert info.value.code == "not_a_settings_file"


def test_ac4_a_link_as_last_part_is_refused_as_symlink(tmp_path):
    deck = make_deck(tmp_path)
    link = deck.install / "linked.ini"
    link.symlink_to(deck.config)
    before = tree_state(deck.base)
    refusal("symlink", safety.plan, with_entry(deck.card, link), str(link), CONFIG_NEW)
    assert tree_state(deck.base) == before
    assert deck.config.read_bytes() == CONFIG_INI


def test_ac4_a_dangling_link_is_refused_as_symlink(tmp_path):
    deck = make_deck(tmp_path)
    link = deck.install / "dangling.ini"
    link.symlink_to(deck.install / "nowhere.ini")
    refusal("symlink", safety.plan, with_entry(deck.card, link), str(link), b"x")
    assert not (deck.install / "nowhere.ini").exists()


def test_a3_a_parent_link_leading_out_of_the_game_is_outside_game(tmp_path):
    deck = make_deck(tmp_path)
    elsewhere = deck.base / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "config.ini").write_bytes(CONFIG_INI)
    (deck.install / "cfg").symlink_to(elsewhere, target_is_directory=True)
    target = deck.install / "cfg" / "config.ini"
    before = tree_state(deck.base)
    refusal("outside_game", safety.plan, with_entry(deck.card, target), str(target), b"x")
    assert tree_state(deck.base) == before


def test_a3_a_forged_entry_outside_install_and_prefix_is_outside_game(tmp_path):
    deck = make_deck(tmp_path)
    outside = deck.home / "Fake Game" / "config.ini"
    outside.parent.mkdir(parents=True)
    outside.write_bytes(CONFIG_INI)
    refusal("outside_game", safety.plan, with_entry(deck.card, outside), str(outside), b"x")


def test_a3_a_folder_target_is_refused(tmp_path):
    deck = make_deck(tmp_path)
    folder = deck.install / "folder.ini"
    folder.mkdir()
    before = tree_state(deck.base)
    with pytest.raises(safety.SafetyError):
        safety.plan(with_entry(deck.card, folder), str(folder), b"x")
    assert tree_state(deck.base) == before


def test_ac7_missing_file_is_refused_with_the_retry_text_and_not_created(tmp_path):
    deck = make_deck(tmp_path)
    deck.gus.unlink()
    before = tree_state(deck.base)
    error = refusal("file_missing", safety.plan, deck.card, str(deck.gus), GUS_NEW)
    assert FILE_MISSING_TEXT in str(error)
    assert not os.path.lexists(deck.gus)
    assert tree_state(deck.base) == before


def test_a10_a_target_over_one_mib_is_too_large(tmp_path):
    deck = make_deck(tmp_path)
    with deck.config.open("wb") as handle:
        handle.truncate(MiB + 1)
    refusal("too_large", safety.plan, deck.card, str(deck.config), CONFIG_NEW)


def test_a10_new_bytes_over_one_mib_are_too_large(tmp_path):
    deck = make_deck(tmp_path)
    before = tree_state(deck.base)
    refusal("too_large", safety.plan, deck.card, str(deck.config), b"a" * (MiB + 1))
    assert tree_state(deck.base) == before


def test_a6_a_target_with_a_second_hard_link_is_refused(tmp_path):
    deck = make_deck(tmp_path)
    os.link(deck.config, deck.install / "config-hardlink.ini")
    refused_at_plan_or_apply("hard_link", deck, [(deck.config, CONFIG_NEW)])
    assert deck.config.read_bytes() == CONFIG_INI
    assert backup_folders(deck) == []


# ---------------------------------------------------------------------------- preview


def _write_opens(opens: list[tuple[str, object, object]]) -> list[tuple[str, object, object]]:
    found = []
    for kind, path, mode in opens:
        by_flags = kind == "os.open" and isinstance(mode, int) and mode & WRITE_FLAGS
        by_mode = isinstance(mode, str) and any(flag in mode for flag in "wax+")
        if by_flags or by_mode:
            found.append((kind, path, mode))
    return found


def test_ac1_preview_lists_path_diff_and_both_hashes(tmp_path):
    deck = make_deck(tmp_path)
    change = safety.plan(deck.card, str(deck.config), CONFIG_NEW)
    [entry] = safety.preview([change])
    assert set(entry) == {"path", "diff", "old_sha256", "new_sha256", "warnings"}
    assert entry["path"] == str(deck.config)
    assert entry["old_sha256"] == sha(CONFIG_INI)
    assert entry["new_sha256"] == sha(CONFIG_NEW)
    diff = entry["diff"]
    lines = diff.splitlines()
    assert any(line.startswith("---") for line in lines)
    assert any(line.startswith("+++") for line in lines)
    assert any(line.startswith("@@") for line in lines)
    assert any(line.startswith("-Upscaler=FSR") for line in lines)
    assert any(line.startswith("+Upscaler=DLSS") for line in lines)
    assert not any(line[:1] in "+-" and "FrameGen=Off" in line for line in lines)
    assert "not_text" not in warning_codes(entry["warnings"])


def test_ac1_preview_gives_one_entry_per_change_in_order(tmp_path):
    deck = make_deck(tmp_path)
    changes = [
        safety.plan(deck.card, str(deck.gus), GUS_NEW),
        safety.plan(deck.card, str(deck.config), CONFIG_NEW),
        safety.plan(deck.card, str(deck.engine), ENGINE_NEW),
    ]
    result = safety.preview(changes)
    assert [entry["path"] for entry in result] == [
        str(deck.gus),
        str(deck.config),
        str(deck.engine),
    ]
    assert [entry["new_sha256"] for entry in result] == [
        sha(GUS_NEW),
        sha(CONFIG_NEW),
        sha(ENGINE_NEW),
    ]


def test_ac1_preview_writes_nothing(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    changes = [safety.plan(deck.card, str(path), b"[X]\nY=1\n") for path in deck.writable]
    before = tree_state(deck.base)
    opens = record_opens(monkeypatch)
    safety.preview(changes)
    monkeypatch.undo()
    assert tree_state(deck.base) == before
    assert not _write_opens(opens)


@pytest.mark.parametrize("encoding", ["utf-8-sig", "utf-16-le", "utf-16-be"])
def test_a10_diff_decodes_using_the_bom(tmp_path, encoding):
    deck = make_deck(tmp_path)
    bom = {"utf-8-sig": b"\xef\xbb\xbf", "utf-16-le": b"\xff\xfe", "utf-16-be": b"\xfe\xff"}
    codec = "utf-8" if encoding == "utf-8-sig" else encoding
    old = bom[encoding] + "[Render]\r\nUpscaler=FSR\r\nNäme=Ünï\r\n".encode(codec)
    new = bom[encoding] + "[Render]\r\nUpscaler=DLSS\r\nNäme=Ünï\r\n".encode(codec)
    deck.config.write_bytes(old)
    [entry] = safety.preview([safety.plan(deck.card, str(deck.config), new)])
    assert entry["diff"] is not None
    assert "\ufeff" not in entry["diff"]
    lines = entry["diff"].splitlines()
    assert any(line.startswith("+Upscaler=DLSS") for line in lines)
    assert any(line.startswith("-Upscaler=FSR") for line in lines)
    assert "not_text" not in warning_codes(entry["warnings"])
    assert entry["old_sha256"] == sha(old)


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (b"[Render]\nName=caf\xe9\n", b"[Render]\nName=cafe\n"),  # Latin-1 old side
        (CONFIG_INI, b"[Render]\nName=caf\xe9\n"),  # Latin-1 new side
        (b"[Render]\nX=\xed\xa0\x80\n", CONFIG_NEW),  # a surrogate: not strict UTF-8
        (b"\x00\x01\x02\xff\xfe\xfd\x80", CONFIG_NEW),  # binary, no BOM at the start
    ],
)
def test_a10_undecodable_side_gives_null_diff_and_not_text(tmp_path, old, new):
    deck = make_deck(tmp_path)
    deck.config.write_bytes(old)
    [entry] = safety.preview([safety.plan(deck.card, str(deck.config), new)])
    assert entry["diff"] is None
    assert "not_text" in warning_codes(entry["warnings"])
    assert entry["old_sha256"] == sha(old)
    assert entry["new_sha256"] == sha(new)
