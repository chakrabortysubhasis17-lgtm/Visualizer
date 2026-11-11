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

BUILD_DIR = "build_reverend_insanity_001_050"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/reverend-insanity/chapter-1",
    "novel_slug": "reverend-insanity",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Reverend Insanity: Rebirth of the Demonic Venerable",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Accurate 5-Beat Intro Hook for Chapter 1
    "intro_hook": [
        # Beat 1: High-Stakes Teaser
        {
            "line_id": "intro_01_teaser",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "authoritative_low",
            "lung_reset": False,
            "rate": "-3%",
            "pause_duration": 0.5,
            "display_text": '"If the Spring Autumn Cicada I have just cultivated is effective, I shall still be a demon in my next life!" Surrounded on all sides by righteous hypocrites on the blood-soaked cliffs of his defeat, Fang Yuan detonates his body in a blinding cataclysm—only to awaken five hundred years in the past on Qing Mao Mountain!',
            "tts_text": '"If the Spring Autumn Cicada I have just cultivated is effective... I shall still be a demon in my next life!" Surrounded on all sides by righteous hypocrites on the blood-soaked cliffs of his defeat... Fahng Yu-ahn detonates his body in a blinding cataclysm... only to awaken, five hundred years in the past, on Ching Mow Mountain!',
            "text": '"If the Spring Autumn Cicada I have just cultivated is effective, I shall still be a demon in my next life!" Surrounded on all sides by righteous hypocrites on the blood-soaked cliffs of his defeat, Fang Yuan detonates his body in a blinding cataclysm—only to awaken five hundred years in the past on Qing Mao Mountain!',
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "explosion",
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
            "display_text": "Demonic Cultivator Decree: To replenish your primeval stones and support today's massive release, hit that Like button and subscribe to the channel. Re-walking the path of supremacy amidst ancient Gu worms demands relentless perseverance.",
            "tts_text": "Demonic Cultivator Decree: To replenish your primeval stones and support today's massive release, hit that Like button and subscribe to the channel. Re-walking the path of supremacy amidst ancient Goo worms demands relentless perseverance.",
            "text": "Demonic Cultivator Decree: To replenish your primeval stones and support today's massive release, hit that Like button and subscribe to the channel. Re-walking the path of supremacy amidst ancient Gu worms demands relentless perseverance.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "coin",
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
            "display_text": "Armed with five hundred years of ruthless worldly experience and cold, unyielding wisdom, the former blood-path master stands before his youth in the Gu Yue clan. Now, entering Chapters 1 through 50 of Reverend Insanity, the awakening ceremony begins. Steel your hearts, and witness the demon's rise.",
            "tts_text": "Armed with five hundred years of ruthless worldly experience and cold, unyielding wisdom, the former blood-path master stands before his youth in the Goo Yu-eh clan. Now, entering Chapters 1 through 50 of Reverend Insanity... the awakening ceremony begins. Steel your hearts, and witness the demon's rise.",
            "text": "Armed with five hundred years of ruthless worldly experience and cold, unyielding wisdom, the former blood-path master stands before his youth in the Gu Yue clan. Now, entering Chapters 1 through 50 of Reverend Insanity, the awakening ceremony begins. Steel your hearts, and witness the demon's rise.",
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
            "sfx": "rain",
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
    "final_audio": "output_reverend_insanity_001_050.mp3",
    "final_video": "final_reverend_insanity_001_050.mp4",
    "cover_image": "cover_reverend_insanity_001_050.jpg",
    "timestamps_file": "youtube_timestamps_reverend_insanity_001_050.txt",
    "subtitles_file": "subtitles_reverend_insanity_001_050.srt",
    "payload_file": "youtube_upload_payload_reverend_insanity_001_050.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "REVEREND INSANITY: REBIRTH OF THE DEMONIC VENERABLE! [Chapters 1-50] | Dark Cultivation Full Audiobook",
    "tags": [
        "Reverend Insanity", "Fang Yuan", "Gu Daoist Master", "Dark Fantasy Audiobook",
        "Cultivation Audiobook", "Xianxia Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to 'Reverend Insanity', covering Chapters 1 through 50!\n\n"
        "Five hundred years of blood, slaughter, and scheming end in a blinding flash as Fang Yuan uses the legendary "
        "Spring Autumn Cicada to reverse time itself. Waking up as a fifteen-year-old youth in Gu Yue Village on "
        "Qing Mao Mountain, he prepares to defy destiny, awaken his primeval aperture, and conquer the world of Gu.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and narration).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#ReverendInsanity #FangYuan #Cultivation #Xianxia #Audiobook #BeingABong #FantasyAudiobook"
    ),

    # 4 Balanced Thematic Visual Blocks for Chapters 1 to 50
    "blocks": [
        {
            "index": 1,
            "range": (1, 12),
            "title": ["SPRING AUTUMN CICADA", "REBIRTH FIVE HUNDRED YEARS AGO"],
            "fallback_color": (15, 20, 25),
            "prompt": (
                "A cinematic wide 16:9 high-contrast key visual set on a jagged mountain precipice of Qing Mao Mountain during a torrential midnight spring storm, "
                "designed for maximum CTR. In the intense spotlight of the foreground stands fifteen-year-old Gu Yue Fang Yuan—a cold, calculating youth with jet-black hair "
                "clothed in traditional dark green Hanfu robes with torn hem, his bottomless obsidian eyes radiating ancient ruthlessness and worldly wisdom far beyond his years. "
                "Hovering before his chest in a brilliant emerald aura is the legendary Rank 7 Spring Autumn Cicada—an exquisite, jade-green mythical cicada insect with "
                "translucent iridescent wings that emit undulating ripples of golden time-distortion waves through the rain. "
                "In the misty valley far below, hundreds of warm lantern lights glow from the traditional wooden stilt houses and stone pavilions of Gu Yue Village. "
                "In the dark stormy sky above, a crescent moon peers through parted thunderclouds, casting cold silver rim light across the wet cliff edge and pine needles. "
                "Glistening raindrops, volumetric mist, photorealistic silk fabric and weathered cliff rock, dark xianxia masterpiece, Unreal Engine 5 digital art, 8k --ar 16:9 --style raw"
            )
        },
        {
            "index": 2,
            "range": (13, 25),
            "title": ["APERTURE AWAKENING", "HOPE GU & THE PRIMEVAL RIVER"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "An epic 16:9 wide interior visual inside the Gu Yue clan's ancestral subterranean cave of spirit flowers. "
                "Center-stage in the spotlight, young Fang Yuan stands barefoot in a calm underground subterranean river of sparkling azure primeval water, "
                "his hand outstretched as a swarm of glowing golden Hope Gu insects flutter toward his navel, piercing into his abdomen to shatter the barrier and ignite "
                "a swirling, glowing copper-green primeval sea within his newly awakened aperture. "
                "Behind him along the stone shores, clan elders in loose ceremonial white robes and arrogant junior disciples stare in suspense, their faces illuminated by the spiritual glow. "
                "The cavern walls are covered in thousands of luminescent violet moon-orchids and stalactites dripping with crystalline dew. "
                "Spectacular water reflections, bioluminescent particle trails, high dynamic range, intricate cloth folds, cinematic fantasy concept art, trending on ArtStation, 8k --ar 16:9 --style raw"
            )
        },
        {
            "index": 3,
            "range": (26, 38),
            "title": ["REFINING JADE SKIN GU", "MIDNIGHT SCHEMING"],
            "fallback_color": (20, 30, 25),
            "prompt": (
                "A moody 16:9 cinematic dark cultivation chamber scene inside a wooden mountain garret lit solely by blue moonlight through carved window screens. "
                "In the sharp foreground limelight, Fang Yuan sits cross-legged on a woven bamboo mat, bare-chested with muscular young definition, his pale skin transforming "
                "into translucent, crystalline mutton-fat jade as he successfully refines the Rank 2 Jade Skin Gu. "
                "On the low dark mahogany table before him rest stacks of polished, translucent blue primeval stones, an opened ancient bamboo scroll, "
                "and an ornate brass basin filled with spirit herbs. "
                "A faint, spectral silhouette of his twin brother Fang Zheng and the village elders looms metaphorically in the swirling incense smoke behind him. "
                "Hyper-realistic skin subsurface scattering, sharp jade luster, deep atmospheric shadows, tactile bamboo and aged paper textures, "
                "dark psychological cultivation thriller aesthetic, 8k digital render --ar 16:9 --style raw"
            )
        },
        {
            "index": 4,
            "range": (39, 50),
            "title": ["DEMONIC RISE", "CLASH OF THE THREE CLANS"],
            "fallback_color": (30, 15, 20),
            "prompt": (
                "A grand 16:9 cinematic combat confrontation on the misty bamboo ridge of Qing Mao Mountain at golden sunset. "
                "In the dramatic center, Fang Yuan stands indomitable in dark green battle robes, commanding a swarm of glowing Moonlight Gu and Razor-Wing Gu "
                "that circle his arms like crescent energy blades, his expression merciless and deadpan. "
                "Opposite him across the red mountain rocks stands Bai Ning Bing—an arrogant, white-haired genius with piercing icy blue irises and a cold demonic smile, "
                "conjuring jagged glacial ice-spikes that surge across the forest floor. "
                "In the far background, towering watchtowers and clan banners from Gu Yue, Bai, and Xiong villages clash amidst smoke and flying sparks. "
                "Intense sunset chiaroscuro (fiery orange sunlight colliding with cold blue glacial ice), flying bamboo leaves, volumetric dust, "
                "photorealistic martial arts dark fantasy, Unreal Engine 5 showcase, 8k --ar 16:9 --style raw"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
