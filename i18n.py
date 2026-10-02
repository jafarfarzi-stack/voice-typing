"""
دو زبانه کردن رابط کاربری
Bilingual UI strings (Persian / English).

زبان رابط از combo زبان پیروی می‌کند:
  fa-IR → فارسی      en-US → English
"""

FA = {
    # --- عمومی ---
    "app_title": "تایپ صوتی — آفلاین",
    "header": "تایپ صوتی — آفلاین",
    "lang_label": "زبان:",
    "engine_label": "موتور:",
    "model_label": "مدل:",
    "hotkey_label": "میان‌بر:",
    "hotkey_set": "ثبت",
    "cancel": "انصراف",
    "save_btn": "ذخیره",
    "ft_text": "متن",
    "engine_whisper": "Whisper (دقیق، آفلاین)",
    "engine_vosk": "Vosk (سریع، آفلاین)",
    "engine_google": "Google (آنلاین)",
    "lang_fa": "فارسی",
    "lang_en": "English",

    # --- چک‌باکس‌ها ---
    "chk_direct": "نوشتن مستقیم",
    "chk_enter": "ارسال Enter",
    "chk_punct": "نقطه‌گذاری",
    "chk_digits": "اعداد به رقم",
    "chk_math": "نمادهای ریاضی",
    "chk_ontop": "همیشه رو",
    "chk_autolang": "تشخیص خودکار زبان",

    # --- دکمه‌ها ---
    "btn_start": "شروع",
    "btn_stop": "توقف",
    "btn_copy": "کپی",
    "btn_clear": "پاک",
    "btn_undo": "برگرد",
    "btn_save": "ذخیره",
    "btn_open": "باز کردن",
    "btn_settings": "تنظیمات",
    "btn_minimize": "مینیمایز",
    "btn_help": "راهنما",
    "btn_model": "مدل آفلاین",
    "btn_mic_test": "تست میکروفون",

    # --- منوی متن ---
    "menu_copy": "کپی",
    "menu_paste": "چسباندن",
    "menu_clear": "پاک کردن",
    "menu_undo": "برگرداندن",
    "menu_save_file": "ذخیره در فایل...",
    "menu_word": "خروجی Word...",

    # --- وضعیت ---
    "st_engine": "موتور: %(s)s",
    "st_stopped": "متوقف شد",
    "st_loading_model": "در حال بارگذاری مدل… (اولین بار کمی طول می‌کشد)",
    "st_wrote": "نوشتم: %(s)s",
    "st_lang": "زبان: %(s)s",
    "st_copied_n": "%(d)s کاراکتر کپی شد",
    "st_copied": "متن کپی شد",
    "st_pasted": "چسبانده شد",
    "st_cleared": "متن پاک شد",
    "st_undone": "برگردانده شد",
    "st_nothing_undo": "چیزی برای برگرداندن نبود",
    "st_saved": "ذخیره شد: %(s)s",
    "st_loaded": "بارگذاری شد: %(s)s",
    "st_docx": "Word ساخته شد: %(s)s",
    "st_nothing_copy": "متنی برای کپی نیست",
    "st_nothing_save": "متنی برای ذخیره نیست",
    "st_hotkey_set": "میان‌بر ثبت شد: %(s)s",
    "st_settings_saved": "تنظیمات اعمال شد",
    "st_model_ready": "مدل آماده شد — حالا F8 بزن",
    "st_direct_fail": "نوشتن مستقیم ناموفق بود (کلیپورد)",
    "st_audio_err": "خطا در پردازش صدا",

    # --- زیرعنوان ---
    "sub_offline": "● آفلاین آماده — %(s)s (بدون اینترنت)",
    "sub_need_model": "○ مدل نصب نیست: %(s)s (~%(d)sMB) — دکمه «مدل آفلاین» را بزنید",
    "sub_online": "⚠ حالت آنلاین — برای کار بدون اینترنت موتور را تغییر دهید",

    # --- خطاها ---
    "err_mic": "دسترسی به میکروفون ممکن نیست: %(s)s",
    "err_engine_build": "ساخت موتور تشخیص صدا ناموفق بود",
    "err_load_model": "بارگذاری مدل ناموفق بود",
    "err_model_missing": "مدل نصب نیست: %(s)s",
    "err_pip": "پکیج %(s)s نصب نیست — pip install %(p)s",
    "err_save": "ذخیره نشد: %(s)s",
    "err_open": "باز نشد: %(s)s",
    "err_docx_lib": "برای خروجی Word:\n\npip install python-docx",
    "err_num": "مقادیر باید عدد باشند",
    "err_docx": "خروجی ساخته نشد: %(s)s",
    "err_mic_test": "خطای میکروفون: %(s)s",

    # --- پیام‌های تأیید ---
    "ask_pip": "برای این موتور باید این پکیج نصب باشد:\n\n"
               "    pip install %(s)s\n\nیا موتور دیگری انتخاب کنید.",
    "ask_online": "موتور انتخابی آنلاین است و به اینترنت نیاز دارد.\nادامه می‌دهید؟",
    "ask_download": "برای کار کاملاً آفلاین باید یک‌بار مدل دانلود شود.\n\n"
                    "مدل:  %(s)s\nحجم:  حدود %(d)d مگابایت\nمنبع: %(p)s\nمسیر: %(o)s\n\n"
                    "این فقط یک‌بار لازم است. حالا دانلود کنم؟",
    "ask_exit": "در حال گوش دادن هستی. خارج می‌شوی؟",
    "info_model_ok": "مدل فعلی نصب است:\n\n    %(s)s\n    %(e)s\n\n"
                     "برنامه بدون اینترنت کار می‌کند.%(p)s",
    "info_model_more": "\n\nمدل‌های نصب‌نشده: %(s)s",
    "dl_title": "دانلود مدل آفلاین",
    "dl_wait": "در حال دانلود %(s)s",
    "dl_note": "این پنجره را نبندید. اولین دانلود ممکن است چند دقیقه طول بکشد.",
    "dl_preparing": "آماده‌سازی…",
    "dl_cancel": "لغو",
    "dl_done": "تمام شد.",
    "dl_progress": "%(a)s از %(b)s  (%(d)s%%)",
    "dl_failed_title": "دانلود ناموفق",
    "dl_failed": "دانلود مدل انجام نشد:\n\n%(s)s",

    # --- تنظیمات ---
    "set_title": "تنظیمات",
    "set_head": "تنظیمات پیشرفته",
    "set_silence": "سکوت پایان جمله (ثانیه)",
    "set_min": "حداقل طول گفتار (ثانیه)",
    "set_max": "حداکثر طول جمله (ثانیه)",
    "set_hint": "مقادیر کوچک‌تر = پاسخ سریع‌تر ولی تکه‌تکه‌تر",

    # --- میکروفون ---
    "mic_ok": "میکروفون سالم است — اوج صدا: %(d)s",
    "mic_low": " (صدا کم است؛ نزدیک‌تر حرف بزنید)",

    # --- کمک ---
    "help_title": "راهنما",
    "help_ok": "باشه",
    "model_title": "دانلود مدل",
    "tray_quit": "خروج",

    # --- نام موتورها ---
    "lang_fa": "فارسی",
}

