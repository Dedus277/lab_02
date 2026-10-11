from datetime import datetime, timezone

from streamstats.errors import InvalidEventError, InvalidTimestampError

REQUIRED_FIELDS = ["timestamp", "level", "source", "message"]
LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]  # новый уровень добавлять сюда
ERROR_LEVELS = ["ERROR", "CRITICAL"]


class Event:
    def __init__(self, timestamp: datetime, level: str, source: str, message: str) -> None:
        self.timestamp = timestamp
        self.level = level
        self.source = source
        self.message = message


def parse_timestamp(text: str) -> datetime:
    text = text.strip()
    # python 3.10 не понимает Z в конце, поэтому меняем на +00:00
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    moment = datetime.fromisoformat(text)
    # если часового пояса нет, считаем что это UTC
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    # все даты приводим к UTC, иначе их нельзя сравнивать между собой
    return moment.astimezone(timezone.utc)


def make_event(record: object, path: str, line: int) -> Event:
    # record может быть чем угодно, например списком, если в jsonl лежит [1, 2]
    if not isinstance(record, dict):
        raise InvalidEventError(path, line, "JSON object expected")

    for name in REQUIRED_FIELDS:
        if record.get(name) is None:
            raise InvalidEventError(path, line, "missing required field", name)
        if not isinstance(record[name], str):
            raise InvalidEventError(path, line, "must be a string", name)

    try:
        timestamp = parse_timestamp(record["timestamp"])
    except ValueError as error:
        reason = "invalid date " + record["timestamp"]
        raise InvalidTimestampError(path, line, reason, "timestamp") from error

    if record["level"] not in LEVELS:
        raise InvalidEventError(path, line, "unknown level " + record["level"], "level")

    if record["source"].strip() == "":
        raise InvalidEventError(path, line, "source is empty", "source")

    return Event(timestamp, record["level"], record["source"], record["message"])
