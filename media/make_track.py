#!/usr/bin/env python3
"""
Epic-but-upbeat hype track for the Kickbacks CLI launch video — synthesized from
scratch (no samples). Cinematic "trailer" flavour (Michael Bay / Zimmer-ish):
huge BRAAM brass, taiko drums, a driving staccato string/brass ostinato, power
chords, risers + impacts, all over a four-on-the-floor pulse so it stays upbeat.
Convolution reverb (synth impulse) gives it size. A minor: Am–F–C–G.

  <venv-python> media/make_track.py <out.wav> [duration] [bpm]

Impacts are placed on the beat grid AND at cinematic "hit points" (the menu-bar
reveal ~23s and the CTA ~26s) so it feels scored to the cut. Needs numpy.
"""
import sys, wave
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "track.wav"
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 31.633
BPM = float(sys.argv[3]) if len(sys.argv) > 3 else 150.0

SR = 44100
np.random.seed(11)
beat = 60.0 / BPM
bar  = 4 * beat
N = int(DUR * SR) + int(2.5 * SR)          # tail room for reverb/fades
drums = np.zeros(N); brass = np.zeros(N); melody = np.zeros(N); low = np.zeros(N)

# cinematic hit points (seconds) — synced to the cut: menu-bar reveal, CTA
HITS = [0.0, 23.0, 26.0]

def place(buf, t, sig, g=1.0):
    s = int(t * SR)
    if s < 0: sig = sig[-s:]; s = 0
    e = min(s + len(sig), len(buf)); buf[s:e] += sig[:e - s] * g

def tt(dur): return np.arange(int(dur * SR)) / SR

def saw(f, x, detune=0.0):
    def s(g): u = g * x; return 2 * (u - np.floor(0.5 + u))
    return s(f) if not detune else (s(f) + s(f * (1 + detune)) + s(f * (1 - detune))) / 3

# --- big brass BRAAM: stacked octaves+fifth, swell attack, vibrato ---------
def braam(root, dur=1.6, amp=0.5):
    x = tt(dur)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.5 * x)
    voices = [root, root, root * 1.5, root * 2, root * 2]
    sig = sum(saw(f * vib, x, detune=0.01) for f in voices) / len(voices)
    env = (1 - np.exp(-x * 14)) * np.exp(-x * 1.1)      # swell in, long body
    # opening lowpass (one-pole) so the attack "blooms"
    a = np.clip(0.02 + 0.5 * (1 - np.exp(-x * 6)), 0, 0.6)
    y = np.zeros_like(sig); p = 0.0
    for i in range(len(sig)):
        p += a[i] * (sig[i] - p); y[i] = p
    return y * env * amp

# --- shorter brass stab (accents) -----------------------------------------
def stab(f, dur=0.28, amp=0.32):
    x = tt(dur)
    sig = (saw(f, x, 0.01) + saw(f * 1.5, x, 0.01) + saw(f * 2, x, 0.01)) / 3
    env = (1 - np.exp(-x * 60)) * np.exp(-x * 6)
    return sig * env * amp

# --- taiko / epic tom: boomy pitched membrane + body noise -----------------
def taiko(freq=95, dur=0.55, amp=0.85):
    x = tt(dur)
    pitch = freq * (1 + 1.2 * np.exp(-x * 22))
    body = np.sin(2 * np.pi * np.cumsum(pitch) / SR) * np.exp(-x * 5.5)
    knock = (np.random.rand(len(x)) * 2 - 1) * np.exp(-x * 40) * 0.25
    return (body + knock) * amp

def kick(dur=0.26, amp=0.8):
    x = tt(dur)
    pitch = 130 * np.exp(-x * 34) + 48
    return (np.sin(2 * np.pi * np.cumsum(pitch) / SR) * np.exp(-x * 8)) * amp

def snare(dur=0.25, amp=0.5):
    x = tt(dur); noise = np.random.rand(len(x)) * 2 - 1
    tone = np.sin(2 * np.pi * 180 * x) * 0.3
    return (noise + tone) * np.exp(-x * 16) * amp

def hat(dur=0.04, amp=0.16):
    x = tt(dur); noise = np.diff(np.random.rand(int(dur * SR)) * 2 - 1, prepend=0.0)
    return noise * np.exp(-x * 80) * amp

def power_bass(root, dur, amp=0.24):
    x = tt(dur)
    sig = (saw(root, x, 0.004) + 0.6 * saw(root * 1.5, x, 0.004)) / 1.6
    env = np.minimum(1, x * 120) * (0.7 + 0.3 * np.exp(-x * 2))
    return sig * env * amp

def ostinato(f, dur, amp=0.12):
    x = tt(dur)
    sig = saw(f, x, 0.008)
    env = (1 - np.exp(-x * 200)) * np.exp(-x * 11)       # staccato pluck
    return sig * env * amp

def impact(dur=1.6, amp=0.7):
    x = tt(dur); noise = np.random.rand(len(x)) * 2 - 1
    crash = noise * np.exp(-x * 3.5)
    boom = np.sin(2 * np.pi * (60 * np.exp(-x * 6) + 35) * x) * np.exp(-x * 4)
    return (crash * 0.6 + boom) * amp

