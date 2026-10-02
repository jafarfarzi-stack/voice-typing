"""
تایپ صوتی فارسی / English  —  نسخه آفلاین
Voice Typing App - Persian & English, offline speech-to-text
"""

import json
import logging
import queue
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import keyboard
import pyperclip
import pystray
from PIL import Image, ImageDraw

import i18n
import math_symbols
import model_download
import number_converter
import offline_stt

APP_NAME = "تایپ صوتی"
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = Path.home() / ".voice_typing_config.json"
LOG_PATH = Path.home() / ".voice_typing.log"
MODEL_DIR = BASE_DIR / "models"

LANGS = {"fa-IR": "fa-IR", "en-US": "en-US"}

COLORS = {
    "bg": "#f0f4f8",
    "primary": "#4a6cf7",
    "danger": "#ff4757",
    "ok": "#2ecc71",
    "text": "#333",
    "muted": "#666",
    "border": "#d0d7e3",
    "white": "#ffffff",
    "panel": "#e8ecf1",
    "warn": "#fff3cd",
}
FONT = ("Tahoma", 10)

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)
log = logging.getLogger("voice_typing")

PUNCTUATION = ".,،؛:!?؟۔؛"
COMMAND_TEXTS = {
    "fa": {
        "copy": "[کپی شد] ",
        "paste": "[پیست شد] ",
        "clear": "[پاک شد] ",
        "stop": "[توقف] ",
    },
    "en": {
        "copy": "[copied] ",
        "paste": "[pasted] ",
        "clear": "[cleared] ",
        "stop": "[stopped] ",
    },
}


