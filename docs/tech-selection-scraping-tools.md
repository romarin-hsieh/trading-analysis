# TECH-SELECTION NOTE — Web-Scraping Tools for the Finance-Data Crawler

> Date: 2026-06-14. Scope: evaluate scraping tools/projects for ingesting finance news, Medium, YouTube. Budget < $15/mo; runs in GitHub Actions (datacenter IP) + a home box (residential IP).
> Method: GitHub REST API for star/license/maintenance (authoritative, as of 2026-06-14); thunderbit roundup; a 2026 anti-bot guide (community-aligned); the scrapinghub article-extraction benchmark.
> ⚠️ **Reddit was hard-blocked** on every path (direct, `old.`, `.json`, and via `r.jina.ai` — "blocked by network security"). The r/webscraping thread content could not be read; its consensus is reconstructed from equivalent sources and flagged as such below.

This note does **not** repeat the already-chosen stack (RSS/feedparser, r.jina.ai + Crawl4AI, Cloudflare Worker proxy, Apify/Camoufox/agent-browser; Firecrawl/ScrapingBee/Bright Data rejected as over-budget). It records **what was missing** — chiefly **article-text extraction**, plus where Playwright fits.

---

## STEP 1 — Notable scraping GitHub projects (from the thunderbit roundup, stars/license verified via GitHub API 2026-06-14)

| Project | Repo | Stars | License | What it does | Anti-bot / JS |
|---|---|---:|---|---|---|
| Scrapy | `scrapy/scrapy` | 62.2k | BSD-3 | Async Python crawl framework, large-scale | None native (needs Playwright/Selenium plugin) |
| Crawlee | `apify/crawlee` | 23.8k | Apache-2.0 | Node crawler lib, Puppeteer/Playwright pools, auto proxy/retry | Via headless + fingerprint injection |
| Crawl4AI | `unclecode/crawl4ai` | 68.5k | Apache-2.0 | LLM-friendly crawler → Markdown (Playwright under the hood) | Browser-level; some stealth (**already chosen, Tier1**) |
| Scrapling | `D4Vinci/Scrapling` | 63.6k | BSD-3 | Adaptive scraper; HTTP + browser; `StealthyFetcher` | **High** — bundles curl_cffi + Camoufox, solves Turnstile |
| Katana | `projectdiscovery/katana` | 17.0k | MIT | Fast Go crawler / endpoint discovery (security recon) | Optional headless |
| Colly | `gocolly/colly` | 25.3k | Apache-2.0 | High-perf Go scraper/crawler | None (static HTML) |
| MechanicalSoup | `MechanicalSoup/MechanicalSoup` | 4.9k | MIT | Python form-fill + simple browsing over requests+BS4 | None (no JS) |
| Selenium | `SeleniumHQ/selenium` | ~30k | Apache-2.0 | Classic browser automation | Real browser; trivially fingerprinted |
| Playwright | `microsoft/playwright` | 90.9k | Apache-2.0 | Modern multi-browser automation | Full JS; see STEP 2 |
| Puppeteer | `puppeteer/puppeteer` | ~91k | Apache-2.0 | Chrome/Firefox automation (Node) | Full JS |
| Maxun / WebMagic / Nokogiri / Heritrix / Nutch | various | 3–13k | mixed | No-code visual / Java / Ruby parser / archival crawlers | Mostly N/A for our use |

Most relevant *new* names here for us: **Scrapling** (an all-in-one stealth alternative that already wires up curl_cffi + Camoufox — i.e. our Tier1/Tier3 in one package) and **Crawlee** (if the dashboard side ever wants a Node crawler).

---

## STEP 2 — Playwright (`microsoft/playwright`, 90.9k★, Apache-2.0, TS core + first-class Python)

