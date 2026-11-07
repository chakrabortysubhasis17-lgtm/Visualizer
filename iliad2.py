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

BUILD_DIR = "build_the_iliad_148_287"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters (Finale: Pages 148 to 287)
    "source_type": "pdf",
    "pdf_path": r"D:\Projects\visualer\ebooks\THE ILIAD.pdf",
    "start_url": r"D:\Projects\visualer\ebooks\THE ILIAD.pdf",
    "novel_slug": "the-iliad-homer-epic",
    "start_chapter": 148,
    "end_chapter": 287,
    "default_topic": "The Iliad",

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
                "From the blazing sterns of the Greek fleet and the tragic fall of Patroclus, "
                "to the divine armor forged by Hephaestus and the cosmic duel beneath the Scaean walls, "
                "witness the final, heartbreaking culmination of Homer's masterpiece. "
                "Behold Achilles unleashed in cataclysmic fury, the doom of horse-taming Hector, "
                "and the midnight meeting of tears between Priam and the slayer of his sons."
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
                "Today, we bring you the grand concluding finale of Homer's immortal epic, The Iliad, "
                "covering pages one hundred and forty-eight to two hundred and eighty-seven. "
                "Please note that the dialogues and verse adaptations featured throughout this production "
                "are the original dramatized screenplay scripts based directly on the timeless text of The Iliad. "
                "If you have journeyed with us across the plains of Troy, take a second to hit that like button, "
                "subscribe to the channel, and drop your thoughts in the comments below. "
                "Prepare for this monumental final saga, turn up the volume, and let us bring the epic to its close."
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
    "final_audio": "output_the_iliad_148_287.mp3",
    "final_video": "final_the_iliad_148_287.mp4",
    "cover_image": "cover_the_iliad_148_287.jpg",
    "timestamps_file": "youtube_timestamps_the_iliad_148_287.txt",
    "subtitles_file": "subtitles_the_iliad_148_287.srt",
    "payload_file": "youtube_upload_payload_the_iliad_148_287.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "THE DEATH OF PATROCLUS & THE FALL OF HECTOR! [Pages 148-287 END] | The Iliad Full Audiobook Finale",
    "tags": [
        "The Iliad", "Homer", "Iliad", "Iliad Ending", "Achilles", "Hector", "Patroclus",
        "Priam", "Trojan War", "Shield of Achilles", "Classics Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to the grand finale and concluding volume of Homer's immortal ancient epic 'The Iliad', covering Pages 148 through 287!\n\n"
        "NOTE ON SCRIPT: This production utilizes the original dramatized screenplay scripts based directly on the classic texts of The Iliad.\n\n"
        "Experience the climactic and devastating conclusion of the Trojan War: the storming of the Greek ships, Patroclus taking the field "
        "in the armor of Achilles, and his fatal clash with Sarpedon and Hector. Witness Achilles' shattering grief, the forging of his divine "
        "shield by Hephaestus, his terrifying return to battle choking the river Scamander with the slain, and the fateful final duel against "
        "Hector outside the walls of Troy. The epic concludes with the solemn funeral games of Patroclus and King Priam's perilous midnight "
        "journey into Achilles' tent to ransom the body of his son, closing with the burial of Hector, tamer of horses.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and rhapsodic narrative).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation using original scripts based on Homer's Iliad. Subscribe for more classic epics and legendary literature sagas!\n\n"
        "#TheIliad #Homer #TrojanWar #Achilles #Hector #Patroclus #AncientClassics #MythologyAudiobook #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks covering Pages 148 to 287: 148-182, 183-217, 218-252, 253-287)
    "blocks": [
        {
            "index": 1, "range": (148, 182),
            "title": ["THE SHIPS IN FLAMES", "THE ARISTEIA OF PATROCLUS"],
            "fallback_color": (45, 15, 10),
            "prompt": (
                "Cinematic 3D dramatic mythological battle scene of the Greek fleet burning on the sands of Troy, "
                "black beached warships engulfed in roaring orange flames and thick billowing smoke, "
                "Patroclus clad in the gleaming armor of Achilles leading the charging Myrmidon phalanx, "
                "flying bronze-tipped spears and shattered shields under a blood-red sky, hyper-detailed 4k digital masterpiece."
            )
        },
        {
            "index": 2, "range": (183, 217),
            "title": ["THE DEATH OF PATROCLUS", "THE SHIELD OF ACHILLES"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D mystical and tragic scene in the divine forge of Mount Olympus, "
                "the god Hephaestus shaping the colossal celestial shield of Achilles on a glowing bronze anvil with showering golden sparks, "
                "intricate cosmic reliefs of constellations, cities at war, and peaceful harvests wrought in gold and silver, "
                "goddess Thetis watching with sorrowful reverence, radiant dramatic lighting, 4k render."
            )
        },
        {
            "index": 3, "range": (218, 252),
            "title": ["THE RAGE UNLEASHED", "THE DUEL OF ACHILLES AND HECTOR"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D epic confrontation outside the stone walls and Scaean Gate of Troy, "
                "Achilles radiating divine solar fire charging with his massive Pelian ash spear, "
                "Prince Hector standing resolute in bronze armor awaiting his fate on the dusty plain, "
                "the Trojan elders and weeping Andromache watching from the high parapets, tense atmosphere, sharp 4k digital art."
            )
        },
        {
            "index": 4, "range": (253, 287),
            "title": ["PRIAM'S MIDNIGHT PLEA", "THE FUNERAL OF HECTOR"],
            "fallback_color": (25, 20, 25),
            "prompt": (
                "Cinematic 3D poignant historical scene inside Achilles' dim tent at midnight, "
                "aged white-haired King Priam kneeling in deep sorrow and kissing the hands of Achilles, "
                "Achilles gazing down with tears of grief and shared mortal tragedy, warm amber glow from a single oil lamp, "
                "emotional chiaroscuro atmosphere, profound reverence, 4k digital masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))