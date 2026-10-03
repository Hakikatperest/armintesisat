# -*- coding: utf-8 -*-
"""Yayın öncesi denetim. Hata varsa 1 döner — commit ETME.
  python3 _src/denetim.py"""
import os, re, json, html, sys, itertools
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data as D

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
hata, uyari = [], []

sayfalar = {}
for kok, _, dosyalar in os.walk(KOK):
    if any(x in kok for x in ("/.git", "/_src", "/assets", "/images")): continue
    for d in dosyalar:
        if d.endswith(".html"):
            tam = os.path.join(kok, d)
            sayfalar[os.path.relpath(tam, KOK)] = open(tam, encoding="utf-8").read()

def govde_metni(s):
    m = re.search(r'<main id="icerik">(.*)</main>', s, re.S)
    b = m.group(1) if m else s
    b = re.sub(r"<script.*?</script>", " ", b, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", b))).strip()

basliklar, aciklamalar, gelen = defaultdict(list), defaultdict(list), defaultdict(set)
for yol, s in sayfalar.items():
    t = re.search(r"<title>(.*?)</title>", s); a = re.search(r'<meta name="description" content="(.*?)"', s)
    if not t: hata.append(f"{yol}: title yok"); continue
    baslik = html.unescape(t.group(1)); basliklar[baslik].append(yol)
    if a: aciklamalar[html.unescape(a.group(1))].append(yol)
    if len(baslik) > 70: uyari.append(f"{yol}: title {len(baslik)} krk")
    if s.count("<h1") != 1: hata.append(f"{yol}: h1 sayısı {s.count('<h1')}")
    if re.search(r"\{[a-z_]+\}", s): hata.append(f"{yol}: doldurulmamış şablon alanı")
    metin = govde_metni(s).lower() + " " + baslik.lower()
    for x in D.TEYITSIZ:
        if x.lower() in metin: hata.append(f"{yol}: teyitsiz iddia '{x}'")
    for x in D.YASAK_IDDIA:
        if re.search(r"(?<![a-zçğıöşü])" + re.escape(x) + r"(?![a-zçğıöşü])", metin): hata.append(f"{yol}: yasak iddia '{x}'")
    # iç bağlantılar
    for href in re.findall(r'href="([^"#]+)', s):
        if href.startswith(("http", "tel:", "mailto:")): continue
        h = href.split("?")[0]
        if yol == "404.html":
            hedef = h.lstrip("/")
        else:
            hedef = os.path.normpath(os.path.join(os.path.dirname(yol), h))
        hedef_dosya = os.path.join(KOK, hedef)
        if os.path.isdir(hedef_dosya) or h.endswith("/") or h in ("./", ""):
            hedef_dosya = os.path.join(hedef_dosya, "index.html")
        if not os.path.exists(hedef_dosya):
            hata.append(f"{yol}: kırık bağlantı {href}")
        elif hedef_dosya.endswith("index.html"):
            gelen[os.path.relpath(hedef_dosya, KOK)].add(yol)
    # SSS görünen metin = şema
    gorunen = [(html.unescape(q), html.unescape(c)) for q, c in
               re.findall(r'<summary>(.*?)</summary><p>(.*?)</p>', s)]
    for ld in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        j = json.loads(ld)
        if j.get("@type") == "FAQPage":
            sema = [(q["name"], q["acceptedAnswer"]["text"]) for q in j["mainEntity"]]
            if sema != gorunen: hata.append(f"{yol}: FAQPage şeması görünen SSS ile aynı değil")

for b, y in basliklar.items():
    if len(y) > 1: hata.append(f"tekrarlanan title '{b}': {y}")
for a, y in aciklamalar.items():
    if len(y) > 1: hata.append(f"tekrarlanan description: {y}")

# örümcek ağı: her ilçe sayfasına en az 6 farklı sayfadan bağlantı gelmeli
for yol in sayfalar:
    if yol in ("index.html", "404.html"): continue
    n = len(gelen[yol] - {yol})
    if n < 6: uyari.append(f"{yol}: yalnızca {n} sayfadan iç bağlantı alıyor")

# benzerlik: aynı hizmetin ilçe sayfaları arasında 5'li kelime kümesi örtüşmesi
def kume(s):
    k = govde_metni(s).lower().split()
    return {" ".join(k[i:i+5]) for i in range(len(k) - 4)}
grup = defaultdict(list)
for yol, s in sayfalar.items():
    m = re.match(r"([a-z]+)-(su-tesisatcisi|tikaniklik-acma|su-kacagi-tespiti|petek-temizleme|kombi-servisi)/", yol)
    if m: grup[m.group(2)].append((yol, kume(s)))
for hiz, liste in grup.items():
    oranlar = [len(a & b) / len(a | b) for (_, a), (_, b) in itertools.combinations(liste, 2)]
    print(f"benzerlik {hiz:18s} ort %{100*sum(oranlar)/len(oranlar):.0f}  en yüksek %{100*max(oranlar):.0f}")

kelime = [len(govde_metni(s).split()) for y, s in sayfalar.items() if re.match(r"[a-z]+-(su|tik|pet|kom)", y)]
print(f"ilçe sayfası gövde kelime: en az {min(kelime)}, ort {sum(kelime)//len(kelime)}, en çok {max(kelime)}")
for u in uyari[:30]: print("UYARI", u)
if len(uyari) > 30: print(f"... +{len(uyari)-30} uyarı")
for h in hata[:50]: print("HATA ", h)
print(f"{len(sayfalar)} sayfa · {len(hata)} hata · {len(uyari)} uyarı")
sys.exit(1 if hata else 0)
