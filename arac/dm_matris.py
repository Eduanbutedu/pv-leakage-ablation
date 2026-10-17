#!/usr/bin/env python3
"""Yil ici esli DM MATRISI - on modelli havuzun 45 ciftinin hepsi, bes yil.

[on-kayit SONRASI] Makaledeki yil ici iddia (Bolum 5.4, kazanan-ikinci 0/5)
`arac/dm_yil.py`'den gelir ve yalnizca her yilin ILK UC modelini kiyaslar.
Bu betik ayni testi havuzun 45 ciftinin hepsine uygular; yeni bir iddia
icin degil, matrisin tamamini okura gostermek icin.

Hesap kopyalanmaz: DM pv10/ozet_sonrasi.py:yil_ici_dm uzerinden kosar
(dm_yil.py ve uc_dm.py ile ayni zincir -> evaluate.diebold_mariano,
kare hata kaybi, zaman damgasinda kumelenme, Bartlett cekirdegi h=24).
Yil -> tahmin dizini eslemesi dm_yil.KAYNAK'tan okunur. Holm duzeltmesi
arac/coklu_test.py:holm'dur; aile = bir yilin 45 testi.

Yonelim: her yilda modeller loglanan RMSE'ye gore siralanir, cift
(daha iyi, daha kotu) sirasiyla kurulur - dm_yil.py ile ayni yonelim.
Pozitif DM -> model_a, model_b'den DAHA KOTU (bu yonelimde beklenen negatif).

Model egitilmez; kayitli tahminler okunur, GA bootstrap'i kosulmaz (DM ve p
ondan bagimsiz). Eksik tahmin dosyasi _tahmin_oku'da acik hata firlatir.

Kontroller (tutmazsa hata, tablo yazilmaz):
  1) yil basina 45 satir, 10 model.
  2) dm_yil'in 15 satirinin (ilk uc model) DM ve p'si bu matristeki karsiligiyla
     BIREBIR (`==`, round_trip okuma). Matristeki 1 ULP bozulmanin yakalandigi
     negatif kontrolle.
  3) Kazanan-ikinci p'leri makaledeki 0.155 / 0.742 / 0.433 / 0.413 / 0.115
     ile uc ondalikta ayni.
  4) Tahminlerden hesaplanan RMSE siralamasi log siralamasiyla ayni.

Kullanim (kok dizinden):
    python -m arac.dm_matris [--cikti <yol>]
"""
import argparse
import os
from itertools import combinations
from pathlib import Path

from pv10.config import OMP_THREAD_SAYISI

# Thread sayisi numpy import edilmeden once sabitlenir; dm_yil.py ile ayni.
for _ad in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_ad] = str(OMP_THREAD_SAYISI)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from pv10.config import SONUC  # noqa: E402
from pv10.ozet_sonrasi import yil_ici_dm  # noqa: E402

from arac.coklu_test import holm  # noqa: E402
from arac.csv_karsilastir import oku  # noqa: E402
from arac.dm_yil import KAYNAK  # noqa: E402

CIKTI = SONUC / "dm_matris_havuz10.csv"
DM_YIL = SONUC / "doygunluk_ozet_dm_yil.csv"
MODEL_N = 10
CIFT_N = MODEL_N * (MODEL_N - 1) // 2
# Makale Bolum 5.4, kazanan-ikinci p'leri (uc ondalik)
MAKALE_KAZANAN_IKINCI_P = {2019: 0.155, 2020: 0.742, 2021: 0.433,
                           2022: 0.413, 2023: 0.115}
SUTUNLAR = ["yil", "model_a", "model_b", "rmse_a", "rmse_b",
            "dm_stat", "p", "p_holm_yil_ici"]


def yil_matrisi(yil: int, log_ad: str, dizin_ad: str) -> tuple[pd.DataFrame, list[str]]:
    g = pd.read_csv(SONUC / log_ad)
    g = g[(g.durum == "tamam") & (g.test_yil == yil)]
    if len(g) != MODEL_N or g.model.duplicated().any():
        raise SystemExit(f"{yil}: {log_ad} icinde {len(g)} tamam hucre, "
                         f"{MODEL_N} tekil model beklenir")
    sira = list(g.set_index("model")["RMSE"].sort_values().index)
    ciftler = list(combinations(sira, 2))

    d = yil_ici_dm(SONUC / "tahminler" / "doygunluk" / dizin_ad, yil, ciftler,
                   bootstrap=False)
    if len(d) != CIFT_N:
        raise SystemExit(f"{yil}: {len(d)} cift, {CIFT_N} beklenir")
    d = d.rename(columns={"test_yil": "yil", "RMSE_a": "rmse_a",
                          "RMSE_b": "rmse_b", "DM": "dm_stat"})
    d["p_holm_yil_ici"] = holm(d["p"].to_numpy())
    return d[SUTUNLAR], sira


