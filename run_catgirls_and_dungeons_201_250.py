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

BUILD_DIR = "build_catgirls_and_dungeons_201_250"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "catgirls-and-dungeons-yuri",
    "start_url": "https://freewebnovel.com/novel/catgirls-and-dungeons-yuri/chapter-201",
    "start_chapter": 201,
    "end_chapter": 250,
    "default_topic": "Catgirls and Dungeons",

    # Concurrency Settings
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_catgirls_and_dungeons_201_250.mp3",
    "final_video": "final_catgirls_and_dungeons_201_250.mp4",
    "cover_image": "cover_catgirls_and_dungeons_201_250.jpg",
    "timestamps_file": "youtube_timestamps_catgirls_and_dungeons_201_250.txt",
    "subtitles_file": "subtitles_catgirls_and_dungeons_201_250.srt",
    "payload_file": "youtube_upload_payload_catgirls_and_dungeons_201_250.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "ABYSSAL DUNGEON DEPTHS & ULTIMATE ROMANCE! [Ch 201-250] | Yuri Fantasy LitRPG Audiobook Marathon",
    "tags": [
        "Catgirls and Dungeons", "Yuri Audiobook", "Progression Fantasy", "Dungeon Crawler",
        "LitRPG Audiobook", "System Audiobook", "Audiobook Marathon", "Full Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Descending into the treacherous abyss of the lower dungeon tiers, survival demands absolute trust and affection!\n\n"
        "Facing terrifying new floor lords, environmental hazards, and rival adventuring parties, the party relies on their "
        "combined combat synergy and growing romantic devotion. With powerful class awakenings and legendary gear drops, "
        "they conquer the darkest corners of the labyrinth together.\n\n"
        "Welcome to Chapters 201 to 250 of 'Catgirls and Dungeons (Yuri)' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 201: Lower Abyss Entry: Navigating the Toxic Void Zones\n"
        "• Ch 208: Catgirl Evolution: Unlocking Legendary Feline Beast Traits\n"
        "• Ch 215: Rival Party Ambush: Defending Territory in the Labyrinth\n"
        "• Ch 222: Deep Sanctuary Respite: Emotional Vulnerability and Romance\n"
        "• Ch 229: Abyssal Dragon Whelp Subjugation: Securing Rare Dragon Scales\n"
        "• Ch 236: Sanctuary Town Establishment: Securing a Safe Haven\n"
        "• Ch 243: Floor 250 Boss Prelude: Preparing for the Ultimate Trial\n"
        "• Ch 250: Conquering the Abyss Threshold\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#CatgirlsAndDungeons #YuriAudiobook #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (201, 205),
            "title": ["LOWER ABYSS", "TOXIC VOID ZONE"],
            "fallback_color": (15, 20, 40),
            "prompt": (
                "Cinematic 3D fantasy portrait of adventurous explorers navigating a misty glowing purple abyss chasm wearing protective filtering gear, "
                "cautious focused expressions, magical barrier shields casting soft blue light. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (206, 210),
            "title": ["FELINE ASCENSION", "LEGENDARY TRAITS"],
            "fallback_color": (25, 20, 50),
            "prompt": (
                "Cinematic 3D fantasy portrait of a majestic catgirl warrior undergoing a mystical skill evolution surrounded by golden aura wisps, "
                "proud confident expression, glowing ethereal cat ears and tail. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (211, 215),
            "title": ["AMBUSH DEFENSE", "TACTICAL STAND"],
            "fallback_color": (35, 15, 25),
            "prompt": (
                "Cinematic 3D fantasy portrait of companions holding firm against a surprise raid in a rocky corridor, fierce determined expressions, "
                "sparkling magic spells clashing in mid-air. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (216, 220),
            "title": ["SANCTUARY REFUGE", "HEARTWARMING ROMANCE"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D fantasy portrait of two female companions sharing a deeply affectionate tender moment in a hidden alcove, "
                "loving gazes, soft magical lantern illumination. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (221, 225),
            "title": ["DRAGON WHELP", "SCALED SUBJUGATION"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D fantasy portrait of the party facing a ferocious small winged dragon whelp inside a volcanic obsidian cavern, "
                "dynamic combat ready postures, glowing embers floating around. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (226, 230),
            "title": ["SAFE HAVEN", "TOWN FOUNDATION"],
            "fallback_color": (20, 30, 35),
            "prompt": (
                "Cinematic 3D fantasy portrait of the adventurer group inspecting the blueprint construction of a fortified underground outpost, "
                "optimistic hopeful smiles, torchlit stone walls background. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (231, 235),
            "title": ["SKILL FUSION", "SYNERGY SURGE"],
            "fallback_color": (30, 15, 45),
            "prompt": (
                "Cinematic 3D fantasy portrait of companions performing a synchronized dual-element magic incantation, concentrated intense focus, "
                "swirling azure and crimson energy vortex. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (236, 240),
            "title": ["ABYSSAL HORDE", "DEFENSIVE LINE"],
            "fallback_color": (25, 25, 45),
            "prompt": (
                "Cinematic 3D fantasy portrait of the party standing side-by-side holding a wide stone bottleneck against encroaching monster waves, "
                "unwavering brave expressions. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (241, 245),
            "title": ["BOSS PRELUDE", "ULTIMATE TRIAL"],
            "fallback_color": (20, 20, 45),
            "prompt": (
                "Cinematic 3D fantasy portrait of the companions checking their gear before stepping through massive bronze double doors, "
                "solemn focused determination, dim magical lighting. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (246, 250),
            "title": ["ABYSS CONQUEST", "TRIUMPHANT VICTORS"],
            "fallback_color": (15, 15, 35),
            "prompt": (
                "Cinematic 3D fantasy portrait of the victorious adventurer party raising their glowing weapons in triumph beneath a radiant celestial skylight "
                "deep within the dungeon core, joyful emotional embrace. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
