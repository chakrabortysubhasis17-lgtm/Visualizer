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

BUILD_DIR = "build_sss_goddess_summon_395_435"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "starting-with-an-sss-rank-goddess-summon",
    "start_url": "https://freewebnovel.com/novel/starting-with-an-sss-rank-goddess-summon/chapter-395",
    "start_chapter": 395,
    "end_chapter": 435,
    "default_topic": "Starting With An SSS-Rank Goddess Summon",

    # Concurrency Settings & Narrator Lock
    "batch_size": 10,
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
                "In our previous chapters, divine pacts and astronomical power scaling shook the continent as our summoner "
                "unlocked forbidden celestial domains alongside his supreme goddess legions. But piercing into the upper god realms "
                "ignited the wrath of ancient celestial pantheons, provoking an unprecedented war of deities across the cosmos."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "hum",
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
                "In this episode, we step right back into the divine battlefield, picking up where the god-tier summoning arrays left off, "
                "take a second to hit that like button, subscribe if you are new to the channel, and drop your thoughts in the comments. "
                "Your support is the engine that keeps this massive releases alive. "
                "Prepare for celestial devastation, adjust your volume, and let's begin today's episode."
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
    "final_audio": "output_sss_goddess_summon_395_435.mp3",
    "final_video": "final_sss_goddess_summon_395_435.mp4",
    "cover_image": "cover_sss_goddess_summon_395_435.jpg",
    "timestamps_file": "youtube_timestamps_sss_goddess_summon_395_435.txt",
    "subtitles_file": "subtitles_sss_goddess_summon_395_435.srt",
    "payload_file": "youtube_upload_payload_sss_goddess_summon_395_435.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "DIVINE PANTHEON WAR & GODDESS AWAKENING! [Ch 395-435] | SSS-Rank Goddess Summon Full Audiobook",
    "tags": [
        "Starting With An SSS-Rank Goddess Summon", "SSS Goddess Summon", "LitRPG Audiobook",
        "Progression Fantasy", "Harem Fantasy", "Summoner", "Overpowered MC", "Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Starting With An SSS-Rank Goddess Summon' covering Chapters 395 through 435!\n\n"
        "Ascending past mortal understanding, our protagonist and his peerless goddess vanguard plunge straight into the ancestral "
        "abode of the high gods. Facing primordial entities, multi-dimensional boundary fractures, and planetary-level spell matrices, "
        "watch as he commands supreme divine authority to rewrite the hierarchy of heaven itself. Experience this 41-chapter marathon with "
        "multi-voice neural TTS, context-aware acoustic soundscapes, and full synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, skill matrices, and divine alerts).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more chapters and goddess summoning sagas!\n\n"
        "#SSSRankGoddessSummon #GoddessSummon #LitRPG #ProgressionFantasy #Audiobook #BeingABong"
    ),

    # Visual Prompts (4 balanced thematic blocks across Ch 395 to 435: 395-404, 405-414, 415-424, 425-435)
    "blocks": [
        {
            "index": 1, "range": (395, 404),
            "title": ["CELESTIAL DOMAIN CRACK", "PRIMORDIAL SUMMONING"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D dark fantasy illustration of a powerful summoner surrounded by radiant golden magical arrays, "
                "standing shoulder-to-shoulder with breathtaking divine goddesses clad in shimmering ethereal armor and flowing silks. "
                "Shattered crystalline cosmic skies, floating divine temples, brilliant volumetric lighting, 4k digital art."
            )
        },
        {
            "index": 2, "range": (405, 414),
            "title": ["PANTHEON CLASH", "HEAVENLY WRATH"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D epic action scene of a colossal celestial battle over floating marble islands in space, "
                "divine spears colliding against elemental shields of fire and frost, shockwaves tearing through nebulas. "
                "Dynamic angle, intense particle effects, dramatic rim lighting, sharp 4k render."
            )
        },
        {
            "index": 3, "range": (415, 424),
            "title": ["GODDESS BLOODLINE EVOLUTION", "ASTRAL CORE"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D fantasy portrait of a majestic goddess ascending within a massive column of starlight, "
                "her feathered wings expanding with brilliant prismatic feathers as ancient cosmic runes orbit her crown. "
                "Breathtaking celestial landscape, drifting stellar embers, serene commanding atmosphere."
            )
        },
        {
            "index": 4, "range": (425, 435),
            "title": ["SUPREME CONQUEROR", "THRONE OF HEAVEN"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D epic render of the summoner sitting on an ornate astral throne overlooking bowing deity legions, "
                "his divine summons flanking him with drawn celestial blades against a backdrop of swirling galaxies. "
                "Magnificent scale, divine golden and violet lighting, masterpiece 4k digital art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
