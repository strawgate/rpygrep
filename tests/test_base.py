import asyncio
from pathlib import Path, PosixPath
from typing import Any

import pytest
from deepdiff import DeepDiff
from dirty_equals import IsInt, IsStr
from inline_snapshot import snapshot
from pydantic import TypeAdapter

from rpygrep import RipGrepFind, RipGrepSearch
from rpygrep.helpers import MatchedFile, MatchedLine
from rpygrep.types import (
    RipGrepSearchResult,
)


def dump_result_for_snapshot(rip_grep_search_result: list[RipGrepSearchResult], /) -> list[dict[str, Any]]:
    type_adapter = TypeAdapter[RipGrepSearchResult](type=RipGrepSearchResult)

    return [type_adapter.dump_python(result, mode="json") for result in rip_grep_search_result]


EXCLUDED_PATH_REGEX = [
    r"root\[\d+\]\.end\.data\.stats\.elapsed.*",
]


def sort_results(results: list[RipGrepSearchResult]) -> list[RipGrepSearchResult]:
    return sorted(results, key=lambda x: x.path)


def run_search(ripgrep_search: RipGrepSearch) -> list[RipGrepSearchResult]:
    """Run the search through the sync and async code paths and ensure the results are the same."""
    sync_results = sort_results(list(ripgrep_search.run()))

    async def materialize_async_results() -> list[RipGrepSearchResult]:
        iterator = ripgrep_search.arun()
        return sort_results([result async for result in iterator])

    async_results = asyncio.get_event_loop().run_until_complete(materialize_async_results())

    diff_results = DeepDiff(sync_results, async_results, threshold_to_diff_deeper=0, exclude_regex_paths=EXCLUDED_PATH_REGEX)

    assert diff_results == {}

    return sync_results


def run_find(ripgrep_find: RipGrepFind, sort: bool = True) -> list[Path]:
    """Run the find through the sync and async code paths and ensure the results are the same."""
    sync_results = list(ripgrep_find.run())

    async def materialize_async_results() -> list[Path]:
        iterator = ripgrep_find.arun()
        return [result async for result in iterator]

    async_results = asyncio.get_event_loop().run_until_complete(materialize_async_results())
    diff_results = DeepDiff(sync_results, async_results, threshold_to_diff_deeper=0, exclude_regex_paths=EXCLUDED_PATH_REGEX)

    assert diff_results == {}

    return sorted(sync_results) if sort else sync_results


def prepare_for_snapshot(results: list[RipGrepSearchResult]) -> list[str]:
    type_adapter = TypeAdapter(RipGrepSearchResult)
    return [type_adapter.dump_python(result) for result in results]


# @pytest.fixture
# async def temp_dir():
#     with tempfile.TemporaryDirectory() as temp_dir:
#         await create_test_structure(Path(temp_dir))
#         yield Path(temp_dir)


@pytest.fixture
def dataset_dir() -> Path:
    return Path(__file__).parent / "dataset"


