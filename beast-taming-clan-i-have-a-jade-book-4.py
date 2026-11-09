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
                if len(rows) < 8 or any("Exposition details continue" in (r.get("display_text") or r.get("tts_text") or r.get("text", "")) for r in rows):
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

BUILD_DIR = "build_beast_taming_clan_106_140"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/beast-taming-clan-i-have-a-jade-book/chapter-106",
    "novel_slug": "beast-taming-clan-i-have-a-jade-book",
    "start_chapter": 106,
    "end_chapter": 140,
    "default_topic": "Beast Taming Clan: I Have A Jade Book",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Accurate Universal 5-Beat Intro Hook for Chapter 106 (Five Poison Mountain & Five Venom Bees)
    "intro_hook": [
        # Beat 1: High-Stakes Teaser (0:00 - 0:12)
        {
            "line_id": "intro_01_teaser",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "Five Poison Mountain has seen the deadly Five Venom Bees—swarms whose toxic stingers pierce a cultivator's spiritual shield with ruthless ease, guarding the ancient cave mansion of the Wu Du Ascendant!",
            "tts_text": "Five Poison Mountain has seen the deadly Five Venom Bees... swarms whose toxic stingers pierce a cultivator's spiritual shield with ruthless ease, guarding the ancient cave mansion of the Wu Du Ascendant!",
            "text": "Five Poison Mountain has seen the deadly Five Venom Bees—swarms whose toxic stingers pierce a cultivator's spiritual shield with ruthless ease, guarding the ancient cave mansion of the Wu Du Ascendant!",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "monster",
            "bgm_mood": "dread"
        },
        {
            "line_id": "intro_pause_01",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "no_mood"
        },

        # Beat 2: Trademark Channel Signature (0:12 - 0:17)
        {
            "line_id": "intro_02_trademark",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "engaged_alert",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": "Welcome back to Being a Bong. We narrate the unreal worlds to life.",
            "tts_text": "Welcome back to Being a Bong. We narrate the unreal worlds to life.",
            "text": "Welcome back to Being a Bong. We narrate the unreal worlds to life.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "gong",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_pause_02",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "no_mood"
        },

        # Beat 3: In-Universe Lore-Bound CTA (0:17 - 0:27)
        {
            "line_id": "intro_03_cta",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "conversational_mid",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": "Ye Clan Spiritual Directive: To refine your spirit beast contracts and secure your sect contribution points for the Foundation Establishment Pill, strike the Like button and subscribe to the channel. Stabilize your dantian before venturing into the insect swarms.",
            "tts_text": "Ye Clan Spiritual Directive: To refine your spirit beast contracts and secure your sect contribution points for the Foundation Establishment Pill, strike the Like button and subscribe to the channel. Stabilize your dantian before venturing into the insect swarms.",
            "text": "Ye Clan Spiritual Directive: To refine your spirit beast contracts and secure your sect contribution points for the Foundation Establishment Pill, strike the Like button and subscribe to the channel. Stabilize your dantian before venturing into the insect swarms.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "chime",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_pause_03",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "no_mood"
        },

        # Beat 4: Recap Bridge (0:27 - 0:40)
        {
            "line_id": "intro_04_bridge",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "Previously, Ye Jingcheng consolidated his beast-taming cultivation amidst family commerce and mountain trials. Now, entering chapters 106 through 140 of Beast Taming Clan: I Have A Jade Book, Ye Jingteng returns with an expedition into the venomous depths of Five Poison Mountain. Savor a cup of Cyan Bamboo Wine, and let the treasure hunt begin.",
            "tts_text": "Previously, Ye Jingcheng consolidated his beast-taming cultivation amidst family commerce and mountain trials. Now, entering chapters 106 through 140 of Beast Taming Clan: I Have A Jade Book, Ye Jingteng returns with an expedition into the venomous depths of Five Poison Mountain. Savor a cup of Cyan Bamboo Wine, and let the treasure hunt begin.",
            "text": "Previously, Ye Jingcheng consolidated his beast-taming cultivation amidst family commerce and mountain trials. Now, entering chapters 106 through 140 of Beast Taming Clan: I Have A Jade Book, Ye Jingteng returns with an expedition into the venomous depths of Five Poison Mountain. Savor a cup of Cyan Bamboo Wine, and let the treasure hunt begin.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "intrigue"
        },

        # Beat 5: Post-Intro Scene SFX & Transition Silence (0:40 - 0:42)
        {
            "line_id": "intro_05_scene_sfx",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.2,
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "rain",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_06_lead_in_silence",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 1.0,
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "no_mood"
        }
    ],

    "build_dir": BUILD_DIR,
    "final_audio": "output_beast_taming_clan_106_140.mp3",
    "final_video": "final_beast_taming_clan_106_140.mp4",
    "cover_image": "cover_beast_taming_clan_106_140.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_clan_106_140.txt",
    "subtitles_file": "subtitles_beast_taming_clan_106_140.srt",
    "payload_file": "youtube_upload_payload_beast_taming_clan_106_140.json",

    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    "video_title": "FIVE POISON MOUNTAIN & THE VENOM BEE SWARM! [Chapters 106-140] | Beast Taming Clan Cultivation Audiobook",
    "tags": [
        "Beast Taming Clan I Have A Jade Book", "Xuanhuan Audiobook", "Five Venom Bees",
        "Wu Du Ascendant", "Cultivation Audiobook", "Progression Fantasy", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Beast Taming Clan: I Have A Jade Book', covering Chapters 106 through 140!\n\n"
        "From rain-swept bamboo pavilions and cups of aged Cyan Bamboo Wine on Lingyun Peak, Ye Jingteng brings "
        "word of an ancient secret realm: the legendary inheritance cave of the Wu Du Ascendant on Five Poison Mountain. "
        "Guarded by terrifying Five Venom Bees whose stingers pierce cultivators' spiritual shields, Ye Jingcheng and "
        "the clan's beast masters prepare to venture into deadly insect swarms.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system notifications).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#BeastTamingClan #WuDuAscendant #FiveVenomBees #CultivationAudiobook #Audiobook #BeingABong"
    ),

    "blocks": [
        {
            "index": 1, "range": (106, 114),
            "title": ["FIVE POISON MOUNTAIN", "THE VENOM BEE SWARM"],
            "fallback_color": (20, 30, 25),
            "prompt": (
                "Cinematic 3D xuanhuan fantasy illustration of cultivators in green robes and bamboo hats standing inside a misty rain-swept bamboo pavilion on a high mountain cliff, "
                "a swarm of glowing, menacing golden-striped venom bees hovering amidst the rain and damp bamboo fog in the distance, "
                "traditional Chinese xianxia atmosphere, cinematic lighting, volumetric mist, highly detailed 4k digital art."
            )
        },
        {
            "index": 2, "range": (115, 123),
            "title": ["INHERITANCE CAVE", "ANCIENT INSECT SECRETS"],
            "fallback_color": (30, 25, 40),
            "prompt": (
                "Cinematic 3D fantasy depiction of a perilous poisonous mountain gorge shrouded in purple toxic miasma, "
                "glowing spirit fungi on jagged cliffside rocks, an ancient overgrown stone cave entrance inscribed with mystical talismans, "
                "octane render, atmospheric lighting, hyper-detailed 4k textures."
            )
        },
        {
            "index": 3, "range": (124, 131),
            "title": ["BLACK WOOD ANTS", "POISONOUS SWARM CLASH"],
            "fallback_color": (35, 20, 20),
            "prompt": (
                "Cinematic 3D action fantasy battle scene inside a dark subterranean cavern, "
                "swarms of armored black wood ants clashing fiercely against giant venomous centipedes and flying poison bees, "
                "glowing spiritual qi talismans, dynamic composition, dramatic rim lighting, 4k."
            )
        },
        {
            "index": 4, "range": (132, 140),
            "title": ["FOUNDATION PROGRESSION", "CLAN TRIUMPH"],
            "fallback_color": (30, 35, 20),
            "prompt": (
                "Cinematic 3D grandiose establishing view of Lingyun Peak at sunrise after the storm, "
                "a young cultivation master in elegant robes standing by a tranquil mountain lake, "
                "tamed spirit insects and beasts resting peacefully beside him, golden morning rays piercing morning clouds, 4k digital masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
