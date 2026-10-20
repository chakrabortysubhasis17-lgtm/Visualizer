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

# Seamless credential resolution across single and multi-account configurations
gemini_key = creds.get("gemini_api_key")
if not gemini_key and creds.get("gemini_api_keys"):
    for k in creds["gemini_api_keys"]:
        if k and not k.startswith("PASTE_") and not k.startswith("YOUR_"):
            gemini_key = k
            break
gemini_key = gemini_key or os.environ.get("GEMINI_API_KEY", "")

cf_id = creds.get("cloudflare_account_id")
cf_token = creds.get("cloudflare_api_token")
if (not cf_id or not cf_token) and creds.get("cloudflare_accounts"):
    for acc in creds["cloudflare_accounts"]:
        if isinstance(acc, dict) and acc.get("account_id") and not acc.get("account_id").startswith("PASTE_"):
            cf_id = cf_id or acc.get("account_id")
            cf_token = cf_token or acc.get("api_token")
            break
cf_id = cf_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
cf_token = cf_token or os.environ.get("CLOUDFLARE_API_TOKEN", "")

def purge_corrupt_cache(build_dir: str):
    """Purges placeholder dummy files from earlier connection dropouts."""
    if not os.path.exists(build_dir):
        return
    removed = 0
    for fname in os.listdir(build_dir):
        if fname.startswith("ch_") and fname.endswith("_staged.json"):
            fpath = os.path.join(build_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                rows = data.get("rows", [])
                if len(rows) < 8 or any("Exposition details continue" in r.get("text", "") for r in rows):
                    os.remove(fpath)
                    removed += 1
            except Exception:
                try:
                    os.remove(fpath)
                    removed += 1
                except OSError:
                    pass
    if removed > 0:
        print(f"[Pre-Flight Cleanup] [✓] Purged {removed} placeholder cache files to guarantee clean scraping.", flush=True)

BUILD_DIR = "build_starting_with_sss_rank_goddess_201_250"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "starting-with-an-sss-rank-goddess-summon",
    "start_url": "https://freewebnovel.com/novel/starting-with-an-sss-rank-goddess-summon/chapter-201",
    "start_chapter": 201,
    "end_chapter": 250,
    "default_topic": "SSS Goddess Summon",

    # Concurrency Settings
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_starting_with_sss_rank_goddess_201_250.mp3",
    "final_video": "final_starting_with_sss_rank_goddess_201_250.mp4",
    "cover_image": "cover_starting_with_sss_rank_goddess_201_250.jpg",
    "timestamps_file": "youtube_timestamps_starting_with_sss_rank_goddess_201_250.txt",
    "subtitles_file": "subtitles_starting_with_sss_rank_goddess_201_250.srt",
    "payload_file": "youtube_upload_payload_starting_with_sss_rank_goddess_201_250.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "DIVINE GODDESS REALM CONQUEST! SSS-RANK SUMMON EVOLUTION [Ch 201-250] | Progression Fantasy LitRPG Marathon",
    "tags": [
        "Starting With An SSS-Rank Goddess Summon", "SSS Rank Goddess Summon", "Progression Fantasy",
        "Goddess Summoning", "LitRPG Audiobook", "System Audiobook", "Audiobook Marathon", "Full Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Marching deep into the contested divine battlegrounds, our summoner unlocks the ancient primordial resonance tiers!\n\n"
        "With each contract bonded to his supreme SSS-rank goddesses, their synergistic battle arrays unleash overwhelming elemental "
        "and spatial domains. Shattering the ambushes of hostile pantheons, conquering abyss trial vaults, and claiming primordial "
        "divine sparks, he proves that true dominion belongs to those who stand shoulder-to-shoulder with celestial deities.\n\n"
        "Welcome to Chapters 201 to 250 of 'Starting with an SSS-Rank Goddess Summon' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 201: Boundary Gate of the Divine Sanctum: Crossing the Holy Meridian Line\n"
        "• Ch 207: Valkyrie Vanguard Breakthrough: Dual-Element Resonant Blade Storm\n"
        "• Ch 214: Underworld Sovereign Cavern: Breaking the Abyssal Contract Seals\n"
        "• Ch 221: Celestial Council Confrontation: Nullifying Extortionate Tribute Demands\n"
        "• Ch 228: Archangel Synthesis Matrix: Awakening the Ten-Winged Radiant Domain\n"
        "• Ch 235: Ancient Titan Heritage Trial: Shattering the Earth Core Labyrinth\n"
        "• Ch 242: Primordial Spark Convergence: Triple Goddess Combined Resonance\n"
        "• Ch 250: Inter-Realm Throne Coronation: Sovereign Master of the Holy Legion\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#StartingWithAnSSSRankGoddessSummon #SSSRankGoddessSummon #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (201, 205),
            "title": ["DIVINE SANCTUM", "BOUNDARY PASS"],
            "fallback_color": (25, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of a determined young summoner master standing with glowing golden summoning glyphs floating around his hands, "
                "sharp intelligent eyes, dressed in dark armored summoner robes with silver trims. Set before an enormous carved marble portal on a mountain peak, "
                "revealing a radiant armored Valkyrie goddess hovering with radiant golden wings in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (206, 210),
            "title": ["VALKYRIE WRATH", "BLADE TEMPEST"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of the summoner coordinating battle tactics, steady calm leadership expression, "
                "surrounded by faint blue kinetic mana barriers. Set in a desolate battlefield under a stormy twilight sky, "
                "revealing twin glowing sword arcs cleaving through enemy shadow beasts in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (211, 215),
            "title": ["ABYSSAL VAULT", "SEAL DESTRUCTION"],
            "fallback_color": (35, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of the summoner extending his palm to shatter a purple runic barrier, concentrated intense focus, "
                "ancient purple and gold runes reflecting off his armor plates. Set in a subterranean cavern shrine surrounded by jagged crystalline formations, "
                "revealing an ancient obsidian reliquary opening in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (216, 220),
            "title": ["COUNCIL TRIBUNAL", "DECREE DEVIANCE"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of the summoner confronting seated celestial elders, defiant unyielding smirk, "
                "holding a burning gold parchment contract. Set inside an opulent high-ceilinged divine council chamber lined with glowing alabaster pillars, "
                "revealing divine inquisitors lowering their weapons in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (221, 225),
            "title": ["HOLY ARCHANGEL", "RADIANT MATRIX"],
            "fallback_color": (40, 35, 20),
            "prompt": (
                "Cinematic 3D portrait of the summoner standing beside a serene celestial goddess draped in white and gold silk, "
                "supportive proud expression, surrounded by gentle shimmering starlight motes. Set in a heavenly floating terrace gardens overlooking infinite clouds, "
                "revealing concentric light rings warding the citadel in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (226, 230),
            "title": ["TITAN HERITAGE", "EARTH CORE LABYRINTH"],
            "fallback_color": (40, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of the summoner touching a glowing monolithic basalt core, analytical tactical focus, "
                "orange magma veins illuminating his profile. Set inside a vast subterranean maze with massive granite arches, "
                "revealing rumbling stone golems awakening from slumber in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (231, 235),
            "title": ["PRIMORDIAL SPARK", "TRIPLE HARMONY"],
            "fallback_color": (30, 15, 45),
            "prompt": (
                "Cinematic 3D portrait of the summoner in profound meditation with three elemental summoning orbs circling his chest, "
                "calm peerless presence, prismatic light refracting across his robes. Set inside a tranquil astral sanctum floor of polished lapis lazuli, "
                "revealing three goddess avatars synchronizing their domain fields in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (236, 240),
            "title": ["ASTRAL LEGION", "FRONTLINE RALLY"],
            "fallback_color": (20, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the summoner drawing a ceremonial silver summoning blade, commanding authoritative glare, "
                "banner fabric whipping in the wind behind him. Set upon a high fortress rampart under starry celestial skies, "
                "revealing thousands of illuminated armored soldiers assembled in battle formation in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (241, 245),
            "title": ["DIVINE TRIBULATION", "CELESTIAL SHIELD"],
            "fallback_color": (25, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of the summoner deploying a massive translucent hexagonal barrier array, fearless resolute posture, "
                "eyes reflecting blinding azure lightning strikes. Set atop a desolate plateau during a cosmic thunderstorm, "
                "revealing descending divine thunderbolts shattering harmlessly against the energy ward in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (246, 250),
            "title": ["SOVEREIGN ENTHRONEMENT", "CELESTIAL REIGN"],
            "fallback_color": (20, 15, 40),
            "prompt": (
                "Cinematic 3D portrait of the supreme summoner seated upon an elevated carved throne of gold and star-stone, "
                "serene invincible gaze, wearing regal dark-violet robes with platinum sashes. Set in an expansive cosmic cathedral overlooking boundless celestial realms under dawn light, "
                "revealing multiple loyal goddesses and divine emissaries kneeling respectfully in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
