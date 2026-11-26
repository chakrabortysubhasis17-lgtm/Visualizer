import hashlib
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

try:
    import ftfy
    FTFY_AVAILABLE = True
except ImportError:
    ftfy = None
    FTFY_AVAILABLE = False

try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

try:
    from flashtext2 import KeywordProcessor
    FLASHTEXT_AVAILABLE = True
except ImportError:
    try:
        from flashtext import KeywordProcessor
        FLASHTEXT_AVAILABLE = True
    except ImportError:
        KeywordProcessor = None
        FLASHTEXT_AVAILABLE = False

try:
    import nltk
    from nltk.tokenize import sent_tokenize as _nltk_sent_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    nltk = None
    _nltk_sent_tokenize = None
    NLTK_AVAILABLE = False

try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer as _NltkVader
    NLTK_VADER_AVAILABLE = True
except ImportError:
    _NltkVader = None
    NLTK_VADER_AVAILABLE = False

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as _StandaloneVader
    STANDALONE_VADER_AVAILABLE = True
except ImportError:
    _StandaloneVader = None
    STANDALONE_VADER_AVAILABLE = False

try:
    from nrclex import NRCLex
    NRCLEX_AVAILABLE = True
except ImportError:
    NRCLex = None
    NRCLEX_AVAILABLE = False

try:
    import spacy
    try:
        _NLP = spacy.load("en_core_web_sm")
    except Exception:
        _NLP = None
except ImportError:
    _NLP = None

try:
    import gender_guesser.detector as _gender_mod
    _GENDER_DETECTOR = _gender_mod.Detector(case_sensitive=False)
except Exception:
    _GENDER_DETECTOR = None

try:
    import pronouncing
    PRONOUNCING_AVAILABLE = True
except ImportError:
    pronouncing = None
    PRONOUNCING_AVAILABLE = False

try:
    from num2words import num2words
    NUM2WORDS_AVAILABLE = True
except ImportError:
    num2words = None
    NUM2WORDS_AVAILABLE = False

try:
    import language_tool_python
    LANG_TOOL_AVAILABLE = True
except ImportError:
    language_tool_python = None
    LANG_TOOL_AVAILABLE = False

try:
    from deepmultilingualpunctuation import PunctuationModel
    DEEP_PUNCT_AVAILABLE = True
except ImportError:
    PunctuationModel = None
    DEEP_PUNCT_AVAILABLE = False

try:
    from lexicon_utils import apply_pronunciation_lexicon
except ImportError:
    def apply_pronunciation_lexicon(text: str) -> str:
        return text

try:
    from registry_utils import FALLBACK_BASE_CHARACTERS
except ImportError:
    FALLBACK_BASE_CHARACTERS = {
        "mc": {"display_name": "Protagonist", "gender": "Male", "voice": "en-US-GuyNeural", "pitch": "+0Hz"},
        "narrator": {"display_name": "Narrator", "gender": "Neutral", "voice": "en-US-ChristopherNeural", "pitch": "-2Hz"},
        "system": {"display_name": "System", "gender": "Neutral", "voice": "en-US-AriaNeural", "pitch": "+0Hz"},
    }

# =====================================================================
# LAZY SINGLETONS FOR NLP & PHONETIC ENGINES
# =====================================================================

_PUNCT_MODEL = None
_PUNCT_INIT_FAILED = False
_LANG_TOOL = None
_LANG_TOOL_INIT_FAILED = False
_VADER_ANALYZER = None
_NLTK_PUNKT_READY: Optional[bool] = None
_NLTK_TAGGER_READY: Optional[bool] = None
_PHONETIC_KP_CS = None
_PHONETIC_KP_CI = None


def _get_punct_model():
    global _PUNCT_MODEL, _PUNCT_INIT_FAILED
    if not DEEP_PUNCT_AVAILABLE or _PUNCT_INIT_FAILED:
        return None
    if _PUNCT_MODEL is None:
        try:
            _PUNCT_MODEL = PunctuationModel()
        except Exception:
            _PUNCT_INIT_FAILED = True
            return None
    return _PUNCT_MODEL


def _get_language_tool():
    global _LANG_TOOL, _LANG_TOOL_INIT_FAILED
    if not LANG_TOOL_AVAILABLE or _LANG_TOOL_INIT_FAILED:
        return None
    if _LANG_TOOL is None:
        try:
            _LANG_TOOL = language_tool_python.LanguageTool("en-US")
        except Exception:
            _LANG_TOOL_INIT_FAILED = True
            return None
    return _LANG_TOOL


def _get_vader():
    global _VADER_ANALYZER
    if _VADER_ANALYZER is not None:
        return _VADER_ANALYZER
    if NLTK_VADER_AVAILABLE and _NltkVader is not None:
        try:
            _VADER_ANALYZER = _NltkVader()
            return _VADER_ANALYZER
        except Exception:
            pass
    if STANDALONE_VADER_AVAILABLE and _StandaloneVader is not None:
        try:
            _VADER_ANALYZER = _StandaloneVader()
            return _VADER_ANALYZER
        except Exception:
            pass
    return None


def _nltk_split_sentences(text: str) -> Optional[List[str]]:
    global _NLTK_PUNKT_READY
    if not NLTK_AVAILABLE or _nltk_sent_tokenize is None or _NLTK_PUNKT_READY is False:
        return None
    try:
        res = _nltk_sent_tokenize(text)
        _NLTK_PUNKT_READY = True
        return res
    except LookupError:
        _NLTK_PUNKT_READY = False
        return None
    except Exception:
        return None


def _nltk_pos_tag_words(words: List[str]) -> Optional[List[Tuple[str, str]]]:
    global _NLTK_TAGGER_READY
    if not NLTK_AVAILABLE or nltk is None or _NLTK_TAGGER_READY is False:
        return None
    try:
        tagged = nltk.pos_tag(words)
        _NLTK_TAGGER_READY = True
        return tagged
    except LookupError:
        _NLTK_TAGGER_READY = False
        return None
    except Exception:
        return None


# =====================================================================
# AUTHORIZED DIRECTIVE CONSTANTS & VOICE POOLS
# =====================================================================

AUTHORIZED_FEMALE_VOICES = [
    "en-US-AvaMultilingualNeural",
    "en-US-JennyNeural",
    "en-US-EmmaMultilingualNeural",
    "en-US-AriaNeural",
    "en-US-MichelleNeural",
    "en-US-AvaNeural",
    "en-US-EmmaNeural",
]

AUTHORIZED_MALE_VOICES = [
    "en-US-AndrewMultilingualNeural",
    "en-US-GuyNeural",
    "en-US-BrianMultilingualNeural",
    "en-US-EricNeural",
    "en-US-SteffanNeural",
    "en-US-RogerNeural",
    "en-US-AndrewNeural",
    "en-US-BrianNeural",
]

FEMALE_VOICE_SET = set(AUTHORIZED_FEMALE_VOICES)
MALE_VOICE_SET = set(AUTHORIZED_MALE_VOICES) | {"en-US-ChristopherNeural"}

SFX_KEYS = frozenset({
    "footsteps", "run", "tiptoe", "horseandcart", "steps_indoor", "patter", "heavy_steps", "car", "screech",
    "creak", "crackle", "thunder", "drip", "wind", "forest", "ocean", "crickets", "rain",
    "hum", "whoosh", "teleport",
    "impact", "thud", "blade", "armor", "slash", "monster", "wardrum", "pain", "gunshot", "explosion", "snarl",
    "chime", "levelup", "interface", "swish", "quest", "alert",
    "achievement", "reward", "loot", "coin", "chest", "equip",
    "heartbeat", "gasp", "knock", "rustle", "splash", "squeak", "sigh", "slam", "clock", "glass_break", "paper",
    "short_breath_male", "short_breath_female",
    "market", "cheer", "disappointed", "dishes", "eating", "cooking",
    "heartwarm", "intimate",
    "whisper", "haunt", "howl", "bells", "gong", "crow", "bark", "steam_engine",
})

BGM_MOODS = frozenset({
    "combat", "tension", "sorrow", "wonder", "warmth",
    "intrigue", "triumph", "dread", "playful", "no_mood",
})

PITCH_TIERS = frozenset({
    "abyssal_floor", "grave_somber", "grim_rumble", "menacing_growl",
    "subdued_mournful", "intimate_whisper", "authoritative_low",
    "narrator_anchor", "thoughtful_drawl", "conversational_mid",
    "engaged_alert", "neutral_statement", "buoyant_lift", "inquisitive_tilt",
    "lung_reset_entry", "tense_strained", "urgent_command", "alarmed_spike",
    "defiant_shout", "frantic_screech", "hysterical_peak",
})

ONOMATOPOEIA_MAP = {
    "boom": "explosion",
    "booom": "explosion",
    "boooom": "explosion",
    "boooooom": "explosion",
    "kaboom": "explosion",
    "kabooooom": "explosion",
    "krakoom": "explosion",
    "kraakoom": "explosion",
    "thoom": "explosion",
    "fwoom": "whoosh",
    "whoosh": "whoosh",
    "whooooom": "whoosh",
    "bwhoom": "explosion",
    "bwhooooom": "explosion",
    "bang": "gunshot",
    "twang": "blade",
    "shing": "blade",
    "shaaa": "slash",
    "crack": "impact",
    "craaaack": "impact",
    "clang": "impact",
    "clink": "coin",
    "scratch": "rustle",
    "shatter": "glass_break",
    "thunk": "thud",
    "thock": "thud",
    "thud": "thud",
    "crunch": "impact",
    "pierce": "blade",
    "dong": "bells",
    "bong": "bells",
    "chime": "chime",
    "pop": "impact",
    "poof": "whoosh",
    "hiss": "steam_engine",
    "zap": "impact",
    "zzz": "impact",
    "gasp": "gasp",
    "beep": "alert",
    "ring": "chime",
    "ding": "chime",
    "roar": "monster",
    "roooaaar": "monster",
    "rooooooaaaaarrrr": "monster",
    "graaaah": "monster",
    "ggrrraaaaaahhhhh": "monster",
    "shriek": "monster",
    "shrieeeek": "monster",
    "bwooooooom": "wardrum",
    "rumble": "thunder",
}

# =====================================================================
# FLASHTEXT2 + REGEX PRONUNCIATION & TTS SANITIZATION ENGINE
# =====================================================================

STATIC_PHONETIC_CASE_SENSITIVE: Dict[str, str] = {
    "Qi": "Chee",
    "qi": "chee",
    "AoE": "A-O-E",
    "HP": "H-P",
    "MP": "M-P",
    "XP": "X-P",
    "DNA": "D-N-A",
    "HUD": "H-U-D",
}

STATIC_PHONETIC_CASE_INSENSITIVE: Dict[str, str] = {
    # Cultivation, Fantasy & LitRPG Core Terms
    "Dantian": "Dahn-tyen",
    "Mana": "Mah-nah",
    "Wyvern": "Why-vern",
    "Aether": "Ee-ther",
    "Nephilim": "Neh-fih-lim",
    "Incubus": "In-kyoo-bus",
    "Succubus": "Suk-yoo-bus",
    "Homunculi": "Ho-mung-kyoo-lye",
    "Homunculus": "Ho-mung-kyoo-lus",
    "Alraune": "Ahl-row-neh",
    "Chthonic": "Thon-ik",
    # Proper Names, Places & Clans across novels
    "Aedan": "Ay-dan",
    "Brocéliande": "Bro-say-lee-ahnd",
    "Broceliande": "Bro-say-lee-ahnd",
    "Nimue": "Nim-way",
    "Gawain": "Gah-wayn",
    "Caer-Londin": "Kair Lon-din",
    "Caerleon": "Kair-lee-on",
    "Tintagel": "Tin-taj-el",
    "Caliburn": "Kal-ih-burn",
    "Excalibur": "Eks-kal-ih-bur",
    "Aethelon": "Ay-theh-lon",
    "Malakor": "Mal-ah-kor",
    "Dubricus": "Doo-brih-kus",
    "Pellinore": "Pel-ih-nor",
    "Fomorian": "Fo-mor-ee-an",
    "Seimei": "Say-may",
    "Virigil": "Vih-rih-jil",
    "Ying Yue": "Ying Yweh",
    "Bingyue": "Bing-yweh",
    "Wan Er": "Wahn Air",
    "Wan Li": "Wahn Lee",
    "Luo": "Lwo",
    "Erebus": "Eh-reh-bus",
    "Lilieth": "Lil-ee-eth",
    "Xenos": "Zee-nos",
    "Yuffy": "Yoo-fee",
    "Celia": "See-lee-ah",
    "Olgor": "Ol-gor",
    "Fatima": "Fah-tee-mah",
    # Censored & Stripped Profanity
    "b**ch": "bitch",
    "b*tch": "bitch",
    "bch": "bitch",
    "s**t": "shit",
    "sht": "shit",
    "a**": "ass",
    # Interjections & Casual Contractions
    "Ahn": "Ahhn",
    "Opsss": "Oops",
    "Opss": "Oops",
    "C'mon": "Come on",
    "ba-dump": "ba dump",
    "Guha": "Guh-ha",
}

PHONETIC_REGEX_FALLBACK_MAP: List[Tuple[re.Pattern, Any]] = [
    (re.compile(r"\bLv\.?\s*(\d+)", re.I), r"Level \1"),
    (re.compile(r"\bf\*\*k(?:ing|ed|er)?\b", re.I), lambda m: "fuck" + m.group(0)[4:]),
    (re.compile(r"\bfck(?:ing|ed|er)?\b", re.I), lambda m: "fuck" + m.group(0)[3:]),
    (re.compile(r"\bSh-!"), "Shh!"),
    # System / Technical Syntax, Ratios & Version Strings ($44/120$, 14/20, v2.4, ==, |)
    (re.compile(r"\$(\d+)/(\d+)\$"), r"\1 of \2"),
    (re.compile(r"\b(\d+)/(\d+)\b"), r"\1 of \2"),
    (re.compile(r"\bv(\d+)\.(\d+)\b", re.I), r"version \1 point \2"),
    (re.compile(r"\s*==\s*"), " equals "),
    (re.compile(r"\s*\|\s*"), ". "),
    # Time Stamps & Slash Word Compounds
    (re.compile(r"\b(\d{1,2})\.(\d{2})\s*(AM|PM)\b", re.I), r"\1:\2 \3"),
    (re.compile(r"\b([a-zA-Z]{2,})/([a-zA-Z]{2,})\b"), r"\1 and \2"),
    (re.compile(r"\bNO\.\s*YOU\.\s*DON'?T!+", re.I), "No, you don't!"),
]


