"""
Merge station blocks from several PFMEA workbooks into a single output
workbook that preserves the template's formatting (styles, merged cells,
column widths, row heights).

Output layout:

    [ template header rows           ]  (once, copied from template)
    [ station 1 data rows            ]  (copied from source file 1)
    [ station 2 data rows            ]  (copied from source file 2)
    ...
    [ template footer rows           ]  (once, copied from template)

The History sheet is copied verbatim from the template (never fabricated).
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
    """Copy value + style + hyperlink from src to dst."""
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
    # Comments on merged cells break the file, so skip them.


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

    Merged cells that overlap the range are clipped to it. Any part of a
    merged range that falls outside the copied rows is dropped (this is
    what you want: it means the destination merge only covers the rows
    we actually kept).
    """
    row_count = src_end - src_start + 1
    offset = dst_start - src_start

    # cells + row heights
    for r in range(src_start, src_end + 1):
        dst_row = r + offset
        src_row_dim = src_ws.row_dimensions.get(r)
        if src_row_dim is not None:
            dst_row_dim = dst_ws.row_dimensions[dst_row]
            if src_row_dim.height is not None:
                dst_row_dim.height = src_row_dim.height
            if src_row_dim.hidden:
                dst_row_dim.hidden = True
            if src_row_dim.outlineLevel:
                dst_row_dim.outlineLevel = src_row_dim.outlineLevel
        for c in range(1, max_col + 1):
            _copy_cell(src_ws.cell(row=r, column=c),
                       dst_ws.cell(row=dst_row, column=c))

    # merged cells: keep any range whose bounds overlap [src_start..src_end]
    # and clip them into the destination range.
    for mr in list(src_ws.merged_cells.ranges):
        if mr.max_row < src_start or mr.min_row > src_end:
            continue
        if mr.min_col > max_col:
            continue
        clip_min_row = max(mr.min_row, src_start) + offset
        clip_max_row = min(mr.max_row, src_end) + offset
        clip_min_col = mr.min_col
        clip_max_col = min(mr.max_col, max_col)
        if clip_min_row > clip_max_row or clip_min_col > clip_max_col:
            continue
        if clip_min_row == clip_max_row and clip_min_col == clip_max_col:
            # single-cell "merge" is not useful; skip
            continue
        new_range = (
            f"{get_column_letter(clip_min_col)}{clip_min_row}:"
            f"{get_column_letter(clip_max_col)}{clip_max_row}"
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
        dst_ws.sheet_view.showGridLines = src_ws.sheet_view.showGridLines
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


def _copy_whole_sheet(src_ws: Worksheet, dst_ws: Worksheet) -> None:
    """Copy an entire worksheet 1:1 into dst_ws (which must be empty)."""
    max_col = src_ws.max_column
    last_row = _last_non_empty_row(src_ws) or src_ws.max_row
    _copy_sheet_settings(src_ws, dst_ws)
    _copy_column_dims(src_ws, dst_ws, max_col)
    _copy_row_range(src_ws, dst_ws, 1, last_row, 1, max_col)


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
    Build the output workbook from a template + selected station blocks.
    station_selections is an ordered list of (source_file_path, StationBlock).
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

    tpl_sheet_name = settings.sheet_name
    if tpl_sheet_name not in template_wb.sheetnames:
        raise ValueError(f"Template does not contain sheet '{tpl_sheet_name}'")
    tpl_ws = template_wb[tpl_sheet_name]

    tpl_analysis = analyze_workbook(template_path, settings)
    tpl_footer_start = tpl_analysis.footer_start_row
    tpl_footer_end = _last_non_empty_row(tpl_ws)
    max_col = tpl_ws.max_column

    # ---- build the output workbook and copy header ------------------------
    out_wb = openpyxl.Workbook()
    out_wb.remove(out_wb.active)
    out_ws = out_wb.create_sheet(title=tpl_sheet_name)

    _copy_sheet_settings(tpl_ws, out_ws)
    _copy_column_dims(tpl_ws, out_ws, max_col)

    report(5, "Copying header...")
    _copy_row_range(tpl_ws, out_ws, 1, settings.header_rows, 1, max_col)

    # ---- copy each selected station ---------------------------------------
    write_row = settings.header_rows + 1
    n = max(1, len(station_selections))
    src_cache: dict[str, openpyxl.Workbook] = {}
    for i, (src_path, block) in enumerate(station_selections, start=1):
        report(5 + int(80 * i / n),
               f"Merging station {i}/{n}: {block.display_label}")
        if src_path not in src_cache:
            src_cache[src_path] = openpyxl.load_workbook(src_path)
        src_wb = src_cache[src_path]
        sheet = tpl_sheet_name if tpl_sheet_name in src_wb.sheetnames \
            else src_wb.sheetnames[0]
        src_ws = src_wb[sheet]
        rows = _copy_row_range(
            src_ws, out_ws,
            block.start_row, block.end_row,
            write_row, max_col,
        )
        write_row += rows

    for wb in src_cache.values():
        wb.close()

    # ---- copy footer ------------------------------------------------------
    if tpl_footer_start:
        report(88, "Copying footer...")
        _copy_row_range(
            tpl_ws, out_ws,
            tpl_footer_start, tpl_footer_end,
            write_row, max_col,
        )

    # ---- History sheet ---------------------------------------------------
    # We copy it VERBATIM from the template (never fabricate or "merge" it
    # from every source file — that produced noisy duplicates before).
    if merge_history:
        report(92, "Copying history sheet from template...")
        _copy_template_history(template_wb, out_wb, settings)

    report(97, "Saving output...")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    out_wb.save(output_path)
    template_wb.close()
    out_wb.close()
    report(100, "Done.")
    return output_path


def _copy_template_history(template_wb, out_wb, settings: MergeSettings) -> None:
    """Copy the template's History sheet verbatim, if one exists."""
    tpl_hist_name = None
    for name in template_wb.sheetnames:
        if name.strip().lower() == settings.history_sheet.strip().lower():
            tpl_hist_name = name
            break
    if tpl_hist_name is None:
        return
    src_ws = template_wb[tpl_hist_name]
    dst_ws = out_wb.create_sheet(title=tpl_hist_name)
    _copy_whole_sheet(src_ws, dst_ws)
