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

BUILD_DIR = "build_five_element_overlord_151_200"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "five-element-overlord-i-can-upgrade-everything",
    "start_url": "https://freewebnovel.com/novel/five-element-overlord-i-can-upgrade-everything/chapter-155",
    "start_chapter": 151,
    "end_chapter": 200,
    "default_topic": "Five Elements Cultivation / Infinite Upgrade System / Sect Dominance",

    # Concurrency Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-GuyNeural",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_five_element_overlord_151_200.mp3",
    "final_video": "final_five_element_overlord_151_200.mp4",
    "cover_image": "cover_five_element_overlord_151_200.jpg",
    "timestamps_file": "youtube_timestamps_five_element_overlord_151_200.txt",
    "subtitles_file": "subtitles_five_element_overlord_151_200.srt",
    "payload_file": "youtube_upload_payload_five_element_overlord_151_200.json",

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
    "video_title": "Five Element Overlord: I Can Upgrade Everything! | Ch 151 - 200 Full Audio Novel Marathon",
    "privacy_status": "unlisted",
    "tags": [
        "Five Element Overlord", "I Can Upgrade Everything", "Lu Chen",
        "Five Elements Cultivation", "Upgrade System Audiobook", "Xianxia Audiobook",
        "Progression Fantasy", "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the full 50-chapter audio novel marathon of 'Five Element Overlord: I Can Upgrade Everything!' (Chapters 151 to 200).\n\n"
        "Witness Lu Chen elevate his Five-Element spiritual roots to divine heights, upgrading artifacts, elixirs, and ancient secret techniques "
        "to overwhelm rival sect prodigies and dominate the cultivation world.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited, dramatized fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#FiveElementOverlord #ICanUpgradeEverything #XianxiaAudiobook #ProgressionFantasy #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 151 to 200 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (151, 160),
            "title": ["ELEMENTAL TRANSCENDENCE", "UPGRADED SPIRIT ROOT"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D xianxia scene of a handsome young cultivator meditating cross-legged on a floating lotus dais, "
                "surrounded by five revolving elemental rings of fire, water, earth, metal, and wood swirling with divine golden runes. "
                "Ancient mountain peak shrouded in sea of clouds, mystical atmospheric god rays, photorealistic 4K rendering."
            )
        },
        {
            "index": 2, "range": (161, 170),
            "title": ["SECT EXPEDITION", "MYSTIC REALM CLASH"],
            "fallback_color": (30, 25, 15),
            "prompt": (
                "Cinematic high fantasy wide shot of xianxia sect disciples clad in embroidered silk robes standing atop a giant flying spiritual boat "
                "entering an ancient primordial mystic realm filled with glowing crystalline peaks and storm clouds, grand scale, volumetric fog, dynamic lighting."
            )
        },
        {
            "index": 3, "range": (171, 180),
            "title": ["DIVINE TALISMAN FORGING", "SUPREME TREASURES"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic interior shot of a grand Daoist alchemy chamber, a cultivator channeling azure flame into an ornate bronze cauldron, "
                "golden upgrade light beams refracting through floating spirit stones and divine talisman scrolls, embers drifting in the air, warm luminous lighting, 4K."
            )
        },
        {
            "index": 4, "range": (181, 190),
            "title": ["ANCIENT RUINS TRIALS", "FIVE-ELEMENT DOMAIN"],
            "fallback_color": (15, 25, 30),
            "prompt": (
                "Cinematic action scene inside a colossal submerged jade underground temple, a powerful cultivator unleashing an expansive five-element domain barrier "
                "to shatter giant stone guardian golems and shockwaves of dark purple miasma, intense action pose, particle effects, dramatic high fantasy lighting."
            )
        },
        {
            "index": 5, "range": (191, 200),
            "title": ["OVERLORD ASCENSION", "SECT SUPREMACY"],
            "fallback_color": (20, 15, 35),
            "prompt": (
                "Cinematic panoramic shot of the supreme Five Elements Overlord standing atop the grand palace stairs of the heavenly sect at twilight, "
                "cloaked in radiant multicolored spiritual radiance, thousands of sect elders and disciples bowing in respect, majestic sunset hues, ultra-detailed 4K."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))