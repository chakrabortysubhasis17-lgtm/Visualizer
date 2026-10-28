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


BUILD_DIR = "build_origin_summoner_31_60"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "origin-summoner-all-my-summons-are-broken",
    "start_url": "https://freewebnovel.com/novel/origin-summoner-all-my-summons-are-broken/chapter-31",
    "start_chapter": 31,
    "end_chapter": 60,
    "default_topic": "Origin Summoner: All My Summons Are Broken / LitRPG / Fantasy / Overpowered Summons / Dungeon Raid",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook
    "intro_hook": "Awakening as an origin summoner in a world of supreme beasts, one young summoner unlocks broken divine entities that defy the laws of reality.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_origin_summoner_31_60.mp3",
    "final_video": "final_origin_summoner_31_60.mp4",
    "cover_image": "cover_origin_summoner_31_60.jpg",
    "timestamps_file": "youtube_timestamps_origin_summoner_31_60.txt",
    "subtitles_file": "subtitles_origin_summoner_31_60.srt",
    "payload_file": "youtube_upload_payload_origin_summoner_31_60.json",

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
    "video_title": "Origin Summoner: All My Summons Are Broken | Ch 31 - 60 Audiobook Marathon | Mythical Awakening",
    "privacy_status": "unlisted",
    "tags": [
        "Origin Summoner", "All My Summons Are Broken", "Origin Summoner Audiobook",
        "LitRPG Audiobook", "Fantasy Audiobook", "Overpowered Summons", "Summoner Progression",
        "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "This episode, we step right back into the story, continuing exactly where we left off in our previous episode of this series.\n\n"
        "Experience 'Origin Summoner: All My Summons Are Broken' (Chapters 31 to 60) — Escalation of Divine Entities.\n\n"
        "As the dungeon's ancient mysteries intensify, Orion's supposedly broken summon contracts reveal terrifying depths of cosmic authority, "
        "defying conventional rank boundaries and stunning both guild elites and nightmare-tier entities alike.\n\n"
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
        "#OriginSummoner #AllMySummonsAreBroken #LitRPG #FantasyAudiobook #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks for Chapters 31 to 60
    "blocks": [
        {
            "index": 1, "range": (31, 38),
            "title": ["DEEPER SECTORS", "SHADOWED DEPTHS"],
            "fallback_color": (15, 18, 28),
            "prompt": (
                "Cinematic subterranean cavern with bioluminescent crystals embedded in craggy obsidian rock walls, "
                "a young summoner walking cautiously along an ancient stone bridge over a misty chasm, glowing blue and purple magical mists, 4K masterpiece."
            )
        },
        {
            "index": 2, "range": (39, 46),
            "title": ["PRIMORDIAL CONTRACT", "BROKEN ENTITY"],
            "fallback_color": (22, 16, 32),
            "prompt": (
                "Cinematic summoning circle carved into ancient stone floor flaring with intense golden and violet light, "
                "an ethereal colossal divine beast materializing out of the rift with towering horns and cosmic eyes, dramatic lighting, 4K digital art."
            )
        },
        {
            "index": 3, "range": (47, 53),
            "title": ["BOSS ENCOUNTER", "OVERPOWERED MIGHT"],
            "fallback_color": (28, 15, 15),
            "prompt": (
                "Massive underground dungeon throne room, a colossal armored beast king towering over stone ruins, "
                "opposing a calm summoner whose surrounding divine aura bends the spatial fabric in crimson ripples, epic atmospheric clash, 4K."
            )
        },
        {
            "index": 4, "range": (54, 60),
            "title": ["ASCENDANT DOMINION", "UNRIVALED SUMMONER"],
            "fallback_color": (16, 25, 26),
            "prompt": (
                "High-angle cinematic view of a victorious young summoner standing at the center of a conquered dungeon core, "
                "swirling ethereal energy particles ascending into the cavern ceiling, glowing status glyphs in the air, hyper-detailed fantasy render."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
