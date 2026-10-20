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

# Seamless fallback supporting both single-key and multi-key JSON structures
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
    """Automatically removes empty or corrupt dummy files from earlier connection aborts."""
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
        print(f"[Pre-Flight Cleanup] [✓] Purged {removed} corrupt placeholder cache files to guarantee clean scraping.", flush=True)

BUILD_DIR = "build_harem_training_system_251_300"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "harem-training-system-every-girl-i-train-makes-me-stronger",
    "start_url": "https://freewebnovel.com/novel/harem-training-system-every-girl-i-train-makes-me-stronger/chapter-251",
    "start_chapter": 251,
    "end_chapter": 300,
    "default_topic": "Arc",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_harem_training_system_251_300.mp3",
    "final_video": "final_harem_training_system_251_300.mp4",
    "cover_image": "cover_harem_training_system_251_300.jpg",
    "timestamps_file": "youtube_timestamps_harem_training_system_251_300.txt",
    "subtitles_file": "subtitles_harem_training_system_251_300.srt",
    "payload_file": "youtube_upload_payload_harem_training_system_251_300.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "DIVINE SECT TRAINING ASCENSION! MULTI-DISCIPLE BOND BREAKTHROUGH [Ch 251-300] | Progression Fantasy LitRPG Marathon",
    "tags": [
        "Harem Training System", "Every Girl I Train Makes Me Stronger", "Progression Fantasy",
        "Cultivation LitRPG", "System Audiobook", "Audiobook Marathon", "Full Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Pushing beyond the boundaries of provincial kingdoms, our master trainer enters the Great Continental Sects!\n\n"
        "With his Training System unlocking higher-tier resonance feedback loops, every breakthrough achieved by his talented "
        "disciples directly multiplies his own physical and spiritual might. Guiding prodigies across sword mastery, heavenly alchemy, "
        "and primordial beast taming, he neutralizes scheming elder councils, conquers ancient heritage chambers, and establishes "
        "his academy as the continent's apex sovereign institution.\n\n"
        "Welcome to Chapters 251 to 300 of 'Harem Training System: Every Girl I Train Makes Me Stronger' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 251: Continental Sect Registration: Testing the Latent Meridian Potentials\n"
        "• Ch 257: The Heavenly Sword Maiden's Breakthrough: Quad-Feedback Strength Amplification\n"
        "• Ch 264: Sovereign Cauldron Refinement: Mastering Nine-Pattern Golden Core Elixirs\n"
        "• Ch 271: Elder Council Infiltration: Shattering Extortionate Disciple Contracts\n"
        "• Ch 278: Beast Empress Soul Synchronization: Taming the Mythic Azure Drake\n"
        "• Ch 285: Grand Inter-Sect Tournament: Sweeping Rivals with Flawless Team Formations\n"
        "• Ch 292: Primordial Heritage Sanctum: Unlocking the Supreme Ancestral Domain Array\n"
        "• Ch 300: Apex Continental Coronation: Standing as the Unrivaled Master of the Realm\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#HaremTrainingSystem #EveryGirlITrainMakesMeStronger #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (251, 255),
            "title": ["CONTINENTAL SECT", "MERIDIAN TESTING"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of a composed young martial master inspecting a glowing crystal training orb, calm sharp eyes, "
                "wearing high-ranking dark blue martial robes with gold embroidery. Set inside an ancient grand marble training courtyard, "
                "revealing disciplined female disciples practicing elegant sword stances in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (256, 260),
            "title": ["SWORD MAIDEN", "FEEDBACK RESONANCE"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the master standing alongside a talented swordswoman disciple, proud supportive expression, "
                "surrounded by faint golden system aura rings. Set atop a mountain peak under a clear azure sky, "
                "revealing twin sword slashes carving light trails across the clouds in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (261, 265),
            "title": ["HEAVENLY CAULDRON", "PILL REFINEMENT"],
            "fallback_color": (40, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of the master guiding an alchemist disciple near a bronze cauldron, focused analytical posture, "
                "warm amber firelight illuminating his features. Set inside a lantern-lit alchemical pavilion, "
                "revealing glowing golden medicinal pills hovering in mid-air in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (266, 270),
            "title": ["COUNCIL CHALLENGE", "AUTHORITY RECLAIMED"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of the master holding a stamped jade sect decree, confident calm smirk, "
                "hands resting on a polished mahogany table. Set in an opulent high-ceilinged council chamber under hanging silk banners, "
                "revealing yielding aristocratic elders lowering their heads in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (271, 275),
            "title": ["BEAST SANCTUARY", "AZURE DRAKE BOND"],
            "fallback_color": (15, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of the master observing a beast-taming disciple connect mana with a majestic winged creature, serene reassuring smile, "
                "breeze ruffling his hair. Set in a lush misty forest clearing filled with glowing spirit flowers, "
                "revealing a friendly azure drake lowering its head respectfully in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (276, 280),
            "title": ["SOUL DOMAIN", "HARMONIC FIELD"],
            "fallback_color": (35, 15, 40),
            "prompt": (
                "Cinematic 3D portrait of the master in meditative concentration, powerful commanding aura, "
                "three concentric rings of cyan, emerald, and gold mana rotating steadily around him. "
                "Set inside a quiet cavern shrine with glowing mineral walls, revealing seated disciples harmonizing their energy in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (281, 285),
            "title": ["SECT TOURNAMENT", "DISCIPLE TRIUMPH"],
            "fallback_color": (20, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the master watching from a grand pavilion terrace, relaxed triumphant posture, "
                "wearing ceremonial embroidered master robes. Set overlooking a massive stone martial colosseum filled with cheering crowds, "
                "revealing his lead disciple raising a gleaming tournament trophy in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (286, 290),
            "title": ["HERITAGE VAULT", "PRIMORDIAL TRIAL"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of the master pointing two fingers toward an ancient stone seal, sharp decisive glare, "
                "runic light reflecting off his sleeves. Set inside a subterranean granite ruin with carved dragon columns, "
                "revealing ancient barrier gates unlocking and parting in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (291, 295),
            "title": ["STARFALL ARRAY", "SYNCHRONIZED POWER"],
            "fallback_color": (25, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of the master raising an ornate jade talisman, regal commanding authority, "
                "eyes shimmering with purple starlight. Set beneath a night sky lit by a shimmering celestial formation, "
                "revealing protective energy barriers shielding a vast mountain sect in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (296, 300),
            "title": ["APEX CORONATION", "SUPREME MASTER"],
            "fallback_color": (20, 15, 45),
            "prompt": (
                "Cinematic 3D portrait of the supreme academy master seated upon an elevated carved throne, serene invincible expression, "
                "wearing regal platinum robes with dark blue sashes. Set in the grand summit hall overlooking boundless mountain peaks under golden sunrise, "
                "revealing grateful disciples and allied elders standing in loyal formation in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
