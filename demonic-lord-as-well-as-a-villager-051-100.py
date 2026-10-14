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
    "novel_slug": "reincarnated-in-the-alternate-world-im-a-demonic-lord-as-well-as-a-villager",
    "start_url": "https://freewebnovel.com/novel/reincarnated-in-the-alternate-world-im-a-demonic-lord-as-well-as-a-villager/chapter-51",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "Demonic Villager",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_demonic_lord_villager_051_100",
    "final_audio": "output_demonic_lord_villager_051_100.mp3",
    "final_video": "final_demonic_lord_villager_051_100.mp4",
    "cover_image": "cover_demonic_lord_villager_051_100.jpg",
    "timestamps_file": "youtube_timestamps_demonic_lord_villager_051_100.txt",
    "subtitles_file": "subtitles_demonic_lord_villager_051_100.srt",
    "payload_file": "youtube_upload_payload_demonic_lord_villager_051_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "SECRET DEMON KING LIVING AS A NOOB VILLAGER! HEROES COMPLETELY CLUELESS [Ch 51-100] | JRPG Fantasy Comedy Audiobook Marathon",
    "tags": [
        "Reincarnated in the Alternate World", "I'm a Demonic Lord as Well as a Villager", "Xia Mi",
        "Demon King", "JRPG Parody", "Overpowered MC", "Comedy Fantasy", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Reincarnated into a classic JRPG world as harmless Villager A in Newbie Village, Xia Mi's dream of a peaceful, "
        "modest life was completely derailed when the system dumped the [Successor to the Demon King] mantle onto his lap!\n\n"
        "By day, he is the mild-mannered, handsome local youth sipping wheat beer at the tavern and nodding politely to passing adventurer parties. "
        "By night, he commands subterranean demon strongholds, recruits quirky monster generals, manages unruly succubi and dragonkin subordinates, "
        "and consolidates world-ending dark mana—all while desperately dodging the kingdom's elite mages and clueless hero factions!\n\n"
        "Watch Xia Mi maneuver absurd dual-identity misunderstandings, dismantle arrogant kingdom inquisitors from the shadows, "
        "and build the most overpowered demon realm right under the Hero Association's nose!\n\n"
        "Welcome to Chapters 51 to 100 of 'Reincarnated in the Alternate World: I'm a Demonic Lord as Well as a Villager' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 51: Tavern Rumors & Feigning Ignorance in Front of High-Tier Holy Knights\n"
        "• Ch 56: Subterranean Throne Expansion: Managing the Dragon Maiden's Clumsy Ambitions\n"
        "• Ch 62: The Fake Quest Trap: Guiding Overconfident Adventurers into Harmless Illusions\n"
        "• Ch 68: Black Market Magic Infiltration & Purchasing Forbidden Ancient Grimoires\n"
        "• Ch 74: Demon General Performance Reviews: Disciplining Lazy Slime & Goblin Chiefs\n"
        "• Ch 80: The Hero Party Visits the Village: Xia Mi's Masterclass in Acting Like a Coward\n"
        "• Ch 86: Night Incursion: Crushing an Arrogant Inquisitor Squad with Dark Sovereign Mana\n"
        "• Ch 92: Territorial Tax Evasion: Out-Administrating the Corrupt Royal Tax Collectors\n"
        "• Ch 100: Absolute Shadow Hegemony: Sovereign Ruler of the Shadows & Peaceful Villager Forever\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#DemonicLordVillager #XiaMi #DemonKing #JRPGParody #FantasyAudiobook #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (51, 55),
            "title": ["NEWBIE VILLAGE TAVERN", "THE DUAL IDENTITY"],
            "fallback_color": (30, 20, 25),
            "prompt": (
                "Cinematic 3D portrait of young protagonist Xia Mi, gentle handsome East Asian facial features, neat short black hair, "
                "calm dark eyes carrying a hidden sharp glint, wearing an unassuming beige linen villager shirt. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a bustling rustic wooden village tavern, "
                "revealing a wooden mug of golden foaming beer on the table and loud, armored fantasy adventurers boasting in the distance. "
                "Illumination from warm amber tavern lantern light and a faint, translucent crimson status panel visible only to him, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (56, 60),
            "title": ["SUBTERRANEAN THRONE", "DRAGON MAIDEN AUDIENCE"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of Xia Mi transitioning into his Demonic Sovereign persona, composed commanding smirk, "
                "eyes glowing with sinister dark-violet magical energy, wearing an obsidian-black high-collared mantle trimmed with silver demon runes. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a grand gothic subterranean cavern palace, "
                "revealing a clumsy, proud horned dragon maiden kneeling in respectful report in the distance. "
                "Illumination from floating purple soul orbs and flickering torch sconces, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (61, 65),
            "title": ["ILLUSORY TRIAL", "ADVENTURER MISDIRECTION"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of Xia Mi holding an antique bronze magical compass, amused calculating expression, dark bangs swaying slightly. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set along a foggy forest crossroad outside the village, "
                "revealing a confused heroic adventuring party wandering hopelessly inside a harmless mirror labyrinth illusion in the distance. "
                "Illumination from pale silver moonlight and delicate cyan runic threads floating at his fingertips, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (66, 70),
            "title": ["SHADOW BAZAAR", "FORBIDDEN SCROLL PROCUREMENT"],
            "fallback_color": (35, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of Xia Mi disguised in a hooded midnight-blue cloak, sharp analytical gaze, examining an ancient parchment grimoire "
                "radiating faint necrotic script. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside a clandestine black-market trading alcove beneath the royal capital, revealing masked demon merchants and caged magical beasts in the distance. "
                "Illumination from glowing amethyst crystal globes cutting through thick atmospheric smoke, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (71, 75),
            "title": ["MONSTER MANAGEMENT", "DEMON GENERAL REVIEW"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of Xia Mi pinching the bridge of his nose in exasperated comedic amusement, sharp jawline, handsome weary expression, "
                "holding a stack of messy dungeon expenditure reports. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set in the demon fortress war room, revealing nervous goblin chieftains and a sheepish succubus maid looking guilty behind a giant stone table in the distance. "
                "Illumination from warm red hearth flames reflecting off polished obsidian floors, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (76, 80),
            "title": ["HERO ENCOUNTER", "PERFECT VILLAGER ACTING"],
            "fallback_color": (25, 30, 25),
            "prompt": (
                "Cinematic 3D portrait of Xia Mi bowing with an innocent, naive smile, hands rubbing together like a timid rural commoner, "
                "wearing a patchworked brown vest and rolled-up sleeves. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set at the entrance of Newbie Village, revealing an arrogant golden-armored Chosen Hero strutting past him without suspecting a thing in the distance. "
                "Illumination from bright sunny afternoon daylight and dusty village road reflections, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (81, 85),
            "title": ["MIDNIGHT PURGE", "INQUISITOR CRUSHED"],
            "fallback_color": (20, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of Xia Mi fully releasing his Demon King aura, terrifying cold gaze, dark hair trailing crimson sparks, "
                "outstretched hand condensing a catastrophic sphere of black gravitational mana. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a ruined stone chapel in deep forest at midnight, revealing corrupt royal inquisitors pinned flat to the cobblestones by sheer aura pressure in the distance. "
                "Illumination from crackling deep-purple lightning and blinding white impact flares, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (86, 90),
            "title": ["BUREAUCRATIC SUBVERSION", "ROYAL TAX EVASION"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of Xia Mi stamping official village grain ledgers with a polite charming smirk, elegant long fingers, "
                "neat brown leather vest over a clean white shirt. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside the village head's rustic office, revealing baffled royal tax inspectors scratching their heads over flawless, zero-profit financial books in the distance. "
                "Illumination from sunny morning window rays and swirling paper dust motes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (91, 95),
            "title": ["DOMINION SYNCHRONIZATION", "DEMON KING AWAKENING"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of Xia Mi commanding multiple dark leyline arrays, regal dominant posture, glowing dual crimson-and-gold pupils, "
                "wearing an imperial midnight mantle with draconic shoulder pauldrons. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set high above the subterranean core caldera, revealing towering demon generals and legions of loyal monster legions kneeling in unison in the distance. "
                "Illumination from roaring subterranean magma rivers and radiant violet demon seal matrices, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (96, 100),
            "title": ["SOVEREIGN OF SHADOWS", "PEACEFUL VILLAGER A"],
            "fallback_color": (20, 25, 30),
            "prompt": (
                "Cinematic 3D portrait of Xia Mi sitting casually on a rustic wooden village fence, relaxed contented smile, dark hair ruffled by a warm countryside breeze, "
                "holding a fresh green apple while half of his shadow stretches behind him as a colossal winged Demon King silhouette. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set overlooking idyllic rolling green pastures and thatched village cottages under an awe-inspiring sunset sky in the distance. "
                "Illumination from rich golden-hour sunset gradients and faint crimson shadow embers, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
