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
    "novel_slug": "harem-training-system-every-girl-i-train-makes-me-stronger",
    "start_url": "https://freewebnovel.com/novel/harem-training-system-every-girl-i-train-makes-me-stronger/chapter-101",
    "start_chapter": 101,
    "end_chapter": 150,
    "default_topic": "Harem Training System",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_harem_training_101_150",
    "final_audio": "output_harem_training_101_150.mp3",
    "final_video": "final_harem_training_101_150.mp4",
    "cover_image": "cover_harem_training_101_150.jpg",
    "timestamps_file": "youtube_timestamps_harem_training_101_150.txt",
    "subtitles_file": "subtitles_harem_training_101_150.srt",
    "payload_file": "youtube_upload_payload_harem_training_101_150.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "ASCENDING TO THE IMMORTAL COURT! GOD-TIER DISCIPLE MULTIPLIERS SHATTER HEAVENS [Ch 101-150] | Progression Fantasy Audiobook Marathon",
    "tags": [
        "Harem Training System", "Every Girl I Train Makes Me Stronger", "Progression Fantasy Audiobook",
        "System LitRPG", "Harem Cultivation", "Overpowered MC", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Transcending mortal continents, the master cultivator leads his peerless inner court into the Upper Immortal Realms!\n\n"
        "With the [Harem Training System] continuously upgrading its return ratios, every stage breakthrough, sword concept mastery, "
        "and immortal bloodline awakening achieved by his circle of disciples triggers astronomical cultivation torrents into his divine core. "
        "Facing arrogant heavenly princes, ancient god-clan matriarchs, and primordial abyssal overlords, our protagonist uses supreme guidance "
        "and synchronized domain auras to crush every obstacle.\n\n"
        "Watch him recruit ancient dragon maidens, unlock heavenly alchemy secrets, and establish an untouchable sovereign sanctuary in the Upper Realm!\n\n"
        "Welcome to Chapters 101 to 150 of 'Harem Training System: Every Girl I Train Makes Me Stronger' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 101: Ascending Beyond Continental Borders into the Upper Heavenly Realm\n"
        "• Ch 107: Awakening the Divine Dragon Maiden & Unlocking Ancient Bloodline Arrays\n"
        "• Ch 114: Heavenly Court Tournament: Humiliating Divine Princes with Synchronized Qi\n"
        "• Ch 121: Secret Realm Infiltration: Harvesting Primordial Chaos Fruits with the Alchemist Saintess\n"
        "• Ch 128: Demonic Invasion Counter-Offensive: Crushing Abyssal Lords with Sword Domain Harmony\n"
        "• Ch 135: Refining the Nine-Revolutions God Physique: Hundredfold System Return Surge\n"
        "• Ch 142: Imperial Matriarch Accord: Forging Immortal Dynasty Alliances\n"
        "• Ch 150: Heavenly Sovereign Coronation: Unrivaled Supreme Master of the Immortal Realms\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#HaremTrainingSystem #ProgressionFantasy #CultivationAudiobook #SystemLitRPG #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (101, 105),
            "title": ["HEAVENLY ASCENSION", "UPPER REALM ARRIVAL"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of the master cultivator ascending to the heavens, calm commanding expression, glowing amber-gold pupils, "
                "wearing radiant pristine white-and-gold immortal robes trimmed with celestial silver runes. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set atop a floating jade celestial staircase bridging mortal clouds to the heavenly court, revealing towering golden palaces and soaring cranes in the distance. "
                "Illumination from heavenly dawn sunlight, iridescent rainbow halos, and ethereal mist, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (106, 110),
            "title": ["DIVINE DRAGON MAIDEN", "ANCIENT BLOODLINE AWAKENING"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the protagonist guiding a striking dragon maiden with elegant pearlescent horns, calm confident posture, "
                "holding an ancient draconic jade seal. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set within a crystalline dragon sanctuary cavern, revealing swirling azure dragon phantoms roaring and illuminating the cavern ceiling in the distance. "
                "Illumination from blinding cyan dragonfire and translucent gold runic arrays, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (111, 115),
            "title": ["HEAVENLY COURT ARENA", "CRUSHING IMMORTAL PRINCES"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of the protagonist standing with effortless nonchalance, hands folded behind his back, cool dismissive smirk. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside the grandiose immortal colosseum carved from floating sun-stone, "
                "revealing arrogant heavenly princes pinned to the arena floor by an invisible atmospheric pressure wave in the distance. "
                "Illumination from brilliant celestial sunbeams and golden combat aura sparks, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (116, 120),
            "title": ["CHAOS GROTTO", "PRIMORDIAL HERB HARVEST"],
            "fallback_color": (15, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist gently inspecting a glowing primordial lotus flower, watchful discerning gaze, "
                "accompanied by his red-haired alchemical saintess disciple. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside a misty subterranean cavern overgrown with bioluminescent primordial roots, revealing ancient guardian statues slumbering in the distance. "
                "Illumination from soft emerald botanical spores and glowing purple lotus petals, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (121, 125),
            "title": ["ABYSSAL INCURSION", "SYNCHRONIZED SWORD HARMONY"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist in decisive combat leadership, sharp commanding expression, channeling synchronized blade energy. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set across the ruined obsidian gates of an immortal border fortress, "
                "revealing abyssal demon commanders incinerated by an impenetrable multi-layered sword formation matrix in the distance. "
                "Illumination from blinding silver sword qi and ominous deep-crimson portal rifts, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (126, 130),
            "title": ["IMPERIAL TEA CEREMONY", "MATRIARCH DIPLOMACY"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of the protagonist pouring spiritual dew from a celadon teapot with regal refinement, subtle charming smile, "
                "wearing tailored midnight-blue scholar robes. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside an open-air celestial pavilion overlooking cascading cloud waterfalls, revealing powerful matriarchs of ancient god-clans listening with deep respect in the distance. "
                "Illumination from warm golden lantern light and twilight sky gradients, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (131, 135),
            "title": ["HUNDREDFOLD SURGE", "NINE-REVOLUTIONS BREAKTHROUGH"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of the protagonist in deep seated meditation, surrounded by concentric rings of pure primordial feedback energy, "
                "flashing divine sigils across his brow. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set upon a floating spirit star platform in the void, revealing nine radiant golden dragons coiling around his spiritual pillar in the distance. "
                "Illumination from blinding white-hot lightning and incandescent gold aura flares, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (136, 140),
            "title": ["IMMORTAL CITADEL", "EXPANDING THE CELESTIAL PALACE"],
            "fallback_color": (20, 30, 40),
            "prompt": (
                "Cinematic 3D portrait of the protagonist surveying his grand immortal estate from a high balcony, calm satisfied smile, "
                "wind gently playing with his dark hair. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set overlooking vast floating jade pavilions, spiritual herb terraces, and training plazas filled with gifted disciples under a starlit twilight sky in the distance. "
                "Illumination from glowing fairy lanterns, starry nebulae, and shimmering defensive ward domes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (141, 145),
            "title": ["TRIBULATION TIDE", "HEAVENLY DAO REWRITTEN"],
            "fallback_color": (25, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of the protagonist challenging the cosmic tribulation clouds, fearless defiant gaze, outstretched palm condensing an omnipotent Dao seal. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set beneath a swirling celestial storm of apocalyptic purple tribulation lightning, "
                "revealing the heavens shattering under his absolute system authority in the distance. "
                "Illumination from crackling deep-violet lightning arcs and brilliant golden divine shockwaves, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (146, 150),
            "title": ["CELESTIAL SOVEREIGN", "SUPREME REALM HEGEMONY"],
            "fallback_color": (20, 20, 55),
            "prompt": (
                "Cinematic 3D portrait of Supreme Sovereign protagonist seated atop the Grand Celestial Throne, serene invincible aura, "
                "eyes glowing with radiant cosmic starlight, wearing the mantle of the Heavenly Master. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside the highest palace of the Immortal Realm, revealing endless ranks of immortal lords and disciples bowing in reverence under a breathtaking celestial aurora sky in the distance. "
                "Illumination from glorious auroras of celestial gold, radiant azure dao flames, and deep nebula starlight, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
