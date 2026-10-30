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


BUILD_DIR = "build_sss_goddess_summon_351_400"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "starting-with-an-sss-rank-goddess-summon",
    "start_url": "https://freewebnovel.com/novel/starting-with-an-sss-rank-goddess-summon/chapter-351",
    "start_chapter": 351,
    "end_chapter": 400,
    "default_topic": "Starting With An SSS-Rank Goddess Summon / LitRPG / Fantasy / Overpowered Summoner / Divine Pantheon / Interstellar Realm War",

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook
    "intro_hook": "Commanding a court of peerless SSS-rank goddesses, an unrivaled summoner breaks past dimensional frontiers to challenge the ancient celestial hegemony.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_sss_goddess_summon_351_400.mp3",
    "final_video": "final_sss_goddess_summon_351_400.mp4",
    "cover_image": "cover_sss_goddess_summon_351_400.jpg",
    "timestamps_file": "youtube_timestamps_sss_goddess_summon_351_400.txt",
    "subtitles_file": "subtitles_sss_goddess_summon_351_400.srt",
    "payload_file": "youtube_upload_payload_sss_goddess_summon_351_400.json",

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
    "video_title": "Starting With An SSS-Rank Goddess Summon | Ch 351 - 400 Full Audiobook Marathon | Divine Domain War",
    "privacy_status": "unlisted",
    "tags": [
        "Starting With An SSS Rank Goddess Summon", "SSS Rank Goddess Summon", "Goddess Summon Audiobook",
        "LitRPG Audiobook", "Fantasy Audiobook", "Overpowered Summoner", "Harem Fantasy",
        "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "This episode, we step right back into the story, continuing exactly where we left off in our previous episode of this series.\n\n"
        "Experience 'Starting With An SSS-Rank Goddess Summon' (Chapters 351 to 400) — The Divine Domain War Arc.\n\n"
        "As galactic battlegrounds collide and ancestral gods mobilize their forces, our summoner leads an elite pantheon of "
        "divine goddesses into sovereign territory. Unlocking cosmic-tier fusion arts, boundary-shattering domain armaments, and "
        "mythical evolution matrices, every clash reshapes the balance of the upper realms.\n\n"
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
        "#GoddessSummon #SSSRank #LitRPG #FantasyAudiobook #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks across Chapters 351 to 400 (50 chapters partitioned)
    "blocks": [
        {
            "index": 1, "range": (351, 363),
            "title": ["CELESTIAL CITADEL", "DIVINE SUMMONING GATE"],
            "fallback_color": (20, 16, 28),
            "prompt": (
                "Cinematic high-fantasy divine floating sanctuary above cosmic nebula clouds, "
                "a young commanding summoner channeling a massive multi-layered golden summoning circle, "
                "radiant ethereal goddess figures materializing with flowing crystalline robes and glowing aura blades, 4K digital masterpiece."
            )
        },
        {
            "index": 2, "range": (364, 375),
            "title": ["REALM EXPEDITION", "ANCIENT PANTHEON CLASH"],
            "fallback_color": (28, 14, 20),
            "prompt": (
                "Epic fantasy cosmic battlefield across floating shattered planetary fragments, "
                "a powerful warrior goddess wielding a blazing lance of starlight clashing against an ancient armored shadow titan, "
                "volumetric shockwaves and dynamic golden light particles illuminating space, 4K resolution."
            )
        },
        {
            "index": 3, "range": (376, 387),
            "title": ["DOMAIN FUSION", "SOVEREIGN AWAKENING"],
            "fallback_color": (16, 22, 28),
            "prompt": (
                "Grand temple of cosmic light with towering marble pillars interwoven with glowing starlight runes, "
                "a regal summoner surrounded by ethereal goddess familiars channeling synchronized elemental energy streams, "
                "brilliant cyan and magenta arcane currents spiraling upward, cinematic lighting, 4K digital painting."
            )
        },
        {
            "index": 4, "range": (388, 400),
            "title": ["SUPREME CONQUEROR", "DAWN OF THE CELESTIAL COURT"],
            "fallback_color": (24, 18, 14),
            "prompt": (
                "Panoramic view of a golden astral throne room overlooking an endless galaxy expanse, "
                "the supreme summoner flanked by majestic ascended goddesses with luminous wings and divine regalia, "
                "celestial banners fluttering in stellar winds, authoritative triumphant composition, 4K concept art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
