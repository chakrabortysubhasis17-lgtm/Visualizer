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


BUILD_DIR = "build_wandering_inn_91_100"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "the-wandering-inn",
    "start_url": "https://freewebnovel.com/novel/the-wandering-inn/chapter-95",
    "start_chapter": 91,
    "end_chapter": 100,
    "default_topic": "The Wandering Inn / LitRPG / Fantasy / Slice of Life / Erin Solstice / Innkeeper / Liscor",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 2,
    "parallel_chapters": 2,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook
    "intro_hook": "Transported to a fantasy world governed by leveling and classes, an eccentric young woman claims an abandoned hillside inn and unites humans, drakes, and antinium over warm food, chess, and sudden violence.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_wandering_inn_91_100.mp3",
    "final_video": "final_wandering_inn_91_100.mp4",
    "cover_image": "cover_wandering_inn_91_100.jpg",
    "timestamps_file": "youtube_timestamps_wandering_inn_91_100.txt",
    "subtitles_file": "subtitles_wandering_inn_91_100.srt",
    "payload_file": "youtube_upload_payload_wandering_inn_91_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # Post-Render Multilingual Subtitle Engine (15 Languages)
    "enable_subtitles": True,
    "subtitle_languages": [
        "de", "es", "pt", "ru", "hi", "bn", "ms", "tl", "fr", "fi", "ja", "pl", "ur", "ar", "vi"
    ],

    # YouTube Metadata
    "video_title": "The Wandering Inn | Episodes 91 - 100 Audiobook | Volume 1 Climax & Siege of Liscor",
    "privacy_status": "unlisted",
    "tags": [
        "The Wandering Inn", "Wandering Inn Audiobook", "Erin Solstice", "Ryoka Griffin",
        "Fantasy Audiobook", "LitRPG Audiobook", "Pirateaba", "Audiobook Marathon",
        "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience 'The Wandering Inn' Episodes 91 to 100 — The Convergence at the Floodplains.\n\n"
        "As tensions reach a boiling point between the Drake watch, the Antinium hives, and relentless monster hordes outside Liscor, "
        "Erin Solstice's eccentric inn becomes the final bastion where unlikely allies clash and stand together.\n\n"
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
        "#TheWanderingInn #ErinSolstice #LitRPG #FantasyAudiobook #AudiobookMarathon #BeingABong"
    ),

    # 2 Thematic Visual Arc Blocks for Episodes 91 to 100
    "blocks": [
        {
            "index": 1, "range": (91, 95),
            "title": ["THE INN ON THE HILL", "WARMTH & SHADOWS"],
            "fallback_color": (30, 20, 15),
            "prompt": (
                "Cinematic fantasy stone inn perched on a windswept grassy hill outside a massive walled city, "
                "glowing warm amber light spilling from timber-framed windows into the dusk mist, "
                "drakes and strange armored ant-like humanoids gathering near wooden tables, highly detailed 4K masterpiece."
            )
        },
        {
            "index": 2, "range": (96, 100),
            "title": ["FLOODPLAINS BATTLE", "DEFENDERS OF LISCOR"],
            "fallback_color": (20, 15, 25),
            "prompt": (
                "Cinematic high fantasy battlefield across marshy floodplains beneath stormy twilight clouds, "
                "armored drake warriors with spears and a resolute young human woman wielding an iron ladle surrounded by magical fire sparks, "
                "swirling mist and dramatic volumetric lighting, 4K digital art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
