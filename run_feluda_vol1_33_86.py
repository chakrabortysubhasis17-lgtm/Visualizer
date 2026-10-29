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


BUILD_DIR = "build_feluda_vol1_33_86"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source: Local PDF path and Page range
    "novel_slug": "adventures-of-feluda",
    "start_url": r"D:\Projects\visualer\ebooks\Satyajit Ray - The Complete Adventures of Feluda Vol 1. 1-Penguin Books.pdf",
    "start_chapter": 33,
    "end_chapter": 86,
    "is_start": False,  # Continues from previous episode; triggers continuation intro
    "default_topic": "The Complete Adventures of Feluda / Satyajit Ray / Detective Fiction / Prodosh C. Mitter / Topshe / Classic Mystery",

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook
    "intro_hook": "Armed with razor-sharp deduction, encyclopedic trivia, and unflinching composure, Prodosh Chandra Mitter and Topshe plunge deeper into intricate webs of deception across classic Bengal.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_feluda_vol1_33_86.mp3",
    "final_video": "final_feluda_vol1_33_86.mp4",
    "cover_image": "cover_feluda_vol1_33_86.jpg",
    "timestamps_file": "youtube_timestamps_feluda_vol1_33_86.txt",
    "subtitles_file": "subtitles_feluda_vol1_33_86.srt",
    "payload_file": "youtube_upload_payload_feluda_vol1_33_86.json",

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
    "video_title": "The Complete Adventures of Feluda | Satyajit Ray | Pages 33 - 86 | Classic Detective Mystery Audiobook",
    "privacy_status": "unlisted",
    "tags": [
        "Feluda", "Satyajit Ray", "Adventures of Feluda", "Feluda Audiobook",
        "Prodosh C Mitter", "Topshe", "Bengali Detective Fiction", "Indian Mystery",
        "Classic Detective", "Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "This episode, we step right back into the story, continuing exactly where we left off in our previous episode of this series.\n\n"
        "Experience 'The Complete Adventures of Feluda' (Volume 1) by Satyajit Ray (Pages 33 to 86).\n\n"
        "Journey alongside Prodosh Chandra Mitter (Feluda) and his observant chronicler Topshe as mysterious clues, "
        "cryptic messages, and shadowed adversaries demand every ounce of Magojastro—the weapon of the brain.\n\n"
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

    # 3 Thematic Visual Arc Blocks across Pages 33 to 86 (54 pages partitioned)
    "blocks": [
        {
            "index": 1, "range": (33, 50),
            "title": ["THE WEB OF SUSPICION", "INVESTIGATION EXPANDS"],
            "fallback_color": (20, 18, 16),
            "prompt": (
                "Cinematic vintage study in late 1960s Bengal, evening shadows falling across a solid wooden desk with a brass desk lamp casting a warm amber pool of light, "
                "open notebook, handwritten clues, a magnifying glass, and a pack of Charminar cigarettes resting by an ashtray, authentic nostalgic detective noir, 4K digital photography."
            )
        },
        {
            "index": 2, "range": (51, 68),
            "title": ["PURSUIT ACROSS BENGAL", "TRAILS & CONFRONTATIONS"],
            "fallback_color": (16, 22, 24),
            "prompt": (
                "Atmospheric foggy railway platform in rural Bengal at night, steam engine headlamp illuminating swirling mist with long dramatic cast shadows, "
                "a sharp observant tall detective in a kurta and shawl scanning the carriages with calm alertness, cinematic mystery frame, 4K masterpiece."
            )
        },
        {
            "index": 3, "range": (69, 86),
            "title": ["MAGOJASTRO UNLEASHED", "THE FINAL REVELATION"],
            "fallback_color": (24, 20, 18),
            "prompt": (
                "Dramatic candlelit colonial library interior with high ceilings and tall arched windows revealing moonlit rain, "
                "a poised intellectual sleuth delivering the final deduction before gathered astonished suspects, warm chiaroscuro lighting, highly detailed 4K illustration."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
