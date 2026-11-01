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


BUILD_DIR = "build_entry_cultivation_501_550"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters (Chapters 501 - 550 Marathon)
    "novel_slug": "entry-cultivation",
    "start_url": "https://mtl-novel.com/novel/entry-cultivation-i-can-copy-entries/chapter-501-crimson-leaf-still-hears-thirty-five-sounds-one-leaf-preserves-truth-condenses-the-dao-seed/",
    "start_chapter": 501,
    "end_chapter": 550,
    "is_start": False,
    "default_topic": (
        "Entry Cultivation: I Can Copy Entries / Xianxia Cultivation / "
        "Crimson Leaf Dao Seed / Immortal Realm Heavenly Laws / Runic Copying / "
        "Sword Dao Transmutation / Sect Elder Confrontation"
    ),

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook
    "intro_hook": "Condensing the true Dao Seed from thirty-five mystic resonance sounds, our cultivator shatters celestial thresholds and begins copying high-immortal heavenly entries.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_entry_cultivation_501_550.mp3",
    "final_video": "final_entry_cultivation_501_550.mp4",
    "cover_image": "cover_entry_cultivation_501_550.jpg",
    "timestamps_file": "youtube_timestamps_entry_cultivation_501_550.txt",
    "subtitles_file": "subtitles_entry_cultivation_501_550.srt",
    "payload_file": "youtube_upload_payload_entry_cultivation_501_550.json",

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
    "video_title": "Entry Cultivation: I Can Copy Entries | Ch 501 - 550 Full Audiobook Marathon",
    "privacy_status": "unlisted",
    "tags": [
        "Entry Cultivation", "I Can Copy Entries", "Entry Cultivation Audiobook",
        "Xianxia Audiobook", "Progression Fantasy", "Cultivation Audiobook",
        "Copy Entries", "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "We plunge into Chapters 501 to 550 of 'Entry Cultivation: I Can Copy Entries'.\n\n"
        "Witnessing the manifestation of the Crimson Leaf and listening to the thirty-five sounds of Dao resonance, "
        "our protagonist condenses his foundational Dao Seed. Boundless immortal secrets unlock as ancient sects clash, "
        "divine abilities evolve, and god-tier entries are copied into his immortal sovereign slate.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "🎙️ NARRATION: en-US-ChristopherNeural (Deep Cinematic Baritone).\n"
        "🎼 SOUNDSCAPE: Low-Volume Dynamic BGM Beds (-27 dB) + Targeted Context SFX.\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audio presentation is an edited fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#EntryCultivation #ICanCopyEntries #Xianxia #ProgressionFantasy #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks partitioned across Chapters 501 to 550
    "blocks": [
        {
            "index": 1, "range": (501, 512),
            "title": ["CRIMSON LEAF RESONANCE", "DAO SEED CONDENSATION"],
            "fallback_color": (32, 12, 14),
            "prompt": (
                "A serene Chinese cultivation immortal meditating in lotus position suspended high in the air above a sacred jade peak, "
                "surrounded by floating glowing golden Sanskrit and runic Dao scriptures, a luminous crimson spirit leaf drifting above his palm "
                "radiating celestial golden rings and misty spiritual qi, ethereal fantasy concept art, hyper-detailed 4K digital painting."
            )
        },
        {
            "index": 2, "range": (513, 525),
            "title": ["HEAVENLY LAW ENTRIES", "IMMORTAL CLASH"],
            "fallback_color": (14, 20, 36),
            "prompt": (
                "Colossal immortal cultivation battlefield across floating mountain peaks, two powerful Daoist sword immortals clashing midair "
                "unleashing colossal azure sword qi shockwaves and golden cosmic talismans that shatter mountain spires, "
                "dramatic volumetric clouds, heavenly lightning, majestic Xianxia masterpiece, 4K resolution."
            )
        },
        {
            "index": 3, "range": (526, 538),
            "title": ["DIVINE SECT SANCTUARY", "ANCIENT SCRIPT REPLICATOR"],
            "fallback_color": (18, 28, 22),
            "prompt": (
                "Vast grand ancient Daoist palace temple chamber overlooking an endless sea of celestial clouds at sunset, "
                "magnificent bronze pill cauldrons releasing fragrant dragon-shaped smoke, giant floating golden entry slate with intricate glowing runes, "
                "cinematic warm atmospheric lighting, Chinese Xianxia architecture, photorealistic 4K."
            )
        },
        {
            "index": 4, "range": (539, 550),
            "title": ["SOVEREIGN BREAKTHROUGH", "CELESTIAL REIGN"],
            "fallback_color": (28, 16, 32),
            "prompt": (
                "An ascended immortal grandmaster in flowing imperial robes standing atop a heavenly dragon's head coiling through thunderous purple stormclouds, "
                "commanding an infinite array of glowing flying spiritual swords pointing toward a radiant cosmic gate in the firmament, "
                "epic scale, breathtaking Xianxia fantasy art, 4K wallpaper."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
