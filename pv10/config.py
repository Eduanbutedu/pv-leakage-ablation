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
#   enkotu : DORT mudahale birden - eszaman + rastgele_kfold + gece +
#            OLCEKLEYICI. Asagidaki tanimda `olcekleyici_tum=True` de var.
#            Bu yorum satiri 8 Agustos 2026'ya kadar "eszaman +
#            rastgele_kfold + gece" diyordu; KOD dogruydu, YORUM eksikti.
#            Yanlis tanimlanmis bir varyanti raporlamak sizinti
#            makalesinde affedilmez, o yuzden kayda geciriliyor.
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

# ----------------------------------------------------------------------------
# DKASC replikasyon kolu (Alice Springs, GERCEK olcum)
#
# Butun esikler ve kararlar dokumanlar/dkasc-kalite-kurallari.md'de ON-KAYIT
# olarak duruyor; buradaki sayilar o belgenin makine tarafidir. Bir esigi
# degistirmeden once belgeyi okuyun - orada her birinin gozlemi, gerekcesi ve
# etkiledigi satir sayisi yazili.
# ----------------------------------------------------------------------------
DKASC_HAM = KOK / "ham" / "dkasc"
DKASC_VERI = KOK / "veri" / "dkasc_m6b.parquet"

# Dondurulmus DKASC surumu; `dkasc_pipeline.py duzenle` her kosuda bunu
# uretilen dosyanin hash'iyle kiyaslar ve uymazsa yuksek sesle soyler.
DKASC_VERI_SHA16 = "f7f644df5e0d1618"

DKASC_BASLANGIC_YIL, DKASC_BITIS_YIL = 2017, 2022
DKASC_TEST_YILLARI = (2018, 2019, 2020, 2021, 2022)  # 2017 yalnizca egitim

DKASC_KONUM = "dkasc_m6b"
# Koordinat DIS KAYNAKLA dogrulandi: 23 46' G / 133 52' D / 558 m,
# Theoretical and Applied Climatology (2022), doi:10.1007/s00704-022-04166-6.
# Ondalik karsiligi -23,7667 / 133,8667; asagidaki degerle fark enlemde
# 0,005 boylamda 0,007 derece - gunes geometrisinde ihmal edilebilir. Deger
# DEGISTIRILMEDI, cunku kesif sayilarinin tamami buna gore uretildi.
DKASC_LAT, DKASC_LON = -23.7621, 133.8744
DKASC_KOORDINAT_KAYNAK = ("Theoret. Appl. Climatol. (2022) "
                          "doi:10.1007/s00704-022-04166-6; 23 46' S, 133 52' E, 558 m")
DKASC_UTC_OFSET = 9.5          # ACST, yaz saati YOK
DKASC_KAPASITE_W = 5250.0      # M6_B = 5,25 kWp (PVGIS kolunda 1 kWp)

# Hedef dizi ve yedegi (karar 3). Yedek uretimde kullanilmaz; kalite
# kiyasi ve olasi bir yeniden secim icin adi burada durur.
DKASC_HEDEF_DIZI = "92_DKA_M6_B_Phase_Active_Power"     # sistem 13, Trina
DKASC_YEDEK_DIZI = "71_DKA_M2_C_Phase_Active_Power"     # sistem 18, SunPower

_W = "101_DKA_WeatherStation_"
DKASC_GHI = _W + "Global_Horizontal_Radiation"
DKASC_DHI = _W + "Diffuse_Horizontal_Radiation"
DKASC_GTI = _W + "Radiation_Global_Tilted"     # YALNIZCA kapi icin (karar 2)
DKASC_DTI = _W + "Radiation_Diffuse_Tilted"    # YALNIZCA kapi icin (karar 2)
DKASC_T = _W + "Weather_Temperature_Celsius"
DKASC_RH = _W + "Weather_Relative_Humidity"
DKASC_ISINIM_KANAL = (DKASC_GHI, DKASC_DHI, DKASC_GTI, DKASC_DTI)

DKASC_SUTUN_SAYISI = 197       # alti yilda da ayni ad, ayni sira
DKASC_YUVA_DK = 5
DKASC_SAAT_YUVA = 12           # kural 10: HEDEF ve DEGERLENDIRME icin 12/12

# Kural 10, yururlukteki hali: esik GIRDIDE gevser, HEDEF ve
# DEGERLENDIRMEDE siki kalir. Girdi olarak >=9/12 yuvasi dolu bir saatin
# kismi ortalamasi kullanilir (gercek olcum, ara deger DEGIL); o saat
# `kismi` bayragini alir ve ne egitim hedefi ne test gozlemi olur.
# Ayni desen gece satirlarinda kullaniliyor: filtre girdide degil ciktida.
# 9 secildi cunku 1/12 "ortalama" saatlik ortalama kiligina girmis bir
# nokta ornegidir; 9/12 saatin ucte dordudur. Olcum belgede.
DKASC_GIRDI_YUVA = 9

