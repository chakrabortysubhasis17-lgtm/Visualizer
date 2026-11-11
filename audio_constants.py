"""
audio_constants.py - Master Acoustic Profiles, 21-Tier Solfège Pitch Matrix, and Audio Taxonomy
"""

SFX_PIPELINE_VERSION = 3
SFX_MAX_CONCURRENT_FFMPEG = 2

# Studio vocal mastering filter chain conforming to EBU R128 (-14 LUFS)
BROADCAST_VOCAL_FILTER = (
    "highpass=f=80,"
    "equalizer=f=250:width_type=h:width=120:g=1.8,"
    "equalizer=f=6500:width_type=h:width=1400:g=-2.5,"
    "acompressor=threshold=-18dB:ratio=3:attack=5:release=100:makeup=2dB,"
    "aecho=0.8:0.88:20|40:0.05|0.02,"
    "loudnorm=I=-14:LRA=7:TP=-1.5"
)

# ---------------------------------------------------------------------------
# 21-TIER SEMANTIC SOLFÈGE PITCH MATRIX (3 Octaves x 7 Tiers)
# Octave 1 (Do1-Ti1): Sub-Bass & Heavy Chest Floor (-6.0Hz to -2.5Hz)
# Octave 2 (Do2-Ti2): Natural Speaking Core (-2.0Hz to +0.8Hz)
# Octave 3 (Do3-Ti3): Upper Midrange, Head Voice & Strained Peaks (+1.0Hz to +4.5Hz)
# ---------------------------------------------------------------------------
VOICE_PITCH_PROFILES = {
    # Christopher: Narrator & Dominant Leads (broad chest resonance down to -6Hz)
    "en-US-ChristopherNeural": {
        # Octave 1 (Do1 - Ti1): Abyssal Dread & Low Authority
        "abyssal_floor": "-6.0Hz",
        "grave_somber": "-5.0Hz",
        "grim_rumble": "-4.0Hz",
        "menacing_growl": "-3.5Hz",
        "subdued_mournful": "-3.0Hz",
        "intimate_whisper": "-2.8Hz",
        "authoritative_low": "-2.5Hz",
        # Octave 2 (Do2 - Ti2): Narrative Foundation & Dialogue Mid
        "narrator_anchor": "-2.0Hz",
        "thoughtful_drawl": "-1.5Hz",
        "conversational_mid": "-1.0Hz",
        "engaged_alert": "-0.5Hz",
        "neutral_statement": "+0.0Hz",
        "buoyant_lift": "+0.4Hz",
        "inquisitive_tilt": "+0.8Hz",
        # Octave 3 (Do3 - Ti3): High-Tension, Strain & Peaks
        "lung_reset_entry": "+1.2Hz",
        "tense_strained": "+1.6Hz",
        "urgent_command": "+2.0Hz",
        "alarmed_spike": "+2.4Hz",
        "defiant_shout": "+2.8Hz",
        "frantic_screech": "+3.2Hz",
        "hysterical_peak": "+3.6Hz",
    },

    # Guy: Agile young male leads & versatile dialogue
    "en-US-GuyNeural": {
        # Octave 1
        "abyssal_floor": "-4.5Hz",
        "grave_somber": "-3.8Hz",
        "grim_rumble": "-3.2Hz",
        "menacing_growl": "-2.8Hz",
        "subdued_mournful": "-2.2Hz",
        "intimate_whisper": "-1.8Hz",
        "authoritative_low": "-1.2Hz",
        # Octave 2
        "narrator_anchor": "-0.5Hz",
        "thoughtful_drawl": "-0.2Hz",
        "conversational_mid": "+0.0Hz",
        "engaged_alert": "+0.5Hz",
        "neutral_statement": "+0.8Hz",
        "buoyant_lift": "+1.2Hz",
        "inquisitive_tilt": "+1.5Hz",
        # Octave 3
        "lung_reset_entry": "+1.8Hz",
        "tense_strained": "+2.2Hz",
        "urgent_command": "+2.6Hz",
        "alarmed_spike": "+3.0Hz",
        "defiant_shout": "+3.4Hz",
        "frantic_screech": "+3.8Hz",
        "hysterical_peak": "+4.2Hz",
    },

    # Eric: Arrogant scions, rivals & aggressive antagonists
    "en-US-EricNeural": {
        # Octave 1
        "abyssal_floor": "-3.5Hz",
        "grave_somber": "-2.8Hz",
        "grim_rumble": "-2.2Hz",
        "menacing_growl": "-1.8Hz",
        "subdued_mournful": "-1.2Hz",
        "intimate_whisper": "-0.8Hz",
        "authoritative_low": "-0.2Hz",
        # Octave 2
        "narrator_anchor": "+0.2Hz",
        "thoughtful_drawl": "+0.5Hz",
        "conversational_mid": "+0.8Hz",
        "engaged_alert": "+1.4Hz",
        "neutral_statement": "+1.8Hz",
        "buoyant_lift": "+2.0Hz",
        "inquisitive_tilt": "+2.4Hz",
        # Octave 3
        "lung_reset_entry": "+2.6Hz",
        "tense_strained": "+2.8Hz",
        "urgent_command": "+3.0Hz",
        "alarmed_spike": "+3.4Hz",
        "defiant_shout": "+3.8Hz",
        "frantic_screech": "+4.0Hz",
        "hysterical_peak": "+4.5Hz",
    },

    # Tony: Panicked civilian mobs & frantic crowd shouts
    "en-US-TonyNeural": {
        # Octave 1
        "abyssal_floor": "-3.5Hz",
        "grave_somber": "-2.8Hz",
        "grim_rumble": "-2.0Hz",
        "menacing_growl": "-1.5Hz",
        "subdued_mournful": "-1.0Hz",
        "intimate_whisper": "-0.5Hz",
        "authoritative_low": "+0.0Hz",
        # Octave 2
        "narrator_anchor": "+0.2Hz",
        "thoughtful_drawl": "+0.5Hz",
        "conversational_mid": "+0.8Hz",
        "engaged_alert": "+1.5Hz",
        "neutral_statement": "+1.8Hz",
        "buoyant_lift": "+2.0Hz",
        "inquisitive_tilt": "+2.4Hz",
        # Octave 3
        "lung_reset_entry": "+2.6Hz",
        "tense_strained": "+2.8Hz",
        "urgent_command": "+3.0Hz",
        "alarmed_spike": "+3.4Hz",
        "defiant_shout": "+3.8Hz",
        "frantic_screech": "+4.2Hz",
        "hysterical_peak": "+4.5Hz",
    },

    # Roger: Grand elders, academy deans & veteran martial masters
    "en-US-RogerNeural": {
        # Octave 1
        "abyssal_floor": "-5.5Hz",
        "grave_somber": "-4.8Hz",
        "grim_rumble": "-4.0Hz",
        "menacing_growl": "-3.5Hz",
        "subdued_mournful": "-3.0Hz",
        "intimate_whisper": "-2.5Hz",
        "authoritative_low": "-2.0Hz",
        # Octave 2
        "narrator_anchor": "-1.8Hz",
        "thoughtful_drawl": "-1.4Hz",
        "conversational_mid": "-1.0Hz",
        "engaged_alert": "-0.5Hz",
        "neutral_statement": "+0.0Hz",
        "buoyant_lift": "+0.4Hz",
        "inquisitive_tilt": "+0.8Hz",
        # Octave 3
        "lung_reset_entry": "+1.0Hz",
        "tense_strained": "+1.4Hz",
        "urgent_command": "+1.8Hz",
        "alarmed_spike": "+2.2Hz",
        "defiant_shout": "+2.5Hz",
        "frantic_screech": "+2.8Hz",
        "hysterical_peak": "+3.2Hz",
    },

    # Jenny: Primary heroines, gentle wives & healers
    "en-US-JennyNeural": {
        # Octave 1
        "abyssal_floor": "-4.0Hz",
        "grave_somber": "-3.2Hz",
        "grim_rumble": "-2.5Hz",
        "menacing_growl": "-2.0Hz",
        "subdued_mournful": "-1.5Hz",
        "intimate_whisper": "-1.0Hz",
        "authoritative_low": "-0.5Hz",
        # Octave 2
        "narrator_anchor": "+0.0Hz",
        "thoughtful_drawl": "+0.3Hz",
        "conversational_mid": "+0.6Hz",
        "engaged_alert": "+1.0Hz",
        "neutral_statement": "+1.3Hz",
        "buoyant_lift": "+1.6Hz",
        "inquisitive_tilt": "+2.0Hz",
        # Octave 3
        "lung_reset_entry": "+2.2Hz",
        "tense_strained": "+2.4Hz",
        "urgent_command": "+2.6Hz",
        "alarmed_spike": "+2.8Hz",
        "defiant_shout": "+3.0Hz",
        "frantic_screech": "+3.2Hz",
        "hysterical_peak": "+3.5Hz",
    },

    # Emma: Spirited younger sisters, second heroines & consorts
    "en-US-EmmaNeural": {
        # Octave 1
        "abyssal_floor": "-3.5Hz",
        "grave_somber": "-2.8Hz",
        "grim_rumble": "-2.0Hz",
        "menacing_growl": "-1.5Hz",
        "subdued_mournful": "-1.0Hz",
        "intimate_whisper": "-0.5Hz",
        "authoritative_low": "+0.0Hz",
        # Octave 2
        "narrator_anchor": "+0.5Hz",
        "thoughtful_drawl": "+0.8Hz",
        "conversational_mid": "+1.0Hz",
        "engaged_alert": "+1.5Hz",
        "neutral_statement": "+1.8Hz",
        "buoyant_lift": "+2.0Hz",
        "inquisitive_tilt": "+2.4Hz",
        # Octave 3
        "lung_reset_entry": "+2.6Hz",
        "tense_strained": "+2.8Hz",
        "urgent_command": "+3.0Hz",
        "alarmed_spike": "+3.2Hz",
        "defiant_shout": "+3.5Hz",
        "frantic_screech": "+3.8Hz",
        "hysterical_peak": "+4.0Hz",
    },

    # Ana: Mascot familiars, beast pets, cute slimes & young children
    "en-US-AnaNeural": {
        # Octave 1
        "abyssal_floor": "-2.5Hz",
        "grave_somber": "-2.0Hz",
        "grim_rumble": "-1.5Hz",
        "menacing_growl": "-1.0Hz",
        "subdued_mournful": "-0.5Hz",
        "intimate_whisper": "+0.0Hz",
        "authoritative_low": "+0.2Hz",
        # Octave 2
        "narrator_anchor": "+0.5Hz",
        "thoughtful_drawl": "+0.8Hz",
        "conversational_mid": "+1.0Hz",
        "engaged_alert": "+1.5Hz",
        "neutral_statement": "+1.8Hz",
        "buoyant_lift": "+2.0Hz",
        "inquisitive_tilt": "+2.2Hz",
        # Octave 3
        "lung_reset_entry": "+2.4Hz",
        "tense_strained": "+2.6Hz",
        "urgent_command": "+2.8Hz",
        "alarmed_spike": "+3.0Hz",
        "defiant_shout": "+3.2Hz",
        "frantic_screech": "+3.4Hz",
        "hysterical_peak": "+3.6Hz",
    },

    # Steffan: Boss monsters, abyssal titans & demonic beasts
    "en-US-SteffanNeural": {
        # Octave 1
        "abyssal_floor": "-6.5Hz",
        "grave_somber": "-5.5Hz",
        "grim_rumble": "-4.8Hz",
        "menacing_growl": "-4.0Hz",
        "subdued_mournful": "-3.5Hz",
        "intimate_whisper": "-3.0Hz",
        "authoritative_low": "-2.5Hz",
        # Octave 2
        "narrator_anchor": "-2.2Hz",
        "thoughtful_drawl": "-1.8Hz",
        "conversational_mid": "-1.5Hz",
        "engaged_alert": "-1.0Hz",
        "neutral_statement": "-0.5Hz",
        "buoyant_lift": "+0.0Hz",
        "inquisitive_tilt": "+0.4Hz",
        # Octave 3
        "lung_reset_entry": "+0.8Hz",
        "tense_strained": "+1.2Hz",
        "urgent_command": "+1.5Hz",
        "alarmed_spike": "+1.8Hz",
        "defiant_shout": "+2.2Hz",
        "frantic_screech": "+2.5Hz",
        "hysterical_peak": "+2.8Hz",
    },

    # Aria: Systems & Divine Empresses (crystalline, emotionally detached)
    "en-US-AriaNeural": {
        # Octave 1
        "abyssal_floor": "-3.0Hz",
        "grave_somber": "-2.5Hz",
        "grim_rumble": "-2.0Hz",
        "menacing_growl": "-1.5Hz",
        "subdued_mournful": "-1.0Hz",
        "intimate_whisper": "-0.5Hz",
        "authoritative_low": "-0.2Hz",
        # Octave 2
        "narrator_anchor": "+0.0Hz",
        "thoughtful_drawl": "+0.0Hz",
        "conversational_mid": "+0.2Hz",
        "engaged_alert": "+0.5Hz",
        "neutral_statement": "+0.8Hz",
        "buoyant_lift": "+1.0Hz",
        "inquisitive_tilt": "+1.2Hz",
        # Octave 3
        "lung_reset_entry": "+1.4Hz",
        "tense_strained": "+1.6Hz",
        "urgent_command": "+1.8Hz",
        "alarmed_spike": "+2.0Hz",
        "defiant_shout": "+2.2Hz",
        "frantic_screech": "+2.4Hz",
        "hysterical_peak": "+2.5Hz",
    },

    # Ryan (en-US): Young modern leads, bards & peers
    "en-US-RyanNeural": {
        # Octave 1
        "abyssal_floor": "-4.5Hz",
        "grave_somber": "-3.8Hz",
        "grim_rumble": "-3.0Hz",
        "menacing_growl": "-2.5Hz",
        "subdued_mournful": "-2.0Hz",
        "intimate_whisper": "-1.5Hz",
        "authoritative_low": "-1.0Hz",
        # Octave 2
        "narrator_anchor": "+0.0Hz",
        "thoughtful_drawl": "+0.2Hz",
        "conversational_mid": "+0.5Hz",
        "engaged_alert": "+1.0Hz",
        "neutral_statement": "+1.4Hz",
        "buoyant_lift": "+1.8Hz",
        "inquisitive_tilt": "+2.0Hz",
        # Octave 3
        "lung_reset_entry": "+2.2Hz",
        "tense_strained": "+2.5Hz",
        "urgent_command": "+2.8Hz",
        "alarmed_spike": "+3.0Hz",
        "defiant_shout": "+3.4Hz",
        "frantic_screech": "+3.8Hz",
        "hysterical_peak": "+4.0Hz",
    },

    # Ryan (en-GB): British accented nobles & scholars
    "en-GB-RyanNeural": {
        # Octave 1
        "abyssal_floor": "-4.5Hz",
        "grave_somber": "-3.8Hz",
        "grim_rumble": "-3.0Hz",
        "menacing_growl": "-2.4Hz",
        "subdued_mournful": "-1.8Hz",
        "intimate_whisper": "-1.2Hz",
        "authoritative_low": "-0.8Hz",
        # Octave 2
        "narrator_anchor": "-0.4Hz",
        "thoughtful_drawl": "-0.1Hz",
        "conversational_mid": "+0.2Hz",
        "engaged_alert": "+0.8Hz",
        "neutral_statement": "+1.2Hz",
        "buoyant_lift": "+1.5Hz",
        "inquisitive_tilt": "+1.8Hz",
        # Octave 3
        "lung_reset_entry": "+2.0Hz",
        "tense_strained": "+2.2Hz",
        "urgent_command": "+2.5Hz",
        "alarmed_spike": "+2.8Hz",
        "defiant_shout": "+3.0Hz",
        "frantic_screech": "+3.4Hz",
        "hysterical_peak": "+3.8Hz",
    },

    # Neerja: South-Asian regional heroines & matriarchs
    "en-IN-NeerjaNeural": {
        # Octave 1
        "abyssal_floor": "-4.0Hz",
        "grave_somber": "-3.2Hz",
        "grim_rumble": "-2.5Hz",
        "menacing_growl": "-2.0Hz",
        "subdued_mournful": "-1.5Hz",
        "intimate_whisper": "-1.0Hz",
        "authoritative_low": "-0.5Hz",
        # Octave 2
        "narrator_anchor": "+0.0Hz",
        "thoughtful_drawl": "+0.2Hz",
        "conversational_mid": "+0.5Hz",
        "engaged_alert": "+1.0Hz",
        "neutral_statement": "+1.3Hz",
        "buoyant_lift": "+1.6Hz",
        "inquisitive_tilt": "+2.0Hz",
        # Octave 3
        "lung_reset_entry": "+2.2Hz",
        "tense_strained": "+2.4Hz",
        "urgent_command": "+2.6Hz",
        "alarmed_spike": "+2.8Hz",
        "defiant_shout": "+3.0Hz",
        "frantic_screech": "+3.2Hz",
        "hysterical_peak": "+3.5Hz",
    },

    # Default Generalized Fallback
    "default": {
        "abyssal_floor": "-4.0Hz",
        "grave_somber": "-3.5Hz",
        "grim_rumble": "-3.0Hz",
        "menacing_growl": "-2.5Hz",
        "subdued_mournful": "-2.0Hz",
        "intimate_whisper": "-1.5Hz",
        "authoritative_low": "-1.0Hz",
        "narrator_anchor": "-0.5Hz",
        "thoughtful_drawl": "-0.2Hz",
        "conversational_mid": "+0.0Hz",
        "engaged_alert": "+0.5Hz",
        "neutral_statement": "+0.8Hz",
        "buoyant_lift": "+1.0Hz",
        "inquisitive_tilt": "+1.4Hz",
        "lung_reset_entry": "+1.8Hz",
        "tense_strained": "+2.2Hz",
        "urgent_command": "+2.5Hz",
        "alarmed_spike": "+2.8Hz",
        "defiant_shout": "+3.0Hz",
        "frantic_screech": "+3.4Hz",
        "hysterical_peak": "+3.8Hz",
    }
}

