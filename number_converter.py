"""
تبدیل اعداد گفتاری به رقم
Convert spoken numbers to digits.

  «بیست سه»            → «23»
  «صد و بیست و سه»     → «123»
  «دو هزار»            → «2000»
  «بیست و پنج درصد»     → «25%»
  «دو ممیز پنج»        → «2.5»
  «twenty three»       → «23»   (lang="en")
"""

import re

# ------------------------------------------------------------------ فارسی

FA_UNITS = {
    "صفر": 0, "یک": 1, "دو": 2, "سه": 3, "چهار": 4, "پنج": 5,
    "شش": 6, "شیش": 6, "هفت": 7, "هشت": 8, "نه": 9,
}
FA_TEENS = {
    "ده": 10, "یازده": 11, "دوازده": 12, "سیزده": 13, "چهارده": 14,
    "پانزده": 15, "شانزده": 16, "هفده": 17, "هجده": 18, "نوزده": 19,
}
FA_TENS = {
    "بیست": 20, "سی": 30, "چهل": 40, "پنجاه": 50, "شصت": 60,
    "هفتاد": 70, "هشتاد": 80, "نود": 90,
}
FA_HUNDREDS = {
    "صد": 100, "دویست": 200, "سیصد": 300, "چهارصد": 400, "پانصد": 500,
    "ششصد": 600, "شیصد": 600, "هفتصد": 700, "هشتصد": 800, "نهصد": 900,
}
FA_SCALES = {
    "هزار": 1_000, "میلیون": 1_000_000,
    "میلیارد": 1_000_000_000, "بیلیون": 1_000_000_000,
}
# کلماتی که تنهایی عدد نیستند و نباید تبدیل شوند
FA_UNSAFE_ALONE = {"نه"}          # «نه» یعنی «not»
FA_UNSAFE_IN_SEQ = {"صفر"}        # «صفر» فقط داخل عدد

# اگر «نه» بلافاصله قبل از یکی از این‌ها بیاید، احتمالاً منظور ۹ بوده است
# («نه نامساوی چهار» → «9 != 4»)
_MATH_AFTER = (
    "نامساوی|نامساوي|نابرابر|مساوی|مساوي|برابر|بعلات|برابرست"
    "|منها|منهی|تفریق|جمع|به علاوه|علاوه|بعلاوه|اضافه"
    "|ضرب|حاصل ضرب|تقسیم|تقسيم|بخش"
    "|بزرگتر|بزرگ تر|بیشتر از|کوچکتر|کوچک تر|کمتر از"
    "|به لابه|به لاب|اسلش|لابه|درصد|ممیز"
)
_FA_NE_BEFORE_MATH = re.compile(
    r"^\s*(?:%s)\b" % _MATH_AFTER, re.IGNORECASE
)

FA_CONNECTORS = {"و"}
FA_DECIMAL = {"ممیز"}
FA_PERCENT = {"درصد", "percents", "percent"}

# ---------------------------------------------------------------- انگلیسی

EN_UNITS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9,
}
EN_TEENS = {
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19,
}
EN_TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
EN_HUNDREDS = {"hundred": 100}
EN_SCALES = {
    "thousand": 1_000, "million": 1_000_000,
    "billion": 1_000_000_000, "trillion": 1_000_000_000_000,
}
EN_CONNECTORS = {"and"}

MAX_SAFE = 10 ** 15


def _boundary():
    """مرز کلمه که نیم‌فاصله (ZWNJ) را هم در نظر می‌گیرد

    بدون این، «سه‌شنبه» به‌اشتباه با «سه» تطبیق می‌کند.
    """
    return r"(?<![\w\u200c\u200d\u0600-\u06ff])"


