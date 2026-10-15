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

CONFIG = {
    # Credentials (Loaded dynamically from api_credentials.json with env fallback)
    "gemini_api_key": creds.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", ""),
    "cf_account_id": creds.get("cloudflare_account_id") or os.environ.get("CLOUDFLARE_ACCOUNT_ID", ""),
    "cf_api_token": creds.get("cloudflare_api_token") or os.environ.get("CLOUDFLARE_API_TOKEN", ""),

    # Novel & Episode Parameters
    "novel_slug": "entry-cultivation-i-can-copy-entries",
    "start_url": "https://mtl-novel.com/novel/entry-cultivation-i-can-copy-entries/chapter-51-a-new-one-of-great-fortune-an-opportunity-given-along-the-way/",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "Entry Cultivation",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_entry_cultivation_051_100",
    "final_audio": "output_entry_cultivation_051_100.mp3",
    "final_video": "final_entry_cultivation_051_100.mp4",
    "cover_image": "cover_entry_cultivation_051_100.jpg",
    "timestamps_file": "youtube_timestamps_entry_cultivation_051_100.txt",
    "subtitles_file": "subtitles_entry_cultivation_051_100.srt",
    "payload_file": "youtube_upload_payload_entry_cultivation_051_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "COPYING RED-TIER FORTUNE ENTRIES! STEADY CULTIVATION SHATTERS SECT PRODIGIES [Ch 51-100] | Xianxia Progression Audiobook Marathon",
    "tags": [
        "Entry Cultivation", "I Can Copy Entries", "Xianxia Audiobook",
        "Progression Fantasy", "Cultivation Marathon", "Overpowered System", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Armed with the unique ability to perceive and replicate the innate talent entries of anyone he meets, "
        "our cautious protagonist Lu Yuan continues his relentless ascent through the immortal cultivation world!\n\n"
        "While arrogant sect prodigies, blessed children of heaven, and ancient legacy heirs flaunt their rare bloodlines, "
        "Lu Yuan quietly copies their supreme entries behind the scenes—stacking [Great Fortune], [Innate Sword Bone], "
        "[Alchemical Dao Heart], and [Heavenly Spiritual Veins] into an unprecedented divine foundation!\n\n"
        "From navigating perilous inner sect promotion trials and out-refining grandmaster alchemists to slaughtering ruthless "
        "evil cultivator ambushes without leaving a trace of karma, watch Lu Yuan master the art of steady, low-key invincibility!\n\n"
        "Welcome to Chapters 51 to 100 of 'Entry Cultivation: I Can Copy Entries' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 51: Encountering the Son of Destiny: Copying the Golden [Great Fortune] Entry\n"
        "• Ch 56: Inner Sect Promotion Exam: Sweeping Martial Trials with Concealed Sword Qi\n"
        "• Ch 62: Pill Pavilion Infiltration: Upgrading the [Grandmaster Alchemical Affinity] Entry\n"
        "• Ch 68: Secret Realm Expedition: Plundering Ancient Spiritual Vein Reserves in Secret\n"
        "• Ch 74: Ruthless Counter-Purge: Decimating Blood-Sect Assassins with Zero Karmic Traces\n"
        "• Ch 80: Foundation Stage Perfection: Fusing Multi-Tier Entries into a Golden Dao Core\n"
        "• Ch 86: Auction Pavilion Treasure Appraisal: Unearthing Dormant Mythic Dragon Bloodlines\n"
        "• Ch 92: Sect Grand Tournament: Crushing Proud Core Disciples with Basic Techniques\n"
        "• Ch 100: Flawless Transcendence: The Low-Key Master of Innate Heavenly Entries\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#EntryCultivation #ICanCopyEntries #XianxiaAudiobook #ProgressionFantasy #CultivationAudiobook #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (51, 55),
            "title": ["GREAT FORTUNE", "ENTRY REPLICATION"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of young cultivator Lu Yuan, calm calculating gaze, neat black hair tied with a dark-wood hairpin, "
                "wearing subtle charcoal-grey outer sect disciple robes. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside a bustling mountain sect marketplace, revealing glowing translucent golden entry status panels floating above a passing youth's head in the distance. "
                "Illumination from warm afternoon sunbeams and radiant golden text reflections, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (56, 60),
            "title": ["INNER SECT TRIAL", "CONCEALED SWORD MASTERY"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan standing in composed martial poise, serene expression, holding an unadorned iron longsword. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set upon a high stone combat platform above mountain clouds, "
                "revealing shattered spirit puppet targets and astonished sect elders watching from the pavilion terrace in the distance. "
                "Illumination from sharp silver blade glints and cool mountain morning mist, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (61, 65),
            "title": ["PILL PAVILION", "ALCHEMICAL DAO HEART"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan refining high-tier spiritual pills, intense artistic focus, palms directing swirling vermilion alchemy flames. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a fragrant stone apothecary grotto, "
                "revealing a heavy bronze cauldron hovering mid-air emitting cloud-shaped medicinal vapors and glowing herb jars in the distance. "
                "Illumination from roaring crimson furnace fires and soft amber medicinal light, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (66, 70),
            "title": ["SECRET REALM EXPEDITION", "SPIRIT VEIN HARVEST"],
            "fallback_color": (15, 30, 25),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan crouching at the boundary of an ancient ruin, watchful cautious eyes, dark cloak blending with shadowed foliage. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set within an overgrown bioluminescent primordial forest, "
                "revealing an underground spirit spring bubbling with luminous liquid jade energy in the distance. "
                "Illumination from glowing emerald forest moss and soft cyan water ripples, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (71, 75),
            "title": ["NOCTURNAL PURGE", "ZERO KARMIC RESIDUE"],
            "fallback_color": (25, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan in swift counter-strike posture, cold decisive glare, fingertips tracing a silent wind-blade talisman. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set along a jagged mountain pass under heavy rain, "
                "revealing masked blood-sect ambushers dissolving into harmless spiritual dust without leaving traces in the distance. "
                "Illumination from pale silver lightning flashes and sharp shadow contrasts, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (76, 80),
            "title": ["FOUNDATION PERFECTION", "ENTRY FUSION"],
            "fallback_color": (30, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan meditating cross-legged, tranquil transcendent aura, glowing golden and violet entry characters orbiting his dantian. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a sealed underground spirit cavern, "
                "revealing solid stone walls illuminated by concentric spiritual shockwaves rippling across the chamber in the distance. "
                "Illumination from brilliant purple core energy and luminous golden status matrices, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (81, 85),
            "title": ["AUCTION PAVILION", "MYTHIC ENTRY APPRAISAL"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan examining an antique rusted iron relic, subtle knowing smirk, intelligent analytical gaze. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set in a private viewing booth of an opulent immortal auction hall, "
                "revealing a dormant crimson dragon-bloodline entry tag glowing faintly through the rust in the distance. "
                "Illumination from warm red lantern light and glistening polished rosewood display cases, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (86, 90),
            "title": ["SECT TOURNAMENT", "EFFORTLESS SUPREMACY"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan standing casually with one hand behind his back, calm dismissive expression, dark sleeves fluttering in the wind. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set in the center of the grand white-jade martial ring, "
                "revealing an elite core disciple's blazing spear attack redirected harmlessly into the barrier shield in the distance. "
                "Illumination from brilliant midday stadium sun and bright blue barrier flares, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (91, 95),
            "title": ["ANCIENT BEAST LAIR", "SPIRITUAL ACCORD"],
            "fallback_color": (25, 35, 30),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan extending a gentle hand toward an ancient slumbering white tiger spirit, respectful fearless presence. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a misty celestial bamboo grove, "
                "revealing glowing golden beast-taming and spiritual affinity entry tags harmonizing in mid-air in the distance. "
                "Illumination from dappled emerald canopy light and glowing spiritual dust motes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (96, 100),
            "title": ["SOVEREIGN ENTRY MASTER", "PEAK FOUNDATION"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan overlooking the boundless sea of clouds from an immortal mountain cliff at sunset, serene invincible posture, "
                "wearing refined dark-blue inner elder robes trimmed with silver cloud borders. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set against a breathtaking mountain horizon with floating sect islands and soaring immortal cranes in the distance. "
                "Illumination from rich golden sunset rays, soft twilight clouds, and countless shimmering golden entry matrices, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
