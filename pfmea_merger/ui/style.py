"""
Dark theme + modern styling for the PFMEA Merger UI.

Applied via `QApplication.setStyle('Fusion')` and a QSS stylesheet.
"""
from PyQt6 import QtCore, QtGui, QtWidgets


# Palette: deep navy surfaces with a violet/cyan accent system.
# The contrast is intentionally softer than pure black so long Excel sessions
# are easier on the eyes.
BG          = "#111827"
BG_ELEV     = "#172235"
BG_ELEV2    = "#1e2d45"
BORDER      = "#30435f"
BORDER_SOFT = "#263852"
TEXT        = "#eef4ff"
TEXT_DIM    = "#9aabc3"
PRIMARY     = "#6d5dfc"
PRIMARY_HOV = "#8275ff"
PRIMARY_PRS = "#5648df"
DANGER      = "#ff647c"
SUCCESS     = "#35d07f"
ACCENT      = "#28c7d9"
ROW_ALT     = "#142036"
SEL_BG      = "#3e3aa8"


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
    font-family: "Segoe UI", "Tahoma", sans-serif;
    font-size: 10pt;
}}

QMainWindow {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {BG}, stop:1 #0d1524);
}}

QDialog {{
    background: {BG};
}}

QMainWindow, QDialog {{
    color: {TEXT};
}}

QLabel {{
    color: {TEXT};
    background: transparent;
}}

QLabel[muted="true"] {{
    color: {TEXT_DIM};
}}

QLabel#AppTitle {{
    color: #f4f7ff;
    letter-spacing: 0.3px;
}}

QToolTip {{
    background: {BG_ELEV2};
    color: {TEXT};
    border: 1px solid {BORDER};
    padding: 6px 8px;
    border-radius: 4px;
}}

/* ----- Line edits / combo / spin ----- */
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox,
QAbstractSpinBox {{
    background: {BG_ELEV};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 9px;
    padding: 7px 10px;
    selection-background-color: {SEL_BG};
    selection-color: white;
    min-height: 22px;
}}

QLineEdit:hover, QPlainTextEdit:hover, QTextEdit:hover,
QComboBox:hover, QSpinBox:hover {{
    border-color: #496181;
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
    border-radius: 9px;
    padding: 8px 15px;
    min-height: 19px;
}}
QPushButton:focus {{
    border: 1px solid {ACCENT};
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
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {BG_ELEV}, stop:1 #142036);
    border: 1px solid {BORDER_SOFT};
    border-radius: 14px;
}}

/* ----- Table ----- */
QTableWidget, QTableView {{
    background: #132039;
    alternate-background-color: {ROW_ALT};
    color: {TEXT};
    gridline-color: transparent;
    border: 1px solid {BORDER};
    border-radius: 11px;
    selection-background-color: {SEL_BG};
    selection-color: white;
    outline: 0;
    padding: 2px;
}}
QTableWidget::item:hover, QTableView::item:hover {{
    background: #253759;
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
    background: #223452;
    color: #dce8ff;
    padding: 10px 9px;
    border: 0;
    border-bottom: 2px solid {PRIMARY};
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
