"""Makale Tablo 2 ve 5-9: sonuc CSV'lerinden yeniden uret, makaleyle kiyasla.

`arac/` statusundedir: hicbir model egitmez, hicbir deney kosmaz; yalnizca
`sonuclar/` altindaki loglari okur. Makaledeki degerler asagida, makalede
YAZILDIKLARI hassasiyetle gomuludur (kaynak: calisma taslagi v0.16;
tablo sayilari ACM v1.0 ile ayni; Tablo 6-7'nin "DKASC CdTe" ve "DKASC
poly-Si" sutunlari ile Tablo 7'nin oran araligi v2.2'den, 22 Ekim 2026). Kiyas toleranssizdir: yeniden uretilen
deger ayni ondalik sayisina yuvarlanir ve METIN olarak esit olmak zorundadir
(`sekiller/sekil_uret.py:kontrol_et` ile ayni kural).

Tutmayan her deger raporlanir; en az biri tutmazsa betik 1 ile doner.

Tablo -> kaynak
    2  tanimlayici_istatistik.csv, donem "test"  N, P_kapasite ort +- SD,
                                              carpiklik, G_i ortalamasi
                                              (metin olarak; v2.2)
    5  sonuclar/ablasyon.csv                     varyant ortalamalari
    6  ablasyon.csv, ablasyon_pvgis_indirgenmis.csv,
       ablasyon_dkasc{,_m15a,_m3a}.csv
    7  ablasyon_belirsizlik_dm_{ana,pvgis_indirgenmis,dkasc,dkasc_m15a,
       dkasc_m3a}_dm.csv (A_model)
    8  doygunluk_ozet_egri.csv                   (ozet.py, on-kayitli)
    9  doygunluk_ozet_varyans.csv                (ozet.py, on-kayitli)

Tanimlar (makaleyle birebir; ikisi de once dogrulandi)
    oran      hucre basina RMSE_varyant / RMSE_temiz, sonra ORTALAMA
              (ortalamalarin orani DEGIL - eszaman'da 0,0469 vs 0,0465)
    R2 kazanc ortalama R2_varyant - ortalama R2_temiz
    A yuzde   rastgele_kfold A_model'in test yili ortalamasi / kapasite x 100
    Tablo 7 orani  A_yuzde(olcum dizisi) / A_yuzde(PVGIS tam); makalede
                   ("Ratio, measured / PVGIS full") uc DKASC dizisinin
                   min-maks ARALIGI, 1 ondalik, "a-b" metni olarak kiyaslanir.
                   Altyazi (v2.2): "the headline range is 3.8 to 4.3, from
                   the model with the largest effect" - HGB'nin araligi ve
                   her olcum dizisinde |A| en buyuk modelin HGB oldugu
                   ayrica kontrol edilir. HGB mono-Si orani Bolum 5.3
                   metninde "3.8" olarak gecer; o da kontrol edilir.

Kosma (kok dizinden):
    .venv\\Scripts\\python.exe -m arac.tablolari_uret
"""

from __future__ import annotations

import sys

import pandas as pd

from pv10.config import DKASC_DIZILER, KAPASITE_W, SONUC

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

TABLO6 = {  # varyant: (PVGIS tam, PVGIS indirgenmis, DKASC mono-Si, DKASC CdTe, DKASC poly-Si)
    "contemporaneous": ("0.0465", "0.0692", "0.2082", "0.1319", "0.1641"),
    "shuffled split": ("0.9891", "0.9906", "0.9179", "0.8470", "0.8777"),
    "night": ("0.7105", "0.7099", "0.7078", "0.7065", "0.7082"),
    "global scaling": ("1.0004", "1.0000", "1.0016", "1.0004", "0.9989"),
    "worst case": ("0.0331", "0.0488", "0.2170", "0.0836", "0.1069"),
}

TABLO7 = {  # model: (PVGIS tam, PVGIS indirgenmis, DKASC mono-Si, DKASC CdTe, DKASC poly-Si, oran araligi)
    "Linear Regression": ("-0.0050", "-0.0048", "-0.0527", "-0.1042", "-0.0751", "10.5-20.9"),
    "Polynomial Ridge": ("-0.1088", "-0.0800", "-0.6118", "-0.7481", "-0.6704", "5.6-6.9"),
    "Hist Gradient Boosting": ("-0.6309", "-0.6109", "-2.4122", "-2.5445", "-2.7354", "3.8-4.3"),
}
OLCUM_DIZILERI = ("DKASC mono-Si", "DKASC CdTe", "DKASC poly-Si")
TABLO7_ALTYAZI = ("Hist Gradient Boosting", "3.8 to 4.3")  # v2.2 altyazisi
TABLO7_BOLUM53 = ("Hist Gradient Boosting", "DKASC mono-Si", "3.8")  # 5.3 metni

