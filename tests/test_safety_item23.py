# Contracts for docs/specs/safety-module.md clarifier answer 23 (written A23 below), decided
# after the verifier review, 2026-10-23. Written before the implementation; fixtures and
# fakes: test_safety_support.py. Nothing here touches a real Steam install (R7).
#
# apply(changes, *, backup_root, confirm, proc_root, userdata_roots) -> str
#   Ctrl-C (A23, AC8): a KeyboardInterrupt at any write-side step (os.mkdir, write, fsync,
#         os.rename, os.replace, chmod ...) is handled like any other failure:
#     Post: apply raises SafetyError with code "interrupted"; the KeyboardInterrupt never
#           escapes apply.
#     Post: every target is fully old (rolled back by the answer-7 rules) or was never
#           touched: the whole Deck outside backup_root is byte- and mode-identical to before.
#     Post: no temp file is left in any game folder (the folders' listings are unchanged).
#     Post: any complete backup left is intact (its copies match its manifest); if a target
#           had been replaced before the interrupt, exactly one complete backup is kept.
#     Post: the error text names the backup folder when a complete backup exists ("where the
#           backup is") and names every target that had been replaced and was put back
#           ("what was restored").
#     Post: the backup_root lock is free afterwards (a new apply is not busy).
#   Modelled two ways: KeyboardInterrupt raised from the patched call (Recorder), and a real
#   SIGINT delivered with signal.raise_signal at that step (the default Python handler then
#   raises KeyboardInterrupt), so a design that installs its own SIGINT handler is held to
#   the same result.
#
# restore(backup_id, *, backup_root, confirm, proc_root) -> dict
#   Ctrl-C (A23): a KeyboardInterrupt at any write-side step:
#     Post: restore raises SafetyError("interrupted"); every target is whole (its applied or
#           its original bytes) with its mode; no temp file in a game folder; the backup
#           being restored is unchanged; restore run again finishes the job; the error names
#           every target already replaced.
#     Post: with "overwrite": any complete new backup is kept, and the error names its folder;
#           once the edited file is gone from disk, a complete new backup holds it.
#   Non-ini records (A23): before any write, a manifest record is refused with
#         not_a_settings_file when its base name does not end in ".ini" (case-insensitive),
#         is user.reg / system.reg / userdef.reg, or its path ends in ".vdf". This holds even
#         when the manifest's own roots were edited so that the record lies inside them.
#     Post: nothing is written: the Deck and the backup root (apart from .lock) are
#           unchanged, also when only the second of two records is bad.
#     A record ending in ".INI" (upper case) is not refused by this rule.
#   Path rules on disk (A3, A21, A23): restore re-checks the answer-3 rules against the
#         manifest's roots before writing:
#     - a target whose parent folder became a link leading out of the game -> outside_game;
#     - a record rerouted to an .ini outside the game folders -> outside_game;
#     - a manifest whose roots were edited to "/" is refused and nothing is written. The
#       spec names no code for this; A18 gives bad_backup_root (the backup root is then
#       inside the manifest's game folders), and outside_game or backup_corrupt are
#       accepted too. Known limit kept: roots edited to some other folder that holds an
#       .ini are not caught by any rule in the spec.
#
# Group (A23): the manifest records each file's gid; apply and restore set the temp file's
#   group to that gid (os.fchown(fd, -1, gid)) before the rename.
#     Post: after apply and after restore, each file's st_gid equals the original's, also
#           when the original group differs from the process's primary group.
#     Post: if changing the group fails with EPERM, the write still happens (bytes and mode
#           as usual) and the warning group_not_kept is reported.
#     ASSUMED (the spec says "reported" but not where): apply returns only the backup_id and
#     restore's result has exactly four keys (A19, pinned by test_safety_restore.py), so the
#     least surprising place is a logging record at WARNING or above whose message holds
#     "group_not_kept" and the target's path. With no handler configured, Python prints
#     such a record on stderr, so the CLI user sees it too.
#   Setting a different group: as root (this sandbox) os.chown may set any gid, even one
#   with no group entry, so the original is given gid <egid> + 4243; as a normal user (CI) a
#   file can only be given one of the user's own supplementary groups, so one of
#   os.getgroups() other than the primary group is used. The test fails (it does not skip)
#   if no such group exists, since skips are refused by the tamper check.
#
# Test gaps (A23):
#   - apply, and restore with "overwrite", fsync the .tmp-<id> folder after its last entry
#     is created and before it is renamed to <id> (seen through the Recorder).
#   - the path re-checks above.

