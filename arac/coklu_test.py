"""Coklu test duzeltmesi - mevcut p-degerleri uzerinden Holm ve BH.

[SONRADAN EKLENDI - 17 Ekim 2026] ON-KAYIT SONRASI SAGLAMLIK ANALIZIDIR.
Hicbir fazin on-kayitli planinda coklu test duzeltmesi YOKTUR; makale
(Bolum 7) "duzeltme uygulanmadi" diyor ve sapma S6'da kayitli. Bu betik
hoca degerlendirmesinden sonra, butun p-degerleri GORULDUKTEN SONRA
yazildi. Aile tanimlari sonuclara bakarak secilmis sayilmalidir; bu yuzden
tek bir "dogru" aile yerine birden fazla aile raporlanir (dar: kaynak x
varyant, genis: Faz 2'nin 228 testi). Hicbir deney yeniden kosulmaz, hicbir
p-degeri yeniden hesaplanmaz - diskteki DM ciktilari okunur.

`arac/` statusundedir: TESHIS/SAGLAMLIK, ana akistan cagrilmaz.

Aileler
    Faz 2   kaynak x varyant (20 aile; gece sinif B, testi yok)
            olcekleyici, uc kaynak birlikte (57) - iddia 19/57 diye yazildi
            Faz 2 tumu (348)
    Faz 3   yedi yil x ilk-iki farki (7)
    Faz 4   yil ici DM, 5 yil x 3 cift (15)
    Faz 4   hacim etkisi K=1 vs K=tum, esli (45)

Iki DKASC dizisi daha  [SONRADAN EKLENDI - 22 Ekim 2026]
    M15_A ("DKASC CdTe") ve M3_A ("DKASC poly-Si") Faz 2 kaynagi olarak
    eklendi (kurallar belgesi, karar 6); her biri kendi kaynak x varyant
    ailelerini alir (varyant basina 15 test). En genis aile 228'den 348'e
    buyudu. M6_B'nin etiketi "DKASC" olarak BIRAKILDI (makalede "DKASC
    mono-Si"): eski aile ve iddia satirlari metin olarak degismesin ve
    onceki ciktiyla kiyaslanabilsin diye. "olcekleyici, uc kaynak (57)"
    ailesi ve 19/57 iddiasi bilincli olarak ESKI UC kaynakla sinirli kalir;
    o iddia bu uc kaynak uzerine yazildi.

Yuvarlama siniri
    Faz 2 ve Faz 4 p-degerleri diskte tam hassasiyette (repr). Faz 3'unkiler
    4 ondalikla yuvarlanmis (`siralama_karsilastirma.csv`); gercek p
    [p - h, p + h] araliginda, h = 0,5e-4 (p = 0 icin [0, h]). Holm ve BH
    monotondur: bir p'yi kucultmek reddi azaltamaz. Bu yuzden butun p'ler
    alt sinirdayken ve ust sinirdayken karar ayni degilse test `sinir`
    diye isaretlenir. Ham karar icin ayni kural esige uygulanir.

Karar kurali: duzeltilmis p < ALFA (ham `anlamli` sutunu p < 0,05 ile
birebir ayni; asagida dogrulanir).

Ciktilar
    sonuclar/coklu_test_ozet.csv      aile basina test / ham / Holm / BH
    sonuclar/coklu_test_iddialar.csv  makale iddialari duzeltme sonrasi
    sonuclar/coklu_test_detay.csv     her (aile, test) icin ham ve
                                      duzeltilmis p - iddialarin denetimi

Kosma (kok dizinden):
    .venv\\Scripts\\python.exe -m arac.coklu_test
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import false_discovery_control

from pv10.config import SONUC

ALFA = 0.05

# Faz 2 kaynaklari: dosya on eki -> etiket
FAZ2_KAYNAK = {
    "ana": "PVGIS tam",
    "pvgis_indirgenmis": "PVGIS indirgenmis",
    "dkasc": "DKASC",
    "dkasc_m15a": "DKASC CdTe",      # [22 Ekim 2026]
    "dkasc_m3a": "DKASC poly-Si",    # [22 Ekim 2026]
}
# 19/57 olcekleyici iddiasinin yazildigi uc kaynak; yeni diziler bu aileye
# GIRMEZ (bkz. modul basligi).
FAZ2_ESKI_KAYNAK = ("PVGIS tam", "PVGIS indirgenmis", "DKASC")
FAZ2_VARYANT = ("eszaman", "olcekleyici", "rastgele_kfold", "enkotu")
FAZ2_BEKLENEN_N = {"ana": 84, "pvgis_indirgenmis": 84, "dkasc": 60,
                   "dkasc_m15a": 60, "dkasc_m3a": 60}
FAZ2_TOPLAM = sum(FAZ2_BEKLENEN_N.values())  # 348

# Diskte yuvarlanmis p-degerleri: kaynak -> ondalik sayisi. Listede olmayan
# kaynak tam hassasiyettedir (h = 0).
YUVARLAMA_ONDALIK = {"faz3": 4}


# --- duzeltme yontemleri ----------------------------------------------------


def holm(p: np.ndarray) -> np.ndarray:
    """Holm-Bonferroni duzeltilmis p (adim adim asagi, monoton)."""
    p = np.asarray(p, dtype=float)
    m = len(p)
    sira = np.argsort(p, kind="mergesort")
    carpan = m - np.arange(m)
    duz = np.minimum(1.0, np.maximum.accumulate(p[sira] * carpan))
    sonuc = np.empty(m)
    sonuc[sira] = duz
    return sonuc


def bh(p: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg duzeltilmis p (adim adim yukari, monoton)."""
    p = np.asarray(p, dtype=float)
    m = len(p)
    sira = np.argsort(p, kind="mergesort")
    oran = p[sira] * m / np.arange(1, m + 1)
    duz = np.minimum(1.0, np.minimum.accumulate(oran[::-1])[::-1])
    sonuc = np.empty(m)
    sonuc[sira] = duz
    return sonuc


