from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, cast

import pyarrow.dataset as ds

LABEL_COLUMNS = [
    "setup_id",
    "setup_type",
    "entry_side",
    "entry_timestamp",
    "exit_reason",
    "success",
    "net_r",
    "reason_codes",
]


def build_report(*, labels_path: Path, output_path: Path, m30_bar_count: int | None = None) -> dict[str, Any]:
    """Build a QEP failure report from Phase 2 labels."""

    rows = _read_labels(labels_path)
    summary = summarize_labels(rows, m30_bar_count=m30_bar_count)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown(summary), encoding="utf-8")
    return summary


def summarize_labels(rows: list[dict[str, Any]], *, m30_bar_count: int | None = None) -> dict[str, Any]:
    candidate_count = len(rows)
    success_count = sum(1 for row in rows if row.get("success") is True)
    exit_counts = Counter(str(row.get("exit_reason")) for row in rows)
    side_counts = Counter(str(row.get("entry_side")) for row in rows)
    reason_counts: Counter[str] = Counter()
    by_exit: dict[str, list[float]] = defaultdict(list)
    by_side: dict[str, list[float]] = defaultdict(list)
    net_values: list[float] = []

    for row in rows:
        net_r = row.get("net_r")
        if net_r is not None:
            value = float(net_r)
            net_values.append(value)
            by_exit[str(row.get("exit_reason"))].append(value)
            by_side[str(row.get("entry_side"))].append(value)
        for reason in row.get("reason_codes") or []:
            reason_counts[str(reason)] += 1

    density = None if m30_bar_count is None or m30_bar_count <= 0 else candidate_count / m30_bar_count
    summary: dict[str, Any] = {
        "candidate_count": candidate_count,
        "success_count": success_count,
        "hit_rate": _ratio(success_count, candidate_count),
        "exit_reason_counts": dict(sorted(exit_counts.items())),
        "side_counts": dict(sorted(side_counts.items())),
        "reason_code_counts": dict(sorted(reason_counts.items())),
        "sum_net_r": _round(sum(net_values)),
        "avg_net_r": _round(sum(net_values) / len(net_values)) if net_values else None,
        "candidate_density_per_m30_bar": None if density is None else _round(density),
        "net_r_by_exit_reason": _bucket_stats(by_exit),
        "net_r_by_side": _bucket_stats(by_side),
    }
    summary["diagnosis"] = _diagnose(summary)
    return summary


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# QEP Failure Diagnostic Report",
        "",
        f"- `candidate_count`: {summary['candidate_count']}",
        f"- `success_count`: {summary['success_count']}",
        f"- `hit_rate`: {summary['hit_rate']}",
        f"- `sum_net_r`: {summary['sum_net_r']}",
        f"- `avg_net_r`: {summary['avg_net_r']}",
        f"- `candidate_density_per_m30_bar`: {summary['candidate_density_per_m30_bar']}",
        "## exit_reason_counts",
    ]
    for key, value in summary["exit_reason_counts"].items():
        lines.append(f"- `{key}`: {value}")
    lines.append("## side_counts")
    for key, value in summary["side_counts"].items():
        lines.append(f"- `{key}`: {value}")
    lines.append("## net_r_by_exit_reason")
    for key, value in summary["net_r_by_exit_reason"].items():
        lines.append(f"- `{key}`: count={value['count']} sum={value['sum']} avg={value['avg']}")
    lines.append("## net_r_by_side")
    for key, value in summary["net_r_by_side"].items():
        lines.append(f"- `{key}`: count={value['count']} sum={value['sum']} avg={value['avg']}")
    lines.append("## diagnosis")
    for item in summary["diagnosis"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _read_labels(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Labels path does not exist: {path}")
    dataset = ds.dataset(path, format="parquet", partitioning="hive")
    missing = sorted(set(LABEL_COLUMNS) - set(dataset.schema.names))
    if missing:
        raise ValueError(f"Labels path missing columns: {', '.join(missing)}")
    return cast(list[dict[str, Any]], dataset.to_table(columns=LABEL_COLUMNS).to_pylist())


def _diagnose(summary: dict[str, Any]) -> list[str]:
    count = int(summary["candidate_count"])
    hit_rate = float(summary["hit_rate"] or 0)
    avg_net_r = summary["avg_net_r"]
    density = summary["candidate_density_per_m30_bar"]
    exits = summary["exit_reason_counts"]
    diagnosis: list[str] = []

    if avg_net_r is not None and avg_net_r < 0:
        diagnosis.append("negative expectancy after costs: average net R is below zero")
    if hit_rate <= 0.2 and count > 0:
        diagnosis.append("target conversion is weak: few candidates reach TARGET_1")
    if count > 0 and exits.get("MAX_HOLD", 0) / count >= 0.5:
        diagnosis.append("MAX_HOLD dominates exits: signals often fail to resolve before timeout")
    if count > 0 and exits.get("STOP", 0) / count >= 0.3:
        diagnosis.append("STOP exits are frequent: adverse movement is common after entry")
    if density is not None and density >= 0.25:
        diagnosis.append("candidate density is high: raw QEP is overtrading the M30 stream")
    if not diagnosis:
        diagnosis.append("no single dominant failure mode detected; inspect trade-level rows")
    return diagnosis


def _bucket_stats(buckets: dict[str, list[float]]) -> dict[str, dict[str, float | int | None]]:
    return {
        key: {
            "count": len(values),
            "sum": _round(sum(values)),
            "avg": _round(sum(values) / len(values)) if values else None,
        }
        for key, values in sorted(buckets.items())
    }


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return _round(numerator / denominator)


def _round(value: float) -> float:
    return round(value, 4)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Diagnose QEP Phase 2 label failure modes.")
    parser.add_argument("--labels", required=True, type=Path, help="Path to setup_labels.parquet or label dataset")
    parser.add_argument("--output", required=True, type=Path, help="Markdown report output path")
    parser.add_argument("--m30-bar-count", type=int, default=None, help="Optional denominator for candidate density")
    parser.add_argument("--print", action="store_true", help="Print the generated report")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    build_report(labels_path=args.labels, output_path=args.output, m30_bar_count=args.m30_bar_count)
    if args.print:
        print(args.output.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
