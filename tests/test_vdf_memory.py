# Memory bound for deckforge.vdf.parse on long quoted strings (PR A, verifier finding F1).
# B5 lets config.vdf reach 16 MiB. With a backtracking string pattern, one long quoted
# line costs about 200 bytes per character (3.2 GB at 16 MiB), and in a memory-capped
# process parse raises MemoryError instead of returning a result or VdfError.
import tracemalloc

import pytest

from deckforge import vdf

MIB = 1024 * 1024
BYTES_PER_CHAR_LIMIT = 64  # measured: 2 to 33 with a linear pattern; 116 to 227 backtracking


@pytest.mark.parametrize(
    ("text", "expect_error"),
    [
        pytest.param('"k" "' + "a" * MIB + '"', False, id="plain-value"),
        pytest.param('"' + "a" * MIB + '" "v"', False, id="plain-key"),
        pytest.param('"k" "' + "\\\\" * (MIB // 2) + '"', False, id="escaped-backslashes"),
        pytest.param('"k" "' + "\\q" * (MIB // 2) + '"', False, id="kept-backslashes"),
        pytest.param('"k" "' + "a" * MIB, True, id="unterminated"),
    ],
)
def test_parse_memory_stays_linear_on_a_long_quoted_string(text, expect_error):
    tracemalloc.start()
    try:
        if expect_error:
            with pytest.raises(vdf.VdfError):
                vdf.parse(text)
        else:
            assert len(vdf.parse(text)) == 1
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert peak < BYTES_PER_CHAR_LIMIT * len(text), (
        f"peak {peak / MIB:.0f} MiB for a {len(text) / MIB:.1f} MiB input"
    )
