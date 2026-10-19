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
    "novel_slug": "game-descends-from-vampire-bat-to-loli-tyrant",
    "start_url": "https://mtl-novel.com/novel/game-descends-from-vampire-bat-to-loli-tyrant/chapter-151-an-extra-egg/",
    "start_chapter": 151,
    "end_chapter": 200,
    "default_topic": "Vampire Bat Tyrant",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_vampire_bat_tyrant_151_200",
    "final_audio": "output_vampire_bat_tyrant_151_200.mp3",
    "final_video": "final_vampire_bat_tyrant_151_200.mp4",
    "cover_image": "cover_vampire_bat_tyrant_151_200.jpg",
    "timestamps_file": "youtube_timestamps_vampire_bat_tyrant_151_200.txt",
    "subtitles_file": "subtitles_vampire_bat_tyrant_151_200.srt",
    "payload_file": "youtube_upload_payload_vampire_bat_tyrant_151_200.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "MYTHIC BLOODLINE AWAKENING! FROM VAMPIRE BAT TO BLOOD TYRANT SOVEREIGN [Ch 151-200] | Monster Evolution Progression Marathon",
    "tags": [
        "Game Descends From Vampire Bat to Loli Tyrant", "Vampire Bat Tyrant", "Monster Evolution",
        "Progression Fantasy Audiobook", "LitRPG Audiobook", "Overpowered Monster", "Bloodline Ascension", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Reincarnated into a reality-merging game world as a humble, fragile vampire bat, our protagonist continues "
        "an unprecedented evolutionary ascent toward apex bloodline godhood!\n\n"
        "Stumbling upon an enigmatic, primordial beast egg and unlocking dormant draconic-vampiric heritage, "
        "every high-tier kill and blood essence harvest unlocks astronomical system rewards. While elite human player guilds "
        "and mutated dungeon lords treat subterranean territories as their playground, our blood tyrant commands lethal "
        "supersonic shrieks, crimson mist domains, and shadow-rending blood claws to hunt down all intruders.\n\n"
        "From deciphering ancient abyssal incubation chambers to obliterating regional raid parties with absolute bloodline pressure, "
        "witness the terrifying rise of an unstoppable dark sovereign!\n\n"
        "Welcome to Chapters 151 to 200 of 'Game Descends: From Vampire Bat to Loli Tyrant' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 151: The Mysterious Extra Egg: Unearthing Ancient Bloodline Incubation Secrets\n"
        "• Ch 157: Subterranean Cavern Purge: Devouring Elite Mutation Cores Overnight\n"
        "• Ch 163: Crimson Mist Domain: Trapping and Annihilating Invasive Player Guild Scouts\n"
        "• Ch 169: Bloodline Mutation Trigger: Unlocking Draconic Bat Flight & Spatial Agility\n"
        "• Ch 175: Ancient Grotto Relic Vault: Harvesting Primordial Shadow Marrow\n"
        "• Ch 182: Raid Boss Counter-Assault: Obliterating Human Champions with Supersonic Shockwaves\n"
        "• Ch 188: Hatching the Beast Companion: Soul Contract Synchronization\n"
        "• Ch 193: Expanding the Dark Territory: Constructing the Underworld Blood Throne\n"
        "• Ch 197: Decimating the Regional Alliance Fleet with Flawless Night Ambush Tactics\n"
        "• Ch 200: Blood Tyrant Monarch Ascension: Crowned Sovereign of the Subterranean Depths\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#VampireBatTyrant #MonsterEvolution #ProgressionFantasy #LitRPG #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Streamlined for Zero Generation Failures)
    "blocks": [
        {
            "index": 1, "range": (151, 155),
            "title": ["MYSTERIOUS EGG", "BLOODLINE INCUBATION"],
            "fallback_color": (30, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of the youthful vampire tyrant inspecting a glowing obsidian beast egg, curious sharp expression, "
                "crimson pupils reflecting swirling red runes, wearing dark gothic velvet attire with silver trim. "
                "Set inside a quiet limestone cave nest lit by bioluminescent moss, revealing translucent crimson mist curling along stone walls in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (156, 160),
            "title": ["CAVERN PURGE", "DEVOURING MUTATION CORES"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic 3D portrait of the tyrant holding an extracted glowing purple beast crystal, serene ruthless smirk, "
                "dark hair framing pale aristocratic features. Set in a deep underground chasm, "
                "revealing defeated crystalline cave beasts dissolving into gray ash in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (161, 165),
            "title": ["CRIMSON MIST", "DOMAIN EXPANSION"],
            "fallback_color": (40, 15, 20),
            "prompt": (
                "Cinematic 3D portrait of the tyrant raising an open hand surrounded by swirling blood-red mist, cold commanding gaze, "
                "fingers tipped with razor-sharp dark claws. Set at the mouth of an underground gorge, "
                "revealing invading armored scouts disoriented within dense crimson fog in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (166, 170),
            "title": ["DRACONIC WINGS", "BLOODLINE MUTATION"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of the tyrant flexing newly evolved draconic bat wings, confident fierce expression, "
                "glowing ruby eyes shining through the dark. Set on a high stone precipice overlooking an expansive subterranean cavern, "
                "revealing glowing stalactites lighting the cavern ceiling in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (171, 175),
            "title": ["GROTTO RELIC", "SHADOW MARROW HARVEST"],
            "fallback_color": (20, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of the tyrant examining an ancient carved stone chalice, watchful calculating gaze, "
                "wearing tailored dark leather traveling robes. Set inside a forgotten subterranean altar chamber, "
                "revealing crumbling gothic pillars and broken guardian statues in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (176, 180),
            "title": ["SUPERSONIC SCREECH", "RAID PARTY ROUT"],
            "fallback_color": (35, 20, 25),
            "prompt": (
                "Cinematic 3D portrait of the tyrant unleashing an invisible sonic shockwave, sharp aggressive jawline, "
                "eyes blazing with intense crimson power. Set across a shattered stone bridge over an abyss, "
                "revealing armored raid warriors covering their ears as their shields fracture in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (181, 185),
            "title": ["EGG HATCHING", "SOUL PACT HARMONY"],
            "fallback_color": (30, 25, 30),
            "prompt": (
                "Cinematic 3D portrait of the tyrant gently cradling a newly hatched dark reptilian beast, subtle affectionate smile, "
                "crimson eyes softened with companion warmth. Set inside a sheltered cavern sanctum lit by gentle crystals, "
                "revealing glowing eggshell fragments scattered on a soft moss bed in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (186, 190),
            "title": ["UNDERWORLD FORTRESS", "EXPANDING THE NEST"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic 3D portrait of the tyrant standing on the ramparts of a dark-stone underground citadel, calm proud aura, "
                "arms folded across a high-collared crimson mantle. Set overlooking a vast fortified cavern city, "
                "revealing loyal bat swarms and dark guardians patrolling perimeter towers in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (191, 195),
            "title": ["NIGHT AMBUSH", "ALLIANCE DESTRUCTION"],
            "fallback_color": (25, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of the tyrant diving forward with silent agility, cold decisive gaze, "
                "dark wings leaving trails of shadowy crimson light. Set along a rocky subterranean pass at midnight, "
                "revealing an invading alliance vanguard falling back in total panic in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (196, 200),
            "title": ["BLOOD TYRANT MONARCH", "UNDERWORLD APEX"],
            "fallback_color": (20, 15, 45),
            "prompt": (
                "Cinematic 3D portrait of the Blood Tyrant Monarch seated upon an obsidian-and-ruby throne, serene invincible posture, "
                "crimson pupils reflecting radiant status matrices, wearing imperial midnight-red sovereign robes. "
                "Set inside a grandiose gothic throne room overlooking a secured subterranean empire in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
