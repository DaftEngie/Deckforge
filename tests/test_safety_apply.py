# Contracts for deckforge.safety.apply: backup, atomic write, rollback
# (docs/specs/safety-module.md: AC2, AC3, AC8, AC10 and clarifier answers A4-A9, A11).
# Written before the implementation; fixtures and fakes: test_safety_support.py.
#
# apply(changes, *, backup_root, confirm=frozenset(), proc_root="/proc",
#       userdata_roots=()) -> str
#   Pre:  changes come from plan; backup_root is an existing absolute folder outside the
#         card's library and prefix; userdata_roots is non-empty (A17).
#   Post: returns backup_id = <YYYYmmdd-HHMMSS>-<appid>-<8 lowercase hex> (A11); the folder
#         is new (os.mkdir); an id whose folder (or .tmp- folder) exists is never reused:
#         a new token_hex(4) is drawn, and the existing folders are left as they were.
#   Post: <backup_root>/<backup_id>/manifest.json holds backup_id, created_utc,
#         deckforge_version (== deckforge.__version__), appid (== the card's), and per file
#         path, size, mode (permission bits == the original's), sha256_before (original),
#         sha256_after (new_bytes) (AC2). The folder holds a byte-identical copy of every
#         original.
#   Post: every target holds exactly new_bytes (no encoding, newline or BOM change) and
#         its original permission bits, whatever the umask (AC3). Folder modes never
#         change; the target itself is never chmod-ed (A8: only the temp file is).
#   Order (A5, AC3), seen through the Recorder:
#         mkdir <backup_root>/.tmp-<id>; every copy written and fsynced; manifest.json
#         written last and fsynced; rename .tmp-<id> -> <id>; fsync <backup_root>; only
#         then, per target: temp file in the target's own folder, fsync of the temp,
#         os.replace(temp, target), fsync of the folder. The target is never written in
#         place.
#   Post: a backup copy whose bytes change after it is written (bad disk) is caught by
#         the read-back check: apply fails, no target changes, no complete backup is listed.
#   Refusals (SafetyError .code; nothing changes, backup_root holds nothing but .lock):
#         changed_since_preview (file differs from Change.old_sha256, A4),
#         duplicate_target (two Changes with the same st_dev/st_ino, A6), hard_link (A6),
#         file_locked (no owner-write and "locked" not confirmed, AC10/A8), not_owner and
#         folder_locked (A8), file_missing (AC7, nothing created), symlink and
#         outside_game re-checked on disk (A3).
#   Locked (AC10/A8): with "locked" confirmed, the target gets new_bytes with its
#         original mode exactly (0o444 stays 0o444); restore puts the recorded mode back.
#   os.replace failing with EPERM or EACCES -> file_locked, temp file removed (A9).
#   Errors (AC8): any OSError at any write-side step -> apply raises (SafetyError or the
#         OSError), every target is back to its original bytes and mode, no temp file is
#         left, nothing outside backup_root differs; any backup folder left is either
#         complete (copies match the manifest) or listed as incomplete.
#   Crash (A5): the process dying (Crash, a BaseException) at any step leaves each target
#         fully old or fully new with its mode; if any target is new, exactly one complete
#         backup is listed and restore() brings every file back.
#   Rollback (A7): after a later failure, only targets whose current hash equals our
#         sha256_after are rewritten; another target is reported in the error and left
#         as it is.
#   Failed rollback (AC8): the backup is kept and the error / output names its folder.

import errno
import os
import secrets
import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from test_safety_support import (
    APPID,
    CONFIG_INI,
    CONFIG_NEW,
    ENGINE_INI,
    ENGINE_NEW,
    FILE_MISSING_TEXT,
    GUS_INI,
    GUS_NEW,
    ID_PATTERN,
    REAL,
    Crash,
    Recorder,
    backup_copies,
    backup_folders,
    complete_ids,
    content_state,
    copy_holding,
    crash,
    deck_state,
    error_text,
    lock_folder,
    make_deck,
    make_foreign,
    manifest_files,
    mode_of,
    read_manifest,
    refusal,
    sha,
    simulate_exit,
    target_folder_names,
    with_entry,
)

import deckforge
from deckforge import safety

THREE = (
    ("config", CONFIG_INI, CONFIG_NEW),
    ("gus", GUS_INI, GUS_NEW),
    ("engine", ENGINE_INI, ENGINE_NEW),
)


