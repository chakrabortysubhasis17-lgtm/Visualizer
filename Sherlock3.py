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

BUILD_DIR = "build_sherlock_holmes_422_587"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters (Local PDF Page Extraction)
    "source_type": "pdf",
    "pdf_path": r"D:\Projects\visualer\ebooks\SherlockHolmesComplete.pdf",
    "start_url": r"D:\Projects\visualer\ebooks\SherlockHolmesComplete.pdf",
    "novel_slug": "the-return-of-sherlock-holmes",
    "start_chapter": 422,
    "end_chapter": 587,
    "default_topic": "The Return of Sherlock Holmes",

    # Concurrency Settings & Hardcoded Narrator Lock
    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Mir-Style Dynamic Intro Sequence Passed in intro_hook
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "From the shadowy alleys of Victorian London to secluded country estates, "
                "the game is once again afoot. Having returned from his supposed death at the Reichenbach Fall, "
                "Sherlock Holmes and Doctor John Watson plunge into a gauntlet of sinister conspiracies—from "
                "the cryptic cipher of the Dancing Men and the grim tragedy of Black Peter, to the ruthless "
                "blackmail of Charles Augustus Milverton and the fractured busts of Napoleon."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "bells",
            "bgm_mood": "tension"
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
            "bgm_mood": "tension"
        },
        {
            "line_id": "intro_02_body",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "Welcome back to Being a Bong. We narrate the unreal worlds to life. "
                "We are thrilled to bring you the premiere episode of this massive Sherlock Holmes case collection, "
                "covering pages four hundred and twenty-two through five hundred and eighty-seven. "
                "Take a second to hit that like button, subscribe if you are new to the channel, and drop your thoughts in the comments. "
                "Your support is the engine that keeps this massive releases alive. "
                "Step into Baker Street as the fog settles, adjust your volume, and let's begin today's episode."
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
    "final_audio": "output_sherlock_holmes_422_587.mp3",
    "final_video": "final_sherlock_holmes_422_587.mp4",
    "cover_image": "cover_sherlock_holmes_422_587.jpg",
    "timestamps_file": "youtube_timestamps_sherlock_holmes_422_587.txt",
    "subtitles_file": "subtitles_sherlock_holmes_422_587.srt",
    "payload_file": "youtube_upload_payload_sherlock_holmes_422_587.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "THE RETURN OF SHERLOCK HOLMES! [Pages 422-587] | Classic Detective Mystery Full Audiobook",
    "tags": [
        "Sherlock Holmes", "The Return of Sherlock Holmes", "Arthur Conan Doyle", "Classic Audiobook",
        "Detective Fiction", "Dr Watson", "Baker Street", "Mystery Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to 'The Return of Sherlock Holmes' collection covering Pages 422 through 587!\n\n"
        "Follow the world's greatest consulting detective and Doctor John Watson across London and the English shires "
        "as they investigate baffling cases: The Adventure of the Norwood Builder, The Dancing Men, The Solitary Cyclist, "
        "The Priory School, Black Peter, Charles Augustus Milverton, The Six Napoleons, The Golden Pince-Nez, The Abbey Grange, "
        "and The Second Stain. Experience this 166-page classic mystery marathon with multi-voice neural TTS, context-aware acoustic "
        "soundscapes, and full synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, period prose, and deduction notes).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation of Sir Arthur Conan Doyle's public domain work is produced for "
        "educational, literary commentary, and entertainment purposes. Subscribe for more classic detective mysteries and literature sagas!\n\n"
        "#SherlockHolmes #ArthurConanDoyle #TheReturnOfSherlockHolmes #ClassicAudiobook #DetectiveMystery #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks covering Pages 422 to 587: 422-463, 464-505, 506-546, 547-587)
    "blocks": [
        {
            "index": 1, "range": (422, 463),
            "title": ["THE NORWOOD BUILDER & DANCING MEN", "CIPHER IN CHALK"],
            "fallback_color": (25, 20, 25),
            "prompt": (
                "Cinematic 3D Victorian detective illustration of Sherlock Holmes examining chalk-drawn dancing figures on a wooden sundial "
                "in a desolate country garden at dusk, Doctor Watson holding a notebook beside him. "
                "Dense twilight fog, Victorian brick manor in the background, dramatic gaslamp illumination, 4k digital art."
            )
        },
        {
            "index": 2, "range": (464, 505),
            "title": ["BLACK PETER & MILVERTON", "MIDNIGHT EXPEDITION"],
            "fallback_color": (20, 25, 30),
            "prompt": (
                "Cinematic 3D mystery scene inside a dark wood-paneled country study, Holmes shining a bull's-eye lantern onto a heavy iron safe, "
                "masked and stealthy, while rain lashes against tall leaded windows. "
                "Shadows cast across antique leather furniture, glinting brass instruments, tense atmospheric lighting, 4k render."
            )
        },
        {
            "index": 3, "range": (506, 546),
            "title": ["THE SIX NAPOLEONS", "THE BUST OF PEARLS"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D interior view of 221B Baker Street by firelight, Holmes kneeling by a shattered plaster bust of Napoleon on the rug, "
                "retrieving a radiant black pearl from the broken core with delicate forceps. "
                "Surrounding tables littered with violins, chemical bottles, and London gazettes, chiaroscuro lighting, sharp textures."
            )
        },
        {
            "index": 4, "range": (547, 587),
            "title": ["THE SECOND STAIN & ABBEY GRANGE", "STATE SECRETS"],
            "fallback_color": (15, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of Sherlock Holmes and Doctor Watson standing before a high stone hearth in an aristocratic Whitehall salon, "
                "confronting a distressed noble lady dressed in mourning silks beneath heavy velvet drapes. "
                "Golden chandelier glow, morning mist through tall windows, commanding intellectual presence, masterpiece 4k render."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
