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
    "start_url": "https://freewebnovel.com/novel/harem-training-system-every-girl-i-train-makes-me-stronger/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Harem Training System",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_harem_training_001_050",
    "final_audio": "output_harem_training_001_050.mp3",
    "final_video": "final_harem_training_001_050.mp4",
    "cover_image": "cover_harem_training_001_050.jpg",
    "timestamps_file": "youtube_timestamps_harem_training_001_050.txt",
    "subtitles_file": "subtitles_harem_training_001_050.srt",
    "payload_file": "youtube_upload_payload_harem_training_001_050.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "EVERY DISCIPLE TRAINED MAKES ME GOD-TIER! ULTIMATE HAREM SYSTEM AWAKENING [Ch 1-50] | Progression Fantasy Audiobook Marathon",
    "tags": [
        "Harem Training System", "Every Girl I Train Makes Me Stronger", "Progression Fantasy Audiobook",
        "System LitRPG", "Harem Cultivation", "Overpowered MC", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Reincarnated into a brutal fantasy martial arts world where supreme strength dictates destiny, our protagonist "
        "awakens the ultimate [Harem Training System]—where every talented heroine, discipline candidate, and fierce martial sister "
        "he trains, nurtures, and empowers directly multiplies his own combat foundation, elemental mastery, and lifespan!\n\n"
        "Instead of walking the lonely path of traditional seclusion, he gathers an elite circle of peerless beauties with unique hidden physiques. "
        "From refining rebellious sword saintesses and taming proud demon princesses to guiding clumsy alchemical geniuses, every breakthrough "
        "they achieve sends tidal waves of synchronized cultivation feedback straight into his dantian!\n\n"
        "Watch him build an invincible faction from scratch, unlock game-breaking system skills, and ascend to the apex of the realm through supreme guidance!\n\n"
        "Welcome to Chapters 1 to 50 of 'Harem Training System: Every Girl I Train Makes Me Stronger' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 01: Reincarnation into the Sect & Awakening the Ultimate Harem Training System\n"
        "• Ch 07: Recruiting the First Disciple: Unlocking the Ice-Phoenix Martial Physique\n"
        "• Ch 14: System Feedback Multipliers: Gaining Tenfold Cultivation Returns Overnight\n"
        "• Ch 21: Sect Competition Incursion: Humiliating Arrogant Elder Disciples with Dual-Sync Power\n"
        "• Ch 28: Discovering the Alchemical Saintess & Crafting Mythic Pill Formulations\n"
        "• Ch 35: Defending the Territory: Crushing Bandit Warlords with Synchronized Sword Formations\n"
        "• Ch 42: Expanding the Inner Court: Welcoming the Rebellious Demon Princess into the Faction\n"
        "• Ch 50: Sovereign Training Domain: Achieving Foundation Transcendence and Regional Supremacy\n\n"
        "══════════════════════════════════════════════\nDCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#HaremTrainingSystem #ProgressionFantasy #CultivationAudiobook #SystemLitRPG #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (1, 5),
            "title": ["SYSTEM AWAKENING", "THE NEW JOURNEY"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of a brilliant young master cultivator, sharp chiseled jawline, intelligent piercing amber-gold eyes, "
                "wearing immaculate white-and-gold daoist scholar robes. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside an ancient mountain sect hall at dawn, revealing glowing translucent golden system assignment panels floating in the air before him in the distance. "
                "Illumination from warm sunrise light and magical system matrices, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (6, 10),
            "title": ["ICE-PHOENIX DISCIPLE", "FIRST RECRUITMENT"],
            "fallback_color": (15, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of the protagonist guiding a proud young female disciple with long silvery-blue hair, calm confident posture, "
                "holding an ancient jade training scroll. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set across a frozen waterfall training courtyard, revealing swirling sapphire ice-phoenix aura ripples coalescing around the disciple in the distance. "
                "Illumination from glittering ice crystals and soft cyan spiritual mist, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (11, 15),
            "title": ["CULTIVATION FEEDBACK", "TENFOLD MULTIPLIER"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of the protagonist experiencing sudden transcendent power absorption, intense focused expression, dark hair whipping back, "
                "surrounded by a rising pillar of golden feedback energy. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside a secluded meditation chamber, revealing concentric ring symbols expanding across the stone floor in the distance. "
                "Illumination from blinding gold-and-amber energy surges, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (16, 20),
            "title": ["SECT COMPETITION", "HUMILIATING RIVALS"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist standing with calm aristocratic indifference, hands behind his back, cold amused gaze. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set in a grand outdoor martial arena of the grand sect, "
                "revealing arrogant elder disciples blown backward off the stage by an invisible pressure wave in the distance. "
                "Illumination from bright afternoon sunlight and vibrant violet combat sparks, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (21, 25),
            "title": ["ALCHEMICAL SAINTESS", "PILL CRAFTING MASTERY"],
            "fallback_color": (40, 20, 20),
            "prompt": (
                "Cinematic 3D portrait of the protagonist mentoring a talented red-haired female alchemist, warm encouraging smile, guiding her hands over a brass burner. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a fragrant alchemical pavilion filled with botanical herbs, "
                "revealing a giant crystal cauldron emitting pearlescent medicinal smoke rings in the distance. "
                "Illumination from roaring crimson furnace flames and golden pill light, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (26, 30),
            "title": ["TERRITORY DEFENSE", "BANDIT WARLORD PURGE"],
            "fallback_color": (25, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of the protagonist in decisive combat leadership, sharp commanding expression, holding an engraved spiritual longsword. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set along the rugged stone mountain gates of his expanding faction estate, "
                "revealing invading bandit warlords trapped inside a synchronized sword formation matrix in the distance. "
                "Illumination from flashing silver blade qi and twilight sky gradients, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (31, 35),
            "title": ["INNER COURT EXPANSION", "DEMON PRINCESS ALLIANCE"],
            "fallback_color": (35, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist in intriguing negotiation with a striking demon princess adorned with subtle dark horns, "
                "calm composed smirk. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside an opulent candlelit inner court reception hall, revealing ancient scrolls and glowing spirit wine decanters on mahogany tables in the distance. "
                "Illumination from warm brass chandeliers and deep amethyst shadow glows, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (36, 40),
            "title": ["MARTIAL BREAKTHROUGH", "SYNCHRONIZED ASCENSION"],
            "fallback_color": (20, 35, 30),
            "prompt": (
                "Cinematic 3D portrait of the protagonist executing high-tier martial arts forms, fluid graceful posture, hands leaving trails of shimmering light. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set upon a high spiritual energy waterfall platform, "
                "revealing multiple female disciples meditating below while absorbing shared breakthrough auras in the distance. "
                "Illumination from radiant emerald qi and midday sunlight reflecting off water mist, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (41, 45),
            "title": ["SECTOR INQUISITION", "CRUSHING THE SECT ELDERS"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the protagonist unleashing overwhelming system pressure, terrifying cold sovereign gaze, dark hair whipping back. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside the main elder assembly hall, "
                "revealing corrupt sect elders trembling and kneeling under insurmountable spiritual weight in the distance. "
                "Illumination from crackling deep-blue lightning and blinding white system flares, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (46, 50),
            "title": ["SOVEREIGN DOMAIN", "THE ULTIMATE FACTION"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Sovereign Leader protagonist seated upon a magnificent dragon-carved jade throne, serene invincible presence, "
                "commanding golden irises, wearing supreme sovereign robes. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set overlooking a sprawling, majestic floating immortal mountain sect filled with powerful disciples and soaring phoenixes under an aurora sky. "
                "Illumination from brilliant auroras of sunrise gold, cyan spiritual energy, and starlit nebulas, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
