#!/usr/bin/env python3
"""scene_kit.py – generators for the recurring scene types, so projects stay consistent and cheap to author.

    from scene_kit import example_scene, bridge_scene, recap_scene

* example_scene  – "Alltags-Analogie | Beispiel | Eselsbrücke" teaching scene.
      narration cues expected in script.md:  [ana] [b1] [b2] … [merk]
* bridge_scene   – "where are we" opener for part N of M (roadmap chips + running-case reminder + recap of before).
      cues: [w1] [w2]
* recap_scene    – take-away cards (+ optional mnemonic chips).  cues: [r1]…[rN] [m] [ende]
All return the HTML fragment (string) for scenes/NN-id.html.  See references/storyboard-guide.md.
"""
import html as _h

L = {"de": dict(ana="Alltags-Analogie", merk="Eselsbrücke", merks="Eselsbrücken", case="Beispiel", takeaway="Merke", part="Teil", of="von", before="Bisher", companion="Unser Begleiter"),
     "en": dict(ana="Everyday analogy", merk="Mnemonic", merks="Mnemonics", case="Example", takeaway="Takeaways", part="Part", of="of", before="So far", companion="Our running example")}


def _e(s):
    return s  # fragments may contain inline html (<b>, &shy;) on purpose


def example_scene(sid, part, kick, title, analogy, example, mnemonic, case_label=None, lang="en"):
    """analogy={'emoji','title','text'}  example={'title'?,'bullets':[..]}  mnemonic={'phrase','sub'?,'tiles':[(letter,word),..]?}"""
    lb = L.get(lang, L["en"]); case_label = case_label or lb["case"]
    bl = example["bullets"]
    fs, mb = {1: (32, 18), 2: (32, 18), 3: (30, 16), 4: (29, 14)}.get(len(bl), (27, 11))   # shrink with more bullets
    bullets = "".join(
        f'<li style="font-size:{fs}px;margin-bottom:{mb}px" data-at="b{i+1}" data-fx="rise">{_e(b)}</li>' for i, b in enumerate(bl))
    tiles = ""
    if mnemonic.get("tiles"):
        n = len(mnemonic["tiles"])
        tiles = '<div class="row" style="gap:14px;margin-top:14px">' + "".join(
            f'<div class="card center" style="--k:var(--a);width:{int((1664-14*(n-1))/n)}px;height:86px;flex-direction:row;gap:12px;padding:6px 14px" data-at="merk+{0.5+0.45*i:.2f}" data-fx="pop">'
            f'<span style="font-size:46px;font-weight:800;color:var(--a)">{l}</span><span style="font-size:24px;line-height:1.1">{w}</span></div>'
            for i, (l, w) in enumerate(mnemonic["tiles"])) + "</div>"
    sub = f'<div class="mute" style="font-size:27px;margin-top:8px" data-at="merk+0.3" data-fx="fade">{mnemonic["sub"]}</div>' if mnemonic.get("sub") else ""
    return f'''<section class="scene" data-scene="{sid}" data-part="{part}">
  <div class="head">
    <span class="kick" data-at="@start+0.2" data-fx="pop">{kick}</span>
    <h2 data-at="@start+0.3" data-fx="rise">{title}</h2>
  </div>
  <div class="body">
    <div class="card ce abs" style="left:0;top:0;width:600px;height:450px;padding:22px 28px" data-at="ana" data-fx="rise">
      <span class="chip ce fill" style="font-size:22px;padding:2px 14px">{lb["ana"]}</span>
      <div style="font-size:104px;line-height:1.1;margin:8px 0 2px" data-at="ana+0.4" data-fx="pop">{analogy["emoji"]}</div>
      <h3 style="font-size:36px;margin-bottom:6px">{analogy["title"]}</h3>
      <p style="font-size:26px;line-height:1.25">{analogy["text"]}</p>
    </div>
    <div class="card cb abs" style="left:632px;top:0;width:1096px;height:450px;padding:22px 32px" data-at="b1-0.4" data-fx="rise">
      <span class="chip cb fill" style="font-size:22px;padding:2px 14px">{case_label}</span>
      {('<div style="font-size:34px;font-weight:700;margin:12px 0 14px">' + example["title"] + '</div>') if example.get("title") else '<div style="height:14px"></div>'}
      <ul class="pts" style="--k:var(--b)">{bullets}</ul>
    </div>
    <div class="card ca abs" style="left:0;top:480px;width:1728px;height:{290 if tiles else 230}px;padding:20px 32px" data-at="merk" data-fx="rise">
      <span class="chip ca fill" style="font-size:22px;padding:2px 14px">{lb["merk"]}</span>
      <div style="font-size:54px;font-weight:800;line-height:1.1;margin-top:10px;color:var(--a)" data-at="merk+0.1" data-fx="rise">{mnemonic["phrase"]}</div>
      {sub}{tiles}
    </div>
  </div>
</section>
'''


