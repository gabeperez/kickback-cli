#!/usr/bin/env python3
"""
Fast-paced hype track for the Kickbacks CLI launch video — synthesized from
scratch (no samples). Four-on-the-floor kick, clap on 2 & 4, driving hats,
a saw bass, an arpeggiated pluck lead, and classic sidechain "pump", in A minor
over a vi–IV–I–V (Am–F–C–G) progression.

  <venv-python> media/make_track.py <out.wav> [duration_seconds] [bpm]

Needs numpy. Render → AAC → mux into the video with a tail fade (see the shell
step in the launch pipeline).
"""
import sys, wave, struct
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "track.wav"
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 31.7
BPM = float(sys.argv[3]) if len(sys.argv) > 3 else 140.0

SR = 44100
np.random.seed(7)                      # reproducible
beat = 60.0 / BPM
bar  = 4 * beat
N = int(DUR * SR) + SR                  # +1s tail
drums = np.zeros(N)
music = np.zeros(N)

def place(buf, t, sig):
    s = int(t * SR)
    if s < 0: sig = sig[-s:]; s = 0
    e = min(s + len(sig), len(buf))
    buf[s:e] += sig[:e - s]

def tt(dur): return np.arange(int(dur * SR)) / SR

def kick(dur=0.30):
    x = tt(dur)
    pitch = 120 * np.exp(-x * 32) + 46
    body = np.sin(2 * np.pi * np.cumsum(pitch) / SR) * np.exp(-x * 7.5)
    click = (np.random.rand(len(x)) * 2 - 1) * np.exp(-x * 220) * 0.35
    return (body + click) * 0.95

def clap(dur=0.22, amp=0.5):
    x = tt(dur); noise = np.random.rand(len(x)) * 2 - 1
    return noise * np.exp(-x * 16) * amp

def hat(dur=0.045, amp=0.25):
    x = tt(dur); noise = np.random.rand(len(x)) * 2 - 1
    noise = np.diff(noise, prepend=0.0)          # crude highpass
    return noise * np.exp(-x * 70) * amp

def saw(freq, dur, detune=0.0):
    x = tt(dur)
    def s(f): u = f * x; return 2 * (u - np.floor(0.5 + u))
    return s(freq) if not detune else 0.5 * (s(freq) + s(freq * (1 + detune)))

def bass(freq, dur, amp=0.20):
    x = tt(dur)
    e = np.minimum(1.0, x * 200) * np.exp(-x * 2.0)   # punchy, slight decay
    return saw(freq, dur, detune=0.004) * e * amp

def pluck(freq, dur, amp=0.16):
    x = tt(dur)
    e = np.exp(-x * 9) * (1 - np.exp(-x * 500))
    tone = 0.7 * saw(freq, dur, detune=0.007) + 0.3 * np.sin(2 * np.pi * freq * x)
    return tone * e * amp

def riser(dur, amp=0.35):
    x = tt(dur); noise = np.random.rand(len(x)) * 2 - 1
    sweep = noise * (x / dur) ** 2                    # swell in
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * 8 * x)
    return sweep * trem * amp

# A minor: chord tones (Hz) + bass root per bar — Am, F, C, G
A,B,C,D,E,F,G = 220.0,246.94,261.63,293.66,329.63,349.23/2,196.0
PROG = [
    ([A, C, E],   110.0),   # Am
    ([F*2, A, C], 87.31),   # F   (F3=174.61)
    ([C, E, G],   130.81),  # C
    ([G, B, D],    98.0),   # G
]

nbars = int(DUR / bar) + 1
for b in range(nbars):
    chord, root = PROG[b % 4]
    intro = b < 1                                     # bar 0 = build (no kick)
    for bt in range(4):
        t0 = b * bar + bt * beat
        if not intro:
            place(drums, t0, kick())
            if bt in (1, 3): place(drums, t0, clap())
        # hats on 8ths (accent the offbeat)
        place(drums, t0,              hat(amp=0.13))
        place(drums, t0 + beat / 2,   hat(amp=0.22))
        # bass on 8ths
        if not intro:
            place(music, t0,            bass(root, beat / 2 * 0.95))
            place(music, t0 + beat / 2, bass(root, beat / 2 * 0.95))
        # lead arp — 16ths up the chord, octave up
        arp = [chord[i % 3] * 2 for i in range(4)]
        if bt % 2 == 1: arp = arp[::-1]
        for s16 in range(4):
            place(music, t0 + s16 * beat / 4, pluck(arp[s16], beat / 4 * 0.95,
                                                    amp=0.10 if intro else 0.15))
    if intro:
        place(drums, b * bar, riser(bar))              # build riser under bar 0

# sidechain pump: duck the musical bus on every kick beat
sc = np.ones(N)
L = int(0.34 * SR); ramp = 0.32 + 0.68 * (np.arange(L) / L)
for b in range(1, nbars):
    for bt in range(4):
        s = int((b * bar + bt * beat) * SR)
        sc[s:s + L] = np.minimum(sc[s:s + L], ramp[:len(sc[s:s + L])])
music *= sc

mix = drums + music
# master: soft-clip + normalize + fades
mix = np.tanh(mix * 1.1)
mix /= (np.max(np.abs(mix)) + 1e-9); mix *= 0.94
fi = int(0.04 * SR); mix[:fi] *= np.linspace(0, 1, fi)
fo = int(1.9 * SR)
end = int(DUR * SR)
mix[end - fo:end] *= np.linspace(1, 0, fo); mix[end:] = 0
mix = mix[:end]

pcm = (np.clip(mix, -1, 1) * 32767).astype("<i2")
with wave.open(OUT, "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"wrote {OUT}  ({len(pcm)/SR:.1f}s @ {BPM:.0f} BPM)")
