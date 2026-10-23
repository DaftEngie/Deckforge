# Contracts for deckforge.safety.restore and list_backups (docs/specs/safety-module.md:
# AC5, AC6, AC10, AC12, AC14 and clarifier answers A5, A11, A12, A19, A20). Written before
# the implementation; fixtures and fakes: test_safety_support.py.
#
# restore(backup_id, *, backup_root, confirm=frozenset(), proc_root="/proc") -> dict
#   Pre:  backup_id names a complete folder <backup_root>/<backup_id>/ made by apply.
#   Post: returns exactly {"backup_id", "restored", "skipped", "new_backup_id"} (A19):
#         backup_id as given; restored and skipped are lists of the manifest's path strings;
#         new_backup_id is None unless "overwrite" was confirmed and used.
#   Post: verification first (AC5): the manifest must exist, parse, and hold for every file
#         a sha256_before and size that the backup copy matches. Otherwise backup_corrupt,
#         and no target is written (also when only the last file's copy is bad).
#   Post: per file (A5), by the current SHA-256:
#           == sha256_before  -> skipped, not written (checked first, so a file whose new
#                                bytes equal its old bytes is skipped)
#           == sha256_after   -> restored: the bytes become the copy's (sha256_before) and
#                                the permission bits become the manifest's mode (AC5, AC10)
#           otherwise         -> changed_since_apply (AC12), and nothing at all is written;
#                                the error carries the A20 sentence and shows the current
#                                content (ASSUMED: as text in str(error) or its attributes).
#   Post: with "overwrite" in confirm (AC12, A19): the current versions are first saved as a
#         new complete backup (new id, A11 format), listed by list_backups, holding the
#         changed file's current bytes; its folder is renamed into place before the first
#         target write; then changed files are overwritten with the originals too.
#   Post: every write goes through a temp file in the target's folder and os.replace
#         (AC3); a target is never written in place.
#   Inv:  restore never deletes (AC14): every path under the Deck (backup root included)
#         that existed before still exists; shutil.rmtree, os.rmdir and os.removedirs are
#         never called; os.unlink / os.remove only touch paths restore itself created.
#   Inv:  restore never creates a settings file (Q5, AC14): a target deleted after apply is
#         refused (file_missing, or changed_since_apply without "overwrite") and stays
#         absent. Nothing new appears outside backup_root.
#   Inv:  an id that is unknown, empty, ".lock", or leads outside backup_root ("..",
#         "../x", "a/b", an absolute path) is refused with a SafetyError (code ASSUMED
#         free) and nothing changes.
#   Crash/error (A5, AC3, AC8): the process dying at any write-side step leaves each
#         target holding its applied or its original bytes, with its mode; running restore
#         again then finishes the job. An OSError at any step raises (SafetyError or the
#         OSError), leaves each target applied-or-original with its mode, leaves no temp
#         file in the target folders, and a second restore finishes the job.
#
# list_backups(backup_root) -> list[dict]
#   Post: one dict per folder in backup_root (not .lock); a complete backup's entry has
#         "backup_id" == its folder name; .tmp-* folders and folders without manifest.json
#         are entries marked incomplete (A5); entries are sorted by backup_id (A12), not
#         by creation order.
#   Inv:  list_backups never deletes or changes anything in backup_root; incomplete folders
#         survive list, apply and restore unchanged (A5).
#
# Round trip (AC6), a fixed-seed property test standing in for Hypothesis (not a project
#   dependency, R8): random change sets over all four fixture layouts (home Steam, SD card
#   with a space and non-English characters, Flatpak, a library reached through a link),
#   random original and new contents (UTF-16 LE/BE with BOM, UTF-8 with BOM, CRLF, LF,
#   mixed and missing line endings, empty, binary, NUL bytes) and random modes (locked ones
#   confirmed with "locked"): apply then restore gives back the starting tree, every byte
#   and permission bit, and the restored/skipped split is the hand-computed one.

import random
import secrets
import shutil
import stat
from pathlib import Path

