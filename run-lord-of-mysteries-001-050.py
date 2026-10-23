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

BUILD_DIR = "build_lord_of_mysteries_reader_001_051"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "lord-of-mysteries-starting-as-a-reader",
    "start_url": "https://freewebnovel.com/novel/lord-of-mysteries-starting-as-a-reader/chapter-1",
    "start_chapter": 1,
    "end_chapter": 51,
    "default_topic": "Lord of the Mysteries / Reader Pathway / White Tower / Beyonder Mysteries",

    # Concurrency Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-GuyNeural",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_lord_of_mysteries_reader_001_051.mp3",
    "final_video": "final_lord_of_mysteries_reader_001_051.mp4",
    "cover_image": "cover_lord_of_mysteries_reader_001_051.jpg",
    "timestamps_file": "youtube_timestamps_lord_of_mysteries_reader_001_051.txt",
    "subtitles_file": "subtitles_lord_of_mysteries_reader_001_051.srt",
    "payload_file": "youtube_upload_payload_lord_of_mysteries_reader_001_051.json",

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
    "video_title": "Lord of Mysteries: Starting as a Reader | Ch 1 - 51 Full Audio Novel Marathon",
    "privacy_status": "unlisted",
    "tags": [
        "Lord of Mysteries", "Lord of the Mysteries", "Starting as a Reader",
        "Reader Pathway", "White Tower", "Beyonder Audiobook", "Mystery Audiobook",
        "Victorian Fantasy", "Progression Fantasy", "Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to Being a Bong!\n\n"
        "Experience the complete 51-chapter audio novel marathon of 'Lord of Mysteries: Starting as a Reader' (Chapters 1 to 51).\n\n"
        "Step into the smog-shrouded, gaslit streets of Victorian Backlund. Follow a transmigrator who treads the path of the "
        "White Tower—consuming the Sequence 9 Reader potion, deciphering ancient mystical grimoires, navigating secret Beyonder gatherings, "
        "and seeking forbidden truths beneath the crimson moon.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited, dramatized fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#LordOfMysteries #StartingAsAReader #WhiteTower #Beyonder #VictorianFantasy #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 1 to 51
    "blocks": [
        {
            "index": 1, "range": (1, 10),
            "title": ["THE READER POTION", "BACKLUND GASLIGHT"],
            "fallback_color": (20, 25, 30),
            "prompt": (
                "Cinematic 3D Victorian steampunk scene of a young scholar in a tweed vest and trench coat sitting inside a dark, "
                "gaslit study surrounded by towering mahogany bookshelves, holding a glowing azure alchemical vial labeled with mystical brass runes. "
                "Rain beating against antique mullioned windows, thick London smog outside, warm fireplace glow, photorealistic 4K rendering."
            )
        },
        {
            "index": 2, "range": (11, 20),
            "title": ["MYSTICAL INQUIRIES", "SHADOW CONGREGATION"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic dark mystery scene of hooded Beyonder figures gathered around a round wooden table in a hidden subterranean cellar, "
                "tarot cards, brass astrolabes, and ancient parchment scrolls illuminated by flickering candlelight, "
                "thick shadows dancing on damp cobblestone walls, atmospheric moody lighting."
            )
        },
        {
            "index": 3, "range": (21, 30),
            "title": ["STUDENT OF RATIOCINATION", "FORBIDDEN TOMES"],
            "fallback_color": (15, 25, 30),
            "prompt": (
                "Cinematic high fantasy scene inside the grand cathedral archives of the Church of Knowledge, colossal white marble arches "
                "and floating glowing glyphs, a young Beyonder scholar deciphering a massive ancient stone grimoire crackling with crystalline white knowledge light, "
                "volumetric god rays, intricate book engravings, 4K detail."
            )
        },
        {
            "index": 4, "range": (31, 40),
            "title": ["CRIMSON NIGHTMARE", "ELDRITCH ENCOUNTERS"],
            "fallback_color": (30, 10, 20),
            "prompt": (
                "Cinematic eldritch horror scene of a desolate Victorian cobbled alley beneath a colossal crimson full moon, "
                "a young gentleman pointing an engraved revolver at writhing shadowy tentacles and eldritch eyes manifesting from the dark sewers, "
                "dramatic red and charcoal lighting, swirling fog, high tension action."
            )
        },
        {
            "index": 5, "range": (41, 51),
            "title": ["THE WHITE TOWER", "TRUTH TRANSCENDENCE"],
            "fallback_color": (20, 20, 35),
            "prompt": (
                "Cinematic wide angle panorama of the supreme mythical White Tower rising above the astral spirit world, "
                "constellations and mystical cosmic eyes swirling in the deep purple void, an ascending Beyonder looking upward cloaked in pure luminous mana radiance, "
                "epic cosmic mystery scale, ultra-detailed 4K."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
