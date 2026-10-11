# вспомогательные функции: создают тестовые файлы во временной папке

import csv
import json

FIELDS = ["timestamp", "level", "source", "message"]

# 5 событий: даты с Z, с +03:00 и без пояса, русский текст, запятая внутри поля
ROWS = [
    ("2024-01-01T10:00:00Z", "INFO", "api", "started"),
    ("2024-01-01T10:00:05+00:00", "ERROR", "база", "Ошибка соединения"),
    ("2024-01-01T09:59:00", "WARNING", "api", "slow"),
    ("2024-01-02T00:00:00Z", "CRITICAL", "база", "диск заполнен"),
    ("2024-01-01T12:00:00+03:00", "ERROR", "auth", "token, expired"),
]

GOOD_LINE = '{"timestamp":"2024-01-01T00:00:00Z","level":"INFO","source":"s","message":"m"}\n'
HEADER = "timestamp,level,source,message\n"


def write_text(folder, name, text):
    path = folder / name
    path.write_bytes(text.encode("utf-8"))
    return str(path)


def write_csv(folder, name="events.csv", rows=ROWS):
    path = folder / name
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(FIELDS)
        writer.writerows(rows)
    return str(path)


def write_jsonl(folder, name="events.jsonl", rows=ROWS):
    path = folder / name
    with open(path, "w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(dict(zip(FIELDS, row, strict=True)), ensure_ascii=False) + "\n")
    return str(path)
