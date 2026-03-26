from typing import Callable, Mapping


def join_addresses(
    addresses: Mapping[str, str], response_filter: Callable[[str], bool] | None = None
) -> str:
    """
    Join email addresses into a comma-separated string.

    Args:
        addresses: Mapping of player name to email address.
        response_filter: Optional predicate applied to player names to decide
            whether the corresponding email address should be included.

    Returns:
        A comma-separated string of email addresses.
    """
    if response_filter is None:
        selected = addresses.values()
    else:
        selected = [email for name, email in addresses.items() if response_filter(name)]
    return ", ".join(selected)


def ask_email_payload(yaml_data: Mapping[str, object]) -> tuple[str, str, str]:
    """
    Build the email payload for requesting player availability.
    """
    addresses = yaml_data["ADDRESSES"]
    can = "CAN" if yaml_data["CAN"] == "y" else "CANNOT"
    title = yaml_data["TITLE"]
    body = yaml_data["REQUEST"]
    return (
        join_addresses(addresses),
        f"{title} - {can} PLAY DATES REQUEST",
        body,
    )


def nag_email_payload(yaml_data: Mapping[str, object]) -> tuple[str, str, str]:
    """
    Build the email payload for reminding non-responders.
    """
    addresses = yaml_data["ADDRESSES"]
    responses = yaml_data["RESPONSES"]
    title = yaml_data["TITLE"]
    body = yaml_data["NAG"]
    return (
        join_addresses(addresses, lambda name: responses[name] == "nr"),
        f"{title} - CAN PLAY DATES REMINDER",
        body,
    )


def schedule_email_payload(yaml_data: Mapping[str, object]) -> tuple[str, str, str]:
    """
    Build the email payload for delivering the completed schedule.
    """
    addresses = yaml_data["ADDRESSES"]
    title = yaml_data["TITLE"]
    body = yaml_data["SCHEDULE"]
    return (
        join_addresses(addresses),
        f"{title} - Schedule",
        body,
    )


def run_email_clipboard_flow(
    addresses: str,
    subject: str,
    body: str,
    *,
    copy_to_clipboard: Callable[[str], None],
    prompt: Callable[..., str],
    intro_text: str,
    body_label: str,
    addresses_step_text: str,
    subject_step_text: str,
    body_step_text: str,
) -> bool:
    """
    Run the common clipboard/paste workflow for email preparation.

    Returns:
        True if all steps were completed, False if the user cancelled.
    """
    print(intro_text)

    copy_to_clipboard(addresses)
    print(addresses_step_text)
    ok = prompt("Have the ADDRESSES been pasted? ", default="yes")
    if ok != "yes":
        print("Cancelled")
        return False

    copy_to_clipboard(subject)
    print(subject_step_text)
    ok = prompt("Has the SUBJECT been pasted? ", default="yes")
    if ok != "yes":
        print("Cancelled")
        return False

    copy_to_clipboard(body)
    print(body_step_text)
    ok = prompt(f"Has the {body_label} been pasted? ", default="yes")
    if ok != "yes":
        print("Cancelled")
        return False

    return True
