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


BUILD_DIR = "build_dragon_genesis_1_50"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "dragon-genesis-i-can-create-dragons",
    "start_url": "https://freewebnovel.com/novel/dragon-genesis-i-can-create-dragons/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Dragon Genesis: I Can Create Dragons / Dragon Creation / LitRPG / Fantasy / Beast Taming / Dragon Lord Ascension",

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook
    "intro_hook": "Awakening a god-tier dragon genesis talent in a world of fierce beast tamers, an underestimated youth begins breeding primordial dragons that defy the laws of nature.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_dragon_genesis_1_50.mp3",
    "final_video": "final_dragon_genesis_1_50.mp4",
    "cover_image": "cover_dragon_genesis_1_50.jpg",
    "timestamps_file": "youtube_timestamps_dragon_genesis_1_50.txt",
    "subtitles_file": "subtitles_dragon_genesis_1_50.srt",
    "payload_file": "youtube_upload_payload_dragon_genesis_1_50.json",

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
    "video_title": "Dragon Genesis: I Can Create Dragons | Ch 1 - 50 Full Audiobook | Rise of the Dragon Creator",
    "privacy_status": "unlisted",
    "tags": [
        "Dragon Genesis I Can Create Dragons", "Dragon Genesis", "Create Dragons Audiobook",
        "Beast Tamer Audiobook", "LitRPG Audiobook", "Fantasy Audiobook", "Dragon Creation",
        "Overpowered MC", "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Welcome to the opening episode of this series. A brand-new adventure awaits, and we are glad to have you with us.\n\n"
        "Experience 'Dragon Genesis: I Can Create Dragons' (Chapters 1 to 50) — The Origin of the Dragon Lord.\n\n"
        "In a harsh realm where one's bonded familiar defines destiny, our protagonist unlocks the forbidden ability to synthesize, "
        "mutate, and birth primordial dragon lineages from scratch. From weak humble origins to shocking Academy trials, witness the "
        "hatching of mythical apex predators that shake the foundations of the beast-taming world.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "🎙️ NARRATION: en-US-ChristopherNeural (Deep Cinematic Baritone).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audio presentation is an edited fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#DragonGenesis #ICanCreateDragons #BeastTaming #LitRPG #FantasyAudiobook #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks across Chapters 1 to 50
    "blocks": [
        {
            "index": 1, "range": (1, 12),
            "title": ["AWAKENING TALENT", "THE FORBIDDEN GENESIS MATRIX"],
            "fallback_color": (20, 16, 26),
            "prompt": (
                "Cinematic high-fantasy ritual chamber with glowing arcane floor runes, "
                "a young determined beast tamer holding a glowing primordial dragon egg pulsing with golden lightning, "
                "ethereal dragon silhouettes swirling in the misty ambient light, hyper-detailed volumetric lighting, 4K."
            )
        },
        {
            "index": 2, "range": (13, 25),
            "title": ["FIRST HATCHLING", "PRIMORDIAL FLAME MUTATION"],
            "fallback_color": (28, 14, 12),
            "prompt": (
                "Dramatic laboratory cavern lit by blazing magma veins, "
                "a fierce juvenile crimson dragon with jagged obsidian horns roaring atop a stone anvil, "
                "swirling embers and dynamic fire shockwaves illuminating the cavern walls, gritty fantasy art, 4K digital painting."
            )
        },
        {
            "index": 3, "range": (26, 38),
            "title": ["ACADEMY ASSESSMENT", "SHATTERING CONVENTIONS"],
            "fallback_color": (16, 22, 28),
            "prompt": (
                "Massive ancient stone arena surrounded by tiered spectator seats beneath a bright sky, "
                "the young dragon creator standing calmly in the arena center as an awe-inspiring serpentine frost dragon uncoils around him, "
                "shattered ice crystals glittering in the air, cinematic framing, 4K masterpiece."
            )
        },
        {
            "index": 4, "range": (39, 50),
            "title": ["WILDLAND EXPEDITION", "LORD OF THE DRAGON FLOCK"],
            "fallback_color": (22, 18, 14),
            "prompt": (
                "Panoramic vista of a sprawling untamed canyon wilderness at sunset, "
                "the confident dragonmaster standing on a high cliff edge with multiple distinct mythical dragons—flame, thunder, and shadow—perched alongside him, "
                "crimson and golden clouds catching twilight rays, epic concept art, 4K."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
