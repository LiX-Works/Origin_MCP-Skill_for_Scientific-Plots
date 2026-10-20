"""Build the README overview figure (assets/overview.png) with the Python standard library.

Writes overview.svg and an overview.html wrapper next to the --output path; render the
HTML to PNG at 2x (3200 x 1680), e.g. with headless Chrome or Edge. The plot on the
Origin screen is a stylized illustration, not a real output.
"""
from pathlib import Path
import argparse
import math
from xml.sax.saxutils import escape

cli = argparse.ArgumentParser(description=__doc__)
cli.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "overview.svg")
args = cli.parse_args()

W, H = 1600, 764
SHIFT = -76  # everything moves up once the Skill card sits beside the MCP bridge
FONT = "Arial,Helvetica,sans-serif"
C = dict(
    ink="#16203A", sub="#2C3850", line="#2E3A55", card="#FFFFFF", cardStroke="#C3CDDD",
    amber="#E8960F", amberText="#A9650A", lead0="#22386A", lead1="#3866A6",
    mcp="#2E3F8F", mcpTint="#EEF1FB", skill="#5A3CC2", skillTint="#F1ECFD",
    cyan="#35D0E0", screen0="#0A1430", screen1="#152A57", chip="#EEF1F6", chipText="#3F4B63",
)

out = []
add = out.append


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def text(x, y, s, size=26, weight=700, fill=C["ink"], anchor="start", extra=""):
    add(f'<text x="{f(x)}" y="{f(y)}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}" {extra}>{escape(s)}</text>')


def line(d, stroke, width, extra=""):
    add(f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{width}" '
        f'stroke-linecap="round" stroke-linejoin="round" {extra}/>')


def head(x2, y2, ux, uy, color, size=22, half=11):
    bx, by = x2 - size * ux, y2 - size * uy
    add(f'<path d="M{f(x2)} {f(y2)} L{f(bx - half * uy)} {f(by + half * ux)} '
        f'L{f(bx + half * uy)} {f(by - half * ux)}Z" fill="{color}"/>')


def arrow(points, color=C["line"]):
    # The shaft stops inside the head, so the tip stays a sharp point.
    (x1, y1), (x2, y2) = points[-2], points[-1]
    n = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / n, (y2 - y1) / n
    end = (x2 - 13 * ux, y2 - 13 * uy)
    d = "M" + " L".join(f"{f(a)} {f(b)}" for a, b in points[:-1] + [end])
    add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="5.5" stroke-linejoin="round"/>')
    head(x2, y2, ux, uy, color)


def card(x, y, w, h, rx=24):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{C["card"]}" '
        f'stroke="{C["cardStroke"]}" stroke-width="1.8" filter="url(#shadow)"/>')


def chips(cx, y, labels, size=20, fill=C["chip"], color=C["chipText"], pad=32, gap=12):
    widths = [len(s) * size * 0.6 + pad for s in labels]
    x = cx - (sum(widths) + gap * (len(labels) - 1)) / 2
    for s, w in zip(labels, widths):
        add(f'<rect x="{f(x)}" y="{y}" width="{f(w)}" height="36" rx="18" fill="{fill}"/>')
        text(x + w / 2, y + 25, s, size, 700, color, "middle")
        x += w + gap


# plasma-like colormap for the stylized heatmap
STOPS = [(0, (13, 8, 135)), (.25, (126, 3, 168)), (.5, (204, 71, 120)), (.75, (248, 149, 64)), (1, (240, 249, 33))]


def cmap(t):
    t = min(max(t, 0), 1)
    for (a, ca), (b, cb) in zip(STOPS, STOPS[1:]):
        if t <= b:
            k = (t - a) / (b - a)
            return "#%02X%02X%02X" % tuple(round(ca[i] + k * (cb[i] - ca[i])) for i in range(3))
    return "#F0F921"


# ---------- layout ----------
MID = 450
IN = dict(x=30, y=340, w=200, h=220)
AG = dict(x=290, y=330, w=200, h=240)
MCP = dict(x=548, y=290, w=284, h=320)
OR = dict(x=880, y=250, w=380, h=400)
OUT = dict(x=1320, y=340, w=250, h=220)
SK = dict(x=24, y=112, w=520, h=150)
ROWS = [380, 438, 496, 554]  # pin centre lines
PINS = ["Import data", "Build graph", "Style & axes", "Save & export"]