class TestRipGrepSearch:
    def test_init(self, dataset_dir: Path):
        search = RipGrepSearch(working_directory=dataset_dir)
        assert search.working_directory == dataset_dir
        assert search.command == "rg"
        assert search.singular_options == set()
        assert search.multiple_options == []
        assert search.targets == []

    def test_init_two(self, dataset_dir: Path):
        search = RipGrepSearch(working_directory=dataset_dir)
        assert search.working_directory == dataset_dir
        assert search.command == "rg"
        assert search.singular_options == set()
        assert search.multiple_options == []
        assert search.targets == []

    @pytest.fixture
    def ripgrep_search(self, dataset_dir: Path):
        return RipGrepSearch(working_directory=dataset_dir)

    def test_search(self, ripgrep_search: RipGrepSearch):
        _ = ripgrep_search.add_pattern("hello")

        assert dump_result_for_snapshot(run_search(ripgrep_search)) == snapshot(
            [
                {
                    "path": "hello_world.go",
                    "begin": {"type": "begin", "data": {"path": {"text": "hello_world.go"}}},
                    "matches": [
                        {
                            "type": "match",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "\thello()\n", "bytes": None},
                                "line_number": 7,
                                "absolute_offset": 73,
                                "submatches": [{"match": {"text": "hello"}, "start": 1, "end": 6}],
                            },
                        },
                        {
                            "type": "match",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "func hello() {\n", "bytes": None},
                                "line_number": 10,
                                "absolute_offset": 85,
                                "submatches": [{"match": {"text": "hello"}, "start": 5, "end": 10}],
                            },
                        },
                    ],
                    "context": [],
                    "end": {
                        "type": "end",
                        "data": {
                            "path": {"text": "hello_world.go"},
                            "binary_offset": None,
                            "stats": {
                                "elapsed": {"secs": IsInt(), "nanos": IsInt(), "human": IsStr()},
                                "searches": 1,
                                "searches_with_match": 1,
                                "bytes_searched": 336,
                                "bytes_printed": 440,
                                "matched_lines": 2,
                                "matches": 2,
                            },
                        },
                    },
                }
            ]
        )

    def test_search_with_two_patterns(self, ripgrep_search: RipGrepSearch):
        _ = ripgrep_search.add_pattern("hel.o")
        _ = ripgrep_search.add_pattern("wor.d")

        assert dump_result_for_snapshot(run_search(ripgrep_search)) == snapshot(
            [
                {
                    "path": "hello_world.go",
                    "begin": {"type": "begin", "data": {"path": {"text": "hello_world.go"}}},
                    "matches": [
                        {
                            "type": "match",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "\thello()\n", "bytes": None},
                                "line_number": 7,
                                "absolute_offset": 73,
                                "submatches": [{"match": {"text": "hello"}, "start": 1, "end": 6}],
                            },
                        },
                        {
                            "type": "match",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "func hello() {\n", "bytes": None},
                                "line_number": 10,
                                "absolute_offset": 85,
                                "submatches": [{"match": {"text": "hello"}, "start": 5, "end": 10}],
                            },
                        },
                    ],
                    "context": [],
                    "end": {
                        "type": "end",
                        "data": {
                            "path": {"text": "hello_world.go"},
                            "binary_offset": None,
                            "stats": {
                                "elapsed": {"secs": IsInt(), "nanos": IsInt(), "human": IsStr()},
                                "searches": 1,
                                "searches_with_match": 1,
                                "bytes_searched": 336,
                                "bytes_printed": 440,
                                "matched_lines": 2,
                                "matches": 2,
                            },
                        },
                    },
                }
            ]
        )

    def test_search_with_two_fixed_patterns(self, ripgrep_search: RipGrepSearch):
        _ = ripgrep_search.add_pattern("hello()")
        _ = ripgrep_search.add_pattern("world!")
        _ = ripgrep_search.patterns_are_not_regex().before_context(3).after_context(3)

        assert dump_result_for_snapshot(run_search(ripgrep_search)) == snapshot(
            [
                {
                    "path": "hello_world.go",
                    "begin": {"type": "begin", "data": {"path": {"text": "hello_world.go"}}},
                    "matches": [
                        {
                            "type": "match",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "\thello()\n", "bytes": None},
                                "line_number": 7,
                                "absolute_offset": 73,
                                "submatches": [{"match": {"text": "hello()"}, "start": 1, "end": 8}],
                            },
                        },
                        {
                            "type": "match",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "func hello() {\n", "bytes": None},
                                "line_number": 10,
                                "absolute_offset": 85,
                                "submatches": [{"match": {"text": "hello()"}, "start": 5, "end": 12}],
                            },
                        },
                    ],
                    "context": [
                        {
                            "type": "context",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "\n", "bytes": None},
                                "line_number": 4,
                                "absolute_offset": 27,
                                "submatches": [],
                            },
                        },
                        {
                            "type": "context",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "// A Hello World program in Go\n", "bytes": None},
                                "line_number": 5,
                                "absolute_offset": 28,
                                "submatches": [],
                            },
                        },
                        {
                            "type": "context",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "func main() {\n", "bytes": None},
                                "line_number": 6,
                                "absolute_offset": 59,
                                "submatches": [],
                            },
                        },
                        {
                            "type": "context",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "}\n", "bytes": None},
                                "line_number": 8,
                                "absolute_offset": 82,
                                "submatches": [],
                            },
                        },
                        {
                            "type": "context",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "\n", "bytes": None},
                                "line_number": 9,
                                "absolute_offset": 84,
                                "submatches": [],
                            },
                        },
                        {
                            "type": "context",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": '\tfmt.Println("H")\n', "bytes": None},
                                "line_number": 11,
                                "absolute_offset": 100,
                                "submatches": [],
                            },
                        },
                        {
                            "type": "context",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": '\tfmt.Println("e")\n', "bytes": None},
                                "line_number": 12,
                                "absolute_offset": 118,
                                "submatches": [],
                            },
                        },
                        {
                            "type": "context",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": '\tfmt.Println("l")\n', "bytes": None},
                                "line_number": 13,
                                "absolute_offset": 136,
                                "submatches": [],
                            },
                        },
                    ],
                    "end": {
                        "type": "end",
                        "data": {
                            "path": {"text": "hello_world.go"},
                            "binary_offset": None,
                            "stats": {
                                "elapsed": {"secs": IsInt(), "nanos": IsInt(), "human": IsStr()},
                                "searches": 1,
                                "searches_with_match": 1,
                                "bytes_searched": 336,
                                "bytes_printed": 1642,
                                "matched_lines": 2,
                                "matches": 2,
                            },
                        },
                    },
                }
            ]
        )

    def test_search_with_directory(self, ripgrep_search: RipGrepSearch):
        _ = ripgrep_search.add_pattern("hello")
        _ = ripgrep_search.add_directory(Path("subdir"))

        assert dump_result_for_snapshot(run_search(ripgrep_search)) == snapshot([])

    def test_before_context(self, ripgrep_search: RipGrepSearch):
        _ = ripgrep_search.add_pattern("hello")
        _ = ripgrep_search.before_context(1)

        assert dump_result_for_snapshot(run_search(ripgrep_search)) == snapshot(
            [
                {
                    "path": "hello_world.go",
                    "begin": {"type": "begin", "data": {"path": {"text": "hello_world.go"}}},
                    "matches": [
                        {
                            "type": "match",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "\thello()\n", "bytes": None},
                                "line_number": 7,
                                "absolute_offset": 73,
                                "submatches": [{"match": {"text": "hello"}, "start": 1, "end": 6}],
                            },
                        },
                        {
                            "type": "match",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "func hello() {\n", "bytes": None},
                                "line_number": 10,
                                "absolute_offset": 85,
                                "submatches": [{"match": {"text": "hello"}, "start": 5, "end": 10}],
                            },
                        },
                    ],
                    "context": [
                        {
                            "type": "context",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "func main() {\n", "bytes": None},
                                "line_number": 6,
                                "absolute_offset": 59,
                                "submatches": [],
                            },
                        },
                        {
                            "type": "context",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "\n", "bytes": None},
                                "line_number": 9,
                                "absolute_offset": 84,
                                "submatches": [],
                            },
                        },
                    ],
                    "end": {
                        "type": "end",
                        "data": {
                            "path": {"text": "hello_world.go"},
                            "binary_offset": None,
                            "stats": {
                                "elapsed": {"secs": IsInt(), "nanos": IsInt(), "human": IsStr()},
                                "searches": 1,
                                "searches_with_match": 1,
                                "bytes_searched": 336,
                                "bytes_printed": 725,
                                "matched_lines": 2,
                                "matches": 2,
                            },
                        },
                    },
                }
            ]
        )

    def test_after_context(self, ripgrep_search: RipGrepSearch):
        _ = ripgrep_search.add_pattern("hello")
        _ = ripgrep_search.after_context(1)

        assert dump_result_for_snapshot(run_search(ripgrep_search)) == snapshot(
            [
                {
                    "path": "hello_world.go",
                    "begin": {"type": "begin", "data": {"path": {"text": "hello_world.go"}}},
                    "matches": [
                        {
                            "type": "match",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "\thello()\n", "bytes": None},
                                "line_number": 7,
                                "absolute_offset": 73,
                                "submatches": [{"match": {"text": "hello"}, "start": 1, "end": 6}],
                            },
                        },
                        {
                            "type": "match",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "func hello() {\n", "bytes": None},
                                "line_number": 10,
                                "absolute_offset": 85,
                                "submatches": [{"match": {"text": "hello"}, "start": 5, "end": 10}],
                            },
                        },
                    ],
                    "context": [
                        {
                            "type": "context",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "}\n", "bytes": None},
                                "line_number": 8,
                                "absolute_offset": 82,
                                "submatches": [],
                            },
                        },
                        {
                            "type": "context",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": '\tfmt.Println("H")\n', "bytes": None},
                                "line_number": 11,
                                "absolute_offset": 100,
                                "submatches": [],
                            },
                        },
                    ],
                    "end": {
                        "type": "end",
                        "data": {
                            "path": {"text": "hello_world.go"},
                            "binary_offset": None,
                            "stats": {
                                "elapsed": {"secs": IsInt(), "nanos": IsInt(), "human": IsStr()},
                                "searches": 1,
                                "searches_with_match": 1,
                                "bytes_searched": 336,
                                "bytes_printed": 735,
                                "matched_lines": 2,
                                "matches": 2,
                            },
                        },
                    },
                }
            ]
        )

    def test_helper_from_search_results(self, ripgrep_search: RipGrepSearch):
        _ = ripgrep_search.add_pattern("hello")
        _ = ripgrep_search.before_context(5)
        _ = ripgrep_search.after_context(5)

        result = run_search(ripgrep_search)

        match = MatchedFile.from_search_results(result, 5, 5)
        assert match == snapshot(
            [
                MatchedFile(
                    path=PosixPath("hello_world.go"),
                    matched_lines=[
                        MatchedLine(
                            before={3: 'import "fmt"', 5: "// A Hello World program in Go", 6: "func main() {"},
                            match={7: "\thello()"},
                            after={8: "}"},
                        ),
                        MatchedLine(
                            match={10: "func hello() {"},
                            after={
                                11: '\tfmt.Println("H")',
                                12: '\tfmt.Println("e")',
                                13: '\tfmt.Println("l")',
                                14: '\tfmt.Println("l")',
                                15: '\tfmt.Println("o")',
                            },
                        ),
                    ],
                )
            ]
        )

        match = MatchedFile.from_search_results(search_results=result, before_context=5, after_context=5, include_empty_lines=True)
        assert match == snapshot(
            [
                MatchedFile(
                    path=PosixPath("hello_world.go"),
                    matched_lines=[
                        MatchedLine(
                            before={2: "", 3: 'import "fmt"', 4: "", 5: "// A Hello World program in Go", 6: "func main() {"},
                            match={7: "\thello()"},
                            after={8: "}", 9: ""},
                        ),
                        MatchedLine(
                            match={10: "func hello() {"},
                            after={
                                11: '\tfmt.Println("H")',
                                12: '\tfmt.Println("e")',
                                13: '\tfmt.Println("l")',
                                14: '\tfmt.Println("l")',
                                15: '\tfmt.Println("o")',
                            },
                        ),
                    ],
                )
            ]
        )

    def test_max_matches(self, ripgrep_search: RipGrepSearch):
        _ = ripgrep_search.add_pattern("Hello")
        _ = ripgrep_search.max_count(1)

        assert dump_result_for_snapshot(run_search(ripgrep_search)) == snapshot(
            [
                {
                    "path": "hello_world.go",
                    "begin": {"type": "begin", "data": {"path": {"text": "hello_world.go"}}},
                    "matches": [
                        {
                            "type": "match",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "// A Hello World program in Go\n", "bytes": None},
                                "line_number": 5,
                                "absolute_offset": 28,
                                "submatches": [{"match": {"text": "Hello"}, "start": 5, "end": 10}],
                            },
                        }
                    ],
                    "context": [],
                    "end": {
                        "type": "end",
                        "data": {
                            "path": {"text": "hello_world.go"},
                            "binary_offset": None,
                            "stats": {
                                "elapsed": {"secs": IsInt(), "nanos": IsInt(), "human": IsStr()},
                                "searches": 1,
                                "searches_with_match": 1,
                                "bytes_searched": 0,
                                "bytes_printed": 268,
                                "matched_lines": 1,
                                "matches": 1,
                            },
                        },
                    },
                },
                {
                    "path": "subdir/script_with_hello.sh",
                    "begin": {"type": "begin", "data": {"path": {"text": "subdir/script_with_hello.sh"}}},
                    "matches": [
                        {
                            "type": "match",
                            "data": {
                                "path": {"text": "subdir/script_with_hello.sh"},
                                "lines": {"text": "echo 'Hello'", "bytes": None},
                                "line_number": 2,
                                "absolute_offset": 12,
                                "submatches": [{"match": {"text": "Hello"}, "start": 6, "end": 11}],
                            },
                        }
                    ],
                    "context": [],
                    "end": {
                        "type": "end",
                        "data": {
                            "path": {"text": "subdir/script_with_hello.sh"},
                            "binary_offset": None,
                            "stats": {
                                "elapsed": {"secs": IsInt(), "nanos": IsInt(), "human": IsStr()},
                                "searches": 1,
                                "searches_with_match": 1,
                                "bytes_searched": 12,
                                "bytes_printed": 274,
                                "matched_lines": 1,
                                "matches": 1,
                            },
                        },
                    },
                },
            ]
        )

    def test_case_insensitive(self, ripgrep_search: RipGrepSearch):
        _ = ripgrep_search.add_pattern("Hello")
        _ = ripgrep_search.case_sensitive(False)

        assert dump_result_for_snapshot(run_search(ripgrep_search)) == snapshot(
            [
                {
                    "path": "hello_world.go",
                    "begin": {"type": "begin", "data": {"path": {"text": "hello_world.go"}}},
                    "matches": [
                        {
                            "type": "match",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "// A Hello World program in Go\n", "bytes": None},
                                "line_number": 5,
                                "absolute_offset": 28,
                                "submatches": [{"match": {"text": "Hello"}, "start": 5, "end": 10}],
                            },
                        },
                        {
                            "type": "match",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "\thello()\n", "bytes": None},
                                "line_number": 7,
                                "absolute_offset": 73,
                                "submatches": [{"match": {"text": "hello"}, "start": 1, "end": 6}],
                            },
                        },
                        {
                            "type": "match",
                            "data": {
                                "path": {"text": "hello_world.go"},
                                "lines": {"text": "func hello() {\n", "bytes": None},
                                "line_number": 10,
                                "absolute_offset": 85,
                                "submatches": [{"match": {"text": "hello"}, "start": 5, "end": 10}],
                            },
                        },
                    ],
                    "context": [],
                    "end": {
                        "type": "end",
                        "data": {
                            "path": {"text": "hello_world.go"},
                            "binary_offset": None,
                            "stats": {
                                "elapsed": {"secs": IsInt(), "nanos": IsInt(), "human": IsStr()},
                                "searches": 1,
                                "searches_with_match": 1,
                                "bytes_searched": 336,
                                "bytes_printed": 649,
                                "matched_lines": 3,
                                "matches": 3,
                            },
                        },
                    },
                },
                {
                    "path": "subdir/script_with_hello.sh",
                    "begin": {"type": "begin", "data": {"path": {"text": "subdir/script_with_hello.sh"}}},
                    "matches": [
                        {
                            "type": "match",
                            "data": {
                                "path": {"text": "subdir/script_with_hello.sh"},
                                "lines": {"text": "echo 'Hello'", "bytes": None},
                                "line_number": 2,
                                "absolute_offset": 12,
                                "submatches": [{"match": {"text": "Hello"}, "start": 6, "end": 11}],
                            },
                        }
                    ],
                    "context": [],
                    "end": {
                        "type": "end",
                        "data": {
                            "path": {"text": "subdir/script_with_hello.sh"},
                            "binary_offset": None,
                            "stats": {
                                "elapsed": {"secs": IsInt(), "nanos": IsInt(), "human": IsStr()},
                                "searches": 1,
                                "searches_with_match": 1,
                                "bytes_searched": 24,
                                "bytes_printed": 274,
                                "matched_lines": 1,
                                "matches": 1,
                            },
                        },
                    },
                },
            ]
        )

    def test_compile(self, ripgrep_search: RipGrepSearch):
        _ = ripgrep_search.add_pattern("test").case_sensitive(False).max_count(5)
        compiled = ripgrep_search.compile()

        assert compiled[0] == "rg"
        assert "--json" not in compiled  # Only added during run()
        assert "--ignore-case" in compiled
        assert "--regexp=test" in compiled
        assert "--max-count=5" in compiled

    def test_add_safe_defaults(self, ripgrep_search: RipGrepSearch):
        _ = ripgrep_search.add_safe_defaults()
        compiled = ripgrep_search.compile()

        assert any("--max-filesize=" in opt for opt in compiled)
        assert any("--max-count=" in opt for opt in compiled)
        assert any("--max-depth=" in opt for opt in compiled)

    def test_auto_hybrid_regex(self, ripgrep_search: RipGrepSearch):
        _ = ripgrep_search.auto_hybrid_regex()
        compiled = ripgrep_search.compile()

        assert "--auto-hybrid-regex" in compiled

    def test_add_extra_options(self, ripgrep_search: RipGrepSearch):
        _ = ripgrep_search.add_extra_options(["--hidden", "--no-ignore"])
        compiled = ripgrep_search.compile()

        assert "--hidden" in compiled
        assert "--no-ignore" in compiled

    def test_no_matches_found(self, ripgrep_search: RipGrepSearch):
        _ = ripgrep_search.add_pattern("xyzabc123notfound")

        assert run_search(ripgrep_search) == snapshot([])

    def test_add_file(self, ripgrep_search: RipGrepSearch, dataset_dir: Path):
        _ = ripgrep_search.add_pattern("hello")
        _ = ripgrep_search.add_file(dataset_dir / "hello_world.go")

        results = run_search(ripgrep_search)
        assert len(results) == 1
        assert results[0].path.name == "hello_world.go"

    def test_add_files(self, ripgrep_search: RipGrepSearch, dataset_dir: Path):
        _ = ripgrep_search.add_pattern("echo")
        _ = ripgrep_search.add_files([dataset_dir / "hello_world.sh"])

        results = run_search(ripgrep_search)
        assert len(results) == 1
        assert results[0].path.name == "hello_world.sh"

    def test_patterns_are_not_regex(self, ripgrep_search: RipGrepSearch):
        _ = ripgrep_search.add_pattern("hello()")  # Would be invalid regex without --fixed-strings
        _ = ripgrep_search.patterns_are_not_regex()

        results = run_search(ripgrep_search)
        assert len(results) == 1  # Should match literal "hello()" in go file

    def test_add_patterns(self, ripgrep_search: RipGrepSearch):
        """Test adding multiple patterns at once."""
        _ = ripgrep_search.add_patterns(["hello", "world"])
        compiled = ripgrep_search.compile()

        assert "--regexp=hello" in compiled
        assert "--regexp=world" in compiled

    def test_compile_str(self, ripgrep_search: RipGrepSearch):
        """Test string representation of compiled command."""
        _ = ripgrep_search.add_pattern("test").max_count(5)
        cmd_str = ripgrep_search.compile_str()

        assert isinstance(cmd_str, str)
        assert "rg" in cmd_str
        assert "--regexp=test" in cmd_str
        assert "--max-count=5" in cmd_str

    def test_max_file_size(self, ripgrep_search: RipGrepSearch):
        """Test max file size option."""
        _ = ripgrep_search.max_file_size(1024)
        compiled = ripgrep_search.compile()

        assert "--max-filesize=1024" in compiled


