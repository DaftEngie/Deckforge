# Contracts for deckforge.settings.read_ini and Ini (docs/specs/settings-read.md, S1, with
# clarifier answers 10, 11, 14 and 18, which win over S1). Written test-first.
#
# read_ini(path) -> Ini
#   Pre:  path names a settings file (str or PathLike).
#   Pre:  checked with lstat before it is opened. It must be a regular file of at most
#         1 MiB (1,048,576 bytes is allowed, one byte more is not). A link (to anything,
#         or broken), a folder or a FIFO raises SettingsError, and a FIFO is never read.
#   Post: Ini is a frozen dataclass with sections: dict[str, dict[str, str]],
#         duplicates: list[tuple[str, str]] and encoding: str.
#   Post: encoding. A UTF-16 BOM (either byte order) means UTF-16. A UTF-8 BOM is stripped.
#         Otherwise strict UTF-8; if that fails, Latin-1, and `encoding` says so. ASSUMED:
#         `encoding` is a Python codec name, so it is compared through codecs.lookup().name.
#   Post: lines. CRLF is accepted. "[name]" opens section `name` (brackets removed, case
#         kept, slashes and dots kept). "key=value" splits at the first "=" with whitespace
#         stripped around key and value, so values keep later "=", ":", "\", "(", ")",
#         ",", ";". Lines starting with ";" or "#", blank lines and lines without "=" are
#         skipped. Keys starting with "+", "-", "." or "!" are skipped (UE arrays); dots
#         elsewhere in a key are kept. Keys before any section go to section "".
#   Post: "key=" stores "" (answer 7 builds on this).
#   Post: a repeated key in one section keeps the first value and adds (section, key) to
#         duplicates. A repeated section header merges into the first one, first value
#         wins, and each repeated key is recorded (answer 11). Skipped lines never count.
#   Inv:  names and values are compared case-sensitively: "[A]" and "[a]" are two
#         sections, "Key" and "key" two keys (answer 10).
#   Inv:  answer 18: the file is opened with os.open and O_NOFOLLOW (the lstat + O_NOFOLLOW
#         pattern of snapshot.py and measure.py), never through a following open().
#   Inv:  read-only: the file's bytes and mtime are unchanged.
#   Answer 14 (a UTF-16 BOM with bad UTF-16 has no Latin-1 fallback) is reported through
#   read_settings and is tested in test_settings_report.py.

import codecs
import dataclasses
import os
import threading

import pytest
from test_discover_output import record_opens
from test_settings_support import (
    MiB,
    REMATCH_GUS,
    SPARKING_GUS,
    WILDS_INI,
    sized,
    unblock_fifo,
    write,
)

from deckforge import settings


def read(tmp_path, data: bytes, name: str = "test.ini"):
    return settings.read_ini(write(tmp_path / name, data))


def codec(ini) -> str:
    return codecs.lookup(ini.encoding).name


# ---------------------------------------------------------------------------- the Ini type


def test_s1_ini_is_a_frozen_dataclass_with_the_three_fields(tmp_path):
    ini = read(tmp_path, b"[A]\nk=v\n")
    assert dataclasses.is_dataclass(ini)
    assert {f.name for f in dataclasses.fields(ini)} == {"sections", "duplicates", "encoding"}
    with pytest.raises(dataclasses.FrozenInstanceError):
        ini.encoding = "x"
    assert ini.sections == {"A": {"k": "v"}}
    assert list(ini.duplicates) == []
    assert isinstance(ini.encoding, str)


def test_s1_settings_error_is_an_exception():
    assert issubclass(settings.SettingsError, Exception)


def test_s1_read_ini_accepts_str_paths(tmp_path):
    path = write(tmp_path / "x.ini", b"[A]\nk=v\n")
    assert settings.read_ini(str(path)).sections == {"A": {"k": "v"}}


# ---------------------------------------------------------------------------- encodings


def test_s1_plain_utf8_is_read_as_utf8(tmp_path):
    ini = read(tmp_path, "[Graphics]\nName=caf\u00e9\n".encode())
    assert ini.sections == {"Graphics": {"Name": "caf\u00e9"}}
    assert codec(ini) == "utf-8"


def test_s1_utf8_bom_is_stripped(tmp_path):
    ini = read(tmp_path, b"\xef\xbb\xbf[Graphics]\nA=1\n")
    assert ini.sections == {"Graphics": {"A": "1"}}
    assert codec(ini) in {"utf-8", "utf-8-sig"}


def test_s1_utf8_bom_before_a_key_outside_any_section(tmp_path):
    ini = read(tmp_path, b"\xef\xbb\xbfk=v\n")
    assert ini.sections == {"": {"k": "v"}}


