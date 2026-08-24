"""
Configuration constants and default settings for PFMEA Merger.
"""
from dataclasses import dataclass, asdict, field
from typing import List, Optional
import json
from pathlib import Path


DEFAULT_HEADER_ROWS = 8          # Rows 1..8 -> Header (title + column names)
DEFAULT_DATA_START_ROW = 9       # Row 9 onwards -> station data
DEFAULT_OPC_COLUMN = 1           # Column A = OPC code
DEFAULT_NAME_COLUMN = 2          # Column B = Station name
DEFAULT_SHEET_NAME = "PFMEA"
DEFAULT_HISTORY_SHEET = "History"
DEFAULT_FOOTER_MARKERS = [
    "تهیه کنندگان",
    "تایید کننده",
    "تصویب کننده",
    "توزيع نسخ",
    "توزیع نسخ",
    "علامت",
    "بازنگری فرم",
    "کد فرم",
]
DEFAULT_MAX_OPC_LEN = 20    # anything longer in column A is probably not an OPC code

APP_ROOT = Path(__file__).resolve().parent.parent
PROFILES_DIR = APP_ROOT / "profiles"
TEMPLATES_DIR = APP_ROOT / "templates"
OUTPUT_DIR = APP_ROOT / "output"
SETTINGS_FILE = APP_ROOT / "settings.json"

for _p in (PROFILES_DIR, TEMPLATES_DIR, OUTPUT_DIR):
    _p.mkdir(parents=True, exist_ok=True)


@dataclass
class MergeSettings:
    """Per-product / per-template merge settings."""
    header_rows: int = DEFAULT_HEADER_ROWS
    data_start_row: int = DEFAULT_DATA_START_ROW
    opc_column: int = DEFAULT_OPC_COLUMN
    name_column: int = DEFAULT_NAME_COLUMN
    sheet_name: str = DEFAULT_SHEET_NAME
    history_sheet: str = DEFAULT_HISTORY_SHEET
    footer_markers: List[str] = field(default_factory=lambda: list(DEFAULT_FOOTER_MARKERS))
    max_opc_length: int = DEFAULT_MAX_OPC_LEN

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "MergeSettings":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class AppSettings:
    """Global app settings."""
    language: str = "fa"            # 'fa' or 'en'
    last_template: str = ""
    last_input_dir: str = ""
    last_output_dir: str = ""
    last_profile: str = ""

    @classmethod
    def load(cls) -> "AppSettings":
        if SETTINGS_FILE.exists():
            try:
                data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except Exception:
                return cls()
        return cls()

    def save(self) -> None:
        SETTINGS_FILE.write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
