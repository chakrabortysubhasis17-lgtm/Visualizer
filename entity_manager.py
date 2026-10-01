import os
import re
import json
import time

REGISTRY_PATH = "novel_entities_registry.json"
BIBLE_PATH = "mtl_regex_bible.json"

STATIC_EXCLUSIONS = {
    "The", "A", "An", "In", "On", "At", "This", "That", "These", "Those", "There", "Here",
    "Divine Kingdom", "Human Federation", "Secret Realm", "Dark Web", "Divine Sea",
    "Divinity Points", "Faith Points", "Spiritual Milk", "Spiritual Veins", "Anshen Fruit",
    "Five Great Families", "Qi Refining", "Foundation Establishment", "Godhead", "Godhood",
    "Soul Transformation", "High-Order God", "First-Order God", "Tier", "Level", "Chapter",
    "ST Huaning Group Company", "Yang Corporation", "Federation Main Board", "First Floor",
    "Second Floor", "Living Room", "Bedroom", "Office", "Planet", "Federation", "Star Domain",
    "Soul Power", "Divine Power", "Law Power", "Ghost Cultivator", "Elven Warrior",
    "Investigation Team", "Security Group", "Federal Bank", "Federal Population"
}

ENGLISH_STOP_WORDS = {
    "The", "This", "That", "These", "Those", "There", "Here", "What", "When", "Where",
    "Who", "Why", "How", "After", "Before", "While", "During", "Since", "Until",
    "Although", "Though", "Even", "Just", "Only", "Also", "Very", "Too", "Quite",
    "Then", "Now", "Suddenly", "Finally", "Actually", "In", "On", "At", "By", "For",
    "With", "About", "Against", "Between", "Into", "Through", "Above", "Below",
    "To", "From", "Up", "Down", "Out", "Off", "Over", "Under", "Again", "Further",
    "Once", "And", "But", "Or", "Nor", "So", "Yet", "Both", "Either", "Neither",
    "Not", "No", "Yes", "Having", "Being", "Doing", "He", "She", "It", "They",
    "We", "You", "I", "Him", "Her", "Them", "Us", "Me", "His", "Their", "Our",
    "Your", "My", "Its", "Chapter", "Tier", "Level", "First", "Second", "Third",
    "Planet", "Federation", "Star", "Domain", "Company", "Group", "Living", "Room",
    "Floor", "Building", "Office", "Villa", "Godhead", "Godhood", "Someone",
    "Anyone", "Everyone", "Nobody", "Another", "Each", "All", "Both", "Many"
}

SPEECH_VERBS = (
    r"(?:said|asked|replied|shouted|muttered|whispered|screamed|yelled|roared|"
    r"barked|sneered|chuckled|laughed|inquired|commanded|snorted|cried|"
    r"exclaimed|called|ordered|sighed|reminded|prompted|nodded)"
)

# Strict Case-Sensitive proper name boundaries
RE_TAG_AFTER = re.compile(
    rf"\b(?P<name>[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)(?:\s+[a-z]+ly)?\s+{SPEECH_VERBS}\b"
)
RE_TAG_BEFORE = re.compile(
    rf"\b{SPEECH_VERBS}\s+(?P<name>[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"
)
RE_TITLE_NAME = re.compile(
    r"\b(?P<title>CEO|President|Director|General Manager|Manager|Elder|Patriarch|Young Master|General|Commander)\s+(?P<name>[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"
)


