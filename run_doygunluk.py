#!/usr/bin/env python3
"""Faz 4 - veri hacmi doygunlugu.

Kullanim:
    python run_doygunluk.py --dogrula      # bes invaryant kapisi, 18 kontrol (ONCE BU)
    python run_doygunluk.py --tahmin       # hucre maliyeti, kosmadan
    python run_doygunluk.py                # ana izgara, sonunda ozet
    python run_doygunluk.py --ozet         # mevcut CSV'lerden ozet, izgara kosmadan

Ana izgaraya invaryant kapisi gecmeden gecilmez.
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# OpenMP thread sayisi numpy/sklearn IMPORT EDILMEDEN once sabitlenmeli;
# sonra atamak OpenMP calisma zamaninda etkisiz kalir. config.py yalnizca
# pathlib import ettigi icin bu asamada guvenle okunabilir.
# ---------------------------------------------------------------------------
from pv10.config import OMP_THREAD_SAYISI  # noqa: E402  (import sirasi kasitli)

# Ucu birden sabitlenir. Bu ortamda OMP_NUM_THREADS tek basina OpenBLAS
# havuzlarini da 8'e cekiyor (olculdu), ama bu numpy'nin derleme detayi ve
# surum degisiminde kayabilir. MLPRegressor matmul'lari OpenBLAS uzerinden
# gectigi icin thread sayisi degisince ciktisi BIT DUZEYINDE degisiyor
# (olculdu: 20 thread'de farkli hash, RMSE 10 ondalik ayni). Agac tabanlilar
# ve HGB bu duyarliligi gostermiyor.
THREAD_DEGISKENLERI = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
ONCEKI_THREAD = {ad: os.environ.get(ad) for ad in THREAD_DEGISKENLERI}
for _ad in THREAD_DEGISKENLERI:
    os.environ[_ad] = str(OMP_THREAD_SAYISI)

import argparse  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from pv10.config import (DOYGUNLUK_KOLLARI, DOYGUNLUK_TEST_YILLARI,  # noqa: E402
                         EGITIM_PENCERELERI, GENIS_KOSU_HARIC,
                         ORNEKLEME_TOHUMLARI, SONUC, VERI)
from pv10 import ozet  # noqa: E402
from pv10.dogrulama import tum_invaryantlar  # noqa: E402
# _tamamlananlar ozel ad ama kasitli olarak yeniden yazilmiyor: "tamamlanmis
# hucre" tanimi (durum == 'tamam') tek yerde kalmali, yoksa devam mantigi ile
# ozetin eksik hucre sayimi birbirinden kayar.
from pv10.doygunluk import (PencereOnbellegi, _tamamlananlar,  # noqa: E402
                            hucre_kos, izgara_hucreleri, izgara_kos,
                            pencere_basi)
from pv10.models import ABLASYON_ALTKUMESI, HIZLI_ALTKUME, modeller  # noqa: E402

LOG = SONUC / "doygunluk.csv"
KONUM_LOG = SONUC / "doygunluk_konum.csv"


def thread_durumu() -> str:
    onceki = ", ".join(f"{k}={v if v is not None else 'ayarsiz'}"
                       for k, v in ONCEKI_THREAD.items())
    return (f"thread sabiti: {OMP_THREAD_SAYISI} "
            f"({', '.join(THREAD_DEGISKENLERI)})\n"
            f"  kosu oncesi ortam: {onceki}")


def dogrula(ham: pd.DataFrame) -> bool:
    print(f"{'=' * 78}")
    print("FAZ 4 INVARYANT KAPISI")
    print(f"{'=' * 78}")
    print(f"  {thread_durumu()}")
    print(f"  veri: {len(ham):,} satir, {ham.konum.nunique()} konum\n")

    t0 = time.time()
    d = tum_invaryantlar(ham)
    sure = time.time() - t0

    for ad in sorted(d.invaryant.unique()):
        alt = d[d.invaryant == ad]
        gecti = bool(alt.gecti.all())
        print(f"\n{'-' * 78}")
        print(f"{'GECTI' if gecti else 'KALDI'}  {ad}")
        print(f"{'-' * 78}")
        sutun = [c for c in alt.columns if c not in ("invaryant",)
                 and alt[c].notna().any()]
        print(alt[sutun].to_string(index=False))

    hepsi = bool(d.gecti.all())
    print(f"\n{'=' * 78}")
    print(f"{'HEPSI GECTI' if hepsi else 'BASARISIZ'} - "
          f"{int(d.gecti.sum())}/{len(d)} kontrol, {sure / 60:.1f} dakika")
    print(f"{'=' * 78}")
    if not hepsi:
        print("\nAna izgara KOSULMAZ. Kirilan invaryantlari duzeltmeden devam "
              "etmek Faz 4'un butun sayilarini supheli hale getirir.")
    return hepsi


def tahmin_et(ham: pd.DataFrame, kollar, pencereler, yillar, model_adlari,
              tohumlar) -> None:
    """Iki uctan olcup izgaranin tamamina yayar.

    Egitim suresi satir sayisiyla kabaca lineer; bootstrap ise egitim
    boyutundan BAGIMSIZ (test seti her yil ~25.8 bin gunduz satiri), o yuzden
    ayri olculup her hucreye sabit eklenir.
    """
    onbellek = PencereOnbellegi(ham)
    hucreler = list(izgara_hucreleri(kollar, pencereler, yillar, model_adlari,
                                     tohumlar))

    # --- her hucrenin egitim_n'i: yalnizca (pencere, test_yil)'e bagli ---
    yil_s = ham["time_utc"].dt.year
    konum_s = ham.konum.nunique()
    isinma_toplam = None

    def egitim_n(pencere, test_yil):
        nonlocal isinma_toplam
        basla = pencere_basi(test_yil, pencere)
        ham_n = int(((yil_s >= basla) & (yil_s <= test_yil - 1)).sum())
        if isinma_toplam is None:
            _, _, isinma = onbellek.al(basla, test_yil)
            isinma_toplam = isinma * konum_s
        return ham_n - isinma_toplam

    # anahtar ORIJINAL pencere degeri (int veya 'tum'); izgara_hucreleri de
    # ayni tipi uretiyor, stringe cevirmek pencere_basi'ni kirar
    boyut = {(p, y): egitim_n(p, y) for p in pencereler for y in yillar}

    print(f"\nIzgara: {len(hucreler)} hucre")
    print(f"  egitim boyutu araligi: {min(boyut.values()):,} - "
          f"{max(boyut.values()):,} satir\n")

    # --- iki uctan olc ---
    kucuk = min(boyut, key=boyut.get)
    buyuk = max(boyut, key=boyut.get)
    print(f"Sonda hucreleri olculuyor (bootstrap DAHIL):")
    olcum = {}
    for etiket, (pen, yil) in (("kucuk", kucuk), ("buyuk", buyuk)):
        for model_ad in model_adlari:
            t0 = time.time()
            ana, _ = hucre_kos(onbellek, "kaydirmali", pen, yil, model_ad, 0,
                               bootstrap=True)
            sure = time.time() - t0
            olcum[(etiket, model_ad)] = (ana["egitim_n"], ana["egitim_sn"],
                                         ana["bootstrap_sn"], sure)
            print(f"  {etiket:6} K={str(pen):4} {yil} {model_ad:24} "
                  f"n={ana['egitim_n']:>7,}  fit {ana['egitim_sn']:>6.1f} sn  "
                  f"boot {ana['bootstrap_sn']:>5.1f} sn")

    # --- lineer yayma: fit ~ a + b*n, bootstrap sabit ---
    boot_ort = float(np.mean([v[2] for v in olcum.values()]))
    toplam = 0.0
    model_toplam = {}
    for model_ad in model_adlari:
        n1, f1, _, _ = olcum[("kucuk", model_ad)]
        n2, f2, _, _ = olcum[("buyuk", model_ad)]
        b = (f2 - f1) / (n2 - n1) if n2 != n1 else 0.0
        a = f1 - b * n1
        s = sum(max(a + b * boyut[(p, y)], 0.0) + boot_ort
                for (kol, p, y, m, t) in hucreler if m == model_ad)
        model_toplam[model_ad] = s
        toplam += s

    print(f"\n  bootstrap ortalamasi: {boot_ort:.1f} sn/hucre "
          f"x {len(hucreler)} = {boot_ort * len(hucreler) / 60:.0f} dakika")
    print(f"\nMODEL BAZINDA TAHMIN:")
    for model_ad, s in sorted(model_toplam.items(), key=lambda x: -x[1]):
        print(f"  {model_ad:24} {s / 60:>7.0f} dakika")
    print(f"\n  KABA TOPLAM: {toplam / 60:.0f} dakika ({toplam / 3600:.1f} saat)")
    print("  (lineer yayma; agir modeller ve bellek baskisi bu tahmini asabilir)")


def _baslik(s: str) -> None:
    print(f"\n{'-' * 78}\n{s}\n{'-' * 78}")


def ozetle(kollar, pencereler, yillar, model_adlari, tohumlar) -> None:
    """Faz 4 ozet tablolari.

    ozet.py sonuclar gorulmeden yazildi; burada yalnizca CAGRILIR. Tablo
    tanimlari, metrik secimleri ve esikler bu dosyadan degistirilmez.

    Eksiklik tespiti tahminle degil, izgara_hucreleri'nin urettigi beklenen
    kume ile logdaki tamamlanmis kumenin farkindan gelir.
    """
    if not LOG.exists():
        raise SystemExit(f"{LOG} yok - once izgarayi kosun.")

    ham_log = pd.read_csv(LOG)
    tamam = _tamamlananlar(LOG)
    beklenen = {(kol, str(p), y, m, t) for kol, p, y, m, t
                in izgara_hucreleri(kollar, pencereler, yillar, model_adlari,
                                    tohumlar)}
    eksik = sorted(beklenen - tamam)
    hatali = ham_log[ham_log.durum == "hata"]

    print(f"\n{'=' * 78}")
    print(f"FAZ 4 OZET - {len(tamam)}/{len(beklenen)} beklenen hucre tamam")
    print(f"{'=' * 78}")

    # Kural 5: eksik ve basarisiz hucreler ACIKCA listelenir, kirpilmadan.
    if len(hatali):
        _baslik(f"BASARISIZ HUCRELER ({len(hatali)})")
        with pd.option_context("display.max_rows", None, "display.width", 200):
            print(hatali[["kol", "pencere", "test_yil", "model", "tohum",
                          "hata"]].to_string(index=False))

    if eksik:
        _baslik(f"EKSIK HUCRELER ({len(eksik)})")
        e = pd.DataFrame(eksik, columns=["kol", "pencere", "test_yil", "model",
                                         "tohum"])
        with pd.option_context("display.max_rows", None, "display.width", 200):
            print(e.to_string(index=False))
        print("\nUYARI: izgara EKSIK. Asagidaki tablolar yalnizca tamamlanan "
              "hucrelerden hesaplandi.")

    d = ham_log[ham_log.durum == "tamam"]
    if d.empty:
        raise SystemExit("tamamlanmis hucre yok - ozet uretilemez.")
    dk = pd.read_csv(KONUM_LOG) if KONUM_LOG.exists() else pd.DataFrame()

    egri = ozet.egri_tablosu(d)
    _baslik("1) OGRENME EGRISI - iki kol")
    print(egri.to_string(index=False))
    _baslik("1b) MARJINAL KAZANC - doygunluk nerede?")
    print(ozet.marjinal_kazanc(egri).to_string(index=False))

    _baslik("2) ANA ORAN - saf hacim vs uygulamali hacim")
    print(ozet.hacim_orani(d).to_string(index=False))

    _baslik("3) TOHUM YAYILIMI - (K, yil, model) bazinda")
    t3 = ozet.tohum_yayilimi(d)
    print("altornekleme hucresi yok" if t3.empty else t3.to_string(index=False))

    _baslik("4) MODEL x PENCERE ETKILESIMI")
    e4 = ozet.model_pencere_etkilesimi(d)
    if not e4:
        print("kaydirmali hucre yok")
    else:
        print(f"kazanan degisiyor mu: {e4['kazanan_degisiyor_mu']}  "
              f"({e4['farkli_kazanan_sayisi']} farkli kazanan, "
              f"{e4['kazanan_dagilimi']})\n")
        print(e4["pencere_bazinda"].to_string(index=False))
        print()
        print(e4["pencere_yil_bazinda"].to_string(index=False))

    _baslik("5) VARYANS AYRISTIRMASI")
    try:
        v = ozet.varyans_ayristirmasi(d)
        print("hizli altkume bos" if v.empty else v.to_string(index=False))
    except ValueError as e:
        # Eksik izgarada dengesiz tasarim BEKLENEN durumdur. Izgara TAMSA ayni
        # hata gercek bir kusurdur ve yutulmaz.
        if not eksik:
            raise
        print(f"ATLANDI - izgara {len(eksik)} hucre eksik, tasarim dengeli "
              f"degil.\n  {e}")

    _baslik("6) KONUM BAZINDA - nRMSE_ortalama")
    if dk.empty:
        print(f"{KONUM_LOG} yok")
    else:
        t6 = ozet.konum_tablosu(dk)
        print("kaydirmali konum satiri yok" if t6.empty else t6.to_string())


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dogrula", action="store_true",
                    help="bes invaryant kapisini (18 kontrol) kos ve cik")
    ap.add_argument("--tahmin", action="store_true",
                    help="maliyeti tahmin et, izgarayi kosma")
    ap.add_argument("--ozet", action="store_true",
                    help="mevcut CSV'lerden ozet tablolari bas, izgarayi kosma")
    ap.add_argument("--modeller", default="hizli",
                    choices=["hizli", "ablasyon", "tumu"])
    ap.add_argument("--yillar", default=",".join(str(y) for y in DOYGUNLUK_TEST_YILLARI))
    ap.add_argument("--kol", default=",".join(DOYGUNLUK_KOLLARI))
    ap.add_argument("--hizli-bootstrap", action="store_true",
                    help="gun-blogu bootstrap GA'sini atla")
    a = ap.parse_args()

    ham = pd.read_parquet(VERI)

    if a.dogrula:
        raise SystemExit(0 if dogrula(ham) else 1)

    kollar = a.kol.split(",")
    bilinmeyen = [k for k in kollar if k not in DOYGUNLUK_KOLLARI]
    if bilinmeyen:
        raise SystemExit(f"bilinmeyen kol: {bilinmeyen}")
    yillar = [int(y) for y in a.yillar.split(",")]
    havuz = list(modeller())
    model_adlari = {"hizli": list(HIZLI_ALTKUME),
                    "ablasyon": list(ABLASYON_ALTKUMESI),
                    "tumu": [m for m in havuz if m not in GENIS_KOSU_HARIC]}[a.modeller]

    if a.ozet:
        ozetle(kollar, EGITIM_PENCERELERI, yillar, model_adlari,
               ORNEKLEME_TOHUMLARI)
        return

    if a.tahmin:
        tahmin_et(ham, kollar, EGITIM_PENCERELERI, yillar, model_adlari,
                  ORNEKLEME_TOHUMLARI)
        return

    print(f"  {thread_durumu()}")
    print(f"  veri: {len(ham):,} satir, {ham.konum.nunique()} konum")
    print(f"  log : {LOG}\n")
    t0 = time.time()
    izgara_kos(ham, kollar, EGITIM_PENCERELERI, yillar, model_adlari,
               ORNEKLEME_TOHUMLARI, LOG, KONUM_LOG,
               bootstrap=not a.hizli_bootstrap)
    print(f"\nToplam sure: {(time.time() - t0) / 60:.1f} dakika")

    ozetle(kollar, EGITIM_PENCERELERI, yillar, model_adlari,
           ORNEKLEME_TOHUMLARI)


if __name__ == "__main__":
    main()