import pytest
from test_safety_support import (
    CHANGED_TEXT,
    CONFIG_INI,
    CONFIG_NEW,
    ENGINE_INI,
    ENGINE_NEW,
    GUS_INI,
    GUS_NEW,
    ID_PATTERN,
    LAYOUTS,
    Crash,
    Recorder,
    abs_path,
    all_paths,
    backup_copies,
    backup_folders,
    complete_ids,
    content_state,
    copy_holding,
    crash,
    deck_state,
    entry_for,
    error_text,
    is_incomplete,
    make_deck,
    manifest_files,
    mode_of,
    read_manifest,
    record_deletions,
    refusal,
    sha,
    simulate_exit,
    target_folder_names,
    write_manifest,
)

from deckforge import safety

OLD = {"config": CONFIG_INI, "gus": GUS_INI, "engine": ENGINE_INI}
NEW = {"config": CONFIG_NEW, "gus": GUS_NEW, "engine": ENGINE_NEW}
KEYS = ("config", "gus", "engine")
USER_EDIT = b"[Render]\r\nUpscaler=Mine\r\nFrameGen=Off\r\nShadow=High\r\n"


def _apply(deck, keys=KEYS, confirm=frozenset()):
    changes = [safety.plan(deck.card, str(deck.files[key]), NEW[key]) for key in keys]
    return safety.apply(changes, **deck.kw(confirm=confirm))


def _paths(deck, keys):
    return sorted(str(deck.files[key]) for key in keys)


def _outside_backup(deck):
    return content_state(deck.base, skip=[deck.backup_root])


# ---------------------------------------------------------------------------- AC5 restore


def test_ac5_restore_returns_every_file_byte_identical_with_its_mode(tmp_path):
    deck = make_deck(tmp_path)
    deck.gus.chmod(0o600)
    deck.engine.chmod(0o640)
    before = deck_state(deck)
    backup_id = _apply(deck)
    assert [deck.files[key].read_bytes() for key in KEYS] == [NEW[key] for key in KEYS]
    result = safety.restore(backup_id, **deck.rkw())
    assert deck_state(deck) == before
    for key in KEYS:
        assert sha(deck.files[key].read_bytes()) == sha(OLD[key])
    assert (mode_of(deck.config), mode_of(deck.gus), mode_of(deck.engine)) == (
        0o644,
        0o600,
        0o640,
    )
    assert set(result) == {"backup_id", "restored", "skipped", "new_backup_id"}
    assert result["backup_id"] == backup_id
    assert sorted(result["restored"]) == _paths(deck, KEYS)
    assert result["skipped"] == []
    assert result["new_backup_id"] is None


def test_ac10_restore_puts_back_the_mode_recorded_in_the_manifest(tmp_path):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck, ("config",))
    deck.config.chmod(0o600)  # the bytes are still ours; only the mode moved
    safety.restore(backup_id, **deck.rkw())
    assert deck.config.read_bytes() == CONFIG_INI
    assert mode_of(deck.config) == 0o644


def test_ac3_restore_writes_through_a_temp_file_and_replace(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck)
    rec = Recorder(monkeypatch, deck.base)
    safety.restore(backup_id, **deck.rkw())
    monkeypatch.undo()
    for target in map(str, deck.writable):
        hits = [src for op, src, dst in rec.steps if op == "replace" and dst == target]
        assert len(hits) == 1, target
        assert str(Path(hits[0]).parent) == str(Path(target).parent)
        assert not [s for s in rec.steps if s[0] == "write" and s[1] == target]
        assert not Path(hits[0]).exists()


# ---------------------------------------------------------------------------- A5 decisions


def test_a5_a_file_already_back_to_its_original_is_skipped(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck)
    deck.gus.write_bytes(GUS_INI)  # someone already put this one back
    inode = deck.gus.stat().st_ino
    rec = Recorder(monkeypatch, deck.base)
    result = safety.restore(backup_id, **deck.rkw())
    monkeypatch.undo()
    assert sorted(result["restored"]) == _paths(deck, ("config", "engine"))
    assert result["skipped"] == [str(deck.gus)]
    assert result["new_backup_id"] is None
    assert deck.gus.stat().st_ino == inode, "a skipped file is not rewritten"
    assert not [s for s in rec.steps if s[2] == str(deck.gus)]
    for key in KEYS:
        assert deck.files[key].read_bytes() == OLD[key]


