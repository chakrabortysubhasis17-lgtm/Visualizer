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

BUILD_DIR = "build_the_odyssey_152_291"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters (Finale: Pages 152 to 291)
    "source_type": "pdf",
    "pdf_path": r"D:\Projects\visualer\ebooks\THE ODYSSEY.pdf",
    "start_url": r"D:\Projects\visualer\ebooks\THE ODYSSEY.pdf",
    "novel_slug": "the-odyssey-homer-epic",
    "start_chapter": 152,
    "end_chapter": 291,
    "default_topic": "The Odyssey",

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
                "After twenty years of wandering across storm-tossed seas, the exile sets foot upon the rocky shores of Ithaca. "
                "Disguised as a battered beggar by Athena's divine grace, Odysseus enters his own palace in stealth, "
                "bearing the insults of insolent suitors while waiting for the fateful hour of vengeance. "
                "Witness the stringing of the great horn bow, the thunderous judgment in the banquet hall, "
                "and the tender reunion beneath the ancient olive tree as the legendary king reclaims his throne."
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
                "Today, we bring you the grand concluding finale of Homer's immortal epic, The Odyssey, "
                "covering pages one hundred and fifty-two to two hundred and ninety-one. "
                "Please note that the dialogues and verse adaptations featured throughout this production "
                "are the original dramatized screenplay scripts based directly on the timeless text of The Odyssey. "
                "If you have journeyed with us across the wine-dark seas, take a second to hit that like button, "
                "subscribe to the channel, and share your reflections in the comments below. "
                "Prepare for the king's reckoning, turn up the volume, and let us bring the voyage home."
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
    "final_audio": "output_the_odyssey_152_291.mp3",
    "final_video": "final_the_odyssey_152_291.mp4",
    "cover_image": "cover_the_odyssey_152_291.jpg",
    "timestamps_file": "youtube_timestamps_the_odyssey_152_291.txt",
    "subtitles_file": "subtitles_the_odyssey_152_291.srt",
    "payload_file": "youtube_upload_payload_the_odyssey_152_291.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "THE RETURN OF THE KING & THE RECKONING IN ITHACA! [Pages 152-291 END] | The Odyssey Full Audiobook Finale",
    "tags": [
        "The Odyssey", "Homer", "Odyssey", "Odyssey Ending", "Odysseus", "Penelope", "Telemachus",
        "Eumaeus", "Slaughter of the Suitors", "Greek Mythology", "Classics Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to the grand finale and final volume of Homer's legendary ancient voyage 'The Odyssey', covering Pages 152 through 291!\n\n"
        "NOTE ON SCRIPT: This production features original dramatized screenplay scripts based directly on the foundational texts of The Odyssey.\n\n"
        "Experience the climactic return of Odysseus to his homeland: landing secretly upon the shores of Ithaca, taking refuge in the humble hut "
        "of loyal swineherd Eumaeus, and revealing his identity to his son Telemachus. Witness the poignant moment his old hunting dog Argos recognizes "
        "his master after twenty years, and the suspenseful test in the palace as Odysseus endures the arrogance of the suitors while disguised as a beggar. "
        "The saga culminates in Penelope's contest of the bow, the terrifying storm of arrows in the banquet hall as the suitors meet their doom, "
        "the secret test of the olive-wood marriage bed, and final peace restored over Ithaca by Athena's divine grace.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and rhapsodic narrative).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation using original scripts based on Homer's Odyssey. Subscribe for more classic epics and legendary literature sagas!\n\n"
        "#TheOdyssey #Homer #Odysseus #AncientClassics #GreekMythology #OdysseyEnding #MythologyAudiobook #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks covering Pages 152 to 291: 152-186, 187-221, 222-256, 257-291)
    "blocks": [
        {
            "index": 1, "range": (152, 186),
            "title": ["RETURN TO ITHACA", "THE SWINEHERD'S HUT"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D historical epic illustration of Odysseus disguised as an aged weathered beggar wrapped in coarse cloak, "
                "standing outside a rustic stone and timber swineherd cottage on the rugged hills of Ithaca at twilight, "
                "faithful hunting hounds resting near wooden palisades, distant view of the Aegean Sea under soft golden sunset clouds, "
                "poignant atmospheric illumination, highly detailed 4k digital masterpiece."
            )
        },
        {
            "index": 2, "range": (187, 221),
            "title": ["THE SHADOW IN THE PALACE", "THE FAITHFUL ARGOS"],
            "fallback_color": (35, 20, 25),
            "prompt": (
                "Cinematic 3D dramatic scene in the grand stone courtyard of the palace of Ithaca, "
                "insolent suitors banqueted under marble colonnades in drunken revelry, "
                "Odysseus in tattered rags sitting near the palace gates looking down at his old loyal hound Argos resting in the dust, "
                "rich chiaroscuro lighting, deep emotional tension, sharp 4k render."
            )
        },
        {
            "index": 3, "range": (222, 256),
            "title": ["THE STRINGING OF THE GREAT BOW", "THE RECKONING"],
            "fallback_color": (45, 15, 15),
            "prompt": (
                "Cinematic 3D climactic battle scene inside the ancient Greek feast hall of Ithaca, "
                "Odysseus standing tall by the great threshold drawing a massive composite horn bow, divine lightning flashing behind him, "
                "arrows flying toward panicked suitors scattering behind overturned oak banquet tables, "
                "prince Telemachus with bronze spear at his side, dynamic shadows and flying sparks, hyper-detailed 4k digital art."
            )
        },
        {
            "index": 4, "range": (257, 291),
            "title": ["THE OLIVE-TREE BED", "PEACE RESTORED TO ITHACA"],
            "fallback_color": (25, 30, 25),
            "prompt": (
                "Cinematic 3D serene and glorious scene of Odysseus and Queen Penelope embracing in their royal chamber, "
                "a massive bed intricately carved into the trunk of a living olive tree rooted in the stone floor, "
                "warm golden candlelight, moonlight streaming through high balcony arches overlooking peaceful olive groves and calm sea waters, "
                "sacred triumph and peace, 4k digital masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
