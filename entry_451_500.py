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


BUILD_DIR = "build_entry_cultivation_451_500"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "entry-cultivation-i-can-copy-entries",
    "start_url": "https://mtl-novel.com/novel/entry-cultivation-i-can-copy-entries/chapter-450-main-body-attains-hunyuan-fruit-good-corpse-will-enter-human-dao-river/",
    "start_chapter": 451,
    "end_chapter": 500,
    "default_topic": "Entry Cultivation / I Can Copy Entries / Xianxia Cultivation / Hunyuan Fruit / Human Dao River / Primordial Dao",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook (start_chapter > 1 -> continuation recap)
    "intro_hook": "We return as the main body attains the supreme Hunyuan Dao Fruit, deploying the Good Corpse into the turbulent River of Humanity to duplicate heaven-defying primordial entries.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_entry_cultivation_451_500.mp3",
    "final_video": "final_entry_cultivation_451_500.mp4",
    "cover_image": "cover_entry_cultivation_451_500.jpg",
    "timestamps_file": "youtube_timestamps_entry_cultivation_451_500.txt",
    "subtitles_file": "subtitles_entry_cultivation_451_500.srt",
    "payload_file": "youtube_upload_payload_entry_cultivation_451_500.json",

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
    "video_title": "Copying Golden Traits: Xianxia Cultivation | Ch 451 - 500 Full Marathon | Hunyuan Fruit Arc",
    "privacy_status": "unlisted",
    "tags": [
        "Copying Golden Traits", "Entry Cultivation", "I Can Copy Entries",
        "Xianxia", "Cultivation Audiobook", "Hunyuan Dao", "Golden Traits",
        "Progression Fantasy", "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the complete 50-chapter audio novel marathon of 'Copying Golden Traits / Entry Cultivation: I Can Copy Entries' (Chapters 451 to 500) — the Hunyuan Fruit Arc.\n\n"
        "Catch up on earlier arcs:\n"
        "• Episode 1 (Ch 1-50): https://www.youtube.com/watch?v=XfVQVn90s4I\n"
        "• Previous Episode (Ch 401-450): https://youtu.be/nowm_nK0quI\n"
        "• Complete Series Playlist: https://www.youtube.com/playlist?list=PLMXchRJ2UDkQ\n\n"
        "Having attained the boundless Hunyuan Dao Fruit, our cultivator projects his incarnations into the cosmic torrent of the Human Dao River. "
        "With the sovereign ability to duplicate golden primordial entries, he manipulates universal destiny, dismantles ancient divine intrigues, "
        "and establishes unprecedented dominion across the immortal realms.\n\n"
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
        "#EntryCultivation #CopyingGoldenTraits #Xianxia #CultivationAudiobook #ProgressionFantasy #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 451 to 500 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (451, 460),
            "title": ["HUNYUAN ASCENSION", "RIVER OF HUMANITY"],
            "fallback_color": (30, 25, 15),
            "prompt": (
                "Cinematic celestial Xianxia landscape, a transcendent immortal sovereign in glowing white and golden robes "
                "standing atop the swirling cosmic River of Humanity composed of countless starry souls and golden destiny threads, "
                "the Hunyuan Dao fruit glowing like a miniature sun behind his head, ethereal volumetric clouds, majestic 4K composition."
            )
        },
        {
            "index": 2, "range": (461, 470),
            "title": ["CORPSE INCARNATION", "ENTRY DUPLICATION"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic high-detail scene of an enlightened Daoist avatar surrounded by rotating translucent golden tablets inscribed with ancient seal script, "
                "extracting radiant purple and crimson destiny entries from the void with two fingers, "
                "rippling space-time fabric, brilliant particle illumination, hyper-detailed rendering."
            )
        },
        {
            "index": 3, "range": (471, 480),
            "title": ["IMMORTAL SCHEMES", "TRIBULATION TIDE"],
            "fallback_color": (15, 20, 30),
            "prompt": (
                "Cinematic high-tension confrontation above jagged jade mountain peaks, massive cosmic thunderstorm churning with purple heavenly tribulation lightning, "
                "an ancient ancestral immortal clad in blackened dragon armor confronting the transcendent protagonist, "
                "immense scale, dramatic cinematic rim lighting, 4K resolution."
            )
        },
        {
            "index": 4, "range": (481, 490),
            "title": ["PRIMORDIAL REFINING", "DAO DOMAIN"],
            "fallback_color": (35, 20, 15),
            "prompt": (
                "Cinematic wide shot inside an infinite primordial void temple, an immense nine-tiered golden cauldron radiating divine fire "
                "refining celestial laws and destiny traits into pure immortal essence, floating lotus blossoms made of golden flame, masterpiece."
            )
        },
        {
            "index": 5, "range": (491, 500),
            "title": ["SOVEREIGN OF ENTRIES", "BOUNDLESS REACH"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic majestic Xianxia climax, the supreme cultivator seated on an ethereal lotus throne high above the multiverse horizon, "
                "infinite golden entry glyphs orbiting his body and stabilizing the cosmic mortal and immortal planes below, "
                "breathtaking celestial lighting, divine harmony, 4K render."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