def yontem_oz_testi() -> None:
    """Kendi uygulamalarimizi bilinen degerlere ve scipy'ye karsi sinar."""
    p = np.array([0.01, 0.04, 0.03, 0.005, 0.20])
    # elle: sirali 0.005,0.01,0.03,0.04,0.20 -> Holm x5,x4,x3,x2,x1
    # = 0.025,0.04,0.09,0.08->0.09,0.20 ; BH x5/1..5/5
    beklenen_holm = np.array([0.04, 0.09, 0.09, 0.025, 0.20])
    beklenen_bh = np.array([0.025, 0.05, 0.05, 0.025, 0.20])
    if not np.allclose(holm(p), beklenen_holm, rtol=0, atol=1e-15):
        raise AssertionError(f"Holm oz testi tutmadi: {holm(p)}")
    if not np.allclose(bh(p), beklenen_bh, rtol=0, atol=1e-15):
        raise AssertionError(f"BH oz testi tutmadi: {bh(p)}")
    rng = np.random.default_rng(0)
    for _ in range(200):
        q = rng.uniform(0, 0.2, rng.integers(1, 60))
        if not np.allclose(bh(q), false_discovery_control(q, method="bh"), rtol=0, atol=1e-12):
            raise AssertionError("BH scipy ile tutmadi")


# --- test kumelerinin okunmasi ----------------------------------------------


