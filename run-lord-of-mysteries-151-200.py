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

BUILD_DIR = "build_lotm_reader_151_200"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/lord-of-mysteries-starting-as-a-reader/chapter-151",
    "novel_slug": "lotm-reader",
    "start_chapter": 151,
    "end_chapter": 200,
    "default_topic": "Lord of the Mysteries: The End of the Demoness",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Accurate 5-Beat Intro Hook for Chapter 151
    "intro_hook": [
        # Beat 1: High-Stakes Teaser (Authoritative low pitch, controlled rate, clear commas)
        {
            "line_id": "intro_01_teaser",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "authoritative_low",
            "lung_reset": False,
            "rate": "-3%",
            "pause_duration": 0.5,
            "display_text": '"I can only say... she was really unlucky today." As Madam Daly summons an evil spirit in the Language of the Dead, Ebner Franklin and Bishop Utravsky confront the Demoness of Afflictions. Trapped between madness and desire, the curse of the Devil Badge prepares to claim its final price!',
            "tts_text": '"I can only say... she was really unlucky today." As Madam Day-lee summons an evil spirit in the Language of the Dead... Ebb-ner Franklin and Bishop Oo-trahv-skee confront the Demoness of Afflictions. Trapped between madness and desire... the curse of the Devil Badge prepares to claim its final price!',
            "text": '"I can only say... she was really unlucky today." As Madam Daly summons an evil spirit in the Language of the Dead, Ebner Franklin and Bishop Utravsky confront the Demoness of Afflictions. Trapped between madness and desire, the curse of the Devil Badge prepares to claim its final price!',
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "hum",
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
        # Beat 3: In-Universe Call to Action
        {
            "line_id": "intro_03_cta",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "conversational_mid",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": "Mystical Directive: To maintain your mental anchors and support today's massive release, hit that Like button and subscribe to the channel. Peeking into the cosmos and deciphering ancient grimoires demands absolute vigilance.",
            "tts_text": "Mystical Directive: To maintain your mental anchors and support today's massive release, hit that Like button and subscribe to the channel. Peeking into the cosmos and deciphering ancient grimoires demands absolute vigilance.",
            "text": "Mystical Directive: To maintain your mental anchors and support today's massive release, hit that Like button and subscribe to the channel. Peeking into the cosmos and deciphering ancient grimoires demands absolute vigilance.",
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
            "rate": "-2%",
            "pause_duration": 0.4,
            "display_text": "Previously, Ebner simulated arcane pathways with his Pure White Eye, surviving perilous investigations across Backlund. Now, entering Chapters 151 through 200 of Lord of the Mysteries, Reader Pathway, ancient deities and forbidden covens emerge from the fog. Steel your minds, and let the mystery unfold.",
            "tts_text": "Previously, Ebb-ner simulated arcane pathways with his Pure White Eye, surviving perilous investigations across Back-lund. Now, entering Chapters 151 through 200 of Lord of the Mysteries, Reader Pathway... ancient deities and forbidden covens emerge from the fog. Steel your minds, and let the mystery unfold.",
            "text": "Previously, Ebner simulated arcane pathways with his Pure White Eye, surviving perilous investigations across Backlund. Now, entering Chapters 151 through 200 of Lord of the Mysteries, Reader Pathway, ancient deities and forbidden covens emerge from the fog. Steel your minds, and let the mystery unfold.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "dread"
        },
        # Beat 5: Lead-In Silence
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
    "final_audio": "output_lotm_reader_151_200.mp3",
    "final_video": "final_lotm_reader_151_200.mp4",
    "cover_image": "cover_lotm_reader_151_200.jpg",
    "timestamps_file": "youtube_timestamps_lotm_reader_151_200.txt",
    "subtitles_file": "subtitles_lotm_reader_151_200.srt",
    "payload_file": "youtube_upload_payload_lotm_reader_151_200.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "LORD OF THE MYSTERIES (READER): THE END OF THE DEMONESS! [Chapters 151-200] | Dark Fantasy Audiobook",
    "tags": [
        "Lord of the Mysteries", "Lord of Mysteries", "Reader Pathway", "Mystery Audiobook",
        "Ebner Franklin", "Fantasy Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to 'Lord of the Mysteries: Starting as a Reader', covering Chapters 151 through 200!\n\n"
        "As Ebner Franklin navigates the Beyonder underworld of Backlund, ancient Sealed Artifacts, the Demoness Sect, "
        "and Sequence advancements demand calculated intellect and steady nerves. "
        "Experience professional multi-voice narration, atmospheric soundscapes, and broadcast audio mastering.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and narration).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#LordOfTheMysteries #LotM #Audiobook #BeingABong #FantasyAudiobook"
    ),

    # 4 Balanced Thematic Visual Blocks (50 Chapters total)
    "blocks": [
        {
            "index": 1, "range": (151, 162),
            "title": ["THE END OF THE DEMONESS", "DARK FLAMES"],
            "fallback_color": (15, 20, 30),
            "prompt": (
                "Cinematic dark fantasy Victorian illustration of a young scholar with an eye of pure white light "
                "standing in an ornate cobblestone courtyard beside a tall necromancer woman in a mourning dress, "
                "confronting a dark-flamed carriage where an eerie Demoness with a black eye embedded in her chest perishes, "
                "atmospheric gaslamp smog, volumetric fog, octane render, unreal engine 5, 4k digital art."
            )
        },
        {
            "index": 2, "range": (163, 175),
            "title": ["SEALED ARTIFACTS", "BEYONDER UNDERWORLD"],
            "fallback_color": (25, 15, 30),
            "prompt": (
                "Cinematic Victorian steampunk fantasy scene of occult scholars examining ancient glowing grimoires and cursed brass badges "
                "inside a dimly lit clandestine study in Backlund, mysterious shadow apparitions, eerie blue candle glow, "
                "cinematic rim lighting, high contrast 4k."
            )
        },
        {
            "index": 3, "range": (176, 187),
            "title": ["READER PATHWAY", "EYE OF PURE WHITE"],
            "fallback_color": (20, 25, 20),
            "prompt": (
                "Cinematic dark fantasy depiction of a scholar channeling divine light and mystical deductions, "
                "surrounded by floating ethereal pages of ancient scriptures in a foggy cathedral hall, "
                "realistic textures, volumetric sunbeams, masterpiece digital render."
            )
        },
        {
            "index": 4, "range": (188, 200),
            "title": ["SEQUENCE ADVANCEMENT", "SHADOWS OVER BACKLUND"],
            "fallback_color": (30, 20, 25),
            "prompt": (
                "Cinematic epic dark fantasy climax shot of a high-sequence Beyonder overlooking the sprawling, smog-choked towers "
                "and iron bridges of Victorian Backlund under a crimson blood moon, deep atmospheric depth of field, "
                "photorealistic textures, masterpiece 4k digital art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
