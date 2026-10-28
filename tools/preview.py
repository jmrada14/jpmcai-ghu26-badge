"""Render the badge app off-device with a rough stand-in for the 2026 firmware.

    pip install pillow
    python tools/preview.py [out_dir]

This only mimics the drawing calls the app uses, with Pillow's default font in
place of the badge's pixel fonts, so spacing is approximate. It is for
catching mistakes and making README screenshots, not a real simulator; for
that use the Badge Simulator in badger/home.
"""

import os
import sys
import types

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.abspath(os.path.join(HERE, "..", "badge", "apps", "jpm_payments_ai"))
W, H = 320, 240


class Vec2:
    def __init__(self, x, y):
        self.x, self.y = x, y


class Rect:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h


class Shape:
    def __init__(self, kind, *args):
        self.kind, self.args, self.width = kind, args, None
        self.transform = None

    def stroke(self, width):
        self.width = width
        return self


def _xy(args):
    if isinstance(args[0], Vec2):
        return (args[0].x, args[0].y) + tuple(args[1:])
    return args


shape = types.SimpleNamespace(
    circle=lambda *a: Shape("circle", *_xy(a)),
    rectangle=lambda *a: Shape("rect", *a),
    rounded_rectangle=lambda *a: Shape("rrect", *a),
    line=lambda a, b, w=1: Shape("line", a.x, a.y, b.x, b.y, w),
)


class Color(tuple):
    pass


color = types.SimpleNamespace(rgb=lambda r, g, b, a=255: Color((r, g, b, a)))


class Img:
    def __init__(self, pil):
        self.pil = pil.convert("RGBA")
        self.width, self.height = self.pil.size


class Screen:
    width, height = W, H

    def __init__(self):
        self.img = Image.new("RGB", (W, H), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.img, "RGBA")
        self.pen = (255, 255, 255, 255)
        self.font = None
        self.antialias = 0
        self.clip = Rect(0, 0, W, H)

    def rectangle(self, x, y=None, w=None, h=None):
        if isinstance(x, Rect):
            x, y, w, h = x.x, x.y, x.w, x.h
        if w > 0 and h > 0:
            self.draw.rectangle((x, y, x + w - 1, y + h - 1), fill=self.pen)

    def line(self, x0, y0, x1, y1):
        self.draw.line((x0, y0, x1, y1), fill=self.pen)

    def shape(self, s):
        d, a = self.draw, s.args
        if s.kind == "circle":
            x, y, r = a
            box = (x - r, y - r, x + r, y + r)
            if s.width:
                d.ellipse(box, outline=self.pen, width=max(1, round(s.width)))
            else:
                d.ellipse(box, fill=self.pen)
        elif s.kind == "rect":
            x, y, w, h = a
            d.rectangle((x, y, x + w, y + h), fill=None if s.width else self.pen,
                        outline=self.pen if s.width else None)
        elif s.kind == "rrect":
            x, y, w, h, r = a
            d.rounded_rectangle((x, y, x + w, y + h), r, fill=self.pen)
        elif s.kind == "line":
            x0, y0, x1, y1, w = a
            d.line((x0, y0, x1, y1), fill=self.pen, width=max(1, round(w)))

    def text(self, text, x, y, *_):
        self.draw.text((x, y), text, font=self.font, fill=self.pen)

    def measure_text(self, text, **_):
        box = self.draw.textbbox((0, 0), text, font=self.font)
        return box[2], self.font.size

    def blit(self, img, at):
        self.img.paste(img.pil, (int(at.x), int(at.y)), img.pil)


class Badge:
    def __init__(self):
        self.ticks, self.ticks_delta = 0, 0
        self.presses = set()

    def mode(self, *_):
        pass

    def pressed(self, button):
        return button in self.presses


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "docs")
    os.makedirs(out, exist_ok=True)

    screen = Screen()
    badge = Badge()
    holder = {}
    fonts = types.SimpleNamespace(
        sins=ImageFont.load_default(10),
        futile=ImageFont.load_default(13),
        bacteria=ImageFont.load_default(12),
    )
    image = types.SimpleNamespace(
        X2=2, OFF=0, load=lambda path: Img(Image.open(os.path.join(APP, path))))
    env = {
        "__name__": "__main__", "badge": badge, "screen": screen, "image": image,
        "font": fonts, "color": color, "shape": shape, "vec2": Vec2, "rect": Rect,
        "run": lambda fn: holder.setdefault("update", fn),
        "HIRES": 1, "VSYNC": 2,
        "BUTTON_UP": "up", "BUTTON_DOWN": "down", "BUTTON_LEFT": "left",
        "BUTTON_RIGHT": "right", "BUTTON_SELECT": "select",
    }
    cwd = os.getcwd()
    os.chdir(APP)
    source = open("__init__.py").read()
    # the firmware's app paths do not exist here; the app falls back to cwd
    exec(compile(source.replace('os.chdir(APP_DIR)', 'pass'), "__init__.py", "exec"), env)
    os.chdir(cwd)

    update = holder["update"]
    step = 33

    def tick(presses=()):
        badge.ticks += step
        badge.ticks_delta = step
        badge.presses = set(presses)
        os.chdir(APP)
        update()
        os.chdir(cwd)

    # warm up so payments are in flight, then capture each page and an animation
    for _ in range(150):
        tick()
    gif = []
    shots = {0: "globe", 1: "about", 2: "scan"}
    for page in range(3):
        if page:
            tick(["right"])
        if page == 0:
            tick(["select"])
        for n in range(120):
            tick()
            if n % 3 == 0:
                gif.append(screen.img.convert("RGB").resize((W * 2, H * 2), Image.NEAREST))
            if n == 60:
                screen.img.convert("RGB").resize((W * 2, H * 2), Image.NEAREST).save(
                    os.path.join(out, "screenshot-%s.png" % shots[page]))
    gif[0].save(os.path.join(out, "preview.gif"), save_all=True, append_images=gif[1:],
                duration=step * 3, loop=0, optimize=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
