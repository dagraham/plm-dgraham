from pathlib import Path

from plm.email_flow import (
    ask_email_payload,
    join_addresses,
    nag_email_payload,
    run_email_clipboard_flow,
    schedule_email_payload,
)
from plm.periods import (
    derive_quarter_period,
    infer_period_from_year_month,
    infer_period_from_year_quarter,
    parse_year_month,
    parse_year_quarter,
    render_title_template,
    suggest_quarter_project_name,
    weekday_tag_suffix,
)
from plm.project_io import list_project_files, load_project, save_project
from plm.relative_dates import (
    format_ymd,
    parse_absolute_template_date,
    parse_relative_weekday_rule,
    parse_template_reply_by,
    resolve_relative_reply_by,
)
from plm.responses import normalize_response_value, parse_response_input
from plm.template_export import (
    dump_template_snippet,
    export_template_mapping,
    exportable_template_data,
    sanitize_template_name,
    suggest_template_description,
    suggest_template_name,
    suggest_title_template,
)
from plm.templates import (
    get_template,
    has_template,
    list_template_names,
    template_defaults,
    template_description,
)
from plm.utils import format_head, rel_path, wrap_format, wrap_text


def test_format_head_uppercases_and_underlines():
    result = format_head("Summary")
    assert result == "SUMMARY\n======="


def test_wrap_text_preserves_content():
    text = "Player Lineup Manager helps organize schedules."
    wrapped = wrap_text(text)
    assert "Player Lineup Manager" in wrapped
    assert "organize schedules." in wrapped


def test_wrap_format_preserves_content():
    text = "Scheduled: Alice, Bob, Carol, Dave"
    wrapped = wrap_format(text, width=20)
    assert "Scheduled:" in wrapped
    assert "Alice" in wrapped
    assert "Dave" in wrapped


def test_rel_path_returns_tilde_prefixed_home_path():
    home = str(Path.home())
    candidate = str(Path(home) / "plm" / "projects")
    result = rel_path(candidate)
    assert result.startswith("~/")


def test_save_and_load_project_round_trip(tmp_path):
    project_path = tmp_path / "sample.yaml"
    data = {
        "TITLE": "Tuesday Tennis",
        "DATES": ["1/7", "1/14"],
        "RESPONSES": {"Doe, Jane": "all"},
    }

    save_project(project_path, data)
    loaded = load_project(project_path)

    assert loaded["TITLE"] == data["TITLE"]
    assert loaded["DATES"] == data["DATES"]
    assert loaded["RESPONSES"] == data["RESPONSES"]


def test_list_project_files_returns_only_yaml_files(tmp_path):
    (tmp_path / "a.yaml").write_text("TITLE: A\n", encoding="utf-8")
    (tmp_path / "b.yaml").write_text("TITLE: B\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignore me\n", encoding="utf-8")

    files = list_project_files(tmp_path)

    assert files == ["a.yaml", "b.yaml"]


def test_join_addresses_filters_when_predicate_is_provided():
    addresses = {
        "Doe, Jane": "jane@example.com",
        "Smith, John": "john@example.com",
    }

    result = join_addresses(addresses, lambda name: name == "Doe, Jane")

    assert result == "jane@example.com"


def test_ask_email_payload_builds_expected_values():
    yaml_data = {
        "ADDRESSES": {
            "Doe, Jane": "jane@example.com",
            "Smith, John": "john@example.com",
        },
        "CAN": "y",
        "TITLE": "Tuesday Tennis",
        "REQUEST": "Please send your dates.",
    }

    addresses, subject, body = ask_email_payload(yaml_data)

    assert addresses == "jane@example.com, john@example.com"
    assert subject == "Tuesday Tennis - CAN PLAY DATES REQUEST"
    assert body == "Please send your dates."


