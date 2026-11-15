import os
import csv
import asyncio
import edge_tts

# Import strictly from your editable test sandbox
from audio_constants_test import (
    VOICE_PITCH_PROFILES,
    BGM_MOODS,
    BGM_MOOD_PITCH_DELTAS_BY_VOICE,
    BGM_MOOD_RATE_DELTAS_BY_VOICE,
    SPEAKER_PITCH_OFFSETS,
)

print("[Audit Generator] Loaded acoustic profiles from: audio_constants_test.py", flush=True)

OUT_DIR = "voice_mood_audit"
os.makedirs(OUT_DIR, exist_ok=True)

# 10 Genre-Representative Lines Mapped to (pitch_tier, base_rate, sample_line)
MOOD_SCENARIOS = {
    "no_mood": (
        "narrator_anchor",
        0,
        "Chapter forty-two. Standing before the bronze gates of the guild hall, he checked his status window."
    ),
    "combat": (
        "defiant_shout",
        -4,
        "Hold the vanguard! Shatter their formation before the boss unleashes its domain!"
    ),
    "tension": (
        "tense_strained",
        -3,
        "Keep your mana suppressed and stay low. Three shadow assassins are stalking the ridge above us."
    ),
    "sorrow": (
        "grave_somber",
        -4,
        "Even after ascending past the mortal realm, I could not save the ones who stood beside me."
    ),
    "wonder": (
        "buoyant_lift",
        -2,
        "Look above the clouds! Nine floating sect peaks suspended by ancient celestial formations!"
    ),
    "warmth": (
        "conversational_mid",
        -3,
        "Rest for tonight. No matter how harsh the cultivation path becomes, you will never walk it alone."
    ),
    "intrigue": (
        "thoughtful_drawl",
        -3,
        "Why would the Grand Elder offer a priceless spatial ring to a rogue disciple with zero backing?"
    ),
    "triumph": (
        "urgent_command",
        -2,
        "The tribulation lightning has parted! Rank S awakening complete—every stat has doubled!"
    ),
    "dread": (
        "abyssal_floor",
        -4,
        "Something ancient just opened its eyes beneath the dungeon floor, and the air turned ice cold."
    ),
    "playful": (
        "inquisitive_tilt",
        -2,
        "Wait a second—you swallowed a peak-rank monster core like candy and you're asking for seconds?"
    ),
}

# 21 Solfège Tiers Ordered by Octave for Full Pitch-Matrix Verification
SOLFEGE_21_LINES = [
    # Octave 1: Sub-Bass & Heavy Chest Floor
    ("abyssal_floor", "Octave 1, Tier 1, abyssal floor. The abyssal titan stirs beneath the shattered continent."),
    ("grave_somber", "Octave 1, Tier 2, grave somber. We bury our fallen brothers beneath the silent ash."),
    ("grim_rumble", "Octave 1, Tier 3, grim rumble. Take one more step across this line and forfeit your life."),
    ("menacing_growl", "Octave 1, Tier 4, menacing growl. You dare covet a treasure that belongs to my clan?"),
    ("subdued_mournful", "Octave 1, Tier 5, subdued mournful. All those years of training vanished the moment my core cracked."),
    ("intimate_whisper", "Octave 1, Tier 6, intimate whisper. Listen closely—the guild master is not who he claims to be."),
    ("authoritative_low", "Octave 1, Tier 7, authoritative low. By decree of the Sovereign Council, the trial begins now."),
    # Octave 2: Natural Speaking Core
    ("narrator_anchor", "Octave 2, Tier 8, narrator anchor. Morning sunlight filtered through the tall stained-glass windows."),
    ("thoughtful_drawl", "Octave 2, Tier 9, thoughtful drawl. If the cooldown is ten seconds, we only get one clean opening."),
    ("conversational_mid", "Octave 2, Tier 10, conversational mid. Let's stock up on mana potions before heading into the rift."),
    ("engaged_alert", "Octave 2, Tier 11, engaged alert. Watch its left flank—the beast is gathering lightning in its jaws."),
    ("neutral_statement", "Octave 2, Tier 12, neutral statement. System notification: you have acquired one spirit-grade blade."),
    ("buoyant_lift", "Octave 2, Tier 13, buoyant lift. We actually cleared the hidden dungeon on our very first attempt!"),
    ("inquisitive_tilt", "Octave 2, Tier 14, inquisitive tilt. How did a level one initiate break through a master-tier barrier?"),
    # Octave 3: Upper Midrange, Head Voice & Strained Peaks
    ("lung_reset_entry", "Octave 3, Tier 15, lung reset entry. Meanwhile, miles away inside the royal capital, alarms rang out!"),
    ("tense_strained", "Octave 3, Tier 16, tense strained. My shield won't hold another strike—hurry up with the chant!"),
    ("urgent_command", "Octave 3, Tier 17, urgent command. Archers, fire at will! Do not let them breach the inner gate!"),
    ("alarmed_spike", "Octave 3, Tier 18, alarmed spike. Behind you! The spatial rift just tore open right beside the altar!"),
    ("defiant_shout", "Octave 3, Tier 19, defiant shout. Even if the heavens themselves block my path, I will cut them down!"),
    ("frantic_screech", "Octave 3, Tier 20, frantic screech. Run! That is not a spirit beast—it's a calamity-class demon!"),
    ("hysterical_peak", "Octave 3, Tier 21, hysterical peak. Impossible! No mortal could survive a direct hit from my ultimate art!"),
]

