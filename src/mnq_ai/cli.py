"""Command-line interface for MNQ research pipeline jobs."""

from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from pathlib import Path

from mnq_ai.config import Phase1Config
from mnq_ai.data.execution_gate import Phase2ExecutionConfig, build_phase2_labels
from mnq_ai.data.manifests import validate_trade_tape
from mnq_ai.data.setup_candidates import build_failed_fvg_candidates
from mnq_ai.data.trade_extractor import Phase1TradeExtractor
from mnq_ai.exceptions import MNQAIError
from mnq_ai.logging_config import configure_logging
from mnq_ai.setups.failed_fvg import FailedFVGConfig


def main(argv: list[str] | None = None) -> int:
    """Run the ``mnq-ai`` CLI."""

    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "audit-mbo":
            config = _config_from_args(args, artifact_root=args.output)
            configure_logging(config.logging_level)
            audit_result = Phase1TradeExtractor(config).audit_mbo(Path(args.input), Path(args.output))
            print(f"audit complete: rows={audit_result.rows_processed} reports={audit_result.reports_dir}")
            return 0
        if args.command == "build-trade-tape":
            config = _config_from_args(args, output_root=args.output, artifact_root=args.artifacts)
            configure_logging(config.logging_level)
            trade_result = Phase1TradeExtractor(config).build_trade_tape(
                Path(args.input),
                Path(args.output),
                Path(args.artifacts),
            )
            print(
                "trade tape complete: "
                f"rows={trade_result.output_rows} output={trade_result.output_root} manifest={trade_result.manifest_path}"
            )
            return 0
        if args.command == "validate-trade-tape":
            observed = validate_trade_tape(Path(args.input), Path(args.manifest))
            print(
                "validation complete: "
                f"rows={observed['row_count']} size={observed['sum_size']} "
                f"signed_volume={observed['sum_signed_volume']}"
            )
            return 0
        if args.command == "build-failed-fvg-candidates":
            config = _config_from_args(args, input_path=args.trade_tape, output_root=args.output, artifact_root=args.artifacts)
            configure_logging(config.logging_level)
            candidate_result = build_failed_fvg_candidates(
                trade_tape_path=Path(args.trade_tape),
                output_root=Path(args.output),
                artifact_root=Path(args.artifacts),
                config=config,
                failed_fvg_config=FailedFVGConfig(
                    tick_size=config.tick_size,
                    effort_range_mult=Decimal(args.effort_range_mult),
                    effort_volume_mult=Decimal(args.effort_volume_mult),
                    atr_window=args.atr_window,
                    volume_window=args.volume_window,
                    stop_buffer_ticks=args.stop_buffer_ticks,
                    max_holding_bars=args.max_holding_bars,
                ),
            )
            print(
                "failed fvg candidates complete: "
                f"candidates={candidate_result.candidate_count} h1_bars={candidate_result.h1_bar_count} "
                f"m30_bars={candidate_result.m30_bar_count} output={candidate_result.output_root} "
                f"manifest={candidate_result.manifest_path}"
            )
            return 0
        if args.command == "build-phase2-labels":
            config = _config_from_args(args, input_path=args.trade_tape, output_root=args.output, artifact_root=args.artifacts)
            configure_logging(config.logging_level)
            label_result = build_phase2_labels(
                trade_tape_path=Path(args.trade_tape),
                setup_candidates_path=Path(args.setup_candidates),
                output_root=Path(args.output),
                artifact_root=Path(args.artifacts),
                config=config,
                execution_config=Phase2ExecutionConfig(
                    tick_size=config.tick_size,
                    commission_per_side=Decimal(args.commission_per_side),
                    entry_slippage_ticks=args.entry_slippage_ticks,
                    stop_slippage_ticks=args.stop_slippage_ticks,
                    time_exit_slippage_ticks=args.time_exit_slippage_ticks,
                    point_value=Decimal(args.point_value),
                    entry_latency_seconds=args.entry_latency_seconds,
                ),
            )
            print(
                "phase2 labels complete: "
                f"labels={label_result.label_count} candidates={label_result.candidate_count} "
                f"gate={label_result.gate_recommendation} output={label_result.output_root} "
                f"manifest={label_result.manifest_path}"
            )
            return 0
    except MNQAIError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    parser.print_help()
    return 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mnq-ai", description="MNQ research pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit-mbo", help="Audit raw Databento MBO Parquet input")
    audit.add_argument("--input", required=True, help="Input Parquet file or dataset directory")
    audit.add_argument("--config", required=True, help="YAML config path")
    audit.add_argument("--output", required=True, help="Artifact report directory")
    audit.add_argument("--overwrite", action="store_true", help="Allow configured overwrite behavior")

    build = subparsers.add_parser("build-trade-tape", help="Build canonical action-T trade tape")
    build.add_argument("--input", required=True, help="Input Parquet file or dataset directory")
    build.add_argument("--config", required=True, help="YAML config path")
    build.add_argument("--output", required=True, help="Partitioned trade-tape output directory")
    build.add_argument("--artifacts", required=True, help="Artifact report directory")
    build.add_argument("--overwrite", action="store_true", help="Overwrite existing output/staging directories")

    validate = subparsers.add_parser("validate-trade-tape", help="Validate a produced trade tape")
    validate.add_argument("--input", required=True, help="Trade-tape dataset directory")
    validate.add_argument("--manifest", required=True, help="Phase 1 manifest JSON")

    failed_fvg = subparsers.add_parser(
        "build-failed-fvg-candidates",
        help="Build deterministic Failed FVG setup candidates from a trade tape",
    )
    failed_fvg.add_argument("--trade-tape", required=True, help="Canonical trade-tape Parquet file or dataset directory")
    failed_fvg.add_argument("--config", required=True, help="YAML config path")
    failed_fvg.add_argument("--output", required=True, help="Output directory for setup_candidates.parquet")
    failed_fvg.add_argument("--artifacts", required=True, help="Artifact report directory")
    failed_fvg.add_argument("--overwrite", action="store_true", help="Overwrite existing candidate output")
    failed_fvg.add_argument("--atr-window", type=int, default=20, help="Trailing M30 bars for range baseline")
    failed_fvg.add_argument("--volume-window", type=int, default=20, help="Trailing M30 bars for volume baseline")
    failed_fvg.add_argument("--effort-range-mult", default="1.20", help="Signal range / trailing range threshold")
    failed_fvg.add_argument("--effort-volume-mult", default="1.30", help="Signal volume / trailing volume threshold")
    failed_fvg.add_argument("--stop-buffer-ticks", type=int, default=0, help="Stop buffer in ticks")
    failed_fvg.add_argument("--max-holding-bars", type=int, default=12, help="Maximum holding time in M30 bars")

    phase2 = subparsers.add_parser(
        "build-phase2-labels",
        help="Build first-barrier execution labels and fail-closed Phase 2 gate artifacts",
    )
    phase2.add_argument("--trade-tape", required=True, help="Canonical trade-tape Parquet file or dataset directory")
    phase2.add_argument("--setup-candidates", required=True, help="Setup-candidate Parquet file or dataset directory")
    phase2.add_argument("--config", required=True, help="YAML config path")
    phase2.add_argument("--output", required=True, help="Output directory for setup_labels.parquet")
    phase2.add_argument("--artifacts", required=True, help="Artifact report directory")
    phase2.add_argument("--overwrite", action="store_true", help="Overwrite existing label output")
    phase2.add_argument("--commission-per-side", default="0", help="Commission in dollars per side")
    phase2.add_argument("--entry-slippage-ticks", type=int, default=0, help="Adverse entry slippage in ticks")
    phase2.add_argument("--stop-slippage-ticks", type=int, default=0, help="Adverse stop slippage in ticks")
    phase2.add_argument("--time-exit-slippage-ticks", type=int, default=0, help="Adverse max-hold exit slippage in ticks")
    phase2.add_argument("--entry-latency-seconds", type=int, default=0, help="Seconds after setup entry before fills can occur")
    phase2.add_argument("--point-value", default="2", help="Dollar value per MNQ point")
    return parser


def _config_from_args(
    args: argparse.Namespace,
    *,
    input_path: str | None = None,
    output_root: str | None = None,
    artifact_root: str | None = None,
) -> Phase1Config:
    return Phase1Config.from_yaml(
        args.config,
        input_path=input_path or args.input,
        output_root=output_root,
        artifact_root=artifact_root,
    ).with_overrides(overwrite=args.overwrite or None)


if __name__ == "__main__":
    raise SystemExit(main())
