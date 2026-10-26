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

BUILD_DIR = "build_investing_wives_251_287"

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,
    "novel_slug": "investing-in-my-three-crippled-wives-get-10000x-times-return",
    "start_url": "https://freewebnovel.com/novel/investing-in-my-three-crippled-wives-get-10000x-times-return/chapter-251",
    "start_chapter": 251,
    "end_chapter": 287,
    "default_topic": "Investing In My Three Crippled Wives / Fantasy / LitRPG / 10000x Returns",
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "intro_hook": "The investment returns multiply as the crippled wives unlock their true power and the empire expands exponentially.",
    "build_dir": BUILD_DIR,
    "final_audio": "output_investing_wives_251_287.mp3",
    "final_video": "final_investing_wives_251_287.mp4",
    "cover_image": "cover_investing_wives_251_287.jpg",
    "timestamps_file": "youtube_timestamps_investing_wives_251_287.txt",
    "subtitles_file": "subtitles_investing_wives_251_287.srt",
    "payload_file": "youtube_upload_payload_investing_wives_251_287.json",
    "branding_assets": {"logo": "logo.png", "subscribe": "subscribe.png", "like": "like.png", "voice": "voice.png"},
    "enable_subtitles": True,
    "subtitle_languages": ["de", "es", "pt", "ru", "hi", "bn", "ms", "tl", "fr", "fi", "ja", "pl", "ur", "ar", "vi"],
    "video_title": "Investing In My Three Crippled Wives | Ch 251 - 287 Full Audio Novel Marathon | 10000x Returns",
    "privacy_status": "unlisted",
    "tags": ["Investing In My Three Crippled Wives", "LitRPG Audiobook", "10000x Return", "Audiobook Marathon", "Being A Bong"],
    "desc_header": "Welcome back to Being a Bong!\n\nExperience chapters 251 to 287 of 'Investing In My Three Crippled Wives Get 10,000x Times Return'.\n\nTIMESTAMPS:\n",
    "desc_footer": "\n#InvestingInMyThreeCrippledWives #LitRPG #AudiobookMarathon #BeingABong",
    "blocks": [
        {"index": 1, "range": (251, 263), "title": ["MULTIPLICATION", "DIVINE INVESTMENT"], "fallback_color": (20, 20, 25), "prompt": "Mystical treasury filled with glowing golden artifacts and divine investment ledgers."},
        {"index": 2, "range": (264, 275), "title": ["WIVES ASCENT", "POWER UNLEASHED"], "fallback_color": (25, 20, 15), "prompt": "Powerful fantasy consorts manifesting overwhelming elemental power in a grand palace."},
        {"index": 3, "range": (276, 287), "title": ["SOVEREIGN DOMINION", "SUPREME RETURN"], "fallback_color": (15, 20, 30), "prompt": "Majestic celestial throne overlooking an endless expanse of conquered realms."}
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))