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
UPDATED   = datetime.date.today().isoformat()
ASSET_V   = datetime.datetime.now().strftime('%Y%m%d%H%M')

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(HERE, '..', 'build_audio')
OUT = os.environ.get('SFX_OUT', os.path.join(HERE, '..', 'web'))
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
ICON = '<svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true"><rect width="32" height="32" rx="8" fill="currentColor"/><path d="M6 16h2M10 11v10M14 7v18M18 12v8M22 9v14M26 15v2" stroke="var(--logo-ink)" stroke-width="2.4" stroke-linecap="round"/></svg>'
DL = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M12 3v12m0 0l-5-5m5 5l5-5M5 21h14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>'

def ad(slot, label):
    # Empty container; filled by assets/ads.js from ads/ads-config.js. Collapses when empty.
    return f'\n<!-- ADSTERRA: {label} (slot "{slot}") - code goes in ads/ads-config.js -->\n<div class="ad-slot" data-ad-slot="{slot}" aria-label="Advertisement"></div>\n'

def page(rel, path, title, desc, body, extra_head='', ld=None, h_type='website', noindex=False):
    """rel = relative prefix to site root ('' or '../'); path = page path from root ('' for home, 'x/' for folders)."""
    canon = f'{SITE_URL}/{path}'
    nav = ''.join(f'<a href="{rel}{c}/">{esc(CATS[c])}</a>' for c in ORDER)
    lds = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    robots = '<meta name="robots" content="noindex">' if noindex else '<meta name="robots" content="index,follow,max-image-preview:large">'
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
<meta name="theme-color" content="#0f1115">
<link rel="icon" href="{rel}assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{rel}assets/logo-512.png">
<script>(function(){{try{{var t=localStorage.getItem('theme');if(t)document.documentElement.dataset.theme=t;}}catch(e){{}}}})();</script>
<link rel="stylesheet" href="{rel}assets/style.css?v={ASSET_V}">
{extra_head}{lds}
<!-- ADSTERRA include point: ads/ads-config.js (slot codes) + assets/ads.js (loader). Nothing else to edit. -->
<script src="{rel}ads/ads-config.js?v={ASSET_V}" defer></script>
<script src="{rel}assets/ads.js?v={ASSET_V}" defer></script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
 <div class="wrap hdr">
  <a class="brand" href="{rel}">{ICON}<span>{SITE_NAME}</span></a>
  <button class="theme-btn" type="button" aria-label="Toggle dark mode" data-theme-toggle>
   <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z" fill="currentColor"/></svg>
  </button>
 </div>
 <nav class="wrap catnav" aria-label="Categories">{nav}</nav>
</header>
<div class="wrap">{ad("header", "header banner (728x90 desktop / 320x50 mobile)")}</div>
<main id="main" class="wrap">
{body}
</main>
<div class="wrap">{ad("footer", "footer banner (728x90 / 300x250)")}</div>
<footer class="site-footer">
 <div class="wrap foot">
  <div>
   <a class="brand small" href="{rel}">{ICON}<span>{SITE_NAME}</span></a>
   <p>Free CC0 sound effects for video editors, creators and game developers. MP3 &amp; WAV, one-click download, no sign-up.</p>
  </div>
  <div class="foot-links">
   <a href="{rel}about/">About</a><a href="{rel}license/">License</a><a href="{rel}privacy/">Privacy Policy</a><a href="{rel}terms/">Terms of Use</a><a href="{rel}contact/">Contact</a>
  </div>
 </div>
 <div class="wrap copy">&copy; {datetime.date.today().year} {SITE_NAME}. Sounds are CC0 / public domain. Last updated {UPDATED}.</div>
