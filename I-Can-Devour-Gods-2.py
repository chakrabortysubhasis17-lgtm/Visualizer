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

BUILD_DIR = "build_sss_awakening_46_90"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters
    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/sss-awakening-i-can-devour-gods-to-evolve-my-goddesses/chapter-46",
    "novel_slug": "sss-awakening-i-can-devour-gods-to-evolve-my-goddesses",
    "start_chapter": 46,
    "end_chapter": 90,
    "default_topic": "SSS Awakening: I Can Devour Gods to Evolve My Goddesses",

    # Concurrency Settings & Hardcoded Narrator Lock
    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Dynamic Awakening Intro Sequence
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "When primordial deities fall from the heavens, ordinary awakeners see apocalyptic catastrophe. "
                "One contractor sees an all-you-can-eat divine banquet. "
                "With forbidden devouring talents devouring godhead remnants and feeding celestial divinity to his bonded goddesses, "
                "witness ancient pantheons tremble as Su Chen marches beyond the mortal domain."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "levelup",
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
                "Today, we bring you chapters forty-six through ninety of "
                "SSS Awakening: I Can Devour Gods to Evolve My Goddesses. "
                "Take a moment to hit that like button, subscribe if you are new to the channel, "
                "and drop your thoughts in the comments below. Your support is the engine that keeps these grand releases alive. "
                "Adjust your volume, brace for divine evolution, and let us begin."
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
    "final_audio": "output_sss_awakening_46_90.mp3",
    "final_video": "final_sss_awakening_46_90.mp4",
    "cover_image": "cover_sss_awakening_46_90.jpg",
    "timestamps_file": "youtube_timestamps_sss_awakening_46_90.txt",
    "subtitles_file": "subtitles_sss_awakening_46_90.srt",
    "payload_file": "youtube_upload_payload_sss_awakening_46_90.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "DEVOURING FALLEN GODS & GODDESS EVOLUTION! [Chapters 46-90] | SSS Awakening Full Audiobook",
    "tags": [
        "SSS Awakening", "I Can Devour Gods to Evolve My Goddesses", "Su Chen",
        "God Devourer", "Goddess Evolution", "Urban Fantasy Audiobook",
        "Web Novel Audio", "LitRPG Awakening", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to the continuous divine ascension of 'SSS Awakening: I Can Devour Gods to Evolve My Goddesses', "
        "covering Chapters 46 through 90!\n\n"
        "Follow Su Chen as his SSS-tier God Devourer system consumes higher-tier divinity fragments, unlocking unprecedented "
        "combat transformations and elemental awakenings for his bonded goddesses[cite: 2]. Watch arrogant academy rivals and hidden sect elders "
        "get overwhelmed by overwhelming celestial power[cite: 2]. Experience this 45-chapter arc with multi-voice neural TTS, "
        "context-aware acoustic soundscapes, voice-aware dynamic rate scaling, and synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system prompts).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more divine awakening, system progression, and urban fantasy sagas!\n\n"
        "#SSSAwakening #ICanDevourGodsToEvolveMyGoddesses #SuChen #GodDevourer #WebNovelAudiobook #BeingABong"
    ),

    # Visual Prompts (4 balanced thematic blocks covering Chapters 46 to 90: 46-56, 57-67, 68-78, 79-90)
    "blocks": [
        {
            "index": 1, "range": (46, 56),
            "title": ["DEVOURING DIVINITY", "THE FIRST GODDESS BREAKTHROUGH"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D urban fantasy illustration of a young male contractor standing before a shattered divine monument, "
                "dark crimson devouring vortexes swirling from his hand consuming radiant golden divinity particles, "
                "beside him an ethereal ice goddess with flowing silver hair glowing with frosted celestial energy, "
                "dramatic chiaroscuro lighting, highly detailed 4k digital masterpiece."
            )
        },
        {
            "index": 2, "range": (57, 67),
            "title": ["ACADEMY TRIALS", "CRUSHING THE ARROGANT SCIONS"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic 3D combat arena scene inside a grand futuristic fantasy academy stadium, "
                "shockwaves of frost and azure flame tearing across reinforced battle platforms, "
                "arrogant scions recoiling in disbelief as twin evolved goddesses unleash overwhelming divine pressure, "
                "flying rubble and glowing energy sparks, sharp 4k render."
            )
        },
        {
            "index": 3, "range": (68, 78),
            "title": ["REALM EXPANSION", "THE FLAME GODDESS UNLEASHED"],
            "fallback_color": (40, 20, 10),
            "prompt": (
                "Cinematic 3D dynamic action scene in a desolate dimensional rift at twilight, "
                "a fiery war goddess with blazing crimson wings commanding pillars of incinerating holy fire, "
                "burning alien monoliths collapsing under immense heat, embers drifting into an apocalyptic sky, "
                "hyper-detailed 4k digital art."
            )
        },
        {
            "index": 4, "range": (79, 90),
            "title": ["PANTHEON SOVEREIGNTY", "ASCENSION BEYOND MORTALITY"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D epic establishing shot of the protagonist standing atop a floating celestial platform overlooking a sea of clouds, "
                "multiple radiant goddesses in divine armors flanking him in absolute loyalty, "
                "golden aura piercing the starry cosmos, majestic godhead ascension, 4k digital masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
