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
    "novel_slug": "entry-cultivation-i-can-copy-entries",
    "start_url": "https://mtl-novel.com/novel/entry-cultivation-i-can-copy-entries/chapter-151-world-destroying-black-lotus-braving-the-great-dao-heaven-reaching-tower/",
    "start_chapter": 151,
    "end_chapter": 200,
    "default_topic": "Entry Cultivation",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_entry_cultivation_151_200",
    "final_audio": "output_entry_cultivation_151_200.mp3",
    "final_video": "final_entry_cultivation_151_200.mp4",
    "cover_image": "cover_entry_cultivation_151_200.jpg",
    "timestamps_file": "youtube_timestamps_entry_cultivation_151_200.txt",
    "subtitles_file": "subtitles_entry_cultivation_151_200.srt",
    "payload_file": "youtube_upload_payload_entry_cultivation_151_200.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "WORLD-DESTROYING BLACK LOTUS! BRAVING THE HEAVEN-REACHING TOWER [Ch 151-200] | Xianxia Progression Audiobook Marathon",
    "tags": [
        "Entry Cultivation", "I Can Copy Entries", "Lu Yuan", "World Destroying Black Lotus",
        "Heaven Reaching Tower", "Xianxia Audiobook", "Progression Fantasy", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Entering the legendary Great Dao Heaven-Reaching Tower, Lu Yuan confronts the terrifying World-Destroying Black Lotus "
        "and pushes his cultivation toward the Nascent Soul realm!\n\n"
        "While supreme prodigies from across the continent risk life and limb facing ancient trial guardians, Lu Yuan observes quietly—"
        "copying rare taboo entries including [Primordial Lotus Origin], [Heaven-Reaching Dao Bone], and [Void Severing Will]. "
        "Each copied entry is integrated cleanly into his foundation, transforming lethal tribulations into fuel for his own ascension.\n\n"
        "From ascending the ninety-nine trial floors of the ancient tower to annihilating hidden outer-domain fiend elders without "
        "leaving a speck of karmic residue, watch Lu Yuan master low-key invincibility on an unprecedented scale!\n\n"
        "Welcome to Chapters 151 to 200 of 'Entry Cultivation: I Can Copy Entries' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 151: Braving the Great Dao Heaven-Reaching Tower & Witnessing the Black Lotus\n"
        "• Ch 156: Copying the Ancient [Tower Guardian Aegis] Entry to Bypass Death Trials\n"
        "• Ch 162: Taming the World-Destroying Black Lotus Seeds with Primordial Fire Qi\n"
        "• Ch 168: Floor Fifty Ascent: Dismantling Arrogant Royal Scions with Phantom Sword Intent\n"
        "• Ch 174: Nascent Soul Core Formation: Fusing Nine Golden Entries into a Pure Dao Spirit\n"
        "• Ch 180: Subduing the Ancient Fiend Beast Relic & Extracting the [Void Step] Entry\n"
        "• Ch 186: Outer Realm Incursion: Annihilating Blood Dao Cultists with Zero Karmic Traces\n"
        "• Ch 192: Secret Dao Chamber Enlightenment: Replicating Peak Patriarch Heavenly Will\n"
        "• Ch 200: Reaching the Peak of the Heaven-Reaching Tower: Sovereign Master of All Entries\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#EntryCultivation #ICanCopyEntries #XianxiaAudiobook #ProgressionFantasy #CultivationAudiobook #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (151, 155),
            "title": ["HEAVEN-REACHING TOWER", "THE BLACK LOTUS"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of young cultivator Lu Yuan standing before a colossal ancient stone gateway, calm analytical gaze, "
                "neat black hair tied with a dark wooden hairpin, wearing dark charcoal-grey cultivator robes. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set at the base of the colossal Great Dao Heaven-Reaching Tower stretching into starry storm clouds, "
                "revealing a sinister World-Destroying Black Lotus blooming with dark purple necrotic energy in the distance. "
                "Illumination from deep amethyst lotus flames and pale cyan runic ward light, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (156, 160),
            "title": ["TOWER TRIAL ASCENT", "GUARDIAN ENTRY REPLICATION"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan inspecting translucent golden entry panels hovering before him, serene composed smirk, "
                "fingers lightly tracing glowing runic script. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set within a massive floating trial chamber inside the Heaven-Reaching Tower, revealing defeated ancient stone guardian golems "
                "crystallizing into glowing entry particles in the distance. "
                "Illumination from golden status characters and soft azure spirit light, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (161, 165),
            "title": ["LOTUS SEED REFINEMENT", "PRIMORDIAL FLAME HARMONY"],
            "fallback_color": (35, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan refining a hovering obsidian lotus seed between his palms, intense artistic focus, "
                "channeling dual streams of vermilion spiritual fire. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside a quiet stone alcove within the tower, revealing dark destructive energy being cleansed into pure golden life nectar in the distance. "
                "Illumination from roaring crimson flames and shimmering gold alchemical halos, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (166, 170),
            "title": ["PRODIGY CLASH", "EFFORTLESS TOWER SUPREMACY"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan standing calmly with hands tucked behind his back, cool dismissive expression, dark sleeves fluttering. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set upon an expansive circular battle arena on the fiftieth floor, "
                "revealing arrogant continental prodigies knocked back against towering rune pillars by invisible sword pressure in the distance. "
                "Illumination from brilliant white stadium crystal lamps and golden sword qi sparks, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (171, 175),
            "title": ["NASCENT SOUL CORE", "NINE-ENTRY CONVERGENCE"],
            "fallback_color": (35, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan in deep cross-legged meditation, serene transcendent posture, glowing golden and violet entry characters "
                "orbiting his chest like a miniature galaxy. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside a sealed dimensional cultivation sanctum, revealing concentric spiritual shockwaves rippling across floating stone platforms in the distance. "
                "Illumination from blinding violet core lightning and radiant gold entry matrices, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (176, 180),
            "title": ["FIEND BEAST DOMAIN", "VOID STEP INHERITANCE"],
            "fallback_color": (20, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan resting his hand on an ancient slumbering fiend beast statue, sharp perceptive gaze, "
                "fingers crackling with spatial distortion threads. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set within a dark subterranean chamber of the tower, revealing translucent purple spatial entry tags dissolving into his palms in the distance. "
                "Illumination from glowing cyan spatial cracks and eerie bioluminescent wall moss, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (181, 185),
            "title": ["STEALTH COUNTER-PURGE", "ZERO KARMIC TRAIL"],
            "fallback_color": (25, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan executing a silent spatial severing strike, cold decisive glare, hair whipped by kinetic air pressure. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set along an ancient misty stone corridor under moonlight, "
                "revealing invading blood-dao cult elders disintegrating into harmless gray spiritual motes without leaving a trace of blood or karma in the distance. "
                "Illumination from razor-thin silver blade glints and deep shadowy contrasts, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (186, 190),
            "title": ["DAO CHAMBER ENLIGHTENMENT", "HEAVENLY WILL COPIED"],
            "fallback_color": (40, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan looking upward with quiet awe, eyes reflecting golden celestial constellations, serene noble composure. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside the apex chamber of the Great Dao Tower, "
                "revealing enormous golden heavenly runes and ancient patriarch wills rotating across the domed ceiling in the distance. "
                "Illumination from radiant amber starlight and warm golden dao glyphs, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (191, 195),
            "title": ["PRIMORDIAL SWORD MATRIX", "CRUSHING REALM BOUNDARIES"],
            "fallback_color": (25, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan commanding a supreme spatial sword array, resolute commanding jawline, two fingers pointed upward with immense authority. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set against the shattered outer walls of the tower overlooking the continent, "
                "revealing ancient tribulation lightning clouds parted cleanly by a colossal golden sword phantom in the distance. "
                "Illumination from brilliant white energy shockwaves and crackling violet lightning arcs, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (196, 200),
            "title": ["APEX ENTRY MASTER", "TOWER SUMMIT SOVEREIGN"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Sovereign Master Lu Yuan standing at the highest spire of the Great Dao Heaven-Reaching Tower at sunset, "
                "serene invincible presence, glowing gold-and-purple irises reflecting infinite copied entry matrices, wearing midnight-blue elder robes billowing in the wind. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set overlooking boundless continental mountain ranges beneath an aurora sky in the distance. "
                "Illumination from rich golden sunset rays, soft purple twilight clouds, and radiant entry halos, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
