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
    "novel_slug": "beast-taming-reincarnated-with-the-ultimate-bond-system",
    "start_url": "https://freewebnovel.com/novel/beast-taming-reincarnated-with-the-ultimate-bond-system/chapter-101",
    "start_chapter": 101,
    "end_chapter": 150,
    "default_topic": "Beast Tamer",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 1,  # Sequential processing to respect 15 RPM limits cleanly
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_beast_taming_101_150",
    "final_audio": "output_beast_taming_101_150.mp3",
    "final_video": "final_beast_taming_101_150.mp4",
    "cover_image": "cover_beast_taming_101_150.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_101_150.txt",
    "subtitles_file": "subtitles_beast_taming_101_150.srt",
    "payload_file": "youtube_upload_payload_beast_taming_101_150.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "COMMANDING PRIMORDIAL GOD BEASTS! ULTIMATE BOND SUPREMACY [Ch 101-150] | LitRPG Audiobook Marathon",
    "tags": [
        "LitRPG Audiobook", "Beast Taming", "Ultimate Bond System", "Reincarnated With The Ultimate Bond System",
        "Progression Fantasy", "Familiar Evolution", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Breaking past continental thresholds, our master tamer enters the supreme Primordial God-Beast Domains!\n\n"
        "Having unlocked multi-familiar domain fusions and ancient bloodline awakenings, our protagonist steps into deep-rift "
        "calamity zones where legendary beasts reign supreme. Through the continuous exponential feedback of the Ultimate Bond System, "
        "his soul space ascends into an immortal god-tier sanctuary, granting him divine armor synchronization, true elemental authority, "
        "and the power to awaken celestial qilin and phoenix lineages within his contracted familiars!\n\n"
        "Facing supreme empire grandmasters, abyssal void monarchs, and catastrophic prehistoric beast tides, "
        "watch him command his mythical beast pantheon to achieve absolute continental reign!\n\n"
        "Welcome to Chapters 101 to 150 of 'Beast Taming: Reincarnated With The Ultimate Bond System!' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 101: Entering the Primordial God-Beast Realm & Awakening SSS-Rank Soul Resonance\n"
        "• Ch 110: Ancient Phoenix Bloodline Metamorphosis & Rebirth Hellfire Breath\n"
        "• Ch 118: Subterranean Calamity Wyrm Purge & Deep Rift Sovereign Slaying\n"
        "• Ch 125: Contracting the Fourth Familiar & Celestial Thunder Kirin Covenant\n"
        "• Ch 132: Continental Grandmaster Arena Finals & Annihilating Imperial Scions\n"
        "• Ch 140: Multi-Familiar Godhead Armor Fusion & Deflecting Abyssal Void Spells\n"
        "• Ch 145: Ancient Celestial Altar Resonance & The Imperial Beast King Awakening\n"
        "• Ch 150: Supreme Mythic Beast God Sovereign Coronation & Continental Unification\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#BeastTaming #UltimateBondSystem #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (101, 105),
            "title": ["PRIMORDIAL REALM", "SSS-RANK RESONANCE"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of an ascending sovereign beast tamer, commanding sharp jawline, neat dark hair, "
                "radiant glowing electric-cyan and gold eyes, wearing ornate mithril-inlaid tactical battle robes with glowing runic conduits. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set upon an overlooking floating crystalline peak "
                "in the Primordial Beast Realm, revealing giant floating celestial continents and his evolved primary familiar bathed in golden starlight in the distance. "
                "Illumination from neon-cyan soul covenant rings and ambient starlight nebula clouds, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (106, 110),
            "title": ["PHOENIX BLOODLINE", "REBIRTH HELLFIRE"],
            "fallback_color": (40, 15, 20),
            "prompt": (
                "Cinematic 3D portrait of a young master tamer, windswept dark hair, confident fierce amber-gold eyes, "
                "wearing heavy heat-tempered dragon-scale armor with crimson clasps. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set atop an active volcanic mountain ridge under sunset, revealing his contracted flying familiar undergoing "
                "celestial metamorphosis into a colossal radiant solar phoenix spreading blinding scarlet and gold wings in the distance. "
                "Illumination from exploding magma rivers and shimmering solar feather trails, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (111, 115),
            "title": ["DEEP RIFT PURGE", "CALAMITY WYRM SLAY"],
            "fallback_color": (15, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of an unyielding warrior tamer, razor-sharp jawline, cold glowing violet-gold pupils, "
                "wielding an engraved kinetic hunting glaive, wearing dark obsidian armor. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set at the bottom of a colossal abyss rift trench, revealing an ancient titanic shadow wyrm collapsing "
                "under a coordinated multi-elemental bombardment from his familiars in the distance. "
                "Illumination from sharp silver weapon glints and glowing purple rift energy fissures, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (116, 120),
            "title": ["FOURTH FAMILIAR", "THUNDER KIRIN COVENANT"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of a dignified tamer sovereign, serene regal gaze, dark hair, glowing electric-azure irises, "
                "extending a glowing palm inscribed with a golden ancestral covenant seal. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in an ancient storm sanctuary temple, revealing a magnificent celestial Thunder Kirin wreathed in white lightning "
                "and shimmering azure scales lowering its head in absolute loyalty in the distance. "
                "Illumination from blinding lightning arcs and shimmering celestial soul rings, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (121, 125),
            "title": ["GRANDMASTER FINALS", "IMPERIAL ARENA SHOCK"],
            "fallback_color": (30, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of a tactical tamer prodigy, sharp facial planes, calm calculating sapphire eyes, "
                "wearing a tailored charcoal-and-gold imperial champion mantle over dark tactical garments. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a monumental circular imperial colosseum packed with tens of thousands of cheering nobles, "
                "revealing an elite empire prince's colossal armored drake pinned to the shattered arena floor by invisible soul pressure in the distance. "
                "Illumination from blinding cyan-white magical shockwaves and cheering spectator braziers, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (126, 130),
            "title": ["GODHEAD SOUL SYNC", "MULTI-BEAST ARMOR"],
            "fallback_color": (35, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of Cultivator Tamer undergoing divine fusion, floating dark hair, brilliant tri-colored glowing pupils, "
                "manifesting translucent ethereal spirit armor incorporating dragon scales, phoenix wings, and kirin gauntlets. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set above the clouds during an arcane thunderstorm, "
                "revealing dense concentric shockwaves of unified elemental force vaporizing surrounding dark cloud banks in the distance. "
                "Illumination from blinding gold, crimson, and cyan auroras, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (131, 135),
            "title": ["CHAOS RIFT INVASION", "TITAN BEAST DEFENSE"],
            "fallback_color": (35, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of a victorious tamer commander, razor-sharp jawline, glowing sun-gold eyes, "
                "wearing high-tier mithril-inlaid battle plate armor with a fluttering deep-navy cape. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set upon the high battlements of an imperial frontier city under siege, revealing an apocalyptic mountain-sized "
                "corrupted void titan collapsing under a synchronized barrage from his beast legion in the distance. "
                "Illumination from sunrise-gold magical artillery beams and billowing smoke trails, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (136, 140),
            "title": ["ANCESTRAL ALTAR", "BEAST KING CORONATION"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of a noble young sovereign tamer, dignified composed expression, radiant amethyst pupils, "
                "touching an ancient floating celestial obelisk inscribed with primeval beast runes. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside the sunken throne room of a prehistoric god-beast temple, revealing four contracted mythic familiars "
                "bathing in cascading pillars of celestial starlight mana in the distance. "
                "Illumination from radiant violet soul fire and floating golden divine characters, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (141, 145),
            "title": ["IMPERIAL CAPITAL", "ABYSS MONARCH PURGE"],
            "fallback_color": (25, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of the master tamer executing absolute imperial authority, dark windswept hair, intense dual-ringed sapphire-gold pupils, "
                "wearing ornate imperial dark-silver sovereign mantle robes. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set before the marble palace gates of the capital city, revealing invading rogue inquisitor covens disarmed and paralyzed "
                "under an expansive four-elemental beast domain field in the distance. "
                "Illumination from brilliant silver, azure, and gold energy streams, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (146, 150),
            "title": ["MYTHIC BEAST GOD", "CONTINENTAL REIGN"],
            "fallback_color": (20, 25, 50),
            "prompt": (
                "Cinematic 3D portrait of the Sovereign Mythic Beast God at the pinnacle of continental rule, majestic windswept dark hair, "
                "commanding sun-gold and sapphire eyes, wearing supreme imperial sovereign robes radiating multi-colored celestial halos. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set atop the highest throne tower overlooking sprawling united fantasy realms, "
                "revealing towering ancestral dragon, phoenix, kirin, and fenrir familiars standing loyally beside his throne under a breathtaking golden sunrise sky. "
                "Illumination from brilliant auroras of sunrise gold, cyan soul fire, and deep-violet mana, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
