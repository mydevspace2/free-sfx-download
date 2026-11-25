# Free SFX Download

Static website with 521 free CC0 sound effects in 22 categories (no music), previews, one-click MP3/WAV downloads, per-category ZIP packs. Hosted on GitHub Pages.

## Category ZIP packs
The ZIPs are NOT in this branch (keeps the Pages site ~250 MB). `_source/build.py` writes them to `release_zips/`; they are committed to the separate **`packs`** branch and linked as `https://github.com/mydevspace2/free-sfx-download/raw/packs/<category>-sfx-pack.zip` (`ZIP_URL` in build.py). After a rebuild that changes sounds, copy the new ZIPs to the packs branch and push it.

## Home page and search
The home page shows 24 popular picks (`POPULAR` in build.py) plus category tiles, not every sound (mobile speed). The search box loads `search-index.json` (all sounds) on first focus and renders matching cards; `/?q=word` works too. Category pages list all their sounds.

## Turn on Adsterra ads
Edit **only** `ads/ads-config.js` (on github.com: open the file → pencil icon → paste → Commit).
- `header` (728x90, mobile 320x50), `incontent` (300x250, inside the sound grid), `footer` (728x90, mobile 300x250): paste each Adsterra *Banner* code between the backticks.
- `global`: paste Popunder or Social Bar code.
Every page loads this file (`<script src="ads/ads-config.js">` in the `<head>`), and `assets/ads.js` puts each code in its slot (`<div class="ad-slot" data-ad-slot="...">`, marked with `<!-- ADSTERRA: ... -->` comments). Empty slots stay hidden.
Rebuilding the site never overwrites `ads/ads-config.js`.

## Switch to a custom domain
Generator: `_source/build.py`. Change at the top (or via env vars) and rebuild:
- `SITE_URL` → `https://yourdomain.com` (used only for canonical, og:url, sitemap.xml, robots.txt, llms.txt)
- `BASE_PATH` → `/` (used only by 404.html)
- `CNAME` → `yourdomain.com` (writes the CNAME file)
All other links are relative. Then in repo Settings → Pages → Custom domain, and DNS: 4 A records to 185.199.108-111.153 + CNAME `www` → mydevspace2.github.io.

## Sources
Every file's original URL, author and licence: `SOURCES.md` and the site's License page.

## SEO structure
- Home `/`, 22 category pages `/<category>/`, one page per sound `/sound/<slug>/` (521), plus About / License / Privacy / Terms / Contact.
- Every page: unique title + meta description, canonical, Open Graph + Twitter card. JSON-LD: WebSite + SearchAction (`/?q=`) + Organization + FAQPage on home; CollectionPage + ItemList + BreadcrumbList on categories; AudioObject + BreadcrumbList on sound pages.
- `sitemap.xml` lists every page with `lastmod`; `robots.txt` explicitly allows Googlebot, Bingbot and the AI crawlers (GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, Claude-SearchBot, PerplexityBot, Google-Extended, Applebot-Extended, CCBot …) and points to the sitemap; `llms.txt` summarises the site for AI assistants.
- Note: on a GitHub *project* site crawlers only read `mydevspace2.github.io/robots.txt` (domain root), so this repo's robots.txt is ignored until the custom domain is set; then it sits at the root and works with no other change.
- Sound pages: prev/next links within the category + 6 related sounds; category pages: every sound as a real link, all other categories, editor bio box. About page holds the editorial / licence-checking policy (brand persona "The FreeSFX Download team").
- Share image: `_source/og.py` regenerates `assets/og-image.{jpg,png,webp}` (pages use the JPG). CSS is minified when inlined; JS is minified with terser (tools/node_modules) if present. Asset URLs use content hashes (`?v=`). Per-sound texts live in `_source/sound_text.py`, category SEO texts in `_source/content.py` (`SEO`).

## Google Search Console (TODO – not done yet)
1. search.google.com/search-console → Add property → **URL prefix** `https://mydevspace2.github.io/free-sfx-download/`.
2. Choose **HTML tag** verification and paste only the `content` value into `GOOGLE_SITE_VERIFICATION` at the top of `_source/build.py` (Bing: `BING_SITE_VERIFICATION`) — rebuild and push, then click Verify.
3. Sitemaps → submit `sitemap.xml`. URL Inspection → Request indexing for home + category pages.
4. Bing Webmaster Tools → Import from Search Console.
(After moving to a custom domain, add a new Domain property and re-submit the sitemap.)
