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
                if len(rows) < 8 or any("Exposition details continue" in (r.get("display_text") or r.get("tts_text") or r.get("text", "")) for r in rows):
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

BUILD_DIR = "build_catgirls_and_dungeons_201_203_test"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters
    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/catgirls-and-dungeons-yuri/chapter-201",
    "novel_slug": "catgirls-and-dungeons-yuri",
    "start_chapter": 201,
    "end_chapter": 203,
    "default_topic": "Catgirls and Dungeons",

    # Concurrency Settings & Hardcoded Narrator Lock
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Locked 5-Beat Intro Hook Sequence (8-Element Architecture)
    "intro_hook": [
        # Beat 1: High-Stakes Teaser (0:00 - 0:12)
        {
            "line_id": "intro_01_teaser",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "Five candy-colored catgirl maids bow in terrifyingly perfect synchronization! Sustained purely by artificial mana cores and packing the combat reflexes of C-rank adventurers, this is no ordinary welcome party!",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "heartwarm",
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
            "bgm_mood": "no_mood"
        },

        # Beat 2: Trademark Channel Signature (0:12 - 0:17)
        {
            "line_id": "intro_02_trademark",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "Welcome back to Being a Bong. We narrate the unreal worlds to life.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "whoosh",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_pause_02",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "",
            "pause_duration": 0.3,
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "",
            "bgm_mood": "no_mood"
        },

        # Beat 3: In-Universe Lore-Bound CTA (0:17 - 0:27)
        {
            "line_id": "intro_03_cta",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "Sanctuary Mana Directive: To fuel the artificial core matrix and unseal today's double release, strike the Like button and subscribe to the channel. Registering your party bond ensures zero maintenance failure.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "chime",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_pause_03",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "",
            "pause_duration": 0.3,
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "",
            "bgm_mood": "no_mood"
        },

        # Beat 4: Recap Bridge (0:27 - 0:40)
        {
            "line_id": "intro_04_bridge",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "Previously, Felicia and Eris finalized their claim over the warded gothic estate of Noctis Sanctum. Now, unlocking an alchemical surprise prepared by the guildmaster, their new domestic life descends into delightful chaos. Let us enter.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "",
            "bgm_mood": "warmth"
        },

        # Beat 5: Post-Intro Scene SFX & Transition Silence (0:40 - 0:42)
        {
            "line_id": "intro_05_scene_sfx",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "",
            "pause_duration": 0.2,
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "footsteps",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_06_lead_in_silence",
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
    "final_audio": "output_catgirls_and_dungeons_201_203_test.mp3",
    "final_video": "final_catgirls_and_dungeons_201_203_test.mp4",
    "cover_image": "cover_catgirls_and_dungeons_201_203_test.jpg",
    "timestamps_file": "youtube_timestamps_catgirls_and_dungeons_201_203_test.txt",
    "subtitles_file": "subtitles_catgirls_and_dungeons_201_203_test.srt",
    "payload_file": "youtube_upload_payload_catgirls_and_dungeons_201_203_test.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "TEST RUN: SURPRISE PRESENT & HOMUNCULUS LAB! [Ch 201-203] | Catgirls and Dungeons Yuri LitRPG",
    "tags": [
        "Catgirls and Dungeons", "Yuri Audiobook", "Progression Fantasy", "Dungeon Crawler",
        "LitRPG Audiobook", "System Audiobook", "Audiobook Test", "Being A Bong"
    ],
    "desc_header": (
        "Testing the integrated pipeline upgrades with Chapters 201 to 203 of 'Catgirls and Dungeons (Yuri)'!\n\n"
        "From the grand gates of Noctis Sanctum to uncovering five identical alchemical homunculi maids "
        "and navigating domestic training, this short 3-chapter test verifies multi-voice TTS, subtitle alignment, "
        "and video rendering.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system notifications).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#CatgirlsAndDungeons #YuriAudiobook #LitRPG #ProgressionFantasy #AudiobookTest #BeingABong"
    ),

    # Visual Prompts (Single block covering all 3 chapters for this test run)
    "blocks": [
        {
            "index": 1,
            "range": (201, 203),
            "title": ["NOCTIS SANCTUM", "THE HOMUNCULI ARRIVAL"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D fantasy illustration of a female catgirl adventurer and her companion discovering a grand gothic estate hall, "
                "five identical catgirl maids in frilly black-and-white uniforms bowing in synchronized formation before them, "
                "soft golden chandelier light, gothic stone architecture with crimson flower petals drifting through open arches, "
                "octane render, unreal engine 5 style, crisp skin textures, volumetric fog, rim lighting, medium shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
