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


BUILD_DIR = "build_dungeon_crawler_carl_9_257"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source: Local PDF path and Page range (~8 to 8.5 Hours of Narration)
    "novel_slug": "dungeon-crawler-carl",
    "start_url": r"D:\Projects\visualer\ebooks\Dungeon_Crawler_Carl_Complete_Series_1-7_-_Matt_Dinniman.pdf",
    "start_chapter": 9,
    "end_chapter": 257,
    "is_start": True,  # Series opening: Earth's collapse, entering the World Dungeon, Level 1 and Level 2 trials
    "default_topic": "Dungeon Crawler Carl / Matt Dinniman / LitRPG / Carl and Princess Donut / World Dungeon / AI Dungeon Master / Apocalyptic Survival",

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook
    "intro_hook": "When Earth is flattened into a televised eighteen-level death dungeon, a former Coast Guard veteran in boxer shorts and an ex-girlfriend's prize-winning cat must survive an insane sadistic AI.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_dungeon_crawler_carl_9_257.mp3",
    "final_video": "final_dungeon_crawler_carl_9_257.mp4",
    "cover_image": "cover_dungeon_crawler_carl_9_257.jpg",
    "timestamps_file": "youtube_timestamps_dungeon_crawler_carl_9_257.txt",
    "subtitles_file": "subtitles_dungeon_crawler_carl_9_257.srt",
    "payload_file": "youtube_upload_payload_dungeon_crawler_carl_9_257.json",

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
    "video_title": "Dungeon Crawler Carl | Matt Dinniman | 8+ Hours Full LitRPG Audiobook Marathon (Pages 9 - 257) | Book 1",
    "privacy_status": "unlisted",
    "tags": [
        "Dungeon Crawler Carl", "Matt Dinniman", "LitRPG Audiobook", "Princess Donut",
        "Carl and Donut", "World Dungeon", "Fantasy Audiobook", "Audiobook Marathon",
        "Apocalyptic LitRPG", "Dungeon Crawler Carl Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the modern LitRPG phenomenon 'Dungeon Crawler Carl' by Matt Dinniman (Pages 9 to 257) — Book 1 Full Audio Marathon.\n\n"
        "It's the middle of winter. Carl steps outside in his boxer shorts and a leather jacket to rescue his ex-girlfriend's Persian cat, Princess Donut. "
        "Seconds later, every roof on Earth collapses, and a galactic reality show forces humanity down the stairwell into the World Dungeon.\n\n"
        "Together with Donut—who rapidly develops high intelligence and magic—Carl must battle through goblin traps, explosive ordnance, and a deranged AI showrunner.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "🎙️ NARRATION: en-US-ChristopherNeural (Deep Cinematic Baritone).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audio presentation is an edited fan reading produced for literature appreciation, commentary, and entertainment purposes.\n\n"
        "#DungeonCrawlerCarl #MattDinniman #LitRPG #AudiobookMarathon #PrincessDonut #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks across Pages 9 to 257 (249 pages partitioned)
    "blocks": [
        {
            "index": 1, "range": (9, 71),
            "title": ["THE COLLAPSE", "DESCENT INTO LEVEL 1"],
            "fallback_color": (20, 18, 26),
            "prompt": (
                "Cinematic high-contrast underground dungeon stairwell carved from dark glowing rock, "
                "a rugged man in leather jacket and boxer shorts holding a fluffy tortoiseshell Persian cat, "
                "neon holographic LitRPG floating status screens flickering with magenta and cyan text, atmospheric fog, 4K digital painting."
            )
        },
        {
            "index": 2, "range": (72, 133),
            "title": ["GOBLIN WARRENS", "UNCONVENTIONAL ORDNANCE"],
            "fallback_color": (28, 16, 12),
            "prompt": (
                "Sprawling subterranean goblin fortress filled with makeshift wooden barricades, rusty scrap metal spikes, and ticking explosive traps, "
                "fiery explosions illuminating jagged stone caverns, volumetric smoke and dynamic sparks, gritty LitRPG action concept art, 4K."
            )
        },
        {
            "index": 3, "range": (134, 195),
            "title": ["THE SPONSOR BOXES", "LEVEL 2: THE MEADOW"],
            "fallback_color": (16, 24, 20),
            "prompt": (
                "Surreal underground biome mimicking an eerie artificial twilight meadow surrounded by dark metallic containment walls, "
                "glowing celestial loot boxes descending on mechanical cables, a sassy regal cat wearing a crown and magic sunglasses, 4K digital art."
            )
        },
        {
            "index": 4, "range": (196, 257),
            "title": ["BOSS ENCOUNTER", "YOU WILL NOT BREAK ME"],
            "fallback_color": (24, 12, 16),
            "prompt": (
                "Colossal underground arena bathed in dramatic crimson warning lights, massive armored alien boss monster roaring amidst debris, "
                "a determined warrior stepping forward with smoking spiked combat boots and explosive charges ready, cinematic framing, 4K masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))