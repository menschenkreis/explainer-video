#!/usr/bin/env python3
"""site_build.py <site.json> [--out DIR]  –  build a free, static study website from explainer-video projects.

Output is plain HTML/CSS/JS (no build tools, no tracking, no external requests): host it anywhere for free
(GitHub Pages, Cloudflare Pages, Netlify, a folder on your own web space) – or just open site/index.html.

site.json (paths relative to the file):
{
  "title": "Systems Engineering lernen", "subtitle": "Erklärvideos, Merkhilfen und Selbsttests", "lang": "de",
  "notice": "Eigene Zusammenfassung mit eigenen Beispielen. Quelle: …",        # shown in the footer
  "courses": [{
     "id": "optics", "title": "Light and colour", "source": "optional source line",
     "videos": [{"slug": "rainbow", "title": "How a rainbow forms", "dir": "../videos/rainbow",
                 "summary": "…", "mnemonics": ["E × B = Aspekt"],
                 "quiz": [{"q": "Was ergibt …?", "a": "…"}]}]}]
}
Each video dir must contain index.html (+ narration.mp3, + video.mp4 if exported) and build/timing.json.
"""
import argparse, html, json, shutil, sys
from pathlib import Path

T = {
    "de": dict(home="Start", cards="Merkkarten", videos="Videos", min="Min.", watch="Video ansehen", dl="MP4 herunterladen", mp3="Audio (MP3)",
               chapters="Kapitel", transcript="Transkript", mnem="Eselsbrücken", quiz="Selbsttest", show="Antwort zeigen", done="Als gelernt markieren",
               summary="Worum geht es?", flip="Karte umdrehen", shuffle="Mischen", all="Alle", next="Weiter", prev="Zurück", of="von", no_mp4="MP4 folgt",
               free="Kostenlos · ohne Anmeldung · ohne Tracking", open="Öffnen", tipt="Tipp: Leertaste = Pause, ←/→ = 5 s, c = Untertitel.", cardhint="Klick auf die Karte dreht sie um.",
               q="Frage", a="Antwort", mn="Eselsbrücke"),
    "en": dict(home="Home", cards="Flashcards", videos="Videos", min="min", watch="Watch video", dl="Download MP4", mp3="Audio (MP3)",
               chapters="Chapters", transcript="Transcript", mnem="Mnemonics", quiz="Self-test", show="Show answer", done="Mark as learned",
               summary="What is it about?", flip="Flip card", shuffle="Shuffle", all="All", next="Next", prev="Previous", of="of", no_mp4="MP4 coming soon",
               free="Free · no sign-up · no tracking", open="Open", tipt="Tip: Space = pause, ←/→ = 5 s, c = captions.", cardhint="Click a card to flip it.",
               q="Question", a="Answer", mn="Mnemonic"),
}
CSS = """:root{--bg:#0d1526;--card:#18263f;--line:#2f4570;--ink:#f2f5fa;--mute:#92a3c2;--a:#ffb547;--b:#4fd1c5;--c:#7aa2ff;--d:#ff7a8a;--ok:#6ee7a8;--font:Inter,system-ui,-apple-system,"Helvetica Neue",Arial,sans-serif}
@media(prefers-color-scheme:light){:root{--bg:#f6f8fc;--card:#fff;--line:#d5deee;--ink:#14203a;--mute:#5a6a88}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.55 var(--font)}a{color:var(--c)}
header.top{display:flex;flex-wrap:wrap;gap:12px 28px;align-items:center;padding:14px 5vw;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:5}
header.top b{font-size:19px}header.top nav{display:flex;gap:18px;margin-left:auto}header.top a{text-decoration:none;color:var(--ink)}header.top a:hover{color:var(--a)}
main{max-width:1100px;margin:0 auto;padding:28px 5vw 60px}h1{font-size:clamp(28px,4vw,44px);line-height:1.1;margin:.2em 0}h2{margin:1.6em 0 .5em}h3{margin:.2em 0}
.sub{color:var(--mute);font-size:19px}.pill{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:2px 12px;font-size:14px;color:var(--mute)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 20px;text-decoration:none;color:var(--ink);display:block}.card:hover{border-color:var(--a)}
.btn{display:inline-block;background:var(--a);color:#0d1526;font-weight:700;border:0;border-radius:10px;padding:10px 18px;text-decoration:none;cursor:pointer;font:700 16px var(--font)}
.btn.ghost{background:transparent;color:var(--ink);border:1px solid var(--line)}.btn[aria-disabled=true]{opacity:.45;pointer-events:none}
.player{position:relative;aspect-ratio:16/9;width:100%;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#000}.player iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.row{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0}ol.chap{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:8px}
ol.chap a{display:flex;gap:10px;text-decoration:none;color:var(--ink);border:1px solid var(--line);border-radius:10px;padding:8px 12px;background:var(--card)}ol.chap a:hover{border-color:var(--a)}ol.chap time{color:var(--a);font-variant-numeric:tabular-nums}
details{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 16px;margin:8px 0}summary{cursor:pointer;font-weight:600}
.tr h3{color:var(--a);margin-top:1.2em}.tr p{margin:.3em 0;color:var(--ink)}.mn{display:flex;flex-wrap:wrap;gap:10px}.mn span{border:1px solid var(--a);color:var(--a);border-radius:999px;padding:5px 16px;font-weight:600}
.fc{perspective:1000px;cursor:pointer;min-height:220px}.fc .in{position:relative;min-height:220px;transition:transform .5s;transform-style:preserve-3d}.fc.flip .in{transform:rotateY(180deg)}
.fc .f,.fc .bk{position:absolute;inset:0;backface-visibility:hidden;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:20px;border-radius:16px;border:1px solid var(--line);background:var(--card)}
.fc .bk{transform:rotateY(180deg);border-color:var(--a)}.fc small{color:var(--mute);margin-bottom:8px}.fc .big{font-size:22px;font-weight:700}
footer{border-top:1px solid var(--line);color:var(--mute);padding:20px 5vw;font-size:14px}label.learned{display:inline-flex;gap:8px;align-items:center;cursor:pointer}
@media print{header.top,.player,.row{display:none}details{display:block}}"""
JS = """
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const store={get:k=>{try{return localStorage.getItem(k)}catch(e){return null}},set:(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}}};
$$('[data-learned]').forEach(cb=>{const k='ev-learned:'+cb.dataset.learned;cb.checked=store.get(k)==='1';cb.onchange=()=>store.set(k,cb.checked?'1':'0')});
$$('.fc').forEach(c=>c.onclick=()=>c.classList.toggle('flip'));
const ifr=$('#player');$$('[data-seek]').forEach(a=>a.onclick=e=>{e.preventDefault();ifr.src=ifr.dataset.base+'?t='+a.dataset.seek;ifr.scrollIntoView({behavior:'smooth',block:'center'})});
const sh=$('#shuffle');if(sh)sh.onclick=()=>{const g=$('#cards');$$('.fc',g).sort(()=>Math.random()-.5).forEach(c=>g.appendChild(c))};
$$('[data-filter]').forEach(b=>b.onclick=()=>{const f=b.dataset.filter;$$('.fc').forEach(c=>c.style.display=(f==='*'||c.dataset.vid===f)?'':'none')});
"""


