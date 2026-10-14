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

    # Novel & Episode Parameters (45 chapters to keep runtime comfortably under 12 hours)
    "novel_slug": "beast-taming-my-beasts-grind-die-and-respawn",
    "start_url": "https://freewebnovel.com/novel/beast-taming-my-beasts-grind-die-and-respawn/chapter-1",
    "start_chapter": 1,
    "end_chapter": 45,
    "default_topic": "Respawn Beast Tamer",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,  # Sequential processing to respect 15 RPM limits cleanly
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_beast_taming_respawn_001_045",
    "final_audio": "output_beast_taming_respawn_001_045.mp3",
    "final_video": "final_beast_taming_respawn_001_045.mp4",
    "cover_image": "cover_beast_taming_respawn_001_045.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_respawn_001_045.txt",
    "subtitles_file": "subtitles_beast_taming_respawn_001_045.srt",
    "payload_file": "youtube_upload_payload_beast_taming_respawn_001_045.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "MY BEASTS CANNOT DIE! SSS INFINITE RESPAWN SYSTEM [Ch 1-45] | LitRPG Beast Taming Audiobook Marathon",
    "tags": [
        "LitRPG Audiobook", "Beast Taming", "My Beasts Grind Die and Respawn", "Lu Yu",
        "SSS Awakening", "Progression Fantasy", "Familiar Evolution", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "In a modern beast-taming world where beast deaths mean permanent soul damage and financial ruin, "
        "every tamer treats their contracted familiars like delicate glass treasures.\n\n"
        "Lu Yu awakens an unprecedented SSS-tier anomaly: The Infinite Grind & Respawn System! "
        "His beasts can enter automated parallel trial dimensions, grind 24/7 without rest, die without penalty, "
        "and immediately respawn stronger—stacking permanent attribute multipliers and awakening mythic bloodlines with every single death!\n\n"
        "While other tamers pamper their pets with expensive potions, Lu Yu commands his little skeleton and starter beasts "
        "to charge fearlessly into suicide rifts. Watch his familiars die ten thousand times only to resurrect as terrifying "
        "undead titan overlords, immortal phoenixes, and abyssal monarchs that shock the entire academy!\n\n"
        "Welcome to Chapters 1 to 45 of 'SSS Awakening: Beast Taming: My Beasts Grind, Die, and Respawn' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 01: Awakening the SSS Respawn Talent & Contracting the Weakest Skeleton\n"
        "• Ch 06: The First Death: Instant Resurrection & 10x Attribute Feedback\n"
        "• Ch 12: Automated Subspace Grinding: A Million Deaths in One Night\n"
        "• Ch 18: Academy Practical Combat Mock Exam & Terrifying the Evaluators\n"
        "• Ch 24: Crushing Arrogant Elite Scions with a Fearless Immortal Charge\n"
        "• Ch 30: Slaying Calamity Rift Bosses via Relentless Undead Attrition\n"
        "• Ch 35: Contracting the Second Familiar: Nether Shadow Crow Metamorphosis\n"
        "• Ch 40: Bone King Evolution: Manifesting the Nether Frost Dragon Armor\n"
        "• Ch 45: Top Rookie Sovereign Coronation & The Unstoppable Respawn Reign\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#BeastTaming #InfiniteRespawn #LuYu #SSSAwakening #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (1, 4),
            "title": ["AWAKENING CEREMONY", "SSS RESPAWN SYSTEM"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of young beast tamer Lu Yu, sharp determined facial features, short neat black hair, "
                "radiant glowing electric-cyan pupils, wearing a modern high-school beast tamer uniform with reinforced shoulder guards. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a grand high-tech awakening hall, "
                "revealing holographic appraisal terminals flashing crimson warning glyphs and a tiny, glowing white-boned skeleton familiar "
                "standing loyally beside his boots in the distance. "
                "Illumination from neon-cyan soul bond matrices and pale moonlight filtering through overhead arena skylights, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (5, 9),
            "title": ["FIRST RESURRECTION", "STAT MULTIPLIER"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu observing an impossible miracle, calm intrigued gaze, subtle knowing smile, "
                "surrounded by floating gold system stat windows. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside an abandoned underground training bunker, revealing his shattered skeleton familiar "
                "reassembling instantly from shimmering golden ash, its eye sockets bursting with intense emerald soul fire in the distance. "
                "Illumination from radiant golden respawn auras clashing with eerie green necromantic flames, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (10, 14),
            "title": ["AUTOMATED GRIND", "NIGHT OF TEN THOUSAND DEATHS"],
            "fallback_color": (15, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu resting peacefully in his bedroom, composed tranquil expression, dark hair, "
                "while an intricate glowing dimensional portal rotates gently beside his desk. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a dimly lit modern city apartment at midnight, revealing the open spatial rift displaying "
                "his skeleton familiar charging endlessly into infinite monster hordes within an alternate dimension in the distance. "
                "Illumination from pulsing deep-violet spatial fissures and cold neon-blue city lights through the window, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (15, 18),
            "title": ["ACADEMY EXAM", "EVALUATOR IN SHOCK"],
            "fallback_color": (25, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu standing calmly on the arena stage, hands casually in his jacket pockets, "
                "cold calculating amber-cyan eyes, relaxed composed demeanor. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a massive circular mock-combat stadium, revealing elderly academy evaluators standing up from their seats "
                "in total disbelief as Lu Yu's evolved dark-iron skeleton warrior cleaves an A-rank testing dummy in half with one stroke in the distance. "
                "Illumination from blinding stadium floodlights and crackling cyan shockwave arcs across the sand, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (19, 23),
            "title": ["SCION CONFRONTATION", "FEARLESS SUICIDE CHARGE"],
            "fallback_color": (35, 20, 25),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu commanding ruthless battlefield strategy, confident mocking smirk, windswept dark hair, "
                "radiant glowing violet runes encircling his wrists. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside an academy tournament ring, revealing an arrogant rival scion's luxurious armored storm lion "
                "recoiling in terror as Lu Yu's undead warrior ignores mortal wounds and detonates an undying bone explosion in the distance. "
                "Illumination from fiery orange impact detonations and blinding green soul flames, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (24, 28),
            "title": ["CALAMITY RIFT", "TITAN BOSS ATTRITION"],
            "fallback_color": (20, 35, 30),
            "prompt": (
                "Cinematic 3D portrait of a battle-hardened Lu Yu, dirt and frost across his sharp cheekbones, piercing predator gaze, "
                "wearing high-durability tactical monster hunter armor. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in a desolate dimensional rift crater under an overcast stormy sky, revealing a colossal mountain-sized "
                "calamity titan monster collapsing in exhaustion as Lu Yu's respawning beast army wears it down relentlessly in the distance. "
                "Illumination from eerie green rift lightning and shimmering golden soul essence dissipation, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (29, 32),
            "title": ["SECOND FAMILIAR", "NETHER SHADOW CROW"],
            "fallback_color": (30, 15, 40),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu sealing a new contractual covenant, dignified majestic expression, dark hair, "
                "holding an outstretched palm inscribed with a glowing obsidian contract seal. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a foggy ancient pet sanctuary, revealing a pitch-black Nether Shadow Crow with glowing amethyst eyes "
                "expanding wings of pure dark mist and alighting loyally upon his gauntlet in the distance. "
                "Illumination from swirling violet shadow flames and twinkling starlight particles, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (33, 37),
            "title": ["WILDERNESS SIEGE", "BEAST TIDE PURGE"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu executing frontline command, razor-sharp jawline, intense sun-gold and sapphire eyes, "
                "directing elemental shockwaves with decisive hand gestures. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set atop the high battlements of a border fortress city under siege, revealing thousands of invading wild beasts "
                "routed and dismantled by his dual familiars' coordinated bone and shadow storm in the distance. "
                "Illumination from exploding defensive artillery spells and radiant purple necrotic auroras, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (38, 41),
            "title": ["BONE KING METAMORPHOSIS", "FROST DRAGON ARMOR"],
            "fallback_color": (20, 30, 50),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu witnessing familiar transcendence, awe-inspiring commanding posture, dark windswept hair, "
                "eyes glowing with blinding glacial-blue radiance. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set atop a frozen peak within a deep subterranean abyss, revealing his primary skeleton familiar "
                "metamorphosing into a towering Nether Frost Bone King clad in colossal translucent dragon armor in the distance. "
                "Illumination from blinding cyan glacial light beams and swirling diamond dust shockwaves, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (42, 45),
            "title": ["ROOKIE SOVEREIGN", "IMMORTAL PANTHEON ASCENT"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Sovereign Tamer Lu Yu at the pinnacle of rookie dominance, calm majestic presence, sun-gold pupils, "
                "wearing tailored midnight-black sovereign tamer mantle over tactical silver armor. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on the championship podium overlooking a cheering metropolitan stadium of tens of thousands, "
                "revealing his towering evolved Nether Bone Dragon and abyssal shadow phoenix familiars flanking him under a breathtaking starlight sky. "
                "Illumination from brilliant auroras of sunrise gold, glowing emerald respawn motes, and radiant cyan frost fire, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