def _get_phonetic_processors():
    global _PHONETIC_KP_CS, _PHONETIC_KP_CI
    if not FLASHTEXT_AVAILABLE or KeywordProcessor is None:
        return None, None
    if _PHONETIC_KP_CS is None:
        kp_cs = KeywordProcessor(case_sensitive=True)
        for k, v in STATIC_PHONETIC_CASE_SENSITIVE.items():
            kp_cs.add_keyword(k, v)
        _PHONETIC_KP_CS = kp_cs
    if _PHONETIC_KP_CI is None:
        kp_ci = KeywordProcessor(case_sensitive=False)
        for k, v in STATIC_PHONETIC_CASE_INSENSITIVE.items():
            kp_ci.add_keyword(k, v)
        _PHONETIC_KP_CI = kp_ci
    return _PHONETIC_KP_CS, _PHONETIC_KP_CI


def apply_fast_phonetic_rules(text: str) -> str:
    """Applies O(N) flashtext2 bulk respellings plus dynamic regex & num2words conversions."""
    kp_cs, kp_ci = _get_phonetic_processors()
    if kp_cs is not None and kp_ci is not None:
        text = kp_cs.replace_keywords(text)
        text = kp_ci.replace_keywords(text)
    else:
        for k, v in STATIC_PHONETIC_CASE_SENSITIVE.items():
            text = re.sub(rf"\b{re.escape(k)}\b", v, text)
        for k, v in STATIC_PHONETIC_CASE_INSENSITIVE.items():
            text = re.sub(rf"\b{re.escape(k)}\b", v, text, flags=re.I)

    for pat, repl in PHONETIC_REGEX_FALLBACK_MAP:
        text = pat.sub(repl, text)

    if NUM2WORDS_AVAILABLE and num2words is not None:
        # Convert standalone percentage decimals ("38.4%" -> "38 point 4 percent") cleanly
        text = re.sub(
            r"\b(\d+)\.(\d+)%",
            lambda m: f"{m.group(1)} point {m.group(2)} percent",
            text,
        )

    return text


def is_known_english_word(word: str) -> bool:
    """Uses CMU Pronouncing Dictionary (pronouncing) to check if a word has standard English phonemes."""
    if not PRONOUNCING_AVAILABLE or pronouncing is None:
        return True
    clean = re.sub(r"[^a-zA-Z]", "", word).lower()
    if len(clean) <= 2:
        return True
    try:
        return bool(pronouncing.phones_for_word(clean))
    except Exception:
        return True


# =====================================================================
# CROSS-CHAPTER ALIASES, NAME LEXICONS & EPITHET MAPPINGS
# =====================================================================

KNOWN_ALIAS_GROUPS: Dict[str, Tuple[str, ...]] = {
    "fang": ("fang", "fong", "fawn"),
    "wan li": ("wan li", "wanli", "wanley"),
    "wan er": ("wan er", "waner", "wan air", "one air"),
    "luo bingyue": ("luo bingyue", "ingue", "ying yue", "yurining yua"),
    "aedan": ("aedan", "devlin", "devlin vance", "devlin-aedan"),
    "morgan le fay": ("morgan le fay", "morgan", "queen morgan", "lady morgan"),
}

COMMON_FEMALE_NAMES = frozenset({
    "fatima", "ember", "fang", "fong", "fawn", "helen", "wan li", "wan er", "luo bingyue", "ying yue",
    "ingue", "fina", "julia", "ada", "zeta", "pearl", "camila", "emma", "olivia", "celia", "mia",
    "diamond", "ivy", "luna", "yuffy", "maria", "foxy", "lilieth", "gabrielle", "kitty", "tiffany",
    "ruby", "briar", "morwenna", "nimue", "seraphina", "vespera", "morgan", "morgana", "elda",
    "lyra", "sera", "alice", "amelia", "anna", "aria", "athena", "audrey", "aurora", "ava", "bella",
    "charlotte", "chloe", "claire", "clara", "daisy", "diana", "elena", "elizabeth", "ella", "ellie",
    "elise", "emily", "eris", "eva", "evelyn", "felicia", "fiona", "freya", "grace", "hannah", "harper",
    "hazel", "iris", "isabella", "jade", "jane", "jasmine", "jenny", "jessica", "kate", "katherine",
    "katie", "kayla", "kylie", "laura", "layla", "leah", "lily", "lucy", "lydia", "madison", "maya",
    "megan", "melissa", "michelle", "mira", "molly", "naomi", "natalie", "nicole", "nina", "nora",
    "paige", "penelope", "rachel", "rebecca", "riley", "rose", "rosie", "sadie", "samantha", "sara",
    "sarah", "savannah", "scarlett", "selena", "serena", "sophia", "sophie", "stella", "summer",
    "sylvia", "taylor", "valerie", "vanessa", "victoria", "violet", "vivian", "wendy", "yuna", "zoe",
    "angel", "goddess", "queen", "princess", "duchess", "lady", "madam", "maiden", "woman", "girl",
    "sister", "mother", "aunt", "wife", "bride", "maid", "waitress", "receptionist", "heroine",
    "dryad", "lynx", "lamia", "serpent", "navigatrix", "baroness",
})

COMMON_MALE_NAMES = frozenset({
    "will", "cloud", "ethan", "damian", "erebus", "damon", "xenos", "bern", "ian", "miguel",
    "zashan", "heiden", "aster", "alvero", "zen", "aedan", "devlin", "merlin", "arthur", "kay",
    "ector", "geraint", "gawain", "pellinore", "thrain", "marcus", "brannoc", "lot", "mark",
    "urien", "carados", "brandegoris", "dubricus", "accolon", "malakor", "vane", "hollis",
    "torin", "wulfstan", "uther", "adam", "aiden", "alex", "alexander", "andrew", "anthony",
    "ben", "benjamin", "brad", "brandon", "brian", "caleb", "carlos", "charles", "chris",
    "christopher", "cole", "connor", "daniel", "david", "derek", "devon", "dominic", "dylan",
    "edward", "eli", "elijah", "eric", "evan", "felix", "frank", "gabriel", "garrett", "gavin",
    "george", "grant", "greg", "guy", "harry", "henry", "hunter", "isaac", "ivan", "jack",
    "jackson", "jacob", "jake", "james", "jason", "jay", "jeff", "jeremy", "john", "jonathan",
    "jordan", "joseph", "josh", "joshua", "julian", "justin", "kai", "kane", "kevin", "kyle",
    "lance", "leo", "leon", "liam", "logan", "lucas", "luke", "martin", "mason", "matt",
    "matthew", "max", "michael", "miles", "nathan", "nicholas", "nick", "noah", "nolan", "oliver",
    "oscar", "owen", "patrick", "paul", "peter", "philip", "ray", "raymond", "rex", "richard",
    "robert", "roger", "roman", "ryan", "sam", "samuel", "scott", "sean", "sebastian", "seth",
    "shane", "simon", "steffan", "stephen", "steve", "steven", "thomas", "tim", "tom", "tony",
    "travis", "trevor", "tristan", "tyler", "victor", "vincent", "walter", "warren", "wayne",
    "william", "wyatt", "xavier", "zach", "king", "prince", "duke", "lord", "sir", "father",
    "brother", "uncle", "husband", "boy", "man", "guard", "knight", "commander", "captain",
    "master", "elder", "grandmaster", "emperor", "baron", "archbishop", "admiral", "baker", "cadet",
})

# =====================================================================
# COMPILED REGEX PATTERNS (CORE DIRECTIVES 1 - 6)
# =====================================================================

RE_ALPHANUM = re.compile(r"[a-zA-Z0-9]")
RE_SCENE_BREAK = re.compile(r"^[\s*\-=~_#]{3,}$")

RE_AD_OR_NOTE_LINE = re.compile(
    r"^(?:"
    r"Ads\s+by\s+Pubfuture|Pubfuture\s+Ads|"
    r">?\s*Read\s+more\s+than\s+\d+\s+chapters|"
    r">?\s*NEW!\s*(?:Extra\s+R18|\[18\+\s*ASMR\])|"
    r"My\s+(?:Patreon-?page|ko-fi\s+page|Discord)|"
    r"Note\s*:|P\.?S\.?\s*:|"
    r"ACT\s+[IVX]+\s*:.*|"
    r"CHAPTER\s+\d+\s*:.*|"
    r"Chapter\s+\d+\.\s+.*|"
    r".*?\s+Chapter\s+\d+\.\s+.*"
    r")$",
    re.I,
)

RE_SYSTEM_LINE = re.compile(
    r"^(?:[\[\【\〖\『\《\［\{]\s*)?"
    r"(?:Ding!|The\s+Pendragon\s+Codex|Corrupted\s+System|Corrupted\s+Codex|Caer-Londin\s+Harbor\s+Status|"
    r"Rebel\s+Coalition\s+Fracture\s+Event|System(?:\s+(?:Alert|Message|Warning|Notice|Notification))?|"
    r"Warning!|Notice:|Announcement:|Prompt:|Quest(?:\s+(?:Updated|Alert|Complete))?:|"
    r"Status(?:\s+Window)?:|Stats?:|Skill(?:\s+Acquired)?:|Level\s+Up!?|Inventory:|Reward:)"
    r".*$",
    re.I,
)
RE_BRACKETED_SYSTEM_PARA = re.compile(r"^[\[\【\〖\『\《\［]([^\]\】\〗\』\》\］]{1,360})[\]\】\〗\』\》\］]$")
RE_SYSTEM_INLINE = re.compile(
    r"(?:[\[\【\〖\『\《\［\{])(?:Ding!|The\s+Pendragon\s+Codex|System|Notice|Warning|Announcement|Prompt|Quest|Stat|Skill|Level|Lv\.|Inventory|Reward).*?(?:[\]\】\〗\』\》\］\}])",
    re.I,
)

RE_QUOTE_SPAN = re.compile(r'("[^"]+"|\u201c[^\u201d]+\u201d)')
RE_INLINE_SINGLE_THOUGHT = re.compile(r"(?:^|(?<=\s))['\u2018]([^'\u2019]{3,180}?)['\u2019](?=\s|$|[.,!?])")
RE_MULTI_ASTERISK_SFX = re.compile(r"^\*[^*]{1,35}\*(?:\s+\*[^*]{1,35}\*)*$")
RE_STANDALONE_ONOMATOPOEIA = re.compile(
    r"^\*?(?:(?:b+o+m|kab+o+m|kr+ak+o+m|th+o+m|fwoom(?:[\s\u2014-]+fwoom)*|wh+o+m|bwho+m|bang|twang|shing|shaaa|beep|ring|ding|cr+ack|cl+ang|clink|scratch|shatter|thunk|thock|thud|crunch|pierce|dong|bong|chime|pop|poof|hiss|zap|z{2,}|gasp|r+o+a+r+|g+r+a+h+|shri+e+k|bwo+m|rumble|t-t)[!?.,\u2014\s*-]*)+\*?$",
    re.I,
)

SPEECH_VERBS = (
    r"said|replied|asked|whispered|murmured|shouted|yelled|screamed|muttered|"
    r"laughed|chuckled|sighed|groaned|growled|snarled|barked|snapped|hissed|"
    r"exclaimed|declared|announced|continued|added|answered|called|cried|"
    r"stammered|stuttered|pleaded|begged|teased|joked|mocked|sneered|scoffed|"
    r"pouted|breathed|gasped|whimpered|roared|bellowed|commanded|ordered|"
    r"conducted|enumerated|reminded|apologized|interrupted|blurted|retorted|"
    r"complained|explained|clarified|guessed|suggested|concluded|refused|"
    r"greeted|followed|defended|commented|tried|spoke|told|warned|cheered|"
    r"purred|drawled|wheezed|grumbled|observed|countered|advised|demanded|"
    r"vowed|proclaimed|crowed|interjected|rumbled|noted|reported|exhaled|echoed|finished"
)

ROLE_EPITHETS = (
    r"cadet|baker|baron|captain|sergeant|priest|bishop|archbishop|king|duke|queen|"
    r"navigatrix|admiral|smith|dwarf|elf|dryad|lynx|lamia|serpent|scout|knight|"
    r"warden|guard|woman|girl|man|boy|witch|envoy|fence|monarch|lord|lady"
)

