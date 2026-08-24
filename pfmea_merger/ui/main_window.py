"""
Main window for the PFMEA Merger app.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple
import os
import traceback

from PyQt6 import QtCore, QtGui, QtWidgets

from ..core.config import AppSettings, MergeSettings, TEMPLATES_DIR, OUTPUT_DIR
from ..core.i18n import Translator
from ..core.excel_reader import StationBlock, WorkbookAnalysis, analyze_workbook
from ..core.excel_merger import merge_pfmea
from ..core import profile_manager as pm
from .settings_dialog import SettingsDialog


# =============================================================================
# Background worker for the merge (keeps UI responsive)
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
# Main window
# =============================================================================
class MainWindow(QtWidgets.QMainWindow):
    COL_USE, COL_ORDER, COL_OPC, COL_NAME, COL_ROWS, COL_FILE = range(6)

    def __init__(self):
        super().__init__()
        self.app_settings = AppSettings.load()
        self.merge_settings = MergeSettings()
        self.tr_ = Translator(self.app_settings.language)

        # (file_path -> WorkbookAnalysis)
        self.workbooks: Dict[str, WorkbookAnalysis] = {}
        # rows are (file_path, StationBlock)
        self.rows: List[Tuple[str, StationBlock]] = []

        self._worker: MergeWorker | None = None

        self._build_ui()
        self._apply_language()
        self._restore_last()
        self._reload_profile_combo()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        self.setWindowTitle("PFMEA Merger")
        self.resize(1100, 680)

        cw = QtWidgets.QWidget()
        self.setCentralWidget(cw)
        root = QtWidgets.QVBoxLayout(cw)
        root.setSpacing(8)

        # ---- Row 1: template + profile
        row1 = QtWidgets.QHBoxLayout()
        self.template_label = QtWidgets.QLabel()
        self.template_edit = QtWidgets.QLineEdit()
        self.template_edit.setReadOnly(True)
        self.template_browse_btn = QtWidgets.QPushButton()
        self.template_browse_btn.clicked.connect(self._pick_template)

        self.profile_label = QtWidgets.QLabel()
        self.profile_combo = QtWidgets.QComboBox()
        self.profile_combo.setMinimumWidth(180)
        self.profile_load_btn = QtWidgets.QPushButton()
        self.profile_save_btn = QtWidgets.QPushButton()
        self.profile_delete_btn = QtWidgets.QPushButton()
        self.profile_load_btn.clicked.connect(self._on_load_profile)
        self.profile_save_btn.clicked.connect(self._on_save_profile)
        self.profile_delete_btn.clicked.connect(self._on_delete_profile)

        row1.addWidget(self.template_label)
        row1.addWidget(self.template_edit, 3)
        row1.addWidget(self.template_browse_btn)
        row1.addSpacing(20)
        row1.addWidget(self.profile_label)
        row1.addWidget(self.profile_combo, 2)
        row1.addWidget(self.profile_load_btn)
        row1.addWidget(self.profile_save_btn)
        row1.addWidget(self.profile_delete_btn)
        root.addLayout(row1)

        # ---- Row 2: add files / folder / clear
        row2 = QtWidgets.QHBoxLayout()
        self.add_files_btn = QtWidgets.QPushButton()
        self.add_folder_btn = QtWidgets.QPushButton()
        self.refresh_btn = QtWidgets.QPushButton()
        self.clear_btn = QtWidgets.QPushButton()
        self.settings_btn = QtWidgets.QPushButton("⚙")
        self.settings_btn.setFixedWidth(36)
        self.add_files_btn.clicked.connect(self._add_files)
        self.add_folder_btn.clicked.connect(self._add_folder)
        self.refresh_btn.clicked.connect(self._refresh_all)
        self.clear_btn.clicked.connect(self._clear_all)
        self.settings_btn.clicked.connect(self._open_settings)
        row2.addWidget(self.add_files_btn)
        row2.addWidget(self.add_folder_btn)
        row2.addWidget(self.refresh_btn)
        row2.addWidget(self.clear_btn)
        row2.addStretch(1)
        row2.addWidget(self.settings_btn)
        root.addLayout(row2)

        # ---- station table
        self.hint_label = QtWidgets.QLabel()
        root.addWidget(self.hint_label)

        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(
            QtWidgets.QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(
            QtWidgets.QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(self.COL_USE, 60)
        self.table.setColumnWidth(self.COL_ORDER, 60)
        self.table.setColumnWidth(self.COL_OPC, 90)
        self.table.setColumnWidth(self.COL_NAME, 260)
        self.table.setColumnWidth(self.COL_ROWS, 80)
        root.addWidget(self.table, 1)

        # ---- Row 3: select-all / move up / down
        row3 = QtWidgets.QHBoxLayout()
        self.select_all_btn = QtWidgets.QPushButton()
        self.deselect_all_btn = QtWidgets.QPushButton()
        self.up_btn = QtWidgets.QPushButton("⬆")
        self.down_btn = QtWidgets.QPushButton("⬇")
        self.up_btn.setFixedWidth(40)
        self.down_btn.setFixedWidth(40)
        self.select_all_btn.clicked.connect(lambda: self._set_all(True))
        self.deselect_all_btn.clicked.connect(lambda: self._set_all(False))
        self.up_btn.clicked.connect(lambda: self._move_row(-1))
        self.down_btn.clicked.connect(lambda: self._move_row(+1))
        row3.addWidget(self.select_all_btn)
        row3.addWidget(self.deselect_all_btn)
        row3.addStretch(1)
        row3.addWidget(self.up_btn)
        row3.addWidget(self.down_btn)
        root.addLayout(row3)

        # ---- output
        row4 = QtWidgets.QHBoxLayout()
        self.output_label = QtWidgets.QLabel()
        self.output_edit = QtWidgets.QLineEdit()
        self.output_browse_btn = QtWidgets.QPushButton()
        self.output_browse_btn.clicked.connect(self._pick_output)
        self.history_chk = QtWidgets.QCheckBox()
        self.history_chk.setChecked(True)
        row4.addWidget(self.output_label)
        row4.addWidget(self.output_edit, 3)
        row4.addWidget(self.output_browse_btn)
        row4.addSpacing(12)
        row4.addWidget(self.history_chk)
        root.addLayout(row4)

        # ---- merge button + progress
        row5 = QtWidgets.QHBoxLayout()
        self.merge_btn = QtWidgets.QPushButton()
        self.merge_btn.setMinimumHeight(38)
        f = self.merge_btn.font(); f.setBold(True); self.merge_btn.setFont(f)
        self.merge_btn.clicked.connect(self._do_merge)
        self.progress = QtWidgets.QProgressBar()
        self.progress.setValue(0)
        row5.addWidget(self.merge_btn, 1)
        row5.addWidget(self.progress, 2)
        root.addLayout(row5)

        self.status = self.statusBar()

    # -------------------------------------------------- translation apply
    def _apply_language(self):
        t = self.tr_.t
        self.setWindowTitle(t("app_title"))
        self.setLayoutDirection(
            QtCore.Qt.LayoutDirection.RightToLeft if self.tr_.is_rtl()
            else QtCore.Qt.LayoutDirection.LeftToRight
        )
        self.template_label.setText(t("template_label"))
        self.template_browse_btn.setText(t("browse"))
        self.profile_label.setText(t("profile_label"))
        self.profile_load_btn.setText(t("load_profile"))
        self.profile_save_btn.setText(t("save_profile"))
        self.profile_delete_btn.setText(t("delete_profile"))
        self.add_files_btn.setText(t("add_files"))
        self.add_folder_btn.setText(t("add_folder"))
        self.refresh_btn.setText(t("refresh"))
        self.clear_btn.setText(t("clear"))
        self.hint_label.setText(t("stations_hint"))
        self.select_all_btn.setText(t("select_all"))
        self.deselect_all_btn.setText(t("deselect_all"))
        self.output_label.setText(t("output_label"))
        self.output_browse_btn.setText(t("browse"))
        self.history_chk.setText(t("include_history"))
        self.merge_btn.setText(t("merge_button"))
        self.table.setHorizontalHeaderLabels([
            t("col_use"), t("col_order"), t("col_opc"),
            t("col_name"), t("col_rows"), t("col_file"),
        ])
        self.status.showMessage(t("ready"))

    # ------------------------------------------------------- persistence
    def _restore_last(self):
        if self.app_settings.last_template and Path(self.app_settings.last_template).exists():
            self.template_edit.setText(self.app_settings.last_template)
        else:
            # Fall back to first template in templates dir
            for p in sorted(TEMPLATES_DIR.glob("*.xlsx")):
                self.template_edit.setText(str(p))
                break
        # default output path
        self.output_edit.setText(str(OUTPUT_DIR / "Merged_PFMEA.xlsx"))

    def _save_last(self):
        self.app_settings.last_template = self.template_edit.text()
        self.app_settings.last_output_dir = str(Path(self.output_edit.text()).parent)
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
            self._add_paths(paths)

    def _add_paths(self, paths: List[str]):
        skipped: List[str] = []
        added_count = 0
        station_count = 0
        for p in paths:
            if p in self.workbooks:
                continue
            analysis = analyze_workbook(p, self.merge_settings)
            if not analysis.is_valid:
                skipped.append(Path(p).name)
                continue
            self.workbooks[p] = analysis
            for block in analysis.stations:
                self.rows.append((p, block))
                station_count += 1
            added_count += 1
        self._rebuild_table()
        if skipped:
            QtWidgets.QMessageBox.warning(
                self, self.tr_.t("warning"),
                "\n".join(self.tr_.t("file_not_pfmea", name=n) for n in skipped),
            )
        self.status.showMessage(self.tr_.t(
            "loaded_files", n=added_count, s=station_count))

    def _refresh_all(self):
        paths = list(self.workbooks.keys())
        self.workbooks.clear()
        self.rows.clear()
        if paths:
            self._add_paths(paths)
        else:
            self._rebuild_table()

    def _clear_all(self):
        self.workbooks.clear()
        self.rows.clear()
        self._rebuild_table()
        self.status.showMessage(self.tr_.t("ready"))

    # -------------------------------------------------------- table ui
    def _rebuild_table(self):
        # apply profile ordering if a profile is selected
        profile_name = self.profile_combo.currentText().strip()
        profile = pm.load_profile(profile_name) if profile_name else None
        if profile and profile.station_order:
            order_map = {code: i for i, code in enumerate(profile.station_order)}
            def key(item):
                return order_map.get(str(item[1].opc_code), 10_000)
            self.rows.sort(key=key)

        self.table.setRowCount(len(self.rows))
        for i, (path, block) in enumerate(self.rows):
            # use checkbox
            chk = QtWidgets.QTableWidgetItem()
            chk.setFlags(chk.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            chk.setCheckState(QtCore.Qt.CheckState.Checked)
            self.table.setItem(i, self.COL_USE, chk)
            # order (1-based)
            self.table.setItem(i, self.COL_ORDER,
                               QtWidgets.QTableWidgetItem(str(i + 1)))
            # opc / name / rows / file
            self.table.setItem(i, self.COL_OPC,
                               QtWidgets.QTableWidgetItem(str(block.opc_code)))
            self.table.setItem(i, self.COL_NAME,
                               QtWidgets.QTableWidgetItem(str(block.name)))
            self.table.setItem(i, self.COL_ROWS,
                               QtWidgets.QTableWidgetItem(str(block.row_count)))
            self.table.setItem(i, self.COL_FILE,
                               QtWidgets.QTableWidgetItem(Path(path).name))
        self._renumber_orders()

    def _renumber_orders(self):
        for i in range(self.table.rowCount()):
            item = self.table.item(i, self.COL_ORDER)
            if item is None:
                item = QtWidgets.QTableWidgetItem()
                self.table.setItem(i, self.COL_ORDER, item)
            item.setText(str(i + 1))

    def _set_all(self, checked: bool):
        state = QtCore.Qt.CheckState.Checked if checked else QtCore.Qt.CheckState.Unchecked
        for i in range(self.table.rowCount()):
            it = self.table.item(i, self.COL_USE)
            if it:
                it.setCheckState(state)

    def _move_row(self, direction: int):
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        if not rows:
            return
        if direction < 0:
            for r in rows:
                if r <= 0:
                    continue
                self.rows[r - 1], self.rows[r] = self.rows[r], self.rows[r - 1]
            new_sel = [max(0, r - 1) for r in rows]
        else:
            for r in reversed(rows):
                if r >= len(self.rows) - 1:
                    continue
                self.rows[r + 1], self.rows[r] = self.rows[r], self.rows[r + 1]
            new_sel = [min(len(self.rows) - 1, r + 1) for r in rows]
        # capture existing check states before rebuild
        checks = [
            self.table.item(i, self.COL_USE).checkState()
            for i in range(self.table.rowCount())
        ]
        # after swap, recompute checks by moving them the same way
        if direction < 0:
            for r in rows:
                if r <= 0:
                    continue
                checks[r - 1], checks[r] = checks[r], checks[r - 1]
        else:
            for r in reversed(rows):
                if r >= len(checks) - 1:
                    continue
                checks[r + 1], checks[r] = checks[r], checks[r + 1]
        self._rebuild_table()
        for i, st in enumerate(checks):
            self.table.item(i, self.COL_USE).setCheckState(st)
        # restore selection
        self.table.clearSelection()
        for r in new_sel:
            self.table.selectRow(r)

    # ------------------------------------------------------ profile ops
    def _reload_profile_combo(self):
        current = self.profile_combo.currentText()
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItem("")
        for name in pm.list_profiles():
            self.profile_combo.addItem(name)
        if current:
            idx = self.profile_combo.findText(current)
            if idx >= 0:
                self.profile_combo.setCurrentIndex(idx)
        self.profile_combo.blockSignals(False)

    def _on_load_profile(self):
        name = self.profile_combo.currentText().strip()
        if not name:
            return
        profile = pm.load_profile(name)
        if profile is None:
            return
        if profile.template_path and Path(profile.template_path).exists():
            self.template_edit.setText(profile.template_path)
        if profile.settings:
            self.merge_settings = profile.settings
        # re-apply ordering
        self._rebuild_table()
        self.app_settings.last_profile = name
        self.app_settings.save()
        QtWidgets.QMessageBox.information(
            self, self.tr_.t("info"),
            self.tr_.t("profile_loaded", name=name),
        )

    def _on_save_profile(self):
        default_name = ""
        # try to auto-name from any loaded workbook
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
        # collect station order from *currently checked* rows in table order
        order: List[str] = []
        for i, (_p, block) in enumerate(self.rows):
            it = self.table.item(i, self.COL_USE)
            if it and it.checkState() == QtCore.Qt.CheckState.Checked:
                order.append(str(block.opc_code))
        product_name = ""
        product_code = ""
        for a in self.workbooks.values():
            if a.product_name:
                product_name = a.product_name
            if a.product_code:
                product_code = a.product_code
            if product_name and product_code:
                break
        profile = pm.ProductProfile(
            name=name.strip(),
            product_name=product_name,
            product_code=product_code,
            template_path=self.template_edit.text(),
            station_order=order,
            settings=self.merge_settings,
        )
        pm.save_profile(profile)
        self._reload_profile_combo()
        idx = self.profile_combo.findText(name.strip())
        if idx >= 0:
            self.profile_combo.setCurrentIndex(idx)
        QtWidgets.QMessageBox.information(
            self, self.tr_.t("info"),
            self.tr_.t("profile_saved", name=name.strip()),
        )

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
            self._refresh_all()

    # ------------------------------------------------------------- merge
    def _do_merge(self):
        template = self.template_edit.text().strip()
        if not template or not Path(template).exists():
            QtWidgets.QMessageBox.warning(
                self, self.tr_.t("warning"), self.tr_.t("no_template"))
            return
        if not self.rows:
            QtWidgets.QMessageBox.warning(
                self, self.tr_.t("warning"), self.tr_.t("no_files"))
            return
        selections: List[Tuple[str, StationBlock]] = []
        for i, (path, block) in enumerate(self.rows):
            it = self.table.item(i, self.COL_USE)
            if it and it.checkState() == QtCore.Qt.CheckState.Checked:
                selections.append((path, block))
        if not selections:
            QtWidgets.QMessageBox.warning(
                self, self.tr_.t("warning"), self.tr_.t("no_selection"))
            return

        output = self.output_edit.text().strip()
        if not output:
            output = str(OUTPUT_DIR / "Merged_PFMEA.xlsx")
            self.output_edit.setText(output)

        self.merge_btn.setEnabled(False)
        self.progress.setValue(0)
        self.status.showMessage(self.tr_.t("processing"))

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
            self.status.showMessage(msg)

    def _on_finished(self, out_path: str):
        self.merge_btn.setEnabled(True)
        self.progress.setValue(100)
        self.status.showMessage(self.tr_.t("ready"))
        QtWidgets.QMessageBox.information(
            self, self.tr_.t("info"),
            self.tr_.t("merge_success", path=out_path),
        )
        # open the folder for convenience
        try:
            if os.name == "nt":
                os.startfile(str(Path(out_path).parent))  # type: ignore
        except Exception:
            pass

    def _on_failed(self, err: str):
        self.merge_btn.setEnabled(True)
        self.status.showMessage(self.tr_.t("ready"))
        QtWidgets.QMessageBox.critical(
            self, self.tr_.t("error"),
            self.tr_.t("merge_error", err=err),
        )