def faz2_testleri() -> pd.DataFrame:
    """Faz 2 DM testleri (348), rastgele_kfold icin bootstrap birlesimiyle."""
    parca = []
    for onek, etiket in FAZ2_KAYNAK.items():
        d = pd.read_csv(SONUC / f"ablasyon_belirsizlik_dm_{onek}_dm.csv")
        b = pd.read_csv(SONUC / f"ablasyon_belirsizlik_dm_{onek}_bootstrap.csv")
        if len(d) != FAZ2_BEKLENEN_N[onek]:
            raise ValueError(f"{onek}: {len(d)} satir, beklenen {FAZ2_BEKLENEN_N[onek]}")
        if set(d["varyant"]) != set(FAZ2_VARYANT) or d["p"].isna().any():
            raise ValueError(f"{onek}: beklenmeyen varyant kumesi ya da eksik p")
        d = d.merge(
            b[["test_yil", "model", "varyant", "bootstrap_sifiri_iceriyor", "bootstrap_fark_W"]],
            on=["test_yil", "model", "varyant"],
            how="left",
            validate="1:1",
        )
        r = d[d["varyant"] == "rastgele_kfold"]
        if r["bootstrap_sifiri_iceriyor"].isna().any():
            raise ValueError(f"{onek}: rastgele_kfold satirinda bootstrap eksik")
        if (r["bootstrap_fark_W"] - r["D_manset"]).abs().max() > 1e-9:
            raise ValueError(f"{onek}: bootstrap farki D_manset ile ayni degil")
        d["kaynak"] = etiket
        d["kaynak_dosya"] = f"ablasyon_belirsizlik_dm_{onek}_dm.csv"
        d["test_id"] = (
            "F2|" + etiket + "|" + d["varyant"] + "|" + d["model"] + "|" + d["test_yil"].astype(str)
        )
        d["yuvarlama"] = "tam"
        parca.append(d)
    t = pd.concat(parca, ignore_index=True)
    if len(t) != FAZ2_TOPLAM:
        raise ValueError(f"Faz 2 toplam {len(t)} test, beklenen {FAZ2_TOPLAM}")
    return t


def faz3_testleri() -> pd.DataFrame:
    """Her test yilinda ilk-iki cifti; sira tam hassasiyetli RMSE'den."""
    rmse = pd.read_csv(SONUC / "siralama_rmse.csv").set_index("test_yil")
    k = pd.read_csv(SONUC / "siralama_karsilastirma.csv", dtype={"p": str})
    ondalik = max(len(s.split(".")[1]) if "." in s else 0 for s in k["p"])
    if ondalik > YUVARLAMA_ONDALIK["faz3"]:
        raise ValueError(f"Faz 3 p {ondalik} ondalik; YUVARLAMA_ONDALIK guncel degil")
    k["p"] = k["p"].astype(float)
    satir = []
    for yil, r in rmse.iterrows():
        s = r.sort_values()
        if s.iloc[0] == s.iloc[1] or s.iloc[1] == s.iloc[2]:
            raise ValueError(f"Faz 3 {yil}: RMSE esitligi, ilk-iki belirsiz")
        ilk_iki = {s.index[0], s.index[1]}
        c = k[(k["test_yil"] == yil) & k.apply(lambda x: {x.model_a, x.model_b} == ilk_iki, axis=1)]
        if len(c) != 1:
            raise ValueError(f"Faz 3 {yil}: ilk-iki cifti {ilk_iki} bulunamadi")
        c = c.iloc[0].to_dict()
        c["test_id"] = f"F3|{yil}|{s.index[0]} vs {s.index[1]}"
        c["yuvarlama"] = "faz3"
        satir.append(c)
    t = pd.DataFrame(satir)
    if len(t) != 7:
        raise ValueError(f"Faz 3 {len(t)} test, beklenen 7")
    return t


def faz4_yil_testleri() -> pd.DataFrame:
    t = pd.read_csv(SONUC / "doygunluk_ozet_dm_yil.csv")
    if len(t) != 15:
        raise ValueError(f"Faz 4 yil ici {len(t)} test, beklenen 15")
    t["test_id"] = "F4y|" + t["test_yil"].astype(str) + "|" + t["model_a"] + " vs " + t["model_b"]
    t["yuvarlama"] = "tam"
    return t


def faz4_hacim_testleri() -> pd.DataFrame:
    t = pd.read_csv(SONUC / "doygunluk_ozet_dm.csv")
    if len(t) != 45 or set(t["model"].value_counts()) != {15}:
        raise ValueError("Faz 4 hacim: 45 test / model basina 15 beklenir")
    t["test_id"] = (
        "F4h|" + t["model"] + "|" + t["test_yil"].astype(str) + "|tohum" + t["tohum"].astype(str)
    )
    t["yuvarlama"] = "tam"
    return t


# --- aile duzeltmesi --------------------------------------------------------


