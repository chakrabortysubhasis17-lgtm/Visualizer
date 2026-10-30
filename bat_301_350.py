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


BUILD_DIR = "build_vampire_bat_to_loli_tyrant_301_350"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "game-descends-from-vampire-bat-to-loli-tyrant",
    "start_url": "https://mtl-novel.com/novel/game-descends-from-vampire-bat-to-loli-tyrant/chapter-301-the-six-dynasties-allied-forces/",
    "start_chapter": 301,
    "end_chapter": 350,
    "is_start": False,  # Continuation volume
    "default_topic": "Game Descends: From Vampire Bat to Loli Tyrant / Global Descent / Blood Clan Evolution / Dynastic War / Overpowered Tyrant / LitRPG",

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook
    "intro_hook": "As the Six Dynasties unite their armies in desperation, our evolved sovereign unleashes supreme bloodline dominance to crush human empires and claim absolute dominion.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_vampire_bat_to_loli_tyrant_301_350.mp3",
    "final_video": "final_vampire_bat_to_loli_tyrant_301_350.mp4",
    "cover_image": "cover_vampire_bat_to_loli_tyrant_301_350.jpg",
    "timestamps_file": "youtube_timestamps_vampire_bat_to_loli_tyrant_301_350.txt",
    "subtitles_file": "subtitles_vampire_bat_to_loli_tyrant_301_350.srt",
    "payload_file": "youtube_upload_payload_vampire_bat_to_loli_tyrant_301_350.json",

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
    "video_title": "Game Descends: From Vampire Bat to Loli Tyrant | Ch 301 - 350 Full Audiobook Marathon",
    "privacy_status": "unlisted",
    "tags": [
        "Game Descends From Vampire Bat to Loli Tyrant", "Vampire Bat to Loli Tyrant",
        "Vampire Evolution Audiobook", "LitRPG Audiobook", "Fantasy Audiobook",
        "Blood Tyrant", "Overpowered MC", "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "This episode, we step right back into the story, continuing exactly where we left off in our previous episode of this series.\n\n"
        "Experience 'Game Descends: From Vampire Bat to Loli Tyrant' (Chapters 301 to 350) — The Six Dynasties War Arc.\n\n"
        "Faced with the terrifying rise of an unstoppable bloodline, the Six Dynasties forge a desperate coalition to exterminate "
        "the blood empire. But as mortal legions, imperial champions, and ancient siege formations march into the warzone, "
        "they find only ruthless slaughter, crimson domain expansion, and the absolute authority of an apex tyrant.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "🎙️ NARRATION: en-US-ChristopherNeural (Deep Cinematic Baritone).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audio presentation is an edited fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#VampireEvolution #LitRPG #BloodTyrant #OverpoweredMC #FantasyAudiobook #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks across Chapters 301 to 350 (50 chapters partitioned)
    "blocks": [
        {
            "index": 1, "range": (301, 313),
            "title": ["SIX DYNASTIES COALITION", "WAR DRUMS GATHER"],
            "fallback_color": (22, 14, 16),
            "prompt": (
                "Massive imperial war council pavilion overlooking endless assembled armies, "
                "six distinct dynastic banners fluttering in stormy wind, armored generals and royal court mages gathered "
                "around a grand strategic glowing battle map, tense war atmosphere, cinematic scale, 4K resolution."
            )
        },
        {
            "index": 2, "range": (314, 325),
            "title": ["CRIMSON DOMAIN", "THE TYRANT'S MARCH"],
            "fallback_color": (26, 10, 14),
            "prompt": (
                "A gothic vampire sovereign floating above a shattered obsidian throne fortress, "
                "surrounded by a surging vortex of crimson blood energy and swarms of dark shadow bats, "
                "deep scarlet aura radiating into a pitch-black night sky with a blood-red moon, dark fantasy 4K masterpiece."
            )
        },
        {
            "index": 3, "range": (326, 338),
            "title": ["CLASH OF EMPIRES", "LEGIONS FALL"],
            "fallback_color": (20, 12, 18),
            "prompt": (
                "Colossal fantasy war battle on shattered plains at dusk, thousands of armored imperial soldiers clashing with "
                "spectral blood beasts and crimson shockwaves tearing through enemy ranks, "
                "catapults firing flaming projectiles, dynamic smoke, fire, and magical explosions, 4K digital painting."
            )
        },
        {
            "index": 4, "range": (339, 350),
            "title": ["ABSOLUTE HEGEMONY", "DYNASTIC SUBJUGATION"],
            "fallback_color": (16, 14, 22),
            "prompt": (
                "Panoramic view of a conquered imperial capital at dawn beneath a pale crimson sky, "
                "ruined palace spires and fallen dynastic banners beneath a colossal dark Gothic spire, "
                "a solitary sovereign standing atop the central palace rampart looking down upon surrendered lands, epic concept art, 4K."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
