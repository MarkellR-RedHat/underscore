"""Collections: distinct sonic worlds.

A collection fixes the instruments, the drum kit, the effects, the harmonic
flavor, and the arrangement signature. The same brief rendered in two
collections sounds like two different libraries. Within a collection, each bed
gets a deterministic instrument assignment from its seed, so eighteen beds in
one world still differ from each other.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class Collection:
    name: str
    tagline: str
    sound: str                      # the paragraph the model composes from
    leads: list[str]                # pick one per bed
    pads: list[str]                 # pick one per bed
    basses: list[str]               # pick one per bed
    kicks: list[str]
    hats: list[str]
    accents: list[str]              # snaps, pings, bells, noise beds
    fx: str
    harmony: str
    arrangement: str
    tempo_shift: int = 0            # added to the profile's bpm
    extra_synths: list[str] = field(default_factory=list)

    def pick(self, seed: int) -> dict[str, str]:
        r = random.Random(seed * 7919 + len(self.name))
        return {
            "lead": r.choice(self.leads), "pad": r.choice(self.pads), "bass": r.choice(self.basses),
            "kick": r.choice(self.kicks), "hat": r.choice(self.hats), "accent": r.choice(self.accents),
        }

    def synths(self) -> list[str]:
        return sorted(set(self.leads + self.pads + self.basses + self.extra_synths))

    def samples(self) -> list[str]:
        return sorted(set(self.kicks + self.hats + self.accents))

    def prompt_block(self, seed: int) -> str:
        p = self.pick(seed)
        return "\n".join([
            f"## Collection: {self.name}",
            self.sound.strip(),
            "",
            f"Instruments for this bed (chosen for you, use these): lead {p['lead']}, pad {p['pad']}, "
            f"bass {p['bass']}, kick {p['kick']}, hats {p['hat']}, accent {p['accent']}.",
            f"Allowed synths: {', '.join(self.synths())}.",
            f"Allowed samples: {', '.join(self.samples())}.",
            f"Effects: {self.fx.strip()}",
            f"Harmony: {self.harmony.strip()}",
            f"Arrangement signature: {self.arrangement.strip()}",
        ])


COLLECTIONS: dict[str, Collection] = {
    "analog": Collection(
        name="analog", tagline="Warm analog pads and soft percussion",
        sound="Warm, rounded, slightly hazy. Detuned analog pads carry the harmony. Percussion is soft and low in the mix. Nothing is sharp.",
        leads=[":prophet", ":blade", ":pluck"], pads=[":prophet", ":hollow", ":dark_ambience"],
        basses=[":tb303", ":subpulse", ":fm"],
        kicks=[":bd_haus", ":bd_tek"], hats=[":drum_cymbal_closed", ":elec_tick"], accents=[":perc_snap", ":sn_dolf", ":elec_ping"],
        fx="reverb room 0.5 to 0.7 on pads, a touch of echo on the lead, lpf between 70 and 100 on everything.",
        harmony="Triads and sevenths. Movement between i, VI, III, VII in minor; I, V, vi, IV in major.",
        arrangement="Pads first, bass on beats 1 and 3, hats only above energy 0.5, motif enters late and stays sparse.",
    ),
    "glass": Collection(
        name="glass", tagline="Bright, clean, and spacious",
        sound="Clean and bright, like light through glass. Bells, piano, and plucked tones in the upper register, lots of air between notes. Percussion is crisp and quiet. Feels modern and precise.",
        leads=[":pretty_bell", ":piano", ":pluck", ":kalimba"], pads=[":hollow", ":sine", ":blade"],
        basses=[":sine", ":fm", ":subpulse"],
        kicks=[":bd_pure", ":bd_haus"], hats=[":elec_tick", ":drum_cymbal_pedal"], accents=[":elec_blip", ":elec_ping", ":perc_bell"],
        fx="reverb room 0.7 to 0.85 with mix 0.3, no distortion, hpf 30 on the master voice. Keep lpf open.",
        harmony="Add9 and sus2 voicings, wide spacing, mostly major or dorian. Avoid dense low chords.",
        arrangement="Arpeggiated lead in eighths above midi 72 from bar one, pad underneath, sparse kick on 1 only until energy passes 0.7, bell accents on offbeats.",
        tempo_shift=6,
    ),
    "pulse": Collection(
        name="pulse", tagline="Driving, electronic, forward motion",
        sound="Driving and rhythmic. Sawtooth leads, pulsing bass in sixteenths, a firm four on the floor once energy allows. The feel is infrastructure at scale: steady, confident, moving.",
        leads=[":dsaw", ":supersaw", ":tech_saws", ":chiplead"], pads=[":dsaw", ":blade", ":supersaw"],
        basses=[":tb303", ":subpulse", ":chipbass"],
        kicks=[":bd_tek", ":bd_klub", ":bd_fat"], hats=[":drum_cymbal_closed", ":elec_tick"], accents=[":sn_dolf", ":elec_blip2", ":perc_snap2"],
        fx="lpf sweeping between 60 and 110 across a section, short reverb room 0.3, slicer or echo in eighths on the lead when energy exceeds 0.7.",
        harmony="Minor with a raised sixth allowed. Root pedal in the bass, chords change every two bars.",
        arrangement="Bass in sixteenths from bar one (amp 0.3), kick on every beat above energy 0.6, hats in eighths, lead arpeggio in sixteenths above 0.7, drop the kick in the resolve.",
        tempo_shift=14,
    ),
    "ember": Collection(
        name="ember", tagline="Lo-fi warmth with a gentle swing",
        sound="Warm, dusty, relaxed. Filtered piano or rhodes-like chords, a soft kick, snapped snare, a little vinyl texture very low in the mix, and a slight swing on the hats. Feels like a well lit desk at night.",
        leads=[":piano", ":pluck", ":kalimba"], pads=[":piano", ":hollow", ":dark_ambience"],
        basses=[":sine", ":fm", ":subpulse"],
        kicks=[":bd_haus", ":drum_bass_soft", ":bd_808"], hats=[":drum_cymbal_closed", ":drum_cymbal_pedal"], accents=[":perc_snap", ":drum_snare_soft", ":vinyl_hiss"],
        fx="lpf 75 to 90 on the piano, reverb room 0.4, vinyl_hiss sample looped at amp 0.05 as texture, echo at a dotted eighth on the lead, sparingly.",
        harmony="Seventh and ninth chords, ii V I movement in major, i iv VII in minor. Voicings in the middle register.",
        arrangement="Chords on beats 1 and the and of 2, kick on 1 and 3, snare accent on 2 and 4 above energy 0.5, hats swung (sleep 0.55 then 0.45), melody in short answered phrases.",
        tempo_shift=-6,
    ),
    "drift": Collection(
        name="drift", tagline="Cinematic ambient, slow and wide",
        sound="Wide, slow, cinematic. Long evolving pads with slow filter movement, deep sub bass notes held for bars, sparse pings far in the distance. Almost no drums until the lift, and even then only a soft pulse. Feels like an architecture walkthrough at altitude.",
        leads=[":blade", ":hollow", ":pretty_bell"], pads=[":dark_ambience", ":hollow", ":blade", ":prophet"],
        basses=[":sine", ":subpulse"],
        kicks=[":bd_boom", ":drum_bass_soft"], hats=[":drum_cymbal_pedal"], accents=[":elec_ping", ":ambi_glass_hum", ":perc_bell"],
        fx="reverb room 0.9 with mix 0.4 on everything, lpf that opens slowly across each section, echo with long decay on pings.",
        harmony="Open fifths and suspended chords, one chord per two bars, minor or aeolian. No leading tones.",
        arrangement="Pad with attack of a full bar from bar one, sub bass notes lasting two bars, one ping every four to eight beats, soft kick on beat 1 only above energy 0.65, nothing faster than eighths anywhere.",
        tempo_shift=-10, extra_synths=[":sine"],
    ),
    "orbit": Collection(
        name="orbit", tagline="Organic, bright, and community warm",
        sound="Organic and friendly. Kalimba, tonewheel organ, plucked strings, and a soft piano, over brushed percussion. Bright major harmony with a human feel. Suits a keynote, a community story, a launch that wants warmth over force.",
        leads=[":kalimba", ":pluck", ":piano", ":organ_tonewheel"], pads=[":organ_tonewheel", ":hollow", ":prophet"],
        basses=[":fm", ":sine", ":subpulse"],
        kicks=[":bd_haus", ":drum_bass_soft", ":bd_pure"], hats=[":drum_cymbal_pedal", ":drum_cymbal_soft"], accents=[":perc_snap", ":elec_bell", ":tabla_ghe1"],
        fx="reverb room 0.5, no lpf below 90, a little echo on the kalimba, keep everything clean and present.",
        harmony="Major with mixolydian color (flat seven allowed). I, IV, V, vi and their inversions, moving every bar.",
        arrangement="Kalimba or pluck pattern in eighths from bar one, organ pad sustaining, brushed hat pattern on the offbeats, kick on 1 and 3 above 0.55, piano answers the lead in the lift.",
        tempo_shift=4,
    ),
}


def get(name: str) -> Collection:
    if name not in COLLECTIONS:
        raise KeyError(f"unknown collection {name!r}; choose from {list(COLLECTIONS)}")
    return COLLECTIONS[name]
