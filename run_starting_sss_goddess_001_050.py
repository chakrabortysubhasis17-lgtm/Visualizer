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
    "novel_slug": "starting-with-an-sss-rank-goddess-summon",
    "start_url": "https://freewebnovel.com/novel/starting-with-an-sss-rank-goddess-summon/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "SSS Goddess Summon",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_starting_sss_goddess_001_050",
    "final_audio": "output_starting_sss_goddess_001_050.mp3",
    "final_video": "final_starting_sss_goddess_001_050.mp4",
    "cover_image": "cover_starting_sss_goddess_001_050.jpg",
    "timestamps_file": "youtube_timestamps_starting_sss_goddess_001_050.txt",
    "subtitles_file": "subtitles_starting_sss_goddess_001_050.srt",
    "payload_file": "youtube_upload_payload_starting_sss_goddess_001_050.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "AWAKENING THE SSS-RANK GODDESS! APEX SUMMONER TRANSCENDS ACADEMY RANKS [Ch 1-50] | LitRPG Progression Audiobook Marathon",
    "tags": [
        "Starting with an SSS-rank Goddess Summon", "SSS Rank Goddess", "Summoner LitRPG",
        "Progression Fantasy Audiobook", "Overpowered MC", "Goddess Summoning", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "In a modern world besieged by dimensional abyssal rifts where a person's awakening ceremony determines their entire future, "
        "our protagonist defies all mortal common sense by summoning the supreme, mythical SSS-Rank Goddess!\n\n"
        "While elite classmates and arrogant legacy scions celebrate summoning ordinary combat beasts, armored wolves, or low-tier elemental spirits, "
        "his summoning altar detonates with blinding golden celestial pillars as a peerless divine entity descends to swear eternal loyalty. "
        "With a shared telepathic soul matrix, absolute combat amplification, and god-tier domain skills, every monster horde and dungeon boss "
        "they encounter is systematically obliterated.\n\n"
        "Watch him shatter academy assessment records, humiliate condescending guild masters, and carve an unstoppable path toward global supremacy!\n\n"
        "Welcome to Chapters 1 to 50 of 'Starting with an SSS-rank Goddess Summon' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 01: The Academy Awakening Ceremony & Summoning the Mythical SSS-Rank Goddess\n"
        "• Ch 07: First Dueling Ring Exhibition: Humiliating Arrogant Aristocratic Prodigies\n"
        "• Ch 14: Maiden Dungeon Expedition: Annihilating Abyssal Beast Swarms with Divine Light\n"
        "• Ch 21: Stat Synchronization Feedback: Overnight Leveling and Telepathic Mastery\n"
        "• Ch 28: Clearing the S-Rank Calamity Boss: The Goddess Unleashes Celestial Judgment\n"
        "• Ch 35: Hunter Guild Inquest: Cold Indifference Before Corrupt Guild Officials\n"
        "• Ch 42: Subterranean Ruin Trial: Extracting Ancient Primordial Core Relics\n"
        "• Ch 50: Grand Inter-Academy Tournament: Crowned the Undisputed Sovereign Summoner\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#StartingWithAnSSSRankGoddessSummon #SSSRankGoddess #SummonerLitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Streamlined for Zero Generation Failures)
    "blocks": [
        {
            "index": 1, "range": (1, 5),
            "title": ["AWAKENING CEREMONY", "SSS-RANK GODDESS SUMMON"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of a young male summoner standing beside a glowing ritual circle, calm confident smile, "
                "amber-gold eyes reflecting golden divine runes, wearing tailored academy uniform with silver trim. "
                "Set in a grand marble awakening hall, revealing the radiant golden silhouette of a descending winged goddess in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (6, 10),
            "title": ["DUELING RING", "HUMILIATING ACADEMY RIVALS"],
            "fallback_color": (30, 20, 25),
            "prompt": (
                "Cinematic 3D portrait of the summoner standing with effortless nonchalance, hands in uniform pockets, cool amused smirk. "
                "Set in the center of an outdoor combat colosseum, revealing defeated rival summoners and their knocked-out beasts across the arena tiles in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (11, 15),
            "title": ["MAIDEN DUNGEON", "SWARM OBLITERATION"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of the summoner in tactical combat stance, sharp focused gaze, holding a glowing crystal catalyst. "
                "Set inside a jagged underground dungeon cavern, revealing swarms of abyssal monster beasts disintegrating into golden dust under divine light in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (16, 20),
            "title": ["STAT SYNCHRONIZATION", "RAPID REFINEMENT"],
            "fallback_color": (25, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of the summoner in deep meditation, serene divine aura, golden stat matrices floating before his face. "
                "Set inside a modern training chamber, revealing glowing concentric energy rings expanding through the polished floor in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (21, 25),
            "title": ["CALAMITY BOSS", "CELESTIAL JUDGMENT"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of the summoner raising an outstretched hand, resolute fierce expression, surrounded by blinding golden energy arcs. "
                "Set across shattered volcanic rocks, revealing a colossal horned dungeon boss pinned under a towering golden celestial blade in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (26, 30),
            "title": ["GUILD INQUEST", "COLD DEFIANCE"],
            "fallback_color": (25, 25, 35),
            "prompt": (
                "Cinematic 3D portrait of the summoner standing in calm defiance, sharp commanding jawline, arms folded across his dark tactical jacket. "
                "Set inside a high-tech guild council chamber, revealing seated guild officials staring down with visible nervousness in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (31, 35),
            "title": ["SACRED DOMAIN", "AEGIS SHIELD AWAKENING"],
            "fallback_color": (20, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of the summoner pointing two fingers forward, proud dignified posture, eyes flashing with brilliant azure-gold power. "
                "Set at the gates of an outpost under monster siege, revealing an impenetrable translucent golden dome repelling dark magic attacks in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (36, 40),
            "title": ["SUBTERRANEAN RUIN", "PRIMORDIAL CORE HARVEST"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of the summoner examining a glowing crystal relic, watchful calculating eyes, neat dark hair framing his forehead. "
                "Set inside an ancient stone grotto overgrown with glowing bioluminescent vines, revealing slumbering ancient stone statues in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (41, 45),
            "title": ["TOURNAMENT CLASH", "TOTAL DOMINATION"],
            "fallback_color": (35, 20, 25),
            "prompt": (
                "Cinematic 3D portrait of the summoner stepping forward with calm authority, handsome chiseled features, subtle confident smirk. "
                "Set in a massive modern tournament stadium with roaring crowds, revealing elite academy champions kneeling in defeat in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (46, 50),
            "title": ["SOVEREIGN SUMMONER", "CONTINENTAL APEX"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of the Sovereign Summoner seated upon a modern crystal throne, serene invincible aura, "
                "eyes glowing with radiant golden starlight, wearing high-rank commander armor. Set atop an observation tower overlooking a secured futuristic metropolis under an aurora sky in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
