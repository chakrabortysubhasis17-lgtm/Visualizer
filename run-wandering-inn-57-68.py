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

BUILD_DIR = "build_the_wandering_inn_57_68"

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,
    "novel_slug": "the-wandering-inn",
    "start_url": "https://freewebnovel.com/novel/the-wandering-inn/chapter-61",
    "start_chapter": 57,
    "end_chapter": 68,
    "default_topic": "The Wandering Inn / LitRPG / High Fantasy / Tavern Management",
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "intro_hook": "We return to the Wandering Inn as new travelers arrive and deeper mysteries unfold across the continent.",
    "build_dir": BUILD_DIR,
    "final_audio": "output_the_wandering_inn_57_68.mp3",
    "final_video": "final_the_wandering_inn_57_68.mp4",
    "cover_image": "cover_the_wandering_inn_57_68.jpg",
    "timestamps_file": "youtube_timestamps_the_wandering_inn_57_68.txt",
    "subtitles_file": "subtitles_the_wandering_inn_57_68.srt",
    "payload_file": "youtube_upload_payload_the_wandering_inn_57_68.json",
    "branding_assets": {"logo": "logo.png", "subscribe": "subscribe.png", "like": "like.png", "voice": "voice.png"},
    "enable_subtitles": True,
    "subtitle_languages": ["de", "es", "pt", "ru", "hi", "bn", "ms", "tl", "fr", "fi", "ja", "pl", "ur", "ar", "vi"],
    "video_title": "The Wandering Inn | Ch 57 - 68 Full Audio Novel Marathon | Crossroads Arc",
    "privacy_status": "unlisted",
    "tags": ["The Wandering Inn", "LitRPG Audiobook", "High Fantasy", "Audiobook Marathon", "Being A Bong"],
    "desc_header": "Welcome back to Being a Bong!\n\nExperience chapters 57 to 68 of 'The Wandering Inn'.\n\nTIMESTAMPS:\n",
    "desc_footer": "\n#TheWanderingInn #LitRPG #AudiobookMarathon #BeingABong",
    "blocks": [
        {"index": 1, "range": (57, 60), "title": ["NEW ARRIVALS", "TAVERN NIGHTS"], "fallback_color": (20, 20, 25), "prompt": "Cozy fantasy tavern interior at night, warm hearth fire, travelers resting."},
        {"index": 2, "range": (61, 64), "title": ["PLAINS WHISPERS", "OUTSIDE THE WALLS"], "fallback_color": (25, 20, 15), "prompt": "Vast green fantasy plains under twilight, mysterious figures moving along a dirt road."},
        {"index": 3, "range": (65, 68), "title": ["HIDDEN DANGERS", "INNKEEPERS RESOLVE"], "fallback_color": (15, 20, 30), "prompt": "Tension inside a rustic fantasy building, glowing magical lantern light, cinematic atmosphere."}
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))