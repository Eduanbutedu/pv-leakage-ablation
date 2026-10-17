#!/usr/bin/env python3
"""Iki sonuc tablosunun TOLERANSSIZ kiyasi - bayt, alan, negatif kontrol.

`arac/uc_dm.py` ve `arac/dm_yil.py` yeniden urettikleri tabloyu repodaki
haliyle bu modul uzerinden kiyaslar; mantik tek yerde durur, kopyalanmaz.

Uc katman:
  1) BAYT     iki dosya bayt bayt ayni mi. En guclu kanit; tutmazsa alan
              kiyasi farkin nerede oldugunu gosterir.
  2) ALAN     anahtar uzerinden birlestirip her alani `==` ile kiyaslar
              (NaN == NaN esit sayilir). Satir sirasi ayrica kontrol edilir.
              Okuma `float_precision="round_trip"` ile: pandas'in varsayilan
              ayristiricisi son basamakta kayiplidir ve 1 ULP'lik bir farki
              iki tarafta ayni float'a esleyip GIZLEYEBILIR (uc_dm'nin ilk
              negatif kontrolu bunu gosterdi).
  3) NEGATIF  her kiyasta referansin kendisi uzerinde kosar: dokunulmamis
     KONTROL  oku-yaz sifir fark vermeli, tek bir sayisal alani 1 ULP
              (np.nextafter) kaydirmak TAM BIR fark vermeli. Ikisinden biri
              tutmazsa kiyas islevsizdir ve hata firlatilir - yesil yanan
              ama hicbir seyi yakalayamayan bir kapi istemiyoruz.

Rapor CSV'si (opsiyonel): her (anahtar, alan) icin referans ve yeni degerin
repr'i ve esitlik bayragi - sonuclar/ altina dogrulama kaydi olarak.

Kullanim:
    python -m arac.csv_karsilastir --yeni A.csv --referans B.csv \\
        --anahtar test_yil,model_a,model_b [--rapor rapor.csv]
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd


def oku(yol: Path) -> pd.DataFrame:
    return pd.read_csv(yol, float_precision="round_trip")


def _goster(v) -> str:
    """Tam hassasiyetli repr; numpy skaleri duz Python degerine indirilir."""
    return repr(v.item() if hasattr(v, "item") else v)


def alan_farklari(ref: pd.DataFrame, yeni: pd.DataFrame,
                  anahtar: list[str]) -> tuple[pd.DataFrame, bool]:
    """Alan alan kiyas. Donus: (her alan icin satir, satir sirasi ayni mi)."""
    if list(ref.columns) != list(yeni.columns):
        raise ValueError(f"sutunlar farkli:\n  ref : {list(ref.columns)}\n"
                         f"  yeni: {list(yeni.columns)}")
    if len(ref) != len(yeni):
        raise ValueError(f"satir sayisi farkli: ref {len(ref)}, yeni {len(yeni)}")
    if ref[anahtar].duplicated().any():
        raise ValueError(f"anahtar {anahtar} referansta tekil degil")
    sira_ayni = ref[anahtar].equals(yeni[anahtar])
    m = ref.merge(yeni, on=anahtar, suffixes=("_ref", "_yeni"), validate="1:1")
    if len(m) != len(ref):
        raise ValueError("anahtarlar eslesmedi")

    satir = []
    for c in (c for c in ref.columns if c not in anahtar):
        r, y = m[f"{c}_ref"], m[f"{c}_yeni"]
        esit = ((r == y) | (r.isna() & y.isna())).to_numpy()
        for i in range(len(m)):
            satir.append({
                **{k: m.loc[i, k] for k in anahtar},
                "alan": c,
                "referans": _goster(r.iloc[i]),
                "yeni": _goster(y.iloc[i]),
                "esit": bool(esit[i]),
            })
    return pd.DataFrame(satir), sira_ayni


def negatif_kontrol(referans: Path, anahtar: list[str]) -> None:
    """Kiyasin 1 ULP'yi yakalayabildigini referansin kendisi uzerinde sinar."""
    ref = oku(referans)
    sayisal = [c for c in ref.columns
               if c not in anahtar and pd.api.types.is_float_dtype(ref[c])
               and ref[c].notna().any()]
    if not sayisal:
        raise ValueError("negatif kontrol icin sayisal alan yok")
    with tempfile.TemporaryDirectory() as gecici:
        yol = Path(gecici) / "nk.csv"

        ref.to_csv(yol, index=False)
        d, _ = alan_farklari(ref, oku(yol), anahtar)
        if not d["esit"].all():
            raise AssertionError(
                f"NEGATIF KONTROL: dokunulmamis oku-yaz {int((~d['esit']).sum())} "
                "fark verdi; okuma yolu kayipli")

        bozuk = ref.copy()
        c = sayisal[0]
        i = int(np.flatnonzero(bozuk[c].notna().to_numpy())[0])
        bozuk.loc[i, c] = np.nextafter(bozuk.loc[i, c], np.inf)
        bozuk.to_csv(yol, index=False)
        d, _ = alan_farklari(ref, oku(yol), anahtar)
        if int((~d["esit"]).sum()) != 1:
            raise AssertionError(
                f"NEGATIF KONTROL: 1 ULP bozulma {int((~d['esit']).sum())} fark "
                "verdi, 1 bekleniyordu; kiyas islevsiz")
    print(f"  negatif kontrol   : gecti (oku-yaz 0 fark; `{c}` +1 ULP -> 1 fark)")


def karsilastir(yeni: Path, referans: Path, anahtar: list[str],
                rapor: Path | None = None) -> int:
    """Bayt + alan kiyasi ve negatif kontrol. Tam esitlikte 0, aksi 1."""
    print(f"\nKIYAS  {Path(yeni).name}  vs  {Path(referans).name}")
    negatif_kontrol(referans, anahtar)

    bayt_ayni = Path(yeni).read_bytes() == Path(referans).read_bytes()
    d, sira_ayni = alan_farklari(oku(referans), oku(yeni), anahtar)
    farkli = d[~d["esit"]]
    satir_n = len(d[anahtar].drop_duplicates())
    alan_n = d["alan"].nunique()

    print(f"  bayt duzeyinde    : {'AYNI' if bayt_ayni else 'FARKLI'}")
    print(f"  satir sirasi ayni : {sira_ayni}")
    print(f"  alan              : {satir_n} satir x {alan_n} alan = {len(d)}")
    print(f"  birebir           : {len(d) - len(farkli)}/{len(d)}")
    if len(farkli):
        print("  FARKLI ALANLAR:")
        print(farkli.to_string(index=False))
    if rapor is not None:
        d.to_csv(rapor, index=False)
        print(f"  rapor             : {rapor}")
    return 0 if (bayt_ayni and sira_ayni and farkli.empty) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--yeni", required=True)
    ap.add_argument("--referans", required=True)
    ap.add_argument("--anahtar", required=True, help="virgullu anahtar sutunlari")
    ap.add_argument("--rapor", default=None)
    a = ap.parse_args()
    return karsilastir(Path(a.yeni), Path(a.referans), a.anahtar.split(","),
                       Path(a.rapor) if a.rapor else None)


if __name__ == "__main__":
    raise SystemExit(main())
