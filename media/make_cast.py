#!/usr/bin/env python3
"""Generate an asciicast v2 recording of the kickback CLI by running each
command under a PTY (so ANSI colors are preserved), with typing animation and
pauses. Output: media/kickback-demo.cast  →  render with `agg`."""
import os, pty, select, subprocess, json, fcntl, termios, struct, sys

ROWS, COLS = 32, 104
KB = os.path.expanduser("~/.local/bin/kickback")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kickback-demo.cast")

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
            try:
                data = os.read(mfd, 65536)
            except OSError:
                break
            if not data:
                break
            out += data
        elif p.poll() is not None:
            break
    try: os.close(mfd)
    except OSError: pass
    p.wait()
    return out.decode("utf-8", "replace")

events = []
t = 0.0
def emit(data, dt=0.0):
    global t
    t += dt
    events.append([round(t, 3), "o", data])

PROMPT = "\x1b[32m❯\x1b[0m "
def type_cmd(cmd, cps=0.028):
    emit(PROMPT, 0.35)
    for ch in cmd:
        emit(ch, cps)
    emit("\r\n", 0.25)

def show(cmd_args, label, hold=3.0, trim=None):
    type_cmd(label)
    out = run_capture(cmd_args)
    if trim:
        lines = out.split("\n")
        if len(lines) > trim:
            out = "\n".join(lines[:trim]) + "\n\x1b[2m   … (truncated for demo) …\x1b[0m\n"
    emit("\r\n".join(out.split("\n")), 0.15)
    emit("", hold)

# intro comment line (no command run)
type_cmd("# kickback — your Kickbacks.ai earnings, right in the terminal")
emit("", 1.0)

show([KB, "--version"], "kickback --version", hold=1.6)
show([KB], "kickback", hold=3.8)
show([KB, "earnings"], "kickback earnings", hold=3.8)
show([KB, "history"], "kickback history", hold=3.8, trim=18)
show([KB, "daily"], "kickback daily", hold=3.0)
show([KB, "auth"], "kickback auth", hold=3.0)
show([KB, "config"], "kickback config", hold=3.6)
show([KB, "doctor"], "kickback doctor", hold=3.8)
show([KB, "about"], "kickback about", hold=4.5, trim=24)

# closing card
type_cmd("clear")
emit("\x1b[2J\x1b[H", 0.3)
type_cmd("# install:  brew install kickback   —   safe by default, fully transparent")
emit("", 2.5)

header = {"version": 2, "width": COLS, "height": ROWS, "timestamp": 0,
          "env": {"TERM": "xterm-256color", "SHELL": "/bin/zsh"},
          "title": "kickback demo"}
with open(OUT, "w") as f:
    f.write(json.dumps(header) + "\n")
    for ev in events:
        f.write(json.dumps(ev) + "\n")
print(f"wrote {OUT}  ({len(events)} events, {t:.1f}s)")
