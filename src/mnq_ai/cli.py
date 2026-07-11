"""Command-line interface for MNQ Phase 1 jobs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mnq_ai.config import Phase1Config
from mnq_ai.data.manifests import validate_trade_tape
from mnq_ai.data.trade_extractor import Phase1TradeExtractor
from mnq_ai.exceptions import MNQAIError
from mnq_ai.logging_config import configure_logging


def main(argv: list[str] | None = None) -> int:
    """Run the ``mnq-ai`` CLI."""

    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "audit-mbo":
            config = _config_from_args(args, artifact_root=args.output)
            configure_logging(config.logging_level)
            result = Phase1TradeExtractor(config).audit_mbo(Path(args.input), Path(args.output))
            print(f"audit complete: rows={result.rows_processed} reports={result.reports_dir}")
            return 0
        if args.command == "build-trade-tape":
            config = _config_from_args(args, output_root=args.output, artifact_root=args.artifacts)
            configure_logging(config.logging_level)
            result = Phase1TradeExtractor(config).build_trade_tape(
                Path(args.input),
                Path(args.output),
                Path(args.artifacts),
            )
            print(
                "trade tape complete: "
                f"rows={result.output_rows} output={result.output_root} manifest={result.manifest_path}"
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
    except MNQAIError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    parser.print_help()
    return 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mnq-ai", description="MNQ Phase 1 data-foundation CLI")
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
    return parser


def _config_from_args(
    args: argparse.Namespace,
    *,
    output_root: str | None = None,
    artifact_root: str | None = None,
) -> Phase1Config:
    return Phase1Config.from_yaml(
        args.config,
        input_path=args.input,
        output_root=output_root,
        artifact_root=artifact_root,
    ).with_overrides(overwrite=args.overwrite or None)


if __name__ == "__main__":
    raise SystemExit(main())
