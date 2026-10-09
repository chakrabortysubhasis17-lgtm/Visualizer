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
    "novel_slug": "harem-powered-kingdom-building-empire-of-carnal-sin",
    "start_url": "https://freewebnovel.com/novel/harem-powered-kingdom-building-empire-of-carnal-sin/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Empire",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 2,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_harem_kingdom_001_050",
    "final_audio": "output_harem_kingdom_001_050.mp3",
    "final_video": "final_harem_kingdom_001_050.mp4",
    "cover_image": "cover_harem_kingdom_001_050.jpg",
    "timestamps_file": "youtube_timestamps_harem_kingdom_001_050.txt",
    "subtitles_file": "subtitles_harem_kingdom_001_050.srt",
    "payload_file": "youtube_upload_payload_harem_kingdom_001_050.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "HAREM-POWERED KINGDOM BUILDING! EMPIRE OF CARNAL SIN [Ch 1-50] | LitRPG Audiobook Marathon",
    "tags": [
        "LitRPG Audiobook", "Harem-Powered Kingdom Building", "Empire of Carnal Sin", "Lord Arthur",
        "Kingdom Building", "Progression Fantasy", "Dark Fantasy", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Summoned into a brutal dark fantasy realm to govern an impoverished wasteland border territory!\n\n"
        "Inheriting a decaying fortress surrounded by hostile warlords, ravenous monsters, and starving refugees, "
        "Lord Arthur awakens the forbidden Carnal Empire System! Under this unique territory-building interface, "
        "forging intimate bonds with powerful maiden representatives of different magical races directly unlocks "
        "unprecedented domain buffs—restoring ancient leylines, granting invincible legion traits, and generating infinite resources!\n\n"
        "From high-elf archer diplomats and fierce beastkin vanguard champions to cunning dark court sorceresses, "
        "Arthur unifies extraordinary heroines under his banner to rebuild society and crush invading warlords underfoot!\n\n"
        "Welcome to Chapters 1 to 50 of 'Harem-Powered Kingdom Building: Empire of Carnal Sin' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 01: Reincarnated in the Ruined Frontier & Carnal Empire System Awakening\n"
        "• Ch 08: Bonding with High Elf Elysia & Forest Leyline Mana Restoration\n"
        "• Ch 15: Beastkin General Valeria Recruited & Vanguard Legion Buff\n"
        "• Ch 22: Repelling Rival Baron Raiders & First Territory Border Expansion\n"
        "• Ch 28: Court Sorceress Morrigan's Loyalty & Grand Barrier Erection\n"
        "• Ch 35: The Great Valley Ambush & Crushing Enemy Iron Siege Engines\n"
        "• Ch 42: Establishing the Multi-Racial Imperial Trade Nexus\n"
        "• Ch 50: Sovereign Emperor Arthur & The Rise of the Unconquered Citadel\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#KingdomBuilding #EmpireOfCarnalSin #LordArthur #LitRPG #DarkFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (1, 5),
            "title": ["RUINED FRONTIER", "CARNAL EMPIRE SYSTEM"],
            "fallback_color": (25, 20, 25),
            "prompt": (
                "Cinematic 3D portrait of a commanding young male lord, sharp dark hair, calculated glowing amber-gold eyes, "
                "wearing battle-worn blackened steel breastplate over a crimson velvet tunic with silver clasps. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a dilapidated stone fortress keep overlooking barren rocky borderlands, revealing a floating translucent "
                "magenta system interface window inscribed with glowing kingdom domain matrices. "
                "Illumination from warm flickering fireplace embers and vibrant neon-violet interface glyphs, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (6, 10),
            "title": ["HIGH ELF ELYSIA", "FOREST LEYLINE BLOOM"],
            "fallback_color": (20, 30, 25),
            "prompt": (
                "Cinematic 3D portrait of an authoritative young male ruler, confident serene expression, refined jawline, warm hazel eyes, "
                "wearing tailored emerald-trimmed lord robes with leather pauldrons. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set along an ancient overgrown elven ruin archway, revealing elegant High Elf archer Elysia with platinum-blonde hair "
                "and pointed ears smiling gently while channeling a swirling stream of life mana in the distance. "
                "Illumination from radiant sunbeams filtering through leaves and glowing jade leylines pulsing across the soil, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (11, 15),
            "title": ["BEASTKIN VALERIA", "VANGUARD LEGION RALLY"],
            "fallback_color": (35, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of a battle-tested commander lord, intense focused dark eyes, sleek black hair, "
                "wearing heavy dark-iron plate armor with engraved wolf-crest emblems. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on the stone ramparts of the frontier fortress, revealing fierce beastkin commander Valeria with amber feline eyes "
                "and striped tail drawing a massive double-edged broadsword before cheering shock troopers in the distance. "
                "Illumination from blazing perimeter fire braziers and gleaming steel weapon edges, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (16, 20),
            "title": ["COURT MAGE MORRIGAN", "OBSIDIAN WARD BARRIER"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of Lord Arthur, calm regal gaze, dark windswept hair, glowing amethyst pupils, "
                "wearing an imperial midnight-blue mantle clasped by a silver dragon brooch. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set upon the high observatory tower, revealing seductive court archmage Morrigan in flowing obsidian silk robes "
                "channeling a massive domed protective barrier of crackling purple sorcery across the settlement in the distance. "
                "Illumination from shimmering violet magical lightning and glowing arcane circles, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (21, 25),
            "title": ["RAIDER INVASION", "BORDERLAND RETRIBUTION"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic 3D portrait of an unyielding warrior monarch, razor-sharp jawline, cold luminous golden eyes, "
                "wielding an engraved runic broadsword dripping with shimmering kinetic energy. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in a misty mountain valley gorge, revealing defeated marauding mercenary warbands fleeing across rocky barricades "
                "under concentrated arrow fire from Arthur's allied defenders in the distance. "
                "Illumination from razor-sharp steel blade glints and pre-dawn cyan mist, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (26, 30),
            "title": ["TERRITORY EXPANSION", "MULTI-RACE INTEGRATION"],
            "fallback_color": (25, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of a visionary sovereign lord, dignified handsome features, calculating amber eyes, "
                "holding an open territory survey parchment, wearing clean charcoal-and-gold formal coats. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set overlooking the expanding settlement plaza, revealing newly constructed stone barracks, bustling artisan markets, "
                "and diverse humans, beastkin, and elves collaborating harmoniously in the distance. "
                "Illumination from warm golden midday sunlight and fluttering imperial banners, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (31, 35),
            "title": ["SHADOW COVENANT", "DEMONESS INFILTRATION"],
            "fallback_color": (30, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of Lord Arthur in strategic contemplation, neat black hair, piercing violet-gold eyes, "
                "wearing high-collared dark leather stealth armor with silver buckles. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a secluded dungeon war room, revealing a dark demoness scout with subtle obsidian horns and crimson eyes "
                "kneeling obediently to deliver enemy tactical intelligence in the distance. "
                "Illumination from shadowy purple candle flame reflections and gleaming silver map daggers, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (36, 40),
            "title": ["VALLEY FORTRESS", "SIEGE ENGINE PURGE"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of a victorious conqueror lord, windswept dark hair, fierce glowing sun-gold eyes, "
                "wearing heavy dragon-bone reinforced battle plate. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set before the burning wreckage of enemy iron siege catapults, revealing retreating hostile warlord battalions "
                "scattered across shattered trenches in the distance. "
                "Illumination from roaring battlefield fires and explosive golden magical artillery impacts, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (41, 45),
            "title": ["ROYAL CITADEL", "LEYLINE CONVERGENCE"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of Arthur as an undisputed regional ruler, majestic posture, radiant sapphire-amber eyes, "
                "wearing ornate imperial dark-silver plate mantle lined with white ermine fur. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside the newly erected grand marble throne chamber, revealing towering crystalline leylines pulsating "
                "pure elemental mana through white stone pillars in the distance. "
                "Illumination from blinding white-gold leyline streams and warm hanging brass chandeliers, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (46, 50),
            "title": ["EMPIRE OF CARNAL SIN", "SOVEREIGN ASCENDANCE"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of Sovereign Emperor Arthur seated upon the grand obsidian dragon throne, refined commanding features, "
                "majestic glowing amber-gold eyes, wearing an imperial crown of blackened gold and velvet-lined sovereign robes. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set overlooking his grand imperial throne hall, "
                "revealing Elysia, Valeria, and Morrigan standing proudly beside his throne while legions of multi-racial knights kneel in absolute loyalty below. "
                "Illumination from brilliant auroras of sunrise gold, violet sorcery mist, and radiant emerald leyline beams, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
