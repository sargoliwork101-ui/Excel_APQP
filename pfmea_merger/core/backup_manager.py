"""Backup and restore for user data, profiles, templates, and settings."""
from __future__ import annotations

from pathlib import Path
import json
import shutil
import tempfile
import zipfile

from .config import APP_ROOT, PROFILES_DIR, TEMPLATES_DIR, SETTINGS_FILE

BACKUP_FORMAT = 1


def create_backup(destination: str | Path) -> str:
    """Create a portable ZIP containing all user-created application data."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "format": BACKUP_FORMAT,
        "application": "PFMEA Merger",
        "contents": ["settings.json", "profiles/", "templates/"],
    }
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("backup_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        if SETTINGS_FILE.exists():
            archive.write(SETTINGS_FILE, "settings.json")
        for root, prefix in ((PROFILES_DIR, "profiles"), (TEMPLATES_DIR, "templates")):
            if not root.exists():
                continue
            for file in root.rglob("*"):
                if file.is_file() and file.suffix.lower() in (".json", ".xlsx", ".xlsm"):
                    archive.write(file, f"{prefix}/{file.relative_to(root).as_posix()}")
    return str(destination)


def restore_backup(source: str | Path) -> dict:
    """Restore user data from a backup ZIP without allowing path traversal."""
    source = Path(source)
    with zipfile.ZipFile(source, "r") as archive:
        try:
            manifest = json.loads(archive.read("backup_manifest.json").decode("utf-8"))
        except Exception as exc:
            raise ValueError("این فایل بک‌آپ معتبر PFMEA Merger نیست.") from exc
        if manifest.get("format") != BACKUP_FORMAT:
            raise ValueError("نسخه فایل بک‌آپ با این نسخه برنامه سازگار نیست.")
        allowed = {"settings.json"}
        allowed_prefixes = ("profiles/", "templates/")
        for name in archive.namelist():
            if name in allowed or name.startswith(allowed_prefixes):
                if Path(name).is_absolute() or ".." in Path(name).parts:
                    raise ValueError("مسیر غیرمجاز داخل فایل بک‌آپ پیدا شد.")
            elif name != "backup_manifest.json":
                raise ValueError("فایل بک‌آپ شامل محتوای ناشناخته است.")
        with tempfile.TemporaryDirectory(dir=str(APP_ROOT)) as temp_dir:
            temp = Path(temp_dir)
            archive.extractall(temp)
            restored = {"profiles": 0, "templates": 0, "settings": False}
            settings = temp / "settings.json"
            if settings.exists():
                shutil.copy2(settings, SETTINGS_FILE)
                restored["settings"] = True
            for folder, target in (("profiles", PROFILES_DIR), ("templates", TEMPLATES_DIR)):
                src = temp / folder
                if not src.exists():
                    continue
                target.mkdir(parents=True, exist_ok=True)
                for file in src.rglob("*"):
                    if file.is_file():
                        dest = target / file.relative_to(src)
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file, dest)
                        restored[folder] += 1
    return restored
