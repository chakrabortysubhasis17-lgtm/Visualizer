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

def purge_corrupt_cache(build_dir: str):
    """Purges placeholder dummy files from earlier connection dropouts."""
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
                if len(rows) < 8 or any("Exposition details continue" in r.get("text", "") for r in rows):
                    os.remove(fpath)
                    removed += 1
            except Exception:
                try:
                    os.remove(fpath)
                    removed += 1
                except OSError:
                    pass
    if removed > 0:
        print(f"[Pre-Flight Cleanup] [✓] Purged {removed} placeholder cache files to guarantee clean scraping.", flush=True)

BUILD_DIR = "build_catgirls_and_dungeons_201_203_test"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "catgirls-and-dungeons-yuri",
    "start_url": "https://freewebnovel.com/novel/catgirls-and-dungeons-yuri/chapter-201",
    "start_chapter": 201,
    "end_chapter": 203,
    "default_topic": "Catgirls and Dungeons",

    # Concurrency Settings & Narrator Lock
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook (Since start_chapter > 1, pipeline prefixes "Today's journey continues from previous episode.")
    "intro_hook": "We rejoin Felicia and Aris as they settle into their new sanctuary and encounter their surprisingly lifelike homunculi maids.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_catgirls_and_dungeons_201_203_test.mp3",
    "final_video": "final_catgirls_and_dungeons_201_203_test.mp4",
    "cover_image": "cover_catgirls_and_dungeons_201_203_test.jpg",
    "timestamps_file": "youtube_timestamps_catgirls_and_dungeons_201_203_test.txt",
    "subtitles_file": "subtitles_catgirls_and_dungeons_201_203_test.srt",
    "payload_file": "youtube_upload_payload_catgirls_and_dungeons_201_203_test.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "TEST RUN: SURPRISE PRESENT & HOMUNCULUS LAB! [Ch 201-203] | Catgirls and Dungeons Yuri LitRPG",
    "tags": [
        "Catgirls and Dungeons", "Yuri Audiobook", "Progression Fantasy", "Dungeon Crawler",
        "LitRPG Audiobook", "System Audiobook", "Audiobook Test", "Being A Bong"
    ],
    "desc_header": (
        "Testing the new integrated pipeline upgrades with Chapters 201 to 203 of 'Catgirls and Dungeons (Yuri)'!\n\n"
        "From unexpected personal gifts and intimate campsite conversations to discovering eerie alchemical homunculi "
        "in the deeper dungeon layers, this short 3-chapter test verifies end-to-end multi-voice TTS, subtitle alignment, "
        "and video rendering.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 CHAPTER BREAKDOWN:\n"
        "• Ch 201: Surprise Present: Heartwarming Camp Exchange\n"
        "• Ch 202: Homunculi: Uncovering Forgotten Alchemy Labs\n"
        "• Ch 203: Lab Defense: Tactically Clearing Artificial Fiends\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#CatgirlsAndDungeons #YuriAudiobook #LitRPG #ProgressionFantasy #AudiobookTest #BeingABong"
    ),

    # Visual Prompts (1 block per chapter for the 3-chapter test)
    "blocks": [
        {
            "index": 1, "range": (201, 201),
            "title": ["SURPRISE PRESENT", "CAMPFIRE INTIMACY"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D fantasy portrait of a female adventurer presenting a small wrapped gift box with a glowing ribbon to an excited catgirl companion, "
                "surprised adorable expression, glowing amber campfire light illuminating their faces. Cozy dungeon campsite alcove background, "
                "crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (202, 202),
            "title": ["HOMUNCULI DISCOVERY", "ALCHEMICAL CHAMBER"],
            "fallback_color": (15, 25, 40),
            "prompt": (
                "Cinematic 3D fantasy portrait of adventurous explorers entering a dusty subterranean laboratory lined with glowing green glass fluid vats "
                "containing homunculi silhouettes, cautious vigilant expressions, glowing blue lantern light. Ancient stone laboratory background, "
                "crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (203, 203),
            "title": ["LAB DEFENSE", "SYNCHRONIZED STRIKE"],
            "fallback_color": (35, 15, 30),
            "prompt": (
                "Cinematic 3D fantasy portrait of the adventurer and catgirl standing back-to-back with drawn glowing daggers and a primed mana shield, "
                "fierce determined expressions, sparks and magic runes illuminating the stone floor. Dungeon laboratory corridor background, "
                "crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))