@pytest.mark.parametrize(
    "bom, codec_name", [(b"\xff\xfe", "utf-16-le"), (b"\xfe\xff", "utf-16-be")]
)
def test_s1_a14_utf16_bom_means_utf16(tmp_path, bom, codec_name):
    text = "[Graphics]\r\nName=caf\u00e9\r\nSharpness=0.65\r\n"
    ini = read(tmp_path, bom + text.encode(codec_name))
    assert ini.sections == {"Graphics": {"Name": "caf\u00e9", "Sharpness": "0.65"}}
    assert codec(ini).startswith("utf-16")


def test_s1_a14_invalid_utf8_without_bom_falls_back_to_latin1(tmp_path):
    ini = read(tmp_path, b"[Graphics]\nName=caf\xe9\nOther=\xff\n")
    assert ini.sections == {"Graphics": {"Name": "caf\u00e9", "Other": "\u00ff"}}
    assert codec(ini) == "iso8859-1"


# ---------------------------------------------------------------------------- lines


def test_s1_crlf_and_mixed_line_endings(tmp_path):
    ini = read(tmp_path, b"[A]\r\nk=v\r\nm=n\n[B]\r\nx=y\r\n")
    assert ini.sections == {"A": {"k": "v", "m": "n"}, "B": {"x": "y"}}


def test_s1_comments_blank_lines_and_lines_without_equals_are_skipped(tmp_path):
    data = b"; top=comment\n# hash=comment\n\n[A]\n;k=1\n#k=2\nJustText\n   \nk=3\n"
    ini = read(tmp_path, data)
    assert ini.sections == {"A": {"k": "3"}}
    assert list(ini.duplicates) == []


def test_s1_semicolon_inside_a_value_is_not_a_comment(tmp_path):
    ini = read(tmp_path, b"[A]\nk=v ; still the value\n")
    assert ini.sections == {"A": {"k": "v ; still the value"}}


def test_s1_split_at_the_first_equals_and_strip_whitespace(tmp_path):
    ini = read(tmp_path, b"[A]\n  Key  =  a = b=c  \nTab\t=\tx\n")
    assert ini.sections == {"A": {"Key": "a = b=c", "Tab": "x"}}


def test_s1_values_keep_colons_backslashes_parens_and_commas(tmp_path):
    data = (
        b"[Graphics]\n"
        b"ShaderConvertVersion=Product:1.42.0.2,File:1.42.0.2\n"
        b"NormalWindowResolution=(1280,800)\n"
        b"Path=C:\\Games\\Wilds\\x.ini\n"
        b"Paths=../../../Engine/Content\n"
    )
    ini = read(tmp_path, data)
    assert ini.sections == {
        "Graphics": {
            "ShaderConvertVersion": "Product:1.42.0.2,File:1.42.0.2",
            "NormalWindowResolution": "(1280,800)",
            "Path": "C:\\Games\\Wilds\\x.ini",
            "Paths": "../../../Engine/Content",
        }
    }


def test_s1_a7_empty_value_is_an_empty_string(tmp_path):
    ini = read(tmp_path, b"[A]\nk=\nm=   \n")
    assert ini.sections == {"A": {"k": "", "m": ""}}


def test_s1_unreal_array_keys_are_skipped(tmp_path):
    data = b"[Core.System]\nPaths=a\n+Paths=b\n+Paths=c\n-Paths=d\n.Paths=e\n!Paths=ClearArray\n"
    ini = read(tmp_path, data)
    assert ini.sections == {"Core.System": {"Paths": "a"}}
    assert list(ini.duplicates) == []


def test_s1_dotted_keys_are_kept(tmp_path):
    ini = read(tmp_path, b"[FSR3]\nr.FidelityFX.FSR3.Enabled=1\nsg.ShadowQuality=2\n")
    assert ini.sections == {"FSR3": {"r.FidelityFX.FSR3.Enabled": "1", "sg.ShadowQuality": "2"}}


def test_s1_slashed_and_dotted_section_names_are_kept_without_brackets(tmp_path):
    data = (
        b"[Graphics/FSR3]\nSharpness=0.65\n"
        b"[/Script/Engine.GameUserSettings]\nbUseDesiredScreenHeight=False\n"
        b"[GameNetDriver StatelessConnectHandlerComponent]\nk=v\n"
    )
    ini = read(tmp_path, data)
    assert ini.sections == {
        "Graphics/FSR3": {"Sharpness": "0.65"},
        "/Script/Engine.GameUserSettings": {"bUseDesiredScreenHeight": "False"},
        "GameNetDriver StatelessConnectHandlerComponent": {"k": "v"},
    }


