# Contracts for deckforge.snapshot (docs/specs/snapshot.md): S1 scan.json, S2 settings
# files, S7 manifest. Written test-first: src/deckforge/snapshot.py does not exist yet.
# Fixtures and readers: test_snapshot_support.py (shapes the spec leaves open are listed
# there).
#
# build_snapshot(steam_root, home, out_dir, *, now) -> str
#   Pre:  steam_root, home and out_dir are path strings; now is a datetime (keyword only).
#         out_dir is not inside steam_root, a library or <home>/homebrew (S8).
#   Post: returns the path of one new zip, <out_dir>/deckforge-snapshot-<UTC stamp>Z.zip,
#         holding scan.json, sizes.json, plugins.json, system.json and manifest.json, plus
#         settings/<appid>/<n>_<basename> and logs/<basename> copies.
#   Post: SnapshotError (and no zip, no .partial) when discover.scan raises DiscoverError.
#
# S1 scan.json
#   Post: its bytes are exactly the B8 text of discover.scan(steam_root):
#         json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n".
#         (Stricter reading: B8 output includes the final newline.)
#
# S2 settings files
#   Post: for each card with installed true, entry n of settings_files is copied byte for
#         byte to settings/<appid>/<n>_<basename>; n is the index in the card's list, also
#         when an earlier entry was skipped.
#   Post: skipped, with exactly one manifest skip record each:
#           not_regular    lstat says not a regular file (link to a file or folder, FIFO,
#                          folder), so a link's target is never copied
#           too_large      larger than 1 MiB (1 MiB exactly is copied)
#           excluded_kind  kind "reg"; and, stricter reading, discover's actual registry kind
#                          "registry" (user.reg): S9 says user.reg is never opened and the
#                          clarifier answer keeps registry files out
#           unreadable     an OS error while reading
#   Post: cards with installed false contribute no settings/ members.
#   Inv:  a settings file that vanished or changed type after the scan (Steam running) is
#         skipped and recorded, never fatal.
#
# S7 manifest.json
#   Post: snapshot_version is the int 1; created_utc is ISO 8601 and equals `now` as an
#         instant. A non-UTC aware `now` still names the zip in UTC (stricter reading of the
#         "Z" suffix).
#   Post: every settings/ and logs/ member has an added-file record (zip name, source path,
#         int size equal to the member's byte count); every skip has a record (source path,
#         reason).
#
# Round trip (test-author rule 3): the write path here is "copy into the zip"; extracting
# must give byte-identical files. Checked across empty, binary, CRLF, non-UTF-8 and exactly
# 1 MiB contents.

import builtins
import contextlib
import errno
import io
import json
import os
import threading
import zipfile
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from test_detect_settings import record_opens
from test_discover_output import mkdir, put
from test_snapshot_support import (
    BIG_RE,
    MiB,
    NOW,
    PENDING,
    REAL_SCAN,
    UNITY,
    UNREAL,
    WILDS,
    WILDS_INI,
    ZIP_NAME,
    added_records,
    card,
    make_deck,
    run,
    scan_editing,
    scan_then,
    skip_reasons,
    zip_json,
    zip_members,
)

from deckforge import discover, snapshot

REQUIRED_MEMBERS = {"scan.json", "sizes.json", "plugins.json", "system.json", "manifest.json"}


def settings_members(members: dict[str, bytes]) -> dict[str, bytes]:
    return {name: data for name, data in members.items() if name.startswith("settings/")}


def real_paths(opened: list[str]) -> set[str]:
    return {os.path.realpath(path) for path in opened}


def fail_reading(monkeypatch: pytest.MonkeyPatch, path: Path, error: int) -> list[str]:
    """Opening `path` (however spelled, through open, io.open, Path.open or os.open) raises
    OSError(error). Returns the list of refused attempts."""
    target = os.path.realpath(path)
    refused: list[str] = []
    real_open, real_os_open = builtins.open, os.open

    def check(file) -> None:
        if isinstance(file, str | bytes | os.PathLike):
            text = os.fsdecode(os.fspath(file))
            if os.path.realpath(text) == target:
                refused.append(text)
                raise OSError(error, os.strerror(error), text)

    def fake_open(file, *args, **kwargs):
        check(file)
        return real_open(file, *args, **kwargs)

    def fake_os_open(file, *args, **kwargs):
        check(file)
        return real_os_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)
    monkeypatch.setattr(io, "open", fake_open)
    monkeypatch.setattr(os, "open", fake_os_open)
    return refused


