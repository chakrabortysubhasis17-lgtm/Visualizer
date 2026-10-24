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


BUILD_DIR = "build_shangrila_frontier_101_150"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "shangrila-frontier",
    "start_url": "https://freewebnovel.com/novel/shangriLa-frontier-shitty-games-hunter-challenges-godly-game/chapter-151",
    "start_chapter": 101,
    "end_chapter": 150,
    "default_topic": "Shangri-La Frontier / VRMMO / Sunraku / World-First Aftermath / Clan Wolfgang / Nephilim Hollow",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook (Since start_chapter > 1, pipeline prefixes continuation intro)
    "intro_hook": "We follow Sunraku through the explosive aftermath of conquering Wezaemon as top clans scramble for world secrets, and our trash-game veteran prepares for an entirely new dimension of high-stakes competition.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_shangrila_frontier_101_150.mp3",
    "final_video": "final_shangrila_frontier_101_150.mp4",
    "cover_image": "cover_shangrila_frontier_101_150.jpg",
    "timestamps_file": "youtube_timestamps_shangrila_frontier_101_150.txt",
    "subtitles_file": "subtitles_shangrila_frontier_101_150.srt",
    "payload_file": "youtube_upload_payload_shangrila_frontier_101_150.json",

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
    "video_title": "Shangri-La Frontier | Ch 101 - 150 Full Audio Novel Marathon | Clan Wolfgang & Nephilim Arc",
    "privacy_status": "unlisted",
    "tags": [
        "Shangri-La Frontier", "Shangri La Frontier Audiobook", "Sunraku", "Rakuro Hizutome",
        "Arthur Pencilgon", "Oikatzo", "Clan Wolfgang", "Nephilim Hollow", "Sylvia Goldbull",
        "VRMMO Audiobook", "LitRPG Audiobook", "Progression Fantasy", "Audiobook Marathon",
        "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the complete 50-chapter audio novel marathon of 'Shangri-La Frontier' (Chapters 101 to 150) — the Clan Wolfgang & Global Arena Arc.\n\n"
        "In the wake of Wezaemon the Tombguard's legendary defeat, the entire player base is thrown into utter turmoil. "
        "Sunraku, Pencilgon, and Oikatzo forge the elite covert clan 'Wolfgang' to negotiate with top guilds while shielding vital world lore. "
        "Take a thrilling detour into the brutal mecha trash-game Nephilim Hollow, witness high-octane overseas tournament rivalries, "
        "and follow the vanguard as they chart a course toward the deepest abyss of the ocean.\n\n"
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
        "#ShangriLaFrontier #Sunraku #ClanWolfgang #NephilimHollow #VRMMO #LitRPG #GamingAudiobook #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 101 to 150 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (101, 110),
            "title": ["FOUNDING OF WOLFGANG", "CLASH OF THE TOP CLANS"],
            "fallback_color": (20, 20, 30),
            "prompt": (
                "Cinematic high-fantasy meeting room inside a grand marble conference hall, "
                "representatives of massive guilds in ornate plate armor and wizard robes surrounding a round table, "
                "facing a shadowy trio consisting of a bird-masked dual-wielding scout, a scheming silver-haired rogue, and a composed martial monk, "
                "dramatic atmospheric rays of light through stained glass, high-detail 4K."
            )
        },
        {
            "index": 2, "range": (111, 120),
            "title": ["NEPHILIM HOLLOW", "RUST-COLORED STEEL"],
            "fallback_color": (30, 20, 15),
            "prompt": (
                "Cinematic gritty sci-fi mech battlefield amidst industrial smoke and rain, "
                "two battered bipedal armored mechas dueling with vibrating thermal blades and ballistic cannons, "
                "sparks flying from shattered cockpit plating, volumetric exhaust fumes, photorealistic hard-surface sci-fi action."
            )
        },
        {
            "index": 3, "range": (121, 130),
            "title": ["OVERSEAS SHOWDOWN", "THE FIGHTING GAME SUMMIT"],
            "fallback_color": (15, 25, 35),
            "prompt": (
                "Cinematic esports arena illuminated by neon blue and magenta floodlights, "
                "two pro gamers locked in intense concentration behind high-end gaming stations, "
                "massive holographic projections above displaying a ferocious fighting game duel between a martial striker and a golden armored champion, "
                "dynamic crowd silhouettes, electric competition atmosphere."
            )
        },
        {
            "index": 4, "range": (131, 140),
            "title": ["VOYAGE TO THE ABYSS", "ANCIENT CORAL REALM"],
            "fallback_color": (10, 25, 30),
            "prompt": (
                "Cinematic underwater fantasy panorama showing ancient sunken stone spires coated in glowing bioluminescent coral, "
                "a bird-masked adventurer swimming effortlessly alongside a magical rabbit companion wearing an underwater diving helmet, "
                "giant aquatic mantas drifting gracefully overhead in deep cerulean waters, ethereal god rays."
            )
        },
        {
            "index": 5, "range": (141, 150),
            "title": ["DEPTHS OF KUTANID", "THE INVERTED LABYRINTH"],
            "fallback_color": (25, 15, 30),
            "prompt": (
                "Cinematic dark fantasy sea floor temple surrounded by an unnatural dome of inverted ocean currents, "
                "a colossal eldritch shadow with sweeping tentacles looming in the abyss beyond the coral arches, "
                "the adventurer party standing on ancient seafloor ruins preparing weapons for an unprecedented colossus raid, "
                "dramatic neon aqua and deep violet lighting, masterwork composition."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