</footer>
<script src="{rel}assets/app.js?v={ASSET_V}" defer></script>
</body>
</html>
'''

def card(m, rel, show_cat=True):
    base = f"{rel}sounds/{m['cat']}/{m['file']}"
    catlink = f'<span class="tag">{esc(CATS[m["cat"]])}</span>'
    return f'''<article class="card" data-name="{esc(m['name'].lower())}" data-cat="{m['cat']}">
 <h3><a href="{rel}sound/{m['file']}/">{esc(m['name'])}</a></h3>
 {catlink}
 <div class="prog" aria-hidden="true"><span></span></div>
 <dl class="specs"><div><dt>Duration</dt><dd>{dur(m['dur'])}</dd></div><div><dt>Size</dt><dd>{kb(m['mp3'])}</dd></div><div><dt>Format</dt><dd>MP3 320k</dd></div></dl>
 <div class="actions">
  <button class="play" type="button" data-src="{base}.mp3" aria-label="Play preview of {esc(m['name'])}" title="Play preview"><svg class="i-play" viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z" fill="currentColor"/></svg><svg class="i-stop" viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor"/></svg></button>
  <a class="btn" href="{base}.mp3" download="{m['file']}.mp3">{DL}Download MP3</a>
  <a class="btn ghost" href="{base}.wav" download="{m['file']}.wav" title="WAV 48 kHz 24-bit, {kb(m['wav'])}">WAV</a>
 </div>
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
def build_home():
    total = len(meta)
    chips = '<button class="chip active" data-filter="all">All <span>' + str(total) + '</span></button>' + ''.join(
        f'<button class="chip" data-filter="{c}">{esc(CATS[c])} <span>{len(by_cat[c])}</span></button>' for c in ORDER)
    cat_cards = ''.join(f'''<a class="catcard" href="{c}/"><strong>{esc(CATS[c])}</strong><span>{esc(CAT_INFO[c]['short'])}</span><em>{len(by_cat[c])} sounds &rarr;</em></a>''' for c in ORDER)
    rows = ''.join(f'<tr><td><a href="{c}/">{esc(CATS[c])}</a></td><td>{len(by_cat[c])}</td><td>{esc(CAT_INFO[c]["short"])}</td></tr>' for c in ORDER)
    body = f'''
<section class="hero">
 <h1>Free Sound Effects Download</h1>
 <p class="lead">{total} hand-picked, editor-ready sound effects &mdash; whooshes, impacts, risers, pops, camera shutters, clicks, glitches and more. CC0 public domain: free for YouTube, TikTok, Reels, games and client work. One click, no sign-up, MP3 and WAV.</p>
 <div class="search">
  <label class="sr" for="q">Search sound effects</label>
  <input id="q" type="search" placeholder="Search {total} sounds, e.g. whoosh, shutter, coin&hellip;" autocomplete="off">
 </div>
 <div class="chips" role="toolbar" aria-label="Filter by category">{chips}</div>
 <p class="count" aria-live="polite"><span id="shown">{total}</span> sounds shown</p>
</section>
<section aria-label="All sound effects">
{grid(meta, '', True, True)}
<p class="empty" hidden>No sounds match your search. Try another word, such as &ldquo;hit&rdquo; or &ldquo;click&rdquo;.</p>
</section>

<section class="cats"><h2>Browse sound effect categories</h2><div class="catgrid">{cat_cards}</div></section>

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
<tr><td>WAV</td><td>48 kHz, 24-bit, uncompressed</td><td>30 KB&ndash;1.2 MB</td><td>Premiere Pro, DaVinci Resolve, Final Cut, further processing</td></tr>
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
<p>We only use sources that clearly release their work into the public domain: the <a href="https://bigsoundbank.com/" rel="noopener">BigSoundBank</a> library recorded by sound designer Joseph Sardin, the CC0 audio packs from <a href="https://kenney.nl/" rel="noopener">Kenney.nl</a>, and CC0 uploads on <a href="https://opengameart.org/" rel="noopener">OpenGameArt</a>. We do not use packs whose licence forbids redistribution, and we do not use AI-generated or code-synthesised sounds. The exact source, author and licence of every single file is listed on the <a href="license/">License page</a>.</p>
</article>

<section class="faqsec prose"><h2>Frequently asked questions</h2>{faq_html(FAQ)}</section>
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
        zsize = os.path.getsize(os.path.join(OUT, 'zips', zipname))
        paras = ''.join(f'<p>{esc(p)}</p>' for p in info['intro'].split('\n')) + f'<p>{esc(info["extra"])}</p>'
        pack = ', '.join(f'<a href="../sound/{m["file"]}/">{esc(m["name"])}</a> ({dur(m["dur"])})' for m in items)
        paras += f'<h3>What is in this {esc(info["noun"])} pack</h3><p>{n} sounds: {pack}. Each one has its own page with a preview player, technical details and the original source.</p>'
        others = ''.join(f'<a href="../{o}/">{esc(CATS[o])}</a>' for o in ORDER if o != c)
        body = f'''
<nav class="crumbs" aria-label="Breadcrumb"><a href="../">Home</a> &rsaquo; <span>{esc(CATS[c])}</span></nav>
<section class="hero small">
 <h1>{esc(info['h1'])}</h1>
 <p class="lead">{n} free {esc(info['noun'])} sound effects. CC0 public domain, free for commercial use, no attribution needed. One-click MP3 or WAV download.</p>
 <a class="btn big" href="../zips/{zipname}" download="{zipname}">{DL}Download whole category as ZIP <small>({n} sounds, MP3 + WAV, {kb(zsize)})</small></a>
</section>
{grid(items, '../', False, True)}
<article class="prose catintro"><h2>About these {esc(info['noun'])} sound effects</h2>{paras}
<p>All files are trimmed, faded and levelled (about -14 LUFS, peaks at -1 dBTP). See the <a href="../license/">License page</a> for the original source of each sound.</p></article>
<section class="prose"><h2>More free sound effect categories</h2><div class="morecats">{others}</div></section>
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
<nav class="crumbs" aria-label="Breadcrumb"><a href="{rel}">Home</a> &rsaquo; <a href="{rel}{c}/">{esc(CATS[c])}</a> &rsaquo; <span>{esc(name)}</span></nav>
<div class="sound-layout">
<section class="hero small sound-hero">
 <h1>{esc(name)} Sound Effect</h1>
 <p class="lead">{esc(sents)}</p>
 <article class="card single" data-name="{esc(name.lower())}" data-cat="{c}">
  <div class="prog" aria-hidden="true"><span></span></div>
  <div class="actions">
   <button class="play" type="button" data-src="{base}.mp3" aria-label="Play preview of {esc(name)}" title="Play preview"><svg class="i-play" viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z" fill="currentColor"/></svg><svg class="i-stop" viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor"/></svg></button>
   <a class="btn" href="{base}.mp3" download="{slug}.mp3">{DL}Download MP3 <small>({kb(m['mp3'])})</small></a>
   <a class="btn ghost" href="{base}.wav" download="{slug}.wav">{DL}WAV <small>({kb(m['wav'])})</small></a>
  </div>
 </article>
