#!/usr/bin/env python3
"""Iki izgara logunun hucre hucre, alan alan birebir kiyasi.

Faz notundaki "510/520 alan birebir" ifadesinin dayanagi bu betiktir.

Ne olcer:
  Ayni hucreler (kol, pencere, test_yil, model, tohum) iki ayri kosuda
  ayni sayilari mi vermis? Kiyas TOLERANSSIZ - `==` ile, "yaklasik esit"
  degil. Uretim kodu degistiginde (or. hucre_kos'a tahmin kaydi
  eklendiginde) veya ortam degistiginde (or. pyarrow surumu) kosulur;
  amaci degisikligin metrikleri KIMILDATMADIGINI gostermektir.

  Fark cikan her alan tam hassasiyette listelenir. Beklenen nondeterminist
  modeller (--nondet) ayri isaretlenir: onlarin disinda TEK bir fark bile
  cikarsa betik 1 ile doner ve "DUR" der. Bilinen nondeterminizmi gerekce
  gostererek gercek bir regresyonu gecistirmemek icin ayrim sart.

Kiyaslanan alanlar:
  egitim_n, n, isinma, egitim_basla   -> kurgu; ASLA oynamamali
  RMSE, MAE, R2, nRMSE_*, skill       -> metrik
  RMSE_persistence, RMSE_GA_alt/ust   -> kiyas taban ve bootstrap araligi

Kullanim (kok dizinden):
    python -m arac.regresyon_kiyas
    python -m arac.regresyon_kiyas --referans sonuclar/doygunluk.csv \\
        --yeni sonuclar/doygunluk_dm.csv --nondet "Extra Trees,Random Forest"

Ilk kosu: 3 Agustos 2026, dm_kalan (pyarrow 22.0.0) vs genis (25.0.0).
40 hucre x 13 alan = 520 karsilastirma, 510'u birebir. Farkli cikan 10
alanin hepsi 1-2 ULP ve yalnizca Random Forest ile Extra Trees'te; sekiz
model tam esit. Sebep surec ici paralel hesap, surum degil - olcumu
arac/nondeterminizm.py yapti.
"""
from __future__ import annotations

import argparse
import sys

import pandas as pd

ANAHTAR = ["kol", "pencere", "test_yil", "model", "tohum"]
KIYAS = ["egitim_n", "n", "RMSE", "MAE", "R2", "nRMSE_kapasite",
         "nRMSE_ortalama", "skill", "isinma", "egitim_basla",
         "RMSE_persistence", "RMSE_GA_alt", "RMSE_GA_ust"]


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--referans", default="sonuclar/doygunluk_genis.csv",
                    help="onceki kosunun logu")
    ap.add_argument("--yeni", default="sonuclar/doygunluk_dm_kalan.csv",
                    help="yeni kosunun logu")
    ap.add_argument("--nondet", default="Extra Trees,Random Forest",
                    help="fark cikmasi BEKLENEN modeller (virgullu); "
                         "bunlarin disindaki fark kapiyi kirmizi yakar")
    a = ap.parse_args()

    beklenen = {m.strip() for m in a.nondet.split(",") if m.strip()}
    r = pd.read_csv(a.referans)
    y = pd.read_csv(a.yeni)
    r, y = r[r.durum == "tamam"], y[y.durum == "tamam"]
    # pencere hem int hem 'tum' olabiliyor; birlestirme oncesi tip esitlenir
    r["pencere"] = r.pencere.astype(str)
    y["pencere"] = y.pencere.astype(str)

    m = y.merge(r, on=ANAHTAR, suffixes=("_yeni", "_ref"))
    if len(m) != len(y):
        # Kural 5: eksik eslesme sessizce kucuk bir kiyasa donusmez
        raise SystemExit(f"eslesme bozuk: {len(y)} yeni hucre, {len(m)} eslesti. "
                         f"Iki log ayni hucre kumesini icermiyor.")

    var = [c for c in KIYAS if f"{c}_yeni" in m.columns]
    fark = []
    for c in var:
        ayni = m[f"{c}_yeni"] == m[f"{c}_ref"]
        for _, s in m[~ayni].iterrows():
            g, n = s[f"{c}_ref"], s[f"{c}_yeni"]
            fark.append(dict(alan=c, test_yil=s.test_yil, model=s.model,
                             beklenen_nondet=s.model in beklenen,
                             referans=g, yeni=n, fark=n - g,
                             bagil=(n - g) / g if g else float("nan")))

    pd.set_option("display.width", 250, "display.max_columns", 60,
                  "display.max_rows", None)
    print(f"referans    : {a.referans}")
    print(f"yeni        : {a.yeni}")
    print(f"hucre       : {len(m)}")
    print(f"kiyaslanan  : {len(var)} alan -> {len(m) * len(var)} karsilastirma")
    print(f"alanlar     : {var}")
    print(f"nondet bekl.: {sorted(beklenen)}")
    print()

    ozet = m[["test_yil", "model"]].copy()
    for c in ("RMSE", "MAE", "R2"):
        if f"{c}_ref" in m.columns:
            ozet[c] = m[f"{c}_ref"]
            ozet[f"{c}_fark"] = m[f"{c}_yeni"] - m[f"{c}_ref"]
    ozet["egitim_n_fark"] = m["egitim_n_yeni"] - m["egitim_n_ref"]
    print(ozet.sort_values(["test_yil", "model"]).to_string(
        index=False, formatters={"RMSE": "{:.12f}".format,
                                 "MAE": "{:.12f}".format,
                                 "R2": "{:.12f}".format,
                                 "RMSE_fark": "{: .3e}".format,
                                 "MAE_fark": "{: .3e}".format,
                                 "R2_fark": "{: .3e}".format}))
    print()

    if not fark:
        print(f"BIREBIR AYNI - {len(m) * len(var)} karsilastirma, sifir fark")
        return 0

    f = pd.DataFrame(fark)
    beklenmeyen = f[~f.beklenen_nondet]
    print(f"FARKLI ALAN: {len(f)}  (beklenen {int(f.beklenen_nondet.sum())}, "
          f"BEKLENMEYEN {len(beklenmeyen)})")
    print(f.to_string(index=False,
                      formatters={"referans": "{:.17g}".format,
                                  "yeni": "{:.17g}".format,
                                  "fark": "{: .6e}".format,
                                  "bagil": "{: .3e}".format}))
    if len(beklenmeyen):
        print()
        print("DUR - beklenen nondeterminist modeller DISINDA fark var. "
              "Degisiklik davranisi kimildatmis olabilir; 'kucuk fark' diye "
              "gecilmez.")
        return 1
    print()
    print(f"Fark yalnizca {sorted(set(f.model))} icinde - bilinen "
          f"nondeterminizm, bkz. arac/nondeterminizm.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
