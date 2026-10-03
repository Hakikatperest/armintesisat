# -*- coding: utf-8 -*-
"""
armintesisat.com statik site üreticisi.
  python3 _src/build.py && python3 _src/denetim.py
⛔ Üretilen HTML'i elle düzenleme; veri _src/data.py'de, şablon burada.

Yapı (kullanıcı kararı 2026-10-03):
  25 ilçe × 5 hizmet = 125 ilçe sayfası  (/<ilce>-<hizmet>/)
  6 hizmet sayfası (/<hizmet>/) · anasayfa · hizmet bölgeleri · iletişim · gizlilik · 404
  ⛔ "tesisat ustası" ve "gider açma" için AYRI sayfa yok — eş anlamlı, kannibalizasyon olur.
"""
import os, json, hashlib, html, re, shutil
from PIL import Image
import data as D

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = D.SITE
ALAN = S["alan"]
ILCE = {i["slug"]: i for i in D.ILCELER}
HIZ = {h["slug"]: h for h in D.HIZMETLER}
ILCE_HIZ = [h for h in D.HIZMETLER if h["ilce"]]
ONEK = ""   # sayfa derinliğine göre göreli yol öneki ("" kök, "../" alt klasör)

# ── yardımcılar ─────────────────────────────────────────────────────────────
def e(t): return html.escape(str(t), quote=True)

def ic(yol=""):
    """Site içi göreli bağlantı. yol: '' (anasayfa) ya da 'esenyurt-su-tesisatcisi/'."""
    return (ONEK + yol) if (ONEK + yol) else "./"

def ek(i, hal="loc"):
    sira = {"loc": 0, "dat": 1, "gen": 2, "abl": 3}[hal]
    return i["ad"] + D.ILCE_EK[i["slug"]][sira]

def tohum(*parca):
    return int(hashlib.md5("|".join(parca).encode()).hexdigest()[:8], 16)

def karistir(liste, *parca):
    t = tohum(*parca); l = list(liste); son = []
    while l:
        t = (t * 1103515245 + 12345) & 0x7FFFFFFF
        son.append(l.pop(t % len(l)))
    return son

def sec(liste, *parca): return liste[tohum(*parca) % len(liste)]

def surum(gorece):
    with open(os.path.join(KOK, gorece), "rb") as f:
        return gorece + "?v=" + hashlib.md5(f.read()).hexdigest()[:8]

def kucuk(s):
    return s.replace("I", "ı").replace("İ", "i").lower()

ALFABE = "abcçdefgğhıijklmnoöprsştuüvyz"
def tr_sira(i): return [ALFABE.index(c) if c in ALFABE else 99 for c in kucuk(i["ad"])]

def ilce_yolu(i, h): return f"{i['slug']}-{h['slug']}/"
def hiz_yolu(h): return f"{h['slug']}/"

def fmt(metin, i):
    return metin.format(ad=i["ad"], loc=D.ILCE_EK[i["slug"]][0] if i["slug"] in D.ILCE_EK else i.get("loc", ""))

AVRUPA = {"ad": "Avrupa yakası", "slug": "_avrupa", "loc": "nda"}

# ── ikonlar (satır içi SVG, üçüncü parti istek yok) ─────────────────────────
IK = {
 "tel": '<path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1z"/>',
 "wa": '<path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2c-1.5 0-3-.4-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.3-.4.7-1.4.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.4.1-.7.3-.2.3-.9.9-.9 2.2s.9 2.5 1 2.7c.1.2 1.8 2.8 4.4 3.9 1.6.7 2.3.8 3.1.6.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.2-1.2-.1-.1-.3-.2-.5-.3z"/>',
 "saat": '<path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm0 18a8 8 0 1 1 0-16 8 8 0 0 1 0 16zm.5-13H11v6l5.2 3.2.8-1.3-4.5-2.7z"/>',
 "konum": '<path d="M12 2a7 7 0 0 0-7 7c0 5.3 7 13 7 13s7-7.7 7-13a7 7 0 0 0-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z"/>',
 "kalkan": '<path d="M12 2 4 5v6c0 5 3.4 9.7 8 11 4.6-1.3 8-6 8-11V5l-8-3zm-1.2 14.2-3.5-3.5 1.4-1.4 2.1 2.1 4.9-4.9 1.4 1.4-6.3 6.3z"/>',
 "hiz": '<path d="M13 2 3 14h7l-1 8 10-12h-7l1-8z"/>',
 "damla": '<path d="M12 2.7S5 10.4 5 15a7 7 0 0 0 14 0c0-4.6-7-12.3-7-12.3z"/>',
 "anahtar": '<path d="M22.7 19 13.6 9.9c.9-2.3.4-5-1.5-6.9-2-2-5-2.4-7.4-1.3L9 6 6 9 1.6 4.7C.4 7.1.9 10.1 2.9 12.1c1.9 1.9 4.6 2.4 6.9 1.5l9.1 9.1c.4.4 1 .4 1.4 0l2.3-2.3c.5-.4.5-1.1.1-1.4z"/>',
 "isi": '<path d="M15 13V5a3 3 0 0 0-6 0v8a5 5 0 1 0 6 0zm-3 7a3 3 0 0 1-1.5-5.6l.5-.3V5a1 1 0 0 1 2 0v9.1l.5.3A3 3 0 0 1 12 20z"/>',
 "kombi": '<path d="M6 2h12a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-1v2h-2v-2H9v2H7v-2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm0 2v14h12V4H6zm2 2h8v4H8V6zm1 7h2v2H9v-2zm4 0h2v2h-2v-2z"/>',
 "sim": '<path d="M7 2v11h3v9l7-12h-4l4-8H7z"/>',
 "tik": '<path d="M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4z"/>',
 "ok": '<path d="M12 4l-1.4 1.4 5.6 5.6H4v2h12.2l-5.6 5.6L12 20l8-8z"/>',
 "menu": '<path d="M3 6h18v2H3zm0 5h18v2H3zm0 5h18v2H3z"/>',
 "kapat": '<path d="M19 6.4 17.6 5 12 10.6 6.4 5 5 6.4 10.6 12 5 17.6 6.4 19 12 13.4 17.6 19 19 17.6 13.4 12z"/>',
 "uyari": '<path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>',
}
HIZ_IKON = {"su-tesisatcisi": "anahtar", "tikaniklik-acma": "damla", "su-kacagi-tespiti": "hiz",
            "petek-temizleme": "isi", "kombi-servisi": "kombi", "elektrikci": "sim"}

