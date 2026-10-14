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
    "start_url": "https://freewebnovel.com/novel/beast-taming-my-beasts-grind-die-and-respawn/chapter-96",
    "start_chapter": 96,
    "end_chapter": 141,
    "default_topic": "Respawn Beast Tamer",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_beast_taming_respawn_096_141",
    "final_audio": "output_beast_taming_respawn_096_141.mp3",
    "final_video": "final_beast_taming_respawn_096_141.mp4",
    "cover_image": "cover_beast_taming_respawn_096_141.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_respawn_096_141.txt",
    "subtitles_file": "subtitles_beast_taming_respawn_096_141.srt",
    "payload_file": "youtube_upload_payload_beast_taming_respawn_096_141.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "MYTHIC ANCIENT BEAST ASCENSION! CONTINENTAL SUPREMACY OVERHAUL [Ch 96-141] | LitRPG Beast Taming Marathon",
    "tags": [
        "LitRPG Audiobook", "Beast Taming", "My Beasts Grind Die and Respawn", "Lu Yu",
        "SSS Awakening", "Progression Fantasy", "Familiar Evolution", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Breaking past regional borders, the immortal beast army enters the grand Continental League!\n\n"
        "Having subjugated provincial trials, Lu Yu pushes his SSS-tier Infinite Grind & Respawn System into "
        "primordial catastrophe rifts and ancient subterranean battlegrounds. While continental conglomerates "
        "and ancient beast clans deploy saint-tier divine treasures to protect their bloodlines, Lu Yu orders his "
        "familiars into lethal automated suicide trials—dying millions of times across forbidden zones to force "
        "impossible mythic bloodline mutations!\n\n"
        "Watch his Nether Frost Bone Dragon manifest sovereign domain armor, his Nether Shadow Crow command abyssal event horizons, "
        "and his Primordial Chaos World-Eater devour calamity bosses whole. Witness Lu Yu crush continental prodigies, "
        "dismantle corrupt beast consortiums, and reign as the unrivaled Immortal Sovereign!\n\n"
        "Welcome to Chapters 96 to 141 of 'SSS Awakening: Beast Taming: My Beasts Grind, Die, and Respawn' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 96: Stepping into the Continental Capital: The Ancient Beast Sanctuary\n"
        "• Ch 101: 500,000 Automated Trial Deaths: Nether Bone Dragon Sovereign Evolution\n"
        "• Ch 105: Dismantling the Imperial Academy's Arrogant Saint-Tier Prodigies\n"
        "• Ch 110: Ancient Calamity Trench Expedition: Purging the Corrupted Abyssal Hydra\n"
        "• Ch 115: Void Crow Transcendence: Manifesting the Eternal Shadow Eclipse Domain\n"
        "• Ch 119: The Continental Beast Consortium Ambush Shattered by Infinite Respawn Waves\n"
        "• Ch 124: Primordial Chaos World-Eater Unlocks Planetary Gravitational Absorption\n"
        "• Ch 128: The 100th Floor Zenith Gate: Subjugating the Ancient Celestial Dragon Sovereign\n"
        "• Ch 133: Triple Familiar Mythic Fusion: Total Frontline Annihilation\n"
        "• Ch 141: Continental Grand Sovereign Coronation & The March to Interstellar Mastery\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#BeastTaming #InfiniteRespawn #LuYu #SSSAwakening #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (96, 100),
            "title": ["CONTINENTAL CAPITAL", "IMMORTAL TAMER ARRIVAL"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of young beast master Lu Yu, sharp chiselled jawline, short neat black hair, "
                "calm predatory eyes glowing with radiant electric-cyan soul energy, wearing an imperial midnight-blue tamer overcoat "
                "with gold-threaded sovereign crests. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set atop the open arrival plaza of the Continental Beast Capital, revealing colossal floating beast towers, "
                "hovering skyships, and shimmering barrier shields enclosing futuristic spire cities in the distance. "
                "Illumination from golden morning sunlight reflecting on polished crystalline pavement and cool cyan matrix lines, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (101, 104),
            "title": ["SOVEREIGN BONE DRAGON", "HALF-MILLION RESPAWNS"],
            "fallback_color": (15, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu orchestrating dimensional sub-trials, cold calculating gaze, dark hair trailing azure embers, "
                "surrounded by translucent violet system status windows overflowing with infinite respawn multipliers. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set before a massive subterranean void fissure, "
                "revealing his primary familiar evolved into a colossal Nether Frost Bone Dragon armored in iridescent glacial crystal plates "
                "unleashing a sky-shattering freezing roar in the distance. "
                "Illumination from blinding glacial-blue energy beams and radiant emerald soul fires, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (105, 109),
            "title": ["CONTINENTAL ARENA", "IMPERIAL PRODIGY CRUSHED"],
            "fallback_color": (30, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu standing undefeated in the arena center, hands casually in his pockets, confident mocking smirk, "
                "intense dual-ringed sapphire-and-gold pupils. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a grand orbital colosseum packed with hundreds of thousands of spectators, "
                "revealing an elite imperial scion's legendary golden chimera beast pinned flat into a shattered stone crater by heavy undead gravity in the distance. "
                "Illumination from blinding stadium arc lights and crackling violet shockwaves across the battle arena, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (110, 114),
            "title": ["ABYSSAL TRENCH", "CORRUPTED HYDRA PURGE"],
            "fallback_color": (15, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of a battle-tested Lu Yu, light combat soot across his cheekbones, razor-sharp focused eyes, "
                "wearing high-durability dragon-scale tactical battle plate. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set deep within a shadowy oceanic abyss trench, revealing a monstrous nine-headed corrupted calamity hydra "
                "collapsing in exhaustion under the relentless, endless respawning onslaught of Lu Yu's familiars in the distance. "
                "Illumination from bioluminescent deep-sea cyan corals and shimmering golden soul essence dissipation, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (115, 118),
            "title": ["VOID CROW ECLIPSE", "EVENT HORIZON DOMAIN"],
            "fallback_color": (25, 15, 40),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu directing aerial space manipulation, dignified commanding posture, dark hair whipped by kinetic winds, "
                "dark-amethyst runes revolving rapidly along his wrists. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in storm-swept skies above jagged volcanic peaks, revealing his Nether Shadow Crow transformed into "
                "a colossal abyssal harbinger blocking the sun and casting an impenetrable gravitational black-hole vortex across the land in the distance. "
                "Illumination from swirling deep-violet accretion rings and sharp white-lightning arcs, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (119, 123),
            "title": ["CONSORTIUM AMBUSH", "INFINITE REVERSE REIGN"],
            "fallback_color": (35, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu calmly predicting an assassination attempt, cold ruthless smirk, sharp jawline, "
                "outstretched gauntlet radiating dense green necromantic halos. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a ruined mountain fortress corridor at midnight, revealing elite cartel assassin squads "
                "reeling in absolute horror as Lu Yu's familiars self-detonate into catastrophic bone novas and respawn instantaneously behind their defenses in the distance. "
                "Illumination from fiery orange impact detonations and blinding green soul-flame flares, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (124, 127),
            "title": ["CHAOS WORLD-EATER", "GRAVITATIONAL COLLAPSE"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu releasing the third primordial beast, awe-inspiring dominant presence, windswept dark hair, "
                "golden irises gleaming with cosmic starlight. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set atop an asteroid impact crater in a dimensional border zone, revealing a titanic primordial chaos serpent "
                "wreathed in shifting nebula dust opening its colossal maw to swallow a falling meteorite whole in the distance. "
                "Illumination from glowing golden cosmic leylines and sparkling stardust clouds, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (128, 132),
            "title": ["ZENITH GATE", "CELESTIAL DRAGON DEFEATED"],
            "fallback_color": (25, 30, 50),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu breaching the highest trial pinnacle, calm majestic posture, silver-trimmed commander mantle "
                "draped over shoulders, eyes radiating piercing cyan light. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set upon the glowing crystalline floor of the 100th-floor Zenith Gate overlooking a sea of endless astral clouds, "
                "revealing an ancient golden Celestial Dragon Guardian bowing its massive horned head in unconditional submission in the distance. "
                "Illumination from radiant white-gold heavenly light pillars and crystalline blue floor reflections, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (133, 137),
            "title": ["MYTHIC TRINITY", "SYNCHRONIZED DESTRUCTION"],
            "fallback_color": (30, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu commanding total frontline dominion, razor-sharp jawline, intense sun-gold and sapphire eyes, "
                "hands raised as tri-elemental runic arrays swirl around his torso. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set overlooking an expansive battlefield overrun by millions of invading rift beasts, revealing his Nether Bone Dragon, "
                "Void Shadow Crow, and Chaos World-Eater unleashing a synchronized tri-beam apocalyptic blast wave in the distance. "
                "Illumination from blinding cyan frost, violet shadow lightning, and golden solar flames, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (138, 141),
            "title": ["CONTINENTAL SOVEREIGN", "UNRIVALED REIGN"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Grand Sovereign Lu Yu at the absolute apex of continental authority, calm majestic demeanor, sun-gold pupils, "
                "wearing the ornate imperial gold-and-obsidian Sovereign Mantle over polished platinum armor. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on the grand throne dais of the Continental Summit Spire overlooking vast metropolitan kingdoms beneath an awe-inspiring starlit sky, "
                "revealing his trio of towering mythic familiars standing proudly behind his throne in divine alignment in the distance. "
                "Illumination from brilliant auroras of sunrise gold, glowing emerald respawn motes, and radiant cyan soul fires, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
