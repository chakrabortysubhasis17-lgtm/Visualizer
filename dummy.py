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
    "novel_slug": "daily-life-starting-from-the-dungeon",
    "start_url": "https://mtl-novel.com/novel/daily-life-starting-from-the-dungeon/chapter-101-exploring-the-lake-bottom/",
    "start_chapter": 101,
    "end_chapter": 150,
    "default_topic": "Abyss",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 2,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_dungeon_daily_life_101_150",
    "final_audio": "output_dungeon_daily_life_101_150.mp3",
    "final_video": "final_dungeon_daily_life_101_150.mp4",
    "cover_image": "cover_dungeon_daily_life_101_150.jpg",
    "timestamps_file": "youtube_timestamps_dungeon_daily_life_101_150.txt",
    "subtitles_file": "subtitles_dungeon_daily_life_101_150.srt",
    "payload_file": "youtube_upload_payload_dungeon_daily_life_101_150.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "EXPLORING THE LAKE BOTTOM! SUBTERRANEAN ABYSS OVERLORD [Ch 101-150] | LitRPG Audiobook",
    "tags": [
        "LitRPG Audiobook", "Daily Life Starting from the Dungeon", "Dungeon Core",
        "Labyrinth Master", "Progression Fantasy", "Dungeon Building", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Plunging into the dark depths of the subterranean subterranean lake!\n\n"
        "As elite adventurer parties and rival guild expeditions delve deeper into the labyrinth, "
        "Dungeon Master Mu Qinglin expands his living core into an unfathomable flooded abyssal zone. "
        "Harnessing aquatic spawners, luminescent trench traps, and ancient drowned ruins, "
        "he commands the subterranean lake with absolute dominion!\n\n"
        "Welcome to Chapters 101 to 150 of 'Daily Life Starting from the Dungeon' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 101: Exploring the Lake Bottom & Uncovering the Drowned Vault\n"
        "• Ch 110: Submerged Trench Spawners & Abyssal Serpent Awakening\n"
        "• Ch 120: Elite Diver Guild Annihilation in the Crystal Deep\n"
        "• Ch 130: The Sunken Temple Altar & Hydraulic Core Evolution\n"
        "• Ch 140: Tide Leviathan Floor Boss Descent\n"
        "• Ch 150: Sovereign Aquatic Labyrinth Ascendance\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#LitRPG #DungeonCore #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (101, 105),
            "title": ["LAKE BOTTOM EXPEDITION", "THE DROWNED VAULT"],
            "fallback_color": (15, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of a young male dungeon master, dark hair, brilliant amber-gold eyes, "
                "wearing midnight-black robes with arcane silver trim. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against an immense submerged underground lake with glowing crystalline turquoise waters, "
                "revealing ancient sunken stone temple spires in the distance. Illumination from bioluminescent teal jellyfish and bright amber "
                "aquatic mana sparks, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (106, 110),
            "title": ["ABYSSAL SERPENT", "DEEPWATER SPAWNER"],
            "fallback_color": (20, 35, 45),
            "prompt": (
                "Clear, high-contrast 3D portrait layout of a dark-haired labyrinth lord wearing crimson-trimmed shadow-weave armor. "
                "Razor-sharp foreground focus on the character, clean studio lighting, pristine face definition, zero motion blur. "
                "In the background scene behind him, a colossal deep-water armored leviathan serpent coils around solid glowing submerged obelisks. "
                "High-intensity turquoise magical searchlights and fiery amber lantern beams slice through deep indigo water, forcing distinct, varied color channels."
            )
        },
        {
            "index": 3, "range": (111, 115),
            "title": ["DIVER GUILD AMBUSH", "HYDROSTATIC TRAP"],
            "fallback_color": (25, 20, 40),
            "prompt": (
                "Ultra-sharp high-contrast 3D action portrait of a handsome male dungeon master standing on a submerged crystal platform. "
                "Clear foreground focus, pristine facial features, sharp clean lines. Beside him, high-tech holographic management nodes float cleanly, "
                "glowing with vibrant neon green and hot-pink telemetry grids. Directly in the background behind him, armored human diver knights stand caught "
                "inside static vortex whirlpool structures triggered by glowing magical floor runes under deep violet underground torchlight."
            )
        },
        {
            "index": 4, "range": (116, 120),
            "title": ["SUNKEN CITADEL", "ANCIENT CORE VAULT"],
            "fallback_color": (30, 15, 35),
            "prompt": (
                "Cinematic close-up 3D portrait of the dungeon master with intense violet-amber eyes, clad in dark obsidian mantle armor plates. "
                "Razor-sharp edge definition, clear bright studio lighting, pristine texturing. Far below him in the distant background chasm, a massive sunken citadel "
                "rises cleanly from the deep lake bed, adorned with glowing sapphire crystals and golden protective runes. A striking clash of warm fiery orange mana torches "
                "and cool cobalt-blue water currents occurs across the far distance in high saturation."
            )
        },
        {
            "index": 5, "range": (121, 125),
            "title": ["HYDRAULIC MATRIX", "TIDE DOMAIN OVERLOAD"],
            "fallback_color": (15, 40, 35),
            "prompt": (
                "Ultra-sharp 3D digital portrait of a male anime dungeon lord with crisp black hair and silver-and-gold enchanted tunics. "
                "Flawless facial features, crystal clear macro focus, perfectly balanced studio portrait light. Directly behind him in the background scene, "
                "the dungeon's hydraulic core matrix stands active, projecting massive, clean geometric water barriers and cascading falls shifting through distinct "
                "bands of bright magenta, vivid turquoise, and radiant gold, filling the lake cavern with crisp color separation."
            )
        },
        {
            "index": 6, "range": (126, 130),
            "title": ["AQUATIC RAID PURGE", "THE CORAL DEFENSE"],
            "fallback_color": (40, 20, 20),
            "prompt": (
                "High-contrast 3D action portrait of a powerful dark-haired dungeon ruler clad in dark cobalt-and-brass armor. "
                "Razor-sharp foreground focus, clean edges, flawless facial details, zero motion blur. Directly behind him in the background layer, invading "
                "high-rank guild mages stand arrayed against summoned chitinous coral crabs along an illuminated submerged bridge, with sharp crimson sparks "
                "localized purely behind the main hero's profile, forcing a vivid multi-colored composition."
            )
        },
        {
            "index": 7, "range": (131, 135),
            "title": ["FLOOR BOSS DESCENT", "TIDE WYRM AWAKENING"],
            "fallback_color": (20, 35, 50),
            "prompt": (
                "Ultra-sharp 3D portrait layout of a male manhwa dungeon master in sleek dark chrome armor with neon red trimming. "
                "Crystal clear focus on his face and hair, professional bright lighting, pristine textures. In the action scene behind him, a colossal ancient "
                "tide wyrm floor boss emerges from a bottomless aquatic abyss, launching solid, static beams of hot-pink and turquoise mana light "
                "straight upward into the massive cavern expanse. Rich color depth, clean geometric architecture, zero blur."
            )
        },
        {
            "index": 8, "range": (136, 140),
            "title": ["SUBTERRANEAN HAVEN", "DROWNED SANCTUARY"],
            "fallback_color": (35, 25, 45),
            "prompt": (
                "Breathtaking 3D cinematic visual. Close-up sharp focus on a dark-haired anime master standing firm on a high overlooking balcony tower. "
                "Pristine clothing textures, clear facial features, studio light alignment. Directly behind him in the background layer, an expansive underwater sanctuary city "
                "protected by a massive glowing air dome shines with warm golden lanterns, floating neon-magenta merchant stalls, and clean stone arcades under the dark lake waters."
            )
        },
        {
            "index": 9, "range": (141, 145),
            "title": ["ELEMENTAL SURGE", "CORE ASCENSION RIFT"],
            "fallback_color": (25, 20, 50),
            "prompt": (
                "Dramatic high-contrast 3D visual. Close-up portrait of the dungeon master wearing pitch-black scale armor with glowing cyan energy runes. "
                "Razor-sharp edge definition, clean facial details, macro focus. Directly behind him in the background scene, the central dungeon core ascends "
                "into a multi-tiered floating spire, radiating clean, solid concentric rings of golden, magenta, and turquoise light into the vast cavern expanse."
            )
        },
        {
            "index": 10, "range": (146, 150),
            "title": ["ABYSSAL SOVEREIGN", "RULER OF THE DEEP"],
            "fallback_color": (25, 30, 50),
            "prompt": (
                "Premium cinematic 3D climax visual. Close-up profile shot of Dungeon Master Mu Qinglin in ornate gold-trimmed silver royal robes. "
                "Razor-sharp focus on the character profile, flawless skin and armor details, crisp clean lines, clear studio portrait light. "
                "He stands firmly on an expansive obsidian throne balcony. Across the background layer behind him, an immense underground lake empire expands, "
                "illuminated by brilliant, highly saturated auroras of neon green, deep violet, and warm amber mana fields dancing across the grand cavern dome ceiling."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
