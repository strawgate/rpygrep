from collections.abc import Sequence
from typing import Any, overload

from pydantic import BaseModel


def handle_exclude_keys(dictionary: dict[str, Any], exclude_keys: list[str] | None = None) -> dict[str, Any]:
    if exclude_keys is None:
        return dictionary
    return {key: value for key, value in dictionary.items() if key not in exclude_keys}  # pyright: ignore[reportAny]


@overload
def dump_for_snapshot(
    basemodel: None,
    /,
    exclude_keys: list[str] | None = None,
    exclude_none: bool = True,
    **dump_kwargs: Any,  # pyright: ignore[reportAny]
) -> None:
    return None


@overload
def dump_for_snapshot(
    basemodel: BaseModel,
    /,
    exclude_keys: list[str] | None = None,
    exclude_none: bool = True,
    **dump_kwargs: Any,  # pyright: ignore[reportAny]
) -> dict[str, Any]:
    return handle_exclude_keys(basemodel.model_dump(exclude_none=exclude_none, **dump_kwargs), exclude_keys)  # pyright: ignore[reportAny]


def dump_for_snapshot(
    basemodel: None | BaseModel,
    /,
    exclude_keys: list[str] | None = None,
    exclude_none: bool = True,
    **dump_kwargs: Any,  # pyright: ignore[reportAny]
) -> dict[str, Any] | None:
    if basemodel is None:
        return None

    return handle_exclude_keys(basemodel.model_dump(exclude_none=exclude_none, **dump_kwargs), exclude_keys)  # pyright: ignore[reportAny]


def dump_list_for_snapshot(
    basemodel: None | Sequence[BaseModel],
    /,
    exclude_keys: list[str] | None = None,
    exclude_none: bool = True,
    **dump_kwargs: Any,  # pyright: ignore[reportAny]
) -> list[dict[str, Any]] | None:
    if basemodel is None:
        return []

    return [dump_for_snapshot(item, exclude_keys, exclude_none, **dump_kwargs) for item in basemodel]
