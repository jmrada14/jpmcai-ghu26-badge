"""
J.P. Morgan Payments AI: a spinning globe of payments for the Universe badge.

Payments arc between the world's financial hubs on a dotted globe while a QR
code points at https://github.com/jpmorgan-payments/ai, the toolkit that gives
GitHub Copilot and other agents working knowledge of the J.P. Morgan Payments
APIs.

Controls:
* Left and right = Globe, About and Scan pages
* Up and down = Spin the globe faster or slower
* Select = A burst of payments out of one hub
"""

import math
import os
import random
import sys

APP_DIRS = (
    "/system/apps/jpm_payments_ai",
    "/apps/jpm_payments_ai",
    "/jpm_payments_ai",
)

APP_DIR = APP_DIRS[0]
for app_dir in APP_DIRS:
    try:
        os.stat(app_dir)
        APP_DIR = app_dir
        break
    except OSError:
        pass

os.chdir(APP_DIR)
sys.path.insert(0, APP_DIR)

badge.mode(HIRES | VSYNC)
screen.antialias = image.X2

WIDTH = screen.width
HEIGHT = screen.height

REPO_URL = "github.com/jpmorgan-payments/ai"

DESCRIPTION = (
    "J.P. Morgan Payments AI: one-stop AI toolkit for building, integrating "
    "and scaling AI-powered products with J.P. Morgan Payments APIs.",
    "Gives GitHub Copilot, Claude Code, Cursor and other agents working "
    "knowledge of onboarding, OAuth and API integration.",
    "Agent Skills for Checkout and Online Payments, plus an MCP server for "
    "the Payments Developer Portal docs.",
    "Install: npx skills add jpmorgan-payments/ai",
)

# palette: deep navy night, cool land, gold money
SPACE = color.rgb(4, 8, 22)
OCEAN = color.rgb(9, 20, 48)
RIM = color.rgb(70, 170, 255, 70)
RIM_SOFT = color.rgb(70, 170, 255, 26)
LAND_FRONT = color.rgb(120, 210, 255)
LAND_MID = color.rgb(60, 140, 210)
LAND_BACK = color.rgb(34, 78, 140)
LAND_DIM = color.rgb(40, 90, 150, 120)
GOLD = color.rgb(255, 196, 64)
GOLD_SOFT = color.rgb(255, 196, 64, 70)
GOLD_GHOST = color.rgb(255, 196, 64, 34)
PACKET = color.rgb(255, 244, 200)
CYAN = color.rgb(90, 230, 255)
WHITE = color.rgb(244, 247, 252)
TEXT = color.rgb(214, 224, 240)
MUTED = color.rgb(130, 146, 176)
PANEL = color.rgb(12, 22, 50, 220)
BAND = color.rgb(16, 30, 66)
STAR = (color.rgb(80, 96, 130), color.rgb(150, 170, 210), color.rgb(230, 238, 255))

small_font = font.sins
head_font = font.futile
big_font = font.bacteria

# The world's payment hubs: code, latitude, longitude, currency.
HUBS = (
    ("NYC", 40.71, -74.01, "USD"),
    ("CHI", 41.88, -87.63, "USD"),
    ("SFO", 37.77, -122.42, "USD"),
    ("TOR", 43.65, -79.38, "CAD"),
    ("MEX", 19.43, -99.13, "MXN"),
    ("GRU", -23.55, -46.63, "BRL"),
    ("LDN", 51.51, -0.13, "GBP"),
    ("PAR", 48.86, 2.35, "EUR"),
    ("FRA", 50.11, 8.68, "EUR"),
    ("JNB", -26.20, 28.05, "ZAR"),
    ("DXB", 25.20, 55.27, "AED"),
    ("BOM", 19.08, 72.88, "INR"),
    ("SGP", 1.35, 103.82, "SGD"),
    ("HKG", 22.32, 114.17, "HKD"),
    ("TYO", 35.68, 139.69, "JPY"),
    ("SYD", -33.87, 151.21, "AUD"),
)
RAILS = ("RTP", "SWIFT", "ACH", "WIRE", "FX", "CARD", "SEPA")


def unit(lat, lon):
    """A point on the unit sphere, with longitude 0 facing the viewer."""
    la, lo = math.radians(lat), math.radians(lon)
    c = math.cos(la)
    return (c * math.sin(lo), math.sin(la), c * math.cos(lo))