def svg(ad, sinif="ik"):
    return f'<svg class="{sinif}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{IK[ad]}</svg>'

# ── görsel ──────────────────────────────────────────────────────────────────
GORSEL = {"tesisat": "su-tesisati-hizmeti", "petek": "petek-temizleme-hizmeti", "elektrik": "elektrik-hizmeti"}

def gorsel(anahtar, alt, sinif="", oncelik=False, boy="(min-width:980px) 520px, 100vw"):
    taban = GORSEL[anahtar]; parcalar = []; olcu = None
    for g in (480, 960):
        yol = f"images/{taban}-{g}.webp"
        w, h = Image.open(os.path.join(KOK, yol)).size
        parcalar.append(f"{ic(yol)} {w}w"); olcu = (w, h)
    yukle = 'fetchpriority="high"' if oncelik else 'loading="lazy" decoding="async"'
    return (f'<img class="{sinif}" src="{ic(f"images/{taban}-960.webp")}" srcset="{", ".join(parcalar)}" '
            f'sizes="{boy}" width="{olcu[0]}" height="{olcu[1]}" alt="{e(alt)}" {yukle}>')

# ── düğmeler ────────────────────────────────────────────────────────────────
def tel_btn(metin=None, sinif="dg dg-mavi"):
    metin = metin or f"Hemen Ara: {S['tel_goster']}"
    return f'<a class="{sinif}" href="tel:{S["tel_link"]}">{svg("tel")}<span>{e(metin)}</span></a>'

def wa_btn(mesaj, metin="WhatsApp'tan Yaz", sinif="dg dg-yesil"):
    from urllib.parse import quote
    return (f'<a class="{sinif}" href="https://wa.me/{S["wa"]}?text={quote(mesaj)}" target="_blank" '
            f'rel="noopener">{svg("wa")}<span>{e(metin)}</span></a>')

def wa_mesaj(h=None, i=None):
    if h and i: return f"Merhaba, {i['ad']} için {kucuk(h['kisa'])} hizmeti almak istiyorum."
    if h: return f"Merhaba, {kucuk(h['kisa'])} hizmeti almak istiyorum."
    return "Merhaba, Armin Tesisat hizmeti almak istiyorum."

# ── iskelet ─────────────────────────────────────────────────────────────────
def ads_head():
    a = D.ADS
    if not a["etiket"]: return ""
    ayar = json.dumps({"etiket": a["etiket"], "tel": a["tel"], "wa": a["wa"]})
    return (f'<script async src="https://www.googletagmanager.com/gtag/js?id={a["etiket"]}"></script>\n'
            "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
            "gtag('js',new Date());" + "".join(f"gtag('config','{k}');" for k in [a["etiket"], *a.get("ek", [])])
            + f"window.W4_ADS={ayar};</script>\n")

def head(baslik, aciklama, yol, sema=None, robots="index,follow"):
    kanonik = ALAN + "/" + yol
    ld = "".join(f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>\n'
                 for s in (sema or []))
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{ads_head()}<title>{e(baslik)}</title>
<meta name="description" content="{e(aciklama)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{kanonik}">
<meta property="og:type" content="website">
<meta property="og:locale" content="tr_TR">
<meta property="og:site_name" content="{e(S['marka'])}">
<meta property="og:title" content="{e(baslik)}">
<meta property="og:description" content="{e(aciklama)}">
<meta property="og:url" content="{kanonik}">
<meta property="og:image" content="{ALAN}/images/su-tesisati-hizmeti-960.webp">
<meta name="theme-color" content="#0B1F40">
<link rel="icon" href="{ic('favicon.ico')}" sizes="48x48">
<link rel="icon" type="image/png" sizes="192x192" href="{ic('images/favicon-192.png')}">
<link rel="apple-touch-icon" href="{ic('images/favicon-180.png')}">
<link rel="preload" href="{ic('assets/fonts/pjs-var-tr.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{ic(surum('assets/css/site.css'))}">
{ld}</head>
<body>
<a class="atla" href="#icerik">İçeriğe geç</a>
"""

def logo():
    return (f'<a class="logo" href="{ic()}" aria-label="{e(S["marka"])} anasayfa">'
            f'<img src="{ic("images/favicon-96.png")}" width="40" height="40" alt="">'
            f'<span class="logo-ad">Armin<b>Tesisat</b></span></a>')

def ust(aktif=""):
    oge = []
    for h in D.HIZMETLER:
        cls = ' class="aktif"' if aktif == h["slug"] else ""
        oge.append(f'<a{cls} href="{ic(hiz_yolu(h))}">{svg(HIZ_IKON[h["slug"]])}{e(h["ad"])}</a>')
    return f"""<header class="ust">
 <div class="kap ust-ic">
  {logo()}
  <nav class="menu" id="menu" aria-label="Ana menü">
   <div class="menu-grup"><span class="menu-baslik">Hizmetler</span><div class="menu-alt">{''.join(oge)}</div></div>
   <a href="{ic('hizmet-bolgeleri/')}"{' class="aktif"' if aktif=='bolge' else ''}>Hizmet Bölgeleri</a>
   <a href="{ic('iletisim/')}"{' class="aktif"' if aktif=='iletisim' else ''}>İletişim</a>
  </nav>
  <div class="ust-sag">
   {tel_btn(S['tel_goster'], 'dg dg-mavi dg-ust')}
   <button class="menu-ac" type="button" aria-controls="menu" aria-expanded="false" aria-label="Menüyü aç">{svg('menu')}</button>
  </div>
 </div>
