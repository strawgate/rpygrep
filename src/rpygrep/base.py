import subprocess
from abc import ABC, abstractmethod
from asyncio.subprocess import Process, create_subprocess_exec
from collections.abc import AsyncIterator, Iterator, Sequence
from pathlib import Path
from typing import Any, ClassVar, Literal, Self, TypeVar, override

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from rpygrep.types import RIPGREP_TYPE_LIST, RipGrepBegin, RipGrepContext, RipGrepEnd, RipGrepMatch, RipGrepRow, RipGrepSearchResult

T = TypeVar("T", bound=BaseModel | list[str] | str)


class BaseRipGrep(BaseModel, ABC):  # pyright: ignore[reportUnsafeMultipleInheritance]
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True, use_attribute_docstrings=True)

    working_directory: Path = Field(default_factory=Path.cwd)
    """The working directory for ripgrep."""

    command: str = Field(default="rg")
    """The ripgrep binary to invoke."""

    singular_options: set[str] = Field(default_factory=set)
    """Options which can only be added once."""

    multiple_options: list[str] = Field(default_factory=list)
    """Options which can be added multiple times."""

    targets: list[Path] = Field(default_factory=list)
    """The directories and files to search."""

    def case_sensitive(self, case_sensitive: bool) -> Self:
        """Ignore case when searching."""
        if not case_sensitive:
            self.multiple_options.append("--ignore-case")
        return self

    def sort(self, by: Literal["none", "path", "name", "size", "accessed", "created", "modified"], ascending: bool = True) -> Self:
        """Sort the results. Will force ripgrep to use a single thread."""
        if ascending:
            self.multiple_options.append(f"--sort={by}")
        else:
            self.multiple_options.append(f"--sortr={by}")
        return self

    def add_safe_defaults(self) -> Self:
        """Add safe defaults to the ripgrep command."""
        _ = self.max_depth(15)
        return self

    def add_directories(self, directories: list[Path]) -> Self:
        """Add directories to the ripgrep command."""
        self.targets.extend(directories)
        return self

    def add_directory(self, directory: Path) -> Self:
        """Add a directory to the ripgrep command."""
        self.targets.append(directory)
        return self

    def include_glob(self, glob: str) -> Self:
        """Include files which match the given glob pattern."""
        self.multiple_options.append(f"--glob={glob}")
        return self

    def include_globs(self, globs: list[str]) -> Self:
        """Include files which match the given glob patterns."""
        [self.include_glob(glob) for glob in globs]
        return self

    def exclude_glob(self, glob: str) -> Self:
        """Exclude files which match the given glob pattern."""
        self.multiple_options.append(f"--glob=!{glob}")
        return self

    def exclude_globs(self, globs: list[str]) -> Self:
        """Exclude files which match the given glob patterns."""
        [self.exclude_glob(glob) for glob in globs]
        return self

    def include_type(self, ripgrep_type: RIPGREP_TYPE_LIST) -> Self:
        """Only search files of the given type."""
        self.multiple_options.append(f"--type={ripgrep_type}")
        return self

    def include_types(self, ripgrep_types: Sequence[RIPGREP_TYPE_LIST]) -> Self:
        """Only search files of the given types."""
        [self.include_type(ripgrep_type) for ripgrep_type in ripgrep_types]
        return self

    def exclude_type(self, ripgrep_type: RIPGREP_TYPE_LIST) -> Self:
        """Exclude files of the given type."""
        self.multiple_options.append(f"--type-not={ripgrep_type}")
        return self

    def exclude_types(self, ripgrep_types: Sequence[RIPGREP_TYPE_LIST]) -> Self:
        """Exclude files of the given types."""
        [self.exclude_type(ripgrep_type) for ripgrep_type in ripgrep_types]
        return self

    def one_file_system(self) -> Self:
        """Only search the file system tree rooted at the path arguments."""
        self.singular_options.add("--one-file-system")
        return self

    def max_depth(self, depth: int) -> Self:
        """Only search this many levels of subdirectories."""
        self.multiple_options.append(f"--max-depth={depth}")
        return self

    def set_working_directory(self, path: Path) -> Self:
        """Set the working directory for the ripgrep command."""
        self.working_directory = path
        return self

    def _targets_str(self) -> list[str]:
        """Get the targets as a list of strings."""
        return [str(target) for target in self.targets]

    @abstractmethod
    def compile(self) -> list[str]: ...

    def compile_str(self) -> str:
        """Compile the ripgrep command."""
        return " ".join(self.compile())

    @abstractmethod
    def run(self) -> Iterator[Any]: ...

    @abstractmethod
    async def arun(self) -> AsyncIterator[Any]:
        msg = "Async support for RipGrepFind is not implemented yet"
        raise NotImplementedError(msg)

        yield  # pyright: ignore[reportUnreachable]


