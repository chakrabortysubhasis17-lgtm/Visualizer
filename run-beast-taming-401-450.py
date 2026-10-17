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
    "start_url": "https://freewebnovel.com/novel/beast-taming-reincarnated-with-the-ultimate-bond-system/chapter-451",
    "start_chapter": 451,
    "end_chapter": 500,
    "default_topic": "Beast Taming",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_beast_taming_451_500",
    "final_audio": "output_beast_taming_451_500.mp3",
    "final_video": "final_beast_taming_451_500.mp4",
    "cover_image": "cover_beast_taming_451_500.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_451_500.txt",
    "subtitles_file": "subtitles_beast_taming_451_500.srt",
    "payload_file": "youtube_upload_payload_beast_taming_451_500.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "ETERNAL CREATION ANCESTOR BEAST SOVEREIGN! ULTIMATE BOND SYSTEM ABSOLUTE FINALE [Ch 451-500] | Beast Taming Audiobook Marathon",
    "tags": [
        "Beast Taming Audiobook", "Ultimate Bond System", "Reincarnated Beast Tamer",
        "Progression Fantasy", "Mythic Evolution", "Monster Taming LitRPG", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Reaching the ultimate creation boundary of existence, our protagonist enters the Eternal Ancestor Realm to finalize his cosmic conquest!\n\n"
        "Fully supercharged by the complete evolutionary registry of the Ultimate Bond System, his legendary beast legions attain primordial ancestor status. "
        "From awakening the Origin Chaos Ancestor Dragon and forging absolute spiritual oneness with the Multi-Versal World Trees to unifying "
        "all dimensional laws into a single everlasting creation singularity, every heartbeat alters the fundamental architecture of reality.\n\n"
        "When the final primordial void entities and absolute extinction forces threaten to erase all multi-versal timelines, our protagonist "
        "unleashes the ultimate synchronized bond domain to secure everlasting peace and supreme creation hegemony!\n\n"
        "Welcome to Chapters 451 to 500 of 'Beast Taming: Reincarnated with the Ultimate Bond System' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 451: Entering the Eternal Ancestor Realm & Awakening Origin Creation Laws\n"
        "• Ch 458: Origin Chaos Dragon Evolution: Unifying Multi-Versal Time-Space Streams\n"
        "• Ch 465: The Supreme Ancestor Tribunal: Subjugating Primeval Extinction Overlords\n"
        "• Ch 472: World Tree Symbiosis: Linking All Dimension Ecosystems into a Single Soul Matrix\n"
        "• Ch 479: Eradicating the Void Annihilation Swarm with Absolute Creation Singularity Waves\n"
        "• Ch 486: Transcendental Bond Synchronization: Achieving Infinite Multi-Versal Omnipresence\n"
        "• Ch 493: The Final Extinction War: Shattering the Ultimate Reality-Wiping Entity\n"
        "• Ch 500: Eternal Ancestor Sovereign Coronation: The Absolute Creator of All Existence\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#BeastTaming #UltimateBondSystem #MonsterEvolution #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Fully Streamlined & Stable)
    "blocks": [
        {
            "index": 1, "range": (451, 455),
            "title": ["ETERNAL ANCESTOR REALM", "ORIGIN CREATION LAWS"],
            "fallback_color": (20, 20, 60),
            "prompt": (
                "Cinematic 3D portrait of a supreme beast tamer entering the Eternal Ancestor Realm, serene invincible posture, "
                "glowing golden-prismatic eyes reflecting cosmic creation matrices, wearing primordial sovereign robes. "
                "Set atop a floating crystal altar above infinite universe clusters, revealing magnificent golden creation lotuses in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (456, 461),
            "title": ["ORIGIN CHAOS DRAGON", "TIME-SPACE UNIFICATION"],
            "fallback_color": (25, 15, 55),
            "prompt": (
                "Cinematic 3D portrait of the beast tamer standing calmly in a zero-gravity origin sanctum, intelligent focused expression, "
                "hands holding a glowing orb of golden starlight. Set inside an ancient cosmic temple, revealing a colossal Chaos Dragon wreathed in temporal runic rings in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (462, 467),
            "title": ["ANCESTOR TRIBUNAL", "EXTINCTION OVERLORDS SUBJUGATED"],
            "fallback_color": (35, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of the tamer standing in absolute supremacy, confident regal smirk, hair windswept by ancestral aura shockwaves. "
                "Set within the grand Ancestor Tribunal hall, revealing primeval extinction overlords collapsing onto fractured tiles in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (468, 473),
            "title": ["WORLD TREE SYMBIOSIS", "ECOSYSTEM SOUL MATRIX"],
            "fallback_color": (15, 35, 25),
            "prompt": (
                "Cinematic 3D portrait of the tamer touching a massive glowing botanical trunk, watchful razor-sharp gaze, fingers crackling with emerald life energy. "
                "Set at the heart of the Multi-Versal World Tree, revealing glowing golden roots threading through planetary biomes in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (474, 479),
            "title": ["VOID SWARM ANNIHILATION", "CREATION SINGULARITY"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of the tamer commanding absolute creation shockwaves, noble resolute presence, eyes blazing with prismatic power. "
                "Set against the dark void of outer reality, revealing void swarms dissolving into harmless golden stardust under an expanding singularity in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (480, 485),
            "title": ["TRANSCENDENTAL SYNCHRONIZATION", "OMNIPRESENT COMMAND"],
            "fallback_color": (20, 25, 60),
            "prompt": (
                "Cinematic 3D portrait of the tamer in profound spiritual synchronization, serene divine aura, golden origin runes glowing across his brow. "
                "Set within an infinite multi-dimensional sanctum, revealing crystal nodes connecting to every universe across existence in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (486, 491),
            "title": ["FINAL EXTINCTION WAR", "REALITY-WIPING ENTITY"],
            "fallback_color": (30, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of the tamer directing the final reality war, sharp commanding jawline, raising an outstretched hand surrounded by prismatic halos. "
                "Set against fracturing space-time, revealing the ultimate reality-wiping entity shattered into light particles by his dragon legion in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (492, 496),
            "title": ["ETERNAL SANCTUARY", "ALL REALMS UNITED"],
            "fallback_color": (25, 30, 40),
            "prompt": (
                "Cinematic 3D portrait of the tamer overlooking a peaceful new universe, calm satisfied smile, wearing tailored sovereign robes. "
                "Set upon the observation balcony of an eternal tower, revealing diverse mythic beasts roaming across peaceful star-systems in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (497, 499),
            "title": ["ANCESTOR MATRIX", "INFINITE SYSTEM ASCENT"],
            "fallback_color": (25, 20, 60),
            "prompt": (
                "Cinematic 3D portrait of the tamer touching a glowing system orb, intense artistic focus, fingers tracing floating runic arrays. "
                "Set inside a pristine crystal foundry, revealing bright energy conduits channeling liquid starlight into the final matrix in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (500, 500),
            "title": ["ETERNAL ANCESTOR SOVEREIGN", "ABSOLUTE CREATOR OF EXISTENCE"],
            "fallback_color": (20, 20, 65),
            "prompt": (
                "Cinematic 3D portrait of the Eternal Ancestor Sovereign Beast Emperor at the pinnacle of creation, commanding sun-gold irises, "
                "wearing imperial ancestor robes. Set atop the Grand Spire overlooking united existence, revealing infinite mythic bonded beasts soaring under an aurora sky. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
