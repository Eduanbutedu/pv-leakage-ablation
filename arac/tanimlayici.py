#!/usr/bin/env python3
"""Tanimlayici istatistik - hedef guc ve duzlem isinimi, saha x donem.

`sonuclar/tanimlayici_istatistik.csv`'nin surucusudur. Makaledeki
tanimlayici istatistik tablosu bu dosyadan okunur.

POPULASYON - modellerin GERCEKTEN degerlendirildigi kume:
  Satirlar ham parquet'ten degil, URETIM oznitelik tablosundan secilir
  (`pv10/features.py:oznitelik_uret`), sonra `pv10/experiment.py:hucre_kos`
  icindeki degerlendirme filtresinin aynisi uygulanir:
    1) oznitelik tablosu: gecikme/roll168 isinmasi ve hedefi eksik satirlar
       zaten dusmus halde (PVGIS: gufbd seti; DKASC: DKASC_GECIKMELI seti)
    2) DKASC: `kismi` satirlari ornek havuzundan cikar (kural 10)
    3) gunduz: `H_sun > 0` (`pv10/evaluate.py:gunduz_maskesi`)
    4) DKASC: `ariza` satirlari cikar (kural 7)
  PVGIS tablosunda `kismi`/`ariza` sutunlari yoktur, 2 ve 4 islemsizdir.
  Gece satirlari egitimde vardir ama bu tabloda YOKTUR - tablo
  degerlendirme populasyonunu tarif eder, egitim havuzunu degil.
  Donem yili `time_utc`'nin yilidir; `bolme_indeksleri` ile ayni.

SAHALAR  [22 Ekim 2026: M15_A ve M3_A eklendi]
  alti PVGIS sahasi + uc DKASC dizisi (`config.DKASC_DIZILER`: M6_B mono-Si,
  M15_A CdTe, M3_A poli-Si). Uc dizi ayni hava istasyonunu paylasir, `G_i`
  satirlari ayni transpozisyondan gelir; populasyonlari dizinin kendi `P`
  bosluklarina gore farklidir. M6_B satirlari eklemeden once uretilenle
  birebir aynidir.

DONEMLER:
  tum           : PVGIS 2014-2023, DKASC 2017-2022
  ilk_egitim    : ilk test yilindan onceki her sey (PVGIS 2014-2016,
                  DKASC 2017) - genisleyen pencerenin ilk egitim penceresi
  test          : PVGIS 2017-2023, DKASC 2018-2022

DEGISKENLER:
  P             : hedef guc, W (saatlik ortalama AC guc)
  P_kapasite    : 100 * P / kapasite, % kapasite. `nRMSE_kapasite` ile ayni
                  payda (PVGIS 1000 W, DKASC 5250 W). Carpiklik ve CV P ile
                  ayni olmak ZORUNDA - olcek degismezdir; betik bunu kontrol
                  eder.
  G_i           : duzlem isinimi, W/m2. PVGIS'te G(i) = Gb_i + Gd_i + Gr_i.
                  DKASC'de OLCULMEZ: GHI + DHI'den izotropik (Liu-Jordan)
                  transpozisyonla 20 derece / kuzey duzlemine TURETILIR
                  (karar 2 ve 4, dokumanlar/dkasc-kalite-kurallari.md);
                  istasyonun egik piranometresi (GTI) kullanilmaz. Bu not
                  `kaynak_notu` sutununda her satirda tasinir.

ISTATISTIKLER:
  N, min, maks, ortalama
  std           : orneklem standart sapmasi, ddof = 1
  carpiklik     : duzeltilmis Fisher-Pearson G1 (pandas `Series.skew`)
  CV            : std / ortalama, ORAN (yuzde degil)

Model egitilmez. Veri hash'i dondurulmus surume karsi kontrol edilir;
tutmazsa hata firlatir.

Kullanim (kok dizinden):
    python -m arac.tanimlayici
    python -m arac.tanimlayici --cikti <yol>

Betik cikti dosyasinin UZERINE YAZAR.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from pv10.config import (BASLANGIC_YIL, BITIS_YIL, DKASC_BASLANGIC_YIL,
                         DKASC_BITIS_YIL, DKASC_DIZILER, DKASC_ESZAMAN,
                         DKASC_GECIKMELI, DKASC_TEST_YILLARI,
                         ESZAMAN_DEGISKEN, GECIKMELI_DEGISKEN, KAPASITE_W,
                         PVGIS_TEST_YILLARI, SONUC, VERI, VERI_SHA16)
from pv10.evaluate import gunduz_maskesi
from pv10.features import oznitelik_uret

CIKTI = SONUC / "tanimlayici_istatistik.csv"

# Anahtar tekil bir girdi adidir; ciktidaki `kaynak` sutunu "pvgis" ya da
# "dkasc". M6_B'nin anahtari "dkasc" olarak kaldi.
KAYNAKLAR = {
    "pvgis": dict(
        kaynak="pvgis",
        yol=VERI, sha=VERI_SHA16, gecikmeli=GECIKMELI_DEGISKEN,
        eszaman=ESZAMAN_DEGISKEN, kapasite_w=KAPASITE_W,
        yillar=(BASLANGIC_YIL, BITIS_YIL), ilk_test=min(PVGIS_TEST_YILLARI),
        not_P="PVGIS-SARAH3 simule, 1 kWp c-Si",
        not_G="PVGIS G(i) = Gb_i + Gd_i + Gr_i (components=1 bilesenlerinden)",
    ),
}
_NOT_G_DKASC = ("TURETILDI: GHI + DHI'den izotropik (Liu-Jordan) "
                "transpozisyon, 20 derece / kuzey; olculen GTI kullanilmadi "
                "(karar 2, 4)")
for _ad, _d in DKASC_DIZILER.items():
    _kwp = f"{_d['kapasite_w'] / 1000:.3g}".replace(".", ",")
    _teknoloji = _d["teknoloji"].split(", ")[-1]
    KAYNAKLAR["dkasc" if _ad == "m6b" else f"dkasc_{_ad}"] = dict(
        kaynak="dkasc",
        yol=_d["veri"], sha=_d["sha16"], gecikmeli=DKASC_GECIKMELI,
        eszaman=DKASC_ESZAMAN, kapasite_w=_d["kapasite_w"],
        yillar=(DKASC_BASLANGIC_YIL, DKASC_BITIS_YIL),
        ilk_test=min(DKASC_TEST_YILLARI),
        not_P=(f"olculen AC aktif guc, {_d['sutun'].split('_DKA_')[1].rsplit('_Phase', 1)[0]} "
               f"(sistem {_d['sistem']}), {_kwp} kWp {_teknoloji}"),
        not_G=_NOT_G_DKASC,
    )


def _hash_kontrol(yol: Path, beklenen: str) -> None:
    h = hashlib.sha256(yol.read_bytes()).hexdigest()[:16]
    if h != beklenen:
        raise ValueError(f"{yol}: hash {h}, dondurulmus surum {beklenen}. "
                         "Tablo dondurulmus veriyi tarif etmeli.")


def degerlendirme_populasyonu(kaynak: str) -> pd.DataFrame:
    """Degerlendirme populasyonu: konum, yil, P, G_i (hedef saatte)."""
    k = KAYNAKLAR[kaynak]
    _hash_kontrol(k["yol"], k["sha"])
    ham = pd.read_parquet(k["yol"])
    o = oznitelik_uret(ham, eszaman=False, gecikmeli=k["gecikmeli"],
                       eszaman_degisken=k["eszaman"])

    n0 = len(o)
    if "kismi" in o.columns:
        o = o[~o["kismi"].to_numpy()]
    n_kismi = n0 - len(o)
    maske = gunduz_maskesi(o)
    if "ariza" in o.columns:
        n_ariza = int((maske & o["ariza"].to_numpy()).sum())
        maske = maske & ~o["ariza"].to_numpy()
    else:
        n_ariza = 0
    o = o[maske]
    print(f"  {kaynak}: oznitelik {n0:,} -> kismi -{n_kismi:,} -> gunduz ve "
          f"ariza (-{n_ariza:,} ariza) -> {len(o):,}")

    # G_i hedef saatte oznitelik tablosunda YOK (yalnizca gecikmeleri var);
    # ham tablodan (konum, time_utc) ile birebir eslenir.
    g = ham[["konum", "time_utc", "G_i"]]
    m = o[["konum", "time_utc", "y"]].merge(g, on=["konum", "time_utc"],
                                           how="left", validate="1:1")
    if len(m) != len(o) or m["G_i"].isna().any():
        raise ValueError(f"{kaynak}: G_i eslemesi eksik "
                         f"({int(m['G_i'].isna().sum())} satir)")
    m = m.rename(columns={"y": "P"})
    m["yil"] = m["time_utc"].dt.year
    return m


def istatistik(x: pd.Series) -> dict:
    x = x.astype(float)
    if x.isna().any():
        raise ValueError("populasyonda eksik deger var")
    ort = float(x.mean())
    std = float(x.std(ddof=1))
    return dict(N=int(len(x)), min=float(x.min()), maks=float(x.max()),
                ortalama=ort, std=std, carpiklik=float(x.skew()),
                CV=std / ort)


def tablo() -> pd.DataFrame:
    satir = []
    for girdi, k in KAYNAKLAR.items():
        d = degerlendirme_populasyonu(girdi)
        kaynak = k["kaynak"]
        bas, son = k["yillar"]
        donemler = [("tum", bas, son),
                    ("ilk_egitim", bas, k["ilk_test"] - 1),
                    ("test", k["ilk_test"], son)]
        disari = d[(d.yil < bas) | (d.yil > son)]
        if len(disari):
            raise ValueError(f"{kaynak}: {len(disari)} satir {bas}-{son} "
                             "disinda - donem siniri yanlis")
        for konum, g in d.groupby("konum", sort=True):
            for donem, y0, y1 in donemler:
                s = g[(g.yil >= y0) & (g.yil <= y1)]
                if s.empty:
                    raise ValueError(f"{konum} / {donem}: bos donem")
                degiskenler = [
                    ("P", "W", s["P"], k["not_P"]),
                    ("P_kapasite", "% kapasite",
                     100.0 * s["P"] / k["kapasite_w"],
                     f"{k['not_P']}; payda {k['kapasite_w']:.0f} W"),
                    ("G_i", "W/m2", s["G_i"], k["not_G"]),
                ]
                for ad, birim, x, not_ in degiskenler:
                    satir.append(dict(saha=konum, kaynak=kaynak, degisken=ad,
                                      birim=birim, donem=donem, yil_bas=y0,
                                      yil_bit=y1, **istatistik(x),
                                      kaynak_notu=not_))
    t = pd.DataFrame(satir)

    # Olcek degismezlik kontrolu: P_kapasite'nin carpiklik ve CV'si P ile
    # ayni olmali. Tutmazsa kapasite donusumu bir yerde bozulmustur.
    a = t[t.degisken == "P"].reset_index(drop=True)
    b = t[t.degisken == "P_kapasite"].reset_index(drop=True)
    for c in ("carpiklik", "CV"):
        if not np.allclose(a[c], b[c], rtol=1e-12, atol=0):
            raise ValueError(f"P ile P_kapasite'nin {c}'si farkli")
    return t


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cikti", default=str(CIKTI))
    a = ap.parse_args()
    t = tablo()
    t.to_csv(a.cikti, index=False)
    print(f"\n{len(t)} satir -> {a.cikti}")


if __name__ == "__main__":
    main()
