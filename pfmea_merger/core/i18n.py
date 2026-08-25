"""
Very small bilingual (FA/EN) translations dictionary.
"""

STRINGS = {
    # ---- window / titles
    "app_title": {"fa": "تجمیع‌ گر PFMEA - فرآیند APQP", "en": "PFMEA Merger - APQP Process"},
    "settings_title": {"fa": "تنظیمات", "en": "Settings"},
    "profile_title": {"fa": "پروفایل محصول", "en": "Product Profile"},

    # ---- top toolbar
    "template_label": {"fa": "فایل قالب:", "en": "Template File:"},
    "browse": {"fa": "انتخاب...", "en": "Browse..."},
    "open_template": {"fa": "باز کردن", "en": "Open"},
    "about": {"fa": "درباره ما", "en": "About"},
    "about_title": {"fa": "درباره برنامه", "en": "About"},
    "save_settings": {"fa": "ذخیره تنظیمات", "en": "Save settings"},
    "restore_settings": {"fa": "بازیابی تنظیمات", "en": "Restore settings"},
    "add_files": {"fa": "افزودن فایل‌ها", "en": "Add Files"},
    "add_folder": {"fa": "افزودن پوشه", "en": "Add Folder"},
    "clear": {"fa": "پاک کردن", "en": "Clear"},
    "refresh": {"fa": "به‌روزرسانی", "en": "Refresh"},

    # ---- list
    "stations_hint": {
        "fa": "ایستگاه‌ها — برای جابه‌جایی از دکمه‌های فلش پایین جدول استفاده کنید:",
        "en": "Stations — use the arrow buttons below the table to reorder:",
    },
    "col_use": {"fa": "استفاده", "en": "Use"},
    "col_order": {"fa": "ترتیب", "en": "Order"},
    "col_opc": {"fa": "کد OPC", "en": "OPC Code"},
    "col_name": {"fa": "نام ایستگاه", "en": "Station Name"},
    "col_rows": {"fa": "حالت‌های خرابی", "en": "Failure modes"},
    "col_file": {"fa": "فایل", "en": "File"},
    "select_all": {"fa": "انتخاب همه", "en": "Select All"},
    "deselect_all": {"fa": "لغو همه", "en": "Deselect All"},
    "move_up": {"fa": "بالا", "en": "Up"},
    "move_down": {"fa": "پایین", "en": "Down"},

    # ---- output
    "output_label": {"fa": "فایل خروجی:", "en": "Output File:"},
    "include_history": {"fa": "تجمیع شیت History", "en": "Merge History Sheet"},
    "all_profiles": {"fa": "خروجی برای همه پروفایل‌ها", "en": "Create output for all profiles"},
    "merge_button": {"fa": "🚀 تجمیع و ذخیره خروجی", "en": "🚀 Merge & Save Output"},

    # ---- profile
    "profile_label": {"fa": "پروفایل:", "en": "Profile:"},
    "save_profile": {"fa": "ذخیره پروفایل", "en": "Save Profile"},
    "load_profile": {"fa": "بارگذاری پروفایل", "en": "Load Profile"},
    "delete_profile": {"fa": "حذف پروفایل", "en": "Delete Profile"},
    "new_profile": {"fa": "پروفایل جدید...", "en": "New Profile..."},
    "profile_name_prompt": {
        "fa": "نام پروفایل (معمولاً نام محصول):",
        "en": "Profile name (usually product name):",
    },

    # ---- settings
    "header_rows_lbl": {"fa": "تعداد ردیف‌های سربرگ:", "en": "Header rows count:"},
    "data_start_row_lbl": {"fa": "ردیف شروع داده:", "en": "Data start row:"},
    "opc_col_lbl": {"fa": "ستون کد OPC:", "en": "OPC code column:"},
    "name_col_lbl": {"fa": "ستون نام ایستگاه:", "en": "Station name column:"},
    "sheet_name_lbl": {"fa": "نام شیت اصلی:", "en": "Main sheet name:"},
    "history_sheet_lbl": {"fa": "نام شیت History:", "en": "History sheet name:"},
    "language_lbl": {"fa": "زبان:", "en": "Language:"},
    "footer_markers_lbl": {
        "fa": "کلیدواژه‌های پاورقی (هرکدام در یک خط):",
        "en": "Footer marker keywords (one per line):",
    },
    "rpn_top_percent_lbl": {
        "fa": "درصد RPNهای بالاتر (پیش‌فرض ۲۰٪):",
        "en": "Top RPN percentage (default 20%):",
    },
    "failure_row_height_lbl": {
        "fa": "ارتفاع ردیف حالت خرابی (۰ = خودکار):",
        "en": "Failure-mode row height (0 = automatic):",
    },
    "failure_column_width_lbl": {
        "fa": "عرض ستون حالت خرابی (۰ = خودکار):",
        "en": "Failure-mode column width (0 = automatic):",
    },
    "ok": {"fa": "تایید", "en": "OK"},
    "cancel": {"fa": "انصراف", "en": "Cancel"},

    # ---- messages
    "no_template": {
        "fa": "لطفاً ابتدا فایل قالب (Template) را انتخاب کنید.",
        "en": "Please select a template file first.",
    },
    "no_selection": {
        "fa": "هیچ ایستگاهی برای تجمیع انتخاب نشده است.",
        "en": "No stations selected for merging.",
    },
    "no_files": {
        "fa": "هیچ فایلی اضافه نشده است.",
        "en": "No input files added.",
    },
    "merge_success": {
        "fa": "تجمیع با موفقیت انجام شد!\nفایل خروجی: {path}",
        "en": "Merge completed successfully!\nOutput: {path}",
    },
    "merge_error": {
        "fa": "خطا در تجمیع: {err}",
        "en": "Merge error: {err}",
    },
    "profile_saved": {
        "fa": "پروفایل «{name}» ذخیره شد.",
        "en": "Profile '{name}' saved.",
    },
    "profile_loaded": {
        "fa": "پروفایل «{name}» بارگذاری شد.",
        "en": "Profile '{name}' loaded.",
    },
    "profile_delete_confirm": {
        "fa": "پروفایل «{name}» حذف شود؟",
        "en": "Delete profile '{name}'?",
    },
    "warning": {"fa": "هشدار", "en": "Warning"},
    "error": {"fa": "خطا", "en": "Error"},
    "info": {"fa": "پیام", "en": "Info"},
    "confirm": {"fa": "تایید", "en": "Confirm"},
    "excel_files": {"fa": "فایل‌های اکسل", "en": "Excel files"},
    "file_not_pfmea": {
        "fa": "فایل «{name}» فرمت PFMEA معتبر ندارد و نادیده گرفته شد.",
        "en": "File '{name}' is not a valid PFMEA file and was skipped.",
    },
    "missing_file": {"fa": "⚠ فایل ورودی موجود نیست", "en": "⚠ Input file missing"},
    "loaded_files": {
        "fa": "{n} فایل بارگذاری شد ({s} ایستگاه).",
        "en": "{n} files loaded ({s} stations).",
    },
    "product_name_lbl": {"fa": "نام محصول:", "en": "Product name:"},
    "product_code_lbl": {"fa": "کد محصول:", "en": "Product code:"},
    "ready": {"fa": "آماده", "en": "Ready"},
    "processing": {"fa": "در حال پردازش...", "en": "Processing..."},

    # ---- new keys
    "remove_selected": {"fa": "حذف ردیف انتخاب‌شده", "en": "Remove Selected Row"},
    "invert": {"fa": "معکوس", "en": "Invert"},
    "move_top": {"fa": "بالاترین", "en": "Move to top"},
    "move_bottom": {"fa": "پایین‌ترین", "en": "Move to bottom"},
    "open_output": {"fa": "باز کردن خروجی", "en": "Open output"},
    "open_after": {"fa": "پس از تجمیع فایل را باز کن", "en": "Open output after merge"},
    "refreshed": {"fa": "به‌روزرسانی انجام شد.", "en": "Refreshed."},
    "restored_folder": {
        "fa": "پوشه آخر به‌صورت خودکار بارگذاری شد: {n} فایل",
        "en": "Last folder restored automatically: {n} files",
    },
    "clear_confirm": {
        "fa": "تمام فایل‌ها و ایستگاه‌های بارگذاری‌شده پاک شوند؟",
        "en": "Clear all loaded files and stations?",
    },
    "no_profile_selected": {
        "fa": "هیچ پروفایلی انتخاب نشده است. از لیست کشویی یک پروفایل انتخاب کنید.",
        "en": "No profile selected. Pick one from the dropdown first.",
    },
    "profile_missing": {
        "fa": "پروفایل «{name}» پیدا نشد.",
        "en": "Profile '{name}' not found.",
    },
    "overwrite_profile": {
        "fa": "پروفایلی به نام «{name}» از قبل وجود دارد. جایگزین شود؟",
        "en": "A profile named '{name}' already exists. Overwrite?",
    },
    "save_profile_before_switch": {
        "fa": "تغییرات پروفایل «{name}» ذخیره شود؟",
        "en": "Save changes to profile '{name}' before switching?",
    },
    "overwrite_output": {
        "fa": "فایل خروجی از قبل وجود دارد:\n{path}\n\nجایگزین شود؟",
        "en": "Output file already exists:\n{path}\n\nOverwrite?",
    },
    "template_missing": {
        "fa": "فایل قالب پیدا نشد:\n{path}",
        "en": "Template file not found:\n{path}",
    },
    "no_xlsx_in_folder": {
        "fa": "در پوشه انتخاب‌شده هیچ فایل .xlsx وجود ندارد.",
        "en": "The selected folder contains no .xlsx files.",
    },
    "merge_done_status": {
        "fa": "تجمیع کامل شد ← {path}",
        "en": "Merge complete → {path}",
    },
    "toggle": {"fa": "تغییر وضعیت", "en": "Toggle"},
}


class Translator:
    def __init__(self, lang: str = "fa"):
        self.lang = lang if lang in ("fa", "en") else "fa"

    def set_lang(self, lang: str):
        self.lang = lang if lang in ("fa", "en") else "fa"

    def t(self, key: str, **kwargs) -> str:
        entry = STRINGS.get(key)
        if entry is None:
            return key
        text = entry.get(self.lang) or entry.get("en") or key
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

    def is_rtl(self) -> bool:
        return self.lang == "fa"