# ---------------------------------------------------------------------------- S1 scan.json


def test_s1_zip_holds_the_required_json_members(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    members = zip_members(run(deck))
    assert set(members) >= REQUIRED_MEMBERS


def test_s1_scan_json_is_the_b8_text_of_discover_scan(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    expected = (
        json.dumps(REAL_SCAN(str(deck.steam)), indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    )
    members = zip_members(run(deck))
    assert members["scan.json"].decode("ascii") == expected


def test_s1_scan_json_is_ascii_even_with_non_ascii_names(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    acf = deck.sd / "steamapps" / f"appmanifest_{UNITY}.acf"
    acf.write_text(acf.read_text("utf-8").replace(f"Game {UNITY}", "Ōkami HD 大神"), "utf-8")
    members = zip_members(run(deck))
    text = members["scan.json"].decode("ascii")
    assert "\\u014ckami" in text
    assert json.loads(text) == REAL_SCAN(str(deck.steam))


@pytest.mark.parametrize("problem", ["no-libraryfolders", "unparsable", "no-steam-root"])
def test_s1_discover_error_becomes_snapshot_error_and_no_zip(tmp_path, monkeypatch, problem):
    deck = make_deck(tmp_path, monkeypatch)
    lf = deck.steam / "steamapps" / "libraryfolders.vdf"
    steam_root = str(deck.steam)
    if problem == "no-libraryfolders":
        lf.unlink()
    elif problem == "unparsable":
        lf.write_text('"libraryfolders"\n{\n', encoding="utf-8")
    else:
        steam_root = str(deck.base / "no_such_steam")
    with pytest.raises(snapshot.SnapshotError) as caught:
        snapshot.build_snapshot(steam_root, str(deck.home), str(deck.out), now=NOW)
    assert not isinstance(caught.value, discover.DiscoverError)
    leftovers = sorted(deck.out.iterdir()) if deck.out.exists() else []
    assert leftovers == []
    assert not list(deck.base.rglob("deckforge-snapshot-*"))


def test_s1_snapshot_error_is_an_exception_class():
    assert issubclass(snapshot.SnapshotError, Exception)
    assert not issubclass(snapshot.SnapshotError, discover.DiscoverError)


# ---------------------------------------------------------------------------- S2 copies


def test_s2_installed_settings_files_are_copied_at_their_index(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    result = REAL_SCAN(str(deck.steam))
    unity = [entry["path"] for entry in card(result, UNITY)["settings_files"]]
    unreal = [entry["path"] for entry in card(result, UNREAL)["settings_files"]]
    assert unity == [str(deck.settings["unity_boot"]), str(deck.settings["unity_reg"])]
    assert unreal == [str(deck.settings["unreal_engine"]), str(deck.settings["unreal_gus"])]
    members = zip_members(run(deck))
    assert settings_members(members) == {
        f"settings/{WILDS}/0_config.ini": WILDS_INI,
        f"settings/{UNITY}/0_boot.config": deck.settings["unity_boot"].read_bytes(),
        f"settings/{UNREAL}/0_Engine.ini": deck.settings["unreal_engine"].read_bytes(),
        f"settings/{UNREAL}/1_GameUserSettings.ini": deck.settings["unreal_gus"].read_bytes(),
    }


def test_s2_cards_not_installed_contribute_no_settings(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    pending = card(REAL_SCAN(str(deck.steam)), PENDING)
    assert pending["installed"] is False
    assert [entry["path"] for entry in pending["settings_files"]] == [str(deck.settings["pending"])]
    members = zip_members(run(deck))
    assert not [name for name in members if name.startswith(f"settings/{PENDING}/")]
    assert b"[Pending]" not in b"".join(settings_members(members).values())


def test_s2_index_is_kept_when_an_earlier_entry_is_skipped(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    deck.settings["unreal_engine"].write_bytes(b"\0" * (MiB + 1))
    members = zip_members(run(deck))
    names = [name for name in members if name.startswith(f"settings/{UNREAL}/")]
    assert names == [f"settings/{UNREAL}/1_GameUserSettings.ini"]


def test_s2_same_basename_twice_is_told_apart_by_index(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    gdk = put(deck.settings["unreal_engine"].parent.parent / "WinGDK" / "Engine.ini", b"[GDK]\n")
    paths = [entry["path"] for entry in card(REAL_SCAN(str(deck.steam)), UNREAL)["settings_files"]]
    assert paths == [
        str(gdk),
        str(deck.settings["unreal_engine"]),
        str(deck.settings["unreal_gus"]),
    ]
    members = zip_members(run(deck))
    assert members[f"settings/{UNREAL}/0_Engine.ini"] == b"[GDK]\n"
    assert members[f"settings/{UNREAL}/1_Engine.ini"] == deck.settings["unreal_engine"].read_bytes()
    assert f"settings/{UNREAL}/2_GameUserSettings.ini" in members


ROUND_TRIP = {
    "empty": b"",
    "binary": bytes(range(256)) * 3,
    "crlf-text": b"[Graphics]\r\nResolution=1280x800\r\nVSync=Off\r\n",
    "latin-1": "Qualit\xe9=Haute\n".encode("latin-1"),
    "no-final-newline": b"[Render]\nFSR=Quality",
    "exactly-1-MiB": (bytes(range(251)) * (MiB // 251 + 1))[:MiB],
}


@pytest.mark.parametrize("content", list(ROUND_TRIP.values()), ids=list(ROUND_TRIP))
def test_s2_round_trip_copy_then_extract_is_byte_identical(tmp_path, monkeypatch, content):
    deck = make_deck(tmp_path, monkeypatch)
    deck.settings["wilds"].write_bytes(content)
    zip_path = run(deck)
    extracted = mkdir(tmp_path / "extracted")
    with zipfile.ZipFile(zip_path) as archive:
        archive.extract(f"settings/{WILDS}/0_config.ini", extracted)
    restored = extracted / "settings" / str(WILDS) / "0_config.ini"
    assert restored.read_bytes() == content
    assert deck.settings["wilds"].read_bytes() == content
    manifest = zip_json(zip_members(zip_path), "manifest.json")
    records = added_records(manifest, f"settings/{WILDS}/0_config.ini", deck.settings["wilds"])
    assert len(records) == 1
    assert len(content) in {v for v in records[0].values() if type(v) is int}


# ---------------------------------------------------------------------------- S2 skips


def test_s2_too_large_settings_file_is_skipped_with_reason(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    assert card(REAL_SCAN(str(deck.steam)), BIG_RE)["installed"] is True
    members = zip_members(run(deck))
    assert not [name for name in members if name.startswith(f"settings/{BIG_RE}/")]
    manifest = zip_json(members, "manifest.json")
    assert skip_reasons(manifest, deck.settings["big"]) == ["too_large"]


def test_s2_exactly_1_mib_is_copied_and_one_byte_more_is_not(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    deck.settings["big"].write_bytes(b"\x07" * MiB)
    deck.settings["wilds"].write_bytes(b"\x07" * (MiB + 1))
    members = zip_members(run(deck))
    assert members[f"settings/{BIG_RE}/0_config.ini"] == b"\x07" * MiB
    assert f"settings/{WILDS}/0_config.ini" not in members
    manifest = zip_json(members, "manifest.json")
    assert skip_reasons(manifest, deck.settings["wilds"]) == ["too_large"]
    assert skip_reasons(manifest, deck.settings["big"]) == []


def test_s2_registry_kind_from_discover_is_excluded_and_never_opened(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    kinds = [entry["kind"] for entry in card(REAL_SCAN(str(deck.steam)), UNITY)["settings_files"]]
    assert kinds == ["boot_config", "registry"]
    with monkeypatch.context() as patch:
        opened = record_opens(patch)
        zip_path = run(deck)
    assert os.path.realpath(deck.settings["unity_reg"]) not in real_paths(opened)
    members = zip_members(zip_path)
    assert f"settings/{UNITY}/1_user.reg" not in members
    assert b"[Unity] token" not in b"".join(members.values())
    manifest = zip_json(members, "manifest.json")
    assert skip_reasons(manifest, deck.settings["unity_reg"]) == ["excluded_kind"]


def test_s2_kind_reg_is_excluded(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)

    def mark_reg(result: dict) -> None:
        card(result, WILDS)["settings_files"][0]["kind"] = "reg"

    scan_editing(monkeypatch, mark_reg)
    with monkeypatch.context() as patch:
        opened = record_opens(patch)
        zip_path = run(deck)
    assert os.path.realpath(deck.settings["wilds"]) not in real_paths(opened)
    members = zip_members(zip_path)
    assert f"settings/{WILDS}/0_config.ini" not in members
    manifest = zip_json(members, "manifest.json")
    assert skip_reasons(manifest, deck.settings["wilds"]) == ["excluded_kind"]


def _swap_to_file_link(deck):
    target = put(deck.base / "elsewhere" / "secret.ini", b"LINK TARGET CONTENT\n")
    deck.settings["wilds"].unlink()
    deck.settings["wilds"].symlink_to(target)
    return target


def _swap_to_folder_link(deck):
    target = mkdir(deck.base / "elsewhere" / "folder")
    put(target / "inside.ini", b"LINK TARGET CONTENT\n")
    deck.settings["wilds"].unlink()
    deck.settings["wilds"].symlink_to(target, target_is_directory=True)
    return target


def _swap_to_fifo(deck):
    deck.settings["wilds"].unlink()
    os.mkfifo(deck.settings["wilds"])


class FifoFeeder:
    """Keeps a writer ready on a FIFO, so an implementation that opens it reads
    b"LINK TARGET CONTENT" and fails the test instead of blocking forever."""

    def __init__(self, fifo: Path) -> None:
        self.fifo = fifo
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._feed, daemon=True)

    def _feed(self) -> None:
        while not self.stop.is_set():
            if not self.fifo.exists():
                self.stop.wait(0.01)
                continue
            try:
                fd = os.open(self.fifo, os.O_WRONLY | os.O_NONBLOCK)
            except OSError as error:  # ENXIO: no reader yet; ENOENT/ENOTDIR: not a FIFO yet
                if error.errno not in (errno.ENXIO, errno.ENOENT, errno.ENOTDIR, errno.EISDIR):
                    raise
                self.stop.wait(0.01)
                continue
            try:
                os.write(fd, b"LINK TARGET CONTENT\n")
            except BlockingIOError:
                self.stop.wait(0.01)
            finally:
                os.close(fd)

    def __enter__(self) -> "FifoFeeder":
        self.thread.start()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.stop.set()
        self.thread.join(timeout=5)


def _swap_to_folder(deck):
    deck.settings["wilds"].unlink()
    put(deck.settings["wilds"] / "inside.ini", b"LINK TARGET CONTENT\n")


SWAPS = {
    "link-to-file": _swap_to_file_link,
    "link-to-folder": _swap_to_folder_link,
    "fifo": _swap_to_fifo,
    "folder": _swap_to_folder,
}


@pytest.mark.parametrize("swap", sorted(SWAPS))
def test_s2_settings_entry_that_is_not_regular_is_skipped(tmp_path, monkeypatch, swap):
    """The entry was a regular file when scanned and is a link (or other non-regular entry)
    when snapshot reaches it: the lstat check decides."""
    deck = make_deck(tmp_path, monkeypatch)
    scan_then(monkeypatch, lambda: SWAPS[swap](deck))
    with FifoFeeder(deck.settings["wilds"]) if swap == "fifo" else contextlib.nullcontext():
        members = zip_members(run(deck))
    assert not [name for name in members if name.startswith(f"settings/{WILDS}/")]
    assert b"LINK TARGET CONTENT" not in b"".join(members.values())
    manifest = zip_json(members, "manifest.json")
    assert skip_reasons(manifest, deck.settings["wilds"]) == ["not_regular"]
    assert f"settings/{UNITY}/0_boot.config" in members


def test_s2_os_error_while_reading_is_skipped_as_unreadable(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    with monkeypatch.context() as patch:
        refused = fail_reading(patch, deck.settings["wilds"], errno.EIO)
        zip_path = run(deck)
    assert refused, "the settings file was never opened, so the failure was not exercised"
    members = zip_members(zip_path)
    assert f"settings/{WILDS}/0_config.ini" not in members
    manifest = zip_json(members, "manifest.json")
    assert skip_reasons(manifest, deck.settings["wilds"]) == ["unreadable"]
    assert f"settings/{UNITY}/0_boot.config" in members


def test_s2_settings_file_that_vanished_after_the_scan_is_recorded(tmp_path, monkeypatch):
    """Steam running: a file listed by the scan is gone when snapshot copies. The snapshot
    still completes and the skip is recorded (reason: unreadable or not_regular; the spec
    does not say which for a vanished file)."""
    deck = make_deck(tmp_path, monkeypatch)
    scan_then(monkeypatch, deck.settings["wilds"].unlink)
    members = zip_members(run(deck))
    assert f"settings/{WILDS}/0_config.ini" not in members
    reasons = skip_reasons(zip_json(members, "manifest.json"), deck.settings["wilds"])
    assert len(reasons) == 1
    assert reasons[0] in {"unreadable", "not_regular"}


def test_s2_skips_cover_every_reason_code_in_one_snapshot(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    deck.settings["unreal_gus"].write_bytes(b"x" * (MiB + 5))

    def link_wilds() -> None:
        _swap_to_file_link(deck)

    scan_then(monkeypatch, link_wilds)
    with monkeypatch.context() as patch:
        refused = fail_reading(patch, deck.settings["unreal_engine"], errno.EACCES)
        members = zip_members(run(deck))
    assert refused
    manifest = zip_json(members, "manifest.json")
    assert skip_reasons(manifest, deck.settings["wilds"]) == ["not_regular"]
    assert skip_reasons(manifest, deck.settings["big"]) == ["too_large"]
    assert skip_reasons(manifest, deck.settings["unreal_gus"]) == ["too_large"]
    assert skip_reasons(manifest, deck.settings["unity_reg"]) == ["excluded_kind"]
    assert skip_reasons(manifest, deck.settings["unreal_engine"]) == ["unreadable"]
    assert list(settings_members(members)) == [f"settings/{UNITY}/0_boot.config"]


# ---------------------------------------------------------------------------- S7 manifest


def test_s7_manifest_version_and_created_utc(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    manifest = zip_json(zip_members(run(deck)), "manifest.json")
    assert manifest["snapshot_version"] == 1
    assert type(manifest["snapshot_version"]) is int
    created = datetime.fromisoformat(manifest["created_utc"])
    assert created.utcoffset() == timedelta(0)
    assert created == NOW


def test_s7_non_utc_now_is_recorded_and_named_in_utc(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    local = NOW.astimezone(timezone(timedelta(hours=-6)))
    assert local.hour == 8
    zip_path = run(deck, now=local)
    assert zip_path.name == ZIP_NAME
    created = datetime.fromisoformat(
        zip_json(zip_members(zip_path), "manifest.json")["created_utc"]
    )
    assert created.utcoffset() == timedelta(0)
    assert created == NOW


def test_s7_every_copied_file_has_an_added_record(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    members = zip_members(run(deck))
    manifest = zip_json(members, "manifest.json")
    sources = {
        f"settings/{WILDS}/0_config.ini": deck.settings["wilds"],
        f"settings/{UNITY}/0_boot.config": deck.settings["unity_boot"],
        f"settings/{UNREAL}/0_Engine.ini": deck.settings["unreal_engine"],
        f"settings/{UNREAL}/1_GameUserSettings.ini": deck.settings["unreal_gus"],
    }
    sources |= {f"logs/{name}": path for name, path in deck.logs.items()}
    copied = [name for name in members if name.startswith(("settings/", "logs/"))]
    assert copied
    for name in copied:
        assert name in sources, f"unexpected member {name}"
        records = added_records(manifest, name, sources[name])
        assert len(records) == 1, f"{name}: {records}"
        sizes = {v for v in records[0].values() if type(v) is int}
        assert len(members[name]) in sizes
        assert sources[name].stat().st_size == len(members[name])


def test_s7_manifest_lists_no_member_that_is_not_in_the_zip(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    members = zip_members(run(deck))
    manifest = zip_json(members, "manifest.json")
    prefixes = ("settings/", "logs/")
    named = set()
    for entry in _records(manifest):
        named |= {value for value in entry.values() if isinstance(value, str)}
    listed = {value for value in named if value.startswith(prefixes)}
    assert listed == {name for name in members if name.startswith(prefixes)}


def _records(obj):
    if isinstance(obj, dict):
        if "reason" not in obj:
            yield obj
        for value in obj.values():
            yield from _records(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _records(value)


def test_s7_created_utc_is_iso_8601_text(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    later = datetime(2027, 1, 2, 3, 4, 5, tzinfo=UTC)
    zip_path = run(deck, now=later)
    assert zip_path.name == "deckforge-snapshot-20270102-030405Z.zip"
    text = zip_json(zip_members(zip_path), "manifest.json")["created_utc"]
    assert isinstance(text, str)
    assert text.startswith("2027-01-02T03:04:05")
    assert datetime.fromisoformat(text) == later
