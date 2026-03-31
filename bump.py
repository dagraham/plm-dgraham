#!/usr/bin/env python3

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from plm.__version__ import version

POSSIBLE_EXTENSIONS = ["a", "b", "rc"]
MAIN_BRANCH = "master"
DRY_RUN = "--dry-run" in sys.argv
SKIP_EXISTING = "--skip-existing" in sys.argv
NO_CLEAN = "--no-clean" in sys.argv


def script_root() -> Path:
    return Path(__file__).resolve().parent


def version_file_path() -> Path:
    return script_root() / "plm" / "__version__.py"


def print_error(cmd: str, output: str) -> None:
    print(f"Error running: {cmd}")
    if output:
        print(output.rstrip())


def exec_cmd(cmd: str, *, env=None, stream: bool = False) -> tuple[bool, str]:
    """
    Run a shell command.

    - stream=False: capture and return combined stdout/stderr
    - stream=True: inherit stdout/stderr so output appears live
    """
    if not cmd:
        return True, ""

    if DRY_RUN:
        print(f"[dry-run] {cmd}")
        return True, ""

    try:
        if stream:
            subprocess.run(cmd, shell=True, env=env, check=True)
            return True, ""
        out = subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            shell=True,
            universal_newlines=True,
            encoding="utf-8",
            env=env,
        )
        return True, out
    except subprocess.CalledProcessError as exc:
        output = (
            getattr(exc, "output", "")
            or f"Command failed with exit code {exc.returncode}"
        )
        print_error(cmd, output)
        last_line = output.strip().split("\n")[-1] if output.strip() else output
        return False, last_line


def check_output(cmd: str, *, env=None) -> tuple[bool, str]:
    return exec_cmd(cmd, env=env, stream=False)


def run(cmd: str, *, env=None) -> tuple[bool, str]:
    return exec_cmd(cmd, env=env, stream=False)


def read(cmd: str, *, env=None) -> tuple[bool, str]:
    """
    Run a read-only command even in dry-run mode.
    """
    if not cmd:
        return True, ""

    try:
        out = subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            shell=True,
            universal_newlines=True,
            encoding="utf-8",
            env=env,
        )
        return True, out
    except subprocess.CalledProcessError as exc:
        output = (
            getattr(exc, "output", "")
            or f"Command failed with exit code {exc.returncode}"
        )
        print_error(cmd, output)
        last_line = output.strip().split("\n")[-1] if output.strip() else output
        return False, last_line


def current_branch() -> str:
    ok, out = read("git rev-parse --abbrev-ref HEAD")
    if not ok:
        return ""
    return out.strip()


def ensure_expected_branch() -> None:
    branch = current_branch()
    if not branch:
        print("Unable to determine current git branch.")
        sys.exit(1)

    if branch != MAIN_BRANCH:
        print(f"Warning: current branch is '{branch}', not '{MAIN_BRANCH}'.")
        ans = input("Continue anyway? [yN] ").strip().lower()
        if ans != "y":
            print("cancelled")
            sys.exit(1)


def clean_build_artifacts(verbose: bool = False) -> None:
    root = script_root()
    candidates = [
        root / "dist",
        root / "build",
        root / ".pytest_cache",
        root / ".mypy_cache",
    ]
    candidates += list(root.glob("*.egg-info"))
    candidates += list(root.rglob("__pycache__"))

    for path in candidates:
        try:
            if path.is_dir():
                import shutil

                shutil.rmtree(path)
                if verbose:
                    print(f"removed directory: {path.relative_to(root)}")
            elif path.exists():
                path.unlink()
                if verbose:
                    print(f"removed file: {path.relative_to(root)}")
        except Exception as exc:
            print(f"could not remove {path}: {exc}")


def build_and_upload(skip_existing: bool = False) -> None:
    if not NO_CLEAN:
        clean_build_artifacts()

    ok, out = exec_cmd("uv build", stream=True)
    if out:
        print(out)
    if not ok:
        sys.exit(1)

    ok, out = exec_cmd("uvx twine check dist/*", stream=True)
    if out:
        print(out)
    if not ok:
        sys.exit(1)

    flags = ["-r", "pypi", "--verbose"]
    if skip_existing:
        flags.append("--skip-existing")

    ok, out = exec_cmd(
        f"uvx twine upload {' '.join(flags)} dist/*",
        stream=True,
    )
    if out:
        print(out)
    if not ok:
        sys.exit(1)


def parse_version_components(current_version: str) -> tuple[str, str, int]:
    pre = current_version
    ext = "a"
    ext_num = 1

    for poss in POSSIBLE_EXTENSIONS:
        if poss in current_version:
            pre, post = current_version.split(poss)
            ext = poss
            ext_num = int(post) + 1
            break

    return pre, ext, ext_num


