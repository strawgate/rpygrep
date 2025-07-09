from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field

RIPGREP_TYPE_LIST = Literal[
    "ada",
    "agda",
    "aidl",
    "alire",
    "amake",
    "asciidoc",
    "asm",
    "asp",
    "ats",
    "avro",
    "awk",
    "bat",
    "batch",
    "bazel",
    "bitbake",
    "brotli",
    "buildstream",
    "bzip2",
    "c",
    "cabal",
    "candid",
    "carp",
    "cbor",
    "ceylon",
    "clojure",
    "cmake",
    "cmd",
    "cml",
    "coffeescript",
    "config",
    "coq",
    "cpp",
    "creole",
    "crystal",
    "cs",
    "csharp",
    "cshtml",
    "csproj",
    "css",
    "csv",
    "cuda",
    "cython",
    "d",
    "dart",
    "devicetree",
    "dhall",
    "diff",
    "dita",
    "docker",
    "dockercompose",
    "dts",
    "dvc",
    "ebuild",
    "edn",
    "elisp",
    "elixir",
    "elm",
    "erb",
    "erlang",
    "fennel",
    "fidl",
    "fish",
    "flatbuffers",
    "fortran",
    "fsharp",
    "fut",
    "gap",
    "gn",
    "go",
    "gprbuild",
    "gradle",
    "graphql",
    "groovy",
    "gzip",
    "h",
    "haml",
    "hare",
    "haskell",
    "hbs",
    "hs",
    "html",
    "hy",
    "idris",
    "janet",
    "java",
    "jinja",
    "jl",
    "js",
    "json",
    "jsonl",
    "julia",
    "jupyter",
    "k",
    "kotlin",
    "lean",
    "less",
    "license",
    "lilypond",
    "lisp",
    "lock",
    "log",
    "lua",
    "lz4",
    "lzma",
    "m4",
    "make",
    "mako",
    "man",
    "markdown",
    "matlab",
    "md",
    "meson",
    "minified",
    "mint",
    "mk",
    "ml",
    "motoko",
    "msbuild",
    "nim",
    "nix",
    "objc",
    "objcpp",
    "ocaml",
    "org",
    "pants",
    "pascal",
    "pdf",
    "perl",
    "php",
    "po",
    "pod",
    "postscript",
    "prolog",
    "protobuf",
    "ps",
    "puppet",
    "purs",
    "py",
    "python",
    "qmake",
    "qml",
    "r",
    "racket",
    "raku",
    "rdoc",
    "readme",
    "reasonml",
    "red",
    "rescript",
    "robot",
    "rst",
    "ruby",
    "rust",
    "sass",
    "scala",
    "sh",
    "slim",
    "smarty",
    "sml",
    "solidity",
    "soy",
    "spark",
    "spec",
    "sql",
    "stylus",
    "sv",
    "svelte",
    "svg",
    "swift",
    "swig",
    "systemd",
    "taskpaper",
    "tcl",
    "tex",
    "texinfo",
    "textile",
    "tf",
    "thrift",
    "toml",
    "ts",
    "twig",
    "txt",
    "typescript",
    "typoscript",
    "usd",
    "v",
    "vala",
    "vb",
    "vcl",
    "verilog",
    "vhdl",
    "vim",
    "vimscript",
    "vue",
    "webidl",
    "wgsl",
    "wiki",
    "xml",
    "xz",
    "yacc",
    "yaml",
    "yang",
    "z",
    "zig",
    "zsh",
    "zstd",
]


@dataclass(frozen=True)
class RipGrepDataPath:
    text: str
    """The path to the file that matched the pattern."""


@dataclass(frozen=True)
class RipGrepBeginData:
    path: RipGrepDataPath
    """The path to the file that matched the pattern."""


@dataclass(frozen=True)
class RipGrepBegin:
    type: Literal["begin"]
    """The type of the event."""

    data: RipGrepBeginData
    """The data for the begin event."""


@dataclass(frozen=True)
class RipGrepDataSubmatchMatch:
    text: str
    """The text of the match."""


