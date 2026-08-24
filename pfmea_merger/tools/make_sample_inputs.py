"""
Split the SBM SOREN template into per-station sample input files.

For each station block, we copy the entire template workbook and delete
all *other* station rows, keeping the header/footer intact. That way each
sample looks exactly like a real user-supplied "one-station" file.

Usage:
    python -m pfmea_merger.tools.make_sample_inputs
"""
from __future__ import annotations

from copy import copy
from pathlib import Path
import shutil
import openpyxl

from pfmea_merger.core.config import MergeSettings, TEMPLATES_DIR, APP_ROOT
from pfmea_merger.core.excel_reader import analyze_workbook


SAMPLES_DIR = APP_ROOT / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

TEMPLATE = TEMPLATES_DIR / "PFMEA_SBM_SOREN_Template.xlsx"


def _delete_rows_range(ws, start: int, end: int) -> None:
    """
    Delete rows [start..end] (inclusive). openpyxl.delete_rows shifts
    subsequent rows up, so we call it once with the amount.
    """
    if end < start:
        return
    amount = end - start + 1
    ws.delete_rows(start, amount)


def _safe_name(s: str) -> str:
    keep = "-_. "
    return "".join(c if (c.isalnum() or c in keep) else "_" for c in s).strip() or "station"


def main():
    settings = MergeSettings()
    analysis = analyze_workbook(TEMPLATE, settings)
    if not analysis.is_valid:
        print("Template invalid:", analysis.error)
        return
    stations = analysis.stations
    print(f"Found {len(stations)} stations in template.")

    for i, block in enumerate(stations):
        out = SAMPLES_DIR / f"station_{i+1:02d}_{block.opc_code}_{_safe_name(block.name)[:20]}.xlsx"
        # Copy the whole template
        shutil.copy2(TEMPLATE, out)
        wb = openpyxl.load_workbook(out)
        ws = wb[settings.sheet_name]

        # Delete OTHER stations. Do it from bottom to top so row numbers
        # remain valid.
        for other in reversed(stations):
            if other.opc_code == block.opc_code and other.start_row == block.start_row:
                continue
            _delete_rows_range(ws, other.start_row, other.end_row)
        wb.save(out)
        wb.close()
        print(f"  ✔ {out.name}  ({block.opc_code} - {block.name}, {block.row_count} rows)")


if __name__ == "__main__":
    main()
