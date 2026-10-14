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
    "start_url": "https://freewebnovel.com/novel/beast-taming-my-beasts-grind-die-and-respawn/chapter-46",
    "start_chapter": 46,
    "end_chapter": 95,
    "default_topic": "Respawn Beast Tamer",

    # Concurrency Throttles (Updated throttles: batch_size 10 & parallel_chapters 3)
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_beast_taming_respawn_046_095",
    "final_audio": "output_beast_taming_respawn_046_095.mp3",
    "final_video": "final_beast_taming_respawn_046_095.mp4",
    "cover_image": "cover_beast_taming_respawn_046_095.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_respawn_046_095.txt",
    "subtitles_file": "subtitles_beast_taming_respawn_046_095.srt",
    "payload_file": "youtube_upload_payload_beast_taming_respawn_046_095.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "IMMORTAL UNDEAD MONARCH ASCENSION! MILLION-DEATH BLOODLINE EVOLUTION [Ch 46-95] | LitRPG Beast Taming Marathon",
    "tags": [
        "LitRPG Audiobook", "Beast Taming", "My Beasts Grind Die and Respawn", "Lu Yu",
        "SSS Awakening", "Progression Fantasy", "Familiar Evolution", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Entering the national-level trial rifts, the immortal army steps onto the grand stage!\n\n"
        "Having dominated rookie leagues, Lu Yu pushes his SSS-tier Infinite Grind & Respawn System into high-risk catastrophe zones. "
        "While elite aristocratic tamers guard their platinum-rank beasts with defensive treasures, Lu Yu's familiars throw themselves "
        "into ancient forbidden death dungeons—grinding through millions of automated lethal cycles overnight.\n\n"
        "With each fatal strike suffered, his Nether Bone King absorbs ancient sovereign laws, the Shadow Crow condenses the Abyssal Void Horizon, "
        "and a mysterious third mythological familiar awakens from primordial chaos. Watch Lu Yu shatter the expectations of provincial guilds, "
        "command unstoppable respawning legions, and carve an immortal path to sovereign authority!\n\n"
        "Welcome to Chapters 46 to 95 of 'SSS Awakening: Beast Taming: My Beasts Grind, Die, and Respawn' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 46: Stepping onto the Provincial Arena & The Secret Forbidden Rift Invitation\n"
        "• Ch 52: Automated Nether Crucible: 100,000 Deaths Unlocking the Bone Monarch Domain\n"
        "• Ch 58: Crushing National Academy Elites with Inexhaustible Undead Momentum\n"
        "• Ch 64: Deep Abyss Expedition & Slaying the Corrupted Void Behemoth\n"
        "• Ch 70: Contracting the Third Familiar: The Primordial Chaos World-Eater\n"
        "• Ch 76: Elite Guild Assassination Ambush Dismantled by Infinite Suicide Counters\n"
        "• Ch 82: The Sovereign Trial Tower: Conquering the 50th Floor Calamity\n"
        "• Ch 88: Nether Dragon Bloodline Resonance & Sky-Splitting Undead Roar\n"
        "• Ch 95: Provincial Sovereign Coronation & The Fearless March to Continental Supremacy\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#BeastTaming #InfiniteRespawn #LuYu #SSSAwakening #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (46, 50),
            "title": ["PROVINCIAL SUMMIT", "IMMORTAL REPUTATION"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of young beast master Lu Yu, sharp chiselled jawline, short neat black hair, "
                "eyes glowing with radiant cyan-gold soul energy, wearing tailored dark-charcoal tamer robes over tactical silver under-armor. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set at the panoramic observation deck of an elite provincial guild skyscraper, "
                "revealing hovering transport shuttles and colossal arena banners fluttering against modern city skyline clouds in the distance. "
                "Illumination from neon-cyan soul matrices and warm amber city lights, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (51, 55),
            "title": ["NETHER CRUCIBLE", "HUNDRED THOUSAND DEATHS"],
            "fallback_color": (30, 15, 45),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu executing sub-dimensional commands, cold calculating smirk, dark windswept hair, "
                "surrounded by floating violet system status panels showing rapid death counters. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set before a swirling dimensional rift leading into an apocalyptic lava wasteland, revealing his Nether Bone King familiar "
                "surging endlessly from pillars of golden resurrection light into demonic hordes in the distance. "
                "Illumination from blazing golden respawn flares and eerie deep-purple spatial rifts, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (56, 60),
            "title": ["PROVINCIAL RING", "NATIONAL ELITE SHOCKED"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu in tournament combat, hands relaxed at his sides, calm dominant gaze, "
                "faint emerald soul fire flickering in his irises. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a massive domed colosseum arena packed with cheering spectators, revealing an arrogant elite scion's "
                "diamond-tier armored beast hurled into the arena wall by the terrifying physical force of Lu Yu's evolved skeleton in the distance. "
                "Illumination from blinding stadium arc lights and crackling cyan shockwave arcs across the sand, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (61, 65),
            "title": ["VOID BEHEMOTH", "RELENTLESS ATTRITION"],
            "fallback_color": (15, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of a battle-hardened Lu Yu, light combat soot on his cheekbones, razor-sharp focused eyes, "
                "wearing a high-tier reinforced monster hunter mantle. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a shadowy subterranean abyss, revealing an immense multi-eyed Void Behemoth collapsing in defeat "
                "beneath the endless synchronized assaults of Lu Yu's undying familiars in the distance. "
                "Illumination from glowing green abyssal moss and shimmering golden soul essence dissipation, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (66, 70),
            "title": ["THIRD COVENANT", "CHAOS WORLD-EATER"],
            "fallback_color": (35, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu establishing a primordial contract, calm regal expression, dark hair floating in zero gravity, "
                "extending a hand marked with an intricate tri-elemental contract seal. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set atop an ancient ruined stone altar adrift in the void, revealing a newly hatched primordial chaos serpent "
                "wreathed in cosmic stardust coiling reverently around his arm in the distance. "
                "Illumination from radiant violet divine runes and sparkling celestial nebula light, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (71, 75),
            "title": ["SHADOW AMBUSH", "SUICIDE COUNTER-STRIKE"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu calmly predicting an enemy ambush, ruthless tactical stare, sharp jawline, "
                "bloodied combat gauntlets clenched in cold confidence. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in a shattered mountain ravine at twilight, revealing masked guild assassins fleeing in panic as Lu Yu's familiars "
                "detonate consecutive self-destruct bone novas only to respawn instantly behind their lines in the distance. "
                "Illumination from fiery orange impact explosions and blinding green soul flame bursts, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (76, 80),
            "title": ["SOVEREIGN TOWER", "50TH FLOOR DOMINION"],
            "fallback_color": (25, 25, 50),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu challenging the pinnacle of the trial tower, windswept dark hair, piercing sun-gold pupils, "
                "wearing an imperial midnight-black longcoat over silver chest plate. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on the crystalline high platform of the 50th floor overlooking endless clouds, revealing a colossal divine guardian "
                "kneeling in defeat as ancient runic tower seals unlock overhead in the distance. "
                "Illumination from blinding white-gold tower energy pillars and cool blue starlight arrays, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (81, 85),
            "title": ["NETHER DRAGON", "BONE KING HARMONY"],
            "fallback_color": (20, 35, 45),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu commanding evolved draconic authority, majestic composed expression, "
                "hands surrounded by swirling glacial frost and necrotic lightning. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set across an icy mountain canyon, revealing his Nether Bone King manifested as a colossal skeletal frost dragon "
                "unleashing a sky-shattering breath beam of pure absolute zero in the distance. "
                "Illumination from blinding cyan glacial light beams and crystalline diamond dust reflections, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (86, 90),
            "title": ["ABYSSAL CROW", "VOID HORIZON STORM"],
            "fallback_color": (30, 15, 40),
            "prompt": (
                "Cinematic 3D portrait of Lu Yu orchestrating aerial devastation, razor-sharp jawline, dark amethyst irises, "
                "billowing dark commander mantle whipping in supersonic wind. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in storm-swept skies above a dimensional breach, revealing his Nether Shadow Crow transformed into an immense "
                "abyssal phoenix casting an eclipse of pure shadow across the battlefield in the distance. "
                "Illumination from swirling violet eclipse rings and crackling dark-lightning arcs, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (91, 95),
            "title": ["PROVINCIAL SOVEREIGN", "IMMORTAL LEGION"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Sovereign Tamer Lu Yu standing at the pinnacle of provincial dominion, calm invincible aura, sun-gold pupils, "
                "wearing the ornate gold-embroidered Grand Sovereign Mantle over dark battle plate. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on the grand imperial balcony overlooking thousands of cheering guild masters and vast city towers, "
                "revealing his trio of evolved mythic familiars standing majestically in divine formation under a breathtaking twilight aurora sky. "
                "Illumination from brilliant auroras of sunrise gold, glowing emerald respawn motes, and radiant cyan soul fire, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