</header>
<main id="icerik">
"""

def kirinti(parcalar):
    li, ld = [], []
    for n, (ad, yol) in enumerate(parcalar, 1):
        if yol is None:
            li.append(f'<li aria-current="page">{e(ad)}</li>')
            ld.append({"@type": "ListItem", "position": n, "name": ad})
        else:
            li.append(f'<li><a href="{ic(yol)}">{e(ad)}</a></li>')
            ld.append({"@type": "ListItem", "position": n, "name": ad, "item": ALAN + "/" + yol})
    return (f'<nav class="kirinti" aria-label="Sayfa yolu"><ol>{"".join(li)}</ol></nav>',
            {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": ld})

def w4_imza():
    return ('<div class="w4"><div class="w4-bag"><span class="w4-etiket">Web Tasarım:</span>'
            '<a class="w4-ad" href="https://www.web4medya.com/" target="_blank" rel="noopener">'
            'Web<span class="w4-d">4</span>Medya</a></div></div>')

def alt():
    hiz = "".join(f'<li><a href="{ic(hiz_yolu(h))}">{e(h["ad"])}</a></li>' for h in D.HIZMETLER)
    ilc = "".join(f'<li><a href="{ic(ilce_yolu(i, HIZ["su-tesisatcisi"]))}">{e(i["ad"])}</a></li>'
                  for i in sorted(D.ILCELER, key=tr_sira))
    return f"""</main>
<footer class="alt">
 <div class="kap alt-izgara">
  <div class="alt-marka">
   {logo()}
   <p>İstanbul Avrupa yakasının 25 ilçesinde su tesisatı, tıkanıklık ve gider açma, su kaçağı tespiti, petek temizleme, kombi servisi ve elektrik işleri. 7/24 hizmet.</p>
   <p class="alt-tel">{svg('tel')}<a href="tel:{S['tel_link']}">{S['tel_goster']}</a></p>
   <p class="alt-tel">{svg('saat')}<span>7 gün 24 saat</span></p>
  </div>
  <div><h2 class="alt-b">Hizmetler</h2><ul class="alt-liste">{hiz}<li><a href="{ic('hizmet-bolgeleri/')}">Tüm hizmet bölgeleri</a></li></ul></div>
  <div class="alt-ilce"><h2 class="alt-b">Hizmet Bölgeleri</h2><ul class="alt-liste alt-liste-2">{ilc}</ul></div>
 </div>
 <div class="kap alt-son">
  <p>© {S['kurulus']}–2026 {e(S['marka'])} · <a href="{ic('gizlilik-politikasi/')}">Gizlilik Politikası</a> · <a href="{ic('iletisim/')}">İletişim</a></p>
 </div>
 {w4_imza()}
</footer>
<div class="dock" id="dock">
 {tel_btn('Hemen Ara', 'dg dg-mavi')}
 {wa_btn(wa_mesaj(), 'WhatsApp')}
</div>
<script src="{ic(surum('assets/js/app.js'))}" defer></script>
</body>
</html>
"""

# ── şema ────────────────────────────────────────────────────────────────────
def isletme():
    return {"@type": "Plumber", "@id": ALAN + "/#isletme", "name": S["marka"], "url": ALAN + "/",
            "telephone": S["tel_link"], "image": ALAN + "/images/su-tesisati-hizmeti-960.webp",
            "logo": ALAN + "/images/favicon-512.png",
            "openingHoursSpecification": {"@type": "OpeningHoursSpecification",
                "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
                "opens": "00:00", "closes": "23:59"},
            "areaServed": [{"@type": "City", "name": f"{i['ad']}, İstanbul"} for i in D.ILCELER]}

def sema_isletme(): return {"@context": "https://schema.org", **isletme()}

def sema_hizmet(h, i=None):
    yer = {"@type": "City", "name": f"{i['ad']}, İstanbul"} if i else \
          {"@type": "AdministrativeArea", "name": "İstanbul Avrupa Yakası"}
    return {"@context": "https://schema.org", "@type": "Service",
            "name": (h["h1"].format(ad=i["ad"]) if i else h["ad"]), "serviceType": h["ad"],
            "provider": {"@type": "Plumber", "@id": ALAN + "/#isletme", "name": S["marka"], "telephone": S["tel_link"]},
            "areaServed": yer, "url": ALAN + "/" + (ilce_yolu(i, h) if i else hiz_yolu(h))}

def sema_sss(sorular):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": s, "acceptedAnswer": {"@type": "Answer", "text": c}} for s, c in sorular]}

# ── ortak bloklar ───────────────────────────────────────────────────────────
def guven():
    oge = [("saat", "7/24 hizmet", "Gece, hafta sonu ve bayramda da arayabilirsiniz."),
           ("hiz", "Ortalama 30 dakika", "Ekiplerimiz Avrupa yakasında adrese ortalama 30 dakikada ulaşıyor."),
           ("konum", "25 ilçe", "Avrupa yakasının tüm ilçelerine servis veriyoruz."),
           ("kalkan", "Fiyat işten önce", "Usta yerinde baktıktan sonra, işe başlamadan fiyatı söylüyor.")]
    return '<ul class="guven">' + "".join(
        f'<li>{svg(i)}<div><b>{e(b)}</b><span>{e(m)}</span></div></li>' for i, b, m in oge) + "</ul>"

def sss_html(sorular, baslik="Sık Sorulan Sorular"):
    oge = "".join(f'<details class="sss-oge"><summary>{e(s)}</summary><p>{e(c)}</p></details>' for s, c in sorular)
    return f'<section class="blok" id="sss"><h2>{e(baslik)}</h2><div class="sss">{oge}</div></section>'

def cta(baslik, metin, h=None, i=None):
    return f"""<section class="cta"><div class="kap cta-ic">
 <div><h2>{e(baslik)}</h2><p>{e(metin)}</p></div>
 <div class="cta-dg">{tel_btn()}{wa_btn(wa_mesaj(h, i))}</div>
