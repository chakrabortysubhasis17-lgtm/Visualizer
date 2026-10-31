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


def purge_corrupt_or_fallback_cache(build_dir: str):
    """
    Purges placeholder files, corrupt manifests, and rule-based fallback files
    staged during earlier runs without Gemini credentials.
    """
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

                is_dummy = len(rows) < 8 or any("Exposition details continue" in r.get("text", "") for r in rows)
                is_fallback_only = not any(r.get("speaker") not in ["Narrator", "Mc", "System"] for r in rows)

                if is_dummy or is_fallback_only:
                    os.remove(fpath)
                    removed += 1
            except Exception:
                try:
                    os.remove(fpath)
                    removed += 1
                except OSError:
                    pass
    if removed > 0:
        print(f"[Pre-Flight Cleanup] [OK] Purged {removed} invalid/fallback staged files. Gemini Director will parse cleanly.", flush=True)


BUILD_DIR = "build_baby_archmage_1_20"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters (Series Opening Volume)
    "novel_slug": "baby-archmage",
    "start_url": "https://www.royalroad.com/fiction/198845/baby-archmage-opmc-litrpg-reincarnator-no-ai-writing/chapter/4195883/chapter-1",
    "start_chapter": 1,
    "end_chapter": 20,
    "is_start": True,  # Series Opening Episode
    "default_topic": "Baby Archmage / LitRPG / Reincarnation / OPMC / Fantasy Magic / Arcane Prodigy / Meditation & System Perks",

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook
    "intro_hook": "Reborn into a magical world with his adult memories intact, an infant prodigy unlocks forbidden meditation disciplines to master the arcane before taking his first steps.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_baby_archmage_1_20.mp3",
    "final_video": "final_baby_archmage_1_20.mp4",
    "cover_image": "cover_baby_archmage_1_20.jpg",
    "timestamps_file": "youtube_timestamps_baby_archmage_1_20.txt",
    "subtitles_file": "subtitles_baby_archmage_1_20.srt",
    "payload_file": "youtube_upload_payload_baby_archmage_1_20.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # Post-Render Multilingual Subtitle Engine (15 Languages)
    "enable_subtitles": True,
    "subtitle_languages": [
        "de", "es", "pt", "ru", "hi", "bn", "ms", "tl", "fr", "fi", "ja", "pl", "ur", "ar", "vi"
    ],

    # YouTube Metadata
    "video_title": "Baby Archmage | Ch 1 - 20 Full LitRPG Audiobook Marathon | OPMC Reincarnation",
    "privacy_status": "unlisted",
    "tags": [
        "Baby Archmage", "Baby Archmage Audiobook", "LitRPG Audiobook", "Progression Fantasy",
        "Reincarnation Audiobook", "OPMC", "Magic Prodigy", "Audiobook Marathon",
        "Web Novel Audiobook", "Royal Road", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Welcome to the opening episode of this series. A brand-new adventure awaits, and we are glad to have you with us.\n\n"
        "Experience 'Baby Archmage' (Chapters 1 to 20) — The Awakening & Infant Prodigy Arc.\n\n"
        "Given a second chance at life through sudden reincarnation, an ordinary man awakes inside the body of a newborn baby. "
        "Blessed by tribal magic and armed with adult reasoning, he wastes no time: diving into deep meditation, he unlocks world-first "
        "system achievements, legendary perks, and nascent mana manipulation right from his wooden crib.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "🎙️ NARRATION: en-US-ChristopherNeural (Deep Cinematic Baritone).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audio presentation is an edited fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#BabyArchmage #LitRPG #ProgressionFantasy #OPMC #Reincarnation #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks across Chapters 1 to 20 (20 chapters partitioned)
    "blocks": [
        {
            "index": 1, "range": (1, 5),
            "title": ["REBORN IN A CRADLE", "AN AWAKENED MIND"],
            "fallback_color": (22, 18, 14),
            "prompt": (
                "Warm rustic fantasy cottage interior illuminated by gentle morning sunlight streaming through open wooden shutters, "
                "a newborn infant lying peacefully inside a hand-carved wooden crib surrounded by faint iridescent golden and emerald mana wisps, "
                "loving parents watching over from the bedside, cozy high fantasy atmosphere, 4K digital painting."
            )
        },
        {
            "index": 2, "range": (6, 10),
            "title": ["INNER FOCUS", "FIRST MANA CONDENSATION"],
            "fallback_color": (14, 20, 24),
            "prompt": (
                "Cinematic nighttime cottage bedroom bathed in soft pale moonlight, "
                "a tiny infant sitting upright in deep meditation with tiny glowing translucent geometric arcane circles spinning around small hands, "
                "shimmering blue and violet ethereal particles condensing into a miniature mana core, 4K concept art."
            )
        },
        {
            "index": 3, "range": (11, 15),
            "title": ["VILLAGE MYSTERIES", "PRODIGIOUS TALENT"],
            "fallback_color": (18, 22, 16),
            "prompt": (
                "Vibrant rural tribal fantasy settlement surrounded by tall lush ancient emerald woodlands and clear running streams, "
                "a wise tribal elder holding a gnarled wooden staff tipped with a glowing amber crystal observing a young child creating playful sparks of magic, "
                "cinematic depth of field, atmospheric lighting, 4K resolution."
            )
        },
        {
            "index": 4, "range": (16, 20),
            "title": ["THE SAGE PERK", "THE PATH OF THE ARCHMAGE"],
            "fallback_color": (20, 16, 26),
            "prompt": (
                "Panoramic high-fantasy landscape at dusk with a starry twilight sky, "
                "ancient stone monolithic arches inscribed with glowing blue runes standing atop a grassy hill overlooking a vast enchanted realm, "
                "swirling ethereal constellations framing the horizon, epic fantasy masterpiece, 4K."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
