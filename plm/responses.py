from __future__ import annotations

from typing import Iterable


def normalize_response_value(value) -> str | list[str]:
    """
    Normalize a stored response value into a prompt-friendly string.

    Lists are converted to comma-separated strings. Scalars are returned
    unchanged after string conversion.
    """
    if isinstance(value, list):
        return ", ".join(value)
    return str(value)


def parse_response_input(
    response,
    valid_dates: Iterable[str],
    allow_last: bool = False,
) -> tuple[str | list[str] | None, list[str]]:
    """
    Parse a player's entered response.

    Args:
        response:
            User-entered response. Usually a string, but may already be a list.
        valid_dates:
            Iterable of allowed project dates in `m/d` format.
        allow_last:
            Whether `last` and `~` suffixed dates are allowed.

    Returns:
        A tuple of `(parsed_value, issues)` where:
        - `parsed_value` is one of:
          - `"nr"`, `"none"`, `"all"`, `"sub"`, `"last"`
          - a list of valid date tokens
          - `None` if nothing valid was parsed
        - `issues` is a list of invalid tokens
    """
    dates = set(valid_dates)

    if isinstance(response, list):
        tokens = [str(x).strip() for x in response if str(x).strip()]
        parsed_dates, issues = _parse_date_tokens(tokens, dates, allow_last)
        return (parsed_dates if parsed_dates else None, issues)

    if response is None:
        return None, []

    text = str(response).strip().lower()
    if not text:
        return None, []

    if text in {"na", "nr"}:
        return "nr", []
    if text == "none":
        return "none", []
    if text == "all":
        return "all", []
    if text == "sub":
        return "sub", []
    if allow_last and text == "last":
        return "last", []

    tokens = [part.strip() for part in text.split(",") if part.strip()]
    parsed_dates, issues = _parse_date_tokens(tokens, dates, allow_last)
    return (parsed_dates if parsed_dates else None, issues)


def _parse_date_tokens(
    tokens: list[str],
    valid_dates: set[str],
    allow_last: bool,
) -> tuple[list[str], list[str]]:
    parsed: list[str] = []
    issues: list[str] = []

    for token in tokens:
        if token.endswith("*"):
            base = token[:-1]
            if base in valid_dates:
                parsed.append(token)
            else:
                issues.append(token)
        elif allow_last and token.endswith("~"):
            base = token[:-1]
            if base in valid_dates:
                parsed.append(token)
            else:
                issues.append(token)
        elif token in valid_dates:
            parsed.append(token)
        else:
            issues.append(token)

    return parsed, issues
