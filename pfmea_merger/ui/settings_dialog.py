"""
Settings dialog: header rows / columns / footer markers / language.
"""
from PyQt6 import QtCore, QtWidgets
from openpyxl.utils import get_column_letter, column_index_from_string

from ..core.config import MergeSettings, AppSettings
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
                 merge_settings: MergeSettings, app_settings: AppSettings):
        super().__init__(parent)
        self.tr_ = translator
        self.merge_settings = merge_settings
        self.app_settings = app_settings

        self.setWindowTitle(self.tr_.t("settings_title"))
        self.setLayoutDirection(
            QtCore.Qt.LayoutDirection.RightToLeft if translator.is_rtl()
            else QtCore.Qt.LayoutDirection.LeftToRight
        )
        self._build_ui()
        self._load_values()

    # ------------------------------------------------------------------
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
        form.setContentsMargins(14, 12, 14, 12)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        self.header_rows_spin = QtWidgets.QSpinBox()
        self.header_rows_spin.setRange(1, 50)

        self.data_start_spin = QtWidgets.QSpinBox()
        self.data_start_spin.setRange(1, 100)

        # Used while detecting station/OPC rows. 20 is the current default,
        # but different PFMEA templates may use longer identifiers.
        self.max_opc_length_spin = QtWidgets.QSpinBox()
        self.max_opc_length_spin.setRange(1, 200)
        self.max_opc_length_spin.setSuffix(" کاراکتر" if translator.is_rtl() else " chars")

        self.opc_col_edit = QtWidgets.QLineEdit()
        self.opc_col_edit.setMaxLength(3)
        self.opc_col_edit.setFixedWidth(80)

        self.name_col_edit = QtWidgets.QLineEdit()
        self.name_col_edit.setMaxLength(3)
        self.name_col_edit.setFixedWidth(80)

        self.sheet_edit = QtWidgets.QLineEdit()
        self.history_edit = QtWidgets.QLineEdit()

        self.footer_edit = QtWidgets.QPlainTextEdit()
        self.footer_edit.setFixedHeight(100)

        self.lang_combo = QtWidgets.QComboBox()
        self.lang_combo.addItem("فارسی", "fa")
        self.lang_combo.addItem("English", "en")

        form.addRow(self.tr_.t("language_lbl"), self.lang_combo)
        form.addRow(self.tr_.t("sheet_name_lbl"), self.sheet_edit)
        form.addRow(self.tr_.t("history_sheet_lbl"), self.history_edit)
        form.addRow(self.tr_.t("header_rows_lbl"), self.header_rows_spin)
        form.addRow(self.tr_.t("data_start_row_lbl"), self.data_start_spin)
        form.addRow(self.tr_.t("max_opc_length_lbl"), self.max_opc_length_spin)
        form.addRow(self.tr_.t("opc_col_lbl"), self.opc_col_edit)
        form.addRow(self.tr_.t("name_col_lbl"), self.name_col_edit)
        form.addRow(self.tr_.t("footer_markers_lbl"), self.footer_edit)

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

        self.resize(470, 520)

    # ------------------------------------------------------------------
    def _load_values(self):
        self.header_rows_spin.setValue(self.merge_settings.header_rows)
        self.data_start_spin.setValue(self.merge_settings.data_start_row)
        self.max_opc_length_spin.setValue(self.merge_settings.max_opc_length)
        self.opc_col_edit.setText(_col_to_letter(self.merge_settings.opc_column))
        self.name_col_edit.setText(_col_to_letter(self.merge_settings.name_column))
        self.sheet_edit.setText(self.merge_settings.sheet_name)
        self.history_edit.setText(self.merge_settings.history_sheet)
        self.footer_edit.setPlainText("\n".join(self.merge_settings.footer_markers))
        idx = self.lang_combo.findData(self.app_settings.language)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)

    def apply_to(self) -> tuple[MergeSettings, AppSettings]:
        self.merge_settings.header_rows = self.header_rows_spin.value()
        self.merge_settings.data_start_row = self.data_start_spin.value()
        self.merge_settings.max_opc_length = self.max_opc_length_spin.value()
        self.merge_settings.opc_column = _letter_to_col(self.opc_col_edit.text())
        self.merge_settings.name_column = _letter_to_col(self.name_col_edit.text())
        self.merge_settings.sheet_name = self.sheet_edit.text().strip() or "PFMEA"
        self.merge_settings.history_sheet = self.history_edit.text().strip() or "History"
        markers = [
            m.strip() for m in self.footer_edit.toPlainText().splitlines()
            if m.strip()
        ]
        self.merge_settings.footer_markers = markers
        self.app_settings.language = self.lang_combo.currentData() or "fa"
        return self.merge_settings, self.app_settings
