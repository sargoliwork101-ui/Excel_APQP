"""
Non-UI smoke test of merge_pfmea.
Picks several sample files and merges them back into one output workbook.

Usage:
    python -m pfmea_merger.tools.test_merge
"""
from pathlib import Path

from pfmea_merger.core.config import MergeSettings, OUTPUT_DIR, TEMPLATES_DIR, APP_ROOT
from pfmea_merger.core.excel_reader import analyze_workbook
from pfmea_merger.core.excel_merger import merge_pfmea


SAMPLES_DIR = APP_ROOT / "samples"
TEMPLATE = TEMPLATES_DIR / "PFMEA_SBM_SOREN_Template.xlsx"


def main():
    settings = MergeSettings()

    files = sorted(SAMPLES_DIR.glob("station_*.xlsx"))
    print(f"Found {len(files)} sample files.")

    selections = []
    for f in files:
        a = analyze_workbook(f, settings)
        if not a.is_valid:
            print(f"  ✗ {f.name}  invalid: {a.error}")
            continue
        for block in a.stations:
            selections.append((str(f), block))
            print(f"  + {block.opc_code:>5}  {block.name[:30]:30s}  rows={block.row_count}  file={f.name}")

    output = OUTPUT_DIR / "Merged_TEST.xlsx"

    def cb(pct, msg):
        print(f"  [{pct:3d}%] {msg}")

    result = merge_pfmea(
        str(TEMPLATE), selections, str(output),
        settings, merge_history=True, progress_cb=cb,
    )
    print(f"\n✔ Written: {result}")
    print(f"  Size: {Path(result).stat().st_size} bytes")


if __name__ == "__main__":
    main()
