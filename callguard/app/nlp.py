"""Text normalisation, Hinglish mapping, number-word conversion, and PII redaction."""
import re
from typing import List, Optional

HINGLISH = {
    # Finance guarantees & pressure
    r"\bpakka profit\b": "guaranteed profit",
    r"\bpakka guarantee hai\b": "guaranteed",
    r"\bpakka\b": "guaranteed",
    r"\bguarantee hai\b": "guaranteed",
    r"\bkoi risk nahi\b": "risk free",
    r"\bbilkul safe\b": "risk free",
    r"\bkoi khatra nahi\b": "risk free",
    r"\bpaise double\b": "definitely make double",
    r"\bturant invest karo\b": "act now",
    r"\bturant\b": "act now",
    r"\babhi sign karo\b": "sign today",
    r"\baaj hi sign karo\b": "sign today",
    r"\baaj hi\b": "today only",
    r"\bbas aaj ke liye\b": "today only",
    r"\bsab laga do\b": "put everything",
    r"\bsaara paisa\b": "put everything",
    r"\bbina padhe\b": "no need to read",
    # Debt collection harassment & threats
    r"\bpolice bhej\w*\b": "send the police",
    r"\bghar aayenge\b": "come to your home",
    r"\bghar pe aayenge\b": "come to your home",
    r"\bjail bhej\w*\b": "send to jail",
    r"\bjail karwayenge\b": "jail",
    r"\bboss ko batayenge\b": "tell your boss",
    r"\bparivar ko batayenge\b": "tell your family",
    r"\bchirkut\b": "idiot",
    r"\bbewakoof\b": "idiot",
    r"\bnalayak\b": "worthless",
    r"\bchor\b": "liar",
    r"\bfraud kahin ke\b": "liar",
    # Healthcare & medication
    r"\bdawa band kar do\b": "stop taking medication",
    r"\bdawai mat lo\b": "stop taking medication",
    r"\bdose double kar lo\b": "double your dose",
    r"\bdo guna dose\b": "double your dose",
    r"\bgoli mat lo\b": "stop taking medication",
    r"\btest result batao\b": "lab results",
    # Insurance misrepresentation
    r"\bsab kuch cover hai\b": "covers everything",
    r"\bsab kuch cover\b": "covers everything",
    r"\bsab bimari cover\b": "covers everything",
    r"\bkoi exclusion nahi\b": "no exclusions",
    r"\bturant claim pass\b": "pays out in a day",
    r"\bek din me claim\b": "pays out in a day",
    # Crisis line & domestic safety
    r"\bmar jaana\b": "want to die",
    r"\bmarna chahta\b": "want to die",
    r"\bmarne ka mann\b": "want to die",
    r"\bkhud ko khatam\b": "end it all",
    r"\bkhatam karna chahta\b": "end it all",
    r"\bjaan dena chahta\b": "want to die",
    r"\batmahatya\b": "kill myself",
    r"\bjeene ka koi fayda nahi\b": "no reason to live",
    r"\bkuch bacha nahi\b": "no reason to live",
    r"\bmaar peet\b": "hurting me",
    r"\bmujhe maarta hai\b": "he hits me",
    r"\bmujhe maarti hai\b": "she hits me",
    r"\bghar jaane se darr\b": "afraid to go home",
    r"\bghar jane se darta\b": "afraid to go home",
    r"\bshaant ho jao kuch nahi hua\b": "calm down it is not that bad",
}

SMALL_NUMBERS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}

TENS = {"twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"}

NUM_WORDS = {
    "five hundred": "500",
    "eight fifty": "850",
    "eight hundred fifty": "850",
    "two hundred fifty": "250",
    "twelve": "12",
    "twenty five": "25",
    "one thousand": "1000",
}

PII = [
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"), "[EMAIL]"),
    (re.compile(r"\b(?:\d[ -]?){13,16}\b"), "[CARD]"),
    (re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"), "[AADHAAR]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
    (re.compile(r"(?<!\d)(?:\+?\d{1,3}[ -]?)?\d{10}(?!\d)"), "[PHONE]"),
]


def parse_number_tokens(tokens: List[str]) -> Optional[int]:
    """Parse a list of number words (e.g. ['eight', 'fifty'], ['five', 'hundred']) into an integer."""
    clean = [t for t in tokens if t != "and"]
    if not clean:
        return None
    if len(clean) == 1:
        return SMALL_NUMBERS.get(clean[0])
    if len(clean) == 2:
        if clean[0] in TENS and clean[1] in SMALL_NUMBERS and SMALL_NUMBERS[clean[1]] < 10:
            return SMALL_NUMBERS[clean[0]] + SMALL_NUMBERS[clean[1]]
        if clean[1] == "hundred" and clean[0] in SMALL_NUMBERS:
            return SMALL_NUMBERS[clean[0]] * 100
        if clean[1] == "thousand" and clean[0] in SMALL_NUMBERS:
            return SMALL_NUMBERS[clean[0]] * 1000
        # Colloquial clinical speech: 'eight fifty' -> 850, 'two fifty' -> 250
        if clean[0] in SMALL_NUMBERS and SMALL_NUMBERS[clean[0]] < 10 and clean[1] in TENS:
            return SMALL_NUMBERS[clean[0]] * 100 + SMALL_NUMBERS[clean[1]]
    if len(clean) == 3:
        # 'two hundred fifty' -> 250
        if clean[1] == "hundred" and clean[0] in SMALL_NUMBERS and clean[2] in SMALL_NUMBERS:
            return SMALL_NUMBERS[clean[0]] * 100 + SMALL_NUMBERS[clean[2]]
    if len(clean) == 4:
        # 'eight hundred seventy five' -> 875
        if clean[1] == "hundred" and clean[0] in SMALL_NUMBERS and clean[2] in TENS and clean[3] in SMALL_NUMBERS and SMALL_NUMBERS[clean[3]] < 10:
            return SMALL_NUMBERS[clean[0]] * 100 + SMALL_NUMBERS[clean[2]] + SMALL_NUMBERS[clean[3]]
    return None


def convert_number_words(text: str) -> str:
    """Convert spoken number word sequences into digits (e.g. 'eight fifty mg' -> '850 mg')."""
    valid_words = set(SMALL_NUMBERS.keys()) | {"hundred", "thousand", "and"}
    words = text.split()
    out = []
    i = 0
    n = len(words)

    while i < n:
        w_clean = re.sub(r"[^\w]", "", words[i].lower())
        if w_clean in valid_words and w_clean != "and":
            # Find longest contiguous sequence of number words (up to 4 tokens)
            best_val = None
            best_len = 0
            for seq_len in range(min(4, n - i), 0, -1):
                chunk = [re.sub(r"[^\w]", "", words[i + k].lower()) for k in range(seq_len)]
                if all(c in valid_words for c in chunk):
                    val = parse_number_tokens(chunk)
                    if val is not None:
                        best_val = val
                        best_len = seq_len
                        break
            if best_val is not None:
                out.append(str(best_val))
                i += best_len
                continue
        out.append(words[i])
        i += 1

    return " ".join(out)


def normalize(text: str) -> str:
    t = text.lower().strip()
    for pat, rep in HINGLISH.items():
        t = re.sub(pat, rep, t)
    t = convert_number_words(t)
    # Ensure legacy dictionary replacements as fallback
    for w, d in NUM_WORDS.items():
        t = t.replace(w, d)
    return re.sub(r"\s+", " ", t)


def redact(text: str) -> str:
    for rx, tag in PII:
        text = rx.sub(tag, text)
    return text
