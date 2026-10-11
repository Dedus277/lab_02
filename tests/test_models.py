import pytest

from streamstats.errors import InvalidEventError, InvalidTimestampError, StreamStatsError
from streamstats.models import make_event, parse_timestamp

GOOD = {"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "source": "s", "message": "m"}


def test_dates_are_converted_to_utc():
    assert parse_timestamp("2024-01-01T10:00:00Z").isoformat() == "2024-01-01T10:00:00+00:00"
    assert parse_timestamp("2024-01-01T12:00:00+03:00").isoformat() == "2024-01-01T09:00:00+00:00"
    assert parse_timestamp("2024-01-01T10:00:00").isoformat() == "2024-01-01T10:00:00+00:00"


def test_good_record():
    event = make_event(GOOD, "f.csv", 2)
    assert event.level == "INFO"
    assert event.message == "m"


def test_empty_message_is_allowed():
    assert make_event({**GOOD, "message": ""}, "f.csv", 2).message == ""


def test_missing_field_is_named():
    for name in GOOD:
        record = dict(GOOD)
        del record[name]
        with pytest.raises(InvalidEventError) as info:
            make_event(record, "f.csv", 5)
        assert info.value.field == name
        assert info.value.line == 5


def test_bad_date_has_field_and_line():
    with pytest.raises(InvalidTimestampError) as info:
        make_event({**GOOD, "timestamp": "yesterday"}, "f.csv", 7)
    assert info.value.field == "timestamp"
    assert info.value.line == 7
    assert "f.csv:7: field 'timestamp'" in str(info.value)


def test_bad_values():
    for bad in [{"level": "NOTICE"}, {"level": "info"}, {"source": "  "}, {"message": 5}]:
        with pytest.raises(InvalidEventError):
            make_event({**GOOD, **bad}, "f.csv", 2)


def test_not_a_dict():
    with pytest.raises(InvalidEventError):
        make_event([1, 2], "f.jsonl", 3)


def test_errors_inherit_from_main_error():
    assert issubclass(InvalidTimestampError, InvalidEventError)
    assert issubclass(InvalidEventError, StreamStatsError)
