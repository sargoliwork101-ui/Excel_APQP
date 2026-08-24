"""
Read PFMEA-style workbooks and extract station structure.

A PFMEA file layout (as understood by this tool):

    Rows 1 .. header_rows              -> Header (company/product/column titles)
    Rows header_rows+1 .. footer_start -> Data rows (one or more stations)
    Rows footer_start .. end           -> Footer (signatures, distribution)

For every "station block" the first row has an OPC code in column A and
a station name in column B (often A/B are merged across the whole block).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple
import openpyxl
from openpyxl.utils import get_column_letter

from .config import MergeSettings


@dataclass
class StationBlock:
    """One station inside a source workbook (row range in that workbook)."""
    opc_code: str                       # e.g. "A123"
    name: str                           # e.g. "SMD"
    start_row: int                      # first data row (in source)
    end_row: int                        # last data row (in source, inclusive)
    source_file: str = ""               # source workbook path
    order_index: int = 0                # order inside its source file

    @property
    def row_count(self) -> int:
        return self.end_row - self.start_row + 1

    @property
    def display_label(self) -> str:
        code = str(self.opc_code) if self.opc_code is not None else ""
        return f"{code} - {self.name}".strip(" -")


@dataclass
class WorkbookAnalysis:
    """Result of analysing a single input workbook."""
    path: str
    sheet_name: str
    stations: List[StationBlock] = field(default_factory=list)
    footer_start_row: Optional[int] = None
    product_name: str = ""
    product_code: str = ""
    is_valid: bool = True
    error: str = ""


# ---------------------------------------------------------------------------

def _cell_str(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _find_footer_start(ws, settings: MergeSettings) -> Optional[int]:
    """
    Look for the first row (scanning columns 1..scan_cols) that contains
    any of the footer marker keywords. That row (and everything below it)
    is considered footer.
    """
    markers = [m.strip() for m in settings.footer_markers if m and m.strip()]
    if not markers:
        return None
    scan_cols = min(ws.max_column, 15)
    for row in range(settings.data_start_row, ws.max_row + 1):
        for col in range(1, scan_cols + 1):
            val = _cell_str(ws.cell(row=row, column=col).value)
            if not val:
                continue
            for marker in markers:
                if marker in val:
                    return row
    return None


def _find_stations(ws, settings: MergeSettings, data_end_row: int) -> List[StationBlock]:
    """
    Walk the OPC column between data_start_row and data_end_row and build
    StationBlock objects. A new station begins whenever a non-empty OPC
    code appears in column A; the block ends just before the next code
    (or at data_end_row).
    """
    opc_col = settings.opc_column
    name_col = settings.name_column

    # Collect all rows where an OPC code is set. We treat a cell as an OPC
    # code only if it is short (real codes are usually <=6 chars) and does
    # not contain whitespace / newlines / colons — that filters out footer
    # rows that happen to spill into column A (e.g. legend text).
    max_len = getattr(settings, "max_opc_length", 20)
    starts: List[Tuple[int, str, str]] = []
    for row in range(settings.data_start_row, data_end_row + 1):
        opc = _cell_str(ws.cell(row=row, column=opc_col).value)
        if not opc:
            continue
        if len(opc) > max_len:
            continue
        if any(ch in opc for ch in ("\n", "\r", ":")):
            continue
        # allow at most one internal space (rare); reject long multi-word text
        if opc.count(" ") > 1:
            continue
        name = _cell_str(ws.cell(row=row, column=name_col).value)
        starts.append((row, opc, name))

    stations: List[StationBlock] = []
    for i, (start_row, opc, name) in enumerate(starts):
        end_row = (starts[i + 1][0] - 1) if i + 1 < len(starts) else data_end_row
        stations.append(StationBlock(
            opc_code=opc,
            name=name,
            start_row=start_row,
            end_row=end_row,
            order_index=i,
        ))
    return stations


def _extract_product_info(ws) -> Tuple[str, str]:
    """Best-effort extraction of product name/code from the header rows."""
    product_name = ""
    product_code = ""
    for row in range(1, 10):
        for col in range(1, min(ws.max_column, 30) + 1):
            val = _cell_str(ws.cell(row=row, column=col).value)
            if not val:
                continue
            # نام قطعه: SBM SOREN ...
            if "نام قطعه" in val:
                after = val.split(":", 1)[-1].strip()
                if after:
                    product_name = after
            elif "شماره فنی" in val:
                after = val.split(":", 1)[-1].strip()
                if after:
                    product_code = after
    return product_name, product_code


def analyze_workbook(path: str | Path, settings: MergeSettings) -> WorkbookAnalysis:
    """Open a workbook and figure out its stations, footer, product info."""
    path = str(path)
    try:
        wb = openpyxl.load_workbook(path, data_only=True, read_only=False)
    except Exception as e:
        return WorkbookAnalysis(
            path=path, sheet_name="", is_valid=False,
            error=f"cannot open: {e}",
        )

    # Find the target sheet (case-insensitive fallback)
    sheet_name = settings.sheet_name
    if sheet_name not in wb.sheetnames:
        # Try to find a sheet whose stripped/lowered name matches
        lower = sheet_name.strip().lower()
        for name in wb.sheetnames:
            if name.strip().lower() == lower:
                sheet_name = name
                break
        else:
            wb.close()
            return WorkbookAnalysis(
                path=path, sheet_name="", is_valid=False,
                error=f"sheet '{settings.sheet_name}' not found",
            )
    ws = wb[sheet_name]

    footer_start = _find_footer_start(ws, settings)
    data_end = (footer_start - 1) if footer_start else ws.max_row
    stations = _find_stations(ws, settings, data_end)
    for s in stations:
        s.source_file = path
    product_name, product_code = _extract_product_info(ws)

    analysis = WorkbookAnalysis(
        path=path,
        sheet_name=sheet_name,
        stations=stations,
        footer_start_row=footer_start,
        product_name=product_name,
        product_code=product_code,
        is_valid=len(stations) > 0,
        error="" if stations else "no stations detected",
    )
    wb.close()
    return analysis
