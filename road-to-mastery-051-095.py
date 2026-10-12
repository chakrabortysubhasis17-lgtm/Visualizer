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

    # Novel & Episode Parameters (45 chapters to keep total runtime comfortably under 12 hours)
    "novel_slug": "road-to-mastery-a-litrpg-apocalypse",
    "start_url": "https://freewebnovel.com/novel/road-to-mastery-a-litrpg-apocalypse/chapter-51",
    "start_chapter": 51,
    "end_chapter": 95,
    "default_topic": "Apocalypse Brawler",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 1,  # Sequential processing to respect 15 RPM limits cleanly
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_road_to_mastery_051_095",
    "final_audio": "output_road_to_mastery_051_095.mp3",
    "final_video": "final_road_to_mastery_051_095.mp4",
    "cover_image": "cover_road_to_mastery_051_095.jpg",
    "timestamps_file": "youtube_timestamps_road_to_mastery_051_095.txt",
    "subtitles_file": "subtitles_road_to_mastery_051_095.srt",
    "payload_file": "youtube_upload_payload_road_to_mastery_051_095.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "BARE-KNUCKLE APOCALYPSE DOMINANCE! PRIMAL BRAWLER ASCENSION [Ch 51-95] | LitRPG Audiobook Marathon",
    "tags": [
        "LitRPG Audiobook", "Road to Mastery", "Jack Rust", "System Apocalypse",
        "Progression Fantasy", "Brorilla Brock", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Breaking out of the beginner zones, Earth's deadliest bare-knuckle pugilist enters the galactic trial grounds!\n\n"
        "Having unlocked the devastating kinetic flow of the Brawler class, Jack Rust and his massive gorilla companion Brock "
        "confront the brutal reality of the extraterrestrial System. Higher-tier trial spires, oppressive gravity chambers, "
        "and predatory alien syndicates attempt to break Earth's remaining survivors—only to learn that Jack's fists shatter "
        "both magical barriers and intergalactic arrogance alike!\n\n"
        "Watch Jack forge his body into an indestructible weapon, harmonize primal qi conduits, and protect his fellow delvers "
        "through raw grit, iron discipline, and relentless bare-knuckle violence!\n\n"
        "Welcome to Chapters 51 to 95 of 'Road to Mastery: A LitRPG Apocalypse' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 51: Beyond Zone One & Entering the High-Tier Planetary Trial Spire\n"
        "• Ch 58: Brock's Primal Evolution & Dual-Strike Kinetic Resonance\n"
        "• Ch 64: Gravity Chamber Crucible & Forging the Iron Bone Foundation\n"
        "• Ch 70: Smashing Alien Syndicate Enforcers with Pure Bare-Fist Impact\n"
        "• Ch 76: Deep Wasteland Incursion & Exterminating Alpha Calamity Behemoths\n"
        "• Ch 82: The Galactic Trial Arena Preliminaries & Unstoppable Earth Delver Momentum\n"
        "• Ch 88: Shattering Extraterrestrial Scions in the High Spire Ring\n"
        "• Ch 95: Apex Brawler Sovereign Ascendance & The Unbroken Path to Mastery\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#RoadToMastery #JackRust #SystemApocalypse #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (51, 55),
            "title": ["TRIAL SPIRE ENTRY", "KINETIC BRAWLER"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic 3D portrait of pugilist Jack Rust, rugged chiselled jawline, short windswept dark hair, "
                "intense amber-gold eyes, athletic muscular build with bruised wrapped knuckles radiating faint golden kinetic energy. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set at the glowing archway entrance "
                "of a colossal alien trial spire, revealing massive crystalline spires and floating system notification glyphs in the distance. "
                "Illumination from neon-cyan alien conduit leylines and warm golden fist auras, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (56, 59),
            "title": ["PRIMAL BROTHERHOOD", "BROCK'S METAMORPHOSIS"],
            "fallback_color": (35, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust fighting side-by-side with his beast partner, fierce battle-hardened expression, "
                "bloodied chin, dark eyes locked on an unseen challenger. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a jagged subterranean cavern, revealing massive gorilla partner Brock wreathed in roaring "
                "crimson primal energy crushing armored alien scavengers in the distance. "
                "Illumination from fiery orange impact sparks and crackling kinetic shockwave rings, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (60, 64),
            "title": ["GRAVITY CRUCIBLE", "IRON BONE FOUNDATION"],
            "fallback_color": (25, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust undergoing intense physical strain, sweat glistening on his focused brow, "
                "veins pulsing with golden qi along his neck and forearms, clenched jaw showing pure determination. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a high-tech octagonal alien gravity chamber, "
                "revealing metallic floor plates groaning and bending under tenfold downward gravitational force in the distance. "
                "Illumination from pulsing deep-violet gravity emitters and golden muscle fibers, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (65, 68),
            "title": ["ALIEN CARTEL PURGE", "SHATTERED SHIELDS"],
            "fallback_color": (35, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust in aggressive forward momentum, cold ruthless glare, knuckles wrapped in heavy dark-leather brawler tape. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a neon-lit extraterrestrial outpost alleyway, "
                "revealing arrogant alien syndicate mercenaries reeling backward as their translucent energy shields shatter into glass-like fragments in the distance. "
                "Illumination from bright magenta neon signs and blinding white kinetic detonation bursts, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (69, 73),
            "title": ["WASTELAND CRADLE", "ALPHA BEHEMOTH SLAY"],
            "fallback_color": (25, 30, 20),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust standing victorious over a fallen beast, rugged handsome face, windswept dark hair, "
                "wiping blood from his knuckles, calm steady gaze. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in an apocalyptic desolate wasteland beneath a twin-mooned night sky, revealing a colossal horned trial behemoth "
                "dissolving into sparkling system experience particles behind him in the distance. "
                "Illumination from soft twin-moonlight and shimmering golden experience dust, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (74, 77),
            "title": ["QI MERIDIAN HARMONY", "THE SAGE'S TEACHINGS"],
            "fallback_color": (20, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust in deep meditative focus, eyes closed peacefully, serene commanding posture, "
                "translucent golden meridians flowing harmoniously beneath his skin and across his chest. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside an ancient floating spirit pavilion adrift above the clouds, revealing ethereal floating scrolls "
                "and swirling vortexes of primal qi in the distance. "
                "Illumination from luminous white-gold spiritual energy streams and deep-blue astral starlight, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (78, 82),
            "title": ["DEFENDING EARTH'S HOPE", "DELVER RESCUE"],
            "fallback_color": (30, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust acting as a protective pillar, fierce resolute expression, piercing amber eyes, "
                "holding an outstretched fist that projects a dense golden kinetic barrier wall. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set before a crumbling human survivor bunker, revealing allied delvers regrouping safely behind his shield "
                "while hostile extraterrestrial vanguard swarms barrage the front line in the distance. "
                "Illumination from burning defensive barricades and brilliant golden barrier impacts, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (83, 86),
            "title": ["GALACTIC ARENA", "EXTRATERRESTRIAL BEATDOWN"],
            "fallback_color": (30, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of an unyielding bare-knuckle champion, sharp jawline, confident mocking smirk, "
                "bloodied combat bandages around his hands wreathed in roaring thunder-kinetic aura. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a monumental floating circular colosseum surrounded by thousands of cheering alien spectators, "
                "revealing an arrogant extraterrestrial champion collapsing into the sand under a devastating body blow in the distance. "
                "Illumination from blinding arena floodlights and crackling electric-blue shockwave flashes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (87, 91),
            "title": ["HIGH SPIRE RING", "SUPERSONIC COMBOS"],
            "fallback_color": (20, 35, 45),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust mid-punch, dark hair trailing motion blur, razor-sharp focused amber eyes, "
                "muscles coiled with immense explosive kinetic force. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set atop the soaring pinnacle ring of the trial spire overlooking boundless planetary continents below, "
                "revealing air distorted into sonic boom shockwaves by the supersonic speed of his fists in the distance. "
                "Illumination from high-altitude sunrise rays and blinding white-hot kinetic friction flares, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (92, 95),
            "title": ["APEX BRAWLER SOVEREIGN", "UNBROKEN PATH"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust at the apex of bare-knuckle mastery, calm invincible aura, commanding sun-gold pupils, "
                "wearing battle-worn dark combat pants and an open sleeveless jacket revealing dense glowing golden runic meridians across his torso. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set on a high cliff overlooking the newly stabilized planetary frontier, "
                "revealing Brock standing proudly at his shoulder and Earth's rising fortress cities below under a breathtaking starlit aurora sky. "
                "Illumination from brilliant auroras of sunrise gold, radiant cyan system matrices, and glowing primal qi, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