RE_POST_QUOTE_SV = re.compile(
    rf"^[,.\s]*((?:[A-Z][a-zA-Z'-]+(?:\s+[A-Z][a-zA-Z'-]+)?|he|she|they|i|the\s+(?:[a-z-]+\s+){{0,3}}(?:{ROLE_EPITHETS}))"
    rf"(?:,\s*[^.!?]+?,|\s+[a-z]+ly|\s+suddenly|\s+quickly|\s+slowly|\s+also|\s+just|\s+quietly|\s+angrily|\s+shyly|\s+calmly|\s+grimly|\s+softly|\s+sharply|\s+warmly|\s+darkly|\s+smoothly|\s+hoarsely|\s+fiercely|\s+cleanly|\s+evenly|\s+dryly|\s+lightly)?"
    rf"\s+(?:{SPEECH_VERBS})\b[^.!?]*[.!?]?)",
    re.I,
)
RE_POST_QUOTE_VS = re.compile(
    rf"^[,.\s]*(?:{SPEECH_VERBS})\s+((?:[A-Z][a-zA-Z'-]+(?:\s+[A-Z][a-zA-Z'-]+)?|he|she|they|i|the\s+(?:[a-z-]+\s+){{0,3}}(?:{ROLE_EPITHETS})))\b",
    re.I,
)
RE_POST_QUOTE_INDIRECT = re.compile(
    r"^(?:(?:finally|then|after|ignoring|hearing|with|at)\s+)?"
    r"(?:(her|his|my)\s+(?:voice|words|complaint|plea|sweet\s+moans|question|reminder|tone|answer|reply|giggle|laughter|sigh)|"
    r"([A-Z][a-zA-Z'-]{2,20})'s\s+(?:voice|words|reminder|complaint|plea|question|reply|answer|tone))",
    re.I,
)
RE_NEXT_PARA_ACTOR = re.compile(
    r"^(?:Saying\s+[^,.]+,\s*|After\s+[^,.]+,\s*|With\s+[^,.]+,\s*)?"
    r"([A-Z][a-zA-Z'-]{2,20}(?:\s+[A-Z][a-zA-Z'-]{2,20})?)\b"
)
RE_NAMED_CHARACTER_LEAD = re.compile(
    r"^(?:[A-Z][^,.]{1,45},\s+)?"
    r"([A-Z][a-zA-Z'-]{2,20}(?:\s+[A-Z][a-zA-Z'-]{2,20})?)"
    r"(?:,\s*[^.!?]+?,|\s+(?:quickly|slowly|suddenly|finally|shyly|quietly|softly|gently|simply|just|also|then|angrily|happily|audibly))*\s+"
    r"(?:stood\s+up|spoke|said|replied|asked|answered|whispered|murmured|shouted|muttered|sighed|giggled|laughed|chuckled|"
    r"smiled|frowned|pouted|nodded|shrugged|greeted|complained|retorted|explained|turned(?:\s+towards?)?|looked|stared|landed|dashed|"
    r"took\s+a\s+deep\s+breath|leaned|stopped|blocked|chased|followed|called|added|continued|enumerated|announced|apologized)\b",
)
RE_PRE_QUOTE_TAG = re.compile(
    rf"((?:[A-Z][a-zA-Z'-]+(?:\s+[A-Z][a-zA-Z'-]+)?|he|she|they|i|the\s+(?:[a-z-]+\s+){{0,3}}(?:{ROLE_EPITHETS}))"
    rf"[^.!?]*?\b(?:{SPEECH_VERBS}|giggled|smiled|frowned|nodded|shrugged|turned(?:\s+towards?)?|stared|looked\s+at|took\s+a\s+deep\s+breath|leaned|stopped)\b[^.!?]*?[:,.]?)\s*$",
    re.I,
)
RE_THOUGHT_TAG = re.compile(
    r"\b(?:I|he|she)\s+(?:thought|wondered|pondered|mused|grumbled\s+internally|asked\s+(?:myself|himself|herself)|"
    r"swore\s+(?:in\s+my\s+heart|to\s+(?:myself|himself|herself))|was\s+thinking)\b",
    re.I,
)

RE_DETACHED_STUTTER = re.compile(r"\b([a-zA-Z])(?:\s+\1){1,4}\s+([a-zA-Z]{2,})\b", re.I)
RE_MULTI_HYPHEN_STUTTER = re.compile(r"\b([a-zA-Z])(?:-\1){1,4}-([a-zA-Z]{2,})\b", re.I)
RE_ELONGATION = re.compile(r"([a-zA-Z])\1{3,}")
RE_SPACED_ELONGATION = re.compile(r"\b([a-zA-Z]{1,3})\s+([a-zA-Z])(?:\s+\2){2,}\b", re.I)

NON_SPEAKER_PROPER_NOUNS = frozenset({
    "i", "me", "my", "mine", "myself", "he", "him", "his", "himself", "she", "her", "hers", "herself",
    "they", "them", "their", "theirs", "themselves", "we", "us", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "it", "its", "itself", "this", "that", "these", "those",
    "someone", "somebody", "everyone", "everybody", "anyone", "anybody", "nobody", "none", "both",
    "all", "some", "many", "few", "other", "others", "another", "each", "either", "neither",
    "the", "a", "an", "and", "but", "or", "for", "nor", "yet", "so", "if", "when", "while", "after",
    "before", "as", "then", "however", "therefore", "meanwhile", "suddenly", "finally", "still",
    "even", "although", "though", "because", "since", "until", "unless", "once", "here", "there",
    "what", "who", "whom", "whose", "which", "where", "why", "how", "yes", "no", "oh", "ah", "hey",
    "well", "now", "just", "only", "very", "too", "also", "not", "never", "always", "instead",
    "besides", "moreover", "otherwise", "unfortunately", "fortunately", "luckily", "thankfully",
    "actually", "apparently", "obviously", "probably", "simply", "quickly", "slowly", "quietly",
    "softly", "gently", "loudly", "reflexively", "involuntarily", "immediately", "instantly",
    "sometimes", "occasionally", "usually", "already", "almost", "nearly", "barely", "merely",
    "despite", "without", "within", "inside", "outside", "through", "across", "around", "between",
    "among", "behind", "beneath", "beside", "toward", "towards", "upon", "from", "into", "onto",
    "over", "under", "with", "about", "against", "during", "following", "including", "regarding",
    "again", "anyway", "anyways", "somehow", "honestly", "basically", "literally", "certainly",
    "clearly", "strangely", "weirdly", "next", "first", "second", "third", "last", "today",
    "tomorrow", "yesterday", "morning", "afternoon", "evening", "night", "later", "soon",
    "chapter", "act", "system", "void", "beast", "god", "tamer", "administrator", "skill", "quest",
    "level", "status", "warning", "alert", "notice", "ding", "damn", "holy", "black", "hole",
    "boulder", "done", "shoot", "stop", "remember", "wait", "fine", "true", "right", "sorry",
    "thanks", "thank", "please", "pardon", "ancient", "family", "families", "kingdom", "kraken",
    "krakens", "demon", "demons", "angel", "angels", "nephilim", "incubus", "devil", "space",
    "dark", "light", "forest", "town", "square", "park", "hotel", "room", "door", "clock", "hearing",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december", "christmas", "halloween", "patreon", "discord",
    "warden", "sky-beacon", "iron-heart", "camelot", "logres", "lothian", "cornwall", "avalon",
})

FEMALE_LEXICAL_CUES = re.compile(
    r"\b(?:she|her|hers|herself|lady|miss|madam|queen|princess|girl|woman|women|female|"
    r"sister|sisters|mother|mom|aunt|maiden|goddess|wife|fiancee|old\s+lady|young\s+miss|"
    r"dryad|lynx|lamia|serpent|navigatrix|baroness|dress|skirt|makeup|handbag|maid|actress|"
    r"slut|bitch|plump|mounds|underwear|blush(?:ed|ing)?|bosom|gown)\b",
    re.I,
)
MALE_LEXICAL_CUES = re.compile(
    r"\b(?:he|him|his|himself|lord|sir|mr|king|prince|boy|man|men|male|"
    r"brother|father|dad|uncle|youth|lad|husband|kid|bastard|son|boyfriend|nephew|"
    r"baron|duke|admiral|archbishop|bishop|priest|baker|cadet|sergeant|smith|dwarf|squire)\b",
    re.I,
)


# =====================================================================
# NLP REFINEMENT LAYER (ftfy, Punctuation, LanguageTool, VADER & NRCLex)
# =====================================================================

def refine_text_grammar_and_punctuation(text: str, line_type: str) -> str:
    if FTFY_AVAILABLE and ftfy is not None:
        try:
            text = ftfy.fix_text(text)
        except Exception:
            pass

    cleaned = " ".join(text.strip().split())
    if not cleaned:
        return ""

    words = cleaned.split()
    if len(words) >= 16 and not re.search(r"[.!?,;:]", cleaned):
        punct_model = _get_punct_model()
        if punct_model is not None:
            try:
                restored = punct_model.restore_punctuation(cleaned)
                if restored and len(restored.split()) == len(words):
                    cleaned = restored.strip()
            except Exception:
                pass

    if line_type in ("Narration", "System") and len(words) >= 4:
        lt = _get_language_tool()
        if lt is not None:
            try:
                corrected = lt.correct(cleaned)
                if corrected and abs(len(corrected) - len(cleaned)) <= max(12, int(len(cleaned) * 0.15)):
                    cleaned = corrected.strip()
            except Exception:
                pass

    return cleaned


def analyze_affect_vader_nrc(text: str) -> Dict[str, Any]:
    compound = 0.0
    vader = _get_vader()
    if vader is not None:
        try:
            scores = vader.polarity_scores(text)
            compound = float(scores.get("compound", 0.0))
        except Exception:
            pass

    nrc_scores: Dict[str, float] = {}
    top_nrc = ""
    if NRCLEX_AVAILABLE and NRCLex is not None:
        try:
            emo_obj = NRCLex(text)
            raw_freq = getattr(emo_obj, "raw_emotion_scores", {}) or {}
            specific = {
                k: float(v)
                for k, v in raw_freq.items()
                if k in ("fear", "anger", "anticipation", "trust", "surprise", "sadness", "disgust", "joy") and v > 0
            }
            nrc_scores = specific
            if specific:
                top_nrc = max(specific.items(), key=lambda kv: kv[1])[0]
        except Exception:
            pass

    return {
        "compound": compound,
        "top_nrc": top_nrc,
        "nrc_scores": nrc_scores,
    }

    # =====================================================================
# DYNAMIC CAST, REGISTRY LOCK & CROSS-PARAGRAPH SPEAKER TRACKER
# =====================================================================

RE_FEMALE_VOICE_INTRO = re.compile(
    r"\b(?:foreign\s+female\s+voice|familiar\s+female\s+voice|woman'?s\s+voice|"
    r"figure\s+of\s+a\s+woman|that\s+angel|the\s+angel|a\s+woman\s+with)\b",
    re.I,
)
RE_MALE_VOICE_INTRO = re.compile(
    r"\b(?:foreign\s+male\s+voice|familiar\s+male\s+voice|man'?s\s+voice|"
    r"deep\s+male\s+voice|booming\s+male\s+voice)\b",
    re.I,
)
RE_FIRST_PERSON_ACTION = re.compile(
    r"^(?:I|my\s+(?:voice|gaze|words|mind|question|heart|disappointment|eyes|hands|lips))\b",
    re.I,
)
RE_FEMALE_ACTION_LEAD = re.compile(
    r"^(?:She|Her\s+(?:eyes|face|expression|voice|words|lips|steps|hands|gaze|pupils|complaint|plea|sweet\s+moans|body))\b",
    re.I,
)
RE_MALE_ACTION_LEAD = re.compile(
    r"^(?:He|His\s+(?:eyes|face|expression|voice|words|lips|steps|hands|gaze))\b",
    re.I,
)
RE_INTIMATE_FEMALE_MOAN = re.compile(
    r"^(?:ah+n?[!~.\s]*|sh-?slow\s+down|n-?no[!,\s]+you\s+idiot|w-?what\?!?\s+t-?that'?s\s+outrageous)",
    re.I,
)


def _load_disk_character_registries() -> Dict[str, Any]:
    """Loads novel_entities_registry.json and session_entities_staged.json, preserving locked profiles."""
    merged: Dict[str, Any] = {}
    cwd = os.getcwd()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    for path in (
        os.path.join(cwd, "novel_entities_registry.json"),
        os.path.join(script_dir, "novel_entities_registry.json"),
    ):
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    for entry in data.values():
                        if isinstance(entry, dict) and isinstance(entry.get("characters"), dict):
                            for ck, cv in entry["characters"].items():
                                if isinstance(cv, dict):
                                    merged.setdefault(ck.strip().lower(), dict(cv))
            except Exception:
                pass

    for root_dir in {cwd, script_dir}:
        try:
            for item in os.listdir(root_dir):
                full_p = os.path.join(root_dir, item)
                staged_p = (
                    full_p
                    if item.startswith("session_entities_staged") and item.endswith(".json")
                    else os.path.join(full_p, "session_entities_staged.json")
                )
                if os.path.isfile(staged_p):
                    with open(staged_p, "r", encoding="utf-8") as sf:
                        sdata = json.load(sf)
                    if isinstance(sdata, dict) and isinstance(sdata.get("characters"), dict):
                        for ck, cv in sdata["characters"].items():
                            if isinstance(cv, dict):
                                merged[ck.strip().lower()] = dict(cv)
        except Exception:
            pass

    return merged


