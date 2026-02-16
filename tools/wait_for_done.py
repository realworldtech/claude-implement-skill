#!/usr/bin/env python3
"""
Block until expected .done marker files appear on disk.

Replaces the manual sleep/ls polling loop that wastes Claude's context
window on repeated tool calls. Run this once — it blocks until all
markers are present (or times out), then exits.

Two modes:

  # Wait for N .done files in a directory
  python wait_for_done.py --dir specs/foo/sections/ --count 3

  # Wait for specific named files
  python wait_for_done.py --files specs/foo/story/story-narrative.done \
                                  specs/foo/story/story-slides.done

Options:
  --timeout SECONDS   Maximum wait time (default: 600 = 10 minutes)
  --interval SECONDS  Poll interval (default: 2)

Exit codes:
  0  All markers found
  1  Timeout reached before all markers appeared
"""

import argparse
import glob
import sys
import time
from pathlib import Path


def wait_for_count(directory: Path, count: int, timeout: float, interval: float) -> bool:
    """Wait for `count` .done files to appear in `directory`."""
    pattern = str(directory / "*.done")
    start = time.monotonic()
    last_report = start

    while True:
        found = sorted(glob.glob(pattern))
        if len(found) >= count:
            print(f"All {count} .done markers found in {directory}/")
            for f in found:
                print(f"  {f}")
            return True

        elapsed = time.monotonic() - start
        if elapsed >= timeout:
            print(
                f"Timeout after {int(elapsed)}s — found {len(found)}/{count} .done markers",
                file=sys.stderr,
            )
            for f in found:
                print(f"  {f}", file=sys.stderr)
            return False

        # Progress update every 30 seconds
        if time.monotonic() - last_report >= 30:
            print(f"Waiting... {len(found)}/{count} .done markers ({int(elapsed)}s elapsed)")
            last_report = time.monotonic()

        time.sleep(interval)


def wait_for_files(files: list[str], timeout: float, interval: float) -> bool:
    """Wait for all specified files to exist."""
    paths = [Path(f) for f in files]
    start = time.monotonic()
    last_report = start

    while True:
        missing = [p for p in paths if not p.exists()]
        if not missing:
            print(f"All {len(paths)} .done markers found:")
            for p in paths:
                print(f"  {p}")
            return True

        elapsed = time.monotonic() - start
        if elapsed >= timeout:
            print(
                f"Timeout after {int(elapsed)}s — still missing {len(missing)}/{len(paths)}:",
                file=sys.stderr,
            )
            for p in missing:
                print(f"  {p}", file=sys.stderr)
            return False

        if time.monotonic() - last_report >= 30:
            found = len(paths) - len(missing)
            print(f"Waiting... {found}/{len(paths)} .done markers ({int(elapsed)}s elapsed)")
            last_report = time.monotonic()

        time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Block until .done marker files appear on disk"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--dir",
        type=Path,
        help="Directory to watch for .done files (use with --count)",
    )
    group.add_argument(
        "--files",
        nargs="+",
        help="Specific .done file paths to wait for",
    )
    parser.add_argument(
        "--count",
        type=int,
        help="Number of .done files expected (required with --dir)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=600,
        help="Maximum wait time in seconds (default: 600)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2,
        help="Poll interval in seconds (default: 2)",
    )
    args = parser.parse_args()

    if args.dir is not None:
        if args.count is None:
            parser.error("--count is required when using --dir")
        if not args.dir.is_dir():
            print(f"Error: not a directory: {args.dir}", file=sys.stderr)
            sys.exit(1)
        success = wait_for_count(args.dir, args.count, args.timeout, args.interval)
    else:
        success = wait_for_files(args.files, args.timeout, args.interval)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
