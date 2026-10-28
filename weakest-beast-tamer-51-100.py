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


BUILD_DIR = "build_weakest_beast_tamer_51_100"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "weakest-beast-tamer-gets-all-sss-dragons",
    "start_url": "https://freewebnovel.com/novel/weakest-beast-tamer-gets-all-sss-dragons/chapter-51",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "Weakest Beast Tamer Gets All SSS Dragons / Beast Taming / LitRPG / Fantasy / SSS-Rank Dragons / Overpowered Awakening",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook
    "intro_hook": "Dismissed by everyone as the weakest beast tamer with no future, one young tamer awakens a mythical lineage to command supreme SSS-rank ancient dragons.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_weakest_beast_tamer_51_100.mp3",
    "final_video": "final_weakest_beast_tamer_51_100.mp4",
    "cover_image": "cover_weakest_beast_tamer_51_100.jpg",
    "timestamps_file": "youtube_timestamps_weakest_beast_tamer_51_100.txt",
    "subtitles_file": "subtitles_weakest_beast_tamer_51_100.srt",
    "payload_file": "youtube_upload_payload_weakest_beast_tamer_51_100.json",

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
    "video_title": "Weakest Beast Tamer Gets All SSS Dragons | Ch 51 - 100 Full Audio Novel Marathon | Sovereign of Dragons",
    "privacy_status": "unlisted",
    "tags": [
        "Weakest Beast Tamer", "All SSS Dragons", "Weakest Beast Tamer Audiobook",
        "Beast Tamer LitRPG", "Dragon Tamer", "Fantasy Audiobook", "Overpowered MC",
        "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "This episode, we step right back into the story, continuing exactly where we left off in our previous episode of this series.\n\n"
        "Experience 'Weakest Beast Tamer Gets All SSS Dragons' (Chapters 51 to 100) — The Sovereign of Dragons Arc.\n\n"
        "Having shaken off the ridicule of his peers, our young beast tamer guides his growing brood of SSS-rank dragons across perilous uncharted frontiers, "
        "unlocking ancient dragon bloodlines and asserting unchallenged dominance over rival beastmasters and foreign empires.\n\n"
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
        "#WeakestBeastTamer #SSSDragons #LitRPG #FantasyAudiobook #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks for Chapters 51 to 100
    "blocks": [
        {
            "index": 1, "range": (51, 62),
            "title": ["DRAGON EVOLUTION", "ANCIENT SANCTUARY"],
            "fallback_color": (24, 18, 12),
            "prompt": (
                "Cinematic high fantasy volcanic sanctum, crystalline magma rivers flowing past colossal stone dragon carvings, "
                "a young beast tamer witnessing an adolescent gold-scaled dragon undergoing a divine evolution in radiant light, 4K masterpiece."
            )
        },
        {
            "index": 2, "range": (63, 75),
            "title": ["FROST PEAK EXPEDITION", "ICE DRAGON SOVEREIGN"],
            "fallback_color": (14, 22, 30),
            "prompt": (
                "Towering glaciers and snow-capped mountain ridges under an aurora-lit sky, "
                "an enormous crystalline ice dragon unfurling diamond-tipped wings beside its fearless tamer, swirling blizzard particles, 4K digital art."
            )
        },
        {
            "index": 3, "range": (76, 88),
            "title": ["WAR OF THE TAMERS", "CONTINENTAL CLASH"],
            "fallback_color": (28, 14, 16),
            "prompt": (
                "Epic grand battlefield across arid canyon plains, armies of armored beast tamers with mythical beasts clashing, "
                "multiple SSS-rank dragons unleashing torrents of elemental breath across the sky, cinematic volumetric lighting, 4K."
            )
        },
        {
            "index": 4, "range": (89, 100),
            "title": ["DRAGON MONARCH ASCENSION", "PEERLESS DOMINION"],
            "fallback_color": (18, 15, 28),
            "prompt": (
                "Majestic floating citadel above the cloud sea at sunset, an ascendant dragon tamer surrounded by nine supreme ancient dragons in formation, "
                "cosmic constellations glowing above, masterpiece fantasy visual composition."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
