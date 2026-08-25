"""Build the bundled Control Plan example output."""
from pathlib import Path
from pfmea_merger.core.cp_merger import merge_cp
from pfmea_merger.core.config import APP_ROOT, TEMPLATES_DIR, OUTPUT_DIR

if __name__ == "__main__":
    source = APP_ROOT.parent / "sample data" / "CP"
    files = [source / "CP_A125.xlsx", source / "CP_A130.xlsx"]
    result = merge_cp(TEMPLATES_DIR / "CP_SBM_SOREN_Template.xlsx", files,
                      OUTPUT_DIR / "Merged_CP.xlsx")
    print(result)
