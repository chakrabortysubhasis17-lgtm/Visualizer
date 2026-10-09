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
    "novel_slug": "five-element-overlord-i-can-upgrade-everything",
    "start_url": "https://freewebnovel.com/novel/five-element-overlord-i-can-upgrade-everything/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Cultivation",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 2,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_five_element_overlord_001_050",
    "final_audio": "output_five_element_overlord_001_050.mp3",
    "final_video": "final_five_element_overlord_001_050.mp4",
    "cover_image": "cover_five_element_overlord_001_050.jpg",
    "timestamps_file": "youtube_timestamps_five_element_overlord_001_050.txt",
    "subtitles_file": "subtitles_five_element_overlord_001_050.srt",
    "payload_file": "youtube_upload_payload_five_element_overlord_001_050.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "FIVE ELEMENT OVERLORD! I CAN UPGRADE EVERYTHING [Ch 1-50] | Cultivation LitRPG Audiobook Marathon",
    "tags": [
        "LitRPG Audiobook", "Five Element Overlord", "I Can Upgrade Everything", "Lu Chen",
        "Cultivation Audiobook", "Xianxia", "Progression Fantasy", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Dismissed by the entire cultivation world as a useless Five-Element waste, one disciple shatters the heavens!\n\n"
        "In a sect where single-element prodigies rule supreme, Lu Chen is cursed with the balanced Five Element Spiritual Root—a "
        "condemnation ensuring impossibly slow progress. But fate intervenes when he unlocks the supreme Infinite Upgrade Panel! "
        "With a simple command, ordinary mortal-grade pills evolve into flaw-free heavenly elixirs, damaged rusted swords transform into "
        "primordial flying artifacts, and basic cultivation manuals ascend into divine emperor scriptures!\n\n"
        "Watch Lu Chen defy sect scions, master all five elemental daos, and turn his supposed trash talent into an unstoppable "
        "force of primordial chaos!\n\n"
        "Welcome to Chapters 1 to 50 of 'Five Element Overlord: I Can Upgrade Everything!' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 01: The Mocked Five-Element Disciple & Infinite Upgrade Panel Awakening\n"
        "• Ch 08: Upgrading Impure Qi Gathering Pills to Flawless Heaven Grade\n"
        "• Ch 15: Protecting Senior Sister Su Ling'er & Crushing Arrogant Disciples\n"
        "• Ch 22: Foundational Five Elements Manual Evolving into Emperor Scripture\n"
        "• Ch 29: Outer Sect Assessment & Five-Colored Divine Light Shockwave\n"
        "• Ch 35: Reforging a Broken Iron Blade into the Dragon-Vein Flying Sword\n"
        "• Ch 42: Pill Pavilion Shock & Elder Gu's Personal Disciple Offer\n"
        "• Ch 50: Sovereign Five Element Overlord & Primordial Chaos Foundation\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#FiveElementOverlord #ICanUpgradeEverything #LuChen #CultivationAudiobook #Xianxia #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (1, 5),
            "title": ["FIVE ELEMENT ROOT", "UPGRADE PANEL AWAKENING"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic 3D portrait of a handsome young male Taoist disciple, refined jawline, focused dark eyes, "
                "wearing humble light-blue outer sect cultivation robes with linen sashes. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a modest wooden cultivation room with bamboo shelves and an old bronze incense burner, "
                "revealing a floating translucent golden system interface window inscribed with ancient upgrade glyphs. "
                "Illumination from neon-cyan interface luminescence and floating five-colored elemental wisps, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (6, 10),
            "title": ["FLAWLESS ELIXIR", "PILL UPGRADE MIRACLE"],
            "fallback_color": (25, 30, 20),
            "prompt": (
                "Cinematic 3D portrait of a young male cultivator, sharp dark hair tied in a clean topknot, calm radiant amber eyes, "
                "holding a floating luminous golden pill emitting fragrant steam above his palm. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set beside an ancient stone alchemy furnace, revealing charred low-grade medicinal herbs transformed into shimmering "
                "spiritual jade in the distance. Illumination from blinding sun-gold pill halos and emerald alchemy flames, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (11, 15),
            "title": ["SENIOR SISTER", "SU LING'ER'S PROTECTION"],
            "fallback_color": (30, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of a resolute young male swordsman, neat hair, protective piercing dark eyes, "
                "wearing reinforced charcoal-and-azure robes with leather armguards. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set along an ornate outer sect stone pavilion overlooking mist-draped mountain peaks, revealing gentle Senior Sister "
                "Su Ling'er in fluttering silk pink-and-white robes stepping forward in the distance. Illumination from warm mountain sunrise rays and sparkling "
                "cherry blossom petals dancing on the wind, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (16, 20),
            "title": ["EMPEROR SCRIPTURE", "FIVE ELEMENT HARMONY"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of an enlightened male cultivator, floating wisps of black hair, serene glowing five-colored irises, "
                "surrounded by concentric rotating rings of Fire, Water, Wood, Metal, and Earth elemental symbols. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set atop an isolated mountain cliff under a starlit twilight sky, revealing an ancient tattered jade scroll radiating "
                "golden primordial scripture runes in the distance. Illumination from vibrant concentric elemental rings and starlight reflections, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (21, 25),
            "title": ["SECT ASSESSMENT", "FIVE-COLORED LIGHT"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of a proud young male disciple, intense focused expression, electric-azure pupils, "
                "placing his glowing palm against a colossal ancient spirit testing stone. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in a grand stone sect arena, revealing a colossal pillar of five-colored divine light shooting into the clouds, "
                "leaving surrounding elders and disciples stunned in the distance. Illumination from blinding white-gold magical shockwaves and iridescent "
                "elemental beams, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (26, 30),
            "title": ["DRAGON FLYING SWORD", "RUSTED BLADE REFORGED"],
            "fallback_color": (30, 15, 20),
            "prompt": (
                "Cinematic 3D portrait of a master swordsman disciple, windswept dark hair, razor-sharp golden eyes, "
                "directing a floating ornate silver-and-crimson flying sword with two fingers. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a mountain forge courtyard, revealing shattered rusted iron pieces dissolving into a roaring spectral crimson dragon "
                "wrapping around the newly forged blade in the distance. Illumination from intense scarlet sword qi arcs and crackling golden sparks, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (31, 35),
            "title": ["ELDER GU'S FAVOR", "PILL PAVILION ASCENT"],
            "fallback_color": (25, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of a dignified young male alchemist, refined handsome features, calm calculating amber eyes, "
                "wearing a pristine dark-silk alchemist robe with golden furnace crests. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in the grand hall of the Alchemy Pavilion surrounded by tiered shelves of jade elixir bottles, revealing Elder Gu "
                "stroking his white beard with profound admiration in the distance. Illumination from warm brass lantern light and glowing purple elixir vapours, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (36, 40),
            "title": ["FOREST AMBUSH", "WANG CLAN RETRIBUTION"],
            "fallback_color": (35, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of a cold commanding cultivator warrior, dark hair whipped by kinetic winds, luminous violet-gold eyes, "
                "unleashing a barrier of interlocking elemental shields. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in a dark ancient pine forest shrouded in thick mountain fog, revealing arrogant scion Wang Tian and his enforcers "
                "staggering backward under a torrent of elemental sword qi in the distance. Illumination from sharp silver blade glints and roaring emerald wind blades, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (41, 45),
            "title": ["CHAOS SPIRIT ROOT", "PRIMORDIAL EVOLUTION"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of Cultivator Lu Chen undergoing breakthrough, majestic windswept dark hair, radiant chaotic-violet pupils, "
                "wearing dark flowing Taoist robes embroidered with celestial constellations. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside an underground spirit-stone grotto, revealing the five elemental spirits fusing into an ancient seed of pure "
                "primordial chaos in the distance. Illumination from blinding concentric yin-yang rings and radiant celestial nebula clouds, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (46, 50),
            "title": ["FIVE ELEMENT OVERLORD", "THE SECT TOURNAMENT"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of Lu Chen as the undisputed Overlord Champion, standing tall atop the grand marble arena stage, "
                "regal dark hair, commanding glowing amber-gold eyes, wearing imperial dark-azure and gold robes with flying sword at his back. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set against the vast panorama of soaring sect palaces and tens of thousands "
                "of cheering disciples under a radiant golden sunset sky in the distance. Illumination from brilliant auroras of sunrise-gold, cyan, and deep-violet spiritual energy, "
                "deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))