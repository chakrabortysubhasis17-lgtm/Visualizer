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


BUILD_DIR = "build_gourmet_innkeeper_201_250"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "the-gourmet-innkeeper-cooking-monsters-in-a-fantasy-world",
    "start_url": "https://freewebnovel.com/novel/the-gourmet-innkeeper-cooking-monsters-in-a-fantasy-world/chapter-201",
    "start_chapter": 201,
    "end_chapter": 250,
    "is_start": False,  # Continuation volume
    "default_topic": "The Gourmet Innkeeper: Cooking Monsters in a Fantasy World / Fantasy Culinary / Monster Cooking / Innkeeper LitRPG / Delicious Delicacies",

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook
    "intro_hook": "Transforming ferocious apex beasts into legendary gourmet feasts, an eccentric innkeeper expands his magical tavern while satisfying the realm's most dangerous appetites.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_gourmet_innkeeper_201_250.mp3",
    "final_video": "final_gourmet_innkeeper_201_250.mp4",
    "cover_image": "cover_gourmet_innkeeper_201_250.jpg",
    "timestamps_file": "youtube_timestamps_gourmet_innkeeper_201_250.txt",
    "subtitles_file": "subtitles_gourmet_innkeeper_201_250.srt",
    "payload_file": "youtube_upload_payload_gourmet_innkeeper_201_250.json",

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
    "video_title": "The Gourmet Innkeeper: Cooking Monsters in a Fantasy World | Ch 201 - 250 Full Audiobook Marathon",
    "privacy_status": "unlisted",
    "tags": [
        "The Gourmet Innkeeper", "Cooking Monsters in a Fantasy World", "Gourmet Innkeeper Audiobook",
        "Monster Cooking", "Culinary Fantasy", "LitRPG Audiobook", "Fantasy Audiobook",
        "Cozy Fantasy", "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "This episode, we step right back into the story, continuing exactly where we left off in our previous episode of this series.\n\n"
        "Experience 'The Gourmet Innkeeper: Cooking Monsters in a Fantasy World' (Chapters 201 to 250) — The Grand Feast Arc.\n\n"
        "As legendary hunters, wandering mercenaries, and secretive nobility flock to the enchanted tavern, rare monster ingredients "
        "arrive from the deepest dungeons and dangerous frontiers. From simmering mythical broths to sizzling high-tier beast steaks, "
        "watch culinary alchemy elevate stats, soothe weary souls, and spark unexpected tavern rivalries.\n\n"
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
        "#GourmetInnkeeper #MonsterCooking #CulinaryFantasy #LitRPG #FantasyAudiobook #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks across Chapters 201 to 250 (50 chapters partitioned)
    "blocks": [
        {
            "index": 1, "range": (201, 213),
            "title": ["WARM TAVERN HEARTH", "RARE INGREDIENTS ARRIVE"],
            "fallback_color": (26, 18, 12),
            "prompt": (
                "Warm cozy fantasy tavern kitchen interior bathed in golden hearth light, "
                "a cheerful skilled innkeeper chef in a clean apron chopping glowing mystical herbs on a rustic wooden cutting board, "
                "a massive bubbling copper stew cauldron giving off sparkling aromatic steam, hanging dried sausages and garlic braids, 4K digital painting."
            )
        },
        {
            "index": 2, "range": (214, 225),
            "title": ["CULINARY ALCHEMY", "BEAST FLAVOR PROFILE"],
            "fallback_color": (28, 16, 14),
            "prompt": (
                "Dramatic sizzling skillet over high flames in an enchanted kitchen, "
                "thick marinated prime cuts of mythical dragon beast meat searing with vibrant red and golden flame sparks, "
                "surrounded by crystalline spice jars and glowing sauce bowls, dynamic action food photography style, 4K masterpiece."
            )
        },
        {
            "index": 3, "range": (226, 238),
            "title": ["A BANQUET FOR WARRIORS", "REPUTATION EXPANDS"],
            "fallback_color": (22, 16, 20),
            "prompt": (
                "Bustling fantasy inn dining hall crowded with diverse adventurers, armored paladins, and elf rangers feasting merrily, "
                "long oak tables laden with roasted monster delicacies, foaming flagons of ale, warm amber lantern illumination, cozy vibrant tavern atmosphere, 4K."
            )
        },
        {
            "index": 4, "range": (239, 250),
            "title": ["SOVEREIGN APPETITE", "THE INNKEEPER'S SECRET"],
            "fallback_color": (18, 20, 26),
            "prompt": (
                "An evening exterior view of a charming two-story wooden fantasy inn with glowing stained-glass windows, "
                "nestled at the edge of a twilight enchanted forest under a star-filled sky, chimney smoke spiraling into the dusk, welcoming lantern light at the door, 4K concept art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))