def test_a5_a_second_restore_skips_everything_and_writes_nothing(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck)
    safety.restore(backup_id, **deck.rkw())
    before = deck_state(deck)
    rec = Recorder(monkeypatch, deck.base)
    result = safety.restore(backup_id, **deck.rkw())
    monkeypatch.undo()
    assert result["restored"] == []
    assert sorted(result["skipped"]) == _paths(deck, KEYS)
    assert result["new_backup_id"] is None
    assert deck_state(deck) == before
    target_dirs = {str(path.parent) for path in deck.writable}
    assert not [s for s in rec.steps if str(Path(s[1]).parent) in target_dirs]


# ---------------------------------------------------------------------------- AC12 changed


def test_ac12_a20_a_file_changed_since_apply_stops_restore_and_shows_it(tmp_path):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck)
    deck.config.write_bytes(USER_EDIT)
    before = deck_state(deck)
    folders = backup_folders(deck)
    error = refusal("changed_since_apply", safety.restore, backup_id, **deck.rkw())
    said = error_text(error)
    assert CHANGED_TEXT in said
    assert "Upscaler=Mine" in said, "the difference is shown"
    assert str(deck.config) in said
    assert deck_state(deck) == before, "nothing is restored, not even the unchanged files"
    assert deck.gus.read_bytes() == GUS_NEW
    assert backup_folders(deck) == folders, "no new backup without overwrite"


def test_ac12_a19_overwrite_saves_the_current_version_first_then_restores(tmp_path):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck)
    old_backup = content_state(deck.backup_root / backup_id)
    deck.config.write_bytes(USER_EDIT)  # changed since apply
    deck.engine.write_bytes(ENGINE_INI)  # already original: skipped
    result = safety.restore(backup_id, **deck.rkw(confirm=frozenset({"overwrite"})))
    assert set(result) == {"backup_id", "restored", "skipped", "new_backup_id"}
    assert result["backup_id"] == backup_id
    assert sorted(result["restored"]) == _paths(deck, ("config", "gus"))
    assert result["skipped"] == [str(deck.engine)]
    new_id = result["new_backup_id"]
    assert isinstance(new_id, str) and ID_PATTERN.match(new_id), new_id
    assert new_id != backup_id
    assert sorted(backup_folders(deck)) == sorted([backup_id, new_id])
    assert new_id in complete_ids(safety.list_backups(str(deck.backup_root)))
    assert copy_holding(deck, new_id, USER_EDIT).read_bytes() == USER_EDIT
    saved = {item["path"] for item in manifest_files(read_manifest(deck, new_id))}
    assert str(deck.config) in saved
    for key in KEYS:
        assert deck.files[key].read_bytes() == OLD[key]
        assert mode_of(deck.files[key]) == 0o644
    assert content_state(deck.backup_root / backup_id) == old_backup


def test_ac12_the_new_backup_is_complete_before_the_first_target_write(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck, ("config", "gus"))
    deck.config.write_bytes(USER_EDIT)
    rec = Recorder(monkeypatch, deck.base)
    result = safety.restore(backup_id, **deck.rkw(confirm=frozenset({"overwrite"})))
    monkeypatch.undo()
    new_id = result["new_backup_id"]
    final_dir = str(deck.backup_root / new_id)
    renames = [
        i
        for i, (op, src, dst) in enumerate(rec.steps)
        if op in ("rename", "replace") and dst == final_dir and Path(src).name.startswith(".tmp-")
    ]
    targets = {str(deck.config), str(deck.gus)}
    replaces = [
        i for i, (op, _src, dst) in enumerate(rec.steps) if op == "replace" and dst in targets
    ]
    assert len(renames) == 1, "the new backup is built as .tmp-<id> and renamed"
    assert len(replaces) == 2
    assert renames[0] < min(replaces)


# ---------------------------------------------------------------------------- AC5 corrupt


