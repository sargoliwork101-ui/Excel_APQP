"""
PFMEA Merger - APQP process tool
Entry point.

Recommended:
    cd <repo root>
    python -m pfmea_merger.app

Also supported (double-clicking / running the file directly):
    python pfmea_merger/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# When the file is executed directly (e.g. `python pfmea_merger/app.py` or
# from an IDE run button) Python only puts THIS folder on sys.path, so the
# `pfmea_merger` package can't be imported. Add the parent folder so both
# invocation styles work.
if __package__ in (None, ""):
    _here = Path(__file__).resolve().parent          # .../pfmea_merger
    _root = _here.parent                             # repo root
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

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