class RipGrepFind(BaseRipGrep):
    """Use RipGrep to find files that match the given pattern."""

    @override
    def compile(self) -> list[str]:
        """Compile the ripgrep command."""
        return [
            self.command,
            *self.singular_options,
            *self.multiple_options,
            *self._targets_str(),
        ]

    @override
    def run(self) -> Iterator[Path]:
        """Run the ripgrep command and return the result."""

        self.singular_options.add("--files")

        cli: list[str] = self.compile()

        with subprocess.Popen(cli, cwd=self.working_directory, stdout=subprocess.PIPE, text=True, universal_newlines=True) as process:  # noqa: S603
            if process.stdout is None:
                msg = "No stdout from ripgrep process"
                raise RuntimeError(msg)

            for line in process.stdout.readlines():
                yield Path(line.rstrip())

    @override
    async def arun(self) -> AsyncIterator[Path]:
        """Run the ripgrep command and return the result."""

        self.singular_options.add("--files")

        cli: list[str] = self.compile()

        process: Process = await create_subprocess_exec(cli[0], *cli[1:], cwd=self.working_directory, stdout=subprocess.PIPE)

        if process.stdout is None:
            msg = "No stdout from ripgrep process"
            raise RuntimeError(msg)

        async for line in process.stdout:
            yield Path(line.decode("utf-8").rstrip())


