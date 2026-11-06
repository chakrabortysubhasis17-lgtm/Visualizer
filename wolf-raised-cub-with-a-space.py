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

BUILD_DIR = "build_wolf_raised_cub_1_50"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "wolf-raised-cub-with-a-space-surviving-the-disaster-years",
    "start_url": "https://freewebnovel.com/novel/wolf-raised-cub-with-a-space-surviving-the-disaster-years/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Wolf Raised Cub with a Space",

    # Concurrency Settings & Narrator Lock
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Full Mir-Style Dynamic Intro Sequence Passed in intro_hook (Premiere Episode)
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "When devastating famine, unyielding blizzards, and apocalyptic calamity strike the frontier, "
                "survival demands more than sheer grit. Reborn into the harsh wilderness as an abandoned child "
                "sheltered by a loyal wolf pack, our protagonist discovers an extraordinary secret: an infinite "
                "interdimensional space capable of hoarding vital grains, clean water, and life-saving remedies. "
                "Surrounded by fierce lupine guardians, a remarkable journey through the disaster years begins."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "howl",
            "bgm_mood": "wonder"
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
            "bgm_mood": "wonder"
        },
        {
            "line_id": "intro_02_body",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "Welcome back to Being a Bong. We narrate the unreal worlds to life. "
                "We are thrilled to bring you the premiere episode of this wilderness survival and spatial hoarding saga, "
                "take a second to hit that like button, subscribe if you are new to the channel, and drop your thoughts in the comments. "
                "Your support is the engine that keeps this massive releases alive. "
                "Step into the frozen wilderness with the pack, adjust your volume, and let's begin today's episode."
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
    "final_audio": "output_wolf_raised_cub_1_50.mp3",
    "final_video": "final_wolf_raised_cub_1_50.mp4",
    "cover_image": "cover_wolf_raised_cub_1_50.jpg",
    "timestamps_file": "youtube_timestamps_wolf_raised_cub_1_50.txt",
    "subtitles_file": "subtitles_wolf_raised_cub_1_50.srt",
    "payload_file": "youtube_upload_payload_wolf_raised_cub_1_50.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "WOLF PACK SURVIVAL & PORTABLE SPACE HOARDING! [Ch 1-50] | Disaster Years Apocalypse Audiobook",
    "tags": [
        "Wolf Raised Cub with a Space", "Disaster Years", "Survival Novel", "Apocalypse Audiobook",
        "Portable Space", "Famine Survival", "Wolf Pack", "Transmigration", "Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to the premiere release of 'Wolf Raised Cub with a Space Surviving the Disaster Years' covering Chapters 1 through 50!\n\n"
        "Awakening during the most unforgiving famine and disaster period, an abandoned child finds an unexpected family among "
        "a protective wolf pack deep in the snowy mountains. Armed with a pocket dimension that preserves crops, fresh water, and "
        "foraged supplies, watch as they navigate harsh weather, famine, and greedy bandits while building an impenetrable frontier haven. "
        "Experience this 50-chapter premiere marathon with multi-voice neural TTS, context-aware acoustic soundscapes, and full soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, internal monologues, and spatial alerts).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more chapters and survival progression sagas!\n\n"
        "#WolfRaisedCub #DisasterYears #SurvivalAudiobook #ApocalypseFiction #SpatialHoarding #Audiobook #BeingABong"
    ),

    # Visual Prompts (4 balanced thematic blocks across Ch 1 to 50: 1-12, 13-25, 26-38, 39-50)
    "blocks": [
        {
            "index": 1, "range": (1, 12),
            "title": ["WOLF DEN SANCTUARY", "PORTABLE SPACE AWAKENING"],
            "fallback_color": (20, 25, 30),
            "prompt": (
                "Cinematic 3D fantasy illustration of a small, warm cave interior during a raging winter blizzard, "
                "a young child nestled safely against the thick silver-gray fur of a massive protective mother wolf. "
                "A faint, ethereal celestial portal glowing gently in the child's small palms, snowflakes swirling outside the cave mouth, "
                "warm den hearth illumination, highly detailed fur and snow textures, 4k digital art."
            )
        },
        {
            "index": 2, "range": (13, 25),
            "title": ["DISASTER HOARDING", "WILDERNESS HARVEST"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D render of the young protagonist accompanied by two alert white wolves, exploring an untouched mountain ravine "
                "filled with wild mountain herbs, lingzhi mushrooms, and crystal-clear spring water flowing into a glowing dimensional vortex. "
                "Golden autumn foliage dusted with light frost, crisp morning rays filtering through pine needles, sharp depth of field."
            )
        },
        {
            "index": 3, "range": (26, 38),
            "title": ["BLIZZARD TRIAL", "THE LOYAL PACK DEFENSE"],
            "fallback_color": (25, 20, 30),
            "prompt": (
                "Cinematic 3D action scene in a frozen forest pass, showing the fierce wolf pack standing in defensive formation "
                "with bared fangs against rogue scavengers and starvation-crazed mountain beasts in the middle of a heavy snowstorm. "
                "Wind-blown snow drifts, glowing feral wolf eyes, dramatic low-angle perspective, dynamic atmospheric lighting, 4k render."
            )
        },
        {
            "index": 4, "range": (39, 50),
            "title": ["PROSPEROUS HAVEN", "SOVEREIGN OF THE PEAKS"],
            "fallback_color": (20, 30, 25),
            "prompt": (
                "Cinematic 3D epic view of the fortified mountain refuge with smoke curling from a cozy stone chimney, "
                "the young protagonist standing proudly on a high rocky ledge surrounded by the thriving wolf pack overlooking "
                "vast snowy mountain ranges bathed in radiant dawn sunlight. Majestic scale, tranquil and triumphant atmosphere, masterpiece 4k render."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
