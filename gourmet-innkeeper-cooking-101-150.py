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

BUILD_DIR = "build_gourmet_innkeeper_101_150"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "the-gourmet-innkeeper-cooking-monsters-in-a-fantasy-world",
    "start_url": "https://freewebnovel.com/novel/the-gourmet-innkeeper-cooking-monsters-in-a-fantasy-world/chapter-101",
    "start_chapter": 101,
    "end_chapter": 150,
    "default_topic": "Monster Cooking / Gourmet Innkeeper / Fantasy Culinary Arts",

    # Concurrency Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-GuyNeural",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_gourmet_innkeeper_101_150.mp3",
    "final_video": "final_gourmet_innkeeper_101_150.mp4",
    "cover_image": "cover_gourmet_innkeeper_101_150.jpg",
    "timestamps_file": "youtube_timestamps_gourmet_innkeeper_101_150.txt",
    "subtitles_file": "subtitles_gourmet_innkeeper_101_150.srt",
    "payload_file": "youtube_upload_payload_gourmet_innkeeper_101_150.json",

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
    "video_title": "The Gourmet Innkeeper: Cooking Monsters in a Fantasy World | Ch 101 - 150 Full Audio Novel Marathon",
    "privacy_status": "unlisted",
    "tags": [
        "The Gourmet Innkeeper", "Cooking Monsters in a Fantasy World", "Gourmet Innkeeper Audiobook",
        "Fantasy Cooking", "Monster Hunter Cooking", "LitRPG Audiobook", "Audiobook Marathon",
        "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the uninterrupted 50-chapter audio novel marathon of 'The Gourmet Innkeeper: Cooking Monsters in a Fantasy World' (Chapters 101 to 150).\n\n"
        "Follow the culinary adventures of an otherworldly innkeeper harvesting rare monster beasts, brewing mystical broths, "
        "and serving high-tier adventurers and royal dignitaries with stat-boosting gourmet dishes.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic mastering, vocal presence).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited, dramatized fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#TheGourmetInnkeeper #MonsterCooking #FantasyAudiobook #WebNovel #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 101 to 150 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (101, 110),
            "title": ["EXOTIC INGREDIENTS", "WYVERN ROAST PREPARATION"],
            "fallback_color": (35, 20, 15),
            "prompt": (
                "Cinematic 3D fantasy scene of a charismatic young chef in an embroidered leather apron skillfully carving seasoned wyvern steak "
                "on a massive wooden kitchen counter, surrounded by glowing mystical spice jars, hanging dried monster herbs, and a roaring stone hearth fire. "
                "Warm amber lighting, crisp food textures, cozy tavern kitchen ambiance, 4K rendering."
            )
        },
        {
            "index": 2, "range": (111, 120),
            "title": ["THE TAVERN RUSH", "STAT-BOOSTING FEASTS"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic wide angle fantasy view of a bustling medieval-fantasy tavern dining hall at night, diverse adventurers in dented armor "
                "cheering and feasting on giant roasted monster ribs and foaming glowing ales, steaming magical dishes served on polished oak tables, "
                "lively tavern atmosphere, volumetric lantern light."
            )
        },
        {
            "index": 3, "range": (121, 130),
            "title": ["DUNGEON EXPEDITION", "RARE BEAST HARVEST"],
            "fallback_color": (15, 25, 35),
            "prompt": (
                "Cinematic fantasy scene of the culinary innkeeper accompanied by party members venturing into an ancient bioluminescent subterranean cavern, "
                "carefully harvesting glowing blue deep-sea fish and enchanted crystal mushrooms from the edge of an underground lake. "
                "Ethereal lighting, moody blue and teal hues, photorealistic textures."
            )
        },
        {
            "index": 4, "range": (131, 140),
            "title": ["ROYAL CULINARY DUEL", "MYTHIC TASTING"],
            "fallback_color": (35, 30, 20),
            "prompt": (
                "Cinematic high-fantasy scene inside an opulent royal palace banquet hall, high nobles and royal judges dressed in velvet and gold "
                "tasting an exquisitely plated mythical dragon-tail consommé radiating subtle rainbow mist, stunned delighted expressions, "
                "magnificent chandeliers, golden rim lighting, highly detailed."
            )
        },
        {
            "index": 5, "range": (141, 150),
            "title": ["LEGENDARY GOURMET BANQUET", "INNKEEPER'S TRIUMPH"],
            "fallback_color": (30, 20, 30),
            "prompt": (
                "Cinematic fantasy shot of the master innkeeper standing proudly in front of his grand, expanded fantasy manor inn at twilight, "
                "holding a steaming, masterfully prepared golden gourmet platter, warmly lit windows glowing behind him, cherry blossom petals drifting "
                "in the evening breeze, celebratory heroic atmosphere, ultra-detailed 4K."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
