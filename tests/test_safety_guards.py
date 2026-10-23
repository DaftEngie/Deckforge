# Contracts for the refusals apply and restore share (docs/specs/safety-module.md: AC9,
# AC11, AC13 and clarifier answers A13-A18). Written before the implementation; fixtures
# and fakes: test_safety_support.py (fake proc_root, userdata roots, statvfs, lock holder).
#
# Game running (AC9, A16)
#   Pre:  proc_root holds <pid>/environ (NUL-separated KEY=VALUE) and maybe <pid>/exe.
#   Post: apply and restore raise game_running when any environ has exactly
#         SteamAppId=<appid> or STEAM_COMPAT_APP_ID=<appid> as an entry; an exe link that
#         resolves inside install_path also counts for apply (restore has no card).
#         Look-alikes do not count: SteamAppId=0, <appid>1, another appid, XSteamAppId.
#   Post: proc_root missing or not a folder -> cannot_check_running (fail closed).
#   Post: an environ of the current user's that cannot be read -> cannot_check_running;
#         one owned by another user that cannot be read is skipped (A16).
#   Post: a game that starts after the backup is built is caught by the check just
#         before the target rename: game_running, no target changes, no temp file left.
#   Inv:  a refusal changes nothing and (before any write) leaves no backup folder.
#
# Steam Cloud (AC11, A17)
#   Pre:  userdata_roots non-empty, else no_userdata (also when left at its default).
#   Post: a match is a key of <root>/<account>/<appid>/remotecache.vdf, for any root and
#         any account, whose last "/" part equals the target's base name. Then
#         preview(..., userdata_roots=...) warns cloud_synced (ASSUMED keyword: the spec's
#         preview(changes) has no way to receive the roots) and apply refuses cloud_synced
#         (message holds "may sync to your other devices") unless "cloud" is confirmed.
#   Post: an unreadable or unparsable remotecache.vdf -> warning cloud_unknown, and apply
#         refuses cloud_unknown (ASSUMED code) unless "cloud" is confirmed.
#   Inv:  a missing remotecache.vdf means not synced; another appid's file never counts.
#
# One at a time (AC13, A13)
#   Post: while another process holds flock(LOCK_EX) on <backup_root>/.lock, apply and
#         restore raise busy and change nothing; once it exits (or is killed) they work.
#         apply holds the lock while it replaces targets.
#
# Free space (A14): os.statvfs (f_bavail * f_frsize) shows less free space than the
#   originals' total on the backup filesystem, or than the new size on a target's
#   filesystem -> no_space before any write (one byte short is enough to refuse); 1 MiB
#   free everywhere is enough for these small files.
# SD card missing (A15): the target's folder or the whole library is gone at apply or
#   restore -> target_unavailable ("insert the SD card or check the library"); nothing is
#   created; the backup is kept and works once the card is back.
# Backup root (A18): relative, missing, not a folder, inside the card's library, install
#   or prefix (also through a link: ASSUMED realpath comparison) -> bad_backup_root;
#   nothing is created.

import fcntl
import os
from pathlib import Path

import pytest
from test_safety_support import (
    ACCOUNT,
    APPID,
    CLOUD_TEXT,
    CONFIG_INI,
    CONFIG_NEW,
    GUS_INI,
    GUS_NEW,
    REAL,
    SECOND_ACCOUNT,
    TARGET_UNAVAILABLE_TEXT,
    Recorder,
    add_process,
    backup_folders,
    complete_ids,
    content_state,
    deck_state,
    environ,
    full_disk,
    hold_lock,
    MiB,
    low_disk,
    make_deck,
    make_foreign,
    make_unreadable,
    mode_of,
    put,
    refusal,
    release,
    remotecache,
    target_folder_names,
    warning_codes,
)

from deckforge import safety

GAME_ENV = {"HOME": "/home/deck", "LD_PRELOAD": ""}


def _changes(deck):
    return [
        safety.plan(deck.card, str(deck.config), CONFIG_NEW),
        safety.plan(deck.card, str(deck.gus), GUS_NEW),
    ]


def _assert_untouched(deck, before):
    assert deck_state(deck) == before
    assert backup_folders(deck) == []


