"""Makale sekilleri F1 ve F2 - diskteki mevcut sonuc CSV'lerinden uretilir.

Bu betik SUNUM icindir, DENEY DEGILDIR. Hicbir model egitmez, hicbir deneyi
yeniden kosmaz ve makalenin hicbir YENI sayisini uretmez; yalnizca
`sonuclar/` altindaki tablolari okuyup cizer. `arac/` ile ayni statudedir ve
ana akistan cagrilmaz.

Her sekil icin taslaktaki tablo degerleri KONTROL olarak gomuldu. Kontrol
tutmazsa sekil URETILMEZ - acik hata firlatilir (CLAUDE.md kural 5).

Kosma (kok dizinden `-m` ile; `arac/` ile ayni desen):
    .venv\\Scripts\\python.exe -m sekiller.sekil_uret
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from pv10.config import DKASC_KAPASITE_W, KAPASITE_W, SONUC

# --- yerlesim sabitleri (yalnizca sunum; deney sabiti DEGIL) -----------------

SEKIL_DIZIN = Path(__file__).resolve().parent
MM = 1.0 / 25.4
TEK_SUTUN_MM = 90.0
CIFT_SUTUN_MM = 190.0
NOKTA = 300

# Okabe-Ito renk korlugu dostu palet; sira SABIT, dongu YOK.
# dataviz validator (light, surface #fcfcfb): 5 kontrolun 5'i PASS,
# en kotu komsu cift #009E73<->#D55E00 dE 11,0 (deutan) / 25,8 (normal).
PALET = ("#0072B2", "#D55E00", "#009E73")
ISARET = ("o", "s", "^")
CIZGI = ("-", "--", "-.")
TARAMA = ("", "///", "...")
MUREKKEP = "#222222"
SILIK = "#666666"

PENCERELER = ("1", "2", "3", "5", "tum")
PENCERE_ETIKET = ("1", "2", "3", "5", "all")  # eksen etiketi: makale dili
MODELLER = ("Linear Regression", "Polynomial Ridge", "Hist Gradient Boosting")
MODEL_KISA = {
    "Linear Regression": "LR",
    "Polynomial Ridge": "PolyRidge",
    "Hist Gradient Boosting": "HGB",
}
KOL_ETIKET = {  # gorunur etiketler makale dilinde; kod/yorum Turkce kalir
    "altornekleme": "subsampling (pure volume)",
    "kaydirmali": "sliding (volume + recency)",
}
KAYNAK_ETIKET = {
    "PVGIS tam": "PVGIS full",
    "PVGIS indirgenmis": "PVGIS reduced",
    "DKASC": "DKASC",
}

KAYNAK = {
    "PVGIS tam": (SONUC / "ablasyon_belirsizlik_dm_ana_dm.csv", KAPASITE_W),
    "PVGIS indirgenmis": (
        SONUC / "ablasyon_belirsizlik_dm_pvgis_indirgenmis_dm.csv",
        KAPASITE_W,
    ),
    "DKASC": (SONUC / "ablasyon_belirsizlik_dm_dkasc_dm.csv", DKASC_KAPASITE_W),
}

# --- kontroller: taslaktaki tablo degerleri, yazildigi hassasiyetle ----------

KONTROL_F1A = {
    "altornekleme": ("140.3506", "139.2749", "138.7122", "138.3580", "138.1457"),
    "kaydirmali": ("141.4722", "139.6685", "138.8771", "138.3765", "138.1457"),
}
KONTROL_F1B = {  # saf hacim span'i, K=1 -> K=tum (W)
    "Hist Gradient Boosting": "4.493244",
    "Polynomial Ridge": "1.911717",
    "Linear Regression": "0.209944",
}
KONTROL_F2 = {  # rastgele_kfold A terimi, kapasite %'si
    "Linear Regression": ("-0.0050", "-0.0048", "-0.0527"),
    "Polynomial Ridge": ("-0.1088", "-0.0800", "-0.6118"),
    "Hist Gradient Boosting": ("-0.6309", "-0.6109", "-2.4122"),
}


def kontrol_et(ad: str, gozlenen: float, beklenen: str) -> None:
    """Gozlenen degeri beklenenin YAZILDIGI basamak sayisinda kiyaslar.

    Tolerans yoktur: yuvarlanmis gosterimler birebir esit olmak zorundadir.
    """
    basamak = len(beklenen.split(".")[1])
    bulunan = f"{gozlenen:.{basamak}f}"
    if bulunan != beklenen:
        raise AssertionError(
            f"KONTROL TUTMADI - {ad}: beklenen {beklenen}, "
            f"gozlenen {bulunan} (tam hassasiyet {gozlenen!r}, "
            f"fark {gozlenen - float(beklenen):+.6e})"
        )
    print(f"  [gecti] {ad:46s} {bulunan}")


# --- veri okuma -------------------------------------------------------------


def doygunluk_oku() -> pd.DataFrame:
    """Faz 4 ana izgara logu; `pencere` metin olarak sabitlenir."""
    d = pd.read_csv(SONUC / "doygunluk.csv")
    d["pencere"] = d["pencere"].astype(str)
    bozuk = d[d["durum"] != "tamam"]
    if len(bozuk):
        raise ValueError(f"izgarada {len(bozuk)} hatali hucre var; sekil cizilmez")
    return d


def hucre_ortalamasi(
    d: pd.DataFrame, kol: str, pencere: str, model: str | None = None
) -> pd.DataFrame:
    """Bir (kol, pencere) icin tohum-ici ortalanmis (model, yil) hucreleri.

    K=tum yalnizca `kaydirmali` kolunda loglanir ve iki kol tarafindan
    PAYLASILIR (`doygunluk_ozet_egri.csv:paylasilan`); altornekleme icin de
    oradan okunur.
    """
    etkin = "kaydirmali" if pencere == "tum" else kol
    alt = d[(d["kol"] == etkin) & (d["pencere"] == pencere)]
    if model is not None:
        alt = alt[alt["model"] == model]
    return alt.groupby(["model", "test_yil"], as_index=False)[
        ["RMSE", "RMSE_GA_alt", "RMSE_GA_ust"]
    ].mean()


def egri(d: pd.DataFrame, kol: str, model: str | None = None) -> pd.DataFrame:
    """Pencere basina ortalama RMSE ve ortalama gun-blogu bootstrap GA'si."""
    satir = []
    for p in PENCERELER:
        h = hucre_ortalamasi(d, kol, p, model)
        satir.append(
            {
                "pencere": p,
                "RMSE": h["RMSE"].mean(),
                "GA_alt": h["RMSE_GA_alt"].mean(),
                "GA_ust": h["RMSE_GA_ust"].mean(),
                "hucre": len(h),
            }
        )
    return pd.DataFrame(satir)


