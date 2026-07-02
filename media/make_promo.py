#!/usr/bin/env python3
"""
Promotional / hype cut of the kickback demo.

HOW TO EDIT THIS VIDEO:
  Scroll down to the STORYBOARD block. It's a plain list — reorder, reword,
  retime. You only ever touch STORYBOARD; the engine below renders it.

  Card("text", style="green", hold=1.8)   → full-screen centered text card
  Card(["line one", "", "line two"], style=["white","dim","green"])
                                           → multi-line card ("" = blank spacer)
  Run("earnings", hold=2.4, trim=14)       → types `kickback earnings` and shows
                                             the REAL output (trim caps long ones)
  CTA(brand=, tagline=, command=, url=)    → the closing call-to-action card

  styles: dim · white · green · greenbold · yellow
  timing: hold = seconds on screen.  ROWS/COLS = canvas size (below).

THEN RENDER:
  python3 media/make_promo.py
  agg --theme dracula --font-size 22 --line-height 1.4 --last-frame-duration 3 \
      media/kickback-promo.cast media/kickback-promo.gif
  ffmpeg -y -i media/kickback-promo.gif -vsync cfr -r 30 -movflags +faststart \
      -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" media/kickback-promo.mp4

Tip: don't preview with `ffmpeg -ss` — it mis-seeks these GIFs. Open the GIF/MP4 directly.
"""
import os, pty, select, subprocess, json, fcntl, termios, struct

# --- canvas ---------------------------------------------------------------
ROWS, COLS = 28, 100
KB = os.path.expanduser("~/.local/bin/kickback")

# --- step types (just data — see STORYBOARD) ------------------------------
class Card:
    def __init__(self, text, style="white", hold=1.8, pre=0.35):
        self.text, self.style, self.hold, self.pre = text, style, hold, pre
class Run:
    def __init__(self, args="", hold=2.0, trim=None):
        self.args, self.hold, self.trim = args, hold, trim
class CTA:
    def __init__(self, brand, tagline, command, url):
        self.brand, self.tagline, self.command, self.url = brand, tagline, command, url


# ===========================================================================
#  ███  STORYBOARD — EDIT EVERYTHING IN THIS LIST  ███
# ===========================================================================
OPENER = [
    Card("what you earn — live, in your terminal.", style="white", hold=1.6),
]

# each function: a tagline (the value) → the command (the proof)
FEATURES = [
    Run("",         hold=1.8),   # the flagship status view (the opener card leads into it)
    Card("track every cent.",            style="greenbold", hold=1.0), Run("earnings", hold=1.6),
    Card("day by day.",                  style="greenbold", hold=1.0), Run("daily",    hold=1.4),
    Card("week. month. year.",           style="greenbold", hold=1.0),
        Run("weekly", hold=1.2), Run("monthly", hold=1.2), Run("yearly", hold=1.4),
    Card("every ad you've seen.",        style="greenbold", hold=1.0), Run("history",  hold=1.5, trim=11),
    # NOTE: `watch` (runs forever) and `notify` (fires a real notification) don't
    # montage cleanly — they live in the slower demo + README instead.
]

# the reveal — in the launch cut, the menu bar VIDEO plays right after this card.
MENUBAR_TEASE = [Card("Oh, it's also on your menu bar.", style="greenbold", hold=1.8)]
GRATITUDE     = [Card("powered by Kickbacks.ai", style="dim", hold=1.4)]
CTA_STEP      = [CTA(brand="Kickbacks CLI",
                     tagline="see everything you're earning — CLI + menu bar app.",
                     command="brew install --cask gabeperez/kickback/kickbacks-bar",
                     url="https://gabeperez.github.io/kickback-cli")]

# `python3 make_promo.py [promo|montage|outro]`
#   promo   → standalone terminal hype cut (default): opener → features → tease → CTA
#   montage → launch part 1: opener → features → "Oh, it's also on your menu bar."
#             (the menu bar VIDEO is stitched in after this)
#   outro   → launch part 2: gratitude → CTA  (plays after the menu bar video)
import sys
_MODE = sys.argv[1] if len(sys.argv) > 1 else "promo"
_TARGETS = {
    "promo":   (OPENER + FEATURES + MENUBAR_TEASE + GRATITUDE + CTA_STEP, "kickback-promo.cast"),
    "montage": (OPENER + FEATURES + MENUBAR_TEASE,                        "kickback-launch-montage.cast"),
    "outro":   (GRATITUDE + CTA_STEP,                                     "kickback-launch-outro.cast"),
}
STORYBOARD, _OUTNAME = _TARGETS[_MODE]
# ===========================================================================
#  end of storyboard — engine below, you shouldn't need to touch it
# ===========================================================================


OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), _OUTNAME)
COLORS = {
    "dim":       "\x1b[2;37m",
    "white":     "\x1b[1;37m",
    "green":     "\x1b[38;5;48m",
    "greenbold": "\x1b[1;38;5;48m",
    "yellow":    "\x1b[38;5;221m",
}
G, GB, W, D, R = COLORS["green"], COLORS["greenbold"], COLORS["white"], COLORS["dim"], "\x1b[0m"

events, t = [], 0.0
def emit(data, dt=0.0):
    global t; t += dt
    events.append([round(t, 3), "o", data])
def clear(): emit("\x1b[2J\x1b[H", 0.0)
def center(text, vis): return " " * max(0, (COLS - vis) // 2) + text

def run_capture(args):
    mfd, sfd = pty.openpty()
    fcntl.ioctl(sfd, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))
    env = dict(os.environ, TERM="xterm-256color", COLUMNS=str(COLS), LINES=str(ROWS))
    p = subprocess.Popen(args, stdin=sfd, stdout=sfd, stderr=sfd, env=env, close_fds=True)
    os.close(sfd)
    out = b""
    while True:
        r, _, _ = select.select([mfd], [], [], 0.3)
        if mfd in r:
            try: data = os.read(mfd, 65536)
            except OSError: break
            if not data: break
            out += data
        elif p.poll() is not None:
            break
    try: os.close(mfd)
    except OSError: pass
    p.wait()
    return out.decode("utf-8", "replace")

def render_card(step):
    lines = step.text if isinstance(step.text, list) else [step.text]
    styles = step.style if isinstance(step.style, list) else [step.style] * len(lines)
    clear(); emit("", step.pre)
    emit("\r\n" * max(0, (ROWS - len(lines)) // 2 - 1))
    for line, sty in zip(lines, styles):
        col = COLORS.get(sty, W)
        emit(center(f"{col}{line}{R}", len(line)) + "\r\n")
    emit("", step.hold)

def render_run(step):
    label = "kickback" + (f" {step.args}" if step.args else "")
    args = [KB] + (step.args.split() if step.args else [])
    clear()
    emit(f"{G}❯{R} ", 0.12)
    for ch in label: emit(ch, 0.007)
    emit("\r\n", 0.15)
    out = run_capture(args)
    if step.trim:
        out = "\n".join(out.split("\n")[:step.trim])
    emit("\r\n".join(out.split("\n")), 0.12)
    emit("", step.hold)

def render_cta(step):
    clear(); emit("", 0.3)
    emit("\r\n" * max(0, (ROWS - 7) // 2 - 1))
    emit(center(f"{W}{step.brand}{G}.{R}", len(step.brand) + 1) + "\r\n", 0.25)
    emit("\r\n", 0.15)
    emit(center(f"{D}{step.tagline}{R}", len(step.tagline)) + "\r\n", 0.4)
    emit("\r\n", 0.15)
    emit(center(f"{G}❯{R} {GB}{step.command}{R}", len(step.command) + 2) + "\r\n", 0.5)
    emit(center(f"{D}{step.url}{R}", len(step.url)) + "\r\n", 0.3)
    emit("", 3.0)

for step in STORYBOARD:
    if isinstance(step, Card): render_card(step)
    elif isinstance(step, Run): render_run(step)
    elif isinstance(step, CTA): render_cta(step)

header = {"version": 2, "width": COLS, "height": ROWS, "timestamp": 0,
          "env": {"TERM": "xterm-256color", "SHELL": "/bin/zsh"}, "title": "kickback promo"}
with open(OUT, "w") as f:
    f.write(json.dumps(header) + "\n")
    for ev in events:
        f.write(json.dumps(ev) + "\n")
print(f"wrote {OUT}  ({len(events)} events, {t:.1f}s)")
