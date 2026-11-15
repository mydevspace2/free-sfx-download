# Free SFX Download

Static website with free CC0 sound effects (no music), one-click MP3/WAV downloads, per-category ZIP packs. Hosted on GitHub Pages.

## Turn on Adsterra ads
Edit **only** `ads/ads-config.js` (on github.com: open the file → pencil icon → paste → Commit).
- `header` (728x90, mobile 320x50), `incontent` (300x250, inside the sound grid), `footer` (728x90, mobile 300x250): paste each Adsterra *Banner* code between the backticks.
- `global`: paste Popunder or Social Bar code.
Every page loads this file (`<script src="ads/ads-config.js">` in the `<head>`), and `assets/ads.js` puts each code in its slot (`<div class="ad-slot" data-ad-slot="...">`, marked with `<!-- ADSTERRA: ... -->` comments). Empty slots stay hidden.
Rebuilding the site never overwrites `ads/ads-config.js`.

## Switch to a custom domain
Generator: `_source/build.py`. Change at the top (or via env vars) and rebuild:
- `SITE_URL` → `https://yourdomain.com` (used only for canonical, og:url, sitemap.xml, robots.txt)
- `BASE_PATH` → `/` (used only by 404.html)
- `CNAME` → `yourdomain.com` (writes the CNAME file)
All other links are relative. Then in repo Settings → Pages → Custom domain, and DNS: 4 A records to 185.199.108-111.153 + CNAME `www` → mydevspace2.github.io.

## Sources
Every file's original URL, author and licence: `SOURCES.md` and the site's License page.
