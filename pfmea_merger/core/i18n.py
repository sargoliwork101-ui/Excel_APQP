"""
Very small bilingual (FA/EN) translations dictionary.
"""

STRINGS = {
    # ---- window / titles
    "app_title": {"fa": "تجمیع‌ گر PFMEA - فرآیند APQP", "en": "PFMEA Merger - APQP Process"},
    "settings_title": {"fa": "تنظیمات", "en": "Settings"},
    "profile_title": {"fa": "پروفایل محصول", "en": "Product Profile"},

    # ---- top toolbar
    "template_label": {"fa": "فایل قالب PFMEA:", "en": "PFMEA Template File:"},
    "cp_template_label": {"fa": "فایل قالب CP:", "en": "CP Template File:"},
    "tpl_open_pfmea_tip": {"fa": "باز کردن فایل قالب PFMEA", "en": "Open the PFMEA template file"},
    "tpl_browse_pfmea_tip": {"fa": "انتخاب فایل قالب PFMEA", "en": "Browse for the PFMEA template file"},
    "tpl_open_cp_tip": {"fa": "باز کردن فایل قالب CP", "en": "Open the CP template file"},
    "tpl_browse_cp_tip": {"fa": "انتخاب فایل قالب CP", "en": "Browse for the CP template file"},
    "browse": {"fa": "انتخاب...", "en": "Browse..."},
    "open_template": {"fa": "باز کردن", "en": "Open"},
    "about": {"fa": "درباره ما", "en": "About"},
    "about_title": {"fa": "درباره برنامه", "en": "About"},
    "backup": {"fa": "پشتیبان‌گیری", "en": "Backup"},
    "restore_backup": {"fa": "بازیابی پشتیبان", "en": "Restore backup"},
    "backup_created": {"fa": "فایل پشتیبان با موفقیت ساخته شد.", "en": "Backup created successfully."},
    "backup_restored": {"fa": "پشتیبان با موفقیت بازیابی شد. برای اعمال کامل تغییرات، برنامه را دوباره اجرا کنید.", "en": "Backup restored. Restart the application to apply all changes."},
    "backup_confirm": {"fa": "اطلاعات فعلی با اطلاعات داخل بک‌آپ جایگزین شود؟", "en": "Replace current user data with this backup?"},
    "backup_file": {"fa": "فایل پشتیبان", "en": "Backup file"},
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
    "col_use": {"fa": "استفاده در PFMEA", "en": "Use in PFMEA"},
    "col_use_cp": {"fa": "استفاده در CP", "en": "Use in CP"},
    "col_order": {"fa": "ترتیب", "en": "Order"},
    "col_opc": {"fa": "کد OPC", "en": "OPC Code"},
    "col_name": {"fa": "نام ایستگاه", "en": "Station Name"},
    "col_rows": {"fa": "حالت‌های خرابی", "en": "Failure modes"},
    "col_file": {"fa": "فایل PFMEA", "en": "PFMEA File"},
    "col_file_cp": {"fa": "فایل CP", "en": "CP File"},
    "select_all": {"fa": "انتخاب همه", "en": "Select All"},
    "deselect_all": {"fa": "لغو همه", "en": "Deselect All"},
    "move_up": {"fa": "بالا", "en": "Up"},
    "move_down": {"fa": "پایین", "en": "Down"},

    # ---- output
    "output_label": {"fa": "فایل خروجی PFMEA:", "en": "PFMEA Output File:"},
    "cp_output_label": {"fa": "فایل خروجی CP:", "en": "CP Output File:"},
    "out_browse_pfmea_tip": {"fa": "انتخاب مسیر فایل خروجی PFMEA", "en": "Browse for the PFMEA output file"},
    "out_browse_cp_tip": {"fa": "انتخاب مسیر فایل خروجی CP", "en": "Browse for the CP output file"},
    "include_history": {"fa": "تجمیع شیت History/تغییرات", "en": "Merge History/تغییرات sheet"},
    "all_profiles": {"fa": "خروجی برای همه پروفایل‌ها", "en": "Create output for all profiles"},
    "merge_button": {"fa": "🚀 تجمیع PFMEA", "en": "🚀 Merge PFMEA"},
    "merge_cp_button": {"fa": "🚀 تجمیع Control Plan", "en": "🚀 Merge Control Plan"},

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
    "failure_mode_col_lbl": {"fa": "ستون حالت خرابی:", "en": "Failure-mode column:"},
    "so_col_lbl": {"fa": "ستون SO:", "en": "SO column:"},
    "rpn_col_lbl": {"fa": "ستون RPN:", "en": "RPN column:"},
    "aq2_cell_lbl": {"fa": "سلول آستانه RPN (AQ2):", "en": "RPN threshold cell (AQ2):"},
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
        "fa": "لطفاً ابتدا فایل قالب {doc} را انتخاب کنید.",
        "en": "Please select the {doc} template file first.",
    },
    "no_selection": {
        "fa": "هیچ ایستگاهی برای تجمیع {doc} انتخاب نشده است.",
        "en": "No stations selected for {doc} merge.",
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
        "fa": "فایل «{name}» فرمت معتبر PFMEA یا CP ندارد و نادیده گرفته شد.",
        "en": "File '{name}' is not a valid PFMEA or CP file and was skipped.",
    },
    "missing_file": {"fa": "⚠ فایل PFMEA موجود نیست", "en": "⚠ PFMEA file missing"},
    "cp_file_missing": {"fa": "⚠ فایل CP موجود نیست", "en": "⚠ CP file missing"},
    "missing_inputs_block": {
        "fa": "برای ایستگاه‌های زیر فایل {doc} موجود نیست:\n{names}\n\nابتدا فایل‌ها را اضافه کنید یا تیک CP آن‌ها را بردارید.",
        "en": "The stations below have no {doc} input file:\n{names}\n\nAdd the files first or untick their CP checkbox.",
    },
    "doc_type_lbl": {"fa": "نوع سند:", "en": "Document type:"},
    "toggle_cp": {"fa": "تغییر وضعیت CP", "en": "Toggle CP"},
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
    "open_output_folder": {"fa": "باز کردن پوشه خروجی‌ها", "en": "Open the output folder"},
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
    "profile_save_failed": {
        "fa": "ذخیره پروفایل انجام نشد!\nممکن است فایل پروفایل در برنامه دیگری باز باشد یا پوشه پروفایل‌ها فقط‌خواندنی باشد. آن را ببندید و دوباره امتحان کنید.",
        "en": "Saving the profile failed!\nThe profile file may be open in another program, or the profiles folder may be read-only. Close it and try again.",
    },
    "overwrite_profile": {
        "fa": "پروفایلی به نام «{name}» از قبل وجود دارد. جایگزین شود؟",
        "en": "A profile named '{name}' already exists. Overwrite?",
    },
    "save_profile_before_switch": {
        "fa": "تغییرات پروفایل «{name}» ذخیره شود؟",
        "en": "Save changes to profile '{name}' before switching?",
    },
    "save_profile_changes": {
        "fa": "تغییرات (حذف ایستگاه‌های انتخاب‌شده) در پروفایل «{name}» ذخیره شود؟",
        "en": "Save these station changes (removal) to profile '{name}'?",
    },
    "overwrite_output": {
        "fa": "فایل خروجی از قبل وجود دارد:\n{path}\n\nجایگزین شود؟",
        "en": "Output file already exists:\n{path}\n\nOverwrite?",
    },
    "template_missing": {
        "fa": "فایل قالب {doc} پیدا نشد:\n{path}",
        "en": "{doc} template file not found:\n{path}",
    },
    "no_xlsx_in_folder": {
        "fa": "در پوشه انتخاب‌شده هیچ فایل .xlsx وجود ندارد.",
        "en": "The selected folder contains no .xlsx files.",
    },
    "merge_done_status": {
        "fa": "تجمیع کامل شد ← {path}",
        "en": "Merge complete → {path}",
    },
    "toggle": {"fa": "تغییر وضعیت PFMEA", "en": "Toggle PFMEA"},
    "check_pfmea": {"fa": "تیک PFMEA", "en": "Check PFMEA"},
    "uncheck_pfmea": {"fa": "حذف تیک PFMEA", "en": "Uncheck PFMEA"},
    "check_cp": {"fa": "تیک CP", "en": "Check CP"},
    "uncheck_cp": {"fa": "حذف تیک CP", "en": "Uncheck CP"},
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
