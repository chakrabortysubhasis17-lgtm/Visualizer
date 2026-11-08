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

BUILD_DIR = "build_invincible_41_80"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters
    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/invincible-novel/chapter-41",
    "novel_slug": "invincible-novel",
    "start_chapter": 41,
    "end_chapter": 80,
    "default_topic": "Invincible",

    # Concurrency Settings & Hardcoded Narrator Lock
    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Mir-Style Dynamic Intro Sequence Passed in intro_hook (Chapters 41 to 80)
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "In a world where only absolute martial prowess commands respect, "
                "the slumbering primordial dragon spirit awakens to defy the heavens. "
                "Watch Huang Xiaolong shatter realm barriers, humiliate arrogant geniuses, "
                "and carve his path across the continent with unyielding dominance."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "gong",
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
                "Today, we bring you chapters forty-one through eighty of the legendary xianxia saga, Invincible. "
                "Take a moment to hit that like button, subscribe if you are new to the channel, "
                "and share your thoughts in the comments below. Your support is the engine that keeps these grand marathons alive. "
                "Adjust your volume, steady your breathing, and let us begin."
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
    "final_audio": "output_invincible_41_80.mp3",
    "final_video": "final_invincible_41_80.mp4",
    "cover_image": "cover_invincible_41_80.jpg",
    "timestamps_file": "youtube_timestamps_invincible_41_80.txt",
    "subtitles_file": "subtitles_invincible_41_80.srt",
    "payload_file": "youtube_upload_payload_invincible_41_80.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "MARTIAL BREAKTHROUGH & HEAVEN-DEFYING SPIRIT! [Chapters 41-80] | Invincible Full Audiobook",
    "tags": [
        "Invincible", "Invincible Novel", "Huang Xiaolong", "Xianxia Audiobook",
        "Cultivation Novel", "Martial Arts Fantasy", "Web Novel Audio", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to the continuous cultivation journey of 'Invincible', covering Chapters 41 through 80!\n\n"
        "Follow Huang Xiaolong as his supreme martial spirits evolve, overcoming clan rivalries, entering dangerous trial grounds, "
        "and advancing through the Order ranks with explosive breakthroughs. Experience this 40-chapter xianxia arc with "
        "multi-voice neural TTS, context-aware acoustic soundscapes, and synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and martial cultivation).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more xianxia epics and martial cultivation sagas!\n\n"
        "#InvincibleNovel #HuangXiaolong #Xianxia #CultivationAudiobook #WebNovel #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks covering Chapters 41 to 80: 41-50, 51-60, 61-70, 71-80)
    "blocks": [
        {
            "index": 1, "range": (41, 50),
            "title": ["MARTIAL SPIRIT AWAKENING", "THE DRAGON'S MIGHT"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D xianxia illustration of a young cultivation prodigy standing atop a misty mountain summit at dawn, "
                "two colossal translucent celestial dragons coiling behind him glowing with golden and black aura, "
                "spiritual energy swirling in radiant vortexes, towering ancient stone pagodas in the background, "
                "vibrant dramatic lighting, highly detailed 4k digital masterpiece."
            )
        },
        {
            "index": 2, "range": (51, 60),
            "title": ["THE CLAN ARENA", "CRUSHING ARROGANT SCIONS"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D martial arts arena scene paved in heavy white granite slabs, "
                "shattered ground radiating golden shockwaves from an explosive fist collision, "
                "crowds of sect elders and disciples watching in stunned awe from high carved stone pavilions, "
                "golden sparks and dust trails swirling in the air, sharp 4k render."
            )
        },
        {
            "index": 3, "range": (61, 70),
            "title": ["TRIAL IN THE WILDERNESS", "BEAST BLOOD HARVEST"],
            "fallback_color": (20, 30, 20),
            "prompt": (
                "Cinematic 3D atmospheric wilderness scene in a primeval spirit beast forest at twilight, "
                "colossal moss-covered roots and glowing spiritual flora, a fallen demonic beast radiating dying crimson energy, "
                "a calm cultivator standing with drawn sword harvesting rare spirit cores, deep forest mist, 4k digital art."
            )
        },
        {
            "index": 4, "range": (71, 80),
            "title": ["HEAVENLY ADVANCEMENT", "SOVEREIGN ROAR"],
            "fallback_color": (30, 15, 35),
            "prompt": (
                "Cinematic 3D epic breakthrough scene in an ancient cultivation cavern illuminated by purple spiritual lightning, "
                "golden core forming above the meditating hero, dense essence condensed into rivers of liquid light, "
                "shattering stone walls, majestic transcendent atmosphere, 4k digital masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))