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
    "start_url": "https://freewebnovel.com/novel/beast-taming-reincarnated-with-the-ultimate-bond-system/chapter-351",
    "start_chapter": 351,
    "end_chapter": 400,
    "default_topic": "Beast Taming",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_beast_taming_351_400",
    "final_audio": "output_beast_taming_351_400.mp3",
    "final_video": "final_beast_taming_351_400.mp4",
    "cover_image": "cover_beast_taming_351_400.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_351_400.txt",
    "subtitles_file": "subtitles_beast_taming_351_400.srt",
    "payload_file": "youtube_upload_payload_beast_taming_351_400.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "UNIVERSAL PRIMORDIAL BEAST AWAKENING! CHAOS REALM DOMINATION [Ch 351-400] | Beast Taming Audiobook Marathon",
    "tags": [
        "Beast Taming Audiobook", "Ultimate Bond System", "Reincarnated Beast Tamer",
        "Progression Fantasy", "Mythic Evolution", "Monster Taming LitRPG", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Pushing beyond the boundaries of interstellar starfields, our protagonist enters the enigmatic Primordial Chaos Realm!\n\n"
        "With the Ultimate Bond System unlocking origin-level synchronization multipliers, every mythical companion breaks through "
        "mortal and celestial bottlenecks into primordial godhood. From awakening the world-bearing Chaos Tortoise and forging pacts "
        "with ancient Void-Rupture Behemoths to guiding the Astral Phoenix into cosmic supernova rebirth, our protagonist commands "
        "an unstoppable legion of divine beast apexes.\n\n"
        "As ancient celestial god-clans, void dreadnought armadas, and primordial entities attempt to conquer human space, "
        "the sovereign beast tamer activates cosmic-tier bond domains to establish undisputed universal hegemony!\n\n"
        "Welcome to Chapters 351 to 400 of 'Beast Taming: Reincarnated with the Ultimate Bond System' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 351: Traversing the Cosmic Event Horizon into the Primordial Chaos Starfield\n"
        "• Ch 356: Origin Evolution: Awakening the World-Bearing Chaos Tortoise Defense Array\n"
        "• Ch 362: The Universal Tamer Summit: Subduing Arrogant Ancient God-Clan Scions\n"
        "• Ch 368: Primordial Void Incursion: Taming the Cosmic Void-Devouring Behemoth\n"
        "• Ch 374: Celestial Phoenix Empress Metamorphosis: Igniting Solar Supernova Domain Flames\n"
        "• Ch 380: Dimensional Law Synchronization: Telepathic Universal Command Unlocked\n"
        "• Ch 386: Annihilating the Void Sovereign Armada with Synchronized Beast Shockwaves\n"
        "• Ch 392: The Star-God Ancient Trial: Subjugating the Celestial Astral Kirin Sovereign\n"
        "• Ch 400: Universal Sovereign Coronation: The Undisputed Ruler of the Cosmic Beast Cosmos\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#BeastTaming #UltimateBondSystem #MonsterEvolution #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (351, 355),
            "title": ["CHAOS STARFIELD", "PRIMORDIAL HORIZON"],
            "fallback_color": (20, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of a master beast tamer traversing the cosmic chaos frontier, resolute chiseled jawline, dual-glowing golden and azure eyes reflecting universal origin laws, "
                "wearing high-tier star-forged commander armor adorned with ancient draconic bone pauldrons. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set upon the edge of a shattered dimensional gate in deep space, revealing vast swirling nebulae of gold and violet primordial gas clouds drifting across the cosmos in the distance. "
                "Illumination from radiant cyan dimensional conduits and distant starlight flares, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (356, 360),
            "title": ["CHAOS TORTOISE", "WORLD-BEARING SHIELD"],
            "fallback_color": (25, 30, 40),
            "prompt": (
                "Cinematic 3D portrait of the beast tamer mid-communion, calm focused expression, hand radiating concentrated emerald evolutionary light. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside an ancient hollow astral mountain chamber, "
                "revealing a colossal Chaos Tortoise bearing floating crystalline continents on its shell awakening with rumbling power in the distance. "
                "Illumination from radiant emerald origin runes and soft jade barrier matrices, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (361, 365),
            "title": ["UNIVERSAL SUMMIT", "CRUSHING GOD-CLAN RIVALS"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of the protagonist standing in absolute dominance, confident regal smirk, dark hair windswept by kinetic aura shockwaves. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside the grandiose floating celestial arena of the Universal Tamer Summit, "
                "revealing arrogant young lords of ancient star god-clans knocked back across fractured crystal tiles by overwhelming pressure in the distance. "
                "Illumination from brilliant celestial sunbeams and golden combat aura flares, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (366, 370),
            "title": ["VOID DEVOURER", "TAMING THE BEHEMOTH"],
            "fallback_color": (20, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of the tamer holding an ancient glowing primordial beast talisman, watchful razor-sharp gaze, fingers crackling with gravitational lightning. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set at the precipice of an abyssal dark-matter singularity, "
                "revealing a gargantuan Void-Devouring Behemoth with luminous purple dorsal plates lowering its titanic head in voluntary submission in the distance. "
                "Illumination from deep-violet void lightning and shimmering silver spatial wards, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (371, 375),
            "title": ["PHOENIX EMPRESS", "SUPERNOVA METAMORPHOSIS"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of the tamer commanding cosmic solar flames, noble resolute presence, eyes blazing with incandescent crimson-gold power. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set against the molten horizon of a burning star, "
                "revealing the Astral Phoenix Empress spreading majestic wings of cosmic supernova plasma that illuminate shattered asteroid rings in the distance. "
                "Illumination from blinding white-hot solar flares and swirling ruby firestorms, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (376, 380),
            "title": ["DIMENSIONAL LAW", "TELEPATHIC RESONANCE"],
            "fallback_color": (20, 25, 50),
            "prompt": (
                "Cinematic 3D portrait of the tamer in profound spiritual synchronization, serene divine aura, intricate golden origin runes glowing across his cheekbones and brow. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set within a zero-gravity cosmic matrix sanctum, "
                "revealing multifaceted celestial crystals revolving in harmony as neural bond conduits connect to cosmic beast silhouettes in the distance. "
                "Illumination from radiant sapphire starlight and vibrant golden soul matrices, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (381, 385),
            "title": ["SOVEREIGN ARMADA", "APOCALYPTIC ROAR"],
            "fallback_color": (30, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of the tamer directing a cosmic war fleet engagement, sharp commanding jawline, raising an outstretched hand surrounded by dense gravitational halos. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set against the burning wreckage of a dreadnought armada, "
                "revealing hostile alien war cruisers torn apart by a combined sonic and kinetic shockwave unleashed by his bonded dragon legion in the distance. "
                "Illumination from massive orange hull explosions and brilliant cyan laser volleys, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (386, 390),
            "title": ["CHAOS CORE", "INFINITE REFINEMENT"],
            "fallback_color": (25, 35, 35),
            "prompt": (
                "Cinematic 3D portrait of the tamer channeling the energy of a glowing cosmic orb, intense artistic focus, fingers delicately tracing floating runic arrays. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside the heart of an ancient celestial core foundry, "
                "revealing planetary-scale energy conduits channeling liquid starlight into his beast-evolution matrix in the distance. "
                "Illumination from radiant aquamarine core energy and warm golden forge sparks, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (391, 395),
            "title": ["ASTRAL KIRIN", "STAR-GOD TRIAL"],
            "fallback_color": (30, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of the tamer completing a supreme divine trial, commanding dignified posture, dual-colored irises pulsing with primordial authority. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside an ethereal palace carved from cosmic starlight crystals, "
                "revealing the legendary Celestial Astral Kirin Sovereign kneeling under a shining halo of origin laws in the distance. "
                "Illumination from radiant violet celestial lightning and warm golden starlight gradients, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (396, 400),
            "title": ["UNIVERSAL SOVEREIGN", "APEX BEAST GOD EMPEROR"],
            "fallback_color": (20, 20, 55),
            "prompt": (
                "Cinematic 3D portrait of the Universal Sovereign Beast Emperor at the apex of cosmic power, commanding sun-gold irises, "
                "wearing imperial cosmic robes woven from starlight silk and bordered with celestial dragon scales. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set atop the Grand Universal Spire overlooking united cosmic galaxy sectors, revealing an infinite armada of mythic bonded beasts soaring under a breathtaking aurora sky. "
                "Illumination from brilliant auroras of sunrise gold, radiant cyan soul conduits, and deep starlit nebulae, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
