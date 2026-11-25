#!/usr/bin/env python3
"""Generates the brand OG/share image (1200x630) -> static/assets/og-image.{png,jpg,webp}. usage: python3 og.py [N_SOUNDS]"""
import sys, os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(HERE, 'static', 'assets')
N = sys.argv[1] if len(sys.argv) > 1 else '500+'
W, H = 1200, 630; BG = (10, 10, 15); LIME = (200, 255, 46); VIOLET = (123, 92, 255); INK = (241, 241, 245); MUTED = (173, 173, 192)
def font(sz, wt=700):
    f = ImageFont.truetype(os.path.join(A, 'space-grotesk.woff2'), sz)
    try: f.set_variation_by_axes([wt])
    except Exception: pass
    return f
MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
img = Image.new('RGB', (W, H), BG)
# glows
g = Image.new('RGB', (W, H), BG); gd = ImageDraw.Draw(g)
gd.ellipse((700, -380, 1500, 360), fill=(70, 50, 150)); gd.ellipse((-300, 420, 400, 900), fill=(40, 55, 12))
img = Image.blend(img, g.filter(ImageFilter.GaussianBlur(160)), 0.85)
d = ImageDraw.Draw(img)
# logo mark
cx, cy, r = 110, 110, 42
d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=LIME)
for x, h in ((-22, 0.01), (-13, 21), (-3, 39), (6, 26), (15, 13), (23, 3)):
    if h > 1: d.rounded_rectangle((cx+x-3, cy-h/2*1.05, cx+x+3, cy+h/2*1.05), 3, fill=BG)
f_wm = font(40); d.text((172, 88), 'FREE', font=f_wm, fill=INK); wx = 172 + d.textlength('FREE ', font=f_wm)
d.text((wx, 88), 'SFX', font=f_wm, fill=LIME); d.text((wx + d.textlength('SFX  ', font=f_wm), 100), 'DOWNLOAD', font=ImageFont.truetype(MONO, 22), fill=MUTED)
# headline
f1 = font(92); y = 200
d.text((70, y), 'Free Sound Effects', font=f1, fill=INK)
tw = d.textlength('Download', font=f1); d.rounded_rectangle((62, y+104, 62+tw+22, y+104+104), 14, fill=LIME)
d.text((73, y+104), 'Download', font=f1, fill=BG)
d.text((70, y+232), f'{N} CC0 SFX  ·  MP3 + WAV  ·  no sign-up', font=ImageFont.truetype(MONO, 28), fill=MUTED)
# waveform strip
rnd = random.Random(7); n = 96; step = W / n; base = 560
for i in range(n):
    env = 0.25 + 0.75*abs(math.sin(i/n*math.pi*2.3))*(0.55+0.45*math.sin(i*0.37)); hh = max(6, min(110, (env*0.8 + rnd.random()*0.35)*95))
    x = i*step + step/2; col = LIME if i < n*0.38 else (70, 70, 92)
    d.rounded_rectangle((x-2.5, base-hh/2, x+2.5, base+hh/2), 2, fill=col)
px = int(n*0.38*step); d.line((px, base-62, px, base+62), fill=INK, width=2)
img.save(os.path.join(A, 'og-image.png'), optimize=True)
img.save(os.path.join(A, 'og-image.jpg'), quality=86, optimize=True, progressive=True)
img.save(os.path.join(A, 'og-image.webp'), quality=85, method=6)
print({f: os.path.getsize(os.path.join(A, f)) for f in ('og-image.png', 'og-image.jpg', 'og-image.webp')})
