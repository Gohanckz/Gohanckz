"""Genera los SVG del README del perfil (misma estética que gohanckz.github.io).

    python scripts/build.py            # banner, tarjetas de proyectos e indicadores
    python scripts/build.py --static   # solo banner y proyectos (sin llamadas a la API)

En GitHub Actions usa GITHUB_TOKEN para la API; en local funciona sin token
(límite de 60 peticiones/hora, de sobra para una ejecución).
"""
import base64, datetime as dt, html, json, os, re, sys, textwrap, urllib.request
from collections import defaultdict

USER = "Gohanckz"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

ACC, ACC_DIM, FG, MUTED, LINE, BG = "#39ff6a", "#166e2e", "#f2f2f2", "#8a8a8a", "#262626", "#000"
LEVELS = ["#101010", "#0c3d1a", "#157a32", "#24c04f", "#39ff6a"]

PROJECTS = [
    ("Synckz", "https://synckz.com", "Autonomous offensive agent system for hackers and bug bounty hunters.", ["AI agents", "Bug bounty"]),
    ("DeepMaw", "https://deepmaw.com", "Bug bounty and pentest project management, driven over MCP by offensive agents.", ["MCP", "Ops"]),
    ("OOB", "https://console.oob.synckz.com", "Out-of-band collaborator for pentesting, bug bounty and vulnerability validation.", ["Out-of-band", "Validation"]),
    ("Hydra", "https://hydra.synckz.com", "Anti-piracy platform: monitors domains and apps that redistribute illegal streams, verifies blocking ISP by ISP and builds cases for the regulator.", ["Anti-piracy", "IPTV"]),
    ("bugbounty.cl", "https://bugbounty.cl", "Official site of Chile's national bug bounty team (Team Chile), with a hunter ranking synced from HackerOne.", ["Community", "HackerOne"]),
    ("YouTube", "https://www.youtube.com/@gohanckz", "Hacking and bug bounty content: techniques, vulnerabilities and real cases explained (ES).", ["Content", "Bug bounty"]),
]

# Ojo 16x16 del favicon: G = contorno, i = iris, d = iris oscuro
EYE = """
................
................
................
....GGGGGGGG....
..GG........GG..
.G....diid....G.
G....diiiid....G
G...dii..iid...G
G....diiiid....G
.G....diid....G.
..GG........GG..
....GGGGGGGG....
""".strip("\n").splitlines()


