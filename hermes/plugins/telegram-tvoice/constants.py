"""Language detection constants for the telegram-tvoice Hermes plugin."""
from __future__ import annotations

UK_HINTS = set("іїєґІЇЄҐ")
PL_HINTS = set("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ")

PL_WORDS = {
    "cześć",
    "czesc",
    "jest",
    "się",
    "sie",
    "nie",
    "tak",
    "proszę",
    "prosze",
    "dziękuję",
    "dziekuje",
    "mówi",
    "mowimy",
    "mówimy",
    "polsku",
    "polski",
    "polska",
}

UK_WORDS = {
    "привіт",
    "дякую",
    "українською",
    "українська",
    "україна",
    "говоримо",
    "будь",
    "ласка",
    "так",
    "ні",
    "що",
    "це",
    "цей",
    "можна",
    "буде",
}

EN_WORDS = {
    "a",
    "and",
    "are",
    "english",
    "hello",
    "is",
    "please",
    "test",
    "the",
    "this",
    "voice",
    "we",
}
