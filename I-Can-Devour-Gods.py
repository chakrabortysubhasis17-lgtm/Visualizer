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

    # Novel & Episode Parameters (45 chapters to keep runtime comfortably under 12 hours)
    "novel_slug": "sss-awakening-i-can-devour-gods-to-evolve-my-goddesses",
    "start_url": "https://freewebnovel.com/novel/sss-awakening-i-can-devour-gods-to-evolve-my-goddesses/chapter-1",
    "start_chapter": 1,
    "end_chapter": 45,
    "default_topic": "God Devourer",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,  # Sequential processing to respect 15 RPM limits cleanly
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_sss_awakening_devour_gods_001_045",
    "final_audio": "output_sss_awakening_devour_gods_001_045.mp3",
    "final_video": "final_sss_awakening_devour_gods_001_045.mp4",
    "cover_image": "cover_sss_awakening_devour_gods_001_045.jpg",
    "timestamps_file": "youtube_timestamps_sss_awakening_devour_gods_001_045.txt",
    "subtitles_file": "subtitles_sss_awakening_devour_gods_001_045.srt",
    "payload_file": "youtube_upload_payload_sss_awakening_devour_gods_001_045.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "AWAKENING SSS GOD DEVOURER! EVOLVING MY DIVINE GODDESSES [Ch 1-45] | Urban Fantasy LitRPG Audiobook Marathon",
    "tags": [
        "LitRPG Audiobook", "SSS Awakening", "I Can Devour Gods to Evolve My Goddesses", "Su Chen",
        "Urban Fantasy", "Progression Fantasy", "Goddess Evolution", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "In a modern world where cataclysmic dimensional rifts open and ancient gods descend as existential calamities, "
        "humanity relies on the Awakening Ceremony to survive.\n\n"
        "Ridiculed for contracting a seemingly dormant, sealed spirit, Su Chen triggers an unprecedented SSS-tier miracle: "
        "the God Devourer Talent! By slaying calamity deities and consuming divine sparks, he can break primordial seals and evolve "
        "his contracted companions into supreme, unyielding Goddesses of absolute authority!\n\n"
        "Starting with the awakening of his first fallen Ice Valkyrie and advancing into high-tier catastrophe zones, "
        "watch Su Chen dismantle arrogant scions, devour divine remnants, and forge an immortal pantheon of evolved goddesses!\n\n"
        "Welcome to Chapters 1 to 45 of 'SSS Awakening: I Can Devour Gods to Evolve My Goddesses' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 01: The Grand Awakening Ceremony & Unlocking the SSS God Devourer Talent\n"
        "• Ch 05: Binding the Sealed Ice Valkyrie & First Divine Resonance\n"
        "• Ch 10: Slumbering God Remains Unearthed & Consuming the First Divine Spark\n"
        "• Ch 15: Ice Goddess Evolution: Absolute Frost Realm Manifestation\n"
        "• Ch 20: Crushing Arrogant Elite Scions in the Academy Trial Exam\n"
        "• Ch 26: Wilderness Calamity Zone Incursion & Slaying Corrupted God Remnants\n"
        "• Ch 32: Contracting the Second Goddess: Awakening the Blazing War Valkyrie\n"
        "• Ch 38: Dual Goddess Domain Synergy & Annihilating Catastrophe Behemoths\n"
        "• Ch 45: Sovereign of the Evolved Pantheon & The Path to God-Slaying Supremacy\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#SSSAwakening #GodDevourer #SuChen #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (1, 4),
            "title": ["AWAKENING CEREMONY", "SSS GOD DEVOURER"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of young prodigy Su Chen during his awakening, sharp refined jawline, short neat dark hair, "
                "eyes glowing with intense dual-ringed gold-and-amethyst energy, wearing modern tactical student uniform with silver trim. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set atop the high marble dais of a high-tech awakening auditorium, "
                "revealing massive holographic appraisal pillars displaying shimmering gold 'SSS' glyphs while stunned crowds watch in the distance. "
                "Illumination from radiant golden divine runes swirling around his palms and cool blue arena spotlights, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (5, 9),
            "title": ["SEALED VALKYRIE", "FIRST COVENANT"],
            "fallback_color": (20, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of Su Chen extending his hand in contractual covenant, calm steady gaze, dark windswept hair, "
                "wearing reinforced carbon-fiber combat jacket. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside an ancient crystalline sanctuary, revealing a stunning silver-haired fallen Ice Valkyrie "
                "in translucent frost armor opening her glowing sapphire eyes as her heavy ethereal chains shatter into shards in the distance. "
                "Illumination from blinding azure frost motes and pale white divine aura flares, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (10, 14),
            "title": ["DIVINE SPARK DEVOUR", "SHADOW MONOLITH"],
            "fallback_color": (30, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of Su Chen executing God Devourer authority, fierce commanding expression, dark amethyst pupils, "
                "a swirling black-and-gold void vortex manifesting within his outstretched hand. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set before a shattered subterranean altar of a fallen catastrophe deity, revealing a pulsing golden divine spark "
                "being drawn and absorbed into Su Chen's palm in the distance. "
                "Illumination from radiant celestial gold sparks clashing against dark purple absorption vortices, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (15, 18),
            "title": ["ICE GODDESS BLOOM", "ABSOLUTE ZERO"],
            "fallback_color": (15, 35, 45),
            "prompt": (
                "Cinematic 3D portrait of Su Chen directing divine battlefield magic, composed aristocratic poise, razor-sharp jawline, "
                "frost condensation mist swirling around his fingers. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set across an expansive frozen lake battlefield, revealing his fully evolved Ice Goddess floating gracefully "
                "with magnificent crystalline wings, freezing an entire horde of calamity monsters into solid blue ice statues in the distance. "
                "Illumination from sparkling diamond dust reflections and glowing neon-cyan glacial leylines, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (19, 23),
            "title": ["ACADEMY TRIALS", "ARROGANT SCION CRUSHED"],
            "fallback_color": (25, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of Su Chen in an urban combat arena, confident mocking smirk, calm calculating golden eyes, "
                "wearing tailored dark combat garments with rolled cuffs. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a grand high-tech circular academy arena packed with thousands of spectators, "
                "revealing an elite rival student's rare-grade armored beast pinned helplessly to the cratered floor by invisible divine pressure in the distance. "
                "Illumination from blinding stadium floodlights and crackling gold energy ripples, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (24, 28),
            "title": ["WILDERNESS INCURSION", "CALAMITY BEHEMOTH SLAY"],
            "fallback_color": (35, 20, 25),
            "prompt": (
                "Cinematic 3D portrait of a battle-hardened Su Chen, blood-splattered tactical vest, dark hair whipped by combat wind, "
                "intense predatory focus in his glowing dual-colored pupils. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set within a desolate monster-infested rift zone under a dark crimson storm sky, revealing an apocalyptic "
                "mountain-sized corrupted behemoth dissolving into glowing soul essence under his goddess's strike in the distance. "
                "Illumination from burning battlefield fires and shimmering silver-gold divine energy currents, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (29, 32),
            "title": ["SECOND GODDESS", "FLAME WAR VALKYRIE"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of Su Chen awakening his second divine companion, regal composed demeanor, warm amber eyes, "
                "holding a blazing crimson covenant crest between his palms. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set atop an ancient volcanic altar, revealing a magnificent crimson-haired War Goddess in ornate scarlet-and-gold plate "
                "spreading blazing fire wings and raising an enchanted spear in absolute loyalty in the distance. "
                "Illumination from roaring molten lava trenches and blinding golden-crimson solar flames, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (33, 37),
            "title": ["DUAL REALM HARMONY", "ICE & FLAME SYNTHESIS"],
            "fallback_color": (30, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of Su Chen commanding dual elemental divinity, hands raised in absolute authority, "
                "left hand swirling with glacial cyan frost while his right hand radiates roaring crimson solar fire. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set in orbital airspace above a ruined city rift, "
                "revealing his Ice Goddess and Flame Goddess flying in synchronized formation, creating a colossal yin-yang elemental storm barrier in the distance. "
                "Illumination from brilliant contrasting cyan and scarlet auroras with golden spark showers, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (38, 41),
            "title": ["DEITY REMNANT PURGE", "GOD DEVOURER ASCENT"],
            "fallback_color": (35, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of Su Chen executing supreme deity consumption, dark hair floating in zero gravity, "
                "intense luminous violet-and-gold irises, wearing an imperial midnight-black longcoat lined with celestial silk. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a sunken primordial pantheon temple, "
                "revealing a colossal ancient god statue shattering into radiant divine sparks that funnel into Su Chen's chest in the distance. "
                "Illumination from blinding white-gold cosmic beams and swirling violet dimensional energy mist, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (42, 45),
            "title": ["PANTHEON SOVEREIGN", "UNRIVALED DOMAIN"],
            "fallback_color": (25, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Sovereign Su Chen at the apex of urban ascension, dignified commanding presence, sun-gold pupils, "
                "wearing high-tier dark-silver commander armor beneath a billowing imperial cape. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on the highest observation balcony of an imperial skyline spire looking over modern fortress cities, "
                "revealing his evolved Ice and Flame Goddesses standing proudly beside him under a breathtaking starlight sky. "
                "Illumination from brilliant auroras of sunrise gold, radiant cyan frost flares, and deep-crimson divine flames, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
