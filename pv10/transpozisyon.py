"""Yatay isinimdan egik duzleme transpozisyon - izotropik (Liu-Jordan).

Karar 4 (dokumanlar/dkasc-kalite-kurallari.md, bolum 2): model gelenege
gore degil OLCUME gore secildi. Ayni 254.741 satirda, olculen egik
piranometreye karsi izotropik Hay-Davies'ten iyi cikti (RMSE 45,9182 vs
46,9048 W/m2; R2 0,98212 vs 0,98134) ve iki model 20 derecelik duzlemde
yalnizca %0,824 ayrisiyor - sonuc model secimine dayanikli.

Bilesenler PVGIS'in `components=1` ciktisini birebir taklit eder:

    Gb_i = (GHI - DHI) * Rb
    Gd_i = DHI * (1 + cos B) / 2
    Gr_i = GHI * albedo * (1 - cos B) / 2
    G_i  = Gb_i + Gd_i + Gr_i

Boylece "G_i bilesenlerden geri kurulur" adimi PVGIS kolunda ne ise DKASC
kolunda da AYNI islemdir (bkz. pvgis_pipeline.py:duzenle).

cos(theta) KOPYALANMIS bir formulden gelmez. Ekvatora bakan (azimut 0)
egik duzlem icin gelis acisinin kosinusu, egimin enleme eklenmesiyle
elde edilen "etkin enlem"deki gunes yuksekligi sinusune esittir:

    cos(theta) = sin(dek) sin(phi + B) + cos(dek) cos(w) cos(phi + B)
               = gunes_yuksekligi_sin(phi + B, lon, t)

Guney yarikurede phi negatiftir ve kuzeye (ekvatora) egilmek phi + B ile
sifira yaklasir. Bu ozdeslik sayesinde Faz 2/3/4'un dondurulmus geometri
koduna hic dokunulmaz; azimut icin tam gelis acisi formulu gerekseydi
dokunmak zorunda kalirdik (bolum 4, madde 3).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import DKASC_ALBEDO, DKASC_RB_TABAN
from .features import gunes_yuksekligi_sin


def egik_bilesenler(ghi: np.ndarray, dhi: np.ndarray, sin_h: np.ndarray,
                    cos_theta: np.ndarray, egim_derece: float,
                    albedo: float = DKASC_ALBEDO,
                    rb_taban: float = DKASC_RB_TABAN
                    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Izotropik transpozisyon; (Gb_i, Gd_i, Gr_i) dondurur.

    ghi, dhi   : yatay global ve yayili isinim (W/m2)
    sin_h      : gunes yuksekliginin sinusu, AYNI anlarda
    cos_theta  : egik duzleme gelis acisinin kosinusu, AYNI anlarda
    egim_derece: duzlemin egimi (B)

    Rb paydasi `max(sin_h, rb_taban)` ile tabanlanir: alcak gunes acilarinda
    Rb tanim geregi patlar. Bu taban DOGRULANMAMIS bir secimdir - kapi
    yalnizca sin h > 0,10 bolgesinde kosar (bolum 4, madde 10).
    """
    for ad, a in (("ghi", ghi), ("dhi", dhi), ("sin_h", sin_h),
                  ("cos_theta", cos_theta)):
        if a.shape != ghi.shape:
            raise ValueError(
                f"transpozisyon girdileri ayni uzunlukta olmali; {ad} "
                f"{a.shape}, ghi {ghi.shape}. Sessizce yayinlamak (broadcast) "
                "yanlis satirlari eslestirir.")

    cos_b = np.cos(np.deg2rad(egim_derece))
    rb = np.clip(cos_theta, 0.0, None) / np.maximum(sin_h, rb_taban)

    gb = np.clip(ghi - dhi, 0.0, None) * rb
    gd = dhi * (1.0 + cos_b) / 2.0
    gr = ghi * albedo * (1.0 - cos_b) / 2.0
    return gb, gd, gr


def transpoze(ghi: np.ndarray, dhi: np.ndarray, zaman_utc: pd.Series,
              lat: float, lon: float, egim_derece: float,
              albedo: float = DKASC_ALBEDO,
              rb_taban: float = DKASC_RB_TABAN) -> dict[str, np.ndarray]:
    """Geometriyi kendi hesaplayan sarmalayici; Gb_i/Gd_i/Gr_i/G_i dondurur.

    zaman_utc gercek gozlem ani olmalidir (etiket degil) - karar 5.
    """
    sin_h = gunes_yuksekligi_sin(lat, lon, zaman_utc)
    cos_theta = gunes_yuksekligi_sin(lat + egim_derece, lon, zaman_utc)
    gb, gd, gr = egik_bilesenler(ghi, dhi, sin_h, cos_theta, egim_derece,
                                 albedo, rb_taban)
    return {"Gb_i": gb, "Gd_i": gd, "Gr_i": gr, "G_i": gb + gd + gr,
            "sin_h": sin_h, "cos_theta": cos_theta}


def olculene_karsi(ghi: np.ndarray, dhi: np.ndarray, gti_olculen: np.ndarray,
                   zaman_utc: pd.Series, lat: float, lon: float,
                   egimler: np.ndarray, albedo: float = DKASC_ALBEDO,
                   rb_taban: float = DKASC_RB_TABAN) -> pd.DataFrame:
    """Her egim icin olculen GTI'ye karsi MBE / RMSE / R2 tablosu.

    URETIM fonksiyonunu (`egik_bilesenler`) cagirir. Kapinin kendi kopyasini
    dogrulamamasi kuralinin geregi budur - invaryant 5 dersi.
    """
    if len(gti_olculen) == 0:
        raise ValueError("kapi bos maskeyle cagrildi: karsilastirilacak satir "
                         "yok. Sessizce 'gecti' demek kapiyi islevsiz kilar.")

    sin_h = gunes_yuksekligi_sin(lat, lon, zaman_utc)
    olcum_ort = float(np.mean(gti_olculen))
    toplam_kare = float(np.sum((gti_olculen - olcum_ort) ** 2))

    satir = []
    for b in egimler:
        cos_theta = gunes_yuksekligi_sin(lat + float(b), lon, zaman_utc)
        gb, gd, gr = egik_bilesenler(ghi, dhi, sin_h, cos_theta, float(b),
                                     albedo, rb_taban)
        hata = (gb + gd + gr) - gti_olculen
        rmse = float(np.sqrt(np.mean(hata ** 2)))
        mbe = float(np.mean(hata))
        satir.append({
            "egim": float(b), "n": len(hata),
            "MBE": mbe, "MBE_yuzde": 100.0 * mbe / olcum_ort,
            "RMSE": rmse, "RMSE_yuzde": 100.0 * rmse / olcum_ort,
            "R2": 1.0 - float(np.sum(hata ** 2)) / toplam_kare,
        })
    return pd.DataFrame(satir)