import errno
import logging
import os
import signal
import stat
from pathlib import Path

import pytest
from test_safety_apply import THREE, _changes, _count_steps, _verify_complete
from test_safety_restore import (
    KEYS,
    NEW,
    OLD,
    USER_EDIT,
    _apply,
    _count_restore_steps,
    _each_target_old_or_new,
)
from test_safety_support import (
    CONFIG_INI,
    CONFIG_NEW,
    GUS_INI,
    GUS_NEW,
    Recorder,
    abs_path,
    backup_folders,
    complete_ids,
    content_state,
    copy_holding,
    deck_state,
    error_text,
    fd_path,
    make_deck,
    manifest_files,
    mode_of,
    read_manifest,
    refusal,
    sha,
    target_folder_names,
    write_manifest,
)

from deckforge import safety

HOWS = ("raise", "signal")
OTHER_GID_OFFSET = 4243


# ---------------------------------------------------------------------------- helpers


def _interrupt_at(monkeypatch, deck, step: int, how: str) -> Recorder:
    """A Recorder that delivers Ctrl-C at write-side step `step`."""
    if how == "raise":

        def ctrl_c(op: str, path: str) -> KeyboardInterrupt:
            return KeyboardInterrupt(f"Ctrl-C at {op} {path}")

        return Recorder(monkeypatch, deck.base, fail_at=step, make_error=ctrl_c)

    assert signal.getsignal(signal.SIGINT) is signal.default_int_handler, (
        "the test runner changed the SIGINT handler"
    )

    def hook(rec: Recorder, _op: str, _path: str, _path2: str | None) -> None:
        if not rec.failed and len(rec.steps) == step:
            rec.failed = True
            signal.raise_signal(signal.SIGINT)

    return Recorder(monkeypatch, deck.base, hook=hook)


def _interrupted(call, *args, **kwargs) -> Exception:
    """Run `call`; it must turn Ctrl-C into SafetyError("interrupted"). A KeyboardInterrupt
    that escapes is turned into a test failure here, so it cannot stop the test run."""
    try:
        call(*args, **kwargs)
    except safety.SafetyError as error:
        assert error.code == "interrupted", f"expected interrupted, got {error.code}: {error}"
        return error
    except KeyboardInterrupt as escaped:
        pytest.fail(f"KeyboardInterrupt escaped instead of SafetyError('interrupted'): {escaped}")
    pytest.fail("Ctrl-C was swallowed: the call returned normally")


def _replaced_before(rec: Recorder, step: int, targets: set[str]) -> list[str]:
    """Targets os.replace-d before the interrupt (the step that raised did not happen)."""
    return [dst for op, _src, dst in rec.steps[:step] if op == "replace" and dst in targets]


# ---------------------------------------------------------------------------- Ctrl-C apply