**"Greater network control" it actually gives us:**
- **Request interception / routing** (`page.route`) — abort images/fonts/analytics to cut bandwidth & time in Actions; rewrite headers; **capture XHR/GraphQL JSON directly** (read the API response instead of parsing rendered HTML — ideal for JS-heavy finance sites and a cleaner alternative to scraping Medium's DOM).
- **Response/network events** (`page.on("response")`) — sniff the JSON a page fetches; great for infinite-scroll feeds.
- **Full headful/headless + persistent context** — real Chromium/Firefox/WebKit, cookies/localStorage reuse for login walls.
- **Tracing/HAR capture** — record `.har` for offline replay and debugging flaky pages.

**Python vs Node:** API parity is high. **Use the Python binding** (`playwright`) so it lives in the same repo/venv as the quant engine and feedparser. Node only if we converge on Crawlee. Note Python's async API doesn't compose with Scrapy's Twisted loop — bridge via `scrapy-playwright` if ever needed.

**Anti-bot limits on datacenter IPs (the load-bearing caveat):** vanilla Playwright is **instantly detectable** and, more importantly, **GitHub Actions' AWS IP ranges are blacklisted by Cloudflare/DataDome/Akamai regardless of fingerprint** — "infrastructure beats code." Stealth wrappers:
- **playwright-stealth** — patches common JS tells; **2026: insufficient** vs Cloudflare Turnstile / Kasada (Kasada fingerprints it via `Function.toString()`).
- **patchright** (`Kaliiiiiiiiii-Vinyzu/patchright`, 3.5k★, Apache-2.0) — drop-in, patches the Python/driver source *before* Chrome starts so there are no runtime signatures. Better than playwright-stealth, **but breaks proxy-auth and `add_init_script`** — use only when scores stay low.
- Even patched, datacenter-IP success vs Enterprise Cloudflare is ~75%; residential IP + real fingerprint ~95–97%.

**Complement vs overlap with our stack:**
- **Overlaps Crawl4AI** (which already drives Playwright internally) — so for plain "URL → clean Markdown," prefer Crawl4AI/`r.jina.ai`; don't hand-roll Playwright there.
- **Complements** when we need *network-level* control Crawl4AI doesn't expose: XHR/GraphQL capture, request blocking, HAR, multi-step auth flows.
- **Where it should run:** the **home box (residential IP)**, not Actions, for any protected target. For Cloudflare-hard pages, drive **Camoufox** (Firefox/Juggler, no CDP leaks) rather than patched Chromium.

---

## STEP 3 — Notable tools NOT yet in our stack

**Article-text extraction (our biggest gap — we had nothing here).** Benchmarked F1 (scrapinghub benchmark + Bevendorff et al.):
| Lib | Repo | Stars | License | F1 (text) | Note |
|---|---|---:|---|---|---|
| **trafilatura** | `adbar/trafilatura` | 6.1k | Apache-2.0 | **0.945–0.958** | Best balance; native **Markdown/JSON/XML-TEI** output, metadata+date, built-in feeds/sitemap crawl. **Pick this.** |
| readability-lxml | `buriy/python-readability` | 2.9k | Apache-2.0 | 0.92–0.95 | Solid fallback; errors on some malformed HTML |
| newspaper3k / 4k | `codelucas/newspaper` 15k / `AndyTheFactory/newspaper4k` 1.1k | MIT | 0.91–0.95 | 4k is the maintained fork; nice author/date helpers, slower |
| goose3 | `goose3/goose3` | 0.9k | Apache-2.0 | 0.896 | Most *precise* but low recall (drops content); slow |

→ **trafilatura** is the clear default for clean finance-article text→Markdown. It also pairs perfectly with Tier1: fetch via `r.jina.ai`/Crawl4AI, but when you have raw HTML, `trafilatura.extract(html, output_format="markdown", with_metadata=True)` gives cleaner body + reliable publish-date than Crawl4AI's generic Markdown.

**General frameworks:** Scrapy (best if we ever need large multi-source crawls w/ pipelines+dedup); MechanicalSoup (login forms, no JS); **Scrapling** (strong all-in-one if we want stealth without assembling pieces); Katana/Colly (Go; fast but no JS — Katana useful for *discovering* article URLs on a site).

**Social/media:** **yt-dlp** (`yt-dlp/yt-dlp`, 170k★, Unlicense) — already implied for transcripts; canonical for YouTube page/metadata/subs. **gallery-dl** (18.5k, GPL-2.0) image/gallery dl (charts/infographics in posts). **you-get** (56.8k) simpler dl. **MediaCrawler** (`NanmiCoder/MediaCrawler`, 51.2k★, non-standard license — *review terms before use*) — 小红书/抖音/快手/B站/微博 notes+comments; the go-to if Chinese-social finance sentiment is in scope.

**Stealth:** **patchright** (above); **undetected-chromedriver** (12.7k, GPL-3.0 — **last push 2025-07, going stale**); **nodriver** (`ultrafunkamsterdam/nodriver`, 4.4k, AGPL-3.0 — its successor, direct-CDP, lighter than Playwright); **botasaurus** (4.8k, MIT — humanized mouse curves, good vs DataDome behavioral checks). ⚠️ GPL/AGPL licenses (uc, nodriver) are copyleft — fine as external CLI/process, watch if linking into distributed code. **curl_cffi** (HTTP-only TLS/JA3 spoof) is the cheapest first move for protected JSON APIs before reaching for a browser.

---

## TECH-SELECTION NOTE — JOB → recommended tool

| Job | Recommended tool | Tier / where | Why |
|---|---|---|---|
| **Clean article text → Markdown** | **trafilatura** (fallback: readability-lxml) | Tier1, Actions | Top F1 0.945+, native Markdown+metadata+date — **fills our gap** |
| Structured news at scale | RSS/feedparser → trafilatura; Scrapy if pipelines needed | Tier0/1, Actions | Cheapest, most legal; derived signals only |
| JS-heavy site (rendered HTML) | Crawl4AI / `r.jina.ai` | Tier1, Actions | Already chosen; foreign IP dodges Actions block |
| JS site needing **network control** (XHR/GraphQL capture, request blocking, multi-step auth) | **Playwright (Python)**, → Camoufox for hard CF | Tier3, **home box** | The role Playwright uniquely fills vs Crawl4AI |
| Anti-bot / Cloudflare Turnstile | Camoufox (`geoip=True`) + residential IP; or Scrapling `StealthyFetcher`; curl_cffi for JSON-only | Tier3, home box | Datacenter IPs are pre-blocked; residential + real fingerprint = ~95% |
| Medium (GraphQL) | Cloudflare Worker proxy (chosen); else Playwright `page.route` to read the GraphQL JSON | Tier2/3 | Worker request originates in-network |
| YouTube (pages/subs/meta) | yt-dlp (+ youtube-transcript-api) | home box (residential) | Canonical; cloud IPs throttled |
| Chinese social media (小红书/抖音/微博) | MediaCrawler *(review license/ToS)* | home box | Only mature OSS option |

**Where Playwright fits (one line):** the **residential-IP, network-control fallback** — use it when Crawl4AI/`r.jina.ai` can't (intercepting requests, reading XHR/GraphQL, scripted login), driving **Camoufox** for Cloudflare-hard targets; do **not** run it on Actions against protected sites.

**Record for future tech selection:**
1. **Add trafilatura now** — the only real gap; pip-install, zero infra, immediate quality win.
2. **Pin tool + stealth-wrapper versions** — anti-bot is an arms race; capabilities here are point-in-time (mid-2026). Re-verify quarterly.
3. **Decision rule = cheapest layer first:** RSS → trafilatura → r.jina.ai/Crawl4AI → curl_cffi (JSON) → Playwright/Camoufox on home box. Stay $0 until a target forces escalation.
4. **IP placement is the real lever, not code:** anything anti-bot runs on the home box (residential); Actions stays for RSS/extraction/quant/LLM.
5. **Watch licenses:** nodriver/uc are AGPL/GPL, MediaCrawler & you-get non-standard — fine as separate processes, flag before bundling.
6. **undetected-chromedriver is aging** (no push since 2025-07) — prefer **nodriver** or **patchright** if a Chromium-stealth need arises.

⚠️ **Uncertainty flags:** anti-bot pass-rates are vendor/blog claims, not independently reproduced; "100% Camoufox" is marketing-flavored. Reddit thread unreadable (blocked) — community consensus here is triangulated. Star counts exact (GitHub API 2026-06-14); F1 scores from published benchmarks but tool versions tested may lag current releases.