</div></section>"""

def kart_hizmet(h, i=None):
    yol = ilce_yolu(i, h) if i else hiz_yolu(h)
    ad = h["h1"].format(ad=i["ad"]) if i else h["ad"]
    return (f'<a class="hkart" href="{ic(yol)}"><span class="hkart-ik">{svg(HIZ_IKON[h["slug"]])}</span>'
            f'<b>{e(ad)}</b><span>{e(h["ozet"])}</span><em>Ayrıntılar {svg("ok")}</em></a>')

# ── ilçe × hizmet sayfası ───────────────────────────────────────────────────
GIRIS = [
 "{ad}{loc} {kisa} için 7/24 hizmet veriyoruz. {ozet} Ekiplerimiz adrese ortalama 30 dakikada ulaşıyor.",
 "{ozet} {ad}{loc} gece ya da gündüz fark etmeden arayabilirsiniz; ekiplerimiz ortalama 30 dakikada yanınızda.",
 "{ad} ve çevresinde {kisa} işleri için 7/24 ulaşabileceğiniz bir ekibiz. {ozet}",
]
BOLGE_H2 = [
 "{ad}{loc} {kisa}: bölgenin binalarını tanıyoruz",
 "{ad}{loc} {kisa} işlerinde neye dikkat ediyoruz?",
 "{ad}{abl} gelen çağrılarda en sık ne görüyoruz?",
]
ISLER_H2 = {
 "su-tesisatcisi":    "{ad} tesisat ustası olarak yaptığımız işler",
 "tikaniklik-acma":   "{ad} gider açma ve tıkanıklık açma işleri",
 "su-kacagi-tespiti": "{ad}{loc} kırmadan su kaçağı tespiti: yaptığımız işler",
 "petek-temizleme":   "{ad}{loc} petek temizliği kapsamı",
 "kombi-servisi":     "{ad} kombi tamiri ve bakımı: yaptığımız işler",
}
KOPRU = {
 "su-tesisatcisi":    "Bu yüzden {ad}{loc} tesisatçı olarak gittiğimiz adreste önce ana vanayı ve görünen bağlantıları kontrol ediyor, sorunu yalnızca o noktada değil hattın geri kalanında da değerlendiriyoruz.",
 "tikaniklik-acma":   "{ad}{loc} gider açmaya gittiğimizde önce tıkanıklığın daire içinde mi yoksa bina ortak hattında mı olduğunu ayırıyor, buna göre yöntem seçiyoruz.",
 "su-kacagi-tespiti": "{ad}{loc} su kaçağı tespitinde önce tesisatı bölümlere ayırıp basınç testi yapıyor, kaçağın hangi hatta olduğunu belirledikten sonra cihazla noktayı daraltıyoruz.",
 "petek-temizleme":   "{ad}{loc} petek temizliğine gitmeden önce sistemin kombili mi merkezi mi olduğunu, kaç petek bulunduğunu telefonda soruyoruz; böylece doğru ekipmanla geliyoruz.",
 "kombi-servisi":     "{ad}{loc} kombi servisine çıkmadan önce kombinin marka-modelini ve ekrandaki hata kodunu soruyoruz; çoğu zaman gereken parçayı yanımızda getirebiliyoruz.",
}
GENEL_H2 = [
 "{ad}{gen} binalarında tesisatın genel durumu",
 "{ad}{loc} tesisat: bilmenizde fayda olanlar",
 "{ad} ve mahalleleri hakkında",
]
MAHALLE = [
 "[MAH] başta olmak üzere {ad}{gen} tüm mahallelerine {kisa} için geliyoruz. Aramada mahalle ve sokak adını söylemeniz ekibi doğru yönlendirmemizi kolaylaştırıyor.",
 "{ad}{loc} [MAH] mahallelerinden sık çağrı alıyoruz; listede olmayan mahalleler için de aynı şekilde geliyoruz.",
 "Hizmet verdiğimiz {ad} mahallelerinden bazıları: [MAH]. Adres tarifini telefonda netleştirip ekibi en kısa güzergâhtan gönderiyoruz.",
]
SSS_H2 = ["{ad} {kisa} hakkında sık sorulanlar", "{ad}{loc} {kisa}: sorular ve cevaplar", "Sık sorulan sorular"]

def yer(metin, i, h):
    loc, dat, gen, abl = D.ILCE_EK[i["slug"]]
    return metin.format(ad=i["ad"], loc=loc, dat=dat, gen=gen, abl=abl,
                        kisa=kucuk(h["kisa"]), ozet=h["ozet"])

def baglanti_agi(i, h):
    """Örümcek ağı: aynı ilçede diğer 4 hizmet + komşu ilçelerde aynı hizmet + dönüşümlü 3 uzak ilçe."""
    ayni = [x for x in ILCE_HIZ if x["slug"] != h["slug"]]
    a1 = "".join(f'<li><a href="{ic(ilce_yolu(i, x))}">{e(x["h1"].format(ad=i["ad"]))}</a></li>' for x in ayni)
    komsu = [ILCE[k] for k in i["komsu"]]
    a2 = "".join(f'<li><a href="{ic(ilce_yolu(k, h))}">{e(h["h1"].format(ad=k["ad"]))}</a></li>' for k in komsu)
    disari = [x for x in D.ILCELER if x["slug"] != i["slug"] and x["slug"] not in i["komsu"]]
    uzak = karistir(disari, i["slug"], h["slug"], "uzak")[:3]
    a3 = "".join(f'<li><a href="{ic(ilce_yolu(k, h))}">{e(k["ad"])}</a></li>' for k in uzak)
    return f"""<section class="blok ag">
 <div class="ag-kol"><h2>{e(ek(i))} diğer hizmetlerimiz</h2><ul class="ag-liste">{a1}</ul></div>
 <div class="ag-kol"><h2>Yakın ilçelerde {e(kucuk(h['kisa']))}</h2><ul class="ag-liste">{a2}</ul>
  <p class="ag-not">Diğer bölgeler: <span class="ag-satir">{a3.replace('<li>','').replace('</li>',' · ').rstrip(' · ')}</span> · <a href="{ic(hiz_yolu(h))}">tüm ilçeler</a></p></div>
