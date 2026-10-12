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
    "novel_slug": "reincarnated-in-the-alternate-world-im-a-demonic-lord-as-well-as-a-villager",
    "start_url": "https://freewebnovel.com/novel/reincarnated-in-the-alternate-world-im-a-demonic-lord-as-well-as-a-villager/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Demon Lord Villager",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 1,  # Sequential processing to respect 15 RPM limits cleanly
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_demonic_lord_villager_001_050",
    "final_audio": "output_demonic_lord_villager_001_050.mp3",
    "final_video": "final_demonic_lord_villager_001_050.mp4",
    "cover_image": "cover_demonic_lord_villager_001_050.jpg",
    "timestamps_file": "youtube_timestamps_demonic_lord_villager_001_050.txt",
    "subtitles_file": "subtitles_demonic_lord_villager_001_050.srt",
    "payload_file": "youtube_upload_payload_demonic_lord_villager_001_050.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "SECRET DEMON LORD LIVING AS AN NPC VILLAGER! [Ch 1-50] | Fantasy LitRPG Comedy Audiobook Marathon",
    "tags": [
        "LitRPG Audiobook", "Demonic Lord as Well as a Villager", "Xia Mi", "Isekai Audiobook",
        "Fantasy Comedy", "Demon King Reincarnation", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Reincarnated into an alternate fantasy world, Xia Mi wakes up as a humble, ordinary villager in a remote newbie hamlet.\n\n"
        "There's just one tiny complication: he has also inherited the supreme throne and catastrophic power of the Demon King!\n\n"
        "By day, he tends vegetables, chops firewood, and chats with oblivious townspeople like the most harmless NPC alive. "
        "By night, he manages ancient demonic ruins, handles loyal yet eccentric monster retainers like the proud blonde elf Luleya, "
        "and disciplines rowdy minotaur warbands into civilized workers.\n\n"
        "To make matters more chaotic, the prophesied white-haired Hero maiden, Lina, arrives in his village seeking traces "
        "of the newly awakened Demon Lord—never suspecting that the clueless villager handing her fresh cabbage is the ultimate calamity "
        "she is destined to slay!\n\n"
        "Welcome to Chapters 1 to 50 of 'Reincarnated in the Alternate World, I'm A Demonic Lord as Well as a Villager' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 01: Reincarnating as Villager Xia Mi & Inheriting the Demon King Throne\n"
        "• Ch 08: Blonde Elf Maiden Luleya Pledges Loyalty to the New Demon Lord\n"
        "• Ch 15: Low-Profile Village Farming vs Managing the Ruined Castle\n"
        "• Ch 20: Taming the Rowdy Minotaur Tribe with Sovereign Suppression\n"
        "• Ch 26: White-Haired Hero Lina Arrives at the Newbie Village\n"
        "• Ch 32: The Art of Acting Like a Harmless NPC While Serving the Hero\n"
        "• Ch 38: Covert Castle Renovations & Establishing Demon Realm Logistics\n"
        "• Ch 44: Eradicating Forest Calamity Beasts Without Revealing True Identity\n"
        "• Ch 50: The Dual Life Master: Perfect Harmony Between Farmland & Demon Throne\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#DemonLordVillager #XiaMi #IsekaiAudiobook #FantasyComedy #LitRPG #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (1, 5),
            "title": ["DUAL AWAKENING", "VILLAGER & DEMON KING"],
            "fallback_color": (20, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of young protagonist Xia Mi, neat black hair, calm expressive amber eyes with a hidden faint crimson demonic glint, "
                "wearing humble rustic brown villager linen clothes over faint dark mana runes along his wrists. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set at the border of a sunny rustic farming meadow transitioning into dark misty demonic castle ruins, revealing "
                "a quaint thatch-roof cottage on one side and ominous gothic stone spires on the other in the distance. "
                "Illumination from warm golden morning sun contrasting with subtle violet demonic aura wisps, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (6, 10),
            "title": ["ELF ENVOY", "LULEYA'S COVENANT"],
            "fallback_color": (25, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of a young covert demon lord, relaxed confident expression, dark hair, subtle knowing smile, "
                "wearing simple traveler clothes adorned with a concealed dark-iron crest. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a dimly lit ancient gothic castle audience hall, revealing elegant blonde elf envoy Luleya "
                "with delicate pointed ears and ceremonial dark robes kneeling in solemn allegiance in the distance. "
                "Illumination from flickering violet braziers and pale moonlight filtering through shattered stained glass, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (11, 15),
            "title": ["PEACEFUL HAMLET", "CLANDESTINE FARMING"],
            "fallback_color": (30, 35, 20),
            "prompt": (
                "Cinematic 3D portrait of Xia Mi acting as an ordinary villager, carefree warm smile, tousled dark hair, gentle hazel eyes, "
                "holding a simple wooden gardening hoe over one shoulder, wearing earthy work attire with rolled-up sleeves. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set across lush green vegetable patch terraces outside a cozy fantasy village, "
                "revealing rolling hills, wooden windmills, and grazing livestock under a peaceful blue sky in the distance. "
                "Illumination from bright natural afternoon sunlight with golden dust motes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (16, 20),
            "title": ["WILDERNESS EXPEDITION", "MINOTAUR SUBJUGATION"],
            "fallback_color": (35, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of Xia Mi unleashing hidden demonic sovereignty, sharp commanding gaze, glowing crimson pupils, "
                "dark windswept hair, subtle shadowy horns of pure energy crowning his head. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in a rugged volcanic rock valley, revealing a massive armored Minotaur chieftain lowering its colossal battle-axe "
                "and kneeling in awe among roaring beastkin cohorts in the distance. "
                "Illumination from glowing red magma cracks and deep purple demonic shockwave ripples, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (21, 25),
            "title": ["HERO'S ARRIVAL", "LINA'S INQUIRY"],
            "fallback_color": (25, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of innocent-looking villager Xia Mi, slightly bemused expression, calm dark eyes, "
                "wiping a wooden table with a clean rag inside a rustic village tavern. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a warm timber tavern, revealing heroic white-haired maiden Lina clad in gleaming silver knight armor "
                "with an ornate holy blade sheathed at her hip, eyeing him suspiciously in the distance. "
                "Illumination from warm amber hearth flames and pale silver daylight streaming through tavern windows, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (26, 30),
            "title": ["CASTLE RESTORATION", "ANCIENT RUNIC FORGE"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of the secretive Demon King overseeing his domain, dark robes draped over rustic shirts, calculated focused gaze, "
                "radiant violet runes revolving gently around his outstretched fingers. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a massive subterranean fortress workshop, revealing demon craftsmen, stone gargoyles, and Luleya "
                "repairing towering obsidian defense wards in the distance. "
                "Illumination from crackling purple magical enchantments and glowing cyan forge fires, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 31, "range": (31, 35),
            "title": ["CHURCH INVESTIGATOR", "MISTY DIVERSION"],
            "fallback_color": (20, 30, 40),
            "prompt": (
                "Cinematic 3D portrait of Xia Mi playing the fool, innocent bewildered look, dark eyes wide with pretend confusion, "
                "scratching the back of his neck in a simple villager straw hat. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on a misty cobblestone crossroad outside the village gates, revealing stern church inquisitors in hooded white-and-gold mantles "
                "inspecting fake monster footprints leading into the dangerous deep forest in the distance. "
                "Illumination from pale morning fog and soft diffused overcast daylight, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (36, 40),
            "title": ["DOUBLE-LIFE BALLET", "TAVERN & THRONE"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of Xia Mi balancing two worlds, sharp jawline, dual reflection in his eyes showing gold and dark amethyst, "
                "wearing a rustic linen coat lined with hidden opulent imperial silk. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in a divided frame environment, showing a cheerful village tavern counter with fresh bread on the left, "
                "and a brooding obsidian demon king throne room draped in velvet banners on the right in the distance. "
                "Illumination from cozy tavern lantern light blending into dramatic violet castle shadows, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (41, 45),
            "title": ["FOREST BEAST PURGE", "SECRET DOMAIN STRIKE"],
            "fallback_color": (20, 35, 30),
            "prompt": (
                "Cinematic 3D portrait of Xia Mi silently exterminating threats to his village, razor-sharp expression, intense glowing crimson eyes, "
                "snapping his fingers to unleash an invisible spatial vortex, dark hair whipping in kinetic wind. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a shadowy ancient pine forest, revealing a rampaging mutant calamity beast dissolving peacefully into black stardust "
                "before it can breach the village perimeter in the distance. "
                "Illumination from glowing green forest spores and sharp neon-violet disintegrating energy lines, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (46, 50),
            "title": ["SOVEREIGN OF THE BORDERLANDS", "DUAL REALM HARMONY"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of Xia Mi standing at the apex of his dual identity, calm sovereign dignity, windswept dark hair, "
                "piercing dual-toned golden-crimson pupils, wearing a refined blend of comfortable village coat and regal demon lord velvet mantle. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set atop a grassy hill overlooking both the peaceful newbie village "
                "and the sprawling hidden demon realm castle under a breathtaking twilight sky, revealing Luleya and Lina unaware of each other in the distance. "
                "Illumination from rich purple-and-gold sunset gradients with sparkling evening starlight, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