# ---------------------------------------------------------------------------
# BGM MOOD PACING & PITCH MATRIX
# ---------------------------------------------------------------------------
BGM_MOODS = frozenset({
    "combat", "tension", "sorrow", "wonder", "warmth",
    "intrigue", "triumph", "dread", "playful", "no_mood"
})

BGM_MOOD_PITCH_DELTAS_BY_VOICE = {
    "en-US-ChristopherNeural": {
        "combat": 0.0,    # Anchor pitch in resonant chest floor (was 0.8)
        "triumph": 0.2,   # Slight lift (was 0.5)
        "tension": -0.2,  # Drop slightly into darker tone for suspense (was 0.4)
        "playful": 0.2,
        "no_mood": 0.0,
        "intrigue": -0.3,
        "warmth": -0.4,
        "wonder": -0.5,
        "sorrow": -0.8,
        "dread": -1.2,
    },
    "en-US-GuyNeural": {
        "combat": 1.2, "triumph": 0.8, "tension": 0.6, "playful": 0.5, "no_mood": 0.0,
        "intrigue": -0.2, "warmth": -0.4, "wonder": -0.5, "sorrow": -0.8, "dread": -1.0,
    },
    "en-US-EricNeural": {
        "combat": 1.4, "triumph": 0.8, "tension": 0.6, "playful": 0.5, "no_mood": 0.0,
        "intrigue": -0.2, "warmth": -0.3, "wonder": -0.4, "sorrow": -0.6, "dread": -0.8,
    },
    "en-US-RogerNeural": {
        "combat": 0.5, "triumph": 0.4, "tension": 0.3, "playful": 0.2, "no_mood": 0.0,
        "intrigue": -0.4, "warmth": -0.4, "wonder": -0.6, "sorrow": -0.9, "dread": -1.3,
    },
    "en-US-JennyNeural": {
        "combat": 0.8, "triumph": 0.6, "tension": 0.4, "playful": 0.4, "no_mood": 0.0,
        "intrigue": -0.3, "warmth": -0.4, "wonder": -0.5, "sorrow": -0.8, "dread": -1.0,
    },
    "en-US-SteffanNeural": {
        "combat": 0.4, "triumph": 0.3, "tension": 0.2, "playful": 0.1, "no_mood": 0.0,
        "intrigue": -0.4, "warmth": -0.4, "wonder": -0.6, "sorrow": -1.0, "dread": -1.5,
    },
    "en-US-AnaNeural": {
        "combat": 0.6, "triumph": 0.4, "tension": 0.3, "playful": 0.4, "no_mood": 0.0,
        "intrigue": -0.2, "warmth": -0.3, "wonder": -0.3, "sorrow": -0.5, "dread": -0.6,
    },
    "default": {
        "combat": 0.8, "triumph": 0.5, "tension": 0.4, "playful": 0.3, "no_mood": 0.0,
        "intrigue": -0.3, "warmth": -0.3, "wonder": -0.5, "sorrow": -0.7, "dread": -1.0,
    }
}