class Config:
    """تنظیمات ذخیره‌شده کاربر"""

    DEFAULTS = {
        "lang": "fa-IR",
        "engine": "whisper",
        "whisper_size": "small",
        "direct": True,
        "auto_enter": False,
        "auto_punct": True,
        "digits": True,
        "math": True,
        "always_on_top": True,
        "hotkey": "f8",
        "silence": 0.9,
        "min_phrase": 0.4,
        "phrase_limit": 14,
        "auto_lang": False,
    }

    NUMERIC = {"silence", "min_phrase", "phrase_limit"}

    def __init__(self, path=CONFIG_PATH):
        self.path = path
        self.data = dict(self.DEFAULTS)
        self.load()

    def load(self):
        try:
            if self.path.exists():
                with open(self.path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                for key, default in self.DEFAULTS.items():
                    if key not in saved:
                        continue
                    value = saved[key]
                    if key in self.NUMERIC:
                        try:
                            value = float(value)
                        except (TypeError, ValueError):
                            continue
                    if isinstance(default, bool) and not isinstance(value, bool):
                        continue
                    self.data[key] = value
                log.info("Config loaded")
        except Exception:
            log.exception("Config load failed")
        return self.data

    def save(self):
        try:
            tmp = self.path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            tmp.replace(self.path)
        except Exception:
            log.exception("Config save failed")

    def __getitem__(self, key):
        return self.data.get(key, self.DEFAULTS.get(key))

    def __setitem__(self, key, value):
        self.data[key] = value


class HotkeyManager:
    def __init__(self):
        self.handlers = set()

    def register(self, combo, callback):
        try:
            keyboard.add_hotkey(combo, callback, suppress=False)
            self.handlers.add(combo)
            log.info("Hotkey registered: %s", combo)
            return True
        except Exception:
            log.exception("Hotkey register failed: %s", combo)
            return False

    def unregister_all(self):
        for combo in list(self.handlers):
            try:
                keyboard.remove_hotkey(combo)
            except Exception:
                log.exception("Hotkey remove failed: %s", combo)
        self.handlers.clear()


class CommandTable:
    """فرمان‌های صوتی — تطبیق دقیق و امن"""

    def __init__(self):
        self.stop_words = {
            "تمام", "پایان", "پایان بده", "بس کن", "توقف", "خداحافظ",
            "finish", "stop", "done",
        }
        self.copy_words = {"کپی", "کپی کن", "کپیش کن", "copy"}
        self.paste_words = {"پیست", "پیست کن", "بچسبان", "paste"}
        self.clear_words = {"پاک", "پاک کن", "پاکش کن", "حذف", "clear", "delete"}
        self.undo_words = {"برگرد", "برگردان", "undo", "بازگرد"}
        self.lang_words = {
            "فارسی": "fa-IR", "برو فارسی": "fa-IR", "زبان فارسی": "fa-IR",
            "حرف بزن فارسی": "fa-IR",
            "انگلیسی": "en-US", "برو انگلیسی": "en-US", "زبان انگلیسی": "en-US",
            "حرف بزن انگلیسی": "en-US",
            "persian": "fa-IR", "farsi": "fa-IR",
            "english": "en-US", "eng": "en-US",
        }
        # ترتیب مهم: طولانی‌ترین عبارت‌ها اول بررسی شوند
        self._lang_keys = sorted(self.lang_words, key=len, reverse=True)

    def detect(self, raw):
        """خروجی: dict(action=..., ...) یا None"""
        cmd = raw.lower().strip(" \t.,،؛:!?؟۔")
        cmd = " ".join(cmd.split())
        if not cmd or len(cmd) > 24:
            return None

        if cmd in self.lang_words:
            return {"action": "lang", "lang": self.lang_words[cmd]}
        for key in self._lang_keys:
            if re_has(cmd, key) and len(cmd) <= len(key) + 6:
                return {"action": "lang", "lang": self.lang_words[key]}

        if cmd in self.stop_words:
            return {"action": "stop"}
        if cmd in self.copy_words:
            return {"action": "copy"}
        if cmd in self.paste_words:
            return {"action": "paste"}
        if cmd in self.clear_words:
            return {"action": "clear"}
        if cmd in self.undo_words:
            return {"action": "undo"}
        return None


def re_has(text, needle):
    return needle in text


class VoiceApp:
    def __init__(self, root, config=None):
        self.root = root
        self.config = config or Config()
        self.hotkeys = HotkeyManager()
        self.commands = CommandTable()

        self.engine = None
        self.engine_name = self.config["engine"]
        self.ui_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = None
        self.is_listening = False
        self.last_text = ""
        self.last_time = 0.0
        self.tray = None
        self._closing = False

        self._check_backends()
        self._setup_window()
        self._build_ui()
        self._register_hotkeys()
        self._start_ui_pump()

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.after(1000, self._auto_save)
        self._update_subtitle()
        self._set_status(self._engine_status_text())

    # ------------------------------------------------------------------ setup

    def _check_backends(self):
        self.available = offline_stt.installed_engines()
        log.info("Available engines: %s", self.available)
        if self.engine_name not in self.available:
            fallback = next(
                (e for e in ("whisper", "vosk", "google") if e in self.available), None
            )
            if fallback:
                log.warning("Engine %s missing, falling back to %s", self.engine_name, fallback)
                self.engine_name = fallback
                self.config["engine"] = fallback
            else:
                self.engine_name = "google"

    def _model_ready(self):
        return offline_stt.model_status(
            self.engine_name, self.lang.get(), self.size_var.get(), MODEL_DIR
        )["ready"]

    def _setup_window(self):
        self.root.title(i18n.tr("app_title", self.config["lang"]))
        self.root.geometry("780x720")
        self.root.minsize(680, 620)
        self.root.configure(bg=COLORS["bg"])
        self.root.attributes("-topmost", bool(self.config["always_on_top"]))

    def _t(self, key, **kwargs):
        return i18n.tr(key, self.lang.get(), **kwargs)

    def _build_ui(self):
        self._lbl = {}      # برچسب‌های ساده
        self._btn = {}      # دکمه‌ها
        self._chk = {}      # چک‌باکس‌ها

        header = tk.Frame(self.root, bg=COLORS["primary"], height=46)
        header.pack(fill="x")
        self._lbl["header"] = tk.Label(
            header, text="", bg=COLORS["primary"], fg="white",
            font=("Tahoma", 13, "bold"),
        )
        self._lbl["header"].pack(pady=10)

        self.subtitle = tk.Label(
            self.root, text="", bg=COLORS["bg"], fg=COLORS["muted"], font=FONT
        )
        self.subtitle.pack(pady=(4, 2))

        # ---------- ردیف موتور و زبان ----------
        top = tk.Frame(self.root, bg=COLORS["bg"])
        top.pack(fill="x", padx=14, pady=4)

        lang_box = tk.Frame(top, bg=COLORS["bg"])
        lang_box.pack(side="right", padx=4)
        self._lbl["lang_label"] = tk.Label(lang_box, text="", bg=COLORS["bg"], font=FONT)
        self._lbl["lang_label"].pack(side="right", padx=4)
        self.lang = tk.StringVar(value=self.config["lang"])
        self.lang_combo = ttk.Combobox(
            lang_box, textvariable=self.lang, values=list(LANGS), width=9,
            state="readonly",
        )
        self.lang_combo.pack(side="right")
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_language_change)

        engine_box = tk.Frame(top, bg=COLORS["bg"])
        engine_box.pack(side="right", padx=4)
        self._lbl["engine_label"] = tk.Label(engine_box, text="", bg=COLORS["bg"], font=FONT)
        self._lbl["engine_label"].pack(side="right", padx=4)
        self.engine_var = tk.StringVar(value=self.engine_name)
        self.engine_combo = ttk.Combobox(
            engine_box, textvariable=self.engine_var, width=9, state="readonly",
            values=[e for e in ("whisper", "vosk", "google")],
        )
        self.engine_combo.pack(side="right")
        self.engine_combo.bind("<<ComboboxSelected>>", self._on_engine_change)

        size_box = tk.Frame(top, bg=COLORS["bg"])
        size_box.pack(side="right", padx=4)
        self._lbl["model_label"] = tk.Label(size_box, text="", bg=COLORS["bg"], font=FONT)
        self._lbl["model_label"].pack(side="right", padx=4)
        self.size_var = tk.StringVar(value=self.config["whisper_size"])
        self.size_combo = ttk.Combobox(
            size_box, textvariable=self.size_var, width=8, state="readonly",
            values=["tiny", "base", "small", "medium", "large-v3"],
        )
        self.size_combo.pack(side="right")

        hotkey_box = tk.Frame(top, bg=COLORS["bg"])
        hotkey_box.pack(side="left", padx=4)
        self._lbl["hotkey_label"] = tk.Label(hotkey_box, text="", bg=COLORS["bg"], font=FONT)
        self._lbl["hotkey_label"].pack(side="left", padx=4)
        self.hotkey_var = tk.StringVar(value=self.config["hotkey"])
        tk.Entry(
            hotkey_box, textvariable=self.hotkey_var, width=7, font=FONT, bg="white",
            relief="flat", highlightthickness=1, highlightbackground=COLORS["border"],
        ).pack(side="left")
        self._btn["hotkey_set"] = tk.Button(
            hotkey_box, text="", font=FONT, relief="flat", bd=1, width=6,
            bg=COLORS["panel"], command=self._apply_hotkey,
        )
        self._btn["hotkey_set"].pack(side="left", padx=3)

        # ---------- چک‌باکس‌ها ----------
        self.direct = tk.BooleanVar(value=self.config["direct"])
        self.auto_enter = tk.BooleanVar(value=self.config["auto_enter"])
        self.auto_punct = tk.BooleanVar(value=self.config["auto_punct"])
        self.digits = tk.BooleanVar(value=self.config["digits"])
        self.math = tk.BooleanVar(value=self.config["math"])
        self.on_top = tk.BooleanVar(value=self.config["always_on_top"])
        self.auto_lang = tk.BooleanVar(value=self.config["auto_lang"])

        checks = tk.Frame(self.root, bg=COLORS["bg"])
        checks.pack(pady=2)
        items = [
            (self.direct, "chk_direct"),
            (self.auto_enter, "chk_enter"),
            (self.auto_punct, "chk_punct"),
            (self.digits, "chk_digits"),
            (self.math, "chk_math"),
            (self.on_top, "chk_ontop"),
            (self.auto_lang, "chk_autolang"),
        ]
        for i, (var, key) in enumerate(items):
            cb = tk.Checkbutton(
                checks, text="", variable=var, bg=COLORS["bg"], font=FONT,
                command=self._on_setting_change,
            )
            cb.grid(row=i // 4, column=i % 4, padx=6, pady=1)
            self._chk[key] = cb

        # ---------- متن ----------
        self.textbox = tk.Text(
            self.root, font=("Tahoma", 13), height=13, wrap="word", bg="white",
            relief="flat", bd=10, highlightthickness=1,
            highlightbackground=COLORS["border"], undo=True,
        )
        self.textbox.pack(padx=14, pady=8, fill="both", expand=True)
        self._add_text_menu()

        self.status = tk.Label(
            self.root, text="", bg=COLORS["bg"], fg=COLORS["primary"],
            font=("Tahoma", 10, "bold"), anchor="center", wraplength=720,
        )
        self.status.pack(fill="x", pady=2, ipady=2)

        self.spinner = ttk.Progressbar(self.root, mode="indeterminate", length=160)
        self.spinner.pack(fill="x", padx=50, pady=(0, 2))

        # ---------- دکمه‌ها ----------
        bar = tk.Frame(self.root, bg=COLORS["bg"])
        bar.pack(pady=6)
        specs = [
            ("btn_start", self.toggle, COLORS["primary"], "white", 11, True),
            ("btn_copy", self.copy_text, "white", COLORS["text"], 7, False),
            ("btn_clear", self.clear_text, "white", COLORS["text"], 7, False),
            ("btn_undo", self.undo_text, "white", COLORS["text"], 7, False),
            ("btn_save", self.save_file, COLORS["panel"], COLORS["text"], 7, False),
            ("btn_open", self.open_file, COLORS["panel"], COLORS["text"], 9, False),
            ("btn_settings", self.show_settings, COLORS["panel"], COLORS["text"], 9, False),
            ("btn_minimize", self.minimize_to_tray, COLORS["panel"], COLORS["text"], 9, False),
            ("btn_help", self.show_help, COLORS["warn"], COLORS["text"], 8, False),
        ]
        for col, (key, cmd, bg, fg, width, is_main) in enumerate(specs):
            btn = tk.Button(
                bar, text="", bg=bg, fg=fg, cursor="hand2", command=cmd,
                font=("Tahoma", 11, "bold") if is_main else FONT,
                width=width, relief="flat", bd=0 if is_main else 1,
                padx=14 if is_main else 4, pady=7 if is_main else 4,
            )
            btn.grid(row=0, column=col, padx=3)
            self._btn[key] = btn
            if is_main:
                self.btn = btn

        foot = tk.Frame(self.root, bg=COLORS["bg"])
        foot.pack(pady=(0, 6))
        self._btn["btn_model"] = tk.Button(
            foot, text="", font=FONT, bg=COLORS["white"], relief="flat",
            bd=1, command=self.prompt_model_download, cursor="hand2",
        )
        self._btn["btn_model"].pack(side="left", padx=4)
        self._btn["btn_mic_test"] = tk.Button(
            foot, text="", font=FONT, bg=COLORS["white"], relief="flat",
            bd=1, command=self.test_microphone, cursor="hand2",
        )
        self._btn["btn_mic_test"].pack(side="left", padx=4)

        self._apply_language()

    def _apply_language(self):
        """همه متن‌های رابط را با زبان فعلی به‌روزرسانی می‌کند"""
        lang = self.lang.get()
        self.root.title(i18n.tr("app_title", lang))
        for key, widget in self._lbl.items():
            widget.config(text=i18n.tr(key, lang))
        for key, widget in self._chk.items():
            widget.config(text=i18n.tr(key, lang))
        if not self.is_listening:
            self._btn["btn_start"].config(text=i18n.tr("btn_start", lang))
        else:
            self._btn["btn_start"].config(text=i18n.tr("btn_stop", lang))
        for key in (
            "btn_copy", "btn_clear", "btn_undo", "btn_save", "btn_open",
            "btn_settings", "btn_minimize", "btn_help", "btn_model",
            "btn_mic_test", "hotkey_set",
        ):
            if key in self._btn:
                self._btn[key].config(text=i18n.tr(key, lang))
        self._refresh_text_menu()

    def _on_language_change(self, _event=None):
        """زبان رابط و زبان موتور با هم عوض می‌شوند"""
        self._apply_language()
        self._update_subtitle()
        self._set_status(self._engine_status_text())
        self.config["lang"] = self.lang.get()
        self.config.save()

    def _add_text_menu(self):
        self.text_menu = tk.Menu(self.root, tearoff=0, font=FONT)

        def show_menu(event):
            self._refresh_text_menu()
            try:
                self.text_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.text_menu.grab_release()

        self.textbox.bind("<Button-3>", show_menu)
        self.textbox.bind("<Button-2>", show_menu)

    def _refresh_text_menu(self):
        lang = self.lang.get()
        menu = self.text_menu
        menu.delete(0, "end")
        menu.add_command(label=i18n.tr("menu_copy", lang), command=self.copy_text)
        menu.add_command(label=i18n.tr("menu_paste", lang), command=self.paste_text)
        menu.add_command(label=i18n.tr("menu_clear", lang), command=self.clear_text)
        menu.add_command(label=i18n.tr("menu_undo", lang), command=self.undo_text)
        menu.add_separator()
        menu.add_command(label=i18n.tr("menu_save_file", lang), command=self.save_file)
        menu.add_command(label=i18n.tr("menu_word", lang), command=self.export_docx)

    def _engine_status_text(self):
        label = offline_stt.engine_info().get(self.engine_name, self.engine_name)
        label = i18n.tr("engine_" + self.engine_name, self.lang.get())
        return self._t("st_engine", s=label)

    def _model_display(self, info):
        """نام مدل به زبان رابط"""
        ui = self.lang.get()
        if self.engine_name == "whisper":
            return "Whisper %s" % self.size_var.get()
        if self.engine_name == "vosk":
            label = i18n.tr("lang_fa" if self.lang.get().startswith("fa") else "lang_en", ui)
            return "Vosk %s" % label
        return i18n.tr("engine_google", ui)

    def _lang_label(self, code=None):
        code = code or self.lang.get()
        return i18n.tr("lang_fa" if code.startswith("fa") else "lang_en", self.lang.get())

    def _update_subtitle(self):
        if self.engine_name == "google":
            self.subtitle.config(text=self._t("sub_online"), fg=COLORS["danger"])
            return
        info = offline_stt.model_status(
            self.engine_name, self.lang.get(), self.size_var.get(), MODEL_DIR
        )
        name = self._model_display(info)
        if info["ready"]:
            self.subtitle.config(
                text=self._t("sub_offline", s=name), fg=COLORS["ok"]
            )
        else:
            self.subtitle.config(
                text=self._t("sub_need_model", s=name, d=info["size_mb"]),
                fg=COLORS["danger"],
            )

    # ------------------------------------------------------------ hotkeys / UI

    def _register_hotkeys(self):
        # هات‌کی از thread جدا صدا زده می‌شود؛ به صف UI می‌فرستیم
        self.hotkeys.register(self.config["hotkey"], lambda: self._post(self.toggle))
        if self.config["hotkey"] != "f8":
            self.hotkeys.register("f8", lambda: self._post(self.toggle))

    def _apply_hotkey(self):
        combo = self.hotkey_var.get().strip().lower()
        if not combo:
            return
        self.hotkeys.unregister_all()
        self.hotkeys.register(combo, lambda: self._post(self.toggle))
        if combo != "f8":
            self.hotkeys.register("f8", lambda: self._post(self.toggle))
        self.config["hotkey"] = combo
        self.config.save()
        self._set_status(self._t("st_hotkey_set", s=combo.upper()), COLORS["ok"])

    def _start_ui_pump(self):
        def pump():
            if self._closing:
                return
            try:
                job = self.ui_queue.get(timeout=0.08)
            except queue.Empty:
                self.root.after(40, pump)
                return
            try:
                job()
            except Exception:
                log.exception("UI job failed")
            self.root.after(10, pump)

        self.root.after(40, pump)

    def _post(self, fn, *args, **kwargs):
        self.ui_queue.put(lambda: fn(*args, **kwargs))

    def _set_status(self, text, color=None):
        self._post(self.status.config, text=text, fg=color or COLORS["primary"])

    def _set_listening_ui(self, on):
        self._post(
            self.btn.config,
            text=i18n.tr("btn_stop" if on else "btn_start", self.lang.get()),
            bg=COLORS["danger"] if on else COLORS["primary"],
        )
        # Progressbar یک شیء است، نه تابع؛ باید متدش را صدا بزنیم
        self._post(self.spinner.start if on else self.spinner.stop)

    def _on_engine_change(self, _event=None):
        self.engine_name = self.engine_var.get()
        self.config["engine"] = self.engine_name
        self.config.save()
        self._release_engine()
        self._update_subtitle()
        self._set_status(self._engine_status_text())

    def _on_setting_change(self):
        self._save_settings()
        self.root.attributes("-topmost", bool(self.on_top.get()))
        self._update_subtitle()

    # ------------------------------------------------------------ voice loop

    def _build_engine(self):
        name = self.engine_var.get()
        size = self.size_var.get()
        options = {
            "size": size,
            "silence": float(self.config["silence"]),
            "min_phrase": float(self.config["min_phrase"]),
            "phrase_limit": float(self.config["phrase_limit"]),
            "auto_lang": bool(self.auto_lang.get()),
            "timeout": 5.0,
        }
        log.info("Building engine %s (size=%s)", name, size)
        return offline_stt.build_engine(
            name, lang=self.lang.get(), model_dir=MODEL_DIR, options=options
        )

    def _release_engine(self):
        if self.engine is not None:
            try:
                self.engine.close()
            except Exception:
                log.exception("Engine close failed")
            self.engine = None

    def toggle(self):
        self.stop() if self.is_listening else self.start()

    def start(self):
        if self.is_listening:
            return

        if not self._preflight():
            return

        self.is_listening = True
        self._stop_event.clear()
        self._set_listening_ui(True)
        self._save_settings()
        self._update_subtitle()
        self.root.iconify()
        self._thread = threading.Thread(target=self._worker, daemon=True, name="voice-loop")
        self._thread.start()

    def _preflight(self):
        """قبل از شروع: پکیج و مدل باید آماده باشند"""
        self._stop_event.clear()
        self._save_settings()
        engine = self.engine_var.get()
        size = self.size_var.get()

        if engine not in offline_stt.installed_engines():
            pkg = offline_stt.missing_pip_package(engine) or engine
            messagebox.showerror(
                self._t("btn_settings"),
                self._t("ask_pip", s=pkg),
                parent=self.root,
            )
            return False

        if engine == "google":
            if not messagebox.askyesno(
                self._t("btn_settings"), self._t("ask_online"), parent=self.root
            ):
                return False
            return True

        if not self._model_ready():
            return self._prompt_download()
        return True

    def _prompt_download(self):
        """پرسیدن از کاربر برای دانلود مدل"""
        engine = self.engine_var.get()
        size = self.size_var.get()
        info = offline_stt.model_status(engine, self.lang.get(), size, MODEL_DIR)

        if not messagebox.askyesno(
            self._t("dl_title"),
            self._t(
                "ask_download",
                s=self._model_display(info), d=info["size_mb"],
                o=info["source"], p=info["path"],
            ),
            parent=self.root,
        ):
            return False

        ok = self._run_download_dialog(
            engine, self.lang.get(), size, self._model_display(info), info["size_mb"]
        )
        self._update_subtitle()
        return ok

    def _run_download_dialog(self, engine, lang, size, name, size_mb):
        """پنجره دانلود با نوار پیشرفت"""
        ui_lang = self.lang.get()
        win = tk.Toplevel(self.root)
        win.title(i18n.tr("dl_title", ui_lang))
        win.geometry("500x250")
        win.configure(bg="white")
        win.resizable(False, False)
        win.transient(self.root)
        win.attributes("-topmost", True)
        win.protocol("WM_DELETE_WINDOW", win.destroy)

        tk.Label(
            win, text=i18n.tr("dl_wait", ui_lang, s=name), bg="white",
            fg=COLORS["text"], font=("Tahoma", 11, "bold"),
        ).pack(pady=(18, 4))
        tk.Label(
            win, text=i18n.tr("dl_note", ui_lang), bg="white",
            fg=COLORS["muted"], font=("Tahoma", 9),
        ).pack()

        bar = ttk.Progressbar(win, mode="determinate", length=420)
        bar.pack(pady=14)

        info_lbl = tk.Label(
            win, text=i18n.tr("dl_preparing", ui_lang), bg="white",
            fg=COLORS["muted"], font=FONT,
        )
        info_lbl.pack()

        result = {"ok": False, "cancelled": False}
        done = threading.Event()

        def on_status(msg):
            self._post(info_lbl.config, text=msg)

        def on_progress(done_bytes, total_bytes):
            if not total_bytes:
                return
            pct = int(done_bytes * 100 / total_bytes)
            self._post(bar.config, value=pct)
            self._post(
                info_lbl.config,
                text=i18n.tr(
                    "dl_progress", ui_lang,
                    a=model_download.human(done_bytes),
                    b=model_download.human(total_bytes),
                    d=pct,
                ),
            )

        def worker():
            try:
                model_download.ensure(
                    engine, lang, size, MODEL_DIR,
                    on_status=on_status, on_progress=on_progress,
                    should_stop=done.is_set,
                )
                result["ok"] = True
            except Exception as exc:
                log.exception("Model download failed")
                result["error"] = str(exc)
            finally:
                done.set()
                self._post(finish)

        def cancel():
            result["cancelled"] = True
            done.set()
            win.destroy()

        def finish():
            if result.get("ok"):
                bar.config(value=100)
                info_lbl.config(
                    text=i18n.tr("dl_done", ui_lang), fg=COLORS["ok"]
                )
                win.after(400, win.destroy)
                return
            win.destroy()
            if result.get("cancelled"):
                return
            messagebox.showerror(
                i18n.tr("dl_failed_title", ui_lang),
                i18n.tr("dl_failed", ui_lang, s=result.get("error", "?")),
                parent=self.root,
            )

        tk.Button(
            win, text=i18n.tr("dl_cancel", ui_lang), font=FONT, width=10,
            relief="flat", command=cancel,
        ).pack(pady=(16, 14))

        threading.Thread(target=worker, daemon=True, name="model-download").start()

        win.transient(self.root)
        win.grab_set()
        win.focus_force()
        win.wait_window(win)
        return result["ok"]

    def stop(self, hide=True):
        if not self.is_listening:
            return
        self.is_listening = False
        self._stop_event.set()
        self._set_listening_ui(False)
        self._set_status(self._t("st_stopped"))
        if hide:
            self.root.deiconify()

    def _worker(self):
        try:
            engine = self._build_engine()
        except Exception:
            log.exception("Engine build failed")
            self._fatal(self._t("err_engine_build"))
            return

        self.engine = engine
        try:
            self._set_status(self._t("st_loading_model"))
            engine.load()
            log.info("Engine %s loaded", engine.name)
        except FileNotFoundError as exc:
            self._fatal(self._t("err_model_missing", s=str(exc)))
            self._post(self._prompt_download)
            return
        except ImportError as exc:
            pkg = offline_stt.missing_pip_package(engine.name) or exc.name
            self._fatal(self._t("err_pip", s=pkg, p=pkg))
            return
        except Exception:
            log.exception("Engine load failed")
            self._fatal(self._t("err_load_model"))
            return

        self._set_status(self._engine_status_text())

        try:
            with offline_stt.AudioCapture() as cap:
                while not self._stop_event.is_set():
                    try:
                        text = engine.transcribe(cap, should_stop=self._stop_event.is_set)
                    except Exception:
                        log.exception("Transcribe iteration failed")
                        self._set_status(self._t("st_audio_err"), COLORS["danger"])
                        time.sleep(0.5)
                        continue
                    if not text:
                        continue
                    self._handle_text(text)
        except Exception as exc:
            log.exception("Audio capture failed")
            self._fatal(self._t("err_mic", s=str(exc)))
            return
        finally:
            self._release_engine()
            log.info("Worker finished")

    def _fatal(self, message):
        log.error("Fatal: %s", message)
        self.is_listening = False
        self._stop_event.set()
        self._set_listening_ui(False)
        self._post(self.root.deiconify)
        self._set_status(message, COLORS["danger"])

    # ------------------------------------------------------------ text logic

    def _handle_text(self, text):
        raw = offline_stt.normalize_persian(text)
        if not raw:
            return

        now = time.time()
        if raw == self.last_text and now - self.last_time < 2.0:
            return
        self.last_text, self.last_time = raw, now

        cmd = self.commands.detect(raw)
        if cmd and self._run_command(cmd):
            return

        # «بیست سه» → «23»
        raw = number_converter.normalize_numbers(
            raw, self.lang.get(), self.digits.get()
        )
        # «23 منها 5» → «23 - 5»  (بعد از تبدیل اعداد)
        raw = math_symbols.normalize_math(
            raw, self.lang.get(), self.math.get()
        )

        if self.auto_punct.get() and raw[-1] not in PUNCTUATION:
            raw += "،" if self.lang.get().startswith("fa") else "."

        self._post(self._append, raw + " ")
        self._set_status(self._t("st_wrote", s=raw))

        if self.direct.get():
            self._type_directly(raw + " ")

    def _run_command(self, cmd):
        action = cmd["action"]
        if action == "lang":
            self._set_lang(cmd["lang"])
            label = i18n.tr(
                "lang_fa" if cmd["lang"].startswith("fa") else "lang_en",
                self.lang.get(),
            )
            prefix = "زبان" if self.lang.get().startswith("fa") else "Language"
            self._echo_command("[%s: %s] " % (prefix, label))
            self._set_status(self._t("st_lang", s=label), COLORS["ok"])
            return True
        if action == "stop":
            self._post(self.stop)
            self._echo_command(self._command_text("stop"))
            return True
        if action == "copy":
            self._post(self.copy_text)
            self._echo_command(self._command_text("copy"))
            self._set_status(self._t("st_copied"), COLORS["ok"])
            return True
        if action == "paste":
            try:
                keyboard.send("ctrl+v")
                self._echo_command(self._command_text("paste"))
            except Exception:
                log.exception("Paste failed")
            return True
        if action == "clear":
            self._post(self.clear_text)
            self._echo_command(self._command_text("clear"))
            return True
        if action == "undo":
            self._post(self.undo_text)
            return True
        return False

    def _command_text(self, name):
        lang = self.lang.get()
        table = COMMAND_TEXTS["en" if lang.startswith("en") else "fa"]
        return table.get(name, "")

    def _echo_command(self, text):
        self._post(self._append, text)
        if self.direct.get():
            self._type_directly(text, enter=False)

    def _type_directly(self, text, enter=True):
        try:
            pyperclip.copy(text)
            time.sleep(0.22)
            keyboard.send("ctrl+v")
            if enter and self.auto_enter.get():
                time.sleep(0.15)
                keyboard.send("enter")
        except Exception:
            log.exception("Direct typing failed")
            self._set_status(self._t("st_direct_fail"), COLORS["danger"])

    def _set_lang(self, code):
        self._post(self.lang.set, code)
        self.config["lang"] = code
        self.config.save()

    # ------------------------------------------------------------- commands

    def _append(self, text):
        self.textbox.insert(tk.END, text)
        self.textbox.see(tk.END)

    def copy_text(self):
        text = self.textbox.get("1.0", tk.END).strip()
        if not text:
            self._set_status(self._t("st_nothing_copy"), COLORS["danger"])
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update_idletasks()
            self._set_status(self._t("st_copied_n", d=len(text)), COLORS["ok"])
        except Exception:
            log.exception("Clipboard failed")

    def paste_text(self):
        try:
            text = pyperclip.paste()
            if text:
                self._append(text)
                self._set_status(self._t("st_pasted"))
        except Exception:
            log.exception("Paste failed")

    def clear_text(self):
        self.textbox.delete("1.0", tk.END)
        self._set_status(self._t("st_cleared"))

    def undo_text(self):
        try:
            self.textbox.edit_undo()
            self._set_status(self._t("st_undone"))
        except tk.TclError:
            self._set_status(self._t("st_nothing_undo"))

    def save_file(self):
        ui = self.lang.get()
        text = self.textbox.get("1.0", tk.END).strip()
        if not text:
            self._set_status(self._t("st_nothing_save"), COLORS["danger"])
            return
        path = filedialog.asksaveasfilename(
            parent=self.root, title=i18n.tr("btn_save", ui),
            defaultextension=".txt",
            filetypes=[(i18n.tr("ft_text", ui), "*.txt"), ("*", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self._set_status(self._t("st_saved", s=Path(path).name), COLORS["ok"])
        except OSError as exc:
            log.exception("Save failed")
            messagebox.showerror(
                i18n.tr("btn_save", ui), i18n.tr("err_save", ui, s=str(exc)),
                parent=self.root,
            )

    def open_file(self):
        ui = self.lang.get()
        path = filedialog.askopenfilename(
            parent=self.root, title=i18n.tr("btn_open", ui),
            filetypes=[(i18n.tr("ft_text", ui), "*.txt"), ("*", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                self._append(f.read())
            self._set_status(self._t("st_loaded", s=Path(path).name), COLORS["ok"])
        except OSError as exc:
            log.exception("Open failed")
            messagebox.showerror(
                i18n.tr("btn_open", ui), i18n.tr("err_open", ui, s=str(exc)),
                parent=self.root,
            )

    def export_docx(self):
        ui = self.lang.get()
        try:
            import docx
        except ImportError:
            messagebox.showinfo(
                i18n.tr("btn_settings", ui), i18n.tr("err_docx_lib", ui),
                parent=self.root,
            )
            return
        text = self.textbox.get("1.0", tk.END).strip()
        if not text:
            return
        path = filedialog.asksaveasfilename(
            parent=self.root, title=i18n.tr("menu_word", ui),
            defaultextension=".docx",
            filetypes=[("Word", "*.docx")],
        )
        if not path:
            return
        try:
            doc = docx.Document()
            for line in text.splitlines():
                doc.add_paragraph(line)
            doc.save(path)
            self._set_status(self._t("st_docx", s=Path(path).name), COLORS["ok"])
        except Exception as exc:
            log.exception("DOCX export failed")
            messagebox.showerror(
                i18n.tr("menu_word", ui), i18n.tr("err_docx", ui, s=str(exc)),
                parent=self.root,
            )

    # ------------------------------------------------------------- settings

    def _save_settings(self):
        try:
            self.config["lang"] = self.lang.get()
            self.config["engine"] = self.engine_var.get()
            self.config["whisper_size"] = self.size_var.get()
            self.config["direct"] = self.direct.get()
            self.config["auto_enter"] = self.auto_enter.get()
            self.config["auto_punct"] = self.auto_punct.get()
            self.config["digits"] = self.digits.get()
            self.config["math"] = self.math.get()
            self.config["always_on_top"] = self.on_top.get()
            self.config["auto_lang"] = self.auto_lang.get()
            self.config.save()
        except tk.TclError:
            log.exception("Setting read failed")

    def _auto_save(self):
        if not self._closing:
            self._save_settings()
            self.root.after(60000, self._auto_save)

    def show_settings(self):
        ui = self.lang.get()
        win = tk.Toplevel(self.root)
        win.title(i18n.tr("set_title", ui))
        win.configure(bg=COLORS["bg"])
        win.transient(self.root)
        win.resizable(False, False)
        frame = tk.Frame(win, bg=COLORS["bg"], padx=20, pady=15)
        frame.pack()

        tk.Label(
            frame, text=i18n.tr("set_head", ui), bg=COLORS["bg"],
            fg=COLORS["primary"], font=("Tahoma", 12, "bold"),
        ).grid(row=0, column=0, columnspan=2, pady=(0, 12))

        silence = tk.StringVar(value=str(self.config["silence"]))
        min_phrase = tk.StringVar(value=str(self.config["min_phrase"]))
        phrase = tk.StringVar(value=str(self.config["phrase_limit"]))

        rows = [
            ("set_silence", silence, 0.3, 3.0),
            ("set_min", min_phrase, 0.2, 3.0),
            ("set_max", phrase, 5, 60),
        ]
        for i, (key, var, lo, hi) in enumerate(rows, start=1):
            tk.Label(
                frame, text=i18n.tr(key, ui), bg=COLORS["bg"], font=FONT
            ).grid(row=i, column=0, sticky="e", pady=5, padx=8)
            tk.Spinbox(
                frame, from_=lo, to=hi, increment=0.1, textvariable=var, width=9,
                font=FONT, state="readonly",
            ).grid(row=i, column=1, pady=5)

        tk.Label(
            frame, text=i18n.tr("set_hint", ui),
            bg=COLORS["bg"], fg=COLORS["muted"], font=("Tahoma", 9),
        ).grid(row=4, column=0, columnspan=2, pady=(10, 0))

        def apply_and_close():
            try:
                self.config["silence"] = float(silence.get())
                self.config["min_phrase"] = float(min_phrase.get())
                self.config["phrase_limit"] = float(phrase.get())
                self.config.save()
                self._set_status(self._t("st_settings_saved"), COLORS["ok"])
                win.destroy()
            except ValueError:
                messagebox.showerror(
                    i18n.tr("set_title", ui), i18n.tr("err_num", ui), parent=win
                )

        btns = tk.Frame(frame, bg=COLORS["bg"])
        btns.grid(row=5, column=0, columnspan=2, pady=15)
        tk.Button(
            btns, text=i18n.tr("save_btn", ui), bg=COLORS["primary"], fg="white",
            font=FONT, width=10, command=apply_and_close, relief="flat",
        ).pack(side="left", padx=5)
        tk.Button(
            btns, text=i18n.tr("cancel", ui), font=FONT, width=10,
            command=win.destroy, relief="flat",
        ).pack(side="left", padx=5)

    def test_microphone(self):
        ui = self.lang.get()

        def run():
            try:
                with offline_stt.AudioCapture() as cap:
                    peak = 0.0
                    frames = 0
                    while frames < 30 and not self._stop_event.is_set():
                        frame = cap.read()
                        if frame is None:
                            raise RuntimeError(i18n.tr("err_mic", ui, s="read failed"))
                        peak = max(peak, offline_stt.rms(frame))
                        frames += 1
                        time.sleep(0.02)
                text = i18n.tr("mic_ok", ui, d=int(peak))
                if peak <= 60:
                    text += i18n.tr("mic_low", ui)
                self._post(
                    self.status.config,
                    text=text,
                    fg=COLORS["ok"] if peak > 60 else COLORS["danger"],
                )
            except Exception as exc:
                log.exception("Mic test failed")
                self._fatal(i18n.tr("err_mic_test", ui, s=str(exc)))

        threading.Thread(target=run, daemon=True).start()

    def prompt_model_download(self):
        """دکمه «مدل آفلاین» — وضعیت را نشان می‌دهد یا دانلود می‌کند"""
        ui = self.lang.get()
        engine = self.engine_var.get()
        size = self.size_var.get()
        lang = self.lang.get()
        info = offline_stt.model_status(engine, lang, size, MODEL_DIR)

        if info["ready"]:
            other = [
                s for s in model_download.WHISPER_SIZES
                if s != size and not model_download.whisper_installed(MODEL_DIR, s)
            ]
            extra = (
                i18n.tr("info_model_more", ui, s=", ".join(other))
                if (engine == "whisper" and other) else ""
            )
            messagebox.showinfo(
                i18n.tr("btn_model", ui),
                i18n.tr("info_model_ok", ui, s=self._model_display(info), p=info["path"], e=extra),
                parent=self.root,
            )
            return

        if self._prompt_download():
            self._set_status(self._t("st_model_ready"), COLORS["ok"])
        self._update_subtitle()

    def show_download_help(self):
        ui = self.lang.get()
        text = i18n.model_help_text(ui) + "\n" + str(MODEL_DIR)
        win = tk.Toplevel(self.root)
        win.title(i18n.tr("model_title", ui))
        win.geometry("640x470")
        win.configure(bg="white")
        win.transient(self.root)
        win.attributes("-topmost", True)
        justify = "right" if i18n.is_rtl(ui) else "left"
        tk.Label(
            win, text=text, bg="white", fg=COLORS["text"], font=FONT,
            justify=justify, anchor="nw",
        ).pack(padx=20, pady=20, fill="both", expand=True)
        tk.Button(
            win, text=i18n.tr("help_ok", ui), bg=COLORS["primary"], fg="white",
            font=FONT, width=12, command=win.destroy, relief="flat",
        ).pack(pady=(0, 15))

    def show_help(self):
        ui = self.lang.get()
        text = i18n.help_text(ui)
        win = tk.Toplevel(self.root)
        win.title(i18n.tr("help_title", ui))
        win.geometry("660x620")
        win.configure(bg="white")
        win.transient(self.root)
        win.attributes("-topmost", True)
        justify = "right" if i18n.is_rtl(ui) else "left"
        tk.Label(
            win, text=text, bg="white", fg=COLORS["text"], font=FONT,
            justify=justify, anchor="nw",
        ).pack(padx=20, pady=18, fill="both", expand=True)
        tk.Button(
            win, text=i18n.tr("help_ok", ui), bg=COLORS["primary"], fg="white",
            font=FONT, width=12, command=win.destroy, relief="flat",
        ).pack(pady=(0, 15))

    # ------------------------------------------------------------------ tray

    @staticmethod
    def create_icon():
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((2, 2, 62, 62), radius=14, fill=COLORS["primary"])
        draw.ellipse((23, 13, 41, 31), fill="white")
        draw.rounded_rectangle((29, 31, 35, 44), radius=3, fill="white")
        draw.arc((19, 32, 45, 52), start=0, end=180, fill="white", width=3)
        draw.line((32, 49, 32, 56), fill="white", width=3)
        return img

    def minimize_to_tray(self):
        self._safe_save()
        self.root.withdraw()
        if self.tray is not None:
            return
        ui = self.lang.get()
        icon = pystray.Icon(
            APP_NAME, self.create_icon(), APP_NAME,
            menu=pystray.Menu(
                pystray.MenuItem(
                    i18n.tr("btn_open", ui), self._tray_show, default=True
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    i18n.tr("btn_start", ui) + " / " + i18n.tr("btn_stop", ui),
                    self._tray_toggle,
                ),
                pystray.MenuItem(i18n.tr("menu_copy", ui), self._tray_copy),
                pystray.MenuItem(i18n.tr("menu_clear", ui), self._tray_clear),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(i18n.tr("tray_quit", ui), self._tray_quit),
            ),
        )
        self.tray = icon
        threading.Thread(target=icon.run, daemon=True, name="tray").start()

    def _tray_show(self, icon=None, item=None):
        self.root.after(0, self.show_window)

    def _tray_toggle(self, icon=None, item=None):
        self.root.after(0, self.toggle)

    def _tray_copy(self, icon=None, item=None):
        self.root.after(0, self.copy_text)

    def _tray_clear(self, icon=None, item=None):
        self.root.after(0, self.clear_text)

    def _tray_quit(self, icon=None, item=None):
        self.root.after(0, self.on_close)

    def show_window(self):
        self.root.after(0, self._deiconify_safe)

    def _deiconify_safe(self):
        if self.tray is not None:
            try:
                self.tray.stop()
            except Exception:
                log.exception("Tray stop failed")
            self.tray = None
        self.root.deiconify()
        self.root.lift()
        try:
            self.root.focus_force()
        except tk.TclError:
            pass

    def on_close(self):
        if self.is_listening:
            if not messagebox.askyesno(
                self._t("tray_quit"), self._t("ask_exit"), parent=self.root
            ):
                return
        self.quit_app()

    def quit_app(self):
        if self._closing:
            return
        self._closing = True
        self.is_listening = False
        self._stop_event.set()
        self.hotkeys.unregister_all()
        self._safe_save()
        self._release_engine()
        if self.tray is not None:
            try:
                self.tray.stop()
            except Exception:
                log.exception("Tray stop failed")
            self.tray = None
        try:
            self.root.quit()
            self.root.destroy()
        except tk.TclError:
            log.exception("Destroy failed")

    def _safe_save(self):
        try:
            self._save_settings()
        except tk.TclError:
            log.exception("Save on exit failed")


def main():
    root = tk.Tk()
    app = VoiceApp(root)
    root.bind("<Control-q>", lambda e: app.on_close())
    root.mainloop()
    log.info("App exited")


if __name__ == "__main__":
    main()
