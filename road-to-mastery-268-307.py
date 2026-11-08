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

BUILD_DIR = "build_road_to_mastery_268_307"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters
    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/road-to-mastery-a-litrpg-apocalypse/chapter-268",
    "novel_slug": "road-to-mastery-a-litrpg-apocalypse",
    "start_chapter": 268,
    "end_chapter": 307,
    "default_topic": "Road to Mastery",

    # Concurrency Settings & Hardcoded Narrator Lock
    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Dynamic Action-Packed Intro Sequence
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "In a universe reshaped by the merciless rules of the System, "
                "where cosmic factions pit mortal survivors against impossible trials, "
                "only iron fists and unyielding willpower shatter the threshold of mortality. "
                "Step back into the arena of survival as Jack Rust and his gorilla brother Brock "
                "clash against alien powerhouses, unleash devastating fist techniques, "
                "and push the brawler path toward supreme mastery."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "impact",
            "bgm_mood": "combat"
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
            "bgm_mood": "combat"
        },
        {
            "line_id": "intro_02_body",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "Welcome back to Being a Bong. We narrate the unreal worlds to life. "
                "Today, we bring you chapters two hundred and sixty-eight through three hundred and seven of "
                "Road to Mastery: A LitRPG Apocalypse. "
                "If you enjoy relentless hand-to-hand combat, progression grit, and apocalyptic survival, "
                "take a moment to hit that like button, subscribe if you are new to the channel, "
                "and drop your thoughts in the comments below. Your support is the engine that keeps these grand releases alive. "
                "Wrap your hands, adjust your volume, and let's step into the fray."
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
    "final_audio": "output_road_to_mastery_268_307.mp3",
    "final_video": "final_road_to_mastery_268_307.mp4",
    "cover_image": "cover_road_to_mastery_268_307.jpg",
    "timestamps_file": "youtube_timestamps_road_to_mastery_268_307.txt",
    "subtitles_file": "subtitles_road_to_mastery_268_307.srt",
    "payload_file": "youtube_upload_payload_road_to_mastery_268_307.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "BRAWLER'S WILL & ALIEN TRIAL BREAKTHROUGH! [Chapters 268-307] | Road to Mastery LitRPG Audiobook",
    "tags": [
        "Road to Mastery", "Road to Mastery A LitRPG Apocalypse", "Jack Rust", "LitRPG Audiobook",
        "Progression Fantasy", "Apocalypse Fiction", "Martial Arts LitRPG", "Web Novel Audio", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to the continuous progression marathon of 'Road to Mastery: A LitRPG Apocalypse', "
        "covering Chapters 268 through 307!\n\n"
        "Follow Jack Rust and Brock as they battle through deadly high-tier trials, shattering alien scions, leveling combat skills, "
        "and advancing along the path of pure physical mastery. Every strike tests Jack's resolve against cosmic entities that treat "
        "Earth's apocalypse as entertainment. Experience this 40-chapter LitRPG arc with multi-voice neural TTS, context-aware acoustic "
        "soundscapes, voice-aware prosody scaling, and synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system notifications).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more apocalyptic LitRPG, martial arts, and progression fantasy sagas!\n\n"
        "#RoadToMastery #LitRPG #ProgressionFantasy #ApocalypseAudiobook #JackRust #WebNovel #BeingABong"
    ),

    # Visual Prompts (4 balanced thematic blocks covering Chapters 268 to 307: 268-277, 278-287, 288-297, 298-307)
    "blocks": [
        {
            "index": 1, "range": (268, 277),
            "title": ["FISTS OF RECKONING", "THE ARENA OF BLOOD"],
            "fallback_color": (35, 15, 15),
            "prompt": (
                "Cinematic 3D sci-fi LitRPG combat illustration inside a massive floating alien colosseum arena, "
                "a muscular human brawler with wrapped fists delivering a thunderous punch that shatters the stone floor with shockwaves, "
                "a massive armored gorilla beast companion smashing through rival gladiators, glowing blue holographic status panels floating in air, "
                "dynamic motion blur and flying rock debris, highly detailed 4k digital masterpiece."
            )
        },
        {
            "index": 2, "range": (278, 287),
            "title": ["SYSTEM BREAKTHROUGH", "COSMIC ESSENCE FORGING"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D progression fantasy scene in a subterranean crystal chamber glowing with ethereal starlight, "
                "a battle-scarred martial artist meditating while golden and azure aura vortexes coil around his muscular frame, "
                "glowing status windows displaying skill mastery upgrades, atmospheric volumetric lighting, sharp 4k render."
            )
        },
        {
            "index": 3, "range": (288, 297),
            "title": ["EXTRATERRESTRIAL ENCOUNTER", "THE SAGE'S SHADOW"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D dramatic science-fantasy exterior scene on a ruined alien world under twin moons, "
                "towering monolithic stone ruins carved with extraterrestrial glyphs, "
                "the brawler standing back-to-back with his silverback beast ally facing towering chimeric monsters, "
                "tense suspenseful atmosphere, rich chiaroscuro illumination, hyper-detailed 4k digital art."
            )
        },
        {
            "index": 4, "range": (298, 307),
            "title": ["UNBREAKABLE WILL", "APEX BRAWLER ASCENSION"],
            "fallback_color": (40, 25, 15),
            "prompt": (
                "Cinematic 3D epic establishing view of the hero standing triumphant atop a colossal cratered summit at sunrise, "
                "his fists smoking with golden kinetic shockwave energy, cosmic clouds swirling in a vibrant dawn sky, "
                "majestic power and raw physical determination, 4k digital masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
