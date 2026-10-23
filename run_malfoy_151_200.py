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

# Credential resolution with multi-key/account fallback matching test.py
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
                
                # Check for corrupt dummy text or fallback-only staging
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

BUILD_DIR = "build_hp_miss_malfoy_151_200"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "hp-miss-malfoy",
    "start_url": "https://mtl-novel.com/novel/hp-miss-malfoy-doesnt-want-to-romance-her-parents-generation/chapter-151-comfortable-company/",
    "start_chapter": 151,
    "end_chapter": 200,
    "default_topic": "Hogwarts / Pureblood Society / Slytherin",

    # Concurrency Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-GuyNeural",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_hp_miss_malfoy_151_200.mp3",
    "final_video": "final_hp_miss_malfoy_151_200.mp4",
    "cover_image": "cover_hp_miss_malfoy_151_200.jpg",
    "timestamps_file": "youtube_timestamps_hp_miss_malfoy_151_200.txt",
    "subtitles_file": "subtitles_hp_miss_malfoy_151_200.srt",
    "payload_file": "youtube_upload_payload_hp_miss_malfoy_151_200.json",

    # Branding Overlay Assets (Matched to verified root assets)
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
    "video_title": "HP: Miss Malfoy Doesn't Want to Romance Her Parents' Generation | Ch 151 - 200 Audio Novel Marathon",
    "privacy_status": "unlisted",
    "tags": [
        "HP Miss Malfoy", "Harry Potter Fanfiction", "Miss Malfoy Audiobook",
        "Slytherin Audiobook", "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the uninterrupted 50-chapter audio novel marathon of 'HP: Miss Malfoy Doesn't Want to Romance Her Parents' Generation' (Chapters 151 to 200).\n\n"
        "Follow Manxi Malfoy navigating Hogwarts, late-night letters to Regulus Black, Quidditch matches, and pureblood society tensions.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic mastering, vocal presence).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Animated Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited, dramatized fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#HPMissMalfoy #HarryPotterAudiobook #MissMalfoy #WebNovel #AudiobookMarathon #BeingABong"
    ),

    # 5 Arc Visual Blocks for Chapters 151 to 200 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (151, 160),
            "title": ["TROPHY ROOM & LETTERS", "REGULUS'S REPLY"],
            "fallback_color": (20, 35, 25),
            "prompt": (
                "Cinematic fantasy portrait of a young aristocratic blonde witch in an elegant Slytherin robe writing a letter with a quill by candlelight, "
                "surrounded by silver trophies and old Hogwarts architecture. Moody atmospheric shadows, rich green and emerald tones, intricate details, 4K rendering."
            )
        },
        {
            "index": 2, "range": (161, 170),
            "title": ["QUIDDITCH RIVALRY", "AUTUMN AT HOGWARTS"],
            "fallback_color": (30, 20, 40),
            "prompt": (
                "Cinematic wide angle fantasy scene of Hogwarts Quidditch pitch in autumn, overcast misty Scottish sky, soaring broomsticks in the distance, "
                "banners fluttering in emerald green and sapphire blue, crisp golden foliage, high fantasy atmosphere, photorealistic lighting."
            )
        },
        {
            "index": 3, "range": (171, 180),
            "title": ["THE SLYTHERIN COMMON ROOM", "WHISPERS IN THE DARK"],
            "fallback_color": (15, 30, 25),
            "prompt": (
                "Cinematic interior shot of the Slytherin underground common room beneath the Black Lake, greenish subterranean ambient light through tall arched windows, "
                "crackling fireplace, plush leather armchairs, silver serpents carved into dark stone, mystery and noble ambiance."
            )
        },
        {
            "index": 4, "range": (181, 190),
            "title": ["SECRET CORRIDORS", "POTIONS & SCHEMES"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic fantasy portrait of a teenage blonde pureblood witch brewing an intricate shimmering potion in a stone dungeon laboratory, "
                "soft magical glowing vapors in violet and silver, bubbling cauldrons, crystal vials, dramatic rim lighting, highly detailed."
            )
        },
        {
            "index": 5, "range": (191, 200),
            "title": ["WINTER WINDS", "THE MARAUDERS' ERA"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic exterior landscape of Hogwarts castle covered in early winter frost and snow, dramatic gothic towers against twilight skies, "
                "glowing warm orange lights from courtyard windows, cold majestic atmosphere, cinematic 3D fantasy style, ultra-detailed."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
