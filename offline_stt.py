"""
موتورهای تشخیص گفتار آفلاین
Offline Speech-to-Text engines (no internet required at runtime)

  WhisperEngine  -> faster-whisper  : دقت بالا (پیشنهادی)، فارسی + انگلیسی
  VoskEngine     -> vosk           : خیلی سریع و کم‌حجم، دقت متوسط
  GoogleEngine   -> SpeechRecognition recognize_google : آنلاین (پشتیبان)

همه موتورها یک رابط یکسان دارند:

    eng = build_engine(name, lang, model_dir)
    eng.load()                       -> آماده‌سازی (ممکن است طول بکشد)
    text = eng.transcribe(capture)   -> متن یا ""
    eng.close()
"""

import json
import logging
import re
import sys
import time
from pathlib import Path

import numpy as np

import model_download

log = logging.getLogger("voice_typing.offline")

SAMPLE_RATE = 16000
FRAME_SAMPLES = 4000          # 0.25 ثانیه
FRAME_SECONDS = FRAME_SAMPLES / SAMPLE_RATE
CHANNELS = 1

DEFAULT_MODEL_DIR = Path(__file__).resolve().parent / "models"

PERSIAN_MAP = str.maketrans({
    "ي": "ی",   # ي -> ی
    "ى": "ی",   # ى -> ی
    "ك": "ک",   # ك -> ک
    "ﻙ": "ک",
    "ﭬ": "و",
    "ة": "ه",
    "أ": "ا",
    "إ": "ا",
    "آ": "آ",
})


def normalize_persian(text):
    """یکسان‌سازی حروف عربی/فارسی و پاکسازی متن"""
    if not text:
        return ""
    text = text.translate(PERSIAN_MAP)
    text = re.sub(r"\s+", " ", text)
    text = text.replace(" ?", "؟").replace(" !", "!")
    text = text.strip()
    # حذف تکرار کلماتی که whisper گاهی لو می‌دهد
    text = re.sub(r"\b(\S+)( \1\b){2,}", r"\1\1", text)
    return text


# --------------------------------------------------------------------- capture


class AudioCapture:
    """خواندن صدای خام 16kHz mono از میکروفون"""

    def __init__(self, device=None):
        self.device = device
        self.pa = None
        self.stream = None

    def __enter__(self):
        import pyaudio

        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=self.device,
            frames_per_buffer=FRAME_SAMPLES,
        )
        return self

    def read(self):
        """یک فریم خواندن. None یعنی دستگاه قطع شد"""
        if self.stream is None:
            return None
        try:
            return self.stream.read(FRAME_SAMPLES, exception_on_overflow=False)
        except Exception:
            log.exception("Audio read failed")
            return None

    def __exit__(self, *exc):
        self.close()
        return False

    def close(self):
        if self.stream is not None:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                log.exception("Stream close failed")
            self.stream = None
        if self.pa is not None:
            try:
                self.pa.terminate()
            except Exception:
                log.exception("PyAudio terminate failed")
            self.pa = None


def rms(frame_bytes):
    """شدت صدا برای تشخیص سکوت"""
    arr = np.frombuffer(frame_bytes, dtype=np.int16).astype(np.float32)
    if arr.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(arr**2)))


# --------------------------------------------------------------------- engines


class BaseEngine:
    name = "base"
    display = "base"

    def __init__(self, lang="fa", model_dir=None, options=None):
        self.lang = lang
        self.model_dir = Path(model_dir or DEFAULT_MODEL_DIR)
        self.options = options or {}
        self._loaded = False

    def load(self):
        raise NotImplementedError

    def transcribe(self, capture, should_stop=None):
        raise NotImplementedError

    def close(self):
        pass

    @property
    def loaded(self):
        return self._loaded

    def set_lang(self, lang):
        self.lang = lang


