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
    "novel_slug": "only-i-level-up-wn",
    "start_url": "https://freewebnovel.com/novel/only-i-level-up-wn/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Hunter",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 2,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_only_i_level_up_001_050",
    "final_audio": "output_only_i_level_up_001_050.mp3",
    "final_video": "final_only_i_level_up_001_050.mp4",
    "cover_image": "cover_only_i_level_up_001_050.jpg",
    "timestamps_file": "youtube_timestamps_only_i_level_up_001_050.txt",
    "subtitles_file": "subtitles_only_i_level_up_001_050.srt",
    "payload_file": "youtube_upload_payload_only_i_level_up_001_050.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "ONLY I LEVEL UP! THE WEAKEST HUNTER AWAKENS [Ch 1-50] | Solo Leveling Audiobook",
    "tags": [
        "LitRPG Audiobook", "Solo Leveling", "Only I Level Up", "Sung Jin-Woo",
        "Shadow Monarch", "Hunter System", "Progression Fantasy", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Known as mankind's weakest E-Rank Hunter, Sung Jin-Woo fights merely to pay his mother's hospital bills.\n\n"
        "Trapped inside the terrifying double dungeon of Cartenon Temple, faced with colossal bloodthirsty god statues, "
        "Jin-Woo accepts a mysterious courage trial right at the brink of death. Awakening in a hospital bed, "
        "a floating game quest log appears before his eyes—granting him an unprecedented ability no other hunter possesses: "
        "The power to level up infinitely!\n\n"
        "Welcome to Chapters 1 to 50 of 'Only I Level Up' (Solo Leveling) in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 01: The Cartenon Temple Double Dungeon & Statue of God Slaughter\n"
        "• Ch 10: Secret Hospital Awakening & The Daily Survival Penalty Quest\n"
        "• Ch 18: Subway Instant Dungeon & Slaying the Blue Poison-Fanged Kasaka\n"
        "• Ch 25: C-Rank Lizard Raid Betrayal & Emergency Quest: Eliminate Enemies\n"
        "• Ch 35: Teaming with Yoo Jin-Ho & Rapid-Clearing Sealed Dungeons\n"
        "• Ch 45: Job Change Quest & Blood-Red Commander Igris Showdown\n"
        "• Ch 50: The Shadow Monarch Rises: 'Arise!'\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to Chugong. Subscribe for more!\n\n"
        "#SoloLeveling #OnlyILevelUp #SungJinWoo #ShadowMonarch #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (1, 5),
            "title": ["CARTENON TEMPLE", "THE DOUBLE DUNGEON"],
            "fallback_color": (15, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of a young male Korean hunter, messy dark hair, bruised determined face, "
                "wearing a torn dark green hooded jacket over battered leather armor. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against an immense subterranean stone temple chamber, revealing a colossal ancient stone god statue with glowing "
                "crimson ruby eyes smiling malevolently in the distance. Illumination from crackling blue blue mana torches and eerie blood-red eyebeams, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (6, 10),
            "title": ["QUEST WINDOW", "THE ONLY PLAYER"],
            "fallback_color": (20, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of a young male hunter, clean black hair, sharp alert eyes, "
                "wearing a clean white hospital gown under cool rim lighting. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against a dark Seoul hospital ward at midnight, revealing a floating holographic translucent blue system window "
                "with glowing golden text and telemetry grids hovering in the distance. Illumination from neon-cyan interface luminescence and ambient city moonlight, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (11, 15),
            "title": ["SUBWAY DUNGEON", "STEEL FANG HUNT"],
            "fallback_color": (30, 20, 20),
            "prompt": (
                "Cinematic 3D portrait of a rapidly evolving male hunter, sharp black hair, intense glowing azure eyes, "
                "wearing dark fitted athletic clothing and steel gauntlets. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against an overgrown abandoned subway platform, revealing glowing red-eyed mutated steel-fanged lycan wolves "
                "stalking the train tracks in the distance. Illumination from crackling neon-emerald leveling particles and flickering emergency orange lanterns, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (16, 20),
            "title": ["POISON FANG KASAKA", "DAGGER MASTERY"],
            "fallback_color": (20, 40, 35),
            "prompt": (
                "Cinematic 3D portrait of an athletic young male hunter, sleek jet-black hair, fierce glowing blue eyes, "
                "wielding a glowing translucent serrated bone dagger. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against a flooded subterranean cavern lake, revealing a massive armored azure venom snake boss "
                "rearing its fangs in the distance. Illumination from toxic glowing turquoise water currents and radiant golden stat indicators, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (21, 25),
            "title": ["LIZARDS BETRAYAL", "EMERGENCY QUEST"],
            "fallback_color": (40, 20, 20),
            "prompt": (
                "Cinematic 3D portrait of a cold commanding male hunter, sharp angular jawline, piercing glowing violet-blue eyes, "
                "wearing sleek dark titanium pauldron armor. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against an enclosed crystal mana cave, revealing treacherous armored human traitor hunters drawing heavy blades "
                "in the distance. Illumination from a floating blood-red emergency quest banner and volcanic orange mana flares, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (26, 30),
            "title": ["MURDEROUS INTENT", "SURVIVAL EXECUTION"],
            "fallback_color": (35, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of a dangerous male assassin hunter, dark windswept hair, intense glowing amethyst eyes, "
                "wearing pitch-black stealth armor with subtle silver trims. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against a fractured subterranean cavern floor, revealing shattered shields and defeated rogue raiders "
                "dissolving into smoke in the distance. Illumination from razor-sharp purple kinetic speed arcs and cool navy shadows, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (31, 35),
            "title": ["RAID PARTNERSHIP", "SPEED CLEARING"],
            "fallback_color": (25, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of an elite Korean hunter, refined handsome features, sharp luminous blue eyes, "
                "wearing a tailored midnight-blue trench coat over reinforced armor. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against a bustling modern Seoul gate perimeter, revealing heavily armored assault squads and luxury SUVs "
                "waiting outside the glowing portal in the distance. Illumination from swirling cyan dimensional vortexes and warm golden city searchlights, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (36, 40),
            "title": ["SURVEILLANCE CLASH", "KANG TAE-SHIK"],
            "fallback_color": (35, 20, 25),
            "prompt": (
                "Cinematic 3D portrait of a lethal male hunter, sleek black hair, glowing cold sapphire eyes, "
                "holding twin glowing curved daggers in reverse grip. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against a bloodstained dungeon tunnel, revealing an elite rogue association inspector dashing at supersonic speed "
                "in the distance. Illumination from blinding silver blade flashes and crackling magenta speed trails, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (41, 45),
            "title": ["COMMANDER IGRIS", "JOB CHANGE QUEST"],
            "fallback_color": (40, 15, 20),
            "prompt": (
                "Cinematic 3D portrait of an imposing male hunter sovereign, tall muscular build, brilliant glowing blue eyes, "
                "wearing dark dragon-scale armor plates. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against the crumbling throne room of a gothic subterranean castle, revealing Blood-Red Commander Igris "
                "standing in towering crimson armor with a massive greatsword in the distance. Illumination from roaring crimson flame braziers and deep indigo shadows, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (46, 50),
            "title": ["ARISE!", "THE SHADOW MONARCH"],
            "fallback_color": (20, 15, 40),
            "prompt": (
                "Cinematic 3D portrait of Sung Jin-Woo as the Shadow Monarch, dark windswept hair, brilliant glowing neon-purple eyes, "
                "wearing an imperial black longcoat with misty dark energy swirling around his shoulders. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against an expansive shadow realm battlefield, revealing thousands of kneeling shadow knights with glowing blue plumes "
                "rising from the ground in the distance. Illumination from radiant violet shadow flames and ethereal cyan soul mist, "
                "deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
