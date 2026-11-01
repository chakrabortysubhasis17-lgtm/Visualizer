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


BUILD_DIR = "build_beast_taming_infinite_respawn_271_305"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters (Chapters 271 - 305 Marathon)
    "novel_slug": "beast-taming-infinite-respawn",
    "start_url": "https://freewebnovel.com/novel/beast-taming-my-beasts-grind-die-and-respawn/chapter-271",
    "start_chapter": 271,
    "end_chapter": 305,
    "is_start": False,
    "default_topic": (
        "Beast Taming: My Beasts Grind, Die, and Respawn / LitRPG / Progression Fantasy / "
        "Infinite Beast Respawn Talent / Mythical Bloodline Evolution / Secret Realm Expeditions / "
        "Divine Beast Contracts / Beast Master League Tournament"
    ),

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Premise Hook
    "intro_hook": "Pushing past fatal trials through infinite resurrection cycles, our beast tamer drives his contract beasts into transcendent, mythic-tier evolutions.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_beast_taming_infinite_respawn_271_305.mp3",
    "final_video": "final_beast_taming_infinite_respawn_271_305.mp4",
    "cover_image": "cover_beast_taming_infinite_respawn_271_305.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_infinite_respawn_271_305.txt",
    "subtitles_file": "subtitles_beast_taming_infinite_respawn_271_305.srt",
    "payload_file": "youtube_upload_payload_beast_taming_infinite_respawn_271_305.json",

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
    "video_title": "Beast Taming: My Beasts Grind, Die, and Respawn | Ch 271 - 305 Full Audiobook Marathon",
    "privacy_status": "unlisted",
    "tags": [
        "Beast Taming My Beasts Grind Die and Respawn", "Beast Taming Audiobook",
        "My Beasts Grind Die and Respawn", "LitRPG Audiobook", "Progression Fantasy",
        "Beast Tamer", "Infinite Respawn", "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "We plunge into Chapters 271 to 305 of 'Beast Taming: My Beasts Grind, Die, and Respawn'.\n\n"
        "Armed with the heaven-defying talent that turns every defeat into accelerated training, our beast master "
        "conquers perilous secret realms, triggers mythical sovereign evolutions, and commands an immortal legion of beasts "
        "that grow deadlier with every cycle of death and rebirth.\n\n"
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
        "#BeastTaming #MyBeastsGrindDieAndRespawn #LitRPG #ProgressionFantasy #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks partitioned across Chapters 271 to 305
    "blocks": [
        {
            "index": 1, "range": (271, 279),
            "title": ["RESURRECTION TEMPERING", "MYTHIC BLOODLINE EMERGENCE"],
            "fallback_color": (18, 14, 28),
            "prompt": (
                "A young powerful beast tamer standing inside an ancient runic trial chamber with glowing crimson and golden summoning circles, "
                "a colossal mythical beast rising from shimmering golden resurrection flames with wings of crackling azure thunder, "
                "dark epic fantasy concept art, highly detailed, dramatic lighting, 4K digital painting."
            )
        },
        {
            "index": 2, "range": (280, 288),
            "title": ["SECRET REALM INVASION", "DEADLY CLASH"],
            "fallback_color": (12, 24, 30),
            "prompt": (
                "Epic fantasy battlefield clash deep inside a subterranean glowing crystalline cavern, "
                "a sovereign armored beast master commanding titanic elemental chimera beasts unleashing beams of radiant energy "
                "against hordes of corrupted abyssal beasts, volumetric smoke, glowing embers, masterpiece 4K digital illustration."
            )
        },
        {
            "index": 3, "range": (289, 297),
            "title": ["COVENANT TRANSCENDENCE", "ANCIENT SHRINE"],
            "fallback_color": (14, 28, 18),
            "prompt": (
                "Ancient mystical stone temple shrine overgrown with luminescent emerald flora and celestial jade statues, "
                "a beast tamer gently bonding with an ethereal celestial spirit fox with multiple glowing tails, "
                "soft atmospheric fog, golden divine particle lights, deep fantasy environment concept art, 4K resolution."
            )
        },
        {
            "index": 4, "range": (298, 305),
            "title": ["IMMORTAL LEGION", "SOVEREIGN TRIUMPH"],
            "fallback_color": (28, 16, 24),
            "prompt": (
                "Dramatic panoramic vista overlooking a high-altitude mountain tournament arena at twilight, "
                "a confident beast master standing tall atop a massive floating dragon-like sovereign beast, "
                "surrounded by an armada of summoned mythical creatures bathed in golden sunset and purple energy rifts, "
                "cinematic composition, photorealistic fantasy masterpiece, 4K wallpaper."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