def load_land():
    """The dots that make up the continents, as flat x, y, z lists.

    tools/build_assets.py spreads them evenly over the land and packs each one
    as a byte of latitude and a byte of longitude.
    """
    with open("assets/land.bin", "rb") as handle:
        packed = handle.read()
    xs, ys, zs = [], [], []
    for i in range(0, len(packed), 2):
        x, y, z = unit(packed[i] - 90, packed[i + 1] * 360 / 255 - 180)
        xs.append(x)
        ys.append(y)
        zs.append(z)
    return xs, ys, zs


LAND_X, LAND_Y, LAND_Z = load_land()
HUB_XYZ = [unit(lat, lon) for _, lat, lon, _ in HUBS]

qr_small = image.load("assets/qr_small.png")
qr_large = image.load("assets/qr_large.png")

TILT = math.radians(20)       # the north pole leans toward the viewer
COS_T, SIN_T = math.cos(TILT), math.sin(TILT)
SPIN_SPEEDS = (0.0, 0.08, 0.18, 0.35, 0.7)   # radians a second
spin_index = 2
spin = 0.6                    # start with the Atlantic in view

# the view the globe is drawn into, set by each page before drawing
view_cx, view_cy, view_r = 0.0, 0.0, 1.0
cos_s, sin_s = 1.0, 0.0


def set_view(cx, cy, r):
    global view_cx, view_cy, view_r, cos_s, sin_s
    view_cx, view_cy, view_r = cx, cy, r
    cos_s, sin_s = math.cos(spin), math.sin(spin)


def project(x, y, z):
    """A world point as screen x, y and depth (positive faces the viewer)."""
    x1 = x * cos_s + z * sin_s
    z1 = z * cos_s - x * sin_s
    y2 = y * COS_T - z1 * SIN_T
    z2 = z1 * COS_T + y * SIN_T
    return view_cx + view_r * x1, view_cy - view_r * y2, z2


def seen(x, y, z):
    """Whether a point at or above the surface is in front of the globe."""
    sx, sy, depth = project(x, y, z)
    if depth > 0:
        return sx, sy, True
    dx, dy = sx - view_cx, sy - view_cy
    return sx, sy, dx * dx + dy * dy > view_r * view_r


# ---------------------------------------------------------------- stars

random.seed(2026)
STARS = [(random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1),
          random.random() * 6.28, 0.6 + random.random() * 2.0) for _ in range(70)]


def draw_stars():
    t = badge.ticks / 1000
    for x, y, phase, rate in STARS:
        level = math.sin(t * rate + phase)
        screen.pen = STAR[0 if level < 0 else (1 if level < 0.7 else 2)]
        screen.rectangle(x, y, 1, 1)


# ---------------------------------------------------------------- globe


def draw_globe(dim=False):
    cx, cy, r = view_cx, view_cy, view_r
    screen.pen = RIM_SOFT
    screen.shape(shape.circle(cx, cy, r + 6))
    screen.pen = OCEAN
    screen.shape(shape.circle(cx, cy, r))
    screen.pen = RIM
    screen.shape(shape.circle(cx, cy, r).stroke(1.5))

    # inlined projection: this loop runs for every land dot every frame
    cs, ss, ct, st = cos_s, sin_s, COS_T, SIN_T
    rect_ = screen.rectangle
    xs, ys, zs = LAND_X, LAND_Y, LAND_Z
    front, mid, back = (LAND_DIM,) * 3 if dim else (LAND_FRONT, LAND_MID, LAND_BACK)
    for i in range(len(xs)):
        x, y, z = xs[i], ys[i], zs[i]
        z1 = z * cs - x * ss
        depth = z1 * ct + y * st
        if depth <= 0.05:
            continue
        if depth > 0.62:
            screen.pen = front
        elif depth > 0.3:
            screen.pen = mid
        else:
            screen.pen = back
        rect_(int(cx + r * (x * cs + z * ss)) - 1, int(cy - r * (y * ct - z1 * st)) - 1, 2, 2)


def draw_hubs():
    pulse = 0.5 + 0.5 * math.sin(badge.ticks / 300)
    for x, y, z in HUB_XYZ:
        sx, sy, depth = project(x, y, z)
        if depth <= 0.08:
            continue
        screen.pen = GOLD_SOFT
        screen.shape(shape.circle(sx, sy, 3 + 2.5 * pulse))
        screen.pen = GOLD
        screen.shape(shape.circle(sx, sy, 1.6))


