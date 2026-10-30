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


BUILD_DIR = "build_10000x_reward_multiplier_51_89"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters (Series Finale)
    "novel_slug": "10000x-reward-multiplier-hell-level-kingdom-building",
    "start_url": "https://freewebnovel.com/novel/10000x-reward-multiplier-hell-level-kingdom-building/chapter-51",
    "start_chapter": 51,
    "end_chapter": 89,
    "is_start": False,  # Continuation into Grand Finale
    "default_topic": "10000x Reward Multiplier: Hell-Level Kingdom Building / Grand Finale / Kingdom Building / 10000x Multiplier / Lord Expansion / Supreme Sovereign",

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook (Grand Finale)
    "intro_hook": "Welcome to the grand finale of this series! With the ten-thousand-fold multiplier pushed to its absolute limits, our lord shatters all rival alliances to establish an everlasting supreme dominion.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_10000x_reward_multiplier_51_89.mp3",
    "final_video": "final_10000x_reward_multiplier_51_89.mp4",
    "cover_image": "cover_10000x_reward_multiplier_51_89.jpg",
    "timestamps_file": "youtube_timestamps_10000x_reward_multiplier_51_89.txt",
    "subtitles_file": "subtitles_10000x_reward_multiplier_51_89.srt",
    "payload_file": "youtube_upload_payload_10000x_reward_multiplier_51_89.json",

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
    "video_title": "10,000x Reward Multiplier: Hell-Level Kingdom Building | Ch 51 - 89 (GRAND FINALE) Full Audiobook",
    "privacy_status": "unlisted",
    "tags": [
        "10000x Reward Multiplier", "Hell Level Kingdom Building", "Kingdom Building Finale",
        "Grand Finale Audiobook", "LitRPG Audiobook", "Fantasy Audiobook", "Overpowered Lord",
        "Reward Multiplier", "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Welcome to the GRAND FINALE of '10,000x Reward Multiplier: Hell-Level Kingdom Building' (Chapters 51 to 89)!\n\n"
        "In this final, definitive volume, the ultimate trial begins. With hell-mode conditions reaching maximum severity and "
        "inter-regional lord factions declaring total war, our lord unleashes exponential system multipliers across every divine "
        "armory, fortress defense, and legendary hero. Witness the climactic conclusion to the road of supreme empire building.\n\n"
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
        "#KingdomBuilding #GrandFinale #LitRPG #RewardMultiplier #OverpoweredMC #FantasyAudiobook #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks across Chapters 51 to 89 (39 chapters partitioned)
    "blocks": [
        {
            "index": 1, "range": (51, 60),
            "title": ["EXPONENTIAL MULTIPLIER", "DIVINE TERRITORY EXPANSION"],
            "fallback_color": (22, 18, 12),
            "prompt": (
                "Cinematic high-fantasy kingdom treasury chamber overflowing with massive mounds of glowing enchanted gold coins, "
                "a confident young lord reviewing floating holographic status screens displaying exponential system multipliers, "
                "golden light rays piercing through high vaulted stone arches, volumetric dust particles, 4K digital painting."
            )
        },
        {
            "index": 2, "range": (61, 70),
            "title": ["THE IRON BASTION", "DIVINE RUNIC BARRIER"],
            "fallback_color": (16, 20, 26),
            "prompt": (
                "Massive ancient stone fortress ramparts rapidly reinforcing with glowing blue defensive arcane runes, "
                "hundreds of disciplined elite armored archers taking defensive positions along high battlements overlooking a dark misty valley, "
                "dramatic storm clouds rolling in, cinematic scale, 4K resolution."
            )
        },
        {
            "index": 3, "range": (71, 80),
            "title": ["HELL-MODE CLASH", "THOUSAND-FOLD ARTILLERY"],
            "fallback_color": (28, 14, 16),
            "prompt": (
                "Epic fantasy siege battlefield at twilight, colossal wild monster hordes charging across shattered plains toward a fortified city, "
                "towering magical ballistas and cannons firing volleys of blazing crimson arcane artillery shells, "
                "explosions lighting up the night sky with dramatic smoke and fire trails, 4K masterpiece."
            )
        },
        {
            "index": 4, "range": (81, 89),
            "title": ["THE SUPREME SOVEREIGN", "GRAND FINALE"],
            "fallback_color": (24, 16, 20),
            "prompt": (
                "Panoramic high-angle view of a colossal golden imperial capital at sunrise, "
                "magnificent shining spires and crystalline palaces rising beneath clear skies with divine light pillars, "
                "the supreme lord standing upon a grand ceremonial throne balcony crowned in golden light, victorious majestic finale composition, 4K concept art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
