#!/usr/bin/env python3
"""Static site generator for the free SFX download site.

=== DOMAIN SWITCH: change these two values, rebuild, push ===
SITE_URL  : absolute base used ONLY for canonical tags, og:url, sitemap.xml and robots.txt
BASE_PATH : URL path where the site lives; used ONLY by 404.html (GitHub serves 404 at any depth)
After buying a domain: SITE_URL='https://yourdomain.com', BASE_PATH='/', and set CNAME='yourdomain.com'.
Every other link in the site is RELATIVE, so nothing else needs to change.
"""
import os, json, shutil, zipfile, html, datetime, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from content import CAT_INFO, FAQ, SEO
from sound_text import DESC
from manifest import CATS

SITE_URL  = os.environ.get('SFX_SITE_URL', 'https://mydevspace2.github.io/free-sfx-download')
BASE_PATH = os.environ.get('SFX_BASE_PATH', '/free-sfx-download/')
CNAME     = os.environ.get('SFX_CNAME', '')
SITE_NAME = 'Free SFX Download'
# Category ZIPs live on the separate 'packs' branch of the repo (not published by Pages, keeps the site small).
# build writes them to ZIP_DIR; commit them to the packs branch (see README). Links point to ZIP_URL.
ZIP_URL   = os.environ.get('SFX_ZIP_URL', 'https://github.com/mydevspace2/free-sfx-download/raw/packs/')
UPDATED   = os.environ.get('SFX_UPDATED') or datetime.datetime.now(__import__('zoneinfo').ZoneInfo('Asia/Karachi')).date().isoformat()
ASSET_V   = datetime.datetime.now().strftime('%Y%m%d%H%M')

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(HERE, '..', 'build_audio')
OUT = os.environ.get('SFX_OUT', os.path.join(HERE, '..', 'web'))
ZIP_DIR = os.environ.get('SFX_ZIP_DIR', os.path.join(HERE, '..', 'release_zips'))
SOURCES = json.load(open(os.path.join(HERE, 'sources.json')))

meta = json.load(open(os.path.join(AUDIO, 'meta.json')))
ORDER = list(CATS.keys())
by_cat = {c: [m for m in meta if m['cat'] == c] for c in ORDER}

esc = html.escape
def kb(n):
    return f'{n/1024:.0f} KB' if n < 1024*1024 else f'{n/1048576:.1f} MB'
def dur(s):
    return f'{s:.1f} s' if s < 10 else f'{s:.0f} s'

# ---------------------------------------------------------------- layout
# Brand mark: round "speaker cone" with equalizer bars (distinct from the square logos of the other sites)
ICON = '<svg class="mark" viewBox="0 0 32 32" width="34" height="34" aria-hidden="true"><circle cx="16" cy="16" r="16" fill="#c8ff2e"/><path d="M8 16v0M11.5 12v8M15 8.5v15M18.5 11v10M22 13.5v5M25 15.5v1" stroke="#0a0a0f" stroke-width="2.4" stroke-linecap="round"/></svg>'
DL = ''  # download icon is drawn in CSS (.btn.dl::before) to keep the DOM small

CAT_ICONS = {  # 24x24 stroke icons, one per category
 'whooshes-transitions': '<path d="M3 8h10a3 3 0 1 0-3-3M3 12h15a3 3 0 1 1-3 3M3 16h7"/>',
 'impacts-hits': '<path d="M12 2.5l1.8 5.4 5.3-2.3-2.4 5.1 4.8 1.6-4.8 1.6 2.4 5.1-5.3-2.3L12 22l-1.8-5.3-5.3 2.3 2.4-5.1-4.8-1.6 4.8-1.6-2.4-5.1 5.3 2.3z"/>',
 'booms-explosions': '<circle cx="10.5" cy="14" r="6.5"/><path d="M15.5 9l2.5-2.5M19 3.5v1.5M22 7h-1.5M20.8 4.2l-1 1"/>',
 'risers-sweeps': '<path d="M3 18l6-6 4 4 8-8M15 8h6v6"/>',
 'pops': '<circle cx="9" cy="14" r="5"/><circle cx="17.5" cy="7" r="3"/><path d="M19 15.5v.01M14 21v.01"/>',
 'camera-shutters': '<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
 'ui-clicks': '<path d="M6 3l12 7.5-5.2 1.6L10.5 17z"/><path d="M13 12.5l4.5 6"/>',
 'notifications-alerts': '<path d="M6 16v-5a6 6 0 0 1 12 0v5l2 2H4zM10 21h4"/>',
 'money-coins': '<circle cx="12" cy="12" r="8.5"/><path d="M12 6.5v11M14.5 9.2h-3.2a1.6 1.6 0 0 0 0 3.2h1.4a1.6 1.6 0 0 1 0 3.2H9.5"/>',
 'glitches-sci-fi': '<path d="M3 7h7v4h5V7h6M3 15h4v3h9v-3h5"/>',
 'cartoon-funny': '<circle cx="12" cy="12" r="9"/><path d="M8.5 14.5a4.5 4.5 0 0 0 7 0M9 9.5v.5M15 9.5v.5"/>',
 'typing-paper': '<rect x="2.5" y="6" width="19" height="12" rx="2"/><path d="M6.5 10h.01M10 10h.01M13.5 10h.01M17 10h.01M7.5 14h9"/>',
 'laughs-applause': '<circle cx="12" cy="12" r="9"/><path d="M7.5 13h9a4.5 4.5 0 0 1-9 0zM8 9.5l2-1M16 9.5l-2-1"/>',
 'human-reactions': '<circle cx="12" cy="8" r="4"/><path d="M4.5 21a7.5 7.5 0 0 1 15 0"/>',
 'horror-suspense': '<path d="M5 21V11a7 7 0 0 1 14 0v10l-2.4-2-2.3 2-2.3-2-2.3 2-2.3-2z"/><path d="M9.5 10.5v.5M14.5 10.5v.5"/>',
 'retro-game-8bit': '<rect x="2.5" y="7" width="19" height="11" rx="4"/><path d="M7.5 10.5v4M5.5 12.5h4M15.5 11.5h.01M18 13.5h.01"/>',
 'animals': '<circle cx="6.5" cy="10" r="1.8"/><circle cx="10" cy="6" r="1.8"/><circle cx="14.5" cy="6" r="1.8"/><circle cx="18" cy="10" r="1.8"/><path d="M8 18c0-3.2 1.9-6 4.3-6s4.2 2.8 4.2 6c0 1.8-1.5 2.6-3 2.1a4 4 0 0 0-2.6 0C9.4 20.6 8 19.8 8 18z"/>',
 'sports-games': '<circle cx="12" cy="12" r="9"/><path d="M3.5 9.5c5 1 12 1 17 0M3.5 14.5c5-1 12-1 17 0M12 3c-3 5-3 13 0 18"/>',
 'doors-household': '<path d="M5 21V4a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v17M3 21h18M15 12h.01"/>',
 'vehicles-horns': '<path d="M3 16v-3l2-5h14l2 5v3zM4 16v2.5h3V16M17 16v2.5h3V16"/><path d="M7.5 12.5h.01M16.5 12.5h.01"/>',
 'nature-weather': '<path d="M7 17a4 4 0 0 1-.5-8 5.5 5.5 0 0 1 10.6-1.2A3.8 3.8 0 0 1 17.5 17"/><path d="M12.5 13l-2 4h3l-2 4"/>',
 'guns-weapons': '<circle cx="12" cy="12" r="7.5"/><path d="M12 2v5M12 17v5M2 12h5M17 12h5"/>',
}
def cat_icon(c, size=24):
    return f'<svg class="ci" viewBox="0 0 24 24" width="{size}" height="{size}" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{CAT_ICONS[c]}</svg>'

