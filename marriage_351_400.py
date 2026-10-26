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

BUILD_DIR = "build_national_fate_351_400"

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,
    "novel_slug": "national-fate-marriage-the-elf-queen-is-pregnant-at-the-start",
    "start_url": "https://mtl-novel.com/novel/national-fate-marriage-the-elf-queen-is-pregnant-at-the-start/chapter-351-in-front-of-the-valkyries-you-dont-even-qualify-to-self-destruct/",
    "start_chapter": 351,
    "end_chapter": 400,
    "default_topic": "National Fate Marriage / LitRPG / Elf Queen / System Progression",
    "batch_size": 5,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "intro_hook": "As the national fate match deepens, Xiao Haoyan faces the Valkyries and shatters divine opposition with absolute power.",
    "build_dir": BUILD_DIR,
    "final_audio": "output_national_fate_351_400.mp3",
    "final_video": "final_national_fate_351_400.mp4",
    "cover_image": "cover_national_fate_351_400.jpg",
    "timestamps_file": "youtube_timestamps_national_fate_351_400.txt",
    "subtitles_file": "subtitles_national_fate_351_400.srt",
    "payload_file": "youtube_upload_payload_national_fate_351_400.json",
    "branding_assets": {"logo": "logo.png", "subscribe": "subscribe.png", "like": "like.png", "voice": "voice.png"},
    "enable_subtitles": True,
    "subtitle_languages": ["de", "es", "pt", "ru", "hi", "bn", "ms", "tl", "fr", "fi", "ja", "pl", "ur", "ar", "vi"],
    "video_title": "National Fate Marriage: Elf Queen | Ch 351 - 400 Full Audio Novel Marathon | Valkyrie Clash",
    "privacy_status": "unlisted",
    "tags": ["National Fate Marriage", "LitRPG Audiobook", "Elf Queen", "Audiobook Marathon", "Being A Bong"],
    "desc_header": "Welcome back to Being a Bong!\n\nExperience chapters 351 to 400 of 'National Fate: Marriage, the Elf Queen is Pregnant at the Start'.\n\nTIMESTAMPS:\n",
    "desc_footer": "\n#NationalFateMarriage #LitRPG #AudiobookMarathon #BeingABong",
    "blocks": [
        {"index": 1, "range": (351, 366), "title": ["VALKYRIE WRATH", "DIVINE TRIAL"], "fallback_color": (20, 20, 25), "prompt": "Epic fantasy battlefield with angelic valkyries descending under a dark golden sky."},
        {"index": 2, "range": (367, 383), "title": ["ELVEN DOMINION", "QUEEN'S BLESSING"], "fallback_color": (25, 20, 15), "prompt": "Magical elven forest sanctuary glowing with ethereal light and ancient runes."},
        {"index": 3, "range": (384, 400), "title": ["SHATTERED GODS", "ASCENDANT REALM"], "fallback_color": (15, 20, 30), "prompt": "Colossal divine citadel shattering as stellar arrows pierce through the heavens."}
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
