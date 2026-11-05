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

BUILD_DIR = "build_the_boy_who_leveled_61_80"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "the-boy-who-leveled",
    "start_url": "https://www.royalroad.com/fiction/132206/the-boy-who-leveled/chapter/3056096/chapter-61",
    "start_chapter": 61,
    "end_chapter": 80,
    "default_topic": "The Boy Who Leveled",

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
                "In our previous chapters, relentless dungeon grinding and solitary trials propelled our young warrior through "
                "impossible stat thresholds, unlocking unprecedented combat classes. But breaking free from beginner tiers draws "
                "the gaze of veteran mercenary factions and higher-floor dungeon bosses hungry to crush rising prodigies."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "levelup",
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
                "In this episode, we step right back into the dungeon depths, picking up where the leveling notification screens left off, "
                "take a second to hit that like button, subscribe if you are new to the channel, and drop your thoughts in the comments. "
                "Your support is the engine that keeps this massive releases alive. "
                "Prepare your stats for lethal combat, adjust your volume, and let's begin today's episode."
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
    "final_audio": "output_the_boy_who_leveled_61_80.mp3",
    "final_video": "final_the_boy_who_leveled_61_80.mp4",
    "cover_image": "cover_the_boy_who_leveled_61_80.jpg",
    "timestamps_file": "youtube_timestamps_the_boy_who_leveled_61_80.txt",
    "subtitles_file": "subtitles_the_boy_who_leveled_61_80.srt",
    "payload_file": "youtube_upload_payload_the_boy_who_leveled_61_80.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "DEEP DUNGEON BOSSES & TIER 2 BREAKTHROUGH! [Ch 61-80] | The Boy Who Leveled LitRPG Full Audiobook",
    "tags": [
        "The Boy Who Leveled", "LitRPG Audiobook", "Progression Fantasy", "Level Up",
        "Dungeon Crawler", "System Apocalypse", "Royal Road", "Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'The Boy Who Leveled' covering Chapters 61 through 80!\n\n"
        "Descending into deeper dungeon sectors, our young protagonist tests his newly evolved skills against lethal floor guardians "
        "and rogue hunter parties. With every close-quarters kill fueling his astronomical stat scaling, he must push his body and mind "
        "to the absolute limit. Experience this 20-chapter marathon with multi-voice neural TTS, context-aware acoustic soundscapes, "
        "and full synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system stat boxes, and skill prompts).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more chapters and leveling progression sagas!\n\n"
        "#TheBoyWhoLeveled #LitRPG #ProgressionFantasy #SystemApocalypse #RoyalRoad #Audiobook #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks across Ch 61 to 80: 61-65, 66-70, 71-75, 76-80)
    "blocks": [
        {
            "index": 1, "range": (61, 65),
            "title": ["DEEP DUNGEON INGRESS", "STAT ACCELERATION"],
            "fallback_color": (20, 20, 30),
            "prompt": (
                "Cinematic 3D LitRPG fantasy illustration of a determined young warrior boy gripping two glowing mana daggers, "
                "standing in a dark, jagged subterranean dungeon corridor illuminated by translucent blue holographic stat screens. "
                "Bioluminescent moss on obsidian stone walls, floating dust particles, sharp dynamic rim lighting, 4k digital art."
            )
        },
        {
            "index": 2, "range": (66, 70),
            "title": ["FLOOR GUARDIAN CLASH", "KINETIC IMPACT"],
            "fallback_color": (35, 20, 20),
            "prompt": (
                "Cinematic 3D action scene of the boy executing a high-speed acrobatic dodge against a towering armored minotaur boss swinging an iron greataxe. "
                "Sparks flying from stone impact, motion blur on weapon trails, glowing red boss eyes, dramatic low-angle perspective, 4k render."
            )
        },
        {
            "index": 3, "range": (71, 75),
            "title": ["ROGUE HUNTER AMBUSH", "SHADOW MANEUVER"],
            "fallback_color": (25, 20, 30),
            "prompt": (
                "Cinematic 3D fantasy thriller scene inside a subterranean cavern camp, the young protagonist slipping through the shadows "
                "behind a party of hostile, armored rogue mercenaries gathered around a smoldering fire. "
                "Dark atmospheric shadows, glowing dagger edge, tense stealth framing, photorealistic textures."
            )
        },
        {
            "index": 4, "range": (76, 80),
            "title": ["TIER 2 ASCENT", "UNTOUCHABLE PRODIGY"],
            "fallback_color": (15, 25, 35),
            "prompt": (
                "Cinematic 3D epic fantasy view of the boy standing triumphant at the exit gateway of a cleared floor dungeon, "
                "surrounded by dissolving golden mana particles and multiple completed quest prompts. "
                "Beams of celestial light piercing the cavern ceiling, confident heroic posture, masterpiece 4k render."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
