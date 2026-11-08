#!/usr/bin/env python3
"""extract_chapter.py – pull the text of a chapter out of a PDF so a script can be written from it.

  extract_chapter.py book.pdf --find "3.1 Zur Anwendung" --until "3.3 Model"   # locate by headings
  extract_chapter.py book.pdf --pages 130-162 -o build/source.txt               # PDF page numbers (1-based)
  extract_chapter.py book.pdf --toc                                             # print outline if the PDF has one
  extract_chapter.py book.pdf --offset 15                                       # show which PDF page prints as "15"
Each page is prefixed '=== PDF PAGE n ===' so the script can cite pages.  Scanned books often have noisy
text (OCR) around figures: read the figure captions and reconstruct diagrams from the prose.
Needs pymupdf (installed by setup.sh).
"""
import argparse, re, sys
import pymupdf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf"); ap.add_argument("--pages"); ap.add_argument("--find"); ap.add_argument("--until")
    ap.add_argument("--toc", action="store_true"); ap.add_argument("--offset", help="printed page number to look up")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    d = pymupdf.open(a.pdf)
    if a.toc:
        for lvl, title, page in d.get_toc():
            print("  " * (lvl - 1) + f"{title}  (p.{page})")
        return
    if a.offset:
        for i in range(d.page_count):
            if re.search(rf"(^|\n)\s*{re.escape(a.offset)}\s*(\n|$)", d[i].get_text()[-40:]) or re.search(rf"(^|\n)\s*{re.escape(a.offset)}\s*(\n|$)", d[i].get_text()[:40]):
                print("candidate PDF page", i + 1)
        return
    if a.pages:
        lo, hi = [int(x) for x in a.pages.split("-")]
    elif a.find:
        lo = hi = None
        pat = re.compile(re.escape(a.find).replace(r"\ ", r"\s+"))
        end = re.compile(re.escape(a.until).replace(r"\ ", r"\s+")) if a.until else None
        hits = [i + 1 for i in range(d.page_count) if pat.search(d[i].get_text())]
        # the table of contents also matches: take the LAST hit before the until-heading's body hit
        body = [h for h in hits if h > 30] or hits
        lo = body[0]
        if end:
            ends = [i + 1 for i in range(lo, d.page_count) if end.search(d[i].get_text())]
            hi = ends[0] if ends else min(d.page_count, lo + 40)
        else:
            hi = min(d.page_count, lo + 40)
        print(f"found pages {lo}-{hi}", file=sys.stderr)
    else:
        sys.exit("give --pages, --find or --toc")
    text = "".join(f"\n\n=== PDF PAGE {n} ===\n" + d[n - 1].get_text() for n in range(lo, hi + 1))
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text); print(f"wrote {a.out} ({len(text)} chars)")
    else:
        print(text)


if __name__ == "__main__":
    main()
