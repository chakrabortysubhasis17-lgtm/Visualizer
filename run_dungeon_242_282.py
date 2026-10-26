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


BUILD_DIR = "build_daily_life_dungeon_242_282"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "daily-life-starting-from-the-dungeon",
    "start_url": "https://mtl-novel.com/novel/daily-life-starting-from-the-dungeon/chapter-22-ley-lines-and-logistics/",
    "start_chapter": 242,
    "end_chapter": 282,
    "default_topic": "Daily Life Starting from the Dungeon / Dungeon Management / Slice of Life / Monster Logistics / Fantasy Infrastructure",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook (start_chapter > 1 -> continuation recap)
    "intro_hook": "We return to the ever-expanding subterranean domain where dungeon management meets chaotic daily life, monster logistics, and surprising architectural wonders.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_daily_life_dungeon_242_282.mp3",
    "final_video": "final_daily_life_dungeon_242_282.mp4",
    "cover_image": "cover_daily_life_dungeon_242_282.jpg",
    "timestamps_file": "youtube_timestamps_daily_life_dungeon_242_282.txt",
    "subtitles_file": "subtitles_daily_life_dungeon_242_282.srt",
    "payload_file": "youtube_upload_payload_daily_life_dungeon_242_282.json",

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
    "video_title": "Daily Life Starting from the Dungeon | Ch 242 - 282 Full Marathon | Ley Lines & Logistics Arc",
    "privacy_status": "unlisted",
    "tags": [
        "Daily Life Starting from the Dungeon", "Dungeon Management Audiobook",
        "Slice of Life Fantasy", "Monster Logistics", "Progression Fantasy",
        "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the complete audio novel marathon of 'Daily Life Starting from the Dungeon' (Chapters 242 to 282) — the Ley Lines & Logistics Arc.\n\n"
        "Catch up on earlier arcs via the channel playlist!\n\n"
        "As subterranean infrastructure scales up, managing ley lines, monster workforces, and peculiar dungeon guests proves just as thrilling "
        "as any battlefield conquest. Sit back and enjoy another massive block of cozy fantasy management and progression.\n\n"
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
        "#DailyLifeDungeon #DungeonManagement #SliceOfLife #ProgressionFantasy #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Arc Visual Blocks for Chapters 242 to 282
    "blocks": [
        {
            "index": 1, "range": (242, 252),
            "title": ["LEY LINE MAPPING", "SUBTERRANEAN EXPANSION"],
            "fallback_color": (20, 25, 20),
            "prompt": (
                "Cinematic glowing subterranean cavern network lit by pulsing blue and green ley line energy veins running through crystal rock walls, "
                "magical blueprints and logistical charts floating in mid-air, scholarly and adventurous atmosphere, 4K resolution."
            )
        },
        {
            "index": 2, "range": (253, 262),
            "title": ["MONSTER WORKFORCE", "LOGISTICAL CHALLENGES"],
            "fallback_color": (25, 20, 15),
            "prompt": (
                "Cinematic busy underground workshop and trading hub inside a massive cave, quirky fantasy creatures and dungeon denizens working together "
                "efficiently with magical tools and conveyor carts, warm amber torchlight, detailed 3D composition."
            )
        },
        {
            "index": 3, "range": (263, 272),
            "title": ["UNEXPECTED VISITORS", "DUNGEON DIPLOMACY"],
            "fallback_color": (15, 20, 30),
            "prompt": (
                "Cinematic elegant underground chamber with stone archways and glowing lanterns, surface delegates and curious travelers meeting "
                "with the dungeon master over wooden banquet tables, rich atmospheric lighting, depth of field."
            )
        },
        {
            "index": 4, "range": (273, 282),
            "title": ["PROSPEROUS DEPTHS", "NEW HORIZONS"],
            "fallback_color": (25, 25, 35),
            "prompt": (
                "Cinematic breathtaking wide view of a thriving subterranean domain glowing with harmonious crystal light and flourishing magical flora, "
                "peaceful and prosperous fantasy settlement, masterpiece 4K render."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
