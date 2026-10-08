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
    # Credentials
    "gemini_api_key": creds.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", ""),
    "cf_account_id": creds.get("cloudflare_account_id") or os.environ.get("CLOUDFLARE_ACCOUNT_ID", ""),
    "cf_api_token": creds.get("cloudflare_api_token") or os.environ.get("CLOUDFLARE_API_TOKEN", ""),

    # Novel & Episode Parameters
    "novel_slug": "everyones-a-monster-but-im-the-only-player",
    "start_url": "https://mtl-novel.com/novel/everyones-a-monster-but-im-the-only-player/chapter-1-highway/",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Apocalypse",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 2,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_everyone_monster_001_050",
    "final_audio": "output_everyone_monster_001_050.mp3",
    "final_video": "final_everyone_monster_001_050.mp4",
    "cover_image": "cover_everyone_monster_001_050.jpg",
    "timestamps_file": "youtube_timestamps_everyone_monster_001_050.txt",
    "subtitles_file": "subtitles_everyone_monster_001_050.srt",
    "payload_file": "youtube_upload_payload_everyone_monster_001_050.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "EVERYONE'S A MONSTER, BUT I'M THE ONLY PLAYER! [Ch 1-50] | LitRPG Audiobook Marathon",
    "tags": [
        "LitRPG Audiobook", "Everyone's a Monster But I'm the Only Player", "Monster Evolution",
        "System Apocalypse", "Highway Survival", "Progression Fantasy", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "The global apocalypse descends and everyone transforms into terrifying mutated monsters—except one!\n\n"
        "Waking up on an infinite death highway overrun by ravenous beast hordes and grotesque mutated predators, "
        "Lin Ye realizes he is the sole remaining human endowed with the exclusive Player System interface. "
        "While mutant overlords hunt each other for biological evolution, Lin Ye levels up, unlocks cheat-grade "
        "class skills, and slays nightmare behemoths like dungeon mobs!\n\n"
        "Welcome to Chapters 1 to 50 of 'Everyone’s a Monster, But I’m the Only Player!' "
        "in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 01: Descent onto the Highway & The Only Player Interface Awakening\n"
        "• Ch 10: First Blood Kill & Unlocking the Kill-Reward Experience Matrix\n"
        "• Ch 20: Highway Ambush by Mutated Raider Packs & Absolute Domination\n"
        "• Ch 30: Breaking the Abyssal Tollbooth & Securing the Safe-Zone Outpost\n"
        "• Ch 40: Subjugating the Chitin Brood Mother & Weaponizing Bug Swarms\n"
        "• Ch 50: Sovereign Player Ascendance & The Apocalypse Realm Ruler\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#LitRPG #MonsterEvolution #SystemApocalypse #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (1, 5),
            "title": ["HIGHWAY DESCENT", "THE ONLY PLAYER"],
            "fallback_color": (15, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of a determined young male player, jet-black hair, sharp amber-gold eyes, "
                "wearing reinforced tactical carbon-fiber armor with glowing cyan system lines. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against an endless fractured apocalyptic highway under a stormy violet twilight sky, revealing grotesque mutated "
                "shadow behemoths prowling the ruined asphalt in the distance. Illumination from floating holographic blue HUD grids and warm amber road flare sparks, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (6, 10),
            "title": ["FIRST BLOOD KILL", "EXPERIENCE HARVEST"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of a young male player, dark windswept hair, fierce glowing golden eyes, "
                "wearing sleek titanium-trimmed combat gear. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against a smoke-choked highway junction, revealing a defeated armored chitin beast dissolving into shimmering golden "
                "experience particles in the distance. Illumination from neon-magenta leveling matrices and blazing amber headlights, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (11, 15),
            "title": ["MUTATED HIGHWAY", "HIGH-SPEED PURSUIT"],
            "fallback_color": (30, 20, 20),
            "prompt": (
                "Cinematic 3D portrait of a male hero commander, intense dark hair, sharp amber-gold eyes, "
                "wearing heavy tactical leather and dark metal pauldrons. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against a desolate multi-lane expressway, revealing aggressive mutated spiked wolves chasing reinforced combat vehicles "
                "in the distance. Illumination from piercing turquoise searchlights and volcanic-orange exhaust flames, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (16, 20),
            "title": ["ELITE BEAST TIDE", "TALENT AWAKENING"],
            "fallback_color": (20, 35, 45),
            "prompt": (
                "Cinematic 3D portrait of a handsome male anime player, short black hair, luminous golden-amber eyes, "
                "wearing sleek dark obsidian breastplate armor. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against a stormy mountain highway pass, revealing a colossal horned chimera monster roaring atop a bridge in the distance. "
                "Illumination from crackling cyan plasma arcs and deep magenta lightning bolts splitting the midnight sky, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (21, 25),
            "title": ["ABYSSAL TOLLBOOTH", "SAFE ZONE OUTPOST"],
            "fallback_color": (15, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of a commanding young male player, refined black hair, calm amber eyes, "
                "wearing ornate silver-and-black tactical battle attire. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against an abandoned colossal steel highway toll plaza fortified with glowing barrier shields, revealing mutant hordes "
                "repelled outside the gate in the distance. Illumination from warm golden barrier runes and cool sapphire perimeter spotlights, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (26, 30),
            "title": ["CHITIN BROOD PURGE", "APEX PREDATOR"],
            "fallback_color": (40, 20, 25),
            "prompt": (
                "Cinematic 3D portrait of a battle-tested male player, dark hair, brilliant amber eyes, "
                "wearing dark brass-trimmed combat armor with runic carvings. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against an overgrown concrete cloverleaf interchange, revealing giant armored insectoid mantis beasts "
                "scattering under energy strikes in the distance. Illumination from brilliant emerald venom glands and crackling crimson kinetic sparks, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (31, 35),
            "title": ["DIMENSIONAL RIFT", "LEVEL-UP BURST"],
            "fallback_color": (25, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of a powerful young male player, dark hair, intense violet-amber eyes, "
                "wearing sleek high-tech alloy armor with pulsing energy conduits. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against a shattered highway overpass opening into a cosmic dimensional rift, revealing swirling nebulae "
                "of turquoise, gold, and violet celestial matter in the distance. Illumination from radiant concentric system rings, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (36, 40),
            "title": ["CALAMITY OVERLORD", "S-RANK STRIKE"],
            "fallback_color": (35, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of a dominant male player warrior, dark hair, brilliant golden eyes, "
                "wearing heavy dark chrome power armor with gold engravings. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against an expansive ruined metropolitan highway vista, revealing an ancient skyscraper-sized calamity behemoth "
                "struck by orbital laser columns in the distance. Illumination from blinding sun-yellow energy beams and deep crimson smoke plumes, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (41, 45),
            "title": ["WAR RIG FORTRESS", "RESOURCE CONQUEST"],
            "fallback_color": (25, 35, 40),
            "prompt": (
                "Cinematic 3D portrait of a young male player sovereign, neat black hair, glowing amber-gold eyes, "
                "wearing tailored midnight-blue reinforced combat robes. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against a heavily upgraded armored mobile war rig citadel rolling down the highway, revealing mounted energy turrets "
                "and automated drone swarms hovering in the distance. Illumination from warm amber cabin lanterns and neon-green telemetry holographic projections, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (46, 50),
            "title": ["SOVEREIGN PLAYER", "RULER OF THE APOCALYPSE"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of Player Lin Ye, refined dark hair, majestic amber-gold eyes, "
                "wearing ornate imperial black-and-gold sovereign power robes. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on an expansive command watchtower overlooking a liberated fortified highway empire stretching toward dawn in the distance. "
                "Illumination from brilliant auroras of neon green, deep violet, and warm sunrise amber mana dancing across the horizon, "
                "deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