# ---------------------------------------------------------------- payments

ARC_STEPS = 16
TRAIL = 6                     # how many arc steps the glowing tail covers
TARGET_FLOWS = 7              # payments in the air at once
RIPPLE_MS = 800

flows = []                    # [arc points, start, duration, src, dst, amount, rail]
ripples = []                  # [hub index, start]
settled = 0
volume = 0.0
next_spawn = 0


def arc_points(a, b):
    """Points along the great circle from a to b, lifted off the surface.

    The lift peaks halfway and grows with distance, so long hauls loop high
    over the globe and short hops skim it.
    """
    dot = max(-1.0, min(1.0, a[0] * b[0] + a[1] * b[1] + a[2] * b[2]))
    omega = math.acos(dot)
    sin_o = math.sin(omega) or 1e-6
    lift = 0.06 + 0.32 * omega / math.pi
    points = []
    for step in range(ARC_STEPS + 1):
        f = step / ARC_STEPS
        wa = math.sin((1 - f) * omega) / sin_o
        wb = math.sin(f * omega) / sin_o
        h = 1 + lift * math.sin(math.pi * f)
        points.append(((a[0] * wa + b[0] * wb) * h,
                       (a[1] * wa + b[1] * wb) * h,
                       (a[2] * wa + b[2] * wb) * h))
    return points


def spawn(src=None, delay=0):
    if src is None:
        src = random.randrange(len(HUBS))
    dst = random.randrange(len(HUBS) - 1)
    if dst >= src:
        dst += 1
    amount = 10 ** (4 + random.random() * 3.4)        # $10K to $25M
    duration = 2200 + random.randint(0, 1600)
    flows.append([arc_points(HUB_XYZ[src], HUB_XYZ[dst]), badge.ticks + delay,
                  duration, src, dst, amount, random.choice(RAILS)])


def burst():
    src = random.randrange(len(HUBS))
    for n in range(10):
        spawn(src, n * 90)


def money(amount):
    if amount >= 1e6:
        return "${:.1f}M".format(amount / 1e6)
    return "$" + str(int(amount / 1e3)) + "K"


def update_flows():
    global settled, volume, next_spawn
    now = badge.ticks
    for flow in flows[:]:
        if now - flow[1] >= flow[2]:
            flows.remove(flow)
            ripples.append([flow[4], now])
            settled += 1
            volume += flow[5]
            _, _, _, src, dst, amount, rail = flow
            ticker.feed(HUBS[src][0] + " > " + HUBS[dst][0] + "  " + HUBS[src][3] + "/"
                        + HUBS[dst][3] + "  " + money(amount) + "  " + rail + "  settled")
    for ripple in ripples[:]:
        if now - ripple[1] > RIPPLE_MS:
            ripples.remove(ripple)
    if len(flows) < TARGET_FLOWS and now >= next_spawn:
        spawn()
        next_spawn = now + 250 + random.randint(0, 500)


def draw_flows():
    now = badge.ticks
    for flow in flows:
        points, start, duration = flow[0], flow[1], flow[2]
        t = (now - start) / duration
        if t < 0:
            continue
        s = t * t * (3 - 2 * t)                       # ease in and out
        head = s * ARC_STEPS

        # where each step of the arc lands on screen, and whether it shows
        placed = [seen(*p) for p in points]

        # the route ahead, faint
        screen.pen = GOLD_GHOST
        for i in range(int(head), ARC_STEPS):
            ax, ay, av = placed[i]
            bx, by, bv = placed[i + 1]
            if av and bv:
                screen.line(int(ax), int(ay), int(bx), int(by))

        # the tail, brightening and thickening toward the packet
        first = max(0, int(head) - TRAIL)
        for i in range(first, int(head)):
            ax, ay, av = placed[i]
            bx, by, bv = placed[i + 1]
            if av and bv:
                k = (i - first + 1) / (int(head) - first + 1)
                screen.pen = color.rgb(255, 196, 64, int(60 + 180 * k))
                screen.shape(shape.line(vec2(ax, ay), vec2(bx, by), 0.8 + 1.8 * k))

        # the packet itself, between two steps
        i = min(int(head), ARC_STEPS - 1)
        f = head - i
        ax, ay, av = placed[i]
        bx, by, bv = placed[i + 1]
        if av or bv:
            px, py = ax + (bx - ax) * f, ay + (by - ay) * f
            screen.pen = GOLD_SOFT
            screen.shape(shape.circle(px, py, 5))
            screen.pen = PACKET
            screen.shape(shape.circle(px, py, 2.2))

    # a ring spreads out where each payment lands
    for hub, start in ripples:
        sx, sy, depth = project(*HUB_XYZ[hub])
        if depth <= 0.05:
            continue
        k = (now - start) / RIPPLE_MS
        screen.pen = color.rgb(90, 230, 255, int(220 * (1 - k)))
        screen.shape(shape.circle(sx, sy, 2 + 14 * k).stroke(1.5))