def riser(dur, amp=0.4):
    x = tt(dur); noise = np.random.rand(len(x)) * 2 - 1
    swell = noise * (x / dur) ** 2.2
    pitch = np.sin(2 * np.pi * (200 + 1200 * (x / dur) ** 2) * x) * (x / dur)
    return (swell * 0.7 + pitch * 0.3) * amp

# A minor progression: chord tones + bass root (Hz)
A,Bf,B,C,D,E,F,G = 220.,233.08,246.94,261.63,293.66,329.63,174.61,196.0
PROG = [([A,C,E],110.0), ([F,A,C],87.31), ([C,E,G],130.81), ([G,B,D],98.0)]

nbars = int(DUR / bar) + 1
for b in range(nbars):
    chord, root = PROG[b % 4]
    phrase_start = (b % 4 == 0)
    build = b < 1
    for bt in range(4):
        t0 = b * bar + bt * beat
        # --- drums: four-on-floor kick + taiko weight on 1&3 + snare on 3 ---
        if not build:
            place(drums, t0, kick())
            if bt in (0, 2): place(drums, t0, taiko())
            if bt == 2:      place(drums, t0, snare())
        place(drums, t0,            hat(amp=0.10))
        place(drums, t0 + beat / 2, hat(amp=0.16))
        # --- power bass on 8ths ---
        if not build:
            place(low, t0,            power_bass(root, beat / 2 * 0.95))
            place(low, t0 + beat / 2, power_bass(root, beat / 2 * 0.95))
        # --- driving ostinato: 16ths up/down the chord (octave up) ---
        arp = [chord[i % 3] * 2 for i in range(4)]
        if bt % 2: arp = arp[::-1]
        for s in range(4):
            place(melody, t0 + s * beat / 4, ostinato(arp[s], beat / 4 * 0.95,
                                                       amp=0.07 if build else 0.12))
    # --- brass: BRAAM at each 4-bar phrase, stabs mid-phrase ---
    if phrase_start and not build:
        place(brass, b * bar, braam(root, dur=min(bar * 2, 3.0)), g=1.0)
    elif not build:
        place(brass, b * bar, stab(root * 2, 0.3))
        place(brass, b * bar + 2 * beat, stab(chord[1] * 2, 0.3))
    if build:
        place(drums, b * bar, riser(bar))
        place(brass, b * bar, braam(root, dur=bar * 1.5, amp=0.4))

# cinematic impacts + braam swells at the hit points (menu-bar reveal, CTA)
for h in HITS:
    place(drums, h, impact())
    root = PROG[int(h / bar) % 4][1]
    place(brass, max(0, h - 0.02), braam(root, dur=2.2, amp=0.42))
# a riser leading into the last two hit points
for h in HITS[1:]:
    place(drums, h - bar, riser(bar, amp=0.5))

# --- sidechain pump on the musical busses (keeps the pulse punchy) ---------
sc = np.ones(N); L = int(0.30 * SR); ramp = 0.4 + 0.6 * (np.arange(L) / L)
for b in range(1, nbars):
    for bt in range(4):
        s = int((b * bar + bt * beat) * SR)
        sc[s:s + L] = np.minimum(sc[s:s + L], ramp[:len(sc[s:s + L])])
melody *= sc; brass *= (0.6 + 0.4 * sc); low *= sc

dry = drums + brass + melody + low

# --- convolution reverb (synth IR: dark exponential-decay noise) -----------
ir_len = int(1.6 * SR); xi = np.arange(ir_len) / SR
ir = (np.random.rand(ir_len) * 2 - 1) * np.exp(-xi * 4.0)
# darken the tail (one-pole lowpass)
lp = np.zeros_like(ir); p = 0.0
for i in range(ir_len): p += 0.25 * (ir[i] - p); lp[i] = p
ir = lp / (np.max(np.abs(lp)) + 1e-9)
nfft = 1 << (len(dry) + ir_len - 1).bit_length()
wet = np.fft.irfft(np.fft.rfft(dry, nfft) * np.fft.rfft(ir, nfft), nfft)[:len(dry)]
wet /= (np.max(np.abs(wet)) + 1e-9)
mix = 0.78 * dry + 0.34 * wet * np.max(np.abs(dry))

# --- master: soft-clip, normalize, fades ----------------------------------
mix = np.tanh(mix * 1.15)
mix /= (np.max(np.abs(mix)) + 1e-9); mix *= 0.95
fi = int(0.03 * SR); mix[:fi] *= np.linspace(0, 1, fi)
end = int(DUR * SR); fo = int(2.0 * SR)
mix[end - fo:end] *= np.linspace(1, 0, fo); mix = mix[:end]

pcm = (np.clip(mix, -1, 1) * 32767).astype("<i2")
with wave.open(OUT, "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"wrote {OUT}  ({len(pcm)/SR:.1f}s @ {BPM:.0f} BPM, epic)")
