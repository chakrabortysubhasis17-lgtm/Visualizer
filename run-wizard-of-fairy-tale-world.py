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


BUILD_DIR = "build_wizard_of_fairy_tale_world_001_050"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "the-wizard-of-fairy-tale-world",
    "start_url": "https://freewebnovel.com/novel/the-wizard-of-fairy-tale-world/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "The Wizard of Fairy Tale World / Fantasy / Magic / Grimm Fairy Tales / Wizard Awakening",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook (Since start_chapter == 1, pipeline prefixes new series debut)
    "intro_hook": "We step into a magical realm where dark fantasy twists classic fairy tales, and a young wizard begins his ascent to uncover mystical secrets.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_wizard_of_fairy_tale_world_001_050.mp3",
    "final_video": "final_wizard_of_fairy_tale_world_001_050.mp4",
    "cover_image": "cover_wizard_of_fairy_tale_world_001_050.jpg",
    "timestamps_file": "youtube_timestamps_wizard_of_fairy_tale_world_001_050.txt",
    "subtitles_file": "subtitles_wizard_of_fairy_tale_world_001_050.srt",
    "payload_file": "youtube_upload_payload_wizard_of_fairy_tale_world_001_050.json",

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
    "video_title": "The Wizard of Fairy Tale World | Ch 1 - 50 Full Audio Novel Marathon | Awakening Arc",
    "privacy_status": "unlisted",
    "tags": [
        "The Wizard of Fairy Tale World", "Fairy Tale World Audiobook", "Wizard Audiobook",
        "Dark Fantasy", "Progression Fantasy", "Magic System", "Audiobook Marathon",
        "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to Being a Bong!\n\n"
        "Experience the complete 50-chapter audio novel marathon of 'The Wizard of Fairy Tale World' (Chapters 1 to 50).\n\n"
        "Step into a mesmerizing dark fantasy universe where familiar fairy tales hide dangerous arcane secrets, ancient curses, "
        "and mystical laws. Follow our protagonist as he navigates enchanted forests, awakens magical talents, and begins his legendary journey "
        "as a wizard in a world where folklore becomes reality.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "🎙️ NARRATION: en-US-ChristopherNeural (Deep Cinematic Baritone).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited, dramatized fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#WizardOfFairyTaleWorld #DarkFantasy #MagicAudiobook #ProgressionFantasy #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 1 to 50 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (1, 10),
            "title": ["AWAKENING IN THE WOODS", "FIRST SPELLCASTING"],
            "fallback_color": (20, 25, 20),
            "prompt": (
                "Cinematic dark fantasy forest at twilight, gnarled ancient trees with glowing moss and floating wisps of blue light, "
                "a young apprentice wizard in hooded robes holding an ancient glowing tome, casting a spark of blue magical flame from his fingertips, "
                "volumetric mist, mysterious and enchanting 4K rendering."
            )
        },
        {
            "index": 2, "range": (11, 20),
            "title": ["MYSTERIOUS VILLAGE", "CURSED FOLKLORE"],
            "fallback_color": (25, 20, 15),
            "prompt": (
                "Cinematic eerie medieval village under a pale crescent moon, thatched-roof cottages shrouded in thick creeping fog, "
                "lantern light casting long shadows across cobbled pathways, mysterious silhouettes peering from windows, dark fantasy atmosphere."
            )
        },
        {
            "index": 3, "range": (21, 30),
            "title": ["WITCH'S TOWER", "ARCANE SECRETS"],
            "fallback_color": (15, 15, 25),
            "prompt": (
                "Cinematic gothic stone tower perched atop a jagged cliffside overlooking a misty valley, tall arched windows glowing with purple arcane light, "
                "shelves lined with bubbling potions, antique globes, and mystical artifacts, detailed interior lighting."
            )
        },
        {
            "index": 4, "range": (31, 40),
            "title": ["ENCHANTED BEASTS", "FOREST ENCOUNTER"],
            "fallback_color": (20, 15, 30),
            "prompt": (
                "Cinematic high-tension encounter inside a deep enchanted thicket, a towering shadow wolf with glowing amber eyes and crystalline fur "
                "confronting the young wizard who summons a swirling barrier of golden magical runes, dynamic action lighting, 4K composition."
            )
        },
        {
            "index": 5, "range": (41, 50),
            "title": ["TOWARDS THE ACADEMY", "RISING WIZARD"],
            "fallback_color": (25, 25, 35),
            "prompt": (
                "Cinematic sweeping wide shot of a grand majestic wizard academy carved directly into glowing mountain crystals at sunrise, "
                "soaring spires piercing golden cloud layers, flocks of magical magical birds circling overhead, inspiring epic atmosphere."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