EKSI = "\u2212"  # makalede eksi isareti U+2212
# Tablo 2 (v2.2), test donemi: satir adi -> (CSV sahasi, N, P ort +- SD, carpiklik, G_i)
TABLO2 = {
    "Ouarzazate": ("ouarzazate", "30,266", "44.0 \u00b1 26.8", EKSI + "0.24", "581"),
    "Portim\u00e3o": ("portimao", "30,113", "39.7 \u00b1 25.9", EKSI + "0.06", "514"),
    "Konya": ("konya", "30,030", "36.9 \u00b1 26.9", "+0.11", "479"),
    "Adana": ("adana", "30,220", "35.3 \u00b1 25.8", "+0.05", "463"),
    "Br\u0103ila": ("braila", "30,260", "30.1 \u00b1 25.6", "+0.43", "388"),
    "Leipzig": ("leipzig", "29,593", "25.5 \u00b1 23.4", "+0.72", "325"),
    "DKASC mono-Si (main)": ("dkasc_m6b", "19,285", "42.9 \u00b1 27.2", EKSI + "0.23", "606"),
    "DKASC CdTe": ("dkasc_m15a", "16,973", "46.2 \u00b1 28.4", EKSI + "0.22", "608"),
    "DKASC poly-Si": ("dkasc_m3a", "19,286", "45.6 \u00b1 28.4", EKSI + "0.23", "606"),
}

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
    "DKASC mono-Si": ("ablasyon_dkasc.csv", "ablasyon_belirsizlik_dm_dkasc_dm.csv",
                      DKASC_DIZILER["m6b"]["kapasite_w"]),
    "DKASC CdTe": ("ablasyon_dkasc_m15a.csv", "ablasyon_belirsizlik_dm_dkasc_m15a_dm.csv",
                   DKASC_DIZILER["m15a"]["kapasite_w"]),
    "DKASC poly-Si": ("ablasyon_dkasc_m3a.csv", "ablasyon_belirsizlik_dm_dkasc_m3a_dm.csv",
                      DKASC_DIZILER["m3a"]["kapasite_w"]),
}
BEKLENEN_HUCRE = {"PVGIS tam": 21, "PVGIS indirgenmis": 21, "DKASC mono-Si": 15,
                  "DKASC CdTe": 15, "DKASC poly-Si": 15}


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


def kiyasla_metin(tablo: str, alan: str, bulunan: str, beklenen: str,
                  tam: str) -> None:
    """Metin olarak uretilmis bir degeri (or. aralik "a-b") makaleyle kiyaslar."""
    SONUCLAR.append({
        "tablo": tablo, "alan": alan, "makale": beklenen, "yeniden": bulunan,
        "tam_hassasiyet": tam, "tutuyor": bulunan == beklenen,
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


def tablo2() -> None:
    t = pd.read_csv(SONUC / "tanimlayici_istatistik.csv", float_precision="round_trip")
    t = t[t["donem"] == "test"].set_index(["saha", "degisken"])
    bekl_saha = {v[0] for v in TABLO2.values()}
    if set(t.index.get_level_values("saha")) != bekl_saha:
        raise ValueError(f"tanimlayici tablo sahalari beklenenden farkli: "
                         f"{sorted(set(t.index.get_level_values('saha')))}")
    for ad, (saha, n_bek, p_bek, c_bek, g_bek) in TABLO2.items():
        pk, gi = t.loc[(saha, "P_kapasite")], t.loc[(saha, "G_i")]
        if pk["N"] != gi["N"]:
            raise ValueError(f"{saha}: P ve G_i N'si farkli")
        kiyasla_metin("2", f"{ad} N", f"{int(pk['N']):,}", n_bek, repr(int(pk["N"])))
        kiyasla_metin("2", f"{ad} P ort \u00b1 SD (% kapasite)",
                      f"{pk['ortalama']:.1f} \u00b1 {pk['std']:.1f}", p_bek,
                      f"{float(pk['ortalama'])!r} / {float(pk['std'])!r}")
        kiyasla_metin("2", f"{ad} carpiklik", f"{pk['carpiklik']:+.2f}".replace("-", EKSI),
                      c_bek, repr(float(pk["carpiklik"])))
        kiyasla_metin("2", f"{ad} G_i ortalamasi", f"{gi['ortalama']:.0f}", g_bek,
                      repr(float(gi["ortalama"])))


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
    for model, (*degerler, aralik) in TABLO7.items():
        for kaynak, bek in zip(KAYNAKLAR, degerler):
            kiyasla("7", f"{model} / {kaynak}", a_yuzde[(kaynak, model)], bek)
        oran = [a_yuzde[(k, model)] / a_yuzde[("PVGIS tam", model)] for k in OLCUM_DIZILERI]
        kiyasla_metin("7", f"{model} oran araligi (uc olcum dizisi)",
                      f"{min(oran):.1f}-{max(oran):.1f}", aralik,
                      " / ".join(repr(float(x)) for x in oran))
    # altyazi: manset araligi en buyuk etkili modelden
    model, bek = TABLO7_ALTYAZI
    oran = [a_yuzde[(k, model)] / a_yuzde[("PVGIS tam", model)] for k in OLCUM_DIZILERI]
    kiyasla_metin("7", f"altyazi manset araligi ({model})",
                  f"{min(oran):.1f} to {max(oran):.1f}", bek,
                  " / ".join(repr(float(x)) for x in oran))
    en_buyuk = {k: max(TABLO7, key=lambda m: abs(a_yuzde[(k, m)])) for k in OLCUM_DIZILERI}
    kiyasla_metin("7", "altyazi: en buyuk etkili model (uc olcum dizisinde)",
                  ", ".join(sorted(set(en_buyuk.values()))), model,
                  "; ".join(f"{k}: {m}" for k, m in en_buyuk.items()))
    model, dizi, bek = TABLO7_BOLUM53
    kiyasla("7", f"Bolum 5.3 metni: {model} {dizi} orani",
            a_yuzde[(dizi, model)] / a_yuzde[("PVGIS tam", model)], bek)


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
    # Tablo 2 metni U+2212 ve U+00B1 tasir; Windows konsolunun kod sayfasi
    # (cp1254) U+2212'yi basamaz ve betik kiyasi bitirmeden coker.
    sys.stdout.reconfigure(encoding="utf-8")
    for f in (tablo2, tablo5, tablo6, tablo7, tablo8, tablo9):
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