def bridge_scene(sid, n, total, parts, before, case, part="Part 1", lang="en", case_title="Running example"):
    """parts = list of (title, sub) for all parts, n = current (1-based)"""
    lb = L.get(lang, L["en"])
    chips = "".join(
        f'<div class="card {"ca" if i+1==n else ""}" style="{"" if i+1==n else "opacity:.55;"}padding:12px 24px;font-size:27px;display:flex;gap:18px;align-items:center" data-at="w1+{0.35*i:.2f}" data-fx="left">'
        f'<span style="font-weight:800;color:var(--a);font-size:34px">{i+1}</span><span><b>{t}</b><br><span class="mute" style="font-size:22px">{s}</span></span></div>'
        for i, (t, s) in enumerate(parts))
    return f'''<section class="scene" data-scene="{sid}" data-part="{part}">
  <div class="head">
    <span class="kick" data-at="@start+0.2" data-fx="pop">{lb["part"]} {n} {lb["of"]} {total}</span>
    <h2 data-at="@start+0.3" data-fx="rise">{parts[n-1][0]}</h2>
  </div>
  <div class="body">
    <div class="col abs" style="left:0;top:0;width:900px;gap:14px">{chips}</div>
    <div class="card cb abs" style="left:960px;top:0;width:768px;height:330px;padding:22px 28px" data-at="w1+1" data-fx="rise">
      <h3 style="font-size:34px">{lb["before"]}</h3><p style="font-size:28px">{before}</p></div>
    <div class="card ce abs" style="left:960px;top:360px;width:768px;height:330px;padding:22px 28px" data-at="w2" data-fx="rise">
      <span class="chip ce fill" style="font-size:22px;padding:2px 14px">{lb["companion"]}</span>
      <h3 style="font-size:34px;margin-top:12px">{case_title}</h3><p style="font-size:27px">{case}</p></div>
  </div>
</section>
'''


def recap_scene(sid, part, title, cards, mnemonics=None, end_text=None, lang="en"):
    """cards=[(color_class, heading, [bullets])]  mnemonics=[str]"""
    lb = L.get(lang, L["en"])
    n = len(cards); w = int((1728 - 24 * (n - 1)) / n)
    cmap = {"cc": "c", "ca": "a", "cb": "b", "cd": "d", "ce": "e", "cok": "ok"}
    cs = "".join(
        f'<div class="card {c} abs" style="left:{i*(w+24)}px;top:0;width:{w}px;height:320px;padding:22px 28px" data-at="r{i+1}" data-fx="rise"><h3>{h}</h3>'
        f'<ul class="pts" style="--k:var(--{cmap[c]})">' + "".join(f'<li style="font-size:28px;margin-bottom:14px">{b}</li>' for b in bl) + "</ul></div>"
        for i, (c, h, bl) in enumerate(cards))
    ms = ""
    if mnemonics:
        ms = ('<div class="abs" style="left:0;top:360px;width:1728px" data-at="m" data-fx="rise"><span class="chip ca fill" style="font-size:22px;padding:2px 14px">' + lb["merks"] + '</span>'
              '<div class="row" style="flex-wrap:wrap;gap:12px;margin-top:12px">' + "".join(f'<span class="chip ca" style="font-size:28px">{m}</span>' for m in mnemonics) + "</div></div>")
    end = f'<div class="abs center" style="left:0;top:600px;width:1728px" data-at="ende" data-fx="pop"><span class="chip cb fill" style="font-size:32px;padding:10px 32px">{end_text}</span></div>' if end_text else ""
    return f'''<section class="scene" data-scene="{sid}" data-part="{part}">
  <div class="head"><span class="kick" data-at="@start+0.2" data-fx="pop">{lb["takeaway"]}</span><h2 data-at="@start+0.3" data-fx="rise">{title}</h2></div>
  <div class="body">
{cs}
{ms}
{end}
  </div>
</section>
'''