def _spoil(deck, backup_id, how):
    folder = deck.backup_root / backup_id
    manifest = read_manifest(deck, backup_id)
    files = manifest_files(manifest)
    config_item = next(item for item in files if item["path"] == str(deck.config))
    copy = copy_holding(deck, backup_id, CONFIG_INI)
    if how == "manifest_missing":
        (folder / "manifest.json").unlink()
    elif how == "manifest_not_json":
        data = (folder / "manifest.json").read_bytes()
        (folder / "manifest.json").write_bytes(data[: len(data) // 2])
    elif how == "manifest_sha256_before_edited":
        config_item["sha256_before"] = sha(b"something else")
        write_manifest(deck, backup_id, manifest)
    elif how == "manifest_size_edited":
        config_item["size"] = config_item["size"] + 1
        write_manifest(deck, backup_id, manifest)
    elif how == "manifest_sha256_before_removed":
        del config_item["sha256_before"]
        write_manifest(deck, backup_id, manifest)
    elif how == "copy_edited":
        copy.write_bytes(CONFIG_INI.replace(b"FSR", b"XeS"))
    elif how == "copy_appended":
        copy.write_bytes(CONFIG_INI + b"\r\n")
    elif how == "copy_deleted":
        copy.unlink()
    else:
        raise ValueError(how)


CORRUPTIONS = [
    "manifest_missing",
    "manifest_not_json",
    "manifest_sha256_before_edited",
    "manifest_size_edited",
    "manifest_sha256_before_removed",
    "copy_edited",
    "copy_appended",
    "copy_deleted",
]


@pytest.mark.parametrize("how", CORRUPTIONS)
def test_ac5_a_corrupt_backup_is_refused_and_nothing_is_written(tmp_path, how):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck)
    _spoil(deck, backup_id, how)
    lock = deck.backup_root / ".lock"
    lock.touch()
    before = deck_state(deck)
    backup_before = content_state(deck.backup_root, skip=[lock])
    refusal("backup_corrupt", safety.restore, backup_id, **deck.rkw())
    refusal(
        "backup_corrupt",
        safety.restore,
        backup_id,
        **deck.rkw(confirm=frozenset({"overwrite"})),
    )
    assert deck_state(deck) == before
    for key in KEYS:
        assert deck.files[key].read_bytes() == NEW[key]
    assert content_state(deck.backup_root, skip=[lock]) == backup_before, "no new backup"


def test_ac5_the_whole_backup_is_verified_before_the_first_write(tmp_path):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck)  # changes in order config, gus, engine
    copy_holding(deck, backup_id, ENGINE_INI).write_bytes(b"[SystemSettings]\n")
    before = deck_state(deck)
    refusal("backup_corrupt", safety.restore, backup_id, **deck.rkw())
    assert deck_state(deck) == before
    assert deck.config.read_bytes() == CONFIG_NEW


# ---------------------------------------------------------------------------- ids


@pytest.mark.parametrize(
    "shape", ["unknown", "empty", "lock", "dot_dot", "up_and_over", "nested", "absolute"]
)
def test_ac5_an_id_that_is_not_a_backup_in_backup_root_is_refused(tmp_path, shape):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck)
    # A valid-looking backup outside backup_root, reachable as "../evil" or by its path.
    evil = deck.backup_root.parent / "evil"
    shutil.copytree(deck.backup_root / backup_id, evil)
    (deck.backup_root / ".lock").touch()
    nested = deck.backup_root / "a"
    nested.mkdir()
    shutil.copytree(deck.backup_root / backup_id, nested / "b")
    asked = {
        "unknown": f"20991231-235959-{deck.card['appid']}-deadbeef",
        "empty": "",
        "lock": ".lock",
        "dot_dot": "..",
        "up_and_over": "../evil",
        "nested": "a/b",
        "absolute": str(evil),
    }[shape]
    before = deck_state(deck)
    with pytest.raises(safety.SafetyError):
        safety.restore(asked, **deck.rkw())
    assert deck_state(deck) == before
    assert deck.config.read_bytes() == CONFIG_NEW


# ---------------------------------------------------------------------------- AC14 deletes


def _plant_incomplete(deck):
    appid = deck.card["appid"]
    tmp = deck.backup_root / f".tmp-20261022-101010-{appid}-aaaaaaaa"
    tmp.mkdir()
    (tmp / "0").write_bytes(CONFIG_INI)
    bare = deck.backup_root / f"20261022-101011-{appid}-bbbbbbbb"
    bare.mkdir()
    (bare / "0").write_bytes(GUS_INI)
    return [tmp, bare]


