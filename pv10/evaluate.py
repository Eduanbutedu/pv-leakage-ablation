"""Degerlendirme metrikleri.

Makaledeki protokolu birebir cogaltir: gunduz saatleri (H_sun > 0), MAE, RMSE,
iki ayri paydali nRMSE, R2 ve persistence'a gore beceri (skill). Ek olarak
Q2 icin gerekli iki arac: gun-blogu bootstrap guven araligi ve iki tahminin
farkinin anlamliligini test eden Diebold-Mariano.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import KAPASITE_W, SEED


def gunduz_maskesi(o: pd.DataFrame, gece_dahil: bool = False) -> np.ndarray:
    """Gunduz gozlemleri: PVGIS'in H_sun sutunu pozitif olanlar."""
    if gece_dahil:
        return np.ones(len(o), dtype=bool)
    return (o["H_sun"] > 0).to_numpy()


def metrikler(y: np.ndarray, tahmin: np.ndarray,
              persistence: np.ndarray | None = None) -> dict[str, float]:
    """MAE, RMSE, nRMSE (iki payda), R2 ve persistence becerisi."""
    y = np.asarray(y, dtype=float)
    tahmin = np.asarray(tahmin, dtype=float)
    hata = tahmin - y

    rmse = float(np.sqrt(np.mean(hata ** 2)))
    mae = float(np.mean(np.abs(hata)))
    ortalama = float(np.mean(y))
    ss_tot = float(np.sum((y - ortalama) ** 2))

    m = {
        "MAE": mae,
        "RMSE": rmse,
        "nRMSE_ortalama": 100.0 * rmse / ortalama if ortalama > 0 else np.nan,
        "nRMSE_kapasite": 100.0 * rmse / KAPASITE_W,
        "R2": 1.0 - float(np.sum(hata ** 2)) / ss_tot if ss_tot > 0 else np.nan,
        "n": int(len(y)),
    }

    if persistence is not None:
        p_rmse = float(np.sqrt(np.mean((np.asarray(persistence, float) - y) ** 2)))
        m["RMSE_persistence"] = p_rmse
        m["skill"] = 100.0 * (1.0 - rmse / p_rmse) if p_rmse > 0 else np.nan
    return m


def gun_blogu_bootstrap(y: np.ndarray, tahmin: np.ndarray, gunler: np.ndarray,
                        tekrar: int = 1000, seed: int = SEED) -> dict[str, tuple]:
    """Gun bloklarini yerine koyarak yeniden ornekleyip %95 GA verir.

    Gun icindeki bagimliligi korumak icin tek tek saatler degil TAM GUNLER
    yeniden orneklenir - makaledeki yaklasimin aynisi.
    """
    rng = np.random.default_rng(seed)
    y = np.asarray(y, float)
    tahmin = np.asarray(tahmin, float)

    indeksler = {g: np.flatnonzero(gunler == g) for g in np.unique(gunler)}
    anahtarlar = np.array(list(indeksler.keys()))

    rmse_d, mae_d, r2_d = [], [], []
    for _ in range(tekrar):
        secilen = rng.choice(anahtarlar, size=len(anahtarlar), replace=True)
        idx = np.concatenate([indeksler[g] for g in secilen])
        yy, tt = y[idx], tahmin[idx]
        hata = tt - yy
        rmse_d.append(np.sqrt(np.mean(hata ** 2)))
        mae_d.append(np.mean(np.abs(hata)))
        ss = np.sum((yy - yy.mean()) ** 2)
        r2_d.append(1.0 - np.sum(hata ** 2) / ss if ss > 0 else np.nan)

    def ga(v):
        return (float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5)))

    return {"RMSE": ga(rmse_d), "MAE": ga(mae_d), "R2": ga(r2_d)}


def diebold_mariano(y: np.ndarray, tahmin_a: np.ndarray, tahmin_b: np.ndarray,
                    h: int = 24, kume: np.ndarray | None = None) -> dict[str, float]:
    """Iki tahminin dogrulugu anlamli olarak farkli mi?

    Kare hata kayip fonksiyonuyla Diebold-Mariano testi. Newey-West tipi
    otokorelasyon duzeltmesi h-1 gecikmeye kadar uygulanir. Pozitif DM
    istatistigi A'nin B'den DAHA KOTU oldugunu gosterir.

    Bu, "Polynomial Ridge Gradient Boosting'i 0.52 W geçti" turu farklarin
    gurultu olup olmadigini gosterecek arac.
    """
    y = np.asarray(y, float)
    d = (np.asarray(tahmin_a, float) - y) ** 2 - (np.asarray(tahmin_b, float) - y) ** 2

    # KRITIK: birden fazla konum havuzlandiginda ayni zaman damgasi veri
    # setinde birden fazla kez gecer. Newey-West yalnizca zaman icindeki
    # otokorelasyonu duzeltir, konumlar arasi eszamanli korelasyonu DEGIL;
    # duzeltilmezse varyans kucuk tahmin edilir ve p-degeri yapay olarak
    # kuculur. Cozum: kayip farkini once zaman damgasi duzeyinde ortalayip
    # testi o seri uzerinde kosmak.
    if kume is not None:
        kume = np.asarray(kume)
        sira = np.argsort(kume, kind="stable")
        k_sirali, d_sirali = kume[sira], d[sira]
        sinir = np.flatnonzero(np.r_[True, k_sirali[1:] != k_sirali[:-1]])
        d = np.array([seg.mean() for seg in np.split(d_sirali, sinir[1:])])

    n = len(d)
    d_ort = float(np.mean(d))

    # uzun donem varyans (Newey-West, Bartlett cekirdegi)
    gamma0 = float(np.mean((d - d_ort) ** 2))
    v = gamma0
    for k in range(1, min(h, n - 1)):
        gk = float(np.mean((d[k:] - d_ort) * (d[:-k] - d_ort)))
        v += 2.0 * (1.0 - k / h) * gk
    v = max(v, 1e-12)

    dm = d_ort / np.sqrt(v / n)
    # normal yaklasimla iki tarafli p degeri
    from math import erfc, sqrt
    p = erfc(abs(dm) / sqrt(2.0))
    return {"DM": float(dm), "p": float(p), "fark_ortalama": d_ort}


def etki_buyuklugu(rmse_a: float, rmse_b: float) -> dict[str, float]:
    """Iki modelin RMSE farkini yorumlanabilir olceklerde verir.

    Istatistiksel anlamlilik ile pratik anlamlilik ayni sey degildir: yeterince
    buyuk bir orneklemde 0.8 W'lik bir fark da "anlamli" cikar. Bu yuzden her
    karsilastirmada p-degerinin yaninda etki buyuklugu raporlanmalidir.
    """
    fark = rmse_a - rmse_b
    return {
        "RMSE_fark_W": float(fark),
        "RMSE_fark_kapasite_yuzde": float(100.0 * fark / KAPASITE_W),
        "RMSE_fark_bagil_yuzde": float(100.0 * fark / rmse_b) if rmse_b else np.nan,
    }