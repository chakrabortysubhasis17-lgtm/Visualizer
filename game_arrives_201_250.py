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


BUILD_DIR = "build_game_arrives_evolve_talents_201_250"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "game-arrives-i-can-evolve-my-talents-infinitely",
    "start_url": "https://mtl-novel.com/novel/game-arrives-i-can-evolve-my-talents-infinitely/chapter-200-the-rebel/",
    "start_chapter": 201,
    "end_chapter": 250,
    "default_topic": "Game Arrives: I Can Evolve My Talents Infinitely / Global Reality Descent / Infinite Talent Evolution / SSS Rank Progression",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook (start_chapter > 1 -> continuation recap)
    "intro_hook": "We return as reality merges further with the primordial game world, where infinite talent evolution allows our protagonist to shatter divine boundaries and suppress global calamity bosses.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_game_arrives_evolve_talents_201_250.mp3",
    "final_video": "final_game_arrives_evolve_talents_201_250.mp4",
    "cover_image": "cover_game_arrives_evolve_talents_201_250.jpg",
    "timestamps_file": "youtube_timestamps_game_arrives_evolve_talents_201_250.txt",
    "subtitles_file": "subtitles_game_arrives_evolve_talents_201_250.srt",
    "payload_file": "youtube_upload_payload_game_arrives_evolve_talents_201_250.json",

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
    "video_title": "Game Arrives: I Can Evolve My Talents Infinitely | Ch 201 - 250 Full Marathon | Divine Evolution Arc",
    "privacy_status": "unlisted",
    "tags": [
        "Game Arrives I Can Evolve My Talents Infinitely", "Evolve My Talents Infinitely",
        "Infinite Evolution", "LitRPG Audiobook", "Progression Fantasy", "Reality Descent",
        "SSS Talent", "System Apocalypse", "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the complete 50-chapter audio novel marathon of 'Game Arrives: I Can Evolve My Talents Infinitely' (Chapters 201 to 250) — the Divine Evolution Arc.\n\n"
        "As the boundary between reality and the cosmic game world collapses completely, high-tier catastrophic entities and rebellious factions descend. "
        "With the unparalleled power of infinite talent mutation, our protagonist continues upgrading sub-skills into god-tier divine authorities, "
        "crushing rival powerhouses and dominating sovereign battlefields.\n\n"
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
        "#GameArrives #InfiniteEvolution #LitRPG #ProgressionFantasy #SystemApocalypse #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 201 to 250 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (201, 210),
            "title": ["REBEL CONFRONTATION", "SOVEREIGN AWAKENING"],
            "fallback_color": (20, 20, 30),
            "prompt": (
                "Cinematic high-detail wide shot of a modern city crumbling as massive glowing blue fantasy portals tear through skyscrapers, "
                "a calm protagonist hovering above the skyline surrounded by multi-layered translucent golden talent rings, "
                "rebel factions and rogue hunters looking up in awe, dramatic volumetric storm lighting, 4K resolution."
            )
        },
        {
            "index": 2, "range": (211, 220),
            "title": ["TALENT UPGRADE", "TIER COLLAPSE"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "Cinematic close-up action sequence inside a shattered celestial dimension, hands wrapped in iridescent divine lightning "
                "mutating an ancient talent orb into SSS-rank mythical power, floating holographic skill trees and stat indicators, "
                "intense particle effects, hyper-detailed rendering."
            )
        },
        {
            "index": 3, "range": (221, 230),
            "title": ["GLOBAL INVASION", "ABYSS SUPPRESSION"],
            "fallback_color": (30, 15, 20),
            "prompt": (
                "Cinematic catastrophic battle on an apocalyptic plains landscape, towering abyssal fiends charging across cracked earth, "
                "the evolved warrior summoning a colossal phantom blade that slices through the cloud cover and incinerates the vanguard, "
                "epic cinematic composition, glowing embers and fiery smoke."
            )
        },
        {
            "index": 4, "range": (231, 240),
            "title": ["DIVINE MATRIX", "GOD-KILLING MOMENTUM"],
            "fallback_color": (15, 25, 30),
            "prompt": (
                "Cinematic grand confrontation in an alien cosmic sanctuary, floating monoliths inscribed with glowing primordial script, "
                "an armored sovereign unleashing a shockwave of evolved divine force against an ancient slumbering calamity entity, "
                "dramatic rim lighting, deep contrast, masterpiece."
            )
        },
        {
            "index": 5, "range": (241, 250),
            "title": ["PEAK TRANSCENDENCE", "UNCONTESTED DOMINION"],
            "fallback_color": (25, 25, 35),
            "prompt": (
                "Cinematic heroic composition standing atop a crystalline orbital spire overlooking Earth enveloped in shimmering game grids, "
                "the supreme player adorned in majestic celestial robes with infinite glowing talent auras pulsing behind him, "
                "sunrise over the curved planetary horizon, breathtaking 4K render."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