# ---------------------------------------------------------------- ticker


class Ticker:
    """A strip of text crawling along the foot of the screen.

    Pieces join the end as the one before clears the right edge: the repo's
    description in turn with the payments that have just landed.
    """

    SPEED = 42                # pixels a second
    GAP = 28

    def __init__(self, top, height):
        self.top, self.height = top, height
        self.pieces = []      # [text, x, width, pen]
        self.fresh = []
        self.line = 0

    def feed(self, text):
        self.fresh = self.fresh[-3:] + [text]

    def next_piece(self):
        if self.fresh and self.line % 2:
            text, pen = self.fresh.pop(0), CYAN
        else:
            text, pen = DESCRIPTION[(self.line // 2) % len(DESCRIPTION)], TEXT
        self.line += 1
        screen.font = small_font
        return [text, 0, screen.measure_text(text)[0], pen]

    def draw(self):
        step = self.SPEED * badge.ticks_delta / 1000
        for piece in self.pieces:
            piece[1] -= step
        self.pieces = [p for p in self.pieces if p[1] + p[2] > 0]
        end = self.pieces[-1][1] + self.pieces[-1][2] + self.GAP if self.pieces else WIDTH
        while end < WIDTH + 1:
            piece = self.next_piece()
            piece[1] = end
            self.pieces.append(piece)
            end += piece[2] + self.GAP

        screen.pen = BAND
        screen.rectangle(0, self.top, WIDTH, self.height)
        screen.pen = GOLD
        screen.rectangle(0, self.top, WIDTH, 1)
        screen.font = small_font
        _, h = screen.measure_text("Ag")
        y = self.top + (self.height - h) // 2 + 1
        for text, x, w, pen in self.pieces:
            screen.pen = GOLD
            screen.shape(shape.circle(x - self.GAP / 2, self.top + self.height / 2 + 1, 1.5))
            screen.pen = pen
            screen.text(text, int(x), y)


ticker = Ticker(HEIGHT - 20, 20)


# ---------------------------------------------------------------- text


def centred(text, cx, y):
    w, _ = screen.measure_text(text)
    screen.text(text, int(cx - w / 2), y)


def wrap(text, width):
    lines, line = [], ""
    for word in text.split(" "):
        trial = word if not line else line + " " + word
        if screen.measure_text(trial)[0] <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def paragraph(text, x, y, width, gap=2):
    _, h = screen.measure_text("Ag")
    for line in wrap(text, width):
        screen.text(line, x, y)
        y += h + gap
    return y


def header(title):
    screen.pen = PANEL
    screen.rectangle(0, 0, WIDTH, 22)
    screen.pen = GOLD
    screen.rectangle(0, 22, WIDTH, 1)
    screen.font = head_font
    _, h = screen.measure_text("Ag")
    screen.pen = WHITE
    screen.text("J.P. Morgan Payments", 8, (22 - h) // 2)
    w, _ = screen.measure_text("J.P. Morgan Payments ")
    screen.pen = GOLD
    screen.text(title, 8 + w, (22 - h) // 2)
    # which of the pages this is
    for n in range(len(PAGES)):
        screen.pen = GOLD if n == page else MUTED
        screen.shape(shape.circle(WIDTH - 12 - (len(PAGES) - 1 - n) * 9, 11, 2.6 if n == page else 1.8))


def qr_card(qr, x, y, pad):
    screen.pen = GOLD_SOFT
    screen.shape(shape.rounded_rectangle(x - pad - 3, y - pad - 3, qr.width + pad * 2 + 6,
                                         qr.height + pad * 2 + 6, 6))
    screen.pen = WHITE
    screen.shape(shape.rounded_rectangle(x - pad, y - pad, qr.width + pad * 2,
                                         qr.height + pad * 2, 4))
    screen.blit(qr, vec2(x, y))


# ---------------------------------------------------------------- pages


def page_globe():
    set_view(104, 120, 84)
    draw_globe()
    draw_hubs()
    draw_flows()
    header("AI")

    # the scan card down the right
    left = 216
    qr_card(qr_small, left + 1, 30, 2)
    mid = left + 1 + qr_small.width / 2
    screen.font = head_font
    screen.pen = GOLD
    centred("SCAN ME", mid, 136)
    screen.font = small_font
    screen.pen = TEXT
    centred("github.com/", mid, 154)
    centred("jpmorgan-payments/ai", mid, 166)

    screen.pen = MUTED
    centred("payments settled", mid, 186)
    screen.font = big_font
    screen.pen = CYAN
    centred(str(settled) + "  " + money(volume), mid, 198)

    ticker.draw()


def page_about():
    set_view(292, 196, 92)
    draw_globe(dim=True)
    draw_flows()
    header("AI")

    x, width = 10, 220
    screen.font = head_font
    screen.pen = GOLD
    y = paragraph("Build payments with your AI agent", x, 30, width + 60)
    screen.font = small_font
    screen.pen = TEXT
    y = paragraph("One-stop toolkit for building, integrating and scaling AI-powered "
                  "products with J.P. Morgan Payments APIs.", x, y + 4, width)
    y = paragraph(DESCRIPTION[1], x, y + 4, width)

    y += 6
    for name, what in (("Agent Skills", "onboarding, OAuth, Checkout, Online Payments"),
                       ("MCP Server", "search & read the Payments Developer docs")):
        screen.pen = GOLD
        screen.shape(shape.circle(x + 3, y + 5, 2))
        screen.pen = CYAN
        screen.text(name, x + 10, y)
        w, _ = screen.measure_text(name + "  ")
        screen.pen = MUTED
        y = paragraph(what, x + 10 + w, y, width - w)
        y += 2

    # the install line, as a terminal prompt
    y += 4
    screen.pen = PANEL
    screen.shape(shape.rounded_rectangle(x - 2, y - 3, 208, 18, 3))
    screen.pen = GOLD
    screen.text(">", x + 3, y)
    screen.pen = WHITE
    screen.text("npx skills add jpmorgan-payments/ai", x + 13, y)

    ticker.draw()


# the packets that run round the big QR code's frame
ORBITERS = 8


def page_scan():
    header("AI")
    qr = qr_large
    x = (WIDTH - qr.width) // 2
    y = 36
    qr_card(qr, x, y, 3)

    # payments chasing each other round the frame
    edge = 9
    left, top = x - edge, y - edge
    w, h = qr.width + edge * 2, qr.height + edge * 2
    perimeter = 2 * (w + h)

    def along(d):
        d %= perimeter
        if d < w:
            return left + d, top
        d -= w
        if d < h:
            return left + w, top + d
        d -= h
        if d < w:
            return left + w - d, top + h
        return left, top + h - (d - w)

    run_ = badge.ticks / 1000 * 90
    for n in range(ORBITERS):
        head = run_ + n * perimeter / ORBITERS
        for k in range(6, 0, -1):
            px, py = along(head - k * 5)
            screen.pen = color.rgb(255, 196, 64, int(200 * (1 - k / 7)))
            screen.shape(shape.circle(px, py, 1.6))
        px, py = along(head)
        screen.pen = GOLD_SOFT
        screen.shape(shape.circle(px, py, 4.5))
        screen.pen = PACKET
        screen.shape(shape.circle(px, py, 2.2))

    screen.font = small_font
    screen.pen = TEXT
    centred(REPO_URL, WIDTH / 2, top + h + 4)


PAGES = (page_globe, page_about, page_scan)
page = 0


def update():
    global page, spin, spin_index
    if badge.pressed(BUTTON_RIGHT):
        page = (page + 1) % len(PAGES)
    if badge.pressed(BUTTON_LEFT):
        page = (page - 1) % len(PAGES)
    if badge.pressed(BUTTON_UP):
        spin_index = min(len(SPIN_SPEEDS) - 1, spin_index + 1)
    if badge.pressed(BUTTON_DOWN):
        spin_index = max(0, spin_index - 1)
    if badge.pressed(BUTTON_SELECT):
        burst()

    spin += SPIN_SPEEDS[spin_index] * badge.ticks_delta / 1000
    update_flows()

    screen.pen = SPACE
    screen.rectangle(0, 0, WIDTH, HEIGHT)
    draw_stars()
    PAGES[page]()


run(update)
