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

BUILD_DIR = "build_the_wandering_inn_026_050"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "the-wandering-inn",
    "start_url": "https://freewebnovel.com/novel/the-wandering-inn/chapter-30",
    "start_chapter": 26,
    "end_chapter": 50,
    "default_topic": "The Wandering Inn / LitRPG / Fantasy Innkeeper / Liscor",

    # Concurrency Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-GuyNeural",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_the_wandering_inn_026_050.mp3",
    "final_video": "final_the_wandering_inn_026_050.mp4",
    "cover_image": "cover_the_wandering_inn_026_050.jpg",
    "timestamps_file": "youtube_timestamps_the_wandering_inn_026_050.txt",
    "subtitles_file": "subtitles_the_wandering_inn_026_050.srt",
    "payload_file": "youtube_upload_payload_the_wandering_inn_026_050.json",

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
    "video_title": "The Wandering Inn | Ch 26 - 50 Full Audio Novel Marathon | Volume 1 Arc",
    "privacy_status": "unlisted",
    "tags": [
        "The Wandering Inn", "Wandering Inn Audiobook", "Erin Solstice", "Relc and Klbkch",
        "Horns of Hammerhand", "Skinner", "Liscor", "LitRPG Audiobook", "Fantasy Audiobook",
        "Progression Fantasy", "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the uninterrupted 25-chapter audio novel marathon of 'The Wandering Inn' (Chapters 26 to 50) — Volume 1.\n\n"
        "Follow Erin Solstice as the stakes escalate around the outskirts of Liscor. Witness the Horns of Hammerhand brave the ancient subterranean ruins, "
        "the growing bonds with Rags and the local Goblins, the terror emerging from the crypts beneath the city, and the desperate stand to protect the inn.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited, dramatized fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#TheWanderingInn #ErinSolstice #LitRPG #FantasyAudiobook #ProgressionFantasy #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 26 to 50 (5 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (26, 30),
            "title": ["RUINS EXPLORATION", "HORNS OF HAMMERHAND"],
            "fallback_color": (25, 20, 30),
            "prompt": (
                "Cinematic 3D fantasy scene of an adventuring bronze-rank party exploring an ancient, moss-covered subterranean stone ruin, "
                "a young half-elf cryomancer in silver-trimmed robes casting a glowing icy frost barrier, torches casting flickering orange light on damp carved stone pillars, "
                "atmospheric dust motes, 4K rendering."
            )
        },
        {
            "index": 2, "range": (31, 35),
            "title": ["GOBLIN ALLIANCE", "RAGS & THE HEARTH"],
            "fallback_color": (20, 25, 20),
            "prompt": (
                "Cinematic high-fantasy tavern scene inside a rustic stone inn, a sharp-eyed small female goblin with a scrap-cloth headband seated by the hearth, "
                "eating fresh bread and sweet juice offered by a gentle young human innkeeper, warm embers glowing, emotional narrative lighting, detailed textures."
            )
        },
        {
            "index": 3, "range": (36, 40),
            "title": ["THE CRYPT OF LISCOR", "ANCIENT TERROR"],
            "fallback_color": (15, 15, 25),
            "prompt": (
                "Cinematic dark fantasy scene deep beneath Liscor's floodplains in a massive vaulted tomb of cracked white stone, "
                "a monstrous skeletal abomination with draped flayed skins emerging from shadow, armored Drake guards and adventurers drawing weapons in fear, "
                "eerie bioluminescent green mist, high tension."
            )
        },
        {
            "index": 4, "range": (41, 45),
            "title": ["DEFENSE OF THE INN", "ANTINIUM VALOR"],
            "fallback_color": (30, 15, 20),
            "prompt": (
                "Cinematic intense action scene on the grassy plains outside the solitary inn at night, an Antinium warrior with gleaming black carapace "
                "wielding dual swords locked in desperate combat against swarming crypt ghouls and spiders, protectively holding the entryway, dramatic dynamic battle lighting."
            )
        },
        {
            "index": 5, "range": (46, 50),
            "title": ["THE SKINNER SIEGE", "HEARTH OF LISCOR"],
            "fallback_color": (35, 20, 15),
            "prompt": (
                "Cinematic wide angle climax shot of the stone inn under siege at daybreak, magical fiery projectiles and frost bursts lighting the foggy morning sky, "
                "the resilient young innkeeper holding high a glowing lantern of pure warm light rallying human, drake, and antinium survivors together, heroic 4K composition."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
