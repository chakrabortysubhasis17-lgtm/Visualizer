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
    "start_url": "https://freewebnovel.com/novel/investing-in-my-three-crippled-wives-get-10000x-times-return/chapter-151",
    "start_chapter": 151,
    "end_chapter": 200,
    "default_topic": "Investing in Three Wives",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_investing_three_wives_151_200",
    "final_audio": "output_investing_three_wives_151_200.mp3",
    "final_video": "final_investing_three_wives_151_200.mp4",
    "cover_image": "cover_investing_three_wives_151_200.jpg",
    "timestamps_file": "youtube_timestamps_investing_three_wives_151_200.txt",
    "subtitles_file": "subtitles_investing_three_wives_151_200.srt",
    "payload_file": "youtube_upload_payload_investing_three_wives_151_200.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "10,000X INVESTMENT RETURN SYSTEM! HEALING FORMER EMPRESS WIVES TO PEAK POWER [Ch 151-200] | Progression Fantasy Audiobook Marathon",
    "tags": [
        "Investing in My Three Crippled Wives", "10000x Return System", "Cultivation Audiobook",
        "Progression Fantasy", "Overpowered MC", "Harem Cultivation", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Armed with the game-breaking 10,000x Investment Return System, our protagonist continues transforming "
        "his three crippled wives—secretly disgraced former empresses, saintesses, and celestial sword prodigies—back into supreme rulers!\n\n"
        "Every divine elixir, celestial cultivation method, and mythic spirit herb he tenderly gifts to heal their severed meridians "
        "and crippled dantian foundations triggers astronomical system feedback. A single high-grade spirit pill invested returns "
        "god-tier immortal cores; an ancient broken blade given returns an omnipotent celestial sword array!\n\n"
        "As arrogant imperial clans, hostile merchant syndicates, and corrupt sect patriarchs attempt to seize his estate and "
        "humiliate his wives, our protagonist unleashes overwhelming returned cultivation bases and supreme heavenly artifacts to crush "
        "all opposition into dust!\n\n"
        "Welcome to Chapters 151 to 200 of 'Investing in My Three Crippled Wives, Get 10,000x Times Return' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 151: Gifting the Nine-Revolutions Meridian Pill: 10,000x Return of Primordial Chaos Core\n"
        "• Ch 156: Unlocking the Empress Wife's Slumbering Phoenix Bloodline & Healing Bone Severance\n"
        "• Ch 162: Continental Auction Infiltration: Out-Bidding Royal Scions with Infinite Wealth\n"
        "• Ch 168: Sword Saintess Breakthrough: Severing Ancient Poison Shackle Formations\n"
        "• Ch 174: Primordial Spirit Grotto Expedition: Plundering Ancient Dao Veins in Secret\n"
        "• Ch 180: Imperial Clan Enforcer Ambush: Obliterating Royal Masters with Effortless Domain Pressure\n"
        "• Ch 186: Gifting Saint-Tier Dao Robes: 10,000x Return of Indestructible Dragon-Scale Aegis\n"
        "• Ch 192: Private Mountain Estate Sanctuary: Cultivating Peaceful Days with Reclaimed Goddesses\n"
        "• Ch 197: Decimating the Corrupt Sect Coalition with Returned God-Grade Sword Arrays\n"
        "• Ch 200: Continental Investment Sovereign: Undisputed Patriarch of the Supreme Family\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#InvestingInMyThreeCrippledWives #10000xReturnSystem #CultivationAudiobook #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Streamlined for Zero Image Generation Failures)
    "blocks": [
        {
            "index": 1, "range": (151, 155),
            "title": ["DIVINE PILL INVESTMENT", "10,000X RETURN TRIGGER"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of a young master cultivator, gentle affectionate smile, warm amber-gold eyes, "
                "wearing elegant white-and-silver scholar robes trimmed with jade embroidery. "
                "Set inside an opulent private tea pavilion, revealing a glowing jade elixir box on a mahogany table and the silhouette of his recovering wife in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (156, 160),
            "title": ["PHOENIX BLOODLINE", "MERIDIAN RESTORATION"],
            "fallback_color": (35, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of the cultivator channeling gentle healing spiritual light, composed focused expression, "
                "holding a radiant crimson spirit lotus. Set within a tranquil courtyard beside flowering cherry trees, "
                "revealing a recovering empress wife surrounded by faint golden phoenix flames in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (161, 165),
            "title": ["CONTINENTAL AUCTION", "INFINITE WEALTH DISPLAY"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of the protagonist sitting in a private viewing booth, calm aristocratic smirk, "
                "holding a glowing imperial VIP jade token. Set inside a multi-tiered grand auction colosseum, "
                "revealing stunned royal scions staring up from the main arena floor in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (166, 170),
            "title": ["SWORD SAINTESS RECOVERY", "SHACKLE SEVERING"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of the protagonist presenting an unadorned ancient longsword, proud admiring gaze, "
                "wearing tailored dark-blue noble robes. Set on a stone cliff overlooking misty mountain peaks, "
                "revealing his sword-master wife cleaving through cursed iron chains with dazzling silver qi in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (171, 175),
            "title": ["SPIRIT GROTTO", "PLUNDERING PRIMORDIAL VEINS"],
            "fallback_color": (15, 30, 30),
            "prompt": (
                "Cinematic 3D portrait of the protagonist inspecting a glowing stalactite of liquid spirit jade, sharp calculating eyes, "
                "wearing a travel cloak with silver clasps. Set inside a bioluminescent cavern filled with crystalline flora, "
                "revealing an underground spirit lake glistening with emerald energy in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (176, 180),
            "title": ["ROYAL ENFORCER PURGE", "EFFORTLESS PRESSURE"],
            "fallback_color": (25, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of the protagonist standing with hands behind his back, cold dismissive glare, "
                "dark hair fluttering in kinetic shockwaves. Set at the outer gates of his mountain estate, "
                "revealing arrogant royal enforcers kneeling on fractured flagstones under an invisible gravitational domain in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (181, 185),
            "title": ["SAINT ROBE GIFT", "10,000X RETURN SHIELD"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the protagonist admiring a hovering dragon-scale armor vest, serene proud aura, "
                "fingers tracing translucent system return text panels. Set inside a quiet master chamber lit by warm lanterns, "
                "revealing intricately embroidered silk gowns folded neatly on carved tables in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (186, 190),
            "title": ["SANCTUARY HARMONY", "PEACEFUL MOUNTAIN RETREAT"],
            "fallback_color": (20, 30, 25),
            "prompt": (
                "Cinematic 3D portrait of the protagonist pouring tea from a celadon teapot, relaxed contented expression, "
                "handsome defined jawline. Set inside an open-air pavilion overlooking misty lotus ponds, "
                "revealing his healthy beautiful wives enjoying peaceful music together in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (191, 195),
            "title": ["SECT COALITION CRUSH", "GOD-GRADE SWORD ARRAY"],
            "fallback_color": (35, 20, 20),
            "prompt": (
                "Cinematic 3D portrait of the protagonist raising two fingers to command the sky, commanding authoritative posture, "
                "eyes blazing with golden returned cultivation power. Set against a stormy mountain horizon, "
                "revealing thousands of golden ethereal blades descending upon an invading sect army in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (196, 200),
            "title": ["INVESTMENT SOVEREIGN", "CONTINENTAL PATRIARCH"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of the Sovereign Family Patriarch seated upon a carved jade throne at sunset, serene invincible aura, "
                "wearing regal midnight-blue robes with golden cloud filigree. Set atop the highest terrace of his vast immortal palace, "
                "revealing his powerful wives and soaring cranes under an expansive golden sunset aurora in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
