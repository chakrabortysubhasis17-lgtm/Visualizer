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


BUILD_DIR = "build_catgirls_and_dungeons_251_284_finale"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Grand Finale Parameters (Chapters 251 - 284)
    "novel_slug": "catgirls-and-dungeons",
    "start_url": "https://freewebnovel.com/novel/catgirls-and-dungeons-yuri/chapter-251",
    "start_chapter": 251,
    "end_chapter": 284,
    "is_start": False,
    # Explicitly locks first-person narrator identity to Felicia (Female) to avoid generic male protagonist fallback
    "default_topic": (
        "Catgirls and Dungeons / Yuri / Grand Finale / "
        "First-Person Protagonist is Felicia (Female, catgirl, en-US-AriaNeural) / "
        "Eris (Female, partner, en-US-AriaNeural) / Dungeon Master Core / Final Resolution"
    ),

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook
    "intro_hook": "Reaching the absolute heart of the dungeon labyrinth, Felicia and Eris confront the core sovereign and cement their eternal bond in the series finale.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_catgirls_and_dungeons_251_284_finale.mp3",
    "final_video": "final_catgirls_and_dungeons_251_284_finale.mp4",
    "cover_image": "cover_catgirls_and_dungeons_251_284_finale.jpg",
    "timestamps_file": "youtube_timestamps_catgirls_and_dungeons_251_284_finale.txt",
    "subtitles_file": "subtitles_catgirls_and_dungeons_251_284_finale.srt",
    "payload_file": "youtube_upload_payload_catgirls_and_dungeons_251_284_finale.json",

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
    "video_title": "Catgirls and Dungeons (Yuri) | Ch 251 - 284 GRAND FINALE Full Audiobook Marathon",
    "privacy_status": "unlisted",
    "tags": [
        "Catgirls and Dungeons", "Catgirls and Dungeons Yuri", "Catgirls and Dungeons Finale",
        "Catgirls and Dungeons Audiobook", "Yuri Audiobook", "Fantasy Yuri", "Dungeon Crawler",
        "Audiobook Marathon", "Web Novel Audiobook", "FreeWebNovel", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "This is the GRAND FINALE of 'Catgirls and Dungeons (Yuri)', covering Chapters 251 to 284.\n\n"
        "Together at the bottommost abyss of the labyrinth, Felicia and Eris stake everything to break the master seals, "
        "protect their cherished home, and forge a forever together. Every mystery unravels, the deepest feelings surface, "
        "and our duo steps forward into the dawn of their newly won life.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "🎙️ NARRATION: en-US-ChristopherNeural (Deep Cinematic Baritone).\n"
        "🎼 SOUNDSCAPE: Low-Volume Dynamic BGM Beds (-27 dB) + Context SFX.\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audio presentation is an edited fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#CatgirlsAndDungeons #Yuri #FantasyAudiobook #GrandFinale #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks partitioned across Chapters 251 to 284
    "blocks": [
        {
            "index": 1, "range": (251, 259),
            "title": ["THE LABYRINTH ABYSS", "PRIMORDIAL REVELATION"],
            "fallback_color": (16, 20, 30),
            "prompt": (
                "Two cute anime catgirl adventurers, one with silver-white cat ears and tail in ornate leather armor, "
                "standing shoulder-to-shoulder before a colossal glowing azure arcane dungeon gate deep subterranean, "
                "surrounded by ancient glowing runes, crystalline stalactites, soft ethereal bioluminescent lighting, "
                "masterpiece anime fantasy concept art, 4K digital painting."
            )
        },
        {
            "index": 2, "range": (260, 268),
            "title": ["COVENANT CLASH", "UNSHAKABLE RESOLVE"],
            "fallback_color": (32, 14, 24),
            "prompt": (
                "Dramatic fantasy anime battle inside an ancient ruined grand cathedral chamber, two brave catgirl heroines "
                "combining magical crimson and gold elemental aura barriers against towering shadowy dungeon monoliths, "
                "dynamic kinetic angles, particle sparks, intense lighting, masterpiece 4K digital illustration."
            )
        },
        {
            "index": 3, "range": (269, 276),
            "title": ["ETERNAL SANCTUARY", "THE HEART'S PROMISE"],
            "fallback_color": (28, 18, 14),
            "prompt": (
                "Warm emotional scene between two beautiful anime catgirls holding hands tenderly at twilight, "
                "their tails gently intertwined, sitting on a balcony overlooking a peaceful gothic mansion estate gardens, "
                "autumn red flower petals blowing in the soft breeze, gorgeous sunset sky, romantic cozy fantasy, 4K resolution."
            )
        },
        {
            "index": 4, "range": (277, 284),
            "title": ["NEW DAWN", "TOGETHER ALWAYS"],
            "fallback_color": (22, 28, 20),
            "prompt": (
                "Wholesome anime grand finale scene, two smiling catgirl heroines standing together happily on a sunlit hillside path, "
                "surrounded by cute loyal homunculi maids waving in the background outside a welcoming grand estate manor, "
                "clear blue sky, golden morning light, vibrant colors, celebratory atmosphere, masterpiece 4K wallpaper."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
