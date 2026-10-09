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
    "start_url": "https://freewebnovel.com/novel/beast-taming-reincarnated-with-the-ultimate-bond-system/chapter-51",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "Beast Tamer",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 1,  # Kept sequential to respect 15 RPM limits cleanly
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_beast_taming_051_100",
    "final_audio": "output_beast_taming_051_100.mp3",
    "final_video": "final_beast_taming_051_100.mp4",
    "cover_image": "cover_beast_taming_051_100.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_051_100.txt",
    "subtitles_file": "subtitles_beast_taming_051_100.srt",
    "payload_file": "youtube_upload_payload_beast_taming_051_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "AWAKENING MYTHIC BEAST SOVEREIGNS! ULTIMATE BOND REVOLUTION [Ch 51-100] | LitRPG Audiobook Marathon",
    "tags": [
        "LitRPG Audiobook", "Beast Taming", "Ultimate Bond System", "Reincarnated With The Ultimate Bond System",
        "Progression Fantasy", "Familiar Evolution", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Breaking past regional academy limitations, our reincarnated master steps onto the continental battlefield!\n\n"
        "Having unlocked the true potential of his contracted familiars, our protagonist enters high-tier dimensional rift zones "
        "and ancient beast sanctuaries. Through the continuous feedback of the Ultimate Bond System, his soul space expands "
        "exponentially, enabling multi-pet soul fusion, mythic ancestral awakenings, and impenetrable domain fields!\n\n"
        "Facing elite grandmaster beast tamers, ancient subterranean leviathans, and deep-rift mutant swarms, "
        "watch him lead his mythical companion legion to complete dominance!\n\n"
        "Welcome to Chapters 51 to 100 of 'Beast Taming: Reincarnated With The Ultimate Bond System!' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 51: Deep Abyss Rift Incursion & Unlocking High-Rank Soul Resonance\n"
        "• Ch 60: Familiar Bloodline Metamorphosis & The Primordial Winged Sovereign\n"
        "• Ch 68: Multi-Beast Domain Fusion & Repelling the Syndicate Ambush\n"
        "• Ch 75: Continental Beast Tamer Grand Tournament Preliminaries\n"
        "• Ch 82: Slaying the Ancient Abyssal Hydra & Contracting the Third Familiar\n"
        "• Ch 90: Grand Altar Resonance & The Imperial Spirit Covenant\n"
        "• Ch 95: Crushing S-Rank Legacy Prodigies in the Central Arena\n"
        "• Ch 100: Sovereign Mythic Beast Master Ascendance & Rift Lord Subjugation\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#BeastTaming #UltimateBondSystem #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (51, 55),
            "title": ["ABYSS INVASION", "SOUL RESONANCE"],
            "fallback_color": (15, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of an evolving male beast tamer, commanding expression, neat dark hair, radiant electric-azure eyes, "
                "wearing reinforced midnight-blue combat armor with glowing kinetic conduits. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a jagged subterranean abyss canyon, revealing massive floating rift crystals and his evolved "
                "spirit familiar radiating bright cyan energy trails in the distance. Illumination from neon-blue soul contract rings and cool teal abyss moss, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (56, 60),
            "title": ["BLOODLINE METAMORPHOSIS", "WINGED SOVEREIGN"],
            "fallback_color": (25, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of a young master tamer, windswept dark hair, confident amber-cyan eyes, "
                "wearing dark titanium battle robes with silver clasps. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set atop an overlooking mountain cliff at sunset, revealing a majestic winged celestial spirit beast "
                "unfurling radiant prismatic feather wings against thunderclouds in the distance. Illumination from blinding white-gold solar flares "
                "and shimmering aura feathers, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (61, 65),
            "title": ["DOMAIN FUSION", "SHADOW SYNDICATE"],
            "fallback_color": (35, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of a battle-tested tamer leader, razor-sharp jawline, cold glowing violet-gold pupils, "
                "wearing dark obsidian stealth armor with protective runic armguards. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in a dark ancient ruins courtyard shrouded in heavy mist, revealing defeated enemy syndicate assassins "
                "and their corrupted shadow beasts pinned down by an expanding dual-elemental barrier in the distance. "
                "Illumination from neon-violet barrier glyphs and crimson spark arcs, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (66, 70),
            "title": ["DIVINE BEAST COVENANT", "SPIRIT WATERFALL"],
            "fallback_color": (15, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of a poised male beast contractor, calm dignified gaze, dark hair, glowing turquoise irises, "
                "holding a floating translucent ancestral covenant seal above his palm. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set beside an immense subterranean crystal waterfall, revealing an ancient serpentine water spirit beast "
                "circling gently through glowing mist pools in the distance. Illumination from sparkling cyan water ripples and ambient crystal glow, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (71, 75),
            "title": ["GRAND TOURNAMENT", "ARENA DISRUPTION"],
            "fallback_color": (30, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of a tactical tamer prodigy, sharp facial planes, fierce focused sapphire eyes, "
                "wearing tailored charcoal-and-gold academy representative coats over dark tactical garments. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a colossal circular tournament colosseum packed with tens of thousands of cheering spectators, "
                "revealing an opposing grandmaster's titanic iron behemoth recoiling from a devastating soul shockwave in the distance. "
                "Illumination from blinding cyan-white magical shockwaves and cheering spectator braziers, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (76, 80),
            "title": ["THIRD FAMILIAR", "ABYSS HYDRA PURGE"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of a dominant master tamer, dark hair whipped by kinetic updrafts, fierce sun-gold eyes, "
                "wearing blackened dragon-scale mantle armor resisting intense venom heat. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on the edge of a boiling subterranean magma marsh, revealing a colossal multi-headed shadow hydra "
                "collapsing under a coordinated barrage from his contracted beasts in the distance. Illumination from exploding crimson fire geysers "
                "and golden lightning spears, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (81, 85),
            "title": ["SACRED ALTAR", "IMPERIAL BLOODLINE"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of a young tamer undergoing spiritual breakthrough, serene expression, radiant amethyst pupils, "
                "touching an ancient floating imperial glyph pillar. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set within a forgotten celestial sanctuary chamber, revealing three contracted mythic familiars bathing in "
                "cascading pillars of starlight mana in the distance. Illumination from radiant violet soul fire and floating golden divine characters, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (86, 90),
            "title": ["LEGACY DUEL", "PRODIGY CRUSHED"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of an unyielding young sovereign tamer, sleek black hair, cold imposing expression with dual-colored pupils, "
                "standing upright with hands clasped behind his back. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in an upscale marble grandmaster duel arena, revealing an arrogant legacy clan champion and his rare mutated "
                "griffin grounded and disarmed under invisible gravitational pressure in the distance. Illumination from neon-violet gravity waves "
                "and gleaming arena lanterns, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (91, 95),
            "title": ["RIFT OVERLORD", "TITAN BEAST WAVE"],
            "fallback_color": (25, 35, 45),
            "prompt": (
                "Cinematic 3D portrait of a victorious tamer commander, razor-sharp jawline, glowing sun-gold eyes, "
                "wearing high-tier mithril-inlaid commander armor with a fluttering deep-navy cape. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set upon the high battlements of an outer fortress city, revealing a massive corrupted rift titan collapsing "
                "under a combined tempest-and-hellfire assault from his pets in the distance. Illumination from sunrise-gold magical artillery beams "
                "and billowing smoke trails, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (96, 100),
            "title": ["MYTHIC SOVEREIGN", "APEX TAMER ASCENT"],
            "fallback_color": (20, 25, 50),
            "prompt": (
                "Cinematic 3D portrait of the Sovereign Beast Master at the apex of continental power, majestic windswept dark hair, "
                "brilliant dual-ringed sapphire-gold eyes, wearing imperial dark-silver sovereign robes radiating multi-colored elemental halos. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set atop a soaring cliff overlooking boundless mythical realms, "
                "revealing towering ancestral dragon, phoenix, and fenrir familiars standing loyally behind him under a breathtaking sunrise sky. "
                "Illumination from brilliant auroras of sunrise gold, cyan soul fire, and deep-violet mana, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
