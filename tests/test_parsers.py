import pytest

from helpers import GOOD_LINE, HEADER, ROWS, write_csv, write_jsonl, write_text
from streamstats.errors import InvalidEventError, UnsupportedFormatError
from streamstats.models import Event
from streamstats.parsers import get_reader, read_csv, read_jsonl


def test_csv_reader(tmp_path):
    events = list(read_csv(write_csv(tmp_path), False))
    assert len(events) == 5
    assert [event.level for event in events] == [row[1] for row in ROWS]
    assert events[4].message == "token, expired"  # запятая внутри кавычек


def test_jsonl_reader(tmp_path):
    events = list(read_jsonl(write_jsonl(tmp_path), False))
    assert [event.message for event in events] == [row[3] for row in ROWS]


def test_unicode(tmp_path):
    for events in (
        list(read_csv(write_csv(tmp_path), False)),
        list(read_jsonl(write_jsonl(tmp_path), False)),
    ):
        assert events[1].source == "база"
        assert events[1].message == "Ошибка соединения"


def test_empty_files(tmp_path):
    assert list(read_csv(write_text(tmp_path, "e.csv", ""), False)) == []
    assert list(read_jsonl(write_text(tmp_path, "e.jsonl", ""), False)) == []
    assert list(read_csv(write_text(tmp_path, "h.csv", HEADER), False)) == []


def test_csv_with_bom_and_windows_line_ends(tmp_path):
    text = "\ufeff" + HEADER.replace("\n", "\r\n") + "2024-01-01T00:00:00Z,INFO,s,m\r\n"
    assert len(list(read_csv(write_text(tmp_path, "a.csv", text), False))) == 1


def test_jsonl_blank_lines_are_ignored(tmp_path):
    path = write_text(tmp_path, "b.jsonl", "\n" + GOOD_LINE + "\n" + GOOD_LINE)
    assert len(list(read_jsonl(path, False))) == 2


def test_bad_json_in_line_7_default_mode(tmp_path):
    path = write_text(tmp_path, "bad.jsonl", GOOD_LINE * 6 + "{not json}\n" + GOOD_LINE)
    with pytest.raises(InvalidEventError) as info:
        list(read_jsonl(path, False))
    assert info.value.line == 7
    assert "bad.jsonl:7" in str(info.value)


def test_bad_json_skip_mode(tmp_path):
    path = write_text(tmp_path, "bad.jsonl", GOOD_LINE * 6 + "{not json}\n" + GOOD_LINE)
    items = list(read_jsonl(path, True))
    assert len(items) == 8
    assert items[6] is None  # плохая седьмая строка пропущена
    assert isinstance(items[7], Event)  # восьмая строка всё равно прочитана


def test_bad_date_in_csv_both_modes(tmp_path):
    path = write_text(tmp_path, "t.csv", HEADER + "2024-01-01T00:00:00Z,INFO,s,m\nnope,INFO,s,m\n")
    with pytest.raises(InvalidEventError) as info:
        list(read_csv(path, False))
    assert info.value.field == "timestamp"
    assert info.value.line == 3
    items = list(read_csv(path, True))
    assert isinstance(items[0], Event)
    assert items[1] is None


def test_csv_short_row_is_a_bad_line(tmp_path):
    path = write_text(tmp_path, "c.csv", HEADER + "2024-01-01T00:00:00Z,INFO,s\n")
    with pytest.raises(InvalidEventError) as info:
        list(read_csv(path, False))
    assert info.value.line == 2
    assert list(read_csv(path, True)) == [None]


def test_csv_without_required_column(tmp_path):
    path = write_text(tmp_path, "h.csv", "timestamp,level,source\n2024-01-01T00:00:00Z,INFO,s\n")
    with pytest.raises(InvalidEventError):
        list(read_csv(path, True))


def test_reader_is_lazy(tmp_path):
    # вторая (плохая) строка не читается, пока мы не попросим второй элемент
    path = write_text(tmp_path, "lazy.jsonl", GOOD_LINE + "{bad\n")
    generator = read_jsonl(path, False)
    assert isinstance(next(generator), Event)
    with pytest.raises(InvalidEventError):
        next(generator)


def test_unsupported_format():
    with pytest.raises(UnsupportedFormatError):
        get_reader("xml")
