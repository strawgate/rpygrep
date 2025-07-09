# rpygrep: A Pythonic ripgrep Wrapper

`rpygrep` is a Python library that provides a convenient and type-safe interface for interacting with the `ripgrep` command-line utility. It allows you to programmatically construct `ripgrep` commands for finding files and searching content, and then parse the structured JSON output into Python objects.

Used in the [Filesystem Operations MCP Server](https://github.com/strawgate/py-mcp-collection/tree/main/filesystem-operations-mcp).

## Features

*   **Fluent API**: Build `ripgrep` commands using method chaining.
*   **File Finding & Content Searching**: Dedicated classes (`RipGrepFind` and `RipGrepSearch`) for different `ripgrep` modes.
*   **Synchronous & Asynchronous Execution**: Supports both `run()` and `arun()` methods for flexible integration.
*   **Structured Output**: Automatically parses `ripgrep`'s JSON output into rich Python data classes, making results easy to access and manipulate.
*   **Comprehensive Options**: Control over a wide range of `ripgrep` options, including case sensitivity, glob patterns, file types, context lines, maximum depth, and more.

## Example

```python
ripgrep = (
    self._ripgrep_find.include_types(included_types or [])
    .exclude_types(excluded_types or [])
    .include_globs(included_globs or [])
    .exclude_globs(excluded_globs or [])
    .max_depth(max_depth)
)

ripgrep.run()
```

```python
ripgrep = (
    self._ripgrep_search.include_types(included_types or [])
    .add_safe_defaults()
    .exclude_types(excluded_types or [])
    .include_globs(included_globs or [])
    .exclude_globs(excluded_globs or [])
    .before_context(before_context)
    .after_context(after_context)
    .add_patterns(patterns)
    .max_depth(max_depth)
    .max_count(matches_per_file)
    .case_sensitive(case_sensitive)
)

await ripgrep.arun()
```

## Prerequisites

`rpygrep` requires the `ripgrep` command-line tool to be installed on your system. You can find installation instructions for `ripgrep` [here](https://github.com/BurntSushi/ripgrep#installation).

## Installation

```bash
uv add rpygrep
```

## Usage Examples

The following examples demonstrate common use cases for `rpygrep`. For these examples to work, assume you have a directory structure similar to the one used in the tests:

```
.
├── code_with_hello_world.py
├── data.json
├── should_be_ignored.env
├── test_with_Hello_World.txt
├── .hidden
├── .git/
└── subdir/
    ├── nested.txt
    ├── script_with_hello.sh
    └── should_be_ignored.env
```

### Basic File Finding (`RipGrepFind`)

Find all Python files in the current directory and its subdirectories:

```python
from pathlib import Path
from rpygrep import RipGrepFind

# Assuming your script is run from the root of the example directory structure
current_dir = Path(".") 

rg_find = RipGrepFind(working_directory=current_dir)
rg_find.include_types(["py"])

print("Python files found:")
for path in rg_find.run():
    print(path)
# Expected output:
# code_with_hello_world.py
```

### Basic Content Search (`RipGrepSearch`)

Search for "hello" (case-insensitive) in all files and print matching lines:

```python
from pathlib import Path
from rpygrep import RipGrepSearch

current_dir = Path(".") 

rg_search = RipGrepSearch(working_directory=current_dir)
rg_search.add_pattern("hello")
rg_search.case_sensitive(False) # Make it case-insensitive

print("\nSearch results for 'hello' (case-insensitive):")
for result in rg_search.run():
    print(f"Found in {result.path}:")
    for match in result.matches:
        # .text might be None if lines.bytes is used, so check for it
        line_content = match.data.lines.text.strip() if match.data.lines.text else "Binary content"
        print(f"  Line {match.data.line_number}: {line_content}")
# Expected output (similar to):
# Found in test_with_Hello_World.txt:
#   Line 1: Hello, World!
# Found in code_with_hello_world.py:
#   Line 2:     print('hello, world!')
# Found in subdir/script_with_hello.sh:
#   Line 2: echo 'Hello'
```

### Asynchronous Usage

Both `RipGrepFind` and `RipGrepSearch` support asynchronous execution using their `arun()` methods.

```python
import asyncio
from pathlib import Path
from rpygrep import RipGrepSearch

async def main():
    current_dir = Path(".") 

    rg_search = RipGrepSearch(working_directory=current_dir)
    rg_search.add_pattern("World")

    print("\nAsynchronous search results for 'World':")
    async for result in rg_search.arun():
        print(f"Async found in {result.path}:")
        for match in result.matches:
            line_content = match.data.lines.text.strip() if match.data.lines.text else "Binary content"
            print(f"  Line {match.data.line_number}: {line_content}")

# To run this:
# asyncio.run(main())
```

### Excluding File Types

Exclude common binary and data file types from your search:

```python
from pathlib import Path
from rpygrep import RipGrepFind, DEFAULT_EXCLUDED_TYPES

current_dir = Path(".") 

rg_find = RipGrepFind(working_directory=current_dir)
rg_find.exclude_types(DEFAULT_EXCLUDED_TYPES) # Exclude common binary/data types

print("\nFiles found excluding default binary/data types:")
for path in rg_find.run():
    print(path)
```

### Limiting Search Depth

Search only the current directory, without recursing into subdirectories:

```python
from pathlib import Path
from rpygrep import RipGrepFind

current_dir = Path(".") 

rg_find = RipGrepFind(working_directory=current_dir)
rg_find.max_depth(1) # Only search current directory, no subdirectories

print("\nFiles found with max depth 1:")
for path in rg_find.run():
    print(path)
# Expected output (may vary based on actual files at depth 1):
# code_with_hello_world.py
# data.json
# should_be_ignored.env
# test_with_Hello_World.txt
# .hidden
```

### Adding Context Lines

Include lines before and after a match:

```python
from pathlib import Path
from rpygrep import RipGrepSearch

current_dir = Path(".") 

rg_search = RipGrepSearch(working_directory=current_dir)
rg_search.add_pattern("print")
rg_search.before_context(1) # 1 line before
rg_search.after_context(1)  # 1 line after

print("\nSearch results for 'print' with context:")
for result in rg_search.run():
    print(f"Found in {result.path}:")
    # Context lines are also in result.context
    for context_line in result.context:
        line_content = context_line.data.lines.text.strip() if context_line.data.lines.text else "Binary content"
        print(f"  Context Line {context_line.data.line_number}: {line_content}")
    for match in result.matches:
        line_content = match.data.lines.text.strip() if match.data.lines.text else "Binary content"
        print(f"  Match Line {match.data.line_number}: {line_content}")
```

## API Reference (Key Classes)

### `rpygrep.RipGrepFind`

Used for finding files based on various criteria.

*   `include_glob(glob: str)`: Includes files matching the given glob pattern.
*   `exclude_glob(glob: str)`: Excludes files matching the given glob pattern.
*   `include_type(ripgrep_type: RIPGREP_TYPE_LIST)`: Includes files of a specific `ripgrep` file type (e.g., "py", "ts", "md").
*   `exclude_type(ripgrep_type: RIPGREP_TYPE_LIST)`: Excludes files of a specific `ripgrep` file type.
*   `max_depth(depth: int)`: Limits the search to a specified number of subdirectory levels.
*   `sort(by: Literal["none", "path", "name", "size", "accessed", "created", "modified"], ascending: bool = True)`: Sorts the results.
*   `run() -> Iterator[Path]`: Executes the command synchronously and yields `Path` objects.
*   `arun() -> AsyncIterator[Path]`: Executes the command asynchronously and yields `Path` objects.

### `rpygrep.RipGrepSearch`

Used for searching content within files.

*   `add_pattern(pattern: str)`: Adds a regular expression pattern to search for. Can be called multiple times for multiple patterns.
*   `case_sensitive(case_sensitive: bool)`: Sets whether the search should be case-sensitive (`True`) or case-insensitive (`False`).
*   `before_context(context: int)`: Specifies the number of lines of context to include *before* a match.
*   `after_context(context: int)`: Specifies the number of lines of context to include *after* a match.
*   `max_count(count: int)`: Sets the maximum number of matches to return per file.
*   `max_file_size(size: int)`: Sets the maximum file size (in bytes) to search.
*   `as_json()`: Configures `ripgrep` to output results in JSON format (automatically called by `run`/`arun`).
*   `run() -> Iterator[RipGrepSearchResult]`: Executes the command synchronously and yields `RipGrepSearchResult` objects.
*   `arun() -> AsyncIterator[RipGrepSearchResult]`: Executes the command asynchronously and yields `RipGrepSearchResult` objects.

### `rpygrep.RipGrepSearchResult`

A dataclass representing a single search result for a file.

*   `path: Path`: The path to the file where matches were found.
*   `begin: RipGrepBegin`: Information about the beginning of the file's search results.
*   `matches: list[RipGrepMatch]`: A list of `RipGrepMatch` objects, each representing a found match.
*   `context: list[RipGrepContext]`: A list of `RipGrepContext` objects, representing context lines around matches.
*   `end: RipGrepEnd`: Information about the end of the file's search results, including statistics.

### Other Important Types

*   `RIPGREP_TYPE_LIST`: A `Literal` type listing all supported `ripgrep` file types.
*   `DEFAULT_EXCLUDED_TYPES`: A list of `RIPGREP_TYPE_LIST` values that are commonly excluded (e.g., binary files, large data files).