class VoskEngine(BaseEngine):
    """vosk — سریع، کم‌حجم، آفلاین کامل"""

    name = "vosk"
    display = "Vosk (سریع، آفلاین)"

    def __init__(self, lang="fa", model_dir=None, options=None):
        super().__init__(lang, model_dir, options)
        self.model = None
        self._rec = None
        self._noise = float(self.options.get("noise_floor", 300.0))

    def _key(self):
        return "fa" if str(self.lang).startswith("fa") else "en"

    def _model_path(self):
        return model_download.vosk_path(self.model_dir, self._key())

    def available(self):
        return model_download.vosk_installed(self.model_dir, self._key())

    def load(self):
        import vosk

        vosk.SetLogLevel(-1)
        path = self._model_path()
        if not model_download.vosk_installed(self.model_dir, self._key()):
            raise FileNotFoundError(
                "مدل Vosk نصب نیست: %s" % path
            )
        log.info("Loading Vosk model from %s", path)
        self.model = vosk.Model(str(path))
        self._loaded = True
        return self

    def _make_rec(self):
        from vosk import KaldiRecognizer

        rec = KaldiRecognizer(self.model, SAMPLE_RATE)
        # کلمات تاییدشده را نگه می‌داریم تا اگر Vosk خودش وسط جمله
        # endpoint زد، چیزی از دست نرود
        rec.SetWords(True)
        return rec

    def transcribe(self, capture, should_stop=None):
        if not self._loaded:
            self.load()

        silence_needed = float(self.options.get("silence", 0.9))
        min_phrase = float(self.options.get("min_phrase", 0.4))
        max_phrase = float(self.options.get("phrase_limit", 14))
        noise_floor = float(self.options.get("noise_floor", 300.0))

        self._rec = self._make_rec()
        words = []
        speech_seconds = 0.0
        silence_run = 0.0

        while True:
            if should_stop and should_stop():
                return ""
            frame = capture.read()
            if frame is None:
                return ""

            level = rms(frame)
            speaking = level > noise_floor

            if speaking:
                noise_floor = max(120.0, min(noise_floor, level * 0.4))
                silence_run = 0.0
                speech_seconds += FRAME_SECONDS
            elif speech_seconds > 0:
                silence_run += FRAME_SECONDS

            # نتیجه نهایی داخلی Vosk را نگه می‌داریم و به تصمیم خودمان ادامه می‌دهیم
            if self._rec.AcceptWaveform(frame):
                payload = json.loads(self._rec.Result())
                for item in payload.get("result", []):
                    word = str(item.get("word", "")).strip()
                    if word:
                        words.append(word)

            if speech_seconds <= 0:
                continue

            long_enough = speech_seconds >= min_phrase
            paused = silence_run >= silence_needed

            if not long_enough or not (paused or speech_seconds >= max_phrase):
                continue

            partial = json.loads(self._rec.PartialResult()).get("partial", "")
            if partial.strip():
                words.extend(partial.split())

            text = normalize_persian(" ".join(words))
            words = []
            speech_seconds = 0.0
            silence_run = 0.0
            self._rec.Reset()

            if text:
                return text

    def close(self):
        self._rec = None
        self.model = None
        self._loaded = False


class WhisperEngine(BaseEngine):
    """faster-whisper — دقت بالا، آفلاین کامل، چندزبانه"""

    name = "whisper"
    display = "Whisper (دقیق، آفلاین)"

    def __init__(self, lang="fa", model_dir=None, options=None):
        super().__init__(lang, model_dir, options)
        self.size = str(self.options.get("size", "small"))
        self.model = None

    def _model_path(self):
        return model_download.whisper_path(self.model_dir, self.size)

    def available(self):
        return model_download.whisper_installed(self.model_dir, self.size)

    def load(self):
        from faster_whisper import WhisperModel

        path = self._model_path()
        if not model_download.whisper_installed(self.model_dir, self.size):
            raise FileNotFoundError("مدل Whisper نصب نیست: %s" % path)
        log.info("Loading faster-whisper '%s' from %s", self.size, path)
        self.model = WhisperModel(
            str(path),
            device=self.options.get("device", "cpu"),
            compute_type=self.options.get("compute_type", "int8"),
            local_files_only=True,
        )
        self._loaded = True
        return self

    def _transcribe_array(self, audio):
        lang_code = None if self.options.get("auto_lang") else (
            "fa" if self.lang.startswith("fa") else "en"
        )
        segments, _info = self.model.transcribe(
            audio,
            language=lang_code,
            task="transcribe",
            beam_size=self.options.get("beam_size", 1),
            best_of=1,
            temperature=0.0,
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
            vad_filter=False,
        )
        parts = [s.text.strip() for s in segments if s.text and s.text.strip()]
        return normalize_persian(" ".join(parts))

    def transcribe(self, capture, should_stop=None):
        if not self._loaded:
            self.load()

        silence_needed = float(self.options.get("silence", 0.9))
        max_phrase = float(self.options.get("phrase_limit", 14))
        min_phrase = float(self.options.get("min_phrase", 0.4))
        noise_floor = float(self.options.get("noise_floor", 300.0))
        buf = []
        buf_seconds = 0.0
        silence_run = 0.0

        while True:
            if should_stop and should_stop():
                return ""
            frame = capture.read()
            if frame is None:
                return ""

            level = rms(frame)
            speaking = level > noise_floor

            if speaking:
                noise_floor = max(120.0, min(noise_floor, level * 0.3))
                silence_run = 0.0
                buf.append(frame)
                buf_seconds += FRAME_SECONDS
            elif buf:
                silence_run += FRAME_SECONDS
                buf.append(frame)          # کمی صدای دنباله برای آخر کلمه
                buf_seconds += FRAME_SECONDS

            ready = False
            if buf:
                if silence_run >= silence_needed and buf_seconds >= min_phrase:
                    ready = True
                elif buf_seconds >= max_phrase:
                    ready = True

            if not ready:
                continue

            audio = np.frombuffer(b"".join(buf), dtype=np.int16)
            buf = []
            buf_seconds = 0.0
            silence_run = 0.0
            try:
                text = self._transcribe_array(audio.astype(np.float32) / 32768.0)
            except Exception:
                log.exception("Whisper transcribe failed")
                text = ""
            if text:
                return text

    def close(self):
        self.model = None
        self._loaded = False


