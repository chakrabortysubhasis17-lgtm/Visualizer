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


BUILD_DIR = "build_lotm_starting_as_a_reader_51_100"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "lord-of-mysteries-starting-as-a-reader",
    "start_url": "https://freewebnovel.com/novel/lord-of-mysteries-starting-as-a-reader/chapter-51",
    "start_chapter": 51,
    "end_chapter": 100,
    "is_start": False,  # Continuation volume
    "default_topic": "Lord of the Mysteries: Starting as a Reader / LoTM Fanfiction / Reader Pathway / Beyonder Mysteries / Victorian Steampunk Occult / White Tower Pathway",

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook
    "intro_hook": "Navigating the murky gaslit streets of Backlund and the treacherous White Tower Pathway, a shrewd Beyonder decodes forbidden occult grimoires while sidestepping cosmic madness.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_lotm_starting_as_a_reader_51_100.mp3",
    "final_video": "final_lotm_starting_as_a_reader_51_100.mp4",
    "cover_image": "cover_lotm_starting_as_a_reader_51_100.jpg",
    "timestamps_file": "youtube_timestamps_lotm_starting_as_a_reader_51_100.txt",
    "subtitles_file": "subtitles_lotm_starting_as_a_reader_51_100.srt",
    "payload_file": "youtube_upload_payload_lotm_starting_as_a_reader_51_100.json",

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
    "video_title": "Lord of Mysteries: Starting as a Reader | Ch 51 - 100 Full Audiobook Marathon | LoTM Fanfiction",
    "privacy_status": "unlisted",
    "tags": [
        "Lord of the Mysteries", "Starting as a Reader", "LoTM Fanfiction", "Reader Pathway",
        "Lord of Mysteries Audiobook", "Beyonder Mystery", "Victorian Occult", "White Tower Pathway",
        "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "This episode, we step right back into the story, continuing exactly where we left off in our previous episode of this series.\n\n"
        "Experience 'Lord of Mysteries: Starting as a Reader' (Chapters 51 to 100) — The White Tower Arcanum Arc.\n\n"
        "Delving deeper into Victorian-era Backlund's fog-choked alleys, our protagonist advances along the meticulous Reader pathway. "
        "Analyzing Beyonder potions, unraveling hidden mystic rituals, and avoiding the gaze of ancient orthodox churches and underground cults, "
        "every analyzed spell and decoded manuscript brings greater wisdom—and edge-of-the-abyss madness.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "🎙️ NARRATION: en-US-ChristopherNeural (Deep Cinematic Baritone).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audio presentation is an edited fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#LordOfTheMysteries #LoTM #StartingAsAReader #ReaderPathway #Beyonder #OccultMystery #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks across Chapters 51 to 100 (50 chapters partitioned)
    "blocks": [
        {
            "index": 1, "range": (51, 63),
            "title": ["THE OCCULT ARCHIVE", "DECIPHERING THE SCROLLS"],
            "fallback_color": (20, 18, 14),
            "prompt": (
                "Cinematic high-contrast Victorian occult study library bathed in eerie amber lantern light, "
                "a focused young scholar in a dark coat and monocle reading glowing crimson esoteric symbols from an ancient leather-bound grimoire, "
                "overflowing bookshelves reaching high vaulted ceilings, floating brass astronomical apparatus, 4K digital painting."
            )
        },
        {
            "index": 2, "range": (64, 75),
            "title": ["GASLIT CONSPIRACY", "BEYONDER UNDERWORLD"],
            "fallback_color": (14, 18, 22),
            "prompt": (
                "A dark cobblestone Victorian steampunk city street blanketed in thick yellow smog and cold gaslight reflections, "
                "silhouettes of mysterious figures in top hats and heavy trench coats exchanging glowing potion vials near an iron bridge, "
                "distant steam engine plumes rising into the gloomy night sky, atmospheric noir concept art, 4K."
            )
        },
        {
            "index": 3, "range": (76, 88),
            "title": ["THE READER'S GAZE", "SPELL ANALYSIS"],
            "fallback_color": (16, 22, 26),
            "prompt": (
                "Dramatic arcane confrontation in an abandoned gothic chapel, "
                "a Beyonder Reader unleashing glowing translucent white-and-silver geometric calculation matrices and eye symbols, "
                "dissecting incoming dark shadowy tentacles and chaotic purple magic rays with crystalline precision, cinematic lighting, 4K resolution."
            )
        },
        {
            "index": 4, "range": (89, 100),
            "title": ["ABOVE THE HORIZON", "THE EYE OF WISDOM"],
            "fallback_color": (18, 16, 24),
            "prompt": (
                "Panoramic view of a sprawling Victorian metropolis at twilight from a high clock tower balcony, "
                "dense industrial smokestacks and majestic cathedral spires framed against a stormy indigo twilight sky, "
                "a solitary scholar looking out into the mist as subtle ethereal starlight glints in his eyes, 4K masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