# Archetype Speaker Role Offsets from SPEAKER_PITCH_OFFSETS
SPEAKER_ROLE_SCENARIOS = {
    "elder": (
        "en-US-RogerNeural",
        "authoritative_low",
        "Kneel before the ancestral tablet and receive the sect's foundational scripture."
    ),
    "sect_master": (
        "en-US-AndrewMultilingualNeural",
        "authoritative_low",
        "From this day forward, any disciple who bullies a fellow clan member shall be expelled!"
    ),
    "patriarch": (
        "en-US-AndrewNeural",
        "grim_rumble",
        "Mobilize the clan elders. No outsider leaves our valley alive tonight."
    ),
    "ancestor": (
        "en-US-SteffanNeural",
        "abyssal_floor",
        "Ten thousand years have passed since a mortal awakened the Supreme Dragon Bloodline."
    ),
    "disciple": (
        "en-US-BrianNeural",
        "buoyant_lift",
        "Senior Brother! Look at the ranking monument—your name just jumped straight into the top ten!"
    ),
    "guard": (
        "en-US-GuyNeural",
        "engaged_alert",
        "Halt! Present your city medallion and state your business at the eastern gate."
    ),
    "system": (
        "en-US-AriaNeural",
        "neutral_statement",
        "Congratulations! You have cleared the Hidden Abyssal Trial. All attributes increased by fifty."
    ),
}

ORDERED_MOODS = [
    "no_mood", "combat", "tension", "sorrow", "wonder",
    "warmth", "intrigue", "triumph", "dread", "playful"
]


def get_short_voice_name(voice: str) -> str:
    return (
        voice.replace("en-US-", "")
        .replace("en-GB-", "GB_")
        .replace("en-IN-", "IN_")
        .replace("Neural", "")
    )


def compute_final_prosody(
    voice: str,
    pitch_tier: str,
    mood: str,
    base_rate: int,
    role_offset_hz: float = 0.0
) -> tuple[str, str]:
    """Combines Solfège tier pitch + BGM mood deltas + speaker offset with integer Hz and [-6%, +6%] rate clamp."""
    profile = VOICE_PITCH_PROFILES.get(voice, VOICE_PITCH_PROFILES["default"])
    base_hz = float(profile.get(pitch_tier, "+0Hz").replace("Hz", ""))

    pitch_deltas = BGM_MOOD_PITCH_DELTAS_BY_VOICE.get(voice, BGM_MOOD_PITCH_DELTAS_BY_VOICE["default"])
    rate_deltas = BGM_MOOD_RATE_DELTAS_BY_VOICE.get(voice, BGM_MOOD_RATE_DELTAS_BY_VOICE["default"])

    # edge-tts requires integer Hz strings (e.g., '+3Hz', '-2Hz')
    final_hz = int(round(base_hz + float(pitch_deltas.get(mood, 0.0)) + role_offset_hz))
    raw_rate = base_rate + int(rate_deltas.get(mood, 0))
    final_rate = max(-6, min(6, raw_rate))

    return f"{final_hz:+d}Hz", f"{final_rate:+d}%"


async def synthesize_line(
    character_label: str,
    text: str,
    voice: str,
    pitch: str,
    rate: str,
    out_mp3: str,
    sem: asyncio.Semaphore,
):
    async with sem:
        for attempt in range(1, 4):
            try:
                communicate = edge_tts.Communicate(text=text, voice=voice, pitch=pitch, rate=rate)
                await communicate.save(out_mp3)
                print(
                    f"[Generated] Character: {character_label:<22} | Voice: {voice:<31} | Rate: {rate:<4} | Pitch: {pitch:<5} -> {out_mp3}",
                    flush=True,
                )
                return
            except Exception as e:
                if attempt == 3:
                    print(
                        f"[Error]     Character: {character_label:<22} | Voice: {voice:<31} | Rate: {rate:<4} | Pitch: {pitch:<5} -> {out_mp3} ({e})",
                        flush=True,
                    )
                else:
                    await asyncio.sleep(1.5 * attempt)


