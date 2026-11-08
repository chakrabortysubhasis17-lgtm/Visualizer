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

BUILD_DIR = "build_billion_points_stronger_101_150"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters
    "source_type": "scrape",
    "start_url": "https://mtl-novel.com/novel/the-end-of-the-world-my-woman-is-a-billion-points-stronger/chapter-101-kowtow-to-death/",
    "novel_slug": "the-end-of-the-world-my-woman-is-a-billion-points-stronger",
    "start_chapter": 101,
    "end_chapter": 150,
    "default_topic": "My Woman is a Billion Points Stronger",

    # Concurrency Settings & Hardcoded Narrator Lock
    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Dynamic Post-Apocalyptic Intro Sequence
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "Across the smoking ruins of a shattered world, where zombies mutate and savage warlords feast, "
                "absolute dominance belongs to the couple who bends reality itself. "
                "With overpowered celestial talents and a peerless goddess holding back apocalyptic swarms, "
                "watch arrogant survivors bow in terror as the sovereign stronghold crushes every challenger."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "explosion",
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
                "Today, we bring you chapters one hundred and one through one hundred and fifty of "
                "The End of the World: My Woman Is a Billion Points Stronger. "
                "Take a moment to hit that like button, subscribe if you are new to the channel, "
                "and drop your thoughts in the comments below. Your support is the engine that keeps these grand marathons alive. "
                "Adjust your volume, brace for total wasteland annihilation, and let's begin."
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
    "final_audio": "output_billion_points_stronger_101_150.mp3",
    "final_video": "final_billion_points_stronger_101_150.mp4",
    "cover_image": "cover_billion_points_stronger_101_150.jpg",
    "timestamps_file": "youtube_timestamps_billion_points_stronger_101_150.txt",
    "subtitles_file": "subtitles_billion_points_stronger_101_150.srt",
    "payload_file": "youtube_upload_payload_billion_points_stronger_101_150.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "OVERPOWERED GODDESS CRUSHES THE WASTELAND! [Chapters 101-150] | Apocalypse Audiobook",
    "tags": [
        "My Woman is a Billion Points Stronger", "The End of the World", "Apocalypse Audiobook",
        "Overpowered Female Lead", "Zombie Apocalypse", "Web Novel Audio", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to the continuous post-apocalyptic action of 'The End of the World: My Woman Is a Billion Points Stronger', "
        "covering Chapters 101 through 150!\n\n"
        "Watch our protagonist and his peerless overpowered partner annihilate rival shelter tyrants, wipe out mutated zombie hordes with ease, "
        "and hoard supreme dimensional supplies while other survivors struggle in the ash. Experience this 50-chapter apocalypse arc with "
        "multi-voice neural TTS, context-aware acoustic soundscapes, voice-aware dynamic rate scaling, and synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and apocalyptic action).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more apocalyptic fiction, overpowered leads, and survival sagas!\n\n"
        "#MyWomanIsABillionPointsStronger #ApocalypseAudiobook #Zombies #OverpoweredMC #WebNovel #BeingABong"
    ),

    # Visual Prompts (4 balanced thematic blocks covering Chapters 101 to 150)
    "blocks": [
        {
            "index": 1, "range": (101, 113),
            "title": ["KOWTOW TO THE SOVEREIGN", "PUNISHMENT IN THE ASH"],
            "fallback_color": (35, 15, 15),
            "prompt": (
                "Cinematic 3D post-apocalyptic action scene in a ruined city square covered in cracked asphalt and ashes, "
                "arrogant armed raiders on their knees trembling in fear, an aloof beautiful heroine in high-tech combat attire "
                "radiating an overwhelming celestial blue aura, collapsed skyscrapers in the background, sharp 4k render."
            )
        },
        {
            "index": 2, "range": (114, 125),
            "title": ["MUTATED HORDE PURGE", "THE CELESTIAL STRIKE"],
            "fallback_color": (40, 20, 10),
            "prompt": (
                "Cinematic 3D apocalyptic battle illustration of thousands of ferocious mutated zombies swarming an abandoned highway, "
                "a colossal shockwave of blinding white psychic energy obliterating the front ranks into dust, "
                "fiery explosions and flying shrapnel under a stormy crimson sky, hyper-detailed 4k digital art."
            )
        },
        {
            "index": 3, "range": (126, 138),
            "title": ["THE FORTRESS DOMAIN", "SUPREME PROVISIONS"],
            "fallback_color": (20, 25, 30),
            "prompt": (
                "Cinematic 3D interior of a luxurious reinforced bunker sanctuary, "
                "steel walls illuminated by clean neon lights, stacks of military-grade supply crates and gourmet delicacies, "
                "a calm protagonist enjoying coffee beside heavy surveillance monitors displaying the frozen wasteland outside, "
                "dramatic chiaroscuro lighting, 4k digital masterpiece."
            )
        },
        {
            "index": 4, "range": (139, 150),
            "title": ["DOMINION OVER THE RUINS", "THE IMMORTAL COUPLE"],
            "fallback_color": (30, 15, 35),
            "prompt": (
                "Cinematic 3D epic establishing shot of the protagonist and his radiant partner standing atop a colossal reinforced armored wall, "
                "watching dawn break over a conquered post-apocalyptic wasteland, wind whipping their long dark cloaks, "
                "absolute supreme power and triumph, 4k digital masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
