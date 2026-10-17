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
    "start_url": "https://freewebnovel.com/novel/beast-taming-my-beasts-grind-die-and-respawn/chapter-188",
    "start_chapter": 188,
    "end_chapter": 233,
    "default_topic": "Beast Taming Respawn",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_beast_grind_die_respawn_188_233",
    "final_audio": "output_beast_grind_die_respawn_188_233.mp3",
    "final_video": "final_beast_grind_die_respawn_188_233.mp4",
    "cover_image": "cover_beast_grind_die_respawn_188_233.jpg",
    "timestamps_file": "youtube_timestamps_beast_grind_die_respawn_188_233.txt",
    "subtitles_file": "subtitles_beast_grind_die_respawn_188_233.srt",
    "payload_file": "youtube_upload_payload_beast_grind_die_respawn_188_233.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "CALAMITY ABYSS RESPAWN LOOP! SUICIDAL BEAST BATTLES UNLOCK GODHOOD [Ch 188-233] | LitRPG Progression Marathon",
    "tags": [
        "Beast Taming", "My Beasts Grind Die and Respawn", "Progression Fantasy",
        "LitRPG Audiobook", "Infinite Respawn", "Monster Taming", "Overpowered MC", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Pushing deeper into the catastrophic Abyssal Rift sectors, our ruthless strategist pushes the "
        "infinite death-loop grinding system into unprecedented sovereign territory!\n\n"
        "While rival federation champions and supreme guild enforcers hoard divine shields and preserve their delicate pets, "
        "our protagonist commands his contracted creatures to throw themselves into lethal spatial disintegrations, toxic miasma lakes, "
        "and primordial beast calderas. Each catastrophic wipe permanently grants absolute damage immunities, mutates forbidden apex "
        "bloodlines, and yields astronomical stat multipliers straight from the respawn engine!\n\n"
        "Watch him shatter ancient federation power hierarchies, out-attrite apocalyptic calamity swarms, and deploy a terrifying army "
        "of undying mythic abominations that grow infinitely more lethal with every death!\n\n"
        "Welcome to Chapters 188 to 233 of 'Beast Taming: My Beasts Grind, Die, and Respawn' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 188: Abyssal Rift Descent: Deploying Tactical Wipe-Cycles in S-Rank Calamity Zones\n"
        "• Ch 193: Toxic Swarm Crucible: Forging Absolute Corrosive Miasma Immunity via Respawn\n"
        "• Ch 198: Federation Elite Showdown: Humiliating High-Tier Champions with Endless Beast Rush\n"
        "• Ch 203: Void Dragonkin Bloodline Awakening: Unlocking Spatial Rupture Claws\n"
        "• Ch 208: Calamity Core Meltdown: Sacrificing Beast Squads to Overload Planetary Trial Wards\n"
        "• Ch 213: The High Council Inquest: Cold Indifference in Front of Arrogant Federation Elders\n"
        "• Ch 218: Cataclysmic Monster Tide Defense: Holding the Line with Self-Destructing Defenders\n"
        "• Ch 223: Primordial Origin Vault Infiltration: Harvesting Divine Beast Relics in Deep Ruin Layers\n"
        "• Ch 227: Awakening the Undying Titan Sovereign: Infinite Regeneration Matrix Synchronized\n"
        "• Ch 233: Apex Undying Hegemony: The Unrivaled Master of the Rebirth Law\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#BeastTaming #MyBeastsGrindDieAndRespawn #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (188, 192),
            "title": ["ABYSSAL THRESHOLD", "TACTICAL WIPE GRIND"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of a young calculating beast tamer, razor-sharp jawline, cold analytical dark eyes reflecting flashing red error codes, "
                "wearing modular carbon-weave combat armor with tactical shoulder pauldrons. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set at the edge of an abyssal rift chasm crackling with violet lightning, revealing floating system death-counter panels "
                "and respawn cooldown matrices hovering in the distance. Illumination from deep-violet spatial rifts and luminous cyan system logs, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (193, 197),
            "title": ["CORROSIVE CRUCIBLE", "MIASMA IMMUNITY FORGED"],
            "fallback_color": (20, 30, 20),
            "prompt": (
                "Cinematic 3D portrait of the tamer mid-communion, composed confident smirk, adjusting a sleek tactical wrist gauntlet. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a subterranean cavern filled with bubbling toxic emerald pools, "
                "revealing an armored beast reforming from brilliant golden rebirth particles while shrugging off melting acid vapor in the distance. "
                "Illumination from neon-green bioluminescent miasma and radiant golden resurrection halos, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (198, 202),
            "title": ["FEDERATION CLASH", "SUICIDAL BEAST SWARM"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of the tamer standing with nonchalant posture, hands buried in tactical cargo pockets, observant mocking glint in his gaze. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set in a shattered stone fortress courtyard, "
                "revealing arrogant federation combatants falling back in absolute panic as his continuously reviving beasts overwhelm their defensive lines in the distance. "
                "Illumination from flashing blue forcefield sparks and golden kinetic explosion flares, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (203, 207),
            "title": ["VOID DRAGONKIN", "SPATIAL CLAW AWAKENING"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the tamer tracking energy spikes, intense focused expression, fingers tracing glowing spatial distortion threads. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a crystalline warp fissure chamber, "
                "revealing a newly evolved draconic beast wreathed in dimensional shadows and razor-thin rift blades roaring silently in the distance. "
                "Illumination from deep amethyst spatial energy and shimmering silver planar cracks, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (208, 212),
            "title": ["CALAMITY CORE", "SACRIFICE OVERLOAD"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of the tamer commanding a massive structural overload, fierce resolute glare, outstretched hand directing synchronized death loops. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set at the burning pedestal of a massive ancient reactor core, "
                "revealing waves of beast vanguard entities self-detonating to shatter ancient protective runes in the distance. "
                "Illumination from blinding white-hot plasma flares and roaring crimson flame bursts, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (213, 217),
            "title": ["COUNCIL INQUEST", "UNSHAKABLE DEFIANCE"],
            "fallback_color": (25, 25, 35),
            "prompt": (
                "Cinematic 3D portrait of the tamer standing in quiet mockery, composed dignified stance, arms folded across his dark tactical mantle. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside an opulent high-tech federation inquiry chamber, "
                "revealing haughty council elders glaring down from tiered floating benches while struggling to mask their rising fear in the distance. "
                "Illumination from cool overhead architectural lights and glowing holographic tribunal seals, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (218, 222),
            "title": ["MONSTER TIDE", "ENDLESS DEFENSIVE WALL"],
            "fallback_color": (30, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of the tamer surveying battlefield carnage, sharp calculating gaze, wind whipping dark strands across his forehead. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set upon the high battlements of an outpost under midnight siege, "
                "revealing a vast horde of wild calamity beasts crashing into an undying vanguard of repeatedly resurrecting defenders in the distance. "
                "Illumination from pale silver moonlight, flaming artillery strikes, and radiant golden respawn beacons, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (223, 226),
            "title": ["ORIGIN VAULT", "ANCIENT RELIC EXTRACTION"],
            "fallback_color": (20, 30, 40),
            "prompt": (
                "Cinematic 3D portrait of the tamer examining an ancient glowing mechanical beast core, serene academic focus, fingertips brushing weathered runic engravings. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a subterranean vault of forgotten technological relics, "
                "revealing massive slumbering titan skeletons and glowing blue conduits threading through stone walls in the distance. "
                "Illumination from soft cyan coolant tubes and amber relic glyphs, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (227, 230),
            "title": ["TITAN SOVEREIGN", "IMMORTAL REGENERATION"],
            "fallback_color": (35, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the tamer conducting an ultimate synchronization ritual, dual-glowing golden and purple pupils, commanding authoritative aura. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set in a grand floating altar chamber, "
                "revealing a colossal Undying Titan Beast encased in impenetrable adamantine armor taking form from endless golden soul loops in the distance. "
                "Illumination from blinding golden resurrection matrices and crackling violet divine sparks, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (231, 233),
            "title": ["DEATH CYCLE HEGEMONY", "APEX RESPAWN MASTER"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of the Apex Sovereign Tamer standing at the absolute summit of the conquered territory, serene invincible posture, "
                "eyes blazing with divine gold-crimson respawn runes, wearing sleek midnight-black commander robes trimmed with golden filigree. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set atop a soaring fortress observation tower overlooking a vast rebuilt civilization, "
                "revealing an invincible legion of immortal mutated beasts standing proud under an awe-inspiring sunset aurora sky in the distance. "
                "Illumination from rich golden sunset rays, crimson resurrection embers, and brilliant starlight nebulas, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