@pytest.mark.parametrize("how", HOWS)
def test_a23_ctrl_c_at_any_apply_step_is_interrupted_and_rolls_back(tmp_path, monkeypatch, how):
    total = _count_steps(tmp_path, monkeypatch)
    for step in range(total):
        deck = make_deck(tmp_path / f"step{step}")
        changes = _changes(deck)
        before = deck_state(deck)
        names = target_folder_names(deck.writable)
        targets = {str(path) for path in deck.writable}
        rec = _interrupt_at(monkeypatch, deck, step, how)
        error = _interrupted(safety.apply, changes, **deck.kw())
        monkeypatch.undo()
        label = f"step {step}: {rec.steps[step] if step < len(rec.steps) else '?'}"
        assert rec.failed, f"step {step} was never reached"
        assert deck_state(deck) == before, f"{label}: a target is not back to old"
        assert target_folder_names(deck.writable) == names, f"{label}: temp file left"
        completes = complete_ids(safety.list_backups(str(deck.backup_root)))
        assert len(completes) <= 1, label
        for backup_id in completes:
            _verify_complete(deck, backup_id)
        replaced = _replaced_before(rec, step, targets)
        if replaced:
            assert completes, f"{label}: a target was written but the backup was not kept"
        said = error_text(error)
        if completes:
            assert str(deck.backup_root / completes[0]) in said, f"{label}: {said}"
        for path in replaced:
            assert path in said, f"{label}: the message does not say {path} was restored"
        # The lock is free again: a new apply is not busy.
        safety.apply([safety.plan(deck.card, str(deck.config), CONFIG_NEW)], **deck.kw())
        assert deck.config.read_bytes() == CONFIG_NEW, label


def test_a23_ctrl_c_after_the_first_target_names_the_backup_and_the_restored_file(
    tmp_path, monkeypatch
):
    # The plainest case, spelled out: Ctrl-C while the second target is being replaced.
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    before = deck_state(deck)
    targets = {str(path) for path in deck.writable}
    replaced: list[str] = []

    def hook(_rec, op, _path, path2):
        if op == "replace" and path2 in targets:
            replaced.append(path2)
            if len(replaced) == 2:
                raise KeyboardInterrupt

    Recorder(monkeypatch, deck.base, hook=hook)
    error = _interrupted(safety.apply, changes, **deck.kw())
    monkeypatch.undo()
    assert deck_state(deck) == before
    for key, old, _new in THREE:
        assert deck.files[key].read_bytes() == old
    [backup_id] = complete_ids(safety.list_backups(str(deck.backup_root)))
    _verify_complete(deck, backup_id)
    said = error_text(error)
    assert str(deck.backup_root / backup_id) in said
    assert replaced[0] in said


# ---------------------------------------------------------------------------- Ctrl-C restore


@pytest.mark.parametrize("how", HOWS)
def test_a23_ctrl_c_at_any_restore_step_is_interrupted_and_leaves_whole_files(
    tmp_path, monkeypatch, how
):
    total = _count_restore_steps(tmp_path, monkeypatch)
    for step in range(total):
        deck = make_deck(tmp_path / f"step{step}")
        before = deck_state(deck)
        backup_id = _apply(deck)
        names = target_folder_names(deck.writable)
        backup_before = content_state(deck.backup_root / backup_id)
        targets = {str(path) for path in deck.writable}
        rec = _interrupt_at(monkeypatch, deck, step, how)
        error = _interrupted(safety.restore, backup_id, **deck.rkw())
        monkeypatch.undo()
        label = f"step {step}"
        assert rec.failed, f"{label} was never reached"
        _each_target_old_or_new(deck, label)
        assert target_folder_names(deck.writable) == names, f"{label}: temp file left"
        assert content_state(deck.backup_root / backup_id) == backup_before, label
        said = error_text(error)
        for path in _replaced_before(rec, step, targets):
            assert path in said, f"{label}: the message does not say {path} was restored"
        safety.restore(backup_id, **deck.rkw())
        assert deck_state(deck) == before, f"{label}: a second restore does not finish"


