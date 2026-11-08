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

BUILD_DIR = "build_beast_taming_306_340"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters
    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/beast-taming-my-beasts-grind-die-and-respawn/chapter-306",
    "novel_slug": "beast-taming-my-beasts-grind-die-and-respawn",
    "start_chapter": 306,
    "end_chapter": 340,
    "default_topic": "Beast Taming",

    # Concurrency Settings & Hardcoded Narrator Lock
    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Dynamic Intro Sequence
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "Where ordinary tamers fear death and guard their fragile contracts, "
                "one tamer turns every fallen battle into an infinite engine of power. "
                "With every demise, his beasts return stronger, deadlier, and evolved beyond comprehension. "
                "Step back into the trial grounds where death is only the beginning of true ascension."
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
                "Today, we bring you chapters three hundred and six through three hundred and forty of "
                "Beast Taming: My Beasts Grind, Die, and Respawn. "
                "Take a moment to hit that like button, subscribe if you are new to the channel, "
                "and share your thoughts in the comments below. Your support is the engine that keeps these marathons alive. "
                "Adjust your volume, check your status screens, and let us begin."
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
    "final_audio": "output_beast_taming_306_340.mp3",
    "final_video": "final_beast_taming_306_340.mp4",
    "cover_image": "cover_beast_taming_306_340.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_306_340.txt",
    "subtitles_file": "subtitles_beast_taming_306_340.srt",
    "payload_file": "youtube_upload_payload_beast_taming_306_340.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "INFINITE RESPAWN ASCENSION & APEX EVOLUTION! [Chapters 306-340] | Beast Taming Full Audiobook",
    "tags": [
        "Beast Taming", "My Beasts Grind Die and Respawn", "Lu Yu", "Infinite Respawn",
        "LitRPG Audiobook", "Monster Taming", "Web Novel Audio", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to the continuous evolution marathon of 'Beast Taming: My Beasts Grind, Die, and Respawn', "
        "covering Chapters 306 through 340!\n\n"
        "Follow Lu Yu as his bonded beasts push through catastrophic trials, turning relentless death into explosive "
        "evolutionary breakthroughs. Watch high-tier calamity beasts fall before an undying legion that learns from every "
        "defeat. Experience this 35-chapter arc with multi-voice neural TTS, context-aware acoustic soundscapes, "
        "voice-aware prosody adjustments, and synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system notifications).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more beast taming, LitRPG, and progression fantasy sagas!\n\n"
        "#BeastTaming #MyBeastsGrindDieAndRespawn #LitRPG #MonsterEvolution #WebNovel #BeingABong"
    ),

    # Visual Prompts (4 balanced thematic blocks covering Chapters 306 to 340)
    "blocks": [
        {
            "index": 1, "range": (306, 314),
            "title": ["DEATH AND REBIRTH", "THE GRINDING DOMAIN"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D dark fantasy illustration of a young beast tamer commanding an undying spectral familiar, "
                "golden and ethereal purple resurrection runes igniting across shattered arena ground, "
                "a skeletal mythical beast rising reconstituted from swirling silver flames, "
                "dramatic chiaroscuro illumination, highly detailed 4k digital masterpiece."
            )
        },
        {
            "index": 2, "range": (315, 323),
            "title": ["SYSTEM ATTRIBUTE SURGE", "TALENT EVOLUTION"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D LitRPG scene inside a high-tier mystical trial cavern, "
                "translucent blue and gold holographic status panels glowing in the air showing skill breakthrough tiers, "
                "spiritual essence forming cascading streams of light around the bonded beast familiar, "
                "sharp reflections on crystalline cavern walls, 4k digital art."
            )
        },
        {
            "index": 3, "range": (324, 331),
            "title": ["CLASH WITH CALAMITY", "SHATTERED BOUNDARIES"],
            "fallback_color": (40, 15, 20),
            "prompt": (
                "Cinematic 3D action scene of a colossal calamity-tier beast crashing through stone ruins, "
                "massive shockwaves tearing through the earth as an agile evolved familiar delivers an explosive counter-strike, "
                "flying rubble and glowing embers under a turbulent stormy sky, hyper-detailed 4k render."
            )
        },
        {
            "index": 4, "range": (332, 340),
            "title": ["APEX ASCENSION", "THE UNDYING SOVEREIGN"],
            "fallback_color": (25, 35, 25),
            "prompt": (
                "Cinematic 3D epic establishing shot of the beast tamer standing atop a conquered mountain peak at sunrise, "
                "majestic fully evolved divine beasts flanked beside him radiating radiant golden auras, "
                "clouds parting under blinding divine rays, supreme authority and triumphant atmosphere, 4k digital masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
