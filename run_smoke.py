#!/usr/bin/env python3
"""Duman testi: temeli dogrular, deney izgarasi DEGILDIR.

Makalenin protokolunu 10 yillik veride tek bir bolmeyle kosar:
  egitim = 2014-2022,  test = 2023
Amac: oznitelik katmani, modeller ve metrikler dogru cakisiyor mu.

Kullanim:
    python run_smoke.py            # hizli alt kume
    python run_smoke.py --tumu     # on bir modelin hepsi (yavas)
"""

from __future__ import annotations

import argparse
import time

import pandas as pd

from pv10.config import VERI
from pv10.evaluate import (diebold_mariano, gun_blogu_bootstrap, gunduz_maskesi,
                           metrikler)
from pv10.features import oznitelik_kolonlari, oznitelik_uret
from pv10.models import ABLASYON_ALTKUMESI, HIZLI_ALTKUME, modeller


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tumu", action="store_true", help="on bir modelin hepsi (cok yavas)")
    ap.add_argument("--ablasyon", action="store_true",
                    help="ablasyon alt kumesi (Random Forest ve MLP dahil, yavas)")
    ap.add_argument("--test-yil", type=int, default=2023)
    a = ap.parse_args()

    print(f"Veri okunuyor: {VERI}")
    ham = pd.read_parquet(VERI)
    print(f"  {len(ham):,} satir, {ham.konum.nunique()} konum")

    t0 = time.time()
    o = oznitelik_uret(ham)
    X = oznitelik_kolonlari(o)
    print(f"Oznitelik uretimi: {time.time()-t0:.1f} sn -> "
          f"{len(o):,} satir, {len(X)} oznitelik")

    yil = o.time_utc.dt.year
    egitim, test = o[yil < a.test_yil], o[yil == a.test_yil]
    print(f"  egitim {len(egitim):,} ({egitim.time_utc.dt.year.min()}-"
          f"{egitim.time_utc.dt.year.max()})   test {len(test):,} ({a.test_yil})")

    # Degerlendirme YALNIZCA gunduz saatlerinde; egitim tum saatleri kullanir
    maske = gunduz_maskesi(test)
    y_test = test.y.to_numpy()[maske]
    pers = test.persistence.to_numpy()[maske]
    gunler = test.time_utc.dt.date.to_numpy()[maske]

    print(f"\n{'model':<28}{'MAE':>9}{'RMSE':>9}{'R2':>8}{'skill%':>9}{'sn':>7}")
    print("-" * 70)
    print(f"{'24-h Persistence':<28}"
          f"{metrikler(y_test, pers)['MAE']:>9.2f}"
          f"{metrikler(y_test, pers)['RMSE']:>9.2f}"
          f"{metrikler(y_test, pers)['R2']:>8.3f}{0.0:>9.2f}{'-':>7}")

    havuz = modeller()
    if a.tumu:
        secilen = havuz
    else:
        anahtar = ABLASYON_ALTKUMESI if a.ablasyon else HIZLI_ALTKUME
        secilen = {k: havuz[k] for k in anahtar}
    tahminler, satirlar = {}, []

    for ad, hat in secilen.items():
        t = time.time()
        hat.fit(egitim[X], egitim.y)
        p = hat.predict(test[X])[maske]
        m = metrikler(y_test, p, pers)
        tahminler[ad] = p
        satirlar.append(dict(model=ad, **m))
        print(f"{ad:<28}{m['MAE']:>9.2f}{m['RMSE']:>9.2f}"
              f"{m['R2']:>8.3f}{m['skill']:>9.2f}{time.time()-t:>7.1f}")

    sonuc = pd.DataFrame(satirlar).sort_values("RMSE")
    en_iyi = sonuc.iloc[0].model

    print(f"\nEn iyi: {en_iyi}")
    ga = gun_blogu_bootstrap(y_test, tahminler[en_iyi], gunler)
    print(f"  gun-blogu bootstrap %95 GA -> RMSE {ga['RMSE'][0]:.2f}-{ga['RMSE'][1]:.2f} W, "
          f"R2 {ga['R2'][0]:.3f}-{ga['R2'][1]:.3f}")

    if len(sonuc) > 1:
        ikinci = sonuc.iloc[1].model
        dm = diebold_mariano(y_test, tahminler[en_iyi], tahminler[ikinci])
        anlam = "ANLAMLI" if dm["p"] < 0.05 else "anlamli DEGIL"
        print(f"  Diebold-Mariano ({en_iyi} vs {ikinci}): "
              f"DM={dm['DM']:.2f}, p={dm['p']:.4f} -> fark {anlam}")

    print("\nBu, deney izgarasi degil bir duman testidir. Faz 2/3 ayrica kurulacak.")


if __name__ == "__main__":
    main()