def a_terimi() -> pd.DataFrame:
    """`rastgele_kfold` icin populasyondan arinmis etki A, kapasite %'si.

    A = RMSE_varyant(kesisim) - RMSE_temiz(kesisim); degerlendirme
    populasyonu SABIT (bkz. varyant-dm-yorum-kurali.md 3.3b). Test yillari
    uzerinden ortalanir.
    """
    satir = []
    for ad, (yol, kapasite) in KAYNAK.items():
        d = pd.read_csv(yol)
        r = d[d["varyant"] == "rastgele_kfold"]
        for model in MODELLER:
            m = r[r["model"] == model]
            if m.empty:
                raise ValueError(
                    f"{yol.name}: {model} icin rastgele_kfold satiri yok"
                )
            satir.append(
                {
                    "kaynak": ad,
                    "model": model,
                    "yil": len(m),
                    "A_W": m["A_model"].mean(),
                    "A_yuzde": m["A_model"].mean() / kapasite * 100.0,
                }
            )
    return pd.DataFrame(satir)


# --- bicim ------------------------------------------------------------------


def bicim_kur() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 8.5,
            "axes.labelsize": 8.5,
            "axes.titlesize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 7.5,
            "axes.linewidth": 0.6,
            "axes.edgecolor": SILIK,
            "axes.labelcolor": MUREKKEP,
            "text.color": MUREKKEP,
            "xtick.color": SILIK,
            "ytick.color": SILIK,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "lines.linewidth": 1.4,
            "lines.markersize": 4.0,
            "grid.color": "#DDDDDD",
            "grid.linewidth": 0.5,
            "legend.frameon": False,
            "figure.dpi": 120,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.02,
            "pdf.fonttype": 42,  # TrueType gomme - dergi sarti
            "ps.fonttype": 42,
            "axes.unicode_minus": True,
            "hatch.linewidth": 0.6,  # 90 mm'de kaba taramayi inceltir
        }
    )