def _changes(deck, keys=("config", "gus", "engine")):
    news = {key: new for key, _old, new in THREE}
    return [safety.plan(deck.card, str(deck.files[key]), news[key]) for key in keys]


def _nothing_backed_up(deck) -> bool:
    return backup_folders(deck) == []


def _verify_complete(deck, backup_id):
    """A complete backup: manifest present and every sha256_before has a matching copy."""
    files = manifest_files(read_manifest(deck, backup_id))
    copies = {sha(path.read_bytes()) for path in backup_copies(deck, backup_id)}
    for item in files:
        assert item["sha256_before"] in copies, item


# ---------------------------------------------------------------------------- AC2 backup


def test_ac2_apply_returns_the_id_and_the_backup_holds_manifest_and_copies(tmp_path):
    deck = make_deck(tmp_path)
    deck.gus.chmod(0o600)
    backup_id = safety.apply(_changes(deck, ("config", "gus")), **deck.kw())
    assert ID_PATTERN.match(backup_id), backup_id
    assert backup_folders(deck) == [backup_id]
    manifest = read_manifest(deck, backup_id)
    assert manifest["backup_id"] == backup_id
    assert isinstance(manifest["created_utc"], str) and manifest["created_utc"]
    assert manifest["deckforge_version"] == deckforge.__version__
    assert manifest["appid"] == APPID
    by_path = {item["path"]: item for item in manifest_files(manifest)}
    assert set(by_path) == {str(deck.config), str(deck.gus)}
    for path, old, new, mode in (
        (deck.config, CONFIG_INI, CONFIG_NEW, 0o644),
        (deck.gus, GUS_INI, GUS_NEW, 0o600),
    ):
        item = by_path[str(path)]
        assert item["size"] == len(old)
        assert stat.S_IMODE(item["mode"]) == mode
        assert item["sha256_before"] == sha(old)
        assert item["sha256_after"] == sha(new)
        assert copy_holding(deck, backup_id, old).read_bytes() == old
        assert path.read_bytes() == new


def test_a11_backup_id_format_and_its_time_part_parses(tmp_path):
    deck = make_deck(tmp_path)
    backup_id = safety.apply(_changes(deck, ("config",)), **deck.kw())
    match = ID_PATTERN.match(backup_id)
    assert match
    parsed = datetime.strptime(match.group(1), "%Y%m%d-%H%M%S")
    assert parsed.strftime("%Y%m%d-%H%M%S") == match.group(1)


def test_a11_two_applies_get_two_new_folders(tmp_path):
    deck = make_deck(tmp_path)
    first = safety.apply(_changes(deck, ("config",)), **deck.kw())
    second = safety.apply(
        [safety.plan(deck.card, str(deck.config), b"[Render]\r\nUpscaler=XeSS\r\n")],
        **deck.kw(),
    )
    assert first != second
    assert backup_folders(deck) == sorted([first, second])
    assert copy_holding(deck, first, CONFIG_INI)
    assert copy_holding(deck, second, CONFIG_NEW)
    assert sorted(complete_ids(safety.list_backups(str(deck.backup_root)))) == sorted(
        [first, second]
    )