@pytest.mark.parametrize("how", HOWS)
def test_a23_ctrl_c_during_an_overwrite_restore_keeps_the_new_backup(tmp_path, monkeypatch, how):
    counter = make_deck(tmp_path / "count")
    counted = _apply(counter)
    counter.config.write_bytes(USER_EDIT)
    rec = Recorder(monkeypatch, counter.base)
    safety.restore(counted, **counter.rkw(confirm=frozenset({"overwrite"})))
    monkeypatch.undo()
    total = len(rec.steps)
    for step in range(total):
        deck = make_deck(tmp_path / f"step{step}")
        backup_id = _apply(deck)
        deck.config.write_bytes(USER_EDIT)
        names = target_folder_names(deck.writable)
        original = content_state(deck.backup_root / backup_id)
        rec = _interrupt_at(monkeypatch, deck, step, how)
        error = _interrupted(
            safety.restore, backup_id, **deck.rkw(confirm=frozenset({"overwrite"}))
        )
        monkeypatch.undo()
        label = f"step {step}"
        assert rec.failed, f"{label} was never reached"
        assert content_state(deck.backup_root / backup_id) == original, label
        assert target_folder_names(deck.writable) == names, f"{label}: temp file left"
        config = deck.config.read_bytes()
        assert config in (USER_EDIT, CONFIG_INI), f"{label}: config is not whole"
        for key in ("gus", "engine"):
            assert deck.files[key].read_bytes() in (OLD[key], NEW[key]), label
        for key in KEYS:
            assert mode_of(deck.files[key]) == 0o644, label
        listed = complete_ids(safety.list_backups(str(deck.backup_root)))
        others = [found for found in listed if found != backup_id]
        assert len(others) <= 1, label
        if config != USER_EDIT:
            assert others, f"{label}: the edited file was overwritten without a backup"
            assert copy_holding(deck, others[0], USER_EDIT)
        if others:
            assert str(deck.backup_root / others[0]) in error_text(error), (
                f"{label}: the message does not say where the new backup is"
            )


# ---------------------------------------------------------------------------- non-ini records


def _roots_to(manifest, deck, new_root: str) -> int:
    """Replace, anywhere in the manifest, every string equal to the card's install_path or
    prefix_path with `new_root`. Returns how many were replaced."""
    olds = {str(deck.install), str(deck.prefix)}
    count = 0

    def walk(node):
        nonlocal count
        items = node.items() if isinstance(node, dict) else enumerate(node)
        for key, value in list(items):
            if isinstance(value, str) and value in olds:
                node[key] = new_root
                count += 1
            elif isinstance(value, dict | list):
                walk(value)

    walk(manifest)
    return count


def _reroute(deck, backup_id, record_of: Path, target: Path, roots: str | None = None) -> None:
    """Edit the manifest so the record of `record_of` points at `target`, with sha256_after
    set to `target`'s current bytes; the backup copy, size and sha256_before stay as they
    are, so the backup still verifies. With `roots`, the manifest's roots are moved too."""
    manifest = read_manifest(deck, backup_id)
    item = next(item for item in manifest_files(manifest) if item["path"] == str(record_of))
    item["path"] = str(target)
    item["sha256_after"] = sha(target.read_bytes())
    if roots is not None:
        assert _roots_to(manifest, deck, roots) >= 1, (
            f"the manifest records no roots to re-check against (A21, A23): {manifest}"
        )
    write_manifest(deck, backup_id, manifest)


def _non_ini_target(deck, shape: str) -> tuple[Path, str | None]:
    """(target, roots to write into the manifest or None)."""
    if shape == "save":
        return deck.files["save"], None
    if shape == "boot_config":
        return deck.files["boot"], None
    if shape == "user_reg":
        return deck.files["userreg"], None
    if shape == "system_reg":
        return deck.files["sysreg"], None
    if shape == "userdef_reg":
        path = deck.prefix / "userdef.reg"
        path.write_bytes(b"WINE REGISTRY Version 2\n")
        return path, None
    if shape == "ini_bak":
        path = deck.install / "config.ini.bak"
        path.write_bytes(CONFIG_NEW)
        return path, None
    if shape == "vdf_in_game":
        path = deck.install / "steam_settings.vdf"
        path.write_bytes(b'"Settings"\n{\n}\n')
        return path, None
    if shape == "steam_config_vdf":  # roots edited so the target lies inside them
        return deck.files["configvdf"], str(deck.steam_root)
    if shape == "steam_localconfig_vdf":
        return deck.files["localconfig"], str(deck.steam_root)
    raise ValueError(shape)


