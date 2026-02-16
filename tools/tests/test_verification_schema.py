"""Tests for verification_schema module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from verification_schema import (
    FileRef,
    Finding,
    Implementation,
    MoSCoW,
    Resolution,
    SchemaError,
    Status,
    TestCoverage,
    assemble_report,
    assign_v_items,
    classify_priority_gaps,
    compute_statistics,
    load_fragment,
    load_report,
    map_v_items_from_previous,
    render_markdown,
    validate_fragment,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _valid_fragment(overrides: dict | None = None) -> dict:
    """Return a minimal valid fragment dict."""
    base = {
        "schema_version": "1.0.0",
        "fragment_id": "02-01-01",
        "section_ref": "\u00a72.1.1",
        "title": "Quick Capture: Scan Barcode",
        "requirement_text": "The system MUST allow adding assets by scanning a barcode",
        "moscow": "MUST",
        "status": "partial",
        "implementation": {
            "files": [
                {
                    "path": "views/capture.py",
                    "lines": "30-45",
                    "description": "Barcode scan view",
                }
            ],
            "notes": "Handles QR and Code128 but not EAN-13",
        },
        "test_coverage": "partial",
        "tests": [
            {
                "path": "tests/test_capture.py",
                "lines": "10-25",
                "description": "Tests scanning",
            }
        ],
        "missing_tests": ["EAN-13 format scanning"],
        "missing_implementation": ["EAN-13 barcode format support"],
        "notes": "Mobile optimisation is template-level",
    }
    if overrides:
        base.update(overrides)
    return base


def _write_fragment(
    tmp_path: Path, data: dict, filename: str = "02-01-01.json"
) -> Path:
    """Write a fragment dict as JSON and return the path."""
    p = tmp_path / filename
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


class TestEnums:
    def test_status_values(self):
        assert Status.IMPLEMENTED == "implemented"
        assert Status.PARTIAL == "partial"
        assert Status.NOT_IMPLEMENTED == "not_implemented"
        assert Status.NA == "na"

    def test_moscow_values(self):
        assert MoSCoW.MUST == "MUST"
        assert MoSCoW.SHOULD == "SHOULD"
        assert MoSCoW.COULD == "COULD"
        assert MoSCoW.WONT == "WONT"

    def test_test_coverage_values(self):
        assert TestCoverage.FULL == "full"
        assert TestCoverage.PARTIAL == "partial"
        assert TestCoverage.NONE == "none"

    def test_resolution_values(self):
        assert Resolution.FIXED == "fixed"
        assert Resolution.PARTIALLY_FIXED == "partially_fixed"
        assert Resolution.NOT_FIXED == "not_fixed"
        assert Resolution.REGRESSED == "regressed"

    def test_status_is_str(self):
        """Enum values are strings for JSON compatibility."""
        assert isinstance(Status.IMPLEMENTED, str)

    def test_moscow_is_str(self):
        assert isinstance(MoSCoW.MUST, str)


# ---------------------------------------------------------------------------
# FileRef tests
# ---------------------------------------------------------------------------


class TestFileRef:
    def test_create_with_all_fields(self):
        ref = FileRef(
            path="views/capture.py", lines="30-45", description="Barcode scan view"
        )
        assert ref.path == "views/capture.py"
        assert ref.lines == "30-45"
        assert ref.description == "Barcode scan view"

    def test_create_with_path_only(self):
        ref = FileRef(path="views/capture.py")
        assert ref.path == "views/capture.py"
        assert ref.lines == ""
        assert ref.description == ""


# ---------------------------------------------------------------------------
# Implementation tests
# ---------------------------------------------------------------------------


class TestImplementation:
    def test_create_with_files(self):
        impl = Implementation(
            files=[FileRef(path="views/capture.py")],
            notes="Some notes",
        )
        assert len(impl.files) == 1
        assert impl.notes == "Some notes"

    def test_notes_optional(self):
        impl = Implementation(files=[])
        assert impl.notes == ""


# ---------------------------------------------------------------------------
# Finding tests
# ---------------------------------------------------------------------------


class TestFinding:
    def test_create_basic(self):
        finding = Finding(
            schema_version="1.0.0",
            fragment_id="02-01-01",
            section_ref="\u00a72.1.1",
            title="Quick Capture",
            requirement_text="The system MUST...",
            moscow=MoSCoW.MUST,
            status=Status.PARTIAL,
            implementation=Implementation(files=[]),
            test_coverage=TestCoverage.PARTIAL,
            tests=[],
            missing_tests=[],
            missing_implementation=[],
        )
        assert finding.fragment_id == "02-01-01"
        assert finding.notes == ""

    def test_reverification_fields_optional(self):
        finding = Finding(
            schema_version="1.0.0",
            fragment_id="02-01-01",
            section_ref="\u00a72.1.1",
            title="Quick Capture",
            requirement_text="The system MUST...",
            moscow=MoSCoW.MUST,
            status=Status.PARTIAL,
            implementation=Implementation(files=[]),
            test_coverage=TestCoverage.PARTIAL,
            tests=[],
            missing_tests=[],
            missing_implementation=[],
        )
        assert finding.v_item_id == ""
        assert finding.previous_status is None
        assert finding.resolution is None

    def test_reverification_fields_set(self):
        finding = Finding(
            schema_version="1.0.0",
            fragment_id="02-01-01",
            section_ref="\u00a72.1.1",
            title="Quick Capture",
            requirement_text="The system MUST...",
            moscow=MoSCoW.MUST,
            status=Status.IMPLEMENTED,
            implementation=Implementation(files=[]),
            test_coverage=TestCoverage.FULL,
            tests=[],
            missing_tests=[],
            missing_implementation=[],
            v_item_id="v1-02-01-01",
            previous_status=Status.PARTIAL,
            resolution=Resolution.FIXED,
        )
        assert finding.v_item_id == "v1-02-01-01"
        assert finding.previous_status == Status.PARTIAL
        assert finding.resolution == Resolution.FIXED


# ---------------------------------------------------------------------------
# validate_fragment tests
# ---------------------------------------------------------------------------


class TestValidateFragment:
    def test_valid_fragment_no_errors(self):
        data = _valid_fragment()
        errors, warnings = validate_fragment(data, "02-01-01.json")
        assert errors == []

    def test_missing_required_field(self):
        data = _valid_fragment()
        del data["title"]
        errors, warnings = validate_fragment(data, "02-01-01.json")
        assert any("title" in e for e in errors)

    def test_missing_schema_version(self):
        data = _valid_fragment()
        del data["schema_version"]
        errors, warnings = validate_fragment(data, "02-01-01.json")
        assert any("schema_version" in e for e in errors)

    def test_invalid_enum_status(self):
        data = _valid_fragment({"status": "banana"})
        errors, warnings = validate_fragment(data, "02-01-01.json")
        assert any("status" in e for e in errors)

    def test_invalid_enum_moscow(self):
        data = _valid_fragment({"moscow": "MAYBE"})
        errors, warnings = validate_fragment(data, "02-01-01.json")
        assert any("moscow" in e for e in errors)

    def test_invalid_enum_test_coverage(self):
        data = _valid_fragment({"test_coverage": "excellent"})
        errors, warnings = validate_fragment(data, "02-01-01.json")
        assert any("test_coverage" in e for e in errors)

    def test_fragment_id_mismatch(self):
        data = _valid_fragment()
        errors, warnings = validate_fragment(data, "99-99-99.json")
        assert any(
            "fragment_id" in e.lower() or "mismatch" in e.lower() for e in errors
        )

    def test_fragment_id_matches_stem(self):
        data = _valid_fragment({"fragment_id": "03-02"})
        errors, warnings = validate_fragment(data, "03-02.json")
        assert not any("mismatch" in e.lower() for e in errors)

    # --- Consistency warnings ---

    def test_warn_implemented_but_missing_implementation(self):
        data = _valid_fragment(
            {"status": "implemented", "missing_implementation": ["something"]}
        )
        errors, warnings = validate_fragment(data, "02-01-01.json")
        assert any("missing_implementation" in w for w in warnings)

    def test_warn_not_implemented_but_has_files(self):
        data = _valid_fragment({"status": "not_implemented"})
        errors, warnings = validate_fragment(data, "02-01-01.json")
        assert any("implementation" in w.lower() for w in warnings)

    def test_warn_full_coverage_but_missing_tests(self):
        data = _valid_fragment(
            {"test_coverage": "full", "missing_tests": ["something"]}
        )
        errors, warnings = validate_fragment(data, "02-01-01.json")
        assert any("missing_tests" in w for w in warnings)

    def test_warn_none_coverage_but_has_tests(self):
        data = _valid_fragment({"test_coverage": "none"})
        # default fragment has tests
        errors, warnings = validate_fragment(data, "02-01-01.json")
        assert any("tests" in w.lower() for w in warnings)

    def test_missing_implementation_field(self):
        data = _valid_fragment()
        del data["implementation"]
        errors, warnings = validate_fragment(data, "02-01-01.json")
        assert any("implementation" in e for e in errors)

    def test_implementation_missing_files(self):
        data = _valid_fragment()
        data["implementation"] = {"notes": "no files key"}
        errors, warnings = validate_fragment(data, "02-01-01.json")
        assert any("files" in e for e in errors)


# ---------------------------------------------------------------------------
# load_fragment tests
# ---------------------------------------------------------------------------


class TestLoadFragment:
    def test_load_valid_fragment(self, tmp_path: Path):
        data = _valid_fragment()
        p = _write_fragment(tmp_path, data)
        finding = load_fragment(p)
        assert isinstance(finding, Finding)
        assert finding.fragment_id == "02-01-01"
        assert finding.moscow == MoSCoW.MUST
        assert finding.status == Status.PARTIAL
        assert len(finding.implementation.files) == 1
        assert finding.implementation.files[0].path == "views/capture.py"

    def test_load_raises_on_missing_field(self, tmp_path: Path):
        data = _valid_fragment()
        del data["title"]
        p = _write_fragment(tmp_path, data)
        with pytest.raises(SchemaError):
            load_fragment(p)

    def test_load_raises_on_invalid_enum(self, tmp_path: Path):
        data = _valid_fragment({"status": "banana"})
        p = _write_fragment(tmp_path, data)
        with pytest.raises(SchemaError):
            load_fragment(p)

    def test_load_with_reverification_fields(self, tmp_path: Path):
        data = _valid_fragment(
            {
                "v_item_id": "v1-02-01-01",
                "previous_status": "not_implemented",
                "resolution": "fixed",
            }
        )
        p = _write_fragment(tmp_path, data)
        finding = load_fragment(p)
        assert finding.v_item_id == "v1-02-01-01"
        assert finding.previous_status == Status.NOT_IMPLEMENTED
        assert finding.resolution == Resolution.FIXED

    def test_load_without_optional_notes(self, tmp_path: Path):
        data = _valid_fragment()
        del data["notes"]
        p = _write_fragment(tmp_path, data)
        finding = load_fragment(p)
        assert finding.notes == ""

    def test_load_invalid_json(self, tmp_path: Path):
        p = tmp_path / "02-01-01.json"
        p.write_text("not json", encoding="utf-8")
        with pytest.raises(SchemaError):
            load_fragment(p)


# ---------------------------------------------------------------------------
# Helper for statistics / priority gap tests
# ---------------------------------------------------------------------------


def _make_finding(
    *,
    moscow: MoSCoW = MoSCoW.MUST,
    status: Status = Status.IMPLEMENTED,
    test_coverage: TestCoverage = TestCoverage.FULL,
    fragment_id: str = "02-01-01",
    section_ref: str = "\u00a72.1.1",
    title: str = "Test Requirement",
    v_item_id: str = "",
) -> Finding:
    """Build a Finding with sensible defaults and keyword overrides."""
    return Finding(
        schema_version="1.0.0",
        fragment_id=fragment_id,
        section_ref=section_ref,
        title=title,
        requirement_text="The system MUST do something",
        moscow=moscow,
        status=status,
        implementation=Implementation(files=[]),
        test_coverage=test_coverage,
        tests=[],
        missing_tests=[],
        missing_implementation=[],
        notes="",
        v_item_id=v_item_id,
    )


# ---------------------------------------------------------------------------
# compute_statistics tests
# ---------------------------------------------------------------------------


class TestComputeStatistics:
    def test_empty_findings(self):
        stats = compute_statistics([])
        assert stats.total_requirements == 0
        assert stats.implementation_rate == 0.0
        assert stats.test_rate == 0.0
        assert stats.must_implementation_rate == 0.0

    def test_all_implemented_and_tested(self):
        findings = [
            _make_finding(
                moscow=MoSCoW.MUST,
                status=Status.IMPLEMENTED,
                test_coverage=TestCoverage.FULL,
            ),
            _make_finding(
                moscow=MoSCoW.SHOULD,
                status=Status.IMPLEMENTED,
                test_coverage=TestCoverage.FULL,
                fragment_id="02-01-02",
            ),
        ]
        stats = compute_statistics(findings)
        assert stats.total_requirements == 2
        assert stats.implementation_rate == 1.0
        assert stats.test_rate == 1.0
        assert stats.must_implementation_rate == 1.0

    def test_partial_counts_as_half(self):
        findings = [
            _make_finding(status=Status.PARTIAL, test_coverage=TestCoverage.PARTIAL),
        ]
        stats = compute_statistics(findings)
        assert stats.implementation_rate == 0.5
        assert stats.test_rate == 0.5

    def test_na_excluded_from_denominators(self):
        findings = [
            _make_finding(status=Status.IMPLEMENTED, test_coverage=TestCoverage.FULL),
            _make_finding(
                status=Status.NA,
                test_coverage=TestCoverage.NONE,
                moscow=MoSCoW.COULD,
                fragment_id="02-01-02",
            ),
        ]
        stats = compute_statistics(findings)
        # Only 1 non-NA finding, fully implemented
        assert stats.implementation_rate == 1.0
        assert stats.test_rate == 1.0

    def test_all_na_returns_zero_rates(self):
        findings = [
            _make_finding(status=Status.NA, test_coverage=TestCoverage.NONE),
        ]
        stats = compute_statistics(findings)
        assert stats.implementation_rate == 0.0
        assert stats.test_rate == 0.0
        assert stats.must_implementation_rate == 0.0

    def test_moscow_breakdown_correct(self):
        findings = [
            _make_finding(
                moscow=MoSCoW.MUST, status=Status.IMPLEMENTED, fragment_id="01"
            ),
            _make_finding(moscow=MoSCoW.MUST, status=Status.PARTIAL, fragment_id="02"),
            _make_finding(
                moscow=MoSCoW.MUST, status=Status.NOT_IMPLEMENTED, fragment_id="03"
            ),
            _make_finding(
                moscow=MoSCoW.SHOULD, status=Status.IMPLEMENTED, fragment_id="04"
            ),
            _make_finding(moscow=MoSCoW.SHOULD, status=Status.NA, fragment_id="05"),
        ]
        stats = compute_statistics(findings)
        must = stats.by_moscow["MUST"]
        assert must.total == 3
        assert must.implemented == 1
        assert must.partial == 1
        assert must.not_implemented == 1
        assert must.na == 0

        should = stats.by_moscow["SHOULD"]
        assert should.total == 2
        assert should.implemented == 1
        assert should.na == 1

    def test_by_status_counts(self):
        findings = [
            _make_finding(status=Status.IMPLEMENTED, fragment_id="01"),
            _make_finding(status=Status.IMPLEMENTED, fragment_id="02"),
            _make_finding(status=Status.PARTIAL, fragment_id="03"),
            _make_finding(status=Status.NOT_IMPLEMENTED, fragment_id="04"),
        ]
        stats = compute_statistics(findings)
        assert stats.by_status["implemented"] == 2
        assert stats.by_status["partial"] == 1
        assert stats.by_status["not_implemented"] == 1

    def test_test_coverage_counts(self):
        findings = [
            _make_finding(test_coverage=TestCoverage.FULL, fragment_id="01"),
            _make_finding(test_coverage=TestCoverage.PARTIAL, fragment_id="02"),
            _make_finding(test_coverage=TestCoverage.NONE, fragment_id="03"),
        ]
        stats = compute_statistics(findings)
        assert stats.test_coverage["full"] == 1
        assert stats.test_coverage["partial"] == 1
        assert stats.test_coverage["none"] == 1

    def test_must_implementation_rate(self):
        findings = [
            _make_finding(
                moscow=MoSCoW.MUST, status=Status.IMPLEMENTED, fragment_id="01"
            ),
            _make_finding(
                moscow=MoSCoW.MUST, status=Status.NOT_IMPLEMENTED, fragment_id="02"
            ),
            _make_finding(
                moscow=MoSCoW.SHOULD, status=Status.NOT_IMPLEMENTED, fragment_id="03"
            ),
        ]
        stats = compute_statistics(findings)
        # MUST: 1 implemented out of 2 = 0.5
        assert stats.must_implementation_rate == 0.5

    def test_rates_rounded_to_3_decimals(self):
        findings = [
            _make_finding(status=Status.IMPLEMENTED, fragment_id="01"),
            _make_finding(status=Status.IMPLEMENTED, fragment_id="02"),
            _make_finding(status=Status.NOT_IMPLEMENTED, fragment_id="03"),
        ]
        stats = compute_statistics(findings)
        # 2/3 = 0.6666... -> 0.667
        assert stats.implementation_rate == 0.667


# ---------------------------------------------------------------------------
# classify_priority_gaps tests
# ---------------------------------------------------------------------------


class TestClassifyPriorityGaps:
    def test_fully_implemented_full_coverage_not_a_gap(self):
        findings = [
            _make_finding(status=Status.IMPLEMENTED, test_coverage=TestCoverage.FULL),
        ]
        gaps = classify_priority_gaps(findings)
        assert len(gaps) == 0

    def test_must_not_implemented_is_high(self):
        findings = [
            _make_finding(
                moscow=MoSCoW.MUST,
                status=Status.NOT_IMPLEMENTED,
                test_coverage=TestCoverage.NONE,
                fragment_id="01",
            ),
        ]
        gaps = classify_priority_gaps(findings)
        assert len(gaps) == 1
        assert gaps[0].priority == "high"
        assert gaps[0].v_item_id == ""
        assert gaps[0].moscow == "MUST"
        assert gaps[0].status == "not_implemented"

    def test_must_partial_no_tests_is_high(self):
        findings = [
            _make_finding(
                moscow=MoSCoW.MUST,
                status=Status.PARTIAL,
                test_coverage=TestCoverage.NONE,
                fragment_id="01",
            ),
        ]
        gaps = classify_priority_gaps(findings)
        assert len(gaps) == 1
        assert gaps[0].priority == "high"

    def test_must_partial_with_test_gap_is_medium(self):
        findings = [
            _make_finding(
                moscow=MoSCoW.MUST,
                status=Status.PARTIAL,
                test_coverage=TestCoverage.PARTIAL,
                fragment_id="01",
            ),
        ]
        gaps = classify_priority_gaps(findings)
        assert len(gaps) == 1
        assert gaps[0].priority == "medium"

    def test_should_not_implemented_is_medium(self):
        findings = [
            _make_finding(
                moscow=MoSCoW.SHOULD,
                status=Status.NOT_IMPLEMENTED,
                test_coverage=TestCoverage.NONE,
                fragment_id="01",
            ),
        ]
        gaps = classify_priority_gaps(findings)
        assert len(gaps) == 1
        assert gaps[0].priority == "medium"

    def test_should_partial_is_low(self):
        findings = [
            _make_finding(
                moscow=MoSCoW.SHOULD,
                status=Status.PARTIAL,
                test_coverage=TestCoverage.PARTIAL,
                fragment_id="01",
            ),
        ]
        gaps = classify_priority_gaps(findings)
        assert len(gaps) == 1
        assert gaps[0].priority == "low"

    def test_could_any_gap_is_low(self):
        findings = [
            _make_finding(
                moscow=MoSCoW.COULD,
                status=Status.NOT_IMPLEMENTED,
                test_coverage=TestCoverage.NONE,
                fragment_id="01",
            ),
        ]
        gaps = classify_priority_gaps(findings)
        assert len(gaps) == 1
        assert gaps[0].priority == "low"

    def test_gaps_sorted_high_medium_low(self):
        findings = [
            _make_finding(
                moscow=MoSCoW.COULD,
                status=Status.NOT_IMPLEMENTED,
                test_coverage=TestCoverage.NONE,
                fragment_id="01",
                title="Low gap",
            ),
            _make_finding(
                moscow=MoSCoW.MUST,
                status=Status.NOT_IMPLEMENTED,
                test_coverage=TestCoverage.NONE,
                fragment_id="02",
                title="High gap",
            ),
            _make_finding(
                moscow=MoSCoW.SHOULD,
                status=Status.NOT_IMPLEMENTED,
                test_coverage=TestCoverage.NONE,
                fragment_id="03",
                title="Medium gap",
            ),
        ]
        gaps = classify_priority_gaps(findings)
        assert len(gaps) == 3
        assert gaps[0].priority == "high"
        assert gaps[1].priority == "medium"
        assert gaps[2].priority == "low"

    def test_gap_has_reason_string(self):
        findings = [
            _make_finding(
                moscow=MoSCoW.MUST,
                status=Status.NOT_IMPLEMENTED,
                test_coverage=TestCoverage.NONE,
                fragment_id="01",
            ),
        ]
        gaps = classify_priority_gaps(findings)
        assert len(gaps[0].reason) > 0

    def test_na_status_not_a_gap(self):
        findings = [
            _make_finding(
                moscow=MoSCoW.MUST,
                status=Status.NA,
                test_coverage=TestCoverage.NONE,
            ),
        ]
        gaps = classify_priority_gaps(findings)
        assert len(gaps) == 0

    def test_implemented_but_no_tests_is_gap(self):
        findings = [
            _make_finding(
                moscow=MoSCoW.MUST,
                status=Status.IMPLEMENTED,
                test_coverage=TestCoverage.NONE,
                fragment_id="01",
            ),
        ]
        gaps = classify_priority_gaps(findings)
        assert len(gaps) >= 1


# ---------------------------------------------------------------------------
# assign_v_items tests
# ---------------------------------------------------------------------------


class TestAssignVItems:
    def test_assigns_sequential_ids(self):
        findings = [
            _make_finding(fragment_id="01-01", section_ref="§1.1"),
            _make_finding(fragment_id="01-02", section_ref="§1.2"),
            _make_finding(fragment_id="01-03", section_ref="§1.3"),
        ]
        assign_v_items(findings)
        assert findings[0].v_item_id == "V1"
        assert findings[1].v_item_id == "V2"
        assert findings[2].v_item_id == "V3"

    def test_assigns_in_fragment_id_sort_order(self):
        findings = [
            _make_finding(fragment_id="03-01", section_ref="§3.1"),
            _make_finding(fragment_id="01-01", section_ref="§1.1"),
            _make_finding(fragment_id="02-01", section_ref="§2.1"),
        ]
        assign_v_items(findings)
        # After assignment, the finding with fragment_id "01-01" should be V1
        by_fid = {f.fragment_id: f.v_item_id for f in findings}
        assert by_fid["01-01"] == "V1"
        assert by_fid["02-01"] == "V2"
        assert by_fid["03-01"] == "V3"


# ---------------------------------------------------------------------------
# map_v_items_from_previous tests
# ---------------------------------------------------------------------------


class TestMapVItemsFromPrevious:
    def test_carries_forward_by_section_ref(self):
        previous = [
            _make_finding(fragment_id="01-01", section_ref="§1.1", v_item_id="V1"),
            _make_finding(fragment_id="01-02", section_ref="§1.2", v_item_id="V2"),
        ]
        new = [
            _make_finding(fragment_id="01-01", section_ref="§1.1"),
            _make_finding(fragment_id="01-02", section_ref="§1.2"),
        ]
        map_v_items_from_previous(new, previous)
        assert new[0].v_item_id == "V1"
        assert new[1].v_item_id == "V2"

    def test_new_findings_get_next_sequential_id(self):
        previous = [
            _make_finding(fragment_id="01-01", section_ref="§1.1", v_item_id="V1"),
            _make_finding(fragment_id="01-02", section_ref="§1.2", v_item_id="V2"),
        ]
        new = [
            _make_finding(fragment_id="01-01", section_ref="§1.1"),
            _make_finding(fragment_id="01-03", section_ref="§1.3"),
        ]
        map_v_items_from_previous(new, previous)
        assert new[0].v_item_id == "V1"
        assert new[1].v_item_id == "V3"

    def test_handles_gaps_in_previous_ids(self):
        previous = [
            _make_finding(fragment_id="01-01", section_ref="§1.1", v_item_id="V1"),
            _make_finding(fragment_id="01-02", section_ref="§1.2", v_item_id="V5"),
        ]
        new = [
            _make_finding(fragment_id="01-01", section_ref="§1.1"),
            _make_finding(fragment_id="01-02", section_ref="§1.2"),
            _make_finding(fragment_id="02-01", section_ref="§2.1"),
            _make_finding(fragment_id="03-01", section_ref="§3.1"),
        ]
        map_v_items_from_previous(new, previous)
        assert new[0].v_item_id == "V1"
        assert new[1].v_item_id == "V5"
        # New items start at V6 (max previous is V5)
        by_fid = {f.fragment_id: f.v_item_id for f in new}
        assert by_fid["02-01"] == "V6"
        assert by_fid["03-01"] == "V7"


# ---------------------------------------------------------------------------
# Helper for assembly tests
# ---------------------------------------------------------------------------


def _minimal_fragment(
    fragment_id: str,
    moscow: str = "MUST",
    status: str = "implemented",
    test_coverage: str = "full",
    section_ref: str | None = None,
    **extra,
) -> dict:
    """Return a minimal valid fragment dict for assembly tests."""
    if section_ref is None:
        section_ref = f"§{fragment_id.replace('-', '.')}"
    base = {
        "schema_version": "1.0.0",
        "fragment_id": fragment_id,
        "section_ref": section_ref,
        "title": f"Requirement {fragment_id}",
        "requirement_text": f"The system {moscow} do {fragment_id}",
        "moscow": moscow,
        "status": status,
        "implementation": {"files": [], "notes": ""},
        "test_coverage": test_coverage,
        "tests": [],
        "missing_tests": [],
        "missing_implementation": [],
        "notes": "",
    }
    base.update(extra)
    return base


# ---------------------------------------------------------------------------
# TestAssembleReport
# ---------------------------------------------------------------------------


class TestAssembleReport:
    def test_assembles_initial_report(self, tmp_path: Path):
        """Write 3 fragments, assemble, verify initial report structure."""
        frags = [
            _minimal_fragment("01-01", moscow="MUST", status="implemented"),
            _minimal_fragment(
                "02-01", moscow="SHOULD", status="partial", test_coverage="partial"
            ),
            _minimal_fragment(
                "03-01", moscow="COULD", status="not_implemented", test_coverage="none"
            ),
        ]
        for frag in frags:
            (tmp_path / f"{frag['fragment_id']}.json").write_text(
                json.dumps(frag), encoding="utf-8"
            )

        report = assemble_report(
            fragments_dir=tmp_path,
            project_name="test-project",
            spec_path="/specs/test",
            impl_path="/src",
            date="2026-02-16",
        )

        assert report.report_type == "initial"
        assert report.metadata.project_name == "test-project"
        assert report.metadata.spec_path == "/specs/test"
        assert report.metadata.implementation_path == "/src"
        assert report.metadata.run == 1
        assert report.metadata.date == "2026-02-16"
        assert len(report.findings) == 3

        # V-item IDs should be assigned
        v_ids = sorted(f.v_item_id for f in report.findings)
        assert v_ids == ["V1", "V2", "V3"]

        # Statistics computed
        assert report.statistics.total_requirements == 3

        # Priority gaps populated (partial and not_implemented are gaps)
        assert len(report.priority_gaps) >= 2

        # No resolution summary for initial
        assert report.resolution_summary is None

    def test_assembles_reverification_report(self, tmp_path: Path):
        """Write a previous report, new fragments with resolution, verify reverify."""
        # Build a previous report by assembling first
        prev_dir = tmp_path / "prev_fragments"
        prev_dir.mkdir()
        prev_frag = _minimal_fragment(
            "01-01", moscow="MUST", status="partial", test_coverage="partial"
        )
        (prev_dir / "01-01.json").write_text(json.dumps(prev_frag), encoding="utf-8")

        prev_report = assemble_report(
            fragments_dir=prev_dir,
            project_name="test-project",
            spec_path="/specs/test",
            impl_path="/src",
            date="2026-02-01",
        )
        # Write previous report to disk
        prev_report_path = tmp_path / "prev_report.json"
        prev_report_path.write_text(
            json.dumps(prev_report.to_dict(), indent=2), encoding="utf-8"
        )

        # New fragments with resolution
        new_dir = tmp_path / "new_fragments"
        new_dir.mkdir()
        new_frag = _minimal_fragment(
            "01-01",
            moscow="MUST",
            status="implemented",
            test_coverage="full",
            previous_status="partial",
            resolution="fixed",
        )
        (new_dir / "01-01.json").write_text(json.dumps(new_frag), encoding="utf-8")

        report = assemble_report(
            fragments_dir=new_dir,
            project_name="test-project",
            spec_path="/specs/test",
            impl_path="/src",
            previous_report_path=prev_report_path,
            date="2026-02-16",
        )

        assert "reverify" in report.report_type
        assert report.metadata.run == 2
        assert report.resolution_summary is not None
        assert report.resolution_summary.fixed >= 1


# ---------------------------------------------------------------------------
# TestReportSerialisation
# ---------------------------------------------------------------------------


class TestReportSerialisation:
    def test_round_trip_json(self, tmp_path: Path):
        """Create report, serialise to JSON, deserialise, verify match."""
        frags = [
            _minimal_fragment("01-01", moscow="MUST", status="implemented"),
            _minimal_fragment(
                "02-01", moscow="SHOULD", status="partial", test_coverage="partial"
            ),
        ]
        for frag in frags:
            (tmp_path / f"{frag['fragment_id']}.json").write_text(
                json.dumps(frag), encoding="utf-8"
            )

        original = assemble_report(
            fragments_dir=tmp_path,
            project_name="roundtrip",
            spec_path="/specs/rt",
            impl_path="/src/rt",
            date="2026-02-16",
        )

        # Serialise
        report_path = tmp_path / "report.json"
        report_path.write_text(
            json.dumps(original.to_dict(), indent=2), encoding="utf-8"
        )

        # Deserialise
        loaded = load_report(report_path)

        assert loaded.metadata.project_name == original.metadata.project_name
        assert loaded.metadata.spec_path == original.metadata.spec_path
        assert loaded.metadata.run == original.metadata.run
        assert len(loaded.findings) == len(original.findings)
        assert (
            loaded.statistics.total_requirements
            == original.statistics.total_requirements
        )
        assert (
            loaded.statistics.implementation_rate
            == original.statistics.implementation_rate
        )
        assert len(loaded.priority_gaps) == len(original.priority_gaps)
        assert loaded.report_type == original.report_type
        assert loaded.schema_version == original.schema_version


# ---------------------------------------------------------------------------
# TestRenderMarkdown
# ---------------------------------------------------------------------------


class TestRenderMarkdown:
    def test_renders_initial_report(self, tmp_path: Path):
        """Render an initial report and verify key sections are present."""
        frags = [
            _minimal_fragment(
                "01-01",
                moscow="MUST",
                status="implemented",
                test_coverage="full",
            ),
            _minimal_fragment(
                "02-01",
                moscow="SHOULD",
                status="partial",
                test_coverage="partial",
            ),
            _minimal_fragment(
                "03-01",
                moscow="COULD",
                status="not_implemented",
                test_coverage="none",
            ),
        ]
        for frag in frags:
            (tmp_path / f"{frag['fragment_id']}.json").write_text(
                json.dumps(frag), encoding="utf-8"
            )

        report = assemble_report(
            fragments_dir=tmp_path,
            project_name="test-project",
            spec_path="/specs/test",
            impl_path="/src",
            date="2026-02-16",
            spec_version="1.2.0",
        )
        md = render_markdown(report)

        # Title with project name
        assert "# Implementation Verification: test-project" in md
        # Metadata header
        assert "**Spec**: /specs/test" in md
        assert "**Spec Version**: 1.2.0" in md
        assert "**Previous Verification**: None" in md
        # Summary section
        assert "## Summary" in md
        # Requirement-by-Requirement section
        assert "## Requirement-by-Requirement Verification" in md
        # V1 heading present
        assert "### V1" in md
        # Test Coverage Summary table
        assert "## Test Coverage Summary" in md
        assert "| V-Item |" in md
        # Scorecard table
        assert "## Scorecard" in md
        assert "Requirements Implemented" in md

    def test_renders_reverification_sections(self, tmp_path: Path):
        """Render a re-verification report and verify resolution sections."""
        # Build previous report
        prev_dir = tmp_path / "prev_fragments"
        prev_dir.mkdir()
        prev_frag = _minimal_fragment(
            "01-01", moscow="MUST", status="partial", test_coverage="partial"
        )
        (prev_dir / "01-01.json").write_text(json.dumps(prev_frag), encoding="utf-8")
        prev_report = assemble_report(
            fragments_dir=prev_dir,
            project_name="test-project",
            spec_path="/specs/test",
            impl_path="/src",
            date="2026-02-01",
        )
        prev_report_path = tmp_path / "prev_report.json"
        prev_report_path.write_text(
            json.dumps(prev_report.to_dict(), indent=2), encoding="utf-8"
        )

        # New fragments with resolution
        new_dir = tmp_path / "new_fragments"
        new_dir.mkdir()
        new_frag = _minimal_fragment(
            "01-01",
            moscow="MUST",
            status="implemented",
            test_coverage="full",
            previous_status="partial",
            resolution="fixed",
        )
        (new_dir / "01-01.json").write_text(json.dumps(new_frag), encoding="utf-8")

        report = assemble_report(
            fragments_dir=new_dir,
            project_name="test-project",
            spec_path="/specs/test",
            impl_path="/src",
            previous_report_path=prev_report_path,
            date="2026-02-16",
        )
        md = render_markdown(report)

        # Re-verification sections
        assert "Resolution" in md
        assert "FIXED" in md
        # Scorecard still present
        assert "## Scorecard" in md or "## Updated Scorecard" in md

    def test_renders_priority_gaps_section(self, tmp_path: Path):
        """Render a report with priority gaps and verify [HIGH] tag."""
        frags = [
            _minimal_fragment(
                "01-01",
                moscow="MUST",
                status="not_implemented",
                test_coverage="none",
            ),
        ]
        for frag in frags:
            (tmp_path / f"{frag['fragment_id']}.json").write_text(
                json.dumps(frag), encoding="utf-8"
            )

        report = assemble_report(
            fragments_dir=tmp_path,
            project_name="test-project",
            spec_path="/specs/test",
            impl_path="/src",
            date="2026-02-16",
        )
        md = render_markdown(report)

        assert "[HIGH]" in md
