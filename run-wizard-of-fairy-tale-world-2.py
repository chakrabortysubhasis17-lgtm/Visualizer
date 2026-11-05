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

BUILD_DIR = "build_wizard_fairy_tale_world_51_100"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "the-wizard-of-fairy-tale-world",
    "start_url": "https://freewebnovel.com/novel/the-wizard-of-fairy-tale-world/chapter-51",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "The Wizard of Fairy Tale World",

    # Concurrency Settings & Narrator Lock
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Full Mir-Style Dynamic Intro Sequence Passed in intro_hook (Continuing Marathon)
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "In our previous chapters, traversing the deceptive wonder of ancient fairy tale realms, "
                "our calculating wizard dissected enchanted curses, harvested rare magical bloodlines, "
                "and turned classic fables on their heads. But peeling back the surface of enchanted kingdoms "
                "has uncovered darker primordial horrors lurking behind every storybook crown."
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
                "In this episode, we step right back into the arcane secrets, picking up where the dark curses and spellcraft left off, "
                "take a second to hit that like button, subscribe if you are new to the channel, and drop your thoughts in the comments. "
                "Your support is the engine that keeps this massive releases alive. "
                "Settle in as the grimoires open, adjust your volume, and let's begin today's episode."
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
    "final_audio": "output_wizard_fairy_tale_world_51_100.mp3",
    "final_video": "final_wizard_fairy_tale_world_51_100.mp4",
    "cover_image": "cover_wizard_fairy_tale_world_51_100.jpg",
    "timestamps_file": "youtube_timestamps_wizard_fairy_tale_world_51_100.txt",
    "subtitles_file": "subtitles_wizard_fairy_tale_world_51_100.srt",
    "payload_file": "youtube_upload_payload_wizard_fairy_tale_world_51_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "DARK FAIRY TALE CURSES & ARCANE RESEARCH! [Ch 51-100] | The Wizard of Fairy Tale World Audiobook",
    "tags": [
        "The Wizard of Fairy Tale World", "Wizard in Fairy Tale World", "Dark Fantasy Audiobook",
        "Magus", "Fairy Tale Fantasy", "Progression Fantasy", "Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'The Wizard of Fairy Tale World' covering Chapters 51 through 100!\n\n"
        "Delving deeper into twisted fairytale domains, our protagonist approaches fables not with romantic ideals, "
        "but with the cold, methodical curiosity of an arcane wizard. From cursed glass relics and witch covens to royal "
        "bloodline experiments, watch as he bends storybook magic into supreme wizardry. Experience this 50-chapter marathon "
        "with multi-voice neural TTS, context-aware acoustic soundscapes, and full synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, arcane research, and spellcraft).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more chapters and dark fantasy wizard sagas!\n\n"
        "#TheWizardOfFairyTaleWorld #WizardInFairyTaleWorld #DarkFantasy #Magus #ProgressionFantasy #Audiobook #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks covering Ch 51 to 100: 51-62, 63-75, 76-88, 89-100)
    "blocks": [
        {
            "index": 1, "range": (51, 62),
            "title": ["ARCANE LABORATORY", "DISSECTING THE CURSE"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic 3D dark fantasy illustration of a robed wizard working inside a stone tower laboratory, "
                "floating magical grimoires surrounded by cyan spell circles, analyzing glowing glass slippers and cursed mirrors. "
                "Alchemical vials bubbling with bioluminescent potions, moonlight pouring through gothic arched windows, 4k digital art."
            )
        },
        {
            "index": 2, "range": (63, 75),
            "title": ["WITCH COVEN ENCOUNTER", "TWISTED FOREST"],
            "fallback_color": (25, 20, 30),
            "prompt": (
                "Cinematic 3D dark fantasy scene in a dense thorny forest shrouded in purple mist, "
                "the young wizard raising his glowing staff against shadowy witch figures surrounded by glowing green fire. "
                "Twisted ancient trees with carved faces, glowing raven eyes in the branches, dramatic rim lighting, sharp 4k render."
            )
        },
        {
            "index": 3, "range": (76, 88),
            "title": ["ROYAL COURT INTRIGUE", "PUPPET MONARCHS"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D fantasy illustration of a grand fairytale throne room where a decadent king and noble lords "
                "are bound by glowing translucent puppet strings, while the wizard stands calmly in the shadows holding an ancient parchment. "
                "Rich velvet drapery, tall stained glass windows, chiaroscuro lighting, highly detailed textures."
            )
        },
        {
            "index": 4, "range": (89, 100),
            "title": ["TIER BREAKTHROUGH", "SOVEREIGN ARCANIST"],
            "fallback_color": (15, 20, 35),
            "prompt": (
                "Cinematic 3D epic dark fantasy view of the wizard standing atop the highest pinnacle of an enchanted castle, "
                "commanding a swirling celestial vortex of arcane energy and runic circles lighting up the stormy night sky. "
                "Billowing midnight robes, glowing eyes, majestic scale, masterpiece 4k render."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