def _wave_paths(n=96, w=1200, h=150, seed=7):
    import math, random
    r = random.Random(seed); cy = h/2; step = w/n; a = []; b = []
    for i in range(n):
        env = 0.25 + 0.75*abs(math.sin(i/n*math.pi*2.3)) * (0.55 + 0.45*math.sin(i*0.37))
        hh = max(6, min(h-8, (env*0.8 + r.random()*0.35) * h*0.78))
        seg = f'M{i*step+step/2:.0f} {cy-hh/2:.0f}v{hh:.0f}'
        (a if i < n*0.38 else b).append(seg)
    return ''.join(a), ''.join(b)
_WA, _WB = _wave_paths()
WAVE = f'<svg class="wave" viewBox="0 0 1200 150" preserveAspectRatio="none" aria-hidden="true"><path d="{_WB}" stroke="currentColor" stroke-opacity=".22" stroke-width="5" stroke-linecap="round"/><path d="{_WA}" stroke="#c8ff2e" stroke-width="5" stroke-linecap="round"/><path d="M457 4v142" stroke="#fff" stroke-width="2"/></svg>'

def band(inner, cls='', wave=False):
    return f'<section class="band {cls}"><div class="wrap band-in">{inner}</div>{WAVE if wave else ""}</section>'

def crumbs(trail):
    """trail: list of (name, href or None)"""
    parts = [f'<a href="{h}">{esc(n)}</a>' if h is not None else f'<span aria-current="page">{esc(n)}</span>' for n, h in trail]
    return '<nav class="crumbs" aria-label="Breadcrumb">' + '<i aria-hidden="true">/</i>'.join(parts) + '</nav>'

def ad(slot, label):
    # Empty container; filled by assets/ads.js from ads/ads-config.js. Collapses when empty.
    return f'\n<!-- ADSTERRA: {label} (slot "{slot}") - code goes in ads/ads-config.js -->\n<div class="ad-slot" data-ad-slot="{slot}" aria-label="Advertisement"></div>\n'

_CSS = None
def css():
    global _CSS
    if _CSS is None:
        _CSS = open(os.path.join(HERE, 'static', 'assets', 'style.css'), encoding='utf-8').read().strip()
    return _CSS

def page(rel, path, title, desc, body, extra_head='', ld=None, h_type='website', noindex=False):
    """rel = relative prefix to site root ('' or '../'); path = page path from root ('' for home, 'x/' for folders)."""
    canon = f'{SITE_URL}/{path}'
    panel = ''.join(f'<a href="{rel}{c}/">{cat_icon(c, 20)}<span>{esc(CATS[c])}</span><em>{len(by_cat[c])}</em></a>' for c in ORDER)
    foot_cats = ''.join(f'<a href="{rel}{c}/">{esc(CATS[c])}</a>' for c in ORDER)
    lds = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    robots = '<meta name="robots" content="noindex">' if noindex else '<meta name="robots" content="index,follow,max-image-preview:large">'
    font = f"@font-face{{font-family:'Space Grotesk';font-style:normal;font-weight:500 700;font-display:swap;src:url({rel}assets/space-grotesk.woff2) format('woff2')}}"
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{robots}
<link rel="canonical" href="{canon}">
<meta property="og:type" content="{h_type}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{SITE_URL}/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{SITE_NAME} – free CC0 sound effects">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{SITE_URL}/assets/og-image.png">
<meta name="theme-color" content="#0a0a0f">
<link rel="icon" href="{rel}assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{rel}assets/logo-512.png">
<link rel="preload" href="{rel}assets/space-grotesk.woff2" as="font" type="font/woff2" crossorigin>
<script>(function(){{try{{var t=localStorage.getItem('theme');if(t)document.documentElement.dataset.theme=t;}}catch(e){{}}}})();</script>
<style>{font}{css()}</style>
{extra_head}{lds}
<!-- ADSTERRA include point: ads/ads-config.js (slot codes) + assets/ads.js (loader). Nothing else to edit. -->
<script src="{rel}ads/ads-config.js?v={ASSET_V}" defer></script>
<script src="{rel}assets/ads.js?v={ASSET_V}" defer></script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
 <div class="wrap hdr">
  <a class="brand" href="{rel}">{ICON}<span class="wm">FREE<b><span class="sr">&nbsp;</span>SFX</b><small><span class="sr">&nbsp;</span>download</small></span></a>
  <nav class="topnav" aria-label="Main">
   <a href="{rel}#sounds">Search sounds</a>
   <a href="{rel}license/">License</a>
   <a href="{rel}about/">About</a>
  </nav>
  <button class="menu-btn" type="button" aria-expanded="false" aria-controls="navpanel" data-menu><span class="bars" aria-hidden="true"></span><span class="lbl">Categories</span></button>
  <button class="theme-btn" type="button" aria-label="Toggle dark mode" data-theme-toggle>
   <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z" fill="currentColor"/></svg>
  </button>
 </div>
 <div class="navpanel" id="navpanel">
  <div class="wrap">
   <nav class="panelgrid" aria-label="Categories">{panel}</nav>
   <nav class="panellinks" aria-label="Site"><a href="{rel}#sounds">Search sounds</a><a href="{rel}license/">License</a><a href="{rel}about/">About</a><a href="{rel}contact/">Contact</a></nav>
  </div>
 </div>
