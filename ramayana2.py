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

BUILD_DIR = "build_the_ramayana_230_398"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters (Final Part: Pages 230 to 398)
    "source_type": "pdf",
    "pdf_path": r"D:\Projects\visualer\ebooks\The Ramayana.pdf",
    "start_url": r"D:\Projects\visualer\ebooks\The Ramayana.pdf",
    "novel_slug": "the-ramayana-ancient-epic",
    "start_chapter": 230,
    "end_chapter": 398,
    "default_topic": "The Ramayana",

    # Concurrency Settings & Hardcoded Narrator Lock
    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Mir-Style Dynamic Intro Sequence Passed in intro_hook (Series Grand Finale)
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "From the deep heart of Kishkindha and the leap across the roaring ocean, "
                "to the cataclysmic clash of divine astras outside the golden gates of Lanka, "
                "witness the final triumph of righteousness over darkness. "
                "Follow Prince Rama, Lakshmana, and the heroic vanara army as they breach the demon stronghold, "
                "vanquish the ten-headed Ravana, and fulfill the ancient prophecy of the Treta Yuga."
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
                "Today, we bring you the grand concluding chapter of the ancient Sanskrit epic, The Ramayana, "
                "covering pages two hundred and thirty to the epic conclusion at page three hundred and ninety-eight. "
                "If you've walked this sacred journey with us, hit that like button, subscribe to the channel, "
                "and share your thoughts in the comments below. "
                "Settle in for this monumental final saga, turn up the volume, and let's bring the legend to its glorious completion."
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
    "final_audio": "output_the_ramayana_230_398.mp3",
    "final_video": "final_the_ramayana_230_398.mp4",
    "cover_image": "cover_the_ramayana_230_398.jpg",
    "timestamps_file": "youtube_timestamps_the_ramayana_230_398.txt",
    "subtitles_file": "subtitles_the_ramayana_230_398.srt",
    "payload_file": "youtube_upload_payload_the_ramayana_230_398.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "THE WAR FOR DHARMA & CORONATION IN AYODHYA! [Pages 230-398 END] | The Ramayana Full Audiobook Finale",
    "tags": [
        "The Ramayana", "Ramayana", "Valmiki Ramayana", "Ramayana Ending", "Rama", "Sita",
        "Hanuman", "Ravana", "War of Lanka", "Yuddha Kanda", "Ramayana Finale", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to the grand finale and final volume of the ancient epic 'The Ramayana', covering Pages 230 through 398!\n\n"
        "Experience the climactic culmination of the sacred legend: the alliance with Sugriva and the leap of Hanuman across the southern seas, "
        "the building of the oceanic bridge Ram Setu, and the apocalyptic War of Lanka. Witness the fall of Kumbhakarna, the fierce clash of Indrajit, "
        "and the final duel between Prince Rama and the ten-headed demon king Ravana using the celestial Brahmastra. Celebrate the rescue of Sita, "
        "the triumphant return upon the Pushpaka Vimana, and Rama's glorious coronation as King of Ayodhya, marking the dawn of the golden age of Ramrajya.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogues and verse narration).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation of the ancient epic is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more classic epics and legendary literature sagas!\n\n"
        "#Ramayana #TheRamayana #AncientEpics #RamayanaFinale #Rama #Hanuman #Ravana #MythologyAudiobook #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks covering Pages 230 to 398: 230-271, 272-313, 314-355, 356-398)
    "blocks": [
        {
            "index": 1, "range": (230, 271),
            "title": ["THE ALLIANCE OF KISHKINDHA", "HANUMAN'S GREAT LEAP"],
            "fallback_color": (30, 25, 15),
            "prompt": (
                "Cinematic 3D epic mythological visualization of Lord Hanuman expanding to colossal size on Mount Mahendra preparing to leap across the turbulent southern ocean, "
                "golden fur glowing with celestial energy, storm clouds parting under divine light, vanara warriors Sugriva and Angada watching in reverence from rocky crags, "
                "massive ocean waves crashing against jagged sea cliffs, highly detailed dynamic lighting, 4k digital masterpiece."
            )
        },
        {
            "index": 2, "range": (272, 313),
            "title": ["RAM SETU & THE MARCH ON LANKA", "THE GATES OF THE CITADEL"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic 3D mythological scene of the vanara army constructing the sacred stone bridge Ram Setu across the vast ocean towards the towering golden fortress of Lanka, "
                "giant floating stones inscribed with sacred Sanskrit letters, Lord Rama and Lakshmana with bows standing at the vanguard, "
                "dark dramatic thunderstorm brewing over the black obsidian spires of Lanka in the distance, vibrant atmospheric 4k render."
            )
        },
        {
            "index": 3, "range": (314, 355),
            "title": ["THE CLASH OF ASTRAS", "THE FALL OF RAVANA"],
            "fallback_color": (45, 15, 10),
            "prompt": (
                "Cinematic 3D climactic mythological battle between Lord Rama and the ten-headed demon king Ravana on a smoking war-torn battlefield outside Lanka, "
                "Rama on a golden chariot drawing the radiant blazing Brahmastra bow, celestial cosmic arrows colliding with dark demonic sorcery, "
                "fiery embers, shattered chariots, epic divine scale, dramatic chiaroscuro illumination, hyper-detailed 4k digital art."
            )
        },
        {
            "index": 4, "range": (356, 398),
            "title": ["THE RETURN TO AYODHYA", "THE CORONATION OF RAMA"],
            "fallback_color": (40, 30, 10),
            "prompt": (
                "Cinematic 3D glorious mythological scene of the grand coronation of King Rama and Queen Sita on the golden throne of Ayodhya, "
                "Lord Rama wearing radiant royal crowns and silk robes, Sita by his side, Lakshmana, Bharata, Shatrughna, and Hanuman kneeling in profound devotion, "
                "great sages showering celestial flowers and sacred waters, golden oil lamps illuminating opulent marble pillars, divine triumph, 4k masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