class FallbackCastTracker:
    """
    Single-source-of-truth cast manager that locks already-identified character profiles
    (gender, voice, pitch, aliases) from novel_entities_registry.json and
    session_entities_staged.json, preventing voice flips and ping-ponging.
    """

    def __init__(self, char_map: Optional[Dict[str, Any]] = None):
        self.registry: Dict[str, Dict[str, Any]] = {}
        self.alias_to_key: Dict[str, str] = {}
        self.locked_keys: set[str] = set()
        self._female_idx = 0
        self._male_idx = 0
        self.mc_key = "mc"
        self.mc_display = "Protagonist"
        self.mc_gender = "Male"
        self.mc_aliases: set[str] = {"mc", "protagonist", "i", "me"}

        self.last_active_speaker: Optional[str] = None
        self.last_female_speaker: Optional[str] = None
        self.last_male_speaker: Optional[str] = None
        self.recent_speakers: List[str] = []
        self.scene_solo_speaker: Optional[str] = None

        combined_map = _load_disk_character_registries()
        if char_map:
            for k, v in char_map.items():
                if isinstance(v, dict):
                    combined_map[k.strip().lower()] = dict(v)

        for k, meta in combined_map.items():
            if not isinstance(meta, dict):
                continue
            key_low = k.strip().lower()
            if key_low in NON_SPEAKER_PROPER_NOUNS and key_low not in ("mc", "narrator", "system"):
                continue

            disp = str(meta.get("display_name") or k.replace("_", " ").title()).strip()
            if disp.lower() in NON_SPEAKER_PROPER_NOUNS and key_low not in ("mc", "narrator", "system"):
                continue

            raw_gender = str(meta.get("gender") or "").strip().title()
            gender = raw_gender if raw_gender in ("Male", "Female", "Neutral") else self._infer_gender(disp, "")
            if key_low in ("narrator", "system"):
                gender = "Neutral"

            stored_voice = str(meta.get("voice") or "").strip()
            voice = stored_voice if stored_voice else self._enforce_gender_voice("", gender, key_low)

            aliases = [str(a).strip() for a in meta.get("aliases", []) if str(a).strip()]
            if disp and disp not in aliases:
                aliases.append(disp)
            clean_key_label = key_low.replace("_", " ").title()
            if clean_key_label.lower() not in [a.lower() for a in aliases]:
                aliases.append(clean_key_label)

            for _, group in KNOWN_ALIAS_GROUPS.items():
                if key_low in group or disp.lower() in group or any(a.lower() in group for a in aliases):
                    for g_alias in group:
                        if g_alias not in [a.lower() for a in aliases]:
                            aliases.append(g_alias.title())

            self.registry[key_low] = {
                "display_name": disp,
                "gender": gender,
                "voice": voice,
                "pitch": str(meta.get("pitch") or "+0Hz"),
                "age_category": str(meta.get("age_category") or "young").lower(),
                "aliases": aliases,
            }
            self.locked_keys.add(key_low)
            self.alias_to_key[key_low] = key_low
            self.alias_to_key[disp.lower()] = key_low
            for al in aliases:
                if al.lower() not in NON_SPEAKER_PROPER_NOUNS:
                    self.alias_to_key.setdefault(al.lower(), key_low)

        if "mc" in self.registry:
            self.mc_key = "mc"
            self.mc_display = self.registry["mc"]["display_name"]
            self.mc_gender = self.registry["mc"]["gender"]
            for al in self.registry["mc"].get("aliases", []):
                self.mc_aliases.add(al.lower())
            self.mc_aliases.add(self.mc_display.lower())
        else:
            for k, v in self.registry.items():
                if k not in ("narrator", "system"):
                    self.mc_key = k
                    self.mc_display = v["display_name"]
                    self.mc_gender = v["gender"]
                    self.mc_aliases.add(self.mc_display.lower())
                    break

    def _infer_gender(self, name: str, context_window: str = "", explicit_gender: str = "") -> str:
        low = name.strip().lower()
        first_tok = low.split()[0] if low.split() else ""
        last_tok = low.split()[-1] if low.split() else ""

        if explicit_gender in ("Male", "Female", "Neutral"):
            return explicit_gender
        if low in COMMON_FEMALE_NAMES or first_tok in COMMON_FEMALE_NAMES or last_tok in COMMON_FEMALE_NAMES:
            return "Female"
        if low in COMMON_MALE_NAMES or first_tok in COMMON_MALE_NAMES or last_tok in COMMON_MALE_NAMES:
            return "Male"

        if _GENDER_DETECTOR is not None and first_tok:
            try:
                guess = _GENDER_DETECTOR.get_gender(first_tok)
                if guess in ("female", "mostly_female"):
                    return "Female"
                if guess in ("male", "mostly_male"):
                    return "Male"
            except Exception:
                pass

        f_hits = len(FEMALE_LEXICAL_CUES.findall(f"{name} {context_window}"))
        m_hits = len(MALE_LEXICAL_CUES.findall(f"{name} {context_window}"))
        if any(t in low for t in ("lady", "miss", "madam", "sister", "queen", "princess", "mother", "aunt", "woman", "girl", "dryad", "lynx", "lamia", "navigatrix")):
            f_hits += 5
        if any(t in low for t in ("lord", "sir", "mr", "brother", "king", "prince", "father", "uncle", "man", "boy", "baron", "duke", "admiral", "archbishop", "captain")):
            m_hits += 5

        if f_hits > m_hits:
            return "Female"
        if m_hits > f_hits:
            return "Male"

        if len(first_tok) >= 4 and first_tok.endswith(("ia", "ina", "elle", "ette", "lyn", "lily", "rose")):
            return "Female"
        return "Male"

    def _next_voice_for_gender(self, gender: str, seed_name: str = "") -> str:
        pool = AUTHORIZED_FEMALE_VOICES if gender == "Female" else AUTHORIZED_MALE_VOICES
        if seed_name:
            h = int(hashlib.md5(seed_name.lower().encode("utf-8")).hexdigest()[:6], 16)
            return pool[h % len(pool)]
        if gender == "Female":
            v = pool[self._female_idx % len(pool)]
            self._female_idx += 1
            return v
        v = pool[self._male_idx % len(pool)]
        self._male_idx += 1
        return v

    def _enforce_gender_voice(self, voice: str, gender: str, seed_name: str = "") -> str:
        if gender == "Neutral":
            return "en-US-ChristopherNeural"
        if gender == "Female":
            if voice in FEMALE_VOICE_SET:
                return voice
            return self._next_voice_for_gender("Female", seed_name)
        if voice in MALE_VOICE_SET:
            return voice
        return self._next_voice_for_gender("Male", seed_name)

    def _lookup_locked_profile(self, name: str) -> Optional[Dict[str, Any]]:
        low = re.sub(r"[^a-zA-Z0-9\s'-]", "", name).strip().lower()
        if not low:
            return None
        key = self.alias_to_key.get(low)
        if key and key in self.registry:
            return self.registry[key]
        for _, group in KNOWN_ALIAS_GROUPS.items():
            if low in group:
                for g_alias in group:
                    k = self.alias_to_key.get(g_alias)
                    if k and k in self.registry:
                        self.alias_to_key[low] = k
                        return self.registry[k]
        return None

    def register_or_get(self, name: str, context_window: str = "", force_gender: str = "") -> Dict[str, Any]:
        existing = self._lookup_locked_profile(name)
        if existing is not None:
            return existing

        clean = re.sub(r"[^a-zA-Z0-9\s'-]", "", name).strip()
        if not clean:
            return self.get_mc()

        low = clean.lower()
        if low in self.mc_aliases or low in ("i", "me", "my", "myself", "mc", "protagonist"):
            return self.get_mc()

        if low in NON_SPEAKER_PROPER_NOUNS:
            if low in ("she", "her", "hers", "herself"):
                return self.get_active_female()
            if low in ("he", "him", "his", "himself"):
                return self.get_active_male()
            return self.get_mc()

        if RAPIDFUZZ_AVAILABLE and self.alias_to_key:
            match = process.extractOne(low, list(self.alias_to_key.keys()), scorer=fuzz.WRatio)
            if match and match[1] >= 88.0:
                return self.registry[self.alias_to_key[match[0]]]

        gender = force_gender if force_gender in ("Male", "Female") else self._infer_gender(clean, context_window)
        age_cat = "young"
        if any(t in low or t in context_window.lower() for t in ("old ", "elder", "grandma", "grandpa", "ancient", "archbishop")):
            age_cat = "elder"
        elif any(t in low or t in context_window.lower() for t in ("kid", "teen", "boy", "girl", "young", "cadet", "squire")):
            age_cat = "teen"

        voice = self._next_voice_for_gender(gender, clean)
        aliases = [clean]
        for _, group in KNOWN_ALIAS_GROUPS.items():
            if low in group:
                aliases.extend([g.title() for g in group if g != low])

        meta = {
            "display_name": clean.title() if clean.islower() else clean,
            "gender": gender,
            "voice": voice,
            "pitch": "+0Hz",
            "age_category": age_cat,
            "aliases": aliases,
        }
        self.registry[low] = meta
        self.locked_keys.add(low)
        for al in aliases:
            if al.lower() not in NON_SPEAKER_PROPER_NOUNS:
                self.alias_to_key.setdefault(al.lower(), low)
        return meta

    def get_mc(self) -> Dict[str, Any]:
        if self.mc_key in self.registry:
            return self.registry[self.mc_key]
        fallback_mc = FALLBACK_BASE_CHARACTERS.get("mc", {})
        return {
            "display_name": fallback_mc.get("display_name", self.mc_display),
            "gender": fallback_mc.get("gender", self.mc_gender),
            "voice": fallback_mc.get("voice", "en-US-GuyNeural"),
            "pitch": fallback_mc.get("pitch", "+0Hz"),
            "age_category": "young",
            "aliases": [self.mc_display],
        }

    def get_active_female(self, preferred_label: str = "Mysterious Woman") -> Dict[str, Any]:
        if self.last_female_speaker:
            locked = self._lookup_locked_profile(self.last_female_speaker)
            if locked and locked["gender"] == "Female":
                return locked
        for sp_name in reversed(self.recent_speakers):
            locked = self._lookup_locked_profile(sp_name)
            if locked and locked["gender"] == "Female":
                return locked
        for meta in self.registry.values():
            if meta["gender"] == "Female":
                return meta
        return self.register_or_get(preferred_label, "she her woman female", force_gender="Female")

    def get_active_male(self) -> Dict[str, Any]:
        if self.last_male_speaker:
            locked = self._lookup_locked_profile(self.last_male_speaker)
            if locked and locked["gender"] == "Male":
                return locked
        return self.get_mc()

    def reset_scene(self, upcoming_text: str = "") -> None:
        self.recent_speakers.clear()
        self.last_active_speaker = None
        self.scene_solo_speaker = None

        if upcoming_text and not re.search(r"\b(I|me|my|myself)\b", upcoming_text[:350]):
            for alias_low, key_low in sorted(self.alias_to_key.items(), key=lambda x: -len(x[0])):
                if len(alias_low) >= 3 and key_low not in (self.mc_key, "narrator", "system"):
                    if re.search(rf"\b{re.escape(alias_low)}\b", upcoming_text[:200], re.I):
                        meta = self.registry[key_low]
                        self.scene_solo_speaker = meta["display_name"]
                        self._record_turn(meta["display_name"])
                        break

    def note_narration_context(self, narr_text: str) -> None:
        if not narr_text:
            return

        if self.scene_solo_speaker and re.search(r"\b(I|me|my|myself)\b", narr_text):
            self.scene_solo_speaker = None

        if RE_FEMALE_VOICE_INTRO.search(narr_text):
            label = "Angel" if "angel" in narr_text.lower() or "wings" in narr_text.lower() else "Mysterious Woman"
            f_meta = self.register_or_get(label, narr_text, force_gender="Female")
            self.last_female_speaker = f_meta["display_name"]
            self._record_turn(f_meta["display_name"])

        if RE_MALE_VOICE_INTRO.search(narr_text):
            m_meta = self.register_or_get("Mysterious Man", narr_text, force_gender="Male")
            self.last_male_speaker = m_meta["display_name"]

        for alias_low, key_low in sorted(self.alias_to_key.items(), key=lambda x: -len(x[0])):
            if len(alias_low) >= 3 and key_low not in (self.mc_key, "narrator", "system"):
                if re.search(rf"\b{re.escape(alias_low)}\b", narr_text, re.I):
                    meta = self.registry[key_low]
                    if meta["gender"] == "Female":
                        self.last_female_speaker = meta["display_name"]
                    elif meta["gender"] == "Male":
                        self.last_male_speaker = meta["display_name"]

    def pre_scan_chapter_entities(self, text: str) -> None:
        # 1. Discover first-person narrator names/aliases
        mc_patterns = [
            re.compile(r"\b(?:my\s+name\s+is|call\s+me|I\s+am|I'm)\s+([A-Z][a-zA-Z]{2,18})\b"),
            re.compile(r"\bcalled\s+me\s+[A-Z][a-zA-Z]+,\s*not\s+([A-Z][a-zA-Z]{2,18})(?:\s+or\s+([A-Z][a-zA-Z]{2,18}))?\b"),
            re.compile(r'"([A-Z][a-zA-Z]{2,18})\s+[A-Z][a-zA-Z]{2,18},\s*I\'m\b'),
        ]
        for pat in mc_patterns:
            for m in pat.finditer(text):
                for grp in m.groups():
                    if grp and grp.lower() not in NON_SPEAKER_PROPER_NOUNS and self._lookup_locked_profile(grp) is None:
                        if self.mc_display == "Protagonist":
                            self.mc_display = grp
                            if self.mc_key in self.registry:
                                self.registry[self.mc_key]["display_name"] = grp
                        self.mc_aliases.add(grp.lower())
                        self.alias_to_key.setdefault(grp.lower(), self.mc_key)

        # 2. Optional spaCy PERSON NER pass
        if _NLP is not None:
            try:
                doc = _NLP(text[:28000])
                for ent in doc.ents:
                    if ent.label_ == "PERSON":
                        ent_name = ent.text.strip()
                        first_w = ent_name.split()[0].lower() if ent_name.split() else ""
                        if 2 <= len(ent_name) <= 28 and ent_name.lower() not in NON_SPEAKER_PROPER_NOUNS and first_w not in NON_SPEAKER_PROPER_NOUNS:
                            start = max(0, ent.start_char - 140)
                            end = min(len(text), ent.end_char + 140)
                            self.register_or_get(ent_name, text[start:end])
            except Exception:
                pass

        # 3. Deterministic SV + VS speech-tag character discovery with NLTK POS-tag guard
        sv_pat = re.compile(
            rf"\b([A-Z][a-zA-Z'-]{{2,20}}(?:\s+[A-Z][a-zA-Z'-]{{2,20}})?)\b[^.!?]{{0,45}}\b(?:{SPEECH_VERBS})\b",
        )
        vs_pat = re.compile(
            rf"\b(?:{SPEECH_VERBS})\s+([A-Z][a-zA-Z'-]{{2,20}})\b",
        )
        for pat in (sv_pat, vs_pat):
            for m in pat.finditer(text):
                cand = m.group(1).strip()
                first_w = cand.split()[0].lower()
                if cand.lower() in NON_SPEAKER_PROPER_NOUNS or first_w in NON_SPEAKER_PROPER_NOUNS:
                    continue
                # Verify via NLTK POS tagger that capitalized token isn't an adjective/adverb/verb
                pos_tags = _nltk_pos_tag_words(["He", "saw", cand.split()[0], "today"])
                if pos_tags and pos_tags[2][1] in ("JJ", "RB", "VBG", "VBN", "IN", "DT"):
                    continue
                start = max(0, m.start() - 140)
                end = min(len(text), m.end() + 140)
                self.register_or_get(cand, text[start:end])

    def _match_signature_address(self, quote_text: str) -> Optional[Dict[str, Any]]:
        q_low = quote_text.lower().strip()
        if re.match(r"^master\b", q_low):
            locked = self._lookup_locked_profile("ember")
            if locked:
                return locked
        if re.match(r"^leader\b", q_low):
            for k in ("fang", "fong"):
                locked = self._lookup_locked_profile(k)
                if locked:
                    return locked
        if "old lady" in q_low or re.search(r",\s*kid[.!?]?$", q_low):
            locked = self._lookup_locked_profile("fatima")
            if locked:
                return locked
        if re.search(r"\b(?:brother\b|nice\s+try,\s*brother)", q_low):
            locked = self._lookup_locked_profile("celia")
            if locked:
                return locked
        if "his highness" in q_low:
            return self.get_active_female()
        if any(p in q_low for p in ("i'm your aunt", "my sister's son", "my nephew", "morning, handsome")):
            return self.get_active_female()
        if RE_INTIMATE_FEMALE_MOAN.match(q_low):
            return self.get_active_female()
        return None

    def _extract_subject_from_tag(self, tag_clause: str, wide_context: str) -> Optional[Dict[str, Any]]:
        clean_tag = tag_clause.strip()
        low_tag = clean_tag.lower()

        if re.match(r"^i\b", low_tag):
            return self.get_mc()

        for alias_low, key_low in sorted(self.alias_to_key.items(), key=lambda x: -len(x[0])):
            if len(alias_low) >= 3 and re.search(rf"\b{re.escape(alias_low)}\b", low_tag):
                return self.registry[key_low]

        if re.match(r"^(?:she|her)\b", low_tag) or re.search(r"\b(?:the\s+woman|the\s+girl|the\s+angel|dryad|lynx|lamia|navigatrix|witch)\b", low_tag):
            return self.get_active_female()
        if re.match(r"^(?:he|his)\b", low_tag) or re.search(r"\b(?:the\s+man|the\s+boy|cadet|baker|baron|captain|sergeant|priest|archbishop|king|duke|admiral|smith|dwarf|knight|guard)\b", low_tag):
            # Register descriptive male epithet if no specific male speaker is active
            epithet_m = re.search(rf"\b(the\s+(?:[a-z-]+\s+){{0,3}}(?:{ROLE_EPITHETS}))\b", low_tag)
            if epithet_m:
                return self.register_or_get(epithet_m.group(1), wide_context, force_gender="Male")
            return self.get_active_male()

        cap_m = re.match(r"^([A-Z][a-zA-Z'-]{2,20}(?:\s+[A-Z][a-zA-Z'-]{2,20})?)\b", clean_tag)
        if cap_m:
            cand = cap_m.group(1).strip()
            first_w = cand.split()[0].lower()
            if cand.lower() not in NON_SPEAKER_PROPER_NOUNS and first_w not in NON_SPEAKER_PROPER_NOUNS:
                return self.register_or_get(cand, wide_context)

        return None

    def _extract_post_speaker(self, text_after: str, wide_ctx: str) -> Optional[Dict[str, Any]]:
        s = text_after.strip()
        if not s:
            return None

        if re.match(
            r"^(?:(?:even\s+)?before\s+I\s+(?:completed|finished)|at\s+my\s+question|upon\s+my\s+words|"
            r"my\s+(?:voice|words|disappointment)\b|seeing\s+a\s+stray\s+boulder.*I\s+warned)",
            s,
            re.I,
        ):
            return self.get_mc()

        vs_m = RE_POST_QUOTE_VS.match(s)
        if vs_m:
            subj = self._extract_subject_from_tag(vs_m.group(1), wide_ctx)
            if subj:
                return subj

        sv_m = RE_POST_QUOTE_SV.match(s)
        if sv_m:
            subj = self._extract_subject_from_tag(sv_m.group(1), wide_ctx)
            if subj:
                return subj

        act_m = RE_NAMED_CHARACTER_LEAD.match(s)
        if act_m:
            cand = act_m.group(1).strip()
            if cand.lower() not in NON_SPEAKER_PROPER_NOUNS:
                return self.register_or_get(cand, wide_ctx)

        ind_m = RE_POST_QUOTE_INDIRECT.match(s)
        if ind_m:
            pron = (ind_m.group(1) or "").lower()
            named = (ind_m.group(2) or "").strip()
            if named and named.lower() not in NON_SPEAKER_PROPER_NOUNS:
                return self.register_or_get(named, wide_ctx)
            if pron == "her":
                return self.get_active_female()
            if pron == "his":
                return self.get_active_male()
            if pron == "my":
                return self.get_mc()

        if re.match(r"^(?:when\s+she\s+said|as\s+she\s+spoke|this\s+time\s+her\s+voice|that\s+voice\s+came|the\s+woman'?s\s+voice)", s, re.I):
            return self.get_active_female()
        if re.match(r"^as\s+I\s+(?:was\s+staring|gave\s+the\s+signal|reflect\s+on\s+myself|quickly\s+conducted)", s, re.I):
            called_m = re.search(rf",\s*([A-Z][a-zA-Z'-]{{2,20}})\s+(?:{SPEECH_VERBS})\b", s)
            if called_m and called_m.group(1).lower() not in NON_SPEAKER_PROPER_NOUNS:
                return self.register_or_get(called_m.group(1), wide_ctx)
            return self.get_mc()

        return None

    def _extract_pre_speaker(self, text_before: str, wide_ctx: str) -> Optional[Dict[str, Any]]:
        s = text_before.strip()
        if not s:
            return None

        sents = _nltk_split_sentences(s) or re.split(r"(?<=[.!?])\s+", s)
        last_sent = sents[-1].strip() if sents else s

        pre_m = RE_PRE_QUOTE_TAG.search(last_sent)
        if pre_m:
            subj = self._extract_subject_from_tag(pre_m.group(1), wide_ctx)
            if subj:
                return subj

        act_m = RE_NAMED_CHARACTER_LEAD.search(last_sent)
        if act_m:
            cand = act_m.group(1).strip()
            if cand.lower() not in NON_SPEAKER_PROPER_NOUNS:
                return self.register_or_get(cand, wide_ctx)

        if RE_FEMALE_ACTION_LEAD.match(last_sent):
            return self.get_active_female()
        if RE_MALE_ACTION_LEAD.match(last_sent):
            return self.get_active_male()
        if RE_FIRST_PERSON_ACTION.match(last_sent) and not re.search(r"\b(?:she|her)\b", last_sent[-35:], re.I):
            return self.get_mc()

        return None

    def resolve_dialogue_speaker(
        self,
        quote_text: str,
        pre_context: str,
        post_context: str,
        prev_para_text: str = "",
        next_para_text: str = "",
        next2_para_text: str = "",
    ) -> Dict[str, Any]:
        wide_ctx = f"{prev_para_text[-140:]} {pre_context} {post_context} {next_para_text[:140]} {next2_para_text[:120]}"

        # 1. Same-paragraph post-quote attribution
        if post_context.strip():
            sp = self._extract_post_speaker(post_context, wide_ctx)
            if sp:
                self._record_turn(sp["display_name"])
                return sp

        # 2. Same-paragraph pre-quote attribution
        if pre_context.strip():
            sp = self._extract_pre_speaker(pre_context, wide_ctx)
            if sp:
                self._record_turn(sp["display_name"])
                return sp

        # 3. Cross-paragraph NEXT-paragraph attribution (skips standalone *SFX* / *ROAR!* lines)
        if not post_context.strip():
            for cand_next in (next_para_text.strip(), next2_para_text.strip()):
                if not cand_next:
                    continue
                if RE_MULTI_ASTERISK_SFX.match(cand_next) or RE_STANDALONE_ONOMATOPOEIA.fullmatch(cand_next):
                    continue
                if not cand_next.startswith(('"', "\u201c")):
                    sp = self._extract_post_speaker(cand_next, wide_ctx)
                    if sp:
                        self._record_turn(sp["display_name"])
                        return sp
                    if not re.match(r"^(?:I|We|My)\b", cand_next, re.I):
                        lead_actor_m = RE_NEXT_PARA_ACTOR.match(cand_next)
                        if lead_actor_m:
                            cand = lead_actor_m.group(1).strip()
                            first_w = cand.split()[0].lower()
                            if cand.lower() not in NON_SPEAKER_PROPER_NOUNS and first_w not in NON_SPEAKER_PROPER_NOUNS:
                                locked = self._lookup_locked_profile(cand)
                                if locked:
                                    self._record_turn(locked["display_name"])
                                    return locked
                break

        # 4. Character-signature address & female intimate moans
        sig_meta = self._match_signature_address(quote_text)
        if sig_meta:
            self._record_turn(sig_meta["display_name"])
            return sig_meta

        # 5. 3rd-person solo scene lock
        if self.scene_solo_speaker:
            locked = self._lookup_locked_profile(self.scene_solo_speaker)
            if locked:
                self._record_turn(locked["display_name"])
                return locked

        # 6. Cross-paragraph PREVIOUS-paragraph lead-in
        if not pre_context.strip() and prev_para_text.strip() and not prev_para_text.strip().endswith(('"', "\u201d")):
            sp = self._extract_pre_speaker(prev_para_text, wide_ctx)
            if sp:
                self._record_turn(sp["display_name"])
                return sp

        # 7. Vocative inside the quote
        voc_m = re.search(r"(?:^|[,\s]+)([A-Z][a-zA-Z]{2,18})(?:[?!.,]|$)", quote_text.strip())
        if voc_m:
            addressed = voc_m.group(1).lower()
            if addressed in self.mc_aliases or addressed in ("will", "ethan", "damian", "erebus", "aedan", "devlin"):
                f_meta = self.get_active_female()
                self._record_turn(f_meta["display_name"])
                return f_meta
            addressed_locked = self._lookup_locked_profile(addressed)
            if addressed_locked and addressed.lower() not in self.mc_aliases:
                if prev_para_text:
                    prev_sents = _nltk_split_sentences(prev_para_text.strip()) or re.split(r"(?<=[.!?])\s+", prev_para_text.strip())
                    prev_actor_m = RE_NAMED_CHARACTER_LEAD.search(prev_sents[-1])
                    if prev_actor_m:
                        actor_locked = self._lookup_locked_profile(prev_actor_m.group(1))
                        if actor_locked and actor_locked["display_name"].lower() != addressed:
                            self._record_turn(actor_locked["display_name"])
                            return actor_locked
                if addressed_locked["gender"] == "Female" and (
                    self.last_active_speaker == self.mc_display
                    or re.search(r"\b(?:I|me|my)\b", prev_para_text[-120:])
                ):
                    mc = self.get_mc()
                    self._record_turn(mc["display_name"])
                    return mc

        # 8. Maintain current active speaker instead of ping-ponging back to a prior speaker
        if self.last_active_speaker:
            curr_locked = self._lookup_locked_profile(self.last_active_speaker)
            if curr_locked:
                return curr_locked

        # 9. Default fallback
        mc = self.get_mc()
        self._record_turn(mc["display_name"])
        return mc

    def _record_turn(self, speaker_name: str) -> None:
        self.last_active_speaker = speaker_name
        locked = self._lookup_locked_profile(speaker_name)
        if locked:
            g = locked["gender"]
            if g == "Female":
                self.last_female_speaker = locked["display_name"]
            elif g == "Male" and locked["display_name"].lower() not in self.mc_aliases:
                self.last_male_speaker = locked["display_name"]

        if not self.recent_speakers or self.recent_speakers[-1] != speaker_name:
            self.recent_speakers.append(speaker_name)
            if len(self.recent_speakers) > 6:
                self.recent_speakers.pop(0)


