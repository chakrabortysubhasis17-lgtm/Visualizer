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
    "start_url": "https://freewebnovel.com/novel/beast-taming-reincarnated-with-the-ultimate-bond-system/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Beast Tamer",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 2,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_beast_taming_001_050",
    "final_audio": "output_beast_taming_001_050.mp3",
    "final_video": "final_beast_taming_001_050.mp4",
    "cover_image": "cover_beast_taming_001_050.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_001_050.txt",
    "subtitles_file": "subtitles_beast_taming_001_050.srt",
    "payload_file": "youtube_upload_payload_beast_taming_001_050.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "REINCARNATED WITH THE ULTIMATE BOND SYSTEM! [Ch 1-50] | Beast Taming LitRPG Audiobook Marathon",
    "tags": [
        "LitRPG Audiobook", "Beast Taming", "Ultimate Bond System", "Reincarnated With The Ultimate Bond System",
        "Progression Fantasy", "Familiar Evolution", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "In a world where soul space talent defines human destiny, one reincarnated youth breaks all known limits!\n\n"
        "Awakening into a society where contracting high-rank spirit beasts is reserved for legacy clans and wealthy academies, "
        "our protagonist starts with what everyone dismisses as an ordinary, low-potential familiar. But upon binding, "
        "the Ultimate Bond System awakens!\n\n"
        "No contract backlash, infinite synchronization thresholds, and the power to awaken dormant primordial god-beast bloodlines! "
        "Every leap in his familiars' strength directly feeds back into his own physical attributes and combat arts, turning a supposed "
        "back-line pet handler into an unstoppable frontline monster!\n\n"
        "Welcome to Chapters 1 to 50 of 'Beast Taming: Reincarnated With The Ultimate Bond System!' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 01: Reincarnation & Awakening the Ultimate Bond System\n"
        "• Ch 08: Contracting the Initial Familiar & Unlocking the Primordial Lineage\n"
        "• Ch 15: Attribute Feedback Resonance & Shattering Academy Test Records\n"
        "• Ch 22: Wilderness Beast Forest Expedition & Subjugating Mutated Predators\n"
        "• Ch 29: Contracting the Second Divine Beast & Dual Elemental Synergy\n"
        "• Ch 35: Crushing Arrogant Legacy Clan Scions in the Ranking Arena\n"
        "• Ch 42: Subterranean Rift Outbreak & Frontline Beast Tamer Defense\n"
        "• Ch 50: Sovereign Tamer Ascendance & The Rise of the Mythic Beast Legion\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#BeastTaming #UltimateBondSystem #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (1, 5),
            "title": ["SOUL SPACE AWAKENING", "ULTIMATE BOND SYSTEM"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of a determined young male beast tamer, neat dark hair, radiant electric-cyan eyes, "
                "wearing practical dark tactical tamer academy garments with silver runic trim. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside an ancient stone awakening hall lined with glowing runic pedestals, revealing a floating holographic "
                "translucent golden system interface displaying beast bond compatibility matrices. "
                "Illumination from neon-blue soul contract rings and golden particle streams, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (6, 10),
            "title": ["FIRST CONTRACT", "PRIMORDIAL BLOODLINE"],
            "fallback_color": (25, 35, 30),
            "prompt": (
                "Cinematic 3D portrait of a young male tamer, calm focused expression, glowing amber-cyan eyes, "
                "holding out a glowing palm inscribed with a silver covenant seal. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in a sunlit forest glade, revealing a sleek, mystical white spirit beast with glowing azure crests and dual tails "
                "nuzzling affectionately against his hand in the distance. Illumination from sparkling cyan soul mist and warm golden sunlight rays, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (11, 15),
            "title": ["ATTRIBUTE FEEDBACK", "ACADEMY ARENA SHOCK"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of a battle-poised young tamer, dark hair whipped by violent mana currents, fierce sapphire eyes, "
                "wearing reinforced carbon-leather combat armor crackling with kinetic arcs. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a crowded stone tournament colosseum, revealing an arrogant rival tamer's massive iron-armored bear "
                "staggering backward under a devastating bare-handed counter-strike in the distance. Illumination from crackling lightning sparks and cheering spectator torches, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (16, 20),
            "title": ["WILDERNESS HUNT", "MUTATED PREDATOR SLAY"],
            "fallback_color": (35, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of a focused hunter tamer, windswept dark hair, razor-sharp amber pupils, "
                "holding an engraved hunting spear, wearing dark stealth mantle gear. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in a dense prehistoric jungle canyon under twilight, revealing his primary spirit familiar cloaked in radiant flames "
                "leaping across rocky ledges to strike down a giant mutated shadow panther in the distance. "
                "Illumination from blazing scarlet flame claws and cool teal forest mist, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (21, 25),
            "title": ["SECOND DIVINE BEAST", "ELEMENTAL SYNTHESIS"],
            "fallback_color": (20, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of an evolving master tamer, refined facial planes, dual-colored crimson-and-azure eyes, "
                "wearing dark titanium battle robes adorned with silver feather emblems. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on an overlooking mountain peak, revealing an enormous magnificent storm falcon radiating white lightning "
                "descending from thunderous clouds to form a sacred bond contract in the distance. "
                "Illumination from blinding lightning arcs and shimmering celestial soul rings, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (26, 30),
            "title": ["RIVAL CONFRONTATION", "LEGACY SCION CRUSHED"],
            "fallback_color": (35, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of a cold commanding young sovereign, sleek black hair, piercing golden-amber eyes, "
                "standing tall with arms crossed in calm authority. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in an upscale academy duel ring, revealing an arrogant legacy heir and his defeated rare-breed drake "
                "pinned to the shattered marble floor by invisible gravitational pressure in the distance. "
                "Illumination from neon-violet gravity ripples and gleaming arena lanterns, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (31, 35),
            "title": ["SUBTERRANEAN RIFT", "BEAST WAVE BREACH"],
            "fallback_color": (40, 15, 20),
            "prompt": (
                "Cinematic 3D portrait of a frontline warrior tamer, dark hair whipped by fiery updrafts, intense glowing azure eyes, "
                "wearing heavy dragon-scale breastplate armor. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set at the edge of an apocalyptic dimensional fissure in the earth, revealing hundreds of charging corrupted subterranean "
                "beasts engulfed in coordinated elemental blasts from his familiars in the distance. "
                "Illumination from roaring volcanic firestorms and blinding cyan mana explosions, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (36, 40),
            "title": ["SOUL ALTAR RUIN", "ANCESTRAL AWAKENING"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of a dignified young tamer prodigy, calm composed gaze, radiant amethyst pupils, "
                "touching an ancient glowing obsidian obelisk covered in forgotten glyphs. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set deep inside a sunken subterranean temple, revealing his contracted familiars surrounded by swirling ethereal pillars "
                "of ancestral beast spirits unlocking forgotten mythic bloodlines in the distance. "
                "Illumination from radiant violet soul fire and floating golden divine characters, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (41, 45),
            "title": ["CITY DEFENSE", "TITAN CALAMITY REPULSED"],
            "fallback_color": (25, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of a victorious tamer commander, razor-sharp jawline, glowing sun-gold eyes, "
                "wearing high-tier mithril-inlaid commander armor with a fluttering navy cape. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set upon the high battlements of an outer border city, revealing a colossal rampaging mountain titan crumbling "
                "under a combined tempest-and-hellfire assault from his pets in the distance. "
                "Illumination from sunrise-gold magical artillery beams and billowing smoke trails, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (46, 50),
            "title": ["SOVEREIGN APEX TAMER", "MYTHIC BEAST LEGION"],
            "fallback_color": (20, 25, 50),
            "prompt": (
                "Cinematic 3D portrait of the Sovereign Beast Master at peak power, majestic windswept dark hair, brilliant dual-ringed sapphire-gold eyes, "
                "wearing imperial dark-silver sovereign robes radiating multiple colored elemental halos. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set atop a soaring cliff overlooking sprawling fantasy kingdoms, revealing towering mythic dragon, phoenix, and fenrir familiars "
                "standing loyally behind him under a breathtaking dawn sky. Illumination from brilliant auroras of sunrise gold, cyan soul fire, and deep-violet mana, "
                "deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))