EN = {
    "app_title": "Voice Typing — Offline",
    "header": "Voice Typing — Offline",
    "lang_label": "Language:",
    "engine_label": "Engine:",
    "model_label": "Model:",
    "hotkey_label": "Hotkey:",
    "hotkey_set": "Set",
    "cancel": "Cancel",
    "save_btn": "Save",
    "ft_text": "Text",
    "engine_whisper": "Whisper (accurate, offline)",
    "engine_vosk": "Vosk (fast, offline)",
    "engine_google": "Google (online)",
    "lang_fa": "فارسی",
    "lang_en": "English",

    "chk_direct": "Direct typing",
    "chk_enter": "Send Enter",
    "chk_punct": "Punctuation",
    "chk_digits": "Numbers as digits",
    "chk_math": "Math symbols",
    "chk_ontop": "Always on top",
    "chk_autolang": "Auto-detect language",

    "btn_start": "Start",
    "btn_stop": "Stop",
    "btn_copy": "Copy",
    "btn_clear": "Clear",
    "btn_undo": "Undo",
    "btn_save": "Save",
    "btn_open": "Open",
    "btn_settings": "Settings",
    "btn_minimize": "Minimize",
    "btn_help": "Help",
    "btn_model": "Offline model",
    "btn_mic_test": "Test microphone",

    "menu_copy": "Copy",
    "menu_paste": "Paste",
    "menu_clear": "Clear all",
    "menu_undo": "Undo",
    "menu_save_file": "Save to file...",
    "menu_word": "Export to Word...",

    "st_engine": "Engine: %(s)s",
    "st_stopped": "Stopped",
    "st_loading_model": "Loading model… (slow the first time)",
    "st_wrote": "Typed: %(s)s",
    "st_lang": "Language: %(s)s",
    "st_copied_n": "%(d)d characters copied",
    "st_copied": "Text copied",
    "st_pasted": "Pasted",
    "st_cleared": "Text cleared",
    "st_undone": "Undone",
    "st_nothing_undo": "Nothing to undo",
    "st_saved": "Saved: %(s)s",
    "st_loaded": "Loaded: %(s)s",
    "st_docx": "Word file created: %(s)s",
    "st_nothing_copy": "No text to copy",
    "st_nothing_save": "No text to save",
    "st_hotkey_set": "Hotkey set: %(s)s",
    "st_settings_saved": "Settings applied",
    "st_model_ready": "Model ready — press F8 now",
    "st_direct_fail": "Direct typing failed (clipboard)",
    "st_audio_err": "Audio processing error",

    "sub_offline": "● Ready offline — %(s)s (no internet needed)",
    "sub_need_model": "○ Model not installed: %(s)s (~%(d)dMB) — click “Offline model”",
    "sub_online": "⚠ Online mode — switch engine to work without internet",

    "err_mic": "Cannot access microphone: %(s)s",
    "err_engine_build": "Could not create the recognition engine",
    "err_load_model": "Model loading failed",
    "err_model_missing": "Model not installed: %(s)s",
    "err_pip": "Package %(s)s is not installed — pip install %(p)s",
    "err_save": "Could not save: %(s)s",
    "err_open": "Could not open: %(s)s",
    "err_docx_lib": "For Word export:\n\npip install python-docx",
    "err_num": "Values must be numbers",
    "err_docx": "Export failed: %(s)s",
    "err_mic_test": "Microphone error: %(s)s",

    "ask_pip": "This engine needs a package:\n\n"
               "    pip install %(s)s\n\nOr choose a different engine.",
    "ask_online": "The selected engine is online and needs internet.\nContinue?",
    "ask_download": "To work fully offline the model must be downloaded once.\n\n"
                    "Model:   %(s)s\nSize:    about %(d)d MB\nSource:  %(o)s\nPath:    %(p)s\n\n"
                    "This is needed only once. Download now?",
    "ask_exit": "Currently listening. Exit anyway?",
    "info_model_ok": "Current model is installed:\n\n    %(s)s\n    %(p)s\n\n"
                     "The app works without internet.%(e)s",
    "info_model_more": "\n\nNot installed: %(s)s",
    "dl_title": "Download offline model",
    "dl_wait": "Downloading %(s)s",
    "dl_note": "Don't close this window. The first download may take a few minutes.",
    "dl_preparing": "Preparing…",
    "dl_cancel": "Cancel",
    "dl_done": "Done.",
    "dl_progress": "%(a)s of %(b)s  (%(d)d%%)",
    "dl_failed_title": "Download failed",
    "dl_failed": "Model download failed:\n\n%(s)s",

    "set_title": "Settings",
    "set_head": "Advanced settings",
    "set_silence": "End-of-sentence silence (sec)",
    "set_min": "Minimum speech length (sec)",
    "set_max": "Maximum phrase length (sec)",
    "set_hint": "Smaller values = faster but more fragmented",

    "mic_ok": "Microphone is fine — peak level: %(d)d",
    "mic_low": " (level is low; move closer)",

    "help_title": "Help",
    "help_ok": "OK",
    "model_title": "Download model",
    "tray_quit": "Quit",
    "lang_fa": "فارسی",
}

