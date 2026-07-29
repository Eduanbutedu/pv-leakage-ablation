"""Faz 3 - siralama kararliligi.

Faz 2 sizintinin basarimi ne kadar sistiktigini olcmustu. Burada asil soruyu
soruyoruz: tek yillik bir kiyaslama calismasi algoritmalari ayirt edebilir mi?

Uc arac:
  1. Kumelenmis Diebold-Mariano  -> fark istatistiksel olarak anlamli mi
  2. Etki buyuklugu              -> fark pratik olarak anlamli mi
  3. Yillar arasi Kendall tau    -> siralama yildan yila korunuyor mu

Ikinci madde kritik. Yeterince buyuk bir orneklemde 0.5 W'lik bir fark da
"anlamli" cikar; bu, sıralama iddiasini haklı cikarmaz. Bu yuzden p-degeri
asla tek basina raporlanmaz.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd

from .config import KAPASITE_W, SEED
from .evaluate import (diebold_mariano, etki_buyuklugu, gunduz_maskesi,
                       metrikler)
from .experiment import OznitelikOnbellegi, bolme_indeksleri
from .models import modeller


# --------------------------------------------------------------------------- #
# yil bazinda tahminler
# --------------------------------------------------------------------------- #
def yil_tahminleri(onbellek: OznitelikOnbellegi, model_adlari: list[str],
                   test_yil: int, ilerleme=print) -> pd.DataFrame:
    """Bir test yili icin tum modellerin gunduz tahminlerini tek tabloda verir.

    Kurgu Faz 2'nin 'temiz' varyantiyla ayni: kronolojik bolme, gunduz
    degerlendirmesi, sizintisiz oznitelikler.
    """
    o, X = onbellek.al(eszaman=False)
    tr, te = bolme_indeksleri(o, test_yil, rastgele=False)

    test_satirlari = o.iloc[te]
    maske = gunduz_maskesi(test_satirlari)

    cikti = pd.DataFrame({
        "time_utc": test_satirlari["time_utc"].to_numpy()[maske],
        "konum": test_satirlari["konum"].to_numpy()[maske],
        "y": test_satirlari["y"].to_numpy()[maske],
        "persistence": test_satirlari["persistence"].to_numpy()[maske],
    })

    havuz = modeller()
    Xtr, ytr = o.iloc[tr][X], o.iloc[tr]["y"]
    Xte = test_satirlari[X]

    for ad in model_adlari:
        hat = havuz[ad]
        hat.fit(Xtr, ytr)
        cikti[ad] = hat.predict(Xte)[maske]
        ilerleme(f"    {ad}: RMSE "
                 f"{metrikler(cikti['y'], cikti[ad])['RMSE']:.2f}")

    return cikti


# --------------------------------------------------------------------------- #
# ikili karsilastirma
# --------------------------------------------------------------------------- #
def esli_bootstrap(y, tahmin_a, tahmin_b, gunler, tekrar=1000,
                   seed=SEED) -> tuple[float, float]:
    """RMSE FARKI icin gun-blogu bootstrap %95 guven araligi.

    Iki modelin ayri ayri guven araliklarini karsilastirmak yanlistir - ayni
    gunlerde degerlendirildikleri icin hatalari korelelidir. Esli bootstrap
    farki dogrudan orneklendirir.
    """
    rng = np.random.default_rng(seed)
    y = np.asarray(y, float)
    a, b = np.asarray(tahmin_a, float), np.asarray(tahmin_b, float)

    indeks = {g: np.flatnonzero(gunler == g) for g in np.unique(gunler)}
    anahtar = np.array(list(indeks.keys()))

    farklar = []
    for _ in range(tekrar):
        secilen = rng.choice(anahtar, size=len(anahtar), replace=True)
        idx = np.concatenate([indeks[g] for g in secilen])
        ra = np.sqrt(np.mean((a[idx] - y[idx]) ** 2))
        rb = np.sqrt(np.mean((b[idx] - y[idx]) ** 2))
        farklar.append(ra - rb)

    return (float(np.percentile(farklar, 2.5)),
            float(np.percentile(farklar, 97.5)))


def ikili_karsilastirma(tahmin: pd.DataFrame, model_adlari: list[str],
                        test_yil: int, bootstrap: bool = True) -> pd.DataFrame:
    """Her model ciftini karsilastirir: DM testi + etki buyuklugu + GA."""
    y = tahmin["y"].to_numpy()
    damga = tahmin["time_utc"].to_numpy()          # DM kumeleme anahtari
    gunler = pd.to_datetime(tahmin["time_utc"]).dt.date.to_numpy()

    rmse = {ad: metrikler(y, tahmin[ad])["RMSE"] for ad in model_adlari}

    satirlar = []
    for a, b in combinations(model_adlari, 2):
        # kume=damga: alti konum ayni saati paylastigi icin zorunlu
        dm = diebold_mariano(y, tahmin[a].to_numpy(), tahmin[b].to_numpy(),
                             kume=damga)
        eb = etki_buyuklugu(rmse[a], rmse[b])
        s = dict(test_yil=test_yil, model_a=a, model_b=b,
                 RMSE_a=round(rmse[a], 2), RMSE_b=round(rmse[b], 2),
                 **{k: round(v, 4) for k, v in eb.items()},
                 DM=round(dm["DM"], 3), p=round(dm["p"], 4),
                 anlamli=dm["p"] < 0.05)
        if bootstrap:
            alt, ust = esli_bootstrap(y, tahmin[a], tahmin[b], gunler)
            s["fark_GA_alt"], s["fark_GA_ust"] = round(alt, 2), round(ust, 2)
        satirlar.append(s)

    return pd.DataFrame(satirlar)


# --------------------------------------------------------------------------- #
# siralama kararliligi
# --------------------------------------------------------------------------- #
def siralama_tablosu(yil_rmse: pd.DataFrame) -> pd.DataFrame:
    """Yil x model RMSE tablosundan yil bazinda siralama uretir (1 = en iyi)."""
    return yil_rmse.rank(axis=1, method="min").astype(int)


def kendall_tau_matrisi(siralama: pd.DataFrame) -> pd.DataFrame:
    """Yillar arasi siralama benzerligi. 1.0 = ayni siralama."""
    from scipy.stats import kendalltau
    yillar = list(siralama.index)
    m = pd.DataFrame(index=yillar, columns=yillar, dtype=float)
    for i in yillar:
        for j in yillar:
            m.loc[i, j] = kendalltau(siralama.loc[i], siralama.loc[j]).statistic
    return m


def kararlilik_ozeti(karsilastirma: pd.DataFrame,
                     siralama: pd.DataFrame) -> dict:
    """Makalenin cevaplayacagi sorulari tek sozlukte toplar."""
    n_yil = siralama.shape[0]
    kazanan = siralama.idxmin(axis=1)

    # her yilda en iyi ile ikinci arasindaki fark
    en_yakin = []
    for yil in siralama.index:
        s = siralama.loc[yil].sort_values()
        ilk, ikinci = s.index[0], s.index[1]
        k = karsilastirma[(karsilastirma.test_yil == yil)
                          & (((karsilastirma.model_a == ilk)
                              & (karsilastirma.model_b == ikinci))
                             | ((karsilastirma.model_a == ikinci)
                                & (karsilastirma.model_b == ilk)))]
        if len(k):
            r = k.iloc[0]
            en_yakin.append(dict(yil=yil, en_iyi=ilk, ikinci=ikinci,
                                 fark_W=abs(r.RMSE_fark_W),
                                 fark_kapasite_yuzde=abs(r.RMSE_fark_kapasite_yuzde),
                                 p=r.p, anlamli=bool(r.anlamli)))

    ey = pd.DataFrame(en_yakin)
    tau = kendall_tau_matrisi(siralama)
    ust = tau.to_numpy()[np.triu_indices(n_yil, k=1)]

    return {
        "yil_sayisi": n_yil,
        "kazanan_dagilimi": kazanan.value_counts().to_dict(),
        "farkli_kazanan_sayisi": int(kazanan.nunique()),
        "kendall_tau_ortalama": float(np.mean(ust)),
        "kendall_tau_min": float(np.min(ust)),
        "ilk_ikili_anlamli_yil": int(ey.anlamli.sum()) if len(ey) else 0,
        "ilk_ikili_medyan_fark_W": float(ey.fark_W.median()) if len(ey) else np.nan,
        "ilk_ikili_medyan_fark_kapasite_yuzde":
            float(ey.fark_kapasite_yuzde.median()) if len(ey) else np.nan,
        "en_yakin_detay": ey,
    }