</header>
<div class="wrap">{ad("header", "header banner (728x90 desktop / 320x50 mobile)")}</div>
<main id="main">
{body}
</main>
<div class="wrap">{ad("footer", "footer banner (728x90 / 300x250)")}</div>
<footer class="site-footer">
 <div class="wrap foot">
  <div class="foot-about">
   <a class="brand" href="{rel}">{ICON}<span class="wm">FREE<b><span class="sr">&nbsp;</span>SFX</b><small><span class="sr">&nbsp;</span>download</small></span></a>
   <p>Free CC0 sound effects for video editors, creators and game developers. MP3 &amp; WAV, one-click download, no sign-up.</p>
  </div>
  <nav class="foot-col" aria-label="Sound categories"><h2>Categories</h2><div class="foot-cats">{foot_cats}</div></nav>
  <nav class="foot-col" aria-label="Site pages"><h2>Site</h2><div class="foot-links">
   <a href="{rel}about/">About</a><a href="{rel}license/">License</a><a href="{rel}privacy/">Privacy Policy</a><a href="{rel}terms/">Terms of Use</a><a href="{rel}contact/">Contact</a>
  </div></nav>
 </div>
 <div class="wrap copy">&copy; {datetime.date.today().year} {SITE_NAME}. Sounds are CC0 / public domain. Last updated {UPDATED}.</div>
</footer>
<script src="{rel}assets/app.js?v={ASSET_V}" defer></script>
</body>
</html>
'''

def card(m, rel, show_cat=True):
    base = f"{rel}sounds/{m['cat']}/{m['file']}"
    tag = f'<span class="tag">{esc(CATS[m["cat"]])}</span>' if show_cat else ''
    return f'''<article class="card" data-name="{esc(m['name'].lower())}" data-cat="{m['cat']}">
 <button class="play" type="button" data-src="{base}.mp3" aria-label="Play preview of {esc(m['name'])}" title="Play preview"></button>
 <div class="ct"><h3><a href="{rel}sound/{m['file']}/">{esc(m['name'])}</a></h3><p class="meta">{tag}{dur(m['dur'])} &middot; {kb(m['mp3'])}</p></div>
 <div class="prog" aria-hidden="true"><span></span></div>
 <div class="actions"><a class="btn dl" href="{base}.mp3" download="{m['file']}.mp3">Download MP3</a><a class="btn ghost" href="{base}.wav" download="{m['file']}.wav" title="WAV 48 kHz 24-bit, {kb(m['wav'])}">WAV</a></div>
</article>'''

def grid(items, rel, show_cat=True, incontent=True):
    out = []
    for i, m in enumerate(items):
        out.append(card(m, rel, show_cat))
        if incontent and i == 11 and len(items) > 16:
            out.append(f'</div>{ad("incontent", "in-content (300x250 / native banner)")}<div class="grid">')
    return '<div class="grid">' + '\n'.join(out) + '</div>'

def faq_html(items):
    return '<div class="faq">' + ''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in items) + '</div>'

def faq_ld(items):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]}

def crumbs_ld(trail):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i+1, "name": n, "item": f"{SITE_URL}/{p}"} for i, (n, p) in enumerate(trail)]}

def write(path, text):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w', encoding='utf-8').write(text)

# ---------------------------------------------------------------- home
POPULAR = ['air-horn-honk', 'cartoon-boing', 'record-scratch', 'ba-dum-tss-joke-drum', 'wrong-answer-buzzer', 'crickets-awkward-silence',
           'censor-beep', 'big-crowd-applause', 'evil-man-laugh', 'surprised-wah-exclamation', 'quick-fart', 'stadium-air-horn-blast',
           'quick-swipe-transition', 'mega-swoosh', 'hard-punch-hit', 'deep-bass-boom', 'thunder-crack-boom', 'shepard-tone-riser',
           'mouth-bubble-pop', 'dslr-shutter-click', 'notification-ping-1', 'computer-data-glitch-1', 'game-over-voice', 'heartbeat-fast']
PER_HOME = 24

def build_index():
    """Small search index for the home page (loaded on first search). Short keys keep it light."""
    by_file = {m['file']: m for m in meta}
    idx = {"cats": {c: CATS[c] for c in ORDER},
           "s": [[m['name'], m['file'], m['cat'], m['dur'], m['mp3'], m['wav'],
                  re.sub(r'[^a-z0-9 ]', ' ', DESC[m['file']].split('. ')[0].lower())] for m in meta]}
    write('search-index.json', json.dumps(idx, ensure_ascii=False, separators=(',', ':')))

def build_home():
    total = len(meta)
    by_file = {m['file']: m for m in meta}
    missing = [p for p in POPULAR if p not in by_file]
    assert not missing, missing
    popular = [by_file[p] for p in POPULAR][:PER_HOME]
    tiles = ''.join(f'<a class="tile" href="{c}/"><span class="ti">{cat_icon(c, 26)}</span><strong>{esc(CATS[c])}</strong><em>View all {len(by_cat[c])} &rarr;</em></a>' for c in ORDER)
    rows = ''.join(f'<tr><td><a href="{c}/">{esc(CATS[c])}</a></td><td>{len(by_cat[c])}</td><td>{esc(CAT_INFO[c]["short"])}</td></tr>' for c in ORDER)
    quick = ''.join(f'<a href="?q={w.replace(" ", "+")}#sounds" data-q="{w}">{w}</a>' for w in ('boing', 'air horn', 'applause', 'whoosh', 'laugh', 'fart', 'scream', 'boom'))
    hero = f'''<p class="eyebrow"><span class="dot" aria-hidden="true"></span>{total} CC0 sounds &middot; MP3 + WAV &middot; no sign-up</p>
 <h1>Free Sound Effects <span class="hl">Download</span></h1>
 <p class="lead">{total} editor-ready sound effects in {len(ORDER)} categories: meme-style funny sounds, laughs, whooshes, impacts, booms, horror, retro 8-bit, animals and more. CC0, free for YouTube, TikTok, Reels and client work. No sign-up, MP3 and WAV.</p>
 <form class="search" role="search" action="./#sounds" method="get">
  <label class="sr" for="q">Search sound effects</label>
  <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2.2"/><path d="M16.5 16.5L21 21" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>
  <input id="q" name="q" type="search" placeholder="Search all {total} sounds&hellip;" autocomplete="off">
  <button type="submit">Search</button>
 </form>
 <p class="quick"><span>Popular:</span>{quick}</p>'''
    body = f'''
{band(hero, 'home', True)}
<div class="wrap">
<section class="sounds" id="sounds" aria-labelledby="sounds-h">
 <div class="sec-head"><h2 id="sounds-h">Popular sound effects</h2><p class="count" aria-live="polite" id="count">{len(popular)} of {total} sounds &middot; search to see all</p></div>
 <div id="pop">{grid(popular, '', True, False)}</div>
 <div id="results" hidden></div>
 <p class="more-res" hidden><button class="btn ghost" type="button" id="more">Show more results</button></p>
 <p class="empty" hidden>No sounds match your search. Try another word, such as &ldquo;hit&rdquo;, &ldquo;laugh&rdquo; or &ldquo;click&rdquo;, or browse a category below.</p>
