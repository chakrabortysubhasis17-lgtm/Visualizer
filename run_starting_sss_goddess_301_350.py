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

BUILD_DIR = "build_sss_goddess_summon_301_350"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "starting-with-an-sss-rank-goddess-summon",
    "start_url": "https://freewebnovel.com/novel/starting-with-an-sss-rank-goddess-summon/chapter-301",
    "start_chapter": 301,
    "end_chapter": 350,
    "default_topic": "Starting with an SSS-rank Goddess Summon / Territory War / Sovereign Realm",

    # Concurrency Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-GuyNeural",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_sss_goddess_summon_301_350.mp3",
    "final_video": "final_sss_goddess_summon_301_350.mp4",
    "cover_image": "cover_sss_goddess_summon_301_350.jpg",
    "timestamps_file": "youtube_timestamps_sss_goddess_summon_301_350.txt",
    "subtitles_file": "subtitles_sss_goddess_summon_301_350.srt",
    "payload_file": "youtube_upload_payload_sss_goddess_summon_301_350.json",

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
    "video_title": "Starting with an SSS-Rank Goddess Summon | Ch 301 - 350 Full Audio Novel Marathon",
    "privacy_status": "unlisted",
    "tags": [
        "Starting with an SSS-rank Goddess Summon", "Goddess Summon Audiobook", "Sylas Graves",
        "Eluned", "Morwenna", "LitRPG Audiobook", "Progression Fantasy", "Audiobook Marathon",
        "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the full 50-chapter audio novel marathon of 'Starting with an SSS-Rank Goddess Summon' (Chapters 301 to 350).\n\n"
        "Witness the climactic battle against the Unmovable Wall, Breeda's unbreakable Titan bastion defense, Tasman's lethal shadow domain, "
        "the grand feasting of 72 newly recruited female warriors, and Sylas's return to Earth for the lively Shajiatown night market festival.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited, dramatized fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#StartingWithAnSSSRankGoddessSummon #GoddessSummon #LitRPG #ProgressionFantasy #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 301 to 350 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (301, 310),
            "title": ["UNMOVABLE WALL ASSAULT", "BREEDA'S TITAN DEFENSE"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic high-impact 3D fantasy scene of a towering, muscular dark-haired female commander in massive adamantine plate armor, "
                "standing firm behind a colossal steel aegis shield while an enemy shockwave shatters stone around her boots. Swirling smoke, red mana particles, "
                "intense battlefield crater background, dynamic lighting, 4K rendering."
            )
        },
        {
            "index": 2, "range": (311, 320),
            "title": ["AURA HARVESTING", "MORWENNA'S DREAD VANGUARD"],
            "fallback_color": (25, 10, 35),
            "prompt": (
                "Cinematic fantasy scene of a charismatic pirate queen in a pristine navy greatcoat riding a massive armored golden wolf beast across a battlefield at sunrise, "
                "drawn cutlass pointing toward distant fortress battlements, dozens of elite shield-maidens and archers in strict formation, majestic atmospheric god rays."
            )
        },
        {
            "index": 3, "range": (321, 330),
            "title": ["FORTRESS SURRENDER", "THE SEVENTY-TWO WARRIORS"],
            "fallback_color": (20, 25, 30),
            "prompt": (
                "Cinematic wide angle fantasy scene of a battered army of disciplined armored women presenting an honorable surrender in a grand stone castle courtyard, "
                "a young sovereign with glowing golden eyes standing calmly on paved walkways beneath towering obsidian keep walls, twilight ambiance, ultra-detailed."
            )
        },
        {
            "index": 4, "range": (331, 340),
            "title": ["THE BLESSED BANQUET", "DIVINE ARM WRESTLING"],
            "fallback_color": (40, 25, 15),
            "prompt": (
                "Cinematic interior scene of an exuberant rowdy fantasy banquet hall packed with cheering armored warrior women, "
                "two powerful female figures engaged in a ferocious glowing mana arm-wrestling contest across a splintering oak table, "
                "overflowing wooden ale tankards, roasted platters, warm roaring fireplace glow."
            )
        },
        {
            "index": 5, "range": (341, 350),
            "title": ["SHAJIATOWN NIGHT MARKET", "UNDERGROUND MASKS"],
            "fallback_color": (30, 15, 35),
            "prompt": (
                "Cinematic cyberpunk-fantasy hybrid street scene of a neon-lit night market festival, red glowing paper lanterns strung above crowded cobblestones, "
                "a young man and a hooded girl wearing traditional ceramic kitsune and oni masks walking through bustling food stalls and cherry blossom petals, 4K resolution."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