def sadelestir(eks: plt.Axes) -> None:
    for kenar in ("top", "right"):
        eks.spines[kenar].set_visible(False)
    eks.grid(axis="y", zorder=0)
    eks.set_axisbelow(True)


def kaydet(sek: plt.Figure, ad: str) -> list[Path]:
    yollar = []
    for uzanti, nokta in (("pdf", None), ("png", NOKTA)):
        yol = SEKIL_DIZIN / f"{ad}.{uzanti}"
        if nokta is None:
            sek.savefig(yol)
        else:
            sek.savefig(yol, dpi=nokta)
        yollar.append(yol)
    plt.close(sek)
    return yollar


# --- F1 ---------------------------------------------------------------------


def sekil_f1(d: pd.DataFrame) -> list[Path]:
    kol_egri = {kol: egri(d, kol) for kol in ("altornekleme", "kaydirmali")}
    model_egri = {m: egri(d, "altornekleme", m) for m in MODELLER}

    print("\nF1(a) kontrol - pencere ortalamasi RMSE (W):")
    for kol, e in kol_egri.items():
        for p, bek, got in zip(PENCERE_ETIKET, KONTROL_F1A[kol], e["RMSE"]):
            kontrol_et(f"F1a {kol} K={p}", got, bek)

    print("\nF1(b) kontrol - model bazinda saf hacim span'i K=1 -> K=tum (W):")
    for model, bek in KONTROL_F1B.items():
        e = model_egri[model]
        span = float(
            e.loc[e.pencere == "1", "RMSE"].iloc[0]
            - e.loc[e.pencere == "tum", "RMSE"].iloc[0]
        )
        kontrol_et(f"F1b {MODEL_KISA[model]} span", span, bek)

    x = range(len(PENCERELER))
    sek, (ea, eb) = plt.subplots(1, 2, figsize=(CIFT_SUTUN_MM * MM, 80 * MM))

    # (a) iki kol, gun-blogu bootstrap GA'si golge
    for i, (kol, e) in enumerate(kol_egri.items()):
        # Iki kolun GA'si neredeyse birebir ortusuyor; dolgu tek basina
        # ayirt edilemiyor, o yuzden her banda kendi renginde ince kenar.
        ea.fill_between(
            x, e["GA_alt"], e["GA_ust"], color=PALET[i], alpha=0.08,
            linewidth=0, zorder=1,
        )
        for sinir in ("GA_alt", "GA_ust"):
            ea.plot(x, e[sinir], CIZGI[i], color=PALET[i], lw=0.6,
                    alpha=0.55, zorder=2)
        ea.plot(
            x, e["RMSE"], CIZGI[i], color=PALET[i], marker=ISARET[i],
            markeredgecolor="white", markeredgewidth=0.5,
            label=KOL_ETIKET[kol], zorder=3,
        )
    ea.annotate(
        "$K$=all shared",
        xy=(4, kol_egri["kaydirmali"]["RMSE"].iloc[-1]),
        xytext=(-4, -18),
        textcoords="offset points",
        ha="right",
        fontsize=7,
        color=SILIK,
        arrowprops=dict(arrowstyle="-", lw=0.5, color=SILIK),
    )
    ea.set_xlabel("Training window length $K$ (years)")
    ea.set_ylabel("RMSE (W)")
    ea.legend(loc="upper right", handlelength=2.4)
    ea.text(
        0.98, 0.62,
        "shaded: day-block bootstrap 95% CI\n(mean over cells, 1000 reps)",
        transform=ea.transAxes, ha="right", va="top",
        fontsize=6.8, color=SILIK, linespacing=1.4,
    )

    # (b) model bazinda, her model kendi K=1'ine gore
    for i, model in enumerate(MODELLER):
        e = model_egri[model]
        fark = e["RMSE"] - float(e.loc[e.pencere == "1", "RMSE"].iloc[0])
        eb.plot(
            x, fark, CIZGI[i], color=PALET[i], marker=ISARET[i],
            markeredgecolor="white", markeredgewidth=0.5,
            label=MODEL_KISA[model], zorder=3,
        )
        # uc etiketi: yalniz PolyRidge ucun USTUNE sigiyor; LR sifir
        # cizgisine, HGB kendi dik inisine carpiyor - ikisi de ALTA.
        eb.annotate(
            f"{fark.iloc[-1]:+.2f} W",
            xy=(4, fark.iloc[-1]),
            xytext=(-3, 6 if model == "Polynomial Ridge" else -11),
            textcoords="offset points",
            ha="right",
            fontsize=7,
            color=PALET[i],
        )
    eb.axhline(0.0, color=SILIK, lw=0.6, ls=":", zorder=2)
    eb.set_ylim(-5.05, 0.45)  # uc etiketlerine yer; kirpilma olmasin
    eb.set_xlabel("Training window length $K$ (years)")
    eb.set_ylabel(r"$\Delta$RMSE relative to own $K{=}1$ (W)")
    eb.legend(loc="lower left", handlelength=2.4)

    for eks, harf in ((ea, "a"), (eb, "b")):
        sadelestir(eks)
        eks.set_xticks(list(x))
        eks.set_xticklabels(PENCERE_ETIKET)
        eks.set_xlim(-0.25, len(PENCERELER) - 0.75)
        eks.text(
            -0.19, 1.04, f"({harf})", transform=eks.transAxes,
            fontsize=9, fontweight="bold",
        )

    sek.subplots_adjust(wspace=0.32)
    return kaydet(sek, "F1_ogrenme_egrileri")


