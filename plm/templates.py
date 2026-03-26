from __future__ import annotations

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

yaml = YAML()


def templates_path() -> Path:
    """
    Return the path to the bundled project templates file.
    """
    return Path(__file__).with_name("templates.yaml")


def load_templates(path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    """
    Load project templates from YAML.

    Args:
        path:
            Optional path to a templates YAML file. If omitted, the bundled
            `templates.yaml` next to this module is used.

    Returns:
        A mapping of template name to template configuration.
    """
    template_file = Path(path) if path is not None else templates_path()
    with template_file.open("r", encoding="utf-8") as stream:
        data = yaml.load(stream) or {}

    if not isinstance(data, dict):
        return {}

    cleaned: dict[str, dict[str, Any]] = {}
    for name, values in data.items():
        if isinstance(values, dict):
            cleaned[str(name)] = dict(values)

    return cleaned


def list_template_names(path: str | Path | None = None) -> list[str]:
    """
    Return sorted available template names.
    """
    return sorted(load_templates(path).keys())


def get_template(name: str, path: str | Path | None = None) -> dict[str, Any] | None:
    """
    Return a copy of a single template by name.

    Args:
        name:
            Template name to fetch.
        path:
            Optional path to a templates YAML file.

    Returns:
        A shallow copy of the template mapping if found, otherwise `None`.
    """
    templates = load_templates(path)
    template = templates.get(name)
    if template is None:
        return None
    return dict(template)


def template_description(name: str, path: str | Path | None = None) -> str | None:
    """
    Return the optional human-readable description for a template.
    """
    template = get_template(name, path)
    if template is None:
        return None
    description = template.get("description")
    return str(description) if description is not None else None


def template_defaults(
    name: str, path: str | Path | None = None
) -> dict[str, Any] | None:
    """
    Return template values intended as project defaults.

    This excludes metadata fields such as `description`.
    """
    template = get_template(name, path)
    if template is None:
        return None
    return {key: value for key, value in template.items() if key != "description"}


def has_template(name: str, path: str | Path | None = None) -> bool:
    """
    Return whether a named template exists.
    """
    return get_template(name, path) is not None
