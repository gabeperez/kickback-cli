#!/usr/bin/env python3
"""
Hype-but-clean track for the Kickbacks CLI launch video — a fusion of the two
earlier drafts: the drive/energy of the fast EDM version (128 BPM, four-on-the-
floor, 16th-note arp, riser → drop, A minor Am–F–C–G, sidechain pump) with the
warm/clean synthesis of the house version (soft sine/triangle tones, additive
pad, gentle percussion, slap delay, warming master lowpass — no harsh saws/noise).

  <venv-python> media/make_track.py <out.wav> [duration] [bpm]

Structure: 2-bar intro (pad + arp) → riser → drop (full energy) → build → fade.
Needs numpy.
"""
import sys, wave
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "track.wav"
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 31.633
BPM = float(sys.argv[3]) if len(sys.argv) > 3 else 132.0

SR = 44100
np.random.seed(5)
beat = 60.0 / BPM
bar  = 4 * beat
N = int(DUR * SR) + int(2.0 * SR)
kickb = np.zeros(N); perc = np.zeros(N); bassb = np.zeros(N)
padb  = np.zeros(N); arpb = np.zeros(N); leadb = np.zeros(N); fx = np.zeros(N)

def place(buf, t, sig, g=1.0):
    s = int(t * SR)
    if s < 0: sig = sig[-s:]; s = 0
    e = min(s + len(sig), len(buf)); buf[s:e] += sig[:e - s] * g

def tt(dur): return np.arange(int(dur * SR)) / SR
def sine(f, x): return np.sin(2 * np.pi * f * x)
def tri(f, x):  return (2 / np.pi) * np.arcsin(np.sin(2 * np.pi * f * x))

def kick(dur=0.34, amp=1.05):
    x = tt(dur)
    pitch = 135 * np.exp(-x * 30) + 50                 # deeper, longer thump
    body = np.sin(2 * np.pi * np.cumsum(pitch) / SR) * np.exp(-x * 6.5)
    sub  = np.sin(2 * np.pi * 45 * x) * np.exp(-x * 9) * 0.5
    return (body + sub + np.exp(-x * 300) * 0.28) * amp

def clap(dur=0.17, amp=0.30):
    x = tt(dur); noise = np.random.rand(len(x)) * 2 - 1
    p = 0.0; y = np.zeros_like(noise)
    for i in range(len(noise)): p += 0.5 * (noise[i] - p); y[i] = p   # softened
    return y * np.exp(-x * 20) * amp

def hat(dur=0.03, amp=0.05):
    x = tt(dur); noise = np.diff(np.random.rand(int(dur * SR)) * 2 - 1, prepend=0.0)
    return noise * np.exp(-x * 130) * amp

def bass(f, dur, amp=0.30):
    x = tt(dur)
    # big low end: strong sub octave + fundamental + a little drive on top
    sig = 0.9 * sine(f / 2, x) + sine(f, x) + 0.30 * sine(2 * f, x) + 0.22 * tri(f, x)
    sig /= 2.4
    env = np.minimum(1, x * 110) * (0.82 + 0.18 * np.exp(-x * 2.5))
    return sig * env * amp

def pad(freqs, dur, amp=0.09):
    x = tt(dur); sig = np.zeros(len(x))
    for f in freqs: sig += sine(f, x) + 0.5 * sine(2 * f, x) + 0.22 * sine(3 * f, x)
    sig /= (len(freqs) * 1.7)
    return sig * (1 - np.exp(-x * 7)) * np.exp(-x * 0.5) * amp

def pluck(f, dur, amp=0.12):
    x = tt(dur)
    sig = tri(f, x) + 0.3 * sine(2 * f, x)
    return sig * np.exp(-x * 8) * (1 - np.exp(-x * 350)) * amp

def lead(f, dur, amp=0.15):
    x = tt(dur)
    sig = tri(f * (1 + 0.004 * np.sin(2 * np.pi * 5 * x)), x) + 0.4 * sine(2 * f, x)
    return sig * (1 - np.exp(-x * 45)) * np.exp(-x * 2.3) * amp

def riser(dur, amp=0.32):
    x = tt(dur); noise = np.random.rand(len(x)) * 2 - 1
    p = 0.0; y = np.zeros_like(noise)
    for i in range(len(noise)): p += 0.15 * (noise[i] - p); y[i] = p    # darkened noise
    return y * (x / dur) ** 2 * amp

