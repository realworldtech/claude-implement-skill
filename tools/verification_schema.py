"""Verification fragment schema: dataclasses, enums, and validation."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Status(str, Enum):
    IMPLEMENTED = "implemented"
    PARTIAL = "partial"
    NOT_IMPLEMENTED = "not_implemented"
    NA = "na"


class MoSCoW(str, Enum):
    MUST = "MUST"
    SHOULD = "SHOULD"
    COULD = "COULD"
    WONT = "WONT"


class TestCoverage(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"


class Resolution(str, Enum):
    FIXED = "fixed"
    PARTIALLY_FIXED = "partially_fixed"
    NOT_FIXED = "not_fixed"
    REGRESSED = "regressed"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class SchemaError(Exception):
    """Raised when a fragment fails hard validation."""

    pass


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class FileRef:
    path: str
    lines: str = ""
    description: str = ""


@dataclass
class Implementation:
    files: list[FileRef] = field(default_factory=list)
    notes: str = ""


@dataclass
class Finding:
    schema_version: str
    fragment_id: str
    section_ref: str
    title: str
    requirement_text: str
    moscow: MoSCoW
    status: Status
    implementation: Implementation
    test_coverage: TestCoverage
    tests: list[FileRef] = field(default_factory=list)
    missing_tests: list[str] = field(default_factory=list)
    missing_implementation: list[str] = field(default_factory=list)
    notes: str = ""
    # Re-verification fields (optional)
    v_item_id: str = ""
    previous_status: Status | None = None
    resolution: Resolution | None = None


@dataclass
class MoSCoWBreakdown:
    total: int = 0
    implemented: int = 0
    partial: int = 0
    not_implemented: int = 0
    na: int = 0


@dataclass
class Statistics:
    total_requirements: int = 0
    by_status: dict[str, int] = field(default_factory=dict)
    by_moscow: dict[str, MoSCoWBreakdown] = field(default_factory=dict)
    test_coverage: dict[str, int] = field(default_factory=dict)
    implementation_rate: float = 0.0
    test_rate: float = 0.0
    must_implementation_rate: float = 0.0


@dataclass
class PriorityGap:
    priority: str
    v_item_id: str
    section_ref: str
    title: str
    moscow: str
    status: str
    test_coverage: str
    reason: str


@dataclass
class ReportMetadata:
    project_name: str
    spec_path: str
    implementation_path: str
    date: str
    run: int
    previous_report: str | None = None
    spec_version: str = ""
    mode: str = ""


@dataclass
class ResolutionSummary:
    previous_total: int
    fixed: int
    partially_fixed: int
    not_fixed: int
    regressed: int
    new_items: int


@dataclass
class VerificationReport:
    schema_version: str
    report_type: str
    metadata: ReportMetadata
    findings: list[Finding]
    statistics: Statistics
    priority_gaps: list[PriorityGap]
    resolution_summary: ResolutionSummary | None = None

    def to_dict(self) -> dict:
        """Serialise the report to a JSON-compatible dict.

        Recursively converts all nested dataclasses and enums.
        """

        def _serialise(obj):
            if isinstance(obj, Enum):
                return obj.value
            if hasattr(obj, "__dataclass_fields__"):
                return {
                    k: _serialise(v)
                    for k, v in obj.__dataclass_fields__.items()
                    for k, v in [(k, getattr(obj, k))]
                }
            if isinstance(obj, list):
                return [_serialise(item) for item in obj]
            if isinstance(obj, dict):
                return {k: _serialise(v) for k, v in obj.items()}
            return obj

        return _serialise(self)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_ENUM_FIELDS: dict[str, type[Enum]] = {
    "moscow": MoSCoW,
    "status": Status,
    "test_coverage": TestCoverage,
}

_REQUIRED_FIELDS: list[str] = [
    "schema_version",
    "fragment_id",
    "section_ref",
    "title",
    "requirement_text",
    "moscow",
    "status",
    "implementation",
    "test_coverage",
    "tests",
    "missing_tests",
    "missing_implementation",
]


def validate_fragment(data: dict, filename: str) -> tuple[list[str], list[str]]:
    """Validate a fragment dict against the schema.

    Returns (errors, warnings). Errors are hard failures; warnings are
    consistency issues that don't prevent loading.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Required fields
    for field_name in _REQUIRED_FIELDS:
        if field_name not in data:
            errors.append(f"Missing required field: {field_name}")

    # implementation must have files array
    impl = data.get("implementation")
    if isinstance(impl, dict) and "files" not in impl:
        errors.append("implementation missing required field: files")

    # Enum validation
    for field_name, enum_cls in _ENUM_FIELDS.items():
        value = data.get(field_name)
        if value is not None:
            valid_values = [e.value for e in enum_cls]
            if value not in valid_values:
                errors.append(
                    f"Invalid {field_name} value: '{value}'. "
                    f"Valid values: {valid_values}"
                )

    # Re-verification enum validation
    if "previous_status" in data and data["previous_status"] is not None:
        valid = [e.value for e in Status]
        if data["previous_status"] not in valid:
            errors.append(f"Invalid previous_status value: '{data['previous_status']}'")

    if "resolution" in data and data["resolution"] is not None:
        valid = [e.value for e in Resolution]
        if data["resolution"] not in valid:
            errors.append(f"Invalid resolution value: '{data['resolution']}'")

    # fragment_id must match filename stem
    fid = data.get("fragment_id")
    if fid is not None:
        stem = Path(filename).stem
        if fid != stem:
            errors.append(
                f"fragment_id mismatch: '{fid}' does not match "
                f"filename stem '{stem}'"
            )

    # --- Consistency warnings ---

    status = data.get("status")
    missing_impl = data.get("missing_implementation", [])
    impl_files = []
    if isinstance(impl, dict):
        impl_files = impl.get("files", [])

    if status == "implemented" and missing_impl:
        warnings.append(
            "status is 'implemented' but missing_implementation is non-empty"
        )

    if status == "not_implemented" and impl_files:
        warnings.append(
            "status is 'not_implemented' but implementation.files is non-empty"
        )

    test_cov = data.get("test_coverage")
    missing_tests = data.get("missing_tests", [])
    tests = data.get("tests", [])

    if test_cov == "full" and missing_tests:
        warnings.append("test_coverage is 'full' but missing_tests is non-empty")

    if test_cov == "none" and tests:
        warnings.append("test_coverage is 'none' but tests is non-empty")

    return errors, warnings


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def _build_file_ref(data: dict) -> FileRef:
    """Build a FileRef from a dict."""
    return FileRef(
        path=data.get("path", ""),
        lines=data.get("lines", ""),
        description=data.get("description", ""),
    )


