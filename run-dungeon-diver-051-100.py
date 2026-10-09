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
    "start_url": "https://freewebnovel.com/novel/dungeon-diver-stealing-a-monsters-power/chapter-51",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "Dungeon",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 2,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_dungeon_diver_051_100",
    "final_audio": "output_dungeon_diver_051_100.mp3",
    "final_video": "final_dungeon_diver_051_100.mp4",
    "cover_image": "cover_dungeon_diver_051_100.jpg",
    "timestamps_file": "youtube_timestamps_dungeon_diver_051_100.txt",
    "subtitles_file": "subtitles_dungeon_diver_051_100.srt",
    "payload_file": "youtube_upload_payload_dungeon_diver_051_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "DEVOURING APEX MONSTER SOULS! THE CLASS 4 DIVER ASCENSION [Ch 51-100] | LitRPG Audiobook",
    "tags": [
        "LitRPG Audiobook", "Dungeon Diver Stealing A Monster's Power", "Jay Soju",
        "Monster Power Stealer", "Progression Fantasy", "Dungeon Diver", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "The former broke porter dives deeper into the subterranean abyss as an unstoppable predator!\n\n"
        "Having shattered the limitations of ordinary hunters, Jay Soju leads his inner team deeper into uncharted catacombs "
        "and lethal mid-tier dungeon layers. With every high-rank beast that falls before his blade, his unique theft skill "
        "absorbs devastating traits—from supersonic shadow-steps to draconic hellfire armor!\n\n"
        "Accompanied by the growing draconic power of flame spirit Ember, Natalie's unbreakable divine wards, and Dane's tempest archery, "
        "Jay challenges elite syndicate death squads, slays ancient crypt lords, and turns dangerous labyrinths into his personal hunting grounds!\n\n"
        "Welcome to Chapters 51 to 100 of 'Dungeon Diver: Stealing A Monster's Power' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 51: Abyssal Chasm Incursion & Stealing the Shadow-Stalker Speed Core\n"
        "• Ch 60: The Alpine Underground Catacombs & Confronting the Crypt Lord\n"
        "• Ch 68: Ember's Juvenile Dragon Metamorphosis & Hellfire Breath Unleashed\n"
        "• Ch 75: Class 4 Hunter Assessment & The Mana Meter Rupture\n"
        "• Ch 82: Syndicate Hit Squad Ambush & Cold-Blooded Retribution\n"
        "• Ch 90: Subterranean Lava Trench & Slaying the Molten Wyrm Boss\n"
        "• Ch 95: Black Market Relic Auction with Broker Chester\n"
        "• Ch 100: Sovereign Apex Diver Ascendance & Multi-Trait Dominance\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#DungeonDiver #StealingAMonstersPower #JaySoju #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (51, 55),
            "title": ["ABYSS CHASM", "SHADOW-STALKER CORE"],
            "fallback_color": (15, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of an evolving male dungeon diver, sleek black hair, piercing glowing violet-azure eyes, "
                "wearing lightweight obsidian-trimmed stealth armor with glowing kinetic conduits. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against a massive subterranean abyss chasm filled with jagged floating rocks, revealing a slain shadow-stalker mantis beast "
                "dissolving into deep-purple stolen skill particles in the distance. Illumination from neon-violet speed trails and cool teal luminescent abyss moss, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (56, 60),
            "title": ["CATACOMB RUINS", "THE CRYPT LORD"],
            "fallback_color": (25, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of an athletic young male hunter, windswept dark hair, fierce glowing amber eyes, "
                "holding twin engraved bone daggers dripping with arcane venom. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside an ancient subterranean tomb hall, revealing a towering four-armed skeletal Crypt Lord draped in ragged royal purple silks "
                "shattered under heavy combat in the distance. Illumination from eerie cyan soul flames and crackling amethyst lightning arcs, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (61, 65),
            "title": ["EMBER'S EVOLUTION", "DRACONIC METAMORPHOSIS"],
            "fallback_color": (40, 15, 15),
            "prompt": (
                "Cinematic 3D portrait of Diver Jay Soju, commanding expression, sharp black hair, brilliant blazing crimson-gold eyes, "
                "wearing heavy dark dragon-scale breastplate armor. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set upon an overlooking cliff of an underground molten cavern, revealing the majestic juvenile form of flame spirit Ember "
                "spreading enormous radiant ruby dragon wings in the distance. Illumination from blinding scarlet hellfire vortexes and roaring volcanic magma rivers, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (66, 70),
            "title": ["DIVINE WARD", "NATALIE'S RESOLVE"],
            "fallback_color": (15, 35, 30),
            "prompt": (
                "Cinematic 3D portrait of a battle-tested male diver, calm confident gaze, neat dark hair, glowing turquoise-gold eyes, "
                "wearing dark titanium battle robes with silver clasps. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set along a narrow crystalline cavern bridge, revealing healer Natalie channeling an enormous dome of golden-emerald "
                "divine protective light to repel charging subterranean beast packs in the distance. Illumination from warm sun-gold healing halos and cool blue crystal shards, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (71, 75),
            "title": ["CLASS 4 TEST", "MANA SENSOR RUPTURE"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of a poised young male hunter, neat black hair, calm imposing expression with electric-blue pupils, "
                "wearing a tailored charcoal-and-navy hunter coat over dark tactical garments. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside an official modern Hunter Association testing arena, revealing a giant mana measurement monolith "
                "fracturing under explosive energy discharge with stunned proctors jumping back in the distance. Illumination from blinding cyan-white magical shockwaves, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (76, 80),
            "title": ["TEMPEST MARKSMAN", "DANE'S GALE FORCE"],
            "fallback_color": (20, 35, 40),
            "prompt": (
                "Cinematic 3D portrait of a tactical male hunter leader, sharp facial planes, focused amber-gold eyes, "
                "wearing reinforced midnight-blue combat gear with runic pauldrons. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on a high cavern ledge overlooking a grand subterranean waterfall, revealing wind-marksman Dane releasing massive "
                "spiraling emerald gale arrows that pierce through armored subterranean manticores in the distance. Illumination from radiant jade wind vortexes and sparkling mist spray, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (81, 85),
            "title": ["SYNDICATE AMBUSH", "SHADOW RETRIBUTION"],
            "fallback_color": (35, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of an unyielding male hunter sovereign, razor-sharp jawline, cold glowing violet eyes, "
                "wielding an obsidian long dagger wreathed in tendrils of stolen shadow magic. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside an abandoned subterranean sewer labyrinth, revealing defeated rogue syndicate assassins disarmed and pinned "
                "against crumbling brick walls in the distance. Illumination from sharp silver blade glints and deep violet shadow mists, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (86, 90),
            "title": ["MOLTEN TRENCH", "LAVA WYRM PURGE"],
            "fallback_color": (45, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of a powerful male diver, dark hair whipped by fiery updrafts, fierce glowing sun-gold eyes, "
                "wearing blackened dragon-bone mantle armor resisting extreme heat. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set beside a colossal subterranean magma trench, revealing an immense armored Lava Wyrm bursting from the molten lava "
                "under a barrage of concentrated magical strikes in the distance. Illumination from exploding volcanic geysers and crackling golden lightning spears, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (91, 95),
            "title": ["CHESTER'S VAULT", "ANCIENT RELIC DEAL"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of a wealthy master hunter, refined handsome features, calculating golden eyes, "
                "wearing an elegant dark-velvet formal trench coat with gold filigree stitching. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside an opulent underground auction house vault, revealing broker Chester showcasing an ancient glowing draconic "
                "artifact inside an enchanted glass pedestal in the distance. Illumination from warm brass chandeliers and shimmering magenta enchantment runes, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (96, 100),
            "title": ["APEX SOVEREIGN", "MULTI-TRAIT EMPEROR"],
            "fallback_color": (25, 25, 50),
            "prompt": (
                "Cinematic 3D portrait of Jay Soju at the pinnacle of Class 4 power, majestic windswept dark hair, brilliant dual-ringed sapphire-and-crimson eyes, "
                "wearing ornate imperial dark-silver dragon armor radiating multiple colored energy currents. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set atop the highest throne tower of a cleared subterranean fortress floor, revealing allied hunter legions cheering below "
                "under vast vaulted cavern ceilings in the distance. Illumination from breathtaking celestial auroras of neon blue, deep violet, and sunrise-gold mana, "
                "deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
