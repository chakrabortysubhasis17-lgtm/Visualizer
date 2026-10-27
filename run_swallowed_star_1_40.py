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


def purge_corrupt_or_fallback_cache(build_dir: str):
    """
    Purges placeholder files, corrupt manifests, and rule-based fallback files
    staged during earlier runs without Gemini credentials.
    """
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

                is_dummy = len(rows) < 8 or any("Exposition details continue" in r.get("text", "") for r in rows)
                is_fallback_only = not any(r.get("speaker") not in ["Narrator", "Mc", "System"] for r in rows)

                if is_dummy or is_fallback_only:
                    os.remove(fpath)
                    removed += 1
            except Exception:
                try:
                    os.remove(fpath)
                    removed += 1
                except OSError:
                    pass
    if removed > 0:
        print(f"[Pre-Flight Cleanup] [OK] Purged {removed} invalid/fallback staged files. Gemini Director will parse cleanly.", flush=True)


BUILD_DIR = "build_swallowed_star_1_40"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "swallowed-star",
    "start_url": "https://freewebnovel.com/novel/swallowed-star/chapter-1",
    "start_chapter": 1,
    "end_chapter": 40,
    "default_topic": "Swallowed Star / Sci-Fi Cultivation / Post-Apocalyptic Earth / Spirit Reader / Martial Arts / Overpowered MC",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook
    "intro_hook": "Surviving on a post-apocalyptic Earth overrun by mutated apex beasts, one determined young martial artist unlocks the terrifying potential of an awakened Spirit Reader.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_swallowed_star_1_40.mp3",
    "final_video": "final_swallowed_star_1_40.mp4",
    "cover_image": "cover_swallowed_star_1_40.jpg",
    "timestamps_file": "youtube_timestamps_swallowed_star_1_40.txt",
    "subtitles_file": "subtitles_swallowed_star_1_40.srt",
    "payload_file": "youtube_upload_payload_swallowed_star_1_40.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # Post-Render Multilingual Subtitle Engine (15 Languages to build/subtitles/)
    "enable_subtitles": True,
    "subtitle_languages": [
        "de", "es", "pt", "ru", "hi", "bn", "ms", "tl", "fr", "fi", "ja", "pl", "ur", "ar", "vi"
    ],

    # YouTube Metadata
    "video_title": "Swallowed Star | Ch 1 - 40 Full Audio Novel Marathon | Rise of the Spirit Reader",
    "privacy_status": "unlisted",
    "tags": [
        "Swallowed Star", "Swallowed Star Audiobook", "Luo Feng", "Sci-Fi Cultivation",
        "Post Apocalyptic", "Spirit Reader", "Martial Arts Audiobook", "Audiobook Marathon",
        "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the complete opening marathon of 'Swallowed Star' (Chapters 1 to 40) — The Awakening of Luo Feng.\n\n"
        "On a ravaged Earth reborn through catastrophe, mutated beasts roam outside heavily fortified headquarter cities. "
        "Luo Feng, a humble student driven to protect his family, steps onto the brutal path of a martial fighter and discovers "
        "the rarest, most lethal mutation known to humanity: the power of a Spirit Reader.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "🎙️ NARRATION: en-US-ChristopherNeural (Deep Cinematic Baritone).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited, dramatized fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#SwallowedStar #LuoFeng #SciFiCultivation #MartialArts #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Arc Visual Blocks for Chapters 1 to 40
    "blocks": [
        {
            "index": 1, "range": (1, 10),
            "title": ["MARTIAL EXAM", "GENETIC AWAKENING"],
            "fallback_color": (15, 20, 30),
            "prompt": (
                "Cinematic futuristic cyberpunk training facility in a dystopian post-apocalyptic city, "
                "a young determined Asian martial artist throwing a lightning-fast punch at a digital high-tech dynamometer target, "
                "neon holographic readouts and HUD lines glowing in blue and amber, cinematic lighting, 4K masterpiece."
            )
        },
        {
            "index": 2, "range": (11, 20),
            "title": ["DOJO OF LIMITS", "FIGHTER ASSESSMENT"],
            "fallback_color": (20, 15, 10),
            "prompt": (
                "Massive high-tech glass-domed martial dojo arena at night, elite fighters in sleek reinforced dark combat exosuits, "
                "subtle telekinetic energy ripples distorting the air around a calm youth with glowing sharp eyes, dramatic volumetric shadows, 4K."
            )
        },
        {
            "index": 3, "range": (21, 30),
            "title": ["RUINED SECTOR", "WILDERNESS HUNT"],
            "fallback_color": (25, 15, 15),
            "prompt": (
                "Post-apocalyptic overgrown ruined city highway, cracked concrete surrounded by collapsed skyscrapers, "
                "a lone agile warrior holding twin ghost-blade daggers facing a ferocious mutated cybernetic beast wave, dusk sky with twin moons, epic action composition, 4K."
            )
        },
        {
            "index": 4, "range": (31, 40),
            "title": ["SPIRIT READER", "FLYING DAGGERS"],
            "fallback_color": (15, 25, 30),
            "prompt": (
                "Cinematic high-angle action shot of an awakened Spirit Reader standing atop a ruined skyscraper, "
                "six razor-sharp gleaming silver daggers hovering in a lethal orbit around him with glowing azure psychic trails, "
                "stormy sky illuminated by lightning, hyper-detailed 4K digital art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
