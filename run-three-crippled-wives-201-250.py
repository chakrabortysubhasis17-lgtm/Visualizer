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

BUILD_DIR = "build_three_crippled_wives_201_250"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "investing-in-my-three-crippled-wives-get-10000x-times-return",
    "start_url": "https://freewebnovel.com/novel/investing-in-my-three-crippled-wives-get-10000x-times-return/chapter-201",
    "start_chapter": 201,
    "end_chapter": 250,
    "default_topic": "Urban Fantasy / 10000x Investment System / Heroine Awakening",

    # Concurrency Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-GuyNeural",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_three_crippled_wives_201_250.mp3",
    "final_video": "final_three_crippled_wives_201_250.mp4",
    "cover_image": "cover_three_crippled_wives_201_250.jpg",
    "timestamps_file": "youtube_timestamps_three_crippled_wives_201_250.txt",
    "subtitles_file": "subtitles_three_crippled_wives_201_250.srt",
    "payload_file": "youtube_upload_payload_three_crippled_wives_201_250.json",

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
    "video_title": "Investing in My Three Crippled Wives, Get 10,000x Times Return | Ch 201 - 250 Full Audio Novel Marathon",
    "privacy_status": "unlisted",
    "tags": [
        "Investing in My Three Crippled Wives", "10000x Return System", "Dexter Ashford",
        "Urban Cultivation", "System Audiobook", "Overpowered MC", "Audiobook Marathon",
        "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the full 50-chapter audio novel marathon of 'Investing in My Three Crippled Wives, Get 10,000x Times Return' (Chapters 201 to 250).\n\n"
        "Follow Dexter as every ounce of care, protection, and resource invested into his three heroines yields exponential god-tier returns, "
        "shattering the arrogant noble families and rewriting the balance of power across the metropolis.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic mastering, vocal presence).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited, dramatized fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#InvestingInMyThreeCrippledWives #SystemAudiobook #ProgressionFantasy #WebNovel #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 201 to 250 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (201, 210),
            "title": ["SACRIFICE & 10000X RETURNS", "DOMESTIC RECOVERY"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D fantasy scene of a sharp-eyed young man in modern street clothes serving nutrient-infused glowing elixir to three aristocratic women "
                "recovering inside a warm sunlit suburban living room. Golden system calculation runes floating faintly in the air, rich warm ambient lighting, "
                "subtle magical particles, photorealistic 4K textures."
            )
        },
        {
            "index": 2, "range": (211, 220),
            "title": ["SPECTRAL ARMS", "MANA RECONSTITUTION"],
            "fallback_color": (35, 15, 25),
            "prompt": (
                "Cinematic dark fantasy portrait of a wheelchair-bound young woman with intense crimson eyes manifesting dual translucent glowing orange spectral mana arms, "
                "intricate magical energy weaving through the room as mana currents swirl around her shoulders. Moody modern interior background, cinematic rim lighting, ultra-detailed."
            )
        },
        {
            "index": 3, "range": (221, 230),
            "title": ["URBAN AMBUSH", "FLAME DEMON AWAKENING"],
            "fallback_color": (40, 15, 10),
            "prompt": (
                "Cinematic action shot in a dark rain-soaked cyberpunk alleyway, a young warrior erupting with royal-grade crimson demon fire, "
                "stepping between masked noble assassins and an armored convoy. Steam rising from wet asphalt, blinding fire light reflections, high-speed dynamic combat pose."
            )
        },
        {
            "index": 4, "range": (231, 240),
            "title": ["GATE INVASION", "DEVASTATING COUNTERATTACK"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic wide angle fantasy scene of an urban gate breach at dusk, high-ranking dungeon monsters invading cracked city streets as an awakened hero "
                "unleashes an expansive golden celestial shockwave, pulverizing armored beasts and protecting defensive barricades. Debris flying, volumetric lighting, epic scale."
            )
        },
        {
            "index": 5, "range": (241, 250),
            "title": ["S-RANK ASCENSION", "SOVEREIGN TRIUMPH"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic wide view from the terrace of a sleek high-rise penthouse overlooking a sprawling neon fantasy metropolis at dawn, "
                "a young powerhouse surrounded by his empowered heroines radiating pristine divine auras, commanding authority, triumphant sunrise god rays, 4K rendering."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
