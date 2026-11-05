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

BUILD_DIR = "build_beast_taming_clan_71_105"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "beast-taming-clan-i-have-a-jade-book",
    "start_url": "https://freewebnovel.com/novel/beast-taming-clan-i-have-a-jade-book/chapter-71",
    "start_chapter": 71,
    "end_chapter": 105,
    "default_topic": "Beast Taming Clan",

    # Concurrency Settings & Narrator Lock
    "batch_size": 7,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Full Mir-Style Dynamic Intro Sequence Passed in intro_hook
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "In our previous chapters, having repelled the allied sect invasion with mutated thunder beasts, our young master "
                "cemented the clan's dominion over the spiritual valleys. Yet as the pages of the Jade Book reveal ancient primordial beast tombs, "
                "a terrifying seal begins to fracture beneath the mountain roots, awakening long-dormant calamity fiends."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "thunder",
            "bgm_mood": "tension"
        },
        {
            "line_id": "intro_pause_01",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "",
            "pause_duration": 0.4,
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "",
            "bgm_mood": "tension"
        },
        {
            "line_id": "intro_02_body",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "Welcome back to Being a Bong. We narrate the unreal worlds to life. "
                "In this episode, we step right back into the cultivation realm, picking up where the ancestral beast pacts left off, "
                "take a second to hit that like button, subscribe if you are new to the channel, and drop your thoughts in the comments. "
                "Your support is the engine that keeps this massive releases alive. "
                "Settle in as the ancient seals crack open, adjust your volume, and let's begin today's episode."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_lead_in_pause",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "",
            "pause_duration": 1.0,
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "",
            "bgm_mood": "no_mood"
        }
    ],

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_beast_taming_clan_71_105.mp3",
    "final_video": "final_beast_taming_clan_71_105.mp4",
    "cover_image": "cover_beast_taming_clan_71_105.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_clan_71_105.txt",
    "subtitles_file": "subtitles_beast_taming_clan_71_105.srt",
    "payload_file": "youtube_upload_payload_beast_taming_clan_71_105.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "ANCIENT BEAST TOMB & CALAMITY MUTATION! [Ch 71-105] | Beast Taming Clan Xianxia Full Audiobook",
    "tags": [
        "Beast Taming Clan", "Jade Book", "Xianxia Audiobook", "Cultivation Audiobook",
        "Beast Tamer", "Clan Building", "Progression Fantasy", "Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Beast Taming Clan: I Have A Jade Book' covering Chapters 71 through 105!\n\n"
        "Venturing into subterranean ancient tombs, our protagonist deciphers archaic spiritual glyphs using the Jade Book, guiding "
        "his winged beasts through heaven-defying tribulation mutations. But as ancient subterranean fiends uncoil from their millennial slumber, "
        "the entire province must reckon with the rise of an apex beast-taming dynasty. Experience this 35-chapter marathon with "
        "multi-voice neural TTS, context-aware acoustic soundscapes, and full synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, beast pacts, and cultivation alerts).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more chapters and cultivation updates!\n\n"
        "#BeastTamingClan #JadeBook #Xianxia #CultivationAudiobook #ProgressionFantasy #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks across Ch 71 to 105: 71-79, 80-88, 89-97, 98-105)
    "blocks": [
        {
            "index": 1, "range": (71, 79),
            "title": ["ANCIENT TOMB DESCENT", "PRIMORDIAL GLYPHS"],
            "fallback_color": (20, 30, 20),
            "prompt": (
                "Cinematic 3D cultivation fantasy view of the young Daoist clan leader exploring a colossal underground tomb cavern, "
                "holding up the luminous emerald Jade Book that casts green light over massive slumbering serpent fossils and glowing runes. "
                "Volumetric cave dust, crystalline subterranean pools, ancient stone totems, dramatic cinematic lighting."
            )
        },
        {
            "index": 2, "range": (80, 88),
            "title": ["CALAMITY TRIBULATION", "HEAVENLY BREAKTHROUGH"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D xianxia battle illustration of a colossal winged chimera beast bathed in violent violet tribulation lightning, "
                "shattering stone cliffs with a single roar while the cultivator channels Qi through a jade staff below. "
                "Storm clouds swirling, lightning arcs striking rocky peaks, cinematic rim lighting, 4k digital art."
            )
        },
        {
            "index": 3, "range": (89, 97),
            "title": ["BEAST TIDE DEFENSE", "CLAN ELITE VANGUARD"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D action scene showing fortified mountain gates defended by disciplined clan disciples riding armored spirit wolves "
                "and iron-scaled bears, repelling a chaotic swarm of rampaging subterranean monsters. "
                "Exploding talisman arrows, fiery defensive barriers, dynamic combat perspective, sharp 4k render."
            )
        },
        {
            "index": 4, "range": (98, 105),
            "title": ["APEX DYNASTY RISING", "PEAK BEAST MONARCH"],
            "fallback_color": (15, 25, 35),
            "prompt": (
                "Cinematic 3D masterpiece portrait of the young clan patriarch standing on the head of an enormous golden-feathered roc bird "
                "gliding peacefully over expansive mountain territories and mist-shrouded spiritual herb farms at dawn. "
                "Golden hour sunlight, billowing silk robes, serene mastery atmosphere, 4k high definition."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
