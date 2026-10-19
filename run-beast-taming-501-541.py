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
    "novel_slug": "beast-taming-reincarnated-with-the-ultimate-bond-system",
    "start_url": "https://freewebnovel.com/novel/beast-taming-reincarnated-with-the-ultimate-bond-system/chapter-501",
    "start_chapter": 501,
    "end_chapter": 541,
    "default_topic": "Beast Taming",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_beast_taming_501_541",
    "final_audio": "output_beast_taming_501_541.mp3",
    "final_video": "final_beast_taming_501_541.mp4",
    "cover_image": "cover_beast_taming_501_541.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_501_541.txt",
    "subtitles_file": "subtitles_beast_taming_501_541.srt",
    "payload_file": "youtube_upload_payload_beast_taming_501_541.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "BEYOND CREATION REALM! PRIMORDIAL BOND TRANSCENDENCE & COSMIC ORIGIN CONQUEST [Ch 501-541] | Beast Taming Audiobook Marathon",
    "tags": [
        "Beast Taming Audiobook", "Ultimate Bond System", "Reincarnated Beast Tamer",
        "Progression Fantasy", "Mythic Evolution", "Monster Taming LitRPG", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Pushing beyond the boundaries of the Eternal Ancestor Realm, our protagonist steps into the uncharted Origin Void "
        "to finalize absolute cosmic sovereignty!\n\n"
        "With the Ultimate Bond System operating at supreme transcendent capacity, his bonded apex beasts evolve beyond universal "
        "rules and physical dimensions. From commanding the Primordial Starlight Behemoth to harmonizing all origin timelines "
        "through the Infinite Soul Nexus, every step cements his status as the undisputed architect of existence.\n\n"
        "Watch him neutralize ancient cosmic anomalies, guide forgotten primordial pantheons, and construct an eternal multi-dimensional "
        "haven across the final chapters of this legendary saga!\n\n"
        "Welcome to Chapters 501 to 541 of 'Beast Taming: Reincarnated with the Ultimate Bond System' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 501: Crossing the Origin Threshold: Entering the Boundary-Less Void Sea\n"
        "• Ch 505: Primordial Starlight Behemoth Awakening: Unlocking Cosmic Origin Bloodlines\n"
        "• Ch 510: The Sovereign Assembly: Unifying Multi-Versal Dynasties Under One Banner\n"
        "• Ch 514: Ancient Void Anomaly Purge: Cleansing Extinction Pockets with Absolute Bond Qi\n"
        "• Ch 519: Synchronizing the Infinite Soul Nexus Across Multiversal Timelines\n"
        "• Ch 523: Primordial Dragon Sovereign Ascendance: Wings That Encompass Galaxy Clusters\n"
        "• Ch 528: Cosmic Haven Inception: Laying the Foundations of the Undying Sanctuary\n"
        "• Ch 532: Subjugating the Last Primeval Remnant Overlords with Effortless Will\n"
        "• Ch 537: Complete System Integration: The Ultimate Bond Registry Achieves Wholeness\n"
        "• Ch 541: Grand Eternal Conclusion: The Supreme Primordial Overlord of All Existence\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#BeastTaming #UltimateBondSystem #MonsterEvolution #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Streamlined for Zero Generation Failures)
    "blocks": [
        {
            "index": 1, "range": (501, 504),
            "title": ["ORIGIN THRESHOLD", "BOUNDARY-LESS VOID SEA"],
            "fallback_color": (20, 20, 55),
            "prompt": (
                "Cinematic 3D portrait of a transcendent beast tamer crossing the Origin Threshold, serene fearless posture, "
                "glowing golden-prismatic eyes reflecting cosmic starfields, wearing sleek midnight-blue sovereign robes with gold trim. "
                "Set upon a floating crystal road overlooking boundless galaxy seas, revealing massive golden origin gates in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (505, 508),
            "title": ["STARLIGHT BEHEMOTH", "COSMIC BLOODLINE AWAKENING"],
            "fallback_color": (25, 15, 50),
            "prompt": (
                "Cinematic 3D portrait of the beast tamer holding a glowing orb of starlight, calm analytical expression, "
                "fingers tracing floating azure runic arrays. Set inside an ancient zero-gravity sanctum, "
                "revealing a colossal Starlight Behemoth covered in glowing crystal armor standing obediently in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (509, 512),
            "title": ["SOVEREIGN ASSEMBLY", "MULTIVERSAL UNIFICATION"],
            "fallback_color": (35, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of the tamer standing in absolute authority, confident regal smirk, "
                "dark hair neatly tied with a gold dragon pin. Set in the grand hall of the Sovereign Assembly, "
                "revealing multi-versal dynastic leaders bowing in respect along carved marble corridors in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (513, 516),
            "title": ["ANOMALY PURGE", "CLEANSING EXTINCTION POCKETS"],
            "fallback_color": (30, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of the tamer directing a wave of pure golden energy, sharp commanding jawline, "
                "outstretched hand releasing bright celestial light. Set against fractured dark space, "
                "revealing dark void rifts dissolving into harmless golden sparks in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (517, 520),
            "title": ["SOUL NEXUS", "TIMELINE SYNCHRONIZATION"],
            "fallback_color": (20, 25, 60),
            "prompt": (
                "Cinematic 3D portrait of the tamer in profound spiritual meditation, serene divine presence, "
                "intricate golden origin runes glowing across his forehead and cheeks. Set within a luminous nexus chamber, "
                "revealing shimmering crystal pillars connecting parallel dimensional planes in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (521, 524),
            "title": ["DRAGON SOVEREIGN", "GALAXY-SPANNING WINGS"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of the tamer standing atop a high observation platform, proud noble demeanor, "
                "eyes blazing with brilliant amber-gold power. Set against a backdrop of deep space nebulae, "
                "revealing a colossal Primordial Chaos Dragon soaring gracefully with glowing wings in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (525, 528),
            "title": ["COSMIC HAVEN", "SANCTUARY FOUNDING"],
            "fallback_color": (15, 35, 25),
            "prompt": (
                "Cinematic 3D portrait of the tamer touching a large floating emerald World Tree seed, warm contented smile, "
                "wearing tailored sovereign armor. Set upon the terrace of a celestial fortress, "
                "revealing lush green floating continents and crystal rivers taking shape across the cosmos in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (529, 532),
            "title": ["FINAL OVERLORDS", "EFFORTLESS SUBJUGATION"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the tamer standing with hands behind his back, cool dismissive gaze, "
                "robes billowing slightly in the cosmic wind. Set on a fractured obsidian battlefield, "
                "revealing the last primeval titan overlords kneeling under an invisible gravitational domain in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (533, 536),
            "title": ["SYSTEM WHOLENESS", "FINAL BOND REGISTRY"],
            "fallback_color": (25, 20, 60),
            "prompt": (
                "Cinematic 3D portrait of the tamer reviewing a hovering golden master system matrix, intense artistic focus, "
                "fingers lightly tapping floating origin glyphs. Set inside a radiant crystal core chamber, "
                "revealing massive streams of pure starlight feeding into a central sovereign engine in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (537, 541),
            "title": ["SUPREME PRIMORDIAL OVERLORD", "ETERNAL CONCLUSION"],
            "fallback_color": (20, 20, 65),
            "prompt": (
                "Cinematic 3D portrait of the Supreme Primordial Overlord standing at the apex of all creation, serene invincible aura, "
                "commanding sun-gold irises, wearing regal robes woven from cosmic starlight. Set atop the Grand Eternal Spire overlooking boundless harmonious universes under a permanent aurora sky in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
