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

def purge_corrupt_cache(build_dir: str):
    """Purges placeholder dummy files from earlier connection dropouts."""
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
                if len(rows) < 8 or any("Exposition details continue" in r.get("text", "") for r in rows):
                    os.remove(fpath)
                    removed += 1
            except Exception:
                try:
                    os.remove(fpath)
                    removed += 1
                except OSError:
                    pass
    if removed > 0:
        print(f"[Pre-Flight Cleanup] [✓] Purged {removed} placeholder cache files to guarantee clean scraping.", flush=True)

BUILD_DIR = "build_dungeon_of_niflheim_1_35"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "dungeon-of-niflheim",
    "start_url": "https://freewebnovel.com/novel/dungeon-of-niflheim/chapter-1",
    "start_chapter": 1,
    "end_chapter": 35,
    "default_topic": "Dungeon of Niflheim",

    # Concurrency Settings & Narrator Lock
    "batch_size": 7,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook
    "intro_hook": "Awakening in the frozen depths of the mythical Niflheim realm, an unlikely soul must master frostbound dungeon architecture, forge deadly traps, and command ancient undead forces to survive.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_dungeon_of_niflheim_1_35.mp3",
    "final_video": "final_dungeon_of_niflheim_1_35.mp4",
    "cover_image": "cover_dungeon_of_niflheim_1_35.jpg",
    "timestamps_file": "youtube_timestamps_dungeon_of_niflheim_1_35.txt",
    "subtitles_file": "subtitles_dungeon_of_niflheim_1_35.srt",
    "payload_file": "youtube_upload_payload_dungeon_of_niflheim_1_35.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "FROST CORE AWAKENING & LABYRINTH DEFENSE! [Ch 1-35] | Dungeon of Niflheim Dark Fantasy Audiobook",
    "tags": [
        "Dungeon of Niflheim", "Dungeon Core", "LitRPG Audiobook", "Progression Fantasy",
        "Dark Fantasy", "Necromancy", "Frost Magic", "Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to the opening marathon of 'Dungeon of Niflheim' covering Chapters 1 through 35!\n\n"
        "Cast into the primordial realm of frost and mist, our protagonist must awaken an ancient dungeon core, "
        "repel invading expeditions, construct lethal labyrinthine defense layers, and bend the frigid horrors of "
        "Niflheim to his will. Experience this arc with multi-voice neural TTS, adaptive soundscapes, "
        "and complete soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more chapters and progression updates!\n\n"
        "#DungeonOfNiflheim #DungeonCore #LitRPG #DarkFantasy #ProgressionFantasy #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks covering Ch 1 to 35: 1-9, 10-18, 19-27, 28-35)
    "blocks": [
        {
            "index": 1, "range": (1, 9),
            "title": ["CORE AWAKENING", "REALM OF FROST"],
            "fallback_color": (15, 25, 40),
            "prompt": (
                "Cinematic 3D dark fantasy illustration of a glowing ethereal glacial dungeon core hovering in the center of an ancient ice cavern, "
                "frost runes spiraling outward across cracked frozen stone floor, mysterious pale protagonist reaching toward the crystal. "
                "Subterranean Niflheim mist, towering icicles catching glowing blue ambient illumination, crisp textures, realistic volumetric lighting."
            )
        },
        {
            "index": 2, "range": (10, 18),
            "title": ["LABYRINTH DEFENSE", "FROZEN SENTINELS"],
            "fallback_color": (20, 20, 35),
            "prompt": (
                "Cinematic 3D dark fantasy view of armored frost skeletons and icy wraiths standing vigilant along a narrow cavern chasm, "
                "frost traps glowing with cyan danger runes as an invading adventurer party approaches with torches in the distance. "
                "Spike-laden ice pillars, drifting snow particles, chilling dramatic rim lighting, highly detailed 4k render."
            )
        },
        {
            "index": 3, "range": (19, 27),
            "title": ["SOUL HARVEST", "ARCHITECTURAL EXPANSION"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "Cinematic 3D fantasy scene of the dungeon core expanding into a grand subterranean throne room carved from black obsidian and permafrost, "
                "the hooded dungeon master manipulating floating translucent blue interface schematics and runic stat arrays. "
                "Swirling soul wisps being absorbed into the walls, cold crystalline glow, atmospheric depth, medium shot."
            )
        },
        {
            "index": 4, "range": (28, 35),
            "title": ["EXPEDITION SIEGE", "BOSS SANCTUARY"],
            "fallback_color": (35, 20, 25),
            "prompt": (
                "Cinematic 3D fantasy action portrait of a colossal frost-forged dungeon guardian emerging from an icy gate behind the dungeon lord, "
                "massive frozen blade drawn and crackling with rime energy facing an elite vanguard raid. "
                "Cathedral-like frozen cavern background, collapsing ice bridges, swirling blizzard embers, epic scale, 4k cinematic lighting."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