def version_options(
    current_version: str,
) -> tuple[dict[str, dict[str, str]], str, str, str, str]:
    pre, ext, ext_num = parse_version_components(current_version)
    major, minor, patch = pre.split(".")

    extension_options = {
        "a": {"a": f"a{ext_num}", "b": "b0", "r": "rc0"},
        "b": {"b": f"b{ext_num}", "r": "rc0"},
        "rc": {"r": f"rc{ext_num}"},
    }

    b_patch = ".".join([major, minor, str(int(patch) + 1)])
    b_minor = ".".join([major, str(int(minor) + 1), "0"])
    b_major = ".".join([str(int(major) + 1), "0", "0"])

    return extension_options, pre, ext, b_patch, b_minor, b_major


def prompt_for_new_version(current_version: str) -> tuple[str, str]:
    extension_options, pre, ext, b_patch, b_minor, b_major = version_options(
        current_version
    )

    opts = [f"The current version is {current_version}"]
    if ext and ext in extension_options:
        for key, value in extension_options[ext].items():
            opts.append(f"  {key}: {pre}{value}")
    opts.extend([f"  p: {b_patch}", f"  n: {b_minor}", f"  j: {b_major}"])

    print("\n".join(opts))
    res = input("Which new version? ").strip().lower()
    if not res:
        print("cancelled")
        sys.exit()

    new_version = ""
    bmsg = ""
    if res in extension_options.get(ext, {}):
        new_version = f"{pre}{extension_options[ext][res]}"
        bmsg = "release candidate version update"
    elif res == "p":
        new_version = b_patch
        bmsg = "patch version update"
    elif res == "n":
        new_version = b_minor
        bmsg = "minor version update"
    elif res == "j":
        new_version = b_major
        bmsg = "major version update"
    else:
        print("Unknown option. Cancelled.")
        sys.exit()

    return new_version, bmsg


def write_version(new_version: str) -> None:
    path = version_file_path()
    if DRY_RUN:
        print(f"[dry-run] write version file: {path}")
        print(f"[dry-run] new version: {new_version}")
        return

    path.write_text(f"version = '{new_version}'\n", encoding="utf-8")
    print(f"new version: {new_version}")


def update_changes_file(count: int = 20) -> None:
    now_text = f"Recent tagged changes as of {datetime.now()}:"
    root = script_root()
    changes_file = root / "CHANGES.txt"

    if DRY_RUN:
        print(f"[dry-run] update {changes_file}")
        return

    changes_file.write_text(f"{now_text}\n", encoding="utf-8")
    ok, changelog = read(
        "git log --pretty=format:'- %ar%d %an%n    %h %ai%n%w(70,4,4)%B' "
        f"--max-count={count} --no-walk --tags"
    )
    if ok:
        with changes_file.open("a", encoding="utf-8") as stream:
            if changelog:
                stream.write(changelog)
                if not changelog.endswith("\n"):
                    stream.write("\n")


def commit_and_tag(new_version: str, tag_message: str) -> None:
    quoted_msg = shlex.quote(tag_message)

    ok, _ = run(f"git commit -a -m {quoted_msg}")
    if not ok:
        sys.exit(1)

    ok, version_info = read("git log --pretty=format:'%ai' -n 1")
    if not ok:
        sys.exit(1)

    quoted_version = shlex.quote(new_version)
    quoted_tag_info = shlex.quote(version_info.strip())
    ok, _ = run(f"git tag -a -f {quoted_version} -m {quoted_tag_info}")
    if not ok:
        sys.exit(1)

    update_changes_file()

    ok, _ = run(f"git commit -a --amend -m {quoted_msg}")
    if not ok:
        sys.exit(1)


def pull_rebase_and_push() -> None:
    ok, out = run(f"git pull --rebase origin {MAIN_BRANCH}")
    if out:
        print(out)
    if not ok:
        sys.exit(1)

    ok, out = run(f"git push origin {MAIN_BRANCH}")
    if out:
        print(out)
    if not ok:
        sys.exit(1)

    ok, out = run("git push origin --tags")
    if out:
        print(out)
    if not ok:
        sys.exit(1)


def upload_sdist() -> None:
    build_and_upload(skip_existing=SKIP_EXISTING)


def main() -> None:
    ensure_expected_branch()

    current_version = version
    new_version, bump_message = prompt_for_new_version(current_version)

    tplus = ""
    if bump_message:
        tplus = input(f"Optional {bump_message} message:\n")

    tag_message = f"Tagged version {new_version}. {tplus}".strip()

    print(f"\nThe tag message for the new version will be:\n{tag_message}\n")

    ans = input(f"Commit and tag new version: {new_version}? [yN] ").strip().lower()
    if ans != "y":
        print("cancelled")
        sys.exit()

    write_version(new_version)
    commit_and_tag(new_version, tag_message)

    ans = (
        input(
            f"pull --rebase and push '{MAIN_BRANCH}' to origin, then push tags? [yN] "
        )
        .strip()
        .lower()
    )
    if ans != "y":
        print("cancelled")
        sys.exit()

    pull_rebase_and_push()

    ans = (
        input("build and upload distribution to PyPi using uv/twine? [yN] ")
        .strip()
        .lower()
    )
    if ans != "y":
        print("cancelled")
        sys.exit()

    upload_sdist()


if __name__ == "__main__":
    main()
