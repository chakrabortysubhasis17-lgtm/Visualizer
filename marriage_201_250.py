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
    "novel_slug": "national-fate-marriage-the-elf-queen-is-pregnant-at-the-start",
    "start_url": "https://mtl-novel.com/novel/national-fate-marriage-the-elf-queen-is-pregnant-at-the-start/chapter-201/",
    "start_chapter": 201,
    "end_chapter": 250,
    "default_topic": "National Fate Marriage",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_national_fate_marriage_201_250",
    "final_audio": "output_national_fate_marriage_201_250.mp3",
    "final_video": "final_national_fate_marriage_201_250.mp4",
    "cover_image": "cover_national_fate_marriage_201_250.jpg",
    "timestamps_file": "youtube_timestamps_national_fate_marriage_201_250.txt",
    "subtitles_file": "subtitles_national_fate_marriage_201_250.srt",
    "payload_file": "youtube_upload_payload_national_fate_marriage_201_250.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "PREGNANT ELF QUEEN DIVINE BLESSINGS! SSS-RANK NATIONAL FATE DOMINATION [Ch 201-250] | Webnovel Audiobook Marathon",
    "tags": [
        "National Fate Marriage", "Elf Queen Is Pregnant", "National Fate Game", "Webnovel Audiobook",
        "Progression Fantasy", "Harem System", "Overpowered MC", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Entering the high-tier dimensional sectors of the National Fate Marriage Game, our chosen representative continues "
        "his absolute hegemony across the multiverse!\n\n"
        "With the Elf Queen carrying divine royal heirs and subsequent mythical marriages continuously multiplying his bloodline perks, "
        "every door chosen yields astronomical returns for the homeland. While rival foreign competitors fall prey to lethal trap rooms, "
        "abyssal beast ambushes, and disastrous debuffs, our protagonist unlocks god-tier resource caches, ancient longevity springs, "
        "and cosmic territory shields for his nation.\n\n"
        "From welcoming celestial angel princesses into his expanding family sanctuary to crushing abyssal invasion hordes with SSS-rank "
        "defensive arrays, watch him solidify his status as the undisputed sovereign of the National Fate Game!\n\n"
        "Welcome to Chapters 201 to 250 of 'National Fate Marriage: The Elf Queen is Pregnant at the Start' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 201: Unlocking the High-Tier Divine Marriage Door & The Goddess Covenant\n"
        "• Ch 207: Astronomical National Fate Feedback: Lifespan and Resource Surges for the Nation\n"
        "• Ch 214: Entering the Celestial Cloud Realm: Meeting the Angel Princess\n"
        "• Ch 220: Foreign Competitors Suffer Calamity: Laughing at Rival Alliance Failures\n"
        "• Ch 226: Abyssal Incursion Defeated: Activating the World Tree SSS-Rank Defense Matrix\n"
        "• Ch 233: Divine Offspring Awakening: Primordial Bloodline Resonance Across Realms\n"
        "• Ch 240: Harvesting the Golden Longevity Fruit in the Primal Sanctuary Garden\n"
        "• Ch 250: Supreme National Fate Sovereign: Dominating the Multiverse Leaderboards\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#NationalFateMarriage #ElfQueenIsPregnant #NationalFateGame #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Streamlined for Zero Generation Failures)
    "blocks": [
        {
            "index": 1, "range": (201, 205),
            "title": ["DIVINE MARRIAGE DOOR", "GODDESS COVENANT"],
            "fallback_color": (25, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of the national fate chosen player standing before a glowing pink-and-gold dimensional door, calm confident smile, "
                "handsome features, wearing sleek black commander robes trimmed with silver dragon embroidery. "
                "Set on an ancient marble portal platform, revealing the radiant glowing silhouette of the pregnant Elf Queen in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (206, 210),
            "title": ["NATIONAL REWARD SURGE", "TERRITORIAL ASCENSION"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of the protagonist reviewing floating golden system status screens, calm aristocratic poise, "
                "amber-gold eyes glowing with divine blessings. Set inside a floating jade palace chamber, revealing pillars of golden national fate light showering down across modern city skyscrapers in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (211, 215),
            "title": ["CELESTIAL REALM", "ANGEL PRINCESS ACCORD"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the protagonist greeting a celestial winged maiden, composed gentle expression, "
                "dark hair tied neatly behind his shoulders. Set atop a soaring crystal cloud terrace, revealing floating golden sanctuaries and soaring white pegasi in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (216, 220),
            "title": ["FOREIGN RIVAL COLLAPSE", "RUTHLESS PRAGMATISM"],
            "fallback_color": (20, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of the protagonist standing with arms crossed, sharp mocking smirk, "
                "observing broadcast screens with cold indifference. Set on an ancient stone balcony overlooking the trial arena, revealing panicked foreign players retreating from vicious trap-door monsters in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (221, 225),
            "title": ["ABYSSAL INCURSION", "SSS-TIER DEFENSE ARRAY"],
            "fallback_color": (30, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of the protagonist raising an open palm surrounded by electric-blue ward barriers, resolute fierce gaze, "
                "wind whipping his dark cloak. Set at the fortified gates of his dimensional sanctuary, revealing invading abyssal shadow beasts disintegrating against shimmering forcefields in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (226, 230),
            "title": ["MYTHIC OFFSPRING", "DIVINE BLOODLINE AWAKENING"],
            "fallback_color": (25, 30, 40),
            "prompt": (
                "Cinematic 3D portrait of the protagonist cradling a glowing celestial infant with tiny silver wings, warm paternal smile, "
                "surrounded by soft emerald spiritual light. Set inside an opulent royal nursery pavilion, revealing lush glowing World Tree vines climbing carved wooden walls in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (231, 235),
            "title": ["WORLD TREE GARDEN", "SPIRITUAL HARVEST"],
            "fallback_color": (15, 35, 25),
            "prompt": (
                "Cinematic 3D portrait of the protagonist plucking a glowing golden longevity fruit, relaxed satisfied expression, "
                "wearing embroidered scholar robes. Set within an expansive botanical garden beneath the colossal World Tree canopy, revealing sparkling jade fountains and floating light spirits in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (236, 240),
            "title": ["COSMIC ARENA", "CRUSHING ALIEN CHAMPIONS"],
            "fallback_color": (35, 20, 20),
            "prompt": (
                "Cinematic 3D portrait of the protagonist pointing a slender runic sword forward, commanding authoritative aura, "
                "dual-toned irises flashing with absolute dominance. Set inside a colossal interstellar fighting arena, revealing defeated alien titans collapsing onto shattered stone tiles in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (241, 245),
            "title": ["FAMILY SANCTUARY", "ROYAL HARMONY"],
            "fallback_color": (30, 25, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist pouring spiritual tea from a celadon pot, handsome refined face, "
                "subtle affectionate smile. Set inside an open-air pavilion overlooking tranquil misty mountain lakes, revealing the Elf Queen and consort maidens laughing together in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (246, 250),
            "title": ["NATIONAL FATE MONARCH", "SUPREME MULTIVERSE RULER"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of the Supreme National Fate Sovereign seated upon a magnificent dragon-carved jade throne, serene invincible posture, "
                "eyes glowing with radiant golden starlight. Set inside the Grand Multiverse Spire overlooking united dimensional realms, revealing glorious auroras lighting the skies in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
