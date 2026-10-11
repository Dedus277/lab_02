import csv
import json
import logging
from collections.abc import Callable, Iterator

from streamstats.errors import InvalidEventError, UnsupportedFormatError
from streamstats.models import REQUIRED_FIELDS, Event, make_event

# Читалки - это генераторы, они отдают события по одному.
# Если строка плохая:
#   - обычный режим: сразу падаем с ошибкой
#   - skip_invalid=True: пишем предупреждение и отдаём None (analysis посчитает его)


def bad_line(error: InvalidEventError, skip_invalid: bool) -> None:
    if not skip_invalid:
        raise error
    logging.warning("Skipping invalid line: %s", error)


def read_jsonl(path: str, skip_invalid: bool) -> Iterator[Event | None]:
    with open(path, encoding="utf-8-sig") as file:
        # for по файлу берёт одну строку за раз, весь файл в память не грузится
        for number, line in enumerate(file, start=1):
            line = line.strip()
            if line == "":
                continue
            event = None
            try:
                event = make_event(json.loads(line), path, number)
            except json.JSONDecodeError:
                bad_line(InvalidEventError(path, number, "invalid JSON"), skip_invalid)
            except InvalidEventError as error:
                bad_line(error, skip_invalid)
            yield event


def read_csv(path: str, skip_invalid: bool) -> Iterator[Event | None]:
    with open(path, encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        # fieldnames это None, когда файл совсем пустой
        if reader.fieldnames is None:
            return
        for name in REQUIRED_FIELDS:
            if name not in reader.fieldnames:
                raise InvalidEventError(path, 1, "missing column", name)
        for row in reader:
            event = None
            try:
                event = make_event(row, path, reader.line_num)
            except InvalidEventError as error:
                bad_line(error, skip_invalid)
            yield event


def get_reader(format_name: str) -> Callable:
    # чтобы добавить новый формат, пишем читалку и добавляем ещё один if
    if format_name == "csv":
        return read_csv
    if format_name == "jsonl":
        return read_jsonl
    raise UnsupportedFormatError("unsupported format " + format_name + ", use csv or jsonl")
