import logging

import pytest

from helpers import GOOD_LINE, ROWS, write_csv, write_jsonl, write_text
from streamstats.analysis import Stats, analyze_files, top_n
from streamstats.errors import InvalidEventError
from streamstats.models import Event, parse_timestamp
from streamstats.report import build_report


def make_event(source, level="ERROR"):
    return Event(parse_timestamp("2024-01-01T00:00:00Z"), level, source, "")


def test_required_statistics(tmp_path):
    report = build_report(analyze_files([write_csv(tmp_path)], "csv"))
    assert report["total_events"] == 5
    assert report["levels"] == {"DEBUG": 0, "INFO": 1, "WARNING": 1, "ERROR": 2, "CRITICAL": 1}
    assert report["sources"] == {"api": 2, "auth": 1, "база": 2}
    assert report["top_error_sources"] == [
        {"source": "база", "count": 2},
        {"source": "auth", "count": 1},
    ]
    assert report["first_timestamp"] == "2024-01-01T09:00:00+00:00"
    assert report["last_timestamp"] == "2024-01-02T00:00:00+00:00"
    assert report["skipped_invalid_lines"] == 0


def test_csv_and_jsonl_give_the_same_report(tmp_path):
    from_csv = build_report(analyze_files([write_csv(tmp_path)], "csv"))
    from_jsonl = build_report(analyze_files([write_jsonl(tmp_path)], "jsonl"))
    assert from_csv == from_jsonl


def test_empty_file_gives_zero_report(tmp_path):
    report = build_report(analyze_files([write_text(tmp_path, "e.jsonl", "")], "jsonl"))
    assert report["total_events"] == 0
    assert report["sources"] == {}
    assert report["top_error_sources"] == []
    assert report["first_timestamp"] is None
    assert report["last_timestamp"] is None
    assert sum(report["levels"].values()) == 0


def test_several_files_are_merged(tmp_path):
    first = write_csv(tmp_path, "a.csv")
    second = write_csv(tmp_path, "b.csv", ROWS[:2])
    stats = analyze_files([first, second], "csv")
    assert stats.total == 7
    assert stats.files == 2
    assert stats.sources["база"] == 3


def test_top_is_stable_when_counters_are_equal():
    stats = Stats()
    for source in ["c", "b", "a", "d"]:
        stats.add(make_event(source))
    assert top_n(stats.error_sources, 2) == [("a", 1), ("b", 1)]
    assert top_n({"b": 2, "a": 2, "c": 3}, 2) == [("c", 3), ("a", 2)]


def test_top_size_is_a_parameter():
    stats = Stats()
    for number in range(10):
        stats.add(make_event("s" + str(number)))
    assert len(build_report(stats, 3)["top_error_sources"]) == 3
    assert len(build_report(stats)["top_error_sources"]) == 5


def test_only_error_and_critical_are_error_sources():
    stats = Stats()
    stats.add(make_event("x", "WARNING"))
    stats.add(make_event("y", "CRITICAL"))
    assert stats.error_sources == {"y": 1}


def test_default_mode_stops_on_bad_line(tmp_path):
    path = write_text(tmp_path, "x.jsonl", GOOD_LINE + "oops\n" + GOOD_LINE)
    with pytest.raises(InvalidEventError) as info:
        analyze_files([path], "jsonl")
    assert info.value.line == 2


def test_skip_mode_counts_other_lines_and_warns(tmp_path, caplog):
    path = write_text(tmp_path, "x.jsonl", GOOD_LINE + "oops\n" + GOOD_LINE)
    with caplog.at_level(logging.WARNING):
        stats = analyze_files([path], "jsonl", True)
    assert stats.total == 2
    assert stats.skipped == 1
    assert any(r.levelname == "WARNING" and "x.jsonl:2" in r.getMessage() for r in caplog.records)


def test_source_file_is_not_changed(tmp_path):
    path = write_csv(tmp_path)
    with open(path, "rb") as file:
        before = file.read()
    analyze_files([path], "csv")
    with open(path, "rb") as file:
        assert file.read() == before
