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

# Dondurulmus veri surumu: sha256(parquet baytlari)[:16], pvgis_pipeline.py
# ile ayni sekilde hesaplanir. Butun deney sonuclari BU surume bagli; ozet
# kunyesi calisilan dosyanin hash'ini buna karsi kontrol eder.
VERI_SHA16 = "f722a717bac502c2"

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

# ----------------------------------------------------------------------------
# Faz 4 - veri hacmi doygunlugu
#
# Egitim penceresi test yilindan GERIYE dogru sayilir. 10 yillik pencere
# uygulanabilir degil: bir test yili ayrildiginda geriye en fazla 9 yil kalir.
# "tum" = BASLANGIC_YIL'dan test yilina kadar her sey (5-9 yil arasi degisir).
#
# K=5 seviyesinin var olabilmesi icin test yili >= BASLANGIC_YIL + 5 olmali;
# test yili kumesi bu yuzden 2019'da basliyor.
# ----------------------------------------------------------------------------
EGITIM_PENCERELERI = (1, 2, 3, 5, "tum")
DOYGUNLUK_TEST_YILLARI = (2019, 2020, 2021, 2022, 2023)

# Iki kol:
#   kaydirmali   : test yilindan onceki son K yil (makalenin anlatisi)
#   altornekleme : TUM gecmisten, ayni satir sayisini tutturacak kadar
#                  gun-blogu cekilir. Yil kompozisyonunu sabit tutup yalnizca
#                  hacmi degistirir - "etki hacimden mi, yil cesitliliginden mi"
#                  sorusunu ayirir.
DOYGUNLUK_KOLLARI = ("kaydirmali", "altornekleme")

# Altornekleme kolu uc tohumla tekrarlanir. Tohum YALNIZCA hangi gunlerin
# cekildigini degistirir; model random_state'leri SEED'de sabit kalir. Ikisi
# birlikte oynatilirsa olculen sey ornekleme tesadufu ile model baslatma
# tesadufunun karisimi olur.
ORNEKLEME_TOHUMLARI = (11, 22, 33)
KAYDIRMALI_TOHUM = 0  # deterministik kol; loga 0 yazilir, NaN DEGIL - devam
                      # anahtarinda NaN != NaN yuzunden hucre asla eslesmezdi

# Genis kosu: yalnizca K=tum seviyesinde, 11 modelin tamami.
# SVR O(n^2) kernel ile 260-470 bin satirda pratikte imkansiz.
GENIS_KOSU_HARIC = ("Support Vector Regression",)

# HistGradientBoosting OpenMP kullanir; thread sayisi degisirse toplama sirasi
# degisir ve bit duzeyi tekrarlanabilirlik bozulur. Kosu basinda sabitlenir.
OMP_THREAD_SAYISI = 8

# Invaryant karsilastirmalarinda bagil tolerans. Bit duzeyi esitlik BEKLENMEZ
# (yukaridaki OpenMP notu); gercek fark her zaman tam hassasiyette loglanir.
INVARYANT_TOLERANS = 1e-6