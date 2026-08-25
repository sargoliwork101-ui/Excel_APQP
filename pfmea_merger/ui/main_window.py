"""
Main window for the PFMEA Merger app (dark themed).
"""
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PyQt6 import QtCore, QtGui, QtWidgets

from ..core.config import AppSettings, MergeSettings, TEMPLATES_DIR, OUTPUT_DIR
from ..core.i18n import Translator
from ..core.excel_reader import StationBlock, WorkbookAnalysis, analyze_workbook
from ..core.excel_merger import merge_pfmea
from ..core import profile_manager as pm
from .settings_dialog import SettingsDialog


# =============================================================================
# Background worker
# =============================================================================
class MergeWorker(QtCore.QThread):
    progress = QtCore.pyqtSignal(int, str)
    finished_ok = QtCore.pyqtSignal(str)
    failed = QtCore.pyqtSignal(str)

    def __init__(self, template, selections, output, settings, merge_history):
        super().__init__()
        self.template = template
        self.selections = selections
        self.output = output
        self.settings = settings
        self.merge_history = merge_history

    def run(self):
        try:
            def cb(pct, msg):
                self.progress.emit(pct, msg)
            out = merge_pfmea(
                self.template, self.selections, self.output,
                self.settings, merge_history=self.merge_history,
                progress_cb=cb,
            )
            self.finished_ok.emit(out)
        except Exception as e:
            self.failed.emit(f"{e}\n\n{traceback.format_exc()}")


# =============================================================================
# Small helpers
# =============================================================================
def _make_card() -> QtWidgets.QFrame:
    f = QtWidgets.QFrame()
    f.setObjectName("Card")
    # A subtle shadow separates cards from the navy background and gives the
    # interface a modern layered look without adding heavy visual noise.
    shadow = QtWidgets.QGraphicsDropShadowEffect(f)
    shadow.setBlurRadius(22)
    shadow.setOffset(0, 5)
    shadow.setColor(QtGui.QColor(0, 0, 0, 80))
    f.setGraphicsEffect(shadow)
    return f


# =============================================================================
# Row model: keeps checkbox state in Python so profile save/load is trivial
# =============================================================================
class Row:
    __slots__ = ("path", "block", "enabled")

    def __init__(self, path: str, block: StationBlock, enabled: bool = True):
        self.path = path
        self.block = block
        self.enabled = enabled


