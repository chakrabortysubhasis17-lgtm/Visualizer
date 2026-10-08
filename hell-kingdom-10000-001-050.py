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
    "novel_slug": "10000x-reward-multiplier-hell-level-kingdom-building",
    "start_url": "https://freewebnovel.com/novel/10000x-reward-multiplier-hell-level-kingdom-building/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Kingdom",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 2,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_hell_kingdom_001_050",
    "final_audio": "output_hell_kingdom_001_050.mp3",
    "final_video": "final_hell_kingdom_001_050.mp4",
    "cover_image": "cover_hell_kingdom_001_050.jpg",
    "timestamps_file": "youtube_timestamps_hell_kingdom_001_050.txt",
    "subtitles_file": "subtitles_hell_kingdom_001_050.srt",
    "payload_file": "youtube_upload_payload_hell_kingdom_001_050.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "10,000X REWARD MULTIPLIER! HELL-LEVEL KINGDOM BUILDING [Ch 1-50] | LitRPG Audiobook Marathon",
    "tags": [
        "LitRPG Audiobook", "10000x Reward Multiplier", "Hell-level Kingdom Building", "Floki Ironside",
        "Kingdom Building", "System Lord", "Progression Fantasy", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Transmigrated into a harsh fantasy wilderness as the young chieftain of a starving, ruined frontier village!\n\n"
        "Facing freezing winters, ravenous monster hordes, and ruthless rival lords, Floki Ironside inherits the "
        "impoverished settlement of Ironside Village. Just as collapse seems inevitable, Floki unlocks a heaven-defying cheat: "
        "The 10,000x Reward Multiplier System! Every resource collected, quest completed, and enemy defeated has its rewards "
        "multiplied tenfold, a hundredfold, and up to ten-thousandfold!\n\n"
        "A single basket of wheat yields a fortress granary; basic iron clubs transform into legendary mithril battleaxes; "
        "and humble barbarian hunters evolve into an invincible legion of superhuman warriors. Watch Floki conquer the desolate "
        "badlands and build an unshakeable empire from the ground up!\n\n"
        "Welcome to Chapters 1 to 50 of '10,000x Reward Multiplier: Hell-level Kingdom Building' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 01: Transmigrating to Ironside & The 10,000x Multiplier Awakening\n"
        "• Ch 08: Miracle Harvest & Restoring Old Charleston's Health\n"
        "• Ch 15: Arming the Barbarian Trio with Multiplied Steel Equipment\n"
        "• Ch 22: Flame-Wolf Beast Tide Slay & Exponential EXP Explosion\n"
        "• Ch 28: Fortress Wall Construction & Ironside Territory Level-Up\n"
        "• Ch 35: Ambush by Kellan Blackstone's Slaver Scouts & Ruthless Defense\n"
        "• Ch 42: Securing the Abyssal Iron Mine & Forging Mythic Weapons\n"
        "• Ch 50: Sovereign Chieftain Floki & The Unbreachable Badlands Empire\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#10000xMultiplier #KingdomBuilding #FlokiIronside #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (1, 5),
            "title": ["IRONSIDE DESOLATION", "THE 10,000X MULTIPLIER"],
            "fallback_color": (25, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of a young male chieftain, rugged dark-brown hair, sharp amber-gold eyes, "
                "wearing weather-beaten wolf-fur mantle and reinforced leather chieftain armor. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against an impoverished rustic wooden village in a barren windswept valley, revealing starving villagers "
                "and dilapidated huts under an overcast grey sky in the distance. Illumination from a glowing golden system interface window with numeric multiplier grids, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (6, 10),
            "title": ["MIRACLE HARVEST", "HEALING OLD CHARLESTON"],
            "fallback_color": (30, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of a confident young barbarian lord, neat dark hair, radiant determined hazel-gold eyes, "
                "wearing a clean fur-lined tunic with polished bronze clasps. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set beside an overflowing wooden granary bursting with giant golden wheat ears, revealing recovered elder Charleston "
                "walking joyfully among lush green farmland in the distance. Illumination from warm golden agricultural vitality auras and bright morning sunbeams, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (11, 15),
            "title": ["BARBARIAN TRIO", "STEEL ARMAMENT UPGRADE"],
            "fallback_color": (35, 20, 20),
            "prompt": (
                "Cinematic 3D portrait of a commanding young chieftain, windswept dark hair, fierce amber eyes, "
                "wearing heavy studded iron pauldron armor. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in an outdoor blacksmith yard with glowing anvil sparks, revealing the hulking barbarian brothers Viktor, Anton, and Jabba "
                "brandishing gleaming heavy steel broadaxes in the distance. Illumination from blazing forge fire embers and gleaming metallic weapon reflections, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (16, 20),
            "title": ["FLAME-WOLF TIDE", "MULTIPLIED EXP SURGE"],
            "fallback_color": (40, 15, 15),
            "prompt": (
                "Cinematic 3D portrait of an athletic male warrior lord, sharp black hair, blazing golden eyes, "
                "wielding an engraved glowing broadsword with runic edge. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on a rocky perimeter ridge at dusk, revealing a slain pack of mutated red-furred flame wolves dissolving into "
                "masses of shimmering golden level-up particles in the distance. Illumination from roaring crimson wolf-fire braziers and golden level-up pillars, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (21, 25),
            "title": ["FORTRESS PALISADE", "TERRITORY EVOLUTION"],
            "fallback_color": (20, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of Chieftain Floki, refined dark hair, focused tactical amber-gold eyes, "
                "holding a rolled parchment architectural blueprint in hand, wearing polished steel chest armor. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set overlooking Ironside settlement, revealing towering newly erected stone battlements and fortified wooden watchtowers "
                "rising rapidly under construction in the distance. Illumination from glowing cyan construction matrix runes and warm amber torchlit scaffoldings, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (26, 30),
            "title": ["BLACKSTONE SCOUTS", "RUTHLESS RETALIATION"],
            "fallback_color": (35, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of a stern imposing male lord, sleek dark hair, cold calculating violet-amber eyes, "
                "wearing blackened steel battle armor with wolf-fur trim. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in a misty mountain forest pass, revealing defeated mercenary scouts from Blackstone territory captured and disarmed "
                "by towering barbarian guards in the distance. Illumination from razor-sharp silver blade glints and cool pre-dawn blue mist, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (31, 35),
            "title": ["MITHRIL DEPOSITS", "ABYSSAL MINE CONQUEST"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of a victorious young monarch, dark windswept hair, glowing sapphire-amber eyes, "
                "wearing reinforced mithril-inlaid scale armor. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a massive subterranean iron mine, revealing towering carts brimming with shimmering purple mithril ore "
                "and bustling miner crews in the distance. Illumination from luminescent blue cave crystals and glowing golden smelting furnace flues, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (36, 40),
            "title": ["HOBGOBLIN WARLORD", "TITANIC DEFENSE"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of a battle-hardened male chieftain, dark hair whipped by violent wind, fierce golden eyes, "
                "wearing heavy dragon-bone shoulder guards over steel battle plate. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set before the massive fortress gate of Ironside, revealing a colossal armored Hobgoblin King staggering backward "
                "under a devastating defensive volley in the distance. Illumination from crackling kinetic impact sparks and roaring perimeter flame traps, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (41, 45),
            "title": ["LEGENDARY ARMORY", "VANGUARD CRUSH"],
            "fallback_color": (30, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of Lord Floki, dignified handsome features, piercing radiant golden eyes, "
                "wearing an ornate dark-steel mantle adorned with pure gold filigree. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set across the fortified stone courtyard, revealing hundreds of fully armored barbarian shock-troopers armed with "
                "masterwork glowing weapons standing in disciplined formation in the distance. Illumination from swirling magenta magic banners and sunrise golden rays, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (46, 50),
            "title": ["SOVEREIGN OF IRONSIDE", "BADLANDS DOMINION"],
            "fallback_color": (25, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of Sovereign Chieftain Floki Ironside, refined dark hair, majestic glowing amber-gold eyes, "
                "wearing imperial black-and-gold chieftain robes with a rich velvet-lined mantle. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set upon the high obsidian citadel balcony, revealing a thriving sprawling stone fortress metropolis with smoking chimneys "
                "and waving lion-crest banners stretching across the valley in the distance. Illumination from brilliant auroras of sunrise gold, violet, and emerald mana, "
                "deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
