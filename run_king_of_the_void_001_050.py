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
    "start_url": "https://freewebnovel.com/novel/transmigrated-to-a-dark-fantasy-world-of-sss-rank-king-of-the-void/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "King of the Void",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_king_of_the_void_001_050",
    "final_audio": "output_king_of_the_void_001_050.mp3",
    "final_video": "final_king_of_the_void_001_050.mp4",
    "cover_image": "cover_king_of_the_void_001_050.jpg",
    "timestamps_file": "youtube_timestamps_king_of_the_void_001_050.txt",
    "subtitles_file": "subtitles_king_of_the_void_001_050.srt",
    "payload_file": "youtube_upload_payload_king_of_the_void_001_050.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "SSS-RANK VOID MONARCH AWAKENS! TRANSMIGRATED INTO A BRUTAL DARK FANTASY WORLD [Ch 1-50] | Dark Fantasy Audiobook Marathon",
    "tags": [
        "King of the Void", "Dark Fantasy Audiobook", "Transmigrated SSS-Rank", "Void Magic",
        "Overpowered MC", "Dark Fantasy LitRPG", "Antihero Audiobook", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Transmigrated into a grim, blood-drenched dark fantasy world plagued by horrific curses and corrupt holy orders, "
        "our protagonist awakens the forbidden supreme talent: SSS-Rank [King of the Void]!\n\n"
        "In a shattered realm where commoners are sacrifice fodder and aristocrats barter with eldritch horrors, "
        "he commands the absolute power of nothingness. Spatial tears, void disintegration, abyssal summoning, and reality-devouring "
        "black flames answer his beck and call. From surviving brutal inquisitorial purges to slaughtering mutant blood-beasts and "
        "dismantling tyrannical noble syndicates, he crushes every enemy with chilling pragmatic dominance.\n\n"
        "Watch him construct an untouchable sanctuary of shadow, claim ancient abyssal relics, and establish an empire of the void!\n\n"
        "Welcome to Chapters 1 to 50 of 'Transmigrated to a Dark Fantasy World of SSS-Rank: King of the Void' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 01: Transmigration into the Execution Yard & Awakening the SSS-Rank Void King Talent\n"
        "• Ch 07: Escaping the Inquisitorial Fortress: Disintegrating Holy Knights with Spatial Tears\n"
        "• Ch 14: The Black-Market Necropolis: Trading Eldritch Cores for Forbidden Void Tomes\n"
        "• Ch 21: Slaughter at the Ruined Abbey: Crushing Corrupt Inquisitors with Void Singularity\n"
        "• Ch 28: Awakening the Void Hound Familiar: Taming Shadow Predators from the Outer Dark\n"
        "• Ch 35: Noble Syndicate Ambush: Decimating Aristocratic Mercenaries with Silent Nullification\n"
        "• Ch 42: Blood Moon Calamity: Consuming an Eldritch Abomination Core with Void Hunger\n"
        "• Ch 50: Sovereign of the Hollow Throne: Establishing the First Void Domain\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#KingOfTheVoid #DarkFantasyAudiobook #SSSRank #VoidMagic #LitRPG #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (1, 5),
            "title": ["EXECUTION YARD", "SSS-RANK VOID AWAKENING"],
            "fallback_color": (20, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of a young dark-fantasy antihero standing in a grim stone courtyard, cold calculating glare, "
                "eyes glowing with deep violet void energy, wearing ragged dark prisoner garments and broken iron manacles. "
                "Set in a bloodstained gothic execution yard under a stormy overcast sky, revealing shattered stone scaffolds and terrified inquisitors in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (6, 10),
            "title": ["FORTRESS ESCAPE", "SPATIAL DISINTEGRATION"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of the void protagonist holding his outstretched hand forward, composed ruthless smirk, "
                "fingertips crackling with jagged purple spatial cracks. Set inside a narrow dark-stone fortress corridor, "
                "revealing armored holy knights disintegrating into black dust particles in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (11, 15),
            "title": ["BLACK NECROPOLIS", "FORBIDDEN VOID TOMES"],
            "fallback_color": (15, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of the protagonist inspecting an ancient obsidian grimoire, watchful analytical eyes, "
                "wearing a tailored dark traveling cloak with silver clasps. Set inside an underground gothic market hall lit by dim brass lanterns, "
                "revealing cloaked occult traders and shelves of glowing monster skulls in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (16, 20),
            "title": ["RUINED ABBEY", "VOID SINGULARITY"],
            "fallback_color": (30, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of the protagonist standing before a broken altar, calm commanding aura, "
                "a miniature swirling black singularity floating between his palms. Set inside a ruined gothic cathedral with broken stained-glass windows, "
                "revealing defeated inquisitors collapsed among shattered stone pews in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (21, 25),
            "title": ["SHADOW FAMILIAR", "VOID HOUND PACT"],
            "fallback_color": (20, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist resting his hand on the skull of a shadowy beast, subtle proud smile, "
                "dark hair falling across his forehead. Set in a desolate moonlit pine forest, revealing a sleek Void Hound wreathed in dark smoke and violet eyes sitting obediently in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (26, 30),
            "title": ["SYNDICATE AMBUSH", "SILENT NULLIFICATION"],
            "fallback_color": (25, 20, 25),
            "prompt": (
                "Cinematic 3D portrait of the protagonist in decisive combat stance, sharp cold expression, "
                "wearing reinforced black-leather armor with obsidian shoulder guards. Set on an abandoned cobblestone bridge at midnight, "
                "revealing aristocratic syndicate assassins frozen and absorbed into expanding shadow rifts in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (31, 35),
            "title": ["BLOOD MOON", "ELDRITCH DEVOURING"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic 3D portrait of the protagonist absorbing energy from a crimson eldritch core, intense focused expression, "
                "irises glowing with incandescent violet power. Set atop a jagged rocky precipice under a colossal blood-red moon, "
                "revealing the decaying carcass of a multi-eyed eldritch monstrosity in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (36, 40),
            "title": ["SANCTUARY FOUNDING", "HOLLOW CITADEL"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist overseeing his newly fortified stronghold, arms crossed with calm pride, "
                "wearing a tailored dark nobleman coat. Set upon the high ramparts of a restored ancient dark-stone fortress, "
                "revealing protective violet void barriers shimmering across the surrounding mountain valley in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (41, 45),
            "title": ["INQUISITION PURGE", "THE VOID STORM"],
            "fallback_color": (30, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of the protagonist raising two fingers wrapped in dense dark-matter lightning, fierce commanding posture, "
                "wind whipping his dark mantle. Set against a stormy midnight sky, revealing an invading grand inquisitorial crusade fleet scattered by void shockwaves in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (46, 50),
            "title": ["HOLLOW MONARCH", "KING OF THE VOID"],
            "fallback_color": (20, 15, 45),
            "prompt": (
                "Cinematic 3D portrait of the King of the Void seated upon a carved obsidian throne, serene invincible aura, "
                "eyes glowing with radiant cosmic purple starlight, wearing the sovereign mantle of the Void Monarch. "
                "Set inside a vast gothic throne room overlooking a secured dark empire beneath an aurora twilight sky in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
