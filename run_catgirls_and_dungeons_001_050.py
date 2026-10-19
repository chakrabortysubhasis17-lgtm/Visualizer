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

CONFIG = {
    # Credentials (Loaded dynamically from api_credentials.json with env fallback)
    "gemini_api_key": creds.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", ""),
    "cf_account_id": creds.get("cloudflare_account_id") or os.environ.get("CLOUDFLARE_ACCOUNT_ID", ""),
    "cf_api_token": creds.get("cloudflare_api_token") or os.environ.get("CLOUDFLARE_API_TOKEN", ""),

    # Novel & Episode Parameters
    "novel_slug": "catgirls-and-dungeons-yuri",
    "start_url": "https://freewebnovel.com/novel/catgirls-and-dungeons-yuri/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Catgirls and Dungeons",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_catgirls_and_dungeons_001_050",
    "final_audio": "output_catgirls_and_dungeons_001_050.mp3",
    "final_video": "final_catgirls_and_dungeons_001_050.mp4",
    "cover_image": "cover_catgirls_and_dungeons_001_050.jpg",
    "timestamps_file": "youtube_timestamps_catgirls_and_dungeons_001_050.txt",
    "subtitles_file": "subtitles_catgirls_and_dungeons_001_050.srt",
    "payload_file": "youtube_upload_payload_catgirls_and_dungeons_001_050.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "CATGIRLS, DUNGEONS & ADVENTURE! EXPLORING THE MYTHIC LABYRINTH [Ch 1-50] | Fantasy Yuri Audiobook Marathon",
    "tags": [
        "Catgirls and Dungeons", "Yuri Audiobook", "Fantasy Dungeon Crawler",
        "Progression Fantasy", "LitRPG Audiobook", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Stepping into a high-fantasy world filled with treacherous labyrinths, mystical beast-kin, "
        "and thrilling dungeon-crawling escapades!\n\n"
        "Navigating complex dungeon floors alongside spirited catgirl companions, our protagonist uncovers hidden loot chambers, "
        "defeats ferocious dungeon bosses, and builds unbreakable bonds in the face of continuous peril.\n\n"
        "Welcome to Chapters 1 to 50 of 'Catgirls and Dungeons' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 01: Entering the First Labyrinth Layer & Meeting the Catgirl Companions\n"
        "• Ch 07: Clearing the Goblin Lair and Securing Rare Dungeon Loot\n"
        "• Ch 14: Navigating the Crystal Caverns and Defeating the Trap-Master Boss\n"
        "• Ch 21: Establishing the Adventurer Guild Outpost and Upgrading Gear\n"
        "• Ch 28: Investigating the Deep Shadow Ruins: Uncovering Ancient Relics\n"
        "• Ch 35: Surviving the Floor 20 Survival Trial against Beast Hordes\n"
        "• Ch 42: Forging Tactical Team Synergies in High-Difficulty Zones\n"
        "• Ch 50: Conquering the Mid-Tier Labyrinth Boss and Claiming Regional Prestige\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#CatgirlsAndDungeons #YuriAudiobook #FantasyDungeonCrawler #LitRPG #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Streamlined for Zero Generation Failures)
    "blocks": [
        {
            "index": 1, "range": (1, 5),
            "title": ["LABYRINTH ENTRANCE", "FIRST DESCENT"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of an adventurous protagonist standing before a massive glowing stone dungeon gate, confident cheerful smile, "
                "wearing sleek leather explorer armor with magical trinkets. Set inside a torch-lit cavern entrance, "
                "revealing curious catgirl companions with soft ears and tails in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (6, 10),
            "title": ["GOBLIN LAIR", "SECURING RARE LOOT"],
            "fallback_color": (30, 20, 25),
            "prompt": (
                "Cinematic 3D portrait of the protagonist examining a glowing treasure chest, excited triumphant expression, "
                "holding a polished adventurer shortsword. Set inside a rough stone dungeon chamber, "
                "revealing defeated goblin scouts scattered across the floor in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (11, 15),
            "title": ["CRYSTAL CAVERNS", "TRAP-MASTER BOSS"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of the protagonist in agile combat stance, sharp focused gaze, "
                "surrounded by glowing blue stalactites. Set inside a subterranean crystal cave, "
                "revealing a massive stone guardian boss emerging from glowing crystals in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (16, 20),
            "title": ["GUILD OUTPOST", "GEAR UPGRADE"],
            "fallback_color": (25, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of the protagonist resting at a lively tavern table, relaxed satisfied smile, "
                "reviewing guild quest bounties on parchment. Set inside a cozy wooden adventurer guild hall, "
                "revealing bustling merchants and fellow explorers in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (21, 25),
            "title": ["SHADOW RUINS", "ANCIENT RELIC DISCOVERY"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic 3D portrait of the protagonist holding an antique glowing amulet, watchful analytical eyes, "
                "wearing a hooded travel cloak. Set inside crumbling ancient stone ruins covered in ivy, "
                "revealing towering broken pillars under pale moonlight in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (26, 30),
            "title": ["SURVIVAL TRIAL", "BEAST HORDE DEFENSE"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of the protagonist raising a magical barrier staff, fierce resolute expression, "
                "wind whipping her hair. Set across a narrow dungeon bridge, "
                "revealing waves of agile shadow beasts crashing against glowing shields in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (31, 35),
            "title": ["TACTICAL SYNERGY", "PARTY COORDINATION"],
            "fallback_color": (20, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of the protagonist sharing a warm laugh with her catgirl teammates, affectionate joyful expression, "
                "holding a map scroll. Set beside a warm camp fire inside a safe zone alcove, "
                "revealing soft lantern light reflecting off stone walls in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (36, 40),
            "title": ["DEEP LABYRINTH", "NAVIGATING MAZES"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist tracing a glowing path on an enchanted compass, focused analytical gaze, "
                "wearing upgraded mithril armor. Set inside a symmetrical labyrinth corridor lined with magical runes, "
                "revealing mysterious branching archways in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (41, 45),
            "title": ["ELITE ENCOUNTER", "SWIFT VICTORY"],
            "fallback_color": (35, 20, 25),
            "prompt": (
                "Cinematic 3D portrait of the protagonist executing a decisive sword strike, sharp athletic posture, "
                "blade leaving trails of golden light. Set in a spacious subterranean colosseum, "
                "revealing a defeated armored minotaur boss collapsing onto stone tiles in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (46, 50),
            "title": ["MID-TIER BOSS DEFEAT", "REGIONAL PRESTIGE"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of the triumphant party standing atop a conquered dungeon floor peak, proud radiant smiles, "
                "holding glowing victory crests. Set inside a magnificent golden treasury chamber overlooking the labyrinth depths in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
