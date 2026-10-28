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


BUILD_DIR = "build_gourmet_innkeeper_151_200"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "the-gourmet-innkeeper-cooking-monsters-in-a-fantasy-world",
    "start_url": "https://freewebnovel.com/novel/the-gourmet-innkeeper-cooking-monsters-in-a-fantasy-world/chapter-151",
    "start_chapter": 151,
    "end_chapter": 200,
    "default_topic": "The Gourmet Innkeeper: Cooking Monsters in a Fantasy World / Fantasy / Culinary / Monster Cooking / Innkeeper",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook
    "intro_hook": "Operating a secluded hillside tavern in a perilous fantasy realm, a master chef hunts deadly mythical monsters to prepare legendary culinary masterpieces that bestow godlike power.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_gourmet_innkeeper_151_200.mp3",
    "final_video": "final_gourmet_innkeeper_151_200.mp4",
    "cover_image": "cover_gourmet_innkeeper_151_200.jpg",
    "timestamps_file": "youtube_timestamps_gourmet_innkeeper_151_200.txt",
    "subtitles_file": "subtitles_gourmet_innkeeper_151_200.srt",
    "payload_file": "youtube_upload_payload_gourmet_innkeeper_151_200.json",

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
    "video_title": "The Gourmet Innkeeper: Cooking Monsters in a Fantasy World | Ch 151 - 200 Audiobook | Mythic Feast",
    "privacy_status": "unlisted",
    "tags": [
        "Gourmet Innkeeper", "Cooking Monsters", "Monster Cooking Fantasy",
        "Fantasy Audiobook", "Culinary Fantasy", "Innkeeper Audiobook", "Monster Hunter Chef",
        "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "This episode, we step right back into the story, continuing exactly where we left off in our previous episode of this series.\n\n"
        "Experience 'The Gourmet Innkeeper: Cooking Monsters in a Fantasy World' (Chapters 151 to 200) — The Mythic Feast Arc.\n\n"
        "From sizzling abyssal dragon steaks to simmering stews made from mythical behemoths, our innkeeper chef takes his tavern to legendary heights. "
        "As renowned heroes, royal envoys, and reclusive archmages flock for a single bite, culinary art becomes the greatest power in the realm.\n\n"
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
        "#GourmetInnkeeper #CookingMonsters #FantasyAudiobook #CulinaryFantasy #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks for Chapters 151 to 200
    "blocks": [
        {
            "index": 1, "range": (151, 162),
            "title": ["WARM TAVERN KITCHEN", "SIZZLING MONSTER MEAT"],
            "fallback_color": (32, 18, 12),
            "prompt": (
                "Cozy rustic fantasy tavern kitchen with a roaring stone hearth and polished copper pots, "
                "a skilled chef searing a massive cut of glowing exotic dragon meat in a smoking cast-iron skillet, aromatic golden embers swirling, 4K masterpiece."
            )
        },
        {
            "index": 2, "range": (163, 175),
            "title": ["HUNTING THE APEX", "RARE INGREDIENTS"],
            "fallback_color": (16, 24, 20),
            "prompt": (
                "Misty primeval jungle waterfall basin, a courageous hunter chef wielding an ornate cleaver and kitchen hunting knives, "
                "facing a giant luminous serpent monster with iridescent scales, dramatic atmospheric lighting, 4K digital art."
            )
        },
        {
            "index": 3, "range": (176, 188),
            "title": ["GRAND FEAST HALL", "DISTINGUISHED PATRONS"],
            "fallback_color": (28, 20, 14),
            "prompt": (
                "Bustling fantasy inn dining hall illuminated by warm amber lanterns and candlelight, "
                "diverse adventurers, elves, and bearded dwarven lords laughing and dining on lavish platters of roasted fantasy beast delicacies, 4K."
            )
        },
        {
            "index": 4, "range": (189, 200),
            "title": ["CELESTIAL DELICACY", "THE TAVERN LEGEND"],
            "fallback_color": (22, 16, 26),
            "prompt": (
                "Cinematic hillside tavern under a starlit night sky, glowing ethereal steam rising from a newly created legendary dish on the counter, "
                "warm amber light spilling from timber-framed tavern windows into the rolling mist, cozy high fantasy aesthetic, 4K."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))