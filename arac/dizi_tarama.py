#!/usr/bin/env python3
"""DKASC dizi taramasi - ikinci olcum dizisinin SECIM kaniti.

`sonuclar/dkasc_dizi_tarama.csv`'nin surucusudur. Karar 6
(dokumanlar/dkasc-kalite-kurallari.md) bu tablodan okunur.

Ne olcer:
  Ham alti dosyadaki her `*_Active_Power` kanali icin (MasterMeter haric),
  karar 3 tablosunun olcutleriyle, yil basina ve alti yil toplu:
    eksik_yuzde         tam 5 dk izgarasina gore eksik
    negatif             P < 0 yuva sayisi (kural 5'in ham sayimi)
    gunduz_sifir_yuzde  gunduz (sin h > 0,1) dolu yuvalarda P == 0
    gunduz_medyan, maks, p99   kW
    ariza_ghi200        GHI > 200 iken P == 0 (kural 7'nin ham sayimi)
    k8a_bayrakli_gun    yalnizca `tum` satirinda: alti yil referansli kural
                        8a gosterge sayimi (karar 3'teki gibi ORNEKTIR)
    k8a_gun             gunduz medyani tanimli gun sayisi

Hicbir kural UYGULANMAZ - karar 3'teki kesif ile ayni duzey. Gunes
yuksekligi etiketin kendisinden hesaplanir (2,5 dk kaydirmasi YOK), yine
karar 3 ile ayni. Kontrol: M6_B satiri karar 3 tablosunu birebir vermeli
(eksik 1,5318, gunduz medyan 2,6351, maks 5,5590, k8a 70 gun).

Model EGITILMEZ, hicbir dizinin tahmin sonucu okunmaz: secim yalnizca veri
kalitesine dayanir.

Kullanim (kok dizinden):
    python -m arac.dizi_tarama
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from pv10.config import (DKASC_BASLANGIC_YIL, DKASC_BITIS_YIL, DKASC_GHI,
                         DKASC_HAM, DKASC_LAT, DKASC_LON, DKASC_UTC_OFSET,
                         DKASC_YUVA_DK, SONUC)
from pv10.features import gunes_yuksekligi_sin

CIKTI = SONUC / "dkasc_dizi_tarama.csv"
GUNDUZ_SIN_H = 0.1   # karar 3 tablosunun gunduz tanimi
K8A_ORAN = 0.3       # kural 8a esigi


def oku(yil: int) -> pd.DataFrame:
    yol = DKASC_HAM / f"Alice_Springs_{yil}.csv"
    b = list(pd.read_csv(yol, nrows=0).columns)
    guc = [c for c in b if c.endswith("Active_Power") and "Master" not in c]
    x = pd.read_csv(yol, usecols=["timestamp", DKASC_GHI] + guc,
                    parse_dates=["timestamp"])
    return x[x["timestamp"].dt.year == yil]


def tara() -> pd.DataFrame:
    yillar = range(DKASC_BASLANGIC_YIL, DKASC_BITIS_YIL + 1)
    d = pd.concat([oku(y) for y in yillar]).sort_values("timestamp")
    if d["timestamp"].duplicated().any():
        raise ValueError("tekrarli zaman damgasi")
    izgara = pd.date_range(f"{DKASC_BASLANGIC_YIL}-01-01",
                           f"{DKASC_BITIS_YIL}-12-31 23:55",
                           freq=f"{DKASC_YUVA_DK}min")
    d = d.set_index("timestamp").reindex(izgara)
    utc = pd.Series(izgara - pd.Timedelta(hours=DKASC_UTC_OFSET))
    gun = gunes_yuksekligi_sin(DKASC_LAT, DKASC_LON, utc) > GUNDUZ_SIN_H
    ghi = d[DKASC_GHI].to_numpy()
    yil = izgara.year.to_numpy()

    satir = []
    for c in [c for c in d.columns if c.endswith("Active_Power")]:
        p = d[c].to_numpy()
        donemler = [("tum", np.ones(len(p), bool))] + \
                   [(str(y), yil == y) for y in yillar]
        for etiket, m in donemler:
            pp = p[m]
            dolu = ~np.isnan(pp)
            gp = pp[gun[m] & dolu]
            satir.append(dict(
                dizi=c, yil=etiket,
                eksik_yuzde=100 * (~dolu).mean(),
                negatif=int((pp < 0).sum()),
                gunduz_sifir_yuzde=100 * (gp == 0).mean() if len(gp) else np.nan,
                gunduz_medyan=float(np.median(gp)) if len(gp) else np.nan,
                maks=float(np.nanmax(pp)) if dolu.any() else np.nan,
                p99=float(np.nanpercentile(pp, 99)) if dolu.any() else np.nan,
                ariza_ghi200=int(((ghi[m] > 200) & (pp == 0)).sum()),
            ))
        # kural 8a gosterge sayimi - alti yil referans, yalnizca `tum`
        s = pd.Series(np.where(gun, p, np.nan), index=izgara)
        gm = s.groupby(izgara.date).median().dropna()
        if len(gm):
            esik = K8A_ORAN * float(np.nanmedian(s))
            satir[-len(donemler)]["k8a_bayrakli_gun"] = int((gm < esik).sum())
        satir[-len(donemler)]["k8a_gun"] = int(len(gm))
    return pd.DataFrame(satir)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cikti", default=str(CIKTI))
    a = ap.parse_args()
    t = tara()
    t.to_csv(a.cikti, index=False)
    print(f"{len(t)} satir -> {a.cikti}")
    ref = t[(t.dizi == "92_DKA_M6_B_Phase_Active_Power") & (t.yil == "tum")]
    print(ref.to_string(index=False))


if __name__ == "__main__":
    main()