# =====================================================================
# DUAL-TEXT & ANTICIPATORY PROSODY SCULPTOR (CORE DIRECTIVE 1 & 3)
# =====================================================================

def normalize_repetitive_phonetics(text: str) -> str:
    text = RE_DETACHED_STUTTER.sub(lambda m: f"{m.group(1)}-{m.group(2).lower()}", text)
    text = RE_MULTI_HYPHEN_STUTTER.sub(lambda m: f"{m.group(1)}-{m.group(2).lower()}", text)
    text = RE_SPACED_ELONGATION.sub(lambda m: f"{m.group(1)}{m.group(2).lower() * 2}...", text)
    text = RE_ELONGATION.sub(lambda m: m.group(1) * 3, text)
    return text


def build_dual_texts(raw_segment: str, line_type: str, pitch_tier: str) -> Tuple[str, str]:
    clean = refine_text_grammar_and_punctuation(raw_segment, line_type)
    if not clean:
        return "", ""

    clean = re.sub(r"^[.,;:\s]+(?=[A-Za-z0-9\"'\[\(])", "", clean).strip()
    if not clean:
        return "", ""

    clean = re.sub(r"\.{2}([!?])", r"...\1", clean)

    if not re.search(r'[.!?…]["\']?$', clean):
        clean += "."

    if line_type == "Narration" and clean.endswith("...") and pitch_tier in (
        "narrator_anchor", "neutral_statement", "conversational_mid"
    ):
        clean = clean[:-3].rstrip() + "."

    display_text = clean
    tts_text = clean

    tts_text = re.sub(r"\[([^\]]+)\]", r"\1", tts_text)
    tts_text = tts_text.replace("~", "")
    tts_text = re.sub(r"-{2,}", " ... ", tts_text)
    tts_text = re.sub(r"[\u2014\u2013]", " ... ", tts_text)
    tts_text = re.sub(r"\s+-\s+", " ... ", tts_text)
    tts_text = normalize_repetitive_phonetics(tts_text)

    tts_text = apply_pronunciation_lexicon(tts_text)
    tts_text = apply_fast_phonetic_rules(tts_text)

    if line_type in ("Narration", "Dialogue") and "..." not in tts_text:
        tts_text = re.sub(
            r"\b(and\s+found\s+it|realized\s+that|actually|unless|that\s+includes)\s+([a-zA-Z0-9'\"-]+[.!?])$",
            r"\1... \2",
            tts_text,
            count=1,
            flags=re.I,
        )

    tts_text = re.sub(r"\s{2,}", " ", tts_text).strip()
    if not re.search(r'[.!?…]["\']?$', tts_text):
        tts_text += "."

    return display_text, tts_text


# =====================================================================
# 21-TIER SOLFÈGE PITCH MATRIX & AFFECT REFINER (CORE DIRECTIVE 3)
# =====================================================================