</section>
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
 <p><a class="btn ghost inline" href="{rel}zips/{zipname}" download="{zipname}">{DL}Download all {len(items)} {esc(info['noun'])} sounds (ZIP)</a></p>
</section>
</div>
<section class="related"><h2>Related {esc(info['noun'])} sound effects</h2>
{grid(related, rel, False, False)}
<p class="more"><a href="{rel}{c}/">See all {len(items)} {esc(CATS[c].lower())} sound effects &rarr;</a></p></section>
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
    body = f'<nav class="crumbs" aria-label="Breadcrumb"><a href="../">Home</a> &rsaquo; <span>{esc(title)}</span></nav><article class="prose page">{inner}</article>'
    write(f'{slug}/index.html', page('../', f'{slug}/', f'{title} – {SITE_NAME}', desc, body,
          ld=[crumbs_ld([('Home', ''), (title, f'{slug}/')])]))

def build_static():
    total = len(meta)
    simple('about', 'About', f'About {SITE_NAME}: a small, fast library of {total} free CC0 sound effects for video editors and creators.', f'''
<h1>About {SITE_NAME}</h1>
<p>{SITE_NAME} is a small, fast library of free sound effects for video editors, short-form creators, streamers and indie game developers. We focus on the sounds editors actually use every day &mdash; whooshes, impacts, risers, pops, camera shutters, UI clicks, notifications, money sounds and glitches &mdash; and make each one ready to drop on a timeline.</p>
<h2>What we do</h2>
<ul><li>Collect sound effects only from sources that release them as <strong>CC0 / public domain</strong>.</li>
<li>Choose realistic, punchy recordings and skip weak, noisy or unusable ones.</li>
<li>Trim leading silence, add short fades and level every file (about -14 LUFS, peaks at -1 dBTP).</li>
<li>Give each sound a clear, searchable name and offer MP3 and WAV with one-click download &mdash; no account, no email, no waiting.</li></ul>
<h2>Who it is for</h2>
<p>YouTubers, TikTok and Reels editors, podcasters, teachers, students, app makers and game developers who need clean sounds they can use commercially without worrying about licences.</p>
<h2>Credits</h2>
<p>The original recordings were made by Joseph Sardin (<a href="https://bigsoundbank.com/" rel="noopener">BigSoundBank</a>), <a href="https://kenney.nl/" rel="noopener">Kenney</a> and CC0 contributors on <a href="https://opengameart.org/" rel="noopener">OpenGameArt</a>. Thank you for giving your work to the public domain. Full per-file credits are on the <a href="../license/">License page</a>.</p>''')

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
    body404 = f'''<section class="hero small"><h1>Page not found</h1><p class="lead">That page or sound does not exist (any more). Try the home page search, or pick a category:</p>
<p><a class="btn" href="{b}">Go to the home page</a></p><div class="morecats">{''.join(f'<a href="{b}{c}/">{esc(CATS[c])}</a>' for c in ORDER)}</div></section>'''
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
    os.makedirs(os.path.join(OUT, 'zips'), exist_ok=True)
    lic = f"""{SITE_NAME} - {{cat}} pack
All sounds: CC0 1.0 Universal (public domain). Free for commercial use, no attribution required.
https://creativecommons.org/publicdomain/zero/1.0/
Original sources and authors: see the License page of the site ({SITE_URL}/license/).
"""
    for c in ORDER:
        zp = os.path.join(OUT, 'zips', f'{c}-sfx-pack.zip')
        with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
            for m in by_cat[c]:
                z.write(os.path.join(AUDIO, c, f"{m['file']}.mp3"), f"{c}/MP3/{m['file']}.mp3")
                z.write(os.path.join(AUDIO, c, f"{m['file']}.wav"), f"{c}/WAV/{m['file']}.wav")
            z.writestr(f'{c}/LICENSE.txt', lic.format(cat=CATS[c]))
            # deterministic-ish timestamps not required

def build_seo():
    urls = [''] + [f'{c}/' for c in ORDER] + [f"sound/{m['file']}/" for m in meta] + ['about/', 'license/', 'privacy/', 'terms/', 'contact/']
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(
        f'  <url><loc>{SITE_URL}/{u}</loc><lastmod>{UPDATED}</lastmod></url>\n' for u in urls) + '</urlset>\n'
    write('sitemap.xml', sm)
    write('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n')
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
    build_files(); build_home(); build_cats(); build_sounds(); build_static(); build_seo()
    print('built', len(meta), 'sounds into', os.path.abspath(OUT))

if __name__ == '__main__':
    main()