def _restore_case(deck, backup_id, case):
    if case == "plain":
        return safety.restore(backup_id, **deck.rkw())
    if case == "overwrite":
        deck.config.write_bytes(USER_EDIT)
        return safety.restore(backup_id, **deck.rkw(confirm=frozenset({"overwrite"})))
    if case == "refused_changed":
        deck.config.write_bytes(USER_EDIT)
        refusal("changed_since_apply", safety.restore, backup_id, **deck.rkw())
        return None
    if case == "refused_corrupt":
        copy_holding(deck, backup_id, GUS_INI).write_bytes(b"x")
        refusal("backup_corrupt", safety.restore, backup_id, **deck.rkw())
        return None
    raise ValueError(case)


def _outside(deck, paths):
    return {rel for rel in paths if not (deck.base / rel).is_relative_to(deck.backup_root)}


@pytest.mark.parametrize("case", ["plain", "overwrite", "refused_changed", "refused_corrupt"])
def test_ac14_restore_never_deletes_anything(tmp_path, monkeypatch, case):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck)
    planted = _plant_incomplete(deck)
    planted_state = [content_state(folder) for folder in planted]
    if case == "overwrite":
        deck.config.write_bytes(USER_EDIT)
    paths_before = all_paths(deck.base)
    absolute_before = {abs_path(deck.base / rel) for rel in paths_before}
    outside_before = _outside(deck, paths_before)
    deletions = record_deletions(monkeypatch)
    _restore_case(deck, backup_id, case)
    monkeypatch.undo()
    paths_after = all_paths(deck.base)
    assert paths_before <= paths_after, sorted(paths_before - paths_after)
    assert not [call for call in deletions if call[0] in ("rmtree", "rmdir", "removedirs")]
    assert not [call for call in deletions if call[1] in absolute_before], deletions
    assert _outside(deck, paths_after) == outside_before, "nothing new outside backup_root"
    assert [content_state(folder) for folder in planted] == planted_state


def test_ac14_q5_restore_never_recreates_a_deleted_settings_file(tmp_path):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck)
    deck.gus.unlink()
    before = _outside_backup(deck)
    with pytest.raises(safety.SafetyError) as info:
        safety.restore(backup_id, **deck.rkw())
    assert info.value.code in ("file_missing", "changed_since_apply")
    refusal("file_missing", safety.restore, backup_id, **deck.rkw(confirm=frozenset({"overwrite"})))
    assert not deck.gus.exists()
    assert _outside_backup(deck) == before


# ---------------------------------------------------------------------------- list


def test_a12_list_backups_sorts_by_backup_id_not_by_creation(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    tokens = ["ffffffff", "88888888", "00000000"]
    real_token_hex = secrets.token_hex

    def token_hex(nbytes=None):
        return tokens.pop(0) if nbytes == 4 and tokens else real_token_hex(nbytes)

    monkeypatch.setattr("secrets.token_hex", token_hex)
    monkeypatch.setattr(safety, "token_hex", token_hex, raising=False)
    made = []
    for text in (b"[Render]\r\nA=1\r\n", b"[Render]\r\nA=2\r\n", b"[Render]\r\nA=3\r\n"):
        made.append(safety.apply([safety.plan(deck.card, str(deck.config), text)], **deck.kw()))
    monkeypatch.undo()
    entries = safety.list_backups(str(deck.backup_root))
    assert complete_ids(entries) == sorted(made)
    for backup_id in made:
        assert entry_for(entries, backup_id)["backup_id"] == backup_id


def test_a5_list_shows_tmp_and_manifestless_folders_as_incomplete_and_keeps_them(tmp_path):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck)
    planted = _plant_incomplete(deck)
    planted_state = [content_state(folder) for folder in planted]
    (deck.backup_root / ".lock").touch()
    root_before = content_state(deck.backup_root, skip=[deck.backup_root / ".lock"])
    entries = safety.list_backups(str(deck.backup_root))
    assert content_state(deck.backup_root, skip=[deck.backup_root / ".lock"]) == root_before
    assert len(entries) == 3, entries
    assert not is_incomplete(entry_for(entries, backup_id))
    for folder in planted:
        assert is_incomplete(entry_for(entries, folder.name))
    assert complete_ids(entries) == [backup_id]
    assert not [entry for entry in entries if any(value == ".lock" for value in entry.values())]
    # They survive an apply and a restore too (A5: never deleted).
    restored = safety.restore(backup_id, **deck.rkw())
    assert sorted(restored["restored"]) == _paths(deck, KEYS)
    _apply(deck, ("gus",))
    assert [content_state(folder) for folder in planted] == planted_state
    assert sum(is_incomplete(e) for e in safety.list_backups(str(deck.backup_root))) == 2


