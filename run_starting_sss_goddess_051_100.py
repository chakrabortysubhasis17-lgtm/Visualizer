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
    "novel_slug": "starting-with-an-sss-rank-goddess-summon",
    "start_url": "https://freewebnovel.com/novel/starting-with-an-sss-rank-goddess-summon/chapter-51",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "SSS Goddess Summon",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_starting_sss_goddess_051_100",
    "final_audio": "output_starting_sss_goddess_051_100.mp3",
    "final_video": "final_starting_sss_goddess_051_100.mp4",
    "cover_image": "cover_starting_sss_goddess_051_100.jpg",
    "timestamps_file": "youtube_timestamps_starting_sss_goddess_051_100.txt",
    "subtitles_file": "subtitles_starting_sss_goddess_051_100.srt",
    "payload_file": "youtube_upload_payload_starting_sss_goddess_051_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "SECOND SSS-RANK GODDESS SUMMONED! DUAL DIVINE DOMAIN SHATTERS WORLD RANKINGS [Ch 51-100] | LitRPG Progression Marathon",
    "tags": [
        "Starting with an SSS-rank Goddess Summon", "SSS Rank Goddess", "Summoner LitRPG",
        "Progression Fantasy Audiobook", "Overpowered MC", "Goddess Summoning", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Graduating from local academy circles to the brutal national stage, our protagonist unlocks the forbidden "
        "secondary soul slot and summons his second mythical SSS-Rank Goddess!\n\n"
        "With dual celestial entities bound to his spiritual core, the feedback loops reach game-breaking heights. "
        "While international hunter syndicates, corrupted military cartels, and rival foreign prodigies attempt to contain "
        "his sudden rise, our summoner marches directly into S-Rank Catastrophe Rifts. Blending radiant holy retribution with "
        "unfathomable primordial destruction, every boss beast and encroaching abyss legion is dismantled with zero effort.\n\n"
        "Watch him dominate national league tournaments, seize ancient continental relics, and establish an autonomous sovereign territory!\n\n"
        "Welcome to Chapters 51 to 100 of 'Starting with an SSS-rank Goddess Summon' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 051: Entering the National Hunter League & Provoking Elite Guild Enforcers\n"
        "• Ch 058: Unlocking the Second Summon Slot: The War Goddess Descends\n"
        "• Ch 065: S-Rank Rift Incursion: Dual Goddess Synergy Vaporizes the Abyssal Swarm\n"
        "• Ch 072: International Hunter Tournament: Humiliating Foreign Champion Teams\n"
        "• Ch 079: Subterranean Vault Raid: Extracting Primordial Titan Core Artifacts\n"
        "• Ch 086: Military Syndicate Ambush: Obliterating Mech Squadrons with Divine Retribution\n"
        "• Ch 092: Frontier Outpost Defense: Holding the Continental Border Single-Handedly\n"
        "• Ch 100: Supreme Commander Coronation: Establishing the Inviolable Goddess Sanctuary\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#StartingWithAnSSSRankGoddessSummon #SSSRankGoddess #SummonerLitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Streamlined for Zero Generation Failures)
    "blocks": [
        {
            "index": 1, "range": (51, 55),
            "title": ["NATIONAL LEAGUE", "ARRIVAL AT THE ARENA"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of a young male summoner walking onto a massive arena platform, confident focused expression, "
                "amber eyes glowing faintly, wearing high-rank black hunter armor with gold trim. "
                "Set inside a futuristic colosseum under stadium floodlights, revealing cheering crowds and hovering digital scoreboards in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (56, 60),
            "title": ["SECOND SUMMON", "WAR GODDESS AWAKENING"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic 3D portrait of the summoner standing beside an altar of red runic light, composed dignified posture, "
                "dark hair framing his chiseled brow. Set inside an ancient underground summoning vault, revealing a towering armored goddess figure descending in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (61, 65),
            "title": ["S-RANK RIFT", "ABYSSAL SWARM PURGE"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of the summoner pointing two fingers forward, razor-sharp gaze, "
                "fingertips crackling with gold and crimson lightning. Set in a fractured volcanic wasteland under dark storm clouds, "
                "revealing swarms of abyssal monsters disintegrating into fiery embers in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (66, 70),
            "title": ["DUAL GODDESS DOMAIN", "HARMONIC SYNERGY"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the summoner in deep tactical focus, calm authoritative presence, "
                "dual-colored golden and scarlet energy rings revolving around his shoulders. Set inside a glowing crystal sanctuary, "
                "revealing twin divine silhouettes guarding his perimeter in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (71, 75),
            "title": ["INTERNATIONAL SHOWDOWN", "EFFORTLESS TRIUMPH"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of the summoner standing with arms folded, mocking cool smirk, "
                "wind rustling his dark hunter cloak. Set across the shattered tiles of an international dueling ring, "
                "revealing defeated foreign champions and fallen beast summons in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (76, 80),
            "title": ["TITAN VAULT", "PRIMORDIAL RELIC HARVEST"],
            "fallback_color": (15, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of the summoner inspecting a glowing titan core crystal, watchful analytical eyes, "
                "wearing reinforced tactical gauntlets. Set inside a subterranean vault with massive stone pillars, "
                "revealing slumbering ancient war golems lined along the walls in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (81, 85),
            "title": ["MECH AMBUSH", "DIVINE COUNTER-STRIKE"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of the summoner raising an open palm surrounded by dense kinetic shockwaves, fierce resolute expression. "
                "Set along a ruined highway at dusk, revealing invading armored mech units collapsing under heavy gravitational beams in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (86, 90),
            "title": ["FRONTIER DEFENSE", "BARRIER OVERLOAD"],
            "fallback_color": (20, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of the summoner standing on high fortress battlements, calm commanding presence, "
                "eyes glowing with intense celestial light. Set overlooking a vast dark valley during a night siege, "
                "revealing a radiant golden energy barrier repelling monster hordes in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (91, 95),
            "title": ["CALAMITY INVASION", "CELESTIAL EXECUTION"],
            "fallback_color": (30, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of the summoner holding a glowing runic command baton, sharp decisive jawline. "
                "Set beneath swirling purple vortex skies, revealing a colossal horned rift overlord falling to its knees under a pillar of light in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (96, 100),
            "title": ["SANCTUARY MONARCH", "NATIONAL SOVEREIGNTY"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of the Supreme Summoner seated upon a grand high-tech command throne, serene invincible aura, "
                "wearing regal dark commander robes with golden crests. Set inside the apex room of an orbital citadel overlooking modern cities under an aurora sky in the distance. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
