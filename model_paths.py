"""
مسیر ثابت مدل‌ها / Persistent model folder

مدل‌ها باید در جایی بمانند که با جابه‌جایی، آپدیت یا حذف پوشه برنامه
از بین نروند. این ماژول:

  - مسیر پایدار پیشفرض را مشخص میکند (~/.voice_typing_models)
  - مسیر دلخواه کاربر را میخواند (از تنظیمات)
  - مدلهای قدیمی را از پوشه کنار برنامه به مسیر پایدار کپی میکند
  - کپی مدلها بین دو پوشه را امن انجام میدهد (فایل ناقص باقی نمیماند)
"""

import os
import shutil
from pathlib import Path

import model_download as md

APP_DIR = Path(__file__).resolve().parent
LEGACY_MODEL_DIR = APP_DIR / "models"
USER_MODEL_DIR = Path.home() / ".voice_typing_models"

MODEL_SUBDIRS = ("whisper", "vosk")


def expand(value):
    """تبدیل ~ و متغیرهای محیطی به یک مسیر مطلق. ورودی خالی → None."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = os.path.expanduser(text)
    text = os.path.expandvars(text)
    try:
        return Path(text).expanduser().resolve()
    except OSError:
        return Path(os.path.abspath(text))


def default_dir():
    """مسیر پایدار پیشفرض (همیشه داخل پوشه کاربر، بیرون پوشه برنامه)."""
    return USER_MODEL_DIR


def legacy_dir():
    """پوشه قدیمی مدلها، کنار app.py (برای سازگاری و مهاجرت)."""
    return LEGACY_MODEL_DIR


def resolve(configured=None):
    """مسیر مدل را از تنظیمات بگیر؛ اگر خالی بود مسیر پایدار پیشفرض."""
    return expand(configured) or USER_MODEL_DIR


def ensure_dir(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def installed_summary(model_dir):
    """فهرست مدلهای آماده در یک پوشه."""
    model_dir = Path(model_dir)
    names = []
    for size in md.WHISPER_SIZES:
        if md.whisper_installed(model_dir, size):
            names.append("Whisper %s" % size)
    for lang in md.VOSK_FILES:
        if md.vosk_installed(model_dir, lang):
            names.append("Vosk %s" % md.VOSK_FILES[lang][1])
    return names


def has_any_model(model_dir):
    return bool(installed_summary(model_dir))


def path_display(path):
    """نمایش کوتاه مسیر: ~/.voice_typing_models به جای مسیر کامل."""
    path = Path(path)
    try:
        return "~" + os.sep + str(path.relative_to(Path.home()))
    except (ValueError, OSError):
        return str(path)


def _same_file(src, dst):
    try:
        return (
            dst.is_file()
            and src.stat().st_size == dst.stat().st_size
            and src.stat().st_mtime <= dst.stat().st_mtime
        )
    except OSError:
        return False


def copy_tree(src, dst, on_status=None, on_progress=None):
    """
    کپی امن محتویات src داخل dst.
    هر فایل ابتدا با postfix موقت نوشته میشود سپس جایگزین میشود،
    بنابراین بسته شدن ناگهانی برنامه فایل ناقص به جای نخواهد گذاشت.
    """
    src, dst = Path(src), Path(dst)
    if not src.is_dir():
        raise FileNotFoundError("پوشه مبدأ پیدا نشد: %s" % src)

    files = [
        p for p in src.rglob("*")
        if p.is_file()
        and not p.name.endswith(".copying")
        and not any(part.endswith(".download") for part in p.parts)
    ]
    copied = skipped = 0
    if on_status:
        on_status("کپی %d فایل…" % len(files))

    for i, src_file in enumerate(files, start=1):
        rel = src_file.relative_to(src)
        dst_file = dst / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        if _same_file(src_file, dst_file):
            skipped += 1
        else:
            tmp = dst_file.with_name(dst_file.name + ".copying")
            try:
                shutil.copy2(src_file, tmp)
                tmp.replace(dst_file)
            finally:
                if tmp.exists():
                    try:
                        tmp.unlink()
                    except OSError:
                        pass
            copied += 1
        if on_progress:
            on_progress(i, len(files))
    return {"copied": copied, "skipped": skipped, "total": len(files)}


def copy_models(src, dst, on_status=None, on_progress=None):
    """کپی مدلهای whisper و vosk از src به dst (چیزی حذف نمیشود)."""
    src, dst = Path(src), Path(dst)
    result = {"copied": 0, "skipped": 0, "total": 0, "found": False}
    for sub in MODEL_SUBDIRS:
        source = src / sub
        if not source.is_dir():
            continue
        result["found"] = True
        if on_status:
            on_status("کپی مدل «%s»…" % sub)
        part = copy_tree(source, dst / sub, on_progress=on_progress)
        for key in ("copied", "skipped", "total"):
            result[key] += part[key]
    return result


def migrate_if_needed(config):
    """
    اگر کاربر هنوز مسیری تنظیم نکرده و مدلهای قدیمی در پوشهٔ کنار
    برنامه وجود دارد، آنها را یکبار به مسیر پایدار کپی میکند.
    مدلهای قدیمی حذف نمیشوند.
    """
    if str(config.get("model_dir") or "").strip():
        return resolve(config.get("model_dir")), False
    if config.get("model_migrated"):
        return default_dir(), False

    target = default_dir()
    try:
        if has_any_model(legacy_dir()) and not has_any_model(target):
            copy_models(legacy_dir(), target)
    except Exception:
        # مهاجرت اختیاری است؛ نباید جلوی اجرای برنامه را بگیرد
        import logging

        logging.getLogger("voice_typing.models").exception("Model migration failed")
    return target, True
