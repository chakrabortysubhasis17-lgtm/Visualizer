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
    "start_url": "https://freewebnovel.com/novel/beast-taming-reincarnated-with-the-ultimate-bond-system/chapter-301",
    "start_chapter": 301,
    "end_chapter": 350,
    "default_topic": "Beast Taming",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_beast_taming_301_350",
    "final_audio": "output_beast_taming_301_350.mp3",
    "final_video": "final_beast_taming_301_350.mp4",
    "cover_image": "cover_beast_taming_301_350.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_301_350.txt",
    "subtitles_file": "subtitles_beast_taming_301_350.srt",
    "payload_file": "youtube_upload_payload_beast_taming_301_350.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "PRIMORDIAL STAR-GOD BEAST AWAKENING! APEX SECTOR WARRIOR TRANSCENDS REALMS [Ch 301-350] | Beast Taming Audiobook Marathon",
    "tags": [
        "Beast Taming Audiobook", "Ultimate Bond System", "Reincarnated Beast Tamer",
        "Progression Fantasy", "Mythic Evolution", "Monster Taming LitRPG", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Breaking past regional federation borders, the ultimate beast tamer enters the vast, cosmic interstellar battle sectors!\n\n"
        "Empowered by the boundless potential of the Ultimate Bond System, his contractual companions achieve primordial soul awakenings. "
        "From awakening the slumbering Celestial Void Dragon to forging divine pacts with ancient Starlight Kirins and Astral Warbeasts, "
        "every synchronized resonance triggers catastrophic stat surges and reality-bending domain skills.\n\n"
        "When extraterrestrial beast syndicates, intergalactic conquerors, and high-tier divine lineages assemble an armada to subjugate "
        "Earth's sovereign sector, our protagonist unleashes an insurmountable legion of bonded mythic apexes to redefine cosmic hierarchy!\n\n"
        "Welcome to Chapters 301 to 350 of 'Beast Taming: Reincarnated with the Ultimate Bond System' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 301: Crossing Interstellar Warp Thresholds & Entering the Cosmic Beast Realm\n"
        "• Ch 308: Awakening the Ancient Starlight Kirin: Unlocking Cosmic Resonance Buffs\n"
        "• Ch 315: The Grand Astral Coliseum: Obliterating High-Tier Alien Tamers in Single Rounds\n"
        "• Ch 322: Deep Void Rift Expedition: Taming the Primordial Space-Rupture Serpent\n"
        "• Ch 329: Interstellar Cartel Incursion: Annihilating Extraterrestrial Siege Mech Legions\n"
        "• Ch 336: Divine Core Refinement: Forging the Star-God Beast Tamer Soul Matrix\n"
        "• Ch 343: The Astral Phoenix Rebirth: Igniting Solar Supernova Domain Flames\n"
        "• Ch 350: Sovereign Interstellar Ruler: Establishing Earth's Inviolable Cosmic Beast Domain\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#BeastTaming #UltimateBondSystem #MonsterEvolution #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (301, 305),
            "title": ["INTERSTELLAR THRESHOLD", "COSMIC BEAST REALM"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of a master beast tamer entering the cosmic void, resolute chiseled jawline, dual-toned gold and cyan eyes glowing with telepathic authority, "
                "wearing sleek star-metal combat armor overlaid with radiant dragon-scale filigree. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set upon a massive floating interstellar warp platform, revealing swirling purple-and-cyan nebulae and colossal alien beast dreadnoughts drifting in deep space in the distance. "
                "Illumination from luminous neon-cyan warp conduits and starlight reflections, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (306, 310),
            "title": ["STARLIGHT KIRIN", "ASTRAL BOND RESONANCE"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the beast tamer mid-communion, calm transcendent expression, hands gently channeling starlight runes. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a hollow crystalline asteroid sanctuary, "
                "revealing a magnificent Starlight Kirin wreathed in blinding azure constellations and silver astral flames bowing in voluntary loyalty in the distance. "
                "Illumination from brilliant celestial starlight and glowing golden system matrices, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (311, 315),
            "title": ["ASTRAL COLISEUM", "INTERSTELLAR DOMINANCE"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of the tamer standing in effortless victory, composed haughty smirk, dark hair windswept by kinetic shockwaves. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set within a massive orbital gladiatorial coliseum, "
                "revealing alien warlords and their titanic cybernetic war beasts crashing into the arena forcefields under overwhelming gravity pressure in the distance. "
                "Illumination from blinding orbital floodlights and electric-gold aura flares, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (316, 320),
            "title": ["VOID RIFT EXPEDITION", "SPACE-RUPTURE SERPENT"],
            "fallback_color": (25, 15, 40),
            "prompt": (
                "Cinematic 3D portrait of the tamer tracking an anomaly, sharp calculating gaze, wielding an ancient stellar beast-guiding staff. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set at the edge of a jagged planar fissure in deep space, "
                "revealing an enormous iridescent Space-Rupture Serpent coiling gracefully through shattered dimensions in the distance. "
                "Illumination from eerie violet rift emissions and pale cyan spatial runes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (321, 325),
            "title": ["CARTEL INVASION", "APEX BEAST CRUSH"],
            "fallback_color": (30, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of the tamer in decisive offensive stance, fierce focused glare, surrounded by swirling gravitational pressure rings. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set across the burning hull of an extraterrestrial battle cruiser, "
                "revealing armored cartel mercenary forces shattered by shockwaves from his summoned beast vanguard in the distance. "
                "Illumination from roaring orange artillery explosions and blinding white kinetic impacts, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (326, 330),
            "title": ["DIVINE SOUL MATRIX", "STAR-GOD HARMONY"],
            "fallback_color": (20, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of the tamer in deep core meditation, serene divine aura, pulsing runic meridians visible beneath his skin. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a zero-gravity astral core chamber, "
                "revealing multifaceted celestial crystals revolving in concentric rings around his spiritual core in the distance. "
                "Illumination from deep sapphire starlight, emerald soul fire, and golden halo arrays, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (331, 335),
            "title": ["ASTRAL PHOENIX", "SUPERNOVA DOMAIN"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of the tamer commanding cosmic solar flames, unwavering noble presence, eyes blazing with crimson-gold power. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set overlooking a dying stellar star, "
                "revealing a glorious Astral Phoenix spreading cosmic supernova wings that bathe surrounding planetary rings in divine light in the distance. "
                "Illumination from blinding solar plasma flares and radiant scarlet firestorms, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (336, 340),
            "title": ["PLANETARY CITADEL", "THE COSMIC BEAST HAVEN"],
            "fallback_color": (25, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of the tamer overseeing the construction of his cosmic stronghold, arms crossed with calm pride, wearing tailored dark commander robes. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set on the observation bridge of a planetary orbital citadel, "
                "revealing thousands of diverse cosmic beasts roaming lush terraformed biomes beneath transparent planetary domes in the distance. "
                "Illumination from warm planetary sunrise rays and shimmering defensive shield arrays, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (341, 345),
            "title": ["INTERSTELLAR FLEET CLASH", "PRIMORDIAL ROAR"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the tamer directing an intergalactic sector clash, commanding posture, extending two fingers wrapped in dense kinetic lightning. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set against the backdrop of an asteroid belt warzone, "
                "revealing hostile alien dreadnought fleets routed by an apocalyptic shockwave unleashed from his bonded primordial dragons in the distance. "
                "Illumination from blinding white energy detonations and vibrant purple laser volleys, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (346, 350),
            "title": ["STAR-GOD SOVEREIGN", "COSMIC HEGEMONY"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of the Star-God Sovereign Beast Tamer at the absolute pinnacle of cosmic mastery, commanding sun-gold irises, "
                "wearing regal interstellar robes woven with starlight silk and celestial dragon bone armor plates. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set atop an ancient celestial throne spire overlooking endless colonized solar sectors, revealing vast legions of bonded mythic cosmic beasts patrolling the cosmos under a breathtaking galaxy aurora sky. "
                "Illumination from radiant galactic auroras, golden soul energy conduits, and brilliant nebula starlight, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
