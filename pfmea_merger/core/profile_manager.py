"""
Product profiles: save/load the ordered list of stations, the template
path and the merge settings for a given product so the user does not have
to reconfigure the app on every run.

Each profile is a JSON file in ./profiles/<name>.json
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Optional
import json
import re

from .config import PROFILES_DIR, MergeSettings


_SAFE = re.compile(r"[^A-Za-z0-9_\-\u0600-\u06FF ]+")


def _safe_filename(name: str) -> str:
    name = _SAFE.sub("_", name).strip() or "profile"
    return name[:80]


@dataclass
class ProductProfile:
    name: str = ""
    product_name: str = ""
    product_code: str = ""
    template_path: str = ""
    station_order: List[str] = field(default_factory=list)   # OPC codes
    settings: MergeSettings = field(default_factory=MergeSettings)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "product_name": self.product_name,
            "product_code": self.product_code,
            "template_path": self.template_path,
            "station_order": list(self.station_order),
            "settings": self.settings.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProductProfile":
        settings = MergeSettings.from_dict(d.get("settings", {}))
        return cls(
            name=d.get("name", ""),
            product_name=d.get("product_name", ""),
            product_code=d.get("product_code", ""),
            template_path=d.get("template_path", ""),
            station_order=list(d.get("station_order", [])),
            settings=settings,
        )


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
    p = profile_path(name)
    if not p.exists():
        # try by name field
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
