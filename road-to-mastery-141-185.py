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

# Seamless credential resolution across single and multi-account configurations
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

def purge_corrupt_cache(build_dir: str):
    """Purges placeholder dummy files from earlier connection dropouts."""
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
                if len(rows) < 8 or any("Exposition details continue" in r.get("text", "") for r in rows):
                    os.remove(fpath)
                    removed += 1
            except Exception:
                try:
                    os.remove(fpath)
                    removed += 1
                except OSError:
                    pass
    if removed > 0:
        print(f"[Pre-Flight Cleanup] [✓] Purged {removed} placeholder cache files to guarantee clean scraping.", flush=True)

BUILD_DIR = "build_road_to_mastery_141_185"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "road-to-mastery-a-litrpg-apocalypse",
    "start_url": "https://freewebnovel.com/novel/road-to-mastery-a-litrpg-apocalypse/chapter-141",
    "start_chapter": 141,
    "end_chapter": 185,
    "default_topic": "Road To Mastery",

    # Concurrency Settings
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_road_to_mastery_141_185.mp3",
    "final_video": "final_road_to_mastery_141_185.mp4",
    "cover_image": "cover_road_to_mastery_141_185.jpg",
    "timestamps_file": "youtube_timestamps_road_to_mastery_141_185.txt",
    "subtitles_file": "subtitles_road_to_mastery_141_185.srt",
    "payload_file": "youtube_upload_payload_road_to_mastery_141_185.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "SYSTEM APOCALYPSE SURVIVAL & CLASS EVOLUTION! [Ch 141-185] | LitRPG Progression Fantasy Audiobook",
    "tags": [
        "Road to Mastery", "A LitRPG Apocalypse", "Progression Fantasy",
        "LitRPG Audiobook", "System Apocalypse", "Audiobook Marathon", "Full Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Navigating the ruthless trials of a system-integrated apocalypse, our survivor pushes his skills to absolute mastery!\n\n"
        "Facing monstrous regional bosses, hostile faction raids, and escalating dungeon tiers, every combat encounter refines his "
        "class attributes and unlocks elite evolutionary milestones. Strategy, grit, and unyielding progression are the only keys to survival.\n\n"
        "Welcome to Chapters 141 to 185 of 'Road to Mastery: A LitRPG Apocalypse' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 141: Regional Sector Expansion: Entering the Dangerous Wild Zones\n"
        "• Ch 147: Skill Master-Level Breakthrough: Unlocking Unique Passive Perks\n"
        "• Ch 154: Hostile Faction Incursion: Neutralizing Territory Raiders\n"
        "• Ch 161: Elite Dungeon Raid: Conquering the Twisted Labyrinth\n"
        "• Ch 168: Core Attribute Evolution: Pushing Stats Past Mortal Limits\n"
        "• Ch 175: Boss Subjugation: Securing Rare System Class Blueprints\n"
        "• Ch 180: Alliance Negotiations: Establishing Safe Settlement Pacts\n"
        "• Ch 185: Preparing for the Continental Zone Trials\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#RoadToMastery #LitRPG #SystemApocalypse #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (141, 145),
            "title": ["WILD ZONE EXPEDITION", "SECTOR CROSSING"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D post-apocalyptic fantasy portrait of a hardened LitRPG survivor scanning a ruined overgrown highway through tactical optics, "
                "calm focused eyes, wearing high-tech reinforced combat armor with glowing system interface displays. Set under an overcast twilight sky, "
                "crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (146, 150),
            "title": ["SKILL MASTERY", "PASSIVE AWAKENING"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D post-apocalyptic portrait of the survivor as golden system notification text boxes float around his hands, "
                "triumphant focused expression, subtle kinetic energy aura wrapping his weapon. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (151, 155),
            "title": ["RAIDER SKIRMISH", "TERRITORY DEFENSE"],
            "fallback_color": (35, 15, 25),
            "prompt": (
                "Cinematic 3D post-apocalyptic portrait of the survivor engaging hostile faction raiders in a ruined urban alleyway, "
                "dynamic combat ready posture, muzzle flashes and blue mana sparks illuminating the scene. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (156, 160),
            "title": ["DUNGEON GATE", "LABYRINTH THRESHOLD"],
            "fallback_color": (15, 30, 35),
            "prompt": (
                "Cinematic 3D post-apocalyptic portrait of the survivor standing before a towering swirling purple dungeon gate pulsing with alien energy, "
                "unwavering resolute gaze, armored gear reflecting portal light. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (161, 165),
            "title": ["TWISTED LABYRINTH", "TRAP EVASION"],
            "fallback_color": (30, 20, 40),
            "prompt": (
                "Cinematic 3D post-apocalyptic portrait of the survivor dodging narrow spike traps inside a gothic stone dungeon corridor, "
                "agile tactical movement, glowing magical torchlight casting deep shadows. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (166, 170),
            "title": ["STAT BREAKTHROUGH", "ATTRIBUTE SURGE"],
            "fallback_color": (25, 30, 45),
            "prompt": (
                "Cinematic 3D post-apocalyptic portrait of the survivor experiencing a profound physical evolution as blue system data streams flow into his veins, "
                "intense powerful focus. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (171, 175),
            "title": ["ZONE BOSS", "APEX PREDATOR"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D post-apocalyptic portrait of the survivor clashing blade-to-claw against a massive mutated apex monster boss, "
                "ferocious combat determination, brilliant skill activation flashes lighting the cavern. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (176, 180),
            "title": ["SETTLEMENT PACT", "ALLIANCE FORGED"],
            "fallback_color": (20, 30, 35),
            "prompt": (
                "Cinematic 3D post-apocalyptic portrait of the survivor shaking hands with a regional settlement leader inside a fortified command bunker, "
                "diplomatic confident posture, glowing holographic map tables background. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (181, 183),
            "title": ["WAR ROOM STRATEGY", "PREPARING FOR TRIALS"],
            "fallback_color": (20, 20, 45),
            "prompt": (
                "Cinematic 3D post-apocalyptic portrait of the survivor analyzing strategic zone maps and system threat alerts, "
                "sharp analytical focus, ambient blue computer monitor lighting. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (184, 185),
            "title": ["ZONE TRIALS", "HORIZON ASCENT"],
            "fallback_color": (15, 15, 35),
            "prompt": (
                "Cinematic 3D post-apocalyptic portrait of the victorious survivor gazing toward distant continental mountain peaks under a brilliant sunrise, "
                "serene resolute mastery expression, fully upgraded armor gleaming. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
