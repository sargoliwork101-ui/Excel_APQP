"""
Merge station blocks from several PFMEA workbooks into a single output
workbook that preserves the template's formatting (styles, merged cells,
column widths, row heights, images-not-supported-here).

The output layout is:

    [ template header rows           ]  (once, copied from template)
    [ station 1 data rows            ]  (copied from source file 1)
    [ station 2 data rows            ]  (copied from source file 2)
    ...
    [ template footer rows           ]  (once, copied from template)

The History sheet, if present in template, is copied as-is; extra history
rows from source files are appended.
"""
from __future__ import annotations

from copy import copy
from pathlib import Path
from typing import Iterable, List, Optional, Tuple
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from .config import MergeSettings
from .excel_reader import StationBlock, WorkbookAnalysis, analyze_workbook


# ---------------------------------------------------------------------------
# helpers to copy formatting

def _copy_cell(src_cell, dst_cell) -> None:
    """Copy value + style + hyperlink + comment from src to dst."""
    dst_cell.value = src_cell.value
    if src_cell.has_style:
        dst_cell.font = copy(src_cell.font)
        dst_cell.fill = copy(src_cell.fill)
        dst_cell.border = copy(src_cell.border)
        dst_cell.alignment = copy(src_cell.alignment)
        dst_cell.number_format = src_cell.number_format
        dst_cell.protection = copy(src_cell.protection)
    if src_cell.hyperlink:
        try:
            dst_cell.hyperlink = copy(src_cell.hyperlink)
        except Exception:
            pass
    if src_cell.comment:
        try:
            dst_cell.comment = copy(src_cell.comment)
        except Exception:
            pass


def _copy_column_dims(src_ws: Worksheet, dst_ws: Worksheet, max_col: int) -> None:
    """Copy column widths / hidden / outline once (idempotent)."""
    for col_idx in range(1, max_col + 1):
        letter = get_column_letter(col_idx)
        src_dim = src_ws.column_dimensions.get(letter)
        if src_dim is None:
            continue
        dst_dim = dst_ws.column_dimensions[letter]
        if src_dim.width is not None:
            dst_dim.width = src_dim.width
        dst_dim.hidden = src_dim.hidden
        if src_dim.outlineLevel:
            dst_dim.outlineLevel = src_dim.outlineLevel
        if src_dim.bestFit:
            dst_dim.bestFit = src_dim.bestFit


def _copy_row_range(
    src_ws: Worksheet,
    dst_ws: Worksheet,
    src_start: int,
    src_end: int,
    dst_start: int,
    max_col: int,
) -> int:
    """
    Copy rows [src_start..src_end] from src_ws to dst_ws starting at
    dst_start. Copies values, styles, merged cells (relative), and row
    heights. Returns the number of rows copied.
    """
    row_count = src_end - src_start + 1
    offset = dst_start - src_start

    # cells
    for r in range(src_start, src_end + 1):
        dst_row = r + offset
        # row height
        src_row_dim = src_ws.row_dimensions.get(r)
        if src_row_dim is not None and src_row_dim.height is not None:
            dst_ws.row_dimensions[dst_row].height = src_row_dim.height
        for c in range(1, max_col + 1):
            src_cell = src_ws.cell(row=r, column=c)
            dst_cell = dst_ws.cell(row=dst_row, column=c)
            _copy_cell(src_cell, dst_cell)

    # merged cells that fall completely inside the copied range
    for mr in list(src_ws.merged_cells.ranges):
        if mr.min_row >= src_start and mr.max_row <= src_end \
                and mr.min_col <= max_col:
            new_min_row = mr.min_row + offset
            new_max_row = mr.max_row + offset
            new_max_col = min(mr.max_col, max_col)
            new_range = (
                f"{get_column_letter(mr.min_col)}{new_min_row}:"
                f"{get_column_letter(new_max_col)}{new_max_row}"
            )
            try:
                dst_ws.merge_cells(new_range)
            except Exception:
                pass

    return row_count


def _copy_sheet_settings(src_ws: Worksheet, dst_ws: Worksheet) -> None:
    """Copy sheet-level formatting (page setup, freeze pane, RTL, print area)."""
    try:
        dst_ws.sheet_view.rightToLeft = src_ws.sheet_view.rightToLeft
    except Exception:
        pass
    try:
        dst_ws.freeze_panes = src_ws.freeze_panes
    except Exception:
        pass
    try:
        dst_ws.page_setup = copy(src_ws.page_setup)
        dst_ws.page_margins = copy(src_ws.page_margins)
        dst_ws.print_options = copy(src_ws.print_options)
        dst_ws.sheet_properties = copy(src_ws.sheet_properties)
        dst_ws.print_title_rows = src_ws.print_title_rows
        dst_ws.print_title_cols = src_ws.print_title_cols
    except Exception:
        pass


# ---------------------------------------------------------------------------
# public API

