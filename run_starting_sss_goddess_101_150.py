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
    "novel_slug": "starting-with-an-sss-rank-goddess-summon",
    "start_url": "https://freewebnovel.com/novel/starting-with-an-sss-rank-goddess-summon/chapter-101",
    "start_chapter": 101,
    "end_chapter": 140,
    "default_topic": "SSS Goddess Summon",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_starting_sss_goddess_101_150",
    "final_audio": "output_starting_sss_goddess_101_150.mp3",
    "final_video": "final_starting_sss_goddess_101_150.mp4",
    "cover_image": "cover_starting_sss_goddess_101_150.jpg",
    "timestamps_file": "youtube_timestamps_starting_sss_goddess_101_150.txt",
    "subtitles_file": "subtitles_starting_sss_goddess_101_150.srt",
    "payload_file": "youtube_upload_payload_starting_sss_goddess_101_150.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "THIRD SSS-RANK GODDESS UNLOCKED! TRIPLE DIVINE DOMAIN DOMINATES WORLD SUMMIT [Ch 101-150] | LitRPG Progression Marathon",
    "tags": [
        "Starting with an SSS-rank Goddess Summon", "SSS Rank Goddess", "Summoner LitRPG",
        "Progression Fantasy Audiobook", "Overpowered MC", "Goddess Summoning", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Ascending to the global stage as international tensions flare, our protagonist unlocks his third mythical soul slot "
        "and summons the peerless Dragon Empress Goddess!\n\n"
        "With three SSS-Rank divine entities harmonized within his soul palace, the feedback resonance shatters mortal limits. "
        "Invited to the Global Hunter Summit, foreign superpower cartels, arrogant divine scions, and secret ruling oligarchies "
        "attempt to subjugate his growth with economic sanctions and covert assassin squadrons. In response, our summoner marches "
        "into apocalyptic Oceanic Calamity Rifts, obliterates deep-sea eldritch horrors, and deploys triple divine domain authority "
        "to force world leaders to bend the knee.\n\n"
        "Watch him conquer world-class trial dungeons, extract primordial origin cores, and secure undisputed global hegemony!\n\n"
        "Welcome to Chapters 101 to 150 of 'Starting with an SSS-rank Goddess Summon' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 101: Arrival at the Global Hunter Summit & Cold Disdain for Foreign Envoys\n"
        "• Ch 107: Unlocking the Third Soul Slot: Summoning the Primordial Dragon Empress\n"
        "• Ch 114: Oceanic Calamity Rift: Cleansing Subterranean Sea Horrors with Divine Light\n"
        "• Ch 121: Global Tournament Arena: Triple Goddess Synergy Dismantles Champion Teams\n"
        "• Ch 128: Ancient Abyssal Vault Raid: Harvesting Forgotten Continental Titan Relics\n"
        "• Ch 135: Triple Resonance Alignment: Achieving Omnipresent Telepathic Battle Command\n"
        "• Ch 142: Ambush of the World Cartel: Obliterating High-Tier Assassin Squadrons\n"
        "• Ch 150: Supreme Global Commander Coronation: Ascending the Orbital Citadel Throne\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#StartingWithAnSSSRankGoddessSummon #SSSRankGoddess #SummonerLitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Streamlined for Zero Generation Failures)
    "blocks": [
        {
            "index": 1, "range": (101, 104),
            "title": ["GLOBAL SUMMIT", "INTERNATIONAL ENVOYS"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of a young male summoner walking through a grand summit hall, confident calm expression, "
                "amber eyes gleaming, wearing tailored black commander robes with gold embroidery. "
                "Set inside a futuristic international assembly chamber, revealing foreign envoys watching with awe in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (105, 108),
            "title": ["THIRD GODDESS", "DRAGON EMPRESS DESCENT"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the summoner standing beside a glowing cyan ritual circle, composed focused posture, "
                "dark hair framing his defined brow. Set in an ancient mountain temple, revealing a radiant celestial dragon goddess descending in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (109, 112),
            "title": ["OCEANIC RIFT", "ABYSSAL SEA CRUSH"],
            "fallback_color": (15, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of the summoner in tactical combat stance, razor-sharp gaze, holding an azure crystal catalyst. "
                "Set at the edge of a raging oceanic abyssal whirlpool under stormy skies, revealing colossal sea monsters disintegrating under pillars of light in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (113, 116),
            "title": ["GLOBAL ARENA", "TOTAL SUPREMACY"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of the summoner standing with effortless nonchalance, hands folded behind his back, cool amused smirk. "
                "Set across the shattered tiles of a global dueling stadium, revealing defeated international champions on the ground in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (117, 120),
            "title": ["TITAN CORE", "ABYSSAL VAULT EXTRACTION"],
            "fallback_color": (20, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of the summoner inspecting an ancient floating core relic, watchful analytical gaze, "
                "wearing tactical leather gauntlets. Set inside an underground crystal vault, revealing massive sleeping guardian golems carved into stone walls in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (121, 124),
            "title": ["TRIPLE RESONANCE", "HARMONIC ALIGNMENT"],
            "fallback_color": (35, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of the summoner in seated meditation, serene commanding presence, "
                "three concentric rings of gold, crimson, and cyan light revolving around his shoulders. "
                "Set inside a floating sanctuary pavilion, revealing three divine goddess silhouettes guarding the perimeter in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (125, 128),
            "title": ["CARTEL AMBUSH", "SHADOW COUNTER-PURGE"],
            "fallback_color": (25, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of the summoner raising an open palm surrounded by dense kinetic shockwaves, fierce resolute expression, "
                "handsome chiseled jawline. Set along a mist-shrouded mountain pass at night, revealing covert syndicate mercenaries vanishing into bright light flashes in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (129, 132),
            "title": ["AERIAL FORTRESS", "BARRIER OVERWATCH"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of the summoner standing on high aerial fortress battlements, calm commanding posture, "
                "dark cloak fluttering in high-altitude wind. Set overlooking a sea of storm clouds at dusk, revealing glowing defensive barrier grids protecting floating cities in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (133, 136),
            "title": ["CALAMITY OVERLORD", "CELESTIAL EXECUTION"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of the summoner pointing two fingers forward with absolute authority, resolute sharp glare, "
                "fingers crackling with golden lightning. Set across a fractured volcanic rift under dark clouds, revealing an ancient calamity overlord crumbling under divine judgment in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (137, 140),
            "title": ["ORBITAL CITADEL", "GLOBAL SOVEREIGN"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of the Global Sovereign Summoner seated upon a grand crystal throne, serene invincible aura, "
                "eyes glowing with radiant golden starlight, wearing imperial commander robes. "
                "Set inside the summit council room of an orbital station overlooking the entire planet under an aurora sky in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