def font_face(name, file):
    with open(os.path.join(ROOT, "scripts", "fonts", file), "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"@font-face{{font-family:'{name}';src:url(data:font/woff2;base64,{b64}) format('woff2')}}"


FONTS = font_face("Px", "Silkscreen-400.woff2") + font_face("Mono", "JetBrainsMono-400.woff2")
BASE_CSS = FONTS + f"""
.px{{font-family:'Px',monospace}} .mono{{font-family:'Mono',ui-monospace,monospace}}
.fg{{fill:{FG}}} .acc{{fill:{ACC}}} .mut{{fill:{MUTED}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""

esc = lambda s: html.escape(str(s), quote=True)


def svg(w, h, body, css="", title=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">'
            f"<title>{esc(title)}</title><style>{BASE_CSS}{css}</style>"
            f'<rect width="{w}" height="{h}" fill="{BG}"/>{body}</svg>\n')


def corners(x, y, w, h, s=22, t=3):
    p = []
    for cx, cy, dx, dy in [(x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)]:
        p.append(f'<path d="M{cx} {cy + dy * s}V{cy}H{cx + dx * s}" fill="none" stroke="{ACC}" stroke-width="{t}"/>')
    return "".join(p)


def frame(w, h, pad=20):
    return (f'<rect x="{pad}" y="{pad}" width="{w - 2 * pad}" height="{h - 2 * pad}" fill="none" stroke="{LINE}" stroke-dasharray="4 5"/>'
            + corners(pad - 6, pad - 6, w - 2 * pad + 12, h - 2 * pad + 12))


def win_bar(x, y, w, label, right=""):
    sq = "".join(f'<rect x="{x + w - 24 - i * 16}" y="{y + 12}" width="10" height="10" fill="none" stroke="{BG}"/>' for i in range(3))
    r = f'<text x="{x + w - 76}" y="{y + 22}" text-anchor="end" class="mono" font-size="13" fill="{BG}">{esc(right)}</text>' if right else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="34" fill="{ACC}"/>'
            f'<text x="{x + 14}" y="{y + 23}" class="px" font-size="16" fill="{BG}">{esc(label)}</text>' + sq + r)


# ───────────────────────────── banner ─────────────────────────────
def header():
    W, H = 1200, 470
    lines = ["OFFENSIVE", "SECURITY", "ENGINEER"]
    t0, step = 0.4, 0.06
    out, k = [], 0
    for li, word in enumerate(lines):
        cls = "acc" if li == 2 else "fg"
        spans = ""
        for ch in word:
            spans += f'<tspan class="ch" style="animation-delay:{t0 + k * step:.2f}s">{ch}</tspan>'
            k += 1
        if li == 2:
            spans += f'<tspan class="caret">_</tspan>'
        out.append(f'<text x="58" y="{148 + li * 70}" class="px {cls}" font-size="66" letter-spacing="2">{spans}</text>')
    typed = t0 + k * step

    stats = [("7+", "years in offsec"), ("100+", "pentest projects"), ("3000+", "pirate sources found"), ("5", "certifications")]
    st = ""
    for i, (v, l) in enumerate(stats):
        x = 58 + i * 200
        st += (f'<g class="in" style="animation-delay:{typed + 0.15 * i:.2f}s">'
               f'<text x="{x}" y="398" class="px acc" font-size="34">{v}</text>'
               f'<text x="{x}" y="424" class="mono mut" font-size="13">{esc(l)}</text></g>')

    # ojo
    S, ex, ey = 18, 850, 128
    outline, iris = [], []
    for y, row in enumerate(EYE):
        for x, c in enumerate(row):
            if c == "G":
                outline.append(f'<rect x="{x}" y="{y}" width="1" height="1"/>')
            elif c in "id":
                iris.append(f'<rect x="{x}" y="{y}" width="1" height="1" fill="{ACC if c == "i" else ACC_DIM}"/>')
    eye = (f'<g transform="translate({ex},{ey - 3 * S}) scale({S})" shape-rendering="crispEdges">'
           f'<g class="blink"><g fill="{ACC}">{"".join(outline)}</g><g class="look">{"".join(iris)}</g></g></g>')
    bx, by, bw, bh = ex - 18, ey - 30, 16 * S + 36, 9 * S + 60
    tags = (f'<text x="{bx + 8}" y="{by - 12}" class="mono mut" font-size="12" letter-spacing="2">RECON</text>'
            f'<text x="{bx + bw - 8}" y="{by - 12}" text-anchor="end" class="mono mut" font-size="12" letter-spacing="2">WATCHING</text>'
            f'<text x="{bx + 8}" y="{by + bh + 24}" class="mono mut" font-size="12" letter-spacing="2">GOHANCKZ.EXE</text>'
            f'<text x="{bx + bw - 8}" y="{by + bh + 24}" text-anchor="end" class="mono acc" font-size="12" letter-spacing="2"><tspan class="live">●</tspan> LIVE</text>')
    scan = f'<rect class="scan" x="{bx + 4}" y="{by + 4}" width="{bw - 8}" height="2" fill="{ACC}" opacity=".35"/>'
    eye_box = corners(bx, by, bw, bh, 18, 2)

    css = f"""
.blink{{transform-box:fill-box;transform-origin:center;animation:blink 5.5s infinite}}
@keyframes blink{{0%,90%,100%{{transform:scaleY(1)}}93%{{transform:scaleY(.08)}}96%{{transform:scaleY(1)}}}}
.look{{animation:look 8s infinite steps(1,end)}}
@keyframes look{{0%{{transform:translate(0,0)}}18%{{transform:translate(-2px,0)}}36%{{transform:translate(-2px,-1px)}}48%{{transform:translate(0,0)}}66%{{transform:translate(2px,0)}}82%{{transform:translate(2px,1px)}}92%{{transform:translate(0,0)}}}}
.scan{{animation:scan 3.2s linear infinite}}
@keyframes scan{{from{{transform:translateY(0)}}to{{transform:translateY({bh - 10}px)}}}}
.ch{{fill-opacity:0;animation:on 0s forwards}}
@keyframes on{{to{{fill-opacity:1}}}}
.live,.caret{{animation:pulse 1.1s steps(2,start) infinite}}
@keyframes pulse{{to{{visibility:hidden}}}}
.in{{opacity:0;animation:in .6s ease forwards}}
@keyframes in{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
"""
    body = (frame(W, H)
            + f'<text x="58" y="66" class="mono mut" font-size="14" letter-spacing="3"><tspan class="acc">●</tspan> IVÁN GONZÁLEZ / GOHANCKZ · SANTIAGO, CHILE</text>'
            + "".join(out)
            + f'<text x="60" y="324" class="mono mut in" font-size="17" style="animation-delay:{typed:.2f}s">Security Researcher · Bug Bounty Hunter · Red Team</text>'
            + f'<line x1="58" x2="{W - 58}" y1="350" y2="350" stroke="{LINE}" stroke-dasharray="4 5"/>'
            + st + eye_box + tags + eye + scan)
    return svg(W, H, body, css, "Iván González — Offensive Security Engineer")


# ─────────────────────────── proyectos ────────────────────────────
def project_card(name, url, desc, tags):
    W, H = 600, 230
    lines = textwrap.wrap(desc, 56)[:3]
    d = "".join(f'<text x="28" y="{122 + i * 24}" class="mono mut" font-size="15">{esc(l)}</text>' for i, l in enumerate(lines))
    cx, chips = 28, ""
    for t in tags:
        w = len(t) * 8.4 + 22
        chips += (f'<rect x="{cx}" y="{H - 44}" width="{w:.0f}" height="24" fill="none" stroke="{LINE}"/>'
                  f'<text x="{cx + 11}" y="{H - 27}" class="mono mut" font-size="13">{esc(t)}</text>')
        cx += w + 8
    host = re.sub(r"^https?://(www\.)?", "", url).rstrip("/")
    body = (f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" fill="none" stroke="{LINE}"/>'
            + win_bar(0, 0, W, name.upper().replace(" ", "_") + ".EXE")
            + f'<text x="28" y="86" class="px fg" font-size="30">{esc(name)}</text>'
            + d + chips
            + f'<text x="{W - 28}" y="{H - 27}" text-anchor="end" class="mono acc" font-size="13">{esc(host)} ↗</text>'
            + f'<rect class="cur" x="{W - 30}" y="64" width="12" height="22" fill="{ACC}"/>')
    css = ".cur{animation:pulse 1.1s steps(2,start) infinite}@keyframes pulse{to{visibility:hidden}}"
    return svg(W, H, body, css, f"{name} — {desc}")


# ─────────────────────────── indicadores ──────────────────────────
def get(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": "gohanckz-profile-readme", "Accept": "application/vnd.github+json"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read().decode()
    return data if raw else json.loads(data)


def fetch():
    user = get(f"https://api.github.com/users/{USER}")
    repos = []
    for page in range(1, 5):
        chunk = get(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&page={page}")
        repos += chunk
        if len(chunk) < 100:
            break
    own = [r for r in repos if not r["fork"]]
    year = dt.date.today().year

    page = get(f"https://github.com/users/{USER}/contributions", raw=True)
    days = {}
    for m in re.finditer(r'data-date="(\d{4}-\d\d-\d\d)"\s+id="([^"]+)"\s+data-level="(\d)"', page):
        days[m.group(2)] = [m.group(1), int(m.group(3)), 0]
    for m in re.finditer(r'<tool-tip[^>]*for="([^"]+)"[^>]*>\s*([\d,]+|No) contribution', page):
        if m.group(1) in days and m.group(2) != "No":
            days[m.group(1)][2] = int(m.group(2).replace(",", ""))
    cal = sorted((d, lvl, n) for d, lvl, n in days.values())
    total = re.search(r"([\d,]+)\s+contributions?\s+in the last year", page)
    total = int(total.group(1).replace(",", "")) if total else sum(n for _, _, n in cal)

    langs = defaultdict(int)
    for r in own:
        if r["language"]:
            langs[r["language"]] += 1
    return dict(repos=len(own), stars=sum(r["stargazers_count"] for r in own), followers=user["followers"],
                year=year, total=total, cal=cal, langs=langs, since=user["created_at"][:4])


def streaks(cal):
    today = dt.date.today().isoformat()
    longest = cur = run = 0
    for d, lvl, n in cal:
        run = run + 1 if (n or lvl) else 0
        longest = max(longest, run)
    for d, lvl, n in reversed(cal):
        if d == today and not (n or lvl):
            continue  # hoy aún no cuenta
        if n or lvl:
            cur += 1
        else:
            break
    return cur, longest


def stats_card(s):
    W = 1200
    cur, longest = streaks(s["cal"])
    tiles = [(f'{s["total"]:,}', "contribs · last year"), (str(cur), "day streak · now"),
             (str(longest), "longest streak"), (str(s["repos"]), "public repos"),
             (str(s["stars"]), "stars earned"), (str(s["followers"]), "followers")]
    tw = (W - 56 - 5 * 12) / 6
    body = win_bar(0, 0, W, "GITHUB_STATS.EXE", f"since {s['since']} · updated {dt.date.today():%Y-%m-%d}")
    for i, (v, l) in enumerate(tiles):
        x = 28 + i * (tw + 12)
        body += (f'<g class="in" style="animation-delay:{0.1 * i:.1f}s">'
                 f'<rect x="{x:.1f}" y="60" width="{tw:.1f}" height="104" fill="none" stroke="{LINE}"/>'
                 f'<rect x="{x:.1f}" y="60" width="6" height="6" fill="{ACC}"/>'
                 f'<text x="{x + 18:.1f}" y="118" class="px acc" font-size="36">{v}</text>'
                 f'<text x="{x + 18:.1f}" y="146" class="mono mut" font-size="12.5">{esc(l)}</text></g>')

    # mapa de contribuciones
    cal, gx, gy, c, g = s["cal"], 70, 240, 15, 4
    weeks, col = [], []
    if cal:
        first = dt.date.fromisoformat(cal[0][0])
        pad = (first.weekday() + 1) % 7  # la semana empieza en domingo
        col = [None] * pad
    for d in cal:
        col.append(d)
        if len(col) == 7:
            weeks.append(col); col = []
    if col:
        weeks.append(col)
    weeks = weeks[-53:]
    body += f'<text x="28" y="204" class="mono mut" font-size="12" letter-spacing="2">CONTRIBUTION MAP · LAST 12 MONTHS</text>'
    for lbl, r in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        body += f'<text x="{gx - 10}" y="{gy + r * (c + g) + 12}" text-anchor="end" class="mono mut" font-size="11">{lbl}</text>'
    last_m = None
    for wi, wk in enumerate(weeks):
        x = gx + wi * (c + g)
        cells = ""
        for di, d in enumerate(wk):
            if not d:
                continue
            m = d[0][:7]
            if di == 0 and m != last_m and wi < len(weeks) - 2:
                body += f'<text x="{x}" y="{gy - 8}" class="mono mut" font-size="11">{dt.date.fromisoformat(d[0]):%b}</text>'
                last_m = m
            cells += f'<rect x="{x}" y="{gy + di * (c + g)}" width="{c}" height="{c}" fill="{LEVELS[d[1]]}"/>'
        body += f'<g class="col" style="animation-delay:{0.6 + wi * 0.025:.3f}s">{cells}</g>'
    lx = gx + 53 * (c + g) - g
    body += f'<text x="{lx - 5 * (c - 3 + 4) - 10}" y="{gy + 7 * (c + g) + 18}" text-anchor="end" class="mono mut" font-size="11">less</text>'
    for i, colr in enumerate(LEVELS):
        body += f'<rect x="{lx - (5 - i) * (c - 3 + 4)}" y="{gy + 7 * (c + g) + 8}" width="{c - 3}" height="{c - 3}" fill="{colr}"/>'
    body += f'<text x="{lx + 6}" y="{gy + 7 * (c + g) + 18}" class="mono mut" font-size="11">more</text>'

    # lenguajes
    ly = gy + 7 * (c + g) + 62
    body += f'<text x="28" y="{ly}" class="mono mut" font-size="12" letter-spacing="2">LANGUAGES · BY REPOSITORY</text>'
    top = sorted(s["langs"].items(), key=lambda kv: -kv[1])
    tot = sum(v for _, v in top) or 1
    shown = top[:5]
    other = tot - sum(v for _, v in shown)
    if other > 0:
        shown.append(("Other", other))
    shades = [ACC, "#24c04f", "#169138", "#0f6328", "#0b4a1e", "#3a3a3a"]
    bx, bw, x = 28, W - 56, 28.0
    bar, leg, lgx = "", "", 28
    for i, (name, v) in enumerate(shown):
        w = bw * v / tot
        bar += f'<rect x="{x:.1f}" y="{ly + 14}" width="{max(w - 2, 1):.1f}" height="14" fill="{shades[i]}"/>'
        x += w
        lab = f"{name} {100 * v / tot:.1f}%"
        leg += (f'<rect x="{lgx}" y="{ly + 44}" width="10" height="10" fill="{shades[i]}"/>'
                f'<text x="{lgx + 16}" y="{ly + 54}" class="mono mut" font-size="12.5">{esc(lab)}</text>')
        lgx += 16 + len(lab) * 7.6 + 26
    body += f'<g class="grow">{bar}</g>' + leg
    H = ly + 82
    body = f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" fill="none" stroke="{LINE}"/>' + body
    css = f"""
.in{{opacity:0;animation:in .5s ease forwards}}
@keyframes in{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
.col{{opacity:0;animation:col .25s ease forwards}}
@keyframes col{{to{{opacity:1}}}}
.grow{{transform-box:fill-box;transform-origin:left;transform:scaleX(0);animation:grow 1.2s 1.4s cubic-bezier(.2,.8,.2,1) forwards}}
@keyframes grow{{to{{transform:scaleX(1)}}}}
"""
    return svg(W, H, body, css, f"GitHub stats for {USER}: {s['total']} contributions in the last year")


def write(path, data):
    path = os.path.join(ASSETS, path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(data)
    print("wrote", os.path.relpath(path, ROOT), f"{len(data) // 1024} KB")


if __name__ == "__main__":
    write("header.svg", header())
    for p in PROJECTS:
        write(f"projects/{re.sub(r'[^a-z0-9]+', '-', p[0].lower()).strip('-')}.svg", project_card(*p))
    if "--static" not in sys.argv:
        write("stats.svg", stats_card(fetch()))
