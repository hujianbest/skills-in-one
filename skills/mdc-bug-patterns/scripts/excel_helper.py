#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
excel_helper.py — Pass 4 reporter for the mdc-bug-patterns skill.

Renders a list of finding-shaped JSON objects (see references/reporting.md)
into an Excel workbook with two sheets:

    Findings   — confidence in {high, medium}
    Audit Gaps — confidence in {low} or status in {inconclusive, open}

Columns (in order):
    Severity, Confidence, Category, Template ID, Name, Location,
    Summary, Evidence, FP Filters Ruled Out, Fix Suggestions,
    Context, Timestamp

Findings are sorted by (severity, confidence, file, line). Rows are
color-coded by severity.

Usage:
    excel_helper.py --bugs-file findings.json [--output report.xlsx]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "openpyxl is required: pip install openpyxl\n"
    )
    raise


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
CONFIDENCE_ORDER = {"high": 0, "medium": 1, "low": 2}
SEVERITY_COLORS = {
    "CRITICAL": "FFFF6666",
    "HIGH":     "FFFFB266",
    "MEDIUM":   "FFFFFF99",
    "LOW":      "FFCCFFCC",
}
HEADERS = [
    "Severity", "Confidence", "Category", "Template ID", "Name", "Location",
    "Summary", "Evidence", "FP Filters Ruled Out", "Fix Suggestions",
    "Context", "Timestamp",
]
COL_WIDTHS = [10, 11, 12, 28, 28, 32, 50, 70, 36, 50, 70, 20]


def _location(b: dict[str, Any]) -> str:
    loc = b.get("location") or {}
    if isinstance(loc, dict):
        s = f"{loc.get('file', '')}:{loc.get('line', '')}"
        if loc.get("function"):
            s += f"  ({loc['function']})"
        return s
    return str(b.get("location", ""))


def _join_evidence(b: dict[str, Any]) -> str:
    ev = b.get("required_evidence") or b.get("evidence") or {}
    if isinstance(ev, dict):
        return "\n".join(f"{k}: {v}" for k, v in ev.items())
    if isinstance(ev, list):
        return "\n".join(str(x) for x in ev)
    return str(ev)


def _join_list(field: Any) -> str:
    if isinstance(field, list):
        return "\n".join(f"- {x}" for x in field)
    return str(field or "")


def _join_context(b: dict[str, Any]) -> str:
    ctx = b.get("context") or []
    if isinstance(ctx, list):
        return "\n".join(str(x) for x in ctx)
    return str(ctx)


def _sort_key(b: dict[str, Any]) -> tuple:
    loc = b.get("location") or {}
    return (
        SEVERITY_ORDER.get(str(b.get("severity", "low")).lower(), 9),
        CONFIDENCE_ORDER.get(str(b.get("confidence", "low")).lower(), 9),
        str(loc.get("file", "")),
        int(loc.get("line", 0) or 0),
    )


def _write_sheet(ws, rows: list[dict[str, Any]], timestamp: str) -> None:
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    mono_font = Font(name="Courier New", size=10)

    for col, h in enumerate(HEADERS, 1):
        c = ws.cell(1, col, h)
        c.fill = header_fill
        c.font = header_font
        c.alignment = Alignment(horizontal="center", vertical="center")

    for col, w in enumerate(COL_WIDTHS, 1):
        ws.column_dimensions[ws.cell(1, col).column_letter].width = w

    for row, b in enumerate(rows, 2):
        sev = str(b.get("severity", "")).upper()
        ws.cell(row, 1, sev)
        ws.cell(row, 2, str(b.get("confidence", "")).lower())
        ws.cell(row, 3, b.get("category", ""))
        ws.cell(row, 4, b.get("template_id", ""))
        ws.cell(row, 5, b.get("name", ""))
        ws.cell(row, 6, _location(b))
        ws.cell(row, 7, b.get("summary", ""))
        cell_ev = ws.cell(row, 8, _join_evidence(b))
        cell_ev.font = mono_font
        ws.cell(row, 9, _join_list(b.get("false_positive_filters_ruled_out")))
        ws.cell(row, 10, _join_list(b.get("fix_suggestions")))
        cell_ctx = ws.cell(row, 11, _join_context(b))
        cell_ctx.font = mono_font
        ws.cell(row, 12, timestamp)

        wrap = Alignment(horizontal="left", vertical="top", wrap_text=True)
        for col in range(1, len(HEADERS) + 1):
            ws.cell(row, col).alignment = wrap

        color = SEVERITY_COLORS.get(sev)
        if color:
            fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
            for col in range(1, len(HEADERS) + 1):
                ws.cell(row, col).fill = fill

        ws.row_dimensions[row].height = 120


def save_to_excel(bugs: list[dict[str, Any]], filepath: Path) -> bool:
    wb = Workbook()
    ws_findings = wb.active
    ws_findings.title = "Findings"
    ws_gaps = wb.create_sheet("Audit Gaps")

    findings, gaps = [], []
    for b in bugs:
        conf = str(b.get("confidence", "low")).lower()
        status = str(b.get("status", "confirmed")).lower()
        if conf == "low" or status in ("inconclusive", "open"):
            gaps.append(b)
        else:
            findings.append(b)

    findings.sort(key=_sort_key)
    gaps.sort(key=_sort_key)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _write_sheet(ws_findings, findings, timestamp)
    _write_sheet(ws_gaps, gaps, timestamp)

    wb.save(str(filepath))
    print(f"wrote {len(findings)} finding(s), {len(gaps)} gap(s) to {filepath}")
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bugs-file", required=True,
                    help="JSON file containing a list of finding objects.")
    ap.add_argument("--output", "-o", default="bug_report.xlsx",
                    help="Output Excel file (default: bug_report.xlsx).")
    args = ap.parse_args(argv)

    bugs = json.loads(Path(args.bugs_file).read_text(encoding="utf-8"))
    if not isinstance(bugs, list):
        sys.stderr.write("bugs file must contain a JSON list\n")
        return 2
    if not bugs:
        print("(no bugs)")
        return 0
    return 0 if save_to_excel(bugs, Path(args.output)) else 1


if __name__ == "__main__":
    sys.exit(main())
