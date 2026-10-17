"""Makale Tablo 5-9: sonuc CSV'lerinden yeniden uret, makaleyle kiyasla.

`arac/` statusundedir: hicbir model egitmez, hicbir deney kosmaz; yalnizca
`sonuclar/` altindaki loglari okur. Makaledeki degerler asagida, makalede
YAZILDIKLARI hassasiyetle gomuludur (kaynak: calisma taslagi v0.16;
tablo sayilari ACM v1.0 ile ayni). Kiyas toleranssizdir: yeniden uretilen
deger ayni ondalik sayisina yuvarlanir ve METIN olarak esit olmak zorundadir
(`sekiller/sekil_uret.py:kontrol_et` ile ayni kural).

Tutmayan her deger raporlanir; en az biri tutmazsa betik 1 ile doner.

Tablo -> kaynak
    5  sonuclar/ablasyon.csv                     varyant ortalamalari
    6  ablasyon.csv, ablasyon_pvgis_indirgenmis.csv, ablasyon_dkasc.csv
    7  ablasyon_belirsizlik_dm_{ana,pvgis_indirgenmis,dkasc}_dm.csv (A_model)
    8  doygunluk_ozet_egri.csv                   (ozet.py, on-kayitli)
    9  doygunluk_ozet_varyans.csv                (ozet.py, on-kayitli)

Tanimlar (makaleyle birebir; ikisi de once dogrulandi)
    oran      hucre basina RMSE_varyant / RMSE_temiz, sonra ORTALAMA
              (ortalamalarin orani DEGIL - eszaman'da 0,0469 vs 0,0465)
    R2 kazanc ortalama R2_varyant - ortalama R2_temiz
    A yuzde   rastgele_kfold A_model'in test yili ortalamasi / kapasite x 100
    Tablo 7 orani  A_yuzde(DKASC) / A_yuzde(PVGIS tam)

Kosma (kok dizinden):
    .venv\\Scripts\\python.exe -m arac.tablolari_uret
"""

from __future__ import annotations

import sys

import pandas as pd

from pv10.config import DKASC_KAPASITE_W, KAPASITE_W, SONUC

VARYANT_AD = {  # makale satir adi -> log varyant adi
    "clean": "temiz",
    "contemporaneous": "eszaman",
    "night": "gece",
    "shuffled split": "rastgele_kfold",
    "global scaling": "olcekleyici",
    "worst case": "enkotu",
}

# --- makaledeki degerler (v0.16), yazildiklari hassasiyetle ------------------

TABLO5 = {  # varyant: (RMSE, oran, R2 kazanc)  ; "-" ve "~0" ayri ele alinir
    "clean": ("138.1468", "1.0000", None),
    "contemporaneous": ("6.4777", "0.0465", "+0.2715"),
    "night": ("98.1564", "0.7105", "+0.1251"),
    "shuffled split": ("136.6343", "0.9891", "+0.0071"),
    "global scaling": ("138.2083", "1.0004", "~0"),
    "worst case": ("4.6140", "0.0331", "+0.2719"),
}
TABLO5_REFERANS_R2 = "0.728"

TABLO6 = {  # varyant: (PVGIS tam, PVGIS indirgenmis, DKASC)
    "contemporaneous": ("0.0465", "0.0692", "0.2082"),
    "shuffled split": ("0.9891", "0.9906", "0.9179"),
    "night": ("0.7105", "0.7099", "0.7078"),
    "global scaling": ("1.0004", "1.0000", "1.0016"),
    "worst case": ("0.0331", "0.0488", "0.2170"),
}

TABLO7 = {  # model: (PVGIS tam, PVGIS indirgenmis, DKASC, oran)
    "Linear Regression": ("-0.0050", "-0.0048", "-0.0527", "10.5"),
    "Polynomial Ridge": ("-0.1088", "-0.0800", "-0.6118", "5.6"),
    "Hist Gradient Boosting": ("-0.6309", "-0.6109", "-2.4122", "3.8"),
}
TABLO7_MANSET = ("Hist Gradient Boosting", "3.82")  # tablo altyazisi

TABLO8 = {  # pencere: (altornekleme, kaydirmali, marjinal kazanc)
    "1": ("140.3506", "141.4722", None),
    "2": ("139.2749", "139.6685", "1.0757"),
    "3": ("138.7122", "138.8771", "0.5627"),
    "5": ("138.3580", "138.3765", "0.3542"),
    "tum": ("138.1457", "138.1457", "0.2124"),
}