def dm_yil_farklari(m: pd.DataFrame, ref: pd.DataFrame) -> int:
    """dm_yil satirlarinin matristeki karsiligiyla `==` kiyasi; fark sayisi."""
    b = ref.merge(m, left_on=["test_yil", "model_a", "model_b"],
                  right_on=["yil", "model_a", "model_b"], validate="1:1")
    if len(b) != len(ref):
        raise SystemExit(f"dm_yil satirlarinin {len(ref) - len(b)} tanesi "
                         "matriste ayni yonelimle yok")
    return int((b["DM"] != b["dm_stat"]).sum() + (b["p_x"] != b["p_y"]).sum())


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cikti", default=None,
                    help="cikti CSV yolu; varsayilan sonuclar/dm_matris_havuz10.csv")
    a = ap.parse_args()
    cikti = Path(a.cikti) if a.cikti else CIKTI

    parca, siralar = [], {}
    for yil, (log_ad, dizin_ad) in sorted(KAYNAK.items()):
        d, sira = yil_matrisi(yil, log_ad, dizin_ad)
        parca.append(d)
        siralar[yil] = sira
        print(f"{yil}  {dizin_ad:9s} {len(d)} cift  ilk iki: {sira[:2]}")
    m = pd.concat(parca, ignore_index=True)

    # --- kontrol 4: tahminlerden RMSE siralamasi == log siralamasi ---------
    for yil, sira in siralar.items():
        r = pd.concat([m.loc[m.yil == yil, ["model_a", "rmse_a"]]
                       .set_axis(["model", "rmse"], axis=1),
                       m.loc[m.yil == yil, ["model_b", "rmse_b"]]
                       .set_axis(["model", "rmse"], axis=1)])
        r = r.drop_duplicates("model").set_index("model")["rmse"]
        if list(r.sort_values().index) != sira:
            raise SystemExit(f"{yil}: tahminlerden RMSE siralamasi logdan farkli")
    print("kontrol 4  RMSE siralamasi logla ayni: 5/5 yil")

    # --- kontrol 2: dm_yil'in 15 satiri birebir, negatif kontrollu ---------
    ref = oku(DM_YIL)
    fark = dm_yil_farklari(m, ref)
    bozuk = m.copy()
    i = int(np.flatnonzero(bozuk.set_index(["yil", "model_a", "model_b"]).index
                           .isin(ref.set_index(["test_yil", "model_a", "model_b"]).index))[0])
    bozuk.loc[i, "p"] = np.nextafter(bozuk.loc[i, "p"], np.inf)
    if dm_yil_farklari(bozuk, ref) != fark + 1:
        raise AssertionError("NEGATIF KONTROL: 1 ULP p bozulmasi yakalanmadi")
    print(f"kontrol 2  dm_yil satirlari ({len(ref)} x DM,p): {fark} fark  "
          "(negatif kontrol: +1 ULP -> 1 fark, gecti)")
    if fark:
        raise SystemExit("DUR: matris dm_yil ile birebir degil")

    # --- kontrol 3: kazanan-ikinci p'leri makaleyle -------------------------
    print("kontrol 3  kazanan-ikinci p (matris -> 3 ondalik | makale):")
    tutmayan = 0
    for yil, sira in siralar.items():
        s = m[(m.yil == yil) & (m.model_a == sira[0]) & (m.model_b == sira[1])]
        p = float(s["p"].iloc[0])
        ok = round(p, 3) == MAKALE_KAZANAN_IKINCI_P[yil]
        tutmayan += not ok
        print(f"  {yil}  {sira[0]} vs {sira[1]}: p={p!r} -> {round(p, 3):.3f} | "
              f"{MAKALE_KAZANAN_IKINCI_P[yil]:.3f}  {'OK' if ok else 'TUTMUYOR'}"
              f"  p_holm={float(s['p_holm_yil_ici'].iloc[0])!r}")
    if tutmayan:
        raise SystemExit(f"DUR: {tutmayan} kazanan-ikinci p'si makaleyle tutmuyor")

    print()
    print("yil basina p < 0.05 (ham | Holm):")
    for yil, g in m.groupby("yil"):
        print(f"  {yil}  {int((g.p < 0.05).sum())}/{len(g)}  |  "
              f"{int((g.p_holm_yil_ici < 0.05).sum())}/{len(g)}")

    m.to_csv(cikti, index=False)
    print(f"\nyazildi -> {cikti}  ({len(m)} satir)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