BGM_MOOD_RATE_DELTAS_BY_VOICE = {
    "en-US-ChristopherNeural": {
        "combat": -2,     # Slow down by -2% so fast-paced action is articulated cleanly (was +8)
        "playful": 2,     # (was +4)
        "triumph": 0,     # (was +3)
        "tension": -3,    # Slow down by -3% for atmospheric suspense (was +2)
        "no_mood": 0,
        "intrigue": -2,
        "warmth": -3,
        "wonder": -5,
        "sorrow": -7,
        "dread": -10,
    },
    "en-US-GuyNeural": {
        "combat": 12, "playful": 7, "triumph": 4, "tension": 3, "no_mood": 0,
        "intrigue": -1, "warmth": -2, "wonder": -3, "sorrow": -5, "dread": -7,
    },
    "en-US-EricNeural": {
        "combat": 14, "playful": 8, "triumph": 5, "tension": 4, "no_mood": 0,
        "intrigue": -1, "warmth": -2, "wonder": -3, "sorrow": -5, "dread": -6,
    },
    "en-US-TonyNeural": {
        "combat": 14, "playful": 8, "triumph": 5, "tension": 4, "no_mood": 0,
        "intrigue": -1, "warmth": -2, "wonder": -3, "sorrow": -5, "dread": -6,
    },
    "en-US-RogerNeural": {
        "combat": 6, "playful": 3, "triumph": 2, "tension": 2, "no_mood": 0,
        "intrigue": -3, "warmth": -3, "wonder": -4, "sorrow": -6, "dread": -8,
    },
    "en-US-JennyNeural": {
        "combat": 10, "playful": 6, "triumph": 4, "tension": 2, "no_mood": 0,
        "intrigue": -2, "warmth": -3, "wonder": -4, "sorrow": -6, "dread": -7,
    },
    "en-US-EmmaNeural": {
        "combat": 11, "playful": 7, "triumph": 4, "tension": 2, "no_mood": 0,
        "intrigue": -2, "warmth": -2, "wonder": -4, "sorrow": -6, "dread": -7,
    },
    "en-US-AnaNeural": {
        "combat": 12, "playful": 9, "triumph": 4, "tension": 3, "no_mood": 0,
        "intrigue": -1, "warmth": -2, "wonder": -3, "sorrow": -5, "dread": -5,
    },
    "en-US-SteffanNeural": {
        "combat": 6, "playful": 2, "triumph": 3, "tension": 2, "no_mood": 0,
        "intrigue": -2, "warmth": -2, "wonder": -4, "sorrow": -5, "dread": -10,
    },
    "en-US-AriaNeural": {
        "combat": 8, "playful": 4, "triumph": 3, "tension": 2, "no_mood": 0,
        "intrigue": -2, "warmth": -2, "wonder": -4, "sorrow": -6, "dread": -8,
    },
    "en-US-RyanNeural": {
        "combat": 11, "playful": 6, "triumph": 4, "tension": 3, "no_mood": 0,
        "intrigue": -2, "warmth": -2, "wonder": -3, "sorrow": -5, "dread": -7,
    },
    "en-GB-RyanNeural": {
        "combat": 10, "playful": 5, "triumph": 3, "tension": 2, "no_mood": 0,
        "intrigue": -2, "warmth": -3, "wonder": -4, "sorrow": -6, "dread": -8,
    },
    "en-IN-NeerjaNeural": {
        "combat": 9, "playful": 5, "triumph": 3, "tension": 2, "no_mood": 0,
        "intrigue": -2, "warmth": -3, "wonder": -4, "sorrow": -7, "dread": -9,
    },
    "default": {
        "combat": 10, "playful": 6, "triumph": 3, "tension": 2, "no_mood": 0,
        "intrigue": -2, "warmth": -2, "wonder": -4, "sorrow": -6, "dread": -8,
    }
}