def test_a11_an_existing_id_is_never_reused(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    taken = "0badc0de"
    now_utc, now_local = datetime.now(UTC), datetime.now()
    planted = []
    for base in (now_utc, now_local):
        for offset in range(-2, 60):
            stamp = (base + timedelta(seconds=offset)).strftime("%Y%m%d-%H%M%S")
            for name in (f"{stamp}-{APPID}-{taken}", f".tmp-{stamp}-{APPID}-{taken}"):
                folder = deck.backup_root / name
                if not folder.exists():
                    folder.mkdir()
                    (folder / "marker").write_bytes(name.encode())
                    planted.append(folder)
    before = content_state(deck.backup_root)
    drawn: list[object] = []
    answers = [taken, taken]
    real_token_hex = secrets.token_hex

    def token_hex(nbytes=None):
        if nbytes != 4:  # another use (a temp name, say) gets a real token
            return real_token_hex(nbytes)
        drawn.append(nbytes)
        return answers.pop(0) if answers else "feedface"

    monkeypatch.setattr("secrets.token_hex", token_hex)
    monkeypatch.setattr(safety, "token_hex", token_hex, raising=False)
    backup_id = safety.apply(_changes(deck, ("config",)), **deck.kw())
    assert backup_id.endswith(f"-{APPID}-feedface")
    assert len(drawn) >= 3, "the taken token was drawn twice, then a new one"
    after = content_state(deck.backup_root)
    for key, value in before.items():
        if key != ".":  # the root's own listing gains the new folder
            assert after[key] == value, key
    assert (deck.backup_root / backup_id / "manifest.json").is_file()


def test_ac2_a5_backup_is_complete_and_renamed_before_the_first_target_write(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    rec = Recorder(monkeypatch, deck.base)
    backup_id = safety.apply(changes, **deck.kw())
    monkeypatch.undo()
    steps = rec.steps
    root = str(deck.backup_root)
    tmp_dir = str(deck.backup_root / f".tmp-{backup_id}")
    final_dir = str(deck.backup_root / backup_id)
    targets = {str(path) for path in deck.writable}
    target_dirs = {str(path.parent) for path in deck.writable}

    mkdirs = [i for i, (op, path, _) in enumerate(steps) if op == "mkdir" and path == tmp_dir]
    renames = [
        i
        for i, (op, src, dst) in enumerate(steps)
        if op in ("rename", "replace") and src == tmp_dir and dst == final_dir
    ]
    replaces = [i for i, (op, _src, dst) in enumerate(steps) if op == "replace" and dst in targets]
    assert mkdirs, "the backup folder is created as .tmp-<id> with os.mkdir"
    assert len(renames) == 1, "the .tmp-<id> folder is renamed to <id>"
    assert len(replaces) == 3
    rename = renames[0]
    first_target_write = min(
        [
            i
            for i, (op, path, path2) in enumerate(steps)
            if (path and str(Path(path).parent) in target_dirs) or path2 in targets
        ]
    )
    assert mkdirs[0] < rename < first_target_write

    def names_of(path: str) -> set[str]:
        # A file may be written under another name in .tmp-<id> and renamed there.
        return {path} | {
            src
            for op, src, dst in steps
            if op in ("rename", "replace") and dst == path and src.startswith(tmp_dir + os.sep)
        }

    manifest = names_of(str(Path(tmp_dir) / "manifest.json"))
    copy_paths = [
        str(Path(tmp_dir) / path.relative_to(final_dir)) for path in backup_copies(deck, backup_id)
    ]
    assert len(copy_paths) >= 3
    manifest_writes = [i for i, (op, p, _) in enumerate(steps) if op == "write" and p in manifest]
    assert manifest_writes, "manifest.json is written inside .tmp-<id>"
    for copy in copy_paths:
        names = names_of(copy)
        writes = [i for i, (op, p, _) in enumerate(steps) if op == "write" and p in names]
        syncs = [i for i, (op, p, _) in enumerate(steps) if op == "fsync" and p in names]
        assert writes and syncs, copy
        assert max(writes) < min(manifest_writes), "copies first, manifest last"
        assert max(syncs) < rename
    manifest_syncs = [i for i, (op, p, _) in enumerate(steps) if op == "fsync" and p in manifest]
    assert manifest_syncs and max(manifest_writes) < max(manifest_syncs) < rename
    parent_syncs = [i for i, (op, p, _) in enumerate(steps) if op == "fsync" and p == root]
    assert [i for i in parent_syncs if rename < i < first_target_write]


def test_ac2_a_backup_copy_that_reads_back_wrong_stops_apply(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    changes = _changes(deck, ("config", "gus"))
    before = deck_state(deck)
    corrupted: set[str] = set()
    root = str(deck.backup_root)

    def spoil(path: str) -> None:
        # Only a backup copy of an original (its bytes are an original's) goes bad.
        if path in corrupted or not path.startswith(root + os.sep) or not Path(path).is_file():
            return
        with REAL["io_open"](path, "r+b") as handle:
            data = handle.read()
            if data not in (CONFIG_INI, GUS_INI):
                return
            corrupted.add(path)
            handle.seek(0)
            handle.write(bytes([data[0] ^ 0xFF]))

    def hook(_rec, op, path, _path2):
        if op == "fsync":
            spoil(path)

    rec = Recorder(monkeypatch, deck.base, hook=hook)
    rec.on_close = spoil
    with pytest.raises((safety.SafetyError, OSError)):
        safety.apply(changes, **deck.kw())
    monkeypatch.undo()
    assert corrupted, "the fixture never saw a backup copy being written"
    assert deck_state(deck) == before
    assert complete_ids(safety.list_backups(str(deck.backup_root))) == []


# ---------------------------------------------------------------------------- AC3 atomic


def test_ac3_each_target_goes_through_a_synced_temp_in_its_own_folder(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    rec = Recorder(monkeypatch, deck.base)
    safety.apply(changes, **deck.kw())
    monkeypatch.undo()
    steps = rec.steps
    for target in map(str, deck.writable):
        folder = str(Path(target).parent)
        hits = [
            (i, src) for i, (op, src, dst) in enumerate(steps) if op == "replace" and dst == target
        ]
        assert len(hits) == 1, target
        index, temp = hits[0]
        assert str(Path(temp).parent) == folder and temp != target
        assert [i for i, (op, p, _) in enumerate(steps[:index]) if op == "write" and p == temp]
        assert [i for i, (op, p, _) in enumerate(steps[:index]) if op == "fsync" and p == temp]
        assert [op for op, p, _ in steps[index + 1 :] if op == "fsync" and p == folder]
        assert not [s for s in steps if s[0] == "write" and s[1] == target]
        assert not [s for s in steps if s[0] == "chmod" and s[1] == target]
        assert not Path(temp).exists()


@pytest.mark.parametrize(
    "new",
    [
        b"[Render]\r\nUpscaler=DLSS\r\n",
        b"[Render]\nUpscaler=DLSS",
        b"\xef\xbb\xbf[Render]\r\nUpscaler=DLSS\r\n",
        "\ufeff[Render]\r\nUpscaler=DLSS\r\n".encode("utf-16-le"),
        b"",
        b"[Render]\x00\xff\xfe\r\r\n\n",
    ],
    ids=["crlf", "lf_no_final_newline", "utf8_bom", "utf16_bom", "empty", "binary"],
)
def test_ac3_bytes_written_are_exactly_new_bytes(tmp_path, new):
    deck = make_deck(tmp_path)
    safety.apply([safety.plan(deck.card, str(deck.config), new)], **deck.kw())
    assert deck.config.read_bytes() == new


@pytest.mark.parametrize("mode", [0o644, 0o604, 0o660, 0o600, 0o751])
def test_ac3_permissions_and_owner_are_kept_whatever_the_umask(tmp_path, mode):
    deck = make_deck(tmp_path)
    deck.config.chmod(mode)
    owner = (deck.config.stat().st_uid, deck.config.stat().st_gid)
    change = safety.plan(deck.card, str(deck.config), CONFIG_NEW)
    old_umask = os.umask(0o077)
    try:
        safety.apply([change], **deck.kw())
    finally:
        os.umask(old_umask)
    assert mode_of(deck.config) == mode
    assert (deck.config.stat().st_uid, deck.config.stat().st_gid) == owner


def test_a8_folder_permissions_never_change(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    folders = {path.parent for path in deck.writable}
    for folder in folders:
        folder.chmod(0o750)
    changes = _changes(deck)
    rec = Recorder(monkeypatch, deck.base)
    safety.apply(changes, **deck.kw())
    monkeypatch.undo()
    assert {mode_of(folder) for folder in folders} == {0o750}
    assert not [s for s in rec.steps if s[0] == "chmod" and s[1] in map(str, folders)]


# ---------------------------------------------------------------------------- AC8 errors


def _count_steps(tmp_path, monkeypatch) -> int:
    deck = make_deck(tmp_path / "count")
    changes = _changes(deck)
    rec = Recorder(monkeypatch, deck.base)
    safety.apply(changes, **deck.kw())
    monkeypatch.undo()
    assert len(rec.steps) >= 12, rec.steps
    return len(rec.steps)


def test_ac3_ac8_an_error_at_any_step_rolls_back_and_leaves_no_temp(tmp_path, monkeypatch):
    total = _count_steps(tmp_path, monkeypatch)
    for step in range(total):
        deck = make_deck(tmp_path / f"step{step}")
        changes = _changes(deck)
        before = deck_state(deck)
        rec = Recorder(monkeypatch, deck.base, fail_at=step)
        with pytest.raises((safety.SafetyError, OSError)) as info:
            safety.apply(changes, **deck.kw())
        monkeypatch.undo()
        assert rec.failed, f"step {step} was never reached"
        assert str(info.value), "the error says what happened"
        assert deck_state(deck) == before, f"step {step}: {rec.steps[step]}"
        entries = safety.list_backups(str(deck.backup_root))
        for backup_id in complete_ids(entries):
            _verify_complete(deck, backup_id)


def test_a5_a_crash_at_any_step_leaves_each_file_old_or_new_and_restorable(tmp_path, monkeypatch):
    total = _count_steps(tmp_path, monkeypatch)
    for step in range(total):
        deck = make_deck(tmp_path / f"step{step}")
        changes = _changes(deck)
        before = deck_state(deck)
        rec = Recorder(monkeypatch, deck.base, fail_at=step, make_error=crash)
        with pytest.raises(Crash):
            safety.apply(changes, **deck.kw())
        monkeypatch.undo()
        simulate_exit(deck.base)
        assert rec.failed
        new_ones, old_ones = [], []
        for key, old, new in THREE:
            path = deck.files[key]
            data = path.read_bytes()
            assert data in (old, new), f"step {step}: {path} is neither old nor new"
            assert mode_of(path) == 0o644
            (new_ones if data == new else old_ones).append(str(path))
        _others_unchanged(deck, before)
        completes = complete_ids(safety.list_backups(str(deck.backup_root)))
        if new_ones:
            assert len(completes) == 1, f"step {step}: a target changed without a backup"
        assert len(completes) <= 1
        for backup_id in completes:
            _verify_complete(deck, backup_id)
            result = safety.restore(backup_id, **deck.rkw())
            assert sorted(result["restored"]) == sorted(new_ones)
            assert sorted(result["skipped"]) == sorted(old_ones)
            for key, old, _new in THREE:
                assert deck.files[key].read_bytes() == old


def _others_unchanged(deck, before):
    """Everything but the targets and their folders' listings is as before."""
    now = deck_state(deck)
    skipped = {str(path.relative_to(deck.base)) for path in deck.writable}
    skipped |= {str(path.parent.relative_to(deck.base)) for path in deck.writable}
    for key, value in before.items():
        if key not in skipped:
            assert now.get(key) == value, key


def test_ac8_disk_full_on_a_later_file_rolls_back_the_earlier_ones(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    before = deck_state(deck)
    targets = {str(path) for path in deck.writable}
    replaced: list[str] = []

    def hook(_rec, op, path, path2):
        if op == "replace" and path2 in targets:
            replaced.append(path2)
            if len(replaced) == 2:  # rename(2) may fail with ENOSPC when the folder grows
                raise OSError(errno.ENOSPC, "No space left on device", path2)

    Recorder(monkeypatch, deck.base, hook=hook)
    with pytest.raises((safety.SafetyError, OSError)) as info:
        safety.apply(changes, **deck.kw())
    monkeypatch.undo()
    assert len(replaced) >= 2, "the first target was replaced before the disk filled"
    assert str(info.value)
    assert deck_state(deck) == before


def test_ac8_a_failed_rollback_keeps_the_backup_and_says_where_it_is(
    tmp_path, monkeypatch, capsys, caplog
):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    targets = {str(path) for path in deck.writable}
    folders = {str(Path(t).parent) for t in targets}
    replaced: list[str] = []

    def hook(_rec, op, path, path2):
        touches = (path and str(Path(path).parent) in folders) or path2 in targets
        if replaced and touches:
            raise OSError(errno.EIO, "Input/output error", path)
        if op == "replace" and path2 in targets:
            replaced.append(path2)

    Recorder(monkeypatch, deck.base, hook=hook)
    with pytest.raises((safety.SafetyError, OSError)) as info:
        safety.apply(changes, **deck.kw())
    monkeypatch.undo()
    assert len(replaced) == 1
    [backup_id] = complete_ids(safety.list_backups(str(deck.backup_root)))
    _verify_complete(deck, backup_id)
    out = capsys.readouterr()
    said = "\n".join([error_text(info.value), out.out, out.err, caplog.text])
    assert str(deck.backup_root / backup_id) in said
    result = safety.restore(backup_id, **deck.rkw())
    assert result["restored"] == replaced
    for key, old, _new in THREE:
        assert deck.files[key].read_bytes() == old


def test_a7_rollback_rewrites_only_files_still_holding_our_bytes(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    targets = {str(path) for path in deck.writable}
    replaced: list[str] = []
    user_edit = b"[Render]\r\nUpscaler=Mine\r\n"

    def hook(_rec, op, path, path2):
        if op == "replace" and path2 in targets:
            replaced.append(path2)
            if len(replaced) == 2:  # someone edits the first file, then the second fails
                with REAL["io_open"](replaced[0], "wb") as handle:
                    handle.write(user_edit)
                raise OSError(errno.EIO, "Input/output error", path2)

    Recorder(monkeypatch, deck.base, hook=hook)
    with pytest.raises((safety.SafetyError, OSError)) as info:
        safety.apply(changes, **deck.kw())
    monkeypatch.undo()
    edited = replaced[0]
    assert edited not in replaced[2:], "the edited file was overwritten by the rollback"
    with REAL["io_open"](edited, "rb") as handle:
        assert handle.read() == user_edit
    assert edited in error_text(info.value)
    for key, old, _new in THREE:
        if str(deck.files[key]) != edited:
            assert deck.files[key].read_bytes() == old


# ---------------------------------------------------------------------------- refusals


def test_a4_a_file_changed_since_preview_is_refused(tmp_path):
    deck = make_deck(tmp_path)
    changes = _changes(deck, ("config", "gus"))
    edited = b"[/Script/Engine.GameUserSettings]\nResolutionSizeX=1920\n"
    deck.gus.write_bytes(edited)
    before = deck_state(deck)
    refusal("changed_since_preview", safety.apply, changes, **deck.kw())
    assert deck_state(deck) == before
    assert deck.gus.read_bytes() == edited
    assert _nothing_backed_up(deck)


def test_a6_the_same_target_twice_is_duplicate_target(tmp_path):
    deck = make_deck(tmp_path)
    change = safety.plan(deck.card, str(deck.config), CONFIG_NEW)
    other = safety.plan(deck.card, str(deck.config), b"[Render]\r\nUpscaler=XeSS\r\n")
    before = deck_state(deck)
    refusal("duplicate_target", safety.apply, [change, other], **deck.kw())
    assert deck_state(deck) == before
    assert _nothing_backed_up(deck)


def test_a6_two_spellings_of_one_file_are_duplicate_target(tmp_path):
    deck = make_deck(tmp_path)
    alias = deck.prefix / "drive_c" / "users" / "steamuser" / "AppData" / "Alias"
    alias.symlink_to(deck.gus.parent, target_is_directory=True)
    second = alias / deck.gus.name
    card = with_entry(deck.card, second)
    changes = [
        safety.plan(card, str(deck.gus), GUS_NEW),
        safety.plan(card, str(second), b"[/Script/Engine.GameUserSettings]\n"),
    ]
    before = deck_state(deck)
    refusal("duplicate_target", safety.apply, changes, **deck.kw())
    assert deck_state(deck) == before
    assert _nothing_backed_up(deck)


def test_ac7_a_file_deleted_after_plan_is_refused_and_not_recreated(tmp_path):
    deck = make_deck(tmp_path)
    changes = _changes(deck, ("config", "gus"))
    deck.gus.unlink()
    before = deck_state(deck)
    error = refusal("file_missing", safety.apply, changes, **deck.kw())
    assert FILE_MISSING_TEXT in str(error)
    assert not os.path.lexists(deck.gus)
    assert deck_state(deck) == before
    assert _nothing_backed_up(deck)


def test_a3_apply_rechecks_that_the_target_is_not_a_link(tmp_path):
    deck = make_deck(tmp_path)
    changes = _changes(deck, ("config",))
    real = deck.install / "real-config.ini"
    deck.config.rename(real)
    deck.config.symlink_to(real)
    before = deck_state(deck)
    refusal("symlink", safety.apply, changes, **deck.kw())
    assert deck_state(deck) == before
    assert real.read_bytes() == CONFIG_INI


def test_a3_apply_rechecks_that_the_target_is_inside_the_game(tmp_path):
    deck = make_deck(tmp_path)
    changes = _changes(deck, ("gus",))
    windows = deck.gus.parent
    outside = deck.base / "outside" / "Windows"
    outside.parent.mkdir()
    windows.rename(outside)
    windows.symlink_to(outside, target_is_directory=True)
    before = deck_state(deck)
    refusal("outside_game", safety.apply, changes, **deck.kw())
    assert deck_state(deck) == before
    assert (outside / "GameUserSettings.ini").read_bytes() == GUS_INI


def test_a6_a_hard_link_made_after_plan_is_refused_at_apply(tmp_path):
    deck = make_deck(tmp_path)
    changes = _changes(deck, ("config",))
    os.link(deck.config, deck.install / "config-hardlink.ini")
    before = deck_state(deck)
    refusal("hard_link", safety.apply, changes, **deck.kw())
    assert deck_state(deck) == before


# ---------------------------------------------------------------------------- AC10 locked


@pytest.mark.parametrize("mode", [0o444, 0o400, 0o464])
def test_ac10_a_target_without_owner_write_is_file_locked(tmp_path, mode):
    deck = make_deck(tmp_path)
    changes = _changes(deck, ("config", "gus"))
    deck.gus.chmod(mode)
    before = deck_state(deck)
    refusal("file_locked", safety.apply, changes, **deck.kw())
    assert deck_state(deck) == before
    assert _nothing_backed_up(deck)


@pytest.mark.parametrize("mode", [0o444, 0o400, 0o464])
def test_ac10_a8_confirmed_locked_write_keeps_the_mode_and_restore_puts_it_back(
    tmp_path, monkeypatch, mode
):
    deck = make_deck(tmp_path)
    changes = _changes(deck, ("gus",))
    deck.gus.chmod(mode)
    rec = Recorder(monkeypatch, deck.base)
    backup_id = safety.apply(changes, **deck.kw(confirm=frozenset({"locked"})))
    monkeypatch.undo()
    assert deck.gus.read_bytes() == GUS_NEW
    assert mode_of(deck.gus) == mode
    assert not [s for s in rec.steps if s[0] == "chmod" and s[1] == str(deck.gus)]
    [item] = manifest_files(read_manifest(deck, backup_id))
    assert stat.S_IMODE(item["mode"]) == mode
    safety.restore(backup_id, **deck.rkw())
    assert deck.gus.read_bytes() == GUS_INI
    assert mode_of(deck.gus) == mode


def test_a8_a_target_owned_by_another_user_is_not_owner(tmp_path, monkeypatch):
    # Faked: os.stat/os.lstat/os.fstat report another st_uid for the target (and, as root,
    # the file is really chowned to that uid).
    deck = make_deck(tmp_path)
    changes = _changes(deck, ("config",))
    make_foreign(monkeypatch, deck.config)
    before = deck_state(deck)
    refusal("not_owner", safety.apply, changes, **deck.kw(confirm=frozenset({"locked"})))
    monkeypatch.undo()
    assert deck.config.read_bytes() == CONFIG_INI
    assert deck_state(deck) == before
    assert _nothing_backed_up(deck)


def test_a8_a_folder_the_user_cannot_write_is_folder_locked(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    changes = _changes(deck, ("config",))
    folder = deck.config.parent
    lock_folder(monkeypatch, folder)
    try:
        before = deck_state(deck)
        refusal("folder_locked", safety.apply, changes, **deck.kw(confirm=frozenset({"locked"})))
        monkeypatch.undo()
        assert mode_of(folder) == 0o555, "folder permissions are never changed"
        assert deck_state(deck) == before
        assert _nothing_backed_up(deck)
    finally:
        monkeypatch.undo()
        folder.chmod(0o755)


@pytest.mark.parametrize("code", [errno.EPERM, errno.EACCES])
def test_a9_replace_failing_with_eperm_or_eacces_is_file_locked_and_temp_is_removed(
    tmp_path, monkeypatch, code
):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    names = target_folder_names(deck.writable)
    before = deck_state(deck)
    targets = {str(path) for path in deck.writable}
    seen: list[str] = []

    def hook(_rec, op, path, path2):
        if op == "replace" and path2 in targets:
            seen.append(path2)
            if len(seen) == 2:
                raise PermissionError(code, os.strerror(code), path2)

    Recorder(monkeypatch, deck.base, hook=hook)
    refusal("file_locked", safety.apply, changes, **deck.kw())
    monkeypatch.undo()
    assert len(seen) == 2
    assert target_folder_names(deck.writable) == names, "temp files are cleaned up"
    assert deck_state(deck) == before, "the first file is rolled back"
