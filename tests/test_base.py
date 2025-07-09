import asyncio
import tempfile
from pathlib import Path

import pytest
from aiofiles import open as aopen
from deepdiff import DeepDiff
from pydantic import TypeAdapter
from syrupy.assertion import SnapshotAssertion
from syrupy.extensions.json import JSONSnapshotExtension
from syrupy.filters import props

from rpygrep import RipGrepFind, RipGrepSearch, RipGrepSearchResult


# Helper function to create test files
async def create_test_file(path: Path, content: str) -> None:
    async with aopen(path, "w") as f:
        _ = await f.write(content)


# Helper function to create test directory structure
async def create_test_structure(root: Path) -> None:
    # Create some text files
    await create_test_file(root / "test_with_Hello_World.txt", "Hello, World!")
    await create_test_file(root / "code_with_hello_world.py", "def hello():\n    print('hello, world!')")
    await create_test_file(root / "data.json", '{"key": "value"}')
    await create_test_file(root / "should_be_ignored.env", "secret_key=1234567890")

    # Create a subdirectory with files
    subdir = root / "subdir"
    subdir.mkdir()
    await create_test_file(subdir / "nested.txt", "Nested content")
    await create_test_file(subdir / "script_with_hello.sh", "#!/bin/bash\necho 'Hello'")
    await create_test_file(subdir / "should_be_ignored.env", "secret_key=1234567890")

    # Create a hidden file
    await create_test_file(root / ".hidden", "Hidden content")

    # create a gitignore file
    gitdir = root / ".git"
    gitdir.mkdir()
    await create_test_file(root / ".gitignore", "*.env\n**/*.env")


EXCLUDED_PATH_REGEX = [
    r"root\[\d+\]\.end\.data\.stats\.elapsed.*",
]


def sort_results(results: list[RipGrepSearchResult]) -> list[RipGrepSearchResult]:
    return sorted(results, key=lambda x: x.path)


def run_search(ripgrep_search: RipGrepSearch) -> list[RipGrepSearchResult]:
    sync_results = sort_results(list(ripgrep_search.run()))

    async def materialize_async_results() -> list[RipGrepSearchResult]:
        iterator = ripgrep_search.arun()
        return sort_results([result async for result in iterator])

    async_results = asyncio.get_event_loop().run_until_complete(materialize_async_results())

    diff_results = DeepDiff(sync_results, async_results, threshold_to_diff_deeper=0, exclude_regex_paths=EXCLUDED_PATH_REGEX)

    assert diff_results == {}

    return sync_results


def run_find(ripgrep_find: RipGrepFind) -> list[Path]:
    sync_results = list(ripgrep_find.run())

    async def materialize_async_results() -> list[Path]:
        iterator = ripgrep_find.arun()
        return [result async for result in iterator]

    async_results = asyncio.get_event_loop().run_until_complete(materialize_async_results())
    diff_results = DeepDiff(sync_results, async_results, threshold_to_diff_deeper=0, exclude_regex_paths=EXCLUDED_PATH_REGEX)

    assert diff_results == {}

    return sync_results


def prepare_for_snapshot(results: list[RipGrepSearchResult]) -> list[str]:
    type_adapter = TypeAdapter(RipGrepSearchResult)
    return [type_adapter.dump_python(result) for result in results]


@pytest.fixture
def ripgrep_snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    return snapshot(exclude=props("elapsed"), extension_class=JSONSnapshotExtension)


@pytest.fixture
async def temp_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        await create_test_structure(Path(temp_dir))
        yield Path(temp_dir)


