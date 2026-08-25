"""
Main window for the PFMEA Merger app (dark themed).
"""
from __future__ import annotations

import json
import os
import re
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PyQt6 import QtCore, QtGui, QtWidgets

from ..core.config import AppSettings, MergeSettings, TEMPLATES_DIR, OUTPUT_DIR, APP_VERSION
from ..core.i18n import Translator
from ..core.excel_reader import StationBlock, WorkbookAnalysis, analyze_workbook
from ..core.excel_merger import merge_pfmea
from ..core.cp_merger import merge_cp
from ..core import profile_manager as pm
from ..core import backup_manager
from .settings_dialog import SettingsDialog


# =============================================================================
# Background worker
# =============================================================================
class MergeWorker(QtCore.QThread):
    progress = QtCore.pyqtSignal(int, str)
    finished_ok = QtCore.pyqtSignal(str)
    failed = QtCore.pyqtSignal(str)

    def __init__(self, template, selections, output, settings, merge_history,
                 jobs=None):
        super().__init__()
        self.template = template
        self.selections = selections
        self.output = output
        self.settings = settings
        self.merge_history = merge_history
        self.jobs = jobs or [(template, selections, output, settings, merge_history)]
        self.output_paths: List[str] = []

    def run(self):
        try:
            total = len(self.jobs)
            for index, (template, selections, output, settings, history) in enumerate(self.jobs):
                def cb(pct, msg, index=index):
                    overall = int(((index * 100) + pct) / total)
                    self.progress.emit(overall, msg)
                out = merge_pfmea(
                    template, selections, output, settings,
                    merge_history=history, progress_cb=cb,
                )
                self.output_paths.append(out)
            self.finished_ok.emit(self.output_paths[-1])
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
        self.merge_settings = MergeSettings.from_dict(
            self.app_settings.saved_merge_settings
        )
        self.tr_ = Translator(self.app_settings.language)

        # file_path -> WorkbookAnalysis (for product info, etc.)
        self.workbooks: Dict[str, WorkbookAnalysis] = {}
        # Ordered list of station rows shown in the table (source of truth)
        self.rows: List[Row] = []
        # Suppresses recursion when we programmatically flip checkboxes
        self._suspend_checks = False
        self._profile_change_guard = False
        self._active_profile_name = ""
        self._profile_snapshot = ""
        self._row_heights: Dict[str, int] = {}
        self._hidden_stations: set[str] = set()
        self._missing_opcs: set[str] = set()
        self._blink_on = False
        self._layout_sync = False
        self._missing_timer = QtCore.QTimer(self)
        self._missing_timer.setInterval(550)
        self._missing_timer.timeout.connect(self._blink_missing_rows)

        self._worker: Optional[MergeWorker] = None
        self._last_output: str = ""

        self._build_ui()
        self._apply_language()
        self._restore_last()
        self._reload_profile_combo()
        # Restore the last input folder automatically once per application
        # start, so the user does not have to browse to it every time.
        self._auto_load_last_folder()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        self.setWindowTitle("PFMEA Merger")
        self.resize(1180, 780)
        self.setMinimumSize(1000, 640)

        cw = QtWidgets.QWidget()
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

        self.about_btn = QtWidgets.QPushButton()
        self.about_btn.setFixedHeight(36)
        self.about_btn.clicked.connect(self._show_about)

        self.backup_btn = QtWidgets.QPushButton()
        self.backup_btn.clicked.connect(self._backup_system)
        self.restore_backup_btn = QtWidgets.QPushButton()
        self.restore_backup_btn.clicked.connect(self._restore_system)

        self.settings_btn = QtWidgets.QPushButton()
        self.settings_btn.setIcon(QtGui.QIcon(str(Path(__file__).parent / "assets" / "settings.svg")))
        self.settings_btn.setIconSize(QtCore.QSize(20, 20))
        self.settings_btn.setFixedSize(38, 38)
        f = self.settings_btn.font(); f.setPointSize(14); self.settings_btn.setFont(f)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self._open_settings)

        title_bar.addWidget(self.lang_btn, 0, QtCore.Qt.AlignmentFlag.AlignTop)
        title_bar.addWidget(self.backup_btn, 0, QtCore.Qt.AlignmentFlag.AlignTop)
        title_bar.addWidget(self.restore_backup_btn, 0, QtCore.Qt.AlignmentFlag.AlignTop)
        title_bar.addWidget(self.about_btn, 0, QtCore.Qt.AlignmentFlag.AlignTop)
        title_bar.addWidget(self.settings_btn, 0, QtCore.Qt.AlignmentFlag.AlignTop)
        root.addLayout(title_bar)

        # ---- Card 1: template + profile
        card1 = _make_card()
        c1 = QtWidgets.QGridLayout(card1)
        c1.setContentsMargins(14, 12, 14, 12)
        c1.setHorizontalSpacing(10)
        c1.setVerticalSpacing(8)

        self.template_label = QtWidgets.QLabel()
        self.template_label.setObjectName("SectionLabel")
        self.template_edit = QtWidgets.QLineEdit()
        self.template_edit.setReadOnly(True)
        self.template_browse_btn = QtWidgets.QPushButton()
        self.template_open_btn = QtWidgets.QPushButton()
        self.template_browse_btn.clicked.connect(self._pick_template)
        self.template_open_btn.clicked.connect(self._open_template)
        self.template_edit.installEventFilter(self)
        self.profile_label = QtWidgets.QLabel()
        self.profile_label.setObjectName("SectionLabel")
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
        c1.addWidget(self.template_open_btn,    0, 5)
        c1.addWidget(self.template_browse_btn,  0, 6)
        c1.addWidget(self.profile_label,        1, 0)
        c1.addWidget(self.profile_combo,        1, 1, 1, 2)
        c1.addWidget(self.profile_load_btn,     1, 3)
        c1.addWidget(self.profile_save_btn,     1, 4)
        c1.addWidget(self.profile_delete_btn,   1, 5, 1, 2)
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
        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setFixedWidth(38)
        # Allow direct row-height editing by dragging the boundary between
        # rows. The settings dialog also provides a fixed height override.
        self.table.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Interactive
        )
        self.table.verticalHeader().setMinimumSectionSize(28)
        self.table.verticalHeader().sectionResized.connect(self._on_row_resized)
        self.table.horizontalHeader().sectionResized.connect(self._on_column_resized)
        self.table.setAlternatingRowColors(True)
        # A clean, spaced table reads more like a modern list than a raw
        # spreadsheet while retaining row selection and keyboard support.
        # Keep light grid lines: they make the row/column boundaries clear
        # without returning to the old heavy spreadsheet look.
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
        self.table.setColumnWidth(self.COL_ROWS,  290)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setWordWrap(True)
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
        self.output_label.setObjectName("SectionLabel")
        self.output_edit = QtWidgets.QLineEdit()
        self.output_browse_btn = QtWidgets.QPushButton()
        self.output_browse_btn.clicked.connect(self._pick_output)
        self.history_chk = QtWidgets.QCheckBox()
        self.history_chk.setChecked(True)
        self.open_after_chk = QtWidgets.QCheckBox()
        self.open_after_chk.setChecked(True)
        self.all_profiles_chk = QtWidgets.QCheckBox()
        self.all_profiles_chk.stateChanged.connect(self._on_all_profiles_toggled)

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
        opts_row.addSpacing(20)
        opts_row.addWidget(self.all_profiles_chk)
        opts_row.addStretch(1)
        c3.addLayout(opts_row,                 1, 0, 1, 5)
        c3.addWidget(self.merge_btn,           2, 0, 1, 2)
        c3.addWidget(self.progress,            2, 2, 1, 2)
        c3.addWidget(self.open_output_btn,     2, 4)
        c3.setColumnStretch(1, 1)
        c3.setColumnStretch(2, 1)
        root.addWidget(card3)

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(cw, "PFMEA")
        tabs.addTab(self._build_cp_tab(), "Control Plan (CP)")
        self.setCentralWidget(tabs)
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
        self.backup_btn.setText("💾 " + t("backup"))
        self.restore_backup_btn.setText("↶ " + t("restore_backup"))
        self.about_btn.setText("ℹ " + t("about"))
        self.template_label.setText(t("template_label"))
        self.template_open_btn.setText("📖 " + t("open_template"))
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
        self.all_profiles_chk.setText(t("all_profiles"))
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
    def _open_template(self):
        path = self.template_edit.text().strip()
        if path and Path(path).exists():
            self._open_file(path)
        else:
            QtWidgets.QMessageBox.warning(
                self, self.tr_.t("warning"),
                self.tr_.t("template_missing", path=path or "—"),
            )

    def eventFilter(self, watched, event):
        if watched is getattr(self, "template_edit", None):
            if event.type() == QtCore.QEvent.Type.MouseButtonDblClick:
                self._open_template()
                return True
        return super().eventFilter(watched, event)

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
    @staticmethod
    def _xlsx_files_in_folder(folder: str) -> List[str]:
        """Return supported Excel files in a folder in a stable order."""
        root = Path(folder)
        paths = [
            p for pattern in ("*.xlsx", "*.xlsm")
            for p in root.rglob(pattern)
            if not p.name.startswith("~$")
        ]
        return sorted({str(p) for p in paths}, key=lambda p: p.lower())

    def _auto_load_last_folder(self):
        """Load the remembered folder once, only when it still exists."""
        folder = self.app_settings.last_input_dir.strip()
        if not folder or not Path(folder).is_dir():
            return
        paths = self._xlsx_files_in_folder(folder)
        if paths:
            self._add_paths(paths)
            self.status.showMessage("● " + self.tr_.t(
                "restored_folder", folder=folder, n=len(paths)))

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
            paths = self._xlsx_files_in_folder(folder)
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
        self._missing_opcs.clear()
        self._missing_timer.stop()
        self._rebuild_table()
        self.status.showMessage("● " + self.tr_.t("ready"))

    def _remove_selected(self):
        rows_idx = sorted({idx.row() for idx in self.table.selectedIndexes()},
                          reverse=True)
        if not rows_idx:
            return
        removed_codes = set()
        for index in rows_idx:
            if 0 <= index < len(self.rows):
                removed_codes.add(str(self.rows[index].block.opc_code))
                del self.rows[index]
        if self._active_profile_name:
            # Removal is a visibility choice for this profile only. Keep the
            # workbook loaded so another profile can still use the station.
            self._hidden_stations.update(removed_codes)
            self._save_profile_data(self._active_profile_name)
        else:
            # Without a profile, retain the old session-only removal behavior.
            remaining_paths = {r.path for r in self.rows}
            for path in list(self.workbooks.keys()):
                if path not in remaining_paths:
                    del self.workbooks[path]
        self._rebuild_table()

    # -------------------------------------------------------- table ui
    def _apply_profile_to_rows(self, profile: pm.ProductProfile) -> None:
        """Apply profile visibility/order and add placeholders for missing files."""
        order_map = {s.opc: i for i, s in enumerate(profile.stations)}
        enabled_map = {s.opc: s.enabled for s in profile.stations}
        self._hidden_stations = set(profile.hidden_stations)
        self._missing_opcs = set()
        # Remove stale placeholders once the user loads a real matching file.
        real_codes = {str(r.block.opc_code) for r in self.rows if r.path}
        self.rows = [r for r in self.rows if r.path or str(r.block.opc_code) not in real_codes]
        known_codes = {str(r.block.opc_code) for r in self.rows}
        for entry in profile.stations:
            code = str(entry.opc)
            if code in self._hidden_stations or code in known_codes:
                continue
            # Empty path marks a profile station whose input file is absent.
            self.rows.append(Row("", StationBlock(code, entry.name, 0, -1), enabled=False))
            self._missing_opcs.add(code)
        for r in self.rows:
            code = str(r.block.opc_code)
            if code in enabled_map:
                r.enabled = enabled_map[code] and code not in self._hidden_stations
        self.rows = [r for r in self.rows if str(r.block.opc_code) not in self._hidden_stations]
        self.rows.sort(key=lambda r: order_map.get(str(r.block.opc_code), 10_000))
        if self._missing_opcs:
            self._missing_timer.start()

    def _rebuild_table(self):
        self._layout_sync = True
        self._suspend_checks = True
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.rows))

        # Let the failure-mode column adapt to its content, while respecting
        # the available window space. A non-zero setting gives the user a
        # fixed width instead.
        manual_width = int(getattr(self.merge_settings, "failure_column_width", 0))
        if manual_width > 0:
            failure_width = manual_width
        else:
            metrics = QtGui.QFontMetrics(self.table.font())
            longest = max(
                (metrics.horizontalAdvance(line)
                 for r in self.rows
                 for mode in r.block.failure_modes
                 for line in mode.splitlines()),
                default=0,
            )
            desired = max(290, min(620, longest + 34))
            available = self.table.viewport().width()
            failure_width = min(desired, max(290, int(available * 0.48))) if available > 0 else desired
        self.table.setColumnWidth(self.COL_ROWS, failure_width)

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
            chk_font = chk.font(); chk_font.setPointSize(14); chk_font.setBold(True)
            chk.setFont(chk_font)
            chk.setForeground(QtGui.QColor("#7d72ff" if r.enabled else "#687992"))
            self.table.setItem(i, self.COL_USE, chk)

            order_item = QtWidgets.QTableWidgetItem(str(i + 1))
            order_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, self.COL_ORDER, order_item)

            opc_item = QtWidgets.QTableWidgetItem(str(r.block.opc_code))
            opc_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            f = opc_item.font(); f.setBold(True); opc_item.setFont(f)
            opc_item.setForeground(QtGui.QColor("#59d6df"))
            opc_item.setBackground(QtGui.QColor("#1d3855"))
            self.table.setItem(i, self.COL_OPC, opc_item)

            name_item = QtWidgets.QTableWidgetItem(str(r.block.name).strip())
            name_item.setToolTip(str(r.block.name).strip())
            self.table.setItem(i, self.COL_NAME, name_item)

            failure_text = r.block.failure_mode_text or "—"
            rows_item = QtWidgets.QTableWidgetItem(failure_text)
            rows_item.setToolTip(failure_text)
            rows_item.setData(
                QtCore.Qt.ItemDataRole.UserRole,
                len(r.block.failure_modes),
            )
            # Burgundy accent reserved for the failure-mode content.
            rows_item.setForeground(QtGui.QColor("#e58a9c"))
            rows_item.setBackground(QtGui.QColor("#422331"))
            rows_item.setTextAlignment(
                QtCore.Qt.AlignmentFlag.AlignLeft
                | QtCore.Qt.AlignmentFlag.AlignTop
            )
            self.table.setItem(i, self.COL_ROWS, rows_item)
            # Give every failure mode its own readable line. The cap prevents
            # one unusually large file from making the whole table unusable.
            mode_count = len(r.block.failure_modes)
            manual_height = int(getattr(self.merge_settings, "failure_row_height", 0))
            saved_height = self._row_heights.get(str(r.block.opc_code), 0)
            if saved_height > 0:
                row_height = saved_height
            elif manual_height > 0:
                row_height = manual_height
            else:
                # Estimate wrapped lines using the current failure-mode
                # column width. This is more accurate than counting rows,
                # because a long mode may occupy several visual lines.
                chars_per_line = max(20, int(failure_width / 8))
                visual_lines = sum(
                    max(1, (len(mode) + chars_per_line - 1) // chars_per_line)
                    for mode in r.block.failure_modes
                ) or 1
                row_height = min(320, max(44, 24 + visual_lines * 22))
            self.table.setRowHeight(i, row_height)

            file_text = Path(r.path).name if r.path else self.tr_.t("missing_file")
            file_item = QtWidgets.QTableWidgetItem(file_text)
            file_item.setToolTip(r.path or self.tr_.t("missing_file"))
            file_item.setForeground(QtGui.QColor("#ff9a65" if not r.path else "#b9c7ff"))
            if not r.path:
                file_item.setBackground(QtGui.QColor("#4a2928"))
            self.table.setItem(i, self.COL_FILE, file_item)
        self.table.blockSignals(False)
        self._suspend_checks = False
        self._layout_sync = False
        self._update_counts()

    def _on_row_resized(self, row: int, _old_size: int, new_size: int):
        if self._layout_sync or not (0 <= row < len(self.rows)):
            return
        self._row_heights[str(self.rows[row].block.opc_code)] = max(28, int(new_size))

    def _on_column_resized(self, section: int, _old_size: int, new_size: int):
        if not self._layout_sync and section == self.COL_ROWS:
            self.merge_settings.failure_column_width = max(180, int(new_size))

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
            it.setForeground(QtGui.QColor("#7d72ff" if self.rows[row].enabled else "#687992"))
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

    def _set_missing_row_background(self, row_index: int, alert: bool):
        for col in range(self.table.columnCount()):
            item = self.table.item(row_index, col)
            if item is None:
                continue
            if alert:
                item.setBackground(QtGui.QColor("#713331"))
                item.setForeground(QtGui.QColor("#ffe0c2"))
            elif col == self.COL_OPC:
                item.setBackground(QtGui.QColor("#1d3855"))
                item.setForeground(QtGui.QColor("#59d6df"))
            elif col == self.COL_ROWS:
                item.setBackground(QtGui.QColor("#422331"))
                item.setForeground(QtGui.QColor("#e58a9c"))
            elif col == self.COL_FILE:
                item.setBackground(QtGui.QColor("#4a2928"))
                item.setForeground(QtGui.QColor("#ff9a65"))
            else:
                item.setBackground(QtGui.QBrush())
                item.setForeground(QtGui.QColor("#eef4ff"))

    def _blink_missing_rows(self):
        self._blink_on = not self._blink_on
        for i, row in enumerate(self.rows):
            if str(row.block.opc_code) in self._missing_opcs:
                self._set_missing_row_background(i, self._blink_on)

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
                it.setForeground(QtGui.QColor("#7d72ff" if r.enabled else "#687992"))
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
        # Do not auto-select the last profile on startup. The initial folder
        # load must remain neutral; the user chooses a profile explicitly.
        target = current or ""
        if target:
            idx = self.profile_combo.findText(target)
            if idx >= 0:
                self.profile_combo.setCurrentIndex(idx)
        self._active_profile_name = self.profile_combo.currentText().strip()
        self.profile_combo.blockSignals(False)

    def _current_profile_signature(self) -> str:
        state = {
            "template": self.template_edit.text(),
            "settings": self.merge_settings.to_dict(),
            "row_heights": self._row_heights,
            "stations": [
                {"opc": str(r.block.opc_code), "enabled": r.enabled}
                for r in self.rows
            ],
        }
        return json.dumps(state, ensure_ascii=False, sort_keys=True, default=str)

    def _on_profile_changed(self, _idx: int):
        if self._profile_change_guard:
            return
        new_name = self.profile_combo.currentText().strip()
        old_name = self._active_profile_name
        if new_name == old_name:
            return
        if old_name and self.rows and self._current_profile_signature() != self._profile_snapshot:
            answer = QtWidgets.QMessageBox.question(
                self, self.tr_.t("confirm"),
                self.tr_.t("save_profile_before_switch", name=old_name),
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No
                | QtWidgets.QMessageBox.StandardButton.Cancel,
                QtWidgets.QMessageBox.StandardButton.Yes,
            )
            if answer == QtWidgets.QMessageBox.StandardButton.Cancel:
                self._profile_change_guard = True
                idx = self.profile_combo.findText(old_name)
                if idx >= 0:
                    self.profile_combo.setCurrentIndex(idx)
                self._profile_change_guard = False
                return
            if answer == QtWidgets.QMessageBox.StandardButton.Yes:
                self._save_profile_data(old_name)
        self._active_profile_name = new_name
        self.app_settings.last_profile = new_name
        self.app_settings.save()
        if new_name:
            self._load_profile_by_name(new_name)

    def _load_profile_by_name(self, name: str) -> bool:
        profile = pm.load_profile(name)
        if profile is None:
            return False
        if profile.template_path and Path(profile.template_path).exists():
            self.template_edit.setText(profile.template_path)
        if profile.settings:
            self.merge_settings = profile.settings
        self._row_heights = dict(profile.row_heights)
        # Recreate the full loaded station list before applying this profile;
        # stations hidden in another profile must remain available here.
        restored = []
        for path, analysis in self.workbooks.items():
            restored.extend(Row(path, block, enabled=True)
                           for block in analysis.stations)
        if restored:
            self.rows = restored
        if profile.stations and self.rows:
            self._apply_profile_to_rows(profile)
            self._rebuild_table()
        self._profile_snapshot = self._current_profile_signature()
        self.status.showMessage("● " + self.tr_.t("profile_loaded", name=name))
        return True

    def _save_profile_data(self, name: str) -> None:
        stations = [
            pm.StationEntry(opc=str(r.block.opc_code),
                            name=str(r.block.name), enabled=r.enabled)
            for r in self.rows
        ]
        product_name = ""
        product_code = ""
        for analysis in self.workbooks.values():
            product_name = product_name or analysis.product_name
            product_code = product_code or analysis.product_code
        pm.save_profile(pm.ProductProfile(
            name=name, product_name=product_name, product_code=product_code,
            template_path=self.template_edit.text(), stations=stations,
            row_heights=dict(self._row_heights), settings=self.merge_settings,
        ))
        self._profile_snapshot = self._current_profile_signature()

    def _on_load_profile(self):
        name = self.profile_combo.currentText().strip()
        if not name:
            QtWidgets.QMessageBox.information(
                self, self.tr_("info"), self.tr_("no_profile_selected"))
            return
        if not self._load_profile_by_name(name):
            QtWidgets.QMessageBox.warning(
                self, self.tr_("warning"),
                self.tr_("profile_missing", name=name))
            return
        self._active_profile_name = name
        self.app_settings.last_profile = name
        self.app_settings.save()

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
            row_heights=dict(self._row_heights),
            hidden_stations=sorted(self._hidden_stations),
            settings=self.merge_settings,
        )
        pm.save_profile(profile)
        self._profile_snapshot = self._current_profile_signature()
        self._reload_profile_combo()
        self._profile_change_guard = True
        idx = self.profile_combo.findText(name)
        if idx >= 0:
            self.profile_combo.setCurrentIndex(idx)
        self._profile_change_guard = False
        self._active_profile_name = name
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

    def _backup_system(self):
        start = str(Path(self.output_edit.text() or OUTPUT_DIR / "").parent / "PFMEA_Merger_Backup.zip")
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, self.tr_.t("backup"), start,
            f"{self.tr_.t('backup_file')} (*.zip)",
        )
        if not path:
            return
        if not path.lower().endswith(".zip"):
            path += ".zip"
        try:
            backup_manager.create_backup(path)
            QtWidgets.QMessageBox.information(
                self, self.tr_.t("info"),
                self.tr_.t("backup_created") + f"\n{path}",
            )
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, self.tr_.t("error"), str(exc))

    def _restore_system(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, self.tr_.t("restore_backup"), str(Path.home()),
            f"{self.tr_.t('backup_file')} (*.zip)",
        )
        if not path:
            return
        answer = QtWidgets.QMessageBox.question(
            self, self.tr_.t("confirm"), self.tr_.t("backup_confirm"),
        )
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        try:
            backup_manager.restore_backup(path)
            self.app_settings = AppSettings.load()
            self.merge_settings = MergeSettings.from_dict(
                self.app_settings.saved_merge_settings
            )
            self._restore_last()
            self._profile_change_guard = True
            self.profile_combo.setCurrentIndex(0)
            self._profile_change_guard = False
            self._active_profile_name = ""
            self._reload_profile_combo()
            self._apply_language()
            self._refresh_all()
            QtWidgets.QMessageBox.information(
                self, self.tr_.t("info"), self.tr_.t("backup_restored"),
            )
        except Exception as exc:
            box = QtWidgets.QMessageBox(self)
            box.setIcon(QtWidgets.QMessageBox.Icon.Critical)
            box.setWindowTitle(self.tr_.t("error"))
            box.setText("بازیابی بک‌آپ انجام نشد. فایل انتخاب‌شده معتبر نیست یا ناقص است.")
            box.setDetailedText(traceback.format_exc())
            box.exec()

    def _show_about(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(self.tr_.t("about_title"))
        dialog.setMinimumSize(520, 390)
        layout = QtWidgets.QVBoxLayout(dialog)
        title = QtWidgets.QLabel(self.tr_.t("app_title"))
        title.setObjectName("AppTitle")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        font = title.font(); font.setPointSize(16); font.setBold(True); title.setFont(font)
        layout.addWidget(title)
        if self.tr_.is_rtl():
            html = (
                "<div align=\"center\"><b>تجمیع‌گر PFMEA برای فرآیند APQP</b><br><br>"
                "این برنامه برای مدیریت فایل‌های PFMEA ایستگاه‌ها، انتخاب ایستگاه‌ها و ساخت "
                "خروجی نهایی در قالب Template طراحی شده است.<br><br>"
                "<b>طراحی و توسعه:</b> حامد سرگلی<br>"
                "<b>تلفن:</b> 09126368924<br>"
                "<b>ایمیل:</b> <a href=\"mailto:hamed.sargoli@gmail.com\">hamed.sargoli@gmail.com</a><br><br>"
                f"<b>نسخه برنامه:</b> {APP_VERSION}</div>"
            )
        else:
            html = (
                "<div align=\"center\"><b>PFMEA Merger for APQP</b><br><br>"
                "A desktop tool for managing station PFMEA files and creating a final "
                "Template-based workbook.<br><br>"
                "<b>Developed by:</b> Hamed Sargoli<br>"
                "<b>Phone:</b> 09126368924<br>"
                "<b>Email:</b> <a href=\"mailto:hamed.sargoli@gmail.com\">hamed.sargoli@gmail.com</a><br><br>"
                f"<b>Version:</b> {APP_VERSION}</div>"
            )
        text = QtWidgets.QLabel(html)
        text.setTextFormat(QtCore.Qt.TextFormat.RichText)
        text.setOpenExternalLinks(True)
        text.setWordWrap(True)
        text.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text, 1)
        close = QtWidgets.QPushButton(self.tr_.t("ok"))
        close.clicked.connect(dialog.accept)
        layout.addWidget(close, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        dialog.exec()

    # ---------------------------------------------------------- settings
    def _open_settings(self):
        try:
            dlg = SettingsDialog(self, self.tr_, self.merge_settings, self.app_settings)
            if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                self.merge_settings, self.app_settings = dlg.apply_to()
                self.app_settings.saved_merge_settings = self.merge_settings.to_dict()
                self.app_settings.save()
                self.tr_.set_lang(self.app_settings.language)
                self._apply_language()
                # re-parse files with new settings
                self._refresh_all()
        except Exception as exc:
            box = QtWidgets.QMessageBox(self)
            box.setIcon(QtWidgets.QMessageBox.Icon.Critical)
            box.setWindowTitle(self.tr_.t("error"))
            box.setText(str(exc))
            box.setDetailedText(traceback.format_exc())
            box.exec()

    # ------------------------------------------------------------- merge
    def _on_all_profiles_toggled(self, state: int):
        batch = state == QtCore.Qt.CheckState.Checked.value
        # Batch mode produces several files, so opening a single Excel file
        # would be ambiguous. Open the output folder instead.
        self.open_after_chk.setEnabled(not batch)
        if batch:
            self.open_after_chk.setChecked(False)

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
            (r.path, r.block) for r in self.rows
            if r.enabled and r.path and Path(r.path).exists()
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

        # Build one job for normal mode, or one ordered job per profile.
        jobs = [(template, selections, output, self.merge_settings,
                 self.history_chk.isChecked())]
        if self.all_profiles_chk.isChecked():
            jobs = []
            for profile_name in pm.list_profiles():
                profile = pm.load_profile(profile_name)
                if profile is None:
                    continue
                order_map = {s.opc: i for i, s in enumerate(profile.stations)}
                enabled = {s.opc for s in profile.stations if s.enabled}
                profile_selections = [
                    (r.path, r.block) for r in self.rows
                    if str(r.block.opc_code) in enabled
                    and r.path and Path(r.path).exists()
                ]
                profile_selections.sort(
                    key=lambda pair: order_map.get(str(pair[1].opc_code), 10_000)
                )
                if not profile_selections:
                    continue
                safe_name = re.sub(
                    r"[^A-Za-z0-9_\\-\\u0600-\\u06FF ]+", "_", profile_name
                ).strip() or "profile"
                profile_output = str(Path(output).with_name(
                    f"{Path(output).stem}_{safe_name}{Path(output).suffix}"
                ))
                jobs.append((template, profile_selections, profile_output,
                             profile.settings, self.history_chk.isChecked()))
            if not jobs:
                QtWidgets.QMessageBox.warning(
                    self, self.tr_.t("warning"), self.tr_.t("no_selection"))
                return

        existing = [job[2] for job in jobs if Path(job[2]).exists()]
        if existing:
            shown = "\\n".join(existing[:8])
            if len(existing) > 8:
                shown += "\\n..."
            ans = QtWidgets.QMessageBox.question(
                self, self.tr_.t("confirm"),
                self.tr_.t("overwrite_output", path=shown),
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
            self.history_chk.isChecked(), jobs=jobs,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _build_cp_tab(self):
        page = QtWidgets.QWidget(); page.setLayoutDirection(self.layoutDirection())
        root = QtWidgets.QVBoxLayout(page); root.setContentsMargins(24, 20, 24, 18); root.setSpacing(14)
        header = QtWidgets.QLabel("Control Plan Merger")
        header.setObjectName("Title"); root.addWidget(header)
        subtitle = QtWidgets.QLabel("تجمیع فایل‌های Control Plan با حفظ قالب Template")
        subtitle.setProperty("muted", True); root.addWidget(subtitle)

        card1 = _make_card(); g = QtWidgets.QGridLayout(card1); g.setContentsMargins(14,12,14,12); g.setHorizontalSpacing(10); g.setVerticalSpacing(8)
        label = QtWidgets.QLabel("Template CP"); label.setObjectName("SectionLabel")
        self.cp_template_edit = QtWidgets.QLineEdit(); self.cp_template_edit.setReadOnly(True)
        bt = QtWidgets.QPushButton("📂 انتخاب Template") ; bt.clicked.connect(self._pick_cp_template)
        g.addWidget(label,0,0); g.addWidget(self.cp_template_edit,0,1,1,4); g.addWidget(bt,0,5)
        root.addWidget(card1)

        card2 = _make_card(); v = QtWidgets.QVBoxLayout(card2); v.setContentsMargins(14,12,14,12); v.setSpacing(9)
        bar=QtWidgets.QHBoxLayout(); self.cp_add_btn=QtWidgets.QPushButton("📄 افزودن فایل‌ها"); self.cp_folder_btn=QtWidgets.QPushButton("📁 افزودن پوشه"); self.cp_remove_btn=QtWidgets.QPushButton("حذف انتخاب"); self.cp_clear_btn=QtWidgets.QPushButton("پاک کردن همه")
        self.cp_add_btn.clicked.connect(self._cp_add_files); self.cp_folder_btn.clicked.connect(self._cp_add_folder); self.cp_remove_btn.clicked.connect(self._cp_remove_selected); self.cp_clear_btn.clicked.connect(self.cp_files.clear)
        for x in (self.cp_add_btn,self.cp_folder_btn): bar.addWidget(x)
        bar.addStretch(1); bar.addWidget(self.cp_remove_btn); bar.addWidget(self.cp_clear_btn); v.addLayout(bar)
        self.cp_files=QtWidgets.QListWidget(); self.cp_files.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection); self.cp_files.setMinimumHeight(220); v.addWidget(self.cp_files)
        root.addWidget(card2,1)

        card3 = _make_card(); g = QtWidgets.QGridLayout(card3); g.setContentsMargins(14,12,14,12); g.setHorizontalSpacing(10); g.setVerticalSpacing(8)
        self.cp_output_edit=QtWidgets.QLineEdit(str(OUTPUT_DIR/"Merged_CP.xlsx")); self.cp_output_browse=QtWidgets.QPushButton("📂 انتخاب مسیر")
        self.cp_output_browse.clicked.connect(self._pick_cp_output)
        self.cp_merge_btn=QtWidgets.QPushButton("ساخت خروجی CP"); self.cp_merge_btn.setProperty("primary",True); self.cp_merge_btn.setMinimumHeight(42); self.cp_merge_btn.clicked.connect(self._do_cp_merge)
        g.addWidget(QtWidgets.QLabel("فایل خروجی"),0,0); g.addWidget(self.cp_output_edit,0,1,1,4); g.addWidget(self.cp_output_browse,0,5); g.addWidget(self.cp_merge_btn,1,0,1,6)
        root.addWidget(card3)
        return page

    def _pick_cp_template(self):
        path,_=QtWidgets.QFileDialog.getOpenFileName(self,"Template CP",str(TEMPLATES_DIR),"Excel (*.xlsx *.xlsm)")
        if path: self.cp_template_edit.setText(path)

    def _cp_add_files(self):
        paths,_=QtWidgets.QFileDialog.getOpenFileNames(self,"فایل‌های CP","","Excel (*.xlsx *.xlsm)")
        for path in paths:
            if not any(self.cp_files.item(i).text()==path for i in range(self.cp_files.count())): self.cp_files.addItem(path)

    def _cp_remove_selected(self):
        for item in self.cp_files.selectedItems():
            self.cp_files.takeItem(self.cp_files.row(item))

    def _cp_add_folder(self):
        folder=QtWidgets.QFileDialog.getExistingDirectory(self,"پوشه فایل‌های CP")
        if folder:
            for path in sorted(Path(folder).glob("*.xlsx")):
                if not any(self.cp_files.item(i).text()==str(path) for i in range(self.cp_files.count())): self.cp_files.addItem(str(path))

    def _pick_cp_output(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "خروجی CP", self.cp_output_edit.text(), "Excel (*.xlsx)")
        if path: self.cp_output_edit.setText(path)

    def _do_cp_merge(self):
        template=self.cp_template_edit.text().strip(); files=[self.cp_files.item(i).text() for i in range(self.cp_files.count())]
        if not template or not files:
            QtWidgets.QMessageBox.warning(self,"CP","Template و حداقل یک فایل CP را انتخاب کنید."); return
        output=self.cp_output_edit.text().strip() or str(OUTPUT_DIR/"Merged_CP.xlsx")
        try:
            merge_cp(template,files,output); self._last_output=output
            QtWidgets.QMessageBox.information(self,"CP",f"خروجی ساخته شد:\n{output}")
        except Exception as exc: QtWidgets.QMessageBox.critical(self,"CP",str(exc))

    def _on_progress(self, pct: int, msg: str):
        self.progress.setValue(pct)
        if msg:
            self.status.showMessage("● " + msg)

    def _on_finished(self, out_path: str):
        self.merge_btn.setEnabled(True)
        self.progress.setValue(100)
        self._last_output = out_path
        self.open_output_btn.setEnabled(True)
        outputs = getattr(self._worker, "output_paths", [out_path])
        batch = len(outputs) > 1 or self.all_profiles_chk.isChecked()
        self.status.showMessage(
            "● " + self.tr_.t("merge_done_status", path=Path(out_path).name)
        )
        if batch:
            # In all-profiles mode let the user choose which generated Excel
            # file to open from the folder.
            self._open_folder(str(Path(out_path).parent))
        elif self.open_after_chk.isChecked():
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
        # A context-menu request does not always select the row first.
        # Select the row under the cursor so right-clicking an unselected row
        # immediately exposes the remove action for that exact row.
        index = self.table.indexAt(pos)
        if index.isValid():
            if not self.table.selectionModel().isRowSelected(index.row(), index.parent()):
                self.table.clearSelection()
                self.table.selectRow(index.row())
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
