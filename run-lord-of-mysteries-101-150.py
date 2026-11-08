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

BUILD_DIR = "build_lotm_reader_101_150"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters
    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/lord-of-mysteries-starting-as-a-reader/chapter-101",
    "novel_slug": "lord-of-mysteries-starting-as-a-reader",
    "start_chapter": 101,
    "end_chapter": 150,
    "default_topic": "Lord of the Mysteries",

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
                "Beneath the gaslamp haze of Backlund and the crimson gaze of the full moon, "
                "every hidden knowledge demands a price, and every potion brings one closer to madness. "
                "Tread carefully through the shadows of the Beyonder pathways, where secrets whisper from the fog, "
                "ancient entities stir in silence, and truth is the deadliest weapon of all."
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
                "Today, we bring you chapters one hundred and one through one hundred and fifty of "
                "Lord of Mysteries: Starting as a Reader. "
                "Take a moment to hit that like button, subscribe if you are new to the channel, "
                "and share your thoughts in the comments below. Your support is the engine that keeps these grand marathons alive. "
                "Adjust your volume, steady your mind against the fog, and let us begin."
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
    "final_audio": "output_lotm_reader_101_150.mp3",
    "final_video": "final_lotm_reader_101_150.mp4",
    "cover_image": "cover_lotm_reader_101_150.jpg",
    "timestamps_file": "youtube_timestamps_lotm_reader_101_150.txt",
    "subtitles_file": "subtitles_lotm_reader_101_150.srt",
    "payload_file": "youtube_upload_payload_lotm_reader_101_150.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "BEYONDER SECRETS & OCCULT INTRIGUE! [Chapters 101-150] | Lord of Mysteries: Starting as a Reader Audiobook",
    "tags": [
        "Lord of Mysteries", "Lord of the Mysteries", "Starting as a Reader", "Beyonder",
        "Occult Fantasy", "Steampunk Mystery", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to the occult investigation arc of 'Lord of Mysteries: Starting as a Reader', "
        "covering Chapters 101 through 150!\n\n"
        "Delve deeper into Victorian gaslamp mystery, forbidden alchemical formulas, and tense clandestine meetings. "
        "Navigate higher-sequence Beyonder battles, decipher cryptic ritual prophecies, and untangle the dark webs of Backlund's "
        "secret organizations. Experience this 50-chapter marathon with multi-voice neural TTS, context-aware acoustic soundscapes, "
        "voice-aware prosody scaling, and synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and occult narrative).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more occult fantasy, mystery, and progression novels!\n\n"
        "#LordOfMysteries #StartingAsAReader #Beyonder #OccultFantasy #WebNovelAudiobook #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks covering Chapters 101 to 150: 101-113, 114-125, 126-138, 139-150)
    "blocks": [
        {
            "index": 1, "range": (101, 113),
            "title": ["GASLAMP SECRETS", "THE READER'S DEDUCTION"],
            "fallback_color": (25, 20, 30),
            "prompt": (
                "Cinematic 3D Victorian steampunk mystery illustration of a foggy Backlund street at midnight, "
                "glowing brass gaslamps casting long amber beams across wet cobblestones, "
                "a sharp detective in a dark trench coat and top hat holding an occult grimoire with glowing blue script, "
                "distant Victorian brick clocktower shrouded in mist, highly detailed 4k digital masterpiece."
            )
        },
        {
            "index": 2, "range": (114, 125),
            "title": ["RITUAL IN THE SHADOWS", "THE CRIMSON MOON"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic 3D dark fantasy interior of an ancient alchemical laboratory, "
                "a massive stained-glass arched window looking out upon an eerie crimson full moon, "
                "brass astrolabes, bubbling potion vials, and floating tarot cards circling a carved obsidian altar, "
                "rich atmospheric chiaroscuro lighting, sharp 4k render."
            )
        },
        {
            "index": 3, "range": (126, 138),
            "title": ["BEYONDER CLASH", "THE POWER OF KNOWLEDGE"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic 3D supernatural action scene in a dilapidated Victorian cathedral at dusk, "
                "a Reader pathway Beyonder unleashing glowing runic energy seals against shadowy eldritch tentacles, "
                "shattered stained glass and flying dust particles catching moonlight, "
                "tense suspenseful atmosphere, hyper-detailed 4k digital art."
            )
        },
        {
            "index": 4, "range": (139, 150),
            "title": ["THE TARIFF OF MADNESS", "ASCENSION IN THE FOG"],
            "fallback_color": (15, 20, 25),
            "prompt": (
                "Cinematic 3D gothic establishing shot of an ornate private study overlooking the Thames river in dense smog, "
                "golden candlelight illuminating tall bookshelves lined with forbidden leatherbound tomes, "
                "an empty high-backed velvet armchair beside a smoking brass censer, "
                "mysterious dignified atmosphere, 4k digital masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
