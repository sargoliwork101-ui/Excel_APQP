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
    "add_files": {"fa": "افزودن فایل‌ها", "en": "Add Files"},
    "add_folder": {"fa": "افزودن پوشه", "en": "Add Folder"},
    "clear": {"fa": "پاک کردن", "en": "Clear"},
    "refresh": {"fa": "به‌روزرسانی", "en": "Refresh"},

    # ---- list
    "stations_hint": {
        "fa": "ایستگاه‌ها (با درگ می‌توانید ترتیب را تغییر دهید):",
        "en": "Stations (drag to reorder):",
    },
    "col_use": {"fa": "استفاده", "en": "Use"},
    "col_order": {"fa": "ترتیب", "en": "Order"},
    "col_opc": {"fa": "کد OPC", "en": "OPC Code"},
    "col_name": {"fa": "نام ایستگاه", "en": "Station Name"},
    "col_rows": {"fa": "تعداد ردیف", "en": "Rows"},
    "col_file": {"fa": "فایل", "en": "File"},
    "select_all": {"fa": "انتخاب همه", "en": "Select All"},
    "deselect_all": {"fa": "لغو همه", "en": "Deselect All"},
    "move_up": {"fa": "بالا", "en": "Up"},
    "move_down": {"fa": "پایین", "en": "Down"},

    # ---- output
    "output_label": {"fa": "فایل خروجی:", "en": "Output File:"},
    "include_history": {"fa": "تجمیع شیت History", "en": "Merge History Sheet"},
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
    "loaded_files": {
        "fa": "{n} فایل بارگذاری شد ({s} ایستگاه).",
        "en": "{n} files loaded ({s} stations).",
    },
    "product_name_lbl": {"fa": "نام محصول:", "en": "Product name:"},
    "product_code_lbl": {"fa": "کد محصول:", "en": "Product code:"},
    "ready": {"fa": "آماده", "en": "Ready"},
    "processing": {"fa": "در حال پردازش...", "en": "Processing..."},
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
