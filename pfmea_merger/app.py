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

# When the file is executed directly (`python pfmea_merger/app.py` or from an
# IDE Run button) only THIS folder is on sys.path, so `import pfmea_merger`
# would fail. Add the parent folder so both invocation styles work.
if __package__ in (None, ""):
    _here = Path(__file__).resolve().parent          # .../pfmea_merger
    _root = _here.parent                             # repo root
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from PyQt6 import QtWidgets, QtGui, QtCore

from pfmea_merger.ui.main_window import MainWindow
from pfmea_merger.ui.style import apply_dark_theme


def _install_excepthook() -> None:
    """Never let a bug in a slot/callback close the whole application.

    PyQt6 calls qFatal() — the app simply disappears — whenever an exception
    escapes a slot or event handler while the default sys.excepthook is
    installed. Replacing the hook keeps the app alive and shows the error
    to the user instead.
    """
    def hook(exc_type, exc_value, tb):
        import traceback
        text = "".join(traceback.format_exception(exc_type, exc_value, tb))
        try:
            sys.stderr.write(text)
        except Exception:
            pass
        try:
            box = QtWidgets.QMessageBox()
            box.setIcon(QtWidgets.QMessageBox.Icon.Critical)
            box.setWindowTitle("Internal error / خطای داخلی")
            box.setText(
                "An unexpected error occurred, but the program stays open.\n"
                "خطای غیرمنتظره‌ای رخ داد، اما برنامه باز می‌ماند.")
            box.setDetailedText(text)
            box.exec()
        except Exception:
            pass

    sys.excepthook = hook


def main() -> int:
    # High-DPI is on by default in Qt6.
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("PFMEA & CP Merger")
    app.setOrganizationName("APQP Tools")
    _install_excepthook()

    # Pick a font that renders Persian well
    fonts_to_try = ["Segoe UI", "Tahoma", "IRANSans", "Vazirmatn", "B Nazanin"]
    for fam in fonts_to_try:
        if fam in QtGui.QFontDatabase.families():
            f = QtGui.QFont(fam, 10)
            app.setFont(f)
            break

    apply_dark_theme(app)

    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