# ---------- input ----------
card(IN["x"], IN["y"], IN["w"], IN["h"])
cx = IN["x"] + IN["w"] / 2
text(cx, IN["y"] + 52, "Your data", 30, 700, C["ink"], "middle")
gx, gy, cw, ch = cx - 66, IN["y"] + 78, 44, 22
for r in range(4):
    for c in range(3):
        fill = "#DCE6F6" if r == 0 else "#FFFFFF"
        add(f'<rect x="{gx + c * cw}" y="{gy + r * ch}" width="{cw}" height="{ch}" fill="{fill}" stroke="#7E92B5" stroke-width="1.6"/>')
text(cx, IN["y"] + 198, "+ figure request", 24, 400, C["sub"], "middle")

# ---------- skill (manual) ----------
card(SK["x"], SK["y"], SK["w"], SK["h"])
bx, by = SK["x"] + 30, SK["y"] + 28
# open book, solid
add(f'<path d="M{bx} {by + 6} q28 -12 52 0 v46 q-24 -10 -52 0z" fill="{C["skill"]}"/>')
add(f'<path d="M{bx + 56} {by + 6} q24 -12 52 0 v46 q-28 -10 -52 0z" fill="{C["skill"]}" opacity=".72"/>')
text(SK["x"] + 162, SK["y"] + 62, "Skill: plotting manual", 30)
chips(SK["x"] + SK["w"] / 2, SK["y"] + 92, ["Fonts", "Axes & units", "Colour", "Page size"],
      20, C["skillTint"], C["skill"], pad=22, gap=8)

# ---------- agent ----------
add(f'<rect x="{AG["x"]}" y="{AG["y"]}" width="{AG["w"]}" height="{AG["h"]}" rx="28" fill="url(#leadGrad)" filter="url(#leadShadow)"/>')
add(f'<rect x="{AG["x"]}" y="{AG["y"]}" width="{AG["w"]}" height="{AG["h"]}" rx="28" fill="url(#sheen)"/>')
acx = AG["x"] + AG["w"] / 2
text(acx, MID - 6, "AI", 52, 700, "#FFFFFF", "middle")
text(acx, MID + 40, "Agent", 34, 700, "#F2F6FD", "middle")

# ---------- MCP bridge ----------
mx, my, mw, mh = MCP["x"], MCP["y"], MCP["w"], MCP["h"]
add(f'<rect x="{mx}" y="{my}" width="{mw}" height="{mh}" rx="24" fill="#FFFFFF" stroke="{C["mcp"]}" stroke-width="4" filter="url(#shadow)"/>')
add(f'<path d="M{mx} {my + 52} V{my + 24} a24 24 0 0 1 24 -24 H{mx + mw - 24} a24 24 0 0 1 24 24 V{my + 52}Z" fill="{C["mcp"]}"/>')
text(mx + mw / 2, my + 36, "MCP bridge", 28, 700, "#FFFFFF", "middle")
# cables: agent -> sockets (ink), sockets -> Origin ports (glowing cyan)
for y, label in zip(ROWS, PINS):
    line(f"M{AG['x'] + AG['w']} {y}H{mx - 10}", C["line"], 5)
    add(f'<path d="M{mx + mw + 10} {y}H{OR["x"] - 4}" stroke="{C["cyan"]}" stroke-width="7" opacity=".35" filter="url(#glow)"/>')
    line(f"M{mx + mw + 10} {y}H{OR['x'] - 4}", "#1FA9BA", 4.5)
    add(f'<rect x="{mx + 22}" y="{y - 22}" width="{mw - 44}" height="44" rx="22" fill="{C["mcpTint"]}"/>')
    text(mx + mw / 2, y + 8, label, 22, 700, C["mcp"], "middle")
    for sx in (mx - 11, mx + mw - 9):
        add(f'<rect x="{sx}" y="{y - 10}" width="20" height="20" rx="4" fill="{C["mcp"]}"/>')
        add(f'<rect x="{sx + 6}" y="{y - 4}" width="8" height="8" rx="1.5" fill="{C["cyan"]}"/>')