def test_nag_email_payload_only_includes_non_responders():
    yaml_data = {
        "ADDRESSES": {
            "Doe, Jane": "jane@example.com",
            "Smith, John": "john@example.com",
        },
        "RESPONSES": {
            "Doe, Jane": "nr",
            "Smith, John": "all",
        },
        "TITLE": "Tuesday Tennis",
        "NAG": "Reminder text.",
    }

    addresses, subject, body = nag_email_payload(yaml_data)

    assert addresses == "jane@example.com"
    assert subject == "Tuesday Tennis - CAN PLAY DATES REMINDER"
    assert body == "Reminder text."


def test_schedule_email_payload_builds_expected_values():
    yaml_data = {
        "ADDRESSES": {
            "Doe, Jane": "jane@example.com",
            "Smith, John": "john@example.com",
        },
        "TITLE": "Tuesday Tennis",
        "SCHEDULE": "Schedule body",
    }

    addresses, subject, body = schedule_email_payload(yaml_data)

    assert addresses == "jane@example.com, john@example.com"
    assert subject == "Tuesday Tennis - Schedule"
    assert body == "Schedule body"


def test_run_email_clipboard_flow_returns_true_when_all_steps_confirmed():
    copied = []
    prompts = []

    def fake_copy(text):
        copied.append(text)

    def fake_prompt(message, default="yes"):
        prompts.append((message, default))
        return "yes"

    result = run_email_clipboard_flow(
        "jane@example.com",
        "Subject",
        "Body",
        copy_to_clipboard=fake_copy,
        prompt=fake_prompt,
        intro_text="Intro",
        body_label="BODY",
        addresses_step_text="Paste addresses",
        subject_step_text="Paste subject",
        body_step_text="Paste body",
    )

    assert result is True
    assert copied == ["jane@example.com", "Subject", "Body"]
    assert prompts == [
        ("Have the ADDRESSES been pasted? ", "yes"),
        ("Has the SUBJECT been pasted? ", "yes"),
        ("Has the BODY been pasted? ", "yes"),
    ]


def test_run_email_clipboard_flow_stops_after_subject_cancellation():
    copied = []
    prompts = iter(["yes", "no"])

    def fake_copy(text):
        copied.append(text)

    def fake_prompt(message, default="yes"):
        return next(prompts)

    result = run_email_clipboard_flow(
        "jane@example.com",
        "Subject",
        "Body",
        copy_to_clipboard=fake_copy,
        prompt=fake_prompt,
        intro_text="Intro",
        body_label="BODY",
        addresses_step_text="Paste addresses",
        subject_step_text="Paste subject",
        body_step_text="Paste body",
    )

    assert result is False
    assert copied == ["jane@example.com", "Subject"]


def test_normalize_response_value_formats_lists_for_prompt_defaults():
    assert normalize_response_value(["1/7", "1/14*"]) == "1/7, 1/14*"
    assert normalize_response_value("all") == "all"


def test_parse_response_input_normalizes_nr_aliases():
    parsed, issues = parse_response_input("na", ["1/7", "1/14"])

    assert parsed == "nr"
    assert issues == []


def test_parse_response_input_accepts_special_keywords():
    parsed, issues = parse_response_input("sub", ["1/7", "1/14"])

    assert parsed == "sub"
    assert issues == []

    parsed, issues = parse_response_input("last", ["1/7", "1/14"], allow_last=True)

    assert parsed == "last"
    assert issues == []


def test_parse_response_input_parses_valid_date_tokens():
    parsed, issues = parse_response_input(
        "1/7, 1/14*, 1/21~",
        ["1/7", "1/14", "1/21"],
        allow_last=True,
    )

    assert parsed == ["1/7", "1/14*", "1/21~"]
    assert issues == []


def test_parse_response_input_reports_invalid_tokens():
    parsed, issues = parse_response_input(
        "1/7, bad, 2/99",
        ["1/7", "1/14"],
    )

    assert parsed == ["1/7"]
    assert issues == ["bad", "2/99"]


