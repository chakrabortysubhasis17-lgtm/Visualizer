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


BUILD_DIR = "build_shangrila_frontier_201_250"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "shangrila-frontier",
    "start_url": "https://freewebnovel.com/novel/shangriLa-frontier-shitty-games-hunter-challenges-godly-game/chapter-343",
    "start_chapter": 201,
    "end_chapter": 250,
    "default_topic": "Shangri-La Frontier / VRMMO / Sunraku / GGC Esports Summit / Unique Monsters Rematch",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook (Since start_chapter > 1, pipeline prefixes continuation intro)
    "intro_hook": "We follow Sunraku as top-tier esports rivalries collide with the mysteries of Shangri-La Frontier, setting the stage for an explosive new tier of monster hunts and godly challenges.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_shangrila_frontier_201_250.mp3",
    "final_video": "final_shangrila_frontier_201_250.mp4",
    "cover_image": "cover_shangrila_frontier_201_250.jpg",
    "timestamps_file": "youtube_timestamps_shangrila_frontier_201_250.txt",
    "subtitles_file": "subtitles_shangrila_frontier_201_250.srt",
    "payload_file": "youtube_upload_payload_shangrila_frontier_201_250.json",

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
    "video_title": "Shangri-La Frontier | Ch 201 - 250 Full Audio Novel Marathon | Global Stage & Apex Hunt Arc",
    "privacy_status": "unlisted",
    "tags": [
        "Shangri-La Frontier", "Shangri La Frontier Audiobook", "Sunraku", "Rakuro Hizutome",
        "Arthur Pencilgon", "Oikatzo", "GGC", "Sylvia Goldbull", "Seven Colossi",
        "Lycagon", "VRMMO Audiobook", "LitRPG Audiobook", "Progression Fantasy",
        "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the complete 50-chapter audio novel marathon of 'Shangri-La Frontier' (Chapters 201 to 250) — the Global Stage & Apex Hunt Arc.\n\n"
        "Following their conquest over the abyss, Sunraku and his companions take their battle-honed reflexes into high-stakes global competitions "
        "and clash with legendary esports champions. But the real game is far from finished. Ancient world secrets awaken across the continent of Shangri-La, "
        "setting off high-tier boss encounters, ruthless player-versus-player rivalries, and the preparation for a fateful rematch with the night itself.\n\n"
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
        "#ShangriLaFrontier #Sunraku #GGC #SylviaGoldbull #Lycagon #VRMMO #LitRPG #GamingAudiobook #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 201 to 250 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (201, 210),
            "title": ["THE GLOBAL STAGE", "ESPORTS CONTENDERS"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic high-octane esports arena, dramatic overhead floodlights in electric blue and gold illuminating "
                "two elite competitive players in high-tech booths, a massive holographic arena above displaying a shirtless fighter "
                "in a blue bird mask executing a lightning-fast counter against an armored gladiator, roaring stadium crowd, 4K rendering."
            )
        },
        {
            "index": 2, "range": (211, 220),
            "title": ["TACTICAL EXPERIMENTATION", "KUSOGE MASTERY"],
            "fallback_color": (30, 20, 25),
            "prompt": (
                "Cinematic action composition inside a bizarre glitch-ridden neon game dimension, a bird-masked dual-blade rogue "
                "exploiting game engine physics to surf along collapsing digital polygons, dodging chaotic laser barrages, "
                "dynamic motion streaks, glowing VR interface artifacts, sharp focus."
            )
        },
        {
            "index": 3, "range": (221, 230),
            "title": ["RETURN OF THE NIGHTSLAYER", "SHADOWS LENGTHEN"],
            "fallback_color": (15, 10, 20),
            "prompt": (
                "Cinematic dark fantasy twilight scene in an eerie mist-draped pine forest, a colossal four-eyed black shadow wolf "
                "with smoke fur standing atop a mossy boulder under an indigo night sky, the bird-masked protagonist gripping twin glowing vorpal daggers, "
                "volumetric moonbeams, tense epic standoff."
            )
        },
        {
            "index": 4, "range": (231, 240),
            "title": ["CELESTIAL BEASTS", "CONTINENTAL STRUGGLE"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic high-fantasy wide angle battle across craggy mountain summits, a majestic golden celestial dragon beast "
                "soaring through thunderous storm clouds while radiating blinding divine lightning, guild strike parties assembling on ridge lines below, "
                "dramatic scale and perspective, photorealistic fantasy textures."
            )
        },
        {
            "index": 5, "range": (241, 250),
            "title": ["SUMMIT OF GOD-TIER", "THE PATH TO APEX"],
            "fallback_color": (25, 20, 30),
            "prompt": (
                "Cinematic panoramic hero shot at sunrise atop an ancient soaring mountain sanctuary, Sunraku flanked by his trusted allies "
                "looking out over vast unexplored continents bathed in golden dawn light, fluttering cloaks and glowing runic weapons, "
                "inspirational atmosphere, masterpiece digital art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