</section>
{ad("incontent", "in-content (300x250 / native banner)")}
<section class="cats" aria-labelledby="cats-h"><h2 id="cats-h">Browse all {total} sounds by category</h2><div class="tiles">{tiles}</div></section>

<article class="guide prose">
<h2>How to use free sound effects in your videos</h2>
<p>Sound effects (SFX) are the quickest way to make an edit feel professional. Viewers often do not notice a good whoosh or a soft click, but they immediately feel when a transition, a pop-up title or a zoom happens in silence. This page gives you a compact, carefully cleaned library of {total} free sound effects and a short guide to using them well, whether you edit in CapCut on your phone, Premiere Pro, DaVinci Resolve, Final Cut Pro or any other editor.</p>
<p>Every file here is released under <strong>CC0 (public domain)</strong>. That means you can use the sounds in monetised YouTube videos, TikToks, Instagram Reels, Facebook ads, podcasts, games, apps and client projects without paying, without attribution and without asking anyone. The full list of original sources is on our <a href="license/">License page</a>.</p>

<h3>What makes these sound effects &ldquo;editor-ready&rdquo;?</h3>
<p>Many free sound packs are hard to use: the sound starts half a second late, the volume is all over the place, or the file clicks when it ends. Each sound on this site has gone through the same four steps:</p>
<ol>
<li><strong>Trimmed</strong> &ndash; leading silence is removed so the sound hits on the first frame you place it.</li>
<li><strong>Faded</strong> &ndash; a few milliseconds of fade-in and a short fade-out stop clicks and pops at the edges.</li>
<li><strong>Levelled</strong> &ndash; loudness is brought towards about -14 LUFS (the level most streaming platforms use), so sounds sit at a similar volume.</li>
<li><strong>Peak-safe</strong> &ndash; true peaks are capped at -1 dBTP so nothing distorts after export or platform compression.</li>
</ol>

<h3>MP3 or WAV: which should you download?</h3>
<table>
<thead><tr><th>Format</th><th>Quality</th><th>Typical size</th><th>Best for</th></tr></thead>
<tbody>
<tr><td>MP3</td><td>320 kbps, 48 kHz</td><td>10&ndash;300 KB</td><td>CapCut, VN, InShot, quick edits, mobile</td></tr>
<tr><td>WAV</td><td>48 kHz, 24-bit, uncompressed</td><td>10 KB&ndash;2 MB</td><td>Premiere Pro, DaVinci Resolve, Final Cut, further processing</td></tr>
</tbody>
</table>
<p>Both versions come from the same edit, so they sound the same. If you are not sure, take the MP3: it is small, plays everywhere and the difference is inaudible on phone speakers.</p>

<h3>Which sound for which moment?</h3>
<table>
<thead><tr><th>Category</th><th>Sounds</th><th>Use it for</th></tr></thead>
<tbody>{rows}</tbody>
</table>

<h3>Five timing tips that make SFX sound professional</h3>
<ol>
<li><strong>Lead the cut slightly.</strong> Place whooshes so their loudest point lands one or two frames before the visual change. Our ears expect movement to arrive just before the picture.</li>
<li><strong>Layer, don&rsquo;t stack.</strong> A short whoosh followed by an impact on the next frame sounds bigger than one loud sound. Two quiet layers beat one loud layer.</li>
<li><strong>Keep SFX under the voice.</strong> Dialogue should stay on top. Pull sound effects 3&ndash;8 dB below your voice track, and lower the music when a key sound plays.</li>
<li><strong>Vary repeated sounds.</strong> When the same action repeats (subtitle pops, clicks, typing), alternate between two or three similar files from the same category so it does not sound robotic.</li>
<li><strong>Silence is a sound too.</strong> Dropping the music for half a second right before a big impact or boom makes the hit feel twice as strong.</li>
</ol>

<h3>How to add a downloaded sound in popular editors</h3>
<p><strong>CapCut (mobile):</strong> tap <em>Audio &rarr; Extracted / Your sounds &rarr; Import</em>, choose the MP3 from your Downloads folder and drag it under the clip. <strong>Premiere Pro:</strong> drag the WAV or MP3 into the Project panel, then onto an audio track under the cut. <strong>DaVinci Resolve:</strong> import into the Media Pool, then drop it on the timeline; use the clip volume handle to fine-tune. <strong>Final Cut Pro:</strong> drag the file into the browser and connect it to the clip at the playhead. In every editor you can trim the end of a sound or shorten it with a fade if you only need the first part.</p>