def aile_duzelt(t: pd.DataFrame, aile: str, faz: str) -> pd.DataFrame:
    """Bir aile icin ham/Holm/BH kararlari ve yuvarlama sinir bayraklari."""
    if t["test_id"].duplicated().any():
        raise ValueError(f"{aile}: tekrarlanan test")
    if "anlamli" in t and not ((t["p"] < ALFA) == t["anlamli"].astype(bool)).all():
        raise ValueError(f"{aile}: diskteki `anlamli` p < {ALFA} ile tutmuyor")
    p = t["p"].to_numpy(dtype=float)
    h = np.array([
        0.5 * 10.0 ** -YUVARLAMA_ONDALIK[y] if y in YUVARLAMA_ONDALIK else 0.0
        for y in t["yuvarlama"]
    ])
    p_alt = np.maximum(p - h, 0.0)
    p_ust = np.minimum(p + h, 1.0)

    d = pd.DataFrame({"aile": aile, "faz": faz, "test_id": t["test_id"].to_numpy(), "p": p})
    for ad, f in (("ham", lambda x: x), ("holm", holm), ("bh", bh)):
        d[f"p_{ad}"] = f(p)
        d[f"{ad}_anlamli"] = d[f"p_{ad}"] < ALFA
        alt_karar = f(p_alt) < ALFA
        ust_karar = f(p_ust) < ALFA
        d[f"{ad}_sinir"] = alt_karar != ust_karar
    d = d.drop(columns="p_ham")
    return d


def aileleri_kur() -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    f2 = faz2_testleri()
    kaynak = {
        "faz2": f2,
        "faz3": faz3_testleri(),
        "faz4y": faz4_yil_testleri(),
        "faz4h": faz4_hacim_testleri(),
    }
    aileler: list[tuple[str, str, pd.DataFrame]] = []
    for etiket in FAZ2_KAYNAK.values():
        for v in FAZ2_VARYANT:
            alt = f2[(f2["kaynak"] == etiket) & (f2["varyant"] == v)]
            aileler.append((f"F2 {etiket} / {v}", "Faz 2 kaynak x varyant", alt))
    eski_olc = f2[(f2["varyant"] == "olcekleyici") & f2["kaynak"].isin(FAZ2_ESKI_KAYNAK)]
    aileler.append(("F2 olcekleyici uc kaynak", "Faz 2 olcekleyici (57)", eski_olc))
    aileler.append(("F2 tumu", f"Faz 2 tumu ({FAZ2_TOPLAM})", f2))
    aileler.append(("F3 ilk-iki x 7 yil", "Faz 3", kaynak["faz3"]))
    aileler.append(("F4 yil ici 5 yil x 3 cift", "Faz 4 yil ici", kaynak["faz4y"]))
    aileler.append(("F4 hacim 45 esli", "Faz 4 hacim", kaynak["faz4h"]))

    detay = pd.concat([aile_duzelt(t, a, f) for a, f, t in aileler], ignore_index=True)
    return detay, kaynak


def ozet_tablosu(detay: pd.DataFrame) -> pd.DataFrame:
    g = detay.groupby(["aile", "faz"], sort=False)
    return pd.DataFrame({
        "test_sayisi": g.size(),
        "ham_anlamli": g["ham_anlamli"].sum(),
        "holm_anlamli": g["holm_anlamli"].sum(),
        "bh_anlamli": g["bh_anlamli"].sum(),
        "ham_sinir": g["ham_sinir"].sum(),
        "holm_sinir": g["holm_sinir"].sum(),
        "bh_sinir": g["bh_sinir"].sum(),
    }).reset_index()


# --- iddialar ---------------------------------------------------------------