def load_fragment(path: Path) -> Finding:
    """Read a JSON fragment file, validate, and return a Finding dataclass.

    Raises SchemaError on hard validation errors or invalid JSON.
    Logs warnings for consistency issues.
    """
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise SchemaError(f"{path.name}: invalid JSON: {exc}") from exc

    errors, warnings = validate_fragment(data, path.name)

    if errors:
        raise SchemaError(
            f"{path.name}: validation errors:\n" + "\n".join(f"  - {e}" for e in errors)
        )

    for w in warnings:
        logger.warning("%s: %s", path.name, w)

    # Build Implementation
    impl_data = data.get("implementation", {})
    impl = Implementation(
        files=[_build_file_ref(f) for f in impl_data.get("files", [])],
        notes=impl_data.get("notes", ""),
    )

    # Build tests list
    tests = [_build_file_ref(t) for t in data.get("tests", [])]

    # Re-verification fields
    previous_status = None
    if "previous_status" in data and data["previous_status"] is not None:
        previous_status = Status(data["previous_status"])

    resolution = None
    if "resolution" in data and data["resolution"] is not None:
        resolution = Resolution(data["resolution"])

    return Finding(
        schema_version=data["schema_version"],
        fragment_id=data["fragment_id"],
        section_ref=data["section_ref"],
        title=data["title"],
        requirement_text=data["requirement_text"],
        moscow=MoSCoW(data["moscow"]),
        status=Status(data["status"]),
        implementation=impl,
        test_coverage=TestCoverage(data["test_coverage"]),
        tests=tests,
        missing_tests=data.get("missing_tests", []),
        missing_implementation=data.get("missing_implementation", []),
        notes=data.get("notes", ""),
        v_item_id=data.get("v_item_id", ""),
        previous_status=previous_status,
        resolution=resolution,
    )


