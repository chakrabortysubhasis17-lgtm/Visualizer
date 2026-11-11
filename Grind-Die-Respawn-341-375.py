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

BUILD_DIR = "build_beast_taming_341_375"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/beast-taming-my-beasts-grind-die-and-respawn/chapter-341",
    "novel_slug": "beast-taming",
    "start_chapter": 341,
    "end_chapter": 375,
    "default_topic": "Beast Taming: Rank 2 Bond Awakening and Assimilated Skills",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Accurate 5-Beat Intro Hook for Chapter 341
    "intro_hook": [
        # Beat 1: High-Stakes Teaser
        {
            "line_id": "intro_01_teaser",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": '"That\'s Harden—on a person!" Watching stony gray armor coat a tamer\'s forearms to deflect a heavy training staff, Jin uncovers the secrets of Rank Two Bond Awakening. As the threshold nears for his EX-Rank Soul Talent, Glitch\'s defensive mastery and little Flicker\'s future prepare to cross the bridge into raw assimilated power!',
            "tts_text": '"That is Harden... on a person!" Watching stony gray armor coat a tamer\'s forearms to deflect a heavy training staff, Jin uncovers the secrets of Rank Two Bond Awakening. As the threshold nears for his E-X-Rank Soul Talent, Glitch\'s defensive mastery and little Flicker\'s future prepare to cross the bridge into raw assimilated power!',
            "text": '"That\'s Harden—on a person!" Watching stony gray armor coat a tamer\'s forearms to deflect a heavy training staff, Jin uncovers the secrets of Rank Two Bond Awakening. As the threshold nears for his EX-Rank Soul Talent, Glitch\'s defensive mastery and little Flicker\'s future prepare to cross the bridge into raw assimilated power!',
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "impact",
            "bgm_mood": "tension"
        },
        {
            "line_id": "intro_pause_01",
            "speaker": "Narrator",
            "gender": "Neutral",
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
        # Beat 2: Trademark Channel Signature
        {
            "line_id": "intro_02_trademark",
            "speaker": "Narrator",
            "gender": "Neutral",
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
            "gender": "Neutral",
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
        # Beat 3: In-Universe CTA
        {
            "line_id": "intro_03_cta",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "conversational_mid",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": "Tamer Directive: To strengthen your Bond Core and fuel today's massive release, hit that Like button and subscribe to the channel. Cultivating nine-stripe cores and breaking through the ninth star requires every drop of astral energy.",
            "tts_text": "Tamer Directive: To strengthen your Bond Core and fuel today's massive release, hit that Like button and subscribe to the channel. Cultivating nine-stripe cores and breaking through the ninth star requires every drop of astral energy.",
            "text": "Tamer Directive: To strengthen your Bond Core and fuel today's massive release, hit that Like button and subscribe to the channel. Cultivating nine-stripe cores and breaking through the ninth star requires every drop of astral energy.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "interface",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_pause_03",
            "speaker": "Narrator",
            "gender": "Neutral",
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
        # Beat 4: Recap Bridge
        {
            "line_id": "intro_04_bridge",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "Previously, Jin pushed through relentless academy trials, grinding avatar simulations while nurturing Glitch and the delicate fledgling Flicker. Now, entering Chapters 341 through 375 of Beast Taming, the breakthrough to Rank Two unlocks assimilated beast skills and the mysteries of the Bond Core. Settle in, and let the awakening begin.",
            "tts_text": "Previously, Jin pushed through relentless academy trials, grinding avatar simulations while nurturing Glitch and the delicate fledgling Flicker. Now, entering Chapters 341 through 375 of Beast Taming... the breakthrough to Rank Two unlocks assimilated beast skills and the mysteries of the Bond Core. Settle in, and let the awakening begin.",
            "text": "Previously, Jin pushed through relentless academy trials, grinding avatar simulations while nurturing Glitch and the delicate fledgling Flicker. Now, entering Chapters 341 through 375 of Beast Taming, the breakthrough to Rank Two unlocks assimilated beast skills and the mysteries of the Bond Core. Settle in, and let the awakening begin.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "triumph"
        },
        # Beat 5: Lead-In Transition
        {
            "line_id": "intro_05_scene_sfx",
            "speaker": "Narrator",
            "gender": "Neutral",
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
            "gender": "Neutral",
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
    "final_audio": "output_beast_taming_341_375.mp3",
    "final_video": "final_beast_taming_341_375.mp4",
    "cover_image": "cover_beast_taming_341_375.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_341_375.txt",
    "subtitles_file": "subtitles_beast_taming_341_375.srt",
    "payload_file": "youtube_upload_payload_beast_taming_341_375.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "BEAST TAMING: RANK 2 BOND AWAKENING & ASSIMILATED SKILLS! [Chapters 341-375] | LitRPG Full Audiobook",
    "tags": [
        "Beast Taming", "My Beasts Grind Die and Respawn", "LitRPG Audiobook",
        "Progression Fantasy", "Monster Taming", "Isekai Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to 'Beast Taming: My Beasts Grind, Die, and Respawn', covering Chapters 341 through 375!\n\n"
        "As Jin explores the mechanics of Rank 2 breakthrough and the power on the tamer's side of the bond, "
        "assimilated beast skills, Bond Core stripes, and the second active contract slot redefine his combat capability. "
        "Experience dramatized multi-voice narration, spatial sound design, and broadcast standard audio mastering.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system notifications).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#BeastTaming #LitRPG #Audiobook #BeingABong #FantasyAudiobook"
    ),

    # 4 Balanced Thematic Visual Blocks (35 Chapters total)
    "blocks": [
        {
            "index": 1, "range": (341, 349),
            "title": ["BOND AWAKENING", "ASSIMILATED SKILLS"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic 3D fantasy illustration of a young beast tamer with stony gray crystallized armor spreading across his forearms, "
                "deflecting an enchanted combat staff in a grand martial academy arena, beside a massive horned ram beast and a resilient iron-shelled avatar beast, "
                "glowing runic bond core circle, volumetric lighting, octane render, unreal engine 5, 4k digital art."
            )
        },
        {
            "index": 2, "range": (350, 357),
            "title": ["CORE STRIPES", "RANK TWO THRESHOLD"],
            "fallback_color": (30, 20, 15),
            "prompt": (
                "Cinematic 3D fantasy scene of an intricate glowing bond core orb manifesting with multiple golden stripes, "
                "floating above an ancient cultivation pedestal, surrounded by swirling elemental energy, deep blue and amber particle aura, "
                "cinematic rim lighting, photorealistic textures, 4k digital art."
            )
        },
        {
            "index": 3, "range": (358, 366),
            "title": ["AVATAR REPETITION", "FLICKER'S EVOLUTION"],
            "fallback_color": (15, 30, 20),
            "prompt": (
                "Cinematic 3D fantasy depiction of a small mystical bird with iridescent feathers perching upon the sturdy horns of an armored beast, "
                "ethereal mana trails swirling through a sunlit training courtyard, ancient academy architecture in background, atmospheric depth of field, "
                "masterpiece digital render."
            )
        },
        {
            "index": 4, "range": (367, 375),
            "title": ["EX-RANK TALENT", "ASCENT OF THE TAMER"],
            "fallback_color": (25, 15, 30),
            "prompt": (
                "Cinematic 3D epic fantasy shot of a powerful young summoner commanding an evolved elemental vanguard beast and a radiant celestial bird "
                "in a sprawling arena stadium, sparkling astral energy storm, golden hour sunbeams, dynamic heroic composition, masterpiece 4k digital art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
