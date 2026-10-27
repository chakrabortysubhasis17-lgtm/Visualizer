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
gemini_key = creds.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", "")
cf_id = creds.get("cloudflare_account_id") or os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
cf_token = creds.get("cloudflare_api_token") or os.environ.get("CLOUDFLARE_API_TOKEN", "")

BUILD_DIR = "build_immortal_dragon_kingdom_201_228"

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,
    "novel_slug": "lord-start-in-exile-and-build-an-immortal-dragon-kingdom",
    "start_url": "https://mtl-novel.com/novel/lord-start-in-exile-and-build-an-immortal-dragon-kingdom/chapter-202-202/",
    "start_chapter": 201,
    "end_chapter": 228,
    "default_topic": "Lord Start in Exile / Immortal Dragon Kingdom / Kingdom Building / LitRPG",
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "intro_hook": "From exile to sovereign rule, the Immortal Dragon Kingdom rises to conquer the continent.",
    "build_dir": BUILD_DIR,
    "final_audio": "output_immortal_dragon_kingdom_201_228.mp3",
    "final_video": "final_immortal_dragon_kingdom_201_228.mp4",
    "cover_image": "cover_immortal_dragon_kingdom_201_228.jpg",
    "timestamps_file": "youtube_timestamps_immortal_dragon_kingdom_201_228.txt",
    "subtitles_file": "subtitles_immortal_dragon_kingdom_201_228.srt",
    "payload_file": "youtube_upload_payload_immortal_dragon_kingdom_201_228.json",
    "branding_assets": {"logo": "logo.png", "subscribe": "subscribe.png", "like": "like.png", "voice": "voice.png"},
    "enable_subtitles": True,
    "subtitle_languages": ["de", "es", "pt", "ru", "hi", "bn", "ms", "tl", "fr", "fi", "ja", "pl", "ur", "ar", "vi"],
    "video_title": "Immortal Dragon Kingdom | Ch 201 - 228 Full Audio Novel Marathon | Kingdom Expansion",
    "privacy_status": "unlisted",
    "tags": ["Immortal Dragon Kingdom", "Kingdom Building Audiobook", "LitRPG", "Audiobook Marathon", "Being A Bong"],
    "desc_header": "Welcome back to Being a Bong!\n\nExperience chapters 201 to 228 of 'Lord: Start in Exile and Build an Immortal Dragon Kingdom'.\n\nTIMESTAMPS:\n",
    "desc_footer": "\n#ImmortalDragonKingdom #KingdomBuilding #AudiobookMarathon #BeingABong",
    "blocks": [
        {"index": 1, "range": (201, 210), "title": ["EXILE WALLS", "DRAGON AWAKENING"], "fallback_color": (20, 20, 25), "prompt": "Massive ancient stone fortress surrounded by mystical dragon banners under a starlit sky."},
        {"index": 2, "range": (211, 219), "title": ["EMPIRE FORGE", "LEGION MARCH"], "fallback_color": (25, 20, 15), "prompt": "Grand medieval military encampment with disciplined legions and glowing armaments."},
        {"index": 3, "range": (220, 228), "title": ["DRAGON THRONE", "SOVEREIGN DOMINION"], "fallback_color": (15, 20, 30), "prompt": "Majestic golden throne hall with soaring dragon statues and divine imperial light."}
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))