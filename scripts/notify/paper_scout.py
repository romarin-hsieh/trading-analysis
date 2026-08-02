"""Weekly paper scout (docs/21 stage 0) -- discover new finance papers, $0, no keys.

Layered sources per the 2026-07-11 assumption audit in docs/21:
  tier 1 (full text same-day)  : arXiv q-fin via the official API (plain urllib works)
  tier 2 (abstract same-day)   : NBER new working papers, RSS at /rss/new.xml -- NOTE:
                                 NBER sits behind a TLS-fingerprint wall (plain urllib /
                                 requests get 403 even with a browser UA); curl_cffi with
                                 chrome impersonation passes (docs/refs anti-bot tier 1).
                                 The /papers.rss path circulating in search results is 404.
Journal TOCs (2-4y lagged formal versions) are NOT scouted here.

Triage signal (citations are useless for week-old papers): keyword relevance against
our registry topics -- papers that could CHALLENGE a docs/18 verdict score highest.
Output: Telegram digest (same secrets as monitor.yml) or stdout fallback; seen-list
state file keeps re-runs incremental.

Run: uv run python scripts/notify/paper_scout.py           (last 7 days)
"""

from __future__ import annotations

import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

SEEN_PATH = os.path.join("data", "_papers_seen.txt")
ARXIV_CATS = ("q-fin.PM", "q-fin.ST", "q-fin.TR", "q-fin.GN", "q-fin.RM")
ARXIV_API = ("http://export.arxiv.org/api/query?search_query={q}"
             "&sortBy=submittedDate&sortOrder=descending&max_results=100")
NBER_RSS = "https://www.nber.org/rss/new.xml"
UA = {"User-Agent": "trading-analysis-paper-scout (research; contact via repo)"}

# keyword -> (weight, why it matters to us). Challenge-map words score highest:
# they touch verdicts already in docs/18.
KEYWORDS = {
    r"momentum": (3, "challenges docs/09 momentum-dead verdict"),
    r"profitability|quality factor": (3, "challenges GP sole-survivor (docs/10, WATCH)"),
    r"volatility.{0,12}(managed|timing)": (3, "Nagel control territory (F6)"),
    r"regime|markov.{0,10}switch": (3, "challenges timing iron law (5 confirmations)"),
    r"machine learning|neural|random forest|transformer": (2, "challenges ML FAILED (TR-08/11/17b)"),
    r"anomal(y|ies)": (2, "TR-23 territory"),
    r"replicat|out.of.sample|publication": (3, "McLean-Pontiff decay literature"),
    r"multiple testing|false discover|data.?mining|p.?hack": (3, "F5/HLZ methodology"),
    r"transaction cost|market impact|turnover": (2, "F2 cost realism"),
    r"risk parity|portfolio construction|covariance": (2, "flagship/TR-03b territory"),
    r"survivorship|delisting": (2, "F11/F13 territory"),
    r"option|implied volatilit|variance risk": (2, "options dimension (collect-forward)"),
    r"analyst (forecast|revision|estimate)": (2, "analyst pipeline (docs/24 #4)"),
    r"earnings announcement|post.earnings": (1, "PEAD territory"),
    r"crash|tail risk|drawdown": (1, "risk-shaping"),
    r"retail|free data": (1, "our habitat"),
}


def _seen() -> set[str]:
    if not os.path.exists(SEEN_PATH):
        return set()
    return set(open(SEEN_PATH, encoding="utf-8").read().split())


def _mark_seen(ids: list[str]) -> None:
    os.makedirs("data", exist_ok=True)
    with open(SEEN_PATH, "a", encoding="utf-8") as fh:
        for i in ids:
            fh.write(i + "\n")


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def scout_arxiv(days: int) -> list[dict]:
    q = "+OR+".join(f"cat:{c}" for c in ARXIV_CATS)
    xml = _fetch(ARXIV_API.format(q=q))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out = []
    for e in ET.fromstring(xml).findall("a:entry", ns):
        pub = datetime.fromisoformat(e.findtext("a:published", "", ns).replace("Z", "+00:00"))
        if pub < cutoff:
            continue
        out.append({
            "id": e.findtext("a:id", "", ns).rsplit("/", 1)[-1],
            "title": re.sub(r"\s+", " ", e.findtext("a:title", "", ns)).strip(),
            "abstract": re.sub(r"\s+", " ", e.findtext("a:summary", "", ns)).strip(),
            "url": e.findtext("a:id", "", ns),
            "src": "arXiv(全文)",
        })
    return out


def scout_nber(days: int) -> list[dict]:
    from curl_cffi import requests as cr        # TLS wall: plain urllib gets 403
    xml = cr.get(NBER_RSS, impersonate="chrome", timeout=60).content
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out = []
    for item in ET.fromstring(xml).iter("item"):
        pd_txt = item.findtext("pubDate", "")
        try:
            pub = datetime.strptime(pd_txt, "%a, %d %b %Y %H:%M:%S %z")
        except ValueError:
            pub = datetime.now(timezone.utc)
        if pub < cutoff:
            continue
        link = item.findtext("link", "").strip()
        out.append({
            "id": "nber:" + link.rsplit("/", 1)[-1],
            "title": re.sub(r"\s+", " ", item.findtext("title", "")).strip(),
            "abstract": re.sub(r"<[^>]+>|\s+", " ", item.findtext("description", "")).strip(),
            "url": link,
            "src": "NBER(摘要)",
        })
    return out


def triage(p: dict) -> tuple[int, list[str]]:
    text = (p["title"] + " " + p["abstract"]).lower()
    score, whys = 0, []
    for pat, (w, why) in KEYWORDS.items():
        if re.search(pat, text):
            score += w
            whys.append(why)
    return score, whys[:2]


def send_telegram(text: str) -> bool:
    import requests
    tok, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not tok or not chat:
        return False
    return requests.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                         json={"chat_id": chat, "text": text,
                               "disable_web_page_preview": True}, timeout=30).ok


def main() -> int:
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    seen = _seen()
    papers = []
    for fn in (scout_arxiv, scout_nber):
        try:
            papers += fn(days)
        except Exception as e:
            print(f"[warn] {fn.__name__}: {str(e)[:100]}")
    fresh = [p for p in papers if p["id"] not in seen]
    ranked = sorted(((p, *triage(p)) for p in fresh), key=lambda t: -t[1])
    hits = [(p, s, w) for p, s, w in ranked if s >= 3]

    print(f"scout: {len(papers)} papers ({days}d window), {len(fresh)} new, "
          f"{len(hits)} above triage bar (score>=3)")
    lines = [f"📄 論文偵察週報 ({datetime.now(timezone.utc).date()}) — "
             f"{len(fresh)} 新 / {len(hits)} 過門檻"]
    for p, s, whys in hits[:10]:
        lines.append(f"\n[{s}] {p['title']}\n{p['src']} · {'; '.join(whys)}\n{p['url']}")
        print(f"  [{s}] {p['title'][:80]}  ({p['src']})")
    if hits:
        msg = "\n".join(lines)[:4000]
        if send_telegram(msg):
            print("[telegram] digest sent")
        else:
            print("[telegram] not configured -- stdout only")
    _mark_seen([p["id"] for p in fresh])
    return 0


if __name__ == "__main__":
    sys.exit(main())
