"""
تبدیل کلمات ریاضی به نماد
Convert spoken math words into symbols.

قاعده‌ی ایمنی: فقط وقتی تبدیل می‌شود که نماد **بین دو عدد** بیاید.
  «بیست سه منها پنج»  → «23 - 5»
  «این مال منه»      → دست‌نخورده
  «جمع کن»           → دست‌نخورده
"""

import re

# --------------------------------------------------------------- فارسی

# طولانی‌ترین عبارت‌ها اول بررسی می‌شوند
FA_OPS = {
    # جمع
    "به علاوه": "+", "به علاوه ی": "+", "علاوه": "+", "بعلاوه": "+",
    "به علاوه بر": "+", "اضافه": "+", "به علاوه اش": "+",
    "جمع": "+", "جمعش": "+", "به جمع": "+", "برابر جمع": "+",
    # منها
    "منها": "-", "منهی": "-", "تفریق": "-", "منهای": "-", "منهایش": "-",
    "به منهای": "-", "کم": "-", "به کم": "-",
    # ضرب
    "ضرب": "*", "در ضرب": "*", "ضربدر": "*", "حاصل ضرب": "*",
    "ضرب در": "*", "ضربه": "*", "برابر با ضرب": "*",
    # تقسیم
    "تقسیم": "/", "تقسيم": "/", "تقسیم بر": "/", "بخش": "/",
    "تقسیم برابر": "/",
    # برابری
    "مساوی": "=", "مساوي": "=", "برابر": "=", "برابر با": "=",
    "برابرست": "=", "بعلات": "=", "برابر باشد": "=",
    # نابرابری
    "نامساوی": "!=", "نامساوي": "!=", "نابرابر": "!=", "نامساوی است": "!=",
    "برابر نیست": "!=", "مساوی نیست": "!=",
    # مقایسه
    "بزرگتر": ">", "بزرگ تر": ">", "بیشتر از": ">", "بزرگتر از": ">",
    "بزرگتر یا مساوی": ">=", "بزرگتر یا برابر": ">=",
    "کوچکتر": "<", "کوچک تر": "<", "کمتر از": "<", "کوچکتر از": "<",
    "کوچکتر یا مساوی": "<=", "کوچکتر یا برابر": "<=",
    # درصد و کسر
    "درصد": "%", "پرکنPercent": "%", "درصدش": "%",
    # اسلش
    "به لابه": "/", "به لاب": "/", "اسلش": "/", "لابه": "/",
    "اسلش میخورد": "/", "اسلش می خورد": "/", "خط مورب": "/",
}

# نمادهایی که لازم نیست بین دو عدد باشند (کلمه‌شان یکتا است)
FA_STANDALONE = {
    "پرانتز باز": "(", "پرانتز بسته": ")",
    "پرانتز باز کن": "(", "پرانتز ببند": ")",
    "کروشه باز": "[", "کروشه بسته": "]",
    "براکت باز": "{", "براکت بسته": "}",
    "علامت سوال": "?", "علامت تعجب": "!",
    "ممیز": ".",
}

# --------------------------------------------------------------- انگلیسی

EN_OPS = {
    # جمع
    "plus": "+", "add": "+", "added to": "+", "and": "+", "plus sign": "+",
    # منها
    "minus": "-", "subtract": "-", "subtracted from": "-", "less": "-",
    "minus sign": "-", "take away": "-",
    # ضرب
    "times": "*", "multiplied by": "*", "multiply by": "*", "multiply": "*",
    "times sign": "*",
    # تقسیم
    "divided by": "/", "divide by": "/", "over": "/", "divided": "/",
    # برابری
    "equals": "=", "equal to": "=", "is equal to": "=", "equal": "=",
    "equals sign": "=",
    # نابرابری
    "not equal to": "!=", "not equals": "!=", "is not equal to": "!=",
    "not equal": "!=", "does not equal": "!=",
    # مقایسه
    "greater than": ">", "more than": ">", "bigger than": ">",
    "greater than or equal to": ">=", "greater or equal to": ">=",
    "at least": ">=", "larger than": ">", "exceeds": ">",
    "less than": "<", "smaller than": "<", "fewer than": "<",
    "below": "<", "lower than": "<",
    "less than or equal to": "<=", "less or equal to": "<=",
    "at most": "<=", "up to": "<=",
}

EN_POSTFIX = {
    "percent": "%", "per cent": "%", "percentage": "%",
}

FA_POSTFIX = {
    "درصد": "%", "درصدش": "%", "پرکنPercent": "%",
}

EN_STANDALONE = {
    "open paren": "(", "close paren": ")",
    "open parenthesis": "(", "close parenthesis": ")",
    "open bracket": "[", "close bracket": "]",
    "open brace": "{", "close brace": "}",
    "question mark": "?", "exclamation mark": "!",
    "decimal point": ".", "dot": ".",
}


def _norm(text):
    return " ".join(text.split())


def _build_ops_pattern(table):
    words = sorted(table, key=len, reverse=True)
    return "(?:%s)" % "|".join(re.escape(w) for w in words)


def _apply_between_numbers(text, table, boundary=None):
    """فقط جاهایی که نماد بین دو رقم است"""
    pattern = _build_ops_pattern(table)
    edge = boundary or ""
    # عدد (اختیاری: رقم فارسی/لاتین) + فاصله + عملگر + فاصله + عدد
    num = r"[0-9\u06F0-\u06F9۰-۹]"
    rx = re.compile(
        edge + r"(?<=[0-9])(\s*)(" + pattern + r")(\s*)(?=[0-9])" + edge
    )

    def repl(m):
        return "%s%s%s" % (m.group(1), table[m.group(2)], m.group(3))

    return rx.sub(repl, text)


def _apply_standalone(text, table):
    """نمادهای یکتا، بدون نیاز به عدد"""
    pattern = _build_ops_pattern(table)

    def repl(m):
        return table[m.group(0)]

    return re.sub(pattern, repl, text, flags=re.IGNORECASE)


def _apply_postfix(text, table, boundary=None):
    """پسوندی: 23 درصد → 23%   (فقط بلافاصله بعد از عدد، بدون فاصله)"""
    pattern = _build_ops_pattern(table)
    edge = boundary or ""
    rx = re.compile(edge + r"(?<=[0-9])\s*(" + pattern + r")" + edge)

    def repl(m):
        return table[m.group(1)]

    return rx.sub(repl, text)


def normalize_math(text, lang="fa-IR", enabled=True):
    """نقطه‌ی ورود اصلی. انتظار دارد اعداد قبلاً به رقم تبدیل شده باشند."""
    if not enabled or not text:
        return text
    try:
        if str(lang).startswith("fa"):
            ops, standalone, postfix = FA_OPS, FA_STANDALONE, FA_POSTFIX
        else:
            ops, standalone, postfix = EN_OPS, EN_STANDALONE, EN_POSTFIX
        out = _apply_between_numbers(text, ops)
        out = _apply_postfix(out, postfix)
        out = _apply_standalone(out, standalone)
        return out
    except Exception:
        return text