TABLO9 = {  # kaynak satiri -> deger; "Remaining" uc etkilesimin toplami
    "Test year": "48.4868",
    "Algorithm": "25.2170",
    "Training volume": "15.2722",
    "Volume x algorithm": "9.7175",
    "Remaining interactions": "1.3064",
}
TABLO9_KAYNAK = {
    "Test year": ["test_yil (yil)"],
    "Algorithm": ["model (algoritma)"],
    "Training volume": ["pencere (veri hacmi)"],
    "Volume x algorithm": ["pencere x model"],
    "Remaining interactions": [
        "artik (uclu etkilesim)", "model x test_yil", "pencere x test_yil",
    ],
}

# Tablo 6 / Tablo 7 kaynaklari: sutun -> (ablasyon logu, dm dosyasi, kapasite)
KAYNAKLAR = {
    "PVGIS tam": ("ablasyon.csv", "ablasyon_belirsizlik_dm_ana_dm.csv", KAPASITE_W),
    "PVGIS indirgenmis": (
        "ablasyon_pvgis_indirgenmis.csv",
        "ablasyon_belirsizlik_dm_pvgis_indirgenmis_dm.csv",
        KAPASITE_W,
    ),
    "DKASC": ("ablasyon_dkasc.csv", "ablasyon_belirsizlik_dm_dkasc_dm.csv", DKASC_KAPASITE_W),
}
BEKLENEN_HUCRE = {"PVGIS tam": 21, "PVGIS indirgenmis": 21, "DKASC": 15}


# --- kiyas ------------------------------------------------------------------

SONUCLAR: list[dict] = []


def kiyasla(tablo: str, alan: str, gozlenen: float, beklenen: str) -> None:
    """Gozleneni beklenenin YAZILDIGI ondalik sayisinda metin olarak kiyaslar."""
    if beklenen == "~0":
        # makale burada sayi vermiyor; mutlak deger dort ondalikta
        # gosterilemeyecek kadar kucuk olmali iddiasi olarak okunur
        bulunan = f"{gozlenen:+.4f}"
        tutar = abs(gozlenen) < 0.0005
    else:
        ondalik = len(beklenen.split(".")[1]) if "." in beklenen else 0
        isaret = "+" if beklenen.startswith("+") else ""
        bulunan = f"{gozlenen:{isaret}.{ondalik}f}"
        tutar = bulunan == beklenen
    SONUCLAR.append({
        "tablo": tablo, "alan": alan, "makale": beklenen, "yeniden": bulunan,
        "tam_hassasiyet": repr(float(gozlenen)), "tutuyor": tutar,
    })


def varyant_ozeti(log: str, beklenen_hucre: int) -> pd.DataFrame:
    """Varyant basina ortalama RMSE, hucre-oran ortalamasi, R2 kazanci."""
    a = pd.read_csv(SONUC / log)
    sayim = a.groupby("varyant").size()
    if set(sayim.index) != set(VARYANT_AD.values()) or (sayim != beklenen_hucre).any():
        raise ValueError(f"{log}: varyant basina {beklenen_hucre} hucre beklenir\n{sayim}")
    temiz = a[a["varyant"] == "temiz"].set_index(["model", "test_yil"])
    a = a.set_index(["model", "test_yil"])
    satir = {}
    for v, g in a.groupby("varyant"):
        oran = g["RMSE"] / temiz["RMSE"].reindex(g.index)
        if oran.isna().any():
            raise ValueError(f"{log}/{v}: temiz hucresi eslesmedi")
        satir[v] = {
            "RMSE": g["RMSE"].mean(),
            "oran": oran.mean(),
            "R2": g["R2"].mean(),
        }
    d = pd.DataFrame(satir).T
    d["R2_kazanc"] = d["R2"] - d.loc["temiz", "R2"]
    return d


