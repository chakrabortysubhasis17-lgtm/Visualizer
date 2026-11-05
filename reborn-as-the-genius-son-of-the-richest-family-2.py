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

BUILD_DIR = "build_reborn_genius_son_51_100"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "reborn-as-the-genius-son-of-the-richest-family",
    "start_url": "https://freewebnovel.com/novel/reborn-as-the-genius-son-of-the-richest-family/chapter-51",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "Reborn as the Genius Son of the Richest Family",

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
                "In our previous chapters, having secured his standing within the conglomerate, our reincarnated heir executed "
                "surgical market maneuvers that stunned senior directors and crippled aggressive hostile takeovers. But as his private "
                "venture empire takes root, old-money cabals and underground financial syndicates unite to force a market collapse."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "coin",
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
                "In this episode, we step right back into the high-stakes boardroom arena, picking up where the billion-dollar trades left off, "
                "take a second to hit that like button, subscribe if you are new to the channel, and drop your thoughts in the comments. "
                "Your support is the engine that keeps this massive releases alive. "
                "Settle in as the trading bell rings, adjust your volume, and let's begin today's episode."
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
    "final_audio": "output_reborn_genius_son_51_100.mp3",
    "final_video": "final_reborn_genius_son_51_100.mp4",
    "cover_image": "cover_reborn_genius_son_51_100.jpg",
    "timestamps_file": "youtube_timestamps_reborn_genius_son_51_100.txt",
    "subtitles_file": "subtitles_reborn_genius_son_51_100.srt",
    "payload_file": "youtube_upload_payload_reborn_genius_son_51_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "MARKET CRASH & CONGLOMERATE TAKEOVER! [Ch 51-100] | Genius Son Urban Reincarnation Full Audiobook",
    "tags": [
        "Reborn as the Genius Son of the Richest Family", "Urban Fantasy Audiobook", "Business Tycoon",
        "Reincarnation Audiobook", "Genius Son", "Billionaire Heir", "Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Reborn as the Genius Son of the Richest Family' covering Chapters 51 through 100!\n\n"
        "Stepping beyond domestic corporate skirmishes, our protagonist leverages future knowledge to navigate international commodity "
        "wars, short hostile financial empires, and establish his personal tech monopoly. Watch as every trap laid by rival dynasties "
        "becomes his greatest windfall. Experience this 50-chapter marathon with multi-voice neural TTS, context-aware acoustic "
        "soundscapes, and full synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, internal thoughts, and financial analysis).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more chapters and tycoon reincarnation sagas!\n\n"
        "#RebornAsTheGeniusSon #RichestFamily #UrbanReincarnation #BusinessTycoon #Audiobook #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks across Ch 51 to 100: 51-62, 63-75, 76-88, 89-100)
    "blocks": [
        {
            "index": 1, "range": (51, 62),
            "title": ["GLOBAL CAPITAL WAR", "SHORTING THE MARKET"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic 3D render of a high-tech modern financial command center with the young tycoon in an open-collar dark suit "
                "analyzing towering curved monitors displaying plummeting red and green market candlestick charts. "
                "Late night ambient blue glow, city skyline through panoramic glass, intense calculating gaze, sharp 4k render."
            )
        },
        {
            "index": 2, "range": (63, 75),
            "title": ["LUXURY AUCTION SHOWDOWN", "PRICELESS ASSETS"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D illustration of an opulent private auction house inside a neoclassical opera hall, "
                "the young protagonist raising an engraved paddle with calm confidence while rival billionaires look on in shock. "
                "Velvet drapery, warm chandelier illumination, detailed fabric and gold watch textures, cinematic depth of field."
            )
        },
        {
            "index": 3, "range": (76, 88),
            "title": ["CORPORATE PURGE", "THE HEIR'S MANDATE"],
            "fallback_color": (25, 20, 30),
            "prompt": (
                "Cinematic 3D dramatic scene in an executive glass boardroom, the young heir dropping a thick dossier of corrupt contracts onto the table "
                "in front of sweating, trembling enterprise directors. Sharp daylight rim lighting, modern minimalist skyscraper architecture, 4k digital art."
            )
        },
        {
            "index": 4, "range": (89, 100),
            "title": ["TECH MONOPOLY", "THE EMPIRE STANDS ALONE"],
            "fallback_color": (20, 30, 40),
            "prompt": (
                "Cinematic 3D view of the protagonist standing atop a helipad of a newly inaugurated corporate headquarters, "
                "watching autonomous drones and city transit below during a dramatic golden sunset. "
                "Wind fluttering his trench coat, majestic urban vista, cinematic lighting, masterpiece 4k render."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