</section>"""

def ilce_sayfasi(i, h):
    yol = ilce_yolu(i, h)
    H1 = h["h1"].format(ad=i["ad"])
    giris = yer(sec(GIRIS, i["slug"], h["slug"], "giris"), i, h)
    bolge_p = [i["yapi"]] + [i[a] for a in h["alan"] if a != "yapi"] + [yer(KOPRU[h["slug"]], i, h), i["saha"]]
    belirti = karistir(h["belirti"], i["slug"], h["slug"], "b")[:4]
    isler = karistir(h["isler"], i["slug"], h["slug"], "i")[:4]
    oneri = karistir(h["oneri"], i["slug"], h["slug"], "o")[:2]
    diger_alan = [a for a in ("boru", "gider", "isinma") if a not in h["alan"]]
    genel_p = [i[a] for a in karistir(diger_alan, i["slug"], h["slug"], "g")[:2]]
    mah_p = yer(sec(MAHALLE, i["slug"], h["slug"], "m"), i, h).replace("[MAH]", ", ".join(i["mahalle"][:-1]) + " ve " + i["mahalle"][-1])
    sss_tum = [(yer(s, i, h), c) for s, c in h["sss"]]
    sss = [sss_tum[0]] + karistir(sss_tum[1:], i["slug"], h["slug"], "s")[:3]
    kir_html, kir_ld = kirinti([("Anasayfa", ""), (h["ad"], hiz_yolu(h)), (i["ad"], None)])
    baslik = h["title"].format(ad=i["ad"])
    aciklama = (f"{i['ad']} {kucuk(h['kisa'])}: {h['ozet']} 7/24 hizmet, ortalama 30 dakikada adreste. "
                f"Hemen arayın: {S['tel_goster']}")
    kombi_not = ""
    if h["slug"] == "kombi-servisi":
        kombi_not = ('<p class="not">' + svg("uyari") + '<span>Armin Tesisat herhangi bir kombi markasının yetkili servisi '
                     'değildir; farklı marka ve modellerde bağımsız servis olarak hizmet verir. Gaz kokusunda önce '
                     '<a href="tel:187">187 Doğalgaz Acil</a>\'i arayın.</span></p>')
    sema = [sema_hizmet(h, i), sema_sss(sss), kir_ld]
    return head(baslik, aciklama, yol, sema) + ust(h["slug"]) + f"""
<section class="hero hero-ic"><div class="kap hero-izgara">
 <div class="hero-metin">
  {kir_html}
  <p class="ust-etiket">{svg('konum')} {e(i['ad'])}, İstanbul Avrupa Yakası</p>
  <h1>{e(H1)}</h1>
  <p class="hero-p">{e(giris)}</p>
  <div class="hero-dg">{tel_btn()}{wa_btn(wa_mesaj(h, i))}</div>
 </div>
 <figure class="hero-gorsel">{gorsel(h['gorsel'], H1, oncelik=True)}</figure>
</div></section>
<div class="kap">{guven()}</div>
<div class="kap govde">
 <section class="blok">
  <h2>{e(yer(sec(BOLGE_H2, i['slug'], h['slug'], 'h2'), i, h))}</h2>
  {''.join(f'<p>{e(x)}</p>' for x in bolge_p)}
  {kombi_not}
 </section>
 <section class="blok">
  <h2>{e(yer('Hangi durumlarda {kisa} için aramalısınız?', i, h))}</h2>
  <ul class="tik-liste">{''.join(f'<li>{svg("tik")}<span>{e(b)}</span></li>' for b in belirti)}</ul>
 </section>
 <section class="blok">
  <h2>{e(yer(ISLER_H2[h['slug']], i, h))}</h2>
  <div class="is-izgara">{''.join(f'<div class="is"><h3>{e(a)}</h3><p>{e(m)}</p></div>' for a, m in isler)}</div>
 </section>
 <section class="blok kutu-acik">
  <h2>Usta gelene kadar ne yapabilirsiniz?</h2>
  <ol class="adim-liste">{''.join(f'<li>{e(o)}</li>' for o in oneri)}</ol>
 </section>
 <section class="blok">
  <h2>{e(yer(sec(GENEL_H2, i['slug'], h['slug'], 'gh'), i, h))}</h2>
  {''.join(f'<p>{e(x)}</p>' for x in genel_p)}
  <p>{e(mah_p)}</p>
 </section>
 {sss_html(sss, yer(sec(SSS_H2, i['slug'], h['slug'], 'sss'), i, h))}
 {baglanti_agi(i, h)}
