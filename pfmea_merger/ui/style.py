"""
Dark theme + modern styling for the PFMEA Merger UI.

Applied via `QApplication.setStyle('Fusion')` and a QSS stylesheet.
"""
from PyQt6 import QtCore, QtGui, QtWidgets


# Palette (Material-ish dark)
BG          = "#1e1f22"
BG_ELEV     = "#2b2d31"
BG_ELEV2    = "#313338"
BORDER      = "#3d3f45"
BORDER_SOFT = "#35363b"
TEXT        = "#e6e6e6"
TEXT_DIM    = "#9ba0a6"
PRIMARY     = "#5865f2"
PRIMARY_HOV = "#6c78ff"
PRIMARY_PRS = "#4750d0"
DANGER      = "#f04747"
SUCCESS     = "#3ba55d"
ACCENT      = "#00b8d4"
ROW_ALT     = "#26272b"
SEL_BG      = "#3f4beb"


def apply_dark_theme(app: QtWidgets.QApplication) -> None:
    """Apply Fusion style + dark palette + a rich QSS stylesheet."""
    app.setStyle("Fusion")

    pal = QtGui.QPalette()
    c = QtGui.QColor
    pal.setColor(QtGui.QPalette.ColorRole.Window,          c(BG))
    pal.setColor(QtGui.QPalette.ColorRole.WindowText,      c(TEXT))
    pal.setColor(QtGui.QPalette.ColorRole.Base,            c(BG_ELEV))
    pal.setColor(QtGui.QPalette.ColorRole.AlternateBase,   c(ROW_ALT))
    pal.setColor(QtGui.QPalette.ColorRole.ToolTipBase,     c(BG_ELEV2))
    pal.setColor(QtGui.QPalette.ColorRole.ToolTipText,     c(TEXT))
    pal.setColor(QtGui.QPalette.ColorRole.Text,            c(TEXT))
    pal.setColor(QtGui.QPalette.ColorRole.Button,          c(BG_ELEV2))
    pal.setColor(QtGui.QPalette.ColorRole.ButtonText,      c(TEXT))
    pal.setColor(QtGui.QPalette.ColorRole.BrightText,      c("#ffffff"))
    pal.setColor(QtGui.QPalette.ColorRole.Highlight,       c(SEL_BG))
    pal.setColor(QtGui.QPalette.ColorRole.HighlightedText, c("#ffffff"))
    pal.setColor(QtGui.QPalette.ColorRole.Link,            c(ACCENT))
    pal.setColor(QtGui.QPalette.ColorRole.PlaceholderText, c(TEXT_DIM))

    # disabled variants
    pal.setColor(QtGui.QPalette.ColorGroup.Disabled,
                 QtGui.QPalette.ColorRole.Text,       c("#6b6f75"))
    pal.setColor(QtGui.QPalette.ColorGroup.Disabled,
                 QtGui.QPalette.ColorRole.ButtonText, c("#6b6f75"))
    pal.setColor(QtGui.QPalette.ColorGroup.Disabled,
                 QtGui.QPalette.ColorRole.WindowText, c("#6b6f75"))
    app.setPalette(pal)

    app.setStyleSheet(_STYLESHEET)