# ==================== 1. BIBLE COMPILER ====================
class BibleEngine:
    def __init__(self, bible_path: str = BIBLE_PATH):
        self.bible_path = bible_path
        self.raw = self._load()
        self.compiled = self._compile()

    def _load(self) -> dict:
        if os.path.exists(self.bible_path):
            try:
                with open(self.bible_path, "r", encoding="utf-8") as f:
                    return json.load(f).get("web_novel_regex_bible", {})
            except Exception as e:
                print(f"[BibleEngine Warning] Failed to parse {self.bible_path}: {e}")
        return {}

    def _compile(self) -> dict:
        def build_regex(word_list):
            if not word_list:
                return None
            unique_sorted = sorted(list(set(word_list)), key=len, reverse=True)
            return re.compile(r"\b(" + "|".join(map(re.escape, unique_sorted)) + r")\b", re.IGNORECASE)

        comp = {"female": {}, "male": {}, "tropes": {}}
        g_data = self.raw.get("gender_classification", {})
        for g in ["female", "male"]:
            for cat, words in g_data.get(g, {}).items():
                comp[g][cat] = build_regex(words)

        tropes = self.raw.get("mtl_archetype_tropes", {})
        for trope_name, t_meta in tropes.items():
            comp["tropes"][trope_name] = {
                "catchphrases": build_regex(t_meta.get("catchphrases", []))
            }
        return comp


BIBLE = BibleEngine()