def test_parse_response_input_handles_list_input():
    parsed, issues = parse_response_input(
        ["1/7", "1/14*"],
        ["1/7", "1/14"],
    )

    assert parsed == ["1/7", "1/14*"]
    assert issues == []


def test_parse_response_input_returns_none_for_empty_response():
    parsed, issues = parse_response_input("   ", ["1/7", "1/14"])

    assert parsed is None
    assert issues == []


def test_list_template_names_includes_bundled_templates():
    names = list_template_names()

    assert "tuesday_doubles" in names
    assert "monday_doubles" in names
    assert "friday_doubles" in names


def test_get_template_returns_expected_template_data():
    template = get_template("tuesday_doubles")

    assert template is not None
    assert template["PLAYER_TAG"] == "tue"
    assert template["DAY"] == 1
    assert template["NUM_PLAYERS"] == 4


def test_template_defaults_excludes_description_metadata():
    defaults = template_defaults("tuesday_doubles")

    assert defaults is not None
    assert "description" not in defaults
    assert defaults["PLAYER_TAG"] == "tue"
    assert defaults["ASSIGN_TBD"] == "y"


def test_template_description_returns_human_readable_text():
    description = template_description("friday_doubles")

    assert description == "Standard Friday doubles schedule"


def test_has_template_distinguishes_existing_and_missing_templates():
    assert has_template("monday_doubles") is True
    assert has_template("not_a_template") is False


def test_derive_quarter_period_returns_expected_boundaries():
    period = derive_quarter_period(2025, 2)

    assert period.year == 2025
    assert period.quarter == 2
    assert period.begin_ymd == "2025/4/1"
    assert period.end_ymd == "2025/6/30"
    assert period.period_label == "2nd Quarter"


def test_infer_period_from_year_month_maps_month_to_quarter():
    period = infer_period_from_year_month(2025, 10)

    assert period.quarter == 4
    assert period.begin_ymd == "2025/10/1"
    assert period.end_ymd == "2025/12/31"


def test_render_title_template_uses_period_values():
    result = render_title_template(
        "Tuesday Tennis {period} {year}",
        year=2025,
        quarter=2,
    )

    assert result == "Tuesday Tennis 2nd Quarter 2025"


def test_parse_year_quarter_accepts_plain_quarter_format():
    year, quarter = parse_year_quarter("2025/2")

    assert year == 2025
    assert quarter == 2


def test_parse_year_month_accepts_two_digit_month_format():
    year, month = parse_year_month("2025/04")

    assert year == 2025
    assert month == 4


def test_parse_year_quarter_rejects_q_prefixed_format():
    try:
        parse_year_quarter("2025/Q4")
        assert False, "expected ValueError for Q-prefixed quarter format"
    except ValueError:
        assert True


def test_infer_period_from_year_quarter_maps_to_expected_boundaries():
    period = infer_period_from_year_quarter("2025/3")

    assert period.quarter == 3
    assert period.begin_ymd == "2025/7/1"
    assert period.end_ymd == "2025/9/30"


def test_suggest_quarter_project_name_formats_expected_name():
    result = suggest_quarter_project_name(2025, 2, "TU")

    assert result == "2025-2Q-TU"


def test_weekday_tag_suffix_returns_expected_abbreviation():
    assert weekday_tag_suffix(1) == "TU"
    assert weekday_tag_suffix(4) == "FR"


def test_parse_absolute_template_date_accepts_zero_padded_input():
    result = parse_absolute_template_date("2026/06/19")

    assert format_ymd(result) == "2026/06/19"


def test_parse_relative_weekday_rule_accepts_third_friday():
    ordinal, weekday = parse_relative_weekday_rule("3FR")

    assert ordinal == 3
    assert weekday == 4


def test_resolve_relative_reply_by_uses_previous_month_of_anchor():
    result = resolve_relative_reply_by(
        "3FR",
        anchor_year=2026,
        anchor_month=7,
    )

    assert format_ymd(result) == "2026/06/19"