# ---------------------------------------------------------------------------
# Statistics computation
# ---------------------------------------------------------------------------


def _calc_rate(
    findings: list[Finding],
    value_fn,
    filter_fn=None,
) -> float:
    """Calculate a rate from findings, excluding NA from the denominator.

    Args:
        findings: List of Finding objects.
        value_fn: Callable(Finding) -> float contribution (e.g. 1.0, 0.5, 0.0).
        filter_fn: Optional callable(Finding) -> bool to pre-filter findings.

    Returns:
        Rate rounded to 3 decimal places, or 0.0 if denominator is 0.
    """
    subset = findings if filter_fn is None else [f for f in findings if filter_fn(f)]
    non_na = [f for f in subset if f.status != Status.NA]
    if not non_na:
        return 0.0
    return round(sum(value_fn(f) for f in non_na) / len(non_na), 3)


def compute_statistics(findings: list[Finding]) -> Statistics:
    """Compute aggregate statistics from a list of findings."""
    if not findings:
        return Statistics()

    # Count by status
    by_status: dict[str, int] = {}
    for f in findings:
        key = f.status.value
        by_status[key] = by_status.get(key, 0) + 1

    # Count by test_coverage
    test_cov: dict[str, int] = {}
    for f in findings:
        key = f.test_coverage.value
        test_cov[key] = test_cov.get(key, 0) + 1

    # MoSCoW breakdown
    by_moscow: dict[str, MoSCoWBreakdown] = {}
    for f in findings:
        key = f.moscow.value
        if key not in by_moscow:
            by_moscow[key] = MoSCoWBreakdown()
        bd = by_moscow[key]
        bd.total += 1
        if f.status == Status.IMPLEMENTED:
            bd.implemented += 1
        elif f.status == Status.PARTIAL:
            bd.partial += 1
        elif f.status == Status.NOT_IMPLEMENTED:
            bd.not_implemented += 1
        elif f.status == Status.NA:
            bd.na += 1

    def impl_value(f: Finding) -> float:
        if f.status == Status.IMPLEMENTED:
            return 1.0
        if f.status == Status.PARTIAL:
            return 0.5
        return 0.0

    def test_value(f: Finding) -> float:
        if f.test_coverage == TestCoverage.FULL:
            return 1.0
        if f.test_coverage == TestCoverage.PARTIAL:
            return 0.5
        return 0.0

    implementation_rate = _calc_rate(findings, impl_value)
    test_rate = _calc_rate(findings, test_value)
    must_implementation_rate = _calc_rate(
        findings, impl_value, filter_fn=lambda f: f.moscow == MoSCoW.MUST
    )

    return Statistics(
        total_requirements=len(findings),
        by_status=by_status,
        by_moscow=by_moscow,
        test_coverage=test_cov,
        implementation_rate=implementation_rate,
        test_rate=test_rate,
        must_implementation_rate=must_implementation_rate,
    )


# ---------------------------------------------------------------------------
# Priority gap classification
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# V-item ID assignment and re-verification mapping
# ---------------------------------------------------------------------------


def assign_v_items(findings: list[Finding]) -> None:
    """Assign sequential V-item IDs (V1, V2, ...) to findings.

    Sorts by fragment_id (lexicographic) for deterministic ordering,
    then assigns V1, V2, ... in that order. Modifies findings in-place.
    """
    sorted_findings = sorted(findings, key=lambda f: f.fragment_id)
    for i, finding in enumerate(sorted_findings, start=1):
        finding.v_item_id = f"V{i}"


def _extract_v_number(v_item_id: str) -> int:
    """Extract the numeric part from a v_item_id like 'V5' -> 5.

    Returns 0 if the ID doesn't match the expected format.
    """
    if v_item_id.startswith("V") and v_item_id[1:].isdigit():
        return int(v_item_id[1:])
    return 0