<h3>Downloading a whole category</h3>
<p>Each category page has a <strong>Download whole category as ZIP</strong> button. The ZIP contains every sound of that category in both MP3 and WAV, plus a licence file, so you can keep a tidy SFX folder for your projects. Unzip it once and drag the folder into your editor&rsquo;s media library.</p>

<h3>Where do these sounds come from?</h3>
<p>We only use sources that clearly release their work into the public domain: the <a href="https://bigsoundbank.com/" rel="noopener">BigSoundBank</a> library recorded by sound designer Joseph Sardin (most of the real-world recordings here), the CC0 audio and voiceover packs from <a href="https://kenney.nl/" rel="noopener">Kenney.nl</a>, and CC0 uploads on <a href="https://opengameart.org/" rel="noopener">OpenGameArt</a> such as Juhani Junkala&rsquo;s 8-bit collection and qubodup&rsquo;s bamboo swooshes. We do not copy viral meme clips from TV, films or apps, because those are copyrighted; our meme-style sounds are original CC0 recordings that do the same job. We do not use packs whose licence forbids redistribution, and we do not use AI-generated or code-synthesised sounds. The exact source, author and licence of every single file is listed on the <a href="license/">License page</a>.</p>
</article>

<section class="faqsec prose"><h2>Frequently asked questions</h2>{faq_html(FAQ)}</section>
</div>
'''
    ld = [
        {"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": SITE_URL + '/',
         "potentialAction": {"@type": "SearchAction",
                             "target": {"@type": "EntryPoint", "urlTemplate": SITE_URL + '/?q={search_term_string}'},
                             "query-input": "required name=search_term_string"}},
        {"@context": "https://schema.org", "@type": "Organization", "name": SITE_NAME, "url": SITE_URL + '/',
         "logo": SITE_URL + '/assets/logo-512.png',
         "sameAs": ["https://github.com/mydevspace2/free-sfx-download"]},
        faq_ld(FAQ),
    ]
    write('index.html', page('', '', f'Free Sound Effects Download – {total} CC0 SFX (MP3 & WAV)',
          f'Download {total} free sound effects in one click: whooshes, impacts, risers, pops, camera shutters, clicks and more. CC0, no attribution, MP3 & WAV.',
          body, ld=ld))

# ---------------------------------------------------------------- categories
def build_cats():
    for c in ORDER:
        info = dict(CAT_INFO[c]); info.update(SEO[c]); items = by_cat[c]; n = len(items)
        zipname = f'{c}-sfx-pack.zip'
        zsize = os.path.getsize(os.path.join(ZIP_DIR, zipname))
        paras = ''.join(f'<p>{esc(p)}</p>' for p in info['intro'].split('\n')) + f'<p>{esc(info["extra"])}</p>'
        pack = ', '.join(f'<a href="../sound/{m["file"]}/">{esc(m["name"])}</a> ({dur(m["dur"])})' for m in items)
        paras += f'<h3>What is in this {esc(info["noun"])} pack</h3><p>{n} sounds: {pack}. Each one has its own page with a preview player, technical details and the original source.</p>'
        others = ''.join(f'<a href="../{o}/">{cat_icon(o, 18)}{esc(CATS[o])}</a>' for o in ORDER if o != c)
        body = f'''
{band(f'''{crumbs([('Home', '../'), (CATS[c], None)])}
 <div class="cat-head"><span class="ti big">{cat_icon(c, 34)}</span><div>
 <h1>{esc(info['h1'])}</h1>
 <p class="lead">{n} free {esc(info['noun'])} sound effects. CC0 public domain, free for commercial use, no attribution needed. One-click MP3 or WAV download.</p>
 </div></div>
 <a class="btn zip" href="{ZIP_URL}{zipname}" download="{zipname}" rel="nofollow">Download whole category as ZIP <small>{n} sounds &middot; MP3 + WAV &middot; {kb(zsize)}</small></a>''', 'cat', True)}
<div class="wrap">
<section class="sounds" aria-labelledby="sounds-h"><div class="sec-head"><h2 id="sounds-h">All {n} {esc(info['noun'])} sound effects</h2></div>
{grid(items, '../', False, True)}
</section>
<article class="prose catintro"><h2>About these {esc(info['noun'])} sound effects</h2>{paras}
<p>All files are trimmed, faded and levelled (about -14 LUFS, peaks at -1 dBTP). See the <a href="../license/">License page</a> for the original source of each sound.</p></article>
<section class="prose"><h2>More free sound effect categories</h2><div class="morecats">{others}</div></section>
</div>
'''
        ld = [crumbs_ld([('Home', ''), (CATS[c], f'{c}/')]),
              {"@context": "https://schema.org", "@type": "CollectionPage", "name": info['h1'], "url": f'{SITE_URL}/{c}/',
               "description": info['short'], "isPartOf": {"@type": "WebSite", "name": SITE_NAME, "url": SITE_URL + '/'}},
              {"@context": "https://schema.org", "@type": "ItemList", "name": info['h1'], "numberOfItems": n,
               "itemListElement": [{"@type": "ListItem", "position": i+1, "name": f"{m['name']} Sound Effect",
                                    "url": f"{SITE_URL}/sound/{m['file']}/"} for i, m in enumerate(items)]}]
        write(f'{c}/index.html', page('../', f'{c}/', info["title"],
              (lambda a: a if len(a)<=158 else f'{n} free {info["noun"]} sound effects. {info["short"]} CC0, free for commercial use.')(f'{n} free {info["noun"]} sound effects. {info["short"]} CC0, free for commercial use, MP3 & WAV download.'),
              body, ld=ld))

# ---------------------------------------------------------------- sound pages
CC0 = 'https://creativecommons.org/publicdomain/zero/1.0/'
def iso_dur(d):
    return f"PT{d:.2f}".rstrip('0').rstrip('.') + 'S'

def sound_desc(m):
    name, d = m['name'], dur(m['dur'])
    sents = [x.strip() for x in DESC[m['file']].split('. ') if x.strip()]
    use = sents[-1].rstrip('.') + '.'
    for cand in (f"Free {name} sound effect ({d}). {use} CC0, MP3 & WAV download.",
                 f"Free {name} sound effect ({d}). {use}",
                 f"Download the free {name} sound effect ({d}) in MP3 & WAV. CC0 public domain, no attribution needed."):
        if len(cand) <= 158: return cand
    return cand[:155].rsplit(' ', 1)[0] + '…'

def build_sounds():
    for c in ORDER:
        items = by_cat[c]; info = dict(CAT_INFO[c]); info.update(SEO[c])
        zipname = f'{c}-sfx-pack.zip'
        for idx, m in enumerate(items):
            rel = '../../'; slug = m['file']; name = m['name']
            src = SOURCES[slug]
            base = f"{rel}sounds/{c}/{slug}"
            others = items[idx+1:] + items[:idx]
            related = others[:6]
            ch = 'Mono' if m.get('ch', 1) == 1 else 'Stereo'
            sents = DESC[slug]
            body = f'''
{band(f'''{crumbs([('Home', rel), (CATS[c], f'{rel}{c}/'), (name, None)])}
 <h1>{esc(name)} Sound Effect</h1>
 <p class="lead">{esc(sents)}</p>
 <article class="card single" data-name="{esc(name.lower())}" data-cat="{c}">
  <button class="play" type="button" data-src="{base}.mp3" aria-label="Play preview of {esc(name)}" title="Play preview"></button>
  <div class="ct"><p class="meta"><span class="tag">{esc(CATS[c])}</span>{dur(m['dur'])} &middot; MP3 320k &middot; WAV 48k/24-bit</p></div>
  <div class="prog" aria-hidden="true"><span></span></div>
  <div class="actions">
   <a class="btn dl" href="{base}.mp3" download="{slug}.mp3">Download MP3 <small>({kb(m['mp3'])})</small></a>
   <a class="btn ghost dl" href="{base}.wav" download="{slug}.wav">WAV <small>({kb(m['wav'])})</small></a>
  </div>
 </article>''', 'snd')}