def merge_pfmea(
    template_path: str | Path,
    station_selections: List[Tuple[str, StationBlock]],
    output_path: str | Path,
    settings: MergeSettings,
    merge_history: bool = True,
    progress_cb=None,
) -> str:
    """
    Build the output workbook.

    station_selections is an ordered list of (source_file_path, StationBlock)
    tuples chosen by the user (already sorted in the desired order).
    """
    template_path = str(template_path)
    output_path = str(output_path)

    def report(pct: int, msg: str = ""):
        if progress_cb:
            try:
                progress_cb(pct, msg)
            except Exception:
                pass

    report(1, "Loading template...")
    template_wb = openpyxl.load_workbook(template_path)

    # find target sheet in template
    tpl_sheet_name = settings.sheet_name
    if tpl_sheet_name not in template_wb.sheetnames:
        raise ValueError(f"Template does not contain sheet '{tpl_sheet_name}'")
    tpl_ws = template_wb[tpl_sheet_name]

    # figure out template metadata using the reader
    tpl_analysis = analyze_workbook(template_path, settings)
    tpl_footer_start = tpl_analysis.footer_start_row  # may be None
    tpl_data_start = settings.data_start_row
    tpl_footer_end = _last_non_empty_row(tpl_ws)
    max_col = tpl_ws.max_column

    # ---- build a fresh output workbook and copy the header --------------
    out_wb = openpyxl.Workbook()
    # remove default sheet, re-create with template sheet name
    default = out_wb.active
    out_wb.remove(default)
    out_ws = out_wb.create_sheet(title=tpl_sheet_name)

    _copy_sheet_settings(tpl_ws, out_ws)
    _copy_column_dims(tpl_ws, out_ws, max_col)

    # copy header rows (1 .. header_rows)
    report(5, "Copying header...")
    header_end = settings.header_rows
    _copy_row_range(tpl_ws, out_ws, 1, header_end, 1, max_col)

    # ---- copy each selected station -------------------------------------
    write_row = header_end + 1
    n = max(1, len(station_selections))
    for i, (src_path, block) in enumerate(station_selections, start=1):
        report(5 + int(80 * i / n),
               f"Merging station {i}/{n}: {block.display_label}")
        src_wb = openpyxl.load_workbook(src_path)
        if block.source_file != src_path or tpl_sheet_name not in src_wb.sheetnames:
            # fall back: find right sheet
            sheet = tpl_sheet_name if tpl_sheet_name in src_wb.sheetnames else src_wb.sheetnames[0]
        else:
            sheet = tpl_sheet_name
        src_ws = src_wb[sheet]

        # copy column widths from the first source file too (idempotent - only
        # widens if the source has wider settings than template). We skip this
        # to keep template widths authoritative.
        rows = _copy_row_range(
            src_ws, out_ws,
            block.start_row, block.end_row,
            write_row, max_col,
        )
        write_row += rows
        src_wb.close()

    # ---- copy footer (if template has one) ------------------------------
    if tpl_footer_start:
        report(88, "Copying footer...")
        _copy_row_range(
            tpl_ws, out_ws,
            tpl_footer_start, tpl_footer_end,
            write_row, max_col,
        )
        write_row += (tpl_footer_end - tpl_footer_start + 1)

    # ---- History sheet --------------------------------------------------
    if merge_history:
        report(92, "Merging history sheet...")
        _merge_history_sheet(
            template_wb, out_wb, settings,
            source_paths=[s[0] for s in station_selections],
        )

    report(97, "Saving output...")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    out_wb.save(output_path)
    template_wb.close()
    out_wb.close()
    report(100, "Done.")
    return output_path


def _merge_history_sheet(
    template_wb,
    out_wb,
    settings: MergeSettings,
    source_paths: Iterable[str],
) -> None:
    """
    Copy the template's history sheet as-is, then append additional history
    rows from every source workbook (rows below the template's history end).
    """
    tpl_hist_name = None
    for name in template_wb.sheetnames:
        if name.strip().lower() == settings.history_sheet.strip().lower():
            tpl_hist_name = name
            break
    if tpl_hist_name is None:
        return

    tpl_ws = template_wb[tpl_hist_name]
    out_ws = out_wb.create_sheet(title=tpl_hist_name)
    max_col = max(tpl_ws.max_column, 3)

    _copy_sheet_settings(tpl_ws, out_ws)
    _copy_column_dims(tpl_ws, out_ws, max_col)

    # copy whole template history sheet
    tpl_rows = tpl_ws.max_row
    _copy_row_range(tpl_ws, out_ws, 1, tpl_rows, 1, max_col)
    write_row = tpl_rows + 1

    # find the first data row in the template's history sheet (the header
    # is usually 1-2 rows; we skip rows that already exist in template).
    # For each source, append rows that are not blank and not already in
    # template.
    seen_signatures = set()
    for r in range(1, tpl_rows + 1):
        sig = tuple(_cell_value_str(tpl_ws.cell(row=r, column=c).value) for c in range(1, max_col + 1))
        if any(sig):
            seen_signatures.add(sig)

    for path in source_paths:
        try:
            wb = openpyxl.load_workbook(path)
        except Exception:
            continue
        hist_name = None
        for name in wb.sheetnames:
            if name.strip().lower() == settings.history_sheet.strip().lower():
                hist_name = name
                break
        if hist_name is None:
            wb.close()
            continue
        src_ws = wb[hist_name]
        src_max_col = max(src_ws.max_column, 3)
        for r in range(1, src_ws.max_row + 1):
            sig = tuple(
                _cell_value_str(src_ws.cell(row=r, column=c).value)
                for c in range(1, min(max_col, src_max_col) + 1)
            )
            if not any(sig):
                continue
            if sig in seen_signatures:
                continue
            seen_signatures.add(sig)
            # copy row
            for c in range(1, min(max_col, src_max_col) + 1):
                _copy_cell(src_ws.cell(row=r, column=c),
                           out_ws.cell(row=write_row, column=c))
            src_row_dim = src_ws.row_dimensions.get(r)
            if src_row_dim is not None and src_row_dim.height is not None:
                out_ws.row_dimensions[write_row].height = src_row_dim.height
            write_row += 1
        wb.close()


def _cell_value_str(v) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _last_non_empty_row(ws: Worksheet) -> int:
    """Return the row number of the last cell that actually holds a value."""
    last = 0
    max_col = ws.max_column
    for r in range(ws.max_row, 0, -1):
        for c in range(1, max_col + 1):
            if ws.cell(row=r, column=c).value is not None:
                last = r
                break
        if last:
            break
    return last or ws.max_row
