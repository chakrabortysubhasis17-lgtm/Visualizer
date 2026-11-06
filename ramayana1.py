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

BUILD_DIR = "build_the_ramayana_1_229"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters (Local PDF Page Extraction)
    "source_type": "pdf",
    "pdf_path": r"D:\Projects\visualer\ebooks\The Ramayana.pdf",
    "start_url": r"D:\Projects\visualer\ebooks\The Ramayana.pdf",
    "novel_slug": "the-ramayana-ancient-epic",
    "start_chapter": 1,
    "end_chapter": 229,
    "default_topic": "The Ramayana",

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
                "In an era where the cosmos was anchored by sacred oaths and the law of dharma, "
                "the divine descent of righteousness walked upon the earth. "
                "From the grand palaces of Ayodhya and the sacred bow of Shiva in Mithila, "
                "to the bitter tears of Dasharatha and the solemn banishment into the wild Dandaka forest, "
                "experience the immortal saga of Prince Rama—the supreme exemplar of truth, honor, and unyielding virtue."
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
                "We are thrilled to bring you this epic presentation of The Ramayana, "
                "covering pages one through two hundred and twenty-nine. Take a moment to hit that like button, "
                "subscribe if you are new to the channel, and share your reflections in the comments below. "
                "Your support is the engine that keeps these grand marathons alive. "
                "Step into the dawn of the Treta Yuga, adjust your volume, and let's begin today's journey."
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
    "final_audio": "output_the_ramayana_1_229.mp3",
    "final_video": "final_the_ramayana_1_229.mp4",
    "cover_image": "cover_the_ramayana_1_229.jpg",
    "timestamps_file": "youtube_timestamps_the_ramayana_1_229.txt",
    "subtitles_file": "subtitles_the_ramayana_1_229.srt",
    "payload_file": "youtube_upload_payload_the_ramayana_1_229.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "THE DIVINE INCARNATION TO THE FOREST EXILE! [Pages 1-229] | The Ramayana Epic Full Audiobook",
    "tags": [
        "The Ramayana", "Ramayana", "Valmiki Ramayana", "Rama", "Sita", "Lakshmana",
        "Ayodhya", "Bala Kanda", "Ayodhya Kanda", "Ancient Epic", "Mythology Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to this comprehensive premiere release of the sacred ancient epic 'The Ramayana', covering Pages 1 through 229!\n\n"
        "Experience the complete foundation of this timeless legend: King Dasharatha's sacred Putrakameshti sacrifice, the miraculous "
        "birth of the four princes in Ayodhya, Rama's youth defending Sage Vishvamitra's yajna, the miraculous breaking of Lord Shiva's bow "
        "in King Janaka's court, and his divine wedding with Sita. Journey onward as palace politics and Kaikeyi's boons plunge the kingdom into "
        "mourning, leading to Rama's graceful renunciation of the throne, the grief of Ayodhya, and his noble journey into the Dandaka forest "
        "with Sita and Lakshmana. Experience this 229-page mythological masterpiece with multi-voice neural TTS, context-aware acoustic "
        "soundscapes, and synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogues and verse narration).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation of the ancient epic is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more classic epics and legendary literature sagas!\n\n"
        "#Ramayana #TheRamayana #AncientEpics #Rama #Sita #Valmiki #MythologyAudiobook #IndianClassics #BeingABong"
    ),

    # Visual Prompts (4 balanced thematic blocks covering Pages 1 to 229: 1-57, 58-114, 115-171, 172-229)
    "blocks": [
        {
            "index": 1, "range": (1, 57),
            "title": ["AYODHYA & THE DIVINE AVATAR", "THE BLESSING OF DASHARATHA"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D sacred epic illustration of the ancient golden city of Ayodhya on the banks of the shimmering Sarayu River at sunrise, "
                "majestic Vedic marble palaces with carved sandstone pillars and fluttering saffron pennants, rishis performing sacred yajna fire rituals with glowing embers, "
                "divine golden sun rays piercing through celestial clouds, highly detailed atmospheric lighting, 4k digital art."
            )
        },
        {
            "index": 2, "range": (58, 114),
            "title": ["THE BOW OF SHIVA", "THE WEDDING IN MITHILA"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D epic mythological scene of Prince Rama stringing the colossal celestial Bow of Shiva in King Janaka's grand court at Mithila, "
                "divine blue-complexioned prince radiating radiant light, sacred lotus petals descending from the heavens, ornate royal court filled with astonished sages and kings, "
                "Princess Sita watching with reverence and joy, vibrant cinematic chiaroscuro lighting, sharp 4k render."
            )
        },
        {
            "index": 3, "range": (115, 171),
            "title": ["KAIKEYI'S BOON", "THE SHADOW OVER THE THRONE"],
            "fallback_color": (30, 20, 20),
            "prompt": (
                "Cinematic 3D dramatic mythological interior scene of King Dasharatha collapsed in anguish before Queen Kaikeyi in a dimly lit marble palace chamber, "
                "flickering brass oil lamps casting long weeping shadows against intricately carved stone walls, scattered royal ornaments on the floor, heavy tragic atmosphere, "
                "poignant emotional tension, 4k digital masterpiece."
            )
        },
        {
            "index": 4, "range": (172, 229),
            "title": ["EXILE TO THE FOREST", "DANDAKA SANCTUARY"],
            "fallback_color": (20, 30, 20),
            "prompt": (
                "Cinematic 3D atmospheric scene of Rama, Sita, and Lakshmana clad in simple bark hermit robes walking peacefully into the primeval Dandaka forest at twilight, "
                "dense ancient banyan trees with hanging moss, gentle deer grazing near a tranquil river, golden evening light filtering through the dense canopy, "
                "sacred and serene solitude, masterpiece 4k render."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
