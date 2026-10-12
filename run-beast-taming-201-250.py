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
    "start_url": "https://freewebnovel.com/novel/beast-taming-reincarnated-with-the-ultimate-bond-system/chapter-201",
    "start_chapter": 201,
    "end_chapter": 250,
    "default_topic": "Beast Tamer",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 1,  # Sequential processing to respect 15 RPM limits cleanly
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_beast_taming_201_250",
    "final_audio": "output_beast_taming_201_250.mp3",
    "final_video": "final_beast_taming_201_250.mp4",
    "cover_image": "cover_beast_taming_201_250.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_201_250.txt",
    "subtitles_file": "subtitles_beast_taming_201_250.srt",
    "payload_file": "youtube_upload_payload_beast_taming_201_250.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "PRIMORDIAL CREATION GOD-BEAST REALM! ULTIMATE BOND OMNIPOTENCE [Ch 201-250] | LitRPG Audiobook Marathon",
    "tags": [
        "LitRPG Audiobook", "Beast Taming", "Ultimate Bond System", "Reincarnated With The Ultimate Bond System",
        "Progression Fantasy", "Familiar Evolution", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Transcending dimensional realities into the Primordial Creation God-Beast Sanctuary!\n\n"
        "With the Ultimate Bond System breaking past universal thresholds, our protagonist awakens the Origin Resonance Law. "
        "Every familiar under his covenant undergoes Primordial Metamorphosis—evolving from stellar sovereigns into living "
        "conceptual cosmic pillars capable of bending spacetime, creating pocket universes, and nullifying absolute void corruption!\n\n"
        "Facing Primordial Abyssal Progenitors, outer-god hive clusters, and celestial pantheon arbiters seeking to reset the cosmos, "
        "watch him command his supreme divine familiar legion to establish eternal universal dominion!\n\n"
        "Welcome to Chapters 201 to 250 of 'Beast Taming: Reincarnated With The Ultimate Bond System!' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 201: Entering the Origin Sanctuary & Unlocking Conceptual Bond Matrices\n"
        "• Ch 208: Primordial Chaos Dragon Awakening & Void Singularity Breath\n"
        "• Ch 215: Cosmic Abyssal Hive Cluster Purge & Slaying Swarm Progenitors\n"
        "• Ch 222: Contracting the Sixth Familiar & Genesis World-Turtle Covenant\n"
        "• Ch 229: Outer-God Pantheon Arena Clash & Nullifying Conceptual Decrees\n"
        "• Ch 235: Universal Origin Leyline Fusion & Macrocosmic Domain Erection\n"
        "• Ch 242: Slaying the Primordial Void Arbiter with Absolute Covenant Sync\n"
        "• Ch 250: Omnipotent Creation God-Beast Sovereign Ascendance & Cosmic Throne Rule\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#BeastTaming #UltimateBondSystem #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (201, 205),
            "title": ["ORIGIN SANCTUARY", "CONCEPTUAL BOND MATRIX"],
            "fallback_color": (15, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of an omnipotent beast sovereign, sharp chiselled jawline, windswept dark hair, "
                "radiant glowing genesis-gold and electric-cyan pupils, wearing cosmic origin mantle armor inlaid with celestial starmaps. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set within an ancient primordial creation nexus "
                "surrounded by floating white-marble conceptual pillars, revealing his evolved familiars radiating blinding celestial halos in the distance. "
                "Illumination from neon-cyan soul bond matrices and shimmering stardust auroras, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (206, 210),
            "title": ["CHAOS DRAGON", "VOID SINGULARITY BREATH"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic 3D portrait of a commanding young beast master, cold calculating expression, luminous sun-gold irises, "
                "wearing blackened dragon-scale battle armor adorned with platinum celestial clasps. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set before a swirling cosmic event horizon in deep space, revealing his primary familiar manifested as an immense "
                "Chaos Primordial Dragon unleashing a blinding singularity beam of white-gold cosmic fire in the distance. "
                "Illumination from blazing stellar flares and shimmering iridescent scales, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (211, 215),
            "title": ["ABYSSAL HIVE", "SWARM PROGENITOR PURGE"],
            "fallback_color": (20, 10, 30),
            "prompt": (
                "Cinematic 3D portrait of an unyielding warrior tamer, dark hair whipped by gravitational currents, piercing amethyst pupils, "
                "holding an engraved cosmic origin glaive radiating dark energy ripples, wearing reinforced obsidian space armor. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set before a colossal bio-mechanical void hive structure, "
                "revealing a gargantuan corrupted Swarm Progenitor disintegrating under a synchronized assault from his familiars in the distance. "
                "Illumination from sharp silver weapon gleams and violet spatial fractures, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (216, 220),
            "title": ["SIXTH FAMILIAR", "GENESIS WORLD-TURTLE"],
            "fallback_color": (20, 30, 40),
            "prompt": (
                "Cinematic 3D portrait of a dignified cosmic contractor, calm regal gaze, dark hair, glowing emerald-cyan irises, "
                "extending a hand bearing a floating translucent world-creation soul seal. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set above a boundless celestial ocean of starlight, revealing a colossal Genesis World-Turtle bearing a lush fantasy "
                "continent on its obsidian shell lowering its head in absolute loyalty in the distance. "
                "Illumination from glowing emerald life leylines and sparkling astral mist, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (221, 225),
            "title": ["PANTHEON ARENA", "OUTER-GOD DECREE BROKEN"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of a tactical tamer sovereign, cold calculating sapphire-gold eyes, sharp facial planes, "
                "wearing tailored charcoal-and-gold astral high-commander robes over dark tactical battle gear. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a grand divine court arena suspended above a golden nebula, revealing an arrogant outer-god arbiter's "
                "colossal golden avatar shattered into glass-like fragments under invisible origin pressure in the distance. "
                "Illumination from neon-cyan energy barriers and cheering galactic spectator platforms, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (226, 230),
            "title": ["ORIGIN LEYLINES", "MACROCOSMIC SHIELD"],
            "fallback_color": (20, 35, 45),
            "prompt": (
                "Cinematic 3D portrait of Cultivator Tamer commanding primordial creation laws, floating dark hair, brilliant dual-ringed turquoise pupils, "
                "manifesting an intricate universe-scale constellation matrix between outstretched palms. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in deep space overlooking multiple spiral galaxies, revealing his six contracted familiars linked by glowing "
                "creation leylines erecting a massive multi-layered dimensional barrier across star systems in the distance. "
                "Illumination from radiant cyan, violet, and gold starlight beams, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (231, 235),
            "title": ["VOID ARBITER", "CONCEPTUAL JUDGMENT PURGE"],
            "fallback_color": (35, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of a victorious cosmic supreme commander, razor-sharp jawline, fierce glowing sun-gold eyes, "
                "wearing high-tier origin commander armor with a billowing deep-navy mantle. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set at the edge of a collapsing dimensional boundary, revealing an ancient Void Arbiter entity dissolving into "
                "shimmering cosmic dust under a unified barrage from his divine familiar pantheon in the distance. "
                "Illumination from blinding yellow-white star explosions and crimson debris trails, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (236, 240),
            "title": ["CREATION TEMPLE", "ORIGIN THRONE AWAKENING"],
            "fallback_color": (25, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of an ascending primordial tamer prodigy, serene majestic expression, radiant tri-colored irises, "
                "touching an ancient floating monad obelisk pulsing with genesis laws. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a grand creation temple drifting through a sea of galaxies, revealing his contracted mythic beasts "
                "enveloped in colossal astral godhead phantoms roaring toward the cosmos in the distance. "
                "Illumination from radiant violet divine soul fire and floating golden primordial scripts, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (241, 245),
            "title": ["ABSOLUTE HARMONY", "COSMIC BOND SYNC"],
            "fallback_color": (25, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of the master tamer wielding supreme cosmic authority, windswept dark hair, intense glowing cyan-gold pupils, "
                "wearing imperial astral dark-silver battle plate. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set at the core of a newly born pocket universe, revealing six mythical creation beasts circling in perfect "
                "celestial orbit around him, radiating pure elemental genesis energy in the distance. "
                "Illumination from blinding white-gold cosmic beams and swirling stardust currents, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (246, 250),
            "title": ["OMNIPOTENT SOVEREIGN", "UNIVERSAL THRONE ASCENT"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of the Omnipotent God-Beast Sovereign at the absolute zenith of reality, majestic windswept dark hair, "
                "commanding sun-gold and astral-azure eyes, wearing supreme celestial sovereign robes radiating multi-layered constellation crowns. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set atop the Universal Origin Throne overlooking countless "
                "shimmering galaxies, revealing ancestral dragons, phoenixes, world-turtles, and void sovereigns flanking his throne under a breathtaking cosmic aurora sky. "
                "Illumination from brilliant auroras of sunrise gold, cyan soul fire, and deep-violet nebula luminescence, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
