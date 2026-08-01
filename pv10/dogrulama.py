"""Faz 4 deney invaryantlari - ana izgaradan ONCE kosulan kapi.

pvgis_pipeline.py'deki dogrula_* fonksiyonlari VERIYI dogrular (yil araligi,
satir sayisi, bosluk). Buradakiler DENEY KURGUSUNU dogrular: pencere
aritmetigi, isinma siniri, ornekleme kod yolu ve Faz 2 ile geriye donuk
uyumluluk.

Besi de basarisiz olabilecek gercek seyleri test eder, tautoloji degildir:
beklenen degerler ablasyon.csv'den ve elle yapilan takvim aritmetiginden
gelir, uretilen koddan turetilmez. Bolmeyi olcen invaryantlar URETIM
fonksiyonlarini (hucre_kos, egitim_test_bolme) cagirir; kendi kopyalarini
tasimazlar. Invaryant 5 ayrica kasten yanlis bir referans uretip kendi
ayirt etme gucunu olcer - yakalayamazsa KENDISI kalir.

Tolerans BAGIL 1e-6. Bit duzeyi esitlik beklenmez: HistGradientBoosting
OpenMP kullanir, thread sayisi degisirse toplama sirasi degisir. Gercek fark
her zaman tam hassasiyette raporlanir.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import (BASLANGIC_YIL, INVARYANT_TOLERANS, KAYDIRMALI_TOHUM,
                     ORNEKLEME_TOHUMLARI, SONUC)
from .doygunluk import (PencereOnbellegi, egitim_test_bolme, hucre_kos,
                        pencere_basi)
from .features import oznitelik_uret
from .models import HIZLI_ALTKUME
from .ornekleme import hedef_satir_sayisi

ABLASYON = SONUC / "ablasyon.csv"

# --- ablasyon.csv'den okunan referanslar; literaller bagimsiz kontrol -------
# Bu sayilar Faz 2'nin 'temiz' varyantindan gelir. Dosya yeniden uretilir de
# degerler kayarsa once BU esitsizlik patlar, sessizce yeni referansa
# gecilmez.
REFERANS_RMSE = {
    2019: {"Linear Regression": 141.343658,
           "Polynomial Ridge": 136.502929,
           "Hist Gradient Boosting": 137.168967},
    2023: {"Linear Regression": 137.839921,
           "Polynomial Ridge": 132.614714,
           "Hist Gradient Boosting": 133.404201},
}
REFERANS_EGITIM_N = {2019: 261798, 2023: 472182}
REFERANS_TEST_N = {2019: 25776, 2023: 25792}

# --- takvim aritmetigi; koddan DEGIL, elle -------------------------------- #
# 2022 ve 2021 artik yil degil: 8760 saat x 6 konum = 52.560
#   K=1 @ 2023 -> 52.560 - 1.146 =  51.414
#   K=2 @ 2023 -> 105.120 - 1.146 = 103.974
# 1.146 = 6 konum x 191 satir; 191 = 24 (shift) + 168 (roll168) - 1
ISINMA_KONUM = 191
BEKLENEN_EGITIM_N = {1: 51414, 2: 103974}


def _bagil_fark(a: float, b: float) -> float:
    """Bagil mutlak fark; b sifirsa mutlak farka duser."""
    return abs(a - b) / abs(b) if b else abs(a - b)


def _kayit(ad: str, gecti: bool, **alan) -> dict:
    return dict(invaryant=ad, gecti=bool(gecti), **alan)


# --------------------------------------------------------------------------- #
# 1) K=5 @ 2019 == K=tum @ 2019 == ablasyon referansi
# --------------------------------------------------------------------------- #
def invaryant_1(onbellek: PencereOnbellegi, referans: dict) -> list[dict]:
    """2019'da gecmis tam 5 yil, yani iki pencere ayni veriyi gormeli.

    Ucul kontrol: pencere aritmetiginde bir kayma iki hucreyi BIRLIKTE
    kaydirabilir, o yuzden ikili esitlik yetmez - ablasyon referansi da sart.
    """
    kayitlar = []
    for model in HIZLI_ALTKUME:
        a, _ = hucre_kos(onbellek, "kaydirmali", 5, 2019, model,
                         KAYDIRMALI_TOHUM, bootstrap=False)
        b, _ = hucre_kos(onbellek, "kaydirmali", "tum", 2019, model,
                         KAYDIRMALI_TOHUM, bootstrap=False)
        ref = referans[2019][model]

        f_ikili = _bagil_fark(a["RMSE"], b["RMSE"])
        f_ref = _bagil_fark(a["RMSE"], ref)
        gecti = (f_ikili <= INVARYANT_TOLERANS and f_ref <= INVARYANT_TOLERANS
                 and a["egitim_n"] == b["egitim_n"] == REFERANS_EGITIM_N[2019])

        kayitlar.append(_kayit(
            "1_pencere_esdegerligi", gecti, model=model,
            K5_RMSE=a["RMSE"], Ktum_RMSE=b["RMSE"], referans_RMSE=ref,
            bagil_fark_ikili=f_ikili, bagil_fark_referans=f_ref,
            K5_egitim_n=a["egitim_n"], Ktum_egitim_n=b["egitim_n"],
            beklenen_egitim_n=REFERANS_EGITIM_N[2019]))
    return kayitlar


# --------------------------------------------------------------------------- #
# 2) K=tum @ 2023 == ablasyon 'temiz' (Faz 2 geriye donuk uyumluluk)
# --------------------------------------------------------------------------- #
def invaryant_2(onbellek: PencereOnbellegi, referans: dict) -> list[dict]:
    """Faz 4'un K=tum hucresi Faz 2'nin genisleyen penceresiyle AYNI kurgu.

    Tutmuyorsa yeni kod yolu Faz 2/3'un sonuclarini gecersiz kilar demektir.
    """
    kayitlar = []
    for model in HIZLI_ALTKUME:
        a, _ = hucre_kos(onbellek, "kaydirmali", "tum", 2023, model,
                         KAYDIRMALI_TOHUM, bootstrap=False)
        ref = referans[2023][model]
        f = _bagil_fark(a["RMSE"], ref)
        gecti = (f <= INVARYANT_TOLERANS
                 and a["egitim_n"] == REFERANS_EGITIM_N[2023]
                 and a["n"] == REFERANS_TEST_N[2023])

        kayitlar.append(_kayit(
            "2_faz2_uyumlulugu", gecti, model=model,
            yeni_RMSE=a["RMSE"], referans_RMSE=ref, bagil_fark=f,
            mutlak_fark=a["RMSE"] - ref,
            egitim_n=a["egitim_n"], beklenen_egitim_n=REFERANS_EGITIM_N[2023],
            test_n=a["n"], beklenen_test_n=REFERANS_TEST_N[2023]))
    return kayitlar


# --------------------------------------------------------------------------- #
# 3) pencere sinirinda oznitelik isinmasi
# --------------------------------------------------------------------------- #
def invaryant_3(onbellek: PencereOnbellegi) -> list[dict]:
    """Isinma pencerenin basinda mi, veri kumesinin basinda mi tuketiliyor?

    K=tum hucreleri bunu ayirt EDEMEZ - hepsi 2014'te basliyor. Kisa
    pencereler ayirt eder: sinir siziyorsa egitim_n tam bir yil cikar
    (52.560 / 105.120), isinma pencere icindeyse 191 satir eksik cikar.

    Sizinti varsa "1 yil veriyle egitildi" dedigimiz model onceki yillarin
    yuvarlanan istatistiklerini tasir ve doygunluk egrisi yapay duzlesir.
    """
    kayitlar = []
    for K, beklenen in BEKLENEN_EGITIM_N.items():
        basla = pencere_basi(2023, K)
        o, _, isinma = onbellek.al(basla, 2023)
        yil = o["time_utc"].dt.year.to_numpy()
        egitim_n = int(np.sum(yil < 2023))
        test_n = int(np.sum(yil == 2023))

        sizinti = egitim_n == beklenen + ISINMA_KONUM * 6
        gecti = (egitim_n == beklenen and isinma == ISINMA_KONUM
                 and test_n == 8760 * 6)

        kayitlar.append(_kayit(
            "3_isinma_siniri", gecti, pencere=K, egitim_basla=basla,
            egitim_n=egitim_n, beklenen_egitim_n=beklenen, fark=egitim_n - beklenen,
            isinma_konum=isinma, beklenen_isinma=ISINMA_KONUM,
            test_n_ham=test_n, sinir_siziyor=sizinti))
    return kayitlar


# --------------------------------------------------------------------------- #
# 4) altornekleme kod yolu
# --------------------------------------------------------------------------- #
def invaryant_4(onbellek: PencereOnbellegi) -> list[dict]:
    """2019'da havuz tam 5 yil, yani K=5 altornekleme havuzun TAMAMINI ceker.

    Uc tohum da birbirine ve kaydirmali K=5 @ 2019'a birebir esit olmali.
    Ornekleme kod yolunun tek dogrudan dogruluk testi bu; ayni zamanda
    cekimin yerine koymadan yapildigini da pinler.
    """
    temel, _ = hucre_kos(onbellek, "kaydirmali", 5, 2019, HIZLI_ALTKUME[0],
                         KAYDIRMALI_TOHUM, bootstrap=False)

    kayitlar = []
    for model in HIZLI_ALTKUME:
        k, _ = hucre_kos(onbellek, "kaydirmali", 5, 2019, model,
                         KAYDIRMALI_TOHUM, bootstrap=False)
        for tohum in ORNEKLEME_TOHUMLARI:
            a, _ = hucre_kos(onbellek, "altornekleme", 5, 2019, model,
                             tohum, bootstrap=False)
            f = _bagil_fark(a["RMSE"], k["RMSE"])
            gecti = (f <= INVARYANT_TOLERANS
                     and a["egitim_n"] == k["egitim_n"] == REFERANS_EGITIM_N[2019])

            kayitlar.append(_kayit(
                "4_ornekleme_kod_yolu", gecti, model=model, tohum=tohum,
                altornekleme_RMSE=a["RMSE"], kaydirmali_RMSE=k["RMSE"],
                bagil_fark=f, mutlak_fark=a["RMSE"] - k["RMSE"],
                altornekleme_egitim_n=a["egitim_n"],
                kaydirmali_egitim_n=k["egitim_n"]))
    return kayitlar


# --------------------------------------------------------------------------- #
# 5) altorneklemede oznitelik HESAP SIRASI
# --------------------------------------------------------------------------- #
# Invaryant 4 dejenere bir hucrede gecer: 2019/K=5'te havuzun tamami cekilir,
# veri hala sureklidir, dolayisiyla hesap sirasini test ETMEZ. Burada
# dejenere olmayan bir hucre kullaniliyor: K=2 @ 2023'te havuzun ~%22'si
# cekilir ve secilen gunler bitisik degildir.
#
# Dogru sira: oznitelikler SUREKLI havuzda hesaplanir, gunler SONRA secilir.
# Ters sirada P_roll168_mean_lag24 bitisik olmayan gunler uzerinden yuvarlanir
# ve sessizce cop uretir - sayilar makul gorunur, sonuc gecersiz olur.
INVARYANT_5_HUCRE = dict(pencere=2, test_yil=2023, tohum=11)
YUVARLANAN_TANIK = "P_roll168_mean_lag24"


ANAHTAR = ["konum", "time_utc"]


def _oznitelik_kiyasla(sol: pd.DataFrame, sag: pd.DataFrame,
                       X: list[str]) -> tuple[list[str], int]:
    """(konum, time_utc) uzerinden eslestirip oznitelik degerlerini kiyaslar.

    Donen: (farkli sutun adlari, eslesen satir sayisi)
    """
    b = sol[ANAHTAR + X].merge(sag[ANAHTAR + X], on=ANAHTAR, how="inner",
                               suffixes=("_a", "_b"))
    farkli = [c for c in X
              if not np.array_equal(b[f"{c}_a"].to_numpy(),
                                    b[f"{c}_b"].to_numpy(), equal_nan=True)]
    return farkli, len(b)


def _ters_sira_referansi(ham: pd.DataFrame, secilen: pd.DataFrame) -> pd.DataFrame:
    """KASTEN YANLIS referans: once gunler secilir, SONRA oznitelik hesaplanir.

    Negatif kontrolun kaynagi. Secilen (konum, zaman) satirlarinin HAM hali
    uzerinde oznitelik uretmek tam olarak "once ornekle, sonra hesapla"
    demektir; bitisik olmayan gunler uzerinde yuvarlanan istatistikler cop
    uretir. Invaryant bunu yakalayamiyorsa uretim ters sirada olsa da
    yakalayamaz demektir - o durumda invaryant islevsizdir.
    """
    ham_sec = ham.merge(secilen[ANAHTAR], on=ANAHTAR, how="inner")
    return oznitelik_uret(ham_sec, eszaman=False)


def invaryant_5(onbellek: PencereOnbellegi, ham: pd.DataFrame) -> list[dict]:
    """Uretimin sectigi satirlarin oznitelikleri surekli havuzdakiyle ayni mi?

    Bolme URETIM fonksiyonundan (egitim_test_bolme) alinir. Onceki surumde
    invaryant bolmeyi kendi icinde yeniden yaziyordu ve karsilastirmanin iki
    tarafi da ayni cagriya dayaniyordu: hucre_kos ters sirada calissa bile bu
    test gecerdi. Simdi olculen sey uretimin ta kendisi.
    """
    pencere = INVARYANT_5_HUCRE["pencere"]
    test_yil = INVARYANT_5_HUCRE["test_yil"]
    tohum = INVARYANT_5_HUCRE["tohum"]

    # --- URETIM yolu: izgaranin kostugu fonksiyon ---
    o, X, tr, te, isinma, basla = egitim_test_bolme(
        onbellek, "altornekleme", pencere, test_yil, tohum)
    secilen = o.iloc[tr]
    hedef = hedef_satir_sayisi(ham, basla, test_yil - 1, isinma)

    # --- dejenere olmadigini BELGELE ---
    # KONUM BAZINDA sayilir: her konum kendi gunlerini bagimsiz cektigi icin
    # gunlerin konumlar arasi BIRLESIMI cok daha buyuk cikar ve "havuzun
    # %78'i cekildi" gibi yanlis okunur. Gercek oran konum basina ~%22.
    yil = o["time_utc"].dt.year.to_numpy()
    havuz_satir = o.iloc[np.flatnonzero(yil < test_yil)]
    havuz_gun = pd.to_datetime(havuz_satir["time_utc"]).dt.floor("D")
    sec_gun = pd.to_datetime(secilen["time_utc"]).dt.floor("D")

    oranlar, kopukluklar = [], []
    for ad in secilen["konum"].unique():
        k_sec = np.sort(sec_gun[secilen["konum"].to_numpy() == ad].unique())
        k_havuz = havuz_gun[havuz_satir["konum"].to_numpy() == ad].nunique()
        oranlar.append(len(k_sec) / k_havuz)
        kopukluklar.append(
            int(np.sum(np.diff(k_sec).astype("timedelta64[D]").astype(int) != 1)))

    n_havuz_gun = int(havuz_gun.nunique())
    n_sec_gun = int(np.mean([r * n_havuz_gun for r in oranlar]))
    gun_orani = float(np.mean(oranlar))
    kopukluk = int(np.mean(kopukluklar))

    # --- surekli havuzda BAGIMSIZ referans ---
    ham_yil = ham["time_utc"].dt.year
    o_referans = oznitelik_uret(
        ham[(ham_yil >= BASLANGIC_YIL) & (ham_yil <= test_yil)], eszaman=False)

    # --- POZITIF: uretimin sectigi satirlar referansla ayni mi? ---
    farkli, n_eslesen = _oznitelik_kiyasla(secilen, o_referans, X)

    # --- NEGATIF KONTROL: ters sirali referansi YAKALIYOR mu? ---
    o_ters = _ters_sira_referansi(ham, secilen)
    farkli_ters, n_ters = _oznitelik_kiyasla(o_ters, o_referans, X)
    yakalandi = len(farkli_ters) > 0

    # tanik oznitelik: farkin BUYUKLUGU de kayda girsin
    tanik = secilen[ANAHTAR + [YUVARLANAN_TANIK]].merge(
        o_ters[ANAHTAR + [YUVARLANAN_TANIK]], on=ANAHTAR, how="inner",
        suffixes=("_dogru", "_ters"))
    d, t = (tanik[f"{YUVARLANAN_TANIK}_dogru"].to_numpy(),
            tanik[f"{YUVARLANAN_TANIK}_ters"].to_numpy())
    gecerli = ~(np.isnan(d) | np.isnan(t))
    ters_farkli_oran = float(np.mean(d[gecerli] != t[gecerli])) if gecerli.any() else 0.0
    ters_maks_fark = float(np.nanmax(np.abs(d[gecerli] - t[gecerli]))) if gecerli.any() else 0.0

    gecti = (not farkli                       # uretim dogru sirada
             and n_eslesen == len(secilen)    # her satir referansta bulundu
             and len(tr) == sum(hedef.values())
             and n_sec_gun < n_havuz_gun      # dejenere degil
             and kopukluk > 0                 # gercekten kopuk
             and yakalandi                    # invaryantin disi var
             and ters_farkli_oran > 0.5)

    return [_kayit(
        "5_ornekleme_hesap_sirasi", gecti,
        pencere=pencere, test_yil=test_yil, tohum=tohum,
        secilen_n=len(tr), hedef_n=sum(hedef.values()), eslesen_n=n_eslesen,
        havuz_gun_konum=n_havuz_gun, secilen_gun_konum=n_sec_gun,
        gun_orani_konum=round(gun_orani, 4), gun_kopuklugu_konum=kopukluk,
        farkli_oznitelik=len(farkli),
        farkli_adlar=",".join(farkli[:5]) if farkli else "",
        negatif_kontrol_farkli_oznitelik=len(farkli_ters),
        negatif_kontrol_yakalandi=yakalandi,
        negatif_kontrol_eslesen_n=n_ters,
        ters_sira_farkli_oran=round(ters_farkli_oran, 4),
        ters_sira_maks_fark=ters_maks_fark)]


# --------------------------------------------------------------------------- #
# referans okuma
# --------------------------------------------------------------------------- #
def referanslari_oku() -> dict:
    """ablasyon.csv'den 'temiz' referanslari okur ve literallerle karsilastirir."""
    if not ABLASYON.exists():
        raise SystemExit(f"{ABLASYON} yok - Faz 2 kosulmadan invaryant dogrulanamaz")

    d = pd.read_csv(ABLASYON)
    d = d[d.varyant == "temiz"]

    okunan = {}
    for yil, beklenen in REFERANS_RMSE.items():
        y = d[d.test_yil == yil]
        if y.empty:
            raise SystemExit(f"ablasyon.csv'de temiz/{yil} satiri yok")
        okunan[yil] = {}
        for model, lit in beklenen.items():
            s = y[y.model == model]
            if s.empty:
                raise SystemExit(f"ablasyon.csv'de temiz/{yil}/{model} yok")
            deger = float(s.iloc[0]["RMSE"])
            if _bagil_fark(deger, lit) > INVARYANT_TOLERANS:
                raise SystemExit(
                    f"ablasyon.csv DEGISMIS: temiz/{yil}/{model} = {deger!r}, "
                    f"beklenen literal {lit!r}. Faz 2 sonuclari yeniden "
                    "uretilmisse invaryant referanslari elle guncellenmeli - "
                    "sessizce yeni degere gecilmez.")
            okunan[yil][model] = deger
    return okunan


