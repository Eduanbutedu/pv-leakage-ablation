"""F1 ogrenme egrisi sekli icin cizim verisi - iki CSV.

Bu betik SUNUM icindir, DENEY DEGILDIR. `sekil_uret.py` ile ayni statude:
hicbir model egitmez, yalnizca `sonuclar/doygunluk.csv`'yi okur.

Degerler `sekil_uret.py`'nin KENDI fonksiyonlarindan (`doygunluk_oku`,
`egri`) gelir; kopya yok. Boylece CSV'deki sayilar F1'de cizilenlerle yapi
geregi ayni kod yolundan gecer. Ayni gomulu kontroller (Tablo 8 ve model
span'leri) uygulanir; biri tutmazsa CSV YAZILMAZ (CLAUDE.md kural 5).

Ciktilar (`sekiller/F1_veri/`):
    egri_havuz.csv  kol, K, rmse_ort, ga_alt, ga_ust        - F1(a)
    egri_model.csv  model, K, delta_rmse, kol               - F1(b)

`delta_rmse` her modelin KENDI K=1 degerine gore farktir (W); kol yalnizca
altornekleme. K=tum iki kolda paylasilir (bkz. `hucre_ortalamasi`).

Kosma (kok dizinden):
    .venv\\Scripts\\python.exe -m sekiller.f1_veri
"""

from __future__ import annotations

import pandas as pd

from sekiller.sekil_uret import (
    KONTROL_F1A,
    KONTROL_F1B,
    MODEL_KISA,
    MODELLER,
    PENCERELER,
    SEKIL_DIZIN,
    doygunluk_oku,
    egri,
    kontrol_et,
)

VERI_DIZIN = SEKIL_DIZIN / "F1_veri"
KOLLAR = ("altornekleme", "kaydirmali")


def egri_havuz(d: pd.DataFrame) -> pd.DataFrame:
    """F1(a): kol x K, uc model uzerinde havuzlanmis ortalama RMSE ve GA."""
    parca = []
    for kol in KOLLAR:
        e = egri(d, kol)
        if list(e["pencere"]) != list(PENCERELER) or (e["hucre"] != 15).any():
            raise ValueError(f"{kol}: beklenmeyen pencere/hucre yapisi\n{e}")
        parca.append(
            pd.DataFrame(
                {
                    "kol": kol,
                    "K": e["pencere"],
                    "rmse_ort": e["RMSE"],
                    "ga_alt": e["GA_alt"],
                    "ga_ust": e["GA_ust"],
                }
            )
        )
    return pd.concat(parca, ignore_index=True)


def egri_model(d: pd.DataFrame) -> pd.DataFrame:
    """F1(b): model x K, kendi K=1'ine gore RMSE farki, altornekleme kolu."""
    parca = []
    for model in MODELLER:
        e = egri(d, "altornekleme", model)
        if list(e["pencere"]) != list(PENCERELER):
            raise ValueError(f"{model}: beklenmeyen pencere yapisi\n{e}")
        k1 = float(e.loc[e["pencere"] == "1", "RMSE"].iloc[0])
        parca.append(
            pd.DataFrame(
                {
                    "model": MODEL_KISA[model],
                    "K": e["pencere"],
                    "delta_rmse": e["RMSE"] - k1,
                    "kol": "altornekleme",
                }
            )
        )
    return pd.concat(parca, ignore_index=True)


def kontrol(havuz: pd.DataFrame, model: pd.DataFrame) -> None:
    print("F1(a) kontrol - Tablo 8 (W):")
    for kol in KOLLAR:
        alt = havuz[havuz["kol"] == kol]
        for k, bek, got in zip(PENCERELER, KONTROL_F1A[kol], alt["rmse_ort"]):
            kontrol_et(f"egri_havuz {kol} K={k}", got, bek)

    print("\nF1(b) kontrol - K=tum delta (W), span'in eksi isaretlisi:")
    for uzun, bek in KONTROL_F1B.items():
        alt = model[(model["model"] == MODEL_KISA[uzun]) & (model["K"] == "tum")]
        kontrol_et(f"egri_model {MODEL_KISA[uzun]} K=tum", float(alt["delta_rmse"].iloc[0]), f"-{bek}")
        k1 = model[(model["model"] == MODEL_KISA[uzun]) & (model["K"] == "1")]
        if float(k1["delta_rmse"].iloc[0]) != 0.0:
            raise AssertionError(f"{uzun}: K=1 delta sifir degil")


def main() -> None:
    d = doygunluk_oku()
    havuz = egri_havuz(d)
    model = egri_model(d)
    kontrol(havuz, model)

    VERI_DIZIN.mkdir(exist_ok=True)
    for ad, tablo in (("egri_havuz", havuz), ("egri_model", model)):
        yol = VERI_DIZIN / f"{ad}.csv"
        # tam hassasiyet: float_format verilmez, repr yazilir
        tablo.to_csv(yol, index=False)
        print(f"\nyazildi: {yol.relative_to(SEKIL_DIZIN.parent)} ({len(tablo)} satir)")


if __name__ == "__main__":
    main()
