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

BUILD_DIR = "build_hp_miss_malfoy_351_392"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "hp-miss-malfoy",
    "start_url": "https://mtl-novel.com/novel/hp-miss-malfoy-doesnt-want-to-romance-her-parents-generation/chapter-351-the-gift-brought-by-the-return/",
    "start_chapter": 351,
    "end_chapter": 392,
    "default_topic": "Miss Malfoy",

    # Concurrency Settings & Narrator Lock
    "batch_size": 7,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook
    "intro_hook": "We rejoin Manxi Malfoy as she navigates the volatile Marauders era, untangling pureblood alliances, hidden family tensions, and the lingering echoes of her return to Hogwarts.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_hp_miss_malfoy_351_392.mp3",
    "final_video": "final_hp_miss_malfoy_351_392.mp4",
    "cover_image": "cover_hp_miss_malfoy_351_392.jpg",
    "timestamps_file": "youtube_timestamps_hp_miss_malfoy_351_392.txt",
    "subtitles_file": "subtitles_hp_miss_malfoy_351_392.srt",
    "payload_file": "youtube_upload_payload_hp_miss_malfoy_351_392.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "THE RETURN & MARAUDERS ERA SECRETS! [Ch 351-392] | HP Miss Malfoy Fanfiction Audiobook Marathon",
    "tags": [
        "Harry Potter Fanfiction", "Miss Malfoy", "Marauders Era", "Slytherin",
        "James Potter", "Sirius Black", "Severus Snape", "Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'HP: Miss Malfoy Doesn't Want to Romance Her Parents' Generation' with Chapters 351 through 392!\n\n"
        "Stepping back into the hallowed halls of 1970s Hogwarts, Manxi Malfoy confronts the shifting tides of pureblood politics, "
        "the growing shadows over the wizarding world, and the chaotic presence of the Marauders. Experience this epic 42-chapter arc "
        "with multi-voice neural TTS, context-aware acoustic soundscapes, and full synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for all character dialogue and narrative prose).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original characters and world concepts belong to their respective creators. Subscribe for more chapters!\n\n"
        "#HPMissMalfoy #HarryPotterFanfiction #MaraudersEra #Slytherin #Audiobook #BeingABong"
    ),

    # Visual Prompts (4 balanced thematic blocks across Ch 351 to 392: 351-360, 361-370, 371-380, 381-392)
    "blocks": [
        {
            "index": 1, "range": (351, 360),
            "title": ["RETURN TO THE MANOR", "UNSPOKEN GIFTS"],
            "fallback_color": (20, 35, 25),
            "prompt": (
                "Cinematic 3D fantasy illustration of an aristocratic young blonde witch with platinum hair dressed in elegant emerald-trimmed Slytherin robes, "
                "standing inside an opulent Malfoy Manor salon beside a roaring marble fireplace, holding an ornate antique magical jewelry box. "
                "Sunlight filtering through gothic arched windows, intricate dark-wood furniture, crisp facial features, high-contrast 4k rendering."
            )
        },
        {
            "index": 2, "range": (361, 370),
            "title": ["HOGWARTS SHADOWS", "MARAUDER CLASHES"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D fantasy scene in a torchlit Hogwarts corridor, showing the young blonde Slytherin heiress with wand raised gracefully, "
                "standing her ground before four confident Gryffindor boys in 1970s school uniforms. "
                "Volumetric dust and candlelight dancing off stone masonry, floating sparks of spellfire, intense dramatic atmosphere, realistic cloth textures."
            )
        },
        {
            "index": 3, "range": (371, 380),
            "title": ["BLACK LAKE REFLECTIONS", "TACTICAL ALLIANCES"],
            "fallback_color": (15, 25, 35),
            "prompt": (
                "Cinematic 3D fantasy portrait of the young blonde witch sitting by the edge of the misty Black Lake beneath the shadow of Hogwarts castle, "
                "holding an open enchanted parchment while looking thoughtfully across the rippling dark water. "
                "Twilight violet sky, gentle cold fog curling across the ground, cinematic lighting, highly detailed features, medium shot."
            )
        },
        {
            "index": 4, "range": (381, 392),
            "title": ["PUREBLOOD CREST", "FORGING DESTINY"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D fantasy illustration of the young female protagonist standing resolute in the Slytherin common room beneath gothic stone arches, "
                "silver and green banners hanging from the walls, glowing magical runes swirling around her outstretched silver wand. "
                "Eerie green subterranean underwater lighting through enchanted windows, intense determined gaze, dramatic masterpiece 3D render."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
