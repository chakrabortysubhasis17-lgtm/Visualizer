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

BUILD_DIR = "build_national_fate_marriage_301_350"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "national-fate-marriage-the-elf-queen-is-pregnant-at-the-start",
    "start_url": "https://mtl-novel.com/novel/national-fate-marriage-the-elf-queen-is-pregnant-at-the-start/chapter-301-have-you-seen-enough/",
    "start_chapter": 301,
    "end_chapter": 350,
    "default_topic": "National Fate / Elven Empire / Divine Marriage",

    # Concurrency Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-GuyNeural",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_national_fate_marriage_301_350.mp3",
    "final_video": "final_national_fate_marriage_301_350.mp4",
    "cover_image": "cover_national_fate_marriage_301_350.jpg",
    "timestamps_file": "youtube_timestamps_national_fate_marriage_301_350.txt",
    "subtitles_file": "subtitles_national_fate_marriage_301_350.srt",
    "payload_file": "youtube_upload_payload_national_fate_marriage_301_350.json",

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
    "video_title": "National Fate Marriage: The Elf Queen is Pregnant at the Start | Ch 301 - 350 Full Audio Novel Marathon",
    "privacy_status": "unlisted",
    "tags": [
        "National Fate Marriage", "Elf Queen Pregnant", "National Fate Audiobook",
        "Fantasy Audiobook", "Elven Empire", "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the full 50-chapter audio novel marathon of 'National Fate Marriage: The Elf Queen is Pregnant at the Start' (Chapters 301 to 350).\n\n"
        "Follow the thrilling development of national fate trials, royal elven court intrigue, divine realm conquests, and empire expansion.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic mastering, vocal presence).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited, dramatized fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#NationalFateMarriage #ElfQueen #FantasyAudiobook #WebNovel #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 301 to 350 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (301, 310),
            "title": ["HAVE YOU SEEN ENOUGH", "ELF QUEEN'S SANCTUARY"],
            "fallback_color": (20, 35, 25),
            "prompt": (
                "Cinematic 3D fantasy scene of a breathtaking silver-haired elven queen wearing an ethereal glowing emerald gown and a delicate golden tiara, "
                "standing in a sacred glowing moonlit palace conservatory with ancient giant roots and silver water fountains. Elegant composition, gentle bioluminescent glow, "
                "photorealistic 4K rendering."
            )
        },
        {
            "index": 2, "range": (311, 320),
            "title": ["NATIONAL FATE TRIAL", "DIVINE REALM BLESSING"],
            "fallback_color": (30, 25, 40),
            "prompt": (
                "Cinematic high fantasy scene of a young human sovereign bathed in golden celestial pillar light, standing on an ancient ceremonial marble dais, "
                "surrounded by floating mystical runic seals and national fate territorial banners fluttering under starry cosmic skies. Dramatic majestic lighting, ultra-detailed."
            )
        },
        {
            "index": 3, "range": (321, 330),
            "title": ["ROYAL ELVEN LEGION", "ANCIENT FOREST CONQUEST"],
            "fallback_color": (15, 30, 35),
            "prompt": (
                "Cinematic wide angle fantasy shot of an elite elven army in gleaming filigree silver armor and bows marching through a mystical misty primordial forest, "
                "glowing green magical wisps floating between giant ancient trees, grand fantasy atmosphere, cinematic lighting."
            )
        },
        {
            "index": 4, "range": (331, 340),
            "title": ["MYTHIC BLESSINGS", "RIVAL REALM INVASION"],
            "fallback_color": (35, 20, 25),
            "prompt": (
                "Cinematic fantasy battle scene of elven vanguard and guardian beasts holding a towering enchanted crystalline gate against invading dark forces, "
                "radiant magical barrier deflecting fiery spells, sparks and mystical runes lighting up the stone ramparts, epic dynamic composition."
            )
        },
        {
            "index": 5, "range": (341, 350),
            "title": ["SOVEREIGN CROWN", "EMPIRE DOMINATION"],
            "fallback_color": (25, 30, 20),
            "prompt": (
                "Cinematic fantasy wide view of the grand throne room of the combined human and elven empire at sunrise, the sovereign and the elf queen standing hand-in-hand "
                "overlooking thousands of assembled diplomats and warriors cheering in the hall, magnificent stained-glass windows, god rays, opulent 4K detail."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
