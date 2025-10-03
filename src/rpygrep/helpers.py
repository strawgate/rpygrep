from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

from rpygrep.types import RipGrepContext, RipGrepMatch, RipGrepSearchResult


@dataclass(frozen=True)
class MatchedLine:
    """A match in a file entry."""

    before: dict[int, str] = field(default_factory=dict)
    """The lines of text before the line"""

    match: dict[int, str] = field(default_factory=dict)
    """The line of text that matches the pattern"""

    after: dict[int, str] = field(default_factory=dict)
    """The lines of text after the line"""


@dataclass(frozen=True)
class MatchedFile:
    """A file with matches."""

    path: Path
    """The path to the file that matched the pattern."""

    matched_lines: list[MatchedLine]

    @classmethod
    def from_search_results(
        cls, search_results: list[RipGrepSearchResult], before_context: int, after_context: int, include_empty_lines: bool = False
    ) -> list[Self]:
        return [
            cls.from_search_result(search_result, before_context, after_context, include_empty_lines) for search_result in search_results
        ]

    @classmethod
    def from_search_result(  # noqa: PLR0912
        cls, search_result: RipGrepSearchResult, before_context: int, after_context: int, include_empty_lines: bool = False
    ) -> Self:
        """Attach context to the matches in the search result and produce a list of FileEntryMatches."""

        line_context_by_line_number: dict[int, RipGrepContext] = {context.data.line_number: context for context in search_result.context}

        matches_by_line_number: dict[int, RipGrepMatch] = {match.data.line_number: match for match in search_result.matches}

        matched_lines: list[MatchedLine] = []

        for line_match in search_result.matches:
            if not line_match.data.lines.text:
                continue

            before_context_lines: dict[int, str] = {}
            after_context_lines: dict[int, str] = {}

            # Find the before context lines
            for line_number in range(line_match.data.line_number - before_context, line_match.data.line_number):
                if line_number in matches_by_line_number:
                    # Do not steal context from the next match
                    break

                if line := line_context_by_line_number.pop(line_number, None):  # noqa: SIM102
                    if text := line.data.lines.text:
                        if stripped_line := text.rstrip():
                            before_context_lines[line_number] = stripped_line
                        elif include_empty_lines:
                            before_context_lines[line_number] = ""

            # Find the after context lines
            for line_number in range(line_match.data.line_number + 1, line_match.data.line_number + after_context + 1):
                if line_number in matches_by_line_number:
                    # Do not steal context from the next match
                    break

                if line := line_context_by_line_number.pop(line_number, None):  # noqa: SIM102
                    if text := line.data.lines.text:
                        if stripped_line := text.rstrip():
                            after_context_lines[line_number] = stripped_line
                        elif include_empty_lines:
                            after_context_lines[line_number] = ""

            matched_lines.append(
                MatchedLine(
                    before=before_context_lines,
                    match={line_match.data.line_number: line_match.data.lines.text.rstrip()},
                    after=after_context_lines,
                )
            )

        return cls(path=Path(search_result.path), matched_lines=matched_lines)
