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

BUILD_DIR = "build_the_odyssey_1_151"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters (Local PDF Page Extraction: Pages 1 to 151)
    "source_type": "pdf",
    "pdf_path": r"D:\Projects\visualer\ebooks\THE ODYSSEY.pdf",
    "start_url": r"D:\Projects\visualer\ebooks\THE ODYSSEY.pdf",
    "novel_slug": "the-odyssey-homer-epic",
    "start_chapter": 1,
    "end_chapter": 151,
    "default_topic": "The Odyssey",

    # Concurrency Settings & Hardcoded Narrator Lock
    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Mir-Style Dynamic Intro Sequence Passed in intro_hook (Original Scripts Notice Included)
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "Sing in me, Muse, and through me tell the story of that man of twists and turns, "
                "driven time and again off course once he had plundered the hallowed heights of Troy. "
                "From the troubled halls of Ithaca where suitors feast upon his wealth, "
                "to the enchanted shores of Ogygia, the cave of the Cyclops, and the perilous halls of Circe, "
                "journey into the wine-dark sea alongside Odysseus on his epic quest for home."
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
                "Today, we bring you the premiere release of Homer's timeless ancient voyage, The Odyssey, "
                "covering pages one through one hundred and fifty-one. "
                "Please note that the dialogues and verse adaptations featured in this production "
                "are the original dramatized screenplay scripts based directly on the classic foundation of The Odyssey. "
                "Take a moment to hit that like button, subscribe if you are new to the channel, "
                "and share your reflections in the comments below. "
                "Cast off from the shores, adjust your volume, and let the voyage begin."
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
    "final_audio": "output_the_odyssey_1_151.mp3",
    "final_video": "final_the_odyssey_1_151.mp4",
    "cover_image": "cover_the_odyssey_1_151.jpg",
    "timestamps_file": "youtube_timestamps_the_odyssey_1_151.txt",
    "subtitles_file": "subtitles_the_odyssey_1_151.srt",
    "payload_file": "youtube_upload_payload_the_odyssey_1_151.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "WANDERINGS OF ODYSSEUS & THE VOYAGE HOME! [Pages 1-151] | The Odyssey Full Audiobook Marathon",
    "tags": [
        "The Odyssey", "Homer", "Odyssey", "Odysseus", "Telemachus", "Penelope",
        "Cyclops", "Circe", "Calypso", "Ancient Greek Epic", "Classics Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to the premiere volume of Homer's legendary ancient epic 'The Odyssey', covering Pages 1 through 151!\n\n"
        "NOTE ON SCRIPT: This production features original dramatized screenplay scripts based directly on the foundational texts of The Odyssey.\n\n"
        "Embark upon the greatest sea-voyage in world literature: young Telemachus setting sail from suitor-besieged Ithaca to find news of his father, "
        "Athena's divine guidance, and Odysseus held captive on the misty island of Calypso. Witness Odysseus' perilous raft voyage, the wrath of Poseidon, "
        "and his miraculous rescue on the shores of Phaeacia. Relive his harrowing tales recounted to King Alcinous—the lotus-drugged shores, the deadly "
        "cave of the Cyclops Polyphemus, the sorcery of Circe turning men into swine, the descent into the shadowy Underworld to consult the seer Tiresias, "
        "and the deadly song of the Sirens. Experience this 151-page epic journey with multi-voice neural TTS, context-aware acoustic soundscapes, "
        "voice-aware prosody adjustments, and synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and rhapsodic narrative).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation using original scripts based on Homer's Odyssey. Subscribe for more classic epics and legendary literature sagas!\n\n"
        "#TheOdyssey #Homer #Odysseus #AncientClassics #GreekMythology #MythologyAudiobook #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks covering Pages 1 to 151: 1-38, 39-76, 77-114, 115-151)
    "blocks": [
        {
            "index": 1, "range": (1, 38),
            "title": ["THE TELEMACHY", "THE SHADOW OVER ITHACA"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D historical epic illustration of the stone palace of Ithaca overlooking a sparkling Mediterranean bay at dawn, "
                "Prince Telemachus in Grecian robes standing near ancient marble colonnades looking out toward the sea, "
                "insolent suitors gathered at banquet tables in the courtyard, goddess Athena disguised as a mentor veiled in soft divine light, "
                "warm atmospheric morning illumination, highly detailed 4k digital masterpiece."
            )
        },
        {
            "index": 2, "range": (39, 76),
            "title": ["ISLE OF OGYGIA", "THE WRATH OF POSEIDON"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic 3D dramatic mythological scene of Odysseus navigating a wooden raft through colossal ocean waves during a tempest, "
                "Poseidon's shadowy silhouette visible within dark thunderous storm clouds wielding a bronze trident, "
                "white sea foam and rain lashing against the timber craft under flashes of lightning, turbulent waters, sharp 4k render."
            )
        },
        {
            "index": 3, "range": (77, 114),
            "title": ["THE CAVE OF THE CYCLOPS", "TALES OF WONDER"],
            "fallback_color": (35, 20, 15),
            "prompt": (
                "Cinematic 3D moody dark fantasy interior scene inside the colossal cavern of Polyphemus the Cyclops, "
                "a massive one-eyed giant asleep beside a towering boulder sealing the cave entrance, "
                "Greek sailors moving stealthily in the shadows with an olive-wood stake by the glow of a dying campfire, "
                "rich chiaroscuro lighting, tense and suspenseful atmosphere, 4k digital art."
            )
        },
        {
            "index": 4, "range": (115, 151),
            "title": ["CIRCE'S ENCHANTMENT", "THE DESCENT TO HADES"],
            "fallback_color": (25, 15, 30),
            "prompt": (
                "Cinematic 3D mystical scene on the enchanted island of Aeaea outside the marble palace of the sorceress Circe, "
                "golden loom gleaming on an open terrace surrounded by tame wolves and mountain lions moving peacefully, "
                "purple dusk sky with a rising crescent moon casting eerie shimmering reflections across stone terraces, "
                "magical and mythical atmosphere, 4k masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