def _applied(deck):
    backup_id = safety.apply(_changes(deck), **deck.kw())
    assert deck.config.read_bytes() == CONFIG_NEW
    return backup_id


# ---------------------------------------------------------------------------- AC9 running


@pytest.mark.parametrize("variable", ["SteamAppId", "STEAM_COMPAT_APP_ID"])
def test_ac9_apply_refuses_while_the_game_runs(tmp_path, variable):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    add_process(deck.proc, 4321, environ(**GAME_ENV, **{variable: str(APPID)}))
    before = deck_state(deck)
    refusal("game_running", safety.apply, changes, **deck.kw())
    _assert_untouched(deck, before)


@pytest.mark.parametrize("variable", ["SteamAppId", "STEAM_COMPAT_APP_ID"])
def test_ac9_restore_refuses_while_the_game_runs(tmp_path, variable):
    deck = make_deck(tmp_path)
    backup_id = _applied(deck)
    add_process(deck.proc, 4321, environ(**{variable: str(APPID)}, **GAME_ENV))
    before = deck_state(deck)
    refusal("game_running", safety.restore, backup_id, **deck.rkw())
    assert deck_state(deck) == before
    assert deck.config.read_bytes() == CONFIG_NEW


@pytest.mark.parametrize("key", ["exe", "shipping"])
def test_ac9_an_exe_link_inside_the_install_folder_counts_as_running(tmp_path, key):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    add_process(deck.proc, 4400, environ(PATH="/usr/bin"), exe=deck.files[key])
    before = deck_state(deck)
    refusal("game_running", safety.apply, changes, **deck.kw())
    _assert_untouched(deck, before)


def test_a16_look_alike_processes_do_not_count(tmp_path):
    # build_proc: SteamAppId=0, SteamAppId=<appid>1, another appid, XSteamAppId=<appid>,
    # an empty environ, an exe link outside the game, and the non-pid entries.
    deck = make_deck(tmp_path)
    add_process(deck.proc, 77, environ(SteamAppId=f"{APPID}0"), exe=deck.base / "elsewhere.exe")
    _applied(deck)


@pytest.mark.parametrize("shape", ["missing", "file"])
def test_ac9_a_proc_root_that_cannot_be_read_fails_closed(tmp_path, shape):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    proc = deck.base / "no-proc"
    if shape == "file":
        proc.write_text("not a folder\n")
    before = deck_state(deck)
    refusal("cannot_check_running", safety.apply, changes, **deck.kw(proc_root=str(proc)))
    _assert_untouched(deck, before)


@pytest.mark.parametrize("shape", ["missing", "file"])
def test_ac9_restore_with_a_proc_root_that_cannot_be_read_fails_closed(tmp_path, shape):
    deck = make_deck(tmp_path)
    backup_id = _applied(deck)
    proc = deck.base / "no-proc"
    if shape == "file":
        proc.write_text("not a folder\n")
    refusal("cannot_check_running", safety.restore, backup_id, **deck.rkw(proc_root=str(proc)))
    assert deck.config.read_bytes() == CONFIG_NEW


def test_a16_an_unreadable_process_of_the_current_user_is_cannot_check_running(
    tmp_path, monkeypatch
):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    folder = add_process(deck.proc, 4500, environ(PATH="/usr/bin"))
    mode = mode_of(folder / "environ")
    before = deck_state(deck)
    make_unreadable(monkeypatch, folder / "environ")
    refusal("cannot_check_running", safety.apply, changes, **deck.kw())
    monkeypatch.undo()
    (folder / "environ").chmod(mode)
    _assert_untouched(deck, before)


def test_a16_an_unreadable_process_of_another_user_is_skipped(tmp_path, monkeypatch):
    # Faked: stat calls report another st_uid for the pid folder and its environ (as root
    # they are really chowned), and opening the environ raises PermissionError.
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    folder = add_process(deck.proc, 4600, environ(SteamAppId=str(APPID)))
    make_foreign(monkeypatch, folder, folder / "environ")
    make_unreadable(monkeypatch, folder / "environ")
    safety.apply(changes, **deck.kw())
    monkeypatch.undo()
    assert deck.config.read_bytes() == CONFIG_NEW


