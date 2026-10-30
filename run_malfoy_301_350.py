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


BUILD_DIR = "build_miss_malfoy_301_350"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "hp-miss-malfoy-doesnt-want-to-romance-her-parents-generation",
    "start_url": "https://mtl-novel.com/novel/hp-miss-malfoy-doesnt-want-to-romance-her-parents-generation/chapter-301-as-a-little-sister/",
    "start_chapter": 301,
    "end_chapter": 350,
    "is_start": False,  # Continuation volume
    "default_topic": "HP: Miss Malfoy Doesn't Want to Romance Her Parents' Generation / Harry Potter Fanfiction / Slytherin / Marauders Era / Hogwarts Magic / Pureblood Society",

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook
    "intro_hook": "Determined to carve out her own magical destiny as a true Malfoy, she steers clear of Marauders-era romantic entanglements while outwitting dark politics in the halls of Hogwarts.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_miss_malfoy_301_350.mp3",
    "final_video": "final_miss_malfoy_301_350.mp4",
    "cover_image": "cover_miss_malfoy_301_350.jpg",
    "timestamps_file": "youtube_timestamps_miss_malfoy_301_350.txt",
    "subtitles_file": "subtitles_miss_malfoy_301_350.srt",
    "payload_file": "youtube_upload_payload_miss_malfoy_301_350.json",

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
    "video_title": "HP: Miss Malfoy Doesn't Want to Romance Her Parents' Generation | Ch 301 - 350 Full Audiobook",
    "privacy_status": "unlisted",
    "tags": [
        "Miss Malfoy", "HP Miss Malfoy", "Harry Potter Fanfiction", "Miss Malfoy Audiobook",
        "Slytherin Audiobook", "Marauders Era", "Hogwarts Fanfiction", "Pureblood Politics",
        "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "This episode, we step right back into the series, continuing exactly where we left off in our previous episode.\n\n"
        "Experience 'HP: Miss Malfoy Doesn't Want to Romance Her Parents' Generation' (Chapters 301 to 350) — The Pureblood Scheming Arc.\n\n"
        "As shadows lengthen over the wizarding world and ancient pureblood houses maneuver for leverage, Miss Malfoy doubles down on "
        "independent arcane mastery. Navigating fragile friendships, Slytherin rivalries, and the looming storm of the First Wizarding War, "
        "she proves that wit, ambition, and self-preservation will always triumph over melodrama.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "🎙️ NARRATION: en-US-ChristopherNeural (Deep Cinematic Baritone).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#MissMalfoy #HarryPotterFanfiction #Slytherin #MaraudersEra #FanfictionAudiobook #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks across Chapters 301 to 350 (50 chapters partitioned)
    "blocks": [
        {
            "index": 1, "range": (301, 313),
            "title": ["A LITTLE SISTER'S RESOLVE", "FAMILY TIES"],
            "fallback_color": (16, 24, 20),
            "prompt": (
                "An elegant Victorian-gothic Malfoy Manor drawing room bathed in emerald and silver moonlight, "
                "a poised young platinum-blonde witch in stylish dark emerald Slytherin robes seated at a carved black walnut desk, "
                "writing with a raven quill while a glowing silver patronus mist shimmers softly around her, 4K digital painting."
            )
        },
        {
            "index": 2, "range": (314, 325),
            "title": ["DUNGEON SECRETS", "SUBTLE ARCANUM"],
            "fallback_color": (14, 20, 18),
            "prompt": (
                "Moody atmospheric Hogwarts Slytherin common room with tall arched windows looking into dark murky Great Lake waters, "
                "green-tinged glowing chandeliers casting ripples over leather armchairs and ancient stone fireplaces, "
                "intricate silver serpentine ornaments reflecting dancing flames, 4K concept art."
            )
        },
        {
            "index": 3, "range": (326, 338),
            "title": ["GATHERING CLOUDS", "NOBLE CONFLICTS"],
            "fallback_color": (22, 16, 18),
            "prompt": (
                "The Great Hall of Hogwarts under a stormy enchanted ceiling with heavy rain and distant lightning flashes, "
                "students in black cloaks seated at long banquet tables whispering tense secrets, "
                "floating wax candles casting warm amber reflections across stone flags and house banners, 4K masterpiece."
            )
        },
        {
            "index": 4, "range": (339, 350),
            "title": ["AN INDEPENDENT PATH", "DESTINY RECLAIMED"],
            "fallback_color": (18, 22, 26),
            "prompt": (
                "The Hogwarts Astronomy Tower balcony at midnight overlooking misty Scottish highland mountains and the Black Lake, "
                "a solitary young blonde witch standing resolutely in the chilling night wind holding a glowing wand, "
                "sparks of silver and blue magic dancing off the wand tip into the starry night sky, cinematic lighting, 4K."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