def test_a5_list_of_an_empty_backup_root_is_empty(tmp_path):
    deck = make_deck(tmp_path)
    assert safety.list_backups(str(deck.backup_root)) == []


# ---------------------------------------------------------------------------- AC6 round trip

SEED = 20261022
WORDS = ["Upscaler", "Shadow", "Größe", "画質", "Ñandú", "Frame Gen", "r.Bloom", "x"]
MODES = [0o644, 0o600, 0o640, 0o664, 0o604, 0o444, 0o400]


def _text(rng: random.Random) -> str:
    lines = [f"[{rng.choice(WORDS)}]"]
    for _ in range(rng.randint(0, 12)):
        lines.append(f"{rng.choice(WORDS)}={rng.choice(WORDS)}{rng.randint(0, 99)}")
    return "\n".join(lines) + "\n"


def _content(rng: random.Random) -> bytes:
    text = _text(rng)
    kind = rng.choice(
        [
            "utf16le_bom",
            "utf16be_bom",
            "utf8_bom",
            "crlf",
            "lf",
            "mixed",
            "no_final_newline",
            "empty",
            "binary",
            "nul",
        ]
    )
    if kind == "utf16le_bom":
        return b"\xff\xfe" + text.replace("\n", "\r\n").encode("utf-16-le")
    if kind == "utf16be_bom":
        return b"\xfe\xff" + text.encode("utf-16-be")
    if kind == "utf8_bom":
        return b"\xef\xbb\xbf" + text.replace("\n", "\r\n").encode("utf-8")
    if kind == "crlf":
        return text.replace("\n", "\r\n").encode("utf-8")
    if kind == "lf":
        return text.encode("utf-8")
    if kind == "mixed":
        parts = text.split("\n")
        ends = [rng.choice(["\n", "\r\n", "\r"]) for _ in parts]
        return "".join(part + end for part, end in zip(parts, ends, strict=True)).encode()
    if kind == "no_final_newline":
        return text.rstrip("\n").encode("utf-8")
    if kind == "empty":
        return b""
    if kind == "binary":
        return rng.randbytes(rng.randint(1, 2048))
    return text.encode("utf-8") + b"\x00\x00" + rng.randbytes(3)


def _cases():
    rng = random.Random(SEED)  # noqa: S311 - a fixed-seed test generator, not crypto
    cases = []
    for index in range(24):
        keys = rng.sample(list(KEYS), rng.randint(1, 3))
        files = []
        for key in keys:
            old = _content(rng)
            new = old if rng.random() < 0.15 else _content(rng)
            files.append((key, old, new, rng.choice(MODES)))
        cases.append((LAYOUTS[index % len(LAYOUTS)], files))
    return cases


@pytest.mark.parametrize(("layout", "files"), _cases(), ids=[f"case{i}" for i in range(24)])
def test_ac6_round_trip_apply_then_restore_gives_the_starting_tree(tmp_path, layout, files):
    deck = make_deck(tmp_path, layout=layout)
    for key, old, _new, mode in files:
        deck.files[key].write_bytes(old)
        deck.files[key].chmod(mode)
    locked = any(not mode & stat.S_IWUSR for _key, _old, _new, mode in files)
    confirm = frozenset({"locked"}) if locked else frozenset()
    before = deck_state(deck)
    changes = [safety.plan(deck.card, str(deck.files[key]), new) for key, _old, new, _m in files]
    backup_id = safety.apply(changes, **deck.kw(confirm=confirm))
    for key, _old, new, mode in files:
        assert deck.files[key].read_bytes() == new
        assert mode_of(deck.files[key]) == mode
    result = safety.restore(backup_id, **deck.rkw())
    assert deck_state(deck) == before
    assert sorted(result["restored"]) == sorted(
        str(deck.files[key]) for key, old, new, _m in files if old != new
    )
    assert sorted(result["skipped"]) == sorted(
        str(deck.files[key]) for key, old, new, _m in files if old == new
    )


