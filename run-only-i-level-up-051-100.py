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
    "novel_slug": "only-i-level-up-wn",
    "start_url": "https://freewebnovel.com/novel/only-i-level-up-wn/chapter-51",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "Hunter",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 2,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_only_i_level_up_051_100",
    "final_audio": "output_only_i_level_up_051_100.mp3",
    "final_video": "final_only_i_level_up_051_100.mp4",
    "cover_image": "cover_only_i_level_up_051_100.jpg",
    "timestamps_file": "youtube_timestamps_only_i_level_up_051_100.txt",
    "subtitles_file": "subtitles_only_i_level_up_051_100.srt",
    "payload_file": "youtube_upload_payload_only_i_level_up_051_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "S-RANK RE-AWAKENING! MONARCH OF SHADOWS ASCENDANCE [Ch 51-100] | Solo Leveling Audiobook",
    "tags": [
        "LitRPG Audiobook", "Solo Leveling", "Only I Level Up", "Sung Jin-Woo",
        "S-Rank Hunter", "Shadow Monarch", "Red Gate", "Demon Castle", "Progression Fantasy", "Being A Bong"
    ],
    "desc_header": (
        "The world's weakest hunter has ceased to exist—now, an unprecedented sovereign walks the earth!\n\n"
        "Stepping out from the shadows of his job-change trial, Sung Jin-Woo shocks the Hunter Association "
        "by measuring beyond measurable limits on the mana crystal scanner. As South Korea's 10th official S-Rank Hunter, "
        "Jin-Woo plunges into lethal Red Gates, cleanses corrupted high-orc dungeons single-handedly, "
        "and ascends the burning tiers of the Demon Castle to forge the miracle cure: the Holy Water of Life!\n\n"
        "Welcome to Chapters 51 to 100 of 'Only I Level Up' (Solo Leveling) in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 51: Demon Castle Infiltration & Slaying Hell's Gatekeeper Cerberus\n"
        "• Ch 60: The Association Mana Explosion & 10th S-Rank Hunter Emergence\n"
        "• Ch 65: Trapped in the Red Gate & White Tiger Guild Trainee Disaster\n"
        "• Ch 70: Ice Monarch Baruka Slay & Forging Shadow Knight Iron\n"
        "• Ch 75: Demon Noble Clan Alliance & Ascending the Upper Towers\n"
        "• Ch 80: High Orc Dungeon Infiltration & S-Rank Porter Reveal\n"
        "• Ch 85: Great Shaman Kargalgan Annihilation & Tusk Joins the Shadows\n"
        "• Ch 90: Official 10th S-Rank Hunter License & Global Guild Tremors\n"
        "• Ch 95: Floor 100 Apex Duel with Demon King Baran & Sky Wyvern Kaisel\n"
        "• Ch 100: Holy Water of Life Miracle & The Jeju Island Calamity Approaches\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to Chugong. Subscribe for more!\n\n"
        "#SoloLeveling #OnlyILevelUp #SungJinWoo #SRankHunter #ShadowMonarch #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (51, 55),
            "title": ["HELL GATEKEEPER", "CERBERUS SLAYER"],
            "fallback_color": (35, 15, 15),
            "prompt": (
                "Cinematic 3D portrait of an elite Korean hunter, sharp jet-black hair, intense glowing sapphire-blue eyes, "
                "wearing sleek reinforced stealth armor with dark violet trims. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against the burning obsidian gates of the Demon Castle enveloped in roaring brimstone fires, revealing "
                "a colossal three-headed demonic hound Cerberus with molten red eyes collapsing in defeat in the distance. Illumination from crackling "
                "electric-blue mana daggers and roaring amber hellfire braziers, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (56, 60),
            "title": ["MANA OVERFLOW", "THE 10TH S-RANK"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of a commanding young male hunter, neat black hair, calm imposing gaze with faint violet pupils, "
                "wearing a stylish dark casual coat over a tailored charcoal shirt. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside the Hunter Association testing chamber, revealing a fractured giant transparent mana crystal "
                "glowing beyond readable capacity with stunned association inspectors reeling backward in the distance. Illumination from blinding white-cyan "
                "magical radiance and neon-blue holographic data screens, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (61, 65),
            "title": ["THE RED GATE", "FROZEN DESOLATION"],
            "fallback_color": (20, 35, 50),
            "prompt": (
                "Cinematic 3D portrait of a composed male hunter sovereign, dark windswept hair, glowing azure eyes, "
                "wearing heavy dark leather insulated hunting armor with fur collar. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against an apocalyptic frozen forest wasteland enclosed within an impassable crimson dimensional dome, "
                "revealing shivering guild trainees huddled behind rock barriers in the distance. Illumination from howling cyan snowstorm vortexes "
                "and an ominous blood-red sky rift, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (66, 70),
            "title": ["ICE MONARCH BARUKA", "SHADOW KNIGHT IRON"],
            "fallback_color": (15, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of an apex assassin hunter, sleek black hair, fierce glowing blue-violet eyes, "
                "wielding dual enchanted daggers releasing misty azure frost trails. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against a bloodstained snowfield clearing, revealing white-haired Ice Elf Warlord Baruka wielding curved silver scimitars "
                "clashing against towering Shadow Knight Iron in the distance. Illumination from gleaming glacier reflections and pulsing deep-purple soul flames, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (71, 75),
            "title": ["DEMONIC TOWERS", "NOBLE CLAN ALLIANCE"],
            "fallback_color": (30, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of a regal male hunter, refined sharp jawline, brilliant glowing amethyst eyes, "
                "wearing midnight-black battle robes embroidered with silver mana thread. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set upon a towering gothic fortress balcony overlooking tiered demon cities, revealing demon noble girl Esil Radiru "
                "with crimson horns and silver hair looking onward in the distance. Illumination from floating violet soul lanterns and glowing golden "
                "alchemy ingredient vials, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (76, 80),
            "title": ["HIGH ORC DUNGEON", "PORTER INFILTRATION"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of a restrained male hunter disguised as a porter, messy black hair, hidden calculating golden-amber eyes, "
                "carrying an oversized reinforced leather supply bag over dark tactical gear. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a colossal red-rock subterranean mine, revealing towering red-skinned High Orc warriors armed with jagged broadswords "
                "encircling panicked A-rank assault squads in the distance. Illumination from crackling blood-red tribal torches and deep cavern shadows, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (81, 85),
            "title": ["HYMN OF FIRE", "SHADOW SHAMAN TUSK"],
            "fallback_color": (45, 15, 20),
            "prompt": (
                "Cinematic 3D portrait of the Shadow Monarch in absolute fury, dark hair whipped by violent mana winds, piercing glowing cyan-violet eyes, "
                "raising his hand to unleash an army of black shadow soldiers. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in a grand subterranean sacrificial hall, revealing High Orc Great Shaman Kargalgan overwhelmed by an enormous pillar "
                "of incinerating scarlet flame in the distance. Illumination from catastrophic crimson firestorms and rising ethereal blue shadow spirits, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (86, 90),
            "title": ["S-RANK LICENSE", "NATIONAL HEADQUARTERS"],
            "fallback_color": (25, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of Sung Jin-Woo as an official S-Rank celebrity hunter, sharp styled black hair, calm majestic eyes, "
                "wearing a sharp dark-navy designer suit with crisp white collar. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in front of the Korean Hunter Association press auditorium, revealing blinding camera flashes, roaring crowds of reporters, "
                "and guild masters watching intently in the distance. Illumination from strobe-light camera flashes and warm golden interior architectural lighting, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (91, 95),
            "title": ["MONARCH OF WHITE FLAMES", "DEMON KING BARAN"],
            "fallback_color": (35, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of a battle-hardened male sovereign hunter, razor-sharp focus, blazing neon-blue eyes, "
                "wearing shattered obsidian dragon armor sparking with kinetic energy. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on the floating ruined pinnacle of Demon Castle Floor 100, revealing Demon King Baran cloaked in crackling white lightning "
                "riding a monstrous sky wyvern in the distance. Illumination from blinding white electrical arcs and explosive magenta magical shockwaves, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (96, 100),
            "title": ["HOLY WATER OF LIFE", "SHADOW WYVERN KAISEL"],
            "fallback_color": (20, 30, 50),
            "prompt": (
                "Cinematic 3D portrait of Sung Jin-Woo riding high across the twilight clouds, windswept black hair, majestic glowing violet eyes, "
                "wearing his iconic fluttering imperial black trench coat. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set atop the soaring black-and-purple Shadow Wyvern Kaisel above the Seoul skyline, revealing a shimmering golden flask "
                "of Holy Water of Life glowing in his hand in the distance. Illumination from radiant golden divine elixir luminescence and deep-violet soul mist trails, "
                "deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