NON_INI = [
    "save",
    "boot_config",
    "user_reg",
    "system_reg",
    "userdef_reg",
    "ini_bak",
    "vdf_in_game",
    "steam_config_vdf",
    "steam_localconfig_vdf",
]


@pytest.mark.parametrize("confirm", [frozenset(), frozenset({"overwrite"})], ids=["plain", "ow"])
@pytest.mark.parametrize("shape", NON_INI)
def test_a23_restore_refuses_a_record_that_is_not_an_ini_file(tmp_path, shape, confirm):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck, ("config",))
    target, roots = _non_ini_target(deck, shape)
    target_bytes = target.read_bytes()
    _reroute(deck, backup_id, deck.config, target, roots)
    lock = deck.backup_root / ".lock"
    lock.touch()
    before = deck_state(deck)
    backup_before = content_state(deck.backup_root, skip=[lock])
    refusal("not_a_settings_file", safety.restore, backup_id, **deck.rkw(confirm=confirm))
    assert target.read_bytes() == target_bytes
    assert deck_state(deck) == before
    assert content_state(deck.backup_root, skip=[lock]) == backup_before, "no new backup"


def test_a23_one_bad_record_stops_the_whole_restore_before_any_write(tmp_path):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck, ("config", "gus"))
    _reroute(deck, backup_id, deck.gus, deck.files["userreg"])
    before = deck_state(deck)
    refusal("not_a_settings_file", safety.restore, backup_id, **deck.rkw())
    assert deck_state(deck) == before
    assert deck.config.read_bytes() == CONFIG_NEW, "the good record was restored anyway"


def test_a23_a_record_ending_in_upper_case_ini_is_not_refused_by_name(tmp_path):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck, ("config",))
    target = deck.install / "Extra Settings.INI"
    target.write_bytes(CONFIG_NEW)
    target.chmod(0o644)
    _reroute(deck, backup_id, deck.config, target)
    result = safety.restore(backup_id, **deck.rkw())
    assert result["restored"] == [str(target)]
    assert target.read_bytes() == CONFIG_INI


# ---------------------------------------------------------------------------- path re-checks


def test_a23_restore_refuses_a_target_whose_parent_became_a_link_out_of_the_game(tmp_path):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck, ("gus",))
    windows = deck.gus.parent
    outside = deck.base / "outside" / "Windows"
    outside.parent.mkdir()
    windows.rename(outside)
    windows.symlink_to(outside, target_is_directory=True)
    before = deck_state(deck)
    refusal("outside_game", safety.restore, backup_id, **deck.rkw())
    assert (outside / "GameUserSettings.ini").read_bytes() == GUS_NEW
    assert deck_state(deck) == before


def _outside_ini(deck) -> Path:
    path = deck.base / "outside" / "evil.ini"
    path.parent.mkdir()
    path.write_bytes(b"[Mine]\nKeep=1\n")
    path.chmod(0o644)
    return path


def test_a23_restore_refuses_a_record_rerouted_to_an_ini_outside_the_game(tmp_path):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck, ("config",))
    target = _outside_ini(deck)
    _reroute(deck, backup_id, deck.config, target)
    before = deck_state(deck)
    refusal("outside_game", safety.restore, backup_id, **deck.rkw())
    assert target.read_bytes() == b"[Mine]\nKeep=1\n"
    assert deck_state(deck) == before