SPEAKER_PITCH_OFFSETS = {
    "elder": -0.8,
    "sect_master": -0.6,
    "patriarch": -0.6,
    "ancestor": -1.0,
    "disciple": +0.4,
    "guard": -0.3,
    "system": -1.5,
}

SFX_EXTENSIONS = (".mp3", ".wav", ".m4a", ".ogg", ".aac", ".flac", ".opus")
BGM_EXTENSIONS = (".mp3", ".wav", ".m4a", ".ogg", ".aac", ".flac", ".opus")

SFX_KEYS = frozenset({
    "footsteps", "run", "tiptoe", "horseandcart", "steps_indoor", "patter", "heavy_steps", "car", "screech",
    "creak", "crackle", "thunder", "drip", "wind", "forest", "ocean", "crickets", "rain", "clock",
    "hum", "whoosh", "teleport", "impact", "thud", "blade", "armor", "slash", "monster", "wardrum",
    "pain", "gunshot", "explosion", "snarl", "chime", "levelup", "interface", "swish", "quest", "alert",
    "achievement", "reward", "loot", "coin", "chest", "equip", "heartbeat", "gasp", "knock", "rustle",
    "splash", "squeak", "sigh", "slam", "glass_break", "paper", "short_breath_male", "short_breath_female",
    "market", "cheer", "disappointed", "dishes", "eating", "cooking", "heartwarm", "intimate",
    "whisper", "haunt", "howl", "bells", "gong", "intro", "crow", "bark", "dog_bark", "steam_engine"
})

