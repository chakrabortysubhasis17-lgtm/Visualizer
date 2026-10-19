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
    "start_url": "https://freewebnovel.com/novel/harem-training-system-every-girl-i-train-makes-me-stronger/chapter-151",
    "start_chapter": 151,
    "end_chapter": 200,
    "default_topic": "Harem Training System",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_harem_training_151_200",
    "final_audio": "output_harem_training_151_200.mp3",
    "final_video": "final_harem_training_151_200.mp4",
    "cover_image": "cover_harem_training_151_200.jpg",
    "timestamps_file": "youtube_timestamps_harem_training_151_200.txt",
    "subtitles_file": "subtitles_harem_training_151_200.srt",
    "payload_file": "youtube_upload_payload_harem_training_151_200.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "PRIMORDIAL GOD-REALM ASCENSION! EXPONENTIAL SYSTEM RETURNS SHATTER HEAVENS [Ch 151-200] | Progression Fantasy Audiobook Marathon",
    "tags": [
        "Harem Training System", "Every Girl I Train Makes Me Stronger", "Progression Fantasy Audiobook",
        "System LitRPG", "Harem Cultivation", "Overpowered MC", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Breaking past the boundaries of the Upper Immortal Courts, our protagonist leads his peerless inner court "
        "into the ancient Primordial God-Realms!\n\n"
        "With the [Harem Training System] continuously evolving into higher-tier multiplier domains, every divine enlightenment, "
        "ancient physique awakening, and primordial bloodline breakthrough achieved by his heroines feeds massive torrents "
        "of god-tier essence directly into his cultivation core. From guiding celestial fox empresses and void sword maidens "
        "to taming arrogant primordial dragon princesses, every disciple breakthrough triggers exponential returns.\n\n"
        "When ancient god-clan patriarchs, supreme star tribunals, and abyssal fiend sovereigns attempt to subjugate his faction, "
        "our protagonist unleashes synchronized domain auras and overwhelming divine power to establish absolute hegemony!\n\n"
        "Welcome to Chapters 151 to 200 of 'Harem Training System: Every Girl I Train Makes Me Stronger' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 151: Entering the Primordial Star-Court Domain & Awakening Ancient Realm Matrices\n"
        "• Ch 156: Guiding the Celestial Nine-Tailed Fox: Unlocking the Primordial Soul Physique\n"
        "• Ch 162: Thousandfold Return Trigger: Absorbing Celestial Dan Energy Overnight\n"
        "• Ch 168: The Grand God-Realm Coliseum: Dismantling Arrogant Divine Princes\n"
        "• Ch 174: Void Sword Empress Awakening: Cleaving Ancient Shackle Arrays in Secret Grottoes\n"
        "• Ch 180: Imperial God-Clan Inquest: Cold Defiance in Front of Supreme Star Patriarchs\n"
        "• Ch 186: Ten-Thousandfold Return Surge: Fusing Multi-Elemental Dao Cores into Godhead\n"
        "• Ch 192: Private Floating Star-Palace: Expanding the Inner Court Sanctuary\n"
        "• Ch 197: Decimating Abyssal Fiend Legions with Synchronized Disciple Sword Arrays\n"
        "• Ch 200: Supreme God-Realm Sovereign: Absolute Master of the Harem Training System\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#HaremTrainingSystem #ProgressionFantasy #CultivationAudiobook #SystemLitRPG #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Streamlined for Zero Generation Failures)
    "blocks": [
        {
            "index": 1, "range": (151, 155),
            "title": ["STAR COURT DOMAIN", "GOD-REALM ARRIVAL"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of a master cultivator entering the Primordial Star Court, calm commanding expression, "
                "amber-gold eyes glowing with divine authority, wearing pristine white-and-gold immortal robes trimmed with celestial silver runes. "
                "Set atop an ancient floating jade pavilion overlooking swirling galaxy nebulae, revealing soaring cranes in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (156, 160),
            "title": ["CELESTIAL FOX EMPRESS", "SOUL PHYSIQUE AWAKENING"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the master cultivator guiding a graceful celestial fox maiden with nine glowing white tails, "
                "calm focused expression, holding an ancient jade scripture scroll. Set inside an ethereal moonlit bamboo sanctuary, "
                "revealing swirling soft pink-and-silver soul mist coalescing in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (161, 165),
            "title": ["THOUSANDFOLD RETURN", "DAN ENERGY SURGE"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of the cultivator in seated meditation, serene composed aura, surrounded by a rising pillar of radiant golden feedback energy. "
                "Set inside a secluded crystal meditation grotto, revealing glowing system status matrices and floating celestial runes in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (166, 170),
            "title": ["GOD-REALM COLISEUM", "CRUSHING DIVINE PRINCES"],
            "fallback_color": (35, 20, 25),
            "prompt": (
                "Cinematic 3D portrait of the cultivator standing with effortless nonchalance, hands tucked behind his back, cool dismissive smirk. "
                "Set in the center of a colossal golden martial arena, revealing arrogant god-clan prodigies knocked back across fractured white-jade tiles in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (171, 175),
            "title": ["VOID SWORD EMPRESS", "SHACKLE SEVERING"],
            "fallback_color": (25, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of the cultivator presenting a radiant dark-steel longsword to a swordswoman disciple, proud noble expression. "
                "Set on a high mountain terrace under twilight skies, revealing ethereal violet sword phantoms cleaving through ancient stone ward pillars in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (176, 180),
            "title": ["STAR CLAN INQUEST", "COLD DEFIANCE"],
            "fallback_color": (25, 25, 35),
            "prompt": (
                "Cinematic 3D portrait of the cultivator standing in absolute defiance, sharp commanding jawline, dark hair fluttering against spiritual pressure. "
                "Set inside a grand star tribunal hall, revealing ancient seated god-clan elders watching with growing unease in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (181, 185),
            "title": ["TEN-THOUSANDFOLD SURGE", "GODHEAD TRANSCENDENCE"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of the cultivator absorbing concentrated multi-colored divine fire, intense resolute gaze, "
                "irises glowing with brilliant golden starlight. Set upon a floating celestial platform, revealing nine revolving elemental rings lighting up the clouds in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (186, 190),
            "title": ["STAR-PALACE SANCTUARY", "INNER COURT HARMONY"],
            "fallback_color": (20, 30, 40),
            "prompt": (
                "Cinematic 3D portrait of the cultivator pouring tea from a white celadon pot, relaxed gentle smile, wearing dark-blue silk robes. "
                "Set inside an open-air celestial pavilion overlooking cascading cloud waterfalls, revealing his peerless disciples practicing sword forms in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (191, 195),
            "title": ["ABYSSAL PURGE", "SYNCHRONIZED SWORD ARRAY"],
            "fallback_color": (30, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of the cultivator directing a grand defensive formation, commanding posture, extending two fingers wrapped in golden qi. "
                "Set along the crumbling stone battlements of a border fortress, revealing encroaching abyssal shadow fiends vaporizing against a golden barrier grid in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (196, 200),
            "title": ["SUPREME SOVEREIGN", "GOD-REALM HEGEMONY"],
            "fallback_color": (20, 20, 55),
            "prompt": (
                "Cinematic 3D portrait of the Supreme God-Realm Sovereign seated upon an imperial dragon-carved throne, serene invincible aura, "
                "radiant golden-and-purple pupils reflecting countless cosmic matrices, wearing majestic midnight-blue sovereign robes. "
                "Set inside the highest palace of the God Realm overlooking endless floating star islands beneath an aurora sky in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
