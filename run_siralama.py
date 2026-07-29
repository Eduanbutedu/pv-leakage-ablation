#!/usr/bin/env python3
"""Faz 3 - siralama kararliligi ve anlamlilik testleri.

Kullanim:
    python run_siralama.py                       # hizli modeller, 2017-2023
    python run_siralama.py --modeller ablasyon   # Random Forest ve MLP dahil
    python run_siralama.py --yillar 2021,2022,2023
    python run_siralama.py --hizli-bootstrap     # esli bootstrap'i atla

Kosu kesilirse ayni komutu tekrar verin: tamamlanmis yillar atlanir.
"""

from __future__ import annotations

import argparse
import time

import pandas as pd

from pv10.config import SONUC, VERI
from pv10.evaluate import metrikler
from pv10.experiment import OznitelikOnbellegi
from pv10.models import ABLASYON_ALTKUMESI, HIZLI_ALTKUME, modeller
from pv10.ranking import (ikili_karsilastirma, kararlilik_ozeti,
                          kendall_tau_matrisi, siralama_tablosu,
                          yil_tahminleri)

KARS_LOG = SONUC / "siralama_karsilastirma.csv"
RMSE_LOG = SONUC / "siralama_rmse.csv"
TAHMIN_DIZIN = SONUC / "tahminler"


def ozetle(kars: pd.DataFrame, yil_rmse: pd.DataFrame) -> None:
    siralama = siralama_tablosu(yil_rmse)

    print(f"\n{'=' * 78}")
    print("YIL BAZINDA RMSE (gunduz, kronolojik, sizintisiz)")
    print(f"{'=' * 78}")
    print(yil_rmse.round(2).to_string())

    print(f"\nSIRALAMA (1 = en iyi)")
    print(siralama.to_string())

    ozet = kararlilik_ozeti(kars, siralama)

    print(f"\n{'=' * 78}")
    print("KARARLILIK OZETI")
    print(f"{'=' * 78}")
    print(f"  degerlendirilen yil            : {ozet['yil_sayisi']}")
    print(f"  farkli kazanan sayisi          : {ozet['farkli_kazanan_sayisi']}")
    print(f"  kazanan dagilimi               : {ozet['kazanan_dagilimi']}")
    print(f"  Kendall tau (yillar arasi ort.): {ozet['kendall_tau_ortalama']:.3f}"
          f"  (en dusuk {ozet['kendall_tau_min']:.3f})")
    print(f"\n  Ilk iki model arasindaki fark:")
    print(f"    anlamli cikan yil sayisi     : "
          f"{ozet['ilk_ikili_anlamli_yil']}/{ozet['yil_sayisi']}")
    print(f"    medyan fark                  : "
          f"{ozet['ilk_ikili_medyan_fark_W']:.2f} W  "
          f"({ozet['ilk_ikili_medyan_fark_kapasite_yuzde']:.3f}% kapasite)")

    print(f"\n  Yil bazinda en yakin ikili:")
    d = ozet["en_yakin_detay"]
    if len(d):
        print(f"    {'yil':<6}{'en iyi':<26}{'ikinci':<26}"
              f"{'fark W':>8}{'p':>8}  anlamli")
        for _, r in d.iterrows():
            print(f"    {r.yil:<6}{r.en_iyi:<26}{r.ikinci:<26}"
                  f"{r.fark_W:>8.2f}{r.p:>8.4f}  "
                  f"{'EVET' if r.anlamli else 'hayir'}")

    print(f"\n{'=' * 78}")
    print("KENDALL TAU MATRISI")
    print(f"{'=' * 78}")
    print(kendall_tau_matrisi(siralama).round(3).to_string())

    print(f"\nTum ikili karsilastirmalar: {KARS_LOG}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modeller", default="hizli",
                    choices=["hizli", "ablasyon", "tumu"])
    ap.add_argument("--yillar", default="2017,2018,2019,2020,2021,2022,2023")
    ap.add_argument("--hizli-bootstrap", action="store_true",
                    help="esli bootstrap GA hesaplamasini atla")
    ap.add_argument("--ozet", action="store_true", help="mevcut loglari ozetle")
    a = ap.parse_args()

    if a.ozet:
        if not (KARS_LOG.exists() and RMSE_LOG.exists()):
            raise SystemExit("once analizi kosun")
        ozetle(pd.read_csv(KARS_LOG),
               pd.read_csv(RMSE_LOG, index_col="test_yil"))
        return

    havuz = list(modeller())
    model_adlari = {"hizli": list(HIZLI_ALTKUME),
                    "ablasyon": list(ABLASYON_ALTKUMESI),
                    "tumu": havuz}[a.modeller]
    yillar = [int(y) for y in a.yillar.split(",")]

    print(f"Siralama kararliligi: {len(model_adlari)} model x {len(yillar)} yil")
    print(f"  modeller: {', '.join(model_adlari)}")

    TAHMIN_DIZIN.mkdir(parents=True, exist_ok=True)
    ham = pd.read_parquet(VERI)
    print(f"  veri   : {len(ham):,} satir, {ham.konum.nunique()} konum\n")
    onbellek = OznitelikOnbellegi(ham)

    tamam = set()
    if KARS_LOG.exists():
        tamam = set(pd.read_csv(KARS_LOG).test_yil.unique())
        if tamam:
            print(f"{sorted(tamam)} yillari daha once tamamlanmis, atlaniyor\n")

    t0 = time.time()
    for yil in yillar:
        if yil in tamam:
            continue
        print(f"  {yil} (egitim 2014-{yil - 1}):")
        tahmin = yil_tahminleri(onbellek, model_adlari, yil,
                               ilerleme=lambda s: print(s))
        tahmin.to_parquet(TAHMIN_DIZIN / f"tahmin_{yil}.parquet", index=False)

        kars = ikili_karsilastirma(tahmin, model_adlari, yil,
                                   bootstrap=not a.hizli_bootstrap)
        kars.to_csv(KARS_LOG, mode="a", header=not KARS_LOG.exists(),
                    index=False)

        satir = {"test_yil": yil}
        satir.update({ad: round(metrikler(tahmin["y"], tahmin[ad])["RMSE"], 3)
                      for ad in model_adlari})
        pd.DataFrame([satir]).to_csv(RMSE_LOG, mode="a",
                                     header=not RMSE_LOG.exists(), index=False)

    print(f"\nToplam sure: {(time.time() - t0) / 60:.1f} dakika")
    ozetle(pd.read_csv(KARS_LOG),
           pd.read_csv(RMSE_LOG, index_col="test_yil"))


if __name__ == "__main__":
    main()