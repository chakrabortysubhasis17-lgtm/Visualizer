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


BUILD_DIR = "build_origin_summoner_1_30"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "origin-summoner-all-my-summons-are-broken",
    "start_url": "https://freewebnovel.com/novel/origin-summoner-all-my-summons-are-broken/chapter-1",
    "start_chapter": 1,
    "end_chapter": 30,
    "default_topic": "Origin Summoner: All My Summons Are Broken / LitRPG / Fantasy / Summoning System / Overpowered Beast Awakening",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook (Episode 1 introduces the premise)
    "intro_hook": "Awakening as an origin summoner in a world of supreme beasts, one young summoner unlocks broken divine entities that defy the laws of reality.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_origin_summoner_1_30.mp3",
    "final_video": "final_origin_summoner_1_30.mp4",
    "cover_image": "cover_origin_summoner_1_30.jpg",
    "timestamps_file": "youtube_timestamps_origin_summoner_1_30.txt",
    "subtitles_file": "subtitles_origin_summoner_1_30.srt",
    "payload_file": "youtube_upload_payload_origin_summoner_1_30.json",

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
    "video_title": "Origin Summoner: All My Summons Are Broken | Ch 1 - 30 Full Audio Novel Marathon | Origin Awakening",
    "privacy_status": "unlisted",
    "tags": [
        "Origin Summoner", "All My Summons Are Broken", "Origin Summoner Audiobook",
        "LitRPG Audiobook", "Summoner System", "Fantasy Audiobook", "Overpowered MC",
        "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the beginning of 'Origin Summoner: All My Summons Are Broken' (Chapters 1 to 30) — The Origin Awakening Arc.\n\n"
        "Witness the awakening of a summoner whose contracts defy comprehension, conjuring celestial horrors, "
        "mythical beasts, and broken anomalies that shake the foundation of the world.\n\n"
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
        "#OriginSummoner #LitRPG #FantasyAudiobook #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Arc Visual Blocks for Chapters 1 to 30
    "blocks": [
        {
            "index": 1, "range": (1, 8),
            "title": ["ORIGIN CONTRACT", "FIRST SUMMONING"],
            "fallback_color": (15, 20, 30),
            "prompt": (
                "Cinematic high-fantasy summoning altar with massive glowing runic circles etched in stone, "
                "a young summoner extending a hand as a colossal celestial shadow manifests through violet and gold energy portals, 4K resolution."
            )
        },
        {
            "index": 2, "range": (9, 15),
            "title": ["BROKEN ANOMALY", "BEAST AWAKENING"],
            "fallback_color": (25, 15, 20),
            "prompt": (
                "Cinematic fantasy battlefield with a mythical winged beast glowing with divine energy, "
                "dark shattered earth floating in anti-gravity, intense arcane aura and atmospheric lightning, epic scale 4K."
            )
        },
        {
            "index": 3, "range": (16, 22),
            "title": ["SUMMONER ACADEMY", "PEERLESS DOMINION"],
            "fallback_color": (20, 25, 20),
            "prompt": (
                "Cinematic grand fantasy academy colosseum, floating stone pillars, crowds watching in awe as "
                "overpowered summoning spirits surround a calm confident summoner standing in the center arena, volumetric morning light."
            )
        },
        {
            "index": 4, "range": (23, 30),
            "title": ["CELESTIAL TIER", "SOVEREIGN ASCENT"],
            "fallback_color": (25, 20, 10),
            "prompt": (
                "Cinematic sweeping fantasy night landscape under a shattered starry nebula sky, "
                "a sovereign summoner surrounded by towering mythical guardian titans radiating golden and azure light, masterpiece 4K render."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))