@dataclass(frozen=True)
class RipGrepDataSubmatch:
    match: RipGrepDataSubmatchMatch
    """The match."""

    start: int
    """The start index of the match."""

    end: int
    """The end index of the match."""


@dataclass(frozen=True)
class RipGrepDataLines:
    text: str | None = None
    """The lines of text that matched the pattern."""

    bytes: str | None = None
    """The bytes of the lines that matched the pattern."""


@dataclass(frozen=True)
class RipGrepMatchData:
    path: RipGrepDataPath
    """The path to the file that matched the pattern."""

    lines: RipGrepDataLines
    """The lines of text that matched the pattern."""

    line_number: int
    """The line number of the line that matched the pattern."""

    absolute_offset: int
    """The absolute offset of the line that matched the pattern."""

    submatches: list[RipGrepDataSubmatch]
    """The submatches of the line that matched the pattern."""


@dataclass(frozen=True)
class RipGrepMatch:
    type: Literal["match"]
    """The type of the event."""

    data: RipGrepMatchData
    """The data for the match event."""


@dataclass(frozen=True)
class RipGrepContextData:
    path: RipGrepDataPath
    """The path to the file that matched the pattern."""

    lines: RipGrepDataLines
    """The lines of text that matched the pattern."""

    line_number: int
    """The line number of the line that matched the pattern."""

    absolute_offset: int
    """The absolute offset of the line that matched the pattern."""

    submatches: list[RipGrepDataSubmatch]
    """The submatches of the line that matched the pattern."""


@dataclass(frozen=True)
class RipGrepContext:
    type: Literal["context"]
    """The type of the event."""

    data: RipGrepContextData
    """The data for the context event."""


@dataclass(frozen=True)
class RipGrepStatsElapsed:
    secs: int
    """The number of seconds."""

    nanos: int
    """The number of nanoseconds."""

    human: str
    """The human readable time."""


@dataclass(frozen=True)
class RipGrepStats:
    elapsed: RipGrepStatsElapsed
    """The elapsed time of the search."""

    searches: int
    """The number of searches."""

    searches_with_match: int
    """The number of searches with a match."""

    bytes_searched: int
    """The number of bytes searched."""

    bytes_printed: int
    """The number of bytes printed."""

    matched_lines: int
    """The number of matched lines."""

    matches: int
    """The number of matches."""


@dataclass(frozen=True)
class RipGrepEndData:
    path: RipGrepDataPath
    """The path to the file that matched the pattern."""

    binary_offset: int | None
    """The binary offset of the line that matched the pattern."""

    stats: RipGrepStats
    """The stats of the search."""


@dataclass(frozen=True)
class RipGrepEnd:
    type: Literal["end"]
    """The type of the event."""

    data: RipGrepEndData
    """The data for the end event."""


@dataclass(frozen=True)
class RipGrepSummaryElapsedTotal:
    human: str
    """The human readable time."""

    nanos: int
    """The number of nanoseconds."""

    secs: int
    """The number of seconds."""


@dataclass(frozen=True)
class RipGrepSummaryData:
    elapsed_total: RipGrepSummaryElapsedTotal
    """The elapsed time of the search."""

    stats: RipGrepStats
    """The stats of the search."""


@dataclass(frozen=True)
class RipGrepSummary:
    type: Literal["summary"]
    """The type of the event."""

    data: RipGrepSummaryData
    """The data for the summary event."""


RipGrepRow = Annotated[RipGrepMatch | RipGrepContext | RipGrepBegin | RipGrepEnd | RipGrepSummary, Field(discriminator="type")]


@dataclass(frozen=True)
class RipGrepSearchResult:
    path: Path
    """The path to the file that matched the pattern."""

    begin: RipGrepBegin
    """The begin event."""

    matches: list[RipGrepMatch]
    """The matches of the search."""

    context: list[RipGrepContext]
    """The context for the matches"""

    end: RipGrepEnd
    """The end event."""
