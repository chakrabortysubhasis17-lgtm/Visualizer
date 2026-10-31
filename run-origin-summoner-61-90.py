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


BUILD_DIR = "build_origin_summoner_61_90"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters (Chapters 61 - 90 Marathon)
    "novel_slug": "origin-summoner",
    "start_url": "https://freewebnovel.com/novel/origin-summoner-all-my-summons-are-broken/chapter-61",
    "start_chapter": 61,
    "end_chapter": 90,
    "is_start": False,
    "default_topic": "Origin Summoner / All My Summons Are Broken / LitRPG / Progression Fantasy / Broken Mythical Summons / Beast Taming / Dimensional Gate Expeditions",

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook
    "intro_hook": "Pushing beyond the frontier boundaries, our summoner unseals forbidden contracts and unleashes catastrophic evolutions across high-tier rift dungeons.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_origin_summoner_61_90.mp3",
    "final_video": "final_origin_summoner_61_90.mp4",
    "cover_image": "cover_origin_summoner_61_90.jpg",
    "timestamps_file": "youtube_timestamps_origin_summoner_61_90.txt",
    "subtitles_file": "subtitles_origin_summoner_61_90.srt",
    "payload_file": "youtube_upload_payload_origin_summoner_61_90.json",

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
    "video_title": "Origin Summoner: All My Summons Are Broken | Ch 61 - 90 Full Audiobook Marathon",
    "privacy_status": "unlisted",
    "tags": [
        "Origin Summoner", "All My Summons Are Broken", "Origin Summoner Audiobook",
        "LitRPG Audiobook", "Progression Fantasy", "Broken Summons", "Beast Taming Audiobook",
        "Audiobook Marathon", "Web Novel Audiobook", "FreeWebNovel", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "We continue the journey with Chapters 61 to 90 of 'Origin Summoner: All My Summons Are Broken'.\n\n"
        "Facing deeper rifts, dangerous beast master factions, and increasingly unstable dimensional anomalies, "
        "our summoner commands his mutated, world-breaking summons into war. Witness new covenant breakthroughs, "
        "overpowered skill synergies, and intense tactical clashes.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "🎙️ NARRATION: en-US-ChristopherNeural (Deep Cinematic Baritone).\n"
        "🎼 SOUNDSCAPE: Low-Volume Dynamic BGM Beds + Targeted Context SFX.\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audio presentation is an edited fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#OriginSummoner #AllMySummonsAreBroken #LitRPG #ProgressionFantasy #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks partitioned across Chapters 61 to 90
    "blocks": [
        {
            "index": 1, "range": (61, 67),
            "title": ["DEEP RIFT INVASION", "MUTATED SUMMON ASCENSION"],
            "fallback_color": (16, 20, 28),
            "prompt": (
                "A powerful male summoner standing at the precipice of a shattered subterranean cavern rift, "
                "surrounded by radiant cosmic summoning circles on the stone ground, gigantic shadowy ethereal mutated mythical beasts "
                "manifesting with glowing arcane eyes and crackling lightning, dark fantasy concept art, highly detailed, 4K digital painting."
            )
        },
        {
            "index": 2, "range": (68, 75),
            "title": ["TACTICAL DOMINATION", "FORBIDDEN EVOLUTIONS"],
            "fallback_color": (28, 14, 18),
            "prompt": (
                "Epic fantasy battlefield clash inside a crystal-encrusted cavern ruin, colossal elemental summon beasts unleashing "
                "blazing waves of azure flames and shockwaves against hordes of crystalline abyss monsters, dramatic cinematic lighting, "
                "volumetric smoke, glowing arcane particles, masterpiece, 4K."
            )
        },
        {
            "index": 3, "range": (76, 82),
            "title": ["DIMENSIONAL EXPEDITION", "THE ABYSS CRADLE"],
            "fallback_color": (14, 26, 22),
            "prompt": (
                "Ancient mystical jungle sanctuary overgrown with luminescent alien flora and colossal monolithic ruin gates, "
                "a summoner walking alongside an imposing winged mythical chimera companion radiating soft emerald mana wisps, "
                "atmospheric fog, deep fantasy environment concept art, 4K resolution."
            )
        },
        {
            "index": 4, "range": (83, 90),
            "title": ["COVENANT BREAKER", "SOVEREIGN SUMMONER"],
            "fallback_color": (22, 16, 30),
            "prompt": (
                "Dramatic panoramic vantage overlooking a stormy dark fantasy citadel engulfed in swirling purple dimensional rifts, "
                "a confident summoner holding a glowing runic grimoire aloft as gigantic spectral dragon-like leviathans coil across the sky, "
                "cinematic composition, intricate details, vivid lighting, 4K wallpaper."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))