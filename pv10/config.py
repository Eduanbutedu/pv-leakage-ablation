"""Merkezi konfigurasyon. Butun sabitler burada - hicbir sayi koda gomulmez."""

from __future__ import annotations

from pathlib import Path

SEED = 42  # makalede kullanilan tohum, degistirmeyin

# ----------------------------------------------------------------------------
# yollar
# ----------------------------------------------------------------------------
KOK = Path(__file__).resolve().parent.parent
VERI = KOK / "veri" / "pvgis_10yil.parquet"
SONUC = KOK / "sonuclar"
SONUC.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------
# veri kapsami
# ----------------------------------------------------------------------------
BASLANGIC_YIL, BITIS_YIL = 2014, 2023
KAPASITE_W = 1000.0  # 1 kWp -> kapasiteye gore nRMSE icin

# ----------------------------------------------------------------------------
# oznitelik tanimlari - GUFBD makalesiyle BIREBIR ayni tutulmali
# ----------------------------------------------------------------------------
UFUK = 24                      # tahmin ufku (saat)
GECIKMELER = (24, 48, 168)     # dinamik ozniteliklerin gecikmeleri
GECIKMELI_DEGISKEN = ("P", "G_i", "T2m", "WS10m")

# Yuvarlanan istatistikler; hepsi en az 24 saat kaydirilir
YUVARLANAN = {
    "P":   [("mean", 24), ("std", 24), ("mean", 168)],
    "G_i": [("mean", 24)],
}

# Berrak-gokyuzu performans orani icin geometrik payda: 1000 * sin(h_s)
BERRAK_GOK_KATSAYI = 1000.0

# ----------------------------------------------------------------------------
# sizinti varyantlari - Faz 2'nin ana deneyi
#   temiz  : makalenin tasarimi (referans)
#   eszaman: hedef saatteki meteoroloji de oznitelik olarak verilir
#   rastgele_kfold: kronolojik bolme yerine karistirmali k-fold
#   gece   : gece saatleri de degerlendirmeye dahil edilir
#   olcekleyici: standardizasyon/imputasyon tum veriye fit edilir
#   enkotu : eszaman + rastgele_kfold + gece birlikte
# ----------------------------------------------------------------------------
SIZINTI_VARYANTLARI = {
    "temiz":          dict(eszaman=False, rastgele_kfold=False, gece=False, olcekleyici_tum=False),
    "eszaman":        dict(eszaman=True,  rastgele_kfold=False, gece=False, olcekleyici_tum=False),
    "rastgele_kfold": dict(eszaman=False, rastgele_kfold=True,  gece=False, olcekleyici_tum=False),
    "gece":           dict(eszaman=False, rastgele_kfold=False, gece=True,  olcekleyici_tum=False),
    "olcekleyici":    dict(eszaman=False, rastgele_kfold=False, gece=False, olcekleyici_tum=True),
    "enkotu":         dict(eszaman=True,  rastgele_kfold=True,  gece=True,  olcekleyici_tum=True),
}

# Eszaman varyantinda eklenen sizdiran oznitelikler
ESZAMAN_DEGISKEN = ("G_i", "T2m", "WS10m")