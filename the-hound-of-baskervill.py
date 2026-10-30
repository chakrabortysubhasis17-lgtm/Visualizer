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

                is_dummy = len(rows) < 8 or any("Visual illustration or blank page" in r.get("text", "") for r in rows)
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


BUILD_DIR = "build_hound_of_the_baskervilles_592_663"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters (Local PDF Page Extraction)
    "novel_slug": "the-hound-of-the-baskervilles",
    "start_url": r"D:\Projects\visualer\ebooks\SherlockHolmesComplete.pdf",
    "start_chapter": 592,
    "end_chapter": 663,
    "is_start": True,  # Series Opening Episode
    "default_topic": "The Hound of the Baskervilles / Sir Arthur Conan Doyle / Sherlock Holmes / Dartmoor / Grimpen Mire / Baskerville Hall / Gothic Mystery",

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook
    "intro_hook": "Drawn to the desolate, fog-shrouded moors of Dartmoor, Sherlock Holmes and Dr. Watson investigate an ancient family curse and the terrifying legend of a demonic phantom hound.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_hound_of_the_baskervilles_592_663.mp3",
    "final_video": "final_hound_of_the_baskervilles_592_663.mp4",
    "cover_image": "cover_hound_of_the_baskervilles_592_663.jpg",
    "timestamps_file": "youtube_timestamps_hound_of_the_baskervilles_592_663.txt",
    "subtitles_file": "subtitles_hound_of_the_baskervilles_592_663.srt",
    "payload_file": "youtube_upload_payload_hound_of_the_baskervilles_592_663.json",

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
    "video_title": "The Hound of the Baskervilles by Arthur Conan Doyle | Full Audiobook | Sherlock Holmes Mystery",
    "privacy_status": "unlisted",
    "tags": [
        "The Hound of the Baskervilles", "Sherlock Holmes", "Arthur Conan Doyle",
        "Hound of the Baskervilles Audiobook", "Sherlock Holmes Audiobook",
        "Gothic Mystery Audiobook", "Dartmoor", "Dr Watson", "Public Domain Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Welcome to the opening episode of this series. A brand-new adventure awaits, and we are glad to have you with us.\n\n"
        "Experience 'The Hound of the Baskervilles' by Sir Arthur Conan Doyle (Pages 592 to 663) — The Complete Gothic Masterpiece.\n\n"
        "When Sir Charles Baskerville is found mysteriously dead upon the eerie grounds of Baskerville Hall, whispers of a supernatural hellhound "
        "echo across the desolate expanses of Dartmoor. Armed with keen deduction and unwavering courage, Sherlock Holmes and Dr. John H. Watson "
        "confront ancient ancestral legends, deadly mire quicksands, and a shadowy conspiracy lurking within the moorland mist.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "🎙️ NARRATION: en-US-ChristopherNeural (Deep Cinematic Baritone).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audio presentation is an unabridged dramatized reading of public domain literature produced for commentary and entertainment purposes.\n\n"
        "#HoundOfTheBaskervilles #SherlockHolmes #ConanDoyle #GothicHorror #ClassicAudiobook #Dartmoor #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks across Pages 592 to 663 (72 pages partitioned)
    "blocks": [
        {
            "index": 1, "range": (592, 609),
            "title": ["THE BASKERVILLE CURSE", "LEGEND OF THE MOOR"],
            "fallback_color": (22, 16, 14),
            "prompt": (
                "Cinematic Victorian study at 221B Baker Street in deep shadow and warm fireplace glow, "
                "Sherlock Holmes and Dr Watson examining an aged, yellowed parchment manuscript bearing an ancient family seal, "
                "a rustic walking stick leaning against an oak table, atmospheric pipe smoke, 4K digital painting."
            )
        },
        {
            "index": 2, "range": (610, 627),
            "title": ["BASKERVILLE HALL", "SHADOW OVER DARTMOOR"],
            "fallback_color": (16, 18, 22),
            "prompt": (
                "Imposing dark stone Victorian gothic manor Baskerville Hall brooding at twilight under heavy rain clouds, "
                "twin castellated towers silhouetted against a stormy desolate sky, tall gnarled leafless oak trees, "
                "a lone horse carriage approaching along a gravel drive, haunting gothic atmosphere, 4K concept art."
            )
        },
        {
            "index": 3, "range": (628, 645),
            "title": ["THE GRIMPEN MIRE", "HOWLS IN THE FOG"],
            "fallback_color": (14, 20, 18),
            "prompt": (
                "Eerie desolate expanse of Dartmoor blanketed in swirling thick night mist and pale green luminescence, "
                "ancient granite stone tor monoliths looming out of the boggy Grimpen Mire, "
                "a solitary shadowy figure standing atop a high rocky crag in the pale moonlight, ominous tension, 4K masterpiece."
            )
        },
        {
            "index": 4, "range": (646, 663),
            "title": ["THE PHANTOM HOUND", "THE FINAL TRAP"],
            "fallback_color": (26, 12, 14),
            "prompt": (
                "Climactic action scene on the fog-drenched moor at night, "
                "a colossal monstrous hound with glowing phosphorus muzzle and eyes leaping through parting fog banks, "
                "two Victorian gentlemen in heavy coats firing revolvers with bright muzzle flashes cutting through the mist, cinematic drama, 4K."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
