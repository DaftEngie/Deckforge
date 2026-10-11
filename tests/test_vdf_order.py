# Pins V5 "the last one in the file first" for keys parse saw more than once (PR A).
# A key repeated after one of its case variants counts at its last position in the file.
import pytest

from deckforge import vdf

TWICE_WITH_VARIANT = '"a" { "x" "1" }\n"A" { "y" "2" }\n"a" "flat"'


@pytest.mark.parametrize(
    ("text", "keys", "expected"),
    [
        pytest.param('"Name" "1"\n"NAME" "2"\n"Name" "3"', ("name",), "3", id="str-values"),
        pytest.param(
            '"a" { "x" "old" }\n"A" { "x" "variant" }\n"a" { "x" "new" }',
            ("a", "x"),
            "new",
            id="block-values",
        ),
        pytest.param(TWICE_WITH_VARIANT, ("a", "y"), "2", id="falls-back-to-variant"),
        pytest.param(TWICE_WITH_VARIANT, ("a", "x"), None, id="replaced-block-is-gone"),
    ],
)
def test_find_counts_a_repeated_key_at_its_last_position(text, keys, expected):
    assert vdf.find(vdf.parse(text), *keys) == expected


def test_parse_orders_keys_by_their_last_occurrence():
    parsed = vdf.parse('"Name" "1"\n"NAME" "2"\n"Name" "3"')
    assert list(parsed.items()) == [("NAME", "2"), ("Name", "3")]
