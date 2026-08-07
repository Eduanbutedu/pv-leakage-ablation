"""Gunes geometrisi ve oznitelik uretimi.

Oznitelik tanimlari GUFBD makalesinin 2.3 bolumunu birebir cogaltir:
  - P, G(i), T2m, WS10m'in 24 / 48 / 168 saat gecikmeleri
  - P'nin gecikmeli yuvarlanan ortalama ve standart sapmasi, G(i)'nin yuvarlanan ortalamasi
  - dongusel takvim kodlamasi (saat ve yilin gunu)
  - hedef saatteki gunes yuksekliginin sinusu, ASTRONOMIK olarak hesaplanir
  - gecikmeli berrak-gokyuzu performans orani ve onun yuvarlanan ortalamasi
  - konum tek-sicak (one-hot) kodlama

Kritik nokta: PVGIS'in H_sun sutunu YALNIZCA gunduz maskesi icin kullanilir,
oznitelik olarak asla kullanilmaz. Bunun yerine gunes yuksekligi enlem, boylam
ve zaman damgasindan yeniden turetilir; boylece herhangi bir tahmin ufkunda
mesru sekilde erisilebilir olur.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import (BERRAK_GOK_KATSAYI, ESZAMAN_DEGISKEN, GECIKMELER,
                     GECIKMELI_DEGISKEN, YUVARLANAN)


# --------------------------------------------------------------------------- #
# gunes geometrisi - Spencer (1971) yaklasimlari
# --------------------------------------------------------------------------- #
def gunes_yuksekligi_sin(lat: float, lon: float, zaman_utc: pd.Series) -> np.ndarray:
    """Gunes yukseklik acisinin sinusunu dondurur (ufkun altinda negatif).

    Spencer (1971) yaklasimlariyla deklinasyon ve zaman denklemi hesaplanir.
    zaman_utc UTC olmalidir; saat acisi boylamdan turetilir.
    """
    gun = zaman_utc.dt.dayofyear.to_numpy()
    saat = (zaman_utc.dt.hour.to_numpy()
            + zaman_utc.dt.minute.to_numpy() / 60.0)

    # gun acisi
    gama = 2.0 * np.pi * (gun - 1) / 365.0

    # deklinasyon (radyan)
    dek = (0.006918
           - 0.399912 * np.cos(gama) + 0.070257 * np.sin(gama)
           - 0.006758 * np.cos(2 * gama) + 0.000907 * np.sin(2 * gama)
           - 0.002697 * np.cos(3 * gama) + 0.001480 * np.sin(3 * gama))

    # zaman denklemi (dakika)
    zd = 229.18 * (0.000075
                   + 0.001868 * np.cos(gama) - 0.032077 * np.sin(gama)
                   - 0.014615 * np.cos(2 * gama) - 0.040849 * np.sin(2 * gama))

    # gercek gunes zamani ve saat acisi
    gunes_saat = saat + lon / 15.0 + zd / 60.0
    omega = np.deg2rad(15.0 * (gunes_saat - 12.0))

    lat_r = np.deg2rad(lat)
    return (np.sin(lat_r) * np.sin(dek)
            + np.cos(lat_r) * np.cos(dek) * np.cos(omega))


# --------------------------------------------------------------------------- #
# oznitelik uretimi
# --------------------------------------------------------------------------- #
def _konum_oznitelikleri(g: pd.DataFrame, eszaman: bool,
                         gecikmeli: tuple[str, ...],
                         eszaman_degisken: tuple[str, ...]) -> pd.DataFrame:
    """Tek bir konum icin oznitelikleri uretir. g zaman siralidir."""
    g = g.sort_values("time_utc").reset_index(drop=True)
    lat, lon = float(g["lat"].iloc[0]), float(g["lon"].iloc[0])

    o = pd.DataFrame(index=g.index)
    o["konum"] = g["konum"]
    o["time_utc"] = g["time_utc"]
    o["y"] = g["P"]                      # hedef
    o["H_sun"] = g["H_sun"]              # SADECE gunduz maskesi icin

    # --- astronomik gunes geometrisi (hedef saat, sizinti degil) ---
    # PVGIS zaman damgasi uydu gozlem dakikasini tasir (:09, :10). Saat basina
    # yuvarlanmis damgayla hesap yapmak ~1.5 derece sistematik sapma verir;
    # varsa orijinal damgayi kullaniyoruz.
    zaman_geo = g["time_gozlem"] if "time_gozlem" in g else g["time_utc"]
    elev_sin = gunes_yuksekligi_sin(lat, lon, zaman_geo)
    o["elev_sin"] = np.clip(elev_sin, 0.0, None)

    # --- gecikmeli dinamik oznitelikler ---
    eksik = [d for d in gecikmeli if d not in g]
    if eksik:
        raise KeyError(
            f"Zorunlu degiskenler veri setinde yok: {eksik}. "
            "Sessizce atlamak modelin en guclu ozniteliklerini kaybettirir - "
            "pipeline'in duzenle adimini yeniden kosun.")
    for d in gecikmeli:
        for k in GECIKMELER:
            o[f"{d}_lag{k}"] = g[d].shift(k)

    # --- gecikmeli yuvarlanan istatistikler (hepsi >=24 saat kaydirilmis) ---
    for d, islemler in YUVARLANAN.items():
        kaydirilmis = g[d].shift(24)
        for islem, pencere in islemler:
            ad = f"{d}_roll{pencere}_{islem}_lag24"
            o[ad] = getattr(kaydirilmis.rolling(pencere, min_periods=pencere), islem)()

    # --- berrak-gokyuzu performans orani ---
    # P / (1000 * sin h_s); gece paydasi sifira gittigi icin eksik kabul edilir
    payda = BERRAK_GOK_KATSAYI * np.where(elev_sin > 0.05, elev_sin, np.nan)
    bg = pd.Series(g["P"].to_numpy() / payda, index=g.index)
    o["bg_orani_lag24"] = bg.shift(24)
    o["bg_orani_roll24_lag24"] = bg.shift(24).rolling(24, min_periods=6).mean()

    # --- dongusel takvim ---
    saat = g["time_utc"].dt.hour.to_numpy()
    gun = g["time_utc"].dt.dayofyear.to_numpy()
    o["h_sin"] = np.sin(2 * np.pi * saat / 24.0)
    o["h_cos"] = np.cos(2 * np.pi * saat / 24.0)
    o["d_sin"] = np.sin(2 * np.pi * gun / 365.25)
    o["d_cos"] = np.cos(2 * np.pi * gun / 365.25)

    # --- persistence referansi (model degil, kiyas icin) ---
    o["persistence"] = g["P"].shift(24)

    # --- SIZINTI varyanti: hedef saatteki meteoroloji ---
    if eszaman:
        eksik_es = [d for d in eszaman_degisken if d not in g]
        if eksik_es:
            raise KeyError(
                f"Eszaman varyanti icin beyan edilen degiskenler yok: "
                f"{eksik_es}. Sessizce atlanirsa varyant BEYAN EDILENDEN daha "
                "az sizinti kanali tasir ve olculen sisme oldugundan kucuk "
                "cikar - tam olarak olcmek istedigimiz sey bozulur.")
        for d in eszaman_degisken:
            o[f"{d}_eszaman"] = g[d]
        o["H_sun_eszaman"] = g["H_sun"]

    return o


def oznitelik_uret(ham: pd.DataFrame, eszaman: bool = False,
                   gecikmeli: tuple[str, ...] = GECIKMELI_DEGISKEN,
                   eszaman_degisken: tuple[str, ...] = ESZAMAN_DEGISKEN
                   ) -> pd.DataFrame:
    """Tum konumlar icin oznitelik tablosunu uretir.

    eszaman=True verildiginde hedef saatteki meteorolojik degiskenler de
    eklenir - bu KASITLI bir sizintidir, yalnizca ablasyon deneyi icindir.

    `gecikmeli` ve `eszaman_degisken` BEYAN EDILEN oznitelik setidir.
    Varsayilanlari `config.GECIKMELI_DEGISKEN` / `config.ESZAMAN_DEGISKEN`,
    yani GUFBD makalesinin cekirdek seti; varsayilanlarla cagrildiginda
    uretilen tablo parametre eklenmeden onceki halle BIREBIR AYNIDIR
    (`arac/oznitelik_regresyon.py` bunu olcer).

    Neden bayrak degil de tuple: DKASC'de `WS10m` kanali yok (karar 1,
    dokumanlar/dkasc-kalite-kurallari.md). Bunu `ruzgar=False` gibi bir
    bayrakla kodlamak sapmayi uretim koduna gomer ve her yeni veri
    setinde bir bayrak daha birikir. Beyan edilen bir tuple ise
    ozniteliK setini kod yolunun yan etkisi olmaktan cikarip
    raporlanabilir bir DEGERE cevirir - makalede raporlanacak sey de
    zaten budur.
    """
    parcalar = [_konum_oznitelikleri(g, eszaman, gecikmeli, eszaman_degisken)
                for _, g in ham.groupby("konum", sort=True)]
    o = pd.concat(parcalar, ignore_index=True)

    # konum tek-sicak kodlama
    o = pd.concat([o, pd.get_dummies(o["konum"], prefix="loc", dtype=float)], axis=1)

    # 168 saatlik gecikme ve yuvarlanan pencereler icin gereken ilk gozlemler
    # tanimsizdir; SADECE bunlari dusuruyoruz.
    #
    # Berrak-gokyuzu orani gece tanim geregi eksiktir (payda sifira gider) ve
    # makalede oldugu gibi imputasyonla doldurulur. Onu zorunlu listeye
    # koymak butun gece satirlarini silerdi - egitim seti gece gozlemlerini
    # icermeli, gunduz filtresi yalnizca DEGERLENDIRMEDE uygulanir.
    # Hedef de zorunludur. PVGIS'te `P` hicbir satirda eksik olmadigi icin bu
    # gorunmuyordu; DKASC'de eksik saatler var ve hedefi eksik bir satir
    # tabloda kalirsa hata `hat.fit()` icinde, izgaranin ortasinda, o hucreyi
    # kaybederek patlar. Burada dusurulur - PVGIS tarafinda ISLEMSIZDIR ve
    # oyle oldugu `arac/oznitelik_regresyon.py` ile olculur.
    zorunlu = ["y"]
    zorunlu += [f"{d}_lag{k}" for d in gecikmeli for k in GECIKMELER
                if f"{d}_lag{k}" in o.columns]
    zorunlu += [c for c in o.columns if "roll168" in c]
    o = o.dropna(subset=zorunlu).reset_index(drop=True)

    return o.sort_values(["konum", "time_utc"]).reset_index(drop=True)


def oznitelik_kolonlari(o: pd.DataFrame) -> list[str]:
    """Modele girecek sutunlar: hedef, kimlik ve yardimci sutunlar dislanir."""
    haric = {"y", "konum", "time_utc", "H_sun", "persistence"}
    return [c for c in o.columns if c not in haric]