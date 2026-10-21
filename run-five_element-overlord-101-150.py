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

BUILD_DIR = "build_five_element_overlord_101_150"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "five-element-overlord-i-can-upgrade-everything",
    "start_url": "https://freewebnovel.com/novel/five-element-overlord-i-can-upgrade-everything/chapter-101",
    "start_chapter": 101,
    "end_chapter": 150,
    "default_topic": "Five Element Overlord",

    # Concurrency & Synthesis Parameters
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_five_element_overlord_101_150.mp3",
    "final_video": "final_five_element_overlord_101_150.mp4",
    "cover_image": "cover_five_element_overlord_101_150.jpg",
    "timestamps_file": "youtube_timestamps_five_element_overlord_101_150.txt",
    "subtitles_file": "subtitles_five_element_overlord_101_150.srt",
    "payload_file": "youtube_upload_payload_five_element_overlord_101_150.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "HEAVENLY DOMAIN AWAKENING & DIVINE REFINEMENT! [Ch 101-150] | Five Element Overlord Xianxia Audiobook",
    "tags": [
        "Five Element Overlord", "I Can Upgrade Everything", "Xianxia Audiobook", 
        "Cultivation Audiobook", "LitRPG Audiobook", "System Cultivation", 
        "Progression Fantasy", "Wuxia Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to the 50-Chapter Marathon of 'Five Element Overlord: I Can Upgrade Everything' (Chapters 101 to 150)!\n\n"
        "Having dominated the mortal provinces, our protagonist enters the central domain where ancient sects clash for supreme dominance. "
        "With the omnipotent upgrade interface unlocking sovereign-grade Dao blueprints, mundane spirit herbs evolve into divine longevity pills, "
        "and standard flying swords transform into world-cleaving primordial relics.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, multi-voice dramatization).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system prompts, and status alerts).\n"
        "🎨 VISUAL ENGINE: 4K 3D Xianxia Visual Artworks + 15s Animated Outro.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 MARATHON ARC BREAKDOWN:\n"
        "• Ch 101 - 110: Central Domain Arrival & Rank Ascension\n"
        "• Ch 111 - 120: Heavenly Court Relics & Dao Artifact Upgrade\n"
        "• Ch 121 - 130: Grand Sect Conclave & Five-Element Slaughter Array\n"
        "• Ch 131 - 140: Abyssal Rift & Void Fiend Decimation\n"
        "• Ch 141 - 150: Sovereign Law Mastery & Primordial Overlord Ascent\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited, dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for upcoming marathons!\n\n"
        "#FiveElementOverlord #XianxiaAudiobook #Cultivation #LitRPG #ProgressionFantasy #AudiobookMarathon #BeingABong"
    ),

    # Visual Prompts (5 blocks, 10 chapters each)
    "blocks": [
        {
            "index": 1, "range": (101, 110),
            "title": ["CENTRAL DOMAIN", "RANK ASCENSION"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D fantasy portrait of a majestic Daoist cultivator in navy-blue and platinum celestial armor, "
                "standing upon a hovering jade pavilion overlooking a vast glowing imperial mountain city. "
                "Floating spirit islands, soaring cranes, swirling five-element mist, crisp sharp facial features, "
                "detailed silk embroidery textures, volumetric golden sunlight, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (111, 120),
            "title": ["HEAVENLY COURT RELICS", "DAO UPGRADE"],
            "fallback_color": (35, 30, 15),
            "prompt": (
                "Cinematic 3D fantasy portrait of an experienced male cultivator hovering before a colossal ancient bronze furnace, "
                "channeling five elemental energy streams into a floating sacred pagoda that radiates blinding upgrade glyphs. "
                "Mystic forge background with floating spirit ore, swirling alchemical flames, intricate dragon engravings, "
                "dynamic particle illumination, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (121, 130),
            "title": ["SECT CONCLAVE", "FIVE-ELEMENT ARRAY"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "Cinematic 3D fantasy portrait of a dominant cultivator surrounded by five gigantic spectral elemental blades "
                "(fire, water, wood, earth, metal) hovering above a massive cracked marble battle arena. "
                "Stormy sky filled with purple thunderbolts, billowing dark robes with glowing runic trims, "
                "commanding expression, dynamic energy ripples, crisp fine detail, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (131, 140),
            "title": ["ABYSSAL RIFT", "VOID DECIMATION"],
            "fallback_color": (15, 10, 25),
            "prompt": (
                "Cinematic 3D fantasy portrait of the cultivator unleashing a blinding five-colored beam of annihilation from his open palm "
                "into a shattered obsidian void rift crawling with shadowy demonic monstrosities. "
                "Dimensional tear effects, floating black crystals, radiant elemental contrast, determined fierce gaze, "
                "ultra-fine hair and armor details, dramatic cinematic lighting, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (141, 150),
            "title": ["SOVEREIGN LAW", "PRIMORDIAL ASCENT"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D fantasy portrait of the Supreme Five-Element Overlord seated upon a throne of condensed Daoist law seals, "
                "a divine elemental halo orbiting behind his head beneath a swirling cosmic galaxy. "
                "Translucent golden system upgrade screens floating in the air, regal immortal presence, intricate divine robes, "
                "crisp photorealistic rendering, volumetric rim lighting, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
