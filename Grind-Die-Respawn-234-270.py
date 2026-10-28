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


BUILD_DIR = "build_beast_grind_die_respawn_234_270"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "beast-taming-my-beasts-grind-die-and-respawn",
    "start_url": "https://freewebnovel.com/novel/beast-taming-my-beasts-grind-die-and-respawn/chapter-234",
    "start_chapter": 234,
    "end_chapter": 270,
    "default_topic": "Beast Taming: My Beasts Grind, Die, and Respawn / LitRPG / Infinite Respawn / Fantasy / Overpowered Tamer",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook
    "intro_hook": "Armed with a limitless resurrection talent, one unconventional beast tamer forces his contracted beasts into lethal grind loops, dying and respawning until they achieve supreme divinity.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_beast_grind_die_respawn_234_270.mp3",
    "final_video": "final_beast_grind_die_respawn_234_270.mp4",
    "cover_image": "cover_beast_grind_die_respawn_234_270.jpg",
    "timestamps_file": "youtube_timestamps_beast_grind_die_respawn_234_270.txt",
    "subtitles_file": "subtitles_beast_grind_die_respawn_234_270.srt",
    "payload_file": "youtube_upload_payload_beast_grind_die_respawn_234_270.json",

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
    "video_title": "Beast Taming: My Beasts Grind, Die, and Respawn | Ch 234 - 270 Audiobook Marathon | Endless Trial",
    "privacy_status": "unlisted",
    "tags": [
        "Beast Taming", "My Beasts Grind Die and Respawn", "Beast Tamer Audiobook",
        "LitRPG Audiobook", "Fantasy Audiobook", "Infinite Respawn", "Overpowered MC",
        "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "This episode, we step right back into the story, continuing exactly where we left off in our previous episode of this series.\n\n"
        "Experience 'Beast Taming: My Beasts Grind, Die, and Respawn' (Chapters 234 to 270) — The Trial of Endless Rebirth.\n\n"
        "Through ruthless high-tier trial zones and deadly spatial cracks, our tamer pushes his beasts past mortality itself. "
        "Every fatal blow is met with instant resurrection, converting sheer death into unstoppable stat growth and breakthrough evolutions.\n\n"
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
        "#BeastTaming #GrindDieRespawn #LitRPG #FantasyAudiobook #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks for Chapters 234 to 270
    "blocks": [
        {
            "index": 1, "range": (234, 242),
            "title": ["CRIMSON TRIAL", "DEATH LOOP GRIND"],
            "fallback_color": (25, 12, 16),
            "prompt": (
                "Cinematic shattered wasteland beneath a blood-red sky, a fierce beast tamer surrounded by glowing soul rifts, "
                "majestic mythical battle beasts covered in glowing runic scars rising from ashes of golden flame, dynamic lighting, 4K masterpiece."
            )
        },
        {
            "index": 2, "range": (243, 251),
            "title": ["SPATIAL CRACK", "APEX CARNAGE"],
            "fallback_color": (16, 20, 28),
            "prompt": (
                "Cinematic dimensional rift tearing through dark mountain cliffs, cosmic purple lightning crackling around a colossal armored wolf beast, "
                "ferocious apex monsters emerging from dimensional rifts, epic dark fantasy, 4K digital art."
            )
        },
        {
            "index": 3, "range": (252, 260),
            "title": ["DIVINE RESURRECTION", "LIMIT BREAKER"],
            "fallback_color": (24, 18, 10),
            "prompt": (
                "Ancient runic stone arena glowing with celestial summoning circles, a powerful tamer radiating golden aura, "
                "transcendent winged sovereign beast undergoing full divine rebirth in bursts of sacred white flames, 4K."
            )
        },
        {
            "index": 4, "range": (261, 270),
            "title": ["DOMINION ASCENSION", "IMMORTAL PACK"],
            "fallback_color": (18, 14, 26),
            "prompt": (
                "High-angle view of a desolate volcanic peak conquered under moonlight, a calm beastmaster standing with a pack of evolved divine beasts, "
                "glowing status windows reflecting in his eyes, atmospheric volumetric fog, hyper-detailed fantasy render."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))