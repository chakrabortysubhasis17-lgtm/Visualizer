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

BUILD_DIR = "build_five_element_overlord_51_100"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "five-element-overlord-i-can-upgrade-everything",
    "start_url": "https://freewebnovel.com/novel/five-element-overlord-i-can-upgrade-everything/chapter-51",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "Five Element Overlord",

    # Concurrency & Synthesis Parameters
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_five_element_overlord_51_100.mp3",
    "final_video": "final_five_element_overlord_51_100.mp4",
    "cover_image": "cover_five_element_overlord_51_100.jpg",
    "timestamps_file": "youtube_timestamps_five_element_overlord_51_100.txt",
    "subtitles_file": "subtitles_five_element_overlord_51_100.srt",
    "payload_file": "youtube_upload_payload_five_element_overlord_51_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "DIVINE UPGRADE SYSTEM & FIVE-ELEMENT DOMINANCE! [Ch 51-100] | Five Element Overlord Xianxia Audiobook",
    "tags": [
        "Five Element Overlord", "I Can Upgrade Everything", "Xianxia Audiobook", 
        "Cultivation Audiobook", "LitRPG Audiobook", "System Cultivation", 
        "Progression Fantasy", "Wuxia Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to the 50-Chapter Marathon of 'Five Element Overlord: I Can Upgrade Everything' (Chapters 51 to 100)!\n\n"
        "Witness the ultimate fusion of Daoist five-element cultivation and an omnipotent upgrade interface. "
        "From ascending through sect rankings and upgrading mundane spirit treasures into peerless divine artifacts, "
        "to crushing arrogant young masters and surviving forbidden realm trials, every step leads closer to cosmic hegemony.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, multi-voice dramatization).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system prompts, and status alerts).\n"
        "🎨 VISUAL ENGINE: 4K 3D Xianxia Visual Artworks + 15s Animated Outro.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 MARATHON ARC BREAKDOWN:\n"
        "• Ch 051 - 060: Sect Tournament & Artifact Evolution\n"
        "• Ch 061 - 070: Five Element Core Breakthrough\n"
        "• Ch 071 - 080: Ancient Mystic Realm Exploration\n"
        "• Ch 081 - 090: Slaying Primordial Spirit Beasts\n"
        "• Ch 091 - 100: Overlord Tribulation & Peak Dominance\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited, dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for upcoming marathons!\n\n"
        "#FiveElementOverlord #XianxiaAudiobook #Cultivation #LitRPG #ProgressionFantasy #AudiobookMarathon #BeingABong"
    ),

    # Visual Prompts (5 blocks, 10 chapters each)
    "blocks": [
        {
            "index": 1, "range": (51, 60),
            "title": ["SECT TOURNAMENT", "ARTIFACT EVOLUTION"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D fantasy portrait of a confident young male Daoist cultivator in white and gold immortal robes, "
                "holding a floating ancient bronze mirror glowing with fiery golden runes and upgrade light rings. "
                "Floating stone martial arena background with banners and sect pavilions, crisp detailed facial features, "
                "dynamic particle sparks, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (61, 70),
            "title": ["FIVE ELEMENT CORE", "DAN breakthrough"],
            "fallback_color": (15, 30, 45),
            "prompt": (
                "Cinematic 3D fantasy portrait of a powerful young cultivator meditating cross-legged while five colored elemental rings "
                "(gold, green, blue, red, brown) swirl around his chest into a concentrated celestial orb. "
                "Ancient stone cultivation cave background with glowing spiritual spirit stones, ethereal lighting, "
                "crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (71, 80),
            "title": ["MYSTIC REALM", "FORBIDDEN RUINS"],
            "fallback_color": (20, 40, 25),
            "prompt": (
                "Cinematic 3D fantasy portrait of a determined male cultivator standing at the entrance of overgrown ancient temple ruins, "
                "drawing a glowing five-element spirit sword surrounded by floating jade talismans. "
                "Misty mystical forest valley background with glowing bioluminescent plants, crisp detailed facial features, "
                "realistic clothing textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (81, 90),
            "title": ["BEAST SLAYING", "DIVINE EXTRACTION"],
            "fallback_color": (40, 15, 20),
            "prompt": (
                "Cinematic 3D fantasy portrait of the fierce male cultivator channeling elemental lightning and flame through his palm, "
                "standing over the fallen silhouette of a colossal scaled dragon beast in a volcanic canyon. "
                "Smoke, embers, and floating spirit cores, intense dramatic lighting, crisp detailed facial features, "
                "realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (91, 100),
            "title": ["OVERLORD TRIBULATION", "PEAK DOMINANCE"],
            "fallback_color": (30, 15, 45),
            "prompt": (
                "Cinematic 3D fantasy portrait of the ascending Five Element Overlord surrounded by swirling heavenly lightning clouds "
                "and an omnipotent glowing translucent status matrix with ancient golden seal script. "
                "Majestic mountain peak background under a cosmic starry sky, regal immortal armor, crisp detailed facial features, "
                "realistic skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
