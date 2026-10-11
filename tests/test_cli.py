import json

import pytest

from helpers import GOOD_LINE, write_csv, write_jsonl, write_text
from streamstats.__main__ import main


def read_file(path):
    with open(path, "rb") as file:
        return file.read()


def test_help():
    with pytest.raises(SystemExit) as info:
        main(["--help"])
    assert info.value.code == 0


def test_two_files_end_to_end(tmp_path):
    first = write_csv(tmp_path, "a.csv")
    second = write_csv(tmp_path, "b.csv")
    report_path = str(tmp_path / "report.json")
    code = main(["analyze", first, second, "--format", "csv", "--output", report_path])
    assert code == 0
    text = read_file(report_path).decode("utf-8")
    assert "база" in text  # русские буквы остались буквами
    report = json.loads(text)
    assert report["total_events"] == 10
    assert report["files_processed"] == 2
    assert report["top_error_sources"][0] == {"source": "база", "count": 4}


def test_default_mode_stops_with_code_2(tmp_path, capsys):
    path = write_text(tmp_path, "bad.jsonl", GOOD_LINE * 6 + "{broken\n" + GOOD_LINE)
    report_path = str(tmp_path / "report.json")
    before = read_file(path)
    code = main(["analyze", path, "--format", "jsonl", "--output", report_path])
    assert code == 2
    assert "bad.jsonl:7" in capsys.readouterr().err
    assert not (tmp_path / "report.json").exists()
    assert read_file(path) == before


def test_skip_invalid_mode(tmp_path):
    path = write_text(tmp_path, "bad.jsonl", GOOD_LINE + "{broken\n" + GOOD_LINE)
    report_path = str(tmp_path / "report.json")
    before = read_file(path)
    code = main(["analyze", path, "--format", "jsonl", "--skip-invalid", "--output", report_path])
    assert code == 0
    report = json.loads(read_file(report_path))
    assert report["total_events"] == 2
    assert report["skipped_invalid_lines"] == 1
    assert read_file(path) == before


def test_report_on_screen_without_output(tmp_path, capsys):
    code = main(["analyze", write_jsonl(tmp_path), "--format", "jsonl"])
    assert code == 0
    assert json.loads(capsys.readouterr().out)["total_events"] == 5


def test_empty_file(tmp_path):
    report_path = str(tmp_path / "r.json")
    empty = write_text(tmp_path, "e.csv", "")
    assert main(["analyze", empty, "--format", "csv", "--output", report_path]) == 0
    assert json.loads(read_file(report_path))["total_events"] == 0


def test_wrong_arguments_give_code_2(tmp_path):
    path = write_jsonl(tmp_path)
    assert main(["analyze", str(tmp_path / "missing.jsonl"), "--format", "jsonl"]) == 2
    assert main(["analyze", path, "--format", "xml"]) == 2
    assert main(["analyze", path, "--format", "jsonl", "--top", "0"]) == 2
    assert main(["analyze", path, "--format", "jsonl", "--output", path]) == 2
    assert read_file(path).startswith(b"{")  # входной файл не испорчен
