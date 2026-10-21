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

# Credential resolution with multi-key/account fallback
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

BUILD_DIR = "build_national_fate_marriage_251_300"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "national-fate-marriage-the-elf-queen-is-pregnant-at-the-start",
    "start_url": "https://mtl-novel.com/novel/national-fate-marriage-the-elf-queen-is-pregnant-at-the-start/chapter-251-the-aloof-empress-instantly-turns-into-a-foodie-who-can-resist-this-contrast/",
    "start_chapter": 251,
    "end_chapter": 300,
    "default_topic": "National Fate Marriage",

    # Concurrency Settings
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_national_fate_marriage_251_300.mp3",
    "final_video": "final_national_fate_marriage_251_300.mp4",
    "cover_image": "cover_national_fate_marriage_251_300.jpg",
    "timestamps_file": "youtube_timestamps_national_fate_marriage_251_300.txt",
    "subtitles_file": "subtitles_national_fate_marriage_251_300.srt",
    "payload_file": "youtube_upload_payload_national_fate_marriage_251_300.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "ALOOF EMPRESS TURNS FOODIE! NATIONAL FATE SPOUSE BLESSINGS [Ch 251-300] | Fantasy Romance Progression Audiobook",
    "tags": [
        "National Fate Marriage", "The Elf Queen Is Pregnant At The Start", "National Fate",
        "Progression Fantasy", "LitRPG Audiobook", "System Audiobook", "Audiobook Marathon", "Full Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "In the high-stakes arena of the National Fate Marriage game, love, divine cuisine, and kingdom rewards reign supreme!\n\n"
        "When our chosen champion introduces heavenly modern culinary arts to the imperial courts, even the coldest, most aloof "
        "Empress cannot resist the adorable temptation of gourmet comfort food. Between caring for the expectant Elf Queen, harmonizing "
        "inter-species palace politics, and securing astronomical territory buffs for his homeland, domestic bliss and supreme "
        "national power march hand-in-hand.\n\n"
        "Welcome to Chapters 251 to 300 of 'National Fate Marriage: The Elf Queen Is Pregnant At The Start' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 251: Gourmet Diplomacy: The Aloof Empress Melts Over Divine Delicacies\n"
        "• Ch 257: National Fate System Dividend: Massive Lifespan & Resource Windfall\n"
        "• Ch 264: Imperial Garden Banquet: The Elf Queen and Empress Form an Unbreakable Bond\n"
        "• Ch 271: Foreign Player Sabotage: Crushing Infiltrators with Sovereign Dragon Qi\n"
        "• Ch 278: Ancestral Spirit Tree Attunement: Nurturing the Royal Heirs\n"
        "• Ch 285: The Empress's Secret Craving: Late-Night Royal Kitchen Escapades\n"
        "• Ch 292: Divine Beast Mount Taming: Securing the Celestial Qilin Chariot\n"
        "• Ch 300: Grand Imperial Inspection: Expanding the National Fate Domain\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#NationalFateMarriage #ElfQueenIsPregnant #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (251, 255),
            "title": ["GOURMET CONTRAST", "EMPRESS FEAST"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D romantic fantasy portrait of an elegant dignified Empress in regal white-and-gold imperial robes blushing adorably "
                "while tasting a steaming gourmet dish, eyes sparkling with delight. Seated beside a handsome, composed young male sovereign in dark silk robes, "
                "opulent candlelit palace banquet hall background. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (256, 260),
            "title": ["NATIONAL REWARD", "GOLDEN WIND FALL"],
            "fallback_color": (40, 30, 15),
            "prompt": (
                "Cinematic 3D fantasy portrait of the protagonist reviewing a glowing golden system rewards interface floating above his palm, "
                "confident reassuring smile, swirling pillars of golden national fortune qi ascending into the sky. Palace balcony setting overlooking a prosperous kingdom. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (261, 265),
            "title": ["ELF QUEEN HARMONY", "PALACE GARDENS"],
            "fallback_color": (20, 35, 25),
            "prompt": (
                "Cinematic 3D fantasy portrait of a graceful Elf Queen with shimmering silver hair and elegant pointed ears gently conversing with the imperial Empress, "
                "warm affectionate sisterly expressions, surrounded by blooming magical luminous flowers in an ancient imperial courtyard. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (266, 270),
            "title": ["ROYAL CONFECTIONS", "KITCHEN DELIGHTS"],
            "fallback_color": (30, 20, 25),
            "prompt": (
                "Cinematic 3D fantasy portrait of the protagonist plating exquisite glazed treats while the Empress watches with an eager, charming expectant look, "
                "warm ambient kitchen lantern glow illuminating the scene, steam curling softly from freshly baked delicacies. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (271, 275),
            "title": ["INTRUDER SUPPRESSION", "SOVEREIGN QI"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "Cinematic 3D fantasy portrait of the protagonist extending a single hand, authoritative commanding glare, "
                "a manifestation of translucent golden dragon qi crushing shadow assassin runes into the stone terrace floor. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (276, 280),
            "title": ["SPIRIT TREE BLESSING", "NURTURING LIGHT"],
            "fallback_color": (15, 30, 35),
            "prompt": (
                "Cinematic 3D fantasy portrait of the protagonist and the radiant Elf Queen standing together before a colossal glowing emerald World Tree, "
                "gentle tender gazes, swirling green life-energy particles providing blessings to their unborn child. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (281, 285),
            "title": ["MIDNIGHT SUPPER", "TENDER REVELATION"],
            "fallback_color": (25, 20, 40),
            "prompt": (
                "Cinematic 3D romantic fantasy portrait of the Empress caught red-handed indulging in a midnight sweet snack by the protagonist, "
                "flustered charming expression, wearing flowing casual silk night robes under warm moonlight streaming through palace windows. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (286, 290),
            "title": ["CELESTIAL QILIN", "DIVINE MOUNT"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D fantasy portrait of the protagonist petting the snout of a magnificent white Qilin with glowing golden scales and fiery hooves, "
                "calm fearless expression, royal guards observing in awe across a marble palace courtyard. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (291, 295),
            "title": ["FAMILY ACCORD", "IMPERIAL BLISS"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D fantasy portrait of the protagonist seated peacefully between the smiling Elf Queen and the content Empress on a plush silk pavilion divan, "
                "heartwarming peaceful expressions, afternoon golden sunlight casting soft amber shadows. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (296, 300),
            "title": ["GRAND INSPECTION", "REALM PROSPERITY"],
            "fallback_color": (20, 15, 45),
            "prompt": (
                "Cinematic 3D fantasy portrait of the supreme sovereign lord in imperial dark blue and gold robes standing at the summit of the palace gateway, "
                "invincible commanding posture, looking out over a flourishing fantasy metropolis bathed in glorious morning dawn light. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))