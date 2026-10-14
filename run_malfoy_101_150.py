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
    "novel_slug": "hp-miss-malfoy-doesnt-want-to-romance-her-parents-generation",
    "start_url": "https://mtl-novel.com/novel/hp-miss-malfoy-doesnt-want-to-romance-her-parents-generation/chapter-101-whitewashing-peace/",
    "start_chapter": 101,
    "end_chapter": 150,
    "default_topic": "Miss Malfoy",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_hp_miss_malfoy_101_150",
    "final_audio": "output_hp_miss_malfoy_101_150.mp3",
    "final_video": "final_hp_miss_malfoy_101_150.mp4",
    "cover_image": "cover_hp_miss_malfoy_101_150.jpg",
    "timestamps_file": "youtube_timestamps_hp_miss_malfoy_101_150.txt",
    "subtitles_file": "subtitles_hp_miss_malfoy_101_150.srt",
    "payload_file": "youtube_upload_payload_hp_miss_malfoy_101_150.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "OUTSMARTING THE FIRST WIZARDING WAR! SLYTHERIN HEIRESS SECURES ABSOLUTE NEUTRALITY [Ch 101-150] | HP Fanfiction Audiobook Marathon",
    "tags": [
        "Harry Potter Fanfiction", "Miss Malfoy", "Marauders Era", "Slytherin",
        "Severus Snape", "Sirius Black", "Regulus Black", "Voldemort War Era", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "As the shadow of the First Wizarding War deepens across magical Britain, Miss Malfoy doubles down on "
        "her grand strategy: complete political neutrality, unassailable defensive magic, and total family survival!\n\n"
        "Refusing to become collateral damage in the ideological clash between Dumbledore's Order of the Phoenix and Voldemort's "
        "fanatical Death Eaters, she moves behind the scenes of Hogwarts and the Wizengamot. Whitewashing delicate political ties, "
        "deciphering esoteric soul and ward magic, and out-maneuvering predatory pureblood recruiters, Miss Malfoy turns the Slytherin "
        "dungeon into an untouchable bastion of independent power.\n\n"
        "Watch her guide young Severus Snape away from self-destructive obsession, shield Regulus Black from reckless martyrdom, "
        "and handle the relentless Marauders with razor-sharp wit and overwhelming spellcraft!\n\n"
        "Welcome to Chapters 101 to 150 of 'HP: Miss Malfoy Doesn’t Want to Romance Her Parents’ Generation' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 101: Whitewashing Peace: Engineering Political Plausible Deniability\n"
        "• Ch 107: Department of Mysteries Incursions & Unraveling Ancient Time Wards\n"
        "• Ch 114: Slytherin Dungeon Counter-Purge: Neutralizing Radical Death Eater Recruiters\n"
        "• Ch 121: The Marauders' Temporary Truce: Defending Castle Borders from Outside Infiltration\n"
        "• Ch 128: Wizengamot Maneuvers: Preserving the Malfoy Assets Against Ministry Seizure\n"
        "• Ch 135: Forbidden Soul Alchemy: Refining Defensive Mind-Palace Occlumency Arrays\n"
        "• Ch 142: Secret Nocturnal Accord: Forging the Regulus-Severus Defensive Pact\n"
        "• Ch 150: Sovereign Aristocratic Sanctuary: Establishing an Autonomous Domain Free from the Dark Lord\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#HPFanfiction #MissMalfoy #MaraudersEra #Slytherin #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (101, 105),
            "title": ["WHITEWASHING PEACE", "POLITICAL NEUTRALITY"],
            "fallback_color": (20, 30, 25),
            "prompt": (
                "Cinematic 3D portrait of young Miss Malfoy sitting at an ornate mahogany writing desk, platinum-blonde hair styled "
                "in a precise braided crown, calculating icy-grey eyes, wearing high-collared dark-green silk robes with silver cufflinks. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside her private study at Malfoy Manor, "
                "revealing wax-sealed diplomatic correspondence scrolls, a crystal inkwell with a silver raven quill, and a burning fireplace in the distance. "
                "Illumination from warm golden candle flames and cool twilight streaming through mullioned windows, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (106, 110),
            "title": ["ESOTERIC WARDS", "ANCIENT RUNIC SEALS"],
            "fallback_color": (15, 25, 35),
            "prompt": (
                "Cinematic 3D portrait of Miss Malfoy tracing glowing runic geometry in mid-air with a slender hawthorn wand, composed academic focus, "
                "hair ribbons floating gently under static magical currents. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside an underground ancient ward vault beneath Hogwarts, revealing massive carved granite stones pulsing with ethereal azure light in the distance. "
                "Illumination from bright cyan magical glyphs casting sharp highlights and deep dramatic shadows, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (111, 115),
            "title": ["SLYTHERIN RESISTANCE", "PURIST COUNTER-STRIKE"],
            "fallback_color": (25, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of Miss Malfoy confronting arrogant pureblood radicals, cold dismissive smirk, chin held high with regal authority, "
                "fingers lightly tapping her wand sheath. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set in the shadowy Slytherin common room beneath the Black Lake, revealing older radical students hesitating under her piercing gaze in the distance. "
                "Illumination from eerie greenish lake-filtered water light and flickering green flames from the hearth, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (116, 120),
            "title": ["BLACK LAKE REFLECTION", "MIND OCCLUMENCY"],
            "fallback_color": (15, 30, 30),
            "prompt": (
                "Cinematic 3D portrait of Miss Malfoy in deep meditative focus, serene expression, delicate eyelids partially closed, "
                "surrounded by a translucent crystalline shield of Occlumency mind-magic. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set along the desolate rocky shores of the Black Lake under heavy mist, revealing Scottish pine forests shrouded in fog in the distance. "
                "Illumination from pale silver dawn light reflecting across still water ripples, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (121, 125),
            "title": ["TEMPORARY TRUCE", "CORRIDOR ACCORD"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of Miss Malfoy in diplomatic negotiation, arms crossed inside long bell-sleeved robes, sharp observant posture, "
                "platinum bangs swept neatly across her brow. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside a quiet stone corridor alcove, revealing silhouettes of young Sirius Black and James Potter standing cautiously across the hallway in the distance. "
                "Illumination from glowing golden wall sconces and soft atmospheric castle dust motes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (126, 130),
            "title": ["WIZENGAMOT INTRIGUE", "FAMILY PRESERVATION"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of Miss Malfoy wearing a formal pureblood heiress traveling cloak of heavy velvet embroidered with silver serpents, "
                "dignified untouchable presence, unwavering steady gaze. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set overlooking the tiered stone amphitheater of the Ministry Wizengamot courtrooms, revealing masked delegates and purple-robed officials in the distance. "
                "Illumination from high overhead gas lamps casting dramatic long architectural shadows, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (131, 135),
            "title": ["FORBIDDEN BREWING", "ALCHEMICAL HARMONY"],
            "fallback_color": (20, 35, 25),
            "prompt": (
                "Cinematic 3D portrait of Miss Malfoy adjusting the heat beneath a silver cauldron, delicate drops of alchemical essence falling from a glass pipette, "
                "eyes reflecting pearlescent potion hues. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside a secluded potions laboratory beneath the dungeons, revealing shelves of rare glowing herbs, crystal vials, and drying mandrake roots in the distance. "
                "Illumination from soft emerald potion vapors and low amber burner embers, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (136, 140),
            "title": ["ASTRONOMY TOWER VIGIL", "WAR ON THE HORIZON"],
            "fallback_color": (20, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of Miss Malfoy standing on the high Astronomy Tower ramparts, winter traveling cloak pulled close against the wind, "
                "solemn watchful expression overlooking the dark horizon. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set against a stormy nighttime sky, revealing distant dark storm clouds and the glowing silhouette of the Forbidden Forest below in the distance. "
                "Illumination from a cold crescent moon and pale starlight cutting through moving clouds, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (141, 145),
            "title": ["SHADOW COALITION", "PROTECTING THE FUTURE"],
            "fallback_color": (30, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of Miss Malfoy leading a discreet strategy meeting, composed commanding aura, "
                "raising two fingers as she explains a defensive counter-measure. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside an abandoned celestial observatory classroom, revealing young Severus Snape and Regulus Black listening with deep intent in the distance. "
                "Illumination from a floating charmed silver sphere casting intricate celestial constellations across stone walls, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (146, 150),
            "title": ["SOVEREIGN SCHOLAR", "UNTOUCHABLE HORIZON"],
            "fallback_color": (25, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of Miss Malfoy at the peak of her authority, windswept platinum hair crowned with a delicate silver circlet, "
                "radiant icy-grey eyes filled with absolute confidence, wearing tailored emerald-and-silver academic robes. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set upon the high viaduct overlooking the vast Hogwarts valley at sunrise, "
                "revealing golden sunlight shattering through mountain mists and glinting off castle spires in the distance. "
                "Illumination from brilliant morning sunlight, soft silver mists, and rich emerald reflections, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