# A minor — Am–F–C–G (1 bar each): chord tones + bass root (Hz)
A,B,C,D,E,F,G = 220.,246.94,261.63,293.66,329.63,174.61,196.0
PROG = [([A,C,E], 110.0/2), ([F,A,C], 174.61/4), ([C,E,G], 130.81/2), ([G,B,D], 98.0)]

DROP = 1                          # bar where the beat drops (earlier = more immediate)
nbars = int(DUR / bar) + 1
for b in range(nbars):
    chord, root = PROG[b % 4]
    intro = b < DROP
    place(padb, b * bar, pad(chord, bar))
    for bt in range(4):
        t0 = b * bar + bt * beat
        if not intro:
            place(kickb, t0, kick())
            if bt in (1, 3): place(perc, t0, clap())
            place(bassb, t0,            bass(root, beat / 2 * 0.95))
            place(bassb, t0 + beat / 2, bass(root, beat / 2 * 0.95))
        place(perc, t0 + beat / 2, hat())
        # arp — 8ths in the intro, driving 16ths in the drop
        div = 2 if intro else 4
        arp = [chord[0], chord[1], chord[2], chord[0] * 2]
        if bt % 2: arp = arp[::-1]
        for s in range(div):
            note = arp[s % 4] * (1 if intro else (2 if s % 2 else 1))
            place(arpb, t0 + s * beat / div, pluck(note, beat / div * 0.95,
                                                   amp=0.08 if intro else 0.12))
    # lead motif in the second half (top-line)
    if b >= 9 and b % 2 == 1:
        motif = [chord[2] * 2, chord[1] * 2, chord[0] * 2, chord[2] * 2]
        for i, f in enumerate(motif):
            place(leadb, b * bar + i * beat, lead(f, beat * 0.9))

# riser into the drop, then a big impact + sub-boom on the downbeat
place(fx, max(0.0, (DROP - 1) * bar), riser(bar))
def subboom(dur=0.9, amp=0.7):
    x = tt(dur)
    return np.sin(2 * np.pi * (55 * np.exp(-x * 5) + 38) * x) * np.exp(-x * 3.2) * amp
place(fx, DROP * bar, kick(0.5, 0.7))            # downbeat impact on the drop
place(fx, DROP * bar, subboom())                 # booming low-end drop hit
mid = (nbars // 2)
place(fx, (mid - 1) * bar, riser(bar, 0.30))
place(fx, mid * bar, subboom(0.7, 0.5))          # second-half re-drop weight

# sidechain pump on pad + bass + arp (the groove)
sc = np.ones(N); L = int(0.26 * SR); ramp = 0.42 + 0.58 * (np.arange(L) / L)
for b in range(DROP, nbars):
    for bt in range(4):
        s = int((b * bar + bt * beat) * SR)
        sc[s:s + L] = np.minimum(sc[s:s + L], ramp[:len(sc[s:s + L])])
padb *= (0.5 + 0.5 * sc); bassb *= sc; arpb *= (0.65 + 0.35 * sc)

# slap delay for space (feed-forward taps)
def slap(buf, taps):
    out = buf.copy()
    for dt, g in taps:
        d = int(dt * SR); out[d:] += buf[:N - d] * g
    return out
arpb  = slap(arpb,  [(beat * 0.75, 0.26), (beat * 1.5, 0.12)])
leadb = slap(leadb, [(beat * 0.75, 0.28), (beat * 1.5, 0.13)])

mix = kickb + perc + bassb + padb + arpb + leadb + fx
# master: warming lowpass (~4 kHz) then soft-clip + normalize + fades
def lp1(sig, a):
    y = np.empty_like(sig); p = 0.0
    for i in range(len(sig)): p += a * (sig[i] - p); y[i] = p
    return y
mix = lp1(mix, 0.64)
mix = np.tanh(mix * 1.1)
mix /= (np.max(np.abs(mix)) + 1e-9); mix *= 0.95
fi = int(0.04 * SR); mix[:fi] *= np.linspace(0, 1, fi)
end = int(DUR * SR); fo = int(1.8 * SR)
mix[end - fo:end] *= np.linspace(1, 0, fo); mix = mix[:end]

pcm = (np.clip(mix, -1, 1) * 32767).astype("<i2")
with wave.open(OUT, "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"wrote {OUT}  ({len(pcm)/SR:.1f}s @ {BPM:.0f} BPM, hype+clean)")
