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

BUILD_DIR = "build_invincible_1_40"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "invincible-novel",
    "start_url": "https://freewebnovel.com/novel/invincible-novel/chapter-1",
    "start_chapter": 1,
    "end_chapter": 40,
    "default_topic": "Invincible",

    # Concurrency Settings & Narrator Lock
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Full Mir-Style Dynamic Intro Sequence Passed in intro_hook (Premiere Episode)
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "In the Martial Spirit World, martial spirit defines your destiny, your clan status, and your very right to exist. "
                "Mocked and cast aside for awakening an apparent common serpent spirit, young Huang Xiaolong conceals a truth that would "
                "terrify the gods: a peerless, double top-grade primordial dragon spirit sleeping within his veins. "
                "With the ancient Asura Sword Art in his grasp, his brutal ascent to supremacy starts from this very courtyard."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "blade",
            "bgm_mood": "wonder"
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
            "bgm_mood": "wonder"
        },
        {
            "line_id": "intro_02_body",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "Welcome back to Being a Bong. We narrate the unreal worlds to life. "
                "We are thrilled to bring you the premiere episode of this Eastern fantasy cultivation epic, "
                "take a second to hit that like button, subscribe if you are new to the channel, and drop your thoughts in the comments. "
                "Your support is the engine that keeps this massive releases alive. "
                "Prepare for an unstoppable martial ascent, adjust your volume, and let's begin today's episode."
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
    "final_audio": "output_invincible_1_40.mp3",
    "final_video": "final_invincible_1_40.mp4",
    "cover_image": "cover_invincible_1_40.jpg",
    "timestamps_file": "youtube_timestamps_invincible_1_40.txt",
    "subtitles_file": "subtitles_invincible_1_40.srt",
    "payload_file": "youtube_upload_payload_invincible_1_40.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "PRIMORDIAL DRAGON AWAKENING & ASURA ART! [Ch 1-40] | Invincible Xuanhuan Full Audiobook",
    "tags": [
        "Invincible Novel", "Invincible Audiobook", "Huang Xiaolong", "Xuanhuan Audiobook",
        "Martial Spirit", "Asura Art", "Cultivation Audiobook", "Progression Fantasy", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to the premiere release of 'Invincible' (Huang Xiaolong's Legend) covering Chapters 1 through 40!\n\n"
        "In a ruthless cultivation realm where a warrior's martial spirit determines their ceiling in life, Huang Xiaolong is written "
        "off by his clan as trash. Unbeknownst to everyone, his soul holds a mythical twin primordial divine dragon spirit, paired with "
        "the blood-drenched legacy of the ancient Asura Ring. Watch as he slaps clan hypocrites, shocks patriarchs, and begins his bloody "
        "walk to the pinnacle. Experience this 40-chapter premiere marathon with multi-voice neural TTS, context-aware acoustic soundscapes, "
        "and full synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for all dialogue, spirit pacts, and cultivation ranks).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more chapters and invincible cultivation sagas!\n\n"
        "#Invincible #HuangXiaolong #Xuanhuan #CultivationAudiobook #MartialSpirit #Audiobook #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks across Ch 1 to 40: 1-10, 11-20, 21-30, 31-40)
    "blocks": [
        {
            "index": 1, "range": (1, 10),
            "title": ["MARTIAL SPIRIT AWAKENING", "SECRET OF THE BLACK DRAGON"],
            "fallback_color": (25, 20, 30),
            "prompt": (
                "Cinematic 3D xuanhua illustration of 7-year-old Huang Xiaolong standing in an ancient clan courtyard, "
                "two colossal shadowy primordial dragon silhouettes with glowing golden eyes coiling behind him in the night air. "
                "Cobblestone martial grounds, glowing spiritual Qi mist, dramatic rim lighting, 4k digital art."
            )
        },
        {
            "index": 2, "range": (11, 20),
            "title": ["ASURA RING INHERITANCE", "NETHERWORLD SWORD"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic 3D fantasy scene of the young cultivator meditating deep inside a hidden mountain cave, "
                "an ancient skull-engraved black ring glowing with eerie crimson netherworld flames on his hand. "
                "Blood-red Qi blades hovering in mid-air, dark jagged rock walls, chiaroscuro lighting, sharp 4k render."
            )
        },
        {
            "index": 3, "range": (21, 30),
            "title": ["CLAN ARENA TOURNAMENT", "THE PRODIGY REVEALED"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D martial arts action shot in an expansive outdoor stone arena surrounded by cheering clan spectators, "
                "Huang Xiaolong launching forward with a fierce palm strike wrapped in dragon-shaped battle Qi against an arrogant rival disciple. "
                "Shattered flagstones, dynamic motion blur, high-contrast sunlight, detailed clothing textures."
            )
        },
        {
            "index": 4, "range": (31, 40),
            "title": ["SILVERMOON FOREST", "BLOOD HUNT BREAKTHROUGH"],
            "fallback_color": (15, 25, 30),
            "prompt": (
                "Cinematic 3D dark fantasy view of the young martial master standing atop a slain massive demonic beast "
                "in a moonlit primeval forest, wiping blood from his dual blades under the cold silver moonlight. "
                "Ancient giant trees, drifting fireflies and spirit mist, commanding victorious posture, masterpiece 4k render."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
