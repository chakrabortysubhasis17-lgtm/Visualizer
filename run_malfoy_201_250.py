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


BUILD_DIR = "build_hp_miss_malfoy_201_250"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "hp-miss-malfoy-doesnt-want-to-romance-her-parents-generation",
    "start_url": "https://mtl-novel.com/novel/hp-miss-malfoy-doesnt-want-to-romance-her-parents-generation/chapter-201/",
    "start_chapter": 201,
    "end_chapter": 250,
    "default_topic": "HP Miss Malfoy Doesn't Want to Romance Her Parents Generation / Harry Potter Fanfiction / Hogwarts",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook (Since start_chapter > 1, pipeline prefixes continuation intro)
    "intro_hook": "We rejoin Miss Malfoy at Hogwarts as magical plots thicken, political tensions rise, and our witty protagonist expertly avoids the romantic entanglements of her parents' generation.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_hp_miss_malfoy_201_250.mp3",
    "final_video": "final_hp_miss_malfoy_201_250.mp4",
    "cover_image": "cover_hp_miss_malfoy_201_250.jpg",
    "timestamps_file": "youtube_timestamps_hp_miss_malfoy_201_250.txt",
    "subtitles_file": "subtitles_hp_miss_malfoy_201_250.srt",
    "payload_file": "youtube_upload_payload_hp_miss_malfoy_201_250.json",

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
    "video_title": "HP: Miss Malfoy Doesn't Want to Romance Her Parents' Generation | Ch 201 - 250 Audiobook",
    "privacy_status": "unlisted",
    "tags": [
        "HP Miss Malfoy", "Harry Potter Fanfiction", "Malfoy Audiobook", "Hogwarts",
        "Fanfic Audiobook", "Magical Society", "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the complete 50-chapter audio novel marathon of 'HP: Miss Malfoy Doesn't Want to Romance Her Parents' Generation' (Chapters 201 to 250).\n\n"
        "Navigating the intricate social and political minefield of magical Britain, Miss Malfoy continues her mission of avoiding past-generation romances "
        "while outsmarting professors, plotting peers, and unexpected twists within the hallowed halls of Hogwarts.\n\n"
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
        "#MissMalfoy #HarryPotterFanfic #Hogwarts #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 201 to 250 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (201, 210),
            "title": ["HOGWARTS HALLS", "POLITICAL MANEUVERS"],
            "fallback_color": (20, 20, 30),
            "prompt": (
                "Cinematic high-fantasy interior of an ancient gothic Hogwarts corridor with floating candles and stone archways, "
                "a clever young witch in Slytherin robes holding a glowing wand with a composed, calculating expression, "
                "ambient torchlight and magical dust motes, 4K resolution."
            )
        },
        {
            "index": 2, "range": (211, 220),
            "title": ["POTIONS AND SECRETS", "SUBTLE INTERVENTIONS"],
            "fallback_color": (15, 25, 20),
            "prompt": (
                "Cinematic fantasy apothecary classroom lined with bubbling glass cauldrons and glowing potion jars casting emerald and sapphire light, "
                "students focused over brewing tables, moody volumetric lighting, highly detailed."
            )
        },
        {
            "index": 3, "range": (221, 230),
            "title": ["SLYTHERIN COMMON ROOM", "MIDNIGHT SCHEMING"],
            "fallback_color": (25, 15, 20),
            "prompt": (
                "Cinematic dark fantasy common room submerged beneath the lake with greenish tinted water filtering through tall arched windows, "
                "ornate velvet furniture and a crackling stone fireplace, mysterious silhouettes whispering in the shadows."
            )
        },
        {
            "index": 4, "range": (231, 240),
            "title": ["MAGICAL DUELS", "AVOIDING ENTANGLEMENTS"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic dynamic action shot inside a stone dueling courtyard, brilliant spells and crimson spark trails clashing against silvery shields, "
                "focused magical combatants in wizard robes, dramatic lens flare, epic composition."
            )
        },
        {
            "index": 5, "range": (241, 250),
            "title": ["ASTRONOMY TOWER", "THE UNFOLDING FUTURE"],
            "fallback_color": (15, 15, 25),
            "prompt": (
                "Cinematic breathtaking panoramic night view from the top of the Hogwarts astronomy tower looking out over the Forbidden Forest under a starry sky, "
                "a solitary witch gazing into the horizon holding an ancient brass telescope, ethereal moonlight, masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
