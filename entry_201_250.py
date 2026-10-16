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
    "start_url": "https://mtl-novel.com/novel/entry-cultivation-i-can-copy-entries/chapter-201-nine-colored-creation-spiritual-root-the-three-nine-heavenly-tribulation/",
    "start_chapter": 201,
    "end_chapter": 250,
    "default_topic": "Entry Cultivation",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_entry_cultivation_201_250",
    "final_audio": "output_entry_cultivation_201_250.mp3",
    "final_video": "final_entry_cultivation_201_250.mp4",
    "cover_image": "cover_entry_cultivation_201_250.jpg",
    "timestamps_file": "youtube_timestamps_entry_cultivation_201_250.txt",
    "subtitles_file": "subtitles_entry_cultivation_201_250.srt",
    "payload_file": "youtube_upload_payload_entry_cultivation_201_250.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "NINE-COLORED CREATION SPIRITUAL ROOT! TRANSCENDING THREE-NINE HEAVENLY TRIBULATION [Ch 201-250] | Xianxia Progression Audiobook Marathon",
    "tags": [
        "Entry Cultivation", "I Can Copy Entries", "Lu Yuan", "Nine Colored Spiritual Root",
        "Heavenly Tribulation", "Xianxia Audiobook", "Progression Fantasy", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Reaching the pinnacle of worldly cultivation, Lu Yuan triggers the mythic [Nine-Colored Creation Spiritual Root] "
        "and faces the terrifying Three-Nine Heavenly Tribulation!\n\n"
        "While ancient sect patriarchs and reclusive holy lands look on in horror as apocalyptic thunderclouds shroud "
        "the continent, Lu Yuan remains unshakeable. Quietly copying divine primordial entries including [Heaven-Defying Creation Core], "
        "[Tribulation Lightning Absorption], and [Five Elements Dao Quintessence], he transforms lethal heavenly punishment into pure, "
        "boundless essence for his Nascent Soul ascension!\n\n"
        "From deciphering primordial secret grottoes and out-refining immortal alchemists to slaughtering blood-fiend covens "
        "without generating an ounce of karmic retribution, witness Lu Yuan solidify his reign as the ultimate low-key immortal overlord!\n\n"
        "Welcome to Chapters 201 to 250 of 'Entry Cultivation: I Can Copy Entries' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 201: Awakening the Mythic [Nine-Colored Creation Spiritual Root] & Apocalyptic Tribulation Clouds Gathering\n"
        "• Ch 206: Surviving the Three-Nine Heavenly Tribulation with Flawless Entry Defenses\n"
        "• Ch 212: Replicating Ancient Nascent Soul Patriarchs' Law Comprehension Entries\n"
        "• Ch 218: Secret Abyssal Realm Expedition: Harvesting Primordial Chaos Lotus Nectar\n"
        "• Ch 225: The Five Elements Great Array: Fusing Elemental Entries into Supreme Quintessence\n"
        "• Ch 232: Decimating Blood-Demon Sect Elders with Zero Karmic Traces\n"
        "• Ch 238: Continental Grand Pill Contest: Out-Refining Ancient Alchemy Immortals\n"
        "• Ch 245: Unveiling the Spatial Tear Sanctuary & Expanding Private Spirit Domain\n"
        "• Ch 250: Absolute Heavenly Sovereign: Master of All Innate Creation Entries\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#EntryCultivation #ICanCopyEntries #XianxiaAudiobook #ProgressionFantasy #CultivationAudiobook #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (201, 205),
            "title": ["NINE-COLORED AWAKENING", "TRIBULATION CLOUDS"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of cultivator Lu Yuan standing atop a storm-swept mountain precipice, calm resolute expression, "
                "eyes swirling with prismatic nine-colored spiritual light, wearing dark midnight-blue inner elder robes. Flawless facial features, "
                "crisp detailed skin textures, medium close-up shot. Set beneath a swirling celestial vortex of apocalyptic black-and-purple tribulation clouds, "
                "revealing crackling lightning serpents illuminating mountain peaks in the distance. Illumination from blinding purple tribulation lightning "
                "and radiant iridescent soul halos, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (206, 210),
            "title": ["THREE-NINE TRIBULATION", "LIGHTNING ABSORPTION"],
            "fallback_color": (25, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan surrounded by a golden lightning barrier, composed dignified posture, raising an outstretched hand "
                "to absorb a falling bolt of heavenly lightning. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside a shattered crater on an ancient sacrificial platform, revealing concentric shockwaves of pure golden energy rippling across solid granite in the distance. "
                "Illumination from blinding white-hot lightning arcs and vibrant golden entry runes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (211, 215),
            "title": ["PATRIARCH ENCOUNTER", "COSMIC LAW REPLICATION"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan inspecting glowing golden status matrices hovering in mid-air, calm perceptive smirk, "
                "fingers tracing floating celestial characters. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set within a high-altitude cloud pavilion overlooking misty peaks, revealing an ancient Nascent Soul patriarch meditating unknowingly in the distance. "
                "Illumination from warm golden afternoon sunbeams and radiant floating script reflections, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (216, 220),
            "title": ["ABYSSAL REALM", "CHAOS LOTUS NECTAR"],
            "fallback_color": (15, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan harvesting a radiant primordial lotus flower, watchful calculating eyes, "
                "holding a delicate carved mutton-fat jade container. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside a bioluminescent subterranean grotto overgrown with ancient glowing roots, revealing a subterranean spirit lake glistening with liquid starlight in the distance. "
                "Illumination from soft emerald plant spores and iridescent cyan lotus vapors, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (221, 225),
            "title": ["FIVE ELEMENTS ARRAY", "QUINTESSENCE FUSION"],
            "fallback_color": (35, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan in profound cross-legged meditation, serene divine presence, five elemental spheres "
                "of gold, wood, water, fire, and earth orbiting his shoulders. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set upon a massive floating stone formation platform carved with elemental seal matrices, revealing swirling vortexes of elemental energy in the distance. "
                "Illumination from brilliant multi-colored elemental lights casting sharp highlights and deep shadows, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (226, 230),
            "title": ["BLOOD-DEMON AMBUSH", "SILENT KARMIC PURGE"],
            "fallback_color": (25, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan executing a silent spatial strike, cold decisive glare, fingertips crackling with razor-thin wind-blade qi. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set along a jagged moonlit mountain pass under drifting mist, "
                "revealing blood-demon sect ambushers disintegrating into harmless gray spiritual dust without leaving a single trace of blood or karma in the distance. "
                "Illumination from pale silver moonlight and razor-thin blade glints, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (231, 235),
            "title": ["GRAND PILL CONTEST", "IMMORTAL ELIXIR REFINING"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan directing multi-colored spiritual alchemy flames into an ancient bronze cauldron, artistic concentration, "
                "palms releasing delicate alchemical mudras. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside the grandiose open-air arena of the Continental Alchemy Guild, revealing stunned grandmaster alchemists staring at dragon-shaped pill clouds in the distance. "
                "Illumination from roaring vermilion furnace fires and radiant golden pill auras, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (236, 240),
            "title": ["CORE ELDER GATHERING", "FLAWLESS CONCEALMENT"],
            "fallback_color": (20, 30, 40),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan sitting quietly in a council meeting, subtle composed smile, dark hair tied neatly with a carved jade hairpin, "
                "wearing elegant dark-blue sect robes. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside an opulent council hall with towering incense burners and carved dragon pillars, revealing powerful supreme elders debating intensely while oblivious to his real strength in the distance. "
                "Illumination from warm morning sunbeams through high wooden latticework, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (241, 245),
            "title": ["SPATIAL TEAR SANCTUARY", "PRIVATE SPIRIT DOMAIN"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan expanding a private spatial domain, commanding authoritative stance, extended palm revealing shimmering spatial cracks. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a concealed dimensional fold filled with floating islands and spiritual herb gardens, "
                "revealing ethereal ward barriers protecting the sanctuary from outside detection in the distance. "
                "Illumination from radiant violet spatial currents and soft cyan starlight, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (246, 250),
            "title": ["CREATION SOVEREIGN", "PEAK ASCENSION"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Supreme Sovereign Master Lu Yuan standing at the pinnacle of the continental peaks at sunset, "
                "serene invincible presence, irises glowing with nine-colored creation matrices, wearing midnight-blue elder robes billowing gracefully in the wind. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set overlooking an endless sea of clouds dotted with soaring cranes and distant floating immortal sanctuaries in the distance. "
                "Illumination from rich golden sunset rays, vibrant twilight nebulae, and shimmering golden entry runes, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
