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

BUILD_DIR = "build_the_gourmet_innkeeper_251_300"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "the-gourmet-innkeeper-cooking-monsters-in-a-fantasy-world",
    "start_url": "https://freewebnovel.com/novel/the-gourmet-innkeeper-cooking-monsters-in-a-fantasy-world/chapter-251",
    "start_chapter": 251,
    "end_chapter": 300,
    "default_topic": "The Gourmet Innkeeper",

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
                "In our previous chapters, within the bustling halls of the otherworldly tavern, exotic beast ingredients "
                "were transformed into legendary culinary masterpieces that cured ailments and boosted cultivation levels. "
                "As the inn's renown spread across kingdoms, new high-tier food critics, royal nobles, and ravenous monster "
                "chieftains arrived at the doorstep demanding tables."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "dishes",
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
                "In this episode, we step right back into the kitchen, picking up where the sizzling woks and secret recipes left off, "
                "take a second to hit that like button, subscribe if you are new to the channel, and drop your thoughts in the comments. "
                "Your support is the engine that keeps this massive releases alive. "
                "Settle in as the stoves roar to life, adjust your volume, and let's begin today's episode."
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
    "final_audio": "output_the_gourmet_innkeeper_251_300.mp3",
    "final_video": "final_the_gourmet_innkeeper_251_300.mp4",
    "cover_image": "cover_the_gourmet_innkeeper_251_300.jpg",
    "timestamps_file": "youtube_timestamps_the_gourmet_innkeeper_251_300.txt",
    "subtitles_file": "subtitles_the_gourmet_innkeeper_251_300.srt",
    "payload_file": "youtube_upload_payload_the_gourmet_innkeeper_251_300.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "LEGENDARY MONSTER FEAST & CULINARY EMPIRE! [Ch 251-300] | The Gourmet Innkeeper Fantasy Audiobook",
    "tags": [
        "The Gourmet Innkeeper", "Cooking Monsters", "Fantasy Audiobook", "Progression Fantasy",
        "Gourmet Fantasy", "Innkeeper", "LitRPG", "Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'The Gourmet Innkeeper: Cooking Monsters in a Fantasy World' covering Chapters 251 through 300!\n\n"
        "Step inside the most famous fantasy tavern where terrifying magical beasts become exquisite Michelin-star dishes. "
        "From dragon-scale hotpot to spirit-beast sashimi, our master chef innkeeper continues to expand his culinary empire, "
        "defying picky nobles and monster hordes alike. Experience this 50-chapter marathon with multi-voice neural TTS, "
        "context-aware acoustic soundscapes, and full synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, recipes, and status buffs).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more chapters and gourmet fantasy sagas!\n\n"
        "#TheGourmetInnkeeper #CookingMonsters #FantasyAudiobook #ProgressionFantasy #GourmetFantasy #BeingABong"
    ),

    # Visual Prompts (4 balanced thematic blocks across Ch 251 to 300: 251-262, 263-275, 276-287, 288-300)
    "blocks": [
        {
            "index": 1, "range": (251, 262),
            "title": ["EXOTIC INGREDIENT HARVEST", "KITCHEN MASTERPIECE"],
            "fallback_color": (30, 20, 15),
            "prompt": (
                "Cinematic 3D fantasy illustration of a glowing rustic tavern kitchen filled with bubbling magical cauldrons, "
                "exquisite plates of monster meat glowing with golden nutritional auras, and a smiling master chef wielding a gleaming cleaver. "
                "Warm hearth illumination, hanging spices, highly detailed food textures, 4k digital art style."
            )
        },
        {
            "index": 2, "range": (263, 275),
            "title": ["ROYAL BANQUET", "NOBLE CRITIC CLASH"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D fantasy banquet hall scene with lavishly dressed nobles and elven dignitaries sitting around a long oak table "
                "staring in absolute awe at a magnificent glowing platter served by the innkeeper. "
                "Warm chandelier lighting, stained glass windows, rich wooden interior, exquisite culinary presentation, 4k render."
            )
        },
        {
            "index": 3, "range": (276, 287),
            "title": ["MONSTER CHIEFTAIN FEAST", "TAVERN DEFENSE"],
            "fallback_color": (25, 20, 30),
            "prompt": (
                "Cinematic 3D fantasy interior view of powerful towering monster chieftains and warriors peacefully enjoying massive roasted beast feasts "
                "inside the cozy, magically expanded tavern hall while friendly spirits serve mugs of sparkling fruit ale. "
                "Magical lanterns, bustling atmosphere, detailed character models, cinematic lighting."
            )
        },
        {
            "index": 4, "range": (288, 300),
            "title": ["CULINARY EMPIRE ASCENT", "THE ETERNAL HEARTH"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic 3D epic fantasy view of the majestic gourmet inn lit up at night under a starry sky, "
                "with travelers, adventurers, and caravans arriving from all directions into the glowing sanctuary. "
                "Warm welcoming lights, cobblestone courtyard, grand scale, masterpiece 4k rendering."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))