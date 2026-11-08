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

BUILD_DIR = "build_wolf_raised_cub_50_100"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters
    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/wolf-raised-cub-with-a-space-surviving-the-disaster-years/chapter-50",
    "novel_slug": "wolf-raised-cub-with-a-space-surviving-the-disaster-years",
    "start_chapter": 50,
    "end_chapter": 100,
    "default_topic": "Wolf Raised Cub with a Space Surviving the Disaster Years",

    # Concurrency Settings & Hardcoded Narrator Lock
    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Dynamic Atmospheric Intro Sequence
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "Deep in the unforgiving wilderness during the bitter years of catastrophe, "
                "a child protected by a loyal wolf pack carves a life of quiet warmth and fierce survival. "
                "With an interdimensional space brimmed with provisions and the pack guarding every snowy ridge, "
                "step into the mountain forest where nature's wild fury meets the tender bond between man and wolf."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "howl",
            "bgm_mood": "warmth"
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
            "bgm_mood": "warmth"
        },
        {
            "line_id": "intro_02_body",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "Welcome back to Being a Bong. We narrate the unreal worlds to life. "
                "Today, we bring you chapters fifty through one hundred of "
                "Wolf Raised Cub with a Space Surviving the Disaster Years. "
                "If you enjoy cozy survival stories, wilderness adventures, and loyal beast companions, "
                "take a moment to hit that like button, subscribe if you are new to the channel, "
                "and share your thoughts in the comments below. "
                "Settle in by the campfire, adjust your volume, and let us head into the woods."
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
    "final_audio": "output_wolf_raised_cub_50_100.mp3",
    "final_video": "final_wolf_raised_cub_50_100.mp4",
    "cover_image": "cover_wolf_raised_cub_50_100.jpg",
    "timestamps_file": "youtube_timestamps_wolf_raised_cub_50_100.txt",
    "subtitles_file": "subtitles_wolf_raised_cub_50_100.srt",
    "payload_file": "youtube_upload_payload_wolf_raised_cub_50_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "WOLF PACK GUARDIANS & THE SPATIAL HARVEST! [Chapters 50-100] | Wilderness Survival Audiobook",
    "tags": [
        "Wolf Raised Cub with a Space Surviving the Disaster Years", "Wilderness Survival",
        "Dimension Space Novel", "Wolf Companion", "Post-Apocalyptic Survival", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to the heartwarming wilderness survival saga of 'Wolf Raised Cub with a Space Surviving the Disaster Years', "
        "covering Chapters 50 through 100!\n\n"
        "Follow our young protagonist and their fierce, protective wolf pack as they brave harsh blizzards, hunt across treacherous "
        "mountain terrain, and quietly stock their pocket dimension with bountiful harvest and foraging supplies. "
        "Experience this 51-chapter survival arc with multi-voice neural TTS, context-aware acoustic soundscapes, "
        "voice-aware prosody scaling, and synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and wilderness narrative).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more cozy wilderness survival, beast companion, and historical fiction sagas!\n\n"
        "#WolfRaisedCub #WildernessSurvival #DimensionSpace #WolfPack #Audiobook #BeingABong"
    ),

    # Visual Prompts (4 balanced thematic blocks covering Chapters 50 to 100: 50-62, 63-75, 76-88, 89-100)
    "blocks": [
        {
            "index": 1, "range": (50, 62),
            "title": ["GUARDIANS OF THE SNOW", "THE WOLF PACK'S VIGIL"],
            "fallback_color": (30, 35, 40),
            "prompt": (
                "Cinematic 3D atmospheric illustration of a winter mountain pine forest covered in fresh deep snow, "
                "a young resilient child in warm handmade fur clothing surrounded by majestic silver-grey wolves resting peacefully, "
                "soft golden sunlight breaking through snow-laden evergreen boughs, tranquil and heartwarming wilderness, "
                "highly detailed 4k digital art."
            )
        },
        {
            "index": 2, "range": (63, 75),
            "title": ["THE DIMENSIONAL HAVEN", "HARVEST IN THE COLD"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D interior of a rustic warm log cabin shelter tucked inside a secluded mountain valley, "
                "a crackling stone fireplace illuminating wooden drying racks filled with wild herbs, mushrooms, and cured meats, "
                "a large wolf curled beside the hearth with soft glowing amber eyes, cozy and safe atmosphere, sharp 4k render."
            )
        },
        {
            "index": 3, "range": (76, 88),
            "title": ["THE FROZEN EXPEDITION", "HUNTING ON THE RIDGES"],
            "fallback_color": (25, 30, 35),
            "prompt": (
                "Cinematic 3D outdoor survival scene along a rugged rocky mountain ridge at twilight, "
                "a pack of agile grey wolves tracking mountain game across frozen crags, "
                "wind kicking up crystalline snow dust against a dramatic violet and amber sunset sky, "
                "vast wilderness expanse, hyper-detailed 4k digital masterpiece."
            )
        },
        {
            "index": 4, "range": (89, 100),
            "title": ["SPRING ON THE MOUNTAIN", "THE FLOURISHING SANCTUARY"],
            "fallback_color": (25, 35, 25),
            "prompt": (
                "Cinematic 3D serene establishing view of a mountain meadow awakening from winter thaw, "
                "wild alpine blossoms blooming beside a crystal-clear meltwater stream, "
                "the young child laughing as playful wolf cubs tumble through green grass under warm morning sunlight, "
                "majestic natural beauty, 4k digital art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
