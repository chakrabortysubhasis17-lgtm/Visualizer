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
    "novel_slug": "isekai-yururi-kikou-raising-children-while-being-an-adventurer",
    "start_url": "https://freewebnovel.com/novel/isekai-yururi-kikou-raising-children-while-being-an-adventurer/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Adventurer",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 2,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_isekai_yururi_kikou_001_050",
    "final_audio": "output_isekai_yururi_kikou_001_050.mp3",
    "final_video": "final_isekai_yururi_kikou_001_050.mp4",
    "cover_image": "cover_isekai_yururi_kikou_001_050.jpg",
    "timestamps_file": "youtube_timestamps_isekai_yururi_kikou_001_050.txt",
    "subtitles_file": "subtitles_isekai_yururi_kikou_001_050.srt",
    "payload_file": "youtube_upload_payload_isekai_yururi_kikou_001_050.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "RAISING SUPERHUMAN TWINS IN ANOTHER WORLD! [Ch 1-50] | Isekai Yururi Kikou Audiobook Marathon",
    "tags": [
        "Isekai Audiobook", "Isekai Yururi Kikou", "Raising Children While Being an Adventurer",
        "Takumi Kayano", "Allen and Elena", "Slice of Life Fantasy", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Reincarnated into a fantasy world by accident, a gentle adventurer becomes the foster father of two superpowered divine twins!\n\n"
        "After an accidental death caused by the Wind God Sylphreel, Takumi Kayano is given high-tier wind magic, "
        "infinite dimensional storage, and transferred safely into the mysterious Great Forest of Garna. While exploring "
        "the dangerous wilderness, he rescues abandoned five-year-old twins, Allen and Elena. To his astonishment, the little "
        "children carry divine blessings of water and wind, casually taking down high-rank dungeon beasts with their bare hands!\n\n"
        "Registering at the Adventurer's Guild in the town of Shirin, Takumi embarks on a heartwarming yet action-packed journey—cooking "
        "delicious Earth meals, pampering his adorable foster children, and letting the little prodigies effortlessly conquer labyrinths!\n\n"
        "Welcome to Chapters 1 to 50 of 'Isekai Yururi Kikou ~Raising Children While Being an Adventurer~' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 01: Reincarnation in Garna Forest & Encountering the Divine Twins\n"
        "• Ch 08: Wind God Sylphreel's Guidance & Unlocking Infinite Storage\n"
        "• Ch 15: Arrival in Shirin & Adventurer Guild Master Isaac Risner\n"
        "• Ch 22: Allen and Elena's Shocking Combat Instincts vs Forest Wolves\n"
        "• Ch 28: Earth Delicacies Cooking & Wholesome Town Life\n"
        "• Ch 34: Shirin Dungeon Delving & The Twins' Martial Arts Display\n"
        "• Ch 40: Taming the Divine Beast Joule the Fenrir\n"
        "• Ch 45: Subjugating Forest Bandits & Carriage Escort Mission\n"
        "• Ch 50: The Loving Adventurer Family & Setting Out on New Journeys\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#IsekaiYururiKikou #RaisingChildrenWhileBeingAnAdventurer #TakumiKayano #AllenAndElena #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
     "blocks": [
        {
        "index": 1, "range": (1, 5),
        "title": ["GARNA FOREST", "THE DIVINE TWINS"],
        "fallback_color": (20, 35, 25),
        "prompt": (
            "3D portrait close-up, male adventurer, brown hair, hazel eyes, green traveler tunic. "
            "Flawless features, macro studio focus. Background: deep forest, silver-blonde twin children "
            "behind ancient roots. Gold fairylight spores, emerald sunbeams, high contrast, crisp lines, zero blur."
        )
    },
    {
        "index": 2, "range": (6, 10),
        "title": ["SYLPHREEL'S BLESSING", "WIND MAGIC MASTERY"],
        "fallback_color": (20, 35, 45),
        "prompt": (
            "3D portrait layout, young male adventurer, brown hair, azure-gold eyes. "
            "Razor-sharp focus, clean studio lighting. Background: forest clearing, translucent silver-haired wind god. "
            "Sharp cyan wind ribbons, floating golden runes, vivid multi-colored contrast, zero motion blur."
        )
    },
        {
            "index": 3, "range": (11, 15),
            "title": ["TOWN OF SHIRIN", "GUILD REGISTRATION"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of Takumi Kayano, gentle refined features, calm amber eyes, "
                "wearing a tailored adventurer mantle over clean leather armor, holding twin children by their hands. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside the bustling wooden Adventurer Guild hall of Shirin, revealing Guild Master Isaac Risner and guild staff "
                "watching in pleasant surprise in the distance. Illumination from warm hanging brass chandeliers and sunlight through stained glass windows, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (16, 20),
            "title": ["TODDLER MARTIAL ARTS", "WOLF PACK SLAY"],
            "fallback_color": (25, 30, 20),
            "prompt": (
                "Cinematic 3D portrait of an amused male guardian adventurer, soft brown hair, bright smiling hazel eyes, "
                "holding a wooden practice staff resting lightly on his shoulder. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on an open grassy meadow bordering dark woods, revealing little Allen and Elena performing high-flying flying kicks "
                "that effortlessly send giant fang wolves tumbling in the distance. Illumination from bright midday sunbeams and glowing blue water mana trails, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (21, 25),
            "title": ["EARTH DELICACIES", "GOURMET COOKING"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of a smiling young male foster father, neat dark hair, cheerful amber eyes, "
                "wearing a rustic linen cooking apron over brown adventurer garments. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set at a cozy outdoor camping campsite by a sparkling river, revealing little twins excitedly clapping hands "
                "over delicious steaming plates of glazed meat and baked buns in the distance. Illumination from flickering campfire embers and warm golden sunset glow, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (26, 30),
            "title": ["SHIRIN DUNGEON", "TWIN EXPLORERS"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of an alert male adventurer protector, windswept hair, sharp protective azure-hazel eyes, "
                "wearing light mithril-chainmail underneath his travel coat. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a mystical subterranean labyrinth cave with glowing blue crystal stalactites, revealing the little twins "
                "fearlessly collecting rare glowing medicinal mushrooms in the distance. Illumination from radiant sapphire cave crystals and floating fireflies, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (31, 35),
            "title": ["DIVINE BEAST JOULE", "FENRIR TAMING"],
            "fallback_color": (25, 35, 50),
            "prompt": (
                "Cinematic 3D portrait of Takumi Kayano, calm composed expression, glowing amber eyes, "
                "gently extending his hand forward in a taming gesture. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in a scenic alpine flower meadow, revealing an enormous magnificent silver-white Fenrir wolf Joule nuzzling affectionately "
                "against laughing little Allen and Elena in the distance. Illumination from shimmering celestial starlight particles and pure white wind auras, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (36, 40),
            "title": ["CARRIAGE DEFENSE", "BANDIT SUBJUGATION"],
            "fallback_color": (35, 20, 20),
            "prompt": (
                "Cinematic 3D portrait of a commanding young male adventurer, serious expression, glowing wind-blade magic swirling around his fingers. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set along a rocky mountain highway pass, revealing defeated "
                "forest bandits pinned firmly to the ground by miniature hydrostatic vortexes cast by the children in the distance. "
                "Illumination from razor-sharp emerald wind arcs and warm carriage lantern beams, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (41, 45),
            "title": ["COASTAL EXCURSION", "SEASIDE HARVEST"],
            "fallback_color": (15, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of a relaxed young male traveler, short brown hair, warm smiling eyes, "
                "wearing comfortable rolled-up linen shirts and traveler trousers. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on a pristine white sandy beach overlooking turquoise ocean waves, revealing Allen and Elena joyfully chasing "
                "magical harmless sea turtles along the surf in the distance. Illumination from bright tropical sunlight reflections and shimmering azure water foam, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (46, 50),
            "title": ["ADVENTURER FAMILY", "JOURNEY TO NEW HORIZONS"],
            "fallback_color": (25, 30, 40),
            "prompt": (
                "Cinematic 3D portrait of Adventurer Takumi Kayano holding smiling twins Allen and Elena on his shoulders, "
                "refined gentle features, joyful glowing golden eyes, wearing top-tier silver-trimmed ranger robes. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set atop a high scenic grassy hill overlooking a grand fantasy capital city with soaring white spires in the distance. "
                "Illumination from a breathtaking sunrise casting brilliant golden, peach, and lavender light rays across the vast horizon, "
                "deep depth of field with high contrast details throughout."
            )
        }
    ]
}


if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