def tablo5() -> None:
    d = varyant_ozeti(*KAYNAKLAR["PVGIS tam"][:1], BEKLENEN_HUCRE["PVGIS tam"])
    for ad, (rmse, oran, r2) in TABLO5.items():
        s = d.loc[VARYANT_AD[ad]]
        kiyasla("5", f"{ad} RMSE", s["RMSE"], rmse)
        kiyasla("5", f"{ad} oran", s["oran"], oran)
        if r2 is not None:
            kiyasla("5", f"{ad} R2 kazanc", s["R2_kazanc"], r2)
    kiyasla("5", "referans R2 (altyazi)", d.loc["temiz", "R2"], TABLO5_REFERANS_R2)


def tablo6() -> None:
    ozet = {k: varyant_ozeti(v[0], BEKLENEN_HUCRE[k]) for k, v in KAYNAKLAR.items()}
    for ad, degerler in TABLO6.items():
        for kaynak, bek in zip(KAYNAKLAR, degerler):
            kiyasla("6", f"{ad} / {kaynak}", ozet[kaynak].loc[VARYANT_AD[ad], "oran"], bek)


def tablo7() -> None:
    a_yuzde = {}
    for kaynak, (_, dm, kapasite) in KAYNAKLAR.items():
        d = pd.read_csv(SONUC / dm)
        r = d[d["varyant"] == "rastgele_kfold"]
        for model in TABLO7:
            m = r[r["model"] == model]
            if len(m) != BEKLENEN_HUCRE[kaynak] // 3:
                raise ValueError(f"{dm}/{model}: {len(m)} yil")
            a_yuzde[(kaynak, model)] = m["A_model"].mean() / kapasite * 100.0
    for model, (*degerler, oran) in TABLO7.items():
        for kaynak, bek in zip(KAYNAKLAR, degerler):
            kiyasla("7", f"{model} / {kaynak}", a_yuzde[(kaynak, model)], bek)
        kiyasla("7", f"{model} oran", a_yuzde[("DKASC", model)] / a_yuzde[("PVGIS tam", model)], oran)
    model, bek = TABLO7_MANSET
    kiyasla("7", f"manset oran (altyazi, {model})",
            a_yuzde[("DKASC", model)] / a_yuzde[("PVGIS tam", model)], bek)


def tablo8() -> None:
    e = pd.read_csv(SONUC / "doygunluk_ozet_egri.csv", dtype={"pencere": str})
    if (e["hucre"] != 15).any() or len(e) != 10:
        raise ValueError("doygunluk_ozet_egri.csv: 2 kol x 5 pencere x 15 hucre beklenir")
    alt = e[e["kol"] == "altornekleme"].set_index("pencere")["RMSE"]
    kay = e[e["kol"] == "kaydirmali"].set_index("pencere")["RMSE"]
    onceki = None
    for p, (a_bek, k_bek, marj_bek) in TABLO8.items():
        kiyasla("8", f"altornekleme K={p}", alt[p], a_bek)
        kiyasla("8", f"kaydirmali K={p}", kay[p], k_bek)
        if marj_bek is not None:
            kiyasla("8", f"marjinal kazanc K={p}", alt[onceki] - alt[p], marj_bek)
        onceki = p


def tablo9() -> None:
    v = pd.read_csv(SONUC / "doygunluk_ozet_varyans.csv").set_index("kaynak")["varyans_payi_yuzde"]
    kullanilan = [k for ks in TABLO9_KAYNAK.values() for k in ks]
    if sorted(kullanilan) != sorted(v.index):
        raise ValueError(f"varyans tablosu satirlari beklenenden farkli: {list(v.index)}")
    if abs(v.sum() - 100.0) > 1e-9:
        raise ValueError(f"varyans paylari 100'e toplanmiyor: {v.sum()!r}")
    for satir, bek in TABLO9.items():
        kiyasla("9", satir, v[TABLO9_KAYNAK[satir]].sum(), bek)


def main() -> int:
    for f in (tablo5, tablo6, tablo7, tablo8, tablo9):
        f()
    d = pd.DataFrame(SONUCLAR)
    with pd.option_context("display.width", 200, "display.max_rows", 200):
        print(d.to_string(index=False))
    print()
    for t, g in d.groupby("tablo"):
        print(f"Tablo {t}: {int(g['tutuyor'].sum())}/{len(g)} tutuyor")
    bozuk = d[~d["tutuyor"]]
    if len(bozuk):
        print(f"\nTUTMAYAN {len(bozuk)} DEGER:")
        print(bozuk.to_string(index=False))
        return 1
    print(f"\nToplam {len(d)}/{len(d)} deger makaleyle birebir.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