def esc(s): return html.escape(str(s), quote=True)
def mmss(t): return f"{int(t // 60)}:{int(t % 60):02d}"


def page(site, t, title, body, depth, active=""):
    up = "../" * depth
    nav = f'<a href="{up}index.html">{t["home"]}</a><a href="{up}cards.html">{t["cards"]}</a>'
    return f'''<!doctype html><html lang="{site["lang"]}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} – {esc(site["title"])}</title><link rel="stylesheet" href="{up}assets/style.css"></head><body>
<header class="top"><b>{esc(site["title"])}</b><span class="pill">{t["free"]}</span><nav>{nav}</nav></header><main>{body}</main>
<footer>{esc(site.get("notice", ""))}</footer><script src="{up}assets/app.js"></script></body></html>'''


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("site_json"); ap.add_argument("--out")
    a = ap.parse_args()
    sj = Path(a.site_json).resolve(); base = sj.parent; site = json.loads(sj.read_text(encoding="utf-8"))
    site.setdefault("lang", "en"); t = T.get(site["lang"], T["en"])
    out = Path(a.out).resolve() if a.out else base / "site"
    if out.exists():
        shutil.rmtree(out)
    (out / "assets").mkdir(parents=True)
    (out / "assets/style.css").write_text(CSS, encoding="utf-8"); (out / "assets/app.js").write_text(JS, encoding="utf-8")
    cards, home = [], []
    for c in site["courses"]:
        home.append(f'<h2>{esc(c["title"])}</h2>' + (f'<p class="sub">{esc(c.get("source", ""))}</p>' if c.get("source") else "") + '<div class="grid">')
        for v in c["videos"]:
            vd = (base / v["dir"]).resolve(); timing = json.loads((vd / "build/timing.json").read_text(encoding="utf-8"))
            dst = out / c["id"] / v["slug"]; pd = dst / "player"; pd.mkdir(parents=True)
            for f in ("index.html", "narration.mp3", "video.mp4"):
                if (vd / f).exists():
                    shutil.copy(vd / f, pd / f)
            has_mp4, has_mp3 = (pd / "video.mp4").exists(), (pd / "narration.mp3").exists()
            minutes = round(timing["duration"] / 60)
            # chapters + transcript from the timing file
            chap, tr = [], []
            for sid in timing["order"]:
                sc = timing["scenes"][sid]
                chap.append(f'<li><a href="#" data-seek="{sc["start"]:.1f}"><time>{mmss(sc["start"])}</time><span>{esc(sc["title"])}</span></a></li>')
                text = " ".join(x["text"] for x in timing["captions"] if sc["start"] <= x["start"] < sc["end"])
                tr.append(f'<h3>{esc(sc["title"])}</h3><p>{esc(text)}</p>')
            vid = f'{c["id"]}-{v["slug"]}'
            mn = "".join(f"<span>{esc(m)}</span>" for m in v.get("mnemonics", []))
            quiz = "".join(f'<details><summary>{esc(q["q"])}</summary><p>{esc(q["a"])}</p></details>' for q in v.get("quiz", []))
            dl = f'<a class="btn" href="player/video.mp4" download>⬇ {t["dl"]}</a>' if has_mp4 else f'<span class="btn" aria-disabled="true">{t["no_mp4"]}</span>'
            mp3 = f'<a class="btn ghost" href="player/narration.mp3" download>⬇ {t["mp3"]}</a>' if has_mp3 else ""
            body = f'''<p><a href="../../index.html">← {esc(c["title"])}</a></p><h1>{esc(v["title"])}</h1><p class="sub">{esc(v.get("summary", ""))}</p>
<div class="player"><iframe id="player" data-base="player/index.html" src="player/index.html" allow="autoplay; fullscreen" title="{esc(v["title"])}"></iframe></div>
<div class="row">{dl}{mp3}<label class="learned"><input type="checkbox" data-learned="{vid}"> {t["done"]}</label></div><p class="sub" style="font-size:14px">{t["tipt"]}</p>
<h2>{t["chapters"]}</h2><ol class="chap">{"".join(chap)}</ol>''' + (f'<h2>{t["mnem"]}</h2><div class="mn">{mn}</div>' if mn else "") + \
                   (f'<h2>{t["quiz"]}</h2>{quiz}' if quiz else "") + f'<h2>{t["transcript"]}</h2><details><summary>{t["transcript"]}</summary><div class="tr">{"".join(tr)}</div></details>'
            (dst / "index.html").write_text(page(site, t, v["title"], body, 2), encoding="utf-8")
            home.append(f'<a class="card" href="{c["id"]}/{v["slug"]}/index.html"><span class="pill">{minutes} {t["min"]}</span><h3>{esc(v["title"])}</h3><p class="sub" style="font-size:15px">{esc(v.get("summary", ""))}</p></a>')
            for m in v.get("mnemonics", []):
                cards.append((vid, t["mn"], m, v["title"], None))
            for q in v.get("quiz", []):
                cards.append((vid, t["q"], q["q"], v["title"], q["a"]))
        home.append("</div>")
    (out / "index.html").write_text(page(site, t, site["title"], f'<h1>{esc(site["title"])}</h1><p class="sub">{esc(site.get("subtitle", ""))}</p>' + "".join(home), 0), encoding="utf-8")
    fc = "".join(f'<div class="fc" data-vid="{vid}"><div class="in"><div class="f"><small>{esc(kind)} · {esc(vt)}</small><div class="big">{esc(front)}</div></div>'
                 f'<div class="bk"><small>{t["a"]}</small><div class="big">{esc(back) if back else esc(front)}</div></div></div></div>' for vid, kind, front, vt, back in cards)
    filt = f'<button class="btn ghost" data-filter="*">{t["all"]}</button> ' + " ".join(
        f'<button class="btn ghost" data-filter="{c["id"]}-{v["slug"]}">{esc(v["title"].split(":")[0])}</button>' for c in site["courses"] for v in c["videos"])
    (out / "cards.html").write_text(page(site, t, t["cards"], f'<h1>{t["cards"]}</h1><p class="sub">{t["cardhint"]}</p><div class="row">{filt} <button class="btn" id="shuffle">{t["shuffle"]}</button></div><div class="grid" id="cards">{fc}</div>', 0), encoding="utf-8")
    size = sum(f.stat().st_size for f in out.rglob("*") if f.is_file()) / 1e6
    print(f"site written to {out}  ({size:.0f} MB, {sum(len(c['videos']) for c in site['courses'])} videos, {len(cards)} flashcards)")


if __name__ == "__main__":
    main()