def test_parse_template_reply_by_accepts_absolute_date():
    result = parse_template_reply_by(
        "2026/06/19",
        anchor_year=2026,
        anchor_month=7,
    )

    assert format_ymd(result) == "2026/06/19"


def test_parse_template_reply_by_accepts_relative_rule():
    result = parse_template_reply_by(
        "3FR",
        anchor_year=2026,
        anchor_month=7,
    )

    assert format_ymd(result) == "2026/06/19"


def test_sanitize_template_name_normalizes_text():
    assert sanitize_template_name("Tuesday Doubles Custom") == "tuesday_doubles_custom"
    assert sanitize_template_name("2025-2Q-TU") == "2025_2q_tu"


def test_suggest_template_name_uses_project_name():
    assert suggest_template_name("2025-2Q-TU.yaml") == "2025_2q_tu"


def test_suggest_template_description_uses_project_name():
    assert (
        suggest_template_description("2025-2Q-TU.yaml")
        == "Template based on 2025-2Q-TU"
    )


def test_suggest_title_template_replaces_quarter_year_phrase():
    assert (
        suggest_title_template("Tuesday Tennis 2nd Quarter 2025")
        == "Tuesday Tennis {period} {year}"
    )


def test_exportable_template_data_extracts_reusable_fields():
    project_data = {
        "TITLE": "Tuesday Tennis 2nd Quarter 2025",
        "PLAYER_TAG": "tue",
        "CAN": "y",
        "REPEAT": "y",
        "DAY": 1,
        "NUM_COURTS": 0,
        "NUM_PLAYERS": 4,
        "ASSIGN_TBD": "y",
        "ALLOW_LAST": "n",
        "REPLY_BY": "2025/3/25",
        "DATES": ["4/1", "4/8"],
        "RESPONSES": {"Doe, Jane": "all"},
    }

    result = exportable_template_data(project_data, description="Tuesday doubles")

    assert result == {
        "description": "Tuesday doubles",
        "TITLE_TEMPLATE": "Tuesday Tennis {period} {year}",
        "PLAYER_TAG": "tue",
        "CAN": "y",
        "REPEAT": "y",
        "DAY": 1,
        "NUM_COURTS": 0,
        "NUM_PLAYERS": 4,
        "ASSIGN_TBD": "y",
        "ALLOW_LAST": "n",
    }


def test_export_template_mapping_wraps_template_under_sanitized_name():
    project_data = {
        "TITLE": "Friday Tennis Q4 2025",
        "PLAYER_TAG": "fri",
        "CAN": "y",
        "REPEAT": "y",
        "DAY": 4,
        "NUM_COURTS": 1,
        "NUM_PLAYERS": 4,
        "ASSIGN_TBD": "y",
        "ALLOW_LAST": "n",
    }

    result = export_template_mapping(
        "Friday Doubles Custom",
        project_data,
        description="Friday doubles",
    )

    assert result["friday_doubles_custom"]["description"] == "Friday doubles"
    assert (
        result["friday_doubles_custom"]["TITLE_TEMPLATE"]
        == "Friday Tennis {period} {year}"
    )


def test_dump_template_snippet_renders_yaml_text():
    project_data = {
        "TITLE": "Tuesday Tennis 2nd Quarter 2025",
        "PLAYER_TAG": "tue",
        "CAN": "y",
        "REPEAT": "y",
        "DAY": 1,
        "NUM_COURTS": 0,
        "NUM_PLAYERS": 4,
        "ASSIGN_TBD": "y",
        "ALLOW_LAST": "n",
    }

    snippet = dump_template_snippet(
        "tuesday_doubles_custom",
        project_data,
        description="Template based on 2025-2Q-TU",
    )

    assert "tuesday_doubles_custom:" in snippet
    assert "description: Template based on 2025-2Q-TU" in snippet
    assert "TITLE_TEMPLATE: Tuesday Tennis {period} {year}" in snippet
    assert "PLAYER_TAG: tue" in snippet
