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


BUILD_DIR = "build_dungeon_diver_101_150"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "dungeon-diver-stealing-a-monsters-power",
    "start_url": "https://freewebnovel.com/novel/dungeon-diver-stealing-a-monsters-power/chapter-101",
    "start_chapter": 101,
    "end_chapter": 150,
    "default_topic": "Dungeon Diver: Stealing A Monster's Power / Dark Fantasy / LitRPG / Monster Skill Plundering / Deep Abyss Floors",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook (start_chapter > 1 -> continuation recap)
    "intro_hook": "We descend back into the perilous abyssal depths as our dungeon diver plunders horrifying monster authorities, pushing mortal limits to survive the lethal lower strata.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_dungeon_diver_101_150.mp3",
    "final_video": "final_dungeon_diver_101_150.mp4",
    "cover_image": "cover_dungeon_diver_101_150.jpg",
    "timestamps_file": "youtube_timestamps_dungeon_diver_101_150.txt",
    "subtitles_file": "subtitles_dungeon_diver_101_150.srt",
    "payload_file": "youtube_upload_payload_dungeon_diver_101_150.json",

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
    "video_title": "Dungeon Diver: Stealing A Monster's Power | Ch 101 - 150 Full Marathon | Plundered Sovereignty Arc",
    "privacy_status": "unlisted",
    "tags": [
        "Dungeon Diver", "Dungeon Diver Audiobook", "Stealing A Monsters Power",
        "LitRPG", "Progression Fantasy", "Dark Fantasy", "Monster Evolution",
        "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the complete 50-chapter audio novel marathon of 'Dungeon Diver: Stealing A Monster's Power' (Chapters 101 to 150) — the Plundered Sovereignty Arc.\n\n"
        "Catch up on earlier arcs:\n"
        "• Episode 1 (Ch 1-50): https://www.youtube.com/watch?v=7yjlZq9efD0\n"
        "• Episode 2 (Ch 51-100): https://www.youtube.com/watch?v=mtleXaBER0Q\n"
        "• Full Series Playlist: https://www.youtube.com/playlist?list=PLQPdvMoYb7vA\n\n"
        "Plunging further into treacherous dungeon ecosystems, our diver encounters elite tier fiends, ancient abyssal sentinels, "
        "and catastrophic mutations. By hunting impossible predators and assimilating their unique traits, he transforms stolen monster power "
        "into devastating martial dominance.\n\n"
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
        "#DungeonDiver #LitRPG #DarkFantasy #MonsterPower #ProgressionFantasy #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 101 to 150 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (101, 110),
            "title": ["ABYSSAL THRESHOLD", "MUTATED APEX"],
            "fallback_color": (15, 20, 25),
            "prompt": (
                "Cinematic dark fantasy dungeon cavern illuminated by glowing bioluminescent fungi and cracked obsidian walls, "
                "a hooded dungeon diver dual-wielding blackened daggers infused with stolen shadow tendrils, "
                "stalking an armored subterranean predator with glowing violet eyes, volumetric mist, 4K resolution."
            )
        },
        {
            "index": 2, "range": (111, 120),
            "title": ["CHITIN & SOVEREIGNTY", "POWER ASSIMILATION"],
            "fallback_color": (25, 15, 20),
            "prompt": (
                "Cinematic high-octane battle inside a crystalline subterranean lair, the hunter shattering the carapace of a colossal crystal scorpion, "
                "absorbing tendrils of radiant azure monster mana into his bare hands, floating translucent system status runes, dramatic motion blur."
            )
        },
        {
            "index": 3, "range": (121, 130),
            "title": ["FORBIDDEN STRATA", "CORRUPTED SENTINEL"],
            "fallback_color": (20, 15, 30),
            "prompt": (
                "Cinematic atmospheric underground ruins of an ancient drowned temple, black water reflecting eerie green witch-fire, "
                "a towering four-armed stone guardian emerging from submerged arches wielding colossal broadswords, "
                "intense depth of field, dramatic cinematic rim lighting."
            )
        },
        {
            "index": 4, "range": (131, 140),
            "title": ["DEVOURING WILL", "CHAOS EXTRACTION"],
            "fallback_color": (30, 20, 15),
            "prompt": (
                "Cinematic dynamic combat sequence in a cavernous magma rift, a agile warrior leaping over erupting molten fissures, "
                "unleashing stolen sonic shockwaves that crack the armored scales of a winged magma drake, sparks flying, volumetric smoke, masterpiece."
            )
        },
        {
            "index": 5, "range": (141, 150),
            "title": ["APEX DIVER", "DEPTHS UNLOCKED"],
            "fallback_color": (20, 25, 30),
            "prompt": (
                "Cinematic heroic composition standing at the precipice of a bottomless subterranean chasm leading to the deepest abyss floor, "
                "the experienced diver equipped with composite chimeric monster armor, glowing runes pulsing across his gear, "
                "looking down into swirling purple void energy, majestic and ominous 4K render."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