<div class="wrap">
<section class="prose sound-info">
 <h2>Sound details</h2>
 <table class="spec-table"><tbody>
  <tr><th scope="row">Duration</th><td>{dur(m['dur'])}</td></tr>
  <tr><th scope="row">Category</th><td><a href="{rel}{c}/">{esc(CATS[c])}</a></td></tr>
  <tr><th scope="row">MP3</th><td>320 kbps, 48 kHz, {ch.lower()}, {kb(m['mp3'])}</td></tr>
  <tr><th scope="row">WAV</th><td>48 kHz, 24-bit, {ch.lower()}, {kb(m['wav'])}</td></tr>
  <tr><th scope="row">Processing</th><td>Silence trimmed, short fades, levelled (about -14 LUFS target), true peak &le; -1 dBTP</td></tr>
  <tr><th scope="row">Licence</th><td><a href="{CC0}" rel="noopener">CC0 1.0</a> &ndash; free for commercial use, no attribution</td></tr>
 </tbody></table>
 <h2>How to use this {esc(name.lower())} sound in video editing</h2>
 <p>Download the MP3 for CapCut, VN, InShot and other phone editors, or the WAV for Premiere Pro, DaVinci Resolve and Final Cut Pro. Drop it on an audio track under the moment it belongs to; the sound starts on the first frame, so it lines up exactly where you place it. Keep it a few decibels below your voice track and trim or fade the end if you only need part of it.</p>
 <h2>Source &amp; licence</h2>
 <p>Original recording: <a href="{esc(src['url'])}" rel="noopener nofollow">{esc(src['title'])}</a> by {esc(src['author'])}, released under CC0 / public domain. This edited version (trimmed, faded and levelled) is also CC0. Credit is optional; see the <a href="{rel}license/">License page</a> for all sources.</p>
 <p><a class="btn ghost dl inline" href="{ZIP_URL}{zipname}" download="{zipname}" rel="nofollow">Download all {len(items)} {esc(info['noun'])} sounds (ZIP)</a></p>
</section>
<section class="related"><h2>Related {esc(info['noun'])} sound effects</h2>
{grid(related, rel, False, False)}
<p class="more"><a href="{rel}{c}/">See all {len(items)} {esc(CATS[c].lower())} sound effects &rarr;</a></p></section>
</div>
'''
            url = f'{SITE_URL}/sound/{slug}/'
            ld = [crumbs_ld([('Home', ''), (CATS[c], f'{c}/'), (name, f'sound/{slug}/')]),
                  {"@context": "https://schema.org", "@type": "AudioObject", "name": f"{name} Sound Effect",
                   "description": DESC[slug], "url": url,
                   "contentUrl": f"{SITE_URL}/sounds/{c}/{slug}.mp3", "encodingFormat": "audio/mpeg",
                   "duration": iso_dur(m['dur']), "contentSize": kb(m['mp3']),
                   "license": CC0, "isAccessibleForFree": True, "genre": CATS[c],
                   "creditText": src['author'], "copyrightNotice": "CC0 1.0 / public domain",
                   "associatedMedia": {"@type": "AudioObject", "contentUrl": f"{SITE_URL}/sounds/{c}/{slug}.wav", "encodingFormat": "audio/wav"},
                   "isBasedOn": src['url']}]
            write(f'sound/{slug}/index.html', page(rel, f'sound/{slug}/', f'{name} Sound Effect – Free MP3 & WAV Download',
                  sound_desc(m), body, ld=ld))

# ---------------------------------------------------------------- static pages
def simple(slug, title, desc, inner):
    m = re.search(r'<h1>(.*?)</h1>', inner, re.S)
    h1 = m.group(0); inner = (inner[:m.start()] + inner[m.end():]).strip()
    body = band(f'{crumbs([("Home", "../"), (title, None)])}{h1}', 'info') + f'<div class="wrap"><article class="prose page">{inner}</article></div>'
    write(f'{slug}/index.html', page('../', f'{slug}/', f'{title} – {SITE_NAME}', desc, body,
          ld=[crumbs_ld([('Home', ''), (title, f'{slug}/')])]))

def build_static():
    total = len(meta)
    simple('about', 'About', f'About {SITE_NAME}: a small, fast library of {total} free CC0 sound effects for video editors and creators.', f'''