# =============================================================================
# Main window
# =============================================================================
class MainWindow(QtWidgets.QMainWindow):
    COL_USE, COL_ORDER, COL_OPC, COL_NAME, COL_ROWS, COL_FILE = range(6)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.app_settings = AppSettings.load()
        self.merge_settings = MergeSettings()
        self.tr_ = Translator(self.app_settings.language)

        # file_path -> WorkbookAnalysis (for product info, etc.)
        self.workbooks: Dict[str, WorkbookAnalysis] = {}
        # Ordered list of station rows shown in the table (source of truth)
        self.rows: List[Row] = []
        # Suppresses recursion when we programmatically flip checkboxes
        self._suspend_checks = False

        self._worker: Optional[MergeWorker] = None
        self._last_output: str = ""

        self._build_ui()
        self._apply_language()
        self._restore_last()
        self._reload_profile_combo()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        self.setWindowTitle("PFMEA Merger")
        self.resize(1180, 780)
        self.setMinimumSize(1000, 640)

        cw = QtWidgets.QWidget()
        self.setCentralWidget(cw)
        root = QtWidgets.QVBoxLayout(cw)
        root.setSpacing(12)
        root.setContentsMargins(16, 14, 16, 12)

        # ---- Title bar
        title_bar = QtWidgets.QHBoxLayout()
        title_col = QtWidgets.QVBoxLayout()
        title_col.setSpacing(2)
        self.title_label = QtWidgets.QLabel()
        self.title_label.setObjectName("AppTitle")
        f = self.title_label.font(); f.setPointSize(17); f.setBold(True)
        self.title_label.setFont(f)
        self.subtitle_label = QtWidgets.QLabel()
        self.subtitle_label.setProperty("muted", True)
        title_col.addWidget(self.title_label)
        title_col.addWidget(self.subtitle_label)
        title_bar.addLayout(title_col, 1)

        self.lang_btn = QtWidgets.QPushButton()
        self.lang_btn.setFixedHeight(36)
        self.lang_btn.setToolTip("Toggle Language / تغییر زبان")
        self.lang_btn.clicked.connect(self._toggle_language)

        self.settings_btn = QtWidgets.QPushButton("⚙")
        self.settings_btn.setFixedSize(38, 38)
        f = self.settings_btn.font(); f.setPointSize(14); self.settings_btn.setFont(f)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self._open_settings)

        title_bar.addWidget(self.lang_btn, 0, QtCore.Qt.AlignmentFlag.AlignTop)
        title_bar.addWidget(self.settings_btn, 0, QtCore.Qt.AlignmentFlag.AlignTop)
        root.addLayout(title_bar)

        # ---- Card 1: template + profile
        card1 = _make_card()
        c1 = QtWidgets.QGridLayout(card1)
        c1.setContentsMargins(14, 12, 14, 12)
        c1.setHorizontalSpacing(10)
        c1.setVerticalSpacing(8)

        self.template_label = QtWidgets.QLabel()
        self.template_edit = QtWidgets.QLineEdit()
        self.template_edit.setReadOnly(True)
        self.template_browse_btn = QtWidgets.QPushButton()
        self.template_browse_btn.clicked.connect(self._pick_template)

        self.profile_label = QtWidgets.QLabel()
        self.profile_combo = QtWidgets.QComboBox()
        self.profile_combo.setMinimumWidth(180)
        self.profile_combo.currentIndexChanged.connect(self._on_profile_changed)
        self.profile_load_btn = QtWidgets.QPushButton()
        self.profile_save_btn = QtWidgets.QPushButton()
        self.profile_delete_btn = QtWidgets.QPushButton()
        self.profile_delete_btn.setProperty("danger", True)
        self.profile_load_btn.clicked.connect(self._on_load_profile)
        self.profile_save_btn.clicked.connect(self._on_save_profile)
        self.profile_delete_btn.clicked.connect(self._on_delete_profile)

        c1.addWidget(self.template_label,       0, 0)
        c1.addWidget(self.template_edit,        0, 1, 1, 4)
        c1.addWidget(self.template_browse_btn,  0, 5)
        c1.addWidget(self.profile_label,        1, 0)
        c1.addWidget(self.profile_combo,        1, 1, 1, 2)
        c1.addWidget(self.profile_load_btn,     1, 3)
        c1.addWidget(self.profile_save_btn,     1, 4)
        c1.addWidget(self.profile_delete_btn,   1, 5)
        c1.setColumnStretch(1, 1)
        c1.setColumnStretch(2, 1)
        root.addWidget(card1)

        # ---- Card 2: files toolbar + station table
        card2 = _make_card()
        c2 = QtWidgets.QVBoxLayout(card2)
        c2.setContentsMargins(14, 12, 14, 12)
        c2.setSpacing(10)

        toolbar = QtWidgets.QHBoxLayout()
        self.add_files_btn = QtWidgets.QPushButton()
        self.add_folder_btn = QtWidgets.QPushButton()
        self.refresh_btn = QtWidgets.QPushButton()
        self.remove_btn = QtWidgets.QPushButton()
        self.clear_btn = QtWidgets.QPushButton()
        self.clear_btn.setProperty("danger", True)
        self.add_files_btn.clicked.connect(self._add_files)
        self.add_folder_btn.clicked.connect(self._add_folder)
        self.refresh_btn.clicked.connect(self._refresh_all)
        self.remove_btn.clicked.connect(self._remove_selected)
        self.clear_btn.clicked.connect(self._clear_all)
        toolbar.addWidget(self.add_files_btn)
        toolbar.addWidget(self.add_folder_btn)
        toolbar.addWidget(self.refresh_btn)
        toolbar.addStretch(1)
        toolbar.addWidget(self.remove_btn)
        toolbar.addWidget(self.clear_btn)
        c2.addLayout(toolbar)

        self.hint_label = QtWidgets.QLabel()
        self.hint_label.setProperty("muted", True)
        c2.addWidget(self.hint_label)

        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setSelectionBehavior(
            QtWidgets.QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(
            QtWidgets.QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(
            QtWidgets.QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionsClickable(False)
        self.table.setColumnWidth(self.COL_USE,   58)
        self.table.setColumnWidth(self.COL_ORDER, 60)
        self.table.setColumnWidth(self.COL_OPC,   90)
        self.table.setColumnWidth(self.COL_NAME,  280)
        self.table.setColumnWidth(self.COL_ROWS,  75)
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.itemChanged.connect(self._on_table_item_changed)
        # The whole USE cell is clickable (not only the native checkbox).
        self.table.cellClicked.connect(self._on_use_cell_clicked)
        # Double-clicking the file column opens that input workbook.
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        # Right-click context menu
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        # Delete key removes selected
        del_action = QtGui.QAction(self)
        del_action.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Delete))
        del_action.triggered.connect(self._remove_selected)
        self.table.addAction(del_action)
        # Space toggles check
        space_action = QtGui.QAction(self)
        space_action.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Space))
        space_action.triggered.connect(self._toggle_selected)
        self.table.addAction(space_action)
        c2.addWidget(self.table, 1)

        row3 = QtWidgets.QHBoxLayout()
        self.select_all_btn = QtWidgets.QPushButton()
        self.deselect_all_btn = QtWidgets.QPushButton()
        self.invert_btn = QtWidgets.QPushButton()
        self.up_btn = QtWidgets.QPushButton("⬆")
        self.down_btn = QtWidgets.QPushButton("⬇")
        self.top_btn = QtWidgets.QPushButton("⏫")
        self.bottom_btn = QtWidgets.QPushButton("⏬")
        for b in (self.up_btn, self.down_btn, self.top_btn, self.bottom_btn):
            b.setFixedWidth(44)
        self.select_all_btn.clicked.connect(lambda: self._set_all(True))
        self.deselect_all_btn.clicked.connect(lambda: self._set_all(False))
        self.invert_btn.clicked.connect(self._invert_selection)
        self.up_btn.clicked.connect(lambda: self._move_row(-1))
        self.down_btn.clicked.connect(lambda: self._move_row(+1))
        self.top_btn.clicked.connect(self._move_top)
        self.bottom_btn.clicked.connect(self._move_bottom)
        row3.addWidget(self.select_all_btn)
        row3.addWidget(self.deselect_all_btn)
        row3.addWidget(self.invert_btn)
        row3.addStretch(1)
        self.count_label = QtWidgets.QLabel()
        self.count_label.setProperty("muted", True)
        row3.addWidget(self.count_label)
        row3.addSpacing(20)
        row3.addWidget(self.top_btn)
        row3.addWidget(self.up_btn)
        row3.addWidget(self.down_btn)
        row3.addWidget(self.bottom_btn)
        c2.addLayout(row3)
        root.addWidget(card2, 1)

        # ---- Card 3: output + merge
        card3 = _make_card()
        c3 = QtWidgets.QGridLayout(card3)
        c3.setContentsMargins(14, 12, 14, 12)
        c3.setHorizontalSpacing(10)
        c3.setVerticalSpacing(8)

        self.output_label = QtWidgets.QLabel()
        self.output_edit = QtWidgets.QLineEdit()
        self.output_browse_btn = QtWidgets.QPushButton()
        self.output_browse_btn.clicked.connect(self._pick_output)
        self.history_chk = QtWidgets.QCheckBox()
        self.history_chk.setChecked(True)
        self.open_after_chk = QtWidgets.QCheckBox()
        self.open_after_chk.setChecked(True)

        self.merge_btn = QtWidgets.QPushButton()
        self.merge_btn.setMinimumHeight(42)
        self.merge_btn.setProperty("primary", True)
        f = self.merge_btn.font(); f.setPointSize(11); f.setBold(True); self.merge_btn.setFont(f)
        self.merge_btn.clicked.connect(self._do_merge)

        self.open_output_btn = QtWidgets.QPushButton()
        self.open_output_btn.setEnabled(False)
        self.open_output_btn.clicked.connect(self._open_last_output)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setValue(0)
        self.progress.setTextVisible(True)

        c3.addWidget(self.output_label,        0, 0)
        c3.addWidget(self.output_edit,         0, 1, 1, 3)
        c3.addWidget(self.output_browse_btn,   0, 4)
        opts_row = QtWidgets.QHBoxLayout()
        opts_row.addWidget(self.history_chk)
        opts_row.addSpacing(20)
        opts_row.addWidget(self.open_after_chk)
        opts_row.addStretch(1)
        c3.addLayout(opts_row,                 1, 0, 1, 5)
        c3.addWidget(self.merge_btn,           2, 0, 1, 2)
        c3.addWidget(self.progress,            2, 2, 1, 2)
        c3.addWidget(self.open_output_btn,     2, 4)
        c3.setColumnStretch(1, 1)
        c3.setColumnStretch(2, 1)
        root.addWidget(card3)

        self.status = self.statusBar()

    # -------------------------------------------------- translation apply
    def _apply_language(self):
        t = self.tr_.t
        self.setWindowTitle(t("app_title"))
        self.setLayoutDirection(
            QtCore.Qt.LayoutDirection.RightToLeft if self.tr_.is_rtl()
            else QtCore.Qt.LayoutDirection.LeftToRight
        )
        self.title_label.setText(t("app_title"))
        self.subtitle_label.setText(
            "قالب PFMEA + فایل‌های ایستگاه ← یک خروجی تجمیعی"
            if self.tr_.is_rtl()
            else "PFMEA template + station files → one merged output"
        )
        self.lang_btn.setText("🌐 " + ("EN" if self.tr_.is_rtl() else "فا"))
        self.template_label.setText(t("template_label"))
        self.template_browse_btn.setText("📂 " + t("browse"))
        self.profile_label.setText(t("profile_label"))
        self.profile_load_btn.setText("↩ " + t("load_profile"))
        self.profile_save_btn.setText("💾 " + t("save_profile"))
        self.profile_delete_btn.setText("🗑 " + t("delete_profile"))
        self.add_files_btn.setText("📄 " + t("add_files"))
        self.add_folder_btn.setText("📁 " + t("add_folder"))
        self.refresh_btn.setText("🔄 " + t("refresh"))
        self.remove_btn.setText("➖ " + t("remove_selected"))
        self.clear_btn.setText("🗑 " + t("clear"))
        self.hint_label.setText(t("stations_hint"))
        self.select_all_btn.setText("☑ " + t("select_all"))
        self.deselect_all_btn.setText("☐ " + t("deselect_all"))
        self.invert_btn.setText("↔ " + t("invert"))
        self.output_label.setText(t("output_label"))
        self.output_browse_btn.setText("📂 " + t("browse"))
        self.history_chk.setText(t("include_history"))
        self.open_after_chk.setText(t("open_after"))
        self.merge_btn.setText(t("merge_button"))
        self.open_output_btn.setText("📂 " + t("open_output"))
        self.table.setHorizontalHeaderLabels([
            t("col_use"), t("col_order"), t("col_opc"),
            t("col_name"), t("col_rows"), t("col_file"),
        ])
        self.up_btn.setToolTip(t("move_up"))
        self.down_btn.setToolTip(t("move_down"))
        self.top_btn.setToolTip(t("move_top"))
        self.bottom_btn.setToolTip(t("move_bottom"))
        self._update_counts()
        self.status.showMessage("● " + t("ready"))

    def _toggle_language(self):
        self.app_settings.language = "en" if self.tr_.is_rtl() else "fa"
        self.tr_.set_lang(self.app_settings.language)
        self.app_settings.save()
        self._apply_language()

    # ------------------------------------------------------- persistence
    def _restore_last(self):
        if self.app_settings.last_template and Path(self.app_settings.last_template).exists():
            self.template_edit.setText(self.app_settings.last_template)
        else:
            for p in sorted(TEMPLATES_DIR.glob("*.xlsx")):
                self.template_edit.setText(str(p))
                break
        default_out = OUTPUT_DIR / "Merged_PFMEA.xlsx"
        if self.app_settings.last_output_dir:
            candidate = Path(self.app_settings.last_output_dir) / "Merged_PFMEA.xlsx"
            self.output_edit.setText(str(candidate))
        else:
            self.output_edit.setText(str(default_out))

    def _save_last(self):
        self.app_settings.last_template = self.template_edit.text()
        p = self.output_edit.text().strip()
        if p:
            self.app_settings.last_output_dir = str(Path(p).parent)
        self.app_settings.save()

    # ---------------------------------------------------- template pick
    def _pick_template(self):
        start = self.template_edit.text() or str(TEMPLATES_DIR)
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, self.tr_.t("template_label"),
            start,
            f"{self.tr_.t('excel_files')} (*.xlsx *.xlsm)",
        )
        if path:
            self.template_edit.setText(path)
            self._save_last()

    def _pick_output(self):
        start = self.output_edit.text() or str(OUTPUT_DIR / "Merged_PFMEA.xlsx")
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, self.tr_.t("output_label"),
            start,
            f"{self.tr_.t('excel_files')} (*.xlsx)",
        )
        if path:
            if not path.lower().endswith(".xlsx"):
                path += ".xlsx"
            self.output_edit.setText(path)
            self._save_last()

    # ---------------------------------------------------- add files/folder
    def _add_files(self):
        start = self.app_settings.last_input_dir or str(Path.home())
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, self.tr_.t("add_files"), start,
            f"{self.tr_.t('excel_files')} (*.xlsx *.xlsm)",
        )
        if paths:
            self.app_settings.last_input_dir = str(Path(paths[0]).parent)
            self.app_settings.save()
            self._add_paths(paths)

    def _add_folder(self):
        start = self.app_settings.last_input_dir or str(Path.home())
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, self.tr_.t("add_folder"), start,
        )
        if folder:
            self.app_settings.last_input_dir = folder
            self.app_settings.save()
            paths = sorted(str(p) for p in Path(folder).glob("*.xlsx")
                           if not p.name.startswith("~$"))
            if not paths:
                QtWidgets.QMessageBox.information(
                    self, self.tr_.t("info"),
                    self.tr_.t("no_xlsx_in_folder"),
                )
                return
            self._add_paths(paths)

    def _add_paths(self, paths: List[str]):
        """
        Read each file, extract stations, append them to self.rows. Skip
        paths already present. If a profile is loaded, reapply its order
        and check state to newly-loaded rows too.
        """
        skipped: List[str] = []
        added_count = 0
        station_count = 0
        for p in paths:
            if p in self.workbooks:
                continue
            analysis = analyze_workbook(p, self.merge_settings)
            if not analysis.is_valid:
                skipped.append(f"{Path(p).name}: {analysis.error}")
                continue
            self.workbooks[p] = analysis
            for block in analysis.stations:
                self.rows.append(Row(p, block, enabled=True))
                station_count += 1
            added_count += 1

        # If a profile is currently selected, apply its order + checks
        profile_name = self.profile_combo.currentText().strip()
        if profile_name:
            profile = pm.load_profile(profile_name)
            if profile and profile.stations:
                self._apply_profile_to_rows(profile)

        self._rebuild_table()
        if skipped:
            QtWidgets.QMessageBox.warning(
                self, self.tr_.t("warning"),
                "\n".join(self.tr_.t("file_not_pfmea", name=n) for n in skipped),
            )
        self.status.showMessage("● " + self.tr_.t(
            "loaded_files", n=added_count, s=station_count))

    def _refresh_all(self):
        paths = list(self.workbooks.keys())
        # remember enabled state per (path, opc) so refresh keeps checks
        prev_enabled = {(r.path, r.block.opc_code): r.enabled for r in self.rows}
        self.workbooks.clear()
        self.rows.clear()
        if not paths:
            self._rebuild_table()
            return
        for p in paths:
            analysis = analyze_workbook(p, self.merge_settings)
            if not analysis.is_valid:
                continue
            self.workbooks[p] = analysis
            for block in analysis.stations:
                self.rows.append(Row(
                    p, block,
                    enabled=prev_enabled.get((p, block.opc_code), True),
                ))
        profile_name = self.profile_combo.currentText().strip()
        if profile_name:
            profile = pm.load_profile(profile_name)
            if profile and profile.stations:
                self._apply_profile_to_rows(profile)
        self._rebuild_table()
        self.status.showMessage("● " + self.tr_.t("refreshed"))

    def _clear_all(self):
        if self.rows:
            ans = QtWidgets.QMessageBox.question(
                self, self.tr_.t("confirm"),
                self.tr_.t("clear_confirm"),
            )
            if ans != QtWidgets.QMessageBox.StandardButton.Yes:
                return
        self.workbooks.clear()
        self.rows.clear()
        self._rebuild_table()
        self.status.showMessage("● " + self.tr_.t("ready"))

    def _remove_selected(self):
        rows_idx = sorted({idx.row() for idx in self.table.selectedIndexes()},
                          reverse=True)
        if not rows_idx:
            return
        for r in rows_idx:
            if 0 <= r < len(self.rows):
                del self.rows[r]
        # If a file no longer has any rows, drop it from workbooks
        remaining_paths = {r.path for r in self.rows}
        for p in list(self.workbooks.keys()):
            if p not in remaining_paths:
                del self.workbooks[p]
        self._rebuild_table()

    # -------------------------------------------------------- table ui
    def _apply_profile_to_rows(self, profile: pm.ProductProfile) -> None:
        """Reorder self.rows by profile order and apply enabled states."""
        order_map = {s.opc: i for i, s in enumerate(profile.stations)}
        enabled_map = {s.opc: s.enabled for s in profile.stations}
        for r in self.rows:
            code = str(r.block.opc_code)
            if code in enabled_map:
                r.enabled = enabled_map[code]
        # stable sort: known codes first (in profile order), unknown at end
        self.rows.sort(key=lambda r: order_map.get(str(r.block.opc_code), 10_000))

    def _rebuild_table(self):
        self._suspend_checks = True
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.rows))
        for i, r in enumerate(self.rows):
            chk = QtWidgets.QTableWidgetItem()
            # Use a text checkbox so the complete cell responds to a click.
            # A native QTableWidget checkbox only responds to its tiny box.
            chk.setFlags(
                QtCore.Qt.ItemFlag.ItemIsEnabled
                | QtCore.Qt.ItemFlag.ItemIsSelectable
            )
            chk.setText("☑" if r.enabled else "☐")
            chk.setData(QtCore.Qt.ItemDataRole.UserRole, r.enabled)
            chk.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, self.COL_USE, chk)

            order_item = QtWidgets.QTableWidgetItem(str(i + 1))
            order_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, self.COL_ORDER, order_item)

            opc_item = QtWidgets.QTableWidgetItem(str(r.block.opc_code))
            opc_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            f = opc_item.font(); f.setBold(True); opc_item.setFont(f)
            self.table.setItem(i, self.COL_OPC, opc_item)

            name_item = QtWidgets.QTableWidgetItem(str(r.block.name).strip())
            name_item.setToolTip(str(r.block.name).strip())
            self.table.setItem(i, self.COL_NAME, name_item)

            rows_item = QtWidgets.QTableWidgetItem(str(r.block.row_count))
            rows_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, self.COL_ROWS, rows_item)

            file_item = QtWidgets.QTableWidgetItem(Path(r.path).name)
            file_item.setToolTip(r.path)
            self.table.setItem(i, self.COL_FILE, file_item)
        self.table.blockSignals(False)
        self._suspend_checks = False
        self._update_counts()

    def _on_table_item_changed(self, item: QtWidgets.QTableWidgetItem):
        # Kept for compatibility with older table items/profiles. Current USE
        # cells are deliberately non-native checkboxes; cellClicked is used so
        # the user can click anywhere in the cell.
        if self._suspend_checks or item.column() != self.COL_USE:
            return
        row = item.row()
        if 0 <= row < len(self.rows):
            value = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if isinstance(value, bool):
                self.rows[row].enabled = value
        self._update_counts()

    def _on_use_cell_clicked(self, row: int, col: int):
        """Toggle a station by clicking anywhere in its USE cell."""
        if col != self.COL_USE or not (0 <= row < len(self.rows)):
            return
        self.rows[row].enabled = not self.rows[row].enabled
        it = self.table.item(row, self.COL_USE)
        if it is not None:
            self._suspend_checks = True
            it.setText("☑" if self.rows[row].enabled else "☐")
            it.setData(QtCore.Qt.ItemDataRole.UserRole, self.rows[row].enabled)
            self._suspend_checks = False
        self._update_counts()

    def _on_cell_double_clicked(self, row: int, col: int):
        """Open an input workbook when its file cell is double-clicked."""
        if col != self.COL_FILE or not (0 <= row < len(self.rows)):
            return
        path = self.rows[row].path
        if Path(path).exists():
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))

    def _update_counts(self):
        total = len(self.rows)
        selected = sum(1 for r in self.rows if r.enabled)
        if self.tr_.is_rtl():
            self.count_label.setText(f"انتخاب‌شده: {selected} از {total}")
        else:
            self.count_label.setText(f"Selected: {selected} / {total}")

    def _set_all(self, checked: bool):
        for r in self.rows:
            r.enabled = checked
        self._sync_checks_from_model()

    def _invert_selection(self):
        for r in self.rows:
            r.enabled = not r.enabled
        self._sync_checks_from_model()

    def _sync_checks_from_model(self):
        self._suspend_checks = True
        for i, r in enumerate(self.rows):
            it = self.table.item(i, self.COL_USE)
            if it:
                it.setText("☑" if r.enabled else "☐")
                it.setData(QtCore.Qt.ItemDataRole.UserRole, r.enabled)
        self._suspend_checks = False
        self._update_counts()

    def _selected_row_indices(self) -> List[int]:
        return sorted({idx.row() for idx in self.table.selectedIndexes()})

    def _reselect_after_reorder(self, indices: List[int]):
        self.table.clearSelection()
        for i in indices:
            if 0 <= i < self.table.rowCount():
                self.table.selectRow(i)

    def _move_row(self, direction: int):
        rows = self._selected_row_indices()
        if not rows:
            return
        n = len(self.rows)
        if direction < 0:
            new_sel = []
            for r in rows:
                if r > 0 and (r - 1) not in new_sel:
                    self.rows[r - 1], self.rows[r] = self.rows[r], self.rows[r - 1]
                    new_sel.append(r - 1)
                else:
                    new_sel.append(r)
        else:
            new_sel = []
            for r in reversed(rows):
                if r < n - 1 and (r + 1) not in new_sel:
                    self.rows[r + 1], self.rows[r] = self.rows[r], self.rows[r + 1]
                    new_sel.append(r + 1)
                else:
                    new_sel.append(r)
        self._rebuild_table()
        self._reselect_after_reorder(sorted(new_sel))

    def _move_top(self):
        rows = self._selected_row_indices()
        if not rows: return
        moved = [self.rows[r] for r in rows]
        keep = [r for i, r in enumerate(self.rows) if i not in rows]
        self.rows = moved + keep
        self._rebuild_table()
        self._reselect_after_reorder(list(range(len(moved))))

    def _move_bottom(self):
        rows = self._selected_row_indices()
        if not rows: return
        moved = [self.rows[r] for r in rows]
        keep = [r for i, r in enumerate(self.rows) if i not in rows]
        self.rows = keep + moved
        self._rebuild_table()
        start = len(keep)
        self._reselect_after_reorder(list(range(start, start + len(moved))))

    # ------------------------------------------------------ profile ops
    def _reload_profile_combo(self):
        current = self.profile_combo.currentText()
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItem("")   # empty = no profile
        for name in pm.list_profiles():
            self.profile_combo.addItem(name)
        # restore last profile
        target = current or self.app_settings.last_profile or ""
        if target:
            idx = self.profile_combo.findText(target)
            if idx >= 0:
                self.profile_combo.setCurrentIndex(idx)
        self.profile_combo.blockSignals(False)

    def _on_profile_changed(self, _idx: int):
        # Only auto-load when the user actively picks a non-empty profile
        name = self.profile_combo.currentText().strip()
        self.app_settings.last_profile = name
        self.app_settings.save()

    def _on_load_profile(self):
        name = self.profile_combo.currentText().strip()
        if not name:
            QtWidgets.QMessageBox.information(
                self, self.tr_.t("info"),
                self.tr_.t("no_profile_selected"),
            )
            return
        profile = pm.load_profile(name)
        if profile is None:
            QtWidgets.QMessageBox.warning(
                self, self.tr_.t("warning"),
                self.tr_.t("profile_missing", name=name),
            )
            return
        if profile.template_path and Path(profile.template_path).exists():
            self.template_edit.setText(profile.template_path)
        if profile.settings:
            self.merge_settings = profile.settings
        if profile.stations and self.rows:
            self._apply_profile_to_rows(profile)
            self._rebuild_table()
        self.app_settings.last_profile = name
        self.app_settings.save()
        self.status.showMessage("● " + self.tr_.t("profile_loaded", name=name))

    def _on_save_profile(self):
        default_name = ""
        for a in self.workbooks.values():
            if a.product_name:
                default_name = a.product_name
                break
        if not default_name:
            default_name = self.profile_combo.currentText().strip()

        name, ok = QtWidgets.QInputDialog.getText(
            self, self.tr_.t("profile_title"),
            self.tr_.t("profile_name_prompt"),
            text=default_name,
        )
        if not ok or not name.strip():
            return
        name = name.strip()

        # If exists, ask for overwrite
        if name in pm.list_profiles():
            ans = QtWidgets.QMessageBox.question(
                self, self.tr_.t("confirm"),
                self.tr_.t("overwrite_profile", name=name),
            )
            if ans != QtWidgets.QMessageBox.StandardButton.Yes:
                return

        # Build stations list (order + check state)
        stations = [
            pm.StationEntry(
                opc=str(r.block.opc_code),
                name=str(r.block.name),
                enabled=r.enabled,
            )
            for r in self.rows
        ]
        product_name = ""
        product_code = ""
        for a in self.workbooks.values():
            if a.product_name: product_name = a.product_name
            if a.product_code: product_code = a.product_code
            if product_name and product_code: break

        profile = pm.ProductProfile(
            name=name,
            product_name=product_name,
            product_code=product_code,
            template_path=self.template_edit.text(),
            stations=stations,
            settings=self.merge_settings,
        )
        pm.save_profile(profile)
        self._reload_profile_combo()
        idx = self.profile_combo.findText(name)
        if idx >= 0:
            self.profile_combo.setCurrentIndex(idx)
        self.app_settings.last_profile = name
        self.app_settings.save()
        self.status.showMessage("● " + self.tr_.t("profile_saved", name=name))

    def _on_delete_profile(self):
        name = self.profile_combo.currentText().strip()
        if not name:
            return
        ans = QtWidgets.QMessageBox.question(
            self, self.tr_.t("confirm"),
            self.tr_.t("profile_delete_confirm", name=name),
        )
        if ans != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        pm.delete_profile(name)
        self._reload_profile_combo()

    # ---------------------------------------------------------- settings
    def _open_settings(self):
        dlg = SettingsDialog(self, self.tr_, self.merge_settings, self.app_settings)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.merge_settings, self.app_settings = dlg.apply_to()
            self.app_settings.save()
            self.tr_.set_lang(self.app_settings.language)
            self._apply_language()
            # re-parse files with new settings
            self._refresh_all()

    # ------------------------------------------------------------- merge
    def _do_merge(self):
        template = self.template_edit.text().strip()
        if not template:
            QtWidgets.QMessageBox.warning(
                self, self.tr_.t("warning"), self.tr_.t("no_template"))
            return
        if not Path(template).exists():
            QtWidgets.QMessageBox.warning(
                self, self.tr_.t("warning"),
                self.tr_.t("template_missing", path=template))
            return
        if not self.rows:
            QtWidgets.QMessageBox.warning(
                self, self.tr_.t("warning"), self.tr_.t("no_files"))
            return
        selections: List[Tuple[str, StationBlock]] = [
            (r.path, r.block) for r in self.rows if r.enabled
        ]
        if not selections:
            QtWidgets.QMessageBox.warning(
                self, self.tr_.t("warning"), self.tr_.t("no_selection"))
            return

        output = self.output_edit.text().strip()
        if not output:
            output = str(OUTPUT_DIR / "Merged_PFMEA.xlsx")
            self.output_edit.setText(output)
        if not output.lower().endswith(".xlsx"):
            output += ".xlsx"
            self.output_edit.setText(output)

        # If output already exists, ask for confirmation
        if Path(output).exists():
            ans = QtWidgets.QMessageBox.question(
                self, self.tr_.t("confirm"),
                self.tr_.t("overwrite_output", path=output),
            )
            if ans != QtWidgets.QMessageBox.StandardButton.Yes:
                return

        self.merge_btn.setEnabled(False)
        self.open_output_btn.setEnabled(False)
        self.progress.setValue(0)
        self.status.showMessage("● " + self.tr_.t("processing"))
        self._save_last()

        self._worker = MergeWorker(
            template, selections, output, self.merge_settings,
            self.history_chk.isChecked(),
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_progress(self, pct: int, msg: str):
        self.progress.setValue(pct)
        if msg:
            self.status.showMessage("● " + msg)

    def _on_finished(self, out_path: str):
        self.merge_btn.setEnabled(True)
        self.progress.setValue(100)
        self._last_output = out_path
        self.open_output_btn.setEnabled(True)
        self.status.showMessage(
            "● " + self.tr_.t("merge_done_status", path=Path(out_path).name)
        )
        if self.open_after_chk.isChecked():
            self._open_file(out_path)
        else:
            box = QtWidgets.QMessageBox(self)
            box.setIcon(QtWidgets.QMessageBox.Icon.Information)
            box.setWindowTitle(self.tr_.t("info"))
            box.setText(self.tr_.t("merge_success", path=out_path))
            open_btn = box.addButton(
                "📂 " + ("باز کردن پوشه" if self.tr_.is_rtl() else "Open folder"),
                QtWidgets.QMessageBox.ButtonRole.ActionRole,
            )
            file_btn = box.addButton(
                "📄 " + ("باز کردن فایل" if self.tr_.is_rtl() else "Open file"),
                QtWidgets.QMessageBox.ButtonRole.ActionRole,
            )
            box.addButton(QtWidgets.QMessageBox.StandardButton.Ok)
            box.exec()
            if box.clickedButton() is open_btn:
                self._open_folder(str(Path(out_path).parent))
            elif box.clickedButton() is file_btn:
                self._open_file(out_path)

    def _open_last_output(self):
        if self._last_output and Path(self._last_output).exists():
            self._open_file(self._last_output)

    def _open_folder(self, folder: str):
        try:
            if os.name == "nt":
                os.startfile(folder)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                os.system(f'open "{folder}"')
            else:
                os.system(f'xdg-open "{folder}" >/dev/null 2>&1 &')
        except Exception:
            pass

    def _open_file(self, path: str):
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}" >/dev/null 2>&1 &')
        except Exception:
            pass

    # ----------------------------------------------------- context menu
    def _show_context_menu(self, pos: QtCore.QPoint):
        rows = self._selected_row_indices()
        if not rows:
            return
        t = self.tr_.t
        menu = QtWidgets.QMenu(self)
        act_toggle = menu.addAction("☑ " + t("toggle"))
        act_check = menu.addAction("☑ " + t("select_all"))
        act_uncheck = menu.addAction("☐ " + t("deselect_all"))
        menu.addSeparator()
        act_top = menu.addAction("⏫ " + t("move_top"))
        act_up = menu.addAction("⬆ " + t("move_up"))
        act_down = menu.addAction("⬇ " + t("move_down"))
        act_bot = menu.addAction("⏬ " + t("move_bottom"))
        menu.addSeparator()
        act_del = menu.addAction("🗑 " + t("remove_selected"))
        chosen = menu.exec(self.table.viewport().mapToGlobal(pos))
        if chosen is act_toggle: self._toggle_selected()
        elif chosen is act_check:
            for r in rows: self.rows[r].enabled = True
            self._sync_checks_from_model()
        elif chosen is act_uncheck:
            for r in rows: self.rows[r].enabled = False
            self._sync_checks_from_model()
        elif chosen is act_top:    self._move_top()
        elif chosen is act_up:     self._move_row(-1)
        elif chosen is act_down:   self._move_row(+1)
        elif chosen is act_bot:    self._move_bottom()
        elif chosen is act_del:    self._remove_selected()

    def _toggle_selected(self):
        rows = self._selected_row_indices()
        if not rows: return
        for r in rows:
            if 0 <= r < len(self.rows):
                self.rows[r].enabled = not self.rows[r].enabled
        self._sync_checks_from_model()

    # ----------------------------------------------------- drag & drop
    def dragEnterEvent(self, e: QtGui.QDragEnterEvent) -> None:
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e: QtGui.QDropEvent) -> None:
        paths: List[str] = []
        for url in e.mimeData().urls():
            p = url.toLocalFile()
            if not p:
                continue
            path = Path(p)
            if path.is_dir():
                paths.extend(str(x) for x in path.glob("*.xlsx")
                             if not x.name.startswith("~$"))
            elif path.suffix.lower() in (".xlsx", ".xlsm"):
                paths.append(str(path))
        if paths:
            self._add_paths(sorted(set(paths)))

    def _on_failed(self, err: str):
        self.merge_btn.setEnabled(True)
        self.status.showMessage("● " + self.tr_.t("ready"))
        # Show short error at top, full traceback in Details
        first_line = err.splitlines()[0] if err else "unknown error"
        box = QtWidgets.QMessageBox(self)
        box.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        box.setWindowTitle(self.tr_.t("error"))
        box.setText(self.tr_.t("merge_error", err=first_line))
        box.setDetailedText(err)
        box.exec()
