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

from pathlib import Path

import numpy as np
import pandas as pd

from .config import EGITIM_PENCERELERI, KAYDIRMALI_TOHUM
from .doygunluk import tahmin_dosyasi
from .evaluate import diebold_mariano, etki_buyuklugu, metrikler
from .ranking import esli_bootstrap

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


# --------------------------------------------------------------------------- #
# C) egri uclarinda ESLI test - kumelenmis Diebold-Mariano
# --------------------------------------------------------------------------- #
# Kumelenme birimi Faz 3'un kullandiginin AYNISI: zaman damgasi (time_utc).
# Gerekce evaluate.diebold_mariano icinde yazili - alti konum ayni saati
# paylastigi icin ayni damga veri setinde alti kez geciyor; Newey-West
# yalnizca zaman icindeki otokorelasyonu duzeltir, konumlar arasi eszamanli
# korelasyonu duzeltmez. Kayip farki once damga duzeyinde ortalanir, test o
# seri uzerinde kosulur. ranking.py:110 ayni cagriyi 'kume=damga' ile yapiyor.
DM_KUMELENME_BIRIMI = "time_utc (zaman damgasi); alti konum ayni damgada"


def _tahmin_oku(dizin: Path, kol: str, pencere, test_yil: int,
                model_ad: str, tohum: int) -> pd.DataFrame:
    yol = tahmin_dosyasi(dizin, kol, pencere, test_yil, model_ad, tohum)
    if not yol.exists():
        raise FileNotFoundError(
            f"{yol} yok. Tahmin vektorleri --tahmin-kaydet ile uretilir; "
            "eksik dosyayi sessizce atlamak DM tablosunu yaniltir.")
    return pd.read_parquet(yol)


def uc_dm(tahmin_dizin, test_yillari, model_adlari, tohumlar,
          bootstrap: bool = True) -> pd.DataFrame:
    """Altornekleme K=1 ile paylasilan K=tum ucu arasinda ESLI DM testi.

    Marjinal GA kiyasi (ga_uclari) muhafazakardir: iki uc AYNI test setinde
    degerlendirildigi icin hatalari korelasyonlu ve esli olmayan kiyas bu
    korelasyonu yok sayar. Burada kayip FARKI dogrudan test edilir.

    Isaret kuralı evaluate.diebold_mariano'dan gelir: pozitif DM, A'nin (K=1)
    B'den (K=tum) DAHA KOTU oldugunu gosterir. Beklenen isaret pozitif, ama
    beklenti dogrulama olcutu degil - cikan isaret bulgudur.
    """
    dizin = Path(tahmin_dizin)
    satir = []

    for yil in test_yillari:
        for model in model_adlari:
            ust = _tahmin_oku(dizin, "kaydirmali", "tum", yil, model,
                              KAYDIRMALI_TOHUM)
            for tohum in tohumlar:
                alt = _tahmin_oku(dizin, "altornekleme", 1, yil, model, tohum)

                b = alt.merge(ust, on=["time_utc", "konum"],
                              suffixes=("_K1", "_Ktum"))
                if len(b) != len(alt) or len(b) != len(ust):
                    raise ValueError(
                        f"{yil}/{model}/t{tohum}: eslesme bozuk "
                        f"({len(alt)} / {len(ust)} -> {len(b)}). Iki ucun test "
                        "satirlari birebir ayni olmali.")
                if not np.array_equal(b["y_K1"].to_numpy(), b["y_Ktum"].to_numpy()):
                    raise ValueError(f"{yil}/{model}/t{tohum}: y serileri farkli")

                y = b["y_K1"].to_numpy()
                a1 = b["tahmin_K1"].to_numpy()
                at = b["tahmin_Ktum"].to_numpy()
                damga = b["time_utc"].to_numpy()

                dm = diebold_mariano(y, a1, at, kume=damga)
                r1 = metrikler(y, a1)["RMSE"]
                rt = metrikler(y, at)["RMSE"]
                eb = etki_buyuklugu(r1, rt)

                s = dict(test_yil=yil, model=model, tohum=tohum,
                         RMSE_K1=r1, RMSE_Ktum=rt, **eb,
                         DM=dm["DM"], p=dm["p"], anlamli=dm["p"] < 0.05,
                         n_ham=len(b), n_kume=int(pd.unique(damga).size),
                         kumelenme=DM_KUMELENME_BIRIMI)

                if bootstrap:
                    gunler = pd.to_datetime(b["time_utc"]).dt.date.to_numpy()
                    lo, hi = esli_bootstrap(y, a1, at, gunler)
                    s["fark_GA_alt"], s["fark_GA_ust"] = lo, hi
                    s["GA_sifiri_iceriyor"] = bool(lo <= 0.0 <= hi)

                satir.append(s)

    return pd.DataFrame(satir)