</div>
{cta(f"{i['ad']} için usta mı lazım?", "7/24 arayabilir ya da WhatsApp'tan yazabilirsiniz.", h, i)}
""" + alt()

# ── hizmet sayfası ──────────────────────────────────────────────────────────
def hizmet_sayfasi(h):
    yol = hiz_yolu(h)
    sss = [(s.format(ad="Avrupa yakası", loc="nda"), c) for s, c in h["sss"]]
    kir_html, kir_ld = kirinti([("Anasayfa", ""), (h["ad"], None)])
    baslik = h["title"].format(ad="İstanbul Avrupa Yakası") if "{ad}" in h["title"] else h["title"]
    H1 = h["h1"].format(ad="İstanbul Avrupa Yakası") if "{ad}" in h["h1"] else h["h1"]
    aciklama = f"{h['ad']}: {h['ozet']} İstanbul Avrupa yakasında 7/24 hizmet. {S['tel_goster']}"
    ilce_bolum = ""
    if h["ilce"]:
        oge = "".join(f'<li><a href="{ic(ilce_yolu(i, h))}">{e(i["ad"])} {e(kucuk(h["kisa"]))}</a></li>'
                      for i in sorted(D.ILCELER, key=tr_sira))
        ilce_bolum = f'<section class="blok"><h2>İlçeye göre {e(kucuk(h["kisa"]))}</h2><ul class="ilce-izgara">{oge}</ul></section>'
    else:
        ilce_bolum = ('<section class="blok"><h2>Hizmet bölgesi</h2><p>Elektrik işleri için Avrupa yakasının 25 ilçesinin '
                      f'tamamına geliyoruz. İlçe listesini <a href="{ic("hizmet-bolgeleri/")}">hizmet bölgeleri</a> sayfasında görebilirsiniz.</p></section>')
    kombi_not = ""
    if h["slug"] == "kombi-servisi":
        kombi_not = ('<p class="not">' + svg("uyari") + '<span>Armin Tesisat herhangi bir kombi markasının yetkili servisi '
                     'değildir; farklı marka ve modellerde bağımsız servis olarak hizmet verir. Gaz kokusunda önce '
                     '<a href="tel:187">187 Doğalgaz Acil</a>\'i arayın.</span></p>')
    diger = "".join(kart_hizmet(x) for x in D.HIZMETLER if x["slug"] != h["slug"])
    sema = [sema_hizmet(h), sema_sss(sss), kir_ld]
    return head(baslik, aciklama, yol, sema) + ust(h["slug"]) + f"""
<section class="hero hero-ic"><div class="kap hero-izgara">
 <div class="hero-metin">
  {kir_html}
  <p class="ust-etiket">{svg('konum')} İstanbul Avrupa Yakası · 25 ilçe</p>
  <h1>{e(H1)}</h1>
  <p class="hero-p">{e(h['ozet'])} 7/24 hizmet veriyoruz; ekiplerimiz adrese ortalama 30 dakikada ulaşıyor.</p>
  <div class="hero-dg">{tel_btn()}{wa_btn(wa_mesaj(h))}</div>
 </div>
 <figure class="hero-gorsel">{gorsel(h['gorsel'], h['ad'], oncelik=True)}</figure>
</div></section>
<div class="kap">{guven()}</div>
<div class="kap govde">
 {kombi_not}
 <section class="blok"><h2>Neler yapıyoruz?</h2>
  <div class="is-izgara">{''.join(f'<div class="is"><h3>{e(a)}</h3><p>{e(m)}</p></div>' for a, m in h['isler'])}</div></section>
 <section class="blok"><h2>Hangi durumlarda aramalısınız?</h2>
  <ul class="tik-liste">{''.join(f'<li>{svg("tik")}<span>{e(b)}</span></li>' for b in h['belirti'])}</ul></section>
 <section class="blok kutu-acik"><h2>Usta gelene kadar ne yapabilirsiniz?</h2>
  <ol class="adim-liste">{''.join(f'<li>{e(o)}</li>' for o in h['oneri'])}</ol></section>
 {ilce_bolum}
 {sss_html(sss)}
 <section class="blok"><h2>Diğer hizmetlerimiz</h2><div class="hkart-izgara">{diger}</div></section>
