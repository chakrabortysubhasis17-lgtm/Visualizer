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

BUILD_DIR = "build_gourmet_innkeeper_301_350"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters
    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/the-gourmet-innkeeper-cooking-monsters-in-a-fantasy-world/chapter-301",
    "novel_slug": "the-gourmet-innkeeper-cooking-monsters-in-a-fantasy-world",
    "start_chapter": 301,
    "end_chapter": 350,
    "default_topic": "The Gourmet Innkeeper",

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
                "Deep within the perilous frontier where calamity beasts roam and ancient dungeons slumber, "
                "a sanctuary of sizzling pans and extraordinary cuisine defies the wild. "
                "From butcher blocks carving legendary behemoth steaks to bubbling cauldrons infusing mythical mana, "
                "step inside the hearth where divine feasts bring warlords to their knees and weary adventurers find home."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "cooking",
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
                "Today, we bring you chapters three hundred and one through three hundred and fifty of "
                "The Gourmet Innkeeper: Cooking Monsters in a Fantasy World. "
                "If you love mouth-watering monster culinary fantasy and cozy tavern adventures, "
                "take a moment to hit that like button, subscribe if you are new to the channel, "
                "and share your thoughts in the comments below. "
                "Pull up a chair by the hearth, adjust your volume, and let's dig into today's feast."
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
    "final_audio": "output_gourmet_innkeeper_301_350.mp3",
    "final_video": "final_gourmet_innkeeper_301_350.mp4",
    "cover_image": "cover_gourmet_innkeeper_301_350.jpg",
    "timestamps_file": "youtube_timestamps_gourmet_innkeeper_301_350.txt",
    "subtitles_file": "subtitles_gourmet_innkeeper_301_350.srt",
    "payload_file": "youtube_upload_payload_gourmet_innkeeper_301_350.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "MYTHICAL DELICACIES & THE INN'S DOMAIN! [Chapters 301-350] | The Gourmet Innkeeper Full Audiobook",
    "tags": [
        "The Gourmet Innkeeper", "Cooking Monsters in a Fantasy World", "Gourmet Fantasy",
        "LitRPG Audiobook", "Cozy Fantasy", "Monster Cooking", "Web Novel Audio", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to the flavorful fantasy adventures of 'The Gourmet Innkeeper: Cooking Monsters in a Fantasy World', "
        "covering Chapters 301 through 350!\n\n"
        "Follow Chef Finn and his trusty companion Pang as they harvest rare ingredients from high-tier mythical beasts, "
        "expand the tavern's magical territory, and serve dishes that boost stats and enchant the most stubborn nobles. "
        "Experience this 50-chapter arc with multi-voice neural TTS, context-aware acoustic soundscapes, "
        "voice-aware prosody scaling, and synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and tavern narrative).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more cozy culinary fantasy, LitRPG, and monster cooking sagas!\n\n"
        "#GourmetInnkeeper #MonsterCooking #FantasyAudiobook #CozyFantasy #WebNovel #BeingABong"
    ),

    # Visual Prompts (4 balanced thematic blocks covering Chapters 301 to 350)
    "blocks": [
        {
            "index": 1, "range": (301, 313),
            "title": ["FEAST OF THE MYTHIC BEASTS", "THE KITCHEN'S DOMAIN"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D cozy fantasy tavern kitchen interior, warm golden fire glowing in a massive stone hearth, "
                "copper pots and sizzling skillets releasing savory steam, seasoned roasted monster meat garnished with glowing magical herbs, "
                "a determined chef plating culinary masterpieces on rustic oak countertops, highly detailed 4k digital art."
            )
        },
        {
            "index": 2, "range": (314, 325),
            "title": ["TAVERN REVELRY", "HONORED GUESTS"],
            "fallback_color": (40, 20, 20),
            "prompt": (
                "Cinematic 3D fantasy tavern dining hall bustling with life at night, "
                "adventurers in battered leather and polished plate armor clinking heavy wooden ale steins at crowded trestle tables, "
                "warm amber lantern glow illuminating exposed timber beams and rich tapestries, cheerful atmospheric illumination, sharp 4k render."
            )
        },
        {
            "index": 3, "range": (326, 338),
            "title": ["HARVEST IN THE WILDS", "RARE INGREDIENTS"],
            "fallback_color": (20, 30, 25),
            "prompt": (
                "Cinematic 3D lush mystical forest grove at twilight, "
                "glowing bioluminescent mushrooms and enchanted crystal springs reflecting evening starlight, "
                "a chef harvesting rare magical spices beside an ancient mossy stone ruin, deep peaceful wilderness, 4k digital masterpiece."
            )
        },
        {
            "index": 4, "range": (339, 350),
            "title": ["THE EXPANDING SANCTUARY", "THE SOVEREIGN CHEF"],
            "fallback_color": (30, 25, 35),
            "prompt": (
                "Cinematic 3D exterior establishing view of an enchanting multi-story fantasy mountain inn surrounded by glowing boundary runes, "
                "chimneys puffing fragrant cedar smoke into a starry violet evening sky, warm light spilling from leaded glass windows, "
                "majestic haven in a wild fantasy world, 4k digital art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
