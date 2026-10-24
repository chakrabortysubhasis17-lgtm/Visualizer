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


BUILD_DIR = "build_daily_life_dungeon_201_250"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "daily-life-starting-from-the-dungeon",
    "start_url": "https://mtl-novel.com/novel/daily-life-starting-from-the-dungeon/chapter-199-secret-planning/",
    "start_chapter": 201,
    "end_chapter": 250,
    "default_topic": "Daily Life Starting From The Dungeon / Urban Fantasy / Dungeon Management / Secret Planning",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook (Since start_chapter > 1, pipeline prefixes continuation intro)
    "intro_hook": "We rejoin the underground management as secret schemes unfold, dungeon boundaries expand, and new challenges arise for our enterprising master.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_daily_life_dungeon_201_250.mp3",
    "final_video": "final_daily_life_dungeon_201_250.mp4",
    "cover_image": "cover_daily_life_dungeon_201_250.jpg",
    "timestamps_file": "youtube_timestamps_daily_life_dungeon_201_250.txt",
    "subtitles_file": "subtitles_daily_life_dungeon_201_250.srt",
    "payload_file": "youtube_upload_payload_daily_life_dungeon_201_250.json",

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
    "video_title": "Daily Life Starting From The Dungeon | Ch 201 - 250 Full Audio Novel Marathon | Secret Planning Arc",
    "privacy_status": "unlisted",
    "tags": [
        "Daily Life Starting From The Dungeon", "Dungeon Management Audiobook", "Urban Fantasy",
        "LitRPG Audiobook", "System Audiobook", "Progression Fantasy", "Audiobook Marathon",
        "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the complete 50-chapter audio novel marathon of 'Daily Life Starting From The Dungeon' (Chapters 201 to 250) — the Secret Planning Arc.\n\n"
        "As confidential plots thicken and external factions begin to take notice of the mysterious underground domain, our dungeon master "
        "must navigate intricate schemes, upgrade defenses, and balance supernatural daily life with high-stakes expansion. "
        "Uncover hidden agendas, magical upgrades, and unexpected twists in this thrilling marathon.\n\n"
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
        "#DailyLifeStartingFromTheDungeon #DungeonMaster #UrbanFantasy #LitRPG #ProgressionFantasy #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 201 to 250 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (201, 210),
            "title": ["CONFIDENTIAL SCHEMES", "SHADOWS IN THE DOMAIN"],
            "fallback_color": (20, 20, 30),
            "prompt": (
                "Cinematic urban fantasy interior of a dimly lit subterranean study room filled with glowing magical holographic blueprints "
                "and parchment maps spread over a dark mahogany table, a composed master strategist reviewing data crystals, "
                "ambient blue and amber magical rim lighting, highly detailed 4K resolution."
            )
        },
        {
            "index": 2, "range": (211, 220),
            "title": ["EXPANDING BOUNDARIES", "NEW DUNGEON TIERS"],
            "fallback_color": (15, 25, 25),
            "prompt": (
                "Cinematic fantasy scene of a massive subterranean cavern undergoing mystical structural expansion, "
                "glowing runic veins pulsing across polished black stone walls as magical energy constructs new chamber corridors, "
                "volumetric lighting, awe-inspiring scale."
            )
        },
        {
            "index": 3, "range": (221, 230),
            "title": ["FACTION INTRIGUE", "EXTERNAL THREATS"],
            "fallback_color": (30, 15, 20),
            "prompt": (
                "Cinematic suspenseful composition of mysterious figures observing a glowing magical barrier shielding a hidden entrance "
                "from a rainy modern city alleyway at night, reflections in puddles, dramatic cinematic lighting, moody atmosphere."
            )
        },
        {
            "index": 4, "range": (231, 240),
            "title": ["REINFORCED DEFENSES", "AUTOMATED TRAPS"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic high-detail fantasy action shot inside an intricate dungeon corridor lined with glowing magical traps, "
                "magical turrets, and hovering arcane runes ready to activate, sharp mechanical precision, neon blue and violet energy glows."
            )
        },
        {
            "index": 5, "range": (241, 250),
            "title": ["MASTERY OF THE DOMAIN", "VICTORY OF PLANNING"],
            "fallback_color": (20, 30, 35),
            "prompt": (
                "Cinematic wide angle panoramic view from a high balcony overlooking a bustling, prosperous subterranean sanctuary "
                "where magical constructs and inhabitants coexist peacefully under an artificial starry sky dome, warm radiant lighting, masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
