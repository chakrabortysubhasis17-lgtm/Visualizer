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
    "start_url": "https://freewebnovel.com/novel/catgirls-and-dungeons-yuri/chapter-101",
    "start_chapter": 101,
    "end_chapter": 150,
    "default_topic": "Catgirls and Dungeons",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,

    # Filepaths & Outputs
    "build_dir": "build_catgirls_and_dungeons_101_150",
    "final_audio": "output_catgirls_and_dungeons_101_150.mp3",
    "final_video": "final_catgirls_and_dungeons_101_150.mp4",
    "cover_image": "cover_catgirls_and_dungeons_101_150.jpg",
    "timestamps_file": "youtube_timestamps_catgirls_and_dungeons_101_150.txt",
    "subtitles_file": "subtitles_catgirls_and_dungeons_101_150.srt",
    "payload_file": "youtube_upload_payload_catgirls_and_dungeons_101_150.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "MYTHIC CONTINENTAL LABYRINTH EXPEDITION! CATGIRL S-RANK GUILD CONQUEST [Ch 101-150] | Fantasy Yuri Audiobook Marathon",
    "tags": [
        "Catgirls and Dungeons", "Yuri Audiobook", "Fantasy Dungeon Crawler",
        "Progression Fantasy", "LitRPG Audiobook", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Venturing past the boundaries of the known empire, our intrepid adventurer party enters the legendary "
        "Continental World Tree Labyrinths!\n\n"
        "With their S-Rank guild status secured and combat synergy sharpened to perfection, our protagonist and her beloved "
        "catgirl companions confront celestial guardian automatons, untamed elemental dragon nests, and forgotten ancient pantheon vaults. "
        "Deepening their emotional bonds and mastering forbidden dual-casting arts, they protect their guild haven from aristocratic intrigue "
        "and claim the sacred fruits of the World Labyrinth.\n\n"
        "Welcome to Chapters 101 to 150 of 'Catgirls and Dungeons' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 101: Entering the World Tree Roots: The Untamed Ancient Flora Strata\n"
        "• Ch 107: Celestial Golem Colosseum: Unlocking Ancient Core Engineering Secrets\n"
        "• Ch 114: Taming the Emerald Forest Dragon: Securing the Guild Airship Pass\n"
        "• Ch 121: Night at the Treehouse Haven: Intimate Reflections and Mutual Vows\n"
        "• Ch 128: Aristocratic Cartel Infiltration: Exposing Corrupt Noble Guild Contracts\n"
        "• Ch 135: The Submerged Mirror Lake Trial: Conquering Illusionary Phantoms\n"
        "• Ch 142: Dual Resonance Spellcasting: Harmonizing Blade Arts with Feline Agility\n"
        "• Ch 150: Supreme World Tree Apex Reached: Standing as the Continent's Premier Vanguard\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#CatgirlsAndDungeons #YuriAudiobook #FantasyDungeonCrawler #LitRPG #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Streamlined for Zero Generation Failures)
    "blocks": [
        {
            "index": 1, "range": (101, 105),
            "title": ["WORLD TREE ROOTS", "UNEXPLORED STRATA"],
            "fallback_color": (15, 30, 20),
            "prompt": (
                "Cinematic 3D portrait of the adventurous protagonist gazing up at colossal bioluminescent tree roots, confident bright smile, "
                "wearing upgraded enchanted leather armor with silver buckles. Set inside a vast subterranean forest cavern filled with glowing green spores, "
                "revealing playful catgirl companions with soft feline ears and twirling tails in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (106, 110),
            "title": ["CELESTIAL GOLEM", "CORE EXTRACTION"],
            "fallback_color": (30, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of the protagonist inspecting a hovering golden core matrix, sharp analytical focus, "
                "holding an enchanted mithril shortsword. Set in an ancient marble courtyard surrounded by overgrown vines, "
                "revealing a defeated celestial stone golem resting against shattered pillars in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (111, 115),
            "title": ["EMERALD DRAGON", "CANOPY EXPEDITION"],
            "fallback_color": (20, 35, 25),
            "prompt": (
                "Cinematic 3D portrait of the protagonist standing atop a high branch terrace, fearless noble posture, "
                "wind blowing through her hair. Set high in the green canopy under bright skybeams, "
                "revealing a friendly emerald feathered drake perched calmly in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (116, 120),
            "title": ["TREEHOUSE HAVEN", "TENDER BONDS"],
            "fallback_color": (35, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of the protagonist sharing a gentle smile with her catgirl partner, warm affectionate gaze, "
                "holding a warm cup of herbal tea. Set inside a cozy wooden treehouse sanctuary lit by warm lantern glow, "
                "revealing a comfortable hammock and maps scattered across a rustic desk in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (121, 125),
            "title": ["CARTEL CLASH", "EXPOSING THE INTRIGUE"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist holding a signed gold-leaf guild document, mocking cool smirk, "
                "eyes sharp and vigilant. Set inside an opulent stone guild hall under chandelier light, "
                "revealing defeated rival mercenary negotiators lowering their heads in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (126, 130),
            "title": ["MIRROR LAKE", "ILLUSION SHATTER"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of the protagonist pointing her blade toward a crystalline water surface, resolute clear eyes, "
                "surrounded by ripples of azure mana light. Set inside a glowing underwater cavern dome, "
                "revealing shimmering mirror phantoms dissolving into light particles in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (131, 135),
            "title": ["AIRSHIP VOYAGE", "ABOVE THE CLOUDS"],
            "fallback_color": (20, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of the protagonist leaning against the railing of a wooden flying airship, relaxed satisfied expression, "
                "wearing high-altitude goggles pushed up on her forehead. Set against an open ocean of rolling white clouds at golden sunrise, "
                "revealing flying manta rays soaring alongside the hull in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (136, 140),
            "title": ["DUAL RESONANCE", "HARMONIC BLADE ARTS"],
            "fallback_color": (30, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of the protagonist in low athletic combat stance, fierce focused intensity, "
                "two swords crackling with synchronized pink-and-gold aura. Set on a fractured stone precipice under twilight skies, "
                "revealing her agile catgirl ally executing a soaring leap strike in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (141, 145),
            "title": ["PANTHEON VAULT", "PRIMORDIAL FRUIT"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of the protagonist reaching toward a glowing golden World Tree fruit, serene reverent expression, "
                "delicate light reflecting off her fingers. Set inside a sacred marble shrine adorned with floral carvings, "
                "revealing ancient guardian statues smiling gently in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (146, 150),
            "title": ["WORLD TREE APEX", "CONTINENTAL CHAMPIONS"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of the victorious adventurer party standing at the absolute summit platform of the World Tree, triumphant radiant smiles, "
                "wearing regal master-rank cloak emblems. Set overlooking boundless green continents stretching to the horizon beneath a glorious rainbow aurora in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
