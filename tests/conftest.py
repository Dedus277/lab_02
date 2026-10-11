"""Shared deterministic fixtures: every test works in its own tmp_path."""

import csv
import json

import pytest

# (timestamp, level, source, message); mixes Z / offset / naive timestamps,
# Cyrillic text and a comma inside a CSV field.
EVENTS = [
    ("2024-01-01T10:00:00Z", "INFO", "api", "started"),
    ("2024-01-01T10:00:05+00:00", "ERROR", "база", "Ошибка соединения"),
    ("2024-01-01T09:59:00", "WARNING", "api", "slow"),
    ("2024-01-02T00:00:00Z", "CRITICAL", "база", "диск заполнен"),
    ("2024-01-01T12:00:00+03:00", "ERROR", "auth", "token, expired"),
]
FIELDS = ["timestamp", "level", "source", "message"]


@pytest.fixture
def events():
    return list(EVENTS)


@pytest.fixture
def make_csv(tmp_path):
    def _make(name="events.csv", rows=EVENTS):
        path = tmp_path / name
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(FIELDS)
            writer.writerows(rows)
        return path

    return _make


@pytest.fixture
def make_jsonl(tmp_path):
    def _make(name="events.jsonl", rows=EVENTS):
        path = tmp_path / name
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(dict(zip(FIELDS, row, strict=True)), ensure_ascii=False))
                handle.write("\n")
        return path

    return _make


@pytest.fixture
def write_text(tmp_path):
    def _write(name, text):
        path = tmp_path / name
        path.write_bytes(text.encode("utf-8"))
        return path

    return _write