class RipGrepSearch(BaseRipGrep):
    """Use RipGrep to search for the given pattern in the given files."""

    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True, use_attribute_docstrings=True)

    @override
    def compile(self) -> list[str]:
        """Compile the ripgrep command."""

        return [
            self.command,
            *self.singular_options,
            *self.multiple_options,
            *self._targets_str(),
        ]

    @override
    def add_safe_defaults(self) -> Self:
        """Add safe defaults to the ripgrep command for searching files.

        Sets the maximum file size to 50 MB, the maximum count to 100, and sorts the results by path.
        """
        _ = super().add_safe_defaults()
        _ = self.max_file_size(50 * 1024 * 1024)  # 50 MB
        _ = self.max_count(100)  # 100 matches per file
        return self

    def add_extra_options(self, options: list[str]) -> Self:
        """Add extra options to the ripgrep command."""
        self.multiple_options.extend(options)
        return self

    def add_patterns(self, patterns: list[str]) -> Self:
        """Add patterns to the ripgrep command."""
        self.multiple_options.extend(f"--regexp={pattern}" for pattern in patterns)
        return self

    def add_pattern(self, pattern: str) -> Self:
        """Add a pattern to the ripgrep command."""
        self.multiple_options.append(f"--regexp={pattern}")
        return self

    def add_files(self, files: list[Path]) -> Self:
        """Add files to the ripgrep command."""
        self.targets.extend(files)
        return self

    def add_file(self, file: Path) -> Self:
        """Add a file to the ripgrep command."""
        self.targets.append(file)
        return self

    def before_context(self, context: int) -> Self:
        """Set the number of lines of context to include before the match."""
        self.multiple_options.append(f"--before-context={context}")
        return self

    def after_context(self, context: int) -> Self:
        """Set the number of lines of context to include after the match."""
        self.multiple_options.append(f"--after-context={context}")
        return self

    def auto_hybrid_regex(self) -> Self:
        """Enable hybrid regex matching. This allows for the use of regex patterns in the search terms."""
        self.singular_options.add("--auto-hybrid-regex")
        return self

    def max_count(self, count: int) -> Self:
        """Set the maximum number of matches to return."""
        self.multiple_options.append(f"--max-count={count}")
        return self

    def max_file_size(self, size: int) -> Self:
        """Set the maximum file size to search."""
        self.multiple_options.append(f"--max-filesize={size}")
        return self

    def as_json(self) -> Self:
        """Enable JSON output."""
        self.singular_options.add("--json")
        return self

    def run_direct(self) -> Iterator[str]:
        """Run the ripgrep command and return the result."""
        cli: list[str] = self.compile()

        # We need to iterate over the lines as they are written to stdout:
        with subprocess.Popen(cli, cwd=self.working_directory, stdout=subprocess.PIPE, text=True, errors="ignore") as process:  # noqa: S603
            if process.stdout is None:
                msg = "No stdout from ripgrep process"
                raise RuntimeError(msg)

            while line := process.stdout.readline():
                stripped_line = line.rstrip()

                yield stripped_line

    async def arun_direct(self) -> AsyncIterator[str]:
        """Run the ripgrep command and return the result."""
        cli: list[str] = self.compile()

        # We need to iterate over the lines as they are written to stdout:
        process: Process = await create_subprocess_exec(
            cli[0],
            *cli[1:],
            cwd=self.working_directory,
            stdout=subprocess.PIPE,
            limit=128 * 1024 * 1024,  # 128kb
        )

        if process.stdout is None:
            msg = "No stdout from ripgrep process"
            raise RuntimeError(msg)

        while line_bytes := await process.stdout.readline():
            line = line_bytes.decode("utf-8").rstrip()

            yield line

    @override
    def run(self, exclude_submatches: bool = False) -> Iterator["RipGrepSearchResult"]:
        """Run the ripgrep command and return the result."""

        _ = self.as_json()

        result_processor = ResultProcessor()

        for row in self.run_direct():
            if result := result_processor.process_line(row):
                yield result

    @override
    async def arun(self, exclude_submatches: bool = False) -> AsyncIterator["RipGrepSearchResult"]:
        """Run the ripgrep command and return the result."""

        _ = self.as_json()

        result_processor = ResultProcessor()

        async for row in self.arun_direct():
            if result := result_processor.process_line(row):
                yield result


class ResultProcessor:
    begin: "RipGrepBegin | None"
    matches: list["RipGrepMatch"]
    context: list["RipGrepContext"]
    end: "RipGrepEnd | None"

    timers: dict[str, float] = Field(default_factory=dict)

    def __init__(self) -> None:
        self.begin = None
        self.matches = []
        self.context = []
        self.end = None

        self.adapter: TypeAdapter[RipGrepRow] = TypeAdapter(RipGrepRow)

    def process_line(self, line: str) -> "RipGrepSearchResult | None":
        """Process a line of stdout from ripgrep."""

        model = self.adapter.validate_json(line)

        if isinstance(model, RipGrepMatch):
            self.matches.append(model)
        elif isinstance(model, RipGrepContext):
            self.context.append(model)
        elif isinstance(model, RipGrepBegin):
            self.begin = model
        elif isinstance(model, RipGrepEnd):
            self.end = model

        if self.begin and self.end:
            path = Path(self.begin.data.path.text)
            result = RipGrepSearchResult(path=path, begin=self.begin, matches=self.matches, context=self.context, end=self.end)

            self.begin = None
            self.matches = []
            self.context = []
            self.end = None

            return result

        return None
