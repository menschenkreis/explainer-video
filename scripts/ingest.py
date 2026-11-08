#!/usr/bin/env python3
"""ingest.py <file-or-folder>… [--out DIR]  –  turn a pile of source material into page-marked text + an inventory.

Supports: .pdf (needs pymupdf – installed by `ev setup`), .docx, .pptx, .md/.txt, .html/.htm.
Writes  <out>/sources/<name>.txt   (with '=== PAGE n ===' / '=== SLIDE n ===' markers)
        <out>/sources/inventory.json   (type, pages, words, headings, reading minutes)
Then read the texts and follow references/curriculum-synthesis.md.
"""
import argparse, html, json, re, sys, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

HEAD = re.compile(r"^(\d+(\.\d+){0,3}\.?\s+[A-ZÄÖÜ0-9].{2,80}|#{1,4}\s+.+|[A-ZÄÖÜ][A-ZÄÖÜ \-]{6,60})$")


def read_pdf(p):
    try:
        import pymupdf
    except ImportError:
        sys.exit("PDF support needs pymupdf – run: ev setup   (and use the `ev ingest` command)")
    d = pymupdf.open(p)
    return [d[i].get_text() for i in range(d.page_count)], "PAGE"


def read_docx(p):
    with zipfile.ZipFile(p) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paras = ["".join(t.text or "" for t in para.iter("{%s}t" % ns["w"])) for para in root.iter("{%s}p" % ns["w"])]
    return ["\n".join(paras)], "PAGE"


def read_pptx(p):
    slides = []
    with zipfile.ZipFile(p) as z:
        names = sorted((n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml", n)), key=lambda n: int(re.findall(r"\d+", n)[0]))
        for n in names:
            root = ET.fromstring(z.read(n))
            slides.append("\n".join(t.text or "" for t in root.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}t")))
    return slides, "SLIDE"


def read_text(p):
    t = Path(p).read_text(encoding="utf-8", errors="replace")
    if p.suffix.lower() in (".html", ".htm"):
        t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t); t = re.sub(r"<[^>]+>", "\n", t); t = html.unescape(t)
    return [t], "PAGE"


READERS = {".pdf": read_pdf, ".docx": read_docx, ".pptx": read_pptx, ".md": read_text, ".txt": read_text, ".html": read_text, ".htm": read_text}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("paths", nargs="+"); ap.add_argument("--out", default=".")
    a = ap.parse_args()
    out = Path(a.out) / "sources"; out.mkdir(parents=True, exist_ok=True)
    files = []
    for p in map(Path, a.paths):
        files += sorted(f for f in p.rglob("*") if f.is_file()) if p.is_dir() else [p]
    inv = []
    for f in files:
        rd = READERS.get(f.suffix.lower())
        if not rd or f.name.startswith("."):
            continue
        try:
            pages, unit = rd(f)
        except Exception as e:
            print(f"skip {f.name}: {e}"); continue
        text = "".join(f"\n=== {unit} {i} ===\n{t}" for i, t in enumerate(pages, 1))
        name = re.sub(r"[^A-Za-z0-9._-]+", "_", f.stem)[:80]
        (out / f"{name}.txt").write_text(text, encoding="utf-8")
        words = len(text.split())
        heads = []
        for i, t in enumerate(pages, 1):
            for line in t.splitlines():
                line = line.strip()
                if HEAD.match(line) and len(heads) < 60 and not line.endswith("."):
                    heads.append({"page": i, "text": line[:90]})
        inv.append({"file": str(f), "text_file": f"sources/{name}.txt", "type": f.suffix.lower().lstrip("."), "pages": len(pages),
                    "words": words, "read_minutes": round(words / 220, 1), "headings": heads})
        print(f"✓ {f.name}: {len(pages)} {unit.lower()}(s), {words} words")
    (out / "inventory.json").write_text(json.dumps({"files": inv, "total_words": sum(x["words"] for x in inv)}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"inventory: {out/'inventory.json'}  ({len(inv)} files, {sum(x['words'] for x in inv)} words)")


if __name__ == "__main__":
    main()
