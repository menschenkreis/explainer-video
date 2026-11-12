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
                 "quiz": [{"q": "Was ergibt …?", "a": "…"}],
                 "exercises": [ … interactive drills, see docs/study-site.md: prefmatrix | nwa | conflict | steps … ],
                 "links": [{"title": "Übungs-App", "href": "https://…"}]}]}]
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
               q="Frage", a="Antwort", mn="Eselsbrücke", ex="Übungen", exhint="Interaktive Methoden-Drills – alles rechnet im Browser, nichts wird gespeichert oder gesendet.",
               links="Weitere Hilfsmittel"),
    "en": dict(home="Home", cards="Flashcards", videos="Videos", min="min", watch="Watch video", dl="Download MP4", mp3="Audio (MP3)",
               chapters="Chapters", transcript="Transcript", mnem="Mnemonics", quiz="Self-test", show="Show answer", done="Mark as learned",
               summary="What is it about?", flip="Flip card", shuffle="Shuffle", all="All", next="Next", prev="Previous", of="of", no_mp4="MP4 coming soon",
               free="Free · no sign-up · no tracking", open="Open", tipt="Tip: Space = pause, ←/→ = 5 s, c = captions.", cardhint="Click a card to flip it.",
               q="Question", a="Answer", mn="Mnemonic", ex="Exercises", exhint="Interactive method drills – everything is computed in your browser, nothing is stored or sent.",
               links="More tools"),
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
.ex{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px 20px;margin:14px 0}.ex h3{margin:0 0 4px}.ex .hint{color:var(--mute);font-size:15px;margin:0 0 10px}
.ex table{border-collapse:collapse;width:100%;font-size:15px;margin:8px 0}.ex th,.ex td{border:1px solid var(--line);padding:5px 7px;text-align:center}.ex th{color:var(--a);font-weight:700}.ex td.l,.ex th.l{text-align:left}
.ex .scroll{overflow-x:auto}.ex input[type=number]{width:4.2em;background:var(--bg);color:var(--ink);border:1px solid var(--line);border-radius:6px;padding:3px}
.ex button.pick{background:var(--bg);color:var(--ink);border:1px solid var(--line);border-radius:7px;padding:3px 8px;cursor:pointer;font:600 14px var(--font);min-width:2.2em}
.ex button.pick.on{background:var(--a);color:#0d1526;border-color:var(--a)}.ex .best{background:color-mix(in srgb,var(--ok) 22%,transparent)}.ex .out{opacity:.4;text-decoration:line-through}
.ex .res{margin-top:8px;font-weight:600}.ex .ok{color:var(--ok)}.ex .bad{color:var(--d)}.ex .neg{color:var(--d);font-weight:800}.ex .pos{color:var(--ok);font-weight:800}
.ex ol.steps li{margin:6px 0}.ex ol.steps li.hidden{display:none}.ex ol.steps .ans{display:none;color:var(--b);margin-top:3px}.ex ol.steps li.shown .ans{display:block}
@media print{header.top,.player,.row{display:none}details{display:block}}"""
JS = """
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const store={get:k=>{try{return localStorage.getItem(k)}catch(e){return null}},set:(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}}};
$$('[data-learned]').forEach(cb=>{const k='ev-learned:'+cb.dataset.learned;cb.checked=store.get(k)==='1';cb.onchange=()=>store.set(k,cb.checked?'1':'0')});
$$('.fc').forEach(c=>c.onclick=()=>c.classList.toggle('flip'));
const ifr=$('#player');$$('[data-seek]').forEach(a=>a.onclick=e=>{e.preventDefault();ifr.src=ifr.dataset.base+'?t='+a.dataset.seek;ifr.scrollIntoView({behavior:'smooth',block:'center'})});
const sh=$('#shuffle');if(sh)sh.onclick=()=>{const g=$('#cards');$$('.fc',g).sort(()=>Math.random()-.5).forEach(c=>g.appendChild(c))};
/* ---------- interactive drills: data in data-ex, rendered here ---------- */
const H=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const L=document.documentElement.lang==='de'?{pair:'Paarvergleich: was ist wichtiger?',crit:'Kriterium',cnt:'Nennungen',rank:'Rang',w:'Gewicht',check:'Prüfen',reset:'Zurücksetzen',
 todo:'Noch offen',ok:'Stimmt mit der Lösung überein.',diff:'Abweichung bei',var:'Variante',sum:'Nutzwert',must:'Mussziele erfüllt?',excl:'ausgeschieden',best:'Höchster Nutzwert',
 next:'Nächster Schritt',show:'Lösung zeigen',sup:'unterstützend',neu:'neutral',con:'konfliktär',conf:'Zielkonflikte',none:'keine',wsum:'Summe Gewichte'}
 :{pair:'Pairwise: which matters more?',crit:'Criterion',cnt:'Count',rank:'Rank',w:'Weight',check:'Check',reset:'Reset',todo:'Still open',ok:'Matches the solution.',diff:'Differs at',
 var:'Option',sum:'Utility',must:'Must-haves met?',excl:'excluded',best:'Highest utility',next:'Next step',show:'Show answer',sup:'supporting',neu:'neutral',con:'conflicting',conf:'Goal conflicts',none:'none',wsum:'Sum of weights'};
