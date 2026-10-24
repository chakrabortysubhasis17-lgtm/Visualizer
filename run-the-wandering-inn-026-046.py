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


BUILD_DIR = "build_the_wandering_inn_026_046"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "the-wandering-inn",
    "start_url": "https://freewebnovel.com/novel/the-wandering-inn/chapter-30",
    "start_chapter": 26,
    "end_chapter": 46,
    "default_topic": "The Wandering Inn / LitRPG / Liscor Floodplains / Ryoka Griffin / Erin Solstice",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook (Since start_chapter > 1, pipeline prefixes continuation intro)
    "intro_hook": "We rejoin Erin Solstice and Ryoka Griffin as the harsh realities of Izril set in, forcing an innkeeper and a bare-footed runner to navigate dangerous alliances and deadly winter beasts.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_the_wandering_inn_026_046.mp3",
    "final_video": "final_the_wandering_inn_026_046.mp4",
    "cover_image": "cover_the_wandering_inn_026_046.jpg",
    "timestamps_file": "youtube_timestamps_the_wandering_inn_026_046.txt",
    "subtitles_file": "subtitles_the_wandering_inn_026_046.srt",
    "payload_file": "youtube_upload_payload_the_wandering_inn_026_046.json",

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
    "video_title": "The Wandering Inn | Ch 26 - 46 Full Audio Novel Marathon | Rising Shadows of Izril",
    "privacy_status": "unlisted",
    "tags": [
        "The Wandering Inn", "Wandering Inn Audiobook", "Erin Solstice", "Ryoka Griffin",
        "Liscor", "Antinium", "Klbkch", "Relc", "LitRPG Audiobook", "Fantasy Audiobook",
        "Progression Fantasy", "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the complete 21-chapter audio novel marathon of 'The Wandering Inn' (Chapters 26 to 46).\n\n"
        "As Erin Solstice continues carving out a sanctuary in her lonely inn on the floodplains outside Liscor, "
        "the world of Izril refuses to stay simple. Tensions flare between Drakes and Antinium, while city runner "
        "Ryoka Griffin tests her speed and survival against the treacherous wilderness, winter predators, and the complex web of power. "
        "Witness shifting bonds, unforgettable chess games, and the darkening horizon before the volume finale.\n\n"
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
        "#TheWanderingInn #ErinSolstice #RyokaGriffin #LitRPG #FantasyAudiobook #ProgressionFantasy #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Arc Visual Blocks spanning Chapters 26 to 46
    "blocks": [
        {
            "index": 1, "range": (26, 30),
            "title": ["CHESSBOARD DIPLOMACY", "THE ANCHOR OF LISCOR"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic high-fantasy interior of a rustic stone inn common room lit by glowing hearth fire, "
                "a young human woman with messy brown hair leaning over a wooden chessboard opposite a tall insectoid Antinium soldier "
                "with polished black chitin armor, warm amber lighting, detailed wood grain and soft shadows, 4K resolution."
            )
        },
        {
            "index": 2, "range": (31, 35),
            "title": ["THE BAREFOOT RUNNER", "ROADS OF THE FLOODPLAINS"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic dramatic wide-angle shot of an athletic young human woman with dark hair sprinting barefoot across craggy, "
                "windswept grasslands, a heavy leather courier bag strapped to her back, dramatic overcast autumn storm clouds rolling over jagged mountain foothills, "
                "volumetric mist, sharp detailed textures."
            )
        },
        {
            "index": 3, "range": (36, 40),
            "title": ["SHADOWS IN THE CAVES", "DRAKE DEFENDERS"],
            "fallback_color": (25, 15, 20),
            "prompt": (
                "Cinematic action composition outside ancient rocky cave tunnels at dusk, a large scaled green Drake city guard holding a barbed spear "
                "standing shoulder-to-shoulder with a black-carapace insectoid warrior facing ferocious multi-legged subterranean cave monsters, "
                "glowing torchlight, dramatic rim lighting, gritty fantasy."
            )
        },
        {
            "index": 4, "range": (41, 46),
            "title": ["THE GATHERING COLD", "SANCTUARY UNDER TRIAL"],
            "fallback_color": (25, 30, 35),
            "prompt": (
                "Cinematic twilight landscape of an isolated two-story stone inn sitting alone in the middle of vast darkening floodplains, "
                "early winter frost dusting the plains grass, warm orange firelight spilling from the downstairs windows into the cold evening blue, "
                "atmospheric mist, moody high-fantasy masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
