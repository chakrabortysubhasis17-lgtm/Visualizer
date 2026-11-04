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

BUILD_DIR = "build_kingdoms_bloodline_29_56"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "kingdoms-bloodline",
    "start_url": "https://freewebnovel.com/novel/kingdoms-bloodline/chapter-29",
    "start_chapter": 29,
    "end_chapter": 56,
    "default_topic": "Kingdom's Bloodline",

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
                "In our previous chapters, from the squalor of the Lower City slums to the blood-slicked corridors of power, "
                "young Thales was thrust into the center of an imperial tempest. Carrying the perilous blood of the Constellation dynasty, "
                "he faced shadowy assassin orders and ruthless ministers with nothing but raw intellect and calculated defiance."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "bells",
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
                "In this episode, we step right back into the lion's den, picking up where the court conspiracies and hidden blades collided, "
                "take a second to hit that like button, subscribe if you are new to the channel, and drop your thoughts in the comments. "
                "Your support is the engine that keeps this massive releases alive. "
                "Prepare your mind for the games of royalty, adjust your volume, and let's begin today's episode."
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
    "final_audio": "output_kingdoms_bloodline_29_56.mp3",
    "final_video": "final_kingdoms_bloodline_29_56.mp4",
    "cover_image": "cover_kingdoms_bloodline_29_56.jpg",
    "timestamps_file": "youtube_timestamps_kingdoms_bloodline_29_56.txt",
    "subtitles_file": "subtitles_kingdoms_bloodline_29_56.srt",
    "payload_file": "youtube_upload_payload_kingdoms_bloodline_29_56.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "ROYAL INTRIGUE & COURT OF ASSASSINS! [Ch 29-56] | Kingdom's Bloodline Epic Fantasy Audiobook",
    "tags": [
        "Kingdoms Bloodline", "Kingdom's Bloodline", "Epic Fantasy Audiobook", "Dark Fantasy",
        "Political Fantasy", "Reincarnation", "Royal Bloodline", "Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Kingdom's Bloodline' with Chapters 29 through 56!\n\n"
        "Stepping deeper into the treacherous halls of the Constellation Kingdom, young Thales finds himself surrounded "
        "by iron-fisted monarchs, calculating ministers, and covert assassin orders. Stripped of physical power, he must "
        "rely entirely on surgical logic, psychological warfare, and nerves of steel to survive the deadly games of royalty. "
        "Experience this 28-chapter political fantasy arc with multi-voice neural TTS, context-aware acoustic soundscapes, "
        "and full soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for all dialogue, internal monologues, and narrative prose).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more chapters and political fantasy sagas!\n\n"
        "#KingdomsBloodline #EpicFantasy #DarkFantasy #PoliticalFantasy #Audiobook #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks covering Ch 29 to 56: 29-35, 36-42, 43-49, 50-56)
    "blocks": [
        {
            "index": 1, "range": (29, 35),
            "title": ["ROYAL REVELATION", "SHADOW OF MIND PALACE"],
            "fallback_color": (25, 20, 25),
            "prompt": (
                "Cinematic 3D dark fantasy illustration of 7-year-old Thales dressed in formal noble attire, "
                "standing under a towering gothic stone archway inside a dimly lit royal castle corridor. "
                "Candlelight casting long dramatic shadows, royal guards in polished plate armor standing at attention, intense reflective gaze."
            )
        },
        {
            "index": 2, "range": (36, 42),
            "title": ["COUNCIL OF VIPERS", "DIPLOMATIC STRATAGEM"],
            "fallback_color": (30, 25, 15),
            "prompt": (
                "Cinematic 3D fantasy portrait of the young prince seated at a massive crescent council table "
                "facing stern, aristocratic noble lords and ministers, holding an ornate wax seal in his hand. "
                "Volumetric dust motes in sunbeams through tall stained-glass windows, rich velvet cloaks and furs, cinematic depth of field."
            )
        },
        {
            "index": 3, "range": (43, 49),
            "title": ["ASSASSIN NIGHT", "THE BLADE BEHIND SILK"],
            "fallback_color": (15, 20, 30),
            "prompt": (
                "Cinematic 3D action thriller scene in a grand bedchamber at midnight, showing the young boy dodging behind an ornate marble pillar "
                "as a masked assassin in black leather leaps with drawn daggers, intercepted by a loyal knight's broadsword. "
                "Sparks flying, torn silk tapestries, dark moonlit room with cold blue shadows, highly detailed 3D render."
            )
        },
        {
            "index": 4, "range": (50, 56),
            "title": ["CONSTELLATION THRONE", "UNWAVERING RESOLVE"],
            "fallback_color": (35, 20, 20),
            "prompt": (
                "Cinematic 3D epic fantasy scene of young Thales standing tall before the imposing Iron Throne of Constellation, "
                "looking upward at the austere king beneath the radiant blue star-patterned banner. "
                "Grand hall filled with armored knights and heraldic standards, dramatic chiaroscuro illumination, sharp 4k rendering."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
