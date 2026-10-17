#!/usr/bin/env python3
"""Ornek gunler - KURALLA secilen acik / parcali / kapali gunler.

[on-kayit SONRASI, sunum] Sekil icin gercek guc, temiz tahmin ve eszaman
tahmini. Gunler ELLE SECILMEZ; kural asagida ve bu dosya, tahmin
dosyalarina dokunan kod yazilmadan ONCE commit edildi. Sira commit
gecmisinde gorunur: (1) kural, (2) secilen gunler, (3) tahmin serileri.

Kaynaklar ve test yillari:
  PVGIS tam (dm_ana tahminleri)  test yili 2023, alti sahadan BIRI
  DKASC     (dm_dkasc tahminleri) test yili 2022, tek saha (dkasc_m6b)
  Model: Hist Gradient Boosting.

`rastgele_kfold` yoktur: o hucrenin test kumesi test yilina kadarki butun
yillardan rastgele saatlerdir (experiment.py:bolme_indeksleri), gun basina
ortalama 2-4 saat dusuyor; gun bazinda seri vermez.

KURAL
  1) Gun = yerel standart saat takvim gunu (`time_local`, yaz saati yok).
  2) Aday gun: 24 yerel saatinin HEPSI deneyin test kumesinde (oznitelik
     tablosu, `kismi` satirlari cikmis, time_utc yili = test yili; temiz ve
     eszaman tablolari ayni satir kumesini tasir - kontrol edilir), isinim
     alani bos degil ve (DKASC) `ariza` bayragi yok. Boylece secilen gunun
     her saati icin tahmin VARDIR; tahmin dosyasina bakmadan bilinir.
  3) Gunluk berraklik:
       DKASC : Kt = sum(GHI) / sum(G0)                  -> "Kt"
       PVGIS : sum(G_i) / sum(G0)                       -> "egik_duzlem_berraklik_proxy"
     G0 = yatay dunya disi isinim = S * (1 + 0.033 cos(2 pi n / 365)) *
     max(sin h, 0); S = DKASC_GUNES_SABITI (1367), n = time_utc gun sirasi,
     h = verideki H_sun. dkasc_pipeline.py kural 6 ile ayni formul.
     PVGIS'te yatay global isinim yok; G(i) egik duzlemdir ve G0 yataydir,
     yani PVGIS degeri GERCEK Kt DEGILDIR (1'i asabilir) - yalnizca gunleri
     siralamak icin bir proxy.
  4) PVGIS sahasi: test yilinda aday gunlerin proxy'sinin P90 - P10 araligi
     EN GENIS olan saha (uc gun turu en belirgin orada ayrisir); esitlikte
     pvgis_pipeline.KONUMLAR sirasi. DKASC'de tek saha var.
  5) Gunler: aday gunlerin berraklik dagiliminin P90 (acik), P50 (parcali),
     P10 (kapali) yuzdeliklerine mutlak farkca EN YAKIN gun; esitlikte
     takvimde ilk gelen. Yuzdelik numpy varsayilani (dogrusal).

Kullanim (kok dizinden):
    python -m arac.ornek_gunler --sec    # kural -> sekiller/F_ornek/secilen_gunler.csv
    python -m arac.ornek_gunler --seri   # secilen gunlerin tahminleri -> ornek_gunler.csv

--seri secimi YENIDEN YAPMAZ; commit edilmis secilen_gunler.csv'yi okur.
Kontroller (tutmazsa hata, dosya yazilmaz): her gun ve varyant icin 24
tahmin satiri; temiz ve eszaman dosyalarindaki `y` birebir ayni; `y`
verideki `P` ile birebir ayni.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from pv10.config import DKASC_GUNES_SABITI, DKASC_VERI, KOK, SONUC, VERI
from pv10.experiment import OznitelikOnbellegi
from pvgis_pipeline import KONUMLAR
from run_ablasyon import OZNITELIK_SETLERI

CIKTI_DIZIN = KOK / "sekiller" / "F_ornek"
SECIM = CIKTI_DIZIN / "secilen_gunler.csv"
SAHA_SECIMI = CIKTI_DIZIN / "saha_secimi.csv"
SERI = CIKTI_DIZIN / "ornek_gunler.csv"
MODEL = "Hist Gradient Boosting"
VARYANTLAR = ("temiz", "eszaman")
# kaynak -> ablasyon tahmin dizini (README'deki etiket tablosu)
TAHMIN_DIZIN = {
    "PVGIS tam": SONUC / "tahminler" / "ablasyon" / "dm_ana",
    "DKASC": SONUC / "tahminler" / "ablasyon" / "dm_dkasc",
}

# kaynak -> (veri, oznitelik seti, test yili, isinim alani, berraklik olcusu)
KAYNAK = {
    "PVGIS tam": (VERI, "gufbd", 2023, "G_i", "egik_duzlem_berraklik_proxy"),
    "DKASC": (DKASC_VERI, "dkasc", 2022, "GHI", "Kt"),
}
GUN_TURU = {"acik": 90, "parcali": 50, "kapali": 10}  # yuzdelik
SAAT_N = 24

KURAL_OZET = [
    "Kural (arac/ornek_gunler.py, tahminlere bakilmadan commit edildi):",
    "gun = yerel standart saat takvim gunu; aday = 24 saatinin hepsi test "
    "kumesinde, isinim bos degil, ariza yok;",
    "DKASC berraklik = Kt = sum(GHI)/sum(G0); PVGIS = "
    "egik_duzlem_berraklik_proxy = sum(G_i)/sum(G0) (gercek Kt degil);",
    "G0 = 1367*(1+0.033cos(2pi n/365))*max(sin h,0);",
    "PVGIS sahasi = proxy P90-P10 araligi en genis saha (esitlikte "
    "KONUMLAR sirasi); DKASC tek saha;",
    "gunler = P90 (acik), P50 (parcali), P10 (kapali) yuzdeligine en "
    "yakin gun, esitlikte takvimde ilk.",
]


def g0_yatay(time_utc: pd.Series, h_sun_derece: pd.Series) -> np.ndarray:
    n = time_utc.dt.dayofyear.to_numpy()
    sin_h = np.sin(np.deg2rad(h_sun_derece.to_numpy()))
    return (DKASC_GUNES_SABITI * (1 + 0.033 * np.cos(2 * np.pi * n / 365.0))
            * np.clip(sin_h, 0.0, None))


def test_satirlari(ham: pd.DataFrame, set_ad: str, yil: int) -> pd.DataFrame:
    """Deneyin test kumesi satirlari (konum, time_utc) - hucre_kos'un
    kronolojik bolmesiyle ayni kume. Temiz ve eszaman tablolari ayni
    kumeyi vermeli; vermezse aday tanimi belirsizdir, hata."""
    gec, esz, _ = OZNITELIK_SETLERI[set_ad]
    ob = OznitelikOnbellegi(ham, gec, esz)
    kumeler = []
    for eszaman in (False, True):
        o, _ = ob.al(eszaman)
        if "kismi" in o.columns:
            o = o[~o["kismi"].to_numpy()]
        t = o.loc[o["time_utc"].dt.year == yil, ["konum", "time_utc"]]
        kumeler.append(t.sort_values(["konum", "time_utc"]).reset_index(drop=True))
    if not kumeler[0].equals(kumeler[1]):
        raise ValueError(f"{set_ad}/{yil}: temiz ve eszaman test kumeleri farkli")
    return kumeler[0]


def gunluk_berraklik(kaynak: str) -> pd.DataFrame:
    """Aday gunler ve gunluk berraklik. Satir: konum, gun, berraklik."""
    veri, set_ad, yil, isinim, _ = KAYNAK[kaynak]
    ham = pd.read_parquet(veri)
    t = test_satirlari(ham, set_ad, yil)

    sut = ["konum", "time_utc", "time_local", "H_sun", isinim]
    if "ariza" in ham.columns:
        sut.append("ariza")
    d = ham[sut].merge(t.assign(test=True), on=["konum", "time_utc"], how="left")
    d["test"] = d["test"].fillna(False).astype(bool)
    d["gun"] = d["time_local"].dt.normalize()
    d["g0"] = g0_yatay(d["time_utc"], d["H_sun"])
    d["gecerli"] = d["test"] & d[isinim].notna()
    if "ariza" in d.columns:
        d["gecerli"] &= ~d["ariza"].to_numpy()

    g = d.groupby(["konum", "gun"], sort=True).agg(
        saat_n=("gecerli", "size"), gecerli_n=("gecerli", "sum"),
        isinim=(isinim, "sum"), g0=("g0", "sum"))
    g = g[(g.saat_n == SAAT_N) & (g.gecerli_n == SAAT_N)].reset_index()
    if g.empty:
        raise ValueError(f"{kaynak}: aday gun yok")
    g["berraklik"] = g["isinim"] / g["g0"]
    return g[["konum", "gun", "berraklik"]]


def saha_sec(g: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    """P90 - P10 araligi en genis saha; esitlikte KONUMLAR sirasi."""
    sira = list(KONUMLAR)
    if set(g.konum) != set(sira):
        raise ValueError(f"veri sahalari {sorted(set(g.konum))} != KONUMLAR {sira}")
    s = pd.DataFrame([
        dict(konum=k, aday_gun=int((g.konum == k).sum()),
             P10=np.percentile(g.loc[g.konum == k, "berraklik"], 10),
             P90=np.percentile(g.loc[g.konum == k, "berraklik"], 90))
        for k in sira])
    s["aralik_P90_P10"] = s["P90"] - s["P10"]
    secilen = s.loc[s["aralik_P90_P10"].idxmax(), "konum"]  # ilk maksimum
    s["secildi"] = s["konum"] == secilen
    return secilen, s


def gun_sec(g: pd.DataFrame) -> pd.DataFrame:
    """P90/P50/P10'a en yakin gun; esitlikte takvimde ilk."""
    g = g.sort_values("gun").reset_index(drop=True)
    satir = []
    for tur, q in GUN_TURU.items():
        hedef = float(np.percentile(g["berraklik"], q))
        uzak = (g["berraklik"] - hedef).abs()
        i = int(np.flatnonzero(uzak.to_numpy() == uzak.min())[0])
        satir.append(dict(gun_turu=tur, yuzdelik=q, hedef_deger=hedef,
                          gun=g.loc[i, "gun"].date().isoformat(),
                          gun_degeri=float(g.loc[i, "berraklik"]),
                          esit_uzaklikta_gun=int((uzak == uzak.min()).sum()),
                          aday_gun=len(g)))
    return pd.DataFrame(satir)


