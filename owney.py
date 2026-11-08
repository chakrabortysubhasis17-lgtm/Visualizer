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

BUILD_DIR = "build_owney_the_dog_1_140"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters (Complete 140-Page Volume)
    "source_type": "pdf",
    "pdf_path": r"D:\Projects\visualer\ebooks\OWNEY THE DOG.pdf",
    "start_url": r"D:\Projects\visualer\ebooks\OWNEY THE DOG.pdf",
    "novel_slug": "owney-the-dog-railway-mascot",
    "start_chapter": 1,
    "end_chapter": 140,
    "default_topic": "Owney the Dog",

    # Concurrency Settings & Hardcoded Narrator Lock
    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Dynamic Atmospheric Intro Sequence
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "On a freezing autumn evening in 1888, a drenched, wire-haired terrier wandered into the Albany Post Office, "
                "curling atop a pile of canvas mail sacks to escape the storm. "
                "Neither the sorting clerks nor the Postmaster could foresee that this scruffy stray would become "
                "the good-luck charm of the Railway Mail Service, survive forty thousand miles of iron rails without a single wreck, "
                "wear an armored vest of over one thousand brass medals, and circumnavigate the globe as America's greatest canine ambassador."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "chime",
            "bgm_mood": "warmth"
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
            "bgm_mood": "warmth"
        },
        {
            "line_id": "intro_02_body",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "Welcome back to Being a Bong. We narrate the unreal worlds to life. "
                "Today, we bring you the complete unabridged presentation of Owney the Dog, "
                "covering all one hundred and forty pages of this original cinematic historical narrative. "
                "If you cherish the romance of the steam rail era and the enduring bond between working men and their four-legged guardian, "
                "take a moment to hit that like button, subscribe to the channel, and leave your thoughts in the comments below. "
                "Listen for the whistle down the line, settle in, and let's ride the rails with Owney."
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
    "final_audio": "output_owney_the_dog_1_140.mp3",
    "final_video": "final_owney_the_dog_1_140.mp4",
    "cover_image": "cover_owney_the_dog_1_140.jpg",
    "timestamps_file": "youtube_timestamps_owney_the_dog_1_140.txt",
    "subtitles_file": "subtitles_owney_the_dog_1_140.srt",
    "payload_file": "youtube_upload_payload_owney_the_dog_1_140.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "OWNEY THE DOG: THE IMMORTAL RAILWAY MASCOT! [Complete Book 1-140] | Full Historical Audiobook",
    "tags": [
        "Owney The Dog", "Owney", "Railway Mail Service", "Historical Audiobook",
        "Smithsonian Postal Museum", "American History", "True Dog Stories",
        "Steam Train Era", "Audiobook Full", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to the complete, unabridged historical saga of 'Owney the Dog', covering Pages 1 through 140[cite: 160]!\n\n"
        "Experience the authentic, heartwarming chronicle of America's most celebrated canine traveler[cite: 160]. From a shivering stray seeking refuge "
        "on a pile of canvas mail sacks in the Albany Post Office in 1888[cite: 160, 162], to becoming the beloved good-luck charm of the United States Railway Mail Service[cite: 160, 163]. "
        "Ride along the swaying wooden Railway Post Office cars[cite: 163, 176], through mountain blizzards[cite: 172, 227], train yards, and transcontinental runs[cite: 162, 202, 206]. "
        "Witness Postmaster General John Wanamaker commissioning his custom leather harness to carry hundreds of clinking baggage tags and tokens[cite: 160, 215, 220], "
        "his record-breaking 129-day circumnavigation of the globe aboard the S.S. Victoria[cite: 160, 240, 270], the tragic misunderstanding in Toledo[cite: 160, 280], "
        "and his eternal enshrinement at the Smithsonian National Postal Museum[cite: 160, 292].\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and historical dramatization).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized historical audiobook is produced for educational, cultural commentary, "
        "and literary appreciation based on the life and historical records of Owney the Postal Dog[cite: 160, 164]. Subscribe for more classic sagas and true historical legends!\n\n"
        "#OwneyTheDog #RailwayMail #AmericanHistory #TrueStory #Smithsonian #Audiobook #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks covering the full 140 pages)
    "blocks": [
        {
            "index": 1, "range": (1, 35),
            "title": ["THE SCENT OF CANVAS", "CAR 42 ON THE HUDSON LINE"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D historical illustration inside a gas-lit 1880s United States Railway Post Office wooden train car[cite: 162, 163, 176], "
                "a scruffy wire-haired terrier sitting proudly atop piles of heavy canvas mail sacks beside pigeonhole sorting cases[cite: 160, 162, 163], "
                "warm amber glow from swinging brass kerosene lanterns, mail clerks in suspenders sorting letters in motion[cite: 176, 180], "
                "coal smoke and snow swirling outside the open doorway, highly detailed 4k digital masterpiece[cite: 176]."
            )
        },
        {
            "index": 2, "range": (36, 70),
            "title": ["TRANSCONTINENTAL RAILS", "THE WANAMAKER HARNESS"],
            "fallback_color": (30, 25, 35),
            "prompt": (
                "Cinematic 3D historical scene of Owney wearing a custom brown leather harness completely covered in hundreds of clinking brass baggage tags[cite: 160, 215, 219], "
                "standing on the observation platform of a speeding Union Pacific steam train crossing a high wooden trestle bridge[cite: 203, 207], "
                "magnificent snow-dusted Rocky Mountain peaks in the background under morning sunlight[cite: 207, 212], "
                "crisp atmospheric illumination, sharp 4k render."
            )
        },
        {
            "index": 3, "range": (71, 105),
            "title": ["ACROSS PACIFIC SWELLS", "THE GLOBAL ODYSSEY"],
            "fallback_color": (20, 30, 40),
            "prompt": (
                "Cinematic 3D maritime adventure scene on the teakwood bridge of the steamship SS Victoria sailing across Pacific waters[cite: 240, 247, 252], "
                "the terrier Owney standing by the rail wearing his medal-covered vest alongside the sea captain[cite: 240, 247, 252], "
                "Mount Fuji rising majestic in the distance across Yokohama Harbor at sunrise[cite: 255, 260], "
                "sea spray catching golden sunlight, rich historical detail, 4k digital art."
            )
        },
        {
            "index": 4, "range": (106, 140),
            "title": ["THE CLERKS' ETERNAL VOW", "THE SMITHSONIAN SHRINE"],
            "fallback_color": (40, 30, 15),
            "prompt": (
                "Cinematic 3D dignified museum interior of the Smithsonian National Postal Museum atrium[cite: 160, 292, 296], "
                "an illuminated mahogany and glass exhibition case displaying the preserved terrier Owney with his historic medal vest[cite: 280, 292], "
                "soft sunlight streaming through tall neoclassical arched windows onto vintage mail cars and brass train bells[cite: 271, 296], "
                "poignant and reverent atmosphere, 4k digital masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))