_STYLESHEET = f"""
* {{
    font-size: 10pt;
}}

QMainWindow, QDialog {{
    background: {BG};
    color: {TEXT};
}}

QLabel {{
    color: {TEXT};
    background: transparent;
}}

QLabel[muted="true"] {{
    color: {TEXT_DIM};
}}

QToolTip {{
    background: {BG_ELEV2};
    color: {TEXT};
    border: 1px solid {BORDER};
    padding: 6px 8px;
    border-radius: 4px;
}}

/* ----- Line edits / combo / spin ----- */
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {BG_ELEV};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 8px;
    selection-background-color: {SEL_BG};
    selection-color: white;
}}

QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus,
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {PRIMARY};
}}

QLineEdit[readOnly="true"] {{
    background: {BG_ELEV2};
    color: {TEXT_DIM};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: right center;
    width: 22px;
    border: none;
    background: transparent;
}}

QComboBox QAbstractItemView {{
    background: {BG_ELEV2};
    color: {TEXT};
    border: 1px solid {BORDER};
    selection-background-color: {SEL_BG};
    selection-color: white;
    outline: 0;
    padding: 4px;
}}

/* ----- Buttons ----- */
QPushButton {{
    background: {BG_ELEV2};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 7px 14px;
    min-height: 18px;
}}
QPushButton:hover {{
    background: #3a3c42;
    border: 1px solid #4b4d54;
}}
QPushButton:pressed {{
    background: #26272b;
}}
QPushButton:disabled {{
    color: #6b6f75;
    background: #2a2b2f;
    border: 1px solid #33353a;
}}

QPushButton[primary="true"] {{
    background: {PRIMARY};
    color: white;
    border: 1px solid {PRIMARY};
    font-weight: 600;
}}
QPushButton[primary="true"]:hover {{
    background: {PRIMARY_HOV};
    border: 1px solid {PRIMARY_HOV};
}}
QPushButton[primary="true"]:pressed {{
    background: {PRIMARY_PRS};
    border: 1px solid {PRIMARY_PRS};
}}
QPushButton[primary="true"]:disabled {{
    background: #3b3f5a;
    border: 1px solid #3b3f5a;
    color: #9095b3;
}}

QPushButton[danger="true"] {{
    background: transparent;
    color: {DANGER};
    border: 1px solid #55302f;
}}
QPushButton[danger="true"]:hover {{
    background: rgba(240,71,71,0.12);
    border: 1px solid {DANGER};
}}

QPushButton[icon-btn="true"] {{
    padding: 4px 8px;
    min-width: 32px;
}}

/* ----- Group / frame ----- */
QGroupBox {{
    background: transparent;
    border: 1px solid {BORDER_SOFT};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 6px;
    color: {TEXT_DIM};
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}}

QFrame#Card {{
    background: {BG_ELEV};
    border: 1px solid {BORDER_SOFT};
    border-radius: 10px;
}}

/* ----- Table ----- */
QTableWidget, QTableView {{
    background: {BG_ELEV};
    alternate-background-color: {ROW_ALT};
    color: {TEXT};
    gridline-color: {BORDER_SOFT};
    border: 1px solid {BORDER_SOFT};
    border-radius: 8px;
    selection-background-color: {SEL_BG};
    selection-color: white;
    outline: 0;
}}
QTableWidget::item, QTableView::item {{
    padding: 4px 8px;
    border: none;
}}
QTableWidget::item:selected, QTableView::item:selected {{
    background: {SEL_BG};
    color: white;
}}

QHeaderView::section {{
    background: {BG_ELEV2};
    color: {TEXT};
    padding: 8px;
    border: 0;
    border-bottom: 1px solid {BORDER};
    font-weight: 600;
}}
QHeaderView::section:hover {{
    background: #3a3c42;
}}

QTableCornerButton::section {{
    background: {BG_ELEV2};
    border: 0;
    border-bottom: 1px solid {BORDER};
}}

/* ----- CheckBox ----- */
QCheckBox {{
    color: {TEXT};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid #55575d;
    border-radius: 4px;
    background: {BG_ELEV};
}}
QCheckBox::indicator:hover {{
    border: 1px solid {PRIMARY};
}}
QCheckBox::indicator:checked {{
    background: {PRIMARY};
    border: 1px solid {PRIMARY};
    image: none;
}}
QCheckBox::indicator:checked:hover {{
    background: {PRIMARY_HOV};
    border: 1px solid {PRIMARY_HOV};
}}

/* ----- ProgressBar ----- */
QProgressBar {{
    background: {BG_ELEV2};
    border: 1px solid {BORDER_SOFT};
    border-radius: 6px;
    text-align: center;
    color: {TEXT};
    height: 20px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {PRIMARY}, stop:1 {ACCENT});
    border-radius: 6px;
}}

/* ----- ScrollBar ----- */
QScrollBar:vertical {{
    background: transparent;
    width: 12px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: #45474d;
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: #55575d; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QScrollBar:horizontal {{
    background: transparent;
    height: 12px;
    margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: #45474d;
    border-radius: 5px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{ background: #55575d; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ----- Status bar ----- */
QStatusBar {{
    background: {BG_ELEV2};
    color: {TEXT_DIM};
    border-top: 1px solid {BORDER_SOFT};
}}

/* ----- Menu / MessageBox ----- */
QMenu {{
    background: {BG_ELEV2};
    color: {TEXT};
    border: 1px solid {BORDER};
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 20px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background: {SEL_BG};
    color: white;
}}

QMessageBox {{
    background: {BG_ELEV};
    color: {TEXT};
}}
QMessageBox QLabel {{
    color: {TEXT};
}}

QDialog {{
    background: {BG};
}}
QDialogButtonBox QPushButton {{
    min-width: 90px;
}}

/* Splitter */
QSplitter::handle {{
    background: {BORDER_SOFT};
}}
"""
