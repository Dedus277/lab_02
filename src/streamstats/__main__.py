import argparse
import logging
import os
import sys

from streamstats.analysis import TOP_N, analyze_files
from streamstats.errors import CLIConfigError, StreamStatsError
from streamstats.report import build_report, report_to_text


def parse_args(argv: list | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="streamstats", description="Statistics for event logs.")
    commands = parser.add_subparsers(dest="command", required=True)
    analyze = commands.add_parser("analyze", help="analyze event files")
    analyze.add_argument("inputs", nargs="+", metavar="INPUT", help="input files")
    analyze.add_argument("--format", required=True, metavar="csv|jsonl", help="input format")
    analyze.add_argument("--output", help="report file (default: print on the screen)")
    analyze.add_argument("--skip-invalid",   action="store_true", help="skip bad lines")
    analyze.add_argument("--top", type=int, default=TOP_N, help="size of the error ranking")
    return parser.parse_args(argv)


def check_arguments(args: argparse.Namespace) -> None:
    if args.top < 1:
        raise CLIConfigError("--top must be 1 or more")
    for path in args.inputs:
        if not os.path.isfile(path):
            raise CLIConfigError("input file not found: " + path)
        # чтобы случайно не затереть входной файл отчётом
        if args.output is not None and os.path.abspath(path) == os.path.abspath(args.output):
            raise CLIConfigError("--output must not be an input file")


def main(argv: list | None = None) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    args = parse_args(argv)
    try:
        check_arguments(args)
        stats = analyze_files(args.inputs, args.format, args.skip_invalid)
        text = report_to_text(build_report(stats, args.top))
        if args.output is None:
            sys.stdout.write(text)
        else:
            with open(args.output, "w", encoding="utf-8") as file:
                file.write(text)
    except StreamStatsError as error:  # плохие данные или аргументы
        print("error:", error, file=sys.stderr)
        return 2
    except UnicodeDecodeError:  # файл не в utf-8
        print("error: the file is not valid UTF-8", file=sys.stderr)
        return 2
    except OSError as error:  # проблемы с диском
        print("I/O error:", error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
