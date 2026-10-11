# Все наши ошибки в одном месте


class StreamStatsError(Exception):
    # главная ошибка, от неё наследуются остальные
    pass


class UnsupportedFormatError(StreamStatsError):
    # формат не csv и не jsonl
    pass


class InvalidEventError(StreamStatsError):
    # плохая строка в файле, помним где именно она находится
    def __init__(self, path: str, line: int, reason: str, field: str = "") -> None:
        if field:
            text = f"{path}:{line}: field '{field}': {reason}"
        else:
            text = f"{path}:{line}: {reason}"
        super().__init__(text)
        self.path = path
        self.line = line
        self.field = field


class InvalidTimestampError(InvalidEventError):
    # дата написана неправильно
    pass


class CLIConfigError(StreamStatsError):
    # пользователь неправильно запустил программу
    pass
