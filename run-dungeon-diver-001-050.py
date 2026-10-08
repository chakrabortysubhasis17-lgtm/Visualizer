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
    "novel_slug": "dungeon-diver-stealing-a-monsters-power",
    "start_url": "https://freewebnovel.com/novel/dungeon-diver-stealing-a-monsters-power/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Dungeon",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 2,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_dungeon_diver_001_050",
    "final_audio": "output_dungeon_diver_001_050.mp3",
    "final_video": "final_dungeon_diver_001_050.mp4",
    "cover_image": "cover_dungeon_diver_001_050.jpg",
    "timestamps_file": "youtube_timestamps_dungeon_diver_001_050.txt",
    "subtitles_file": "subtitles_dungeon_diver_001_050.srt",
    "payload_file": "youtube_upload_payload_dungeon_diver_001_050.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "I CAN STEAL MONSTER POWERS! THE ULTIMATE DUNGEON DIVER [Ch 1-50] | LitRPG Audiobook Marathon",
    "tags": [
        "LitRPG Audiobook", "Dungeon Diver Stealing A Monster's Power", "Jay Soju",
        "Monster Power Stealer", "Progression Fantasy", "Dungeon Diver", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "In a world where awakening as an elite hunter is reserved for the wealthy, one desperate porter breaks the rules!\n\n"
        "Unable to afford college tuition or standard awakening serums, 20-year-old Jay Soju risks his life savings to hire "
        "a beginner raid party for a single goblin kill in the Alpine Square Dungeon. When the beast falls, the impossible occurs: "
        "Jay unlocks an unprecedented cheat skill that allows him to permanently steal and absorb the traits, instincts, "
        "and supernatural powers of every monster he slays!\n\n"
        "From an ignored baggage porter to an unstoppable apex predator accompanied by the primordial flame spirit Ember, "
        "witness Jay's rapid ascension as he conquers subterranean labyrinths and terrorizes dungeon bosses!\n\n"
        "Welcome to Chapters 1 to 50 of 'Dungeon Diver: Stealing A Monster's Power' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 01: The Broke Porter & Slaying the Alpine Square Goblin\n"
        "• Ch 10: Awakening the Monster Steal Skill & First Stat Explosion\n"
        "• Ch 18: Primordial Dragon Ember Awakens & Hellfire Soul Resonance\n"
        "• Ch 25: Teaming with Natalie the Healer & Rapid Dungeon Clearance\n"
        "• Ch 32: Dane's Gale Force Arrival & Alpine Catacomb Incursion\n"
        "• Ch 40: Subjugating the Armored Ogre Warlord & Stealing Titan Resilience\n"
        "• Ch 50: Sovereign Dungeon Diver & Multi-Skill Hybrid Evolution\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#DungeonDiver #StealingAMonstersPower #JaySoju #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (1, 5),
            "title": ["ALPINE SQUARE", "THE BROKE PORTER"],
            "fallback_color": (15, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of a determined young male hunter, messy dark hair, sharp amber-gold eyes, "
                "wearing scuffed tactical leather porter gear and fingerless steel-mesh gloves. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against the damp stone entrance cavern of Alpine Square Dungeon, revealing glowing blue moss-covered stalagmites "
                "and green-skinned goblin scouts lurking in the dark shadows in the distance. Illumination from a translucent blue status window and warm amber torch flames, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (6, 10),
            "title": ["MONSTER STEAL", "FIRST AWAKENING"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of a young male hunter, short black hair, intense glowing cyan eyes, "
                "wearing reinforced tactical carbon-fiber chest armor over a dark tunic. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a jagged subterranean cavern, revealing a slain armored horned wolf dissolving into shimmering golden "
                "mana particles in the distance. Illumination from swirling neon-blue skill absorption tendrils and radiant golden level-up notifications, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (11, 15),
            "title": ["FLAME SPIRIT", "EMBER AWAKENS"],
            "fallback_color": (35, 15, 15),
            "prompt": (
                "Cinematic 3D portrait of an evolving male diver, windswept dark hair, fiery amber-crimson eyes, "
                "wearing dark obsidian leather combat armor with glowing magma veins. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against an ancient volcanic ruin deep within the dungeon floor, revealing the spectral silhouette of Ember the primordial "
                "dragon flame spirit roaring with blazing ruby wings in the distance. Illumination from crackling volcanic embers and roaring scarlet hellfire arcs, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (16, 20),
            "title": ["BROKER CHESTER", "BLACK MARKET ALLIANCE"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of a confident male hunter, neat black hair, calm calculating golden eyes, "
                "wearing a tailored charcoal-and-navy adventurer overcoat with brass buckles. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a clandestine underground merchant vault, revealing glass display cases filled with glowing enchanted monster cores "
                "and broker Chester inspecting rare loot in the distance. Illumination from warm brass lantern beams and shimmering purple crystal reflections, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (21, 25),
            "title": ["HEALER NATALIE", "DEPTH INVASION"],
            "fallback_color": (15, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of an athletic male dungeon diver, sleek black hair, sharp electric-blue eyes, "
                "wearing dark titanium-plated hunter armor. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in a luminous crystal-lined cave corridor, revealing beautiful healer Natalie in white-and-emerald robes casting radiant green "
                "restoration barriers in the distance. Illumination from soft emerald healing rings and brilliant cyan cave crystals, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (26, 30),
            "title": ["TITAN OGRE", "BRUTE STRENGTH STEAL"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of a battle-hardened male diver, dark hair whipped by kinetic shockwaves, fierce glowing amber eyes, "
                "wearing heavy chitin-reinforced battle pauldrons. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a shattered subterranean colosseum, revealing a colossal armored Ogre Warlord with a massive spiked iron club "
                "staggering backward under a devastating strike in the distance. Illumination from crackling crimson kinetic sparks and deep cavern torchlight, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (31, 35),
            "title": ["WIND USER DANE", "TEMPEST SYNERGY"],
            "fallback_color": (20, 35, 45),
            "prompt": (
                "Cinematic 3D portrait of a commanding young male hunter, sharp angular features, piercing turquoise-gold eyes, "
                "wearing aerodynamic midnight-black combat garb with silver wind runes. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set along an underground abyss bridge, revealing archer Dane releasing howling green gale arrows into charging monster hordes "
                "in the distance. Illumination from glowing jade vortex blades and crackling sapphire plasma bolts, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (36, 40),
            "title": ["ROGUE AMBUSH", "SHADOW EXECUTION"],
            "fallback_color": (30, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of a lethal male predator diver, sleek jet-black hair, cold luminous violet-amber eyes, "
                "wielding dual stolen monster-bone daggers dripping with shadowy mist. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a dark subterranean crypt, revealing defeated rogue syndicate hunters fleeing across fractured stone sarcophagi "
                "in the distance. Illumination from eerie violet shadow flames and razor-sharp silver blade glints, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (41, 45),
            "title": ["CHIMERA ABYSS", "MULTI-POWER SURGE"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of a dominant male hunter master, dark hair, brilliant dual-colored crimson-and-azure eyes, "
                "wearing pitch-black dragon-scale mantle armor with pulsing runic engravings. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against the edge of a bottomless subterranean chasm, revealing a three-headed chimera monster roaring under concentrated "
                "elemental bombardment in the distance. Illumination from blazing golden lightning pillars and roaring violet flame columns, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (46, 50),
            "title": ["APEX DIVER", "MONSTER OVERLORD"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of Diver Jay Soju at peak power, refined dark hair, majestic glowing golden-amber eyes, "
                "wearing ornate imperial dark-silver battle robes infused with stolen draconic scales. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set atop an overlooking dungeon throne balcony, revealing conquered subterranean labyrinth halls glowing with allied hunter banners "
                "stretching toward the horizon in the distance. Illumination from radiant auroras of emerald, violet, and sunrise-gold mana fields, "
                "deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
