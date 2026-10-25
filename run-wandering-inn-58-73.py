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


BUILD_DIR = "build_the_wandering_inn_58_73"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "the-wandering-inn",
    "start_url": "https://freewebnovel.com/novel/the-wandering-inn/chapter-62",
    "start_chapter": 58,
    "end_chapter": 73,
    "default_topic": "The Wandering Inn / LitRPG / High Fantasy / Slice of Life / Innkeeper Escalation",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook (start_chapter > 1 -> continuation recap)
    "intro_hook": "We step back into the unpredictable world of the Wandering Inn, where dangerous politics, monstrous incursions, and heartwarming tavern camaraderie test Erin's resolve.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_the_wandering_inn_58_73.mp3",
    "final_video": "final_the_wandering_inn_58_73.mp4",
    "cover_image": "cover_the_wandering_inn_58_73.jpg",
    "timestamps_file": "youtube_timestamps_the_wandering_inn_58_73.txt",
    "subtitles_file": "subtitles_the_wandering_inn_58_73.srt",
    "payload_file": "youtube_upload_payload_the_wandering_inn_58_73.json",

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
    "video_title": "The Wandering Inn | Ch 58 - 73 Full Audio Novel Marathon | Tavern Defense Arc",
    "privacy_status": "unlisted",
    "tags": [
        "The Wandering Inn", "The Wandering Inn Audiobook", "LitRPG Audiobook",
        "High Fantasy", "Portal Fantasy", "Innkeeper LitRPG", "Slice of Life Fantasy",
        "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the complete audio novel marathon of 'The Wandering Inn' (Chapters 58 to 73) — the Tavern Defense Arc.\n\n"
        "Catch up on earlier arcs:\n"
        "• Episode 1 (Ch 1-41): Check channel playlist\n"
        "• Previous Episode (Ch 42-57): https://www.youtube.com/watch?v=wanderinginn_ch42_57\n"
        "• Full Series Playlist: https://www.youtube.com/playlist?list=PLQPdvMoYb7vA\n\n"
        "As threats mount around Liscor, Erin and her patrons face escalating trials that push the cozy inn to its absolute limits. "
        "Packed with deep character growth, high stakes, and unforgettable fantasy moments.\n\n"
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
        "#TheWanderingInn #LitRPG #HighFantasy #PortalFantasy #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Arc Visual Blocks for Chapters 58 to 73
    "blocks": [
        {
            "index": 1, "range": (58, 62),
            "title": ["GATHERING STORM", "TAVERN PREPARATIONS"],
            "fallback_color": (20, 20, 25),
            "prompt": (
                "Cinematic high-tension fantasy tavern interior at dusk, glowing magical lanterns, weary adventurers sharpening weapons by the hearth, "
                "the innkeeper organizing supplies with determined focus, dramatic shadows, 4K resolution."
            )
        },
        {
            "index": 2, "range": (63, 67),
            "title": ["MONSTER SIEGE", "WALLS OF LISCOR"],
            "fallback_color": (30, 15, 15),
            "prompt": (
                "Cinematic epic night siege outside massive stone city ramparts, soldiers and tactical defense units fighting off aggressive hordes of monsters, "
                "flaming arrows lighting up the dark sky, dynamic action composition."
            )
        },
        {
            "index": 3, "range": (68, 70),
            "title": ["INNKEEPER'S STAND", "TACTICAL MANEUVERS"],
            "fallback_color": (25, 20, 30),
            "prompt": (
                "Cinematic dramatic interior shot of the Wandering Inn fortified with heavy barricades, magical aura shielding the doorway, "
                "defenders standing firm ready for battle, cinematic rim lighting."
            )
        },
        {
            "index": 4, "range": (71, 73),
            "title": ["AFTERMATH", "DAWN OF RESOLVE"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic peaceful sunrise breaking over a misty fantasy landscape, the battered yet standing inn illuminated by golden morning light, "
                "smoke rising gently from the chimney, inspiring and hopeful atmosphere, masterpiece 4K render."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))