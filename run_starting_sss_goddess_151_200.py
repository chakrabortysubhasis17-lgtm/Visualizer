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
    "start_url": "https://freewebnovel.com/novel/starting-with-an-sss-rank-goddess-summon/chapter-151",
    "start_chapter": 151,
    "end_chapter": 200,
    "default_topic": "SSS Goddess Summon",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,

    # Filepaths & Outputs
    "build_dir": "build_starting_sss_goddess_151_200",
    "final_audio": "output_starting_sss_goddess_151_200.mp3",
    "final_video": "final_starting_sss_goddess_151_200.mp4",
    "cover_image": "cover_starting_sss_goddess_151_200.jpg",
    "timestamps_file": "youtube_timestamps_starting_sss_goddess_151_200.txt",
    "subtitles_file": "subtitles_starting_sss_goddess_151_200.srt",
    "payload_file": "youtube_upload_payload_starting_sss_goddess_151_200.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "FOURTH SSS GODDESS AWAKENS! PRIMORDIAL STAR SOVEREIGN CRUSHES GOD-TIER INVADERS [Ch 151-200] | LitRPG Progression Marathon",
    "tags": [
        "Starting with an SSS-rank Goddess Summon", "SSS Rank Goddess", "Summoner LitRPG",
        "Progression Fantasy Audiobook", "Overpowered MC", "Goddess Summoning", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Breaking past the mortal barrier into the cosmic expanse, our summoner achieves an unprecedented divine resonance!\n\n"
        "Unlocking his fourth mythic soul slot, he summons the Primordial Starlight Empress Goddess, expanding his soul domain "
        "into an astral sanctuary. When extraterrestrial void legions and ancient god-tier pantheon scions descend upon Earth "
        "demanding planetary surrender, our summoner unleashes quad-divine authority to obliterate intergalactic warships, "
        "subjugate ancient stellar calamities, and establish Earth as a supreme sovereign nexus.\n\n"
        "Welcome to Chapters 151 to 200 of 'Starting with an SSS-rank Goddess Summon' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 151: The Starlight Altar Awakening: Unlocking the Fourth Mythic Soul Slot\n"
        "• Ch 157: Summoning the Primordial Astral Empress: Celestial Constellation Domain\n"
        "• Ch 164: Void Legion Invasion: Vaporizing Alien Dreadnoughts with Starlight Rays\n"
        "• Ch 172: Ancient Pantheon Scion Clash: Disarming Divine Spear Scions Effortlessly\n"
        "• Ch 179: Cosmic Core Extraction: Upgrading the Earth Defense Array to God-Tier\n"
        "• Ch 186: Quad-Goddess Resonance Alignment: Omnipresent Astral Field Command\n"
        "• Ch 193: Abyssal Rift Lord Counter-Purge: Cleansing Extraterrestrial Calamity Rifts\n"
        "• Ch 200: Supreme Interstellar Sovereign Coronation: Establishing the Terran Divine Realm\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#StartingWithAnSSSRankGoddessSummon #SSSRankGoddess #SummonerLitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Streamlined for Zero Generation Failures)
    "blocks": [
        {
            "index": 1, "range": (151, 155),
            "title": ["STARLIGHT ALTAR", "FOURTH SLOT AWAKENING"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the youthful male summoner standing before a massive floating celestial altar, focused confident gaze, "
                "eyes glowing with violet starlight, wearing tailored midnight-blue robes with platinum embroidery. "
                "Set inside a cosmic observatory sanctum overlooking swirling purple nebulas in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (156, 160),
            "title": ["FOURTH GODDESS", "ASTRAL EMPRESS DESCENT"],
            "fallback_color": (30, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of the summoner holding a radiant starlight catalyst, calm regal posture, "
                "dark hair framing defined aristocratic features. Set in a floating crystalline palace courtyard, "
                "revealing a luminous celestial starlight goddess descending surrounded by constellation rings in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (161, 165),
            "title": ["VOID INVASION", "INTERSTELLAR STRIKE"],
            "fallback_color": (15, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of the summoner raising an open palm surrounded by dense gravitational starlight beams, fierce resolute glare, "
                "wearing combat gauntlets engraved with celestial runes. Set on the exterior hull of an orbital citadel, "
                "revealing invading void dreadnoughts disintegrating under blinding starlight rays in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (166, 170),
            "title": ["PANTHEON SCION", "DIVINE DUEL"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of the summoner standing with effortless nonchalance, cool amused smirk, "
                "arms folded across a high-collared mantle. Set across a shattered astral battle arena in deep space, "
                "revealing an arrogant armored pantheon champion falling to his knees in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (171, 175),
            "title": ["COSMIC CORE", "CELESTIAL HARVEST"],
            "fallback_color": (20, 30, 40),
            "prompt": (
                "Cinematic 3D portrait of the summoner inspecting a pulsating cosmic star core, watchful analytical eyes, "
                "hands surrounded by translucent cyan barrier rings. Set inside an ancient stellar vault, "
                "revealing colossal sleeping celestial constructs embedded in stone walls in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (176, 180),
            "title": ["QUAD RESONANCE", "HARMONIC ALIGNMENT"],
            "fallback_color": (35, 15, 45),
            "prompt": (
                "Cinematic 3D portrait of the summoner in seated meditation, serene commanding presence, "
                "four concentric rings of gold, crimson, cyan, and violet starlight revolving around his shoulders. "
                "Set inside a floating astral pavilion, revealing four divine goddess silhouettes standing guard in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (181, 185),
            "title": ["DEFENSE GRID", "PLANETARY SHIELD"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of the summoner pointing two fingers forward, sharp decisive expression, "
                "golden aura rippling from his fingertips. Set on an orbital observation deck, "
                "revealing a vast geometric energy barrier enveloping planet Earth against a starry void in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (186, 190),
            "title": ["CALAMITY PURGE", "EXTRATERRESTRIAL CLEANSE"],
            "fallback_color": (40, 20, 20),
            "prompt": (
                "Cinematic 3D portrait of the summoner in high-speed tactical flight, razor-sharp gaze, "
                "starlight wings trailing glowing particles behind him. Set over a fractured planetary rift under burning auroras, "
                "revealing colossal eldritch void behemoths crumbling under pillars of radiant light in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (191, 195),
            "title": ["STELLAR CITADEL", "COUNCIL COMMAND"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of the summoner reviewing tactical star charts, composed commanding posture, "
                "wearing high-ranking imperial commander robes with golden epaulets. Set inside an expansive orbital command bridge, "
                "revealing allied galactic envoys bowing respectfully in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (196, 200),
            "title": ["INTERSTELLAR MONARCH", "DIVINE APEX"],
            "fallback_color": (20, 15, 50),
            "prompt": (
                "Cinematic 3D portrait of the Interstellar Sovereign Summoner seated upon a grand cosmic starlight throne, serene invincible aura, "
                "eyes glowing with radiant solar light, crowned with a floating starlight diadem. "
                "Set inside the grand summit pavilion overlooking conquered star systems and glowing nebulas in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
