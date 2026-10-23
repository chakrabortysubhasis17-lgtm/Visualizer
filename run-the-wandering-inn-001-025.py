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

BUILD_DIR = "build_the_wandering_inn_001_025"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "the-wandering-inn",
    "start_url": "https://freewebnovel.com/novel/the-wandering-inn/chapter-1",
    "start_chapter": 1,
    "end_chapter": 25,
    "default_topic": "The Wandering Inn / LitRPG / Fantasy Innkeeper / Liscor",

    # Concurrency Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-GuyNeural",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_the_wandering_inn_001_025.mp3",
    "final_video": "final_the_wandering_inn_001_025.mp4",
    "cover_image": "cover_the_wandering_inn_001_025.jpg",
    "timestamps_file": "youtube_timestamps_the_wandering_inn_001_025.txt",
    "subtitles_file": "subtitles_the_wandering_inn_001_025.srt",
    "payload_file": "youtube_upload_payload_the_wandering_inn_001_025.json",

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
    "video_title": "The Wandering Inn | Ch 1 - 25 Full Audio Novel Marathon | Volume 1 Arc",
    "privacy_status": "unlisted",
    "tags": [
        "The Wandering Inn", "Wandering Inn Audiobook", "Erin Solstice", "Relc and Klbkch",
        "LitRPG Audiobook", "Fantasy Audiobook", "Progression Fantasy", "Audiobook Marathon",
        "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to Being a Bong!\n\n"
        "Experience the uninterrupted 25-chapter audio novel marathon of 'The Wandering Inn' (Chapters 1 to 25) — Volume 1.\n\n"
        "Follow Erin Solstice as she arrives in an unforgiving fantasy world, stumbles upon an abandoned stone building outside the Drake city of Liscor, "
        "defends herself with boiling pasta water, unlocks the [Innkeeper] class, and begins serving the first unlikely patrons of her hearth.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited, dramatized fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#TheWanderingInn #ErinSolstice #LitRPG #FantasyAudiobook #ProgressionFantasy #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 1 to 25 (5 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (1, 5),
            "title": ["THE RUINED INN", "FIRST ENCOUNTER"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D fantasy scene of a young, disoriented college girl in modern clothes standing outside a weathered, "
                "derelict stone inn on a breezy hillside under twin moons, holding a heavy iron skillet defensively as small glowing red eyes "
                "watch from the tall grass, atmospheric volumetric moonlight, 4K rendering."
            )
        },
        {
            "index": 2, "range": (6, 10),
            "title": ["LEVEL UP: INNKEEPER", "DRAKE & ANTINIUM"],
            "fallback_color": (25, 30, 20),
            "prompt": (
                "Cinematic fantasy tavern interior with a cheerful female innkeeper wiping a freshly scrubbed wooden counter, "
                "greeting a formidable green-scaled Drake guardsman carrying a spear and a stoic insectoid Antinium warrior with glossy black carapace, "
                "warm amber fireplace light, cozy tavern atmosphere, ultra-detailed."
            )
        },
        {
            "index": 3, "range": (11, 15),
            "title": ["CHESS & BLUE CRUSH", "TASTES OF HOME"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic scene inside a rustic fantasy common room, a young woman intensely engaged in a wooden chess game opposite "
                "a four-armed insectoid creature, surrounded by clay mugs of glowing blue juice and steaming bowls of flat pasta, "
                "soft candle illumination, detailed wood textures, dramatic lighting."
            )
        },
        {
            "index": 4, "range": (16, 20),
            "title": ["THE LONELY GOBLIN", "KINDNESS IN THE WILD"],
            "fallback_color": (20, 30, 25),
            "prompt": (
                "Cinematic twilight scene outside the stone tavern doorway, the young innkeeper kneeling down to offer a warm baked loaf "
                "of bread to a timid, scrawny green goblin child clutching a rough stone dagger, wind whispering through tall prairie grass, "
                "emotive storytelling lighting, 4K resolution."
            )
        },
        {
            "index": 5, "range": (21, 25),
            "title": ["LISCOR FLOODPLAINS", "RISING THREATS"],
            "fallback_color": (35, 20, 25),
            "prompt": (
                "Cinematic wide angle panorama of the vast Liscor floodplains at dusk, the solitary stone inn glowing with welcoming lantern light "
                "against brooding storm clouds, distant Drake watchtowers standing guard along massive stone city walls in the background, "
                "epic fantasy scale, high-detail rendering."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
