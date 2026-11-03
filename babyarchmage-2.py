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

BUILD_DIR = "build_baby_archmage_21_34"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "baby-archmage",
    "start_url": "https://www.royalroad.com/fiction/198845/baby-archmage-opmc-litrpg-reincarnator-no-ai-writing/chapter/4250777/chapter-21-bonus-chapper",
    "start_chapter": 21,
    "end_chapter": 34,
    "default_topic": "Baby Archmage",

    # Concurrency Settings & Narrator Lock
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook
    "intro_hook": "We return to our reincarnated archmage as he continues navigating childhood while stealthily mastering arcane fundamentals, shocking his family, and expanding his overpowered status sheet.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_baby_archmage_21_34.mp3",
    "final_video": "final_baby_archmage_21_34.mp4",
    "cover_image": "cover_baby_archmage_21_34.jpg",
    "timestamps_file": "youtube_timestamps_baby_archmage_21_34.txt",
    "subtitles_file": "subtitles_baby_archmage_21_34.srt",
    "payload_file": "youtube_upload_payload_baby_archmage_21_34.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "INFANT PRODIGY & SECRET SPELLCRAFT! [Ch 21-34] | Baby Archmage OP Reincarnation LitRPG Audiobook",
    "tags": [
        "Baby Archmage", "LitRPG Audiobook", "Progression Fantasy", "Reincarnation Audiobook",
        "Overpowered MC", "OP MC", "Magic Academy", "Isekai Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Baby Archmage' with Chapters 21 through 34!\n\n"
        "Even trapped in an infant's body, a legendary archmage's mind cannot be contained. Watch as he discreetly "
        "reconstructs high-tier spell arrays, maneuvers through aristocratic family dynamics, and pushes his mana core "
        "to unprecedented limits while everyone around him thinks he's just playing.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more chapters and progression updates!\n\n"
        "#BabyArchmage #LitRPG #ProgressionFantasy #Reincarnation #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks covering Ch 21 to 34: 21-24, 25-27, 28-30, 31-34)
    "blocks": [
        {
            "index": 1, "range": (21, 24),
            "title": ["SECRET ARCANUM", "TODDLER MANA FORGING"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D fantasy illustration of an adorable toddler boy sitting on a lavish royal nursery rug, "
                "eyes glowing with intense azure magical power, floating intricate miniature geometric spell circles between his tiny hands. "
                "Cozy sunlit aristocratic manor room background, soft golden rays, toys scattered on floor, medium close-up, sharp 4k render."
            )
        },
        {
            "index": 2, "range": (25, 27),
            "title": ["PRODIGIOUS INTELLECT", "FAMILY PERPLEXITY"],
            "fallback_color": (20, 30, 40),
            "prompt": (
                "Cinematic 3D fantasy scene of a young infant sitting at a large mahogany library desk holding a giant leatherbound grimoire, "
                "a bewildered noble father and gentle mother watching in shock from the doorway. "
                "Warm fireplace glow, towering bookshelves, magical particles drifting through the air, highly detailed faces, 4k cinematic lighting."
            )
        },
        {
            "index": 3, "range": (28, 30),
            "title": ["MANA CORE SURGE", "UNPRECEDENTED DENSITY"],
            "fallback_color": (40, 20, 30),
            "prompt": (
                "Cinematic 3D fantasy portrait of a small gifted boy meditating cross-legged atop a stone balcony, "
                "swirling ethereal violet and golden mana streams condensing into a radiant core inside his chest. "
                "Dusk sky over a sprawling fantasy castle estate background, gentle wind rustling his hair, magical runes, 4k digital art style."
            )
        },
        {
            "index": 4, "range": (31, 34),
            "title": ["ARCANE DISCOVERY", "UNSTOPPABLE TRAJECTORY"],
            "fallback_color": (25, 35, 25),
            "prompt": (
                "Cinematic 3D fantasy illustration of the young protagonist pointing a tiny finger forward, "
                "effortlessly deflecting a magical training barrier with a brilliant crystalline shield array. "
                "Outdoor estate training arena, surprised knight instructors in background, sparkling sparks, dramatic hero lighting, crisp 3D render."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
