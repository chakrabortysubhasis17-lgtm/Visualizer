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

BUILD_DIR = "build_daily_life_dungeon_151_200"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "daily-life-starting-from-the-dungeon",
    "start_url": "https://mtl-novel.com/novel/daily-life-starting-from-the-dungeon/chapter-149-salt-layer/",
    "start_chapter": 151,
    "end_chapter": 200,
    "default_topic": "Dungeon Exploration / Daily Life / Fantasy Adventure",

    # Concurrency Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-GuyNeural",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_daily_life_dungeon_151_200.mp3",
    "final_video": "final_daily_life_dungeon_151_200.mp4",
    "cover_image": "cover_daily_life_dungeon_151_200.jpg",
    "timestamps_file": "youtube_timestamps_daily_life_dungeon_151_200.txt",
    "subtitles_file": "subtitles_daily_life_dungeon_151_200.srt",
    "payload_file": "youtube_upload_payload_daily_life_dungeon_151_200.json",

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
    "video_title": "Daily Life Starting from the Dungeon | Ch 151 - 200 Full Audio Novel Marathon",
    "privacy_status": "unlisted",
    "tags": [
        "Daily Life Starting from the Dungeon", "Dungeon Life Audiobook", "LitRPG Audiobook",
        "Fantasy Audiobook", "Dungeon Crawler", "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Dive into an uninterrupted 50-chapter marathon of 'Daily Life Starting from the Dungeon' (Chapters 151 to 200).\n\n"
        "Explore deeper subterranean floors, subterranean salt formations, cozy campsite cooking, item harvesting, and survival in the labyrinth.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic mastering, vocal presence).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited, dramatized fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#DailyLifeStartingFromTheDungeon #DungeonAudiobook #WebNovel #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 151 to 200 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (151, 160),
            "title": ["THE SALT LAYER", "SUBTERRANEAN EXPEDITION"],
            "fallback_color": (30, 35, 45),
            "prompt": (
                "Cinematic 3D fantasy scene of adventurers traversing a vast subterranean cavern filled with crystalline white salt pillars, "
                "gleaming mineral formations, soft bioluminescent blue cave light casting gentle reflections across mineral rock walls, high detail, 4K rendering."
            )
        },
        {
            "index": 2, "range": (161, 170),
            "title": ["DUNGEON HARVEST", "CAMPFIRE COOKING"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic fantasy shot of a cozy campsite in a dry dungeon alcove, a seasoned adventurer stirring a sizzling pan of freshly harvested dungeon ingredients "
                "over an amber campfire, glowing embers, cooking utensils, warm and cozy atmospheric lighting, detailed textures."
            )
        },
        {
            "index": 3, "range": (171, 180),
            "title": ["MINING & RESOURCE CRAFTING", "LABYRINTH EXPEDITIONS"],
            "fallback_color": (25, 30, 25),
            "prompt": (
                "Cinematic fantasy scene of adventurers inspecting rare glowing ore veins embedded in dark ancient stone walls, holding enchanted lanterns, "
                "backpacks filled with crafting materials and monster drops, intricate underground cave architecture, moody volumetric lighting."
            )
        },
        {
            "index": 4, "range": (181, 190),
            "title": ["BEAST ENCOUNTERS", "TACTICAL ADVANCE"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic wide angle fantasy battle stance in a stone dungeon corridor, party members holding glowing weapons and defensive shields facing down "
                "shadowy dungeon monsters in the distance, spark particles, magical runes along the floor, high fantasy atmosphere."
            )
        },
        {
            "index": 5, "range": (191, 200),
            "title": ["THE DEEPER FLOORS", "SURFACE RETURN"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic wide view of adventurers stepping out of a massive carved dungeon entrance gate into the warm golden light of a medieval border town at sunset, "
                "carrying heavy rucksacks and weathered weapons, relieved expressions, rich atmospheric lighting, ultra-detailed."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
