from streamstats.models import ERROR_LEVELS, LEVELS, Event
from streamstats.parsers import get_reader

TOP_N = 5


def sort_key(item: tuple) -> tuple:
    name, count = item
    # минус, чтобы больше ошибок было выше; если поровну, то по алфавиту
    return (-count, name)


def top_n(counts: dict, n: int) -> list:
    items = sorted(counts.items(), key=sort_key)
    return items[:n]


class Stats:
    # тут только числа, сами события мы не храним
    def __init__(self) -> None:
        self.total = 0
        self.files = 0
        self.skipped = 0
        self.levels = {}
        for level in LEVELS:
            self.levels[level] = 0
        self.sources = {}
        self.error_sources = {}
        self.first = None
        self.last = None

    def add(self, event: Event) -> None:
        self.total += 1
        self.levels[event.level] += 1
        self.sources[event.source] = self.sources.get(event.source, 0) + 1
        if event.level in ERROR_LEVELS:
            self.error_sources[event.source] = self.error_sources.get(event.source, 0) + 1
        if self.first is None or event.timestamp < self.first:
            self.first = event.timestamp
        if self.last is None or event.timestamp > self.last:
            self.last = event.timestamp


def analyze_files(paths: list, format_name: str, skip_invalid: bool = False) -> Stats:
    reader = get_reader(format_name)
    stats = Stats()  # один на все файлы, так статистика объединяется
    for path in paths:
        for event in reader(path, skip_invalid):
            if event is None:
                stats.skipped += 1
            else:
                stats.add(event)
        stats.files += 1
    return stats
