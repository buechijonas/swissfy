import re

from .content import EGGS


def phrase_pattern(phrase):
    words = []
    for word in phrase.lower().split():
        words.append(r"\W*".join(re.findall(r"\w+", word)))
    return r"\W+".join(words)


def egg_pattern(egg):
    return "|".join(f"(?:{phrase_pattern(phrase)})" for phrase in egg["phrases"])


PATTERNS = {egg["key"]: re.compile(egg_pattern(egg), re.IGNORECASE) for egg in EGGS}
