#!/usr/bin/env python3
"""
Upbeat, warm electronic track for the Kickbacks CLI launch video — synthesized
from scratch (no samples). Clean "uplifting house" feel: soft sine/triangle
tones (no harsh saws), four-on-the-floor kick, sub bass, a warm additive pad,
a flowing arpeggio, light hats + clap, sidechain pump, and a gentle slap delay.
C major, I–V–vi–IV (C–G–Am–F). 122 BPM.

  <venv-python> media/make_track.py <out.wav> [duration] [bpm]

Deliberately soft/consonant so it reads as pleasant even without harsh synths.
Needs numpy.
"""
import sys, wave
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "track.wav"
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 31.633
BPM = float(sys.argv[3]) if len(sys.argv) > 3 else 122.0

SR = 44100
np.random.seed(3)
beat = 60.0 / BPM
bar  = 4 * beat
N = int(DUR * SR) + int(2.0 * SR)
kickb = np.zeros(N); perc = np.zeros(N); bassb = np.zeros(N)
padb  = np.zeros(N); arpb = np.zeros(N); leadb = np.zeros(N)

def place(buf, t, sig, g=1.0):
    s = int(t * SR)
    if s < 0: sig = sig[-s:]; s = 0
    e = min(s + len(sig), len(buf)); buf[s:e] += sig[:e - s] * g

def tt(dur): return np.arange(int(dur * SR)) / SR
def sine(f, x): return np.sin(2 * np.pi * f * x)
def tri(f, x):  return (2 / np.pi) * np.arcsin(np.sin(2 * np.pi * f * x))

def kick(dur=0.32, amp=0.92):
    x = tt(dur)
    pitch = 115 * np.exp(-x * 32) + 47
    body = np.sin(2 * np.pi * np.cumsum(pitch) / SR) * np.exp(-x * 7)
    click = np.exp(-x * 300) * 0.25
    return (body + click) * amp

def clap(dur=0.18, amp=0.28):
    x = tt(dur); noise = np.random.rand(len(x)) * 2 - 1
    # soften: lowpass the noise so it's a warm clap, not a hiss
    p = 0.0; y = np.zeros_like(noise)
    for i in range(len(noise)): p += 0.5 * (noise[i] - p); y[i] = p
    return y * np.exp(-x * 20) * amp

def hat(dur=0.028, amp=0.035):
    x = tt(dur); noise = np.diff(np.random.rand(int(dur * SR)) * 2 - 1, prepend=0.0)
    return noise * np.exp(-x * 150) * amp

def sub(f, dur, amp=0.24):
    x = tt(dur)
    sig = sine(f, x) + 0.25 * sine(2 * f, x)          # sub + gentle 2nd for presence
    env = np.minimum(1, x * 90) * (0.85 + 0.15 * np.exp(-x * 3))
    return sig * env * amp

def pad(freqs, dur, amp=0.10):
    x = tt(dur); sig = np.zeros(len(x))
    for f in freqs:                                    # additive, warm
        sig += sine(f, x) + 0.5 * sine(2 * f, x) + 0.25 * sine(3 * f, x)
    sig /= (len(freqs) * 1.75)
    env = (1 - np.exp(-x * 6)) * np.exp(-x * 0.5)      # slow swell, gentle decay
    return sig * env * amp

def pluck(f, dur, amp=0.13):
    x = tt(dur)
    sig = tri(f, x) + 0.3 * sine(2 * f, x)
    env = np.exp(-x * 7) * (1 - np.exp(-x * 300))
    return sig * env * amp

def lead(f, dur, amp=0.16):
    x = tt(dur)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5 * x)
    sig = tri(f * vib, x) + 0.4 * sine(2 * f, x)
    env = (1 - np.exp(-x * 40)) * np.exp(-x * 2.2)
    return sig * env * amp

