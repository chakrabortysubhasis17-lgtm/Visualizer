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
    "novel_slug": "road-to-mastery-a-litrpg-apocalypse",
    "start_url": "https://freewebnovel.com/novel/road-to-mastery-a-litrpg-apocalypse/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Apocalypse Brawler",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 1,  # Sequential processing to respect 15 RPM limits cleanly
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_road_to_mastery_001_050",
    "final_audio": "output_road_to_mastery_001_050.mp3",
    "final_video": "final_road_to_mastery_001_050.mp4",
    "cover_image": "cover_road_to_mastery_001_050.jpg",
    "timestamps_file": "youtube_timestamps_road_to_mastery_001_050.txt",
    "subtitles_file": "subtitles_road_to_mastery_001_050.srt",
    "payload_file": "youtube_upload_payload_road_to_mastery_001_050.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "EARTH GETS INTEGRATED! THE APEX BRAWLER AWAKENS [Ch 1-50] | LitRPG Apocalypse Audiobook Marathon",
    "tags": [
        "LitRPG Audiobook", "Road to Mastery", "LitRPG Apocalypse", "Jack Rust",
        "Progression Fantasy", "Unarmed Brawler", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Earth is forcefully integrated into the grand cosmic System, thrusting humanity into a brutal survival game!\n\n"
        "While others scramble for magical staves or swords, Jack Rust relies on biological insight, unyielding grit, "
        "and pure bare-knuckle violence. Thrust into a lethal tutorial subterranean zone, Jack chooses the path of the Unarmed Brawler—refusing "
        "weapons to forge his body into a living weapon of kinetic force!\n\n"
        "Teaming up with Brock, a massive gorilla beast companion sharing his love for sheer physical power, Jack punches his way "
        "through deadly cave horrors, arrogant alien scions, and rogue human syndicates. Witness the birth of an unstoppable brawler sovereign!\n\n"
        "Welcome to Chapters 1 to 50 of 'Road to Mastery: A LitRPG Apocalypse' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 01: Planetary Integration Day & Awakening the Unarmed Brawler Class\n"
        "• Ch 08: Subterranean Cavern Survival & Meeting Brock the Primal Beast\n"
        "• Ch 15: Raw Punch Kinetic Mastery & Smashing the First Mutated Cave Troll\n"
        "• Ch 22: Confronting Arrogant Alien Delvers & Bare-Handed Shield Shatter\n"
        "• Ch 29: Uniting with Vivi, Li Xiang, and Dorman in the Intermediate Depths\n"
        "• Ch 35: Clashing with Gan Salin's Syndicate & Crushing Rogue Cultivators\n"
        "• Ch 40: The Ancient Sage's Trial Chamber & Unlocking Primal Body Resonance\n"
        "• Ch 50: Tutorial Zone Floor Sovereign Purge & Stepping onto the Galactic Stage\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#RoadToMastery #LitRPG #Apocalypse #ProgressionFantasy #JackRust #FullAudiobook #AudiobookMarathon #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (1, 5),
            "title": ["SYSTEM INTEGRATION", "THE BRAWLER AWAKENS"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust at the dawn of the apocalypse, athletic muscular physique, neat short brown hair, "
                "focused determined hazel eyes, wearing rugged torn tactical outdoor clothing with taped knuckles. Flawless facial features, "
                "crisp detailed skin textures, medium close-up shot. Set inside a crumbling subterranean limestone cavern, revealing floating "
                "translucent blue system stat interfaces and shattered alien monolith debris in the distance. "
                "Illumination from neon-cyan interface luminescence and dim cavern torches, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (6, 10),
            "title": ["PRIMAL BROTHERHOOD", "BROCK'S ARRIVAL"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of brawler Jack Rust standing side-by-side with his companion beast, sharp square jawline, confident grin, "
                "blood-stained bandages wrapped tightly around forearms. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set within an overgrown underground fungal forest, revealing Brock, a colossal silver-furred brawny gorilla beast "
                "pounding his massive fists onto the stone ground in loyal camaraderie in the distance. "
                "Illumination from bioluminescent emerald mushrooms and ambient golden crystal veins, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (11, 15),
            "title": ["KINETIC IMPACT", "CAVE HORROR PURGE"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust delivering a devastating bare-knuckle punch, intense ferocious expression, sweat glistening on his brow, "
                "eyes glowing with activated physical mana. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a narrow rocky tunnel, revealing a monstrous multi-eyed cave predator collapsing "
                "backward under a visible circular kinetic shockwave in the distance. "
                "Illumination from exploding kinetic air ripples and crimson monster blood spatter, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (16, 20),
            "title": ["UNARMED MASTERY", "BODY FORGED AS STEEL"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of a battle-hardened Jack Rust, chiselled facial planes, calm calculating gaze, "
                "wearing reinforced monster-hide combat trousers and dark fingerless brawling wraps glowing with bronze energy conduits. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set on an overlooking underground precipice, "
                "revealing vast subterranean cave cities carved into stalactites below in the distance. "
                "Illumination from warm bronze physical aura currents and glowing blue stalactite crystals, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (21, 25),
            "title": ["ALIEN SCIONS", "SHIELD CRUSH"],
            "fallback_color": (30, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of an unyielding Earth brawler, razor-sharp jawline, cold defiant smirk, "
                "wiping blood from his cheek with a scarred fist. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside an ancient metallic alien ruin, revealing an arrogant extraterrestrial scion's shimmering prismatic energy barrier "
                "spiderwebbing and shattering under Brock and Jack's combined assault in the distance. "
                "Illumination from crackling violet energy sparks and harsh fluorescent alien corridor lighting, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (26, 30),
            "title": ["PARTY UNIFICATION", "ALLIES OF EARTH"],
            "fallback_color": (20, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust in tactical command, alert protective gaze, short windswept hair, "
                "wearing blackened leather armguards with reinforced brass studs. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set around a secure stone campfire inside a cave alcove, revealing party members Vivi, Li Xiang, and Dorman "
                "sharpening weapons and tending to magical wards in the distance. "
                "Illumination from flickering campfire embers and cool ambient subterranean mist, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (31, 35),
            "title": ["ROGUE SYNDICATE", "GAN SALIN'S AMBUSH"],
            "fallback_color": (35, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust enveloped in pure combat focus, razor-sharp expression, fierce golden-amber irises, "
                "his fists trailing visible supersonic condensation cones. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in a blood-soaked canyon floor, revealing defeated hostile rogue cultivators and syndicate enforcers "
                "pinned against jagged boulders in the distance. "
                "Illumination from burning magical seals and harsh orange torches, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (36, 40),
            "title": ["THE SAGE'S SANCTUM", "PRIMAL TRIAL"],
            "fallback_color": (25, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust undergoing spiritual body breakthrough, serene intense expression, "
                "veins pulsing with incandescent gold mana across his neck and arms. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a grand crystalline sanctuary chamber of the mysterious Sage, revealing towering runic trial pillars "
                "radiating celestial glyphs into Jack and Brock in the distance. "
                "Illumination from blinding golden ascension light beams and floating silver ancient scripts, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (41, 45),
            "title": ["BEAST TIDE DEFENSE", "SURVIVORS' BASTION"],
            "fallback_color": (30, 20, 25),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust as an emerging vanguard leader, powerful commanding posture, dark hair whipped by shockwaves, "
                "wearing heavy chitin-reinforced battle plate over his brawler vest. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on the fortified stone ramparts of the human tutorial outpost, revealing a massive tidal wave of subterranean beasts "
                "collapsing under Brock's ground-slam shockwaves and Jack's forward charge in the distance. "
                "Illumination from exploding defensive mana ballistas and fiery crater plumes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (46, 50),
            "title": ["TUTORIAL APEX", "COSMIC THRESHOLD"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Apex Brawler Jack Rust standing triumphant, majestic chiselled features, radiant electric-gold eyes, "
                "wearing battle-hardened titan-leather brawler vestments with glowing cosmic conduit wraps. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set atop the final colossal tutorial gateway overlooking the boundless cosmic void and distant alien planets, "
                "revealing giant Brock roaring in absolute victory beside him under a breathtaking stellar aurora. "
                "Illumination from brilliant auroras of starlight gold, cyan kinetic halos, and deep-purple space nebulae, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