</div>
{cta(f"{h['ad']} için hemen ulaşın", "7/24 arayabilir ya da WhatsApp'tan yazabilirsiniz.", h)}
""" + alt()

# ── anasayfa ────────────────────────────────────────────────────────────────
ANA_SSS = [
 ("Hangi ilçelere hizmet veriyorsunuz?", "İstanbul Avrupa yakasının 25 ilçesinin tamamına geliyoruz: " + ", ".join(i["ad"] for i in D.ILCELER) + "."),
 ("Gece ya da hafta sonu ulaşabilir miyim?", "Evet. 7 gün 24 saat hizmet veriyoruz; telefonla arayabilir ya da WhatsApp'tan yazabilirsiniz."),
 ("Usta ne kadar sürede gelir?", "Ekiplerimiz Avrupa yakasında adrese ortalama 30 dakikada ulaşıyor. Trafik ve iş yoğunluğuna göre süre değişebilir; arama sırasında size tahmini süreyi söylüyoruz."),
 ("Fiyatı ne zaman öğrenirim?", "Fotoğraf ya da videoyla yaklaşık bilgi verebiliyoruz. Kesin fiyatı usta yerinde baktıktan sonra, işe başlamadan önce söylüyor."),
 ("Kombi markalarının yetkili servisi misiniz?", "Hayır. Herhangi bir kombi markasının yetkili servisi değiliz; farklı marka ve modellerde bağımsız servis olarak arıza tespiti, bakım ve onarım yapıyoruz."),
]

def anasayfa():
    kartlar = "".join(kart_hizmet(h) for h in D.HIZMETLER)
    ilceler = []
    for i in sorted(D.ILCELER, key=tr_sira):
        l = "".join(f'<a href="{ic(ilce_yolu(i, h))}">{e(h["kisa"])}</a>' for h in ILCE_HIZ)
        ilceler.append(f'<details class="ilce-kart"><summary>{svg("konum")}{e(i["ad"])}</summary><div>{l}</div></details>')
    sema = [sema_isletme(), sema_sss(ANA_SSS)]
    return head("Armin Tesisat | Su Tesisatçısı, Tıkanıklık Açma · Avrupa Yakası",
                "İstanbul Avrupa yakasının 25 ilçesinde su tesisatçısı, tıkanıklık ve gider açma, su kaçağı tespiti, "
                f"petek temizleme ve kombi servisi. 7/24 hizmet, ortalama 30 dakikada adreste. {S['tel_goster']}",
                "", sema) + ust() + f"""
<section class="hero hero-ana"><div class="kap hero-izgara">
 <div class="hero-metin">
  <p class="ust-etiket">{svg('konum')} İstanbul Avrupa Yakası · 25 ilçe · 7/24</p>
  <h1>Su Tesisatçısı, Tıkanıklık Açma ve Kombi Servisi</h1>
  <p class="hero-p">Boru patlağından tıkalı gidere, görünmeyen su kaçağından ısınmayan peteğe kadar evinizdeki tesisat işleri için 7 gün 24 saat ulaşabileceğiniz ekibiz. Ekiplerimiz Avrupa yakasında adrese ortalama 30 dakikada ulaşıyor.</p>
  <div class="hero-dg">{tel_btn()}{wa_btn(wa_mesaj())}</div>
 </div>
 <figure class="hero-gorsel">{gorsel('tesisat', 'Armin Tesisat su tesisatı hizmeti', oncelik=True)}</figure>
</div></section>
<div class="kap">{guven()}</div>
<div class="kap govde">
 <section class="blok"><h2>Hizmetlerimiz</h2>
  <p class="blok-giris">Her hizmetin ilçenize özel sayfasında, o bölgenin binalarında en sık karşılaştığımız durumları da anlattık.</p>
  <div class="hkart-izgara">{kartlar}</div></section>
 <section class="blok" id="bolgeler"><h2>Hizmet verdiğimiz ilçeler</h2>
  <p class="blok-giris">İlçenizi seçin, ihtiyacınız olan hizmetin sayfasına gidin. Tüm liste için <a href="{ic('hizmet-bolgeleri/')}">hizmet bölgeleri</a> sayfasına bakabilirsiniz.</p>
  <div class="ilce-kartlar">{''.join(ilceler)}</div></section>
 <section class="blok"><h2>Nasıl çalışıyoruz?</h2>
  <ol class="surec">
   <li><b>Arayın ya da yazın</b><span>Sorunu anlatın; mümkünse WhatsApp'tan fotoğraf gönderin.</span></li>
   <li><b>Ekip yola çıksın</b><span>Adresinize en yakın ekibi yönlendiriyoruz.</span></li>
   <li><b>Yerinde tespit</b><span>Usta sorunu yerinde görüyor, fiyatı işe başlamadan söylüyor.</span></li>
   <li><b>Onarım ve kontrol</b><span>İş bittikten sonra birlikte kontrol ediyor, ortamı temiz bırakıyoruz.</span></li>
  </ol></section>
 {sss_html(ANA_SSS)}
</div>
{cta("Tesisatta acil bir sorun mu var?", "7/24 arayabilir ya da WhatsApp'tan yazabilirsiniz.")}
""" + alt()

# ── diğer sayfalar ──────────────────────────────────────────────────────────
def basit(baslik, aciklama, yol, h1, govde, aktif="", robots="index,follow", kirinti_ad=None):
    kir_html, kir_ld = kirinti([("Anasayfa", ""), (kirinti_ad or h1, None)])
    return head(baslik, aciklama, yol, [kir_ld], robots) + ust(aktif) + f"""
<section class="hero hero-ic hero-dar"><div class="kap"><div class="hero-metin">{kir_html}<h1>{e(h1)}</h1></div></div></section>
<div class="kap govde">{govde}</div>
""" + alt()

def bolgeler():
    satir = []
    for i in sorted(D.ILCELER, key=tr_sira):
        l = "".join(f'<li><a href="{ic(ilce_yolu(i, h))}">{e(h["h1"].format(ad=i["ad"]))}</a></li>' for h in ILCE_HIZ)
        satir.append(f'<section class="bolge"><h2>{e(i["ad"])}</h2><ul>{l}</ul></section>')
    govde = (f'<p class="blok-giris">İstanbul Avrupa yakasının 25 ilçesinin tamamına 7/24 servis veriyoruz. '
             f'Elektrik işleri için <a href="{ic("elektrikci/")}">elektrikçi</a> sayfasına bakabilirsiniz.</p>'
             f'<div class="bolge-izgara">{"".join(satir)}</div>')
    return basit("Hizmet Bölgeleri | Armin Tesisat · İstanbul Avrupa Yakası 25 İlçe",
                 "Armin Tesisat'ın hizmet verdiği İstanbul Avrupa yakası ilçeleri: su tesisatçısı, tıkanıklık açma, "
                 "su kaçağı tespiti, petek temizleme ve kombi servisi.", "hizmet-bolgeleri/", "Hizmet Bölgeleri", govde, "bolge")

def iletisim():
    govde = f"""<section class="blok iletisim">
 <div class="ilt-kart">{svg('tel')}<div><h2>Telefon</h2><p><a href="tel:{S['tel_link']}">{S['tel_goster']}</a></p></div></div>
 <div class="ilt-kart">{svg('wa')}<div><h2>WhatsApp</h2><p>Fotoğraf ya da video göndererek sorunu anlatabilirsiniz.</p>{wa_btn(wa_mesaj())}</div></div>
 <div class="ilt-kart">{svg('saat')}<div><h2>Çalışma saatleri</h2><p>7 gün 24 saat</p></div></div>
 <div class="ilt-kart">{svg('konum')}<div><h2>Hizmet bölgesi</h2><p>İstanbul Avrupa yakasının 25 ilçesi. <a href="{ic('hizmet-bolgeleri/')}">İlçe listesi</a></p></div></div>