class TestRipGrepSearch:
    def test_init(self, temp_dir: Path):
        search = RipGrepSearch(working_directory=temp_dir)
        assert search.working_directory == temp_dir
        assert search.command == "rg"
        assert search.singular_options == set()
        assert search.multiple_options == []
        assert search.targets == []

    def test_init_two(self, temp_dir: Path):
        search = RipGrepSearch(working_directory=temp_dir)
        assert search.working_directory == temp_dir
        assert search.command == "rg"
        assert search.singular_options == set()
        assert search.multiple_options == []
        assert search.targets == []

    @pytest.fixture
    def ripgrep_search(self, temp_dir: Path):
        return RipGrepSearch(working_directory=temp_dir)

    def test_ripgrep_search(self, ripgrep_search: RipGrepSearch, ripgrep_snapshot: SnapshotAssertion):
        _ = ripgrep_search.add_pattern("hello")
        results = run_search(ripgrep_search)

        results = sort_results(results)

        assert len(results) == 1
        assert prepare_for_snapshot(results) == ripgrep_snapshot

    def test_ripgrep_search_with_directory(self, ripgrep_search: RipGrepSearch, ripgrep_snapshot: SnapshotAssertion):
        _ = ripgrep_search.add_pattern("hello")
        _ = ripgrep_search.add_directory(Path("subdir"))

        results = run_search(ripgrep_search)

        results = sort_results(results)

        assert len(results) == 0
        assert prepare_for_snapshot(results) == ripgrep_snapshot

    def test_before_context(self, ripgrep_search: RipGrepSearch, ripgrep_snapshot: SnapshotAssertion):
        _ = ripgrep_search.add_pattern("hello")
        _ = ripgrep_search.before_context(1)

        results = run_search(ripgrep_search)

        assert len(results) == 1
        assert prepare_for_snapshot(results) == ripgrep_snapshot

    def test_after_context(self, ripgrep_search: RipGrepSearch, ripgrep_snapshot: SnapshotAssertion):
        _ = ripgrep_search.add_pattern("hello")
        _ = ripgrep_search.after_context(1)

        results = run_search(ripgrep_search)

        assert len(results) == 1
        assert prepare_for_snapshot(results) == ripgrep_snapshot

    def test_max_matches(self, ripgrep_search: RipGrepSearch, ripgrep_snapshot: SnapshotAssertion):
        _ = ripgrep_search.add_pattern("Hello")
        _ = ripgrep_search.max_count(1)

        results = run_search(ripgrep_search)

        assert len(results) == 2
        for result in results:
            assert len(result.matches) == 1
        assert prepare_for_snapshot(results) == ripgrep_snapshot

    def test_case_insensitive(self, ripgrep_search: RipGrepSearch, ripgrep_snapshot: SnapshotAssertion):
        _ = ripgrep_search.add_pattern("Hello")
        _ = ripgrep_search.case_sensitive(False)

        results = run_search(ripgrep_search)

        assert len(results) == 3
        assert prepare_for_snapshot(results) == ripgrep_snapshot


class TestRipGrepFind:
    def test_init(self, temp_dir: Path):
        ripgrep_find = RipGrepFind(working_directory=temp_dir)
        assert ripgrep_find.working_directory == temp_dir
        assert ripgrep_find.command == "rg"
        assert ripgrep_find.singular_options == set()
        assert ripgrep_find.multiple_options == []
        assert ripgrep_find.targets == []

    @pytest.fixture
    def ripgrep_find(self, temp_dir: Path):
        return RipGrepFind(working_directory=temp_dir)

    def test_include_globs(self, ripgrep_find: RipGrepFind, ripgrep_snapshot: SnapshotAssertion):
        _ = ripgrep_find.include_globs(["*.py"])

        results = run_find(ripgrep_find)
        assert len(results) == 1
        assert results[0] == Path("code_with_hello_world.py")

        assert sorted(results) == ripgrep_snapshot

    def test_exclude_globs(self, ripgrep_find: RipGrepFind, ripgrep_snapshot: SnapshotAssertion):
        _ = ripgrep_find.exclude_globs(["*.py"])
        results = run_find(ripgrep_find)
        assert len(results) == 4

        assert sorted(results) == ripgrep_snapshot

    def test_include_types(self, ripgrep_find: RipGrepFind, ripgrep_snapshot: SnapshotAssertion):
        _ = ripgrep_find.include_types(ripgrep_types=["py"])
        results = run_find(ripgrep_find)
        assert len(results) == 1
        assert results[0] == Path("code_with_hello_world.py")

        assert sorted(results) == ripgrep_snapshot

    def test_exclude_types(self, ripgrep_find: RipGrepFind, ripgrep_snapshot: SnapshotAssertion):
        _ = ripgrep_find.exclude_types(ripgrep_types=["py"])
        results = run_find(ripgrep_find)
        assert len(results) == 4

        assert sorted(results) == ripgrep_snapshot

    def test_max_depth(self, ripgrep_find: RipGrepFind, ripgrep_snapshot: SnapshotAssertion):
        _ = ripgrep_find.max_depth(1)
        results = run_find(ripgrep_find)
        assert len(results) == 3

        assert sorted(results) == ripgrep_snapshot

    def test_sort(self, ripgrep_find: RipGrepFind, ripgrep_snapshot: SnapshotAssertion):
        _ = ripgrep_find.sort("path")
        results = run_find(ripgrep_find)
        assert len(results) == 5
        assert results[0] == Path("code_with_hello_world.py")

        assert sorted(results) == ripgrep_snapshot
