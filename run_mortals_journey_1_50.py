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


BUILD_DIR = "build_mortals_journey_1_50"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "a-record-of-a-mortals-journey-to-immortality-novel",
    "start_url": "https://freewebnovel.com/novel/a-record-of-a-mortals-journey-to-immortality-novel/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "A Record of a Mortal's Journey to Immortality / Classical Xianxia / Cultivation / Daoism / Han Li / Alchemy",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook
    "intro_hook": "Born an ordinary village boy with mediocre talent, one young disciple navigates deadly sect betrayals and discovers a mysterious green bottle that alters the path of cultivation forever.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_mortals_journey_1_50.mp3",
    "final_video": "final_mortals_journey_1_50.mp4",
    "cover_image": "cover_mortals_journey_1_50.jpg",
    "timestamps_file": "youtube_timestamps_mortals_journey_1_50.txt",
    "subtitles_file": "subtitles_mortals_journey_1_50.srt",
    "payload_file": "youtube_upload_payload_mortals_journey_1_50.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # Post-Render Multilingual Subtitle Engine (15 Languages to build/subtitles/)
    "enable_subtitles": True,
    "subtitle_languages": [
        "de", "es", "pt", "ru", "hi", "bn", "ms", "tl", "fr", "fi", "ja", "pl", "ur", "ar", "vi"
    ],

    # YouTube Metadata
    "video_title": "A Record of a Mortal's Journey to Immortality | Ch 1 - 50 Full Audio Novel Marathon | Seven Mysteries Sect",
    "privacy_status": "unlisted",
    "tags": [
        "Mortals Journey to Immortality", "RMJI", "Han Li", "Xianxia Audiobook",
        "Cultivation Audiobook", "Seven Mysteries Sect", "Doctor Mo", "Audiobook Marathon",
        "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the complete opening saga of 'A Record of a Mortal's Journey to Immortality' (Chapters 1 to 50) — The God Hand Valley Arc.\n\n"
        "Han Li, an ordinary poor boy from an unremarkable village, enters the Seven Mysteries Sect with zero cultivation roots. "
        "Apprenticed to the enigmatic Doctor Mo, he uncovers the brutal reality of the martial and immortal worlds while harboring a "
        "world-shaking secret: a palm-sized heavenly vial that condenses celestial dew.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "🎙️ NARRATION: en-US-ChristopherNeural (Deep Cinematic Baritone).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited, dramatized fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#MortalsJourney #HanLi #RMJI #Xianxia #CultivationAudiobook #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Arc Visual Blocks for Chapters 1 to 50
    "blocks": [
        {
            "index": 1, "range": (1, 12),
            "title": ["SECT ENTRANCE", "GOD HAND VALLEY"],
            "fallback_color": (15, 25, 20),
            "prompt": (
                "Ancient Chinese mountain monastery perched on steep mist-shrouded limestone cliffs, "
                "winding stone steps climbing into misty pine forests, traditional pavilions with tiled roofs, "
                "serene early morning light, ink-wash painting aesthetic meets photorealism, 4K masterpiece."
            )
        },
        {
            "index": 2, "range": (13, 25),
            "title": ["CELESTIAL VIAL", "HERBAL ALCHEMY"],
            "fallback_color": (20, 25, 15),
            "prompt": (
                "Secluded wooden apothecary cottage in a hidden mountain valley under night moonlight, "
                "a young commoner disciple in coarse grey robes carefully holding an ornate palm-sized green glass bottle that absorbs celestial starlight, "
                "rare ancient medicinal herbs glowing softly in ceramic pots, 4K."
            )
        },
        {
            "index": 3, "range": (26, 38),
            "title": ["ETERNAL SPRING ART", "UNDERGROUND TENSION"],
            "fallback_color": (25, 20, 15),
            "prompt": (
                "Dimly lit stone alchemy chamber illuminated by glowing medicinal furnace embers and hanging dried roots, "
                "an elderly crippled physician with sharp suspicious eyes observing a calm young apprentice in shadow, "
                "tense psychological atmosphere, cinematic chiaroscuro lighting, 4K."
            )
        },
        {
            "index": 4, "range": (39, 50),
            "title": ["VALLEY SHOWDOWN", "STEP TOWARD THE DAO"],
            "fallback_color": (20, 15, 25),
            "prompt": (
                "Dramatic confrontation inside a misty bamboo grove at dusk, a young cultivator wielding a curved hidden dagger, "
                "dark spiritual talismans burning with eerie golden light, wind blowing bamboo leaves across misty stone ground, hyper-detailed 4K."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
