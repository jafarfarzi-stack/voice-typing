"""
مدیریت مدل‌های آفلاین
Download / check offline models on demand.

هیچ چیزی خودکار دانلود نمی‌شود. برنامه موقع اجرا می‌پرسد و
فقط در صورت تایید کاربر دانلود انجام می‌شود.
"""

import logging
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

log = logging.getLogger("voice_typing.models")

VOSK_BASE = "https://alphacephei.com/vosk/models"
VOSK_FILES = {
    "fa": ("vosk-model-small-fa-0.42", "فارسی", 47),
    "en": ("vosk-model-small-en-us-0.15", "English", 40),
}
WHISPER_SIZES = ["tiny", "base", "small", "medium", "large-v3"]
WHISPER_MB = {
    "tiny": 75,
    "base": 145,
    "small": 480,
    "medium": 1530,
    "large-v3": 3090,
}
WHISPER_FILES = ("config.json", "model.bin", "tokenizer.json")


def human(nbytes):
    n = float(nbytes)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return "%.0f %s" % (n, unit)
        n /= 1024
    return "%.1f TB" % n


def dir_size(path):
    total = 0
    path = Path(path)
    if not path.exists():
        return 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                pass
    return total


def free_space(path):
    probe = Path(path)
    while not probe.exists() and probe.parent != probe:
        probe = probe.parent
    try:
        return shutil.disk_usage(probe).free
    except OSError:
        return 0


# ------------------------------------------------------------------ whisper


def whisper_path(model_dir, size):
    return Path(model_dir) / "whisper" / size


def whisper_installed(model_dir, size):
    path = whisper_path(model_dir, size)
    return all((path / name).is_file() for name in WHISPER_FILES)


def download_whisper(model_dir, size, on_status=None, should_stop=None):
    """دانلود مدل Whisper. گزارش پیشرفت از بیرون (اندازه پوشه) انجام می‌شود."""
    from faster_whisper.utils import download_model

    target = whisper_path(model_dir, size)
    target.mkdir(parents=True, exist_ok=True)

    if on_status:
        on_status("دانلود مدل Whisper «%s» شروع شد…" % size)
    try:
        download_model(size, output_dir=str(target))
    except Exception as exc:
        log.exception("Whisper download failed")
        shutil.rmtree(target, ignore_errors=True)
        raise RuntimeError("دانلود مدل Whisper ناموفق بود: %s" % exc) from exc

    if not whisper_installed(model_dir, size):
        raise RuntimeError("فایل‌های مدل Whisper ناقص است")

    if on_status:
        on_status("مدل Whisper «%s» آماده شد" % size)
    return target


# --------------------------------------------------------------------- vosk


def vosk_path(model_dir, lang):
    return Path(model_dir) / "vosk" / VOSK_FILES[lang][0]


def vosk_installed(model_dir, lang):
    path = vosk_path(model_dir, lang)
    return path.is_dir() and any(path.iterdir())


def _http_download(url, dest, on_progress=None, should_stop=None):
    req = urllib.request.Request(url, headers={"User-Agent": "voice-typing"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        done = 0
        next_report = 0
        with open(dest, "wb") as f:
            while True:
                if should_stop and should_stop():
                    raise RuntimeError("دانلود لغو شد")
                chunk = resp.read(256 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if on_progress and done >= next_report:
                    on_progress(done, total)
                    next_report = done + 4 * 1024 * 1024
        if on_progress:
            on_progress(done, total)
    return done


def download_vosk(model_dir, lang, on_status=None, on_progress=None, should_stop=None):
    folder, label, mb = VOSK_FILES[lang]
    fname = folder + ".zip"
    target_dir = Path(model_dir) / "vosk"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / folder

    if on_status:
        on_status("دانلود مدل Vosk «%s» (~%dMB) …" % (label, mb))

    tmpdir = tempfile.mkdtemp(prefix="vosk_dl_")
    try:
        zip_path = Path(tmpdir) / fname
        _http_download(
            "%s/%s" % (VOSK_BASE, fname),
            zip_path,
            on_progress=on_progress,
            should_stop=should_stop,
        )
        if on_status:
            on_status("در حال باز کردن فایل مدل…")
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(target_dir)
    except Exception as exc:
        log.exception("Vosk download failed")
        if isinstance(exc, RuntimeError):
            raise
        raise RuntimeError("دانلود مدل Vosk ناموفق بود: %s" % exc) from exc
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    if not target.is_dir():
        raise RuntimeError("پوشه مدل پس از باز کردن پیدا نشد")
    if on_status:
        on_status("مدل Vosk «%s» آماده شد" % label)
    return target


# ------------------------------------------------------------------- status


def installed(engine, lang="fa", size="small", model_dir="models"):
    """آیا مدل این موتور/زبان/سایز روی دیسک هست؟"""
    if engine == "whisper":
        return whisper_installed(model_dir, size)
    if engine == "vosk":
        key = "fa" if str(lang).startswith("fa") else "en"
        return vosk_installed(model_dir, key)
    return True


def describe(engine, lang="fa", size="small", model_dir="models"):
    """اطلاعات مدل برای نمایش به کاربر"""
    if engine == "whisper":
        return {
            "name": "Whisper %s" % size,
            "size_mb": WHISPER_MB.get(size, 0),
            "path": str(whisper_path(model_dir, size)),
            "ready": whisper_installed(model_dir, size),
            "source": "huggingface.co",
        }
    if engine == "vosk":
        key = "fa" if str(lang).startswith("fa") else "en"
        folder, label, mb = VOSK_FILES[key]
        return {
            "name": "Vosk %s" % label,
            "size_mb": mb,
            "path": str(vosk_path(model_dir, key)),
            "ready": vosk_installed(model_dir, key),
            "source": "alphacephei.com",
        }
    return {
        "name": "Google (آنلاین)",
        "size_mb": 0,
        "path": "-",
        "ready": True,
        "source": "google.com",
    }


def ensure(engine, lang="fa", size="small", model_dir="models",
           on_status=None, on_progress=None, should_stop=None):
    """اگر مدل نصب نبود دانلود کن. True یعنی مدل آماده است."""
    if installed(engine, lang, size, model_dir):
        return True

    need = (WHISPER_MB.get(size, 100) + 60) * 1024 * 1024
    if free_space(model_dir) < need:
        raise RuntimeError(
            "فضای دیسک کافی نیست. حدود %s لازم است." % human(need)
        )

    if engine == "whisper":
        target = whisper_path(model_dir, size)
        download_whisper(model_dir, size, on_status=on_status, should_stop=should_stop)
        return True

    if engine == "vosk":
        key = "fa" if str(lang).startswith("fa") else "en"
        target = vosk_path(model_dir, key)
        download_vosk(
            model_dir, key, on_status=on_status,
            on_progress=on_progress, should_stop=should_stop,
        )
        return True

    return True


def watch_progress(engine, lang, size, model_dir, should_stop, poll=1.0):
    """مولد گزارش پیشرفت بر اساس اندازه پوشه مدل (برای نوار پیشرفت UI)"""
    info = describe(engine, lang, size, model_dir)
    path = Path(info["path"])
    target_bytes = info["size_mb"] * 1024 * 1024
    last = -1
    while not (should_stop and should_stop()):
        current = dir_size(path)
        pct = min(100, int(current * 100 / target_bytes)) if target_bytes else 0
        if pct != last:
            last = pct
            yield pct, human(current), human(target_bytes)
        if current >= target_bytes * 0.98 and current > 0:
            yield 100, human(current), human(target_bytes)
            return
        import time as _t
        _t.sleep(poll)