const EX={
prefmatrix(el,d){const c=d.criteria,n=c.length,pick={};const pairs=[];for(let i=0;i<n;i++)for(let j=i+1;j<n;j++)pairs.push([i,j]);
 if(d.answers)Object.assign(pick,d.answers);
 el.innerHTML+=`<p class="hint">${L.pair}</p><div class="scroll"><table class="pm"></table></div><div class="scroll"><table class="tot"></table></div><div class="res"></div>`+
  `<button class="btn ghost" data-a="reset">${L.reset}</button> `+(d.solution?`<button class="btn" data-a="check">${L.check}</button>`:'');
 const draw=()=>{let h=`<tr><th class="l">${L.crit}</th>`+c.map((x,j)=>`<th>${j+1}</th>`).join('')+'</tr>';
  for(let i=0;i<n;i++){h+=`<tr><td class="l">${i+1}. ${H(c[i])}</td>`;for(let j=0;j<n;j++){if(j<=i){h+='<td>–</td>';continue}const k=i+'-'+j;
   h+=`<td><button class="pick${pick[k]===i?' on':''}" data-k="${k}" data-v="${i}">${i+1}</button><button class="pick${pick[k]===j?' on':''}" data-k="${k}" data-v="${j}">${j+1}</button></td>`}h+='</tr>'}
  $('.pm',el).innerHTML=h;
  const cnt=c.map(()=>d.plus_one?1:0);pairs.forEach(([i,j])=>{const v=pick[i+'-'+j];if(v!==undefined)cnt[v]++});
  const tot=cnt.reduce((a,b)=>a+b,0)||1,scale=d.total||100,w=cnt.map(x=>x/tot*scale),order=[...cnt].sort((a,b)=>b-a);
  $('.tot',el).innerHTML=`<tr><th class="l">${L.crit}</th><th>${L.cnt}</th><th>${L.rank}</th><th>${L.w}${scale===100?' %':''}</th></tr>`+
   c.map((x,i)=>`<tr><td class="l">${H(x)}</td><td>${cnt[i]}</td><td>${order.indexOf(cnt[i])+1}</td><td>${w[i].toFixed(1)}</td></tr>`).join('');
  const open=pairs.filter(([i,j])=>pick[i+'-'+j]===undefined).length;$('.res',el).textContent=open?`${L.todo}: ${open}/${pairs.length}`:'';
  $$('button.pick',el).forEach(b=>b.onclick=()=>{pick[b.dataset.k]=+b.dataset.v;draw()});el._w=w};
 el.addEventListener('click',e=>{const a=e.target.dataset.a;if(a==='reset'){for(const k in pick)delete pick[k];draw()}
  if(a==='check'){const op=pairs.filter(([i,j])=>pick[i+'-'+j]===undefined).length;if(op){$('.res',el).textContent=`${L.todo}: ${op}/${pairs.length}`;return}
   const bad=c.filter((x,i)=>d.solution[x]!==undefined&&Math.abs(el._w[i]-d.solution[x])>(d.tolerance??1));
   $('.res',el).innerHTML=bad.length?`<span class="bad">${L.diff}: ${bad.map(H).join(', ')}</span>`:`<span class="ok">${L.ok}</span>`}});draw()},
nwa(el,d){const cr=d.criteria,va=d.variants,mx=d.max||10,sc=d.scores?JSON.parse(JSON.stringify(d.scores)):va.map(()=>cr.map(()=>'')),mu=d.musts||[],mok=d.must_ok?JSON.parse(JSON.stringify(d.must_ok)):va.map(()=>mu.map(()=>true));
 el.innerHTML+=`<p class="hint">0–${mx} · ${L.sum} = Σ ${L.w} × Punkte</p><div class="scroll"><table></table></div><div class="res"></div><button class="btn ghost" data-a="reset">${L.reset}</button>`;
 const draw=()=>{const ws=cr.reduce((a,c)=>a+(+c.weight||0),0);
  const sum=va.map((v,i)=>cr.reduce((a,c,j)=>a+(+c.weight||0)*(+sc[i][j]||0),0)),out=va.map((v,i)=>mok[i].some(x=>!x));
  const best=Math.max(...sum.filter((x,i)=>!out[i]));
  let h=`<tr><th class="l">${L.crit}</th><th>${L.w}</th>`+va.map((v,i)=>`<th class="${out[i]?'out':''}">${H(v)}</th>`).join('')+'</tr>';
  mu.forEach((m,k)=>{h+=`<tr><td class="l">✓ ${H(m)}</td><td>Muss</td>`+va.map((v,i)=>`<td><input type="checkbox" data-m="${i}-${k}" ${mok[i][k]?'checked':''}></td>`).join('')+'</tr>'});
  cr.forEach((c,j)=>{h+=`<tr><td class="l">${H(c.name)}</td><td>${c.weight}</td>`+va.map((v,i)=>`<td><input type="number" min="0" max="${mx}" step="0.5" data-s="${i}-${j}" value="${sc[i][j]}"></td>`).join('')+'</tr>'});
  h+=`<tr><th class="l">${L.sum}</th><th>${ws}</th>`+va.map((v,i)=>`<th class="${out[i]?'out':(sum[i]===best&&best>0?'best':'')}">${out[i]?L.excl:sum[i].toFixed(0)}</th>`).join('')+'</tr>';
  $('table',el).innerHTML=h;const bi=sum.findIndex((x,i)=>!out[i]&&x===best&&best>0);$('.res',el).textContent=bi>=0?`${L.best}: ${va[bi]} (${best.toFixed(0)})`:'';
  $$('input[data-s]',el).forEach(x=>x.oninput=()=>{const[i,j]=x.dataset.s.split('-');sc[i][j]=x.value;const f=document.activeElement===x;draw();if(f){const y=$(`input[data-s="${i}-${j}"]`,el);y.focus();y.setSelectionRange?.(99,99)}});
  $$('input[data-m]',el).forEach(x=>x.onchange=()=>{const[i,k]=x.dataset.m.split('-');mok[i][k]=x.checked;draw()})};
 el.addEventListener('click',e=>{if(e.target.dataset.a==='reset'){va.forEach((v,i)=>{cr.forEach((c,j)=>sc[i][j]='');mu.forEach((m,k)=>mok[i][k]=true)});draw()}});draw()},
conflict(el,d){const g=d.goals,n=g.length,st={},sym={'+':'+','0':'0','-':'−'};
 el.innerHTML+=`<p class="hint">+ ${L.sup} · 0 ${L.neu} · − ${L.con}</p><div class="scroll"><table></table></div><div class="res"></div>`+(d.solution?`<button class="btn" data-a="check">${L.check}</button>`:'');
 const draw=()=>{let h='<tr><th class="l"></th>'+g.map((x,j)=>`<th>${j+1}</th>`).join('')+'</tr>';
  for(let i=0;i<n;i++){h+=`<tr><td class="l">${i+1}. ${H(g[i])}</td>`;for(let j=0;j<n;j++){if(i===j){h+='<td>■</td>';continue}const k=Math.min(i,j)+'-'+Math.max(i,j);
   if(j<i){const v=st[k];h+=`<td class="${v==='-'?'neg':v==='+'?'pos':''}">${v?sym[v]:''}</td>`;continue}
   h+='<td>'+['+','0','-'].map(v=>`<button class="pick${st[k]===v?' on':''}" data-k="${k}" data-v="${v}">${sym[v]}</button>`).join('')+'</td>'}h+='</tr>'}
  $('table',el).innerHTML=h;const cf=Object.keys(st).filter(k=>st[k]==='-').map(k=>k.split('-').map(x=>+x+1).join('↔'));
  $('.res',el).textContent=`${L.conf}: ${cf.length?cf.join(', '):L.none}`;$$('button.pick',el).forEach(b=>b.onclick=()=>{st[b.dataset.k]=b.dataset.v;draw()})};
 el.addEventListener('click',e=>{if(e.target.dataset.a==='check'){const bad=Object.keys(d.solution).filter(k=>st[k]!==d.solution[k]).map(k=>k.split('-').map(x=>+x+1).join('↔'));
  $('.res',el).innerHTML=bad.length?`<span class="bad">${L.diff}: ${bad.join(', ')}</span>`:`<span class="ok">${L.ok}</span>`}});draw()},
steps(el,d){el.innerHTML+=(d.intro?`<p>${H(d.intro)}</p>`:'')+'<ol class="steps">'+d.steps.map((s,i)=>`<li class="${i?'hidden':''}"><b>${H(s.q)}</b><div class="ans">${H(s.a)}</div></li>`).join('')+
  `</ol><button class="btn ghost" data-a="show">${L.show}</button> <button class="btn" data-a="next">${L.next}</button>`;
 el.addEventListener('click',e=>{const a=e.target.dataset.a,li=$$('ol.steps li',el);if(a==='show'){const c=li.filter(x=>!x.classList.contains('hidden')).pop();c&&c.classList.add('shown')}
  if(a==='next'){const c=li.find(x=>x.classList.contains('hidden'));if(c){li.forEach(x=>{if(!x.classList.contains('hidden'))x.classList.add('shown')});c.classList.remove('hidden')}else li.forEach(x=>x.classList.add('shown'))}})}};