def map_v_items_from_previous(
    new_findings: list[Finding],
    previous_findings: list[Finding],
) -> None:
    """Map V-item IDs from previous findings to new findings by section_ref.

    For each new finding whose section_ref matches a previous finding,
    the previous v_item_id is carried forward. New findings with no match
    get the next available sequential ID (continuing from the max existing
    numeric ID). Unmatched findings are assigned in fragment_id sort order
    for determinism. Modifies new_findings in-place.
    """
    # Build section_ref -> v_item_id map from previous findings
    prev_map: dict[str, str] = {}
    for f in previous_findings:
        if f.v_item_id:
            prev_map[f.section_ref] = f.v_item_id

    # Find max numeric ID across all previous findings
    max_id = 0
    for f in previous_findings:
        num = _extract_v_number(f.v_item_id)
        if num > max_id:
            max_id = num

    # First pass: carry forward matched IDs, track which IDs are used
    unmatched: list[Finding] = []
    for f in new_findings:
        if f.section_ref in prev_map:
            f.v_item_id = prev_map[f.section_ref]
            num = _extract_v_number(f.v_item_id)
            if num > max_id:
                max_id = num
        else:
            unmatched.append(f)

    # Second pass: assign new IDs to unmatched in fragment_id sort order
    unmatched.sort(key=lambda f: f.fragment_id)
    next_id = max_id + 1
    for f in unmatched:
        f.v_item_id = f"V{next_id}"
        next_id += 1


_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def classify_priority_gaps(findings: list[Finding]) -> list[PriorityGap]:
    """Identify and classify priority gaps from findings.

    A gap is any finding that is NOT (implemented with full test coverage).
    NA-status findings are excluded.

    Returns gaps sorted by priority: high, medium, low.
    """
    gaps: list[PriorityGap] = []

    for f in findings:
        # Skip NA
        if f.status == Status.NA:
            continue

        # Not a gap if fully implemented and fully tested
        if f.status == Status.IMPLEMENTED and f.test_coverage == TestCoverage.FULL:
            continue

        # Determine priority
        priority = _classify_single_gap(f)
        reason = _build_reason(f)

        gaps.append(
            PriorityGap(
                priority=priority,
                v_item_id=f.v_item_id,
                section_ref=f.section_ref,
                title=f.title,
                moscow=f.moscow.value,
                status=f.status.value,
                test_coverage=f.test_coverage.value,
                reason=reason,
            )
        )

    gaps.sort(key=lambda g: _PRIORITY_ORDER.get(g.priority, 99))
    return gaps


def _classify_single_gap(f: Finding) -> str:
    """Determine the priority level of a single gap finding."""
    moscow = f.moscow
    status = f.status
    test_cov = f.test_coverage

    # High: MUST + (not_implemented OR (partial AND no tests))
    if moscow == MoSCoW.MUST:
        if status == Status.NOT_IMPLEMENTED:
            return "high"
        if status == Status.PARTIAL and test_cov == TestCoverage.NONE:
            return "high"

    # Medium: MUST + partial + any test gap, OR SHOULD + not_implemented
    if moscow == MoSCoW.MUST and status == Status.PARTIAL:
        return "medium"
    if moscow == MoSCoW.MUST and status == Status.IMPLEMENTED:
        # Implemented but test gap (since we already excluded full coverage above)
        return "medium"
    if moscow == MoSCoW.SHOULD and status == Status.NOT_IMPLEMENTED:
        return "medium"

    # Low: SHOULD + partial, COULD + any gap
    if moscow == MoSCoW.SHOULD:
        return "low"
    if moscow == MoSCoW.COULD:
        return "low"

    # Fallback for WONT or other edge cases
    return "low"


def _build_reason(f: Finding) -> str:
    """Generate a human-readable reason string for a gap."""
    parts: list[str] = []

    if f.status == Status.NOT_IMPLEMENTED:
        parts.append("not implemented")
    elif f.status == Status.PARTIAL:
        parts.append("partially implemented")
    elif f.status == Status.IMPLEMENTED:
        parts.append("implemented")

    if f.test_coverage == TestCoverage.NONE:
        parts.append("no test coverage")
    elif f.test_coverage == TestCoverage.PARTIAL:
        parts.append("partial test coverage")

    moscow_label = f.moscow.value
    return f"{moscow_label} requirement: {'; '.join(parts)}"


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------

