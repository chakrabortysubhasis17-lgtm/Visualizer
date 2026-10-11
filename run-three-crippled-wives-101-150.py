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
    "novel_slug": "investing-in-my-three-crippled-wives-get-10000x-times-return",
    "start_url": "https://freewebnovel.com/novel/investing-in-my-three-crippled-wives-get-10000x-times-return/chapter-101",
    "start_chapter": 101,
    "end_chapter": 150,
    "default_topic": "Cultivation",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 1,  # Sequential processing to respect 15 RPM limits cleanly
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_investing_three_wives_101_150",
    "final_audio": "output_investing_three_wives_101_150.mp3",
    "final_video": "final_investing_three_wives_101_150.mp4",
    "cover_image": "cover_investing_three_wives_101_150.jpg",
    "timestamps_file": "youtube_timestamps_investing_three_wives_101_150.txt",
    "subtitles_file": "subtitles_investing_three_wives_101_150.srt",
    "payload_file": "youtube_upload_payload_investing_three_wives_101_150.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "SUPREME IMMORTAL REALM TRANSCENDENCE! 10,000X RETURN EMPEROR [Ch 101-150] | Cultivation LitRPG Marathon",
    "tags": [
        "LitRPG Audiobook", "Investing In My Three Crippled Wives", "10000x Return System", "Gu Chen",
        "Cultivation Audiobook", "Xianxia", "Harem Cultivation", "Progression Fantasy", "Being A Bong"
    ],
    "desc_header": (
        "Breaking past continental boundaries, Patriarch Gu Chen enters the supreme Central Holy Domains!\n\n"
        "With the unstoppable momentum of the 10,000x Investment Return System, Gu Chen bestows quasi-immortal scriptures, "
        "primordial chaos pills, and ancestral sovereign artifacts upon his three peerless empress wives. In return, the critical "
        "multipliers trigger god-tier returns directly into his soul foundation—unlocking the Nine Heavens Chaos Dantian, "
        "True Dragon Bone physique, and absolute domain supremacy!\n\n"
        "When ancient immortal dynasties, sacred land grand elders, and primordial beast warlords assemble to suppress his family, "
        "Gu Chen and his three fully awakened empresses stand side-by-side to shatter the heavens and rewrite the laws of the realm!\n\n"
        "Welcome to Chapters 101 to 150 of 'Investing In My Three Crippled Wives Get 10,000x Times Return' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 101: Crossing into the Central Holy Domain & Gifting Immortal Jade Elixirs\n"
        "• Ch 110: Ye Qingxue's Supreme Chaos Sword Domain vs Sacred Land Elders\n"
        "• Ch 118: Ancient Immortal Beast Graveyard & Bai Ling's Heavenly Qilin Metamorphosis\n"
        "• Ch 125: Jiang Luoli's Imperial Frost Throne & Absolute Zero Realm Freeze\n"
        "• Ch 132: Gifting Chaos Primordial Lotus & Gu Chen's 10,000x Chaos Emperor Body\n"
        "• Ch 140: The Grand Holy Land Alliance Siege & Cold-Blooded Sovereign Annihilation\n"
        "• Ch 145: Ancient Heavenly Dao Auction & Bidding for the Immortal Bone of Reincarnation\n"
        "• Ch 150: Supreme Sovereign Domain Ascendance & Multi-Empress Divine Rule\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#InvestingInMyThreeCrippledWives #10000xReturn #GuChen #CultivationAudiobook #Xianxia #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (101, 105),
            "title": ["CENTRAL HOLY DOMAIN", "IMMORTAL JADE ELIXIR"],
            "fallback_color": (25, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of Patriarch Gu Chen as an ascending sovereign cultivator, commanding sharp jawline, "
                "calm glowing sun-gold eyes, wearing imperial midnight-azure silk robes with silver crane embroidery. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set upon an overlooking floating cloud terrace "
                "of the Central Holy Domain, revealing an ancient jade medicine chest radiating emerald and golden return matrices in the distance. "
                "Illumination from warm sunrise light and floating translucent 10,000x multiplier system runes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (106, 110),
            "title": ["CHAOS SWORD DOMAIN", "YE QINGXUE'S WRATH"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of Gu Chen fighting alongside his First Wife, razor-sharp jawline, cold calculating golden eyes, "
                "wearing blackened dragon-scaled vambraces over dark robes. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set high above a jagged floating mountain pass, revealing Sword Empress Ye Qingxue brandishing an ancient "
                "black-and-silver chaos longsword that splits massive incoming heavenly lightning bolts in the distance. "
                "Illumination from blinding silver blade light and amethyst storm flashes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (111, 115),
            "title": ["BEAST GRAVEYARD", "BAI LING'S METAMORPHOSIS"],
            "fallback_color": (35, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of a protective young master cultivator, gentle confident gaze, radiant amber pupils, "
                "holding an ancient glowing beast talisman, wearing reinforced charcoal-silk traveler robes. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in a primordial petrified forest cemetery of mythical beasts, revealing innocent Third Wife Bai Ling "
                "surrounded by ethereal celestial amethyst fox fire and roaring ancestral beast phantoms in the distance. "
                "Illumination from soft magenta divine mist and floating golden beast runes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (116, 120),
            "title": ["IMMORTAL QILIN CORE", "CRITICAL 10,000X RETURN"],
            "fallback_color": (40, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of Gu Chen absorbing primordial feedback, dark windswept hair, brilliant dual-colored crimson-and-gold pupils, "
                "radiating an ancient draconic bone aura along his shoulders. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a hollow volcanic spirit grotto, revealing dense rings of primordial beast vitality swirling into his dantian "
                "and cracking the surrounding magma stone floor. Illumination from blinding golden-amber vitality shockwaves and crimson lava glow, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (121, 125),
            "title": ["FROST EMPRESS THRONE", "JIANG LUOLI'S POWER"],
            "fallback_color": (15, 30, 50),
            "prompt": (
                "Cinematic 3D portrait of a dignified clan ruler, refined features, warm amber eyes, "
                "channeling an unyielding solar barrier with an outstretched palm. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in an opulent frozen celestial throne room, revealing regal Second Wife Jiang Luoli with long silver-white hair "
                "commanding an immense crystalline absolute-zero blizzard that freezes invading enemy elders into solid ice in the distance. "
                "Illumination from blinding sapphire ice crystals and warm golden solar embers, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (126, 130),
            "title": ["CHAOS EMPEROR BODY", "NINE HEAVENS DANTIAN"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of Gu Chen undergoing transcendent realm ascension, serene majestic expression, glowing white-gold pupils, "
                "wearing flowing celestial daoist robes covered in constellation emblems. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set atop a soaring mountain peak touching the stars, revealing nine concentric golden solar rings revolving "
                "around his spiritual core in the distance. Illumination from radiant nebula clouds, blinding starlight arcs, and deep purple soul fire, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (131, 135),
            "title": ["SACRED LAND ALLIANCE", "TERRITORY SIEGE PURGE"],
            "fallback_color": (35, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of an unyielding warrior patriarch, cold ruthless golden eyes, sharp jawline, "
                "wielding an invisible wave of overwhelming emperor-grade spiritual pressure. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set along the high marble ramparts of the Gu Clan imperial city, revealing thousands of enemy holy land warships "
                "shattering and burning under an immense golden domain field in the distance. Illumination from exploding warship debris and sharp silver sword flashes, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (136, 140),
            "title": ["CELESTIAL DAO AUCTION", "REINCARNATION BONE"],
            "fallback_color": (25, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of a wealthy master sovereign, elegant handsome features, calculating golden eyes, "
                "wearing an imperial midnight-blue trench coat with gold dragon filigree embroidery. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a grand multi-tiered heavenly auction palace, revealing broker elders unveiling a floating translucent "
                "reincarnation bone radiating iridescent yin-yang energy on a floating jade pillar in the distance. "
                "Illumination from warm brass chandeliers and shimmering magenta spiritual mist, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (141, 145),
            "title": ["SUPREME SOUL SEVER", "COMBINED EMPRESS STRIKE"],
            "fallback_color": (20, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of Gu Chen coordinating a three-way supreme technique, commanding posture, radiant sun-gold irises, "
                "directing a multi-layered heavenly seal with two raised fingers. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set above the sea of clouds, revealing Ye Qingxue, Jiang Luoli, and Bai Ling executing a tri-elemental strike "
                "combining silver sword qi, absolute-zero frost, and celestial beast lightning against a dying ancient sect lord in the distance. "
                "Illumination from blinding silver, sapphire, and violet energy beams, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (146, 150),
            "title": ["SOVEREIGN CORONATION", "THE THREE EMPRESS DOMAIN"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Sovereign Emperor Gu Chen seated upon an imperial jade throne, regal dark hair, commanding sun-gold eyes, "
                "wearing supreme imperial black-and-gold sovereign robes woven from dragon silk. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set overlooking a sprawling immortal domain realm, revealing his three fully restored empress wives standing "
                "confidently beside him as countless sect elders and holy land leaders kneel in absolute deference under a radiant golden aurora sky. "
                "Illumination from brilliant auroras of sunrise gold, silver sword qi, and celestial violet starlight, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