# ---------- Origin screen ----------
ox, oy, ow, oh = OR["x"], OR["y"], OR["w"], OR["h"]
add(f'<rect x="{ox - 3}" y="{oy - 3}" width="{ow + 6}" height="{oh + 6}" rx="26" fill="none" stroke="{C["cyan"]}" stroke-width="6" opacity=".45" filter="url(#glow)"/>')
add(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" rx="24" fill="url(#screenGrad)" stroke="#3E6FA8" stroke-width="2"/>')
add(f'<path d="M{ox} {oy + 50} V{oy + 24} a24 24 0 0 1 24 -24 H{ox + ow - 24} a24 24 0 0 1 24 24 V{oy + 50}Z" fill="#1C3366"/>')
for i, col in enumerate(("#FF6B6B", "#FFC857", "#5EE6A8")):
    add(f'<circle cx="{ox + 28 + i * 22}" cy="{oy + 25}" r="7" fill="{col}"/>')
text(ox + 106, oy + 34, "Origin", 24, 700, "#FFFFFF")
for y in ROWS:  # ports on the screen edge
    add(f'<rect x="{ox - 8}" y="{y - 9}" width="14" height="18" rx="4" fill="{C["cyan"]}"/>')
# plot area
px, py, pw, ph = ox + 52, oy + 82, 272, 276
# faint grid
for k in range(1, 5):
    line(f"M{f(px + k * pw / 5)} {py}v{ph}", "#2D4A80", 1, 'opacity=".55"')
    line(f"M{px} {f(py + k * ph / 5)}h{pw}", "#2D4A80", 1, 'opacity=".55"')
# heatmap cells
nx, ny = 46, 46
for i in range(nx):
    for j in range(ny):
        u, v = (i + .5) / nx, (j + .5) / ny
        val = (0.55 * math.exp(-((u - .66) ** 2 + (v - .34) ** 2) / .045)
               + 0.42 * math.exp(-((u - .28) ** 2 + (v - .70) ** 2) / .06)
               + 0.10 * math.sin(6 * u) * math.cos(5 * v) + 0.08) * 1.25
        add(f'<rect x="{f(px + i * pw / nx)}" y="{f(py + j * ph / ny)}" width="{f(pw / nx + .4)}" '
            f'height="{f(ph / ny + .4)}" fill="{cmap(val)}"/>')
# glowing curve with markers on top
pts = []
for k in range(9):
    u = .06 + k * .11
    v = .78 - .55 * (1 - math.exp(-3.2 * u)) + .05 * math.sin(9 * u)
    pts.append((px + u * pw, py + v * ph))
d = "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts)
add(f'<path d="{d}" fill="none" stroke="{C["cyan"]}" stroke-width="9" opacity=".55" filter="url(#glow)"/>')
line(d, "#E9FDFF", 3.6)
for a, b in pts:
    add(f'<circle cx="{f(a)}" cy="{f(b)}" r="6" fill="#0A1430" stroke="#E9FDFF" stroke-width="2.6"/>')
# axes, ticks
line(f"M{px} {py}V{py + ph}H{px + pw}", "#B9C9E6", 2.6)
for k in range(6):
    line(f"M{f(px + k * pw / 5)} {py + ph}v8", "#B9C9E6", 2)
    line(f"M{px} {f(py + k * ph / 5)}h-8", "#B9C9E6", 2)
# colour bar
cbx = px + pw + 22
for k in range(40):
    add(f'<rect x="{cbx}" y="{f(py + k * ph / 40)}" width="16" height="{f(ph / 40 + .5)}" fill="{cmap(1 - k / 39)}"/>')
add(f'<rect x="{cbx}" y="{py}" width="16" height="{ph}" fill="none" stroke="#B9C9E6" stroke-width="1.6"/>')
for k in range(3):
    line(f"M{cbx + 16} {f(py + k * ph / 2)}h6", "#B9C9E6", 2)

# ---------- output ----------
card(OUT["x"], OUT["y"], OUT["w"], OUT["h"])
ocx = OUT["x"] + OUT["w"] / 2
text(ocx, OUT["y"] + 52, "Editable figure", 28, 700, C["ink"], "middle")
dx, dy = ocx - 40, OUT["y"] + 76
add(f'<path d="M{dx} {dy} h56 l24 24 v74 h-80z" fill="#FFFFFF" stroke="{C["mcp"]}" stroke-width="3"/>')
add(f'<path d="M{dx + 56} {dy} v24 h24" fill="none" stroke="{C["mcp"]}" stroke-width="3"/>')
line(f"M{dx + 14} {dy + 84}v-36M{dx + 14} {dy + 84}h50", C["mcp"], 2.4)
line(f"M{dx + 20} {dy + 74} l12 -12 l10 6 l18 -20", "#1FA9BA", 3.4)
add(f'<rect x="{dx - 30}" y="{dy + 16}" width="72" height="30" rx="6" fill="{C["mcp"]}"/>')
text(dx + 6, dy + 38, ".opju", 21, 700, "#FFFFFF", "middle")
text(ocx, OUT["y"] + 196, "Project + exports", 24, 400, C["sub"], "middle")

# ---------- flow arrows ----------
g = 7
arrow([(IN["x"] + IN["w"] + g, MID), (AG["x"] - g, MID)])
arrow([(acx, SK["y"] + SK["h"] + g), (acx, AG["y"] - g)], C["skill"])
arrow([(ox + ow + g, MID), (OUT["x"] - g, MID)])
# review loop: rendered figure back to the agent
ly = 720
arrow([(ox + ow / 2, oy + oh + g), (ox + ow / 2, ly), (acx, ly), (acx, AG["y"] + AG["h"] + g)], C["amber"])
lcx = (acx + ox + ow / 2) / 2
# the loop label carries the human: a person reviews the figure, the agent refines it
add(f'<rect x="{f(lcx - 286)}" y="{ly - 30}" width="572" height="60" rx="30" fill="#FFFFFF"/>')
# person mark inside a ring, sized to match the 30 px label
pcx = lcx - 246
add(f'<circle cx="{f(pcx)}" cy="{ly}" r="24" fill="#FFFFFF" stroke="{C["amber"]}" stroke-width="3.5"/>')
add(f'<circle cx="{f(pcx)}" cy="{ly - 7}" r="7.5" fill="{C["amber"]}"/>')
add(f'<rect x="{f(pcx - 12)}" y="{ly + 3}" width="24" height="13" rx="6.5" fill="{C["amber"]}"/>')
text(lcx + 22, ly + 11, "Human reviews, agent refines", 30, 700, C["amberText"], "middle")
chips(lcx, ly + 46, ["Scale", "Ticks", "Legend", "Values"], 22)

defs = f"""<defs>
  <linearGradient id="leadGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{C['lead0']}"/><stop offset="1" stop-color="{C['lead1']}"/></linearGradient>
  <linearGradient id="screenGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{C['screen0']}"/><stop offset="1" stop-color="{C['screen1']}"/></linearGradient>
  <linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".18"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <filter id="shadow" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="5" stdDeviation="8" flood-color="#16203A" flood-opacity=".10"/></filter>
  <filter id="leadShadow" x="-30%" y="-30%" width="160%" height="170%"><feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="#22386A" flood-opacity=".32"/></filter>
  <filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="5"/></filter>
</defs>"""
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       f'font-family="{FONT}" role="img" aria-labelledby="title desc">\n'
       '<title id="title">Origin MCP + Skill overview</title>\n'
       '<desc id="desc">Your data and figure request go to an AI agent. The Skill supplies plotting rules; '
       'the MCP bridge lets the agent import data, build the graph, set styles and axes, and save and export in Origin. '
       'The agent reviews the rendered figure and refines it, then delivers an editable Origin project and exports. '
       'The plot on the Origin screen is a stylized illustration.</desc>\n'
       f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>\n{defs}\n<g transform="translate(0 {SHIFT})">\n'
       + "\n".join(out) + "\n</g>\n</svg>\n")
args.output.write_text(svg, encoding="utf-8")
args.output.with_suffix(".html").write_text(
    '<!doctype html><meta charset="utf-8"><style>html,body{margin:0;background:#fff}svg{display:block}</style>' + svg,
    encoding="utf-8")
print(args.output)
