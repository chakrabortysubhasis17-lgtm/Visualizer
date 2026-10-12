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
    "start_url": "https://freewebnovel.com/novel/road-to-mastery-a-litrpg-apocalypse/chapter-96",
    "start_chapter": 96,
    "end_chapter": 140,
    "default_topic": "Apocalypse Brawler",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 1,  # Sequential processing to respect 15 RPM limits cleanly
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_road_to_mastery_096_140",
    "final_audio": "output_road_to_mastery_096_140.mp3",
    "final_video": "final_road_to_mastery_096_140.mp4",
    "cover_image": "cover_road_to_mastery_096_140.jpg",
    "timestamps_file": "youtube_timestamps_road_to_mastery_096_140.txt",
    "subtitles_file": "subtitles_road_to_mastery_096_140.srt",
    "payload_file": "youtube_upload_payload_road_to_mastery_096_140.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "GALACTIC SECTOR WARLORD PURGE! INDESTRUCTIBLE FIST TITAN [Ch 96-140] | LitRPG Audiobook Marathon",
    "tags": [
        "LitRPG Audiobook", "Road to Mastery", "Jack Rust", "System Apocalypse",
        "Progression Fantasy", "Brorilla Brock", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Breaking past regional planet boundaries, Earth's deadliest bare-knuckle master enters the interstellar war theater!\n\n"
        "Having unlocked the profound mysteries of advanced kinetic condensation and internal organ tempering, Jack Rust and his "
        "titanic partner Brock step into higher-tier system battlegrounds. Predatory galactic factions, corrupt sector administrators, "
        "and ancient alien warlords attempt to carve up Earth's zone assets—unaware that Jack has tempered his fists into catastrophic "
        "planetary siege weapons!\n\n"
        "Watch Jack push beyond mortal kinetic thresholds, shatter spatial suppression barriers, and forge an impenetrable "
        "defensive bastion for Earth's survivors through unyielding discipline and raw bare-fist dominance!\n\n"
        "Welcome to Chapters 96 to 140 of 'Road to Mastery: A LitRPG Apocalypse' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 96: Crossing Interstellar Zone Thresholds & Unlocking Deep Kinetic Resonance\n"
        "• Ch 102: Brock's Primal Behemoth Metamorphosis & Thunder-Stomp Rampage\n"
        "• Ch 108: Crushing Extraterrestrial Sector Enforcers with Heavy Body Blows\n"
        "• Ch 115: Void Rift Incursion & Purging Dimensional Calamity Swarms\n"
        "• Ch 121: The Secret Trial of the Ancient Titan Forge & Bone Marrow Tempering\n"
        "• Ch 127: Shattering Galactic Syndicate Siege Dreadnoughts with Bare Knuckles\n"
        "• Ch 134: Master Pugilist Domain Expansion & Deflecting Spatial Disintegration\n"
        "• Ch 140: Apex Sector Conqueror Coronation & Establishing Earth's Sovereign Zone\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#RoadToMastery #JackRust #SystemApocalypse #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (96, 100),
            "title": ["INTERSTELLAR BOUNDARY", "KINETIC MASTERY"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of master brawler Jack Rust, rugged chiselled jawline, windswept dark hair, "
                "intense amber-gold eyes, athletic muscular build with wrapped knuckles radiating intense electric-gold kinetic energy. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set at the glowing edge of an interstellar "
                "warp platform, revealing swirling purple-and-gold nebulae and floating alien sector banners in the distance. "
                "Illumination from neon-cyan energy conduits and crackling golden fist auras, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (101, 104),
            "title": ["PRIMAL TITAN", "BROCK'S ASCENSION"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust in combat synchronization, fierce focused expression, wrapped fists clenched, "
                "dark hair trailing kinetic embers. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside a shattered crystalline asteroid valley, revealing colossal gorilla partner Brock wreathed in roaring "
                "crimson-and-gold primal energy shattering alien siege mechs into scrap metal in the distance. "
                "Illumination from fiery orange impact detonations and blinding white kinetic shockwave rings, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (105, 109),
            "title": ["SECTOR ENFORCERS", "HEAVY IMPACT PURGE"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of an unyielding pugilist warrior, bloodied jawline, cold calculating glare, "
                "heavy combat tape wrapped tightly around his forearms wreathed in dense gravity-defying shockwaves. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside an upscale extraterrestrial trade citadel, "
                "revealing elite armored sector enforcers hurled backward through reinforced titanium pillars under invisible concussive shockwaves in the distance. "
                "Illumination from neon-magenta holographic billboards and blinding yellow impact flashes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (110, 114),
            "title": ["VOID RIFT SWARM", "UNBROKEN STRIKE"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust mid-assault, razor-sharp focus in his glowing amber eyes, muscles coiled with explosive power, "
                "shrouded in golden kinetic heat shimmer. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set before a colossal jagged dimensional fissure in deep space, revealing grotesque chitinous void swarms disintegrating "
                "into purple ash under supersonic shockwave punches in the distance. "
                "Illumination from eerie violet rift fissures and brilliant sun-gold kinetic bursts, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (115, 118),
            "title": ["ANCIENT TITAN FORGE", "MARROW TEMPERING"],
            "fallback_color": (40, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust enduring extreme physical refinement, calm unyielding expression, sweat on his brow, "
                "golden runic meridians pulsing brightly beneath his skin and across his shoulders. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside an ancient subterranean primordial forge chamber, revealing rivers of molten cosmic metal "
                "and floating runic anvil stones in the distance. "
                "Illumination from roaring magma currents and radiant golden bone-marrow resonance, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (119, 123),
            "title": ["DREADNOUGHT SMASH", "GALACTIC WARLORD CLASH"],
            "fallback_color": (35, 20, 25),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust executing a devastating forward strike, dark windswept hair, intense warrior gaze, "
                "an outstretched fist unleashing an immense compressed kinetic blast wave. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set across the burning hull of an extraterrestrial battle dreadnought, revealing heavily armored alien warlord captains "
                "buckling under insurmountable kinetic shockwaves in the distance. "
                "Illumination from exploding starship artillery and blinding white-hot concussive energy, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (124, 127),
            "title": ["DEFENSIVE BASTION", "DELVER SANCTUARY"],
            "fallback_color": (20, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust acting as Earth's sovereign guardian, calm dignified posture, piercing sun-gold eyes, "
                "holding two fists together to project a colossal translucent golden aegis barrier. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set overlooking an expanding human forward colony city, revealing allied delvers cheering behind his protective dome "
                "while hostile alien bombardments detonate harmlessly against the shield in the distance. "
                "Illumination from shimmering golden kinetic hex-shields and sunrise-lit settlement towers, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (128, 131),
            "title": ["SPATIAL DOMAIN", "DISINTEGRATION NULLIFIED"],
            "fallback_color": (25, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of an enlightened master pugilist, sharp facial planes, confident composed smirk, "
                "surrounded by an expanding domain field of pure kinetic force that bends incoming energy attacks. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a crumbling planar arena, "
                "revealing an arrogant high-tier alien sorcerer's spatial disintegration beams bending and dissipating harmlessly against Jack's aura in the distance. "
                "Illumination from warped neon-cyan spatial ripples and dense golden fist halos, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (132, 135),
            "title": ["SUPERSONIC RAMPAGE", "SECTOR ARENA FINALS"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust mid-air after a supersonic leap, dark hair whipping back, razor-sharp predatory eyes, "
                "wrapped hands wreathed in crackling gold-and-white kinetic lightning. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a grand galactic sector arena floating above an alien capital planet, revealing the sector's reigning "
                "champion cratered into the shattered bedrock arena floor in the distance. "
                "Illumination from blinding orbital floodlights and roaring electric-gold shockwave discharges, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (136, 140),
            "title": ["SECTOR WARLORD SOVEREIGN", "THE UNBROKEN PATH"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Jack Rust at the pinnacle of galactic brawler mastery, calm invincible presence, commanding amber-gold pupils, "
                "wearing battle-worn dark combat pants and an open vest revealing dense glowing runic meridians across his muscular torso. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set atop a soaring observation spire overlooking sprawling "
                "united planetary sectors, revealing Brock resting loyally beside him and Earth's starfleet ascending into the cosmos under a breathtaking aurora sky. "
                "Illumination from brilliant auroras of sunrise gold, radiant cyan system matrices, and deep-blue starlight, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))