</section>"""
    return basit("İletişim | Armin Tesisat · 0532 247 21 59", "Armin Tesisat iletişim: 0532 247 21 59, WhatsApp, 7/24 hizmet. "
                 "İstanbul Avrupa yakası 25 ilçe.", "iletisim/", "İletişim", govde, "iletisim")

def gizlilik():
    p = lambda *x: "".join(f"<p>{e(t)}</p>" for t in x)
    govde = f"""<section class="blok metin">
<h2>Kişisel veriler</h2>{p("Bu site üzerinden form doldurulmaz ve kişisel veri toplanmaz. Bizi telefonla aradığınızda ya da WhatsApp'tan yazdığınızda paylaştığınız ad, telefon numarası ve adres bilgisi yalnızca talep ettiğiniz hizmeti vermek amacıyla kullanılır ve üçüncü kişilerle paylaşılmaz.")}
<h2>Çerezler ve reklam ölçümü</h2>{p("Reklamlarımızın sonuç verip vermediğini ölçmek için Google Ads dönüşüm etiketi kullanılır. Bu etiket, siteye hangi reklamdan geldiğinizi ve arama ya da WhatsApp düğmesine tıklayıp tıklamadığınızı anonim olarak Google'a bildirir. Tarayıcı ayarlarınızdan çerezleri silebilir ya da engelleyebilirsiniz; Google'ın reklam ayarlarını adssettings.google.com adresinden yönetebilirsiniz.")}
<h2>Haklarınız</h2>{p("6698 sayılı Kişisel Verilerin Korunması Kanunu kapsamındaki haklarınızla ilgili talepleriniz için " + S["tel_goster"] + " numarasından bize ulaşabilirsiniz.")}
</section>"""
    return basit("Gizlilik Politikası | Armin Tesisat", "Armin Tesisat gizlilik politikası, çerez ve reklam ölçümü bilgilendirmesi.",
                 "gizlilik-politikasi/", "Gizlilik Politikası", govde)

def hata404():
    global ONEK
    eski = ONEK; ONEK = "/"
    govde = (f'<section class="blok"><p>Aradığınız sayfa bulunamadı. <a href="/">Anasayfaya</a> ya da '
             f'<a href="/hizmet-bolgeleri/">hizmet bölgelerine</a> göz atabilirsiniz.</p></section>')
    s = basit("Sayfa bulunamadı | Armin Tesisat", "Aradığınız sayfa bulunamadı.", "404.html", "Sayfa bulunamadı",
              govde, robots="noindex,follow")
    ONEK = eski
    return s

# ── yazma ───────────────────────────────────────────────────────────────────
def yaz(yol, icerik):
    hedef = os.path.join(KOK, yol, "index.html") if yol.endswith("/") or yol == "" else os.path.join(KOK, yol)
    os.makedirs(os.path.dirname(hedef), exist_ok=True)
    with open(hedef, "w", encoding="utf-8") as f: f.write(icerik)

def sayfa(yol, uretici, *arg):
    global ONEK
    ONEK = "../" * yol.count("/")
    yaz(yol, uretici(*arg))
    return yol

def temizle():
    """Önceki üretimden kalan, artık üretilmeyen sayfa klasörlerini sil (yalnızca index.html içerenler)."""
    korunan = {"assets", "images", "_src", ".git"}
    for ad in os.listdir(KOK):
        tam = os.path.join(KOK, ad)
        if os.path.isdir(tam) and ad not in korunan and os.path.isfile(os.path.join(tam, "index.html")):
            shutil.rmtree(tam)

def main():
    temizle()
    yollar = [sayfa("", anasayfa)]
    for h in D.HIZMETLER: yollar.append(sayfa(hiz_yolu(h), hizmet_sayfasi, h))
    for h in ILCE_HIZ:
        for i in D.ILCELER: yollar.append(sayfa(ilce_yolu(i, h), ilce_sayfasi, i, h))
    yollar += [sayfa("hizmet-bolgeleri/", bolgeler), sayfa("iletisim/", iletisim),
               sayfa("gizlilik-politikasi/", gizlilik)]
    global ONEK; ONEK = "/"
    yaz("404.html", hata404())
    sm = "".join(f"<url><loc>{ALAN}/{y}</loc></url>" for y in yollar if y != "gizlilik-politikasi/")
    yaz("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n')
    yaz("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {ALAN}/sitemap.xml\n")
    yaz("CNAME", S["cname"] + "\n")
    print(f"{len(yollar)} sayfa üretildi")

if __name__ == "__main__":
    main()