async def build_voice_mood_suite():
    sem = asyncio.Semaphore(5)
    manifest_rows = []
    tasks = []

    voices_to_test = [v for v in VOICE_PITCH_PROFILES.keys() if v != "default"]
    print(f"[Audit Generator] Queuing full acoustic test suite for ALL {len(voices_to_test)} voices...", flush=True)

    # 1. All 10 BGM Moods for EVERY Voice
    for voice in voices_to_test:
        short_voice = get_short_voice_name(voice)
        mood_dir = os.path.join(OUT_DIR, short_voice, "10_moods")
        os.makedirs(mood_dir, exist_ok=True)

        for idx, mood in enumerate(ORDERED_MOODS, 1):
            pitch_tier, default_base_rate, sample_line = MOOD_SCENARIOS[mood]
            if voice == "en-US-ChristopherNeural":
                base_rate = 0
                char_label = f"Narrator ({short_voice})"
            elif voice == "en-US-AriaNeural":
                base_rate = 2
                char_label = f"System ({short_voice})"
            else:
                base_rate = default_base_rate
                char_label = short_voice

            final_pitch, final_rate = compute_final_prosody(voice, pitch_tier, mood, base_rate)
            spoken_text = f"Mood: {mood.replace('_', ' ')}. {sample_line}"
            mp3_path = os.path.join(mood_dir, f"{idx:02d}_{mood}.mp3")

            manifest_rows.append({
                "suite": "10_Mood_Sweep",
                "character": char_label,
                "voice": voice,
                "role_or_mood": mood,
                "pitch_tier": pitch_tier,
                "final_pitch": final_pitch,
                "final_rate": final_rate,
                "file": mp3_path,
                "text": spoken_text,
            })
            tasks.append(synthesize_line(char_label, spoken_text, voice, final_pitch, final_rate, mp3_path, sem))

    # 2. All 21 Solfège Pitch Tiers for EVERY Voice
    for voice in voices_to_test:
        short_voice = get_short_voice_name(voice)
        tier_dir = os.path.join(OUT_DIR, short_voice, "21_tiers")
        os.makedirs(tier_dir, exist_ok=True)

        if voice == "en-US-ChristopherNeural":
            base_r = 0
            char_label = f"Narrator ({short_voice})"
        elif voice == "en-US-AriaNeural":
            base_r = 2
            char_label = f"System ({short_voice})"
        else:
            base_r = -4
            char_label = short_voice

        for idx, (tier, line) in enumerate(SOLFEGE_21_LINES, 1):
            final_pitch, final_rate = compute_final_prosody(voice, tier, "no_mood", base_r)
            mp3_path = os.path.join(tier_dir, f"{idx:02d}_{tier}.mp3")

            manifest_rows.append({
                "suite": "21_Tier_Matrix",
                "character": char_label,
                "voice": voice,
                "role_or_mood": "no_mood",
                "pitch_tier": tier,
                "final_pitch": final_pitch,
                "final_rate": final_rate,
                "file": mp3_path,
                "text": line,
            })
            tasks.append(synthesize_line(char_label, line, voice, final_pitch, final_rate, mp3_path, sem))

    # 3. Speaker Role Pitch Offsets (elder, sect_master, patriarch, ancestor, disciple, guard, system)
    roles_dir = os.path.join(OUT_DIR, "_speaker_role_offsets")
    os.makedirs(roles_dir, exist_ok=True)
    for idx, (role_key, offset_hz) in enumerate(SPEAKER_PITCH_OFFSETS.items(), 1):
        voice, tier, line = SPEAKER_ROLE_SCENARIOS.get(
            role_key,
            ("en-US-GuyNeural", "conversational_mid", f"Testing speaker role offset for {role_key}.")
        )
        base_r = 2 if role_key == "system" else -4
        final_pitch, final_rate = compute_final_prosody(voice, tier, "no_mood", base_r, role_offset_hz=float(offset_hz))
        char_label = f"{role_key.title()} ({get_short_voice_name(voice)})"
        spoken_text = f"Role: {role_key.replace('_', ' ')}. {line}"
        mp3_path = os.path.join(roles_dir, f"{idx:02d}_{role_key}_{get_short_voice_name(voice)}.mp3")

        manifest_rows.append({
            "suite": "Speaker_Role_Offsets",
            "character": char_label,
            "voice": voice,
            "role_or_mood": role_key,
            "pitch_tier": tier,
            "final_pitch": final_pitch,
            "final_rate": final_rate,
            "file": mp3_path,
            "text": spoken_text,
        })
        tasks.append(synthesize_line(char_label, spoken_text, voice, final_pitch, final_rate, mp3_path, sem))

    print(f"[Audit Generator] Synthesizing {len(tasks)} separate MP3 files...", flush=True)
    await asyncio.gather(*tasks)

    # Save CSV audit manifest
    manifest_csv = os.path.join(OUT_DIR, "voice_mood_manifest.csv")
    with open(manifest_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["suite", "character", "voice", "role_or_mood", "pitch_tier", "final_pitch", "final_rate", "file", "text"]
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(f"[✓] Completed! Generated {len(tasks)} separate MP3 files in '{OUT_DIR}/'", flush=True)
    print(f"[✓] Full parameter manifest saved to '{manifest_csv}'", flush=True)


if __name__ == "__main__":
    asyncio.run(build_voice_mood_suite())