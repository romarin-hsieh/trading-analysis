"""YouTube transcript extractor for creator-mechanism intake (docs/23 pipeline) -- $0, no key.

Give it a YouTube URL or video id; it pulls the caption track (prefers human zh-TW/zh,
then en, then auto-generated), writes the plain text to data/transcripts/<id>.txt
(gitignored, re-fetchable), and prints it so it can be distilled in the same session.

The transcript is a LEAD, not evidence (docs/23 §5 meta-lesson): a creator's claim must
map to a primary source and enter fabric with F0 pre-commitment + Nagel controls before
it counts. This script only gets the text; the distillation -> F0 -> TR is the next step.

Run:  uv run python scripts/collect/yt_transcript.py "https://youtu.be/VIDEOID"
      uv run python scripts/collect/yt_transcript.py VIDEOID --lang en
"""

from __future__ import annotations

import os
import re
import sys

OUT = os.path.join("data", "transcripts")
PREF = ["zh-TW", "zh-Hant", "zh", "zh-CN", "zh-Hans", "en", "en-US"]


def video_id(s: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|/shorts/|/embed/)([A-Za-z0-9_-]{11})", s)
    return m.group(1) if m else s.strip()


def fetch(vid: str, want: list[str]) -> tuple[str, str]:
    from youtube_transcript_api import YouTubeTranscriptApi
    api = YouTubeTranscriptApi()
    tl = api.list(vid)
    avail = {t.language_code: t for t in tl}
    # priority: requested langs -> human first, then generated
    order = want + [c for c in avail if c not in want]
    picked = None
    for want_gen in (False, True):
        for code in order:
            t = avail.get(code)
            if t is not None and t.is_generated == want_gen:
                picked = t
                break
        if picked:
            break
    if picked is None:
        raise RuntimeError(f"no caption track found (available: {list(avail)})")
    data = picked.fetch()
    text = " ".join(seg.text.replace("\n", " ") for seg in data).strip()
    text = re.sub(r"\s+", " ", text)
    tag = f"{picked.language_code}{'(auto)' if picked.is_generated else ''}"
    return text, tag


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if len(sys.argv) < 2:
        print("usage: yt_transcript.py <url|id> [--lang xx]"); return 1
    vid = video_id(sys.argv[1])
    want = list(PREF)
    if "--lang" in sys.argv:
        want = [sys.argv[sys.argv.index("--lang") + 1]] + PREF
    try:
        text, tag = fetch(vid, want)
    except Exception as e:
        print(f"[{vid}] failed: {str(e)[:160]}"); return 1
    os.makedirs(OUT, exist_ok=True)
    fp = os.path.join(OUT, f"{vid}.txt")
    with open(fp, "w", encoding="utf-8") as f:
        f.write(text)
    words = len(text.split())
    print(f"[{vid}] caption track: {tag} | {words} words / {len(text)} chars -> {fp}")
    print("=" * 80)
    print(text[:4000] + (" ..." if len(text) > 4000 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