def iddialar(detay: pd.DataFrame, kaynak: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Makale iddialarini her aile tanimi altinda yeniden sayar.

    Her iddia bir test alt kumesi (maske) ve opsiyonel bir ek kosul
    (bootstrap GA sifiri iceriyor, isaret ters) ile tanimlanir. Ham sayi
    makaledeki sayiyla tutmazsa acik hata.
    """
    f2 = kaynak["faz2"].set_index("test_id")
    satir = []

    def say(iddia, makale, payda, aile, maske_id, ek=None):
        alt = detay[(detay["aile"] == aile) & detay["test_id"].isin(maske_id)]
        if len(alt) != len(maske_id):
            raise ValueError(f"{iddia}: {aile} icinde {len(alt)}/{len(maske_id)} test bulundu")
        if len(alt) != payda and ek is None:
            raise ValueError(f"{iddia}: payda {len(alt)}, beklenen {payda}")
        ek_m = np.ones(len(alt), bool) if ek is None else ek(alt["test_id"]).to_numpy()
        kayit = {"iddia": iddia, "aile": aile, "makaledeki": f"{makale}/{payda}"}
        for ad in ("ham", "holm", "bh"):
            n = int((alt[f"{ad}_anlamli"].to_numpy() & ek_m).sum())
            kayit[ad] = n
            kayit[f"{ad}_sinir"] = int((alt[f"{ad}_sinir"].to_numpy() & ek_m).sum())
        if kayit["ham"] != makale:
            raise AssertionError(f"{iddia} [{aile}]: ham {kayit['ham']}, makale {makale}")
        kayit["holm_ayakta"] = kayit["holm"] == makale
        kayit["bh_ayakta"] = kayit["bh"] == makale
        satir.append(kayit)

    def f2_id(kaynak_ad=None, varyant=None):
        m = pd.Series(True, index=f2.index)
        if kaynak_ad:
            m &= f2["kaynak"] == kaynak_ad
        if varyant:
            m &= f2["varyant"] == varyant
        return list(f2.index[m])

    ci0 = lambda ids: f2.loc[ids, "bootstrap_sifiri_iceriyor"].astype(bool).reset_index(drop=True)
    ters = lambda ids: ((f2.loc[ids, "A_model"] * f2.loc[ids, "D_manset"]) < 0).reset_index(drop=True)
    ci0_ters = lambda ids: ci0(ids) & ters(ids)

    # 1) olcekleyici 19/57 - uc aile tanimi altinda
    olc_ids = [i for e in FAZ2_ESKI_KAYNAK for i in f2_id(e, "olcekleyici")]
    # dar aile: kaynak x varyant, uc ailenin toplami
    dar = [detay[(detay["aile"] == f"F2 {e} / olcekleyici")] for e in FAZ2_ESKI_KAYNAK]
    dar = pd.concat(dar)
    kayit = {"iddia": "olcekleyici anlamli hucre, uc kaynak", "aile": "F2 kaynak x varyant (3 aile toplami)",
             "makaledeki": "19/57"}
    for ad in ("ham", "holm", "bh"):
        kayit[ad] = int(dar[f"{ad}_anlamli"].sum())
        kayit[f"{ad}_sinir"] = int(dar[f"{ad}_sinir"].sum())
    if kayit["ham"] != 19:
        raise AssertionError(f"olcekleyici dar ham {kayit['ham']} != 19")
    kayit["holm_ayakta"] = kayit["holm"] == 19
    kayit["bh_ayakta"] = kayit["bh"] == 19
    satir.append(kayit)
    say("olcekleyici anlamli hucre, uc kaynak", 19, 57, "F2 olcekleyici uc kaynak", olc_ids)
    say("olcekleyici anlamli hucre, uc kaynak", 19, 57, "F2 tumu", olc_ids)

    # 2) rastgele_kfold: A anlamli, kaybolan, ters
    beklenen = {
        "PVGIS tam": (15, 21, 10, 5, None),
        "PVGIS indirgenmis": (15, 21, 10, 5, None),
        "DKASC": (13, 15, 4, None, 2),
        # [22 Ekim 2026] M6_B satiriyla ayni bicim: A anlamli, kaybolan,
        # A anlamli VE isaret ters
        "DKASC CdTe": (12, 15, 4, None, 1),
        "DKASC poly-Si": (14, 15, 7, None, 2),
    }
    for etiket, (a_anl, payda, kayb, kayb_ters, a_ters) in beklenen.items():
        ids = f2_id(etiket, "rastgele_kfold")
        for aile in (f"F2 {etiket} / rastgele_kfold", "F2 tumu"):
            say(f"rastgele_kfold A anlamli - {etiket}", a_anl, payda, aile, ids)
            say(f"rastgele_kfold A anlamli VE bootstrap GA sifiri iceriyor (etki kayboluyor) - {etiket}",
                kayb, payda, aile, ids, ci0)
            if kayb_ters is not None:
                say(f"rastgele_kfold kaybolanlarin icinde isaret ters - {etiket}",
                    kayb_ters, payda, aile, ids, ci0_ters)
            if a_ters is not None:
                # Parantez ICI OLCULUR, yazilmaz: M6_B'de ters hucreler
                # kaybolanlardan farkli; M15_A ve M3_A'da kaybolanlarin
                # ICINDE. Etiketi kopyalamak yanlis iddia yazardi.
                f = f2.loc[ids]
                ortusen = int((f["anlamli"].astype(bool) & f["bootstrap_sifiri_iceriyor"].astype(bool)
                               & (f["A_model"] * f["D_manset"] < 0)).sum())
                nerede = ("kaybolanlardan FARKLI hucreler" if ortusen == 0 else
                          "hepsi kaybolanlarin ICINDE" if ortusen == a_ters else
                          f"{ortusen}'i kaybolanlarin icinde")
                say(f"rastgele_kfold A anlamli VE isaret ters ({nerede}) - {etiket}",
                    a_ters, payda, aile, ids, ters)

    # 3) Faz 3: 7 yilin 1'inde anlamli (2023)
    f3 = kaynak["faz3"]
    say("Faz 3 ilk-iki farki anlamli yil (2023, p=0.038)", 1, 7, "F3 ilk-iki x 7 yil", list(f3["test_id"]))

    # 4) Faz 4 yil ici: kazanan-ikinci 0/5, toplam 1/15
    f4y = kaynak["faz4y"]
    ki = list(f4y.loc[f4y["kazanan_ikinci_cifti"].astype(bool), "test_id"])
    if len(ki) != 5:
        raise ValueError(f"Faz 4 kazanan-ikinci cifti {len(ki)}, beklenen 5")
    say("Faz 4 yil ici kazanan-ikinci farki anlamli yil", 0, 5, "F4 yil ici 5 yil x 3 cift", ki)
    say("Faz 4 yil ici anlamli cift, toplam", 1, 15, "F4 yil ici 5 yil x 3 cift", list(f4y["test_id"]))

    # 5) Faz 4 hacim: model basina
    f4h = kaynak["faz4h"]
    for model, n in (("Hist Gradient Boosting", 15), ("Polynomial Ridge", 15), ("Linear Regression", 5)):
        say(f"Faz 4 hacim etkisi anlamli - {model}", n, 15, "F4 hacim 45 esli",
            list(f4h.loc[f4h["model"] == model, "test_id"]))
    say("Faz 4 hacim etkisi anlamli, toplam", 35, 45, "F4 hacim 45 esli", list(f4h["test_id"]))

    return pd.DataFrame(satir)


def main() -> None:
    yontem_oz_testi()
    print("yontem oz testi: Holm/BH elle hesaplanan degerlerle ve BH scipy ile tutuyor\n")
    detay, kaynak = aileleri_kur()
    ozet = ozet_tablosu(detay)
    idd = iddialar(detay, kaynak)

    for ad, tablo in (("coklu_test_ozet", ozet), ("coklu_test_iddialar", idd), ("coklu_test_detay", detay)):
        tablo.to_csv(SONUC / f"{ad}.csv", index=False)

    with pd.option_context("display.width", 250, "display.max_columns", 30, "display.max_colwidth", 90):
        print(ozet.to_string(index=False))
        print()
        print(idd.to_string(index=False))
        sinir = detay[detay[["ham_sinir", "holm_sinir", "bh_sinir"]].any(axis=1)]
        print(f"\nyuvarlama siniri isaretli test: {len(sinir)}")
        if len(sinir):
            print(sinir.to_string(index=False))


if __name__ == "__main__":
    main()
