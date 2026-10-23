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

BUILD_DIR = "build_all_gods_sss_talent_601_650"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "all-gods-starting-with-sss-level-talent",
    "start_url": "https://mtl-novel.com/novel/all-gods-starting-with-sss-level-talent/chapter-601-tier-3-wraith-clan/",
    "start_chapter": 601,
    "end_chapter": 650,
    "default_topic": "Age of Gods / Divine Domain / Wraith Clan Subjugation / Faith War",

    # Concurrency Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-GuyNeural",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_all_gods_sss_talent_601_650.mp3",
    "final_video": "final_all_gods_sss_talent_601_650.mp4",
    "cover_image": "cover_all_gods_sss_talent_601_650.jpg",
    "timestamps_file": "youtube_timestamps_all_gods_sss_talent_601_650.txt",
    "subtitles_file": "subtitles_all_gods_sss_talent_601_650.srt",
    "payload_file": "youtube_upload_payload_all_gods_sss_talent_601_650.json",

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
    "video_title": "All Gods: Starting with SSS-Level Talent | Ch 601 - 650 Full Audio Novel Marathon",
    "privacy_status": "unlisted",
    "tags": [
        "All Gods Starting with SSS Level Talent", "Global Godhood", "Age of Gods Audiobook",
        "Divine Domain", "SSS Talent", "Faith Evolution", "LitRPG Audiobook",
        "Progression Fantasy", "Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the complete 50-chapter audio novel marathon of 'All Gods: Starting with SSS-Level Talent' (Chapters 601 to 650).\n\n"
        "Witness divine domain warfare as Tier-3 Wraith Clan forces face supreme subjugation, ancient faith cores evolve, "
        "and SSS-grade divine authority reshapes cosmic battlefields across the divine pantheon.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited, dramatized fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#AllGodsStartingWithSSSTalent #GlobalGodhood #DivineDomain #LitRPG #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 601 to 650 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (601, 610),
            "title": ["TIER 3 WRAITH CLAN", "SHADOW REALM SUBJUGATION"],
            "fallback_color": (15, 20, 30),
            "prompt": (
                "Cinematic 3D dark fantasy scene of an ethereal divine sovereign commanding vast legions of spectral wraiths with glowing cyan eyes, "
                "hovering over floating shattered crystal islands in the astral void. Spectral wisps, divine gold and cyan energy, 4K rendering."
            )
        },
        {
            "index": 2, "range": (611, 620),
            "title": ["DIVINE REALM EXPANSION", "FAITH CORE UPGRADE"],
            "fallback_color": (30, 25, 15),
            "prompt": (
                "Cinematic wide angle view of an expanding personal divine domain, towering celestial temples crowned with golden halos, "
                "millions of devout believers praying at grand marble altars beneath cosmic nebula skies, god rays, majestic scale."
            )
        },
        {
            "index": 3, "range": (621, 630),
            "title": ["SSS TALENT EVOLUTION", "PRISMATIC GODHOOD"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "Cinematic high fantasy portrait of a radiant supreme deity activating an SSS-rank ancient divine talent, "
                "kaleidoscopic prismatic runic circles revolving around outstretched palms, crackling with celestial thunder and golden stellar fire, dramatic lighting."
            )
        },
        {
            "index": 4, "range": (631, 640),
            "title": ["GOD REALM WARS", "CLAN CRUSHING ASSAULT"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic intense cosmic battle across orbital space, divine battleships and summoned celestial titans clashing against abyssal fiends "
                "and alien deity armies, stellar explosions lighting up asteroid rings, epic fantasy war atmosphere."
            )
        },
        {
            "index": 5, "range": (641, 650),
            "title": ["SUPREME DEITY ASCENSION", "UNIVERSAL PANTHEON"],
            "fallback_color": (20, 10, 30),
            "prompt": (
                "Cinematic panoramic shot of the supreme lord of all gods seated on a colossal crystalline throne carved into a dying star, "
                "crowned with cosmic authority, overlooking an endless armada of divine followers, radiant gold and obsidian tones, ultra-detailed 4K."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
