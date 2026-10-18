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
    "start_url": "https://freewebnovel.com/novel/transmigrated-to-a-dark-fantasy-world-of-sss-rank-king-of-the-void/chapter-51",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "King of the Void",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_king_of_the_void_051_100",
    "final_audio": "output_king_of_the_void_051_100.mp3",
    "final_video": "final_king_of_the_void_051_100.mp4",
    "cover_image": "cover_king_of_the_void_051_100.jpg",
    "timestamps_file": "youtube_timestamps_king_of_the_void_051_100.txt",
    "subtitles_file": "subtitles_king_of_the_void_051_100.srt",
    "payload_file": "youtube_upload_payload_king_of_the_void_051_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "ABYSSAL VOID DOMAIN EXPANSION! SSS-RANK VOID MONARCH CRUSHES THE HOLY EMPIRE [Ch 51-100] | Dark Fantasy Audiobook Marathon",
    "tags": [
        "King of the Void", "Dark Fantasy Audiobook", "Transmigrated SSS-Rank", "Void Magic",
        "Overpowered MC", "Dark Fantasy LitRPG", "Antihero Audiobook", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Having secured the Hollow Citadel, our transmigrated antihero expands his dominion across the blood-soaked dark continent!\n\n"
        "As the corrupt Holy Empire declares an all-out crusade to eradicate his heretical existence, our protagonist demonstrates "
        "the horrifying reality of SSS-Rank [King of the Void]. Armed with spatial collapse fields, nullification singularities, "
        "and an army of shadow predators, he turns defensive war into systematic extermination. High inquisitorial prelates, "
        "arrogant holy paladins, and subterranean demon barons alike discover that against absolute nothingness, divine armor "
        "and ancient pacts are utterly worthless.\n\n"
        "Watch him conquer forgotten catacombs, bind primeval void knights, and force imperial legions to bend the knee!\n\n"
        "Welcome to Chapters 51 to 100 of 'Transmigrated to a Dark Fantasy World of SSS-Rank: King of the Void' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 051: Fortifying the Hollow Citadel & Repelling the Vanguard Crusader Scouts\n"
        "• Ch 058: Descent into the Cursed Catacombs: Reclaiming Ancient Void Scepter Relics\n"
        "• Ch 065: The Holy Inquisitor Ambush: Obliterating Iron Paladins with Spatial Tears\n"
        "• Ch 072: Duel with the Corrupt Prelate: Nullifying Golden Divine Light with Black Flames\n"
        "• Ch 079: The Abyssal Blood Lake Expedition: Consuming Demonic Baron Cores with Void Hunger\n"
        "• Ch 086: Awakening the Void Knight Legion: Binding Undying Shadow Warriors to the Throne\n"
        "• Ch 092: Nocturnal Counter-Assault: Eradicating Aristocratic Occult Syndicates\n"
        "• Ch 100: Continental Void Monarch Ascension: Establishing Hegemony Over the Empire\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#KingOfTheVoid #DarkFantasyAudiobook #SSSRank #VoidMagic #LitRPG #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (51, 55),
            "title": ["CITADEL DEFENSE", "CRUSADER VANGUARD ROUT"],
            "fallback_color": (20, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of the void protagonist standing on fortress ramparts, cold analytical expression, "
                "eyes glowing with deep violet void energy, wearing tailored black leather coat with silver buckles. "
                "Set atop the high stone walls of the Hollow Citadel, revealing retreating armored crusader scouts in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (56, 60),
            "title": ["CURSED CATACOMBS", "ANCIENT VOID RELIC"],
            "fallback_color": (15, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of the protagonist inspecting an ancient obsidian scepter, watchful sharp gaze, "
                "fingers tracing glowing purple runic engravings on the artifact. Set inside a subterranean gothic stone crypt lit by pale mist, "
                "revealing carved stone sarcophagi and broken statues in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (61, 65),
            "title": ["SPATIAL AMBUSH", "PALADIN DISINTEGRATION"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of the void protagonist holding his open palm forward, calm composed smirk, "
                "fingertips crackling with jagged purple spatial tears. Set along a rocky mountain pass under stormy dark skies, "
                "revealing golden-armored holy paladins turning into black dust particles in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (66, 70),
            "title": ["PRELATE DUEL", "NULLIFYING DIVINE LIGHT"],
            "fallback_color": (30, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of the protagonist commanding a swirling black singularity between his hands, resolute icy glare, "
                "dark hair windswept by kinetic air pressure. Set in a grand gothic stone square, revealing a corrupt holy prelate collapsing "
                "as his golden staff shatters in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (71, 75),
            "title": ["ABYSSAL BLOOD LAKE", "DEVOURING DEMON CORES"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic 3D portrait of the protagonist absorbing energy from a crimson demon core, intense focused expression, "
                "dark eyes blazing with violet power. Set on the stone shores of an eerie subterranean blood-red lake, "
                "revealing the defeated carcass of a colossal horned demon in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (76, 80),
            "title": ["VOID KNIGHT PACT", "SHADOW LEGION AWAKENING"],
            "fallback_color": (20, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist raising his dark hand with commanding authority, subtle confident smile, "
                "wearing reinforced black-iron pauldrons over dark armor. Set inside a grand underground fortress hall, "
                "revealing kneeling spectral void knights wreathed in dark smoke in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (81, 85),
            "title": ["NOCTURNAL PURGE", "OCCULT SYNDICATE FALL"],
            "fallback_color": (25, 20, 25),
            "prompt": (
                "Cinematic 3D portrait of the protagonist in decisive combat stance, sharp ruthless gaze, "
                "holding a slender black blade wrapped in violet void currents. Set upon an abandoned cobblestone bridge at midnight, "
                "revealing masked occult syndicate mercenaries vanishing into spatial rifts in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (86, 90),
            "title": ["BLACK SUN ECLIPSE", "DIMENSIONAL COLLAPSE"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic 3D portrait of the protagonist gazing upward at a dark celestial eclipse, serene proud aura, "
                "two fingers extended to channel atmospheric spatial rifts. Set upon the high battlement of an ancient tower, "
                "revealing a black sun ring casting purple twilight over the surrounding misty valleys in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (91, 95),
            "title": ["IMPERIAL DEFIANCE", "SHATTERING THE DECREE"],
            "fallback_color": (30, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of the protagonist tearing an imperial gold-sealed proclamation with calm disdain, sharp commanding jawline, "
                "wind blowing dark strands across his brow. Set on the marble steps of a conquered fortress, "
                "revealing retreating royal inquisitors fleeing into mountain fog in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (96, 100),
            "title": ["CONTINENTAL MONARCH", "HOLLOW THRONE HEGEMONY"],
            "fallback_color": (20, 15, 45),
            "prompt": (
                "Cinematic 3D portrait of the King of the Void seated upon the Grand Hollow Throne, serene invincible presence, "
                "eyes glowing with radiant cosmic purple starlight, wearing the sovereign mantle of the Void Monarch. "
                "Set inside a vast gothic cathedral hall overlooking a secured dark empire beneath an aurora twilight sky in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