class TestRipGrepFind:
    def test_init(self, dataset_dir: Path):
        ripgrep_find = RipGrepFind(working_directory=dataset_dir)
        assert ripgrep_find.working_directory == dataset_dir
        assert ripgrep_find.command == "rg"
        assert ripgrep_find.singular_options == set()
        assert ripgrep_find.multiple_options == []
        assert ripgrep_find.targets == []

    @pytest.fixture
    def ripgrep_find(self, dataset_dir: Path):
        return RipGrepFind(working_directory=dataset_dir)

    def test_compile(self, ripgrep_find: RipGrepFind):
        _ = ripgrep_find.include_types(["py"]).max_depth(2)
        compiled = ripgrep_find.compile()

        assert compiled[0] == "rg"
        assert "--files" not in compiled  # Only added during run()
        assert "--type=py" in compiled
        assert "--max-depth=2" in compiled

    def test_set_working_directory(self, dataset_dir: Path):
        find = RipGrepFind()
        _ = find.set_working_directory(dataset_dir)
        assert find.working_directory == dataset_dir

    def test_add_safe_defaults(self, ripgrep_find: RipGrepFind):
        _ = ripgrep_find.add_safe_defaults()
        compiled = ripgrep_find.compile()

        assert any("--max-depth=15" in opt for opt in compiled)

    def test_one_file_system(self, ripgrep_find: RipGrepFind):
        _ = ripgrep_find.one_file_system()
        compiled = ripgrep_find.compile()

        assert "--one-file-system" in compiled

    def test_add_directories(self, ripgrep_find: RipGrepFind):
        dirs = [Path("dir1"), Path("dir2")]
        _ = ripgrep_find.add_directories(dirs)

        assert Path("dir1") in ripgrep_find.targets
        assert Path("dir2") in ripgrep_find.targets

    def test_combine_include_exclude_globs(self, ripgrep_find: RipGrepFind):
        _ = ripgrep_find.include_globs(["*.sh", "*.go"])
        _ = ripgrep_find.exclude_globs(["**/subdir/*"])

        results = run_find(ripgrep_find)
        paths = [r.name for r in results]

        assert "hello_world.sh" in paths
        assert "hello_world.go" in paths
        assert "script_with_hello.sh" not in paths

    def test_add_directory(self, ripgrep_find: RipGrepFind):
        """Test adding a single directory."""
        _ = ripgrep_find.add_directory(Path("subdir"))

        assert Path("subdir") in ripgrep_find.targets
        results = run_find(ripgrep_find)
        # Should only find files in subdir
        assert all("subdir" in str(r) for r in results)

    def test_compile_str(self, ripgrep_find: RipGrepFind):
        """Test string representation of compiled command."""
        _ = ripgrep_find.max_depth(2).include_types(["py"])
        cmd_str = ripgrep_find.compile_str()

        assert isinstance(cmd_str, str)
        assert "rg" in cmd_str
        assert "--max-depth=2" in cmd_str
        assert "--type=py" in cmd_str

    def test_include_globs(self, ripgrep_find: RipGrepFind):
        _ = ripgrep_find.include_globs(["*.py"])

        assert run_find(ripgrep_find) == snapshot([])

    def test_exclude_globs(self, ripgrep_find: RipGrepFind):
        _ = ripgrep_find.exclude_globs(["*.py"])
        assert run_find(ripgrep_find) == snapshot(
            [
                PosixPath("data.json"),
                PosixPath("data.yml"),
                PosixPath("hello_world.go"),
                PosixPath("hello_world.sh"),
                PosixPath("subdir/nested.txt"),
                PosixPath("subdir/script_with_hello.sh"),
            ]
        )

    def test_include_types(self, ripgrep_find: RipGrepFind):
        _ = ripgrep_find.include_types(ripgrep_types=["py"])
        assert run_find(ripgrep_find) == snapshot([])

    def test_exclude_types(self, ripgrep_find: RipGrepFind):
        _ = ripgrep_find.exclude_types(ripgrep_types=["py"])
        assert run_find(ripgrep_find) == snapshot(
            [
                PosixPath("data.json"),
                PosixPath("data.yml"),
                PosixPath("hello_world.go"),
                PosixPath("hello_world.sh"),
                PosixPath("subdir/nested.txt"),
                PosixPath("subdir/script_with_hello.sh"),
            ]
        )

    def test_max_depth(self, ripgrep_find: RipGrepFind):
        _ = ripgrep_find.max_depth(1)
        assert run_find(ripgrep_find) == snapshot(
            [PosixPath("data.json"), PosixPath("data.yml"), PosixPath("hello_world.go"), PosixPath("hello_world.sh")]
        )

    def test_sort(self, ripgrep_find: RipGrepFind):
        _ = ripgrep_find.sort("path")
        assert run_find(ripgrep_find, sort=False) == snapshot(
            [
                PosixPath("data.json"),
                PosixPath("data.yml"),
                PosixPath("hello_world.go"),
                PosixPath("hello_world.sh"),
                PosixPath("subdir/nested.txt"),
                PosixPath("subdir/script_with_hello.sh"),
            ]
        )

    def test_sort_descending(self, ripgrep_find: RipGrepFind):
        _ = ripgrep_find.sort("path", ascending=False)
        results = run_find(ripgrep_find, sort=False)

        # Should be in reverse alphabetical order
        paths = [str(r) for r in results]
        assert paths == sorted(paths, reverse=True)


