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

BUILD_DIR = "build_the_spy_cooper_10_207"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters (Local PDF Page Extraction)
    "source_type": "pdf",
    "pdf_path": r"D:\Projects\visualer\ebooks\The-Spy-James-Fenimore-Cooper.pdf",
    "start_url": r"D:\Projects\visualer\ebooks\The-Spy-James-Fenimore-Cooper.pdf",
    "novel_slug": "the-spy-a-tale-of-the-neutral-ground",
    "start_chapter": 10,
    "end_chapter": 207,
    "default_topic": "The Spy: A Tale of the Neutral Ground",

    # Concurrency Settings & Hardcoded Narrator Lock
    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Mir-Style Dynamic Intro Sequence Passed in intro_hook (Premiere Episode)
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "In the contested neutral ground of Westchester during the American Revolution, "
                "loyalty is a fatal commodity. Betwixt the encampments of British regulars and "
                "Continental patriots, shadows conceal double agents, guerilla marauders, and unyielding martyrs. "
                "Here walks Harvey Birch—a solitary peddler despised by his countrymen as a traitor, "
                "yet bound to a covert oath that will shape the fate of a nascent nation."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "wind",
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
                "We are thrilled to bring you the premiere episode of James Fenimore Cooper's timeless historical masterpiece, "
                "covering pages ten through two hundred and seven. Take a second to hit that like button, "
                "subscribe if you are new to the channel, and drop your thoughts in the comments. "
                "Your support is the engine that keeps this massive releases alive. "
                "Step into the mist of the neutral ground, adjust your volume, and let's begin today's episode."
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
    "final_audio": "output_the_spy_10_207.mp3",
    "final_video": "final_the_spy_10_207.mp4",
    "cover_image": "cover_the_spy_10_207.jpg",
    "timestamps_file": "youtube_timestamps_the_spy_10_207.txt",
    "subtitles_file": "subtitles_the_spy_10_207.srt",
    "payload_file": "youtube_upload_payload_the_spy_10_207.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "THE NEUTRAL GROUND & THE SHADOW PATRIOT! [Pages 10-207] | The Spy Historical Classic Full Audiobook",
    "tags": [
        "The Spy", "James Fenimore Cooper", "Historical Fiction", "Audiobook", "American Revolution",
        "Harvey Birch", "Classic Literature", "Espionage Classic", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to the premiere release of James Fenimore Cooper's classic novel 'The Spy: A Tale of the Neutral Ground', "
        "covering Pages 10 through 207!\n\n"
        "Set in 1780 during the height of the American Revolutionary War, the county of Westchester becomes a lawless corridor "
        "of espionage and betrayal between the British and Continental armies. Follow Harvey Birch, an enigmatic peddler suspected "
        "of treason, as he navigates clandestine missions, hostile cavalry patrols, and dangerous loyalties. Experience this "
        "198-page historical marathon with multi-voice neural TTS, context-aware acoustic soundscapes, and full synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and period prose).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation of James Fenimore Cooper's public domain classic is produced for educational, "
        "literary commentary, and entertainment purposes. Subscribe for more classic literature marathons and historical audio dramas!\n\n"
        "#TheSpy #JamesFenimoreCooper #ClassicAudiobook #HistoricalFiction #AmericanRevolution #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks covering Pages 10 to 207: 10-59, 60-109, 110-159, 160-207)
    "blocks": [
        {
            "index": 1, "range": (10, 59),
            "title": ["THE SOLITARY TRAVELER", "THE LOCUSTS ESTATE"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D historical illustration of an autumn twilight in 1780 Westchester, "
                "a cloaked solitary traveler riding along a muddy dirt trail toward a colonial mansion with glowing candlelight windows. "
                "Gnarled leafless oak trees, dense rolling fog, chilling rain mist, brooding atmospheric chiaroscuro lighting, 4k digital art."
            )
        },
        {
            "index": 2, "range": (60, 109),
            "title": ["THE MYSTERIOUS PEDDLER", "MIDNIGHT RENDEZVOUS"],
            "fallback_color": (25, 20, 20),
            "prompt": (
                "Cinematic 3D portrait of Harvey Birch the peddler carrying a weathered leather pack over his shoulder, "
                "whispering to a masked Continental officer inside a dim rustic stone tavern by a roaring hearth. "
                "Shadows cast across wooden beams, antique tallow candles, flintlock pistols on the table, dramatic cinematic lighting."
            )
        },
        {
            "index": 3, "range": (110, 159),
            "title": ["CAVALRY CLASH", "SKIRMISH AT THE NEUTRAL GROUND"],
            "fallback_color": (35, 20, 15),
            "prompt": (
                "Cinematic 3D Revolutionary War battle scene in a rolling wooded valley, "
                "blue-coated Virginia Continental dragoons clashing sabers with British redcoat infantry and skinners. "
                "Musket smoke drifting through autumnal forests, galloping horses, dynamic action framing, sharp 4k render."
            )
        },
        {
            "index": 4, "range": (160, 207),
            "title": ["THE UNKNOWN SPY", "FAITHFUL UNTO DEATH"],
            "fallback_color": (20, 25, 30),
            "prompt": (
                "Cinematic 3D dramatic historical scene of the peddler standing on a rocky hill overlooking a river valley at dawn, "
                "holding a secret letter bearing an unbroken wax seal as Continental regiments march in the far distance below. "
                "Dramatic sunrise breaking through storm clouds, wind whipping his wool coat, resolute expression, masterpiece 4k rendering."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
