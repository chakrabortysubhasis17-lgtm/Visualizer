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
    "start_url": "https://freewebnovel.com/novel/isekai-yururi-kikou-raising-children-while-being-an-adventurer/chapter-52",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "Yururi Adventurer",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_isekai_yururi_kikou_051_100",
    "final_audio": "output_isekai_yururi_kikou_051_100.mp3",
    "final_video": "final_isekai_yururi_kikou_051_100.mp4",
    "cover_image": "cover_isekai_yururi_kikou_051_100.jpg",
    "timestamps_file": "youtube_timestamps_isekai_yururi_kikou_051_100.txt",
    "subtitles_file": "subtitles_isekai_yururi_kikou_051_100.srt",
    "payload_file": "youtube_upload_payload_isekai_yururi_kikou_051_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "RAISING OVERPOWERED TWINS IN ANOTHER WORLD! COASTAL DUNGEONS & COZY SEAFOOD [Ch 51-100] | Cozy Isekai Audiobook Marathon",
    "tags": [
        "Isekai Yururi Kikou", "Takumi Kayano", "Allen and Elena", "Cozy Fantasy",
        "Slice of Life Isekai", "Raising Children While Being an Adventurer", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Reincarnated into a gentle fantasy realm by the wind god Sylphreel, Takumi Kayano continues "
        "his heartwarming journey raising the adorable, superpowered twin toddlers Allen and Elena!\n\n"
        "Leaving the beginner towns behind, the joyful family travels toward the bustling coastal territory of Bailey. "
        "Between exploring vibrant ocean markets, discovering fresh seafood, and experimenting with delicious new Earth recipes "
        "like fried fish, tempura, and sweet desserts, life as a foster adventurer father has never been more delightful!\n\n"
        "Of course, dungeon exploration remains a breeze when your toddlers can casually dispatch giant sea monsters with flying kicks "
        "while riding aboard their fluffy Fenrir and Celestial Tiger familiars! Settle in for a wholesome, stress-free, and delicious "
        "fantasy adventure!\n\n"
        "Welcome to Chapters 51 to 100 of 'Isekai Yururi Kikou ~Raising Children While Being an Adventurer~' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 51: Heading Toward the Coast: Carriage Travels & Forest Gatherings\n"
        "• Ch 56: Port City Bailey: Ocean Breezes, Busy Docks & Seaside Markets\n"
        "• Ch 62: Seafood Feast: Takumi Introduces Tempura & Fried Fish Delights\n"
        "• Ch 68: Exploring the Coastal Dungeon: Allen & Elena's High-Kick Monster Clear\n"
        "• Ch 74: Fluffy Playtime: Joule and Feat Splash in the Gentle Shallow Waves\n"
        "• Ch 80: Secret Pearl Grotto: Rare Ingredients & Water Magic Harvesting\n"
        "• Ch 86: Local Guild Commendation & Sweet Treats for Friendly Adventurers\n"
        "• Ch 92: Deep Water Chamber Expedition & Effortless Boss Subjugation\n"
        "• Ch 100: Sunset Along the Shoreline: A Loving Family's Unending Wholesome Journey\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#IsekaiYururiKikou #TakumiKayano #AllenAndElena #CozyFantasy #IsekaiAudiobook #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (51, 55),
            "title": ["COASTAL ROADWAY", "CARRIAGE JOURNEY"],
            "fallback_color": (25, 35, 45),
            "prompt": (
                "Cinematic 3D portrait of gentle adventurer Takumi Kayano, kind expressive dark-brown eyes, neat dark-brown hair, "
                "friendly warm smile, wearing practical light-leather adventurer attire with blue linen accents. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set beside a rustic wooden travel carriage "
                "along a scenic ocean cliffside road, revealing energetic twin toddlers Allen and Elena pointing excitedly at the shimmering blue sea "
                "and rolling waves in the distance. "
                "Illumination from warm golden morning sunlight reflecting off ocean water, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (56, 60),
            "title": ["PORT CITY BAILEY", "SEASIDE HARBOR"],
            "fallback_color": (20, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of Takumi holding hands with little Allen and Elena, relaxed joyful posture, gentle breezes ruffling his hair. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set along the bustling cobblestone harbor promenade of Port City Bailey, "
                "revealing tall-masted wooden sailing ships, colorful seafood vendor canopies, and cheerful townsfolk trading fresh ocean catches in the distance. "
                "Illumination from crisp azure sky daylight with sparkling white ocean spray, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (61, 65),
            "title": ["SEAFOOD MASTERCLASS", "TEMPURA & SWEETS"],
            "fallback_color": (40, 30, 20),
            "prompt": (
                "Cinematic 3D portrait of Takumi acting as a loving chef, cheerful affectionate gaze, neatly rolled sleeves, "
                "holding a wooden skewer with golden crispy fried fish fresh from the pan. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set at an outdoor stone cooking hearth beside a cozy seaside inn, revealing little Allen and Elena with sparkling eyes "
                "happily munching on delicious seafood snacks at a wooden picnic bench in the distance. "
                "Illumination from warm flickering hearth flames and soft afternoon golden-hour sun, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (66, 70),
            "title": ["COASTAL DUNGEON", "TWIN FLYING KICKS"],
            "fallback_color": (15, 35, 40),
            "prompt": (
                "Cinematic 3D portrait of Takumi watching over his children with proud amusement, calm protective stance, light leather rapier scabbard at his hip. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a luminous sea-cavern dungeon with crystalline turquoise tidal pools, "
                "revealing toddlers Allen and Elena leaping into the air delivering superhuman playful kicks that send a comical giant crab monster tumbling backward in the distance. "
                "Illumination from glowing cyan cavern crystals and sparkling water droplets, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (71, 75),
            "title": ["FLUFFY GUARDIANS", "BEACHSIDE PLAYTIME"],
            "fallback_color": (25, 40, 35),
            "prompt": (
                "Cinematic 3D portrait of Takumi kneeling warmly on soft white sand, gentle laughter in his eyes, casual linen travel shirt. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set across a secluded tropical cove beach, "
                "revealing massive majestic Fenrir Joule and fluffy Celestial Tiger Feat lying playfully in the shallow surf as the twins hug their thick silvery fur in the distance. "
                "Illumination from bright sunny turquoise waters and sparkling golden sand reflections, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (76, 80),
            "title": ["PEARL GROTTO", "WATER MAGIC GATHERING"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of Takumi gently channeling water magic, calm focused expression, delicate translucent water spheres swirling "
                "above his outstretched palm. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside a hidden underwater cavern reachable through an air bubble ward, revealing Allen and Elena swimming playfully "
                "and collecting glowing rainbow pearls from giant clams in the distance. "
                "Illumination from ethereal iridescent pearl luminescence and shimmering deep-water blue glow, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (81, 85),
            "title": ["ADVENTURER'S GUILD", "SEASIDE COMMENDATION"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of Takumi at the reception counter, polite humble smile, holding an adventurer guild card with high rank insignia. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside the busy coastal adventurer guild hall, "
                "revealing surprised guild receptionists and veteran armored divers staring in awe at the rare monster materials and giant crab carapaces stacked neatly in the distance. "
                "Illumination from warm amber indoor lanterns and sunlit tavern stained-glass windows, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (86, 90),
            "title": ["STREET FESTIVAL", "SHAVED ICE DELIGHT"],
            "fallback_color": (35, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of Takumi enjoying a festive festival day, relaxed happy expression, holding two wooden cups of shaved fruit ice. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set along an evening lantern-lit festival street by the docks, "
                "revealing Allen and Elena with colorful fruit syrup on their cheeks happily jumping around food stalls while townsfolk laugh warmly in the distance. "
                "Illumination from glowing red and gold paper festival lanterns and twilight indigo sky, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (91, 95),
            "title": ["DEEP SEA GUARDIAN", "FAMILY SYNCHRONIZATION"],
            "fallback_color": (15, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of Takumi commanding a defensive wind shield, firm protective gaze, wind ripples dancing along his leather vambraces. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set within the grand flooded boss chamber of the sea dungeon, "
                "revealing a colossal kraken guardian retreating in defeat as Allen, Elena, Joule, and Feat coordinate an unstoppable flurry of elemental strikes in the distance. "
                "Illumination from swirling emerald wind barriers and bright cyan tidal waves, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (96, 100),
            "title": ["TWILIGHT SHORELINE", "JOYFUL FAMILY VOYAGE"],
            "fallback_color": (35, 25, 30),
            "prompt": (
                "Cinematic 3D portrait of Takumi Kayano walking along the shoreline with Allen and Elena resting sleepily against his shoulders, "
                "heartfelt peaceful smile, serene loving eyes, evening breeze gently swaying his hair. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set along a tranquil sandy beach looking out over a boundless calm sea under an awe-inspiring sunset sky, "
                "revealing Joule and Feat padding faithfully beside them with gentle pawprints in the sand in the distance. "
                "Illumination from rich purple-and-gold sunset gradients reflecting off gentle shoreline ripples, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
