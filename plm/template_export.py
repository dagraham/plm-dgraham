from __future__ import annotations

import re
from typing import Any

from ruamel.yaml import YAML

_EXPORT_FIELDS = [
    "PLAYER_TAG",
    "CAN",
    "REPEAT",
    "DAY",
    "NUM_COURTS",
    "NUM_PLAYERS",
    "ASSIGN_TBD",
    "ALLOW_LAST",
]

_QUARTER_YEAR_PATTERNS = [
    re.compile(r"\b([1-4])(st|nd|rd|th)\s+Quarter\s+\d{4}\b", re.IGNORECASE),
    re.compile(r"\bQ([1-4])\s+\d{4}\b", re.IGNORECASE),
    re.compile(r"\b\d{4}\s+Q([1-4])\b", re.IGNORECASE),
]


def sanitize_template_name(name: str) -> str:
    """
    Convert arbitrary text into a template-friendly key.

    Examples:
        "Tuesday Doubles Custom" -> "tuesday_doubles_custom"
        "2025-2Q-TU" -> "2025_2q_tu"
    """
    text = str(name).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def suggest_template_name(project_name: str) -> str:
    """
    Suggest a template name based on a project filename or display name.
    """
    base = str(project_name).strip()
    if base.endswith(".yaml"):
        base = base[:-5]
    return sanitize_template_name(base)


def suggest_template_description(project_name: str) -> str:
    """
    Suggest a human-readable description for a template exported from a project.
    """
    base = str(project_name).strip()
    if base.endswith(".yaml"):
        base = base[:-5]
    return f"Template based on {base}"


def suggest_title_template(title: str) -> str:
    """
    Suggest a reusable TITLE_TEMPLATE from a concrete project title.

    This performs a conservative replacement of common quarter/year phrases.
    If no known pattern is found, the original title is returned unchanged.
    """
    text = str(title).strip()
    if not text:
        return text

    for pattern in _QUARTER_YEAR_PATTERNS:
        if pattern.search(text):
            return pattern.sub("{period} {year}", text)

    return text


def exportable_template_data(
    project_data: dict[str, Any],
    *,
    description: str = "",
    title_template: str | None = None,
) -> dict[str, Any]:
    """
    Extract reusable template fields from a project mapping.

    Args:
        project_data:
            Parsed project YAML data.
        description:
            Optional human-readable description to include.
        title_template:
            Optional title template override. If omitted, a suggestion is
            derived from the project's TITLE.

    Returns:
        A mapping suitable for use as the value of a template entry.
    """
    title = str(project_data.get("TITLE", "")).strip()
    data: dict[str, Any] = {}

    if description:
        data["description"] = description

    data["TITLE_TEMPLATE"] = (
        title_template if title_template is not None else suggest_title_template(title)
    )

    for field in _EXPORT_FIELDS:
        if field in project_data:
            data[field] = project_data[field]

    return data


def export_template_mapping(
    template_name: str,
    project_data: dict[str, Any],
    *,
    description: str = "",
    title_template: str | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Build a one-entry template mapping ready for YAML serialization.
    """
    key = sanitize_template_name(template_name)
    if not key:
        raise ValueError("template_name must not be empty")

    return {
        key: exportable_template_data(
            project_data,
            description=description,
            title_template=title_template,
        )
    }


def dump_template_snippet(
    template_name: str,
    project_data: dict[str, Any],
    *,
    description: str = "",
    title_template: str | None = None,
) -> str:
    """
    Render a template snippet as YAML text.
    """
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.indent(mapping=2, sequence=4, offset=2)

    import io

    buffer = io.StringIO()
    yaml.dump(
        export_template_mapping(
            template_name,
            project_data,
            description=description,
            title_template=title_template,
        ),
        buffer,
    )
    return buffer.getvalue()
