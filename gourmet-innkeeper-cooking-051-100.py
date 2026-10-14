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
    "novel_slug": "the-gourmet-innkeeper-cooking-monsters-in-a-fantasy-world",
    "start_url": "https://freewebnovel.com/novel/the-gourmet-innkeeper-cooking-monsters-in-a-fantasy-world/chapter-51",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "Gourmet Innkeeper",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_gourmet_innkeeper_051_100",
    "final_audio": "output_gourmet_innkeeper_051_100.mp3",
    "final_video": "final_gourmet_innkeeper_051_100.mp4",
    "cover_image": "cover_gourmet_innkeeper_051_100.jpg",
    "timestamps_file": "youtube_timestamps_gourmet_innkeeper_051_100.txt",
    "subtitles_file": "subtitles_gourmet_innkeeper_051_100.srt",
    "payload_file": "youtube_upload_payload_gourmet_innkeeper_051_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "COOKING MONSTER DELICACIES IN AN UNTOUCHED WILDERNESS! COZY INN EXPANSION [Ch 51-100] | Fantasy Gourmet Audiobook Marathon",
    "tags": [
        "The Gourmet Innkeeper", "Cooking Monsters in a Fantasy World", "Masterchef Finn",
        "Cozy Fantasy", "Monster Cuisine", "Innkeeper LitRPG", "Slice of Life Fantasy", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Reincarnated deep into a dangerous, monster-infested frontier with an indestructible barrier shield, "
        "Masterchef Finn continues transforming ferocious beast apexes into mouthwatering gourmet cuisine!\n\n"
        "Leaving mundane kitchen struggles behind, Finn expands his cozy fantasy haven into a premier wilderness sanctuary. "
        "From searing tender wyvern flanks in aromatic herbal butter and simmering crystalline lake crabs into hearty stews, "
        "to harvesting rare alchemical spices and catering to legendary adventuring guilds, high-ranking nobles, and beastfolk mercenaries, "
        "the inn's reputation spreads across entire kingdoms!\n\n"
        "With his fluffy panda companion assisting in taste-testing and an automated system unlocking rare architectural upgrades, "
        "watch Finn balance high-stakes monster hunting expeditions with comforting culinary mastery!\n\n"
        "Welcome to Chapters 51 to 100 of 'The Gourmet Innkeeper: Cooking Monsters in a Fantasy World' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 51: Morning Harvest in the Perimeter Orchard & Searing Flame-Boar Bacon\n"
        "• Ch 56: Expanding the Dining Hall: Second-Tier Spatial Architecture Unlocked\n"
        "• Ch 62: The Frost-Tusk Mammoth Stew: Warming Weary Silver-Rank Adventurers\n"
        "• Ch 68: Secret Spice Grotto Expedition & Taming Rare Alchemical Truffles\n"
        "• Ch 74: Fluffy Panda Mascot's Sweet Tooth: Introducing Honey Glazed Pastries\n"
        "• Ch 80: High-End Aristocratic Incursion: Conquering Refined Palates with Monster Broth\n"
        "• Ch 86: Constructing the Open-Air Garden Terrace & Hearthside Brew Fermentation\n"
        "• Ch 92: Crimson Dragon-Horn Viper Hunt: Perfecting Tender Skewers under Ward Shields\n"
        "• Ch 100: Grand Banquet for the Borderland Alliance: The Sovereign Chef's Unrivaled Oasis\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#TheGourmetInnkeeper #MonsterCooking #MasterchefFinn #CozyFantasy #FantasyAudiobook #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (51, 55),
            "title": ["WILDERNESS HEARTH", "MORNING HARVEST"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of master chef Finn, athletic lean build, warm amber-gold eyes, windswept auburn hair, "
                "gentle satisfied smile, wearing a pristine rolled-sleeve linen chef tunic over sturdy leather foraging breeches. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside the open-air rustic stone kitchen "
                "of his wilderness inn, revealing smoking cast-iron skillets sizzling with savory monster bacon and glowing braided garlic braids in the distance. "
                "Illumination from golden morning sunlight pouring through timber windows and soft hearth embers, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (56, 60),
            "title": ["SPATIAL ARCHITECTURE", "INN EXPANSION"],
            "fallback_color": (25, 30, 40),
            "prompt": (
                "Cinematic 3D portrait of Finn reviewing glowing architectural blue matrices, focused calculating expression, holding a brass carving ladle. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set within the newly expanded two-story timber tavern hall, "
                "revealing polished oak dining tables, a massive roaring fieldstone fireplace, and a cute round panda mascot nibbling glazed buns on a wooden stool in the distance. "
                "Illumination from luminous cyan system status lines and warm flickering orange hearth flames, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (61, 65),
            "title": ["FROST-TUSK STEW", "ADVENTURER RECEPTION"],
            "fallback_color": (40, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of Finn lifting the lid from a colossal bubbling copper cauldron, steam carrying golden savory aromas, "
                "confident proud expression, clean apron dusted with exotic seasoning herbs. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in the bustling tavern bar, revealing battle-weary armored adventurers and elf rangers staring in wide-eyed delight "
                "at steaming bowls of rich monster meat stew in the distance. "
                "Illumination from glowing amber soup steam and warm brass hanging oil lamps, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (66, 70),
            "title": ["FORBIDDEN GROTTO", "MONSTER SPICE GATHERING"],
            "fallback_color": (20, 35, 30),
            "prompt": (
                "Cinematic 3D portrait of Finn foraging in dangerous wilderness terrain, watchful sharp gaze, wearing reinforced leather forearm guards, "
                "holding a delicate crystal harvesting knife and an aromatic glowing purple root. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a luminous cave entrance just outside his inn's defensive ward shield, revealing giant glowing mushrooms "
                "and dormant beast silhouettes prowling the misty forest floor in the distance. "
                "Illumination from bioluminescent emerald moss and shimmering translucent ward barriers, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (71, 75),
            "title": ["SWEET TOOTH MASCOT", "HONEY PASTRY BAKING"],
            "fallback_color": (35, 30, 20),
            "prompt": (
                "Cinematic 3D portrait of Finn laughing warmly as he brushes golden wild-honey glaze over freshly baked pastries, flour smudged playfully on his cheek, "
                "bright lively eyes. Flawless facial features, crisp detailed skin textures, medium close-up shot. Set on the bakery counter beside the brick oven, "
                "revealing his chubby panda mascot companion standing on tiptoes with paws on the counter eagerly awaiting sweet berry tarts in the distance. "
                "Illumination from warm golden oven embers and radiant afternoon sunbeams, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (76, 80),
            "title": ["ARISTOCRATIC BANQUET", "CONQUERING REFINED PALATES"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of Finn presenting an opulent multi-course platter of braised wyvern ribs with glazed seasonal greens, "
                "composed dignified posture, immaculate black-and-silver head chef coat. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside the private VIP dining pavilion of the inn, revealing arrogant high-born imperial nobles "
                "dropping their snobbish demeanor in absolute ecstasy after their first bite in the distance. "
                "Illumination from crystal chandelier candlelight and glistening meat glaze reflections, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (81, 85),
            "title": ["GARDEN TERRACE", "HEARTHSIDE BREWERY"],
            "fallback_color": (25, 35, 30),
            "prompt": (
                "Cinematic 3D portrait of Finn tasting fermented honey-fruit mead from an engraved wooden tankard, thoughtful refined palate, "
                "evening breeze gently moving his auburn hair. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set across the newly opened wooden garden terrace surrounded by climbing grapevines and floral lanterns, revealing cheerful mercenary tables "
                "toasting drinks under the twilight sky in the distance. "
                "Illumination from glowing fairy lights and purple-orange sunset sky gradients, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (86, 90),
            "title": ["DEFENSIVE PERIMETER", "DRAGON-VIPER HUNT"],
            "fallback_color": (25, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of Finn in defensive combat preparation, determined resolute glare, holding an enchanted silver filleting cleaver "
                "swirling with razor-sharp kinetic cutting wind. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set at the boundary of his translucent dome barrier, revealing a defeated crimson dragon-horned viper dissipating into usable grade-A culinary meat materials in the distance. "
                "Illumination from electric-blue barrier ripples and iridescent crimson scales, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (91, 95),
            "title": ["CULINARY TRANSCENDENCE", "ANCIENT RECIPE UNLOCKED"],
            "fallback_color": (40, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of Finn executing master-tier culinary alchemy, intense artistic concentration, hands deftly juggling flaming alchemical seasonings "
                "over an ancient bronze wok. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside the upgraded master kitchen suite, revealing golden culinary runes floating around the bubbling broth and rows of crystal condiment jars in the distance. "
                "Illumination from bright golden culinary magic flares and glowing hearth embers, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (96, 100),
            "title": ["THE SOVEREIGN OASIS", "GRAND ALLIANCE BANQUET"],
            "fallback_color": (30, 25, 25),
            "prompt": (
                "Cinematic 3D portrait of Grand Innkeeper Finn standing atop the central courtyard balcony, warm noble presence, serene welcoming smile, "
                "wearing an ornate tailored master chef mantle with embroidered golden wheat and knife crests. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set overlooking the sprawling, illuminated inn estate packed with hundreds of celebrating adventurers, beastfolk, and trade merchants, "
                "revealing fireworks bursting over the ancient fantasy forest under an awe-inspiring starry night in the distance. "
                "Illumination from colorful magical fireworks, warm lantern glow, and starlit sky reflections, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