def test_ac6_round_trip_cases_cover_every_required_shape():
    files = [item for _layout, case in _cases() for item in case]
    contents = [data for _key, old, new, _mode in files for data in (old, new)]
    assert any(data.startswith(b"\xff\xfe") for data in contents), "UTF-16 LE with BOM"
    assert any(data.startswith(b"\xfe\xff") for data in contents), "UTF-16 BE with BOM"
    assert any(data.startswith(b"\xef\xbb\xbf") for data in contents), "UTF-8 with BOM"
    assert any(b"\r\n" in data and not data.startswith(b"\xff") for data in contents), "CRLF"
    assert b"" in contents, "empty"
    assert any(old == new for _key, old, new, _mode in files), "unchanged file"
    assert any(not mode & stat.S_IWUSR for *_rest, mode in files), "locked file"
    assert {layout for layout, _case in _cases()} == set(LAYOUTS)


# ---------------------------------------------------------------------------- crashes


def _count_restore_steps(tmp_path, monkeypatch) -> int:
    deck = make_deck(tmp_path / "count")
    backup_id = _apply(deck)
    rec = Recorder(monkeypatch, deck.base)
    safety.restore(backup_id, **deck.rkw())
    monkeypatch.undo()
    assert len([s for s in rec.steps if s[0] == "replace"]) >= 3, rec.steps
    return len(rec.steps)


def _each_target_old_or_new(deck, label):
    for key in KEYS:
        data = deck.files[key].read_bytes()
        assert data in (OLD[key], NEW[key]), f"{label}: {key} is neither applied nor original"
        assert mode_of(deck.files[key]) == 0o644, label


def test_a5_a_crash_at_any_restore_step_leaves_whole_files_and_restore_can_finish(
    tmp_path, monkeypatch
):
    total = _count_restore_steps(tmp_path, monkeypatch)
    for step in range(total):
        deck = make_deck(tmp_path / f"step{step}")
        before = deck_state(deck)
        backup_id = _apply(deck)
        rec = Recorder(monkeypatch, deck.base, fail_at=step, make_error=crash)
        with pytest.raises(Crash):
            safety.restore(backup_id, **deck.rkw())
        monkeypatch.undo()
        simulate_exit(deck.base)
        assert rec.failed, f"step {step} was never reached"
        _each_target_old_or_new(deck, f"step {step}")
        safety.restore(backup_id, **deck.rkw())
        for key in KEYS:
            assert deck.files[key].read_bytes() == OLD[key], f"step {step}"
        # A dead process leaves its temp file behind; everything else is as it was.
        folders = {str(path.parent.relative_to(deck.base)) for path in deck.writable}
        state = deck_state(deck)
        for key, value in before.items():
            if key not in folders:
                assert state.get(key) == value, f"step {step}: {key}"


def test_ac3_ac8_an_error_at_any_restore_step_leaves_whole_files_and_no_temp(tmp_path, monkeypatch):
    total = _count_restore_steps(tmp_path, monkeypatch)
    for step in range(total):
        deck = make_deck(tmp_path / f"step{step}")
        before = deck_state(deck)
        backup_id = _apply(deck)
        names = target_folder_names(deck.writable)
        rec = Recorder(monkeypatch, deck.base, fail_at=step)
        with pytest.raises((safety.SafetyError, OSError)) as info:
            safety.restore(backup_id, **deck.rkw())
        monkeypatch.undo()
        assert rec.failed, f"step {step} was never reached"
        assert str(info.value), "the error says what happened"
        _each_target_old_or_new(deck, f"step {step}")
        assert target_folder_names(deck.writable) == names, f"step {step}: temp file left"
        safety.restore(backup_id, **deck.rkw())
        assert deck_state(deck) == before, f"step {step}"


def test_ac5_backup_copies_are_left_as_they_were_after_restore(tmp_path):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck)
    copies_before = {path: path.read_bytes() for path in backup_copies(deck, backup_id)}
    manifest_before = read_manifest(deck, backup_id)
    safety.restore(backup_id, **deck.rkw())
    assert {path: path.read_bytes() for path in backup_copies(deck, backup_id)} == copies_before
    assert read_manifest(deck, backup_id) == manifest_before
