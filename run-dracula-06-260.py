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


BUILD_DIR = "build_dracula_6_260"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source: Local PDF path and Page range (~8.5 to 9 Hours of Narration)
    "novel_slug": "dracula-bram-stoker",
    "start_url": r"D:\Projects\visualer\ebooks\Dracula - Bram Stoker.pdf",
    "start_chapter": 6,
    "end_chapter": 260,
    "is_start": True,  # Series opening: Jonathan Harker's arrival through the Whitby crisis and Van Helsing's vigil
    "default_topic": "Dracula / Bram Stoker / Gothic Horror / Jonathan Harker / Count Dracula / Whitby / Lucy Westenra / Van Helsing",

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook
    "intro_hook": "From the nocturnal imprisonment of Castle Dracula to the mist-drenched cliffs of Whitby, an ancient shadow crosses the sea to stalk Victorian England.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_dracula_6_260.mp3",
    "final_video": "final_dracula_6_260.mp4",
    "cover_image": "cover_dracula_6_260.jpg",
    "timestamps_file": "youtube_timestamps_dracula_6_260.txt",
    "subtitles_file": "subtitles_dracula_6_260.srt",
    "payload_file": "youtube_upload_payload_dracula_6_260.json",

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
    "video_title": "Dracula | Bram Stoker | 8+ Hours Gothic Audiobook Marathon (Pages 6 - 260) | Unabridged Classic",
    "privacy_status": "unlisted",
    "tags": [
        "Dracula", "Bram Stoker", "Dracula Audiobook", "Jonathan Harker",
        "Count Dracula", "Gothic Horror", "Classic Literature", "Audiobook Marathon",
        "Van Helsing", "Whitby", "Lucy Westenra", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience Bram Stoker's monumental gothic masterpiece 'Dracula' (Pages 6 to 260) — An Epic Audio Novel Marathon.\n\n"
        "This expansive volume spans the heart of the novel: Jonathan Harker's terrifying confinement in Transylvania, "
        "the derelict Russian schooner Demeter washing ashore at Whitby during a violent tempest, Lucy Westenra's mysterious nocturnal illness, "
        "and Professor Abraham Van Helsing's desperate occult defense against an immortal predator.\n\n"
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
        "#Dracula #BramStoker #GothicHorror #AudiobookMarathon #CountDracula #VanHelsing #BeingABong"
    ),

    # 4 Balanced Thematic Visual Arc Blocks across Pages 6 to 260 (255 pages partitioned)
    "blocks": [
        {
            "index": 1, "range": (6, 69),
            "title": ["CASTLE DRACULA", "THE TRANSYLVANIAN PRISON"],
            "fallback_color": (16, 18, 24),
            "prompt": (
                "Cinematic high-contrast gothic landscape of the Carpathian Mountains at twilight, "
                "a colossal crumbling gothic fortress perched on sheer black cliffs above swirling misty chasms, "
                "pale moonlight cutting through dark storm clouds, atmospheric volumetric shadows, 4K digital painting."
            )
        },
        {
            "index": 2, "range": (70, 133),
            "title": ["THE VOYAGE OF THE DEMETER", "THE TEMPEST AT WHITBY"],
            "fallback_color": (14, 20, 26),
            "prompt": (
                "Dramatic 19th-century coastal harbor during a raging midnight tempest, giant storm waves crashing against a stone pier, "
                "a derelict ghost schooner with tattered sails drifting into Whitby harbor, lightning illuminating ruined abbey cliffs above, 4K masterpiece."
            )
        },
        {
            "index": 3, "range": (134, 197),
            "title": ["THE SHADOW OVER LUCY", "NOCTURNAL VISITATIONS"],
            "fallback_color": (22, 14, 18),
            "prompt": (
                "Victorian bedroom interior illuminated by pale moonbeams filtering through French windows, "
                "flowing white lace curtains billowing in a cold draft, dark creeping silhouette of an unnatural figure on the balcony, psychological dread, chiaroscuro lighting, 4K."
            )
        },
        {
            "index": 4, "range": (198, 260),
            "title": ["THE SCHOLAR OF AMSTERDAM", "VAN HELSING'S VIGIL"],
            "fallback_color": (24, 18, 14),
            "prompt": (
                "Moody antique study lined with leather-bound occult grimoires and medical specimen jars, "
                "an elderly resolute scholar holding a brass crucifix and garland of garlic blossoms under warm amber lamplight, heavy atmospheric fog outside the leaded window, 4K digital art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