<h1>About {SITE_NAME}</h1>
<p>{SITE_NAME} is a small, fast library of free sound effects for video editors, short-form creators, streamers and indie game developers. We focus on the sounds editors actually use every day &mdash; funny and meme-style sounds, laughs and applause, human reactions, whooshes, impacts, booms, risers, pops, glitches, notifications, horror stingers, retro 8-bit effects, animals, horns and sirens, nature ambiences and more &mdash; and make each one ready to drop on a timeline.</p>
<h2>What we do</h2>
<ul><li>Collect sound effects only from sources that release them as <strong>CC0 / public domain</strong>.</li>
<li>Choose realistic, punchy recordings and skip weak, noisy or unusable ones.</li>
<li>Trim leading silence, add short fades and level every file (about -14 LUFS, peaks at -1 dBTP).</li>
<li>Give each sound a clear, searchable name and offer MP3 and WAV with one-click download &mdash; no account, no email, no waiting.</li></ul>
<h2>Who it is for</h2>
<p>YouTubers, TikTok and Reels editors, podcasters, teachers, students, app makers and game developers who need clean sounds they can use commercially without worrying about licences.</p>
<h2>Credits</h2>
<p>The original recordings were made by Joseph Sardin (<a href="https://bigsoundbank.com/" rel="noopener">BigSoundBank</a>), <a href="https://kenney.nl/" rel="noopener">Kenney</a> and CC0 contributors on <a href="https://opengameart.org/" rel="noopener">OpenGameArt</a> (including Juhani Junkala, qubodup, artisticdude and pyranostudios). Thank you for giving your work to the public domain. Full per-file credits are on the <a href="../license/">License page</a>.</p>''')

    rows = ''.join(f'<tr><td>{esc(m["name"])}</td><td>{esc(CATS[m["cat"]])}</td><td><a href="{esc(SOURCES[m["file"]]["url"])}" rel="noopener nofollow">{esc(SOURCES[m["file"]]["title"])}</a></td><td>{esc(SOURCES[m["file"]]["author"])}</td><td>CC0 1.0</td></tr>' for m in meta)
    simple('license', 'License', 'All sound effects on this site are CC0 / public domain: free for personal and commercial use, no attribution required. Full source list.', f'''
<h1>License: CC0 &ndash; free for commercial use</h1>
<p><strong>All {total} sound effects on {SITE_NAME} are released under the <a href="https://creativecommons.org/publicdomain/zero/1.0/" rel="noopener">Creative Commons CC0 1.0 Universal</a> public domain dedication.</strong> Our edited versions (trimmed, faded and loudness-levelled MP3 and WAV files) are also dedicated to the public domain under CC0.</p>
<h2>You can</h2>
<ul><li>Use the sounds in personal and <strong>commercial</strong> projects: monetised YouTube videos, TikTok, Instagram Reels, ads, films, podcasts, games, apps, websites and client work.</li>
<li>Edit, cut, layer, pitch and remix them.</li>
<li>Use them without attribution and without asking permission.</li></ul>
<h2>We kindly ask</h2>
<ul><li>Please link to this site rather than re-uploading the packs as your own sound library.</li>
<li>Credit is optional but appreciated: &ldquo;Sound effects: BigSoundBank.com / Kenney.nl&rdquo;.</li></ul>
<h2>Copyright claims</h2>
<p>BigSoundBank states that its sounds are not registered in YouTube Content ID. If a third party wrongly claims a video that uses one of these sounds, you can dispute the claim and cite the original CC0 source below.</p>
<h2>Original sources (every file)</h2>
<p>Licences: BigSoundBank &mdash; <a href="https://bigsoundbank.com/licenses.html" rel="noopener">CC0 / public domain</a>; Kenney &mdash; CC0 1.0 (License.txt in each pack); OpenGameArt &mdash; items marked CC0.</p>
<div class="tablewrap"><table class="src"><thead><tr><th>Our file</th><th>Category</th><th>Original</th><th>Author</th><th>Licence</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="note">Disclaimer: the sounds are provided &ldquo;as is&rdquo;, without warranty. Do not use a sound in a way that suggests endorsement by its original author.</p>''')

    simple('privacy', 'Privacy Policy', f'Privacy policy of {SITE_NAME}: no accounts, no forms; cookies may be used by advertising partners.', f'''
<h1>Privacy Policy</h1>
<p>Last updated: {UPDATED}</p>
<p>{SITE_NAME} (&ldquo;we&rdquo;, &ldquo;the site&rdquo;) is a static website. We do not ask you to create an account, and we do not collect your name, email address or any other personal details to download sounds.</p>
<h2>Information collected automatically</h2>
<p>Like every website, our hosting provider (GitHub Pages) receives technical data such as your IP address, browser type and the pages requested, in order to deliver the site and protect it from abuse. See the <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement" rel="noopener">GitHub Privacy Statement</a>.</p>
<h2>Local storage</h2>
<p>If you switch between light and dark mode, your choice is saved in your browser&rsquo;s local storage. It never leaves your device.</p>
<h2>Advertising</h2>
<p>We may show ads from third-party advertising networks (such as Adsterra) to keep the site free. These partners may use cookies, web beacons or similar technologies to show ads and measure their performance, and may collect information such as your IP address, device and browser type. Their use of this data is governed by their own privacy policies. You can control cookies in your browser settings, and you can opt out of personalised advertising at <a href="https://www.youronlinechoices.com/" rel="noopener">youronlinechoices.com</a> (EU) or <a href="https://optout.aboutads.info/" rel="noopener">optout.aboutads.info</a> (US).</p>
<h2>Analytics</h2>
<p>We may use privacy-friendly analytics to count page views. If we do, this policy will be updated to name the provider.</p>
<h2>Children</h2>
<p>The site is not directed at children under 13 and we do not knowingly collect information from them.</p>
<h2>Your rights</h2>
<p>Depending on where you live (for example under the GDPR or CCPA) you may have rights to access or delete data about you. Because we do not store personal data ourselves, requests about advertising data should go to the relevant ad partner. For anything else, see our <a href="../contact/">Contact page</a>.</p>
<h2>Changes</h2>
<p>We may update this policy. The date at the top shows the latest version.</p>''')

    simple('terms', 'Terms of Use', f'Terms of use for {SITE_NAME}: free CC0 sound effects provided as is.', f'''
