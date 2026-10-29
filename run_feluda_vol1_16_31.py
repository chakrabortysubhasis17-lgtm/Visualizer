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


BUILD_DIR = "build_feluda_vol1_16_31"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source: Local PDF path and Page range
    "novel_slug": "adventures-of-feluda",
    "start_url": r"D:\Projects\visualer\ebooks\Satyajit Ray - The Complete Adventures of Feluda Vol 1. 1-Penguin Books.pdf",
    "start_chapter": 16,
    "end_chapter": 31,
    "is_start": True,  # Opening story arc trigger: enables series opening greeting and prepends title
    "default_topic": "The Complete Adventures of Feluda / Satyajit Ray / Detective Fiction / Prodosh C. Mitter / Topshe / Kolkata Mystery",

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook
    "intro_hook": "Sharp-eyed Kolkata sleuth Prodosh Chandra Mitter, famously known as Feluda, steps into his first documented investigation alongside his observant young cousin Topshe.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_feluda_vol1_16_31.mp3",
    "final_video": "final_feluda_vol1_16_31.mp4",
    "cover_image": "cover_feluda_vol1_16_31.jpg",
    "timestamps_file": "youtube_timestamps_feluda_vol1_16_31.txt",
    "subtitles_file": "subtitles_feluda_vol1_16_31.srt",
    "payload_file": "youtube_upload_payload_feluda_vol1_16_31.json",

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
    "video_title": "The Complete Adventures of Feluda | Satyajit Ray | Pages 16 - 31 | Classic Detective Mystery Audiobook",
    "privacy_status": "unlisted",
    "tags": [
        "Feluda", "Satyajit Ray", "Adventures of Feluda", "Feluda Audiobook",
        "Prodosh C Mitter", "Topshe", "Bengali Detective Fiction", "Indian Mystery",
        "Classic Detective", "Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience 'The Complete Adventures of Feluda' (Volume 1) by Satyajit Ray (Pages 16 to 31).\n\n"
        "Step into 21 Rajani Sen Road, Kolkata, as Prodosh Chandra Mitter—Feluda—applies keen analytical intellect, "
        "encyclopedic knowledge, and careful observation to unravel an intriguing web of secrets narrated by his faithful cousin Topshe.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "🎙️ NARRATION: en-US-ChristopherNeural (Deep Cinematic Baritone).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audio presentation is an educational and commentary reading produced for literature appreciation, cultural preservation, and study purposes.\n\n"
        "#Feluda #SatyajitRay #DetectiveFiction #MysteryAudiobook #ProdoshCMitter #Topshe #BeingABong"
    ),

    # 2 Thematic Visual Arc Blocks across Pages 16 to 31
    "blocks": [
        {
            "index": 1, "range": (16, 23),
            "title": ["THE SLEUTH OF RAJANI SEN ROAD", "OBSERVATION & DEDUCTION"],
            "fallback_color": (22, 20, 18),
            "prompt": (
                "Cinematic vintage Kolkata sitting room in the late afternoon, tall wooden shuttered windows letting in soft golden dust motes, "
                "dark teak bookcases lined with leather-bound volumes, a magnifying glass and a pipe resting beside an open notebook on a coffee table, classic 1970s detective atmosphere, 4K digital photography."
            )
        },
        {
            "index": 2, "range": (24, 31),
            "title": ["TRAIL OF CLUES", "THE GAME AFOOT"],
            "fallback_color": (18, 22, 24),
            "prompt": (
                "Atmospheric twilight street in classic North Kolkata, colonial-era brick architecture, cast-iron balconies, "
                "warm amber street lamps reflecting on damp cobblestones, a sharp silhouette in a trench coat walking purposefully into misty shadows, classic mystery noir aesthetic, 4K resolution."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
