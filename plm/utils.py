import os
import shutil
import textwrap


def rel_path(path: str) -> str:
    userhome = os.path.expanduser("~")
    if path.startswith(userhome):
        return os.path.join("~", os.path.relpath(path, userhome))
    return path


def wrap_text(text: str, init_indent: int = 0, subs_indent: int = 0) -> str:
    width = shutil.get_terminal_size()[0] - 2
    paragraphs = text.split("\n")
    wrapped = [
        textwrap.fill(
            paragraph,
            width=width,
            initial_indent=" " * init_indent,
            subsequent_indent=" " * subs_indent,
        )
        for paragraph in paragraphs
    ]
    return "\n".join(wrapped)


def format_head(text: str) -> str:
    text = text.strip()
    return f"{text.upper()}\n{'=' * len(text)}"


def wrap_format(
    text: str, width: int | None = None, subsequent_indent: str = "        "
) -> str:
    if width is None:
        width = max(shutil.get_terminal_size()[0] - 4, 20)
    return "\n".join(
        textwrap.wrap(text, width=width, subsequent_indent=subsequent_indent)
    )


def print_head(text: str) -> None:
    print(format_head(text))


def wrap_print(
    text: str, width: int | None = None, subsequent_indent: str = "        "
) -> None:
    print(wrap_format(text, width=width, subsequent_indent=subsequent_indent))
