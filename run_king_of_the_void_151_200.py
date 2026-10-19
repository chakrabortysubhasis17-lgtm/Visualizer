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
    "novel_slug": "transmigrated-to-a-dark-fantasy-world-of-sss-rank-king-of-the-void",
    "start_url": "https://freewebnovel.com/novel/transmigrated-to-a-dark-fantasy-world-of-sss-rank-king-of-the-void/chapter-151",
    "start_chapter": 151,
    "end_chapter": 200,
    "default_topic": "King of the Void",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_king_of_the_void_151_200",
    "final_audio": "output_king_of_the_void_151_200.mp3",
    "final_video": "final_king_of_the_void_151_200.mp4",
    "cover_image": "cover_king_of_the_void_151_200.jpg",
    "timestamps_file": "youtube_timestamps_king_of_the_void_151_200.txt",
    "subtitles_file": "subtitles_king_of_the_void_151_200.srt",
    "payload_file": "youtube_upload_payload_king_of_the_void_151_200.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "ABYSSAL PANTHEON EXTINCTION! SSS-RANK VOID MONARCH CONSUMES THE ELDER GODS [Ch 151-200] | Dark Fantasy Audiobook Marathon",
    "tags": [
        "King of the Void", "Dark Fantasy Audiobook", "Transmigrated SSS-Rank", "Void Magic",
        "Overpowered MC", "Dark Fantasy LitRPG", "Antihero Audiobook", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Breaching the dimensional boundaries between the mortal realms and the cosmic outer expanse, our transmigrated "
        "Void Monarch ascends into the domain of ancient slumbering gods!\n\n"
        "As the divine celestial pantheons descend with apocalyptic holy decrees to cleanse his heretical existence, "
        "our protagonist elevates his SSS-Rank Void authority into conceptual reality-devouring extinction. Primordial singularities, "
        "black star collapses, and absolute dimensional erasure reduce ancient archangels and elder horrors into mere fuel "
        "for his ever-expanding hollow throne.\n\n"
        "From desecrating forgotten god-graves and plundering ancient cosmic relics to binding primeval astral titans under his banner, "
        "watch him wage an unholy war against the cosmos itself and claim absolute supremacy as the Sovereign of Nothingness!\n\n"
        "Welcome to Chapters 151 to 200 of 'Transmigrated to a Dark Fantasy World of SSS-Rank: King of the Void' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 151: Breaching the Astral Barrier: Entering the Realm of the Elder Pantheons\n"
        "• Ch 157: Plundering the Slumbering God-Grave: Reclaiming the Nether Sovereign Eye\n"
        "• Ch 164: Celestial Fleet Ambush: Obliterating Golden Dreadnoughts with Black Singularities\n"
        "• Ch 171: The Black Sun Ritual: Absorbing Extinct Star Cores into the Void Matrix\n"
        "• Ch 178: Awakening the Spectral Knight Vanguard: Expanding the Undying Shadow Legion\n"
        "• Ch 184: Duel with the High Celestial Arbiter: Disintegrating Divine Law with Void Blades\n"
        "• Ch 191: Subjugating the Primordial Void Leviathan in the Deep Astral Sea\n"
        "• Ch 200: Supreme Void Emperor Coronation: Undisputed Ruler of Existence and Nothingness\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#KingOfTheVoid #DarkFantasyAudiobook #SSSRank #VoidMagic #LitRPG #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Streamlined for Zero Generation Failures)
    "blocks": [
        {
            "index": 1, "range": (151, 155),
            "title": ["ASTRAL BARRIER", "ELDER PANTHEON REALM"],
            "fallback_color": (20, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of the void protagonist standing before a colossal celestial gateway, cold calculating glare, "
                "eyes glowing with deep violet starlight, wearing tailored midnight-black armored mantle. "
                "Set on the shattered steps of an ancient cosmic gateway, revealing swirling violet spatial nebulae in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (156, 160),
            "title": ["GOD-GRAVE CHAMBER", "SOVEREIGN EYE RELIC"],
            "fallback_color": (15, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist inspecting a floating obsidian elder core, serene ruthless smirk, "
                "dark hair neatly framing his brow. Set inside a subterranean god-grave chamber, "
                "revealing slumbering stone titan statues covered in glowing purple runes in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (161, 165),
            "title": ["CELESTIAL FLEET", "SINGULARITY CLEAVE"],
            "fallback_color": (30, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist raising his open palm wrapped in dense dark-matter lightning, fierce resolute expression, "
                "handsome chiseled jawline. Set atop a floating crystal observation platform, "
                "revealing celestial golden warships fracturing in spatial tears in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (166, 170),
            "title": ["BLACK SUN", "STAR CORE ABSORPTION"],
            "fallback_color": (35, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of the protagonist absorbing dark solar radiation between his hands, intense focused gaze, "
                "eyes burning with violet cosmic fire. Set beneath a colossal black sun eclipse, "
                "revealing fractured mountain ranges bathed in purple twilight in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (171, 175),
            "title": ["SHADOW VANGUARD", "KNIGHT SOVEREIGN COMMAND"],
            "fallback_color": (20, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist directing his shadow vanguard with commanding authority, subtle confident smile, "
                "wearing reinforced obsidian shoulder pauldrons. Set in a grand subterranean stone courtyard, "
                "revealing spectral void knights kneeling with dark-steel greatswords in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (176, 180),
            "title": ["ASTRAL MAUSOLEUM", "DIVINITY HARVEST"],
            "fallback_color": (25, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of the protagonist examining an ancient glowing divinity crystal, watchful analytical eyes, "
                "fingers lightly tapping glowing runic etchings. Set inside a forgotten astral mausoleum, "
                "revealing decaying divine relics and broken marble columns in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (181, 185),
            "title": ["ARBITER DUEL", "DIVINE LAW DISINTEGRATION"],
            "fallback_color": (30, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of the protagonist stepping forward in decisive sword stance, sharp cold glare, "
                "holding a slender black void blade. Set on the marble dais of an imperial sanctuary, "
                "revealing an arbiter in shattered golden armor collapsing in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (186, 190),
            "title": ["OUTER CITADEL", "DOMAIN EXPANSION"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of the protagonist overseeing his expanded outer citadel, calm satisfied expression, "
                "dark noble robes billowing in the wind. Set upon the high battlement of a black-crystal fortress, "
                "revealing glowing purple barrier domes shielding vast misty territories in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (191, 195),
            "title": ["VOID LEVIATHAN", "PRIMORDIAL SUBJUGATION"],
            "fallback_color": (25, 15, 45),
            "prompt": (
                "Cinematic 3D portrait of the protagonist raising an obsidian scepter to command the cosmos, commanding regal posture, "
                "eyes glowing with incandescent violet power. Set beneath a swirling spatial vortex, "
                "revealing a gargantuan abyssal horror dissolving into stardust in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (196, 200),
            "title": ["SUPREME VOID EMPEROR", "ABSOLUTE EXTINCTION"],
            "fallback_color": (20, 15, 50),
            "prompt": (
                "Cinematic 3D portrait of the Supreme Void Emperor seated upon an ancient black-crystal throne, serene invincible aura, "
                "eyes glowing with radiant cosmic purple starlight, wearing imperial void sovereign mantle. "
                "Set inside the Grand Astral Palace overlooking boundless secured realms beneath an aurora sky in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
