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
    "novel_slug": "investing-in-my-three-crippled-wives-get-10000x-times-return",
    "start_url": "https://freewebnovel.com/novel/investing-in-my-three-crippled-wives-get-10000x-times-return/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Cultivation",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 2,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_investing_three_wives_001_050",
    "final_audio": "output_investing_three_wives_001_050.mp3",
    "final_video": "final_investing_three_wives_001_050.mp4",
    "cover_image": "cover_investing_three_wives_001_050.jpg",
    "timestamps_file": "youtube_timestamps_investing_three_wives_001_050.txt",
    "subtitles_file": "subtitles_investing_three_wives_001_050.srt",
    "payload_file": "youtube_upload_payload_investing_three_wives_001_050.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "INVESTING IN MY THREE CRIPPLED WIVES GETS 10,000X RETURN! [Ch 1-50] | Cultivation LitRPG Marathon",
    "tags": [
        "LitRPG Audiobook", "Investing In My Three Crippled Wives", "10000x Return System", "Gu Chen",
        "Cultivation Audiobook", "Xianxia", "Harem Cultivation", "Progression Fantasy", "Being A Bong"
    ],
    "desc_header": (
        "While other young masters seek marriages with powerful royal clans, Gu Chen chooses three crippled maidens!\n\n"
        "Transmigrated into an impoverished branch family of the Gu Clan, Gu Chen is mocked when he agrees to marry "
        "three former peerless genius heroines whose cultivations were brutally destroyed by enemies: a Sword Saintess whose divine "
        "sword bone was dug out, an Empress afflicted with fatal Nine-Yin Frost poison, and an innocent maiden whose primordial "
        "divine beast bloodline was completely sealed.\n\n"
        "What the world doesn't know is that Gu Chen has bound the 10,000x Investment Return System! Every single pill, martial scroll, "
        "and spiritual treasure he gifts to his wives returns multiplied tenfold, a hundredfold, and up to ten-thousandfold directly "
        "into his own dantian! While nursing his three wives back to divine supremacy, Gu Chen ascends into an untouchable peerless sovereign!\n\n"
        "Welcome to Chapters 1 to 50 of 'Investing In My Three Crippled Wives Get 10,000x Times Return' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 01: Three Crippled Wives Marriage & 10,000x Investment System Awakening\n"
        "• Ch 08: Gifting Bone-Reconstruction Pill & 10,000x Return of Primordial Sword Bone\n"
        "• Ch 15: Suppressing Clan Cynics & First Wife Ye Qingxue's Undying Loyalty\n"
        "• Ch 22: Purging the Nine-Yin Frost Poison & Second Wife Jiang Luoli's Awakening\n"
        "• Ch 29: Extreme Yang Sacred Body Return & Gu Chen's Shocking Realm Breakthrough\n"
        "• Ch 35: Unsealing Third Wife Bai Ling & Heavenly Divine Beast Resonance\n"
        "• Ch 42: Grand Gu Clan Assembly & Crushing the Arrogant Main Branch Scions\n"
        "• Ch 50: Sovereign Patriarch Gu Chen & The Three Restored Peerless Empresses\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#InvestingInMyThreeCrippledWives #10000xReturn #GuChen #CultivationAudiobook #Xianxia #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (1, 5),
            "title": ["THREE CRIPPLED WIVES", "10,000X INVESTMENT SYSTEM"],
            "fallback_color": (25, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of a handsome young male clan patriarch, refined facial features, calm calculating amber-gold eyes, "
                "wearing elegant dark-navy silk cultivation robes with silver embroidery. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a quiet traditional courtyard chamber with carved wooden lattices, revealing a floating holographic "
                "translucent golden system window displaying glowing critical return multiplier grids. "
                "Illumination from warm oil lanterns and glowing golden investment runes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (6, 10),
            "title": ["FIRST WIFE YE QINGXUE", "SWORD BONE INVESTMENT"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of a young male cultivator, windswept dark hair, compassionate yet sharp eyes, "
                "gently extending a glowing jade medicine elixir box forward. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set beside a wooden pavilion bed, revealing beautiful pale First Wife Ye Qingxue with long raven hair and cold noble "
                "features leaning against white silk pillows with misty silver sword qi awakening around her. "
                "Illumination from radiant silver blade gleams and emerald pill luminescence, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (11, 15),
            "title": ["PRIMORDIAL SWORD BONE", "CRITICAL 10,000X RETURN"],
            "fallback_color": (25, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of Cultivator Gu Chen undergoing internal evolution, floating strands of black hair, brilliant silver-gold pupils, "
                "with an ethereal glowing translucent sword bone manifesting along his spine. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a private stone meditation grotto, revealing dense concentric shockwaves of primordial sword intent "
                "carving razor-sharp fissures into the stone floor. Illumination from blinding white-silver sword radiance and celestial starlight particles, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (16, 20),
            "title": ["SECOND WIFE JIANG LUOLI", "NINE-YIN FROST PURGE"],
            "fallback_color": (15, 30, 40),
            "prompt": (
                "Cinematic 3D portrait of a focused male strategist cultivator, warm expression, radiant amber eyes, "
                "channeling warm golden solar spiritual flames between his open hands. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in a frost-covered courtyard room, revealing Second Wife Jiang Luoli, a breathtaking former empress with silver-white hair "
                "and regal features, surrounded by melting azure ice crystals. Illumination from warm crimson solar energy clashing against icy sapphire mist, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (21, 25),
            "title": ["EXTREME YANG SACRED BODY", "REALM BREAKTHROUGH"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of a dominant male cultivator, dark hair whipped by kinetic heatwaves, blazing sun-gold pupils, "
                "wearing charcoal battle robes with golden sun insignias. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set atop an open mountain cultivation terrace under a starry midnight sky, revealing colossal golden solar halos "
                "erupting from his dantian and incinerating surrounding mist. Illumination from blinding sun-yellow spiritual fire columns and crimson auroras, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (26, 30),
            "title": ["THIRD WIFE BAI LING", "PRIMORDIAL BEAST BLOODLINE"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of Gu Chen, gentle protective smile, sharp handsome facial structure, luminous amber eyes, "
                "handing an ancient glowing crimson bloodstone talisman to a young maiden. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in a bamboo garden courtyard, revealing innocent Third Wife Bai Ling with delicate features and glowing amethyst fox ears "
                "staring in joyful awe as celestial beast shadows circle above her. Illumination from soft violet divine beast mist and floating golden runes, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (31, 35),
            "title": ["TEN HEAVENLY BEASTS", "BLOODLINE PHANTOM SURGE"],
            "fallback_color": (35, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of an awe-inspiring male sovereign, dark windswept hair, intense dual-colored violet-and-amber eyes, "
                "wearing heavy dark-silk robes reinforced with draconic scales. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against an expanse of thunderous storm clouds, revealing towering spectral phantoms of ten ancient mythical beasts "
                "bowing loyally behind him. Illumination from crackling magenta lightning bolts and deep golden ancestral beast auras, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (36, 40),
            "title": ["CLAN ASSEMBLY", "CRUSHING THE MOCKERS"],
            "fallback_color": (25, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of a cold majestic young master, neat dark hair, razor-sharp jawline, piercing cold golden eyes, "
                "wielding an unmanifested wave of overwhelming spiritual pressure. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside the grand marble assembly hall of the Gu Clan, revealing arrogant elders and branch disciples "
                "kneeling in shock under an invisible heavy domain in the distance. Illumination from hanging imperial bronze lanterns and gleaming jade floors, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (41, 45),
            "title": ["SWORD INTENT REAWAKENED", "YE QINGXUE'S WRATH"],
            "fallback_color": (20, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of Gu Chen standing back-to-back with his First Wife, calm confident expression, radiant amber eyes, "
                "wearing dark battle robes with silver sword crests. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set at the fortified mountain gates of the Gu territory, revealing fully restored Sword Saintess Ye Qingxue "
                "in pristine white battle robes brandishing a colossal divine silver sword that cuts through approaching enemy warships in the distance. "
                "Illumination from blinding silver sword light and azure storm clouds, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (46, 50),
            "title": ["SOVEREIGN PATRIARCH", "THE THREE EMPRESSES"],
            "fallback_color": (20, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of Sovereign Patriarch Gu Chen at peak dominion, majestic dark hair, imperial golden-amber eyes, "
                "wearing ornate imperial black-and-gold sovereign robes embroidered with divine dragons. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on the highest throne pavilion of an expansive mountain empire, revealing his three peerless wives standing proudly "
                "by his side overlooking thousands of kneeling cultivators under a radiant sunrise. Illumination from brilliant auroras of sunrise gold, "
                "violet soul mist, and pristine silver sword qi, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
