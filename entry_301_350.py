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
    "novel_slug": "entry-cultivation-i-can-copy-entries",
    "start_url": "https://mtl-novel.com/novel/entry-cultivation-i-can-copy-entries/chapter-301-the-nine-great-demon-sages-deploy-a-strange-formation-the-zhu-xian-sword-formation-suppresses-the-yao-race/",
    "start_chapter": 301,
    "end_chapter": 350,
    "default_topic": "Entry Cultivation",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_entry_cultivation_301_350",
    "final_audio": "output_entry_cultivation_301_350.mp3",
    "final_video": "final_entry_cultivation_301_350.mp4",
    "cover_image": "cover_entry_cultivation_301_350.jpg",
    "timestamps_file": "youtube_timestamps_entry_cultivation_301_350.txt",
    "subtitles_file": "subtitles_entry_cultivation_301_350.srt",
    "payload_file": "youtube_upload_payload_entry_cultivation_301_350.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "ZHU XIAN SWORD FORMATION SUPPRESSES THE YAO RACE! NINE DEMON SAGES CRUSHED [Ch 301-350] | Xianxia Audiobook Marathon",
    "tags": [
        "Entry Cultivation", "I Can Copy Entries", "Lu Yuan", "Zhu Xian Sword Formation",
        "Nine Great Demon Sages", "Xianxia Audiobook", "Progression Fantasy", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Facing the apocalyptic descent of the Nine Great Demon Sages and their primeval beast army, Lu Yuan unleashes "
        "the legendary Zhu Xian Sword Formation to suppress the ancient Yao race!\n\n"
        "While holy land armies retreat and immortal sects suffer catastrophic casualties, Lu Yuan remains utterly composed. "
        "Behind the veil of chaos, he quietly scans and replicates unprecedented divine and primeval entries, including "
        "[Zhu Xian Slaughter Intent], [Demon Sage Primordial Bloodline], [Ancient Formation Sovereign], and [Undying Yao Core]. "
        "Every copied attribute reinforces his transcendent foundation while neutralizing lethal curses without a shred of karmic backlash.\n\n"
        "Watch Lu Yuan turn a continent-ending demonic war into his personal realm-breakthrough harvest while maintaining his "
        "signature low-profile mastery!\n\n"
        "Welcome to Chapters 301 to 350 of 'Entry Cultivation: I Can Copy Entries' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 301: The Nine Great Demon Sages Deploy the Beast Formation & The Zhu Xian Sword Formation Awakens\n"
        "• Ch 306: Replicating the Primeval Demon Sage Core Entries Amid Battlefield Chaos\n"
        "• Ch 312: Slaughter Qi Condensation: Fusing Four Divine Sword Intents into the Sovereign Array\n"
        "• Ch 318: Shattering the Blood-Moon Beast Barrier with Invisible Spatial Sword Threads\n"
        "• Ch 324: Ancient Yao Treasury Infiltration: Harvesting Dormant Divine Dragon Marrow in Secret\n"
        "• Ch 330: Counter-Purging Demonic Infiltrators with Zero Karmic Residual Trace\n"
        "• Ch 336: Nascent Soul Perfection: Ascending toward the Soul Transformation Realm\n"
        "• Ch 342: Demon Sage Truce Accord: Forcing Ancient Beast Overlords to Retreat\n"
        "• Ch 350: Continental Grand Sovereign: Master of the Zhu Xian Sword Formation\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#EntryCultivation #ICanCopyEntries #XianxiaAudiobook #ProgressionFantasy #CultivationAudiobook #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (301, 305),
            "title": ["ZHU XIAN FORMATION", "SUPPRESSING THE YAO RACE"],
            "fallback_color": (30, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of young cultivator Lu Yuan standing atop a stormy fortress wall, calm resolute expression, "
                "eyes reflecting four glowing red-and-gold flying swords, wearing dark charcoal-blue elder robes. "
                "Set against dark storm clouds, revealing the colossal crimson Zhu Xian Sword Formation descending over fleeing demon beasts in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (306, 310),
            "title": ["DEMON SAGE CORE", "ENTRY EXTRACTION"],
            "fallback_color": (35, 20, 20),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan inspecting translucent golden entry panels hovering in the air, composed analytical smirk, "
                "fingers lightly tapping an ancient jade talisman. Set inside a shattered battlefield fortress, revealing the defeated avatar of an ancient Demon Sage dissolving into golden sparks in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (311, 315),
            "title": ["FOUR SWORD INTENTS", "SLAUGHTER QI CONDENSATION"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan surrounded by four miniature ethereal swords orbiting his shoulders, serene focused posture, "
                "palms channeling concentrated white sword energy. Set atop a high mountain altar, revealing concentric shockwaves cutting cleanly through mist and stone pillars in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (316, 320),
            "title": ["BLOOD-MOON CRUSH", "SPATIAL SEVERING"],
            "fallback_color": (40, 15, 20),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan executing a silent sword technique, cold decisive gaze, two fingers raised toward an ominous crimson moon. "
                "Set along a jagged canyon ridge under blood-red moonlight, revealing a colossal demon array barrier shattering into glowing red glass shards in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (321, 325),
            "title": ["YAO TREASURY", "DIVINE MARROW HARVEST"],
            "fallback_color": (20, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan inspecting a glowing crystal urn of golden dragon marrow, watchful calculating gaze, "
                "wearing a hooded traveler mantle. Set inside a concealed underground cavern filled with ancient beast relics, revealing giant sleeping stone dragon statues lined along the hall in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (326, 330),
            "title": ["STEALTH COUNTER-PURGE", "ZERO KARMIC RESIDUE"],
            "fallback_color": (25, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan in swift stealth stance, resolute sharp eyes, hair windswept by kinetic air currents. "
                "Set in a shadowed bamboo grove at midnight, revealing masked demonic spies dissolving into harmless gray spiritual dust without leaving traces in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (331, 335),
            "title": ["NASCENT SOUL ASCENSION", "CORE EXPANSION"],
            "fallback_color": (30, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan in deep cross-legged meditation, serene transcendent presence, glowing golden and violet entry characters orbiting his chest. "
                "Set inside a sealed mountain cultivation cave, revealing brilliant purple spiritual shockwaves illuminating carved stone walls in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (336, 340),
            "title": ["DEMON SAGE ACCORD", "PEACE THROUGH STRENGTH"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan standing calmly before a grand stone treaty stele, subtle composed smile, dark robes billowing in the wind. "
                "Set upon a desolate border plateau between realms, revealing massive beast overlord silhouettes retreating into distant mountain fog in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (341, 345),
            "title": ["SECT SANCTUARY", "PRIVATE SPIRIT DOMAIN"],
            "fallback_color": (20, 30, 40),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan overlooking his private mountain valley, calm satisfied demeanor, holding an unadorned tea cup. "
                "Set on a timber pavilion balcony overlooking terraced spirit herb fields, revealing protective sword arrays humming softly across mountain peaks in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (346, 350),
            "title": ["SWORD SOVEREIGN", "PEAK CONTINENTAL SUPREMACY"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Sovereign Master Lu Yuan standing at the pinnacle of continental peaks at sunset, serene invincible posture, "
                "eyes glowing with radiant golden entry matrices, wearing refined midnight-blue robes. Set against an endless sea of clouds dotted with floating sect islands in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