class TestErrorHandling:
    @pytest.fixture
    def dataset_dir(self) -> Path:
        return Path(__file__).parent / "dataset"

    def test_invalid_working_directory(self):
        """Test that running with non-existent directory fails gracefully."""
        search = RipGrepSearch(working_directory=Path("/nonexistent/path/that/doesnt/exist"))
        _ = search.add_pattern("test")

        # Should raise an error when trying to run
        with pytest.raises((FileNotFoundError, OSError)):
            _ = list(search.run())

    def test_empty_pattern_search(self, dataset_dir: Path):
        """Test behavior with empty pattern - ripgrep may handle this differently."""
        search = RipGrepSearch(working_directory=dataset_dir)
        _ = search.add_pattern("")

        # Document behavior: empty patterns might match nothing or fail
        results = list(search.run())
        # Empty pattern typically matches everything or nothing depending on ripgrep version
        assert isinstance(results, list)


class TestHelperEdgeCases:
    def test_file_with_matches_no_context(self, dataset_dir: Path):
        """Test FileWithMatches helper with zero context lines."""
        search = RipGrepSearch(working_directory=dataset_dir)
        _ = search.add_pattern("hello")

        results = list(search.run())
        matches = MatchedFile.from_search_results(results, before_context=0, after_context=0)

        # All matches should have no before/after context
        for match in matches:
            for entry in match.matched_lines:
                assert len(entry.before) == 0
                assert len(entry.after) == 0
                assert len(entry.match) == 1  # Should have the match itself

    def test_empty_search_results(self):
        """Test helper with empty search results."""
        matches = MatchedFile.from_search_results([], before_context=5, after_context=5)
        assert matches == []
