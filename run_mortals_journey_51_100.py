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


BUILD_DIR = "build_rmji_51_100"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "a-record-of-a-mortals-journey-to-immortality",
    "start_url": "https://freewebnovel.com/novel/a-record-of-a-mortals-journey-to-immortality-novel/chapter-51",
    "start_chapter": 51,
    "end_chapter": 100,
    "is_start": False,  # Continuation volume
    "default_topic": "A Record of a Mortal's Journey to Immortality / Xianxia / Cultivation / Han Li / Seven Mysteries Sect / Doctor Mo / Spiritual Medicine",

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook
    "intro_hook": "Navigating deadly mortal martial factions and the dark scheming of Doctor Mo, Han Li relies on cold calculation and his mysterious green vial to step onto the true path of immortal cultivation.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_rmji_51_100.mp3",
    "final_video": "final_rmji_51_100.mp4",
    "cover_image": "cover_rmji_51_100.jpg",
    "timestamps_file": "youtube_timestamps_rmji_51_100.txt",
    "subtitles_file": "subtitles_rmji_51_100.srt",
    "payload_file": "youtube_upload_payload_rmji_51_100.json",

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
    "video_title": "A Record of a Mortal's Journey to Immortality | Ch 51 - 100 Full Xianxia Audiobook Marathon",
    "privacy_status": "unlisted",
    "tags": [
        "A Record of a Mortals Journey to Immortality", "RMJI", "Han Li", "Xianxia Audiobook",
        "Cultivation Audiobook", "Chinese Web Novel", "Seven Mysteries Sect", "Doctor Mo",
        "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "This episode, we step right back into the story, continuing exactly where we left off in our previous episode of this series.\n\n"
        "Experience 'A Record of a Mortal's Journey to Immortality' (Chapters 51 to 100) — The Seven Mysteries Crisis & Hidden Plots.\n\n"
        "As conflicts between the Seven Mysteries Sect and the Feral Wolf Gang erupt into open bloodshed, Han Li uncovers "
        "the sinister true purpose behind Doctor Mo's guidance. Armed with spiritual herbs ripened by the heaven-defying mysterious vial "
        "and guarded by calculating pragmatism, Han Li faces mortal martial masters while taking his decisive first steps into the realm of true cultivation.\n\n"
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
        "#RMJI #HanLi #Xianxia #CultivationAudiobook #MortalsJourneyToImmortality #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks across Chapters 51 to 100 (50 chapters partitioned)
    "blocks": [
        {
            "index": 1, "range": (51, 63),
            "title": ["THE HERBAL CHAMBER", "DOCTOR MO'S AMBITION"],
            "fallback_color": (18, 22, 18),
            "prompt": (
                "Cinematic high-contrast ancient Chinese herbal apothecary study lit by warm oil lanterns, "
                "rows of wooden drying racks filled with rare ginseng roots and dark clay medicine jars, "
                "a cautious young disciple grinding jade medicine pills while observing a gaunt enigmatic elder, volumetric shadows, 4K digital painting."
            )
        },
        {
            "index": 2, "range": (64, 75),
            "title": ["THE MYSTERIOUS VIAL", "SPIRIT DEW REFINEMENT"],
            "fallback_color": (12, 24, 20),
            "prompt": (
                "Secluded rocky mountain cave courtyard bathed in pale midnight moonlight, "
                "a tiny ornate dark-green jade bottle gathering glowing emerald spiritual condensation droplets from the starry sky, "
                "translucent glowing mist coiling around ancient herbal stalks, mystical xianxia concept art, 4K."
            )
        },
        {
            "index": 3, "range": (76, 88),
            "title": ["SEVEN MYSTERIES TURMOIL", "BLOODSHED AT THE SUNSET SUMMIT"],
            "fallback_color": (26, 14, 16),
            "prompt": (
                "Dramatic wuxia combat arena atop misty mountain wooden pavilion cliffs at dusk, "
                "ruthless martial artists in black and crimson robes clashing with flying curved sabers and throwing daggers, "
                "splintered wooden palisades, dynamic wind blowing fallen autumn leaves, cinematic lighting, 4K resolution."
            )
        },
        {
            "index": 4, "range": (89, 100),
            "title": ["CROSSING THE THRESHOLD", "THE CULTIVATOR'S EYE"],
            "fallback_color": (16, 18, 26),
            "prompt": (
                "Panoramic mountain precipice overlooking an endless sea of rolling cloud valleys at sunrise, "
                "a solitary calm young cultivator in simple green daoist robes standing with his hands behind his back, "
                "faint golden spiritual light radiating subtly around his silhouette, epic serene composition, 4K masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))