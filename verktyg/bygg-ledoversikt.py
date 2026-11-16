#!/usr/bin/env python3
"""Bygger översiktssidan leder/index.html.

Kör från repots rot:  python3 verktyg/bygg-ledoversikt.py [sökväg till StegAppens trails.json]

- "Leder med egen sida": alla mappar leder/<slug>/index.html (namn, område och längd läses från sidan).
- "Alla leder i appen": de inbyggda lederna i StegAppen (src/data/trails.json), grupperade per område.
  En inbyggd led som har en egen sida länkas automatiskt.
Kör om skriptet varje gång en ny ledsida läggs till.
"""
import glob, html, json, os, re, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAILS = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/Projects/StegAppen/src/data/trails.json')
SITE = 'https://stegappen.se'
AREA_ORDER = ['Stockholm', 'Huddinge', 'Göteborg', 'Figeholm', 'Abisko']
AREA_TEXT = {
    'Stockholm': 'Upplandsleden, Roslagsleden, Sörmlandsleden, Värmdöleden och fler leder runt huvudstaden.',
    'Huddinge': 'Huddingeleden i sju etapper och leder genom skog och naturreservat söder om Stockholm.',
    'Göteborg': 'Bohusleden, Vildmarksleden och Gotaleden – från Skatås ut i skogarna öster om stan.',
    'Figeholm': 'Ostkustleden längs kusten i Småland.',
    'Abisko': 'Kungsleden etapp för etapp från Abisko och söderut genom fjällen.',
}


def slug(name):
    s = name.lower().replace('å', 'a').replace('ä', 'a').replace('ö', 'o').replace('é', 'e')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def km(v):
    return (f'{v:.1f}'.rstrip('0').rstrip('.') if isinstance(v, float) else str(v)).replace('.', ',')


def page_info(path):
    s = open(path, encoding='utf-8').read()
    name = html.unescape(re.sub('<[^>]+>', '', re.search(r'<h1[^>]*>(.*?)</h1>', s, re.S).group(1))).strip()
    title = html.unescape(re.search(r'<title>(.*?)</title>', s, re.S).group(1))
    m = re.search(r'([\d,]+)\s*km vandringsled i ([^|]+)', title)
    return {'name': name, 'km': m.group(1) if m else '', 'area': m.group(2).strip() if m else ''}


pages = {}
for p in sorted(glob.glob(os.path.join(ROOT, 'leder', '*', 'index.html'))):
    pages[os.path.basename(os.path.dirname(p))] = page_info(p)

trails = json.load(open(TRAILS, encoding='utf-8'))['trails']
by_area = {}
for t in trails:
    by_area.setdefault(t['area'], []).append(t)
areas = [a for a in AREA_ORDER if a in by_area] + sorted(a for a in by_area if a not in AREA_ORDER)

e = html.escape
own = '\n'.join(
    f'''        <a class="trail-card" href="/leder/{s}/"><b>{e(i['name'])}</b><span>{e(i['km'])} km · {e(i['area'])}</span><i>Karta, start och tips →</i></a>'''
    for s, i in pages.items())

sections = []
for a in areas:
    rows = []
    for t in sorted(by_area[a], key=lambda t: (t.get('group') or t['name'], t.get('stage') or 0, t['name'])):
        sg = slug(t['name'])
        label = e(t['name'])
        name = f'<a href="/leder/{sg}/">{label}</a>' if sg in pages else label
        rows.append(f'          <li>{name}<small>{km(t["distanceKm"])} km</small></li>')
    sections.append(f'''      <section class="area" id="{slug(a)}">
        <h2>{e(a)} <span>{len(by_area[a])} leder</span></h2>
        <p>{e(AREA_TEXT.get(a, ''))}</p>
        <ul class="list">
{chr(10).join(rows)}
        </ul>
      </section>''')