class GoogleEngine(BaseEngine):
    """پشتیبان آنلاین — فقط اگر کاربر صریحاً انتخاب کند"""

    name = "google"
    display = "Google (آنلاین)"

    def load(self):
        import speech_recognition as sr

        self._sr = sr
        self._rec = sr.Recognizer()
        self._rec.pause_threshold = 1.8
        self._rec.non_speaking_duration = 0.8
        self._loaded = True
        return self

    def available(self):
        return True

    def transcribe(self, capture, should_stop=None):
        if not self._loaded:
            self.load()

        timeout = float(self.options.get("timeout", 5))
        phrase_limit = float(self.options.get("phrase_limit", 14))
        noise_floor = float(self.options.get("noise_floor", 300.0))

        deadline = time.time() + timeout
        audio_bytes = []
        silent = 0.0

        while time.time() < deadline:
            if should_stop and should_stop():
                return ""
            frame = capture.read()
            if frame is None:
                return ""

            audio_bytes.append(frame)
            level = rms(frame)
            if level > noise_floor:
                noise_floor = max(120.0, min(noise_floor, level * 0.3))
                silent = 0.0
            else:
                silent += FRAME_SECONDS

            if silent >= 1.2:
                break
            if len(audio_bytes) * FRAME_SECONDS >= phrase_limit:
                break

        if not audio_bytes:
            return ""

        raw = self._sr.AudioData(b"".join(audio_bytes), SAMPLE_RATE, 2)
        code = "fa-IR" if str(self.lang).startswith("fa") else "en-US"
        try:
            text = self._rec.recognize_google(raw, language=code)
        except self._sr.UnknownValueError:
            return ""
        except self._sr.RequestError:
            log.exception("Google request error")
            return ""
        return normalize_persian(text)


ENGINES = {
    "whisper": WhisperEngine,
    "vosk": VoskEngine,
    "google": GoogleEngine,
}


def engine_info():
    return {key: cls.display for key, cls in ENGINES.items()}


def build_engine(name, lang="fa", model_dir=None, options=None):
    cls = ENGINES.get(name)
    if cls is None:
        raise ValueError("موتور ناشناخته: %s" % name)
    return cls(lang=lang, model_dir=model_dir, options=options)


def backend_available(name):
    """آیا پکیج این موتور نصب است"""
    checks = {
        "whisper": "faster_whisper",
        "vosk": "vosk",
        "google": "speech_recognition",
    }
    mod = checks.get(name)
    if not mod:
        return False
    try:
        __import__(mod)
        return True
    except ImportError:
        return False


def installed_engines():
    return [name for name in ENGINES if backend_available(name)]


def ready_engines(lang="fa", size="small", model_dir=None):
    """موتورهایی که هم پکیجشان نصب است هم مدلشان روی دیسک"""
    model_dir = model_dir or DEFAULT_MODEL_DIR
    out = []
    for name in installed_engines():
        if name == "google":
            out.append(name)
        elif model_download.installed(name, lang, size, model_dir):
            out.append(name)
    return out


def model_status(engine, lang="fa", size="small", model_dir=None):
    model_dir = model_dir or DEFAULT_MODEL_DIR
    return model_download.describe(engine, lang, size, model_dir)


def missing_pip_package(engine):
    """نام پکیجی که باید نصب شود، یا None"""
    return {
        "whisper": "faster-whisper",
        "vosk": "vosk",
        "google": "SpeechRecognition",
    }.get(engine)