def test_a23_restore_refuses_a_manifest_whose_roots_were_edited_to_slash(tmp_path):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck, ("config",))
    target = _outside_ini(deck)
    _reroute(deck, backup_id, deck.config, target, roots="/")
    before = deck_state(deck)
    with pytest.raises(safety.SafetyError) as info:
        safety.restore(backup_id, **deck.rkw())
    # With roots "/", the backup root itself lies inside the manifest's game folders, which
    # A18 refuses (bad_backup_root); a refusal by the A3 rule or as a corrupt backup is as
    # good. What matters: refused, and nothing written.
    assert info.value.code in ("bad_backup_root", "outside_game", "backup_corrupt"), info.value
    assert target.read_bytes() == b"[Mine]\nKeep=1\n"
    assert deck_state(deck) == before


# ---------------------------------------------------------------------------- group


def _other_gid() -> int:
    """A gid other than the process's primary group that this process may give a file."""
    primary = os.getegid()
    if os.geteuid() == 0:
        return primary + OTHER_GID_OFFSET
    others = [gid for gid in os.getgroups() if gid != primary]
    assert others, "no supplementary group to test with: the group tests cannot run here"
    return others[0]


def _set_group(path: Path, gid: int) -> None:
    os.chown(path, -1, gid)
    assert path.stat().st_gid == gid


def _record(deck, backup_id, path: Path) -> dict:
    return next(
        item for item in manifest_files(read_manifest(deck, backup_id)) if item["path"] == str(path)
    )


def test_a23_manifest_records_gid_and_apply_then_restore_keep_the_group(tmp_path):
    deck = make_deck(tmp_path)
    gid = _other_gid()
    for path in (deck.config, deck.gus):
        _set_group(path, gid)
    backup_id = _apply(deck, ("config", "gus"))
    for path, new in ((deck.config, CONFIG_NEW), (deck.gus, GUS_NEW)):
        assert path.read_bytes() == new
        assert path.stat().st_gid == gid, f"apply lost the group of {path}"
        assert mode_of(path) == 0o644
        assert _record(deck, backup_id, path)["gid"] == gid
    safety.restore(backup_id, **deck.rkw())
    for path, old in ((deck.config, CONFIG_INI), (deck.gus, GUS_INI)):
        assert path.read_bytes() == old
        assert path.stat().st_gid == gid, f"restore lost the group of {path}"
        assert mode_of(path) == 0o644


def test_a23_restore_puts_back_the_gid_recorded_in_the_manifest(tmp_path):
    deck = make_deck(tmp_path)
    gid = _other_gid()
    _set_group(deck.config, gid)
    backup_id = _apply(deck, ("config",))
    _set_group(deck.config, os.getegid())  # the bytes are still ours; only the group moved
    safety.restore(backup_id, **deck.rkw())
    assert deck.config.read_bytes() == CONFIG_INI
    assert deck.config.stat().st_gid == gid


def _chown_denied(monkeypatch, deck) -> list[str]:
    """os.fchown / os.chown / os.lchown of anything under the Deck fail with EPERM, as the
    kernel answers a normal user asking for a group they are not in. Returns the paths."""
    asked: list[str] = []
    root = abs_path(deck.base)

    def denied(target) -> None:
        shown = fd_path(target) if isinstance(target, int) else abs_path(target)
        if shown == root or shown.startswith(root + os.sep):
            asked.append(shown)
            raise PermissionError(errno.EPERM, os.strerror(errno.EPERM), shown)

    real_fchown, real_chown, real_lchown = os.fchown, os.chown, os.lchown

    def fchown(fd, uid, gid):
        denied(fd)
        return real_fchown(fd, uid, gid)

    def chown(path, uid, gid, *args, **kwargs):
        denied(path)
        return real_chown(path, uid, gid, *args, **kwargs)

    def lchown(path, uid, gid):
        denied(path)
        return real_lchown(path, uid, gid)

    monkeypatch.setattr(os, "fchown", fchown)
    monkeypatch.setattr(os, "chown", chown)
    monkeypatch.setattr(os, "lchown", lchown)
    return asked


