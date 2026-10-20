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

BUILD_DIR = "build_catgirls_and_dungeons_151_200"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "catgirls-and-dungeons-yuri",
    "start_url": "https://freewebnovel.com/novel/catgirls-and-dungeons-yuri/chapter-151",
    "start_chapter": 151,
    "end_chapter": 200,
    "default_topic": "Catgirls and Dungeons",

    # Concurrency Settings
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_catgirls_and_dungeons_151_200.mp3",
    "final_video": "final_catgirls_and_dungeons_151_200.mp4",
    "cover_image": "cover_catgirls_and_dungeons_151_200.jpg",
    "timestamps_file": "youtube_timestamps_catgirls_and_dungeons_151_200.txt",
    "subtitles_file": "subtitles_catgirls_and_dungeons_151_200.srt",
    "payload_file": "youtube_upload_payload_catgirls_and_dungeons_151_200.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "DEEPER DUNGEON EXPEDITION & CATGIRL BONDING! [Ch 151-200] | Yuri Fantasy LitRPG Audiobook Marathon",
    "tags": [
        "Catgirls and Dungeons", "Yuri Audiobook", "Progression Fantasy", "Dungeon Crawler",
        "LitRPG Audiobook", "System Audiobook", "Audiobook Marathon", "Full Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Venture deeper into perilous labyrinth floors where dangerous traps and rich treasures await!\n\n"
        "As the party expands their dungeon-clearing exploits, intimate moments, tactical teamwork, and heartwarming "
        "yuri romance bloom amidst the monster hordes. Facing rare boss encounters and unlocking specialized class progressions, "
        "the bonds between the companions grow unbreakable.\n\n"
        "Welcome to Chapters 151 to 200 of 'Catgirls and Dungeons (Yuri)' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 151: Mid-Tier Labyrinth Descent: Mapping the Crystal Caverns\n"
        "• Ch 158: Catgirl Companion Awakening: Unlocking Dual-Wield Agility Stats\n"
        "• Ch 165: Dungeon Merchant Rendezvous: Rare Artifact Procurement\n"
        "• Ch 172: Moonlight Campfire Confessions: Deepening Emotional Bonds\n"
        "• Ch 179: Floor Guardian Subjugation: Overcoming the Iron Golem Surge\n"
        "• Ch 186: Secret Chamber Discovery: Ancient Relics and Hidden Lore\n"
        "• Ch 193: Guild Rank Up Examination: Proving Combat Mastery\n"
        "• Ch 200: Preparing for the Deep Floor Incursion\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#CatgirlsAndDungeons #YuriAudiobook #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (151, 155),
            "title": ["CRYSTAL CAVERNS", "LABYRINTH DESCENT"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D fantasy portrait of a brave adventurer explorer and a cute catgirl companion holding glowing magical torches, "
                "alert expressions, wearing stylish leather dungeon exploration gear. Set inside a vast subterranean crystal cavern filled with glowing blue mineral pillars, "
                "crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (156, 160),
            "title": ["AGILITY TRAINING", "BLADE SPARK"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D fantasy portrait of a nimble catgirl warrior practicing rapid dagger strikes with neon-blue energy trails, "
                "focused playful expression, cat ears twitching. Set in a stone dungeon training room lit by wall sconces, "
                "crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (161, 165),
            "title": ["DUNGEON MARKET", "ARTIFACT HUNT"],
            "fallback_color": (40, 25, 15),
            "prompt": (
                "Cinematic 3D fantasy portrait of the party examining mystical glowing trinkets at a shadowy merchant booth, "
                "curious excited expressions, colorful magical lantern lighting. Set within a bustling underground adventurer trading outpost, "
                "crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (166, 170),
            "title": ["CAMPFIRE TENDERNESS", "MOONLIGHT BONDS"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D fantasy portrait of two female companions sharing a warm tender embrace near a crackling campfire, "
                "affectionate loving gazes, soft amber fire glow illuminating their faces. Set inside a safe-zone dungeon chamber at night, "
                "crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (171, 175),
            "title": ["TRAP DISARMAMENT", "PRECISION TIMING"],
            "fallback_color": (15, 30, 35),
            "prompt": (
                "Cinematic 3D fantasy portrait of a focused adventurer kneeling to disarm a complex magical pressure trap, intense concentration, "
                "faint red warning light illuminating the floor tiles. Set in a narrow dungeon corridor lined with ancient stone statues, "
                "crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (176, 180),
            "title": ["IRON GOLEM", "BOSS SHOWDOWN"],
            "fallback_color": (35, 15, 40),
            "prompt": (
                "Cinematic 3D fantasy portrait of the party unleashing synchronized magic spells against a towering runic automaton boss, "
                "fierce determined expressions, brilliant violet and gold magic circles flashing in the air. Set in a massive stone boss chamber, "
                "crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (181, 185),
            "title": ["SECRET VAULT", "ANCIENT RELICS"],
            "fallback_color": (20, 20, 45),
            "prompt": (
                "Cinematic 3D fantasy portrait of companions discovering a hidden treasury chest overflowing with glowing gold and magical tomes, "
                "joyful amazed smiles, shafts of golden light piercing through cracked stone ceilings. Set in a forgotten subterranean vault, "
                "crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (186, 190),
            "title": ["GUILD EVALUATION", "RANK ASCENSION"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D fantasy portrait of the adventurer receiving a high-ranking guild insignia badge from an approving guild master, "
                "proud satisfied posture, grand wooden guild hall background. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (191, 195),
            "title": ["HEALING SPRINGS", "REJUVENATION"],
            "fallback_color": (25, 20, 50),
            "prompt": (
                "Cinematic 3D fantasy portrait of party members resting near a magical subterranean hot spring, relaxed peaceful expressions, "
                "mist rising from sparkling turquoise waters under glowing ceiling moss. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (196, 200),
            "title": ["DEEP FLOOR PREPARATION", "READY FOR WAR"],
            "fallback_color": (20, 15, 45),
            "prompt": (
                "Cinematic 3D fantasy portrait of the fully-equipped adventurer party standing united before a massive iron dungeon gate, "
                "unwavering resolute expressions, magical weapons gleaming under torchlight. Set at the threshold of the abyss, "
                "crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