_REPORT_SCHEMA_VERSION = "1.0.0"


def assemble_report(
    fragments_dir: Path,
    project_name: str,
    spec_path: str,
    impl_path: str,
    previous_report_path: Path | None = None,
    spec_version: str = "",
    date: str | None = None,
) -> VerificationReport:
    """Assemble a VerificationReport from fragment JSON files.

    Args:
        fragments_dir: Directory containing ``*.json`` fragment files.
        project_name: Human-readable project name.
        spec_path: Path to the specification directory/file.
        impl_path: Path to the implementation root.
        previous_report_path: Optional path to a previous report JSON for
            re-verification mode.
        spec_version: Optional spec version string.
        date: Report date as ``YYYY-MM-DD``; defaults to today.

    Returns:
        Fully populated VerificationReport.

    Raises:
        SchemaError: If any fragment has hard validation errors.
    """
    # Collect and validate fragments
    fragment_paths = sorted(fragments_dir.glob("*.json"))
    all_errors: list[str] = []
    findings: list[Finding] = []

    for fp in fragment_paths:
        try:
            finding = load_fragment(fp)
            findings.append(finding)
        except SchemaError as exc:
            all_errors.append(str(exc))

    if all_errors:
        raise SchemaError(
            "Fragment validation errors:\n" + "\n".join(f"  - {e}" for e in all_errors)
        )

    # Determine report type and handle V-item assignment
    report_type = "initial"
    run = 1
    resolution_summary: ResolutionSummary | None = None
    previous_report_str: str | None = None
    mode = ""

    if previous_report_path is not None:
        prev_report = load_report(previous_report_path)
        previous_report_str = str(previous_report_path)
        run = prev_report.metadata.run + 1
        mode = "delta"
        report_type = "reverify_delta"

        map_v_items_from_previous(findings, prev_report.findings)

        # Compute resolution summary
        fixed = 0
        partially_fixed = 0
        not_fixed = 0
        regressed = 0
        new_items = 0
        for f in findings:
            if f.resolution == Resolution.FIXED:
                fixed += 1
            elif f.resolution == Resolution.PARTIALLY_FIXED:
                partially_fixed += 1
            elif f.resolution == Resolution.NOT_FIXED:
                not_fixed += 1
            elif f.resolution == Resolution.REGRESSED:
                regressed += 1
            if f.resolution is None and f.previous_status is None:
                # New finding not in previous report
                prev_refs = {pf.section_ref for pf in prev_report.findings}
                if f.section_ref not in prev_refs:
                    new_items += 1

        resolution_summary = ResolutionSummary(
            previous_total=len(prev_report.findings),
            fixed=fixed,
            partially_fixed=partially_fixed,
            not_fixed=not_fixed,
            regressed=regressed,
            new_items=new_items,
        )
    else:
        assign_v_items(findings)

    # Compute statistics and priority gaps
    statistics = compute_statistics(findings)
    priority_gaps = classify_priority_gaps(findings)

    if date is None:
        from datetime import date as date_cls

        date = date_cls.today().isoformat()

    metadata = ReportMetadata(
        project_name=project_name,
        spec_path=spec_path,
        implementation_path=impl_path,
        date=date,
        run=run,
        previous_report=previous_report_str,
        spec_version=spec_version,
        mode=mode,
    )

    return VerificationReport(
        schema_version=_REPORT_SCHEMA_VERSION,
        report_type=report_type,
        metadata=metadata,
        findings=findings,
        statistics=statistics,
        priority_gaps=priority_gaps,
        resolution_summary=resolution_summary,
    )


# ---------------------------------------------------------------------------
# Report loading (deserialisation)
# ---------------------------------------------------------------------------


