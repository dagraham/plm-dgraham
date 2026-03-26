# AGENTS.md

## Project overview
`plm-dgraham` is a Python terminal application for managing player lineup scheduling. It is primarily an interactive CLI app rather than a stateless command-only tool.

## Repository layout
- `plm/__main__.py` — main entry point for the installed `plm` command
- `plm/plm.py` — main interactive application logic
- `plm/__version__.py` — package version
- `start_plm.py` — convenience launcher for local use
- `pyproject.toml` — package metadata and dependencies
- `setup.py` — legacy packaging file; prefer `pyproject.toml`

## Entry points
Preferred ways to run the app:
- Installed command: `plm`
- Module entry point: `python3 -m plm`
- Local launcher: `python3 start_plm.py`

## Environment and dependencies
Use an isolated virtual environment for development.

Typical setup:
1. Create a venv: `python3 -m venv .venv`
2. Activate it: `. .venv/bin/activate`
3. Upgrade pip: `python3 -m pip install --upgrade pip`
4. Install the project: `python3 -m pip install -e .`

Notes:
- Use `python3 -m pip ...` instead of bare `pip`.
- Python package install names may use hyphens while import names use underscores.
- Example: install `prompt-toolkit`, import `prompt_toolkit`.

If using `uv`, preferred workflow is:
- `uv venv`
- `uv sync`
- `uv run plm`

## Validation
For quick validation after edits, use small checks first:
- `python3 -m compileall plm start_plm.py`
- then run the app locally if needed

Prefer minimal, behavior-preserving changes unless the task explicitly requests refactoring.

## Editing guidance
- Treat `plm/plm.py` as legacy but active code.
- Preserve the current interactive `prompt_toolkit` workflow unless asked to redesign it.
- Avoid introducing `click` or changing the UI model unless explicitly requested.
- Separate business logic from terminal interaction when making larger improvements.

## Documentation notes
The README may contain older installation or startup examples. When changing docs, keep them aligned with current behavior in `plm/__main__.py` and packaging in `pyproject.toml`.

## Files and directories to avoid editing unless necessary
These are typically generated artifacts or local/editor state:
- `build/`
- `dist/`
- `plm_dgraham.egg-info/`
- `.mypy_cache/`
- `.vscode/`

## Packaging and release notes
- Prefer modern packaging via `pyproject.toml`.
- Do not add new packaging metadata only to `setup.py`.
- Keep the console script entry point as `plm = plm.__main__:main` unless there is a clear reason to change it.

## Scope expectations for agents
Good tasks:
- small bug fixes
- README updates
- packaging modernization
- light refactoring with no behavior change
- adding tests around isolated logic

Be cautious with:
- large rewrites of `plm/plm.py`
- changing home-directory behavior
- changing project file format
- changing the interactive command flow