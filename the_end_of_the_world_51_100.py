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

BUILD_DIR = "build_end_of_world_billion_points_51_100"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "the-end-of-the-world-my-woman-is-a-billion-points-stronger",
    "start_url": "https://mtl-novel.com/novel/the-end-of-the-world-my-woman-is-a-billion-points-stronger/chapter-51-killing-people-more-cruel-than-men/",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "Doomsday Apocalypse / Reborn Sovereign / Overpowered Heroine",

    # Concurrency Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-GuyNeural",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_end_of_world_billion_points_51_100.mp3",
    "final_video": "final_end_of_world_billion_points_51_100.mp4",
    "cover_image": "cover_end_of_world_billion_points_51_100.jpg",
    "timestamps_file": "youtube_timestamps_end_of_world_billion_points_51_100.txt",
    "subtitles_file": "subtitles_end_of_world_billion_points_51_100.srt",
    "payload_file": "youtube_upload_payload_end_of_world_billion_points_51_100.json",

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
    "video_title": "Reborn Before Doomsday: My Woman is a Billion Points Stronger | Ch 51 - 100 Full Audio Novel Marathon",
    "privacy_status": "unlisted",
    "tags": [
        "Reborn Before Doomsday", "The End of the World My Woman is a Billion Points Stronger",
        "Doomsday Audiobook", "Apocalypse Audiobook", "Overpowered Heroine", "LitRPG Audiobook",
        "Progression Fantasy", "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the full 50-chapter audio novel marathon of 'Reborn Before Doomsday: My Woman is a Billion Points Stronger' (Chapters 51 to 100).\n\n"
        "Follow the ruthless survival journey as the apocalyptic wasteland erupts into chaos. Witness lethal clashes against bandit factions, "
        "relentless mutant horde assaults, base fortification, and the terrifying exponential power spikes of the peerless female lead.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic mastering, vocal presence).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited, dramatized fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#RebornBeforeDoomsday #DoomsdayAudiobook #ApocalypseNovel #ProgressionFantasy #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 51 to 100 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (51, 60),
            "title": ["RUTHLESS PURGE", "BLOOD-SOAKED RUINS"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic 3D post-apocalyptic scene of an icy cold, lethal heroine standing amidst crumbling city ruins after wiping out a ruthless raider gang, "
                "glowing blade dripping with blue mana energy, dark stormy apocalyptic sky with purple lightning, gritty concrete textures, 4K rendering."
            )
        },
        {
            "index": 2, "range": (61, 70),
            "title": ["MUTANT HORDE ASSAULT", "FORTRESS DEFENSE"],
            "fallback_color": (30, 20, 15),
            "prompt": (
                "Cinematic wide angle action shot of an armored apocalyptic base rampart, heavily fortified defensive turrets firing into a monstrous horde "
                "of mutant zombies and colossal infected beasts climbing up shattered barricades, muzzle flashes, volumetric smoke, high tension, ultra-detailed."
            )
        },
        {
            "index": 3, "range": (71, 80),
            "title": ["AWAKENED POWER", "BILLION-POINT REACTION"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "Cinematic dark fantasy scene of a young reborn leader and his overpowered female companion surrounded by swirling celestial energy rings "
                "and floating holographic system attribute screens, shockwaves cracking the concrete highway beneath their boots, dramatic lighting, 4K."
            )
        },
        {
            "index": 4, "range": (81, 90),
            "title": ["DOOMSDAY LEVIATHAN", "ABYSSAL INFECTION"],
            "fallback_color": (20, 30, 25),
            "prompt": (
                "Cinematic high-impact apocalyptic encounter with a colossal mutated behemoth looming through toxic neon green fog in a flooded metropolis crater, "
                "heroic duo charging forward with radiant energy weapons drawn, epic scale, photorealistic textures."
            )
        },
        {
            "index": 5, "range": (91, 100),
            "title": ["SOVEREIGN OVERLORD", "THE NEW SANCTUARY"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic wide view of a pristine, high-tech fortress city built atop a mountain overlook at sunset, the sovereign protagonist and his celestial partner "
                "standing side by side looking over their thriving post-apocalyptic sanctuary, warm god rays cutting through storm clouds, 4K resolution."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))