# --------------------------------------------------------------------------- #
# C2) ayni yil icinde MODEL CIFTLERI arasinda esli DM
# --------------------------------------------------------------------------- #
def yil_ici_dm(tahmin_dizin, test_yil: int, model_ciftleri,
               kol: str = "kaydirmali", pencere="tum",
               tohum: int = KAYDIRMALI_TOHUM,
               bootstrap: bool = True) -> pd.DataFrame:
    """Bir test yilinda iki modelin farki anlamli mi?

    uc_dm egrinin iki UCUNU kiyasliyor; bu ayni hucrede iki MODELI kiyasliyor.
    Kumelenme birimi ayni: zaman damgasi (bkz. DM_KUMELENME_BIRIMI).

    Pozitif DM -> model_a, model_b'den DAHA KOTU.
    """
    dizin = Path(tahmin_dizin)
    satir = []

    for a_ad, b_ad in model_ciftleri:
        a = _tahmin_oku(dizin, kol, pencere, test_yil, a_ad, tohum)
        b = _tahmin_oku(dizin, kol, pencere, test_yil, b_ad, tohum)

        m = a.merge(b, on=["time_utc", "konum"], suffixes=("_a", "_b"))
        if len(m) != len(a) or len(m) != len(b):
            raise ValueError(f"{test_yil} {a_ad}/{b_ad}: eslesme bozuk "
                             f"({len(a)} / {len(b)} -> {len(m)})")
        if not np.array_equal(m["y_a"].to_numpy(), m["y_b"].to_numpy()):
            raise ValueError(f"{test_yil} {a_ad}/{b_ad}: y serileri farkli")

        y = m["y_a"].to_numpy()
        ta, tb = m["tahmin_a"].to_numpy(), m["tahmin_b"].to_numpy()
        damga = m["time_utc"].to_numpy()

        dm = diebold_mariano(y, ta, tb, kume=damga)
        ra, rb = metrikler(y, ta)["RMSE"], metrikler(y, tb)["RMSE"]
        s = dict(test_yil=test_yil, model_a=a_ad, model_b=b_ad,
                 RMSE_a=ra, RMSE_b=rb, **etki_buyuklugu(ra, rb),
                 DM=dm["DM"], p=dm["p"], anlamli=dm["p"] < 0.05,
                 n_ham=len(m), n_kume=int(pd.unique(damga).size),
                 kumelenme=DM_KUMELENME_BIRIMI)

        if bootstrap:
            gunler = pd.to_datetime(m["time_utc"]).dt.date.to_numpy()
            lo, hi = esli_bootstrap(y, ta, tb, gunler)
            s["fark_GA_alt"], s["fark_GA_ust"] = lo, hi
            s["GA_sifiri_iceriyor"] = bool(lo <= 0.0 <= hi)

        satir.append(s)

    return pd.DataFrame(satir)