HELP_FA = """راهنمای تایپ صوتی آفلاین

شروع کار
  1) موتور را روی Whisper و مدل small بگذارید.
  2) F8 (یا دکمه شروع) را بزنید.
  3) برنامه می‌پرسد «مدل دانلود شود؟» — تایید کنید.
     این فقط بار اول است؛ بعد از آن بدون اینترنت کار می‌کند.

میان‌برها
  F8 (قابل تغییر)  شروع / توقف
  Ctrl+Q          خروج
  کلیک راست روی متن  منوی کپی، پاک کردن، ذخیره، Word

فرمان‌های صوتی
  «زبان فارسی» / «برو فارسی» / «persian»   → فارسی
  «زبان انگلیسی» / «english»               → English
  «کپی کن»   کپی متن تا این لحظه
  «پیست کن»  چسباندن از کلیپورد
  «پاک کن»   پاک کردن متن
  «برگرد»    برگشت آخرین تغییر
  «تمام»     توقف گوش دادن

تبدیل خودکار
  اعداد    «بیست سه» → 23 ، «دو هزار» → 2000 ، «بیست و پنج درصد» → 25%
  ریاضی    «بیست سه منها پنج» → 23 - 5
           «نامساوی» → != ، «بزرگتر» → > ، «به لابه» → /
  این‌ها فقط بین دو عدد تبدیل می‌شوند؛
  «این مال منه» و «جمع کن» دست‌نخورده می‌مانند.

موتورها
  Whisper  دقت بالا، فارسی و انگلیسی، مدل small ~480MB
  Vosk     خیلی سریع، حجم کم (~47MB)، دقت متوسط
  Google   آنلاین (فقط برای مقایسه)

نکات دقت
  برای فارسی، مدل small یا medium بهترین نتیجه را می‌دهد.
  محیط ساکت و میکروفون نزدیک، مهم‌ترین عامل است.
  اعداد را به شکل «بیست سه» بگویید تا درست نوشته شود.
  اگر جمله‌ها تکه‌تکه شد، «سکوت پایان جمله» را در تنظیمات کم کنید.
  اگر کلمه‌ها به هم چسبیده شد، آن مقدار را زیاد کنید.
"""

