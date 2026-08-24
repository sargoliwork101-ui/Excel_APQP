"""
PFMEA Merger - APQP process tool
Entry point.
Run:  python -m pfmea_merger.app
"""
from __future__ import annotations

import sys
from PyQt6 import QtWidgets, QtGui

from pfmea_merger.ui.main_window import MainWindow


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("PFMEA Merger")
    app.setOrganizationName("APQP Tools")

    # Try to pick a font that renders Persian well
    fonts_to_try = ["Tahoma", "IRANSans", "Vazirmatn", "B Nazanin", "Segoe UI"]
    for fam in fonts_to_try:
        if fam in QtGui.QFontDatabase.families():
            f = app.font()
            f.setFamily(fam)
            f.setPointSize(10)
            app.setFont(f)
            break

    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
