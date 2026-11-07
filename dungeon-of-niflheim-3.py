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

BUILD_DIR = "build_dungeon_of_niflheim_71_105"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters
    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/dungeon-of-niflheim/chapter-71",
    "novel_slug": "dungeon-of-niflheim",
    "start_chapter": 71,
    "end_chapter": 105,
    "default_topic": "Dungeon of Niflheim",

    # Concurrency Settings & Hardcoded Narrator Lock
    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Mir-Style Dynamic Intro Sequence Passed in intro_hook (Chapters 71 to 105)
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "In the cold, forbidding depths of the underworld realm, where eternal frost and ancient malice entwine, "
                "the dark dominion expands its ruthless grip. "
                "Step further into the frozen halls of Niflheim, where traps are sprung, intruders are crushed, "
                "and the dungeon master claims absolute supremacy over death itself."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "gong",
            "bgm_mood": "dread"
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
            "bgm_mood": "dread"
        },
        {
            "line_id": "intro_02_body",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "Welcome back to Being a Bong. We narrate the unreal worlds to life. "
                "We are thrilled to bring you chapters seventy-one through one hundred and five of Dungeon of Niflheim. "
                "Take a second to hit that like button, subscribe if you are new to the channel, "
                "and drop your thoughts in the comments. Your support is the engine that keeps these grand marathons alive. "
                "Adjust your volume, embrace the icy chill, and let's descend into the dark."
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
    "final_audio": "output_dungeon_of_niflheim_71_105.mp3",
    "final_video": "final_dungeon_of_niflheim_71_105.mp4",
    "cover_image": "cover_dungeon_of_niflheim_71_105.jpg",
    "timestamps_file": "youtube_timestamps_dungeon_of_niflheim_71_105.txt",
    "subtitles_file": "subtitles_dungeon_of_niflheim_71_105.srt",
    "payload_file": "youtube_upload_payload_dungeon_of_niflheim_71_105.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "THE FROZEN DOMINION & UNDEAD EXPANSION! [Chapters 71-105] | Dungeon of Niflheim Audiobook",
    "tags": [
        "Dungeon of Niflheim", "Dungeon Core Novel", "LitRPG Audiobook", "Dark Fantasy",
        "Undead Army", "Web Novel Audio", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to the continuous dark fantasy arc of 'Dungeon of Niflheim', covering Chapters 71 through 105!\n\n"
        "Witness the terrifying expansion of the underworld dungeon as dead-cold traps are laid, foolish adventurers are eradicated, "
        "and new horrors awaken beneath the frozen earth. Experience this multi-chapter saga with multi-voice neural TTS, "
        "context-aware acoustic soundscapes, and synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogues and dark narrative).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more dungeon core and dark fantasy sagas!\n\n"
        "#DungeonOfNiflheim #DungeonCore #DarkFantasy #LitRPG #WebNovel #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks covering Chapters 71 to 105)
    "blocks": [
        {
            "index": 1, "range": (71, 79),
            "title": ["THE FROZEN CRYPTS", "TRAPS OF THE UNDERWORLD"],
            "fallback_color": (20, 30, 40),
            "prompt": (
                "Cinematic 3D dark fantasy illustration of a subterranean glacial dungeon corridor covered in blue frost and icicles, "
                "glowing magical runes carved into ancient black stone walls, skeletal sentinels standing guard in the shadows, "
                "cold eerie lighting, highly detailed 4k digital art."
            )
        },
        {
            "index": 2, "range": (80, 88),
            "title": ["MARCH OF THE UNDEAD", "THE VANGUARD OF BONES"],
            "fallback_color": (25, 25, 30),
            "prompt": (
                "Cinematic 3D moody dark fantasy scene of an army of armored skeletal warriors marching through a cavernous subterranean hall, "
                "blue soul-fire glowing in their empty eye sockets, held weapons reflecting an ethereal glacial glow, "
                "dramatic chiaroscuro lighting, sharp 4k render."
            )
        },
        {
            "index": 3, "range": (89, 96),
            "title": ["INTRUDERS IN THE DARK", "THE SLAUGHTER IN THE ICE"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic 3D gritty combat scene of arrogant human adventurers trapped in an icy subterranean chamber, "
                "surrounded by vicious frost beasts and ghoulish guardians under dim magical illumination, "
                "suspenseful and perilous atmosphere, hyper-detailed 4k digital masterpiece."
            )
        },
        {
            "index": 4, "range": (97, 105),
            "title": ["HEART OF THE DOMINION", "THE ASCENT OF NIFLHEIM"],
            "fallback_color": (15, 25, 35),
            "prompt": (
                "Cinematic 3D epic establishing shot of a magnificent glowing blue dungeon core crystal suspended in the center of an immense ice throne room, "
                "frost patterns spreading across towering obsidian pillars, supreme dark majesty, 4k digital art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