def test_s1_keys_before_any_section_go_to_the_empty_section(tmp_path):
    ini = read(tmp_path, b"early=1\nalso=2\n[A]\nk=v\n")
    assert ini.sections == {"": {"early": "1", "also": "2"}, "A": {"k": "v"}}


def test_s1_an_empty_section_is_kept(tmp_path):
    ini = read(tmp_path, b"[ScalabilityGroups]\r\n\r\n[B]\r\nk=v\r\n")
    assert ini.sections == {"ScalabilityGroups": {}, "B": {"k": "v"}}


# ---------------------------------------------------------------------------- duplicates


def test_s1_repeated_key_keeps_the_first_value_and_is_recorded(tmp_path):
    ini = read(tmp_path, b"[A]\nx=1\ny=2\nx=3\n[B]\nx=9\n")
    assert ini.sections == {"A": {"x": "1", "y": "2"}, "B": {"x": "9"}}
    assert [tuple(pair) for pair in ini.duplicates] == [("A", "x")]


def test_s1_repeated_key_before_any_section_is_recorded_under_the_empty_section(tmp_path):
    ini = read(tmp_path, b"k=1\nk=2\n[A]\n")
    assert ini.sections[""] == {"k": "1"}
    assert [tuple(pair) for pair in ini.duplicates] == [("", "k")]


def test_s1_a_key_repeated_three_times_keeps_the_first_value(tmp_path):
    ini = read(tmp_path, b"[A]\nx=1\nx=2\nx=3\n")
    assert ini.sections == {"A": {"x": "1"}}
    assert {tuple(pair) for pair in ini.duplicates} == {("A", "x")}


def test_a11_repeated_section_merges_into_the_first_and_first_value_wins(tmp_path):
    ini = read(tmp_path, b"[A]\nx=1\n[B]\ny=2\n[A]\nx=3\nz=4\n")
    assert ini.sections == {"A": {"x": "1", "z": "4"}, "B": {"y": "2"}}
    assert [tuple(pair) for pair in ini.duplicates] == [("A", "x")]


def test_a11_repeated_section_records_each_repeated_key(tmp_path):
    ini = read(tmp_path, b"[A]\nx=1\ny=1\n[A]\nx=2\ny=2\nw=2\n")
    assert ini.sections == {"A": {"x": "1", "y": "1", "w": "2"}}
    assert {tuple(pair) for pair in ini.duplicates} == {("A", "x"), ("A", "y")}


# ---------------------------------------------------------------------------- case


def test_a10_section_names_are_case_sensitive(tmp_path):
    ini = read(tmp_path, b"[Graphics]\nA=1\n[graphics]\nA=2\n")
    assert ini.sections == {"Graphics": {"A": "1"}, "graphics": {"A": "2"}}
    assert list(ini.duplicates) == []


def test_a10_keys_are_case_sensitive(tmp_path):
    ini = read(tmp_path, b"[A]\nVSync=True\nvsync=false\n")
    assert ini.sections == {"A": {"VSync": "True", "vsync": "false"}}
    assert list(ini.duplicates) == []


def test_a10_values_keep_their_case(tmp_path):
    ini = read(tmp_path, b"[A]\nShadowQuality=LOWEST\nQuality=Balanced\n")
    assert ini.sections == {"A": {"ShadowQuality": "LOWEST", "Quality": "Balanced"}}


# ---------------------------------------------------------------------------- real files


def test_s10_rematch_real_file_reads_exactly(tmp_path):
    ini = read(tmp_path, REMATCH_GUS, "GameUserSettings.ini")
    assert ini.sections == {
        "ScalabilityGroups": {"sg.ResolutionQuality": "87", "sg.ShadingQuality": "0"}
    }
    assert list(ini.duplicates) == []
    assert codec(ini) == "utf-8"


def test_s10_sparking_zero_real_file_reads_exactly(tmp_path):
    ini = read(tmp_path, SPARKING_GUS, "GameUserSettings.ini")
    assert ini.sections == {
        "ScalabilityGroups": {
            "sg.ResolutionQuality": "100",
            "sg.ViewDistanceQuality": "1",
            "sg.AntiAliasingQuality": "3",
            "sg.ShadowQuality": "1",
            "sg.GlobalIlluminationQuality": "3",
            "sg.ReflectionQuality": "3",
            "sg.PostProcessQuality": "1",
            "sg.TextureQuality": "3",
            "sg.EffectsQuality": "1",
            "sg.FoliageQuality": "3",
            "sg.ShadingQuality": "3",
        }
    }