<h1>Terms of Use</h1>
<p>Last updated: {UPDATED}</p>
<p>By using {SITE_NAME} you agree to these terms.</p>
<h2>1. The sounds</h2>
<p>All sound effects are offered under the CC0 1.0 public domain dedication described on our <a href="../license/">License page</a>. You may use them for any purpose, including commercial use.</p>
<h2>2. Fair use of the site</h2>
<p>Please do not hot-link our files from other websites, scrape the site automatically, or re-publish the packs as a competing download library. Link to the relevant page instead.</p>
<h2>3. No warranty</h2>
<p>The site and the sounds are provided &ldquo;as is&rdquo;, without warranties of any kind. We are not liable for any damages arising from their use. You are responsible for checking that your final project complies with the rules of the platforms you publish on.</p>
<h2>4. Third-party links and ads</h2>
<p>The site may contain links and advertisements from third parties. We are not responsible for their content or practices.</p>
<h2>5. Removal requests</h2>
<p>If you believe a file was published by mistake, contact us through the <a href="../contact/">Contact page</a> and we will review it promptly.</p>
<h2>6. Changes</h2>
<p>We may change these terms at any time; the date above shows the current version.</p>''')

    simple('contact', 'Contact', f'Contact {SITE_NAME}: sound requests, removal requests and feedback.', f'''
<h1>Contact</h1>
<p>Have a request for a sound category, found a problem with a file, or want to report something? We read every message.</p>
<ul>
<li><strong>Sound requests &amp; bug reports:</strong> open an issue on our <a href="https://github.com/mydevspace2/free-sfx-download/issues" rel="noopener">GitHub page</a>.</li>
<li><strong>Removal or licence questions:</strong> open an issue with the file name and the reason; we review removal requests within a few days.</li>
</ul>
<p>Please do not send personal or sensitive information.</p>''')

    # 404 uses BASE_PATH absolute links because GitHub serves it at any depth
    b = BASE_PATH
    body404 = band(f'''<h1>Page not found</h1><p class="lead">That page or sound does not exist (any more). Try the home page search, or pick a category:</p>
<p><a class="btn" href="{b}">Go to the home page</a></p><div class="morecats">{''.join(f'<a href="{b}{c}/">{cat_icon(c, 18)}{esc(CATS[c])}</a>' for c in ORDER)}</div>''', 'info nf', True)
    p = page(b, '404.html', f'Page not found – {SITE_NAME}', 'Page not found.', body404, noindex=True)
    write('404.html', p)

# ---------------------------------------------------------------- assets
def build_files():
    # audio
    for c in ORDER:
        os.makedirs(os.path.join(OUT, 'sounds', c), exist_ok=True)
        for m in by_cat[c]:
            for ext in ('mp3', 'wav'):
                shutil.copy2(os.path.join(AUDIO, c, f"{m['file']}.{ext}"), os.path.join(OUT, 'sounds', c, f"{m['file']}.{ext}"))
    # zips
    os.makedirs(ZIP_DIR, exist_ok=True)
    lic = f"""{SITE_NAME} - {{cat}} pack
All sounds: CC0 1.0 Universal (public domain). Free for commercial use, no attribution required.
https://creativecommons.org/publicdomain/zero/1.0/
Original sources and authors: see the License page of the site ({SITE_URL}/license/).
"""
    for c in ORDER:
        zp = os.path.join(ZIP_DIR, f'{c}-sfx-pack.zip')
        with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
            def add(arc, data):  # fixed timestamp -> identical ZIP bytes on every rebuild (no git churn)
                zi = zipfile.ZipInfo(arc, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED
                zi.external_attr = 0o644 << 16; z.writestr(zi, data)
            for m in by_cat[c]:
                add(f"{c}/MP3/{m['file']}.mp3", open(os.path.join(AUDIO, c, f"{m['file']}.mp3"), 'rb').read())
                add(f"{c}/WAV/{m['file']}.wav", open(os.path.join(AUDIO, c, f"{m['file']}.wav"), 'rb').read())
            add(f'{c}/LICENSE.txt', lic.format(cat=CATS[c]))
            # deterministic-ish timestamps not required

def build_seo():
    urls = [''] + [f'{c}/' for c in ORDER] + [f"sound/{m['file']}/" for m in meta] + ['about/', 'license/', 'privacy/', 'terms/', 'contact/']
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(
        f'  <url><loc>{SITE_URL}/{u}</loc><lastmod>{UPDATED}</lastmod></url>\n' for u in urls) + '</urlset>\n'
    write('sitemap.xml', sm)
    write('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n')
    # SOURCES.md: one row per published sound, generated so it never drifts from the site
    rows = ''.join(f"| {i+1} | sounds/{m['cat']}/{m['file']}.mp3 (+ .wav) | {CATS[m['cat']]} | [{SOURCES[m['file']]['title']}]({SOURCES[m['file']]['url']}) | {SOURCES[m['file']]['file']} | {SOURCES[m['file']]['author']} | {SOURCES[m['file']]['license']} |\n" for i, m in enumerate(meta))
    write('SOURCES.md', open(os.path.join(HERE, 'sources_head.md'), encoding='utf-8').read() + '| # | Site file | Category | Original (source page) | Original file | Author | Licence |\n|---|---|---|---|---|---|---|\n' + rows)
    write('.nojekyll', '')
    if CNAME:
        write('CNAME', CNAME + '\n')

def main():
    os.makedirs(OUT, exist_ok=True)
    # copy static assets (css/js/ads/images) from src/static
    for sub in ('assets', 'ads'):
        src = os.path.join(HERE, 'static', sub)
        dst = os.path.join(OUT, sub)
        if sub == 'ads' and os.path.exists(os.path.join(dst, 'ads-config.js')):
            # never overwrite pasted ad codes
            for f in os.listdir(src):
                if f != 'ads-config.js': shutil.copy2(os.path.join(src, f), dst)
            continue
        shutil.copytree(src, dst, dirs_exist_ok=True)
    build_files(); build_index(); build_home(); build_cats(); build_sounds(); build_static(); build_seo()
    print('built', len(meta), 'sounds into', os.path.abspath(OUT))

if __name__ == '__main__':
    main()
