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
    "novel_slug": "beast-taming-my-beasts-grind-die-and-respawn",
    "start_url": "https://freewebnovel.com/novel/beast-taming-my-beasts-grind-die-and-respawn/chapter-142",
    "start_chapter": 142,
    "end_chapter": 187,
    "default_topic": "Beast Taming Respawn",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_beast_grind_die_respawn_142_187",
    "final_audio": "output_beast_grind_die_respawn_142_187.mp3",
    "final_video": "final_beast_grind_die_respawn_142_187.mp4",
    "cover_image": "cover_beast_grind_die_respawn_142_187.jpg",
    "timestamps_file": "youtube_timestamps_beast_grind_die_respawn_142_187.txt",
    "subtitles_file": "subtitles_beast_grind_die_respawn_142_187.srt",
    "payload_file": "youtube_upload_payload_beast_grind_die_respawn_142_187.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "INFINITE DEATH RESPAWN GRIND! TAMED BEASTS DIE TO UNLOCK GOD-TIER EVOLUTIONS [Ch 142-187] | LitRPG Audiobook Marathon",
    "tags": [
        "Beast Taming", "My Beasts Grind Die and Respawn", "Progression Fantasy",
        "LitRPG Audiobook", "Infinite Respawn", "Monster Taming", "Overpowered MC", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "In a ruthless world of fierce beast tamers and lethal spatial rifts, our protagonist exploits the ultimate "
        "cheat: an infinite respawn and death-loop grinding system where every casualty fuels game-breaking evolutions!\n\n"
        "While other tamers pamper their contracted beasts in terror of permanent death, our tamer sends his combat partners "
        "straight into high-tier death zones, suicidal boss gauntlets, and deadly forbidden trials. Every death returns his beasts "
        "stronger, immune to previous lethal damage, and stacked with terrifying passive combat perks, mutated talent traits, and "
        "sovereign-tier bloodlines!\n\n"
        "Watch him grind through elite regional academies, crush arrogant beast prodigies, and unleash an undying legion of "
        "mythical apex horrors that literally cannot stay dead!\n\n"
        "Welcome to Chapters 142 to 187 of 'Beast Taming: My Beasts Grind, Die, and Respawn' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 142: High-Level Spatial Fissure Expedition & Tactical Death-Loop Grinding\n"
        "• Ch 147: Mutated Shadow Beast Breakthrough: Gaining Abyssal Void Immunity via Respawn\n"
        "• Ch 152: Academy Combat Trials: Humiliating Elite Legacy Tamers with Kamikaze Tactics\n"
        "• Ch 157: Subterranean Magma Nest Incursion: Forging Flame-Resistant Divine Dragonscales\n"
        "• Ch 162: Underground Black Market Arena: Slaughtering Illegal Chimera Syndicates\n"
        "• Ch 167: Legendary Bloodline Mutation: The Undying Beast Legion Transcends Rank Ceilings\n"
        "• Ch 172: Ancient Relic Defense: Out-Attriting Swarms of Calamity Beasts Without Losses\n"
        "• Ch 177: Sovereign Beast Guild Challenge: Crushing Elder Champions with Undying Pets\n"
        "• Ch 182: Spatial Rupture Collapse: Sacrificing and Rebirthing at the Singularity Core\n"
        "• Ch 187: Apex Undying Commander: The Sovereign Tamer Who Commands the Cycles of Death\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#BeastTaming #MyBeastsGrindDieAndRespawn #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (142, 146),
            "title": ["SPATIAL FISSURE", "DEATH-LOOP GRINDING"],
            "fallback_color": (25, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of a young tactical beast tamer, sharp calculating eyes, short messy dark hair, "
                "wearing reinforced carbon-fiber beast handler combat armor. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a jagged spatial rift cavern crackling with neon-purple rift energy, revealing glowing "
                "translucent respawn system status panels and beast death-counter metrics floating in the distance. "
                "Illumination from deep amethyst spatial rifts and bright cyan system text reflections, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (147, 151),
            "title": ["VOID MUTATION", "RESPAWN BREAKTHROUGH"],
            "fallback_color": (20, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of the beast tamer mid-communion, calm analytical smirk, hands directing swirling rebirth runes. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside an underground stone dungeon chamber, "
                "revealing a defeated shadow wolf reforming from pure black mist and golden resurrection light with hardened crystal armor plates in the distance. "
                "Illumination from golden respawn halos and deep shadow essence, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (152, 156),
            "title": ["ACADEMY ARENA", "KAMIKAZE OVERWHELM"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of the tamer standing with casual indifference, hands in combat jacket pockets, observant confident smirk. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set in a grand modern arena colosseum with roaring spectator stands, "
                "revealing arrogant academy prodigies staring in sheer shock as his repeatedly reborn beasts relentlessly swarm their prized creatures in the distance. "
                "Illumination from bright stadium floodlights and electric-gold combat sparks, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (157, 161),
            "title": ["MAGMA CALDERA", "FIRE IMMUNITY FORGING"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of the tamer shielding his face from searing heat, intense resolute expression, wearing heat-resistant goggles on his forehead. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set along the stone rim of a bubbling volcanic magma caldera, "
                "revealing his armored reptile beast respawning directly inside molten lava pools while absorbing fiery essence into ruby scales in the distance. "
                "Illumination from roaring red-orange lava currents and blinding white-hot plasma flares, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (162, 166),
            "title": ["BLACK MARKET ARENA", "SYNDICATE MASSACRE"],
            "fallback_color": (30, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of the tamer in decisive battle command, sharp ruthless gaze, outstretched hand glowing with summoner command seals. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside an illegal neon-lit subterranean gladiatorial pit, "
                "revealing defeated illegal syndicate chimeras crushed beneath the claws of his undying beast vanguard in the distance. "
                "Illumination from flickering neon-red cage lights and bright azure command glyphs, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (167, 171),
            "title": ["SOVEREIGN BLOODLINE", "UNDYING LEGION ASCENT"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the tamer watching multiple summon circles blaze simultaneously, serene proud aura, eyes gleaming with golden system runes. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside an ancient underground training sanctum, "
                "revealing multiple mutated apex beasts standing side by side, wreathed in immortal golden rebirth flames in the distance. "
                "Illumination from radiant golden resurrection pillars and soft blue spiritual mist, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (172, 176),
            "title": ["SWARM ATTRITION", "ENDLESS DEFENSIVE CYCLE"],
            "fallback_color": (20, 30, 30),
            "prompt": (
                "Cinematic 3D portrait of the tamer calmly checking digital tactical logs on an arm console, unflinching composure amidst chaos. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set at the fortified gates of an ancient ruined fortress, "
                "revealing endless waves of invading wild monsters collapsing in exhaustion while his reborn beasts attack tirelessly in the distance. "
                "Illumination from flashing defense ward shields and pale silver moonlight, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (177, 180),
            "title": ["GUILD CHALLENGE", "ELDER SUBMISSION"],
            "fallback_color": (35, 20, 25),
            "prompt": (
                "Cinematic 3D portrait of the tamer standing on an elevated tournament platform, hands folded casually behind his back, cool dismissive gaze. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set in an opulent guild master dueling pavilion, "
                "revealing veteran tamer elders wiping cold sweat as their exhausted champion beasts drop to their knees in the distance. "
                "Illumination from warm golden chandeliers and crackling electric duel barriers, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (181, 184),
            "title": ["SINGULARITY CORE", "DEATH SACRIFICE OVERLOAD"],
            "fallback_color": (25, 15, 45),
            "prompt": (
                "Cinematic 3D portrait of the tamer commanding a massive gravitational collapse array, commanding posture, eyes flashing with dual-toned violet power. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set at the core of a fractured dimensional rift singularity, "
                "revealing chaotic vortexes of spatial lightning shattering reality while his beasts dive into the core to trigger system stat loops in the distance. "
                "Illumination from blinding white spatial energy detonations and deep purple gravitational arcs, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (185, 187),
            "title": ["APEX UNDYING COMMANDER", "DEATH-CYCLE MASTER"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of the Apex Sovereign Beast Tamer at the pinnacle of his power, serene invincible posture, "
                "glowing golden-and-crimson pupils reflecting eternal respawn matrices, wearing midnight-black sovereign handler armor with golden trim. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set atop a high fortress battlement overlooking a vast secured territory, "
                "revealing an unstoppable army of immortal mutated beasts roaring in triumph under a breathtaking sunset aurora sky in the distance. "
                "Illumination from rich golden sunset rays, radiant crimson respawn embers, and cyan starlight, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