def load_report(path: Path) -> VerificationReport:
    """Load a VerificationReport from a JSON file.

    This is the inverse of ``VerificationReport.to_dict()`` — it
    reconstructs the full typed dataclass hierarchy from a dict.
    """
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)

    metadata = ReportMetadata(**data["metadata"])

    findings: list[Finding] = []
    for fd in data.get("findings", []):
        impl_data = fd.get("implementation", {})
        impl = Implementation(
            files=[_build_file_ref(f) for f in impl_data.get("files", [])],
            notes=impl_data.get("notes", ""),
        )
        tests = [_build_file_ref(t) for t in fd.get("tests", [])]

        previous_status = None
        if fd.get("previous_status") is not None:
            previous_status = Status(fd["previous_status"])

        resolution = None
        if fd.get("resolution") is not None:
            resolution = Resolution(fd["resolution"])

        findings.append(
            Finding(
                schema_version=fd["schema_version"],
                fragment_id=fd["fragment_id"],
                section_ref=fd["section_ref"],
                title=fd["title"],
                requirement_text=fd["requirement_text"],
                moscow=MoSCoW(fd["moscow"]),
                status=Status(fd["status"]),
                implementation=impl,
                test_coverage=TestCoverage(fd["test_coverage"]),
                tests=tests,
                missing_tests=fd.get("missing_tests", []),
                missing_implementation=fd.get("missing_implementation", []),
                notes=fd.get("notes", ""),
                v_item_id=fd.get("v_item_id", ""),
                previous_status=previous_status,
                resolution=resolution,
            )
        )

    # Reconstruct statistics
    stats_data = data.get("statistics", {})
    by_moscow: dict[str, MoSCoWBreakdown] = {}
    for key, bd in stats_data.get("by_moscow", {}).items():
        by_moscow[key] = MoSCoWBreakdown(**bd)

    statistics = Statistics(
        total_requirements=stats_data.get("total_requirements", 0),
        by_status=stats_data.get("by_status", {}),
        by_moscow=by_moscow,
        test_coverage=stats_data.get("test_coverage", {}),
        implementation_rate=stats_data.get("implementation_rate", 0.0),
        test_rate=stats_data.get("test_rate", 0.0),
        must_implementation_rate=stats_data.get("must_implementation_rate", 0.0),
    )

    # Reconstruct priority gaps
    priority_gaps = [PriorityGap(**pg) for pg in data.get("priority_gaps", [])]

    # Reconstruct resolution summary
    resolution_summary = None
    rs_data = data.get("resolution_summary")
    if rs_data is not None:
        resolution_summary = ResolutionSummary(**rs_data)

    return VerificationReport(
        schema_version=data["schema_version"],
        report_type=data["report_type"],
        metadata=metadata,
        findings=findings,
        statistics=statistics,
        priority_gaps=priority_gaps,
        resolution_summary=resolution_summary,
    )


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

_STATUS_DISPLAY: dict[str, str] = {
    "implemented": "Implemented",
    "partial": "Partial",
    "not_implemented": "Not Implemented",
    "na": "N/A",
}

_TEST_COV_DISPLAY: dict[str, str] = {
    "full": "Full",
    "partial": "Partial",
    "none": "None",
}

_RESOLUTION_DISPLAY: dict[str, str] = {
    "fixed": "FIXED",
    "partially_fixed": "PARTIALLY FIXED",
    "not_fixed": "NOT FIXED",
    "regressed": "REGRESSED",
}


def _fmt_status(status: Status) -> str:
    return _STATUS_DISPLAY.get(status.value, status.value)


def _fmt_test_cov(tc: TestCoverage) -> str:
    return _TEST_COV_DISPLAY.get(tc.value, tc.value)


def _fmt_resolution(res: Resolution | None) -> str:
    if res is None:
        return "\u2014"
    return _RESOLUTION_DISPLAY.get(res.value, res.value)


def _fmt_file_ref(ref: FileRef) -> str:
    """Format a FileRef as ``path:lines`` \u2014 description."""
    if ref.lines:
        code = f"`{ref.path}:{ref.lines}`"
    else:
        code = f"`{ref.path}`"
    if ref.description:
        return f"{code} \u2014 {ref.description}"
    return code


def _fmt_file_refs(refs: list[FileRef]) -> str:
    if not refs:
        return "\u2014"
    return ", ".join(_fmt_file_ref(r) for r in refs)


def _fmt_string_list(items: list[str]) -> str:
    if not items:
        return "\u2014"
    return ", ".join(items)


def _pct(num: int, denom: int) -> str:
    if denom == 0:
        return "0%"
    return f"{round(num / denom * 100)}%"


