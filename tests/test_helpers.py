from pathlib import PosixPath

from inline_snapshot import snapshot

from rpygrep.helpers import FileEntryMatch, FileWithMatches
from rpygrep.types import (
    RipGrepBegin,
    RipGrepBeginData,
    RipGrepDataLines,
    RipGrepDataPath,
    RipGrepDataSubmatch,
    RipGrepDataSubmatchMatch,
    RipGrepEnd,
    RipGrepEndData,
    RipGrepMatch,
    RipGrepMatchData,
    RipGrepSearchResult,
    RipGrepStats,
    RipGrepStatsElapsed,
)


def test_conversion():
    result = RipGrepSearchResult(
        path=PosixPath("code_with_hello_world.py"),
        begin=RipGrepBegin(type="begin", data=RipGrepBeginData(path=RipGrepDataPath(text="code_with_hello_world.py"))),
        matches=[
            RipGrepMatch(
                type="match",
                data=RipGrepMatchData(
                    path=RipGrepDataPath(text="code_with_hello_world.py"),
                    lines=RipGrepDataLines(text="def hello():\n"),
                    line_number=1,
                    absolute_offset=0,
                    submatches=[RipGrepDataSubmatch(match=RipGrepDataSubmatchMatch(text="hello()"), start=4, end=11)],
                ),
            ),
            RipGrepMatch(
                type="match",
                data=RipGrepMatchData(
                    path=RipGrepDataPath(text="code_with_hello_world.py"),
                    lines=RipGrepDataLines(text="    print('hello, world!')"),
                    line_number=2,
                    absolute_offset=13,
                    submatches=[RipGrepDataSubmatch(match=RipGrepDataSubmatchMatch(text="world!"), start=18, end=24)],
                ),
            ),
        ],
        context=[],
        end=RipGrepEnd(
            type="end",
            data=RipGrepEndData(
                path=RipGrepDataPath(text="code_with_hello_world.py"),
                binary_offset=None,
                stats=RipGrepStats(
                    elapsed=RipGrepStatsElapsed(secs=0, nanos=17208, human="0.000017s"),
                    searches=1,
                    searches_with_match=1,
                    bytes_searched=39,
                    bytes_printed=486,
                    matched_lines=2,
                    matches=2,
                ),
            ),
        ),
    )

    file_entry_matches: FileWithMatches = FileWithMatches.from_search_result(result, 0, 0)
    assert file_entry_matches == snapshot(
        FileWithMatches(
            path=PosixPath("code_with_hello_world.py"),
            matches=[FileEntryMatch(match={1: "def hello():"}), FileEntryMatch(match={2: "    print('hello, world!')"})],
        )
    )