# --------------------------------------------------------------------------- #
# hepsi
# --------------------------------------------------------------------------- #
def tum_invaryantlar(ham: pd.DataFrame, ilerleme=print) -> pd.DataFrame:
    """Dort invaryanti kosar, tek tabloda dondurur. Ucuzdan pahaliya sirali."""
    referans = referanslari_oku()
    onbellek = PencereOnbellegi(ham)

    kayitlar = []
    # 3 once: model egitimi gerektirmez, en ucuz ve en cok kirilmasi beklenen
    ilerleme("  [3/5]isinma siniri (egitim yok)...")
    kayitlar += invaryant_3(onbellek)

    ilerleme("  [1/5]pencere esdegerligi (2019, 6 fit)...")
    kayitlar += invaryant_1(onbellek, referans)

    ilerleme("  [4/5]ornekleme kod yolu (2019, 12 fit)...")
    kayitlar += invaryant_4(onbellek)

    ilerleme("  [5/5] ornekleme hesap sirasi (2023/K=2, egitim yok)...")
    kayitlar += invaryant_5(onbellek, ham)

    ilerleme("  [2/5] Faz 2 uyumlulugu (2023, 3 fit)...")
    kayitlar += invaryant_2(onbellek, referans)

    return pd.DataFrame(kayitlar)
