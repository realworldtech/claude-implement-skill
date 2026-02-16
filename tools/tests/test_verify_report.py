"""Tests for verify_report.py CLI tool."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

TOOL_PATH = Path(__file__).parent.parent / "verify_report.py"


def _minimal_fragment(
    fragment_id: str = "02-01-01", section_ref: str = "§2.1.1"
) -> dict:
    return {
        "schema_version": "1.0.0",
        "fragment_id": fragment_id,
        "section_ref": section_ref,
        "title": "Test Requirement",
        "requirement_text": "The system MUST do something",
        "moscow": "MUST",
        "status": "implemented",
        "implementation": {
            "files": [{"path": "app.py", "lines": "1-10", "description": "impl"}],
            "notes": "",
        },
        "test_coverage": "full",
        "tests": [{"path": "test_app.py", "lines": "1-5", "description": "test"}],
        "missing_tests": [],
        "missing_implementation": [],
    }


class TestCLI:
    """Tests for the verify_report.py CLI interface."""

    def test_produces_json_and_md_output(self, tmp_path: Path) -> None:
        """Run CLI with a valid fragment; verify exit 0, .json and .md produced."""
        frags = tmp_path / "fragments"
        frags.mkdir()
        frag = _minimal_fragment()
        (frags / "02-01-01.json").write_text(json.dumps(frag), encoding="utf-8")

        output_json = tmp_path / "output" / "verify.json"

        result = subprocess.run(
            [
                sys.executable,
                str(TOOL_PATH),
                "--fragments-dir",
                str(frags),
                "--spec-path",
                "/fake/spec.md",
                "--impl-path",
                "/fake/impl",
                "--project-name",
                "TestProject",
                "--output",
                str(output_json),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert output_json.exists(), "JSON output file should exist"

        output_md = output_json.with_suffix(".md")
        assert output_md.exists(), "Markdown output file should exist"

        report = json.loads(output_json.read_text(encoding="utf-8"))
        assert report["report_type"] == "initial"
        assert len(report["findings"]) == 1

    def test_reverification_with_previous(self, tmp_path: Path) -> None:
        """Run CLI with --previous; verify exit 0, report_type contains 'reverify'."""
        frags = tmp_path / "fragments"
        frags.mkdir()
        frag = _minimal_fragment()
        (frags / "02-01-01.json").write_text(json.dumps(frag), encoding="utf-8")

        # Build a minimal previous report by running the tool first
        initial_json = tmp_path / "initial.json"
        subprocess.run(
            [
                sys.executable,
                str(TOOL_PATH),
                "--fragments-dir",
                str(frags),
                "--spec-path",
                "/fake/spec.md",
                "--impl-path",
                "/fake/impl",
                "--project-name",
                "TestProject",
                "--output",
                str(initial_json),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        # Now run with --previous
        reverify_json = tmp_path / "reverify.json"
        result = subprocess.run(
            [
                sys.executable,
                str(TOOL_PATH),
                "--fragments-dir",
                str(frags),
                "--spec-path",
                "/fake/spec.md",
                "--impl-path",
                "/fake/impl",
                "--project-name",
                "TestProject",
                "--output",
                str(reverify_json),
                "--previous",
                str(initial_json),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"
        report = json.loads(reverify_json.read_text(encoding="utf-8"))
        assert "reverify" in report["report_type"]

    def test_exits_nonzero_on_invalid_fragment(self, tmp_path: Path) -> None:
        """Invalid JSON fragment causes exit code != 0."""
        frags = tmp_path / "fragments"
        frags.mkdir()
        # Missing required fields
        (frags / "bad.json").write_text('{"invalid": true}', encoding="utf-8")

        output_json = tmp_path / "output.json"
        result = subprocess.run(
            [
                sys.executable,
                str(TOOL_PATH),
                "--fragments-dir",
                str(frags),
                "--spec-path",
                "/fake/spec.md",
                "--impl-path",
                "/fake/impl",
                "--project-name",
                "TestProject",
                "--output",
                str(output_json),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0

    def test_verbose_flag_shows_warnings(self, tmp_path: Path) -> None:
        """Fragment with status=implemented but non-empty missing_implementation
        should produce WARNING on stderr when -v is used."""
        frags = tmp_path / "fragments"
        frags.mkdir()
        frag = _minimal_fragment()
        frag["missing_implementation"] = ["some_module.py"]
        (frags / "02-01-01.json").write_text(json.dumps(frag), encoding="utf-8")

        output_json = tmp_path / "output.json"
        result = subprocess.run(
            [
                sys.executable,
                str(TOOL_PATH),
                "--fragments-dir",
                str(frags),
                "--spec-path",
                "/fake/spec.md",
                "--impl-path",
                "/fake/impl",
                "--project-name",
                "TestProject",
                "--output",
                str(output_json),
                "-v",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "WARNING" in result.stderr
