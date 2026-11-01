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


BUILD_DIR = "build_dragon_genesis_51_100"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters (Chapters 51 - 100 Marathon)
    "novel_slug": "dragon-genesis",
    "start_url": "https://freewebnovel.com/novel/dragon-genesis-i-can-create-dragons/chapter-51",
    "start_chapter": 51,
    "end_chapter": 100,
    "is_start": False,
    "default_topic": (
        "Dragon Genesis: I Can Create Dragons / LitRPG / Progression Fantasy / "
        "Draconic Bloodline Creation / Ancient Dragon Hatching / Sovereign Beast Master / "
        "Elemental Dragon Armies / Abyssal Invasion"
    ),

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook
    "intro_hook": "Synthesizing divine dragon bloodlines from primordial catalysts, our beast master unleashes world-ending draconic evolutions across continental frontiers.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_dragon_genesis_51_100.mp3",
    "final_video": "final_dragon_genesis_51_100.mp4",
    "cover_image": "cover_dragon_genesis_51_100.jpg",
    "timestamps_file": "youtube_timestamps_dragon_genesis_51_100.txt",
    "subtitles_file": "subtitles_dragon_genesis_51_100.srt",
    "payload_file": "youtube_upload_payload_dragon_genesis_51_100.json",

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
    "video_title": "Dragon Genesis: I Can Create Dragons | Ch 51 - 100 Full Audiobook Marathon",
    "privacy_status": "unlisted",
    "tags": [
        "Dragon Genesis", "I Can Create Dragons", "Dragon Genesis Audiobook",
        "LitRPG Audiobook", "Progression Fantasy", "Create Dragons", "Beast Taming Audiobook",
        "Dragon Tamer", "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "We dive into Chapters 51 to 100 of 'Dragon Genesis: I Can Create Dragons'.\n\n"
        "With ancient dragon catalysts unlocked and primordial gene matrices perfected, our protagonist synthesizes "
        "legendary draconic beasts that defy the world's common sense. Witness catastrophic dragon breath clashes, "
        "terrifying realm wars, and the birth of sovereign elemental dragon legions.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "🎙️ NARRATION: en-US-ChristopherNeural (Deep Cinematic Baritone).\n"
        "🎼 SOUNDSCAPE: Low-Volume Dynamic BGM Beds (-27 dB) + Targeted Context SFX.\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audio presentation is an edited fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#DragonGenesis #ICanCreateDragons #LitRPG #ProgressionFantasy #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks partitioned across Chapters 51 to 100
    "blocks": [
        {
            "index": 1, "range": (51, 62),
            "title": ["PRIMORDIAL HATCHING", "DRACONIC BLOODLINE SYNTHESIS"],
            "fallback_color": (28, 14, 10),
            "prompt": (
                "A powerful young summoner standing before a glowing ancient draconic incubation altar in a vast volcanic cavern, "
                "a colossal dragon egg radiating crackling crimson flames and golden runic veins cracking open, "
                "majestic newborn winged dragon hatchling emerging with glowing molten eyes, dark epic fantasy concept art, 4K digital painting."
            )
        },
        {
            "index": 2, "range": (63, 75),
            "title": ["ELEMENTAL BREATH", "FRONTIER DOMINATION"],
            "fallback_color": (12, 22, 34),
            "prompt": (
                "Epic fantasy battlefield clash atop a shattered mountain plateau, a colossal azure storm dragon and a titanic obsidian fire dragon "
                "unleashing dual beams of devastating lightning and cosmic fire against hordes of abyssal chittering fiends, "
                "dramatic volumetric clouds, blinding energy arcs, masterpiece 4K digital illustration."
            )
        },
        {
            "index": 3, "range": (76, 88),
            "title": ["SOVEREIGN EVOLUTION", "ANCIENT SANCTUARY"],
            "fallback_color": (14, 28, 20),
            "prompt": (
                "Ancient mystical dragon shrine overgrown with glowing emerald moss and crystalline dragon fossils, "
                "a sovereign dragon tamer accompanied by a serpentine jade emerald dragon coiling across massive marble columns, "
                "atmospheric misty lighting, glowing spirit particles, deep fantasy matte painting, 4K resolution."
            )
        },
        {
            "index": 4, "range": (89, 100),
            "title": ["DRAGON LEGION REIGN", "CELESTIAL DRAGON GENESIS"],
            "fallback_color": (24, 16, 32),
            "prompt": (
                "Panoramic cinematic vista overlooking an empire engulfed in purple dimensional rifts at twilight, "
                "a majestic dragon sovereign commanding an entire fleet of gigantic armored elemental dragons soaring through the skies, "
                "epic scale, golden hour lighting, cinematic composition, photorealistic fantasy masterpiece, 4K wallpaper."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
