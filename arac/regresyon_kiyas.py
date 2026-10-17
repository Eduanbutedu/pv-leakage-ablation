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

Faz 2 (ablasyon) logu farkli anahtarlanir; --anahtar ile verilir:
    python -m arac.regresyon_kiyas --referans sonuclar/ablasyon.csv \\
        --yeni sonuclar/ablasyon_regresyon.csv \\
        --anahtar varyant,model,test_yil --nondet ""

Ilk kosu: 3 Agustos 2026, dm_kalan (pyarrow 22.0.0) vs genis (25.0.0).
40 hucre x 13 alan = 520 karsilastirma, 510'u birebir. Farkli cikan 10
alanin hepsi 1-2 ULP ve yalnizca Random Forest ile Extra Trees'te; sekiz
model tam esit. Sebep surec ici paralel hesap, surum degil - olcumu
arac/nondeterminizm.py yapti.

Okuma ve negatif kontrol [17 Ekim 2026'da eklendi]:
  Loglar `arac/csv_karsilastir.oku` ile `float_precision="round_trip"`
  okunur. Ilk surum pandas'in varsayilan ayristiricisini kullaniyordu; o
  son basamakta kayiplidir ve 1 ULP'lik bir farki iki tarafta ayni float'a
  esleyip gizleyebilir. Her kosuda iki negatif kontrol, BU betigin kendi
  kiyas yolu (`hazirla` + `farklari_bul`) uzerinden kosar: (1) yeni logun
  dokunulmamis oku-yaz turu fark kumesini degistirmemeli; (2) nondet
  OLMAYAN bir modelin tek bir sayisal alanini 1 ULP kaydirmak TAM BIR yeni
  beklenmeyen fark uretmeli. Tutmazsa kiyas islevsizdir, hata firlatilir.

  Bayt kiyasi burada YAPILMAZ: iki log farkli kosulardan gelir; `egitim_sn`
  gibi sure alanlari ve hucre kumeleri farklidir, bayt esitligi beklenmez.

  `--kayit <csv>` kosunun ozet satirini dosyaya EKLER (dogrulama kaydi).
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from arac.csv_karsilastir import oku

ANAHTAR = ["kol", "pencere", "test_yil", "model", "tohum"]
KIYAS = ["egitim_n", "n", "RMSE", "MAE", "R2", "nRMSE_kapasite",
         "nRMSE_ortalama", "skill", "isinma", "egitim_basla",
         "RMSE_persistence", "RMSE_GA_alt", "RMSE_GA_ust"]
FARK_SUTUN = ["alan", "test_yil", "model", "beklenen_nondet",
              "referans", "yeni", "fark", "bagil"]


def hazirla(r: pd.DataFrame, y: pd.DataFrame,
            anahtar: list[str]) -> pd.DataFrame:
    """Durum filtresi, pencere tipi, anahtar uzerinden birlestirme."""
    # `durum` yalnizca Faz 4 izgarasinda var; olmadiginda filtre atlanir
    if "durum" in r.columns and "durum" in y.columns:
        r, y = r[r.durum == "tamam"], y[y.durum == "tamam"]
    # pencere hem int hem 'tum' olabiliyor; birlestirme oncesi tip esitlenir
    if "pencere" in r.columns and "pencere" in y.columns:
        r, y = r.copy(), y.copy()
        r["pencere"] = r.pencere.astype(str)
        y["pencere"] = y.pencere.astype(str)

    eksik = [c for c in anahtar if c not in r.columns or c not in y.columns]
    if eksik:
        raise SystemExit(f"anahtar sutunlari loglarda yok: {eksik}")

    m = y.merge(r, on=anahtar, suffixes=("_yeni", "_ref"))
    if len(m) != len(y):
        # Kural 5: eksik eslesme sessizce kucuk bir kiyasa donusmez
        raise SystemExit(f"eslesme bozuk: {len(y)} yeni hucre, {len(m)} eslesti. "
                         f"Iki log ayni hucre kumesini icermiyor.")
    return m


def kiyas_alanlari(m: pd.DataFrame) -> list[str]:
    return [c for c in KIYAS if f"{c}_yeni" in m.columns]


def farklari_bul(m: pd.DataFrame, beklenen: set[str]) -> pd.DataFrame:
    """Alan alan `==` (NaN == NaN esit). Her fark tam hassasiyetle."""
    fark = []
    for c in kiyas_alanlari(m):
        a, b = m[f"{c}_yeni"], m[f"{c}_ref"]
        ayni = (a == b) | (a.isna() & b.isna())
        for _, s in m[~ayni].iterrows():
            g, n = s[f"{c}_ref"], s[f"{c}_yeni"]
            fark.append(dict(alan=c, test_yil=s.test_yil, model=s.model,
                             beklenen_nondet=s.model in beklenen,
                             referans=g, yeni=n, fark=n - g,
                             bagil=(n - g) / g if g else float("nan")))
    return pd.DataFrame(fark, columns=FARK_SUTUN)


def negatif_kontrol(r: pd.DataFrame, y: pd.DataFrame, anahtar: list[str],
                    beklenen: set[str], fark: pd.DataFrame) -> str:
    """Kiyasin 1 ULP'yi yakaladigini KENDI kod yolu uzerinden sinar."""
    with tempfile.TemporaryDirectory() as gecici:
        yol = Path(gecici) / "nk.csv"

        # (1) dokunulmamis oku-yaz: fark kumesi degismemeli
        y.to_csv(yol, index=False)
        f1 = farklari_bul(hazirla(r, oku(yol), anahtar), beklenen)
        if len(f1) != len(fark):
            raise AssertionError(
                f"NEGATIF KONTROL: dokunulmamis oku-yaz {len(fark)} farki "
                f"{len(f1)}'e cevirdi; okuma yolu kayipli")

        # (2) nondet olmayan bir modelin tek alani +1 ULP: tam 1 yeni fark
        m = hazirla(r, y, anahtar)
        aday = [c for c in kiyas_alanlari(m) if pd.api.types.is_float_dtype(y[c])]
        tamam = y["durum"] == "tamam" if "durum" in y.columns else True
        satir = y.index[(~y["model"].isin(beklenen)) & tamam]
        if not aday or not len(satir):
            raise ValueError("negatif kontrol icin uygun alan/satir yok")
        c, i = aday[0], satir[0]
        bozuk = y.copy()
        bozuk.loc[i, c] = np.nextafter(bozuk.loc[i, c], np.inf)
        bozuk.to_csv(yol, index=False)
        f2 = farklari_bul(hazirla(r, oku(yol), anahtar), beklenen)
        artis = int((~f2.beklenen_nondet).sum()) - int((~fark.beklenen_nondet).sum())
        if artis != 1:
            raise AssertionError(
                f"NEGATIF KONTROL: `{c}` +1 ULP {artis} yeni beklenmeyen fark "
                "verdi, 1 bekleniyordu; kiyas islevsiz")
    return f"gecti (oku-yaz fark kumesini korudu; `{c}` +1 ULP -> 1 yeni fark)"


def kayit_yaz(yol: Path, a, anahtar: list[str], hucre: int, alan_n: int,
              f: pd.DataFrame, nk: str) -> None:
    bek = f[~f.beklenen_nondet]
    satir = pd.DataFrame([{
        "referans": Path(a.referans).as_posix(),
        "yeni": Path(a.yeni).as_posix(),
        "anahtar": ",".join(anahtar),
        "nondet": a.nondet,
        "hucre": hucre,
        "alan": alan_n,
        "karsilastirma": hucre * alan_n,
        "birebir": hucre * alan_n - len(f),
        "fark": len(f),
        "fark_beklenen_nondet": int(f.beklenen_nondet.sum()),
        "fark_beklenmeyen": len(bek),
        "fark_modeller": ";".join(sorted(set(f.model))),
        "maks_bagil_fark": float(f.bagil.abs().max()) if len(f) else 0.0,
        "okuma": "round_trip",
        "negatif_kontrol": nk,
    }])
    satir.to_csv(yol, mode="a", header=not yol.exists(), index=False)


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
    ap.add_argument("--anahtar", default=",".join(ANAHTAR),
                    help="hucreyi tanimlayan sutunlar, virgullu; varsayilan "
                         "Faz 4 izgarasi. Faz 2 icin: varyant,model,test_yil")
    ap.add_argument("--kayit", default=None,
                    help="ozet satirini bu CSV'ye EKLE (dogrulama kaydi)")
    a = ap.parse_args()

    beklenen = {m.strip() for m in a.nondet.split(",") if m.strip()}
    anahtar = [c.strip() for c in a.anahtar.split(",") if c.strip()]
    r = oku(Path(a.referans))
    y = oku(Path(a.yeni))
    m = hazirla(r, y, anahtar)
    var = kiyas_alanlari(m)
    f = farklari_bul(m, beklenen)
    nk = negatif_kontrol(r, y, anahtar, beklenen, f)

    pd.set_option("display.width", 250, "display.max_columns", 60,
                  "display.max_rows", None)
    print(f"referans    : {a.referans}")
    print(f"yeni        : {a.yeni}")
    print(f"anahtar     : {anahtar}")
    print(f"hucre       : {len(m)}")
    print(f"kiyaslanan  : {len(var)} alan -> {len(m) * len(var)} karsilastirma")
    print(f"alanlar     : {var}")
    print(f"nondet bekl.: {sorted(beklenen)}")
    print("okuma       : float_precision=round_trip")
    print(f"negatif kon.: {nk}")
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

    if a.kayit:
        kayit_yaz(Path(a.kayit), a, anahtar, len(m), len(var), f, nk)

    if f.empty:
        print(f"BIREBIR AYNI - {len(m) * len(var)} karsilastirma, sifir fark")
        return 0

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
