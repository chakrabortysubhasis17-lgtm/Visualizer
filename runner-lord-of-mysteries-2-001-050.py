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


BUILD_DIR = "build_circle_of_inevitability_001_050"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "circle-of-inevitability",
    "start_url": "https://freewebnovel.com/novel/lord-of-mysteries-2-circle-of-inevitability/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Lord of the Mysteries 2 / Circle of Inevitability / Lumian Lee / Cordu Village / Hunter Pathway / Occult Mystery",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook (start_chapter == 1 triggers the new podcast debut intro)
    "intro_hook": "We step into the mysterious mountain village of Cordu alongside Lumian Lee as strange omens, ancient rituals, and cosmic dread herald the start of a terrifying new occult age.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_circle_of_inevitability_001_050.mp3",
    "final_video": "final_circle_of_inevitability_001_050.mp4",
    "cover_image": "cover_circle_of_inevitability_001_050.jpg",
    "timestamps_file": "youtube_timestamps_circle_of_inevitability_001_050.txt",
    "subtitles_file": "subtitles_circle_of_inevitability_001_050.srt",
    "payload_file": "youtube_upload_payload_circle_of_inevitability_001_050.json",

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
    "video_title": "Circle of Inevitability (LOTM 2) | Ch 1 - 50 Full Audio Novel Marathon | Cordu Nightmare Arc",
    "privacy_status": "unlisted",
    "tags": [
        "Lord of the Mysteries 2", "Circle of Inevitability", "Circle of Inevitability Audiobook",
        "LOTM 2", "Lumian Lee", "Aurore Lee", "Cordu Village", "Hunter Pathway",
        "Tarot Club", "Occult Mystery", "Lovecraftian Horror", "Audiobook Marathon",
        "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to Being a Bong!\n\n"
        "Experience the complete 50-chapter audio novel marathon of 'Lord of the Mysteries 2: Circle of Inevitability' (Chapters 1 to 50) — the Cordu Nightmare Arc.\n\n"
        "Return to the mystical world created by Cuttlefish That Loves Diving. In the southern Intis mountain village of Cordu, "
        "mischievous youth Lumian Lee lives a quiet life with his sister Aurore. But bizarre foreigners, cryptic tarot readers, "
        "uncanny owls, and sinister subterranean ruins soon shatter the idyllic peace. As hidden cults conduct forbidden rites "
        "and cosmic entities stir, Lumian must consume the Hunter potion and unlock the harrowing truth behind an inescapable nightmare.\n\n"
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
        "#LordOfTheMysteries2 #CircleOfInevitability #LumianLee #LOTM2 #OccultHorror #FantasyAudiobook #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 1 to 50 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (1, 10),
            "title": ["VILLAGE OF CORDU", "THE MISCHIEVOUS YOUTH"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic high-detail Victorian gaslamp fantasy scene of a picturesque mountain village at sunset, "
                "rustic stone cottages with slate roofs nestled between craggy peaks, a clever young man with ruffled black hair "
                "and an observant mischievous smirk leaning against a wooden tavern fence, atmospheric amber god rays, 4K composition."
            )
        },
        {
            "index": 2, "range": (11, 20),
            "title": ["WHISPERS OF THE OCCULT", "TAROT CARDS AND STRANGERS"],
            "fallback_color": (20, 15, 30),
            "prompt": (
                "Cinematic mystery scene inside a dimly lit rustic parlor, a mysterious elegant lady in a dark traveling cloak "
                "laying out mystical tarot cards on an antique table, an uncanny barn owl perched outside on a stone window ledge under moonlight, "
                "shadowy silhouettes, subtle violet magical motes, moody atmospheric lighting."
            )
        },
        {
            "index": 3, "range": (21, 30),
            "title": ["DREAMSCAPE RUINS", "THE HUNTER AWAKENS"],
            "fallback_color": (25, 15, 15),
            "prompt": (
                "Cinematic dark fantasy nightmare landscape of crumbling ancient stone ruins surrounded by a swirling fog of ash and crimson embers, "
                "a young agile fighter gripping an iron hunting axe with glowing red sparks dancing across the blade, "
                "grotesque horned shadowy monsters stalking through shattered arches, dynamic dramatic action perspective."
            )
        },
        {
            "index": 4, "range": (31, 40),
            "title": ["THE SINS OF THE PADRE", "HERETICAL SECT"],
            "fallback_color": (15, 20, 25),
            "prompt": (
                "Cinematic eerie gothic scene in an ancient village chapel at midnight, dim candlelight illuminating an ominous altar "
                "carved with unholy circular thorn symbols, a stern corrupt clergyman whispering forbidden incantations in Latinate script, "
                "chiaroscuro shadows, deep psychological horror atmosphere."
            )
        },
        {
            "index": 5, "range": (41, 50),
            "title": ["THE LOOPING CYCLE", "INEVITABLE DOOM"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic breathtaking dark fantasy wide shot of Cordu village enveloped by an ethereal cosmic dome of distorting gray mist, "
                "ethereal astrological runes and spinning clock hands faintly superimposed in the stormy night sky, "
                "a resolute young hunter standing atop a hill overlooking the village preparing for the cycle to shatter, masterpiece rendering."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