def _build_fa_pattern():
    words = sorted(
        set(FA_UNITS) | set(FA_TEENS) | set(FA_TENS)
        | set(FA_HUNDREDS) | set(FA_SCALES) | FA_CONNECTORS,
        key=len,
        reverse=True,
    )
    word = "(?:%s)" % "|".join(re.escape(w) for w in words)
    digit = "(?:%s)" % "|".join(sorted(set(FA_UNITS) - {"نه"}, key=len, reverse=True))
    connector = "(?:و\\s+)"
    seq = "%s(?:\\s+%s?%s)*" % (word, connector, word)
    # بخش اعشار: «دو ممیز پنج»
    frac = "(?:\\s+(?:%s)\\s+(?:%s)+)?" % (
        "|".join(FA_DECIMAL),
        "|".join(sorted(set(FA_UNITS) - FA_UNSAFE_ALONE, key=len, reverse=True)),
    )
    pct = "(?:\\s+(?:%s))?" % "|".join(FA_PERCENT)
    return _boundary() + seq + frac + pct + r"(?![\w\u200c\u200d])"


def _build_en_pattern():
    words = sorted(
        set(EN_UNITS) | set(EN_TEENS) | set(EN_TENS)
        | set(EN_HUNDREDS) | set(EN_SCALES) | EN_CONNECTORS,
        key=len,
        reverse=True,
    )
    word = "(?:%s)" % "|".join(re.escape(w) for w in words)
    digit = "(?:%s)" % "|".join(re.escape(w) for w in EN_UNITS)
    seq = "%s(?:\\s+(?:and\\s+)?%s)*" % (word, word)
    frac = "(?:\\s+point\\s+%s+)?" % digit
    pct = "(?:\\s+(?:%s))?" % "|".join(FA_PERCENT)
    return _boundary() + seq + frac + pct + r"(?![\w\u200c\u200d])"


FA_RE = re.compile(_build_fa_pattern(), re.IGNORECASE)
EN_RE = re.compile(_build_en_pattern(), re.IGNORECASE)

_FA_TABLES = (FA_UNITS, FA_TEENS, FA_TENS, FA_HUNDREDS, FA_SCALES)
_EN_TABLES = (EN_UNITS, EN_TEENS, EN_TENS, EN_HUNDREDS, EN_SCALES)


def _value_of(token, tables, connectors, lower=False):
    for table in tables:
        if lower and token in table:
            return table[token], False
        if token in table:
            return table[token], True
        if lower:
            for key, val in table.items():
                if key.lower() == token.lower():
                    return val, True
    return None, False


def _parse_fa(tokens):
    total = 0
    current = 0
    scale_seen = False
    for token in tokens:
        if token in FA_CONNECTORS:
            continue
        found = False
        for table in _FA_TABLES:
            if token in table:
                value, is_scale = table[token], table is FA_SCALES
                if is_scale:
                    total += (current or 1) * value
                    current = 0
                    scale_seen = True
                else:
                    current += value
                found = True
                break
        if not found:
            return None, False
    if current == 0 and not scale_seen and total == 0:
        return None, False
    return total + current, scale_seen


def _parse_en(tokens):
    """در انگلیسی hundred ضریب است: five hundred = 500"""
    total = 0
    current = 0
    scale_seen = False
    for token in tokens:
        if token in EN_CONNECTORS:
            continue
        key = token.lower()
        found = False
        for table in _EN_TABLES:
            match = None
            for k, v in table.items():
                if k == key:
                    match = (v, table is EN_SCALES, table is EN_HUNDREDS)
                    break
            if match:
                value, is_scale, is_hundred = match
                if is_scale:
                    total += (current or 1) * value
                    current = 0
                    scale_seen = True
                elif is_hundred:
                    current = (current or 1) * value
                else:
                    current += value
                found = True
                break
        if not found:
            return None, False
    if current == 0 and not scale_seen and total == 0:
        return None, False
    return total + current, scale_seen


