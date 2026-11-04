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

BUILD_DIR = "build_dungeon_of_niflheim_36_70"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "dungeon-of-niflheim",
    "start_url": "https://freewebnovel.com/novel/dungeon-of-niflheim/chapter-36",
    "start_chapter": 36,
    "end_chapter": 70,
    "default_topic": "Dungeon of Niflheim",

    # Concurrency Settings & Narrator Lock
    "batch_size": 7,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Full Mir-Style Dynamic Intro Sequence Passed in intro_hook
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "In our previous chapters, deep within the subterranean frost of Niflheim, an ancient dungeon core awakened. "
                "From skeletal sentinels to crystalline trap arrays, every floor was forged with ruthless precision. But as the anomaly's "
                "chilling presence breached the surface, kingdom vanguards and high-tier adventurer legions mobilized for an all-out invasion."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "wind",
            "bgm_mood": "tension"
        },
        {
            "line_id": "intro_pause_01",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "",
            "pause_duration": 0.4,
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "",
            "bgm_mood": "tension"
        },
        {
            "line_id": "intro_02_body",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "Welcome back to Being a Bong. We narrate the unreal worlds to life. "
                "In this episode, we step right back into the frozen deep, picking up where the war drums of the surface kingdom left off, "
                "take a second to hit that like button, subscribe if you are new to the channel, and drop your thoughts in the comments. "
                "Your support is the engine that keeps this massive releases alive. "
                "Settle in as the defensive traps trigger, adjust your volume, and let's begin today's episode."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_lead_in_pause",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "",
            "pause_duration": 1.0,
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "",
            "bgm_mood": "no_mood"
        }
    ],

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_dungeon_of_niflheim_36_70.mp3",
    "final_video": "final_dungeon_of_niflheim_36_70.mp4",
    "cover_image": "cover_dungeon_of_niflheim_36_70.jpg",
    "timestamps_file": "youtube_timestamps_dungeon_of_niflheim_36_70.txt",
    "subtitles_file": "subtitles_dungeon_of_niflheim_36_70.srt",
    "payload_file": "youtube_upload_payload_dungeon_of_niflheim_36_70.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "PRIMORDIAL FROST EXPANSION & KINGDOM SIEGE! [Ch 36-70] | Dungeon of Niflheim Dark Fantasy Audiobook",
    "tags": [
        "Dungeon of Niflheim", "Dungeon Core", "LitRPG Audiobook", "Progression Fantasy",
        "Dark Fantasy", "Necromancy", "Frost Magic", "Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Dungeon of Niflheim' with Chapters 36 through 70!\n\n"
        "As the dungeon's presence threatens the surface realms, high-tier adventurer guilds and imperial legions "
        "mount coordinated assaults into the glacial labyrinth. Watch as our protagonist unlocks primordial frost runes, "
        "upgrades lethal trap complexes, and deploys ancient skeletal dreadnoughts to defend the core. Experience this "
        "35-chapter marathon with multi-voice neural TTS, context-aware acoustic soundscapes, and full soft subtitles.\n\n"
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

    # Visual Prompts (4 thematic blocks covering Ch 36 to 70: 36-44, 45-53, 54-62, 63-70)
    "blocks": [
        {
            "index": 1, "range": (36, 44),
            "title": ["GLACIAL SANCTUM EXPANSION", "RUNIC FORTIFICATION"],
            "fallback_color": (15, 20, 35),
            "prompt": (
                "Cinematic 3D dark fantasy illustration of an expansive subterranean ice cathedral, "
                "the pale dungeon master in obsidian armor commanding swirling blizzard mana to carve massive runic arches. "
                "Crystalline blue stalactites suspended over chasms, ancient frozen tombs lining the walls, eerie cyan glow, volumetric mist."
            )
        },
        {
            "index": 2, "range": (45, 53),
            "title": ["INVASION DEFENSE", "FROSTBOUND SENTINEL LEGION"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D fantasy battle scene in a narrow frozen canyon, showing heavily armored royal knights clashing "
                "against hulking frost revenants and icy wraiths with glowing eyes. "
                "Blizzard winds whipping snow across the screen, ice traps exploding into lethal crystalline shards, dramatic rim lighting."
            )
        },
        {
            "index": 3, "range": (54, 62),
            "title": ["CORE EVOLUTION", "PRIMORDIAL ARCHITECTURE"],
            "fallback_color": (25, 15, 30),
            "prompt": (
                "Cinematic 3D dark fantasy view of the central dungeon core pulsing violently with intense violet and sapphire rime energy, "
                "intricate multi-tiered geometric magical arrays rotating in mid-air above a stone altar. "
                "Floor covered in frosted black obsidian tiles, soul energy condensing into physical gems, cinematic high-contrast lighting."
            )
        },
        {
            "index": 4, "range": (63, 70),
            "title": ["APEX DREADNOUGHT", "SURFACE KINGDOM STANDOFF"],
            "fallback_color": (30, 20, 25),
            "prompt": (
                "Cinematic 3D fantasy action portrait of a massive frost-dreadnought colossus standing behind the dungeon lord, "
                "confronting a shattered vanguard expedition at the threshold of the deep domain. "
                "Vast underground chasm, drifting blizzard embers, broken armor and banners on the ground, epic scale, 4k digital art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
