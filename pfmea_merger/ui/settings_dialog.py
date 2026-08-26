"""
Settings dialog: header rows / columns / footer markers / language.
"""
from PyQt6 import QtCore, QtWidgets
from openpyxl.utils import get_column_letter, column_index_from_string

from ..core.config import MergeSettings, AppSettings, default_cp_settings
from ..core.i18n import Translator


def _col_to_letter(idx: int) -> str:
    try:
        return get_column_letter(int(idx))
    except Exception:
        return "A"


def _letter_to_col(letter: str) -> int:
    try:
        return column_index_from_string(letter.strip().upper())
    except Exception:
        return 1


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent, translator: Translator,
                 merge_settings: MergeSettings, app_settings: AppSettings,
                 cp_settings: MergeSettings = None):
        super().__init__(parent)
        self.tr_ = translator
        self.merge_settings = merge_settings
        self.app_settings = app_settings
        # Control Plan has its own independent settings object.
        self.cp_settings = cp_settings if cp_settings is not None \
            else default_cp_settings()

        self.setWindowTitle(self.tr_.t("settings_title"))
        self.setLayoutDirection(
            QtCore.Qt.LayoutDirection.RightToLeft if self.tr_.is_rtl()
            else QtCore.Qt.LayoutDirection.LeftToRight
        )
        self._build_ui()
        self._load_values()

    # ------------------------------------------------------------------
    def _active(self) -> MergeSettings:
        """The settings object currently being edited (PFMEA or CP)."""
        data = self.doc_combo.currentData() if hasattr(self, "doc_combo") else "pfmea"
        return self.cp_settings if data == "cp" else self.merge_settings

    def _build_ui(self):
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(12)

        title = QtWidgets.QLabel(self.tr_.t("settings_title"))
        f = title.font(); f.setPointSize(13); f.setBold(True); title.setFont(f)
        outer.addWidget(title)

        card = QtWidgets.QFrame()
        card.setObjectName("Card")
        outer.addWidget(card, 1)
        form = QtWidgets.QFormLayout(card)
        self.form = form
        form.setContentsMargins(14, 12, 14, 12)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        self.header_rows_spin = QtWidgets.QSpinBox()
        self.header_rows_spin.setRange(1, 50)

        self.data_start_spin = QtWidgets.QSpinBox()
        self.data_start_spin.setRange(1, 100)

        # Percentage used by the AQ2 formula for the highest RPN values.
        self.rpn_top_percent_spin = QtWidgets.QSpinBox()
        self.rpn_top_percent_spin.setRange(1, 100)
        self.rpn_top_percent_spin.setSuffix("٪" if self.tr_.is_rtl() else "%")

        self.failure_row_height_spin = QtWidgets.QSpinBox()
        self.failure_row_height_spin.setRange(0, 400)
        self.failure_row_height_spin.setSuffix(" پیکسل" if self.tr_.is_rtl() else " px")
        self.failure_row_height_spin.setSpecialValueText("خودکار" if self.tr_.is_rtl() else "Auto")

        self.failure_column_width_spin = QtWidgets.QSpinBox()
        self.failure_column_width_spin.setRange(0, 800)
        self.failure_column_width_spin.setSuffix(" پیکسل" if self.tr_.is_rtl() else " px")
        self.failure_column_width_spin.setSpecialValueText("خودکار" if self.tr_.is_rtl() else "Auto")

        self.opc_col_edit = QtWidgets.QLineEdit()
        self.opc_col_edit.setMaxLength(3)
        self.opc_col_edit.setFixedWidth(80)

        self.name_col_edit = QtWidgets.QLineEdit()
        self.name_col_edit.setMaxLength(3)
        self.name_col_edit.setFixedWidth(80)

        self.failure_mode_col_edit = QtWidgets.QLineEdit()
        self.failure_mode_col_edit.setMaxLength(3)
        self.failure_mode_col_edit.setFixedWidth(80)
        self.so_col_edit = QtWidgets.QLineEdit()
        self.so_col_edit.setMaxLength(3)
        self.so_col_edit.setFixedWidth(80)
        self.rpn_col_edit = QtWidgets.QLineEdit()
        self.rpn_col_edit.setMaxLength(3)
        self.rpn_col_edit.setFixedWidth(80)
        self.aq2_cell_edit = QtWidgets.QLineEdit()
        self.aq2_cell_edit.setMaxLength(10)
        self.aq2_cell_edit.setFixedWidth(100)

        self.sheet_edit = QtWidgets.QLineEdit()
        self.history_edit = QtWidgets.QLineEdit()

        self.footer_edit = QtWidgets.QPlainTextEdit()
        self.footer_edit.setFixedHeight(100)

        self.lang_combo = QtWidgets.QComboBox()
        self.lang_combo.addItem("فارسی", "fa")
        self.lang_combo.addItem("English", "en")

        # Document type switcher: PFMEA and CP keep separate settings.
        self.doc_combo = QtWidgets.QComboBox()
        self.doc_combo.addItem("PFMEA", "pfmea")
        self.doc_combo.addItem("Control Plan (CP)", "cp")
        self.doc_combo.currentIndexChanged.connect(self._on_doc_type_changed)

        form.addRow(self.tr_.t("doc_type_lbl"), self.doc_combo)
        form.addRow(self.tr_.t("language_lbl"), self.lang_combo)
        form.addRow(self.tr_.t("sheet_name_lbl"), self.sheet_edit)
        form.addRow(self.tr_.t("history_sheet_lbl"), self.history_edit)
        form.addRow(self.tr_.t("header_rows_lbl"), self.header_rows_spin)
        form.addRow(self.tr_.t("data_start_row_lbl"), self.data_start_spin)
        form.addRow(self.tr_.t("rpn_top_percent_lbl"), self.rpn_top_percent_spin)
        form.addRow(self.tr_.t("failure_row_height_lbl"), self.failure_row_height_spin)
        form.addRow(self.tr_.t("failure_column_width_lbl"), self.failure_column_width_spin)
        form.addRow(self.tr_.t("opc_col_lbl"), self.opc_col_edit)
        form.addRow(self.tr_.t("name_col_lbl"), self.name_col_edit)
        form.addRow(self.tr_.t("failure_mode_col_lbl"), self.failure_mode_col_edit)
        form.addRow(self.tr_.t("so_col_lbl"), self.so_col_edit)
        form.addRow(self.tr_.t("rpn_col_lbl"), self.rpn_col_edit)
        form.addRow(self.tr_.t("aq2_cell_lbl"), self.aq2_cell_edit)
        form.addRow(self.tr_.t("footer_markers_lbl"), self.footer_edit)

        # PFMEA-only fields (SO/RPN/AQ2 formulas and failure-mode layout) do
        # not apply to Control Plan; their rows hide when CP is selected.
        self._pfmea_only_widgets = (
            self.rpn_top_percent_spin,
            self.failure_row_height_spin,
            self.failure_column_width_spin,
            self.failure_mode_col_edit,
            self.so_col_edit,
            self.rpn_col_edit,
            self.aq2_cell_edit,
        )

        settings_tools = QtWidgets.QHBoxLayout()
        self.save_defaults_btn = QtWidgets.QPushButton(self.tr_.t("save_settings"))
        self.restore_defaults_btn = QtWidgets.QPushButton(self.tr_.t("restore_settings"))
        settings_tools.addWidget(self.save_defaults_btn)
        settings_tools.addWidget(self.restore_defaults_btn)
        settings_tools.addStretch(1)
        outer.addLayout(settings_tools)
        self.save_defaults_btn.clicked.connect(self._save_defaults)
        self.restore_defaults_btn.clicked.connect(self._restore_defaults)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        ok_btn = btns.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        if ok_btn is not None:
            ok_btn.setProperty("primary", True)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        outer.addWidget(btns)

        self.resize(560, 700)
        self.setMinimumSize(520, 650)

    # ------------------------------------------------------------------
    def _on_doc_type_changed(self):
        # Apply pending edits to the previous type is not needed here:
        # values are only committed via apply_to()/save on the active type.
        self._load_values()

    def _apply_doc_visibility(self):
        is_cp = self.doc_combo.currentData() == "cp"
        for w in getattr(self, "_pfmea_only_widgets", ()):
            try:
                self.form.setRowVisible(w, not is_cp)
            except Exception:
                w.setEnabled(not is_cp)

    def _load_values(self):
        s = self._active()
        self.header_rows_spin.setValue(s.header_rows)
        self.data_start_spin.setValue(s.data_start_row)
        self.rpn_top_percent_spin.setValue(s.rpn_top_percent)
        self.failure_row_height_spin.setValue(s.failure_row_height)
        self.failure_column_width_spin.setValue(s.failure_column_width)
        self.opc_col_edit.setText(_col_to_letter(s.opc_column))
        self.name_col_edit.setText(_col_to_letter(s.name_column))
        self.failure_mode_col_edit.setText(_col_to_letter(s.failure_mode_column))
        self.so_col_edit.setText(_col_to_letter(s.so_column))
        self.rpn_col_edit.setText(_col_to_letter(s.rpn_column))
        self.aq2_cell_edit.setText(s.aq2_cell)
        self.sheet_edit.setText(s.sheet_name)
        self.history_edit.setText(s.history_sheet)
        markers = s.footer_markers
        if not isinstance(markers, list):
            markers = []
        self.footer_edit.setPlainText("\n".join(str(m) for m in markers))
        idx = self.lang_combo.findData(self.app_settings.language)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        self._apply_doc_visibility()

    def _save_defaults(self):
        self.apply_to()
        if self._active() is self.cp_settings:
            self.app_settings.saved_cp_merge_settings = self.cp_settings.to_dict()
        else:
            self.app_settings.saved_merge_settings = self.merge_settings.to_dict()
        self.app_settings.save()

    def _restore_defaults(self):
        if self._active() is self.cp_settings:
            saved = self.app_settings.saved_cp_merge_settings
            if saved:
                cp = MergeSettings.from_dict(saved)
                if cp.doc_type == "cp":
                    self.cp_settings = cp
            self._load_values()
            return
        saved = self.app_settings.saved_merge_settings
        if saved:
            self.merge_settings = MergeSettings.from_dict(saved)
        self._load_values()

    def apply_to(self) -> tuple[MergeSettings, MergeSettings, AppSettings]:
        s = self._active()
        s.header_rows = self.header_rows_spin.value()
        s.data_start_row = self.data_start_spin.value()
        s.rpn_top_percent = self.rpn_top_percent_spin.value()
        s.failure_row_height = self.failure_row_height_spin.value()
        s.failure_column_width = self.failure_column_width_spin.value()
        s.opc_column = _letter_to_col(self.opc_col_edit.text())
        s.name_column = _letter_to_col(self.name_col_edit.text())
        s.failure_mode_column = _letter_to_col(self.failure_mode_col_edit.text())
        s.so_column = _letter_to_col(self.so_col_edit.text())
        s.rpn_column = _letter_to_col(self.rpn_col_edit.text())
        s.aq2_cell = self.aq2_cell_edit.text().strip().upper() or "AQ2"
        if s is self.cp_settings:
            s.sheet_name = self.sheet_edit.text().strip() or "برنامه کنترل"
            s.history_sheet = self.history_edit.text().strip() or "تغییرات"
        else:
            s.sheet_name = self.sheet_edit.text().strip() or "PFMEA"
            s.history_sheet = self.history_edit.text().strip() or "History"
        markers = [
            m.strip() for m in self.footer_edit.toPlainText().splitlines()
            if m.strip()
        ]
        s.footer_markers = markers
        self.app_settings.language = self.lang_combo.currentData() or "fa"
        return self.merge_settings, self.cp_settings, self.app_settings