def basligi_yaz(yol: Path, satirlar: list[str], d: pd.DataFrame) -> None:
    yol.parent.mkdir(parents=True, exist_ok=True)
    with open(yol, "w", encoding="utf-8", newline="") as f:
        for s in satirlar:
            f.write(f"# {s}\n")
        d.to_csv(f, index=False)


def secim() -> pd.DataFrame:
    parca = []
    for kaynak, (_, _, yil, _, olcu) in KAYNAK.items():
        g = gunluk_berraklik(kaynak)
        if kaynak == "PVGIS tam":
            saha, s = saha_sec(g)
            print("PVGIS saha secimi (2023, proxy):")
            print(s.to_string(index=False))
            basligi_yaz(SAHA_SECIMI, KURAL_OZET, s)
        else:
            saha = g["konum"].iloc[0]
            if g["konum"].nunique() != 1:
                raise ValueError(f"{kaynak}: tek saha beklenir")
        sec = gun_sec(g[g.konum == saha])
        sec.insert(0, "berraklik_olcusu", olcu)
        sec.insert(0, "test_yil", yil)
        sec.insert(0, "saha", saha)
        sec.insert(0, "kaynak", kaynak)
        parca.append(sec)
    d = pd.concat(parca, ignore_index=True)
    print()
    print(d.to_string(index=False))
    basligi_yaz(SECIM, KURAL_OZET, d)
    print(f"\nyazildi -> {SECIM}\nyazildi -> {SAHA_SECIMI}")
    return d


