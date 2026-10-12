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
    "start_url": "https://freewebnovel.com/novel/beast-taming-reincarnated-with-the-ultimate-bond-system/chapter-151",
    "start_chapter": 151,
    "end_chapter": 200,
    "default_topic": "Beast Tamer",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 1,  # Sequential processing to respect 15 RPM limits cleanly
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_beast_taming_151_200",
    "final_audio": "output_beast_taming_151_200.mp3",
    "final_video": "final_beast_taming_151_200.mp4",
    "cover_image": "cover_beast_taming_151_200.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_151_200.txt",
    "subtitles_file": "subtitles_beast_taming_151_200.srt",
    "payload_file": "youtube_upload_payload_beast_taming_151_200.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "PRIMORDIAL COSMIC GOD-BEAST SOVEREIGN! ULTIMATE BOND TRANSCENDENCE [Ch 151-200] | LitRPG Audiobook Marathon",
    "tags": [
        "LitRPG Audiobook", "Beast Taming", "Ultimate Bond System", "Reincarnated With The Ultimate Bond System",
        "Progression Fantasy", "Familiar Evolution", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Transcending mortal worlds and planetary planes, our master tamer enters the Primordial Astral Sea!\n\n"
        "With the Ultimate Bond System unlocking cosmic-tier resonance, our protagonist contracts astral god-beasts "
        "and awakens ancestral constellation forms across his entire spirit roster. The attribute feedback reaches godhood scale: "
        "every leap in his familiars' cosmic power grants him spatial warping, stellar soul armor, and absolute domain sovereignty!\n\n"
        "Facing planar conquerors, ancient void leviathans, and stellar empire fleet armadas, watch him command his "
        "pantheon of mythical beasts to conquer the stars and establish an eternal astral sanctuary!\n\n"
        "Welcome to Chapters 151 to 200 of 'Beast Taming: Reincarnated With The Ultimate Bond System!' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 151: Ascending into the Astral Void Sea & Awakening Cosmic Soul Resonance\n"
        "• Ch 160: Stellar Dragon Bloodline Metamorphosis & Galactic Sunfire Roar\n"
        "• Ch 168: Void Leviathan Rift Extermination & Slaying Dimensional Marauders\n"
        "• Ch 175: Contracting the Fifth Familiar & Celestial Chrono-Beast Covenant\n"
        "• Ch 182: Planar Overlord Tournament Clash & Crushing Starlight Empire Champions\n"
        "• Ch 190: Multi-Beast Stellar Constellation Fusion & Planetary Barrier Erection\n"
        "• Ch 195: Slaying the Void Sovereign Fleet with Unified Astral Divine Arts\n"
        "• Ch 200: Eternal God-Beast Emperor Ascendance & Cosmic Domain Unification\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#BeastTaming #UltimateBondSystem #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (151, 155),
            "title": ["ASTRAL VOID ASCENT", "COSMIC SOUL RESONANCE"],
            "fallback_color": (15, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of a cosmic beast sovereign, razor-sharp jawline, windswept dark hair, "
                "radiant glowing starlight-cyan eyes, wearing celestial mithril-inlaid armor with floating orbital runic rings. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set upon a drifting crystalline asteroid terrace "
                "overlooking a swirling purple-and-gold nebula, revealing his evolved spirit familiars bathed in celestial starfire in the distance. "
                "Illumination from neon-cyan astral soul contract matrices and glittering star clusters, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (156, 160),
            "title": ["STELLAR DRAGON", "GALACTIC SUNFIRE ROAR"],
            "fallback_color": (35, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of a commanding young beast master, confident focused gaze, luminous sun-gold irises, "
                "wearing blackened dragon-scale battle mantle adorned with gold celestial clasps. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on the shattered rim of a dying star crater, revealing his primary familiar transformed into a titanic stellar dragon "
                "unleashing a blinding torrent of cosmic white-gold sunfire across space in the distance. "
                "Illumination from blazing stellar flares and shimmering gold scales, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (161, 165),
            "title": ["VOID LEVIATHAN", "DIMENSIONAL RIFT PURGE"],
            "fallback_color": (20, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of an unyielding astral warrior tamer, dark hair whipped by gravitational eddies, piercing amethyst pupils, "
                "holding an engraved cosmic glaive radiating dark energy ripples, wearing reinforced obsidian space armor. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set before a massive dimensional void fissure in deep space, revealing an ancient tentacled abyssal leviathan "
                "shattered under a synchronized strike from his familiars in the distance. "
                "Illumination from sharp silver weapon gleams and violet spatial fractures, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (166, 170),
            "title": ["FIFTH FAMILIAR", "CHRONO-BEAST COVENANT"],
            "fallback_color": (25, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of a dignified planar contractor, calm regal gaze, dark hair, glowing electric-amber irises, "
                "extending a hand bearing a floating translucent hourglass-shaped soul seal. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside an ancient cosmic time sanctuary surrounded by floating temporal gears, revealing an elusive silver-furred "
                "Chrono-Beast wreathed in shimmering temporal clock glyphs lowering its head in absolute loyalty in the distance. "
                "Illumination from blinding silver chronal waves and celestial soul mist, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (171, 175),
            "title": ["PLANAR ARENA", "STARLIGHT EMPIRE CRUSHED"],
            "fallback_color": (30, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of a tactical tamer sovereign, cold calculating sapphire-gold eyes, sharp facial planes, "
                "wearing tailored charcoal-and-gold astral diplomat robes over dark tactical battle gear. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set within an orbital floating colosseum suspended above a ringed planet, revealing an arrogant stellar empire prince's "
                "colossal mechanical battle chimera grounded and dismantled under invisible gravity waves in the distance. "
                "Illumination from neon-cyan energy barriers and cheering galactic spectator platforms, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (176, 180),
            "title": ["CONSTELLATION FUSION", "PLANETARY SHIELD"],
            "fallback_color": (20, 35, 50),
            "prompt": (
                "Cinematic 3D portrait of Cultivator Tamer commanding divine cosmic harmony, floating dark hair, brilliant dual-ringed turquoise pupils, "
                "manifesting an intricate celestial star chart between outstretched palms. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in orbital space looking down at a blue fantasy world, revealing his five contracted familiars linked by glowing "
                "constellation leylines creating a massive iridescent planetary barrier in the distance. "
                "Illumination from radiant cyan, violet, and gold starlight beams, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (181, 185),
            "title": ["VOID FLEET INVASION", "ASTRAL WARSHIP PURGE"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic 3D portrait of a victorious fleet-commanding tamer, razor-sharp jawline, fierce glowing sun-gold eyes, "
                "wearing high-tier astral commander armor with a billowing deep-navy mantle. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set upon the exterior hull of a celestial war spire, revealing hundreds of enemy dark-iron space dreadnoughts "
                "exploding in silent brilliant supernovas under his beasts' coordinated elemental assault in the distance. "
                "Illumination from blinding yellow-white star explosions and crimson debris trails, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (186, 190),
            "title": ["CELESTIAL TEMPLE", "ANCESTRAL GODHEAD AWAKENING"],
            "fallback_color": (25, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of an ascending primordial tamer prodigy, serene majestic expression, radiant tri-colored irises, "
                "touching a massive ancient celestial monad obelisk pulsing with cosmic laws. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a sunken primordial pantheon hall drifting through space, revealing his contracted mythic beasts "
                "enveloped in colossal astral godhead phantoms roaring toward the cosmos in the distance. "
                "Illumination from radiant violet divine soul fire and floating golden primordial scripts, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (191, 195),
            "title": ["VOID OVERLORD SLAY", "STELLAR AUTHORITY"],
            "fallback_color": (25, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of the master tamer wielding supreme cosmic authority, windswept dark hair, intense glowing cyan-gold pupils, "
                "wearing imperial astral dark-silver battle plate. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set at the epicenter of a collapsing void realm, revealing a colossal ancient Void Sovereign dissolving "
                "into brilliant cosmic particles under a combined multi-beast divine judgment beam in the distance. "
                "Illumination from blinding white-gold cosmic beams and swirling stardust currents, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (196, 200),
            "title": ["ETERNAL GOD-BEAST EMPEROR", "COSMIC SOVEREIGN ASCENT"],
            "fallback_color": (20, 25, 50),
            "prompt": (
                "Cinematic 3D portrait of the Eternal God-Beast Sovereign at the pinnacle of cosmic supremacy, majestic windswept dark hair, "
                "commanding sun-gold and astral-azure eyes, wearing supreme celestial sovereign robes radiating multi-layered constellation crowns. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set atop an astral throne world overlooking billions of unified galaxies, "
                "revealing towering ancestral cosmic dragons, phoenixes, kirins, and void sovereigns flanking his throne under a breathtaking cosmic aurora sky. "
                "Illumination from brilliant auroras of sunrise gold, cyan soul fire, and deep-violet nebula luminescence, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
