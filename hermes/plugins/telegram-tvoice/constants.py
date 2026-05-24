"""Constants for the telegram-tvoice Hermes plugin."""
from __future__ import annotations

PRESETS: dict[str, dict[str, str]] = {
    "ua-ostap": {
        "provider": "edge",
        "voice": "uk-UA-OstapNeural",
        "label": "Ukrainian Ostap",
        "lang": "uk",
    },
    "pl-marek": {
        "provider": "edge",
        "voice": "pl-PL-MarekNeural",
        "label": "Polish Marek",
        "lang": "pl",
    },
}

ALIASES: dict[str, str] = {
    "ua": "ua-ostap",
    "uk": "ua-ostap",
    "ukrainian": "ua-ostap",
    "ostap": "ua-ostap",
    "українська": "ua-ostap",
    "укр": "ua-ostap",
    "pl": "pl-marek",
    "polish": "pl-marek",
    "marek": "pl-marek",
    "польська": "pl-marek",
    "пол": "pl-marek",
}

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