def _group_warnings(caplog, path: Path) -> list[str]:
    return [
        record.getMessage()
        for record in caplog.records
        if record.levelno >= logging.WARNING
        and "group_not_kept" in record.getMessage()
        and str(path) in record.getMessage()
    ]


def test_a23_apply_with_group_change_denied_still_writes_and_warns_group_not_kept(
    tmp_path, monkeypatch, caplog
):
    deck = make_deck(tmp_path)
    _set_group(deck.config, _other_gid())
    changes = _changes(deck, ("config",))
    asked = _chown_denied(monkeypatch, deck)
    with caplog.at_level(logging.WARNING):
        backup_id = safety.apply(changes, **deck.kw())
    monkeypatch.undo()
    assert asked, "apply never tried to set the temp file's group"
    assert deck.config.read_bytes() == CONFIG_NEW
    assert mode_of(deck.config) == 0o644
    assert stat.S_IMODE(_record(deck, backup_id, deck.config)["mode"]) == 0o644
    assert _group_warnings(caplog, deck.config), caplog.text


def test_a23_restore_with_group_change_denied_still_restores_and_warns_group_not_kept(
    tmp_path, monkeypatch, caplog
):
    deck = make_deck(tmp_path)
    _set_group(deck.config, _other_gid())
    backup_id = _apply(deck, ("config",))
    asked = _chown_denied(monkeypatch, deck)
    with caplog.at_level(logging.WARNING):
        result = safety.restore(backup_id, **deck.rkw())
    monkeypatch.undo()
    assert asked, "restore never tried to set the temp file's group"
    assert result["restored"] == [str(deck.config)]
    assert deck.config.read_bytes() == CONFIG_INI
    assert mode_of(deck.config) == 0o644
    assert _group_warnings(caplog, deck.config), caplog.text


# ---------------------------------------------------------------------------- folder fsync


def _tmp_folder_synced_before_rename(steps, tmp_dir: str, final_dir: str) -> None:
    renames = [
        i
        for i, (op, src, dst) in enumerate(steps)
        if op in ("rename", "replace") and src == tmp_dir and dst == final_dir
    ]
    assert len(renames) == 1, f"{tmp_dir} is renamed to {final_dir} once"
    rename = renames[0]
    inside = [
        i
        for i, (_op, path, path2) in enumerate(steps[:rename])
        if (path and path.startswith(tmp_dir + os.sep))
        or (path2 and path2.startswith(tmp_dir + os.sep))
    ]
    assert inside, "the backup's files are made inside .tmp-<id>"
    syncs = [
        i
        for i, (op, path, _) in enumerate(steps)
        if op == "fsync" and path == tmp_dir and max(inside) < i < rename
    ]
    assert syncs, "the .tmp-<id> folder is fsynced after its last entry and before the rename"


def test_a23_apply_fsyncs_the_tmp_backup_folder_before_renaming_it(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    rec = Recorder(monkeypatch, deck.base)
    backup_id = safety.apply(changes, **deck.kw())
    monkeypatch.undo()
    _tmp_folder_synced_before_rename(
        rec.steps,
        str(deck.backup_root / f".tmp-{backup_id}"),
        str(deck.backup_root / backup_id),
    )


def test_a23_overwrite_restore_fsyncs_the_new_tmp_backup_folder_before_renaming_it(
    tmp_path, monkeypatch
):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck, ("config", "gus"))
    deck.config.write_bytes(USER_EDIT)
    rec = Recorder(monkeypatch, deck.base)
    result = safety.restore(backup_id, **deck.rkw(confirm=frozenset({"overwrite"})))
    monkeypatch.undo()
    new_id = result["new_backup_id"]
    assert new_id and new_id in backup_folders(deck)
    _tmp_folder_synced_before_rename(
        rec.steps,
        str(deck.backup_root / f".tmp-{new_id}"),
        str(deck.backup_root / new_id),
    )
