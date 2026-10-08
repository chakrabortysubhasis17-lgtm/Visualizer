import os
import json

PRIMARY_REGISTRY_FILE = "novel_entities_registry.json"
FALLBACK_REGISTRY_FILE = "mtl_regex_bible.json"

FALLBACK_BASE_CHARACTERS = {
    "narrator": {"display_name": "Narrator", "gender": "Male", "line_type": "Narration", "voice": "en-US-GuyNeural", "pitch": "+0Hz", "rate": "+5%", "aliases": ["narrator"]},
    "mc": {"display_name": "Protagonist", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-GuyNeural", "pitch": "+0Hz", "rate": "+6%", "aliases": ["host", "mc", "boss"]},
    "system": {"display_name": "System", "gender": "Synthetic", "line_type": "System", "voice": "en-US-SteffanNeural", "pitch": "-18Hz", "rate": "-6%", "aliases": ["system", "prompt", "ding"]},
    "mob": {"display_name": "Crowd", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-TonyNeural", "pitch": "+2Hz", "rate": "+8%", "aliases": ["crowd", "people", "mob"]}
}

def get_active_master_registry_path() -> str:
    """Resolves whether novel_entities_registry.json or mtl_regex_bible.json exists."""
    if os.path.exists(PRIMARY_REGISTRY_FILE):
        return PRIMARY_REGISTRY_FILE
    if os.path.exists(FALLBACK_REGISTRY_FILE):
        return FALLBACK_REGISTRY_FILE
    return PRIMARY_REGISTRY_FILE

def init_session_registry(novel_slug: str, stage_file: str) -> dict:
    """
    Step 1: Reads master registry, extracts the novel's entity block,
    and isolates it in session_entities_staged.json inside the build dir.
    """
    master_path = get_active_master_registry_path()
    staged_data = {"characters": {}, "vocatives": {}}

    if os.path.exists(stage_file):
        try:
            with open(stage_file, "r", encoding="utf-8") as f:
                staged_data = json.load(f)
            print(f"[Registry] [✓] Resumed existing session staging: '{stage_file}'", flush=True)
            return staged_data
        except Exception:
            pass

    if os.path.exists(master_path):
        try:
            with open(master_path, "r", encoding="utf-8") as f:
                full_reg = json.load(f)
            if novel_slug in full_reg:
                staged_data = full_reg[novel_slug]
                print(f"[Registry] [✓] Extracted '{novel_slug}' block ({len(staged_data.get('characters', {}))} characters) from '{master_path}'.", flush=True)
        except Exception as e:
            print(f"[Registry Warning] Error reading master registry: {e}", flush=True)

    if not staged_data.get("characters"):
        print(f"[Registry] Seeding initial fallback characters for '{novel_slug}'.", flush=True)
        staged_data["characters"] = {k: v for k, v in FALLBACK_BASE_CHARACTERS.items()}

    os.makedirs(os.path.dirname(stage_file), exist_ok=True)
    with open(stage_file, "w", encoding="utf-8") as f:
        json.dump(staged_data, f, indent=2, ensure_ascii=False)

    return staged_data

def sync_new_characters_to_staging(stage_file: str, segments: list, mc_aliases: list = None):
    """
    Step 2: Analyzes parsed lines for newly identified characters and writes
    them immediately to the session staging file for subsequent chapter continuity.
    """
    if not os.path.exists(stage_file):
        return

    try:
        with open(stage_file, "r", encoding="utf-8") as f:
            staged_data = json.load(f)
    except Exception:
        return

    chars = staged_data.setdefault("characters", {})
    alias_lookup = {}
    for c_key, c_val in chars.items():
        alias_lookup[c_key.lower()] = c_key
        for alias in c_val.get("aliases", []):
            alias_lookup[alias.lower()] = c_key

    mc_aliases = [a.lower() for a in (mc_aliases or ["mc", "host"])]
    updated = False

    for seg in segments:
        spk = seg.get("speaker", "").strip()
        spk_lower = spk.lower()
        if not spk or spk_lower in ["narrator", "narrator:"] or spk_lower in alias_lookup:
            continue

        gender = seg.get("gender", "Male")
        voice = seg.get("voice", "en-US-GuyNeural")
        pitch = seg.get("pitch", "+0Hz")
        rate = seg.get("rate", "+5%")
        line_type = seg.get("line_type", "Dialogue")
        role = "system" if line_type == "System" else ("mc" if spk_lower in mc_aliases else "supporting_character")

        chars[spk_lower] = {
            "gender": gender,
            "role": role,
            "voice": voice,
            "pitch": pitch,
            "rate": rate,
            "aliases": [spk_lower]
        }
        alias_lookup[spk_lower] = spk_lower
        updated = True
        print(f"[Registry Learn] [★] Staged New Character: '{spk}' | Gender: {gender} | Voice: {voice}", flush=True)

    if updated:
        with open(stage_file, "w", encoding="utf-8") as f:
            json.dump(staged_data, f, indent=2, ensure_ascii=False)

def finalize_and_merge_master_registry(novel_slug: str, stage_file: str):
    """
    Step 3: Merges all newly discovered characters from session_entities_staged.json
    back into the master registry file on disk after video generation is complete.
    """
    master_path = get_active_master_registry_path()
    if not os.path.exists(stage_file):
        return

    try:
        with open(stage_file, "r", encoding="utf-8") as f:
            staged_data = json.load(f)
    except Exception:
        return

    staged_chars = staged_data.get("characters", {})
    if not staged_chars:
        return

    master_data = {}
    if os.path.exists(master_path):
        try:
            with open(master_path, "r", encoding="utf-8") as f:
                master_data = json.load(f)
        except Exception:
            master_data = {}

    novel_master = master_data.setdefault(novel_slug, {"characters": {}, "vocatives": {}})
    master_chars = novel_master.setdefault("characters", {})

    merged_count = 0
    for c_key, c_val in staged_chars.items():
        if c_key.lower() not in [k.lower() for k in master_chars.keys()]:
            master_chars[c_key] = c_val
            merged_count += 1
            print(f"[Registry Finalize] Merging '{c_key.title()}' ({c_val.get('gender')}) -> '{master_path}'.", flush=True)

    if merged_count > 0:
        try:
            with open(master_path, "w", encoding="utf-8") as f:
                json.dump(master_data, f, indent=2, ensure_ascii=False)
            print(f"[Registry Finalize] [✓] Successfully merged {merged_count} new characters into '{master_path}'!", flush=True)
        except Exception as e:
            print(f"[Registry Finalize Error] Failed writing to '{master_path}': {e}", flush=True)
    else:
        print(f"[Registry Finalize] Master registry '{master_path}' is up to date.", flush=True)
