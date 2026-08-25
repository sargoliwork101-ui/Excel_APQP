"""
Product profiles: save/load the ordered list of stations, their
enabled/disabled state, template path and merge settings so the user
doesn't have to reconfigure the app on every run.

Each profile is a JSON file in ./profiles/<name>.json
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional
import json
import re

from .config import PROFILES_DIR, MergeSettings


_SAFE = re.compile(r"[^A-Za-z0-9_\-\u0600-\u06FF ]+")


def _safe_filename(name: str) -> str:
    name = _SAFE.sub("_", name).strip() or "profile"
    return name[:80]


@dataclass
class StationEntry:
    """A saved station in a profile: its OPC code, name and check state."""
    opc: str
    name: str = ""
    enabled: bool = True

    def to_dict(self) -> dict:
        return {"opc": self.opc, "name": self.name, "enabled": self.enabled}

    @classmethod
    def from_dict(cls, d) -> "StationEntry":
        if isinstance(d, str):
            # backwards compat: old profiles stored plain strings
            return cls(opc=d, name="", enabled=True)
        return cls(
            opc=str(d.get("opc", "")),
            name=str(d.get("name", "")),
            enabled=bool(d.get("enabled", True)),
        )


@dataclass
class ProductProfile:
    name: str = ""
    product_name: str = ""
    product_code: str = ""
    template_path: str = ""
    stations: List[StationEntry] = field(default_factory=list)
    # Optional per-station row heights, keyed by OPC. Kept separate from
    # global settings so every product profile can preserve its own layout.
    row_heights: Dict[str, int] = field(default_factory=dict)
    settings: MergeSettings = field(default_factory=MergeSettings)

    # ---- helpers ---------------------------------------------------
    @property
    def station_order(self) -> List[str]:
        """OPC codes in profile order (backwards-compat helper)."""
        return [s.opc for s in self.stations]

    def enabled_set(self) -> set:
        return {s.opc for s in self.stations if s.enabled}

    def order_index(self, opc: str) -> int:
        for i, s in enumerate(self.stations):
            if s.opc == opc:
                return i
        return 10_000

    # ---- (de)serialisation ----------------------------------------
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "product_name": self.product_name,
            "product_code": self.product_code,
            "template_path": self.template_path,
            "stations": [s.to_dict() for s in self.stations],
            "row_heights": self.row_heights,
            "settings": self.settings.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProductProfile":
        settings = MergeSettings.from_dict(d.get("settings", {}))
        # Prefer new "stations" field; fall back to old "station_order".
        raw_stations = d.get("stations")
        if raw_stations is None:
            raw_stations = d.get("station_order", [])
        stations = [StationEntry.from_dict(x) for x in raw_stations]
        return cls(
            name=d.get("name", ""),
            product_name=d.get("product_name", ""),
            product_code=d.get("product_code", ""),
            template_path=d.get("template_path", ""),
            stations=stations,
            row_heights={str(k): int(v) for k, v in d.get("row_heights", {}).items()
                         if str(v).isdigit() and int(v) > 0},
            settings=settings,
        )


# ---------------------------------------------------------------------------
# File-system operations

def profile_path(name: str) -> Path:
    return PROFILES_DIR / f"{_safe_filename(name)}.json"


def list_profiles() -> List[str]:
    files = sorted(PROFILES_DIR.glob("*.json"))
    names: List[str] = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            names.append(data.get("name") or f.stem)
        except Exception:
            names.append(f.stem)
    return names


def load_profile(name: str) -> Optional[ProductProfile]:
    if not name:
        return None
    p = profile_path(name)
    if not p.exists():
        for f in PROFILES_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if data.get("name") == name:
                    return ProductProfile.from_dict(data)
            except Exception:
                continue
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return ProductProfile.from_dict(data)
    except Exception:
        return None


def save_profile(profile: ProductProfile) -> Path:
    if not profile.name:
        profile.name = profile.product_name or "profile"
    p = profile_path(profile.name)
    p.write_text(
        json.dumps(profile.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return p


def delete_profile(name: str) -> bool:
    p = profile_path(name)
    if p.exists():
        p.unlink()
        return True
    for f in PROFILES_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("name") == name:
                f.unlink()
                return True
        except Exception:
            continue
    return False
