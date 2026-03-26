from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.default_flow_style = None


def load_project(project_path: str | Path) -> dict[str, Any]:
    path = Path(project_path).expanduser()
    with path.open("r", encoding="utf-8") as stream:
        data = yaml.load(stream)
    return data or {}


def save_project(project_path: str | Path, data: dict[str, Any]) -> None:
    path = Path(project_path).expanduser()
    with path.open("w", encoding="utf-8") as stream:
        yaml.dump(data, stream)


def list_project_files(projects_dir: str | Path) -> list[str]:
    path = Path(projects_dir).expanduser()
    if not path.is_dir():
        return []
    return sorted(
        project_file.name
        for project_file in path.iterdir()
        if project_file.suffix == ".yaml"
    )