chips = '\n'.join(f'        <a href="#{slug(a)}">{e(a)} <b>{len(by_area[a])}</b></a>' for a in areas)
n = len(trails)
ld = [
    {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': 'Vandringsleder i StegAppen',
     'url': f'{SITE}/leder/', 'inLanguage': 'sv',
     'description': f'{n} vandringsleder i StegAppen – från Kungsleden i Abisko till Bohusleden, Sörmlandsleden och Huddingeleden.',
     'mainEntity': {'@type': 'ItemList', 'itemListElement': [
         {'@type': 'ListItem', 'position': i + 1, 'name': inf['name'], 'url': f'{SITE}/leder/{s}/'}
         for i, (s, inf) in enumerate(pages.items())]}},
    {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'StegAppen', 'item': f'{SITE}/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'Leder', 'item': f'{SITE}/leder/'}]},
]

out = f'''<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vandringsleder – {n} leder med karta och etapper | StegAppen</title>
<meta name="description" content="Hitta din nästa vandring: {n} vandringsleder i StegAppen, från Kungsleden i Abisko till Bohusleden, Sörmlandsleden, Upplandsleden och Huddingeleden. Se längd, karta och etapper.">
<meta name="keywords" content="vandringsleder, vandring Stockholm, vandring Göteborg, Kungsleden etapper, Bohusleden, Sörmlandsleden, Upplandsleden, Huddingeleden, Ostkustleden">
<meta name="theme-color" content="#2F7D4F">
<meta name="color-scheme" content="light only">
<link rel="canonical" href="{SITE}/leder/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="StegAppen">
<meta property="og:title" content="Vandringsleder i StegAppen – {n} leder">
<meta property="og:description" content="Från Kungsleden till Bohusleden och Sörmlandsleden. Se längd, karta och etapper.">
<meta property="og:url" content="{SITE}/leder/">
<meta property="og:locale" content="sv_SE">
<meta property="og:image" content="{SITE}/img/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/icon.png">
<link rel="apple-touch-icon" href="/icon.png">
<script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False, indent=1)}
</script>
<style>
  :root {{
    --bg: #F4F6F1; --surface: #FFFFFF; --text: #1E2A22; --muted: #5F6E64; --line: #E3E8E0;
    --green: #2F7D4F; --green-soft: #DCEFE2; --orange: #E08A2C; --orange-soft: #FBEBD6;
  }}
  * {{ box-sizing: border-box; }}
  html {{ -webkit-text-size-adjust: 100%; scroll-behavior: smooth; }}
  body {{ margin: 0; background: var(--bg); color: var(--text); font: 17px/1.55 -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif; overflow-x: hidden; }}
  a {{ color: var(--green); }}
  .wrap {{ max-width: 1000px; margin: 0 auto; padding: 0 16px; }}
  .brand .s {{ color: var(--green); }} .brand .a {{ color: var(--orange); }}
  header.top {{ position: sticky; top: 0; z-index: 10; background: color-mix(in srgb, var(--bg) 88%, transparent); backdrop-filter: saturate(1.4) blur(12px); -webkit-backdrop-filter: saturate(1.4) blur(12px); border-bottom: 1px solid var(--line); }}
  header.top .wrap {{ display: flex; align-items: center; gap: 10px; height: 60px; }}
  header.top img {{ width: 34px; height: 34px; border-radius: 9px; background: #fff; }}
  header.top .brand {{ font-weight: 700; font-size: 20px; letter-spacing: -.2px; text-decoration: none; display: flex; align-items: center; gap: 10px; }}
  header.top nav {{ margin-left: auto; }}
  .btn {{ display: inline-flex; align-items: center; justify-content: center; background: var(--green); color: #fff; text-decoration: none; font-weight: 600; padding: 9px 16px; border-radius: 11px; font-size: 15px; }}
  .crumbs {{ font-size: 14px; color: var(--muted); margin: 22px 0 10px; }}
  .crumbs a {{ color: var(--muted); text-decoration: none; }}
  h1 {{ font-size: clamp(32px, 6vw, 48px); line-height: 1.08; letter-spacing: -1px; margin: 0 0 12px; }}
  .lead {{ font-size: 19px; color: var(--muted); margin: 0 0 22px; max-width: 40em; }}
  .chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 34px; }}
  .chips a {{ background: var(--surface); border: 1px solid var(--line); border-radius: 999px; padding: 8px 14px; font-size: 15px; font-weight: 600; text-decoration: none; color: var(--text); }}
  .chips a b {{ color: var(--green); margin-left: 4px; }}
  h2 {{ font-size: 26px; letter-spacing: -.4px; margin: 0 0 6px; }}
  h2 span {{ font-size: 15px; font-weight: 600; color: var(--muted); letter-spacing: 0; margin-left: 6px; }}
  .own {{ margin: 0 0 40px; }}
  .own-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; margin-top: 12px; }}
  .trail-card {{ display: flex; flex-direction: column; gap: 2px; background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 16px 18px; text-decoration: none; color: var(--text); box-shadow: 0 1px 2px rgba(30,42,34,.06), 0 8px 24px rgba(30,42,34,.06); }}
  .trail-card span {{ color: var(--muted); font-size: 15px; }}
  .trail-card i {{ font-style: normal; color: var(--green); font-weight: 600; font-size: 15px; margin-top: 6px; }}
  .area {{ margin: 0 0 34px; scroll-margin-top: 76px; }}
  .area > p {{ color: var(--muted); margin: 0 0 12px; }}
  .list {{ list-style: none; margin: 0; padding: 0; background: var(--surface); border: 1px solid var(--line); border-radius: 16px; columns: 2; column-gap: 0; }}
  @media (max-width: 680px) {{ .list {{ columns: 1; }} }}
  .list li {{ display: flex; justify-content: space-between; gap: 12px; padding: 10px 16px; border-bottom: 1px solid var(--line); break-inside: avoid; font-size: 15px; }}
  .list small {{ color: var(--muted); white-space: nowrap; font-size: 14px; }}
  .more {{ background: var(--green); color: #fff; border-radius: 24px; padding: 28px 22px; margin: 10px 0 30px; }}
  .more h2 {{ color: #fff; }}
  .more p {{ margin: 0 0 16px; opacity: .94; }}
  .more a {{ display: inline-block; background: #fff; color: #2F7D4F; font-weight: 700; padding: 13px 22px; border-radius: 14px; text-decoration: none; }}
  footer {{ padding: 32px 0 44px; color: var(--muted); font-size: 14px; border-top: 1px solid var(--line); }}
  footer .wrap {{ display: flex; flex-wrap: wrap; gap: 12px; justify-content: space-between; }}
</style>
</head>
<body>
<header class="top">
  <div class="wrap">
    <a class="brand" href="/"><img src="/icon.png" alt=""><span><span class="s">Steg</span><span class="a">Appen</span></span></a>
    <nav><a class="btn" href="/#kom-igang">Kom igång</a></nav>
  </div>
</header>

<main>
  <div class="wrap">
    <div class="crumbs"><a href="/">StegAppen</a> › Leder</div>
    <h1>Vandringsleder</h1>
    <p class="lead">{n} leder finns inbyggda i StegAppen – från Kungsleden i Abisko till Bohusleden, Sörmlandsleden och Huddingeleden. Starta en vandring i appen när du går – appen känner igen leden själv och bockar av den automatiskt.</p>
    <nav class="chips" aria-label="Områden">
{chips}
    </nav>

    <section class="own">
      <h2>Leder med egen sida</h2>
      <p style="color:var(--muted);margin:0">Karta, start, längd, tid och tips inför turen. Fler sidor kommer.</p>
      <div class="own-grid">
{own}
      </div>
    </section>

{chr(10).join(sections)}

    <section class="more">
      <h2>Hundratals leder till i appen</h2>
      <p>Utöver lederna ovan hittar du hundratals leder runt om i Sverige direkt i appen – sorterade efter var du är.</p>
      <a href="/#kom-igang">Testa StegAppen gratis</a>
    </section>
  </div>
</main>

<footer>
  <div class="wrap">
    <span class="brand"><b><span class="s">Steg</span><span class="a">Appen</span></b> – gå mer, tillsammans.</span>
    <span><a href="/">Startsidan</a> · <a href="/integritet/">Integritetspolicy</a> · Leddata © OpenStreetMap-bidragsgivare</span>
  </div>
</footer>
</body>
</html>
'''
open(os.path.join(ROOT, 'leder', 'index.html'), 'w', encoding='utf-8').write(out)
print(f'leder/index.html: {n} inbyggda leder i {len(areas)} områden, {len(pages)} egna sidor')