def render_markdown(report: VerificationReport) -> str:
    """Render a VerificationReport as a formatted markdown string."""
    lines: list[str] = []
    meta = report.metadata
    stats = report.statistics
    findings = report.findings
    gaps = report.priority_gaps
    is_reverify = report.resolution_summary is not None

    # --- Header ---
    lines.append(f"# Implementation Verification: {meta.project_name}")
    lines.append("")
    lines.append(f"**Spec**: {meta.spec_path}")
    lines.append(f"**Implementation**: {meta.implementation_path}")
    lines.append(f"**Date**: {meta.date}")
    if meta.spec_version:
        lines.append(f"**Spec Version**: {meta.spec_version}")
    if is_reverify and meta.previous_report:
        lines.append(f"**Previous Verification**: {meta.previous_report}")
        lines.append(f"**Run**: {meta.run}")
        if meta.mode:
            lines.append(f"**Mode**: {meta.mode}")
    else:
        lines.append("**Previous Verification**: None \u2014 initial verification")
        lines.append(f"**Run**: {meta.run}")

    # --- Summary ---
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    non_na = [f for f in findings if f.status != Status.NA]
    implemented = sum(1 for f in non_na if f.status == Status.IMPLEMENTED)
    lines.append(
        f"**Overall Implementation Status**: "
        f"{implemented} of {len(non_na)} requirements verified"
    )
    testable = [f for f in non_na]
    tested = sum(1 for f in testable if f.test_coverage != TestCoverage.NONE)
    lines.append(
        f"**Test Coverage**: "
        f"{tested} of {len(testable)} testable requirements have tests"
    )

    # --- Requirement-by-Requirement Verification ---
    lines.append("")
    lines.append("## Requirement-by-Requirement Verification")

    # Sort findings by v_item_id for display
    sorted_findings = sorted(findings, key=lambda f: _extract_v_number(f.v_item_id))
    for f in sorted_findings:
        lines.append("")
        lines.append(f"### {f.v_item_id} \u2014 {f.section_ref} \u2014 {f.title}")
        lines.append("")
        lines.append(f"**Spec says**: {f.requirement_text}")
        lines.append(f"**Status**: {_fmt_status(f.status)}")
        lines.append(f"**Implementation**: {_fmt_file_refs(f.implementation.files)}")
        lines.append(f"**Test coverage**: {_fmt_test_cov(f.test_coverage)}")
        lines.append(f"**Tests**: {_fmt_file_refs(f.tests)}")
        lines.append(f"**Missing tests**: {_fmt_string_list(f.missing_tests)}")

    # --- Previous V-Item Resolution (re-verification only) ---
    if is_reverify:
        reverify_findings = [
            f for f in sorted_findings if f.previous_status is not None
        ]
        if reverify_findings:
            lines.append("")
            lines.append("## Previous V-Item Resolution")
            lines.append("")
            for f in reverify_findings:
                prev = _fmt_status(f.previous_status) if f.previous_status else "\u2014"
                curr = _fmt_status(f.status)
                res = _fmt_resolution(f.resolution)
                lines.append(
                    f"- **{f.v_item_id}** \u2014 {f.section_ref} \u2014 "
                    f"{f.title}: {prev} \u2192 {curr} \u2014 {res}"
                )

    # --- Test Coverage Summary table ---
    lines.append("")
    lines.append("## Test Coverage Summary")
    lines.append("")
    lines.append(
        "| V-Item | Section | Requirement | Impl Status "
        "| Test Coverage | Missing Tests |"
    )
    lines.append(
        "|--------|---------|-------------|-------------|"
        "---------------|---------------|"
    )
    for f in sorted_findings:
        missing = _fmt_string_list(f.missing_tests)
        lines.append(
            f"| {f.v_item_id} | {f.section_ref} | {f.title} "
            f"| {_fmt_status(f.status)} | {_fmt_test_cov(f.test_coverage)} "
            f"| {missing} |"
        )

    # --- Items Requiring Tests ---
    if gaps:
        lines.append("")
        lines.append("## Items Requiring Tests")
        lines.append("")
        for i, g in enumerate(gaps, 1):
            tag = f"[{g.priority.upper()}]"
            lines.append(
                f"{i}. {tag} {g.v_item_id} \u2014 {g.section_ref} \u2014 "
                f"{g.title} \u2014 {g.reason}"
            )

    # --- Scorecard ---
    lines.append("")
    if is_reverify and report.resolution_summary:
        rs = report.resolution_summary
        lines.append("## Updated Scorecard")
        lines.append("")
        lines.append("| Metric | Previous | Current | Delta |")
        lines.append("|--------|----------|---------|-------|")
        prev_impl = rs.previous_total
        curr_impl = stats.total_requirements
        lines.append(
            f"| Total Requirements | {prev_impl} | {curr_impl} "
            f"| {curr_impl - prev_impl:+d} |"
        )
        lines.append(f"| Fixed | | {rs.fixed} | |")
        lines.append(f"| Partially Fixed | | {rs.partially_fixed} | |")
        lines.append(f"| Not Fixed | | {rs.not_fixed} | |")
        lines.append(f"| Regressed | | {rs.regressed} | |")
        lines.append(f"| New Items | | {rs.new_items} | |")

        # Also render the standard scorecard
        lines.append("")

    lines.append("## Scorecard")
    lines.append("")
    lines.append("| Metric | Score |")
    lines.append("|--------|-------|")

    impl_count = stats.by_status.get("implemented", 0)
    partial_count = stats.by_status.get("partial", 0)
    not_impl_count = stats.by_status.get("not_implemented", 0)
    total_non_na = impl_count + partial_count + not_impl_count
    lines.append(
        f"| Requirements Implemented | {impl_count} / {total_non_na} "
        f"({_pct(impl_count, total_non_na)}) |"
    )

    full_tested = stats.test_coverage.get("full", 0)
    partial_tested = stats.test_coverage.get("partial", 0)
    no_tests = stats.test_coverage.get("none", 0)
    testable_total = full_tested + partial_tested + no_tests
    lines.append(
        f"| Fully Tested | {full_tested} / {testable_total} "
        f"({_pct(full_tested, testable_total)}) |"
    )
    lines.append(f"| Partially Tested | {partial_tested} |")
    lines.append(f"| No Tests | {no_tests} |")

    critical = sum(1 for g in gaps if g.priority == "high")
    lines.append(f"| Critical Gaps | {critical} |")

    # --- Still Open (re-verification only) ---
    if is_reverify:
        unresolved = [
            f
            for f in sorted_findings
            if f.resolution is not None and f.resolution not in (Resolution.FIXED,)
        ]
        if unresolved:
            lines.append("")
            lines.append("## Still Open")
            lines.append("")
            for f in unresolved:
                lines.append(
                    f"- **{f.v_item_id}** \u2014 {f.section_ref} \u2014 "
                    f"{f.title} \u2014 {_fmt_resolution(f.resolution)}"
                )

    # --- Recommendations ---
    lines.append("")
    lines.append("## Recommendations")
    lines.append("")

    rec_num = 1

    # Must add tests for: items that are implemented but missing tests
    untested_impl = [
        f
        for f in sorted_findings
        if f.status == Status.IMPLEMENTED and f.test_coverage != TestCoverage.FULL
    ]
    if untested_impl:
        items = ", ".join(f"{f.v_item_id} ({f.section_ref})" for f in untested_impl)
        lines.append(f"{rec_num}. **Must add tests for**: {items}")
        rec_num += 1

    # Implementation gaps: not implemented items
    not_impl = [f for f in sorted_findings if f.status == Status.NOT_IMPLEMENTED]
    if not_impl:
        items = ", ".join(f"{f.v_item_id} ({f.section_ref})" for f in not_impl)
        lines.append(f"{rec_num}. **Implementation gaps**: {items}")
        rec_num += 1

    # Partial implementations
    partials = [f for f in sorted_findings if f.status == Status.PARTIAL]
    if partials:
        items = ", ".join(f"{f.v_item_id} ({f.section_ref})" for f in partials)
        lines.append(f"{rec_num}. **Partial implementations**: {items}")
        rec_num += 1

    if rec_num == 1:
        lines.append(
            "No recommendations \u2014 all requirements verified with full test coverage."
        )

    lines.append("")
    return "\n".join(lines)
