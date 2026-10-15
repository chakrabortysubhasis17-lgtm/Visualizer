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
    # Note: If mtl-novel requires the full chapter slug, use the exact URL from Chapter 101.
    "novel_slug": "entry-cultivation-i-can-copy-entries",
    "start_url": "https://mtl-novel.com/novel/entry-cultivation-i-can-copy-entries/chapter-100-sword-venerable-possession-a-banished-immortal-suppresses-the-flood-dragon/",
    "start_chapter": 101,
    "end_chapter": 150,
    "default_topic": "Entry Cultivation",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_entry_cultivation_101_150",
    "final_audio": "output_entry_cultivation_101_150.mp3",
    "final_video": "final_entry_cultivation_101_150.mp4",
    "cover_image": "cover_entry_cultivation_101_150.jpg",
    "timestamps_file": "youtube_timestamps_entry_cultivation_101_150.txt",
    "subtitles_file": "subtitles_entry_cultivation_101_150.srt",
    "payload_file": "youtube_upload_payload_entry_cultivation_101_150.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "TRANSCENDING TO GOLDEN CORE! COPYING HEAVENLY SWORD VENERABLE ENTRIES [Ch 101-150] | Xianxia Progression Audiobook Marathon",
    "tags": [
        "Entry Cultivation", "I Can Copy Entries", "Lu Yuan", "Sword Venerable",
        "Xianxia Audiobook", "Progression Fantasy", "Golden Core Breakthrough", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Following the legendary suppression of the Ancient Flood Dragon and inheriting residual Sword Venerable imprints, "
        "Lu Yuan pushes beyond the Foundation Establishment realm into the revered Golden Core stage!\n\n"
        "While rival sect elders and legacy heirs wage bloody wars over rare spiritual veins, Lu Yuan quietly observes from "
        "the sidelines—copying supreme golden and purple entries including [Banished Immortal Sword Intent], [Nine-Revolutions Core Harmony], "
        "and [Innate Dao Comprehension]. Every copied entry weaves seamlessly into his dantian, forging an unshakeable foundation "
        "without drawing karmic retribution or the jealousy of ancient monsters.\n\n"
        "From unraveling esoteric sword tombs and navigating perilous pill auctions to annihilating blood fiend sects with flawless "
        "stealth execution, watch Lu Yuan redefine low-key immortal cultivation!\n\n"
        "Welcome to Chapters 101 to 150 of 'Entry Cultivation: I Can Copy Entries' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 101: Flood Dragon Aftermath: Absorbing the Banished Immortal Sword Intent Entry\n"
        "• Ch 107: Golden Core Tribulation Preparation: Gathering Ancient Qi-Condensation Dew\n"
        "• Ch 114: Exploring the Forgotten Sword Tomb & Replicating Ancient Weapon Soul Entries\n"
        "• Ch 121: Decimating Blood-Corpse Cult Ambushers with Silent Spatial Sword Qi\n"
        "• Ch 128: Grand Auction Intrigue: Copying the [Heavenly Eye of Treasure Appraisal]\n"
        "• Ch 135: Refining the Nine-Revolutions Golden Core: Hundredfold Dan Energy Breakthrough\n"
        "• Ch 142: Core Elder Assembly: Concealing True Cultivation Beneath Mundane Aura Seals\n"
        "• Ch 150: Peak Golden Core Hegemony: The Sovereign Master of Heavenly Entries\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#EntryCultivation #ICanCopyEntries #XianxiaAudiobook #ProgressionFantasy #CultivationAudiobook #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (101, 105),
            "title": ["SWORD INTENT INHERITANCE", "FLOOD DRAGON AFTERMATH"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of young cultivator Lu Yuan standing calmly beside a mist-shrouded riverbank, neat black hair tied with a dark wood pin, "
                "observant dark eyes reflecting golden runic entries, wearing charcoal-grey inner sect scholar robes. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set along a stormy river gorge, revealing the dissipating silhouette of a colossal defeated flood dragon under parting storm clouds in the distance. "
                "Illumination from pale silver lightning glints, golden floating entry script, and cool river mist, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (106, 110),
            "title": ["GOLDEN CORE PREPARATION", "QI-CONDENSATION EXPEDITION"],
            "fallback_color": (25, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan inspecting a glowing jade vial of celestial dew, serene calculating expression, holding a delicate crystal pipette. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a secluded mountain cavern overgrown with spirit herbs, "
                "revealing an ancient limestone stalactite dripping glowing azure essence into a carved jade basin in the distance. "
                "Illumination from bioluminescent cyan droplets and soft golden aura reflections, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (111, 115),
            "title": ["FORGOTTEN SWORD TOMB", "EXTRACTING WEAPON ENTRIES"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan resting his fingers on the hilt of an ancient rusted broadsword embedded in solid granite, sharp focused gaze. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set across a desolate battlefield littered with thousands of dormant swords stuck into rocky ground, "
                "revealing translucent golden sword-intent entries floating into his palms in the distance. "
                "Illumination from ethereal silver blade glints and twilight purple sky gradients, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (116, 120),
            "title": ["SPATIAL PURGE", "SEVERING KARMIC TRAILS"],
            "fallback_color": (25, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan executing a silent sword strike, resolute cold expression, sleeves fluttering under kinetic wind pressure. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set along a foggy mountain pass under heavy rain, "
                "revealing blood-sect ambushers disintegrating into harmless spiritual ashes without leaving a trace of blood or karma in the distance. "
                "Illumination from pale silver rain streaks and sharp razor-thin blade flashes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (121, 125),
            "title": ["TREASURE APPRAISAL", "AUCTION PAVILION INTRIGUE"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan seated in an ornate private booth, calm aristocratic composure, examining an ancient sealed bronze box with glowing golden pupils. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a multi-tiered immortal auction hall, "
                "revealing wealthy sect patriarchs bidding on stage while translucent item entries reveal hidden flaws and treasures in the distance. "
                "Illumination from warm red silk lanterns and shimmering golden appraisal runes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (126, 130),
            "title": ["ALCHEMICAL TRANSCENDENCE", "NINE-SUN CORE REFINEMENT"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan coordinating multi-flame pill refinement, artistic concentration, hands deftly guiding swirling vermilion and purple spiritual fires. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a sealed subterranean alchemical grotto, "
                "revealing a heavy carved bronze cauldron hovering mid-air emitting cloud-shaped golden pill mist in the distance. "
                "Illumination from roaring red furnace fires and radiant golden pill halos, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (131, 135),
            "title": ["GOLDEN CORE BREAKTHROUGH", "PURPLE QI SURGE"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan in deep cross-legged meditation, serene divine aura, pulsing purple and golden core runes revolving across his chest and brow. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside an underground spirit array sanctum, "
                "revealing concentric shockwaves of golden core energy rippling across solid stone walls in the distance. "
                "Illumination from brilliant violet core energy and luminous golden entry glyphs, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (136, 140),
            "title": ["CORE ELDER PROMOTION", "LOW-KEY CONCEALMENT"],
            "fallback_color": (20, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan bowing slightly with polite humility, calm understated smile, wearing refined deep-blue inner elder robes trimmed with silver cloud embroidery. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside the grand hall of the mountain sect, "
                "revealing powerful grand elders nodding approvingly while completely unaware of his true transcendent cultivation level in the distance. "
                "Illumination from warm morning sunbeams pouring through high timber windows and incense smoke motes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (141, 145),
            "title": ["ANCIENT FIEND INVASION", "CONCEALED SWORD FORMATION"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan commanding a hidden defensive sword matrix, watchful razor-sharp gaze, fingers extended with silent authority. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set at the border of the mountain sect under midnight skies, "
                "revealing encroaching abyssal fiends silently shredded by an invisible web of golden sword qi in the distance. "
                "Illumination from electric-blue barrier ripples and radiant golden blade sparks, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (146, 150),
            "title": ["PEAK GOLDEN CORE", "SOVEREIGN ENTRY OVERLORD"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Sovereign Entry Master Lu Yuan standing atop a soaring immortal peak at sunset, serene invincible posture, "
                "radiant golden-and-purple pupils reflecting countless cosmic entry matrices, wearing midnight-blue elder robes billowing in the mountain wind. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set overlooking an endless sea of clouds dotted with floating jade sect islands and soaring cranes in the distance. "
                "Illumination from rich golden sunset rays, soft twilight clouds, and countless glowing golden status matrices, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
