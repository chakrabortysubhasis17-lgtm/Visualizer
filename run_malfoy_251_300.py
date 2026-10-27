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


BUILD_DIR = "build_miss_malfoy_251_300"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "hp-miss-malfoy-doesnt-want-to-romance-her-parents-generation",
    "start_url": "https://mtl-novel.com/novel/hp-miss-malfoy-doesnt-want-to-romance-her-parents-generation/chapter-251-the-wolf-and-the-dog-in-the-shrieking-shack/",
    "start_chapter": 251,
    "end_chapter": 300,
    "default_topic": "HP: Miss Malfoy Doesn't Want to Romance Her Parents' Generation / Harry Potter Fanfiction / Magic / Slytherin / Marauders Era",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook
    "intro_hook": "Shadows deepen within the Shrieking Shack as long-buried secrets, past loyalties, and the perilous fate of the Malfoy heiress collide under the full moon.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_miss_malfoy_251_300.mp3",
    "final_video": "final_miss_malfoy_251_300.mp4",
    "cover_image": "cover_miss_malfoy_251_300.jpg",
    "timestamps_file": "youtube_timestamps_miss_malfoy_251_300.txt",
    "subtitles_file": "subtitles_miss_malfoy_251_300.srt",
    "payload_file": "youtube_upload_payload_miss_malfoy_251_300.json",

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
    "video_title": "Miss Malfoy Doesn't Want to Romance Her Parents' Generation | Ch 251 - 300 Full Audio Novel Marathon",
    "privacy_status": "unlisted",
    "tags": [
        "Miss Malfoy", "Miss Malfoy Doesn't Want to Romance Her Parents' Generation",
        "Harry Potter Fanfiction", "Miss Malfoy Audiobook", "Slytherin", "Marauders Era",
        "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience chapters 251 to 300 of 'HP: Miss Malfoy Doesn't Want to Romance Her Parents' Generation'.\n\n"
        "Step into the wizarding world as the confrontation in the Shrieking Shack reaches its boiling point, "
        "weaving intricate pureblood politics, ancient magic, and the divergent destinies of Hogwarts.\n\n"
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
        "#MissMalfoy #HarryPotterFanfiction #Slytherin #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Arc Visual Blocks for Chapters 251 to 300
    "blocks": [
        {
            "index": 1, "range": (251, 262),
            "title": ["SHRIEKING SHACK", "WOLF AND DOG"],
            "fallback_color": (15, 18, 25),
            "prompt": (
                "Cinematic moody interior of a dilapidated abandoned wooden house at night, moonlight piercing through dusty broken floorboards, "
                "an elegant platinum-blonde young witch in a dark emerald-trimmed robe holding a glowing magic wand, tense gothic mystery, 4K masterpiece."
            )
        },
        {
            "index": 2, "range": (263, 275),
            "title": ["SLYTHERIN DUNGEONS", "PUREBLOOD INTRIGUE"],
            "fallback_color": (10, 25, 20),
            "prompt": (
                "Cinematic underground gothic castle common room beneath a lake, green-tinted underwater ambient lighting shining through massive arched glass, "
                "ornate black leather armchairs, glowing potions shelves, emerald serpent banners, photorealistic 4K."
            )
        },
        {
            "index": 3, "range": (276, 288),
            "title": ["MARAUDERS ECHO", "TIME AND FATE"],
            "fallback_color": (25, 20, 15),
            "prompt": (
                "Cinematic misty enchanted forest beneath a full silvery moon, glowing silvery patronus energy spiraling between ancient twisted trees, "
                "subtle shadows of a black dog and a werewolf in the mist, atmospheric magical realism, 4K."
            )
        },
        {
            "index": 4, "range": (289, 300),
            "title": ["ASTRONOMY TOWER", "CONVERGING DESTINIES"],
            "fallback_color": (18, 15, 28),
            "prompt": (
                "Cinematic high gothic castle tower balcony overlooking rolling misty Scottish highlands at twilight, star-filled nebula sky, "
                "swirling magical sparks floating in the cold night air, stunning architectural fantasy render, 4K."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
