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
    "start_url": "https://freewebnovel.com/novel/harem-training-system-every-girl-i-train-makes-me-stronger/chapter-51",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "Harem Training System",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_harem_training_051_100",
    "final_audio": "output_harem_training_051_100.mp3",
    "final_video": "final_harem_training_051_100.mp4",
    "cover_image": "cover_harem_training_051_100.jpg",
    "timestamps_file": "youtube_timestamps_harem_training_051_100.txt",
    "subtitles_file": "subtitles_harem_training_051_100.srt",
    "payload_file": "youtube_upload_payload_harem_training_051_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "EXPANDING THE SUPREME SECT EMPIRE! SYSTEM MULTIPLIERS OVERLOAD [Ch 51-100] | Progression Fantasy Audiobook Marathon",
    "tags": [
        "Harem Training System", "Every Girl I Train Makes Me Stronger", "Progression Fantasy Audiobook",
        "System LitRPG", "Harem Cultivation", "Overpowered MC", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Breaking past regional borders, the protagonist and his elite faction of inner disciples enter the fierce continental arenas!\n\n"
        "With the [Harem Training System] generating astronomical cultivation returns, every breakthrough, sword form mastery, and alchemical "
        "enlightenment achieved by his circle of peerless heroines feeds directly into his own divine foundation. From rival dynastic sects "
        "and ancient martial patriarchs to hidden monster domains, anyone attempting to challenge his growing empire is systematically dismantled!\n\n"
        "Watch him unlock divine-grade martial inheritances, forge unbreakable spiritual bonds, and cement absolute hegemony across the realm!\n\n"
        "Welcome to Chapters 51 to 100 of 'Harem Training System: Every Girl I Train Makes Me Stronger' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 51: Entering the Continental Sect Arena & Shocking the Imperial Elders\n"
        "• Ch 58: Unlocking the Ancient Sword Spirit Physique with the Sword Saintess\n"
        "• Ch 65: Continental Auction House Incursion: Bidding for Divine-Grade Cultivation Herbs\n"
        "• Ch 72: Defeating the Shadow Sect Assassins with Synchronized Dual-Sync Defenses\n"
        "• Ch 79: Awakening the Phoenix Bloodline Inheritance in the Volcanic Secret Realm\n"
        "• Ch 86: Defying the Royal Dynasty's Decree and Establishing Autonomous Sovereign Land\n"
        "• Ch 93: Sovereign Martial Domain Expansion: Merging Disciples' Auras into a Single God-Seal\n"
        "• Ch 100: Continental Supremacy Coronation: Absolute Mastery of the Harem Training System\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#HaremTrainingSystem #ProgressionFantasy #CultivationAudiobook #SystemLitRPG #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (51, 55),
            "title": ["CONTINENTAL ARENA", "SHOCKING THE IMPERIAL ELDERS"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of the master cultivator standing with effortless confidence, intelligent amber-gold eyes, "
                "wearing immaculate white-and-silver sovereign daoist robes. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside the majestic white-jade colosseum of the continental arena, revealing stunned imperial elders staring in disbelief at towering cultivation rank pillars in the distance. "
                "Illumination from bright stadium sunlight and shimmering gold-and-azure energy rings, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (56, 60),
            "title": ["ANCIENT SWORD SPIRIT", "SWORD SAINTESS AWAKENING"],
            "fallback_color": (15, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of the protagonist mentoring the elegant Sword Saintess, calm focused expression, "
                "holding an ancient engraved blade radiating blinding silver qi. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set across a misty stone cliffside training terrace, revealing giant ethereal sword phantoms splitting drifting clouds in the distance. "
                "Illumination from brilliant silver blade light and soft azure spiritual mist, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (61, 65),
            "title": ["AUCTION HOUSE INCURSION", "ACQUIRING DIVINE HERBS"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of the protagonist bidding with casual aristocratic poise, holding a jade token, calm amused smirk. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a grand multi-tiered continental auction hall, "
                "revealing rival dynastic young masters grinding their teeth in frustration as a floating glowing divine herb is unveiled in the distance. "
                "Illumination from warm brass chandeliers and magenta magical display lights, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (66, 70),
            "title": ["SHADOW SECT PURGE", "SYNCHRONIZED DEFENSES"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist in decisive combat readiness, sharp analytical glare, dark hair whipping back. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a shadowed night-shrouded courtyard, "
                "revealing elite stealth assassins deflected and trapped inside a shimmering golden barrier matrix in the distance. "
                "Illumination from crackling deep-blue lightning sparks and sharp dagger reflections, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (71, 75),
            "title": ["VOLCANIC SECRET REALM", "PHOENIX BLOODLINE AWAKENING"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of the protagonist guiding his elite disciples through intense spiritual heat, resolute calm gaze. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set within a subterranean volcanic grotto, "
                "revealing a magnificent crimson phoenix spirit bursting from molten magma pillars in the distance. "
                "Illumination from roaring red lava flows and brilliant white-hot plasma light, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (76, 80),
            "title": ["ROYAL DECREE DEFIANCE", "ESTABLISHING AUTONOMY"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist tearing up a golden imperial proclamation with calm disdain, sharp commanding jawline. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set on the grand marble steps of his newly expanded mountain palace, "
                "revealing royal envoys retreating in absolute terror under his mounting aura pressure in the distance. "
                "Illumination from bright morning sunlight and radiant golden soul seals, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (81, 85),
            "title": ["DIVINE PILL CONCOCTION", "ALCHEMICAL TRANSCENDENCE"],
            "fallback_color": (35, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist coordinating advanced pill refinement, artistic concentration, hands directing multiple flames. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside the master alchemical hall, "
                "revealing nine floating pearlescent medicinal pills emitting dragon roars inside a giant crystal furnace in the distance. "
                "Illumination from vibrant violet magical flames and golden medicinal aura, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (86, 90),
            "title": ["MARTIAL DOMAIN EXPANSION", "GOD-SEAL CONVERGENCE"],
            "fallback_color": (20, 35, 30),
            "prompt": (
                "Cinematic 3D portrait of the protagonist expanding a massive universal combat domain, commanding posture, dual-colored irises flashing. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set high above the cloud layer across floating mountain peaks, "
                "revealing synchronized disciple energy streams merging into an impenetrable continental defense shield in the distance. "
                "Illumination from radiant emerald qi and blinding gold boundary rings, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (91, 95),
            "title": ["SUPREME SECT CLASH", "CRUSHING THE ANCIENT PATRIARCHS"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the protagonist unleashing ultimate system power, terrifying sovereign gaze, dark hair trailing golden sparks. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set across a shattered celestial battlefield, "
                "revealing ancient closed-door martial patriarchs crashing into the bedrock under absolute pressure in the distance. "
                "Illumination from brilliant white energy shockwaves and deep-purple portal rifts, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (96, 100),
            "title": ["CONTINENTAL SUPREMACY", "ABSOLUTE REALM MASTERY"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Supreme Sovereign Leader protagonist seated upon a magnificent celestial dragon throne, serene invincible presence, "
                "commanding golden pupils, wearing supreme sovereign robes. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set overlooking an endless unified continental empire filled with thriving sects and soaring phoenixes under an awe-inspiring aurora sky. "
                "Illumination from brilliant auroras of sunrise gold, cyan spiritual energy, and starlit nebulas, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
