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

BUILD_DIR = "build_highway_survival_101_150"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://mtl-novel.com/novel/highway-survival-for-all-my-rvs-infinite-evolution/chapter-101-subverting-perceptions-this-is-the-real-bigshot-2-4/",
    "novel_slug": "highway-survival-for-all-my-rvs-infinite-evolution",
    "start_chapter": 101,
    "end_chapter": 150,
    "default_topic": "Highway Survival for All: My RV's Infinite Evolution",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Accurate Universal 5-Beat Intro Hook for Chapter 101 (Lin Hui, Evil Wolf Guild Annihilation & Cauldron City Expedition)
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
            "display_text": '"My car, you can\'t stop. My path, you can\'t block either. In your next life, keep your eyes wider." Delivered like a hogtied dead dog by his terrified allies, the tyrant of the Evil Wolf Guild is executed in cold blood before Lin Hui\'s black apocalypse RV—subduing the entire district without firing a single missile!',
            "tts_text": '"My car, you cannot stop. My path, you cannot block either. In your next life, keep your eyes wider." Delivered like a hogtied dead dog by his terrified allies, the tyrant of the Evil Wolf Guild is executed in cold blood before Lin Hui\'s black apocalypse RV... subduing the entire district without firing a single missile!',
            "text": '"My car, you can\'t stop. My path, you can\'t block either. In your next life, keep your eyes wider." Delivered like a hogtied dead dog by his terrified allies, the tyrant of the Evil Wolf Guild is executed in cold blood before Lin Hui\'s black apocalypse RV—subduing the entire district without firing a single missile!',
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "gunshot",
            "bgm_mood": "tension"
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
            "sfx": "whoosh",
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
            "display_text": "Highway Survival System Directive: To fuel your mobile fortress for today's grand release, smash the Like button and subscribe to the channel. Upgrading your vehicle's armor matrix ensures survival on the lethal highway to Cauldron City.",
            "tts_text": "Highway Survival System Directive: To fuel your mobile fortress for today's grand release, smash the Like button and subscribe to the channel. Upgrading your vehicle's armor matrix ensures survival on the lethal highway to Cauldron City.",
            "text": "Highway Survival System Directive: To fuel your mobile fortress for today's grand release, smash the Like button and subscribe to the channel. Upgrading your vehicle's armor matrix ensures survival on the lethal highway to Cauldron City.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "interface",
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
            "display_text": "Previously, Lin Hui dismantled hostile roadblocks and forced rival warlords to betray their own allies in sheer terror. Now, driving into chapters 101 through 150 of Highway Survival for All: My RV's Infinite Evolution, the road to Cauldron City and the deadly Fushi Expedition begins. Fasten your seatbelts, and let the apocalyptic convoy roll out.",
            "tts_text": "Previously, Lin Hui dismantled hostile roadblocks and forced rival warlords to betray their own allies in sheer terror. Now, driving into chapters 101 through 150 of Highway Survival for All: My RV's Infinite Evolution, the road to Cauldron City and the deadly Fushi Expedition begins. Fasten your seatbelts, and let the apocalyptic convoy roll out.",
            "text": "Previously, Lin Hui dismantled hostile roadblocks and forced rival warlords to betray their own allies in sheer terror. Now, driving into chapters 101 through 150 of Highway Survival for All: My RV's Infinite Evolution, the road to Cauldron City and the deadly Fushi Expedition begins. Fasten your seatbelts, and let the apocalyptic convoy roll out.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "triumph"
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
            "sfx": "wind",
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

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_highway_survival_101_150.mp3",
    "final_video": "final_highway_survival_101_150.mp4",
    "cover_image": "cover_highway_survival_101_150.jpg",
    "timestamps_file": "youtube_timestamps_highway_survival_101_150.txt",
    "subtitles_file": "subtitles_highway_survival_101_150.srt",
    "payload_file": "youtube_upload_payload_highway_survival_101_150.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "HIGHWAY OVERLORD & THE INFINITE RV EVOLUTION! [Chapters 101-150] | Post-Apocalyptic LitRPG Full Audiobook",
    "tags": [
        "Highway Survival for All My RVs Infinite Evolution", "Highway Survival", "Post-Apocalyptic Survival",
        "LitRPG Audiobook", "Infinite Evolution", "Vehicle Upgrade Novel", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to 'Highway Survival for All: My RV's Infinite Evolution', covering Chapters 101 through 150!\n\n"
        "After forcing the Overlord Alliance to betray their own allies and eliminating the Evil Wolf Guild without firing a missile, "
        "Lin Hui continues his unyielding journey across the lethal apocalyptic highway. Embarking on the treacherous Fushi Expedition "
        "toward Cauldron City, witness his heavily armored mobile fortress evolve through infinite upgrades, crushing rival fleets "
        "and mutated highway horrors alike.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system notifications).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#HighwaySurvival #InfiniteEvolution #LitRPG #ApocalypseSurvival #Audiobook #BeingABong"
    ),

    # Visual Prompts (4 Balanced Thematic Blocks covering Chapters 101 to 150)
    "blocks": [
        {
            "index": 1, "range": (101, 112),
            "title": ["HIGHWAY BIGSHOT", "RUINS OF EVIL WOLF"],
            "fallback_color": (25, 20, 20),
            "prompt": (
                "Cinematic 3D post-apocalyptic illustration of a massive heavily armored black Level 6 RV mobile fortress "
                "standing dominant over a ruined highway littered with smoking vehicle wreckage and defeated post-apocalyptic gang members, "
                "dramatic dust storm, sunset rim lighting, octane render, unreal engine 5 style, hyper-detailed 4k digital art."
            )
        },
        {
            "index": 2, "range": (113, 125),
            "title": ["CAULDRON CITY CONVOY", "APOCALYPSE EXPEDITION"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D post-apocalyptic scene of an armored convoy speeding down a cracked desert highway toward the sprawling neon-lit ruins of Cauldron City, "
                "twin Apache helicopters flying overhead in the twilight sky, gritty textures, dynamic motion blur, high contrast 4k."
            )
        },
        {
            "index": 3, "range": (126, 137),
            "title": ["FUSHI WASTELAND", "INFINITE VEHICLE EVOLUTION"],
            "fallback_color": (20, 25, 30),
            "prompt": (
                "Cinematic 3D sci-fi fantasy depiction of Lin Hui upgrading his RV inside a futuristic fortified garage, "
                "blue holographic interface grids projecting infinite vehicle modifications, heavy missile pods, and reinforced titanium plating, "
                "volumetric lighting, moody atmosphere, sharp 4k render."
            )
        },
        {
            "index": 4, "range": (138, 150),
            "title": ["SOVEREIGN OVERLORD", "RULE OF THE HIGHWAY"],
            "fallback_color": (25, 15, 20),
            "prompt": (
                "Cinematic 3D grandiose wide shot of the upgraded Level 7 apocalypse RV plowing through mutant hordes and hostile armored buggies on an open highway, "
                "explosions lighting up the stormy midnight sky, epic scale, photorealistic textures, masterpiece 4k digital art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
