"""
lexicon_utils.py - Phonetic Substitution Engine for LitRPG and Cultivation Audiobooks
"""

import os
import re
import json

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_LEXICON_PATH = os.path.join(_SCRIPT_DIR, "litrpg_pronunciation_lexicon.json")
_COMPILED_LEXICON = []

# Hardcoded fallback dictionary ensures the pipeline never breaks if the JSON file is missing
_DEFAULT_LEXICON = {
    "dantian": "dahn-tee-en",
    "dantians": "dahn-tee-ens",
    "qi": "chee",
    "mantou": "mahn-toe",
    "mantous": "mahn-toes",
    "wastrel": "way-stril",
    "lackey": "lackey",
    "lackeys": "lackeys",
    "dao": "dow",
    "daoist": "dow-ist",
    "xianxia": "she-ahn-she-ah",
    "wuxia": "woo-she-ah",
    "fushi": "foo-she",
    "litrpg": "lit-R-P-G",
    "hp": "H-P",
    "mp": "M-P",
    "exp": "E-X-P"
}


def load_pronunciation_lexicon(json_path: str = _LEXICON_PATH) -> list:
    """Loads the pronunciation mapping and compiles case-insensitive word-boundary patterns."""
    global _COMPILED_LEXICON
    data = {}
    if os.path.isfile(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    data = loaded
        except Exception as e:
            print(f"[Lexicon Notice] Could not parse '{json_path}' ({e}). Falling back to defaults.", flush=True)

    if not data:
        data = _DEFAULT_LEXICON

    compiled = []
    for term, phonetic in data.items():
        if term and phonetic:
            pattern = re.compile(rf"\b{re.escape(term.strip())}\b", re.IGNORECASE)
            compiled.append((pattern, str(phonetic).strip()))

    # Sort descending by length so compound phrases match before single words
    compiled.sort(key=lambda x: len(x[0].pattern), reverse=True)
    _COMPILED_LEXICON = compiled
    return _COMPILED_LEXICON


def apply_pronunciation_lexicon(tts_text: str) -> str:
    """Substitutes raw terms with phonetic transliterations exclusively for speech synthesis."""
    if not tts_text or not isinstance(tts_text, str):
        return ""

    if not _COMPILED_LEXICON:
        load_pronunciation_lexicon()

    result = tts_text
    for pattern, replacement in _COMPILED_LEXICON:
        result = pattern.sub(replacement, result)

    return result