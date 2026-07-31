"""Faz 4 ozet tablolari.

Bu modul izgara KOSULMADAN once yazildi. Hangi tablonun uretilecegi sayilar
gelmeden sabitlendi; aksi halde metrik secimi post-hoc olurdu ve makalenin
elestirdigi seyi kendi kurulumumuzda tekrarlamis olurduk.

Metrik secimi:
  - yillar arasi kiyas  -> nRMSE_kapasite (payda sabit 1000 W)
  - konumlar arasi kiyas -> nRMSE_ortalama (payda o konumun ortalama uretimi)
  - ana oran            -> W cinsinden RMSE farki, Faz 3'un 0.4669 W'siyla
                           ayni birimde olsun diye
nRMSE_kapasite sabit paydali oldugu icin RMSE'nin lineer olcegidir (RMSE/10);
oranlar iki birimde de aynidir. Yila gore degisen payda yalnizca
nRMSE_ortalama'da vardir, o yuzden yillar arasi kiyasa girmez.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import EGITIM_PENCERELERI, ORNEKLEME_TOHUMLARI
from .models import HIZLI_ALTKUME

# Faz 3'un en iyi-ikinci medyan farki. Iki yil kumesinde de ayni cikti;
# ikisi de raporlanir ki makaledeki paydanin hangi kumeden geldigi belirsiz
# kalmasin. run_siralama.py ciktisindan, sonuclar/siralama_karsilastirma.csv.
FAZ3_MEDYAN = {
    "7 yil (2017-2023)": 0.4669,
    "5 yil (2019-2023, Faz 4 ile eslesen dilim)": 0.4669,
}
FAZ3_PAYDA_ADI = "5 yil (2019-2023, Faz 4 ile eslesen dilim)"

PENCERE_SIRA = [str(p) for p in EGITIM_PENCERELERI]


def _pencere_kategori(s: pd.Series) -> pd.Categorical:
    return pd.Categorical(s.astype(str), categories=PENCERE_SIRA, ordered=True)


def _tohum_ortala(d: pd.DataFrame) -> pd.DataFrame:
    """Altornekleme kolunu tohumlar uzerinde ortalar; kaydirmali kol aynen kalir."""
    anahtar = ["kol", "pencere", "test_yil", "model"]
    sayi = ["RMSE", "MAE", "nRMSE_kapasite", "nRMSE_ortalama", "R2", "skill", "egitim_n"]
    var = [c for c in sayi if c in d.columns]
    return d.groupby(anahtar, as_index=False)[var].mean()


# --------------------------------------------------------------------------- #
# 1) iki kolun egrisi
# --------------------------------------------------------------------------- #
def egri_tablosu(d: pd.DataFrame) -> pd.DataFrame:
    """K ekseninde iki ogrenme egrisi, paylasilan uc noktayla.

    Altornekleme K=tum tanim geregi havuzun tamamidir, yani kaydirmali K=tum
    hucresiyle AYNI hucredir. Ayrica hesaplanmaz; kaydirmali koldan odunc
    alinip paylasilan olarak isaretlenir. Saf hacim egrisi boylece dort degil
    bes noktali olur.
    """
    o = _tohum_ortala(d)
    ortak = (o.groupby(["kol", "pencere"], as_index=False)
             .agg(RMSE=("RMSE", "mean"), nRMSE_kapasite=("nRMSE_kapasite", "mean"),
                  egitim_n=("egitim_n", "mean"), hucre=("RMSE", "size")))
    ortak["paylasilan"] = False

    tum = ortak[(ortak.kol == "kaydirmali") & (ortak.pencere == "tum")]
    if len(tum) and not (ortak.kol == "altornekleme").any():
        return ortak
    if len(tum):
        odunc = tum.copy()
        odunc["kol"] = "altornekleme"
        odunc["paylasilan"] = True
        ortak = pd.concat([ortak[~((ortak.kol == "altornekleme")
                                   & (ortak.pencere == "tum"))], odunc])

    ortak["pencere"] = _pencere_kategori(ortak["pencere"])
    return ortak.sort_values(["kol", "pencere"]).reset_index(drop=True)


def marjinal_kazanc(egri: pd.DataFrame) -> pd.DataFrame:
    """Ardisik K seviyeleri arasindaki RMSE kazanci - doygunluk nerede?"""
    satir = []
    for kol, g in egri.groupby("kol", observed=True):
        g = g.sort_values("pencere")
        r = g.RMSE.to_numpy()
        p = g.pencere.astype(str).to_numpy()
        for i in range(1, len(r)):
            satir.append(dict(kol=kol, gecis=f"{p[i-1]} -> {p[i]}",
                              RMSE_kazanc_W=r[i - 1] - r[i],
                              kumulatif_W=r[0] - r[i]))
    return pd.DataFrame(satir)


# --------------------------------------------------------------------------- #
# 2) ANA ORAN - saf hacim vs uygulamali hacim
# --------------------------------------------------------------------------- #
def hacim_orani(d: pd.DataFrame) -> pd.DataFrame:
    """Makalenin ana orani.

    Kaydirmali kolda hacim ile GUNCELLIK ic ice: pencere buyudukce eklenen
    yillar hep daha eski. Saf hacim etkisi yalnizca altornekleme kolunda
    olculur - orada yil kompozisyonu sabit, degisen tek sey satir sayisi.

    Bu yuzden makaleye giren oran ALTORNEKLEME kolundan gelir; kaydirmali kol
    "uygulamada ne olur" sorusunun cevabi, ikisinin farki da guncellik /
    yil cesitliligi etkisi.
    """
    o = _tohum_ortala(d)
    y = (o.groupby(["kol", "pencere"], as_index=False)
         .agg(RMSE=("RMSE", "mean")))

    def al(kol, pencere):
        s = y[(y.kol == kol) & (y.pencere == str(pencere))]
        return float(s.iloc[0].RMSE) if len(s) else np.nan

    # K=tum iki kolda ayni hucre; kaydirmali koldan okunur
    tum = al("kaydirmali", "tum")
    saf = al("altornekleme", 1) - tum
    uyg = al("kaydirmali", 1) - tum
    payda = FAZ3_MEDYAN[FAZ3_PAYDA_ADI]

    satir = [
        dict(etki="saf hacim (altornekleme, K=1 -> tum)", RMSE_fark_W=saf,
             makaleye_giren=True,
             aciklama="yil kompozisyonu sabit; degisen tek sey satir sayisi"),
        dict(etki="uygulamali hacim (kaydirmali, K=1 -> tum)", RMSE_fark_W=uyg,
             makaleye_giren=False,
             aciklama="hacim + guncellik ic ice; tek basina yorumlanamaz"),
        dict(etki="guncellik / yil cesitliligi (fark)", RMSE_fark_W=uyg - saf,
             makaleye_giren=False,
             aciklama="iki kolun farki"),
    ]
    t = pd.DataFrame(satir)
    t["Faz3_medyan_W"] = payda
    t["Faz3_payda_kumesi"] = FAZ3_PAYDA_ADI
    t["oran_algoritma_farkina"] = t.RMSE_fark_W / payda
    return t


# --------------------------------------------------------------------------- #
# 3) tohum yayilimi - YIL BAZINDA
# --------------------------------------------------------------------------- #
def tohum_yayilimi(d: pd.DataFrame) -> pd.DataFrame:
    """Ornekleme tesadufunun buyuklugu, (K, test_yil, model) basina.

    Havuzlanmis ortalama YANLIS okunur: 2019/K=5'te havuz tam 5 yil oldugu
    icin cekim havuzun tamamini alir ve yayilim TANIM GEREGI sifirdir;
    2020/K=5'te havuz 6 yil, yani yayilim yine kucuktur. Bes yil uzerinden
    havuzlamak "orneklem tesadufu onemsiz" yanilgisi uretir.

    havuz_orani sutunu bu yapisal etkiyi acikca gosterir.
    """
    a = d[d.kol == "altornekleme"]
    if a.empty:
        return pd.DataFrame()

    g = (a.groupby(["pencere", "test_yil", "model"], as_index=False)
         .agg(tohum_sayisi=("RMSE", "size"), RMSE_ort=("RMSE", "mean"),
              RMSE_min=("RMSE", "min"), RMSE_maks=("RMSE", "max"),
              RMSE_std=("RMSE", lambda s: s.std(ddof=1)),
              egitim_n=("egitim_n", "mean")))
    g["RMSE_aralik_W"] = g.RMSE_maks - g.RMSE_min

    # havuz orani: cekilen satir / havuzdaki satir
    havuz = (d[(d.kol == "kaydirmali") & (d.pencere == "tum")]
             .groupby("test_yil")["egitim_n"].mean().rename("havuz_n"))
    g = g.join(havuz, on="test_yil")
    g["havuz_orani"] = (g.egitim_n / g.havuz_n).round(4)

    g["Faz3_medyan_W"] = FAZ3_MEDYAN[FAZ3_PAYDA_ADI]
    g["yayilim_algoritma_farkina"] = g.RMSE_aralik_W / FAZ3_MEDYAN[FAZ3_PAYDA_ADI]
    g["pencere"] = _pencere_kategori(g["pencere"])
    return g.sort_values(["pencere", "test_yil", "model"]).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# 4) model x pencere etkilesimi
# --------------------------------------------------------------------------- #
def model_pencere_etkilesimi(d: pd.DataFrame, kol: str = "kaydirmali") -> dict:
    """Veri hacmi KAZANAN algoritmayi degistiriyor mu?

    Faz 2'de rastgele bolme siralamayi ters cevirmisti. Hacim de ceviriyorsa
    bu, tek yillik kiyaslama calismalarinin gecersizligine Faz 3'ten BAGIMSIZ
    ikinci bir kanit olur.
    """
    o = _tohum_ortala(d)
    o = o[o.kol == kol]
    if o.empty:
        return {}

    # (a) pencere seviyesinde, yillar uzerinde ortalanmis
    p = o.pivot_table(index="pencere", columns="model", values="RMSE", aggfunc="mean")
    p = p.reindex([x for x in PENCERE_SIRA if x in p.index])

    seviye = []
    for pen, r in p.iterrows():
        s = r.sort_values()
        seviye.append(dict(pencere=pen, kazanan=s.index[0], ikinci=s.index[1],
                           kazanan_RMSE=s.iloc[0], ikinci_RMSE=s.iloc[1],
                           ilk_iki_fark_W=s.iloc[1] - s.iloc[0]))
    seviye = pd.DataFrame(seviye)

    # (b) (pencere, yil) kiriliminda - yil bazinda oynaklik gorunsun
    ayrinti = []
    for (pen, yil), g in o.groupby(["pencere", "test_yil"]):
        s = g.set_index("model")["RMSE"].sort_values()
        ayrinti.append(dict(pencere=pen, test_yil=yil, kazanan=s.index[0],
                            ilk_iki_fark_W=s.iloc[1] - s.iloc[0]))
    ayrinti = pd.DataFrame(ayrinti)
    ayrinti["pencere"] = _pencere_kategori(ayrinti["pencere"])

    return {
        "kol": kol,
        "pencere_bazinda": seviye,
        "pencere_yil_bazinda": ayrinti.sort_values(["pencere", "test_yil"]),
        "kazanan_degisiyor_mu": bool(seviye.kazanan.nunique() > 1),
        "farkli_kazanan_sayisi": int(seviye.kazanan.nunique()),
        "kazanan_dagilimi": seviye.kazanan.value_counts().to_dict(),
    }


# --------------------------------------------------------------------------- #
# 5) varyans ayristirmasi
# --------------------------------------------------------------------------- #
def varyans_ayristirmasi(d: pd.DataFrame, kol: str = "kaydirmali",
                         deger: str = "nRMSE_kapasite") -> pd.DataFrame:
    """{pencere, model, test_yil} uc faktorlu kare toplami ayristirmasi.

    YALNIZCA 3 hizli modelin ortak alt kumesinde hesaplanir. Genis kosunun 10
    modelli araligi ayni tabloya KONMAZ: 10 seviyeli bir faktorun aralig 5
    seviyeliden yapisal olarak buyuk cikar ve algoritma payini sisirir.

    Hucre basina tek gozlem oldugu icin uclu etkilesim artik terime duser.
    """
    o = _tohum_ortala(d)
    o = o[(o.kol == kol) & (o.model.isin(HIZLI_ALTKUME))]
    if o.empty:
        return pd.DataFrame()

    faktor = ["pencere", "model", "test_yil"]
    beklenen = int(np.prod([o[f].nunique() for f in faktor]))
    if len(o) != beklenen:
        raise ValueError(
            f"tasarim dengeli degil: {len(o)} satir, beklenen {beklenen} "
            f"({' x '.join(f'{o[f].nunique()} {f}' for f in faktor)}). "
            "Eksik hucreyle kare toplami ayristirmasi yanlis sonuc verir - "
            "once eksik hucreleri tamamlayin.")

    y = o[deger].to_numpy()
    genel = y.mean()
    ss_toplam = float(np.sum((y - genel) ** 2))

    def ana(f):
        m = o.groupby(f)[deger].mean()
        n = o.groupby(f).size()
        return float(np.sum(n.to_numpy() * (m.to_numpy() - genel) ** 2))

    def ikili(f1, f2):
        m12 = o.groupby([f1, f2])[deger].mean()
        n12 = o.groupby([f1, f2]).size()
        m1 = o.groupby(f1)[deger].mean()
        m2 = o.groupby(f2)[deger].mean()
        t = 0.0
        for (a, b), v in m12.items():
            t += n12[(a, b)] * (v - m1[a] - m2[b] + genel) ** 2
        return float(t)

    kalem = {
        "pencere (veri hacmi)": ana("pencere"),
        "model (algoritma)": ana("model"),
        "test_yil (yil)": ana("test_yil"),
        "pencere x model": ikili("pencere", "model"),
        "pencere x test_yil": ikili("pencere", "test_yil"),
        "model x test_yil": ikili("model", "test_yil"),
    }
    kalem["artik (uclu etkilesim)"] = ss_toplam - sum(kalem.values())

    t = pd.DataFrame([{"kaynak": k, "kare_toplami": v,
                       "varyans_payi_yuzde": 100.0 * v / ss_toplam}
                      for k, v in kalem.items()])
    t.attrs["deger"] = deger
    t.attrs["kol"] = kol
    t.attrs["model_sayisi"] = int(o.model.nunique())
    return t.sort_values("varyans_payi_yuzde", ascending=False).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# 6) konum bazinda
# --------------------------------------------------------------------------- #
def konum_tablosu(dk: pd.DataFrame, kol: str = "kaydirmali") -> pd.DataFrame:
    """Konumlar arasi kiyas - nRMSE_ortalama.

    Mutlak W konumlar arasinda kiyaslanamaz: alti konumun ortalama uretimi
    farkli. Payda o konumun kendi gunduz ortalamasi.
    """
    o = dk[dk.kol == kol]
    if o.empty:
        return pd.DataFrame()
    t = o.pivot_table(index=["konum"], columns="pencere",
                      values="nRMSE_ortalama", aggfunc="mean")
    return t.reindex(columns=[x for x in PENCERE_SIRA if x in t.columns])