# --------------------------------------------------------------------------- #
# D) DUZELTILMIS ANA TABLO - uc soru, ayni turden olculer
# --------------------------------------------------------------------------- #
# hacim_orani (ozet.py) hacim SPAN'ini Faz 3'un algoritma MEDYAN IKILI
# farkiyla boluyordu. Ikisi ayni turden istatistik degil; o tablo yerinde
# duruyor ama makalenin ana iddiasi BURADAN okunur.
#
# Uc kural:
#   1. Hacim etkisi TEK SAYIYA indirgenmez - model bazinda verilir. Havuzlanmis
#      2.204968 W ortalamasi, Linear Regression'in 0.209944 W'sini HGB'nin
#      4.493244 W'siyle ayni potaya koyuyor ve etkinin model bagimli oldugunu
#      gizliyor.
#   2. Algoritma etkisi icin iki farkli soru iki farkli sayi ister: "en iyi iki
#      algoritma ayirt edilebilir mi" (ilk-iki farki) ile "algoritma secimi ne
#      kadar oynatir" (havuz span'i) ayni sey degil.
#   3. Her satir kaynagini ve on-kayitli mi sonradan mi eklendigini tasir.
DUZELTILMIS_KAYNAK = {
    "S1": "sonuclar/doygunluk_ozet_dm.csv (uc_dm)",
    "S2": "sonuclar/doygunluk_genis.csv",
    "S3": "sonuclar/doygunluk_ozet_varyans.csv + doygunluk_genis.csv",
}


