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
    "novel_slug": "transmigrated-to-a-dark-fantasy-world-of-sss-rank-king-of-the-void",
    "start_url": "https://freewebnovel.com/novel/transmigrated-to-a-dark-fantasy-world-of-sss-rank-king-of-the-void/chapter-101",
    "start_chapter": 101,
    "end_chapter": 150,
    "default_topic": "King of the Void",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_king_of_the_void_101_150",
    "final_audio": "output_king_of_the_void_101_150.mp3",
    "final_video": "final_king_of_the_void_101_150.mp4",
    "cover_image": "cover_king_of_the_void_101_150.jpg",
    "timestamps_file": "youtube_timestamps_king_of_the_void_101_150.txt",
    "subtitles_file": "subtitles_king_of_the_void_101_150.srt",
    "payload_file": "youtube_upload_payload_king_of_the_void_101_150.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "FORBIDDEN ELDRITCH RIFT CONQUEST! SSS-RANK VOID MONARCH OBLITERATES GOD-REALMS [Ch 101-150] | Dark Fantasy Audiobook Marathon",
    "tags": [
        "King of the Void", "Dark Fantasy Audiobook", "Transmigrated SSS-Rank", "Void Magic",
        "Overpowered MC", "Dark Fantasy LitRPG", "Antihero Audiobook", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Crossing the forbidden ocean into the forgotten Outer Continents, our transmigrated Void Monarch confronts "
        "eldritch abominations and the supreme god-realms of the high heavens!\n\n"
        "Unfazed by the ancient pantheon's holy sanctions or the horrifying tentacled horrors of the primordial rifts, "
        "our protagonist elevates his SSS-Rank Void authority to conceptual omnipotence. Forging the Nether Void Scepter "
        "and commanding absolute dimensional severing, he systematically tears apart holy armada fleets, executes Archbishops "
        "of the Sun God, and forces elder eldritch titans to submit as loyal familiars.\n\n"
        "Watch him conquer forgotten god-graves, expand his black singularity domain, and crown himself the undisputed Sovereign of Nothingness!\n\n"
        "Welcome to Chapters 101 to 150 of 'Transmigrated to a Dark Fantasy World of SSS-Rank: King of the Void' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 101: Voyage to the Outer Continents: Traversing the Cursed Abyssal Sea\n"
        "• Ch 107: Clashing with the Sun God's Inquisition: Disintegrating Holy Solar Miracles\n"
        "• Ch 114: Forging the Nether Void Scepter in the Heart of the Black Iron Foundry\n"
        "• Ch 121: Subjugating the Ancient Tentacled Rift Titan: Unlocking Abyssal Maw Magic\n"
        "• Ch 128: Demolishing the Imperial Grand Armada with Combined Spatial Singularity Waves\n"
        "• Ch 135: Midnight Council Summit: Forcing Aristocratic Warlords to Pledge Soul Vows\n"
        "• Ch 142: Refining the Infinite Mana Core: Transcending Mortal Biological Constraints\n"
        "• Ch 150: Absolute Sovereign Coronation: Monarch of the Hollow Dimension and Outer Dark\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#KingOfTheVoid #DarkFantasyAudiobook #SSSRank #VoidMagic #LitRPG #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (101, 105),
            "title": ["ABYSSAL SEA VOYAGE", "OUTER CONTINENT ARRIVAL"],
            "fallback_color": (15, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of the void protagonist standing at the bow of an ironclad black warship, calm sharp glare, "
                "eyes glowing with deep violet starlight, wearing dark fur-trimmed naval coat. Set upon stormy black waters under overcast clouds, "
                "revealing jagged dark cliffs of the Outer Continent looming in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (106, 110),
            "title": ["SUN GOD CLASH", "DISINTEGRATING SOLAR MIRACLES"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of the protagonist raising two fingers surrounded by dense void lightning, cold dismissive smirk, "
                "dark hair trailing subtle purple sparks. Set inside a grand marble cathedral ruins, revealing golden solar miracles dissolving "
                "into black dust before an Archbishop in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (111, 115),
            "title": ["NETHER SCEPTER", "FORGING IN THE BLACK FOUNDRY"],
            "fallback_color": (30, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of the protagonist channeling purple void flames into an obsidian scepter, intense artistic focus, "
                "palms directing floating runic metal plates. Set inside a subterranean volcanic iron foundry, revealing glowing embers and dark stone forge machinery in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (116, 120),
            "title": ["RIFT TITAN", "SUBJUGATING TENTACLED HORRORS"],
            "fallback_color": (20, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist holding an outstretched hand over a colossal abyss, resolute fearless presence, "
                "wearing reinforced black-leather armor. Set at the edge of a massive jagged dimensional fissure, revealing an ancient tentacled titan entity bowing its head in submission in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (121, 125),
            "title": ["ARMADA DEMOLITION", "SPATIAL SINGULARITY WAVE"],
            "fallback_color": (25, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of the protagonist commanding a massive black singularity orb above his palm, fierce commanding jawline, "
                "coat billowing against shockwave winds. Set overlooking a coastal cliffside, revealing imperial ironclad warships fracturing in spatial tears across the ocean in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (126, 130),
            "title": ["MIDNIGHT SUMMIT", "WARLORD SOUL VOWS"],
            "fallback_color": (20, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of the protagonist seated at a long obsidian table, subtle composed smile, dark eyes assessing terrified guests, "
                "wearing tailored midnight-blue noble attire. Set in an opulent candlelit stone hall, revealing masked aristocratic warlords kneeling and signing glowing purple contracts in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (131, 135),
            "title": ["INFINITE MANA CORE", "TRANSCENDING MORTAL LIMITS"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the protagonist in deep seated meditation, serene transcendent presence, glowing violet origin glyphs revolving around his shoulders. "
                "Set inside a zero-gravity crystal sanctum, revealing concentric rings of pure spatial energy expanding through solid granite walls in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (136, 140),
            "title": ["SIEGE COUNTER-PURGE", "ZERO SURVIVORS"],
            "fallback_color": (25, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of the protagonist in swift sword stance, sharp cold gaze, fingertips crackling with razor-thin spatial threads. "
                "Set on the moonlit battlements of an ancient conquered fortress, revealing invading elite crusader squads vanishing into thin air without leaving blood in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (141, 145),
            "title": ["GOD-REALM COLLAPSE", "NULLIFYING DIVINE SANCTION"],
            "fallback_color": (35, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of the protagonist raising an obsidian scepter to challenge the heavens, defiant regal expression, "
                "two eyes glowing with dual-toned purple starlight. Set beneath swirling dark clouds, revealing golden divine barrier seals cracking and crumbling in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (146, 150),
            "title": ["HOLLOW EMPEROR", "ABSOLUTE SOVEREIGNTY"],
            "fallback_color": (20, 15, 50),
            "prompt": (
                "Cinematic 3D portrait of the Hollow Dimension Emperor seated upon a carved black-crystal throne, serene invincible aura, "
                "eyes glowing with radiant cosmic purple starlight, wearing the sovereign mantle of the Void Monarch. Set inside an immense throne room overlooking a secured dark empire beneath an aurora twilight sky in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
