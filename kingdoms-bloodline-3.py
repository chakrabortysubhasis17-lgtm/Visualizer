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

BUILD_DIR = "build_kingdoms_bloodline_57_84"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters
    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/kingdoms-bloodline/chapter-57",
    "novel_slug": "kingdoms-bloodline",
    "start_chapter": 57,
    "end_chapter": 84,
    "default_topic": "Kingdom's Bloodline",

    # Concurrency Settings & Hardcoded Narrator Lock
    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Mir-Style Dynamic Intro Sequence Passed in intro_hook (Chapters 57 to 84)
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "In a realm where crowns are forged in blood, treachery, and ancient debt, "
                "every political maneuver carries the weight of a kingdom's doom. "
                "Step deeper into the dark, intricate web of power as noble houses clash, "
                "secrets are buried in shadows, and survival demands a cold, calculating mind."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "gong",
            "bgm_mood": "intrigue"
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
            "bgm_mood": "intrigue"
        },
        {
            "line_id": "intro_02_body",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "Welcome back to Being a Bong. We narrate the unreal worlds to life. "
                "We are thrilled to bring you chapters fifty-seven through eighty-four of Kingdom's Bloodline. "
                "Take a second to hit that like button, subscribe if you are new to the channel, "
                "and drop your thoughts in the comments. Your support is the engine that keeps these multi-chapter arcs alive. "
                "Adjust your volume, steady your nerves, and let's step back into the intrigue."
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
    "final_audio": "output_kingdoms_bloodline_57_84.mp3",
    "final_video": "final_kingdoms_bloodline_57_84.mp4",
    "cover_image": "cover_kingdoms_bloodline_57_84.jpg",
    "timestamps_file": "youtube_timestamps_kingdoms_bloodline_57_84.txt",
    "subtitles_file": "subtitles_kingdoms_bloodline_57_84.srt",
    "payload_file": "youtube_upload_payload_kingdoms_bloodline_57_84.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "THE WEB OF TREASON & ROYAL INTRIGUE! [Chapters 57-84] | Kingdom's Bloodline Audiobook",
    "tags": [
        "Kingdom's Bloodline", "Kingdoms Bloodline Novel", "Fantasy Political Intrigue",
        "Web Novel Audio", "Dark Fantasy", "Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to the continuous narrative arc of 'Kingdom's Bloodline', covering Chapters 57 through 84!\n\n"
        "Dive deeper into the treacherous underbelly of court politics, dangerous power struggles, and psychological warfare. "
        "Every alliance is tested and every secret threatens to unravel empires. Experience this multi-chapter arc with "
        "multi-voice neural TTS, context-aware acoustic soundscapes, and synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogues and narrative).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more dark fantasy epics and web novel sagas!\n\n"
        "#KingdomsBloodline #FantasyAudiobook #PoliticalIntrigue #DarkFantasy #WebNovel #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks covering Chapters 57 to 84)
    "blocks": [
        {
            "index": 1, "range": (57, 63),
            "title": ["SHADOWS IN THE COURT", "THE WHISPERS OF TREASON"],
            "fallback_color": (30, 20, 25),
            "prompt": (
                "Cinematic 3D dark fantasy illustration of a medieval stone council chamber bathed in flickering torchlight, "
                "noble lords gathered around an oak table covered in parchment maps and sealed royal decrees, "
                "deep brooding shadows, tense political atmosphere, highly detailed atmospheric lighting, 4k digital art."
            )
        },
        {
            "index": 2, "range": (64, 70),
            "title": ["THE CALCULATED GAMBIT", "ALLIANCES OF CONVENIENCE"],
            "fallback_color": (25, 25, 35),
            "prompt": (
                "Cinematic 3D moody interior scene of a high gothic castle library at midnight, "
                "tall stained glass windows casting moonlight across polished marble floors, an ornate desk with open ledgers and quills, "
                "mysterious hooded figures conferring in hushed tones, dramatic chiaroscuro lighting, sharp 4k render."
            )
        },
        {
            "index": 3, "range": (71, 77),
            "title": ["THE BLADE IN THE DARK", "DANGEROUS ENCOUNTERS"],
            "fallback_color": (35, 15, 15),
            "prompt": (
                "Cinematic 3D gritty medieval street scene in a foggy capital city at dusk, "
                "cobblestone alleys reflecting lantern light through thick mist, cloaked figures moving stealthily near ancient stone walls, "
                "suspenseful and perilous atmosphere, hyper-detailed 4k digital masterpiece."
            )
        },
        {
            "index": 4, "range": (78, 84),
            "title": ["THE TURNING TIDE", "RECKONING AT DAWN"],
            "fallback_color": (20, 30, 30),
            "prompt": (
                "Cinematic 3D epic establishing shot of a grand feudal fortress looming over a misty valley at sunrise, "
                "banners fluttering from stone battlements, royal guards in polished plate armor standing at attention, "
                "majestic and imposing atmosphere, 4k digital art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
