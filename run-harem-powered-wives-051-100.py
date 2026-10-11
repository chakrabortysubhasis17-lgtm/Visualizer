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
    "start_url": "https://freewebnovel.com/novel/harem-powered-kingdom-building-empire-of-carnal-sin/chapter-51",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "Empire",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 1,  # Sequential processing to respect 15 RPM limits cleanly
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_harem_kingdom_051_100",
    "final_audio": "output_harem_kingdom_051_100.mp3",
    "final_video": "final_harem_kingdom_051_100.mp4",
    "cover_image": "cover_harem_kingdom_051_100.jpg",
    "timestamps_file": "youtube_timestamps_harem_kingdom_051_100.txt",
    "subtitles_file": "subtitles_harem_kingdom_051_100.srt",
    "payload_file": "youtube_upload_payload_harem_kingdom_051_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "FORGING AN UNCONQUERABLE IMPERIAL REALM! CARNAL SIN ASCENSION [Ch 51-100] | LitRPG Audiobook Marathon",
    "tags": [
        "LitRPG Audiobook", "Harem-Powered Kingdom Building", "Empire of Carnal Sin", "Lord Arthur",
        "Kingdom Building", "Progression Fantasy", "Dark Fantasy", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Having secured the frontier fortress, Lord Arthur pushes the borders of his burgeoning empire into continental supremacy!\n\n"
        "With the continuous territorial feedback from the Carnal Empire System, Arthur's sovereign domain transcends ordinary mortal limits. "
        "Through deepening bonds with his multi-racial consorts, ancient leylines awaken beneath the soil: "
        "High Elf Elysia harmonizes ancient forest spirits to shield expansive farmlands and trade corridors; "
        "Beastkin General Valeria commands unstoppable shock-troop legions armed with runic dwarven steel; "
        "and Court Sorceress Morrigan constructs abyssal void wards that completely deflect foreign imperial siege spells!\n\n"
        "As rival neighboring duchies, church crusaders, and treacherous royal coalitions march to purge his unorthodox domain, "
        "Arthur turns the borderlands into an impenetrable bastion of absolute conquest!\n\n"
        "Welcome to Chapters 51 to 100 of 'Harem-Powered Kingdom Building: Empire of Carnal Sin' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 51: Annexing the Iron Duchy Borderlands & Grand Citadel Reconstruction\n"
        "• Ch 60: High Elf Imperial Envoy & Elysia's World-Tree Leyline Bloom\n"
        "• Ch 68: Ironfang Beast Vanguard Assault & Crushing Hostile Warlord Cohorts\n"
        "• Ch 75: Court Sorceress Morrigan's Shadow Veil & Repelling Holy Church Inquisitors\n"
        "• Ch 82: Dragonkin Consort Covenant & Igniting the Magma Core Forge\n"
        "• Ch 90: Grand Multi-Racial Imperial Trade Nexus & Subjugating Mercenary Guilds\n"
        "• Ch 95: The Valley of Broken Kings & Decisive Field Artillery Annihilation\n"
        "• Ch 100: Sovereign Emperor Arthur's Continental Coronation & Rise of the Undying Realm\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#KingdomBuilding #EmpireOfCarnalSin #LordArthur #LitRPG #DarkFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (51, 55),
            "title": ["IRON DUCHY ANNEXATION", "CITADEL EXPANSION"],
            "fallback_color": (25, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of a commanding young monarch, sharp dark hair, calculated glowing amber-gold eyes, "
                "wearing polished blackened steel plate armor with an imperial crimson cape clasped by silver dragon brooches. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set atop the high stone battlements "
                "of an expanding frontier citadel, revealing massive stone siege towers and allied construction teams erecting towering outer walls below. "
                "Illumination from blazing perimeter braziers and floating violet domain interface runes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (56, 60),
            "title": ["WORLD-TREE LEYLINE", "ELYSIA'S SANCTUARY"],
            "fallback_color": (20, 35, 25),
            "prompt": (
                "Cinematic 3D portrait of Lord Arthur in serene regal command, refined jawline, warm hazel-amber eyes, "
                "wearing dark velvet robes trimmed with emerald elven silk. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set along the base of a colossal glowing white-bark ancient spirit tree, revealing High Elf Consort Elysia "
                "with platinum hair and pointed ears channeling radiant streams of jade life mana across the flourishing valley in the distance. "
                "Illumination from sparkling emerald leyline veins pulsing through the soil and golden sunbeams, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (61, 65),
            "title": ["IRONFANG VANGUARD", "VALERIA'S CHARGE"],
            "fallback_color": (35, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of a battle-hardened commander lord, intense focused dark eyes, sleek black hair, "
                "wearing reinforced dragon-bone cuirass over dark leather combat garb. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set overlooking a misty canyon battlefield, revealing beastkin general Valeria brandishing a glowing runic broadsword "
                "at the head of an armored beast-rider vanguard routing enemy coalition cavalry in the distance. "
                "Illumination from blazing battle standards and gleaming steel blade reflections, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (66, 70),
            "title": ["ABYSSAL VOID WARD", "MORRIGAN'S PURGE"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of Lord Arthur, calm imposing expression, dark windswept hair, luminous amethyst pupils, "
                "wearing an imperial midnight-blue mantle. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on the roof of an arcane observatory tower, revealing seductive court archmage Morrigan in flowing obsidian silk "
                "raising her staff to disintegrate incoming church holy spells against a colossal domed purple barrier in the distance. "
                "Illumination from crackling magenta magical lightning and glowing geometric spell circles, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (71, 75),
            "title": ["DRAGONKIN COVENANT", "MAGMA CORE FORGE"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of an unyielding emperor, dark hair whipped by thermal updrafts, fierce sun-gold eyes, "
                "wearing heavy heat-tempered obsidian-steel breastplate armor. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set deep inside a subterranean volcanic forge chamber, revealing an imposing dragonkin maiden with crimson horns "
                "and radiant scaled gauntlets hammering enchanted war plate above bubbling lava trenches in the distance. "
                "Illumination from roaring molten magma rivers and blinding golden anvil sparks, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (76, 80),
            "title": ["IMPERIAL ARENA", "LEGION TRIALS"],
            "fallback_color": (30, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of a dignified conqueror sovereign, sharp facial planes, calculating golden eyes, "
                "wearing a tailored charcoal-and-gold formal military greatcoat. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in the grand royal box of a newly constructed stone amphitheater, revealing allied human, beastkin, "
                "and elven legionnaires sparring in synchronized discipline before cheering thousands in the distance. "
                "Illumination from bright midday sunlight and fluttering multi-colored imperial banners, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (81, 85),
            "title": ["CRUSADE INVASION", "VALLEY OF BROKEN KINGS"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic 3D portrait of an unyielding warrior monarch, razor-sharp jawline, cold glowing amber pupils, "
                "holding an engraved broadsword wreathed in dark kinetic mana. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set across a shattered war-torn mountain pass under overcast storm skies, revealing retreating enemy crusader armies "
                "shattered under heavy magical ballista and elemental artillery barrages in the distance. "
                "Illumination from burning enemy iron siege towers and sharp silver blade glints, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (86, 90),
            "title": ["IMPERIAL TRADE NEXUS", "MULTI-RACE HARMONY"],
            "fallback_color": (25, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of Arthur as a wise founding emperor, refined handsome features, warm confident smile, "
                "holding a golden imperial proclamation scroll, wearing royal navy and gold vestments. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set overlooking a sprawling marble marketplace courtyard, revealing diverse merchants, dwarf craftsmen, "
                "and elven alchemists trading under grand vaulted stone arches in the distance. "
                "Illumination from warm golden lantern light and sparkling crystal fountains, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (91, 95),
            "title": ["INQUISITOR BEHEMOTH", "SOVEREIGN RETRIBUTION"],
            "fallback_color": (30, 15, 40),
            "prompt": (
                "Cinematic 3D portrait of Lord Arthur executing supreme command, dark windswept hair, radiant dual-colored violet-and-amber eyes, "
                "wearing ornate imperial dark-silver sovereign armor. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set at the fortified mountain gates, revealing a colossal iron-clad church war behemoth collapsing "
                "under a combined tempest-and-void strike unleashed by Arthur and his consorts in the distance. "
                "Illumination from blinding white-silver magical shockwaves and billowing smoke trails, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (96, 100),
            "title": ["EMPIRE OF CARNAL SIN", "CONTINENTAL CORONATION"],
            "fallback_color": (25, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Sovereign Emperor Arthur seated upon the grand obsidian throne, regal posture, commanding sun-gold eyes, "
                "wearing an imperial crown of blackened gold and velvet-lined sovereign robes. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set overlooking his grand imperial palace hall, revealing Elysia, Valeria, Morrigan, and his consort council "
                "standing proudly beside his throne while allied multi-racial legions kneel in absolute loyalty below under vast vaulted ceilings. "
                "Illumination from brilliant auroras of sunrise gold, radiant emerald leyline beams, and celestial violet sorcery mist, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
