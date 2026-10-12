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
    "start_url": "https://freewebnovel.com/novel/the-gourmet-innkeeper-cooking-monsters-in-a-fantasy-world/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Gourmet Innkeeper",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 1,  # Sequential processing to respect 15 RPM limits cleanly
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_gourmet_innkeeper_001_050",
    "final_audio": "output_gourmet_innkeeper_001_050.mp3",
    "final_video": "final_gourmet_innkeeper_001_050.mp4",
    "cover_image": "cover_gourmet_innkeeper_001_050.jpg",
    "timestamps_file": "youtube_timestamps_gourmet_innkeeper_001_050.txt",
    "subtitles_file": "subtitles_gourmet_innkeeper_001_050.srt",
    "payload_file": "youtube_upload_payload_gourmet_innkeeper_001_050.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "COOKING S-RANK MONSTERS IN ANOTHER WORLD! MYTHICAL GOURMET INNKEEPER [Ch 1-50] | LitRPG Audiobook Marathon",
    "tags": [
        "LitRPG Audiobook", "The Gourmet Innkeeper", "Cooking Monsters in a Fantasy World", "Finn Solthar",
        "Progression Fantasy", "Cozy Fantasy", "Culinary Fantasy", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Transmigrated into a perilous fantasy wilderness with a rundown lodge and a Culinary Sovereign System!\n\n"
        "Master Chef Finnick Solthar finds himself in the dangerous Blackwood forest, armed with an absolute territory barrier, "
        "an enchanted kitchen, and his gluttonous panda mascot Pang. In a world where ferocious beasts terrorize mankind, "
        "Finn discovers that high-tier magical monsters are simply gourmet ingredients waiting to be harvested!\n\n"
        "From Dire Boar crackling roasts that cleanse soul impurities, to Flame Serpent soups granting permanent fire resistance, "
        "his dishes turn exhausted elven mages and battle-scarred hunters into ecstatic regulars. And whenever arrogant mercenaries "
        "or greedy guilds try to extort the lodge, the Inn's invincible defensive boundary teaches them the house rules!\n\n"
        "Welcome to Chapters 1 to 50 of 'The Gourmet Innkeeper: Cooking Monsters in a Fantasy World' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 01: Wilderness Transmigration & Awakening the Gourmet Innkeeper System\n"
        "• Ch 06: Meeting Pang & The First Customer Sylwen's Mana Recovery\n"
        "• Ch 12: Dire Boar Barbecue & Cleansing Ancient Bloodline Curses\n"
        "• Ch 18: Flame Serpent Stew & Unlocking the Absolute Domain Barrier\n"
        "• Ch 24: Crushing Extorting Mercenaries with Territorial Punishment\n"
        "• Ch 30: Veteran Hunter Marcus & Permanent Attribute Buff Banquets\n"
        "• Ch 36: S-Rank Frost Wolf Hunt & Harvesting Glacial Culinary Cores\n"
        "• Ch 42: Grand Inn Renovation: Hot Springs & The Adventurers' Tavern\n"
        "• Ch 47: Repelling the Calamity Beast Swarm with Boundary Authority\n"
        "• Ch 50: The Continental Gourmet Legend Begins & Opening the Celestial Hall\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#GourmetInnkeeper #CookingMonsters #FinnSolthar #LitRPG #ProgressionFantasy #CozyFantasy #AudiobookMarathon #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (1, 5),
            "title": ["WILDERNESS INN", "GOURMET AWAKENING"],
            "fallback_color": (30, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of an ambitious young master chef, handsome refined features, neat dark hair, "
                "curious radiant amber eyes, wearing a tailored charcoal-and-cream chef's tunic with rolled-up sleeves and dark leather bracers. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a rustic wooden tavern kitchen with polished "
                "oak counters and hanging brass cooking pots, revealing a mystical glowing forest through the window and an enchanted kitchen knife "
                "glowing with faint golden rune light on the cutting board in the distance. Illumination from warm hearth fire embers and floating golden "
                "system interface runes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (6, 10),
            "title": ["FIRST GUEST", "ELVEN RECOVERY"],
            "fallback_color": (20, 30, 25),
            "prompt": (
                "Cinematic 3D portrait of Innkeeper Finn Solthar, confident hospitable smile, sharp jawline, glowing hazel eyes, "
                "presenting a piping-hot wooden platter of caramelized roast ribs surrounded by sparkling steam. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in the cozy lantern-lit dining hall of the inn, revealing exhausted elven maiden Sylwen Thariel with long silver hair "
                "and emerald robes looking on in utter wonder as her mana reserves restore in radiant green ripples in the distance. "
                "Illumination from warm amber lantern light and glowing emerald culinary steam trails, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (11, 15),
            "title": ["PANDA MASCOT", "DIRE BOAR BANQUET"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of Chef Finn Solthar laughing warmly, expressive dark eyes, holding a polished carving knife above a roasted beast feast. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set by the large stone hearth of the wilderness inn, "
                "revealing his chubby magical panda mascot Pang wearing a tiny chef bandana eagerly stuffing savory roasted monster cutlets into its paws "
                "on the tabletop in the distance. Illumination from roaring golden brick oven fires and sparkling savory glaze highlights, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (16, 20),
            "title": ["FLAME SERPENT", "ABSOLUTE BARRIER"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of an authoritative innkeeper monarch, calm imposing expression, dark windswept hair, intense amber-gold pupils, "
                "wearing high-collared dark-aproned culinary robes with silver filigree clasps. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set at the open entrance of the fantasy inn, revealing an aggressive flame serpent monster and hostile rogue hunters "
                "shattered and repelled against a colossal translucent geometric barrier dome in the distance. "
                "Illumination from neon-golden barrier defense runes and exploding crimson flame embers, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (21, 25),
            "title": ["HUNTER GUILD", "PERMANENT BUFFS"],
            "fallback_color": (25, 25, 35),
            "prompt": (
                "Cinematic 3D portrait of Chef Finn Solthar, calm calculating gaze, neatly parted black hair, radiant electric-gold eyes, "
                "holding a crystal tureen of simmering radiant beast broth with glowing herb garnishes. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside the expanding dining hall packed with wooden tables, revealing veteran hunter Marcus and his armored companions "
                "flexing their muscles in disbelief as golden strength auras ignite around their shoulders in the distance. "
                "Illumination from glowing golden stat-enhancement halos and warm ceiling chandeliers, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (26, 30),
            "title": ["GLACIAL ELK", "FROST HARVEST"],
            "fallback_color": (15, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of Finn Solthar dressed in cold-weather fur-lined traveler's leather over his chef attire, focused sharp gaze, "
                "holding an insulated mithril culinary cleaver emitting cool cyan mist. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on the snow-dusted edge of the enchanted forest just outside the inn's boundary, revealing a defeated colossal Glacial Elk "
                "with crystalline sapphire antlers sparkling under winter twilight in the distance. "
                "Illumination from crystalline ice reflections, twinkling diamond dust, and warm lodge window glows, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (31, 35),
            "title": ["NOBLE GOURMANDS", "ROYAL TASTING"],
            "fallback_color": (30, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of an elegant master restaurateur, refined handsome facial structure, gentle welcoming amber eyes, "
                "wearing an imperial midnight-blue waistcoat with gold button embroidery over crisp white linen. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in a newly renovated private VIP dining chamber with rich velvet drapes, revealing visiting high elven nobles and royal court mages "
                "raising delicate porcelain spoons in awe at multi-colored glowing elixir soups in the distance. "
                "Illumination from warm crystal chandeliers and iridescent culinary mana luminescence, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (36, 40),
            "title": ["GRAND INN EXPANSION", "ENCHANTED TAVERN"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of Innkeeper Finn Solthar leaning gracefully against a polished mahogany bar counter, cheerful confident expression, "
                "sparkling amber pupils, wiping a crystalline beer flagon with a clean white cloth. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside the bustling, multi-tiered grand tavern expansion of the Solthar Inn, revealing dozens of diverse adventurers, "
                "dwarven smiths, and elven rangers clinking foaming golden mugs under soaring vaulted timber rafters in the distance. "
                "Illumination from brass gas lamps, roaring stone fireplaces, and floating fairy lights, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (41, 45),
            "title": ["CALAMITY BEAST WAVE", "SOVEREIGN DEFENSE"],
            "fallback_color": (35, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of Finn Solthar commanding the inn's master control core, fierce authoritative gaze, dark hair whipped by magical updrafts, "
                "raising his hand inscribed with the Master Innkeeper Crest. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on the high open-air terrace of the fortress inn, revealing a massive midnight horde of subterranean mutant beasts "
                "disintegrating against the multi-layered golden boundary matrix without shaking the foundation in the distance. "
                "Illumination from blinding golden territory shockwaves and exploding beast vitality embers, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (46, 50),
            "title": ["CELESTIAL BANQUET", "MYTHIC INNKEEPER"],
            "fallback_color": (25, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Sovereign Innkeeper Finn Solthar at the height of continental renown, majestic posture, radiant glowing sun-gold irises, "
                "wearing an ornate master chef mantle woven from silver starlight silk and deep charcoal dragon leather. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside the breathtaking Celestial Dining Pavilion overlooking mountain sunrises, revealing Pang, Sylwen, and kingdom champions "
                "raising a celebratory toast around a legendary mythic monster feast in the distance. "
                "Illumination from brilliant auroras of sunrise gold, soft rainbow culinary steam, and ambient starlight, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
