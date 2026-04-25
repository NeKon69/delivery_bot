from pi.keypad_parser import KeypadParser


def test_parses_multiple_jobs_on_double_hash() -> None:
    parser = KeypadParser()

    result = None
    for key in "123#2#111#1##":
        result = parser.handle_key(key)

    assert result is not None
    assert [(job.cabinet_id, job.box_id) for job in result.completed_jobs] == [
        ("123", 2),
        ("111", 1),
    ]
    assert parser.buffer == ""


def test_star_backspaces_and_d_clears() -> None:
    parser = KeypadParser()

    parser.handle_key("1")
    parser.handle_key("2")
    result = parser.handle_key("*")
    assert result.display_text == "1"

    result = parser.handle_key("D")
    assert result.display_text == ""
    assert parser.buffer == ""


def test_zero_requests_full_reset() -> None:
    parser = KeypadParser()

    parser.handle_key("1")
    parser.handle_key("2")
    result = parser.handle_key("0")

    assert result.reset_requested is True
    assert result.display_text == ""
    assert parser.buffer == ""


def test_rejects_invalid_box_id() -> None:
    parser = KeypadParser()

    result = None
    for key in "123#3##":
        result = parser.handle_key(key)

    assert result is not None
    assert result.error == "Invalid box id: 3"