def classify_solfege_pitch_tier(
    text: str,
    line_type: str,
    is_paragraph_start: bool,
    bgm_mood: str,
    speaker_meta: Dict[str, Any],
    affect: Dict[str, Any],
) -> Tuple[str, str, bool]:
    low = text.lower()
    age = speaker_meta.get("age_category", "young")
    compound = affect.get("compound", 0.0)
    top_nrc = affect.get("top_nrc", "")
    nrc_scores = affect.get("nrc_scores", {})

    if line_type == "System":
        if any(w in low for w in ("warning", "danger", "alert", "critical", "error", "fatality", "cancelled", "intrusion", "tamper", "breach")) or top_nrc == "fear":
            return "urgent_command", "urgent", False
        return "neutral_statement", "neutral", False

    if line_type == "Narration":
        if is_paragraph_start:
            return "lung_reset_entry", "engaged", True
        if bgm_mood == "dread" or any(w in low for w in ("eldritch", "abyss", "void beast", "horror", "corpse", "blood", "nothingness", "miasma")):
            return "grave_somber", "fearful", False
        if bgm_mood == "sorrow" or any(w in low for w in ("tears", "crying", "died", "sacrific", "grief", "mourn", "fallen comrades", "sobs", "broken heart")):
            return "subdued_mournful", "solemn", False
        if any(w in low for w in ("kiss", "moans", "panting", "pounded", "pounding", "thrusts", "climax", "embrace", "underwear", "slipped")):
            return "intimate_whisper", "romantic", False
        if bgm_mood == "combat" or any(w in low for w in ("exploded", "charged", "slashed", "roared", "shockwave", "clashed", "pulverized", "detonated")):
            return "tense_strained", "urgent", False
        if bgm_mood == "tension" or any(w in low for w in ("heart", "breath", "quietly", "crept", "shadow", "watching", "trembled")):
            return "engaged_alert", "tense", False
        if any(w in low for w in ("thought", "wondered", "noticed", "realized", "memory", "recalled")):
            return "thoughtful_drawl", "thoughtful", False
        if compound <= -0.55 or top_nrc == "sadness":
            return "subdued_mournful", "solemn", False
        if top_nrc in ("fear", "anticipation"):
            return "engaged_alert", "tense", False
        return "narrator_anchor", "neutral", False

    if "!" in text and any(w in low for w in ("die", "kill", "bastard", "idiot", "dare", "stop", "impossible", "no!", "b**ch", "bch", "no. you. don't", "fire!", "ignite", "charge")):
        if text.isupper() or "!!!" in text:
            return "hysterical_peak", "angry", False
        return "defiant_shout", "angry", False

    if any(w in low for w in ("help", "run!", "watch out", "look out", "dodge", "hurry", "quick!", "incoming", "shoot!", "go, now", "wait!", "hold the line", "clear the")):
        return "urgent_command", "fearful", False

    if re.search(r"\b(?:y-you|n-no|w-what|t-that|w-we|i-i|sh-slow|b-briar)\b", low) or ("?!" in text) or (
        nrc_scores.get("surprise", 0) >= 1 and nrc_scores.get("fear", 0) >= 1
    ):
        return "alarmed_spike", "fearful", False

    if any(w in low for w in ("whisper", "secret", "quietly", "kiss", "blush", "love", "forgive me", "ahh", "ahn", "turn~", "forget about me", "husband")):
        return "intimate_whisper", "romantic", False

    if any(w in low for w in ("sorry", "died", "sacrific", "tears", "comrades", "foolish", "sad", "hurt", "can't", "failed")) or (
        top_nrc == "sadness" and compound <= -0.35
    ):
        return "subdued_mournful", "solemn", False

    if any(w in low for w in ("kill you", "crush you", "regret", "prey", "pathetic", "kneel", "butcher", "flay")) or (
        top_nrc in ("anger", "disgust") and compound <= -0.45
    ):
        return "menacing_growl", "angry", False

    if age == "elder" or any(w in low for w in ("decree", "order", "silenced", "obey", "council", "laws and rules", "hearken", "witness")):
        return "authoritative_low", "solemn", False

    if text.strip().endswith("?"):
        return "inquisitive_tilt", "curious", False

    if (
        any(w in low for w in ("haha", "hehe", "joked", "thanks", "great", "congratulations", "welcome", "kid", "old lady", "good work", "morning", "bravo", "hah!"))
        or (compound >= 0.45 and top_nrc in ("joy", "trust"))
    ):
        return "buoyant_lift", "playful", False

    if bgm_mood in ("combat", "tension") or top_nrc in ("fear", "anticipation"):
        return "tense_strained", "tense", False

    return "conversational_mid", "neutral", False


def compute_segment_rate(line_type: str, pitch_tier: str) -> str:
    if line_type == "System":
        return "+2%"
    if line_type == "Dialogue":
        if pitch_tier in ("grim_rumble", "menacing_growl", "grave_somber", "abyssal_floor"):
            return "-5%"
        return "-4%"
    return "+0%"

# =====================================================================
# CONTEXT-AWARE SFX ENGINE (100% Parity + Metaphor Guards)
# =====================================================================

def detect_literal_sfx(text: str, line_type: str, bgm_mood: str, speaker_gender: str) -> str:
    """Matches all 74 authorized SFX keys with strict metaphor and false-positive guards."""
    t_low = text.lower()
    is_brief = len(text.split()) < 24

    if re.search(r"\b(gasp|gasps|gasped|sharp\s+intake\s+of\s+breath)\b", t_low) and is_brief:
        return "gasp"
    if re.search(r"\b(badump|ba\s+dump|thump-thump|heart\s+(?:is\s+)?thunder(?:ed|ing)|heartbeat\s+starts|pounding\s+heart)\b", t_low) and is_brief:
        return "heartbeat"
    if re.search(r"\b(sigh(?:ed|s|ing)?\s+(?:in\s+relief|audibly)|soft\s+sigh|audibly\s+sighed|let\s+out\s+a\s+(?:long\s+)?sigh|weary\s+exhale)\b", t_low) and is_brief:
        return "sigh"

    if re.search(r"\b(gunshot|shot\s+rang|fired\s+(?:his|her|a|the)\s+(?:gun|revolver|pistol|rifle|shotgun|sniper)|shot\s+both\s+her\s+pistols|pulled\s+the\s+trigger)\b", t_low):
        return "gunshot"
    if re.search(r"\b(grenade\s+exploded|bomb\s+went\s+off|detonated|violent\s+explosion|exploded\s+into\s+shards|atomic\s+bomb|erupted\s+upward\s+in\s+roaring|fire-?pitch\s+met)\b", t_low):
        if not re.search(r"\b(temper|rage|anger|fury|laughter|burst\s+out)\b", t_low):
            return "explosion"
    if line_type != "Dialogue" and re.search(
        r"\b(drew|drawn|unsheathed?|pulled\s+out\s+(?:his|her|their)\s+(?:sword|blade|dagger|caliper))\b", t_low
    ):
        return "blade"
    if line_type != "Dialogue" and re.search(r"\b(blade\s+sliced|sword\s+severed|slashed\s+across|cleaved\s+through|clove\s+cleanly)\b", t_low):
        return "slash"
    if re.search(r"\b(hammer\s+slammed|blunt\s+collision|crashed\s+into\s+the\s+(?:wall|ground|shield)|landed\s+a\s+clean\s+punch|pulverized\s+the\s+boulder|slammed\s+square\s+into)\b", t_low):
        return "impact"
    if re.search(r"\b(stomp|stomps|stomping|body\s+collapsed|collapsed\s+lifelessly|slammed\s+onto\s+the\s+ground|fell\s+to\s+(?:his|her)\s+knees|slumped\s+heavily)\b", t_low):
        if not re.search(r"\b(stopped|clenched\s+(?:his|her|their)\s+fists?)\b", t_low):
            return "thud"
    if re.search(r"\b(armor|plate|chainmail|cuirass|greaves?|gauntlets?|pauldron)\b", t_low) and re.search(
        r"\b(clank|clanked|rattled|shifted|donned|unbuckled)\b", t_low
    ):
        return "armor"
    if line_type != "Dialogue" and is_brief and re.search(
        r"\b(groaned\s+in\s+agony|sharp\s+gasp\s+of\s+pain|clutched\s+(?:his|her)\s+bleeding\s+wound|shattering\s+my\s+right\s+shoulder)\b", t_low
    ):
        if not re.search(r"\b(illness|disease|cryosis|sickness|fever)\b", t_low):
            return "pain"
    if re.search(r"\b(beast\s+roared|monster\s+roared|screeched\s+violently|deafening\s+roar|loud\s+roar\s+echoed|agonized\s+cry|dragon-roar|leonine\s+roar)\b", t_low):
        return "monster"
    if re.search(r"\b(low\s+snarl|snarled\s+menacingly|growled\s+with\s+bared\s+fangs|lupine\s+betrayal)\b", t_low):
        return "snarl"
    if re.search(r"\b(war\s+drums?\s+beat|marching\s+drums?\s+echoed|assault-drums|war-horns?)\b", t_low):
        return "wardrum"

    if re.search(r"\b(sprint(?:s|ed|ing)?|dashes\s+forward|dashed\s+forward|fled\s+at\s+top\s+speed|charging\s+forward|ran\s+at\s+the\s+fastest\s+speed)\b", t_low):
        if not re.search(r"\b(tears?\s+running|running\s+down\s+(?:her|his|their)\s+cheeks?)\b", t_low):
            return "run"
    if re.search(r"\b(paced\s+(?:toward|across|around)|rushed\s+(?:in|into|out\s+of)\s+the\s+room|walked\s+into\s+the\s+(?:room|hall|study|chamber|cave|tunnel)|strode\s+onto\s+the\s+stairs|spiral\s+stair)\b", t_low):
        return "steps_indoor"
    if re.search(r"\b(walked\s+down\s+the|stepped\s+across\s+the\s+courtyard|traveled\s+along\s+the\s+(?:road|path|trail)|strolling\s+in\s+a\s+park|steps\s+on\s+.*street|marching\s+boots)\b", t_low):
        return "footsteps"
    if re.search(r"\b(tiptoe(?:d|s|ing)?|sneak(?:s|ed|ing)?|creeping|cautious\s+steps?|light\s+footing)\b", t_low):
        return "tiptoe"
    if re.search(r"\b(tiny\s+paws|cat\s+padded|paws\s+pattered|claws\s+scuttled|scurrying\s+steps?|bare\s+feet\s+padded)\b", t_low):
        return "patter"
    if re.search(r"\b(ground\s+shook\s+with\s+(?:each|every)\s+step|colossus\s+marched|giant\s+stomped|behemoth\s+strode|forty-foot\s+titan|twenty-foot\s+strides)\b", t_low):
        return "heavy_steps"
    if re.search(r"\b(carriage\s+rolled|wheels?\s+rattled|wagon\s+approached|horses?\s+trotted|hoofbeats)\b", t_low):
        return "horseandcart"
    if re.search(r"\b(car\s+(?:engine|sped|drove)|engine\s+roared\s+to\s+life|vehicle\s+rolled|drove\s+us\s+back)\b", t_low):
        return "car"
    if re.search(r"\b(tires?\s+screeched|screeching\s+tires?|braked\s+violently|skidded\s+to\s+a\s+halt|friction-shoes)\b", t_low):
        return "screech"
    if re.search(r"\b(steam\s+engine|locomotive|train\s+whistle|chugged\s+along\s+the\s+tracks|steam-whistle|iron-heart\s+one)\b", t_low):
        return "steam_engine"
    if re.search(r"\b(dog\s+barked|barked\s+loudly|canine\s+yelp|hounds?\s+.*baying)\b", t_low):
        return "bark"

    if re.search(r"\b(slammed\s+(?:the\s+)?door|slammed\s+shut|iron\s+grate\s+slammed|portcullises\s+slamming)\b", t_low):
        return "slam"
    if re.search(r"\b(doors?\s+creak(?:ed|s|ing)?|hinges?\s+groaned|creaked\s+open|groaned\s+silently\s+open)\b", t_low):
        return "creak"
    if re.search(r"\b(knocked\s+on\s+the\s+door|rapped\s+on\s+the\s+wood|iron\s+knocker\s+boomed)\b", t_low):
        return "knock"
    if re.search(r"\b(window\s+shattered|glass\s+shattered|vial\s+smashed|potion\s+bottle\s+shattered|made\s+of\s+glass|shattering\s+into\s+frozen\s+mud)\b", t_low):
        return "glass_break"
    if re.search(r"\b(turned\s+the\s+page|unfolded\s+(?:the\s+)?(?:letter|map|scroll|parchment)|parchment\s+rustled)\b", t_low):
        return "paper"
    if re.search(r"\b(ticking\s+of\s+(?:the\s+)?clock|grandfather\s+clock\s+ticked|pendulum\s+swung|electronic\s+alarm)\b", t_low):
        return "clock"
    if re.search(r"\b(rain\s+(?:poured|drummed|lashed)|raindrops?\s+tapped|freezing\s+rain|sleet\s+drummed|downpour)\b", t_low):
        return "rain"
    if re.search(r"\b(thunder\s+(?:roared|clapped|rumbled)|bolt\s+of\s+lightning\s+struck|flash\s+of\s+lightning|white-silver\s+lightning\s+struck)\b", t_low):
        if not re.search(r"\b(like\s+lightning|as\s+if\s+lightning)\b", t_low):
            return "thunder"
    if re.search(r"\b(fire\s+crackled|flames?\s+crackled|logs?\s+crackled|campfire|hearth-fire|birch\s+logs\s+burning)\b", t_low):
        return "crackle"
    if re.search(r"\b(water\s+dripped|dripping\s+water|droplet\s+fell)\b", t_low):
        return "drip"
    if re.search(r"\b(splashed\s+into\s+the\s+(?:water|pool|river|lake)|splashing\s+loudly\s+into)\b", t_low):
        return "splash"
    if re.search(r"\b(wind\s+howled|howling\s+gale|chilling\s+draft|northern\s+gale)\b", t_low):
        return "wind"
    if re.search(r"\b(primeval\s+forest|rustling\s+canopy|whispering\s+woods)\b", t_low):
        return "forest"
    if re.search(r"\b(waves\s+crashed\s+against|ocean\s+surf|tidal\s+wall|boiling\s+sea)\b", t_low):
        return "ocean"
    if re.search(r"\b(crickets?\s+chirped|crickets?\s+sang)\b", t_low):
        return "crickets"
    if re.search(r"\b(crows?\s+cawed|ravens?\s+cawed|croak\s+of\s+a\s+raven)\b", t_low):
        return "crow"
    if re.search(
        r"\b(fidgeting\s+with\s+(?:my|her|his)\s+sleeves|straightening\s+(?:his|her)\s+coat|bow(?:s|ed)?\s+low|"
        r"bow(?:s|ed)?\s+in\s+(?:perfect\s+)?sync|kneel(?:s|ed|ing)?\b.*?\bunison\b|kneel(?:s|ed|ing)?\s+before|"
        r"outfit\s+adjusts|leaned\s+on\s+the\s+wall|took\s+out\s+a\s+towel|removed\s+her\s+clothes|dressed\s+up)\b",
        t_low,
    ):
        return "rustle"

    if re.search(r"\b(teleported|teleportation|spatial\s+flash|spatial\s+warp|vanished\s+into\s+thin\s+air|vanished\s+in\s+a\s+flash\s+of\s+light|ejected\s+from\s+that\s+space)\b", t_low):
        return "teleport"
    if re.search(r"\b(spatial\s+rift|burst\s+of\s+air\s+whooshed|swept\s+past|sucking\s+the\s+air)\b", t_low):
        return "whoosh"
    if re.search(r"\b(glowing\s+(?:strands|crystal|runes)|aura\s+hummed|energy\s+strands\s+flying|golden\s+light|hands\s+glowed\s+in\s+white|leyline\s+current|harmonic\s+hum)\b", t_low):
        return "hum"
    if line_type == "System" or re.search(r"\b(ding!|system\s+notification|system\s+message|pendragon\s+codex)\b", t_low):
        if any(w in t_low for w in ("warning", "danger", "alert", "error", "fatality", "cancelled", "intrusion", "tamper", "breach")):
            return "alert"
        if "level up" in t_low:
            return "levelup"
        if "quest" in t_low:
            return "quest"
        if "achievement" in t_low or "milestone" in t_low:
            return "achievement"
        if "reward" in t_low:
            return "reward"
        return "chime" if "ding" in t_low else "interface"
    if re.search(r"\b(coins?\s+(?:clinked|jingled|dropped)|pouch\s+of\s+coins?|gold\s+sovereigns)\b", t_low):
        return "coin"
    if re.search(r"\b(opened\s+the\s+(?:treasure\s+)?chest|chest\s+lid\s+opened|cedar\s+chest)\b", t_low):
        return "chest"
    if re.search(r"\b(equipped\s+the|donned\s+the\s+(?:armor|ring|blade))\b", t_low):
        return "equip"

    if re.search(r"\b(bustling\s+market|vendors\s+shouting|noisy\s+bazaar)\b", t_low):
        return "market"
    if re.search(r"\b(stadium\s+erupted|crowd\s+cheered|applause\s+echoed|roaring\s+cheers)\b", t_low):
        return "cheer"
    if re.search(r"\b(crowd\s+groaned|disappointed\s+murmurs?)\b", t_low):
        return "disappointed"
    if re.search(r"\b(set\s+down\s+the\s+plates?|plates?\s+clattered|dishes\s+clattered|clattering\s+trenchers)\b", t_low):
        return "dishes"
    if re.search(r"\b(chewed\s+hungrily|chewing\s+the\s+meat|took\s+a\s+bite\s+of\s+(?:the\s+)?food)\b", t_low):
        if not re.search(r"\b(water|drink|drank|potion|elixir|chugged)\b", t_low):
            return "eating"
    if re.search(r"\b(sizzled\s+in\s+the\s+pan|pot\s+bubbled\s+over|seared\s+the\s+meat)\b", t_low):
        return "cooking"
    if re.search(r"\b(lips\s+and\s+hers\s+were\s+touching|closed\s+her\s+eyes.*released\s+the\s+tension|leaned\s+in\s+close|tongues\s+intertwined|sweet\s+moans|pounded\s+her|rode\s+on\s+top\s+of\s+me|claimed\s+her\s+waiting\s+lips)\b", t_low):
        return "intimate"
    if re.search(r"\b(bright\s+red|shyly\s+smiled|patted\s+(?:her|his)\s+head|laced\s+(?:her|his|our)\s+fingers|fingers\s+slipped\s+through|hugged\s+one\s+of\s+my\s+arms|snuggling\s+my|kiss\s+on\s+my\s+cheek)\b", t_low):
        return "heartwarm"
    if line_type != "Dialogue" and re.search(r"\b(phantom\s+murmurs?|eldritch\s+whispers?|voices?\s+coiling\s+in\s+(?:his|her)\s+head)\b", t_low):
        return "whisper"
    if re.search(r"\b(unnatural\s+chill|temperature\s+dropped|chilling\s+presence)\b", t_low):
        return "haunt"
    if re.search(r"\b(distant\s+howl|wolf\s+howl(?:ed|ing)?)\b", t_low):
        return "howl"
    if re.search(r"\b(bells?\s+(?:chimed|tolled|rang)|bronze\s+chime)\b", t_low):
        return "bells"
    if re.search(r"\b(spiritual\s+gong|temple\s+gong|gong\s+sounded|boarding-gongs)\b", t_low):
        return "gong"

    if bgm_mood in ("combat", "tension", "dread") and len(text.split()) >= 25:
        return "short_breath_female" if speaker_gender == "Female" else "short_breath_male"

    return ""