def test_s10_wilds_real_file_keeps_its_sections_apart(tmp_path):
    ini = read(tmp_path, WILDS_INI, "config.ini")
    assert set(ini.sections) == {"Graphics", "Graphics/FSR3", "Graphics/RayTracing", "RenderConfig"}
    assert ini.sections["Graphics"]["Quality"] == "Balanced"
    assert ini.sections["Graphics/RayTracing"]["Quality"] == "STANDARD"
    assert ini.sections["Graphics"]["AOSetting"] == "LOW"
    assert ini.sections["Graphics/RayTracing"]["AOSetting"] == "CUSTOM"
    assert ini.sections["Graphics/FSR3"] == {"EnableSharpness": "True", "Sharpness": "0.65"}
    assert ini.sections["Graphics"]["ShaderConvertVersion"] == "Product:1.42.0.2,File:1.42.0.2"
    assert ini.sections["RenderConfig"]["VSync"] == "true"
    assert len(ini.sections["Graphics"]) == 35
    assert list(ini.duplicates) == []


# ---------------------------------------------------------------------------- refusals


def test_s1_a_file_of_exactly_1_mib_is_read(tmp_path):
    path = sized(tmp_path / "config.ini", MiB)
    assert path.stat().st_size == MiB
    assert settings.read_ini(path).sections == {"Graphics": {"ShaderConvertVersion": "1"}}


def test_s1_a_file_over_1_mib_raises(tmp_path):
    path = sized(tmp_path / "config.ini", MiB + 1)
    with pytest.raises(settings.SettingsError):
        settings.read_ini(path)


def test_s1_a_link_to_a_regular_file_raises(tmp_path):
    target = write(tmp_path / "real.ini", b"[A]\nk=v\n")
    link = tmp_path / "GameUserSettings.ini"
    link.symlink_to(target)
    with pytest.raises(settings.SettingsError):
        settings.read_ini(link)


def test_s1_a_broken_link_raises(tmp_path):
    link = tmp_path / "config.ini"
    link.symlink_to(tmp_path / "missing.ini")
    with pytest.raises(settings.SettingsError):
        settings.read_ini(link)


def test_s1_a_link_to_a_folder_raises(tmp_path):
    (tmp_path / "folder").mkdir()
    link = tmp_path / "config.ini"
    link.symlink_to(tmp_path / "folder", target_is_directory=True)
    with pytest.raises(settings.SettingsError):
        settings.read_ini(link)


def test_s1_a_folder_raises(tmp_path):
    folder = tmp_path / "config.ini"
    folder.mkdir()
    with pytest.raises(settings.SettingsError):
        settings.read_ini(folder)


def test_s1_a_fifo_raises_without_being_read(tmp_path):
    fifo = tmp_path / "config.ini"
    os.mkfifo(fifo)
    done = threading.Event()
    guard = threading.Thread(target=unblock_fifo, args=(fifo, done), daemon=True)
    guard.start()
    try:
        with pytest.raises(settings.SettingsError):
            settings.read_ini(fifo)
    finally:
        done.set()
        guard.join(timeout=5)


# ---------------------------------------------------------------------------- answer 18


def test_a18_the_file_is_opened_with_o_nofollow_and_read_only(tmp_path, monkeypatch):
    path = write(tmp_path / "config.ini", b"[A]\nk=v\n")
    with monkeypatch.context() as patch:
        seen = record_opens(patch)
        settings.read_ini(path)
    mine = [
        (route, mode)
        for route, file, mode in seen
        if isinstance(file, str | bytes | os.PathLike) and os.fsdecode(file) == str(path)
    ]
    assert mine, "the settings file was not opened through any recorded route"
    for route, mode in mine:
        assert route == "os.open", f"{route} follows links"
        assert mode & os.O_NOFOLLOW
        assert mode & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND) == 0


# ---------------------------------------------------------------------------- read-only


@pytest.mark.parametrize(
    "data",
    [WILDS_INI, SPARKING_GUS, b"\xff\xfe" + "[A]\r\nk=v\r\n".encode("utf-16-le"), b"[A]\nk=\xe9\n"],
    ids=["wilds", "unreal-crlf", "utf16", "latin1"],
)
def test_s9_read_ini_leaves_the_file_unchanged(tmp_path, data):
    path = write(tmp_path / "config.ini", data)
    os.utime(path, ns=(1_700_000_000_000_000_000, 1_700_000_000_000_000_000))
    before = path.lstat()
    for _ in range(3):
        settings.read_ini(path)
    after = path.lstat()
    assert path.read_bytes() == data
    assert (after.st_mtime_ns, after.st_size, after.st_ino) == (
        before.st_mtime_ns,
        before.st_size,
        before.st_ino,
    )
    assert sorted(p.name for p in tmp_path.iterdir()) == ["config.ini"]
