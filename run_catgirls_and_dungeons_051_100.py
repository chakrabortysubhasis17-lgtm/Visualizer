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
    "start_url": "https://freewebnovel.com/novel/catgirls-and-dungeons-yuri/chapter-51",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "Catgirls and Dungeons",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_catgirls_and_dungeons_051_100",
    "final_audio": "output_catgirls_and_dungeons_051_100.mp3",
    "final_video": "final_catgirls_and_dungeons_051_100.mp4",
    "cover_image": "cover_catgirls_and_dungeons_051_100.jpg",
    "timestamps_file": "youtube_timestamps_catgirls_and_dungeons_051_100.txt",
    "subtitles_file": "subtitles_catgirls_and_dungeons_051_100.srt",
    "payload_file": "youtube_upload_payload_catgirls_and_dungeons_051_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "DEEP ABYSSAL DUNGEON CONQUEST! LEGENDARY CATGIRL PARTY ASCENDS TO THE APEX [Ch 51-100] | Fantasy Yuri Audiobook Marathon",
    "tags": [
        "Catgirls and Dungeons", "Yuri Audiobook", "Fantasy Dungeon Crawler",
        "Progression Fantasy", "LitRPG Audiobook", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Descending into the lethal lower strata of the world's most perilous labyrinths, our intrepid party "
        "faces terrifying floor lords and unearths divine-tier artifacts!\n\n"
        "With teamwork forged through countless battles, intricate magic enchantments, and deepening emotional bonds, "
        "they conquer multi-elemental abyssal zones, outsmart rival mercenary clans, and claim legendary sovereign status.\n\n"
        "Welcome to Chapters 51 to 100 of 'Catgirls and Dungeons' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 051: Descending into the Abyssal Volcanic Strata & Facing Magma Beasts\n"
        "• Ch 058: Unlocking Legendary Enchantment Forges in the Dwarven Under-Realm\n"
        "• Ch 065: Rival Mercenary Ambush: Outsmarting Hostile Guilds in the Labyrinth\n"
        "• Ch 072: The Frozen Glacier Floor: Conquering Elemental Ice Phantoms\n"
        "• Ch 079: Discovering the Mythic Sunken Temple and Ancient Goddess Shrines\n"
        "• Ch 086: Team Bond Deepening: Overcoming Emotional Trials in the Dream Maze\n"
        "• Ch 092: Preparing for the Floor 100 Sovereign Boss Confrontation\n"
        "• Ch 100: Apex Labyrinth Conquerors: Crowning the Ultimate Adventurer Party\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#CatgirlsAndDungeons #YuriAudiobook #FantasyDungeonCrawler #LitRPG #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Streamlined for Zero Generation Failures)
    "blocks": [
        {
            "index": 1, "range": (51, 55),
            "title": ["VOLCANIC STRATA", "MAGMA BEAST ENCOUNTER"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic 3D portrait of the protagonist standing before glowing magma rivers, intense focused expression, "
                "wearing heat-resistant enchanted armor. Set inside a subterranean volcanic cavern, "
                "revealing towering fire elemental beasts emerging from molten lava in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (56, 60),
            "title": ["ENCHANTMENT FORGE", "DWARVEN UNDER-REALM"],
            "fallback_color": (30, 20, 25),
            "prompt": (
                "Cinematic 3D portrait of the protagonist inspecting a glowing enchanted blade, admiring scholarly focus, "
                "surrounded by floating magical sparks. Set inside a majestic underground dwarven smithy, "
                "revealing massive stone hammers and burning furnaces in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3,
            "range": (61, 65),
            "title": ["MERCENARY AMBUSH", "OUTSMARTING RIVALS"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist in tactical combat stance, sharp cold gaze, "
                "holding a glowing defense shield. Set along a narrow labyrinth corridor at shadow-dusk, "
                "revealing rival mercenary scouts retreating in confusion in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (66, 70),
            "title": ["GLACIER FLOOR", "ELEMENTAL ICE PHANTOMS"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of the protagonist breathing visible frosty mist, calm resolute posture, "
                "wearing warm fur-lined exploratory gear. Set inside a vast frozen cavern of glittering blue ice, "
                "revealing floating translucent ice phantoms in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (71, 75),
            "title": ["SUNKEN TEMPLE", "ANCIENT GODDESS SHRINE"],
            "fallback_color": (15, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist touching an ancient glowing stone altar, serene awe-struck expression, "
                "surrounded by gentle aquatic blue light reflections. Set inside a magnificent submerged temple ruin, "
                "revealing giant carved stone statues covered in moss in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (76, 80),
            "title": ["DREAM MAZE", "OVERCOMING EMOTIONAL TRIALS"],
            "fallback_color": (30, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of the protagonist sharing a tender reassuring moment with her catgirl companion, warm affectionate smile, "
                "soft ethereal lighting filtering through mist. Set inside a surreal glowing astral dreamscape, "
                "revealing floating pastel clouds and starlight arches in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (81, 85),
            "title": ["BATTLE PREPARATION", "STRATEGY PLANNING"],
            "fallback_color": (25, 25, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist reviewing detailed dungeon blueprints on a wooden table, sharp analytical focus, "
                "holding a magical quill. Set inside a fortified camp site lit by warm lantern glow, "
                "revealing gear racks and resting party members in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (86, 90),
            "title": ["ABYSSAL ASCENT", "APPROACHING THE APEX"],
            "fallback_color": (20, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of the protagonist looking upward toward a massive glowing portal staircase, determined brave stance, "
                "mithril armor gleaming with magical runes. Set at the base of the final dungeon spire, "
                "revealing swirling golden atmospheric energy fields in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (91, 95),
            "title": ["SOVEREIGN SHOWDOWN", "CLASH WITH THE FLOOR LORD"],
            "fallback_color": (35, 20, 25),
            "prompt": (
                "Cinematic 3D portrait of the protagonist directing a synchronized party attack, fierce commanding posture, "
                "two hands gripping a glowing divine sword. Set inside the colossal final boss sanctum, "
                "revealing a towering mythical floor lord roaring under magical shockwaves in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (96, 100),
            "title": ["APEX CONQUERORS", "LEGENDARY ADVENTURER PARTY"],
            "fallback_color": (20, 20, 55),
            "prompt": (
                "Cinematic 3D portrait of the victorious party standing at the absolute apex of the world labyrinth, triumphant joyous smiles, "
                "wearing legendary sovereign crowns and gear. Set upon the grand surface balcony overlooking the entire realm beneath a brilliant sunrise sky in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