# =====================================================================
# SUSTAINED SCENE BGM MOOD CLASSIFIER (Rules + VADER + NRCLex)
# =====================================================================

MOOD_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "combat": (
        "battle", "attack", "slash", "roar", "explosion", "boom", "sniper", "bullet",
        "void beast", "mock battle", "barehanded", "clashed", "strike", "weapon", "ballista", "javelin",
        "siege", "breach", "mortars", "broadsword", "halberd", "dreadnought",
    ),
    "tension": (
        "danger", "d-day", "sweat", "heart", "breath", "quietly", "crept", "searched",
        "approached", "shadow", "stiffened", "surprise", "concealment", "detection range", "spies", "sabotage",
    ),
    "sorrow": (
        "crying", "tears", "fallen comrades", "sacrific", "died", "casualties", "foolish",
        "old lady's history", "sad", "grief", "mourn", "loss", "weeping", "sobs", "anguished", "regret",
        "failed", "broken heart", "gloomy",
    ),
    "wonder": (
        "crystal", "golden energy", "purple strands", "amazement", "illuminating",
        "core", "dimension", "administrator", "ancient", "carved on the wall", "black hole", "wings", "white light",
        "starlight", "leyline", "sky-beacon",
    ),
    "warmth": (
        "kiss", "towel", "handkerchief", "smile", "shyly", "pat", "console",
        "bright red", "shoulders", "tender", "warm", "trust", "hugged", "snuggling", "moans", "embrace", "cheerful",
    ),
    "intrigue": (
        "clue", "eliminating", "secret", "scheme", "plan", "method", "studying",
        "nobility", "contract", "guilt", "suspicious", "ancient families", "bloodline", "seimei", "virigil",
        "kingdom", "politics", "economy", "competitors", "demon lords", "holy barrier", "cipher", "blueprint",
    ),
    "triumph": (
        "victory", "granted", "achievement", "conquered", "breakthrough", "celebrat",
        "champion", "won", "succeed", "vanquished", "annihilation",
    ),
    "dread": (
        "horror", "corpse", "blood", "abyss", "curse", "eldritch", "nightmare",
        "void", "despair", "chill", "crumble", "darkness", "fatality", "miasma", "void-rot",
    ),
    "playful": (
        "idiot", "joked", "poutily", "teenager", "cute", "banter", "giggle",
        "teas", "kid", "flustered", "plump ass", "winked playfully", "colourblind", "fashion expert", "mock",
    ),
}

NRC_TO_BGM_MAP = {
    "anger": "combat",
    "fear": "tension",
    "sadness": "sorrow",
    "surprise": "wonder",
    "trust": "warmth",
    "anticipation": "intrigue",
    "joy": "playful",
    "disgust": "dread",
}


def score_segment_bgm_mood(text: str, affect: Dict[str, Any]) -> str:
    low = text.lower()
    best_mood = "no_mood"
    best_score = 0
    for mood, keywords in MOOD_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in low)
        if score > best_score:
            best_score = score
            best_mood = mood

    if best_score >= 1:
        return best_mood

    top_nrc = affect.get("top_nrc", "")
    compound = affect.get("compound", 0.0)
    if top_nrc in NRC_TO_BGM_MAP and abs(compound) >= 0.35:
        mapped = NRC_TO_BGM_MAP[top_nrc]
        if mapped == "playful" and compound >= 0.55 and "!" not in text:
            return "warmth"
        return mapped

    return "no_mood"


def enforce_bgm_governing_rules(segments: List[Dict[str, Any]]) -> None:
    n = len(segments)
    if n == 0:
        return

    for i in range(1, n - 1):
        if segments[i]["bgm_mood"] == "no_mood":
            prev_m = segments[i - 1]["bgm_mood"]
            next_m = segments[i + 1]["bgm_mood"]
            if prev_m != "no_mood" and prev_m == next_m:
                segments[i]["bgm_mood"] = prev_m

    i = 0
    while i < n:
        m = segments[i]["bgm_mood"]
        if m != "no_mood":
            j = i
            while j < n and segments[j]["bgm_mood"] == m:
                j += 1
            if (j - i) < 4:
                for k in range(i, j):
                    segments[k]["bgm_mood"] = "no_mood"
            i = j
        else:
            i += 1

    for i in range(1, n):
        prev_m = segments[i - 1]["bgm_mood"]
        curr_m = segments[i]["bgm_mood"]
        if prev_m != "no_mood" and curr_m != "no_mood" and prev_m != curr_m:
            segments[i]["bgm_mood"] = "no_mood"


# =====================================================================
# SCARE-QUOTE GUARD, TOKENIZER & CROSS-PARAGRAPH CONSOLIDATION
# =====================================================================

def _balance_quotes(p: str) -> str:
    p = p.replace("\u201c", '"').replace("\u201d", '"')
    if p.count('"') % 2 != 0:
        if re.search(rf"\b(?:{SPEECH_VERBS})\b", p, re.I):
            p = p + '"'
        else:
            p = '"' + p
    return p


def _is_scare_quote(spoken: str, pre_ctx: str, post_ctx: str) -> bool:
    pre_s = pre_ctx.strip()
    post_s = post_ctx.strip()
    words = spoken.split()

    if not pre_s:
        return False

    if re.search(rf"\b(?:{SPEECH_VERBS}|tell\s+\w+\s+that|say|saying|thought|muttered|whispered)\b[^.!?]{{0,25}}$", pre_s, re.I):
        return False
    if pre_s.endswith((":", ",")) and spoken[0:1].isupper():
        return False

    if len(words) <= 3 and not re.search(r"[!?]$", spoken):
        if re.match(r"^(?:\.\s+[A-Z]|\.$|[a-z]|,\s*[a-z])", post_s) or (
            not post_s and re.search(r"\b(?:the|a|an|her|his|my|our|their|inside|called|as)\s*$", pre_s, re.I)
        ):
            return True

    return False


def _is_inline_single_quote_thought(inner: str, lead_text: str, tail_text: str) -> bool:
    lead_s = lead_text.strip()
    tail_s = tail_text.strip()

    if re.search(r"\b(?:the|a|an|another|that|this|called|said\s+the)\s*$", lead_s, re.I):
        return False

    if not lead_s or lead_s.endswith((".", "!", "?", ":")):
        return True
    if RE_THOUGHT_TAG.search(tail_s[:60]) or RE_THOUGHT_TAG.search(lead_s[-60:]):
        return True
    if re.search(r"[!?…]$", inner) and len(inner.split()) >= 3:
        return True
    return False


def _split_sentences(text: str, max_len: int = 650) -> List[str]:
    cleaned = " ".join(text.strip().split())
    if not cleaned:
        return []
    if len(cleaned) <= max_len:
        return [cleaned]

    # Prefer NLTK punkt sentence tokenizer so abbreviations (Lv. 9, Mr., St.) never split mid-sentence
    nltk_sents = _nltk_split_sentences(cleaned)
    if nltk_sents and len(nltk_sents) > 1:
        out: List[str] = []
        buf: List[str] = []
        acc = 0
        for s in nltk_sents:
            s_clean = s.strip()
            if not s_clean:
                continue
            if acc + len(s_clean) + 1 > max_len and buf:
                out.append(" ".join(buf))
                buf = [s_clean]
                acc = len(s_clean)
            else:
                buf.append(s_clean)
                acc += len(s_clean) + 1
        if buf:
            out.append(" ".join(buf))
        if out:
            return out

    sent_pat = re.compile(r'.*?[.!?…]["\')]?(?=\s+|$)', re.DOTALL)
    out = []
    rem = cleaned
    while rem:
        if len(rem) <= max_len:
            out.append(rem)
            break
        buf = []
        acc = 0
        last_end = 0
        for m in sent_pat.finditer(rem):
            s = m.group(0).strip()
            buf.append(s)
            acc += len(s) + 1
            last_end = m.end()
            if acc >= max_len:
                break
        if buf and last_end > 0:
            out.append(" ".join(buf))
            rem = rem[last_end:].strip()
        else:
            out.append(rem)
            break
    return out


def _map_onomatopoeia_to_sfx(raw_sound: str) -> str:
    tokens = re.findall(r"[a-zA-Z]+", raw_sound.lower())
    for w in tokens:
        if w in ONOMATOPOEIA_MAP:
            return ONOMATOPOEIA_MAP[w]
        if w.startswith(("roar", "rooo", "graa", "ggrr", "shriek")):
            return "monster"
        if w.startswith(("booo", "kaboo", "krakoo")):
            return "explosion"
        if w.startswith("beep"):
            return "alert"
        if w.startswith("bwooo"):
            return "wardrum"
    return "impact"


# =====================================================================
# MAIN FALLBACK DIRECTOR ENTRY POINT
# =====================================================================

