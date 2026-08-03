#!/usr/bin/env python3
"""Nondeterminizm olcumunun karari.

YORUM KURALI SONUC GORULMEDEN yazildi - hangi sonucun neye yorulacagi
olcum kosulmadan sabitlendi ki cikan sayiya gore secim yapilmasin:

  A'da fark VAR          -> surec ICI nondeterminizm; acik madde kapanir,
                            sebep paralel hesap
  A ayni, B'de fark VAR  -> SUREC duzeyi (thread/havuz atamasi); kapanir,
                            pyarrow degil
  A ve B ayni            -> supheyi pyarrow'a KAYDIRAMAYIZ, cunku 25.0.0'a
                            donulemiyor (Smart App Control blogu). ACIK MADDE
                            kalir ve "olculemedi" diye yazilir - tahmin
                            yurutulmez

Kontrol modeli (Neural Network) icin ayni kural anlamli DEGILDIR: orada
beklenen sonuc "A ve B ayni"dir ve bu, duzenegin yapay fark uretmedigini
gosterir. Kontrolun kendisi farkli cikarsa olcum degersizdir.
"""
import sys

import pandas as pd

from pv10.config import SONUC

CIKTI = SONUC / "nondeterminizm_olcum.csv"
KONTROL = "Neural Network"


def karar(a_farkli: bool, b_farkli: bool) -> str:
    if a_farkli:
        return ("A'da fark VAR -> surec ICI nondeterminizm. Acik madde KAPANIR; "
                "sebep paralel hesap, pyarrow degil.")
    if b_farkli:
        return ("A ayni, B'de fark VAR -> SUREC duzeyi (thread/havuz atamasi). "
                "Acik madde KAPANIR; pyarrow degil.")
    return ("A ve B ayni -> supheyi pyarrow'a KAYDIRAMAYIZ: 25.0.0'a donulemiyor "
            "(SAC blogu). ACIK MADDE kalir, 'olculemedi' diye yazilir.")


def main() -> int:
    if not CIKTI.exists():
        raise SystemExit(f"{CIKTI} yok - once arac/nondeterminizm.py kosun.")
    d = pd.read_csv(CIKTI)
    pd.set_option("display.width", 250, "display.max_columns", 40,
                  "display.max_rows", None)

    print("HAM OLCUM")
    print(d[["surec", "tekrar", "model", "pid", "pyarrow", "n", "RMSE",
             "tahmin_sha"]].to_string(index=False))
    print()

    # Kural 5: y ve persistence modelden bagimsiz olmali. Oynuyorlarsa sorun
    # modelde DEGIL test setindedir ve karar tablosu yaniltir - sessiz gecilmez.
    for c in ("y_sha", "pers_sha"):
        if d[c].nunique() != 1:
            print(f"DUR - {c} satirlar arasi degisiyor; sorun modelde DEGIL, "
                  f"test verisinde:\n{d[[c, 'surec', 'tekrar', 'model']]}")
            return 1
    print(f"y_sha / pers_sha tum satirlarda tek deger: test seti sabit  "
          f"(y {d.y_sha.iloc[0][:16]}, pers {d.pers_sha.iloc[0][:16]})")
    print()

    sat = []
    for model_ad, g in d.groupby("model", sort=False):
        # A: her surecin KENDI icinde tekrarlar arasi fark
        a_farkli = any(gs.sort_values("tekrar").tahmin_sha.nunique() > 1
                       for _, gs in g.groupby("surec"))
        # B: surecler arasi, ilk tekrarlar
        b_farkli = g[g.tekrar == 1].tahmin_sha.nunique() > 1
        sat.append(dict(model=model_ad, kontrol=model_ad == KONTROL,
                        A_surec_ici_farkli=a_farkli,
                        B_surecler_arasi_farkli=b_farkli,
                        farkli_sha_sayisi=g.tahmin_sha.nunique(),
                        farkli_RMSE_sayisi=g.RMSE.nunique(),
                        tekrar_sayisi=len(g)))
    o = pd.DataFrame(sat)
    print("DUZEY OZETI")
    print(o.to_string(index=False))
    print()

    k = o[o.kontrol]
    if len(k) and bool(k.iloc[0].farkli_sha_sayisi > 1):
        print(f"DUZENEK GECERSIZ - kontrol modeli ({KONTROL}) da farkli hash "
              f"veriyor. Fark modele ozgu degil; karar tablosu okunmaz.")
        return 1
    if len(k):
        print(f"Kontrol tanigi ({KONTROL}): {k.iloc[0].tekrar_sayisi} kosuda "
              f"tek hash - duzenek yapay fark uretmiyor.")
        print()

    for _, r in o[~o.kontrol].iterrows():
        print(f"{r.model}:")
        print(f"  {karar(r.A_surec_ici_farkli, r.B_surecler_arasi_farkli)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
