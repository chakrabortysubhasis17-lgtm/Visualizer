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

BUILD_DIR = "build_the_iliad_1_147"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters (Local PDF Page Extraction: Pages 1 to 147)
    "source_type": "pdf",
    "pdf_path": r"D:\Projects\visualer\ebooks\THE ILIAD.pdf",
    "start_url": r"D:\Projects\visualer\ebooks\THE ILIAD.pdf",
    "novel_slug": "the-iliad-homer-epic",
    "start_chapter": 1,
    "end_chapter": 147,
    "default_topic": "The Iliad",

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
                "Sing, O Goddess, the ruinous wrath of Achilles, son of Peleus, that brought "
                "untold agony upon the Achaeans and cast the brave souls of countless heroes down to Hades. "
                "From the pestilence of Apollo and the furious quarrel of bronze-clad kings, "
                "to the duel of champions and Hector storming the black ships, "
                "witness the ancient cradle of epic tragedy where mortal glory is purchased with blood."
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
                "Today, we bring you the ultimate presentation of Homer's masterpiece, The Iliad, "
                "covering pages one through one hundred and forty-seven. "
                "Please note that the dialogues and verse adaptations featured in this release "
                "are the original dramatized screenplay scripts based directly on the foundational text of The Iliad. "
                "Take a moment to hit that like button, subscribe if you are new to the channel, "
                "and share your thoughts in the comments below. "
                "Set your volume, step onto the windswept sands of Troy, and let us begin."
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
    "final_audio": "output_the_iliad_1_147.mp3",
    "final_video": "final_the_iliad_1_147.mp4",
    "cover_image": "cover_the_iliad_1_147.jpg",
    "timestamps_file": "youtube_timestamps_the_iliad_1_147.txt",
    "subtitles_file": "subtitles_the_iliad_1_147.srt",
    "payload_file": "youtube_upload_payload_the_iliad_1_147.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "THE RAGE OF ACHILLES & THE SIEGE OF TROY! [Pages 1-147] | The Iliad Full Audiobook Marathon",
    "tags": [
        "The Iliad", "Homer", "Iliad", "Achilles", "Hector", "Agamemnon", "Odysseus",
        "Trojan War", "Ancient Greek Epic", "Classics Audiobook", "Mythology Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to this definitive presentation of Homer's immortal epic 'The Iliad', covering Pages 1 through 147!\n\n"
        "NOTE ON SCRIPT: This production utilizes the original dramatized screenplay scripts based directly on the classic texts of The Iliad.\n\n"
        "Experience the fury and tragedy of the Trojan War: Apollo's plague falling upon the Greek encampment, the disastrous quarrel "
        "between King Agamemnon and Achilles, and Achilles' fateful withdrawal from battle. Witness the single combat of Menelaus and Paris, "
        "the heartbreak of Hector and Andromache at the Scaean Gate, the aristeia of Diomedes wounding gods upon the field of dust, "
        "and the desperate midnight embassy pleading for Achilles' return. Experience this 147-page epic journey with multi-voice neural TTS, "
        "context-aware cinematic soundscapes, voice-aware prosody adjustments, and complete soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and rhapsodic narrative).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation using original scripts based on Homer's Iliad. Subscribe for more classic epics and legendary literature sagas!\n\n"
        "#TheIliad #Homer #TrojanWar #Achilles #Hector #AncientClassics #MythologyAudiobook #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks covering Pages 1 to 147: 1-36, 37-73, 74-110, 111-147)
    "blocks": [
        {
            "index": 1, "range": (1, 36),
            "title": ["THE RAGE OF ACHILLES", "THE BLACK SHIPS AT TROY"],
            "fallback_color": (35, 20, 15),
            "prompt": (
                "Cinematic 3D epic historical visualization of the ancient Greek warrior camp along the sandy shore of Troy, "
                "hundreds of weathered black wooden war ships beached along the Aegean coast, smoke rising from bronze-smithies, "
                "bronze-clad Mycenaean kings in horned helmets gathered outside royal linen pavilions at sunrise, "
                "dramatic chiaroscuro lighting, highly detailed 4k digital masterpiece."
            )
        },
        {
            "index": 2, "range": (37, 73),
            "title": ["THE DUEL OF CHAMPIONS", "HECTOR AT THE WALLS"],
            "fallback_color": (40, 25, 20),
            "prompt": (
                "Cinematic 3D dramatic mythological scene of the towering stone ramparts and massive Scaean Gate of ancient Troy, "
                "Prince Hector in gleaming bronze armor and horsehair helmet standing tall, overlooking the vast dust-choked plain of the Troad, "
                "massed ranks of Trojan and Achaean spearmen locked in tense standoff, golden afternoon dust storm, sharp 4k render."
            )
        },
        {
            "index": 3, "range": (74, 110),
            "title": ["THE BATTLE FOR THE TRENCH", "THE EMBASSY OF BRONZE"],
            "fallback_color": (30, 20, 30),
            "prompt": (
                "Cinematic 3D atmospheric nocturnal scene inside the royal pavilion of Achilles beside the Greek fleet, "
                "Achilles seated with a silver lyre in contemplation beside Patroclus, Odysseus and aged Phoenix pleading before him in the amber glow of oil lamps, "
                "heaps of bronze cauldrons and golden tripods gleaming in the shadows, deep emotional tension, 4k digital art."
            )
        },
        {
            "index": 4, "range": (111, 147),
            "title": ["THE BREACH OF THE GATE", "THE THOUSAND WATCHFIRES"],
            "fallback_color": (45, 15, 10),
            "prompt": (
                "Cinematic 3D climactic battle scene of Trojan prince Hector lifting a colossal boulder and shattering the double oak gates of the Greek defensive wall, "
                "splintered timbers flying, blazing pine torches illuminating the night sky, thousands of campfires blazing across the plain of Scamander like constellations, "
                "epic warfare, dynamic smoke and embers, 4k masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
