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


BUILD_DIR = "build_dracula_262_509"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source: Local PDF path and Page range (Final Volume / Grand Finale)
    "novel_slug": "dracula-bram-stoker",
    "start_url": r"D:\Projects\visualer\ebooks\Dracula - Bram Stoker.pdf",
    "start_chapter": 262,
    "end_chapter": 509,
    "is_start": False,  # Continuation from Part 1; triggers mid-story greeting
    "default_topic": "Dracula / Bram Stoker / Gothic Horror / Mina Harker / Van Helsing / Pursuit to Transylvania / Final Reckoning",

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook
    "intro_hook": "United by solemn oaths and guided by Mina Harker's telepathic connection, the hunters track Count Dracula from London across Europe for the final reckoning at Castle Dracula.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_dracula_262_509.mp3",
    "final_video": "final_dracula_262_509.mp4",
    "cover_image": "cover_dracula_262_509.jpg",
    "timestamps_file": "youtube_timestamps_dracula_262_509.txt",
    "subtitles_file": "subtitles_dracula_262_509.srt",
    "payload_file": "youtube_upload_payload_dracula_262_509.json",

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
    "video_title": "Dracula | Bram Stoker | Grand Finale 8+ Hours Audiobook Marathon (Pages 262 - 509) | The Final Reckoning",
    "privacy_status": "unlisted",
    "tags": [
        "Dracula", "Bram Stoker", "Dracula Audiobook", "Dracula Finale",
        "Count Dracula", "Mina Harker", "Van Helsing", "Jonathan Harker",
        "Gothic Horror", "Classic Literature", "Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "This episode, we step right back into the story, continuing exactly where we left off in our previous episode of this series.\n\n"
        "Experience the epic conclusion to Bram Stoker's gothic masterpiece 'Dracula' (Pages 262 to 509) — The Grand Finale.\n\n"
        "As the nocturnal menace tightens its grip around Mina Harker, Professor Van Helsing, Jonathan, Dr. Seward, Lord Godalming, "
        "and Quincey Morris sterilize Dracula's London lairs and pursue the fleeing vampire across land and sea back to the wilderness of Transylvania.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "🎙️ NARRATION: en-US-ChristopherNeural (Deep Cinematic Baritone).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audio presentation is an educational and commentary reading produced for literature appreciation, gothic horror preservation, and study purposes.\n\n"
        "#Dracula #BramStoker #GothicHorror #DraculaFinale #CountDracula #VanHelsing #MinaHarker #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks across Pages 262 to 509 (248 pages partitioned)
    "blocks": [
        {
            "index": 1, "range": (262, 323),
            "title": ["THE BAPTISM OF BLOOD", "PURGING THE EARTH BOXES"],
            "fallback_color": (20, 14, 18),
            "prompt": (
                "Dark Victorian cellar beneath London shrouded in cold mist and cobwebs, "
                "group of determined armed gentlemen and a scholar with silver crucifixes and consecrated hosts confronting ancient wooden earth boxes, "
                "dramatic lantern lighting cutting through damp shadow, gothic atmosphere, 4K digital painting."
            )
        },
        {
            "index": 2, "range": (324, 385),
            "title": ["MINA'S TRANCE", "PURSUIT ACROSS THE BLACK SEA"],
            "fallback_color": (14, 18, 26),
            "prompt": (
                "A steamship cutting through stormy dark waves on the Black Sea under moonlight, "
                "on deck an elegant Victorian woman in deep hypnotic trance wrapped in heavy wool coat, "
                "an elderly resolute doctor beside her writing notes in a pocket journal, cinematic mood, 4K resolution."
            )
        },
        {
            "index": 3, "range": (386, 447),
            "title": ["RACE ACROSS THE SNOW", "THE CARPATHIAN GORGE"],
            "fallback_color": (18, 22, 28),
            "prompt": (
                "Epic cinematic winter vista of the Carpathian wilderness at twilight, snow-laden pine forest flanking a frozen winding river gorge, "
                "armed riders on horseback in hot pursuit of a swift horse-drawn wagon carrying a heavy wooden coffin, swirling blizzard particles, 4K digital art."
            )
        },
        {
            "index": 4, "range": (448, 509),
            "title": ["THE FINAL RECKONING", "PEACE AT LAST"],
            "fallback_color": (28, 14, 16),
            "prompt": (
                "Dramatic high-contrast sunset over the jagged ruins of Castle Dracula high in the mountains, "
                "crimson sunlight flaring across a snowy mountain pass, flash of steel blades against a shattered coffin as shadows dissolve into red evening mist, "
                "poignant heroic finale composition, 4K masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