def duzeltilmis_ana_tablo(dm: pd.DataFrame, genis: pd.DataFrame,
                          varyans: pd.DataFrame,
                          yil_dm: pd.DataFrame | None = None) -> pd.DataFrame:
    """Uc soruyu ayri satirlarda, ayni turden olculerle veren ana tablo.

    dm      : uc_dm ciktisi (esli DM, 45 karsilastirma)
    genis   : doygunluk_genis.csv (K=tum, 10 model, 5 yil)
    varyans : ozet.varyans_ayristirmasi ciktisi (3 model, kaydirmali)
    yil_dm  : yil_ici_dm ciktisi; hangi yillarin SINANDIGI buradan gelir
    """
    satir = []

    # --- S1: veri hacmi, MODEL BAZINDA ---------------------------------- #
    if dm is not None and len(dm):
        for model, g in dm.groupby("model"):
            satir.append(dict(
                soru="S1 veri hacmi",
                olcu=f"saf hacim span'i, {model}",
                deger_W=g.RMSE_fark_W.mean(),
                ek=f"{int(g.anlamli.sum())}/{len(g)} esli DM p<0.05",
                aciklama="altornekleme K=1 -> K=tum; yil kompozisyonu sabit",
                hucre=len(g), kaynak=DUZELTILMIS_KAYNAK["S1"],
                kayit="SONRADAN"))

    # --- S2: algoritma secimi, IKI AYRI SORU ---------------------------- #
    if genis is not None and len(genis):
        o = genis[genis.durum == "tamam"].groupby("model")["RMSE"].mean()
        s = o.sort_values()
        n_hucre = int((genis.durum == "tamam").sum())
        en_kotu = s.index[-1]
        s2 = s.drop(en_kotu)
        satir += [
            dict(soru="S2 algoritma", olcu="ilk-iki farki",
                 deger_W=s.iloc[1] - s.iloc[0],
                 ek=f"{s.index[0]} vs {s.index[1]}",
                 aciklama="en iyi iki algoritma ayirt edilebilir mi",
                 hucre=n_hucre, kaynak=DUZELTILMIS_KAYNAK["S2"],
                 kayit="SONRADAN"),
            dict(soru="S2 algoritma", olcu=f"havuz span'i ({en_kotu} haric)",
                 deger_W=s2.iloc[-1] - s2.iloc[0],
                 ek=f"{len(s2)} model",
                 aciklama="makul aday kumesinde algoritma secimi ne oynatir",
                 hucre=n_hucre, kaynak=DUZELTILMIS_KAYNAK["S2"],
                 kayit="SONRADAN"),
            dict(soru="S2 algoritma", olcu="havuz span'i (tam kume)",
                 deger_W=s.iloc[-1] - s.iloc[0],
                 ek=f"{len(s)} model, {en_kotu} dahil",
                 aciklama="zayif aday dahil edilirse span buyur; SVR haric",
                 hucre=n_hucre, kaynak=DUZELTILMIS_KAYNAK["S2"],
                 kayit="SONRADAN"),
        ]

        # yil bazinda kazanan degisimi
        kaz = (genis[genis.durum == "tamam"]
               .loc[lambda x: x.groupby("test_yil").RMSE.idxmin()]
               [["test_yil", "model"]])
        dagilim = kaz.model.value_counts().to_dict()
        satir.append(dict(
            soru="S3 test yili", olcu="kazanan degisimi (10 model)",
            deger_W=np.nan, ek=f"{kaz.model.nunique()} farkli kazanan: {dagilim}",
            aciklama="ayni kurulumda yil degisince kazanan degisiyor mu",
            hucre=n_hucre, kaynak=DUZELTILMIS_KAYNAK["S2"],
            kayit="SONRADAN"))

        # --- KAPSAM: hangi yilin ilk-iki farki SINANDI, hangisi sinanmadi --- #
        # Genis kosuda tahmin vektoru kaydedilmedi; esli DM yalnizca tahmin
        # kaydiyla YENIDEN kosulan yillarda yapilabiliyor. Sinanmayan yillar
        # icin "fark anlamli" da "fark yok" da IDDIA EDILEMEZ.
        ilk_iki = {}
        for yil, gy in genis[genis.durum == "tamam"].groupby("test_yil"):
            s = gy.set_index("model")["RMSE"].sort_values()
            ilk_iki[int(yil)] = (s.index[0], s.index[1], s.iloc[1] - s.iloc[0])

        sinanan = sorted(set(yil_dm.test_yil.astype(int))) if yil_dm is not None \
            and len(yil_dm) else []
        sinanmayan = [y for y in sorted(ilk_iki) if y not in sinanan]

        for yil in sorted(ilk_iki):
            en_iyi, ikinci, fark = ilk_iki[yil]
            if yil in sinanan:
                k = yil_dm[(yil_dm.test_yil == yil)
                           & (((yil_dm.model_a == en_iyi) & (yil_dm.model_b == ikinci))
                              | ((yil_dm.model_a == ikinci) & (yil_dm.model_b == en_iyi)))]
                if len(k):
                    r = k.iloc[0]
                    ek = (f"{en_iyi} vs {ikinci}; p={r.p:.6g}, "
                          f"{'ANLAMLI' if r.anlamli else 'anlamli DEGIL'}")
                else:
                    ek = f"{en_iyi} vs {ikinci}; esli DM kosuldu ama cift yok"
                acik = "esli kumelenmis DM ile SINANDI"
            else:
                ek = f"{en_iyi} vs {ikinci}; SINANMADI"
                acik = ("tahmin vektoru yok -> esli DM kosulamaz; bu yil icin "
                        "ne 'anlamli' ne 'anlamsiz' iddia EDILEMEZ")
            satir.append(dict(
                soru="S3 kapsam", olcu=f"{yil} ilk-iki farki", deger_W=fark,
                ek=ek, aciklama=acik, hucre=10,
                kaynak=DUZELTILMIS_KAYNAK["S2"],
                kayit="SONRADAN"))

        satir.append(dict(
            soru="S3 kapsam", olcu="kazanan degisimi iddiasinin dayanagi",
            deger_W=np.nan,
            ek=f"sinanan yil: {sinanan or 'yok'} | sinanmayan: {sinanmayan}",
            aciklama=("'kazanan yila gore degisiyor' iddiasi yalnizca sinanan "
                      "yil(lar)a dayanir; kalan yillar icin siralama farki "
                      "OLCULDU ama anlamliligi test EDILMEDI"),
            hucre=n_hucre, kaynak=DUZELTILMIS_KAYNAK["S2"], kayit="SONRADAN"))

    # --- S3: test yili ---------------------------------------------------- #
    if varyans is not None and len(varyans):
        v = varyans.set_index("kaynak")["varyans_payi_yuzde"]
        for ad, etiket in (("test_yil (yil)", "varyans payi: test yili"),
                           ("model (algoritma)", "varyans payi: algoritma"),
                           ("pencere (veri hacmi)", "varyans payi: veri hacmi"),
                           ("pencere x model", "varyans payi: hacim x algoritma")):
            if ad in v.index:
                satir.append(dict(
                    soru="S3 test yili", olcu=etiket, deger_W=np.nan,
                    ek=f"%{v[ad]:.6f}",
                    aciklama="uc faktorlu kare toplami, 3 hizli model",
                    hucre=int(varyans.attrs.get("model_sayisi", 0)),
                    kaynak=DUZELTILMIS_KAYNAK["S3"], kayit="ON-KAYITLI"))

    return pd.DataFrame(satir)