# --- F2 ---------------------------------------------------------------------


def sekil_f2() -> list[Path]:
    a = a_terimi()

    print("\nF2 kontrol - rastgele_kfold A terimi (kapasite %'si):")
    for model, bekler in KONTROL_F2.items():
        for kaynak, bek in zip(KAYNAK, bekler):
            got = float(
                a[(a.model == model) & (a.kaynak == kaynak)]["A_yuzde"].iloc[0]
            )
            kontrol_et(f"F2 {MODEL_KISA[model]} / {kaynak}", got, bek)

    sek, eks = plt.subplots(figsize=(TEK_SUTUN_MM * MM, 78 * MM))
    genislik = 0.26
    for i, kaynak in enumerate(KAYNAK):
        alt = a[a.kaynak == kaynak].set_index("model").loc[list(MODELLER)]
        yer = [j + (i - 1) * genislik for j in range(len(MODELLER))]
        eks.bar(
            yer, alt["A_yuzde"].abs(), genislik * 0.88,
            label=KAYNAK_ETIKET[kaynak],
            color=PALET[i], hatch=TARAMA[i], edgecolor="white",
            linewidth=0.7, zorder=3,
        )
        for xi, (_, s) in zip(yer, alt.iterrows()):
            eks.annotate(
                f"{s['A_yuzde']:+.4f}",
                xy=(xi, abs(s["A_yuzde"])),
                xytext=(0, 3),
                textcoords="offset points",
                rotation=90,
                ha="center",
                va="bottom",
                fontsize=6.5,
                color=MUREKKEP,
            )

    eks.set_yscale("log")
    eks.set_ylim(2e-3, 20)
    eks.set_ylabel("|A| (% of capacity)")
    eks.set_xticks(range(len(MODELLER)))
    eks.set_xticklabels([MODEL_KISA[m] for m in MODELLER])
    eks.legend(
        loc="upper left", handlelength=1.6, handleheight=1.2,
        ncol=1, borderaxespad=0.2,
    )
    sadelestir(eks)
    # Isaret bilgisi her cubugun kendi etiketinde zaten var; ayrica bir
    # kose notu HGB cubuklarinin uzerine binyordu - kaldirildi, aciklama
    # sekil altyazisina gider.
    return kaydet(sek, "F2_rastgele_kfold_A")


def main() -> None:
    bicim_kur()
    d = doygunluk_oku()
    uretilen = sekil_f1(d) + sekil_f2()
    print("\nuretilen dosyalar:")
    for yol in uretilen:
        print(f"  {yol.relative_to(SONUC.parent)}  ({yol.stat().st_size:,} bayt)")


if __name__ == "__main__":
    main()
