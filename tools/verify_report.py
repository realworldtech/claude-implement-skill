#!/usr/bin/env python3
"""CLI tool to assemble verification fragments into JSON and markdown reports."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Allow importing verification_schema from the same directory
sys.path.insert(0, str(Path(__file__).parent))

from verification_schema import (  # noqa: E402
    SchemaError,
    assemble_report,
    render_markdown,
)

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assemble verification fragments into a JSON and markdown report.",
    )
    parser.add_argument(
        "--fragments-dir",
        required=True,
        type=Path,
        help="Path to directory containing fragment JSON files",
    )
    parser.add_argument(
        "--spec-path",
        required=True,
        help="Path to the spec file",
    )
    parser.add_argument(
        "--impl-path",
        required=True,
        help="Path to the implementation directory",
    )
    parser.add_argument(
        "--project-name",
        required=True,
        help="Project name for the report header",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output path for the JSON report file",
    )
    parser.add_argument(
        "--previous",
        type=Path,
        default=None,
        help="Path to a previous verification report JSON (triggers re-verification mode)",
    )
    parser.add_argument(
        "--spec-version",
        default="",
        help="Spec version string",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show warnings on stderr",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the CLI tool.

    Returns exit code: 0 on success, 1 on error.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Configure logging: capture warnings from verification_schema
    if args.verbose:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("WARNING: %(message)s"))
        handler.setLevel(logging.WARNING)
        logging.getLogger("verification_schema").addHandler(handler)
        logging.getLogger("verification_schema").setLevel(logging.WARNING)

    # Validate fragments directory
    fragments_dir: Path = args.fragments_dir
    if not fragments_dir.is_dir():
        print(f"Error: fragments directory not found: {fragments_dir}", file=sys.stderr)
        return 1

    json_files = list(fragments_dir.glob("*.json"))
    if not json_files:
        print(
            f"Error: no .json files found in {fragments_dir}",
            file=sys.stderr,
        )
        return 1

    # Assemble the report
    try:
        report = assemble_report(
            fragments_dir=fragments_dir,
            project_name=args.project_name,
            spec_path=args.spec_path,
            impl_path=args.impl_path,
            previous_report_path=args.previous,
            spec_version=args.spec_version,
        )
    except SchemaError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # Ensure output directory exists
    output_path: Path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON report
    report_dict = report.to_dict()
    output_path.write_text(
        json.dumps(report_dict, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Write markdown report alongside the JSON
    md_path = output_path.with_suffix(".md")
    md_content = render_markdown(report)
    md_path.write_text(md_content, encoding="utf-8")

    # Print summary to stdout
    stats = report.statistics
    print(f"Fragments: {len(report.findings)}")
    print(f"Findings:  {stats.total_requirements}")
    print(f"Implementation rate: {stats.implementation_rate:.1%}")
    print(f"Test rate: {stats.test_rate:.1%}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
