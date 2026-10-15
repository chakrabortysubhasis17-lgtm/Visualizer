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
    "start_url": "https://freewebnovel.com/novel/beast-taming-reincarnated-with-the-ultimate-bond-system/chapter-251",
    "start_chapter": 251,
    "end_chapter": 300,
    "default_topic": "Beast Taming",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_beast_taming_251_300",
    "final_audio": "output_beast_taming_251_300.mp3",
    "final_video": "final_beast_taming_251_300.mp4",
    "cover_image": "cover_beast_taming_251_300.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_251_300.txt",
    "subtitles_file": "subtitles_beast_taming_251_300.srt",
    "payload_file": "youtube_upload_payload_beast_taming_251_300.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "SUPREME MYTHIC BEAST EVOLUTION! ULTIMATE BOND SYSTEM DOMINATES THE SECTOR [Ch 251-300] | Beast Taming Audiobook Marathon",
    "tags": [
        "Beast Taming Audiobook", "Ultimate Bond System", "Reincarnated Beast Tamer",
        "Progression Fantasy", "Mythic Evolution", "Monster Taming LitRPG", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Pushing past regional federation boundaries, the ultimate beast tamer ascends into high-tier sovereign domains!\n\n"
        "With the unstoppable power of the Ultimate Bond System, every mythical creature, ancient spirit beast, and primordial dragon "
        "linked to his soul unlocks hidden evolutionary pathways, terrifying divine skills, and absolute loyalty multipliers. "
        "As hostile beast-taming clans, arrogant imperial academies, and corrupt sector syndicates attempt to usurp his rare companions, "
        "our protagonist and his bonded beast army unleash apocalyptic combat power to crush all opposition!\n\n"
        "Watch him shatter legendary evolutionary bottlenecks, forge unbreakable spiritual pacts, and establish an undisputed beast domain!\n\n"
        "Welcome to Chapters 251 to 300 of 'Beast Taming: Reincarnated with the Ultimate Bond System' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 251: Entering the Sovereign Beast Domain & Awakening the Ancestral Dragon Bloodline\n"
        "• Ch 258: Mythic Evolution: Transforming the Shadow Panther into a Nine-Tailed Void Stalker\n"
        "• Ch 265: The Imperial Beast Tournament: Demolishing Rival Guild Masters with Shared Buffs\n"
        "• Ch 272: Exploring the Primordial Ruin Wards & Taming Ancient Spirit Guardians\n"
        "• Ch 279: Syndicate Incursion: Crushing Corrupt Tamer Cartels with Combined Beast Domain\n"
        "• Ch 286: Soul Synchronization Breakthrough: Achieving Telepathic Combat Mastery\n"
        "• Ch 293: The Celestial Phoenix Nest: Securing Divine Flames and Reincarnation Herbs\n"
        "• Ch 300: Supreme Beast Tamer Coronation: Establishing the Ultimate Sovereign Sanctuary\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#BeastTaming #UltimateBondSystem #MonsterEvolution #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (251, 255),
            "title": ["SOVEREIGN DOMAIN", "DRAGON BLOODLINE AWAKENING"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of a master beast tamer, sharp chiseled jawline, glowing gold-and-azure eyes reflecting telepathic bonds, "
                "wearing sleek dark-azure beast hunter robes interwoven with silver scaling. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set atop an ancient misty mountain summit overlooking a vast beast sanctuary, revealing a majestic primordial dragon "
                "coiling in the clouds overhead in the distance. Illumination from radiant cyan soul-bond matrices and golden sunrise rays, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (256, 261),
            "title": ["MYTHIC EVOLUTION", "VOID STALKER METAMORPHOSIS"],
            "fallback_color": (30, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of the beast tamer mid-synchronization, intense focused expression, hands glowing with evolutionary light. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a radiant spiritual evolution chamber, "
                "revealing a sleek shadow panther transforming into a majestic Nine-Tailed Void Stalker wreathed in shimmering purple starlight in the distance. "
                "Illumination from blinding violet evolution energy and brilliant white rune rings, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (262, 267),
            "title": ["IMPERIAL TOURNAMENT", "DOMINATING RIVAL GUILDS"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of the confident tamer, calm commanding posture, wrapped in a shared combat aura with his bonded beasts. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a colossal gladiatorial beast arena filled with roaring crowds, "
                "revealing rival guild masters reeling back as their elite beasts submit to absolute pressure in the distance. "
                "Illumination from dazzling golden stadium floodlights and electric-blue combat sparks, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (268, 273),
            "title": ["PRIMORDIAL RUINS", "SPIRIT GUARDIAN PACT"],
            "fallback_color": (15, 30, 25),
            "prompt": (
                "Cinematic 3D portrait of the tamer holding an ancient glowing beast talisman, watchful discerning eyes, dark wind-swept hair. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set within overgrown moss-covered stone ruins of a lost civilization, "
                "revealing an ethereal multi-winged ancient spirit guardian kneeling in voluntary oath in the distance. "
                "Illumination from bioluminescent emerald forest flora and soft golden relic light, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (274, 279),
            "title": ["SYNDICATE INCURSION", "COMBINED BEAST DOMAIN"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of the tamer in fierce battle stance, razor-sharp gaze, glowing combat aura surging across his shoulders. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set across a shattered canyon pass, revealing corrupt cartel mercenaries "
                "and their mechanical war beasts crushed under an overwhelming gravity-beast domain in the distance. "
                "Illumination from neon-red syndicate explosives and radiant golden bond shockwaves, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (280, 285),
            "title": ["SOUL SYNCHRONIZATION", "TELEPATHIC COMBAT"],
            "fallback_color": (20, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of the tamer in deep meditation, serene majestic expression, dual-colored irises pulsing with telepathic resonance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a floating crystal sanctuary chamber, "
                "revealing intricate golden neural link pathways connecting him to floating holographic beast silhouettes in the distance. "
                "Illumination from soft cyan starlight and radiant golden mind-matrices, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (286, 291),
            "title": ["CELESTIAL PHOENIX NEST", "DIVINE FLAME HARVEST"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of the tamer shielding his face from intense heat, determined resolute glare, wearing heat-resistant scale armor. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set atop a blazing volcanic caldera nest, "
                "revealing a magnificent scarlet celestial phoenix spreading wings of pure sacred flame under a twilight sky in the distance. "
                "Illumination from roaring crimson flames and brilliant white-hot plasma light, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (292, 296),
            "title": ["GUILD EXPANSION", "SANCTUARY FORTRESS"],
            "fallback_color": (20, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of the tamer overlooking his growing domain, calm satisfied smile, arms crossed over tailored battle attire. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set upon the high balcony of a newly constructed tamer fortress, "
                "revealing hundreds of diverse bonded beasts and trainers living in harmony across terraced mountain valleys in the distance. "
                "Illumination from warm afternoon sunbeams and shimmering protective barrier domes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (297, 299),
            "title": ["SUPREME TAINER TRIAL", "ABSOLUTE DOMINANCE"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the tamer commanding a supreme energy array, commanding posture, eyes flashing with blinding gold power. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a dimensional trial arena, "
                "revealing ancient celestial beast test entities bowing in absolute submission to his ultimate bond authority in the distance. "
                "Illumination from vibrant violet portal rifts and radiant golden divine light, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (300, 300),
            "title": ["SOVEREIGN CORONATION", "THE ULTIMATE BOND"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Supreme Beast Tamer Sovereign at the pinnacle of his journey, serene invincible presence, commanding golden pupils, "
                "wearing regal midnight-blue sovereign robes interwoven with celestial dragon scales. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set atop a soaring celestial spire overlooking united world sectors, revealing an endless armada of mythic bonded beasts soaring across a breathtaking aurora sky. "
                "Illumination from brilliant auroras of sunrise gold, cyan soul energy, and starlit nebulas, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