def tahmin_oku(kaynak: str, varyant: str, yil: int) -> pd.DataFrame:
    yol = (TAHMIN_DIZIN[kaynak]
           / f"{varyant}__{MODEL.replace(' ', '_')}__{yil}.parquet")
    if not yol.exists():
        raise FileNotFoundError(f"{yol} yok")
    return pd.read_parquet(yol, columns=["konum", "time_utc", "y", "tahmin"])


def seriler() -> pd.DataFrame:
    sec = pd.read_csv(SECIM, comment="#")
    parca = []
    for (kaynak, saha, yil), s in sec.groupby(["kaynak", "saha", "test_yil"],
                                              sort=False):
        veri = KAYNAK[kaynak][0]
        ham = pd.read_parquet(veri, columns=["konum", "time_utc", "time_local", "P"])
        ham = ham[ham.konum == saha]
        ham = ham.assign(gun=ham["time_local"].dt.normalize())
        ham = ham[ham["gun"].isin(pd.to_datetime(s["gun"]))]

        d = ham
        for v in VARYANTLAR:
            t = tahmin_oku(kaynak, v, int(yil)).rename(
                columns={"y": f"y_{v}", "tahmin": v})
            d = d.merge(t, on=["konum", "time_utc"], how="left")
        eksik = d[list(VARYANTLAR)].isna().any(axis=1)
        if (eksik.any() or d.groupby("gun").size().ne(SAAT_N).any()
                or d["gun"].nunique() != len(s)):
            raise ValueError(f"{kaynak}/{saha}: secilen gunlerde eksik tahmin "
                             f"({int(eksik.sum())} saat) - aday tanimi tutmadi")
        if not np.array_equal(d["y_temiz"].to_numpy(), d["y_eszaman"].to_numpy()):
            raise ValueError(f"{kaynak}: temiz ve eszaman y serileri farkli")
        if not np.array_equal(d["y_temiz"].to_numpy(), d["P"].to_numpy()):
            raise ValueError(f"{kaynak}: tahmin dosyasindaki y verideki P degil")

        tur = dict(zip(pd.to_datetime(s["gun"]), s["gun_turu"]))
        parca.append(pd.DataFrame({
            "kaynak": kaynak, "saha": saha,
            "gun_turu": d["gun"].map(tur).to_numpy(),
            "zaman": d["time_local"].dt.strftime("%Y-%m-%d %H:%M").to_numpy(),
            "gercek": d["P"].to_numpy(),
            "temiz": d["temiz"].to_numpy(),
            "eszaman": d["eszaman"].to_numpy()}))
        print(f"{kaynak:9s} {saha:10s} {yil}: {d['gun'].nunique()} gun x "
              f"{SAAT_N} saat, kontroller gecti")

    out = pd.concat(parca, ignore_index=True)
    sira = {t: i for i, t in enumerate(GUN_TURU)}
    out = out.sort_values(["kaynak", "gun_turu", "zaman"],
                          key=lambda c: c.map(sira) if c.name == "gun_turu" else c,
                          kind="stable").reset_index(drop=True)
    baslik = KURAL_OZET + [
        "Saha: PVGIS'te 2023 proxy P90-P10 araligi en genis saha (konya), "
        "uc gun turu en belirgin orada ayrisir; DKASC'de tek saha (dkasc_m6b).",
        "Model: Hist Gradient Boosting; PVGIS test 2023 (dm_ana), DKASC test "
        "2022 (dm_dkasc). zaman = yerel standart saat; gercek/temiz/eszaman W "
        "(PVGIS 1 kWp, DKASC 5,25 kWp).",
        "rastgele_kfold bu sekilde yok; test kumesi rastgele saatlerden "
        "olustugu icin gun bazinda seri vermez.",
    ]
    basligi_yaz(SERI, baslik, out)
    print(f"\nyazildi -> {SERI}  ({len(out)} satir)")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sec", action="store_true",
                    help="kurali uygula, secilen gunleri yaz (tahmin okunmaz)")
    ap.add_argument("--seri", action="store_true",
                    help="commit edilmis secimin tahmin serilerini yaz")
    a = ap.parse_args()
    if a.sec == a.seri:
        ap.error("tam olarak bir islem ver: --sec ya da --seri")
    secim() if a.sec else seriler()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