SFX_SYNONYMS = {
    "footstep": "footsteps", "walking": "footsteps", "steps": "footsteps", "walk": "footsteps",
    "step_indoor": "steps_indoor", "indoor_steps": "steps_indoor", "indoor_footsteps": "steps_indoor",
    "pacing": "steps_indoor", "corridor_steps": "steps_indoor",
    "running": "run", "sprint": "run", "sprinting": "run", "charge": "run", "charging": "run", "flee": "run",
    "stealth": "tiptoe", "sneaking": "tiptoe", "sneak": "tiptoe", "careful_steps": "tiptoe",
    "scurry": "patter", "scuttling": "patter", "pattering": "patter", "claws": "patter", "paw_steps": "patter",
    "stomp": "heavy_steps", "stomps": "heavy_steps", "heavysteps": "heavy_steps", "colossus_steps": "heavy_steps",
    "giant_steps": "heavy_steps", "earthquake_steps": "heavy_steps",
    "carriage": "horseandcart", "cart": "horseandcart", "wagon": "horseandcart", "horse_cart": "horseandcart",
    "horse_and_cart": "horseandcart", "hooves": "horseandcart",
    "automobile": "car", "vehicle": "car", "driving": "car", "motor": "car",
    "skid": "screech", "skidding": "screech", "braking": "screech", "tire_screech": "screech",
    "locomotive": "steam_engine", "train": "steam_engine", "train_engine": "steam_engine",
    "train_whistle": "steam_engine", "steam_train": "steam_engine", "railway": "steam_engine",
    "barking": "bark", "dog_bark": "bark", "dog_barking": "bark", "yelp": "bark", "canine_bark": "bark",
    "caw": "crow", "cawing": "crow", "raven": "crow", "raven_caw": "crow",
    "wolf_howl": "howl", "howling": "howl",
    "short_breath_male": "short_breath_male", "short-breath-male": "short_breath_male",
    "breath_male": "short_breath_male", "male_breath": "short_breath_male",
    "short_breath_female": "short_breath_female", "short-breath-female": "short_breath_female",
    "breath_female": "short_breath_female", "female_breath": "short_breath_female",
    "creaking": "creak", "door_creak": "creak", "hinge": "creak", "gate_creak": "creak",
    "fire": "crackle", "crackling": "crackle", "campfire": "crackle", "bonfire": "crackle", "flames": "crackle",
    "lightning": "thunder", "thunderclap": "thunder", "thunderstorm": "thunder",
    "dripping": "drip", "water_drop": "drip", "droplet": "drip",
    "gale": "wind", "breeze": "wind", "draft": "wind", "howling_wind": "wind",
    "woods": "forest", "woodland": "forest", "jungle": "forest", "canopy": "forest",
    "sea": "ocean", "waves": "ocean", "surf": "ocean", "ocean_waves": "ocean", "tide": "ocean",
    "cricket": "crickets", "cicadas": "crickets", "night_insects": "crickets",
    "rainfall": "rain", "downpour": "rain", "drizzle": "rain", "storm_rain": "rain",
    "ticking": "clock", "clock_tick": "clock", "pendulum": "clock",
    "magic": "hum", "aura": "hum", "shimmer": "hum", "mana_hum": "hum", "glow": "hum",
    "air_whoosh": "whoosh", "gust": "whoosh", "swish_air": "whoosh",
    "teleportation": "teleport", "blink": "teleport", "phase_shift": "teleport", "spatial_jump": "teleport",
    "hit": "impact", "strike": "impact", "blunt_hit": "impact", "collision": "impact", "clash": "impact",
    "collapse": "thud", "body_fall": "thud", "fall": "thud", "foot_stomp": "thud",
    "sword": "blade", "draw_sword": "blade", "unsheathe": "blade", "sheath": "blade", "dagger": "blade",
    "plate_armor": "armor", "clank": "armor", "chainmail": "armor", "metal_armor": "armor",
    "slice": "slash", "cut": "slash", "sword_slash": "slash", "cleave": "slash",
    "roar": "monster", "beast_roar": "monster", "monster_roar": "monster", "screech_beast": "monster",
    "growl": "snarl", "snarling": "snarl", "growling": "snarl",
    "drums": "wardrum", "war_drum": "wardrum", "war_drums": "wardrum", "marching_drums": "wardrum",
    "groan": "pain", "hurt": "pain", "agony": "pain", "wound": "pain", "grunt_pain": "pain",
    "gun": "gunshot", "shot": "gunshot", "firearm": "gunshot", "revolver": "gunshot", "rifle": "gunshot",
    "blast": "explosion", "detonation": "explosion", "bomb": "explosion", "boom": "explosion",
    "notification": "chime", "ding": "chime", "system_ding": "chime", "bell_chime": "chime",
    "level_up": "levelup", "stat_increase": "levelup",
    "ui": "interface", "menu": "interface", "status_window": "interface", "panel": "interface",
    "warning": "alert", "alarm": "alert", "danger_alert": "alert", "system_warning": "alert",
    "coins": "coin", "gold_coin": "coin", "gold": "coin", "money": "coin",
    "treasure_chest": "chest", "open_chest": "chest", "treasure": "chest",
    "equipment": "equip", "equip_item": "equip",
    "pulse": "heartbeat", "racing_heart": "heartbeat", "heart": "heartbeat", "badump": "heartbeat",
    "gasping": "gasp", "audible_gasp": "gasp",
    "door_knock": "knock", "knocking": "knock", "rap": "knock",
    "rustling": "rustle", "clothes": "rustle", "fabric": "rustle", "robe": "rustle", "kneel": "rustle", "bow": "rustle",
    "water_splash": "splash", "splashing": "splash",
    "door_slam": "slam", "slammed": "slam", "gate_slam": "slam",
    "shatter": "glass_break", "broken_glass": "glass_break", "glass_shatter": "glass_break",
    "page_turn": "paper", "turning_page": "paper", "scroll": "paper", "parchment": "paper", "unfold": "paper",
    "crowd": "market", "bazaar": "market", "marketplace": "market", "crowd_chatter": "market",
    "cheering": "cheer", "applause": "cheer", "crowd_cheer": "cheer",
    "groan_crowd": "disappointed", "crowd_groan": "disappointed", "letdown": "disappointed",
    "plates": "dishes", "plate": "dishes", "tableware": "dishes", "cutlery": "dishes",
    "eat": "eating", "chew": "eating", "chewing": "eating", "bite": "eating",
    "sizzle": "cooking", "frying": "cooking", "boiling": "cooking", "pot_bubbling": "cooking",
    "tenderness": "heartwarm", "blush": "heartwarm", "handhold": "heartwarm", "hand_holding": "heartwarm",
    "sensual": "intimate", "embrace": "intimate", "close_whisper": "intimate",
    "sighed": "sigh", "sighing": "sigh", "exhale": "sigh", "weary_exhale": "sigh",
    "whispering": "whisper", "murmur": "whisper", "occult_whisper": "whisper", "telepathy": "whisper",
    "chilling": "haunt", "ghost": "haunt", "eerie": "haunt", "chill": "haunt", "supernatural_chill": "haunt",
    "bell": "bells", "toll": "bells", "tolling": "bells", "church_bell": "bells", "clocktower": "bells",
    "temple_bell": "gong", "bronze_gong": "gong", "chime_gong": "gong", "breakthrough_chime": "gong"
}