# C major: chord tones + bass root (Hz).  C–G–Am–F  (I–V–vi–IV)
C,D,E,F,G,A,B = 261.63,293.66,329.63,349.23,392.0,440.0,493.88
PROG = [([C,E,G], 130.81/2),   # C  (root ~65)
        ([G,B,D], 98.0/2),     # G
        ([A,C,E], 110.0/2),    # Am
        ([F,A,C], 87.31/2)]    # F
CHORDS_PER = 2                 # bars per chord

nbars = int(DUR / bar) + 1
for b in range(nbars):
    chord, root = PROG[(b // CHORDS_PER) % 4]
    intro = b < 2                                      # 2-bar intro: pad + arp only
    if b % CHORDS_PER == 0:                             # sustain a pad across each chord
        place(padb, b * bar, pad(chord, bar * CHORDS_PER))
    for bt in range(4):
        t0 = b * bar + bt * beat
        if not intro:
            place(kickb, t0, kick())
            if bt in (1, 3): place(perc, t0, clap())
        place(perc, t0 + beat / 2, hat())              # soft offbeat hat
        if not intro:
            place(bassb, t0,            sub(root, beat / 2 * 0.95))
            place(bassb, t0 + beat / 2, sub(root, beat / 2 * 0.95))
        # flowing arpeggio (8ths): root, 3rd, 5th, octave, 5th, 3rd ...
        seq = [chord[0], chord[1], chord[2], chord[0] * 2, chord[2], chord[1], chord[0] * 2, chord[2]]
        for e8 in range(2):
            idx = (bt * 2 + e8) % len(seq)
            place(arpb, t0 + e8 * beat / 2, pluck(seq[idx], beat / 2 * 0.9,
                                                  amp=0.09 if intro else 0.13))
    # simple lead motif in the second half (top-line, octave up on chord tones)
    if b >= 8 and b % 2 == 0:
        motif = [chord[2] * 2, chord[0] * 2, chord[1] * 2, chord[2] * 2]
        for i, f in enumerate(motif):
            place(leadb, b * bar + i * beat, lead(f, beat * 0.9))

# sidechain pump on pad + bass + arp (classic house groove)
sc = np.ones(N); L = int(0.28 * SR); ramp = 0.45 + 0.55 * (np.arange(L) / L)
for b in range(2, nbars):
    for bt in range(4):
        s = int((b * bar + bt * beat) * SR)
        sc[s:s + L] = np.minimum(sc[s:s + L], ramp[:len(sc[s:s + L])])
padb *= (0.55 + 0.45 * sc); bassb *= sc; arpb *= (0.7 + 0.3 * sc)

# gentle slap delay on arp + lead for space (feed-forward taps, no mud)
def slap(buf, times_gains):
    out = buf.copy()
    for dt, g in times_gains:
        d = int(dt * SR); out[d:] += buf[:N - d] * g
    return out
arpb  = slap(arpb,  [(beat * 0.75, 0.28), (beat * 1.5, 0.12)])
leadb = slap(leadb, [(beat * 0.75, 0.30), (beat * 1.5, 0.14)])

mix = kickb + perc + bassb + padb + arpb + leadb
# master: warm it with a gentle 2-pole lowpass (~4 kHz), then soft-clip/normalize
def lp1(sig, a):
    y = np.empty_like(sig); p = 0.0
    for i in range(len(sig)): p += a * (sig[i] - p); y[i] = p
    return y
mix = lp1(mix, 0.62)
mix = np.tanh(mix * 1.08)
mix /= (np.max(np.abs(mix)) + 1e-9); mix *= 0.94
fi = int(0.05 * SR); mix[:fi] *= np.linspace(0, 1, fi)
end = int(DUR * SR); fo = int(1.8 * SR)
mix[end - fo:end] *= np.linspace(1, 0, fo); mix = mix[:end]

pcm = (np.clip(mix, -1, 1) * 32767).astype("<i2")
with wave.open(OUT, "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"wrote {OUT}  ({len(pcm)/SR:.1f}s @ {BPM:.0f} BPM, warm/house)")
