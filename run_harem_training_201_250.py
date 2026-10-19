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
    "start_url": "https://freewebnovel.com/novel/harem-training-system-every-girl-i-train-makes-me-stronger/chapter-201",
    "start_chapter": 201,
    "end_chapter": 250,
    "default_topic": "Harem Training System",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_harem_training_201_250",
    "final_audio": "output_harem_training_201_250.mp3",
    "final_video": "final_harem_training_201_250.mp4",
    "cover_image": "cover_harem_training_201_250.jpg",
    "timestamps_file": "youtube_timestamps_harem_training_201_250.txt",
    "subtitles_file": "subtitles_harem_training_201_250.srt",
    "payload_file": "youtube_upload_payload_harem_training_201_250.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "HEAVENLY DAO TRAINING SOVEREIGN! 100,000X MULTIPLIER TRANSCENDENCE [Ch 201-250] | Progression Fantasy Audiobook Marathon",
    "tags": [
        "Harem Training System", "Every Girl I Train Makes Me Stronger", "Progression Fantasy Audiobook",
        "System LitRPG", "Harem Cultivation", "Overpowered MC", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Transcending the Primordial God-Realms, our protagonist leads his inner court into the supreme Heavenly Dao Star Domains!\n\n"
        "With the [Harem Training System] unlocking astronomical 100,000x multiplier feedback loops, every sacred breakthrough "
        "achieved by his disciples floods his foundation with boundless origin essence. Guiding Divine Phoenix Princesses through "
        "sacred nirvana fires, elevating Starlight Alchemists to pill godhood, and untying the primordial shackles of Void Valkyries, "
        "his personal cultivation ascends past mortal comprehension.\n\n"
        "When supreme Holy Land Ancestors, ancient cosmic star alliances, and abyssal demon courts conspire to suppress his rising faction, "
        "our protagonist unleashes synchronized domain authority and god-tier formation arrays to establish absolute dominion!\n\n"
        "Welcome to Chapters 201 to 250 of 'Harem Training System: Every Girl I Train Makes Me Stronger' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 201: Crossing into the Heavenly Dao Star Domain & Unlocking 100,000x System Multipliers\n"
        "• Ch 206: Divine Phoenix Princess Nirvana Awakening: Absorbing Cosmic Flame Feedback\n"
        "• Ch 212: Heavenly Dao Arena Showdown: Crushing Holy Land Prodigies with Effortless Aura\n"
        "• Ch 218: Void Valkyrie Trial: Cleaving Ancient Dimensional Seals in Secret Grottoes\n"
        "• Ch 225: The Star Court Ancestor Inquest: Cold Defiance in the Apex Tribunal\n"
        "• Ch 231: Starlight Alchemy Mastery: Refining Divine Sovereign Elixirs Overnight\n"
        "• Ch 237: Constructing the Grand Celestial Sanctuary: Expanding the Inner Court Domain\n"
        "• Ch 242: Decimating Abyssal Demon Invasions with Synchronized Disciple Formations\n"
        "• Ch 247: Primordial Soul Resonance: Fusing Multi-Elemental Domains into Absolute Authority\n"
        "• Ch 250: Supreme Heavenly Dao Sovereign: Undisputed Ruler of the Infinite Courts\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#HaremTrainingSystem #ProgressionFantasy #CultivationAudiobook #SystemLitRPG #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Streamlined for Zero Generation Failures)
    "blocks": [
        {
            "index": 1, "range": (201, 205),
            "title": ["HEAVENLY DAO DOMAIN", "STAR SANCTUARY ARRIVAL"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of a master cultivator entering the Heavenly Dao Star Domain, serene commanding posture, "
                "amber-gold eyes glowing with celestial authority, wearing immaculate white-and-gold robes trimmed with silver starlight embroidery. "
                "Set atop an ancient floating jade platform, revealing massive golden gates and swirling purple nebulae in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (206, 210),
            "title": ["PHOENIX PRINCESS", "NIRVANA FLAME AWAKENING"],
            "fallback_color": (35, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of the master cultivator guiding a regal female disciple, calm focused expression, "
                "holding a radiant crimson spirit feather. Set inside a luminous volcanic sanctum, "
                "revealing swirling golden-red phoenix firewings expanding across carved stone pillars in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (211, 215),
            "title": ["HUNDRED-THOUSANDFOLD SURGE", "ORIGIN ESSENCE FEEDBACK"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of the cultivator in seated meditation, serene divine presence, "
                "golden origin runes glowing across his cheekbones and forehead. Set inside a secluded crystal meditation grotto, "
                "revealing concentric shockwaves of pure golden essence lighting up the walls in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (216, 220),
            "title": ["DAO ARENA CLASH", "CRUSHING HOLY SCIONS"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of the cultivator standing with hands behind his back, cool dismissive smirk, "
                "dark hair fluttering in kinetic wind currents. Set in the center of a colossal floating arena, "
                "revealing arrogant holy land champions knocked onto fractured jade flagstones in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (221, 225),
            "title": ["VOID VALKYRIE", "SEVERING DIMENSIONAL SEALS"],
            "fallback_color": (25, 15, 40),
            "prompt": (
                "Cinematic 3D portrait of the cultivator presenting a slender dark longsword to an armored swordswoman disciple, proud noble expression. "
                "Set on a high stone precipice under violet twilight skies, revealing razor-thin spatial fissures cutting through ancient ward pillars in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (226, 230),
            "title": ["STAR ANCESTOR TRIBUNAL", "COLD DEFIANCE"],
            "fallback_color": (25, 25, 35),
            "prompt": (
                "Cinematic 3D portrait of the cultivator standing in absolute defiance, sharp commanding jawline, "
                "wearing high-rank dark-blue robes with silver cloud motifs. Set inside a grandiose celestial star chamber, "
                "revealing ancient seated elders watching with visible apprehension in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (231, 235),
            "title": ["STARLIGHT ALCHEMY", "DIVINE ELIXIR REFINEMENT"],
            "fallback_color": (20, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of the cultivator inspecting a hovering iridescent pill, attentive scholarly focus, "
                "fingers lightly directing swirling azure spiritual fires. Set inside an opulent alchemy pavilion, "
                "revealing an ancient bronze cauldron emitting dragon-shaped pill clouds in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (236, 240),
            "title": ["CELESTIAL SANCTUARY", "INNER COURT HARMONY"],
            "fallback_color": (20, 30, 30),
            "prompt": (
                "Cinematic 3D portrait of the cultivator pouring tea from a celadon pot, relaxed gentle smile, handsome defined features. "
                "Set inside an open-air pavilion overlooking misty mountain waterfalls, revealing his peerless disciples conversing harmoniously in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (241, 245),
            "title": ["DEMON PURGE", "SYNCHRONIZED SWORD DOMAIN"],
            "fallback_color": (30, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of the cultivator directing a grand defensive formation, commanding authoritative posture, "
                "two fingers extended with glowing golden sword qi. Set along the crumbling stone walls of a border citadel, "
                "revealing invading abyssal demon beasts dissolving into ash against a golden barrier grid in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (246, 250),
            "title": ["HEAVENLY DAO SOVEREIGN", "SUPREME THRONE ASCENSION"],
            "fallback_color": (20, 20, 55),
            "prompt": (
                "Cinematic 3D portrait of the Supreme Heavenly Dao Sovereign seated upon a massive carved jade throne, serene invincible aura, "
                "radiant golden pupils reflecting cosmic entry matrices, wearing majestic midnight-blue robes. "
                "Set inside the highest palace of the Heavenly Star Realm overlooking boundless floating continents beneath an aurora sky in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
