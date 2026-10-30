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


BUILD_DIR = "build_road_to_mastery_227_267"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "road-to-mastery-a-litrpg-apocalypse",
    "start_url": "https://freewebnovel.com/novel/road-to-mastery-a-litrpg-apocalypse/chapter-227",
    "start_chapter": 227,
    "end_chapter": 267,
    "default_topic": "Road to Mastery: A LitRPG Apocalypse / Brawler Class / System Apocalypse / Bareknuckle Combat / Cultivation Trial / Mastery Path",

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook
    "intro_hook": "Refusing weapons, spells, and shortcuts, an iron-fisted brawler hammers his way through a cutthroat System Apocalypse, letting raw discipline forge the true road to mastery.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_road_to_mastery_227_267.mp3",
    "final_video": "final_road_to_mastery_227_267.mp4",
    "cover_image": "cover_road_to_mastery_227_267.jpg",
    "timestamps_file": "youtube_timestamps_road_to_mastery_227_267.txt",
    "subtitles_file": "subtitles_road_to_mastery_227_267.srt",
    "payload_file": "youtube_upload_payload_road_to_mastery_227_267.json",

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
    "video_title": "Road to Mastery: A LitRPG Apocalypse | Ch 227 - 267 Full Audiobook Marathon | Iron Brawler",
    "privacy_status": "unlisted",
    "tags": [
        "Road to Mastery", "Road to Mastery Audiobook", "LitRPG Apocalypse",
        "System Apocalypse", "LitRPG Audiobook", "Brawler Class", "Martial Arts LitRPG",
        "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "This episode, we step right back into the story, continuing exactly where we left off in our previous episode of this series.\n\n"
        "Experience 'Road to Mastery: A LitRPG Apocalypse' (Chapters 227 to 267) — The Trials of Iron and Will.\n\n"
        "Pitted against ruthless zone trials, alien adversaries, and system overseers, our relentless unarmed brawler "
        "tests his kinetic boundaries. Through sheer grit, body tempering, and bone-shattering strikes, the struggle "
        "for survival deepens across treacherous apocalyptic landscapes.\n\n"
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
        "#RoadToMastery #LitRPG #SystemApocalypse #FantasyAudiobook #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks across Chapters 227 to 267 (41 chapters partitioned)
    "blocks": [
        {
            "index": 1, "range": (227, 237),
            "title": ["TEMPERED FLESH", "THE TRIAL CONTINUES"],
            "fallback_color": (22, 16, 18),
            "prompt": (
                "Cinematic high-contrast scene of a muscular martial brawler wrapped in fraying hand wraps, "
                "standing amidst the shattered ruins of a futuristic apocalyptic city, dust and sparks swirling in the air, "
                "subtle glowing golden veins of kinetic power running down his forearms, dramatic rim lighting, 4K digital art."
            )
        },
        {
            "index": 2, "range": (238, 247),
            "title": ["APOCALYPTIC WASTES", "SAVAGE CONFRONTATION"],
            "fallback_color": (28, 18, 14),
            "prompt": (
                "Vast desolate desert crater zone beneath an alien sky with shattered celestial rings, "
                "a fearless lone brawler bracing against a colossal armored beast charging through dust clouds, "
                "dynamic motion blur, flying debris and shockwaves tearing through the barren ground, 4K resolution."
            )
        },
        {
            "index": 3, "range": (248, 257),
            "title": ["KINETIC SURGE", "BREAKING THE CEILING"],
            "fallback_color": (16, 20, 26),
            "prompt": (
                "Cavernous subterranean alien dungeon illuminated by glowing azure crystal pillars, "
                "a focused fighter meditating upon a high stone precipice, dense atmospheric mist swirling below, "
                "faint cyan system status glyphs radiating softly in the dim light, atmospheric composition, 4K digital painting."
            )
        },
        {
            "index": 4, "range": (258, 267),
            "title": ["IRON RESOLVE", "THE ROAD AHEAD"],
            "fallback_color": (24, 14, 18),
            "prompt": (
                "A weathered warrior overlooking an endless expanse of alien biomes from a high mountain ridge at sunset, "
                "clenched fists smoking with spent kinetic force, crimson evening sky casting long dramatic shadows across the peaks, "
                "resolute solitary posture representing unyielding mastery, 4K masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
