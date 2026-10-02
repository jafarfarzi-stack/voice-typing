"""
ابزار خط فرمان برای مدل‌های آفلاین (اختیاری)

برنامه اصلی (app.py) خودش موقع اجرا می‌پرسد و دانلود می‌کند،
پس معمولاً نیازی به این اسکریپت نیست.

  python download_models.py --list
  python download_models.py --engine whisper --size small
  python download_models.py --engine vosk --lang fa
"""

import argparse
import sys
from pathlib import Path

import model_download as md

MODEL_DIR = Path(__file__).resolve().parent / "models"


def setup_utf8():
    """جلوگیری از UnicodeEncodeError در کنسول فارسی"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def show_list():
    print("\nWhisper (dقت بالا، پیشنهادی برای فارسی)")
    for size in md.WHISPER_SIZES:
        mark = "[نصب شده]" if md.whisper_installed(MODEL_DIR, size) else "[ندارد]"
        print("  %-9s ~%-5s MB  %s" % (size, md.WHISPER_MB[size], mark))
    print("\nVosk (سبک و سریع)")
    for lang, (folder, label, mb) in md.VOSK_FILES.items():
        mark = "[نصب شده]" if md.vosk_installed(MODEL_DIR, lang) else "[ندارد]"
        print("  %-4s %-30s ~%sMB  %s" % (lang, folder, mb, mark))
    print("\nمسیر مدل‌ها: %s" % MODEL_DIR)
    print("فضای آزاد: %s\n" % md.human(md.free_space(MODEL_DIR)))


def do_download(engine, lang, size):
    def on_status(msg):
        print("  " + msg)

    def on_progress(done, total):
        if total:
            pct = int(done * 100 / total)
            bar = "#" * int(pct // 3)
            print("\r  [%s%s] %d%%" % (bar, "." * (33 - int(pct // 3)), pct), end="")
            if done >= total:
                print()

    print("شروع دانلود…")
    md.ensure(engine, lang, size, MODEL_DIR, on_status, on_progress)
    print("تمام شد.")


def main():
    setup_utf8()
    ap = argparse.ArgumentParser(description="مدل‌های آفلاین تایپ صوتی")
    ap.add_argument("--engine", choices=["whisper", "vosk"], default="whisper")
    ap.add_argument("--size", choices=md.WHISPER_SIZES, default="small")
    ap.add_argument("--lang", choices=["fa", "en"], default="fa")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.list:
        show_list()
        return
    do_download(args.engine, args.lang, args.size)
    show_list()


if __name__ == "__main__":
    main()