def run_comprehensive_fallback_director(
    raw_text: str,
    char_map: Dict[str, Any],
    max_narr_merge: int = 650,
) -> List[Dict[str, Any]]:
    """
    Complete local Screenplay Director fallback for Gemini 503 / 429 / Timeout /
    PROHIBITED_CONTENT / SAFETY blocks, combining registry-locked character profiles,
    flashtext2 O(N) phonetic respellings, NLTK sentence/POS verification, VADER + NRCLex
    affect scoring, 74-key SFX detection, and sustained BGM mood classification.
    """
    cast = FallbackCastTracker(char_map)
    cast.pre_scan_chapter_entities(raw_text)

    paragraphs = [
        p.strip()
        for p in raw_text.split("\n\n")
        if p.strip() and not RE_AD_OR_NOTE_LINE.match(p.strip())
    ]

    staged_rows: List[Dict[str, Any]] = []
    prev_spoken_speaker: Optional[str] = None
    narr_buffer: List[Tuple[str, bool]] = []

    def _flush_narration_buffer() -> None:
        nonlocal prev_spoken_speaker
        if not narr_buffer:
            return
        full_narr = " ".join(chunk_txt for chunk_txt, _ in narr_buffer)
        first_is_para_start = narr_buffer[0][1]
        narr_buffer.clear()

        for c_idx, chunk in enumerate(_split_sentences(full_narr, max_len=max_narr_merge)):
            cast.note_narration_context(chunk)
            affect = analyze_affect_vader_nrc(chunk)
            mood_val = score_segment_bgm_mood(chunk, affect)
            tier, emo, l_reset = classify_solfege_pitch_tier(
                chunk,
                "Narration",
                is_paragraph_start=(first_is_para_start and c_idx == 0),
                bgm_mood=mood_val,
                speaker_meta={"age_category": "adult"},
                affect=affect,
            )
            disp_t, tts_t = build_dual_texts(chunk, "Narration", tier)
            if not disp_t:
                continue
            sfx_val = detect_literal_sfx(disp_t, "Narration", mood_val, cast.mc_gender)

            staged_rows.append({
                "line_id": "0000",
                "speaker": "Narrator",
                "gender": "Neutral",
                "line_type": "Narration",
                "emotion": emo,
                "age_category": "adult",
                "display_text": disp_t,
                "tts_text": tts_t,
                "text": disp_t,
                "voice": "en-US-ChristopherNeural",
                "pitch_tier": tier,
                "pitch": "-2Hz",
                "rate": "+0%",
                "lung_reset": l_reset,
                "pause_duration": 0.0,
                "sfx": sfx_val,
                "bgm_mood": mood_val,
            })
            prev_spoken_speaker = "Narrator"

    total_paras = len(paragraphs)
    for p_idx, raw_para in enumerate(paragraphs):
        prev_para_raw = paragraphs[p_idx - 1] if p_idx > 0 else ""
        next_para_raw = paragraphs[p_idx + 1] if (p_idx + 1) < total_paras else ""
        next2_para_raw = paragraphs[p_idx + 2] if (p_idx + 2) < total_paras else ""

        # 0. Scene Divider ("---" / "***") -> 0.85s pause row + reset scene POV tracking
        if RE_SCENE_BREAK.match(raw_para):
            _flush_narration_buffer()
            upcoming_window = " ".join(paragraphs[p_idx + 1: min(total_paras, p_idx + 3)])
            cast.reset_scene(upcoming_window)
            staged_rows.append({
                "line_id": "0000",
                "speaker": "Narrator",
                "gender": "Neutral",
                "line_type": "Narration",
                "emotion": "neutral",
                "age_category": "adult",
                "display_text": "",
                "tts_text": "",
                "text": "",
                "voice": "en-US-ChristopherNeural",
                "pitch_tier": "narrator_anchor",
                "pitch": "-2Hz",
                "rate": "+0%",
                "lung_reset": False,
                "pause_duration": 0.85,
                "sfx": "",
                "bgm_mood": "no_mood",
            })
            continue

        para = _balance_quotes(raw_para)
        if not para or not RE_ALPHANUM.search(para):
            continue

        # 1. Standalone Onomatopoeia & Asterisk Sound Interception
        if RE_STANDALONE_ONOMATOPOEIA.fullmatch(para) or (
            RE_MULTI_ASTERISK_SFX.match(para) and len(para.split()) <= 6
        ):
            _flush_narration_buffer()
            sfx_hit = _map_onomatopoeia_to_sfx(para)
            staged_rows.append({
                "line_id": "0000",
                "speaker": "Narrator",
                "gender": "Neutral",
                "line_type": "Narration",
                "emotion": "neutral",
                "age_category": "adult",
                "display_text": "",
                "tts_text": "",
                "text": "",
                "voice": "en-US-ChristopherNeural",
                "pitch_tier": "narrator_anchor",
                "pitch": "-2Hz",
                "rate": "+0%",
                "lung_reset": False,
                "pause_duration": 0.45,
                "sfx": sfx_hit,
                "bgm_mood": "combat" if sfx_hit in ("explosion", "impact", "blade", "gunshot", "monster") else "no_mood",
            })
            continue

        # 2. System Window Detection (explicit prefix, bracketed cards, or inline System prompt)
        if '"' not in para and (
            RE_SYSTEM_LINE.match(para)
            or RE_BRACKETED_SYSTEM_PARA.match(para)
            or RE_SYSTEM_INLINE.search(para)
        ):
            _flush_narration_buffer()
            affect = analyze_affect_vader_nrc(para)
            mood_val = score_segment_bgm_mood(para, affect)
            tier, emo, _ = classify_solfege_pitch_tier(
                para, "System", False, mood_val, {"age_category": "n/a"}, affect
            )
            disp_t, tts_t = build_dual_texts(para, "System", tier)
            sfx_val = detect_literal_sfx(disp_t, "System", mood_val, "Neutral")
            staged_rows.append({
                "line_id": "0000",
                "speaker": "System",
                "gender": "Neutral",
                "line_type": "System",
                "emotion": emo,
                "age_category": "n/a",
                "display_text": disp_t,
                "tts_text": tts_t,
                "text": disp_t,
                "voice": "en-US-AriaNeural",
                "pitch_tier": tier,
                "pitch": "+0Hz",
                "rate": "+2%",
                "lung_reset": False,
                "pause_duration": 0.25,
                "sfx": sfx_val,
                "bgm_mood": mood_val,
            })
            prev_spoken_speaker = "System"
            continue

        # 3. Inline Single-Quoted First-Person Internal Thought
        if '"' not in para and RE_INLINE_SINGLE_THOUGHT.search(para):
            matches = list(RE_INLINE_SINGLE_THOUGHT.finditer(para))
            valid_thoughts = [
                m for m in matches
                if _is_inline_single_quote_thought(m.group(1).strip(), para[:m.start()], para[m.end():])
            ]
            if valid_thoughts:
                _flush_narration_buffer()
                mc_meta = cast.get_mc()
                cursor = 0
                for m in valid_thoughts:
                    lead_narr = para[cursor:m.start()].strip()
                    if lead_narr and RE_ALPHANUM.search(lead_narr):
                        narr_buffer.append((lead_narr, cursor == 0))
                        _flush_narration_buffer()

                    inner = m.group(1).strip()
                    affect = analyze_affect_vader_nrc(inner)
                    mood_val = score_segment_bgm_mood(inner, affect)
                    tier, emo, _ = classify_solfege_pitch_tier(inner, "Dialogue", False, mood_val, mc_meta, affect)
                    if tier == "conversational_mid":
                        tier = "thoughtful_drawl"
                    disp_t, tts_t = build_dual_texts(inner, "Dialogue", tier)
                    sfx_val = detect_literal_sfx(disp_t, "Dialogue", mood_val, mc_meta["gender"])
                    staged_rows.append({
                        "line_id": "0000",
                        "speaker": mc_meta["display_name"],
                        "gender": mc_meta["gender"],
                        "line_type": "Dialogue",
                        "emotion": emo,
                        "age_category": mc_meta["age_category"],
                        "display_text": disp_t,
                        "tts_text": tts_t,
                        "text": disp_t,
                        "voice": mc_meta["voice"],
                        "pitch_tier": tier,
                        "pitch": mc_meta.get("pitch", "+0Hz"),
                        "rate": compute_segment_rate("Dialogue", tier),
                        "lung_reset": False,
                        "pause_duration": 0.15,
                        "sfx": sfx_val,
                        "bgm_mood": mood_val,
                    })
                    prev_spoken_speaker = mc_meta["display_name"]
                    cursor = m.end()

                tail_narr = para[cursor:].strip()
                if tail_narr and RE_ALPHANUM.search(tail_narr):
                    narr_buffer.append((tail_narr, False))
                continue

        # 4. Mixed Dialogue & Narration Segmentation (with Scare-Quote Guard & 2-Para Lookahead)
        tokens = [t for t in RE_QUOTE_SPAN.split(para) if t and t.strip()]
        is_first_narr_in_para = True

        for t_idx, tok in enumerate(tokens):
            tok_clean = tok.strip()
            if not tok_clean or not RE_ALPHANUM.search(tok_clean):
                continue

            is_quote = tok_clean.startswith('"') and tok_clean.endswith('"')
            pre_ctx = " ".join(tokens[:t_idx])
            post_ctx = " ".join(tokens[t_idx + 1:])

            if is_quote:
                spoken = tok_clean.strip('"').strip()
                if not spoken or not RE_ALPHANUM.search(spoken):
                    continue

                if _is_scare_quote(spoken, pre_ctx, post_ctx):
                    if narr_buffer:
                        prev_txt, prev_flag = narr_buffer[-1]
                        narr_buffer[-1] = (f"{prev_txt} {spoken}", prev_flag)
                    else:
                        narr_buffer.append((spoken, is_first_narr_in_para))
                        is_first_narr_in_para = False
                    continue

                _flush_narration_buffer()

                if RE_THOUGHT_TAG.search(f"{pre_ctx[-60:]} {post_ctx[:60]}") and not re.search(
                    rf"\b(?:{SPEECH_VERBS})\b", f"{pre_ctx[-60:]} {post_ctx[:60]}", re.I
                ):
                    sp_meta = cast.get_mc()
                else:
                    sp_meta = cast.resolve_dialogue_speaker(
                        quote_text=spoken,
                        pre_context=pre_ctx,
                        post_context=post_ctx,
                        prev_para_text=prev_para_raw,
                        next_para_text=next_para_raw,
                        next2_para_text=next2_para_raw,
                    )

                # Always enforce locked registry profile if present
                locked_sp = cast._lookup_locked_profile(sp_meta["display_name"])
                if locked_sp:
                    sp_meta = locked_sp

                sp_name = sp_meta["display_name"]
                affect = analyze_affect_vader_nrc(f"{spoken} {post_ctx[:80]}")
                mood_val = score_segment_bgm_mood(f"{spoken} {post_ctx[:80]}", affect)

                if prev_spoken_speaker and prev_spoken_speaker != sp_name and prev_spoken_speaker != "Narrator":
                    prev_text = staged_rows[-1].get("display_text", "") if staged_rows else ""
                    if prev_text.endswith("-") or prev_text.endswith("--"):
                        turn_pause = 0.05
                    elif mood_val == "combat" or ("!" in spoken and "!" in prev_text):
                        turn_pause = 0.2
                    else:
                        turn_pause = 0.6

                    staged_rows.append({
                        "line_id": "0000",
                        "speaker": "Narrator",
                        "gender": "Neutral",
                        "line_type": "Narration",
                        "emotion": "neutral",
                        "age_category": "adult",
                        "display_text": "",
                        "tts_text": "",
                        "text": "",
                        "voice": "en-US-ChristopherNeural",
                        "pitch_tier": "narrator_anchor",
                        "pitch": "-2Hz",
                        "rate": "+0%",
                        "lung_reset": False,
                        "pause_duration": turn_pause,
                        "sfx": "",
                        "bgm_mood": "no_mood",
                    })

                tier, emo, _ = classify_solfege_pitch_tier(spoken, "Dialogue", False, mood_val, sp_meta, affect)
                disp_t, tts_t = build_dual_texts(spoken, "Dialogue", tier)
                if not disp_t:
                    continue
                sfx_val = detect_literal_sfx(f"{disp_t} {post_ctx[:80]}", "Dialogue", mood_val, sp_meta["gender"])
                rate_str = compute_segment_rate("Dialogue", tier)

                staged_rows.append({
                    "line_id": "0000",
                    "speaker": sp_name,
                    "gender": sp_meta["gender"],
                    "line_type": "Dialogue",
                    "emotion": emo,
                    "age_category": sp_meta["age_category"],
                    "display_text": disp_t,
                    "tts_text": tts_t,
                    "text": disp_t,
                    "voice": sp_meta["voice"],
                    "pitch_tier": tier,
                    "pitch": sp_meta.get("pitch", "+0Hz"),
                    "rate": rate_str,
                    "lung_reset": False,
                    "pause_duration": 0.0,
                    "sfx": sfx_val,
                    "bgm_mood": mood_val,
                })
                prev_spoken_speaker = sp_name

            else:
                if tok_clean.startswith((".", ",", ";", ":")) and narr_buffer:
                    prev_txt, prev_flag = narr_buffer[-1]
                    if re.match(r"^[.,;:]\s*$", tok_clean):
                        narr_buffer[-1] = (prev_txt + tok_clean.strip(), prev_flag)
                        continue
                    punct_char = tok_clean[0]
                    rest_txt = tok_clean[1:].strip()
                    narr_buffer[-1] = (prev_txt + punct_char, prev_flag)
                    if rest_txt and RE_ALPHANUM.search(rest_txt):
                        narr_buffer.append((rest_txt, False))
                    continue

                narr_clean = re.sub(r"^[,;:\s]+", "", tok_clean).strip()
                if not narr_clean or not RE_ALPHANUM.search(narr_clean):
                    continue
                cast.note_narration_context(narr_clean)
                narr_buffer.append((narr_clean, is_first_narr_in_para))
                is_first_narr_in_para = False
                curr_len = sum(len(x[0]) for x in narr_buffer)
                if curr_len >= max_narr_merge:
                    _flush_narration_buffer()

    _flush_narration_buffer()

    enforce_bgm_governing_rules(staged_rows)

    for idx, row in enumerate(staged_rows, 1):
        row["line_id"] = f"{idx:04d}"
        if row.get("sfx"):
            recent_sfx = [r["sfx"] for r in staged_rows[max(0, idx - 4): idx - 1] if r.get("sfx")]
            if row["sfx"] in recent_sfx:
                row["sfx"] = ""

    return staged_rows