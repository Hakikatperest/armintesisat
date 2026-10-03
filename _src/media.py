# -*- coding: utf-8 -*-
"""Görsel türevleri + favicon. Kaynak: _src/kaynak/ (orijinaller). Çıktı: images/, kökte favicon.
Çalıştır: python3 _src/media.py   (build.py'den önce, yalnızca görsel değişince)"""
import os
from PIL import Image, ImageDraw, ImageFont

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KAYNAK = os.path.join(KOK, "_src", "kaynak")
CIKTI = os.path.join(KOK, "images")

# kaynak dosya → yayın adı (eski "alya*" adları yayından kalktı)
GORSELLER = {
    "tesisat.jpg":  "su-tesisati-hizmeti",
    "elektrik.jpg": "elektrik-hizmeti",
    "petek.webp":   "petek-temizleme-hizmeti",
}
GENISLIK = (480, 960)

def turev():
    os.makedirs(CIKTI, exist_ok=True)
    for kaynak, ad in GORSELLER.items():
        im = Image.open(os.path.join(KAYNAK, kaynak)).convert("RGB")
        for g in GENISLIK:
            k = im.copy()
            if k.width > g:
                k = k.resize((g, round(k.height * g / k.width)), Image.LANCZOS)
            k.save(os.path.join(CIKTI, f"{ad}-{g}.webp"), "WEBP", quality=78, method=6)
            print(f"{ad}-{g}.webp", k.size)

def favicon():
    # Marka işareti: lacivert yuvarlak kare + beyaz "A" + mavi damla vurgusu.
    # ⚠️ WebP favicon Google'da görünmez → ico + png.
    S = 512
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, S - 1, S - 1), radius=112, fill=(11, 31, 64, 255))
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 360)
    kutu = d.textbbox((0, 0), "A", font=f)
    w, h = kutu[2] - kutu[0], kutu[3] - kutu[1]
    d.text(((S - w) / 2 - kutu[0], (S - h) / 2 - kutu[1] + 8), "A", font=f, fill=(255, 255, 255, 255))
    d.ellipse((350, 52, 450, 152), fill=(37, 99, 235, 255))
    im.resize((48, 48), Image.LANCZOS).save(os.path.join(KOK, "favicon.ico"), sizes=[(48, 48), (32, 32), (16, 16)])
    for b in (48, 96, 180, 192, 512):
        im.resize((b, b), Image.LANCZOS).save(os.path.join(CIKTI, f"favicon-{b}.png"), optimize=True)
    print("favicon tamam")

if __name__ == "__main__":
    turev()
    favicon()