def test_a16_a_game_started_after_the_backup_is_caught_before_the_rename(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    names = target_folder_names([deck.config, deck.gus])
    before = content_state(deck.base, skip=[deck.backup_root, deck.proc])
    root = str(deck.backup_root)

    def hook(_rec, op, path, path2):
        moved_backup = op in ("rename", "replace") and Path(path).name.startswith(".tmp-")
        if moved_backup and str(Path(path2).parent) == root:
            add_process(deck.proc, 4700, environ(SteamAppId=str(APPID)))

    Recorder(monkeypatch, deck.base, hook=hook)
    refusal("game_running", safety.apply, changes, **deck.kw())
    monkeypatch.undo()
    assert (deck.proc / "4700").exists(), "the backup folder was never renamed"
    assert content_state(deck.base, skip=[deck.backup_root, deck.proc]) == before
    assert target_folder_names([deck.config, deck.gus]) == names


# ---------------------------------------------------------------------------- AC11 cloud


def _sync(deck, keys, account=ACCOUNT, root=None):
    put(
        (root or deck.userdata) / account / str(APPID) / "remotecache.vdf", remotecache(APPID, keys)
    )


def test_a17_empty_userdata_roots_is_no_userdata(tmp_path):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    before = deck_state(deck)
    refusal("no_userdata", safety.apply, changes, **deck.kw(userdata_roots=()))
    kwargs = deck.kw()
    del kwargs["userdata_roots"]
    refusal("no_userdata", safety.apply, changes, **kwargs)
    _assert_untouched(deck, before)


def test_ac11_preview_warns_cloud_synced_for_the_listed_file_only(tmp_path):
    deck = make_deck(tmp_path)
    _sync(deck, ["Saved/SaveGames/slot1.sav", "Saved/Config/Windows/GameUserSettings.ini"])
    result = safety.preview(_changes(deck), userdata_roots=(str(deck.userdata),))
    by_path = {entry["path"]: warning_codes(entry["warnings"]) for entry in result}
    assert "cloud_synced" in by_path[str(deck.gus)]
    assert "cloud_synced" not in by_path[str(deck.config)]
    assert "cloud_unknown" not in by_path[str(deck.config)]


def test_ac11_apply_refuses_cloud_synced_unless_confirmed(tmp_path):
    deck = make_deck(tmp_path)
    _sync(deck, ["Saved/Config/Windows/GameUserSettings.ini"])
    changes = _changes(deck)
    before = deck_state(deck)
    error = refusal("cloud_synced", safety.apply, changes, **deck.kw())
    assert CLOUD_TEXT in str(error).lower()
    _assert_untouched(deck, before)
    refusal("cloud_synced", safety.apply, changes, **deck.kw(confirm=frozenset({"locked"})))
    safety.apply(changes, **deck.kw(confirm=frozenset({"cloud"})))
    assert deck.gus.read_bytes() == GUS_NEW


def test_a17_every_account_folder_is_checked(tmp_path):
    deck = make_deck(tmp_path)
    _sync(deck, ["GameUserSettings.ini"], account=SECOND_ACCOUNT)
    refusal("cloud_synced", safety.apply, _changes(deck), **deck.kw())


def test_a17_every_userdata_root_is_checked(tmp_path):
    deck = make_deck(tmp_path)
    second_root = deck.base / "flatpak-userdata"
    _sync(deck, ["Saved/Config/Windows/GameUserSettings.ini"], account="555", root=second_root)
    roots = (str(deck.userdata), str(second_root))
    refusal("cloud_synced", safety.apply, _changes(deck), **deck.kw(userdata_roots=roots))


@pytest.mark.parametrize(
    "key",
    [
        "GameUserSettings.ini",
        "Saved/Config/Windows/GameUserSettings.ini",
        "%WinAppDataLocal%/X/GameUserSettings.ini",
    ],
)
def test_a17_a_key_whose_last_part_is_the_base_name_matches(tmp_path, key):
    deck = make_deck(tmp_path)
    _sync(deck, [key])
    refusal("cloud_synced", safety.apply, _changes(deck), **deck.kw())


@pytest.mark.parametrize(
    "key",
    ["GameUserSettings.ini.bak", "OldGameUserSettings.ini", "Saved/GameUserSettings.ini/x"],
)
def test_a17_a_key_whose_last_part_differs_does_not_match(tmp_path, key):
    deck = make_deck(tmp_path)
    _sync(deck, [key])
    safety.apply(_changes(deck), **deck.kw())
    assert deck.gus.read_bytes() == GUS_NEW


def test_a17_another_games_remotecache_does_not_count(tmp_path):
    # The fixture's userdata/<account>/<OTHER_APPID>/remotecache.vdf lists config.ini and
    # GameUserSettings.ini.
    deck = make_deck(tmp_path)
    _applied(deck)


def test_a17_a_missing_remotecache_means_not_synced(tmp_path):
    deck = make_deck(tmp_path)
    deck.files["remotecache"].unlink()
    _applied(deck)


def _unknown(deck, monkeypatch, how):
    path = deck.files["remotecache"]
    if how == "unreadable":
        make_unreadable(monkeypatch, path)
    else:
        path.write_text(f'"{APPID}"\n{{\n\t"GameUserSettings.ini\n')


@pytest.mark.parametrize("how", ["unreadable", "unparsable"])
def test_ac11_a17_an_unknown_remotecache_warns_and_needs_confirmation(tmp_path, monkeypatch, how):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    before = deck_state(deck)
    _unknown(deck, monkeypatch, how)
    result = safety.preview(changes, userdata_roots=(str(deck.userdata),))
    for entry in result:
        assert "cloud_unknown" in warning_codes(entry["warnings"])
    refusal("cloud_unknown", safety.apply, changes, **deck.kw())
    safety.apply(changes, **deck.kw(confirm=frozenset({"cloud"})))
    monkeypatch.undo()
    deck.files["remotecache"].chmod(0o644)
    assert deck.config.read_bytes() == CONFIG_NEW
    assert set(before) == set(deck_state(deck))


# ---------------------------------------------------------------------------- AC13 lock


def test_ac13_another_process_holding_the_lock_makes_apply_busy(tmp_path):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    holder = hold_lock(deck.backup_root / ".lock")
    try:
        before = deck_state(deck)
        refusal("busy", safety.apply, changes, **deck.kw())
        _assert_untouched(deck, before)
    finally:
        release(holder)
    safety.apply(changes, **deck.kw())
    assert deck.config.read_bytes() == CONFIG_NEW


def test_ac13_another_process_holding_the_lock_makes_restore_busy(tmp_path):
    deck = make_deck(tmp_path)
    backup_id = _applied(deck)
    holder = hold_lock(deck.backup_root / ".lock")
    try:
        refusal("busy", safety.restore, backup_id, **deck.rkw())
        assert deck.config.read_bytes() == CONFIG_NEW
    finally:
        release(holder)
    safety.restore(backup_id, **deck.rkw())
    assert deck.config.read_bytes() == CONFIG_INI


def test_a13_a_lock_left_by_a_killed_process_is_free(tmp_path):
    deck = make_deck(tmp_path)
    holder = hold_lock(deck.backup_root / ".lock")
    holder.kill()
    holder.wait(timeout=30)
    for stream in (holder.stdin, holder.stdout):
        if stream is not None:
            stream.close()
    (deck.backup_root / ".lock").write_text("999999\n")
    _applied(deck)


def test_a13_the_lock_is_held_while_targets_are_replaced(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    targets = {str(deck.config), str(deck.gus)}
    lock = str(deck.backup_root / ".lock")
    seen: list[bool] = []

    def hook(_rec, op, _path, path2):
        if op == "replace" and path2 in targets:
            fd = REAL["os_open"](lock, os.O_RDWR)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                seen.append(True)
            else:
                seen.append(False)
            finally:
                os.close(fd)

    Recorder(monkeypatch, deck.base, hook=hook)
    safety.apply(changes, **deck.kw())
    monkeypatch.undo()
    assert seen == [True, True]
    fd = REAL["os_open"](lock, os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)  # free again once apply returned
    finally:
        os.close(fd)


# ---------------------------------------------------------------------------- A14 space


def test_a14_a_full_backup_disk_is_no_space_before_any_write(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    before = deck_state(deck)
    asked = full_disk(monkeypatch, deck.backup_root)
    refusal("no_space", safety.apply, changes, **deck.kw())
    monkeypatch.undo()
    root = os.path.realpath(deck.backup_root)
    assert [path for path in asked if path == root or path.startswith(root + os.sep)]
    _assert_untouched(deck, before)


@pytest.mark.parametrize("key", ["config", "gus"])
def test_a14_a_full_target_disk_is_no_space_before_any_write(tmp_path, monkeypatch, key):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    before = deck_state(deck)
    full_disk(monkeypatch, deck.files[key].parent)
    refusal("no_space", safety.apply, changes, **deck.kw())
    monkeypatch.undo()
    _assert_untouched(deck, before)


# A14 backup-room fixtures: new contents whose total size differs from the originals'
# total (CONFIG_NEW + GUS_NEW happen to sum to the same 126 bytes as the originals, which
# cannot tell "sum of originals" from "sum of new sizes"). "shorter" catches an apply that
# sizes the backup by the new bytes and so accepts one byte short of the originals;
# "longer" catches the same mistake in the exact-room case, where it would refuse.
A14_NEW = {
    "shorter": (
        b"[Render]\r\nUpscaler=XeSS\r\n",
        b"[/Script/Engine.GameUserSettings]\nResolutionSizeX=960\n",
    ),
    "longer": (
        CONFIG_NEW + b"Textures=Medium\r\nAmbientOcclusion=Off\r\n",
        GUS_NEW + b"FrameRateLimit=35.000000\nbUseVSync=False\n",
    ),
}


def _a14_changes(deck, config_new, gus_new):
    """The two changes of _changes, with new bytes of a different total length."""
    needed = len(CONFIG_INI) + len(GUS_INI)
    assert needed != len(config_new) + len(gus_new)
    return needed, [
        safety.plan(deck.card, str(deck.config), config_new),
        safety.plan(deck.card, str(deck.gus), gus_new),
    ]


@pytest.mark.parametrize("sizes", sorted(A14_NEW))
def test_a14_backup_room_one_byte_short_of_the_originals_is_no_space(tmp_path, monkeypatch, sizes):
    # A14: the backup filesystem needs the sum of the ORIGINAL sizes (not the new ones).
    deck = make_deck(tmp_path)
    needed, changes = _a14_changes(deck, *A14_NEW[sizes])
    before = deck_state(deck)
    low_disk(monkeypatch, {deck.backup_root: needed - 1})
    refusal("no_space", safety.apply, changes, **deck.kw())
    monkeypatch.undo()
    _assert_untouched(deck, before)


@pytest.mark.parametrize("sizes", sorted(A14_NEW))
def test_a14_backup_room_exactly_the_originals_is_enough(tmp_path, monkeypatch, sizes):
    # A14: exactly the sum of the ORIGINAL sizes free on the backup filesystem is accepted.
    deck = make_deck(tmp_path)
    config_new, gus_new = A14_NEW[sizes]
    needed, changes = _a14_changes(deck, config_new, gus_new)
    low_disk(monkeypatch, {deck.backup_root: needed})
    backup_id = safety.apply(changes, **deck.kw())
    monkeypatch.undo()
    assert deck.config.read_bytes() == config_new
    assert deck.gus.read_bytes() == gus_new
    assert backup_folders(deck) == [backup_id]


def test_a14_target_room_one_byte_short_of_the_new_size_is_no_space(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    before = deck_state(deck)
    low_disk(monkeypatch, {deck.gus.parent: len(GUS_NEW) - 1})
    refusal("no_space", safety.apply, changes, **deck.kw())
    monkeypatch.undo()
    _assert_untouched(deck, before)


def test_a14_a_mib_free_everywhere_is_enough(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    free = {deck.backup_root: MiB, deck.config.parent: MiB, deck.gus.parent: MiB}
    low_disk(monkeypatch, free)
    safety.apply(changes, **deck.kw())
    monkeypatch.undo()
    assert deck.config.read_bytes() == CONFIG_NEW
    assert deck.gus.read_bytes() == GUS_NEW


# ---------------------------------------------------------------------------- A15 SD card


def _unplug(deck) -> Path:
    away = deck.base / "unplugged"
    deck.library.rename(away)
    return away


def test_a15_sd_card_missing_at_apply_is_target_unavailable(tmp_path):
    deck = make_deck(tmp_path, layout="sd")
    changes = _changes(deck)
    away = _unplug(deck)
    error = refusal("target_unavailable", safety.apply, changes, **deck.kw())
    assert TARGET_UNAVAILABLE_TEXT in str(error)
    assert not os.path.lexists(deck.library), "nothing is created"
    assert backup_folders(deck) == []
    assert (away / "steamapps" / "common" / "Fake Game" / "config.ini").read_bytes() == CONFIG_INI


def test_a15_a_missing_target_folder_at_apply_is_target_unavailable(tmp_path):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    windows = deck.gus.parent
    windows.rename(deck.base / "moved-away")
    refusal("target_unavailable", safety.apply, changes, **deck.kw())
    assert not os.path.lexists(windows)
    assert deck.config.read_bytes() == CONFIG_INI
    assert backup_folders(deck) == []


def test_a15_sd_card_missing_at_restore_keeps_the_backup(tmp_path):
    deck = make_deck(tmp_path, layout="sd")
    backup_id = _applied(deck)
    backup_before = content_state(deck.backup_root / backup_id)
    away = _unplug(deck)
    error = refusal("target_unavailable", safety.restore, backup_id, **deck.rkw())
    assert TARGET_UNAVAILABLE_TEXT in str(error)
    assert not os.path.lexists(deck.library), "restore never creates folders"
    assert content_state(deck.backup_root / backup_id) == backup_before
    assert backup_id in complete_ids(safety.list_backups(str(deck.backup_root)))
    away.rename(deck.library)
    safety.restore(backup_id, **deck.rkw())
    assert deck.config.read_bytes() == CONFIG_INI
    assert deck.gus.read_bytes() == GUS_INI


# ---------------------------------------------------------------------------- A18 root


def _bad_roots(deck):
    a_file = deck.base / "a-file"
    a_file.write_text("x")
    link = deck.home / "backups-link"
    inside_library = deck.library / "deckforge-backups"
    inside_library.mkdir()
    link.symlink_to(inside_library, target_is_directory=True)
    inside_install = deck.install / "backups"
    inside_install.mkdir()
    inside_prefix = deck.prefix / "backups"
    inside_prefix.mkdir()
    return {
        "relative": "deckforge/backups",
        "missing": str(deck.home / "no-such-folder"),
        "file": str(a_file),
        "inside_library": str(inside_library),
        "inside_install": str(inside_install),
        "inside_prefix": str(inside_prefix),
        "link_into_library": str(link),
    }


@pytest.mark.parametrize(
    "shape",
    [
        "relative",
        "missing",
        "file",
        "inside_library",
        "inside_install",
        "inside_prefix",
        "link_into_library",
    ],
)
def test_a18_apply_refuses_a_bad_backup_root(tmp_path, monkeypatch, shape):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    root = _bad_roots(deck)[shape]
    monkeypatch.chdir(deck.home)
    before = deck_state(deck)
    refusal("bad_backup_root", safety.apply, changes, **deck.kw(backup_root=root))
    assert deck_state(deck) == before
    assert not os.path.lexists(deck.home / "no-such-folder")


@pytest.mark.parametrize("shape", ["relative", "missing", "file"])
def test_a18_restore_and_list_refuse_a_bad_backup_root(tmp_path, monkeypatch, shape):
    deck = make_deck(tmp_path)
    backup_id = _applied(deck)
    root = _bad_roots(deck)[shape]
    monkeypatch.chdir(deck.home)
    refusal("bad_backup_root", safety.restore, backup_id, **deck.rkw(backup_root=root))
    refusal("bad_backup_root", safety.list_backups, root)
    assert deck.config.read_bytes() == CONFIG_NEW
    assert not os.path.lexists(deck.home / "no-such-folder")