HELP_EN = """Offline Voice Typing — Help

Getting started
  1) Set engine to Whisper and model to small.
  2) Press F8 (or the Start button).
  3) The app asks whether to download the model — confirm.
     This is only needed once; after that no internet is required.

Shortcuts
  F8 (changeable)  start / stop
  Ctrl+Q           quit
  Right-click text  copy, clear, save, Word export

Voice commands
  "persian" / "switch to persian"  → Persian
  "english"                        → English
  "copy"      copy text so far
  "paste"     paste from clipboard
  "clear"     clear the text
  "undo"      undo last change
  "finish"    stop listening

Automatic conversion
  Numbers  "twenty three" → 23, "two thousand" → 2000,
           "twenty five percent" → 25%, "two point five" → 2.5
  Math     "twenty three minus five" → 23 - 5
           "not equal to" → !=, "greater than" → >, "divided by" → /
  Symbols are only replaced between two numbers, so
  "this is a test" and "one plus my phone" stay untouched.

Engines
  Whisper  high accuracy, Persian + English, small model ~480MB
  Vosk     very fast, small (~47MB), moderate accuracy
  Google   online (for comparison only)

Accuracy tips
  For Persian, the small or medium model works best.
  A quiet room and a close microphone matter most.
  If phrases get cut, lower "end-of-sentence silence" in Settings.
  If words run together, raise it.
"""

MODEL_HELP_FA = """دانلود مدل آفلاین

روش معمول: دکمه «مدل آفلاین» پایین برنامه را بزنید.
برنامه می‌پرسد و بعد از تایید شما دانلود می‌کند.

روش خط فرمان (اختیاری):
    python download_models.py --list
    python download_models.py --engine whisper --size small
    python download_models.py --engine vosk --lang fa

اندازه مدل‌های Whisper
    tiny    ~75 MB    سریع، دقت کم
    base    ~145 MB   سبک
    small   ~480 MB   پیشنهادی برای فارسی
    medium  ~1.5 GB   دقت خیلی خوب، کند روی CPU
    large-v3 ~3 GB    بهترین کیفیت، خیلی کند

مدل Vosk
    فارسی   ~47 MB
    English ~40 MB

بعد از دانلود، هیچ اینترنتی لازم نیست.
"""

MODEL_HELP_EN = """Downloading an offline model

Usual way: click the "Offline model" button at the bottom.
The app asks first and downloads only after you confirm.

Command line (optional):
    python download_models.py --list
    python download_models.py --engine whisper --size small
    python download_models.py --engine vosk --lang en

Whisper model sizes
    tiny    ~75 MB    fastest, low accuracy
    base    ~145 MB   light
    small   ~480 MB   recommended
    medium  ~1.5 GB   very accurate, slow on CPU
    large-v3 ~3 GB    best quality, very slow

Vosk models
    Persian  ~47 MB
    English  ~40 MB

After downloading, no internet is required.
"""


def table(lang):
    return EN if str(lang).startswith("en") else FA


def tr(key, lang="fa-IR", **kwargs):
    """ترجمه یک کلید؛ اگر نبود خود کلید برگردانده می‌شود"""
    text = table(lang).get(key)
    if text is None:
        return key
    if kwargs:
        try:
            return text % kwargs
        except (KeyError, TypeError, ValueError):
            return text
    return text


def help_text(lang):
    return HELP_EN if str(lang).startswith("en") else HELP_FA


def model_help_text(lang):
    return MODEL_HELP_EN if str(lang).startswith("en") else MODEL_HELP_FA


def is_rtl(lang):
    return not str(lang).startswith("en")


def font_for(lang, size=10, weight=None):
    """فونت مناسب هر زبان"""
    family = "Tahoma"
    return (family, size, weight) if weight else (family, size)
