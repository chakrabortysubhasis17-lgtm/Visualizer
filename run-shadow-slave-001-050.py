import os
import json
import asyncio
from pipeline_orchestrator import run_audiobook_pipeline

CREDENTIALS_FILE = "api_credentials.json"

def load_credentials(file_path: str = CREDENTIALS_FILE) -> dict:
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Warning] Failed to parse '{file_path}': {e}", flush=True)
    return {}

creds = load_credentials()

# Credential resolution with multi-key/account fallback
gemini_key = creds.get("gemini_api_key")
if not gemini_key and creds.get("gemini_api_keys"):
    for k in creds["gemini_api_keys"]:
        if k and not k.startswith("PASTE_") and not k.startswith("YOUR_"):
            gemini_key = k
            break
gemini_key = gemini_key or os.environ.get("GEMINI_API_KEY", "")

cf_id = creds.get("cloudflare_account_id")
cf_token = creds.get("cloudflare_api_token")
if (not cf_id or not cf_token) and creds.get("cloudflare_accounts"):
    for acc in creds["cloudflare_accounts"]:
        if isinstance(acc, dict) and acc.get("account_id") and not acc.get("account_id").startswith("PASTE_"):
            cf_id = cf_id or acc.get("account_id")
            cf_token = cf_token or acc.get("api_token")
            break
cf_id = cf_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
cf_token = cf_token or os.environ.get("CLOUDFLARE_API_TOKEN", "")

def purge_corrupt_or_fallback_cache(build_dir: str):
    """
    Purges placeholder files, corrupt manifests, and rule-based fallback files
    staged during earlier runs without Gemini credentials.
    """
    if not os.path.exists(build_dir):
        return
    removed = 0
    for fname in os.listdir(build_dir):
        if fname.startswith("ch_") and fname.endswith("_staged.json"):
            fpath = os.path.join(build_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                rows = data.get("rows", [])
                
                is_dummy = len(rows) < 8 or any("Exposition details continue" in r.get("text", "") for r in rows)
                is_fallback_only = not any(r.get("speaker") not in ["Narrator", "Mc", "System"] for r in rows)
                
                if is_dummy or is_fallback_only:
                    os.remove(fpath)
                    removed += 1
            except Exception:
                try:
                    os.remove(fpath)
                    removed += 1
                except OSError:
                    pass
    if removed > 0:
        print(f"[Pre-Flight Cleanup] [OK] Purged {removed} invalid/fallback staged files. Gemini Director will parse cleanly.", flush=True)

BUILD_DIR = "build_shadow_slave_001_051"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "shadow-slave",
    "start_url": "https://freewebnovel.com/novel/shadow-slave/chapter-1",
    "start_chapter": 1,
    "end_chapter": 51,
    "default_topic": "Nightmare Spell / Shadow Slave / Divine Aspect",

    # Concurrency Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-GuyNeural",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_shadow_slave_001_051.mp3",
    "final_video": "final_shadow_slave_001_051.mp4",
    "cover_image": "cover_shadow_slave_001_051.jpg",
    "timestamps_file": "youtube_timestamps_shadow_slave_001_051.txt",
    "subtitles_file": "subtitles_shadow_slave_001_051.srt",
    "payload_file": "youtube_upload_payload_shadow_slave_001_051.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # Post-Render Multilingual Subtitle Engine (15 Languages to build/subtitles/)
    "enable_subtitles": True,
    "subtitle_languages": [
        "de", "es", "pt", "ru", "hi", "bn", "ms", "tl", "fr", "fi", "ja", "pl", "ur", "ar", "vi"
    ],

    # YouTube Metadata
    "video_title": "Shadow Slave | Ch 1 - 51 Full Audio Novel Marathon | The First Nightmare",
    "privacy_status": "unlisted",
    "tags": [
        "Shadow Slave", "Shadow Slave Audiobook", "Sunny", "Lost from Light",
        "Nightmare Spell", "Forgotten Shore", "Divine Aspect", "Dark Fantasy Audiobook",
        "Progression Fantasy", "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to Being a Bong!\n\n"
        "Experience the complete 51-chapter audio novel marathon of 'Shadow Slave' (Chapters 1 to 51) — The First Nightmare Arc.\n\n"
        "Follow Sunny, an impoverished slum kid chosen by the Nightmare Spell, as he survives the treacherous slave caravan in the frozen mountains, "
        "faces the Mountain King, awakens his divine shadow aspect [Shadow Slave], and enters the nightmare world of the Forgotten Shore.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited, dramatized fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#ShadowSlave #Sunny #NightmareSpell #DarkFantasy #ProgressionFantasy #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 1 to 51
    "blocks": [
        {
            "index": 1, "range": (1, 10),
            "title": ["THE NIGHTMARE SPELL", "THE FROZEN PASS"],
            "fallback_color": (15, 20, 30),
            "prompt": (
                "Cinematic dark fantasy scene of a frail, dark-haired teenage boy in ragged clothes and iron collar chains, "
                "standing amidst a brutal blizzard on a narrow mountain ridge. A giant shadowy monstrous silhouette lurks among the swirling snow drifts, "
                "cold blue rim lighting, icy stone cliffs, dramatic atmospheric volumetric fog, 4K rendering."
            )
        },
        {
            "index": 2, "range": (11, 20),
            "title": ["SHRINE OF CARNAGE", "THE MOUNTAIN KING"],
            "fallback_color": (25, 10, 15),
            "prompt": (
                "Cinematic high-tension scene inside an ancient ruined stone mountain shrine half-buried in ice and snow, "
                "a colossal terrifying multi-limbed tyrant beast with glowing pale eyes hunting through broken stone pillars, "
                "a clever young slave hiding beneath shadows clutching a bloody iron shackle, dramatic high-contrast chiaroscuro lighting."
            )
        },
        {
            "index": 3, "range": (21, 30),
            "title": ["DIVINE ASPECT", "SHADOW SLAVE AWAKENING"],
            "fallback_color": (10, 10, 25),
            "prompt": (
                "Cinematic dark fantasy portrait of a pale young man surrounded by writhing, living shadows that rise from the floor into sentient silhouettes, "
                "ethereal black mist crackling with dark violet runes, celestial appraisal script glowing faintly in the air, moody atmospheric lighting, photorealistic textures."
            )
        },
        {
            "index": 4, "range": (31, 40),
            "title": ["THE ACADEMY", "DREAM REALM CALLING"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic modern sci-fi fantasy scene of a grand futuristic Awakened training colosseum, young elite combatants in sleek battle suits "
                "sparring under holographic simulation rings, a slender silver-haired girl with radiant white flame aura commanding attention, sharp detailed 4K."
            )
        },
        {
            "index": 5, "range": (41, 51),
            "title": ["FORGOTTEN SHORE", "ASHEN LABYRINTH"],
            "fallback_color": (30, 15, 20),
            "prompt": (
                "Cinematic wide angle shot of a vast apocalyptic alien coastline beneath an eerie eclipse, colossal shattered white marble statues "
                "drowning in dark crimson ocean waves, ancient labyrinth ruins stretching across an endless expanse, towering shadows moving beneath the crimson water, ultra-detailed."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