# ==================== 2. LOCAL & MASTER REGISTRY MANAGER ====================
class EntityManager:
    def __init__(self, novel_slug: str, build_dir: str):
        self.novel_slug = novel_slug
        self.build_dir = build_dir
        self.local_staging_file = os.path.join(build_dir, "local_entities_staging.json")
        os.makedirs(self.build_dir, exist_ok=True)

        self.registry = self._load_merged_registry()
        self.characters = self.registry.get("characters", {})
        self.vocatives = self.registry.get("vocatives", {})
        self.new_local_discoveries = {}

    def _load_merged_registry(self) -> dict:
        master_data = {}
        if os.path.exists(REGISTRY_PATH):
            for _ in range(5):
                try:
                    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                        master_data = json.load(f)
                    break
                except (IOError, json.JSONDecodeError):
                    time.sleep(0.1)

        section = master_data.get(self.novel_slug, {"characters": {}, "vocatives": {}})

        if os.path.exists(self.local_staging_file):
            try:
                with open(self.local_staging_file, "r", encoding="utf-8") as f:
                    local_data = json.load(f)
                    section["characters"].update(local_data.get("characters", {}))
            except Exception:
                pass

        return section

    def _persist_local_staging(self):
        if not self.new_local_discoveries:
            return
        data = {"characters": {}}
        if os.path.exists(self.local_staging_file):
            try:
                with open(self.local_staging_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass

        data["characters"].update(self.new_local_discoveries)
        with open(self.local_staging_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _is_valid_proper_name(self, name: str) -> bool:
        words = name.strip().split()
        if not (1 <= len(words) <= 2):
            return False
        for w in words:
            if not re.match(r"^[A-Z][a-z]{1,18}$", w):
                return False
            if w in ENGLISH_STOP_WORDS:
                return False
            if w.endswith("ly") and len(w) > 4:
                return False
        if name in STATIC_EXCLUSIONS:
            return False
        return True

    def _infer_entity_profile(self, name: str, context: str) -> dict:
        ctx = context.lower()
        role_key = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")

        if any(w in ctx for w in ["brat", "little fellow", "little guy", "son", "child", "daddy", "mommy"]):
            return {
                "gender": "Male", "role": "child_character",
                "voice": "en-US-AnaNeural", "pitch": "+8Hz", "rate": "+4%", "aliases": [name.lower()]
            }

        if any(w in ctx for w in ["elder", "patriarch", "ceo", "president", "general", "commander", "director"]):
            return {
                "gender": "Male", "role": "corporate_boss",
                "voice": "en-US-RogerNeural", "pitch": "-10Hz", "rate": "+2%", "aliases": [name.lower()]
            }

        if any(w in ctx for w in ["manager", "assistant", "secretary", "subordinate"]):
            return {
                "gender": "Male", "role": "manager_ma",
                "voice": "en-US-ChristopherNeural", "pitch": "-4Hz", "rate": "+4%", "aliases": [name.lower()]
            }

        if any(w in ctx for w in ["young master", "scion", "heir", "sneered", "barked", "arrogant"]):
            return {
                "gender": "Male", "role": "arrogant_scion",
                "voice": "en-US-EricNeural", "pitch": "+6Hz", "rate": "+10%", "aliases": [name.lower()]
            }

        fem_titles = BIBLE.compiled["female"].get("high_confidence_titles")
        if (fem_titles and fem_titles.search(ctx)) or any(w in ctx for w in ["sister", "miss", "lady", "girl", "woman", "mother", "wife"]):
            return {
                "gender": "Female", "role": "goddess_peer",
                "voice": "en-US-JennyNeural", "pitch": "+2Hz", "rate": "+8%", "aliases": [name.lower()]
            }

        return {
            "gender": "Male", "role": role_key,
            "voice": "en-US-ChristopherNeural", "pitch": "+2Hz", "rate": "+6%", "aliases": [name.lower()]
        }

    def register_new_entity(self, raw_name: str, context: str) -> str:
        name = raw_name.strip()
        if not self._is_valid_proper_name(name):
            return ""

        name_lower = name.lower()
        for existing_name, meta in self.characters.items():
            if name_lower == existing_name or name_lower in meta.get("aliases", []):
                return meta["role"]

        profile = self._infer_entity_profile(name, context)
        self.new_local_discoveries[name_lower] = profile
        self.characters[name_lower] = profile
        self._persist_local_staging()

        print(f"  [Entity Auto-Discovery] Registered Verified Character '{name}' -> Role: '{profile['role']}'")
        return profile["role"]

    def scan_chapter_for_entities(self, text: str, default_female_role: str = "goddess_peer", default_male_role: str = "yang_fan"):
        for match in RE_TITLE_NAME.finditer(text):
            self.register_new_entity(match.group("name"), text[max(0, match.start() - 60):min(len(text), match.end() + 60)])

        for match in RE_TAG_AFTER.finditer(text):
            self.register_new_entity(match.group("name"), text[max(0, match.start() - 60):min(len(text), match.end() + 60)])

        for match in RE_TAG_BEFORE.finditer(text):
            self.register_new_entity(match.group("name"), text[max(0, match.start() - 60):min(len(text), match.end() + 60)])

    def is_scare_quote_or_narration(self, quote: str, prev_context: str, next_context: str) -> bool:
        quote_strip = quote.strip()
        words = quote_strip.split()

        # Phrases <= 4 words with no terminal punctuation and no speech verb
        if len(words) <= 4 and not re.search(r'[.!?]$', quote_strip):
            speech_verb = re.compile(rf'\b{SPEECH_VERBS}\b', re.I)
            if not speech_verb.search(prev_context[-35:]) and not speech_verb.search(next_context[:35]):
                return True

        has_dialogue_pronoun = bool(re.search(r"\b(i|me|my|mine|you|your|yours|we|us|our)\b", quote_strip, re.I))
        if not has_dialogue_pronoun:
            if re.search(r"\b(she|he|they)\s+(still|obediently|gradually|silently|suddenly|eventually|was|were|could)\b", quote_strip, re.I):
                return True
            if re.search(r"^(the core theme|wants it\?|likes it\?|wants to play\?|what the son wants|a wage slave's life)", quote_strip, re.I):
                return True

        return False

    def classify_dialogue(self, quote: str, prev_context: str, next_context: str, last_dialogue_role: str, local_character_registry: dict) -> str:
        quote_clean = quote.strip()
        prev_clean = prev_context.strip().lower()
        next_clean = next_context.strip().lower()
        surrounding = f"{prev_clean} {next_clean}"
        immediate_prev = prev_clean[-60:]
        immediate_next = next_clean[:60]
        tag_zone = f"{immediate_prev} | {immediate_next}"

        # 1. Scare Quotes
        if self.is_scare_quote_or_narration(quote_clean, prev_clean, next_clean):
            return "narrator"

        # 2. Vocatives (Opening word priority)
        for voc, meta in self.vocatives.items():
            if re.search(r'^(["“\']?\s*)' + re.escape(voc) + r'[\s,!?:.]', quote_clean, re.I) or quote_clean.lower() == voc:
                if meta["role"] in local_character_registry:
                    return meta["role"]

        # 3. Known Tag Matching in Tag Zone
        for name, meta in self.characters.items():
            all_names = [name] + meta.get("aliases", [])
            pattern = r"\b(" + "|".join(re.escape(n) for n in all_names) + r")\b"
            if re.search(pattern, tag_zone):
                if meta["role"] in local_character_registry:
                    return meta["role"]

        # 4. Continuation of Multi-Sentence Dialogue
        if last_dialogue_role in local_character_registry and last_dialogue_role != "narrator":
            speech_verb = re.compile(rf'\b{SPEECH_VERBS}\b', re.I)
            if not speech_verb.search(immediate_prev):
                last_gender = local_character_registry[last_dialogue_role].get("gender")
                if re.search(r"^(however|and|besides|after all|no matter|furthermore|speaking of|since|although|in reality|it's just that|right)\b", quote_clean, re.I):
                    return last_dialogue_role
                if last_gender == "Female" and not re.search(r"\b(yang fan|he said|he asked)\b", immediate_prev):
                    return last_dialogue_role
                if "child" in last_dialogue_role and not re.search(r"\b(yang fan|he said)\b", immediate_prev):
                    return last_dialogue_role

        # 5. Surrounding Text Matching
        for name, meta in self.characters.items():
            all_names = [name] + meta.get("aliases", [])
            pattern = r"\b(" + "|".join(re.escape(n) for n in all_names) + r")\b"
            if re.search(pattern, surrounding):
                if meta["role"] in local_character_registry:
                    return meta["role"]

        # 6. Gender Attribution Fallback
        fem_score = len(re.findall(r"\b(she|her|mother|sister|maiden|wife|girl)\b", immediate_prev))
        male_score = len(re.findall(r"\b(he|him|his|father|brother|man|boy)\b", immediate_prev))
        if fem_score > male_score and fem_score >= 1:
            for rk in ["lu_wan", "goddess_peer", "wife_luo_bing", "wife_luo_rou"]:
                if rk in local_character_registry:
                    return rk

        return "yang_fan" if "yang_fan" in local_character_registry else "mc"

    def finalize_and_merge(self):
        if not os.path.exists(self.local_staging_file):
            return

        try:
            with open(self.local_staging_file, "r", encoding="utf-8") as f:
                local_data = json.load(f)
            local_chars = local_data.get("characters", {})

            valid_chars = {k: v for k, v in local_chars.items() if self._is_valid_proper_name(k.title())}

            if not valid_chars:
                try: os.remove(self.local_staging_file)
                except OSError: pass
                return

            for _ in range(10):
                try:
                    master_data = {}
                    if os.path.exists(REGISTRY_PATH):
                        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                            master_data = json.load(f)

                    if self.novel_slug not in master_data:
                        master_data[self.novel_slug] = {"characters": {}, "vocatives": {}}

                    merged_count = 0
                    for name, meta in valid_chars.items():
                        if name not in master_data[self.novel_slug]["characters"]:
                            master_data[self.novel_slug]["characters"][name] = meta
                            merged_count += 1

                    if merged_count > 0:
                        tmp_file = f"{REGISTRY_PATH}.tmp_{os.getpid()}"
                        with open(tmp_file, "w", encoding="utf-8") as f:
                            json.dump(master_data, f, indent=2, ensure_ascii=False)
                        os.replace(tmp_file, REGISTRY_PATH)
                        print(f"  [Master Registry Sync] Atomically merged {merged_count} verified character(s) into master registry.")
                    break
                except (IOError, json.JSONDecodeError):
                    time.sleep(0.15)

            if os.path.exists(self.local_staging_file):
                try: os.remove(self.local_staging_file)
                except OSError: pass
        except Exception as e:
            print(f"[Master Registry Warning] Merge failed: {e}")