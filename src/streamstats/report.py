import json

from streamstats.analysis import TOP_N, Stats, top_n


def build_report(stats: Stats, top: int = TOP_N) -> dict:
    # если событий не было, то дат тоже нет
    first = None
    last = None
    if stats.first is not None:
        first = stats.first.isoformat()
        last = stats.last.isoformat()

    top_list = []
    for source, count in top_n(stats.error_sources, top):
        top_list.append({"source": source, "count": count})

    return {
        "total_events": stats.total,
        "files_processed": stats.files,
        "skipped_invalid_lines": stats.skipped,
        "levels": stats.levels,
        "sources": dict(sorted(stats.sources.items())),
        "top_error_sources": top_list,
        "first_timestamp": first,
        "last_timestamp": last,
    }


def report_to_text(report: dict) -> str:
    # ensure_ascii=False нужен, чтобы русские буквы не превращались в \u0431
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n"
