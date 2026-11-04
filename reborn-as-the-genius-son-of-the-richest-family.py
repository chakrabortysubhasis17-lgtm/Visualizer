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

BUILD_DIR = "build_reborn_genius_son_1_50"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "reborn-as-the-genius-son-of-the-richest-family",
    "start_url": "https://freewebnovel.com/novel/reborn-as-the-genius-son-of-the-richest-family/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Reborn as the Genius Son of the Richest Family",

    # Concurrency Settings & Narrator Lock
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Full Mir-Style Dynamic Intro Sequence Passed in intro_hook (Premiere Episode)
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "In the cutthroat arena of global capital, billions change hands in seconds, but few ever get a second chance at life. "
                "Betrayed and bankrupted in his past life, a financial prodigy awakens back in time—reborn into the most influential, "
                "unfathomably wealthy dynasty on the planet. Armed with decades of future economic foresight and the bottomless resources "
                "of an empire, he steps forth to claim the throne and dismantle his enemies before they even make their moves."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "coin",
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
                "We are thrilled to bring you the premiere episode of this urban business saga, "
                "take a second to hit that like button, subscribe if you are new to the channel, and drop your thoughts in the comments. "
                "Your support is the engine that keeps this massive releases alive. "
                "Prepare for a masterclass in wealth and retribution, adjust your volume, and let's begin today's episode."
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
    "final_audio": "output_reborn_genius_son_1_50.mp3",
    "final_video": "final_reborn_genius_son_1_50.mp4",
    "cover_image": "cover_reborn_genius_son_1_50.jpg",
    "timestamps_file": "youtube_timestamps_reborn_genius_son_1_50.txt",
    "subtitles_file": "subtitles_reborn_genius_son_1_50.srt",
    "payload_file": "youtube_upload_payload_reborn_genius_son_1_50.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "REBORN AS THE RICHEST HEIR! [Ch 1-50] | Genius Tycoon Urban Reincarnation Full Audiobook",
    "tags": [
        "Reborn as the Genius Son of the Richest Family", "Urban Fantasy Audiobook", "Business Tycoon",
        "Reincarnation Audiobook", "Genius Son", "Billionaire Heir", "Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to the premiere release of 'Reborn as the Genius Son of the Richest Family' covering Chapters 1 through 50!\n\n"
        "Given a second chance at life, a genius investor reincarnates as the young heir to an all-powerful trillion-dollar conglomerate. "
        "With memories of the future, global tech shifts, and financial crashes, he maneuvers through high-society vultures, outsmarts "
        "rival business conglomerates, and forges an unstoppable modern dynasty. Experience this 50-chapter premiere marathon with "
        "multi-voice neural TTS, context-aware acoustic soundscapes, and full synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, internal thoughts, and market analysis).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more chapters and tycoon reincarnation sagas!\n\n"
        "#RebornAsTheGeniusSon #RichestFamily #UrbanReincarnation #BusinessTycoon #Audiobook #BeingABong"
    ),

    # Visual Prompts (4 balanced thematic blocks across Ch 1 to 50: 1-12, 13-25, 26-38, 39-50)
    "blocks": [
        {
            "index": 1, "range": (1, 12),
            "title": ["REBIRTH OF THE HEIR", "THE BILLION-DOLLAR AWAKENING"],
            "fallback_color": (25, 25, 35),
            "prompt": (
                "Cinematic 3D illustration of a sharp young man in a tailored black suit standing by a floor-to-ceiling penthouse window "
                "overlooking a sprawling neon-lit modern metropolis at night. Raindrops on the glass, golden reflections, "
                "luxury modern penthouse interior, quiet calculated expression, cinematic atmospheric lighting, 4k digital art."
            )
        },
        {
            "index": 2, "range": (13, 25),
            "title": ["BOARDROOM STRATAGEM", "FAMILY POWER CLASH"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D render of a high-stakes corporate boardroom meeting inside a skyscraper, "
                "the young genius heir confidently addressing elderly executives and investors with digital market holographic charts floating in mid-air. "
                "Polished mahogany table, elegant architectural design, crisp rim lighting, sharp 4k render."
            )
        },
        {
            "index": 3, "range": (26, 38),
            "title": ["HIGH SOCIETY GAMBIT", "BANQUET SHOWDOWN"],
            "fallback_color": (35, 20, 25),
            "prompt": (
                "Cinematic 3D lavish gala banquet scene inside a grand marble ballroom, luxury chandeliers hanging overhead, "
                "the well-dressed young protagonist holding a glass of champagne, surrounded by whispering aristocrats and envious rivals. "
                "Warm golden illumination, photorealistic clothing folds, dramatic depth of field."
            )
        },
        {
            "index": 4, "range": (39, 50),
            "title": ["FINANCIAL EMPIRE", "THE NEW TYCOON RISES"],
            "fallback_color": (20, 30, 35),
            "prompt": (
                "Cinematic 3D low-angle view of the young tycoon stepping out of a sleek luxury limousine in front of a towering corporate headquarters, "
                "bodyguards holding umbrellas under a light drizzle, flashing press cameras in the background. "
                "Sophisticated atmosphere, wet pavement reflections, dramatic cinematic lighting, masterpiece 4k render."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
