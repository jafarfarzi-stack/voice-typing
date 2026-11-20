"""
ابزار خط فرمان برای مدل‌های آفلاین (اختیاری)

برنامه اصلی (app.py) خودش موقع اجرا میپرسد و دانلود میکند،
پس معمولاً نیازی به این اسکریپت نیست.

  python download_models.py --list
  python download_models.py --engine whisper --size small
  python download_models.py --engine vosk --lang fa
  python download_models.py --copy-from D:\\some\\folder
  python download_models.py --copy-to D:\\VoiceTyping-Portable
  python download_models.py --model-dir D:\\my-models --list
"""

import argparse
import sys

import model_download as md
import model_paths

MODEL_DIR = model_paths.default_dir()


def setup_utf8():
    """جلوگیری از UnicodeEncodeError در کنسول فارسی"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def show_list(model_dir=MODEL_DIR):
    print("\nWhisper (دقت بالا، پیشنهادی برای فارسی)")
    for size in md.WHISPER_SIZES:
        mark = "[نصب شده]" if md.whisper_installed(model_dir, size) else "[ندارد]"
        print("  %-9s ~%-5s MB  %s" % (size, md.WHISPER_MB[size], mark))
    print("\nVosk (سبک و سریع)")
    for lang, (folder, label, mb) in md.VOSK_FILES.items():
        mark = "[نصب شده]" if md.vosk_installed(model_dir, lang) else "[ندارد]"
        print("  %-4s %-30s ~%sMB  %s" % (lang, folder, mb, mark))
    print("\nمسیر مدلها: %s" % model_dir)
    print("فضای آزاد: %s\n" % md.human(md.free_space(model_dir)))


def do_download(engine, lang, size, model_dir=MODEL_DIR):
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
    md.ensure(engine, lang, size, model_dir, on_status, on_progress)
    print("تمام شد.")


def copy(src, dst):
    def status(msg):
        print("  " + msg)

    result = model_paths.copy_models(src, dst, on_status=status)
    if not result["found"]:
        print("  هیچ مدلی در پوشه مبدأ پیدا نشد.")
    else:
        print("  %d فایل کپی شد، %d فایل از قبل بود." % (
            result["copied"], result["skipped"]
        ))


def main():
    setup_utf8()
    ap = argparse.ArgumentParser(description="مدلهای آفلاین تایپ صوتی")
    ap.add_argument("--engine", choices=["whisper", "vosk"], default="whisper")
    ap.add_argument("--size", choices=md.WHISPER_SIZES, default="small")
    ap.add_argument("--lang", choices=["fa", "en"], default="fa")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--model-dir", default="", help="پوشه ثابت مدلها (پیشفرض: ~/.voice_typing_models)")
    ap.add_argument("--copy-from", default="", help="کپی مدلها از این پوشه به پوشه مدل")
    ap.add_argument("--copy-to", default="", help="کپی مدلها از پوشه مدل به این پوشه")
    args = ap.parse_args()

    model_dir = model_paths.resolve(args.model_dir)
    model_paths.ensure_dir(model_dir)

    if args.copy_from:
        copy(args.copy_from, model_dir)
    if args.copy_to:
        copy(model_dir, args.copy_to)

    if args.list:
        show_list(model_dir)
        return
    if not args.copy_from and not args.copy_to:
        do_download(args.engine, args.lang, args.size, model_dir)
    show_list(model_dir)


if __name__ == "__main__":
    main()