# Karar 5: 5 dk etiketi araligin BASI kabul edilir, temsil ettigi an
# etiket + 2,5 dk'dir. On iki yuvanin ortalamasi boylece HH:30 olur.
# Aralik SONU olcumle ELENDI; BASI ile ANLIK ornek ayrilamadi (bolum 4,
# madde 9) - bu sabit o varsayimi TEK YERDE tutar, degistirmek isteyen
# 0,0 yazar ve butun zincir birlikte kayar.
DKASC_ETIKET_ORTA_DK = 2.5

# --- kural esikleri (belge, bolum 1) ---
DKASC_RH_UST = 100.0           # kural 2: kirpma siniri
DKASC_RH_BAYRAK = 105.0        # kural 2: bayrak siniri
DKASC_DHI_ORAN_BAYRAK = 1.05   # kural 3
DKASC_GUC_OLU_BOLGE = 0.05     # kural 5: |P| <= 0,05 kW -> 0 (kW cinsinden)
DKASC_G0_CARPAN = 1.5          # kural 6: GHI > 1,5 x G0 -> eksik
DKASC_ARIZA_GHI = 200.0        # kural 7: GHI > 200 iken P == 0 -> ariza
DKASC_T_ALT, DKASC_T_UST = -10.0, 50.0   # kural 9: gecerli sicaklik araligi
DKASC_T_RAY = -39.0            # kural 9: analog ray; RH de bu satirlarda duser
DKASC_GUNES_SABITI = 1367.0    # G0 icin (kural 6)

# --- transpozisyon (karar 2 + karar 4) ---
DKASC_EGIM = 20.0              # dizi duzlemi: Tilt 20 / Azi 0 (Solar North)
DKASC_ALBEDO = 0.20            # olculmedi, varsayim (bolum 4, madde 11)
DKASC_RB_TABAN = 0.05          # Rb paydasi: max(sin h, taban)

# --- transpozisyon kapisi (karar 4) ---
# Esikler sonuc gorulmeden sabitlendi. Kapi olculen GTI'ye karsi kosar ve
# gecmezse pipeline DURUR. Negatif kontrol: egim 0 dereceye ZORLANDIGINDA
# kapi KIRMIZI yanmali (0 derecede RMSE %15,13, MBE -%5,99).
DKASC_KAPI_RMSE_YUZDE = 9.0
DKASC_KAPI_MBE_YUZDE = 2.0
DKASC_KAPI_EGIM_ARALIK = (11.0, 20.0)
DKASC_KAPI_SIN_H = 0.10        # dogrulama maskesi - alcak gunes OLCULMEDI
DKASC_KAPI_GHI = 20.0
DKASC_EGIM_TARAMA = (0.0, 36.0, 1.0)   # arange(bas, son, adim)

# --- oznitelik seti (karar 1: ruzgar YOK) ---
# GECIKMELI_DEGISKEN'in DKASC karsiligi. Beyan edilen bir deger olmasi
# kasitli: oznitelik seti kod yolunun yan etkisi degil, raporlanabilir bir
# sabittir. Eslesmis kontrol kosusunda (PVGIS verisi + bu set) da bu tuple
# kullanilir.
DKASC_GECIKMELI = ("P", "G_i", "T2m")
DKASC_ESZAMAN = ("G_i", "T2m")

# --- kesif sayimlari (belge, bolum 1) - uretimle KIYAS icin ---
# Kesif HAM veride, hicbir kural uygulanmadan, etiketin kendisinden hesaplanan
# gunes konumuyla sayildi. Uretim ise kurallari SIRAYLA uygular ve gunes
# konumunu etiket + 2,5 dk'dan hesaplar. Bu yuzden bazi sayilar birebir
# TUTMAZ; tutmamalari da beklenir ve sebebi her satirda yazilidir. Kiyas
# yine de yapilir: buyuk bir sapma kural sirasinin bozuldugunu gosterir.
DKASC_KESIF_SAYIM = {
    "k2_kirpilan": (5054, "birebir tutmali - kural 1 RH'ye dokunmaz"),
    "k2_bayrak": (5, "birebir tutmali"),
    "k3_duzeltilen": (6146, "DUSMELI - kural 1 gece GHI/DHI'yi sifirladi"),
    "k3_bayrak": (5134, "DUSMELI - ayni sebep"),
    "k6_eksige_cevrilen": (1126, "yakin - gece esigi ve 2,5 dk kaymasi"),
    "k9_t_eksige_cevrilen": (3046, "birebir tutmali - sicaklik kanali bagimsiz"),
    "k9_rh_eksige_cevrilen": (1649, "birebir tutmali"),
    "k5_negatif": (1825, "birebir tutmali - kural 5 oncesi ham sayim"),
}