def _fraction_digits(raw, is_fa):
    """بخش اعشار را به رقم تبدیل می‌کند. None یعنی اعشار نبود"""
    lowered = raw.lower()
    if is_fa:
        marker = "ممیز"
        table = FA_UNITS
    else:
        marker = "point"
        table = EN_UNITS
    idx = lowered.find(marker)
    if idx < 0:
        return None
    rest = raw[idx + len(marker):]
    digits = ""
    for token in re.split(r"\s+", rest.strip()):
        token = token.strip()
        if not token:
            continue
        val = None
        if is_fa:
            val = FA_UNITS.get(token)
            if val is None:
                val = FA_UNITS.get(token.strip("."))
        else:
            for k, v in EN_UNITS.items():
                if k == token.lower().strip(".,"):
                    val = v
                    break
        if val is None:
            break
        digits += str(val)
    return digits or None


def _strip_tail(raw, is_fa):
    """جدا کردن بخش درصد از عبارت"""
    low = raw.lower()
    for word in ("درصد", "percent", "percents"):
        idx = low.rfind(" " + word)
        if idx > 0:
            return raw[:idx], True
    return raw, False


def _format(value, frac, percent, digits_sep):
    if value is None or value < 0 or value > MAX_SAFE:
        return None
    if value == 0 and frac is None:
        return None
    if frac:
        out = "%d%s%s" % (value, digits_sep, frac)
    else:
        out = "%d" % value
    if percent:
        out += "%"
    return out


def convert_persian(text):
    """اعداد فارسی را به رقم لاتین تبدیل می‌کند"""

    def repl(match):
        raw = match.group(0)
        body, percent = _strip_tail(raw, True)
        frac = _fraction_digits(body, True)
        if frac is not None:
            head = body[: body.lower().find("ممیز")]
            head_tokens = re.split(r"\s+", head.strip())
        else:
            head_tokens = re.split(r"\s+", body.strip())

        tokens = [t for t in head_tokens if t and t not in FA_CONNECTORS]
        if not tokens:
            return raw
        # محافظت: «نه» تنهایی یعنی «نه/not» — مگر اینکه قبل از عملگر ریاضی بیاید
        if len(tokens) == 1 and tokens[0] in FA_UNSAFE_ALONE:
            after = match.string[match.end():]
            if not _FA_NE_BEFORE_MATH.match(after):
                return raw
        # «صفر» فقط داخل عدد معتبر است
        if len(tokens) == 1 and tokens[0] in FA_UNSAFE_IN_SEQ:
            return raw

        value, _scale = _parse_fa(head_tokens)
        if value is None:
            return raw
        out = _format(value, frac, percent, ".")
        return out if out is not None else raw

    return FA_RE.sub(repl, text)


def convert_english(text):
    """اعداد انگلیسی را به رقم تبدیل می‌کند"""

    def repl(match):
        raw = match.group(0)
        body, percent = _strip_tail(raw, False)
        frac = _fraction_digits(body, False)
        if frac is not None:
            head = body[: body.lower().find("point")]
            head_tokens = re.split(r"\s+", head.strip())
        else:
            head_tokens = re.split(r"\s+", body.strip())

        tokens = [t for t in head_tokens if t and t.lower() not in EN_CONNECTORS]
        if not tokens:
            return raw
        # تنها یک کلمه‌ی بی‌ارزش تبدیل نشود (مثل «a»-مانند موارد)
        if len(tokens) == 1 and tokens[0].lower() in ("one", "two", "six"):
            pass

        value, _scale = _parse_en(head_tokens)
        if value is None:
            return raw
        out = _format(value, frac, percent, ".")
        return out if out is not None else raw

    return EN_RE.sub(repl, text)


def normalize_numbers(text, lang="fa-IR", enabled=True):
    """نقطه‌ی ورود اصلی"""
    if not enabled or not text:
        return text
    try:
        if str(lang).startswith("fa"):
            return convert_persian(text)
        return convert_english(text)
    except Exception:
        return text
