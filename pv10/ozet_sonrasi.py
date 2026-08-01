"""Faz 4 - SONUCLAR GORULDUKTEN SONRA eklenen ozet tablolari.

ozet.py'den AYRI tutulmasinin tek sebebi kayit duzeni. ozet.py izgara
kosulmadan once yazildi ve o dosyaya dokunulmadigi `git log -- pv10/ozet.py`
ile gosterilebilir; metrik seciminin post-hoc olmadigi iddiasi buna dayaniyor.
Burada duran iki tablo ise sayilar gorulduKTEN SONRA eklendi. Karistirilmalari
o ayrimi yok ederdi.

Ikisi de yeni bir kosu gerektirmez; doygunluk.csv'de zaten duran sutunlardan
hesaplanir.

--------------------------------------------------------------------------- #
1) algoritma_span - NEDEN SONRADAN EKLENDI

Ana oran tablosu hacim SPAN'ini (K=1 -> K=tum, 2.204968 W) Faz 3'un algoritma
MEDYAN IKILI farkiyla (0.4669 W) kiyasliyordu. Ikisi ayni turden istatistik
degil: biri bir aralik, digeri ikili farklarin medyani. Hakem buraya vurur.
Ayni turden kiyas icin algoritma tarafinin da SPAN olarak verilmesi gerekiyor:
sabit K'de en iyi model ile en kotu model arasindaki fark.

2) ga_uclari - NEDEN SONRADAN EKLENDI

Gun blogu bootstrap %95 GA'si hucre basina hesaplanip loga yazildi (plandaydi,
sonradan secilmedi) ama hicbir ozet tablosunda yuzeye cikmiyordu. Ogrenme
egrisinin iki ucu icin GA'lar cakisiyorsa 2.205 W'lik etki icin "olculdu"
denemez.

GA YORUMU ICIN UYARI: iki ucun MARJINAL GA'larinin cakismasi "fark yok"
demek DEGILDIR. Cakismama farki ispatlar, cakisma farksizligi ispatlamaz -
ozellikle burada iki tahmin AYNI test setinde uretildigi icin hatalar
korelasyonlu ve marjinal GA kiyasi muhafazakardir. Kesin ifade icin
eslestirilmis test gerekir (Faz 3'teki kumelenmis Diebold-Mariano).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import EGITIM_PENCERELERI

PENCERE_SIRA = [str(p) for p in EGITIM_PENCERELERI]


def _pencere_sirala(d: pd.DataFrame, sutun: str = "pencere") -> pd.DataFrame:
    k = pd.Categorical(d[sutun].astype(str), categories=PENCERE_SIRA, ordered=True)
    return d.assign(**{sutun: k}).sort_values(sutun)


# --------------------------------------------------------------------------- #
# A) algoritma span'i vs hacim span'i - AYNI TURDEN ISTATISTIK
# --------------------------------------------------------------------------- #
def algoritma_span(d: pd.DataFrame, kol: str = "kaydirmali") -> pd.DataFrame:
    """Sabit K'de modeller arasi aralik, sabit modelde K araligi.

    Uc blok tek tabloda, `satir_turu` ile ayrilir:
      pencere_rmse : her K'de uc modelin RMSE'si + algoritma span'i
      hacim_span   : her modelde K=1 -> K=tum farki
      kiyas        : iki span'in min / ortalama / maks ozeti
    """
    o = d[d.kol == kol]
    if o.empty:
        return pd.DataFrame()

    # yillar (ve varsa tohumlar) uzerinde ortalama
    g = o.groupby(["pencere", "model"], as_index=False)["RMSE"].mean()
    p = g.pivot(index="pencere", columns="model", values="RMSE")
    p = p.reindex([x for x in PENCERE_SIRA if x in p.index])
    modeller = list(p.columns)

    blok1 = []
    for pen, r in p.iterrows():
        s = r.sort_values()
        blok1.append(dict(satir_turu="pencere_rmse", seviye=str(pen),
                          **{m: r[m] for m in modeller},
                          en_iyi=s.index[0], en_kotu=s.index[-1],
                          span_W=s.iloc[-1] - s.iloc[0]))

    blok2 = []
    if "1" in p.index and "tum" in p.index:
        for m in modeller:
            blok2.append(dict(satir_turu="hacim_span", seviye=m,
                              en_iyi="K=tum", en_kotu="K=1",
                              span_W=p.loc["1", m] - p.loc["tum", m]))

    a_span = np.array([b["span_W"] for b in blok1], dtype=float)
    h_span = np.array([b["span_W"] for b in blok2], dtype=float)
    blok3 = []
    for ad, v in (("algoritma_span (K sabit)", a_span),
                  ("hacim_span (model sabit)", h_span)):
        if len(v):
            blok3.append(dict(satir_turu="kiyas", seviye=ad,
                              span_min_W=v.min(), span_ort_W=v.mean(),
                              span_maks_W=v.max(), n=len(v)))

    t = pd.DataFrame(blok1 + blok2 + blok3)
    t.attrs["kol"] = kol
    return t


# --------------------------------------------------------------------------- #
# B) ogrenme egrisinin iki ucunda guven araligi
# --------------------------------------------------------------------------- #
def ga_uclari(d: pd.DataFrame) -> pd.DataFrame:
    """Altornekleme K=1 ile paylasilan K=tum ucunun %95 GA'lari cakisiyor mu?

    K=tum hucresi altornekleme kolunda URETILMEZ (havuzun tamami = kaydirmali
    K=tum). Ust uc bu yuzden kaydirmali koldan alinir; egri zaten o noktada
    birlesiyor.
    """
    gerekli = {"RMSE_GA_alt", "RMSE_GA_ust"}
    if not gerekli.issubset(d.columns):
        return pd.DataFrame()

    alt = d[(d.kol == "altornekleme") & (d.pencere.astype(str) == "1")]
    ust = d[(d.kol == "kaydirmali") & (d.pencere.astype(str) == "tum")]
    if alt.empty or ust.empty:
        return pd.DataFrame()

    u = ust[["test_yil", "model", "RMSE", "RMSE_GA_alt", "RMSE_GA_ust"]]
    m = alt[["test_yil", "model", "tohum", "RMSE", "RMSE_GA_alt",
             "RMSE_GA_ust"]].merge(u, on=["test_yil", "model"],
                                   suffixes=("_K1", "_Ktum"))
    if len(m) != len(alt):
        raise ValueError(f"eslesme bozuk: {len(m)} != {len(alt)}")

    m["fark_W"] = m.RMSE_K1 - m.RMSE_Ktum
    m["cakisiyor"] = ~((m.RMSE_GA_alt_K1 > m.RMSE_GA_ust_Ktum)
                       | (m.RMSE_GA_alt_Ktum > m.RMSE_GA_ust_K1))
    m["K1_GA_genislik_W"] = m.RMSE_GA_ust_K1 - m.RMSE_GA_alt_K1
    m["Ktum_GA_genislik_W"] = m.RMSE_GA_ust_Ktum - m.RMSE_GA_alt_Ktum

    ozet = pd.DataFrame([dict(
        test_yil="TOPLAM", model="", tohum=np.nan,
        RMSE_K1=np.nan, RMSE_Ktum=np.nan,
        fark_W=m.fark_W.mean(),
        cakisiyor=bool(m.cakisiyor.any()),
        cakisan_n=int(m.cakisiyor.sum()), toplam_n=len(m),
        K1_GA_genislik_W=m.K1_GA_genislik_W.mean(),
        Ktum_GA_genislik_W=m.Ktum_GA_genislik_W.mean())])

    m = m.sort_values(["test_yil", "model", "tohum"])
    return pd.concat([m, ozet], ignore_index=True)