$$('.ex[data-ex]').forEach(el=>{try{const d=JSON.parse(el.dataset.ex);(EX[d.type]||(()=>{}))(el,d)}catch(e){el.insertAdjacentHTML('beforeend','<p class="bad">'+e+'</p>')}});
$$('[data-filter]').forEach(b=>b.onclick=()=>{const f=b.dataset.filter;$$('.fc').forEach(c=>c.style.display=(f==='*'||c.dataset.vid===f)?'':'none')});
"""


def esc(s): return html.escape(str(s), quote=True)
def mmss(t): return f"{int(t // 60)}:{int(t % 60):02d}"


def page(site, t, title, body, depth, active=""):
    up = "../" * depth
    nav = f'<a href="{up}index.html">{t["home"]}</a><a href="{up}cards.html">{t["cards"]}</a>' + (f'<a href="{up}drills.html">{t["ex"]}</a>' if site.get("_has_ex") else "")
    return f'''<!doctype html><html lang="{site["lang"]}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} – {esc(site["title"])}</title><link rel="stylesheet" href="{up}assets/style.css"></head><body>
<header class="top"><b>{esc(site["title"])}</b><span class="pill">{t["free"]}</span><nav>{nav}</nav></header><main>{body}</main>
<footer>{esc(site.get("notice", ""))}</footer><script src="{up}assets/app.js"></script></body></html>'''


EX_TYPES = {"prefmatrix": ("criteria",), "nwa": ("criteria", "variants"), "conflict": ("goals",), "steps": ("steps",)}


def exercise_html(x):
    """one interactive drill; the browser script (JS above) renders it from data-ex"""
    need = EX_TYPES.get(x.get("type"))
    if need is None:
        raise SystemExit(f"unknown exercise type '{x.get('type')}' (use one of: {', '.join(EX_TYPES)})")
    miss = [k for k in need if not x.get(k)]
    if miss:
        raise SystemExit(f"exercise '{x.get('title', x['type'])}' is missing {miss}")
    return (f'<div class="ex" data-ex="{esc(json.dumps(x, ensure_ascii=False))}"><h3>{esc(x.get("title", ""))}</h3>'
            + (f'<p class="hint">{esc(x["task"])}</p>' if x.get("task") else "") + "</div>")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("site_json"); ap.add_argument("--out")
    a = ap.parse_args()
    sj = Path(a.site_json).resolve(); base = sj.parent; site = json.loads(sj.read_text(encoding="utf-8"))
    site.setdefault("lang", "de"); t = T.get(site["lang"], T["en"])
    out = Path(a.out).resolve() if a.out else base / "site"
    if out.exists():
        shutil.rmtree(out)
    (out / "assets").mkdir(parents=True)
    (out / "assets/style.css").write_text(CSS, encoding="utf-8"); (out / "assets/app.js").write_text(JS, encoding="utf-8")
    cards, home, drills = [], [], []
    site["_has_ex"] = any(v.get("exercises") for c in site["courses"] for v in c["videos"])
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
            exs = "".join(exercise_html(x) for x in v.get("exercises", []))
            if exs:
                drills.append(f'<h2>{esc(v["title"])}</h2>' + exs)
            links = "".join(f'<a class="btn ghost" href="{esc(l["href"])}" target="_blank" rel="noopener">{esc(l["title"])} ↗</a>' for l in v.get("links", []))
            dl = f'<a class="btn" href="player/video.mp4" download>⬇ {t["dl"]}</a>' if has_mp4 else f'<span class="btn" aria-disabled="true">{t["no_mp4"]}</span>'
            mp3 = f'<a class="btn ghost" href="player/narration.mp3" download>⬇ {t["mp3"]}</a>' if has_mp3 else ""
            body = f'''<p><a href="../../index.html">← {esc(c["title"])}</a></p><h1>{esc(v["title"])}</h1><p class="sub">{esc(v.get("summary", ""))}</p>
<div class="player"><iframe id="player" data-base="player/index.html" src="player/index.html" allow="autoplay; fullscreen" title="{esc(v["title"])}"></iframe></div>
<div class="row">{dl}{mp3}<label class="learned"><input type="checkbox" data-learned="{vid}"> {t["done"]}</label></div><p class="sub" style="font-size:14px">{t["tipt"]}</p>
<h2>{t["chapters"]}</h2><ol class="chap">{"".join(chap)}</ol>''' + (f'<h2>{t["mnem"]}</h2><div class="mn">{mn}</div>' if mn else "") + \
                   (f'<h2>{t["quiz"]}</h2>{quiz}' if quiz else "") + (f'<h2>{t["ex"]}</h2>{exs}' if exs else "") + \
                   (f'<h2>{t["links"]}</h2><div class="row">{links}</div>' if links else "") + f'<h2>{t["transcript"]}</h2><details><summary>{t["transcript"]}</summary><div class="tr">{"".join(tr)}</div></details>'
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
    if drills:
        (out / "drills.html").write_text(page(site, t, t["ex"], f'<h1>{t["ex"]}</h1><p class="sub">{t["exhint"]}</p>' + "".join(drills), 0), encoding="utf-8")
    size = sum(f.stat().st_size for f in out.rglob("*") if f.is_file()) / 1e6
    print(f"site written to {out}  ({size:.0f} MB, {sum(len(c['videos']) for c in site['courses'])} videos, {len(cards)} flashcards, {sum(d.count('class="ex"') for d in drills)} drills)")


if __name__ == "__main__":
    main()
