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


BUILD_DIR = "build_demon_lord_villager_101_150"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "reincarnated-in-the-alternate-world-im-a-demonic-lord-as-well-as-a-villager",
    "start_url": "https://freewebnovel.com/novel/reincarnated-in-the-alternate-world-im-a-demonic-lord-as-well-as-a-villager/chapter-101",
    "start_chapter": 101,
    "end_chapter": 150,
    "default_topic": "I'm a Demonic Lord as Well as a Villager / Isekai / Dual Identity / Fantasy / Overpowered Demon Lord",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook
    "intro_hook": "Balancing a tranquil rustic life as an ordinary villager with absolute sovereignty as a feared demon lord, one reincarnated soul manipulates the fate of nations from the shadows.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_demon_lord_villager_101_150.mp3",
    "final_video": "final_demon_lord_villager_101_150.mp4",
    "cover_image": "cover_demon_lord_villager_101_150.jpg",
    "timestamps_file": "youtube_timestamps_demon_lord_villager_101_150.txt",
    "subtitles_file": "subtitles_demon_lord_villager_101_150.srt",
    "payload_file": "youtube_upload_payload_demon_lord_villager_101_150.json",

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
    "video_title": "I'm a Demonic Lord as Well as a Villager | Ch 101 - 150 Full Audiobook Marathon | Shadow Ruler",
    "privacy_status": "unlisted",
    "tags": [
        "Demonic Lord and Villager", "Demon Lord Villager", "Isekai Audiobook",
        "Dual Identity", "Fantasy Audiobook", "Overpowered MC", "Villager Demon Lord",
        "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "This episode, we step right back into the story, continuing exactly where we left off in our previous episode of this series.\n\n"
        "Experience 'Reincarnated in the Alternate World: I'm a Demonic Lord as Well as a Villager' (Chapters 101 to 150) — The Shadow Sovereign Arc.\n\n"
        "While maintaining his peaceful everyday facade in a humble farming hamlet, our protagonist commands terrifying demonic armies, "
        "thwarting royal schemes and overwhelming legendary knights without ever exposing his quiet village life.\n\n"
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
        "#DemonLordVillager #IsekaiAudiobook #FantasyAudiobook #OverpoweredMC #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks for Chapters 101 to 150
    "blocks": [
        {
            "index": 1, "range": (101, 112),
            "title": ["RUSTIC COUNTRYSIDE", "HIDDEN POWER"],
            "fallback_color": (20, 24, 15),
            "prompt": (
                "Peaceful European medieval farming village surrounded by golden wheat fields at sunset, "
                "a humble young villager carrying firewood, casting an ominous dark demonic shadow with glowing crimson eyes, cinematic lighting, 4K."
            )
        },
        {
            "index": 2, "range": (113, 125),
            "title": ["DEMON REALM THRONE", "SOVEREIGN COMMAND"],
            "fallback_color": (25, 12, 28),
            "prompt": (
                "Grand Gothic demon castle hall illuminated by floating purple flames and arched stained glass, "
                "a supreme demonic lord seated on an obsidian throne, demonic generals and shadow wraiths kneeling in allegiance, 4K digital art."
            )
        },
        {
            "index": 3, "range": (126, 138),
            "title": ["KNIGHTS OF THE REALM", "CLASH OF FACTIONS"],
            "fallback_color": (16, 20, 30),
            "prompt": (
                "Misty forest valley skirmish between royal holy paladins in gleaming silver plate armor and terrifying shadowy demonic beasts, "
                "golden holy magic colliding against black abyssal magic waves, volumetric fog, 4K masterpiece."
            )
        },
        {
            "index": 4, "range": (139, 150),
            "title": ["DUAL SOVEREIGN", "PEACE & DOMINION"],
            "fallback_color": (18, 16, 22),
            "prompt": (
                "Split-composition cinematic portrait, one half showing a serene smiling villager under a warm sunny sky, "
                "the other half revealing a terrifying horned Demon Lord wreathed in dark abyssal lightning, masterpiece fantasy concept art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))