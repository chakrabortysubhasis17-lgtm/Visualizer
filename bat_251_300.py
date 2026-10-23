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

BUILD_DIR = "build_vampire_bat_loli_tyrant_251_300"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "game-descends-from-vampire-bat-to-loli-tyrant",
    "start_url": "https://mtl-novel.com/novel/game-descends-from-vampire-bat-to-loli-tyrant/chapter-251-death-is-not-the-end/",
    "start_chapter": 251,
    "end_chapter": 300,
    "default_topic": "Game Reality / Bloodline Evolution / Vampire Tyrant",

    # Concurrency Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-GuyNeural",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_vampire_bat_loli_tyrant_251_300.mp3",
    "final_video": "final_vampire_bat_loli_tyrant_251_300.mp4",
    "cover_image": "cover_vampire_bat_loli_tyrant_251_300.jpg",
    "timestamps_file": "youtube_timestamps_vampire_bat_loli_tyrant_251_300.txt",
    "subtitles_file": "subtitles_vampire_bat_loli_tyrant_251_300.srt",
    "payload_file": "youtube_upload_payload_vampire_bat_loli_tyrant_251_300.json",

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
    "video_title": "Game Descends: From Vampire Bat to Loli Tyrant | Ch 251 - 300 Full Audio Novel Marathon",
    "privacy_status": "unlisted",
    "tags": [
        "From Vampire Bat to Loli Tyrant", "Game Descends", "Vampire Tyrant Audiobook",
        "Evolution Novel", "LitRPG Audiobook", "Progression Fantasy", "Audiobook Marathon",
        "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the complete 50-chapter audio novel marathon of 'Game Descends: From Vampire Bat to Loli Tyrant' (Chapters 251 to 300).\n\n"
        "Witness supreme bloodline evolution, relentless dungeon domination, kingdom-scale conquests, and the unstoppable rise of the Vampire Monarch.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited, dramatized fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#VampireBatToLoliTyrant #GameDescends #VampireAudiobook #EvolutionNovel #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 251 to 300 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (251, 260),
            "title": ["DEATH IS NOT THE END", "ABYSSAL AWAKENING"],
            "fallback_color": (30, 10, 20),
            "prompt": (
                "Cinematic 3D fantasy scene of a petite gothic vampire queen with glowing crimson eyes and elegant black lace dress, "
                "standing atop an obsidian altar surrounded by swirling red necrotic mist and floating blood runes. Dark gothic cathedral background, "
                "intricate bat wing silhouettes, volumetric eerie lighting, highly detailed 4K rendering."
            )
        },
        {
            "index": 2, "range": (261, 270),
            "title": ["BLOODLINE ASCENSION", "SOVEREIGN AWAKENING"],
            "fallback_color": (40, 10, 15),
            "prompt": (
                "Cinematic dark fantasy portrait of a powerful young vampire sovereign commanding floating crystalline blood daggers, "
                "regal dark crown, glowing ruby aura crackling with crimson lightning, cold imperious gaze. Ancient vampire throne room background, "
                "marble columns, dynamic shadows, photorealistic 3D textures."
            )
        },
        {
            "index": 3, "range": (271, 280),
            "title": ["REALM EXPEDITION", "LEGION DEPLOYMENT"],
            "fallback_color": (20, 15, 30),
            "prompt": (
                "Cinematic wide angle fantasy scene of a massive undead vampire swarm and dark knights advancing across a devastated battlefield under a blood-red eclipsed moon, "
                "gothic banners tearing in the wind, mystical purple and crimson magic explosions in the background, high fantasy atmosphere, epic scale."
            )
        },
        {
            "index": 4, "range": (281, 290),
            "title": ["TYRANT'S WRATH", "ABYSSAL CLASH"],
            "fallback_color": (35, 10, 25),
            "prompt": (
                "Cinematic high-impact battle scene of a gothic vampire tyrant executing a devastating blood magic strike, shattering stone ramparts, "
                "swirling sonic shockwaves of dark red energy, sparks and pulverized debris flying, dynamic action pose, cinematic lighting."
            )
        },
        {
            "index": 5, "range": (291, 300),
            "title": ["APEX MONARCH", "ABSOLUTE DOMINATION"],
            "fallback_color": (25, 5, 20),
            "prompt": (
                "Cinematic fantasy scene of the supreme vampire monarch standing at the pinnacle of a colossal dark spire looking out over a conquered gothic fantasy empire at twilight, "
                "crimson capes billowing, ethereal glowing bats circling the towers, dramatic golden and blood-red twilight rays, ultra-detailed."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
