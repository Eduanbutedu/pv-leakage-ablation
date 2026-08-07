#!/usr/bin/env python3
"""
DKASC veri hatti: dogrula -> duzenle
====================================
Alti ham yillik dosyadan tek bir dondurulmus, hash'lenmis tabloya.
`pvgis_pipeline.py`'nin yapisini izler ama INDIR adimi YOKTUR - DKASC
dosyalari elle indirilir.

Butun esikler ve kararlar `dokumanlar/dkasc-kalite-kurallari.md`'de
ON-KAYIT olarak duruyor ve bu dosyanin ILK SATIRINDAN once commit edildi
(`git log dokumanlar/dkasc-kalite-kurallari.md`). Buradaki kod o belgenin
uygulanmasidir; sayilar `pv10/config.py`'de.

Cikti semasi `pv10/` katmaninin bekledigi semayla ayni:

    konum, time_utc, time_local, time_gozlem, lat, lon, utc_ofset,
    P, G_i, Gb_i, Gd_i, Gr_i, H_sun, T2m   (+ tasinan: GHI, DHI, RH, ariza)

`WS10m` YOKTUR - karar 1. Oznitelik seti `config.DKASC_GECIKMELI` ile
beyan edilir.

Kullanim:
    python dkasc_pipeline.py dogrula ham/dkasc
    python dkasc_pipeline.py duzenle ham/dkasc
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from pv10.config import (DKASC_ALBEDO, DKASC_ARIZA_GHI, DKASC_BASLANGIC_YIL,
                         DKASC_BITIS_YIL, DKASC_DHI, DKASC_DHI_ORAN_BAYRAK,
                         DKASC_DTI, DKASC_EGIM, DKASC_EGIM_TARAMA, DKASC_G0_CARPAN,
                         DKASC_GHI, DKASC_GIRDI_YUVA, DKASC_GTI,
                         DKASC_GUC_OLU_BOLGE,
                         DKASC_GUNES_SABITI, DKASC_HEDEF_DIZI,
                         DKASC_KAPI_EGIM_ARALIK, DKASC_KAPI_GHI,
                         DKASC_KAPI_MBE_YUZDE, DKASC_KAPI_RMSE_YUZDE,
                         DKASC_KAPI_SIN_H, DKASC_KESIF_SAYIM,
                         DKASC_KOORDINAT_KAYNAK, DKASC_KONUM,
                         DKASC_LAT, DKASC_LON, DKASC_RB_TABAN, DKASC_RH,
                         DKASC_RH_BAYRAK, DKASC_RH_UST, DKASC_SAAT_YUVA,
                         DKASC_SUTUN_SAYISI, DKASC_T, DKASC_T_ALT, DKASC_T_RAY,
                         DKASC_T_UST, DKASC_UTC_OFSET, DKASC_VERI,
                         DKASC_VERI_SHA16,
                         DKASC_YUVA_DK, DKASC_ETIKET_ORTA_DK)
from pv10.features import gunes_yuksekligi_sin
from pv10.transpozisyon import olculene_karsi, transpoze

OKUNAN = ["timestamp", DKASC_GHI, DKASC_DHI, DKASC_GTI, DKASC_DTI,
          DKASC_T, DKASC_RH, DKASC_HEDEF_DIZI]
ISINIM = [DKASC_GHI, DKASC_DHI, DKASC_GTI, DKASC_DTI]
ACST = pd.Timedelta(hours=DKASC_UTC_OFSET)
YUVA = pd.Timedelta(minutes=DKASC_YUVA_DK)
ORTA = pd.Timedelta(minutes=DKASC_ETIKET_ORTA_DK)


def _yol(klasor: Path, yil: int) -> Path:
    return klasor / f"Alice_Springs_{yil}.csv"


def _basliklar(yol: Path) -> list[str]:
    return list(pd.read_csv(yol, nrows=0).columns)


# --------------------------------------------------------------------------- #
# 1) dogrula
# --------------------------------------------------------------------------- #
def dogrula_klasor(klasor: Path) -> bool:
    """Ham dosyalarin semasini ve zaman eksenini kontrol eder.

    VERIYI degil KURGUYU dogrular: sutun kumesi alti yilda ayni mi, zaman
    damgasi tekrarli mi, dosya beklenen yili kapsiyor mu.
    """
    yillar = range(DKASC_BASLANGIC_YIL, DKASC_BITIS_YIL + 1)
    eksik = [y for y in yillar if not _yol(klasor, y).exists()]
    if eksik:
        print(f"  [HATA] su yillarin dosyasi yok: {eksik}")
        return False

    print(f"{klasor} kontrol ediliyor:\n")
    referans, tumu = None, True
    for y in yillar:
        yol = _yol(klasor, y)
        basliklar = _basliklar(yol)
        sorunlar = []

        if len(basliklar) != DKASC_SUTUN_SAYISI:
            sorunlar.append(f"sutun sayisi {len(basliklar)}, "
                            f"beklenen {DKASC_SUTUN_SAYISI}")
        if referans is None:
            referans = basliklar
        elif basliklar != referans:
            fark = set(basliklar) ^ set(referans)
            sorunlar.append(f"sutun semasi {DKASC_BASLANGIC_YIL} ile ayni degil "
                            f"(simetrik fark {len(fark)}: {sorted(fark)[:5]})")
        for c in OKUNAN[1:]:
            if c not in basliklar:
                sorunlar.append(f"zorunlu sutun yok: {c}")

        d = pd.read_csv(yol, usecols=["timestamp"], parse_dates=["timestamp"])
        t = d["timestamp"]
        if t.duplicated().any():
            sorunlar.append(f"{int(t.duplicated().sum())} tekrarli zaman damgasi")
        if t.min() != pd.Timestamp(f"{y}-01-01"):
            sorunlar.append(f"ilk damga {t.min()}, beklenen {y}-01-01 00:00")
        ic = int((t.dt.year == y).sum())

        print(f"  [{'SORUNLU' if sorunlar else 'TAMAM'}] {y}: {len(d):,} satir, "
              f"{t.min()} .. {t.max()}, takvim yili ici {ic:,}, "
              f"{len(basliklar)} sutun")
        for s in sorunlar:
            print(f"          -> {s}")
        tumu &= not sorunlar
    return tumu


# --------------------------------------------------------------------------- #
# 2) duzenle - adim adim, her adimda satir sayisi basilir
# --------------------------------------------------------------------------- #
def oku_birlestir(klasor: Path) -> pd.DataFrame:
    """Adim 1-2: alti dosyayi oku, takvim disi kirp, tam 5 dk izgarasina otur."""
    parcalar = []
    for y in range(DKASC_BASLANGIC_YIL, DKASC_BITIS_YIL + 1):
        x = pd.read_csv(_yol(klasor, y), usecols=OKUNAN,
                        parse_dates=["timestamp"])
        ic = x[x["timestamp"].dt.year == y]
        print(f"  {y}: {len(x):,} satir okundu, takvim disi {len(x)-len(ic):,} "
              f"kirpildi -> {len(ic):,}")
        parcalar.append(ic)

    d = pd.concat(parcalar, ignore_index=True).sort_values("timestamp")
    if d["timestamp"].duplicated().any():
        raise ValueError(
            f"{int(d['timestamp'].duplicated().sum())} tekrarli zaman damgasi. "
            "Dosyalar ust uste biniyor; sessizce birini tutmak hangi olcumun "
            "kaldigini belirsiz birakir.")

    izgara = pd.date_range(f"{DKASC_BASLANGIC_YIL}-01-01",
                           f"{DKASC_BITIS_YIL}-12-31 23:55",
                           freq=f"{DKASC_YUVA_DK}min")
    damga = len(d)
    d = d.set_index("timestamp").reindex(izgara)
    d.index.name = "yerel"
    # Iki ayri sayi: dosyada VAR OLAN damga, ve o damgalardan icinde en az bir
    # olcum bulunani. Ikisini tek sayiya indirmek "eksik" kelimesini bulandirir.
    veriliy = int(d.notna().any(axis=1).sum())
    print(f"  birlesik damga {damga:,} -> tam izgara {len(izgara):,} "
          f"(hic olmayan damga {len(izgara)-damga:,}, "
          f"%{100*(len(izgara)-damga)/len(izgara):.4f})")
    print(f"  var olan damgalardan tamamen bos olan: {damga-veriliy:,} "
          f"(okunan 8 sutunun hicbirinde deger yok)")
    return d


def kurallar_5dk(d: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Adim 3-5: kural 1, 2, 3, 6, 9, 5. Hepsi 5 dakika cozunurlugunde."""
    say = {}
    # gozlem ani: etiket + 2,5 dk (karar 5), UTC'ye cevrilir
    an_utc = pd.Series(d.index + ORTA - ACST, index=d.index)
    sin_h = gunes_yuksekligi_sin(DKASC_LAT, DKASC_LON, an_utc)
    d["_sin_h"] = sin_h

    # --- Kural 1: piranometre gece ofseti ---
    gece = sin_h < 0
    n = 0
    for c in ISINIM:
        vurus = gece & d[c].notna()
        n += int(vurus.sum())
        d[c] = np.where(vurus, 0.0, d[c])
    say["k1_gece_izgara_satiri"] = int(gece.sum())
    say["k1_sifirlanan_deger"] = n

    # --- Kural 2: bagil nem ust siniri ---
    say["k2_bayrak"] = int((d[DKASC_RH] > DKASC_RH_BAYRAK).sum())
    say["k2_kirpilan"] = int((d[DKASC_RH] > DKASC_RH_UST).sum())
    d["rh_bayrak"] = (d[DKASC_RH] > DKASC_RH_BAYRAK).fillna(False)
    d[DKASC_RH] = d[DKASC_RH].clip(0.0, DKASC_RH_UST)

    # --- Kural 3: yayili bilesen globali asamaz ---
    oran = d[DKASC_DHI] / d[DKASC_GHI].replace(0.0, np.nan)
    say["k3_bayrak"] = int((oran > DKASC_DHI_ORAN_BAYRAK).sum())
    say["k3_duzeltilen"] = int((d[DKASC_DHI] > d[DKASC_GHI]).sum())
    d["dhi_bayrak"] = (oran > DKASC_DHI_ORAN_BAYRAK).fillna(False)
    d[DKASC_DHI] = np.minimum(d[DKASC_DHI], d[DKASC_GHI])

    # --- Kural 6: isinim ust siniri (G0 ile normalize) ---
    gun_no = an_utc.dt.dayofyear.to_numpy()
    g0 = (DKASC_GUNES_SABITI * (1 + 0.033 * np.cos(2 * np.pi * gun_no / 365.0))
          * np.clip(sin_h, 0.0, None))
    asan = d[DKASC_GHI] > DKASC_G0_CARPAN * g0
    say["k6_eksige_cevrilen"] = int(asan.sum())
    d[DKASC_GHI] = np.where(asan, np.nan, d[DKASC_GHI])

    # --- Kural 9: sicaklik gecerli araligi (+ rayda RH de duser) ---
    ray = d[DKASC_T] <= DKASC_T_RAY
    disari = (d[DKASC_T] < DKASC_T_ALT) | (d[DKASC_T] > DKASC_T_UST)
    say["k9_t_eksige_cevrilen"] = int(disari.sum())
    say["k9_rh_eksige_cevrilen"] = int(ray.sum())
    d[DKASC_T] = np.where(disari, np.nan, d[DKASC_T])
    d[DKASC_RH] = np.where(ray, np.nan, d[DKASC_RH])

    # --- Kural 5: negatif guc (kW cinsinden, donusum sonra) ---
    p = d[DKASC_HEDEF_DIZI]
    buyuk_negatif = p < -DKASC_GUC_OLU_BOLGE
    olu = p.abs() <= DKASC_GUC_OLU_BOLGE
    say["k5_negatif"] = int((p < 0).sum())
    say["k5_eksige_cevrilen"] = int(buyuk_negatif.sum())
    say["k5_sifirlanan"] = int(olu.sum())
    d[DKASC_HEDEF_DIZI] = np.where(buyuk_negatif, np.nan,
                                   np.where(olu, 0.0, p))
    return d, say


def transpozisyon_kapisi(d: pd.DataFrame, zorla_egim: float | None = None
                         ) -> tuple[bool, dict, pd.DataFrame]:
    """Karar 4'un kapisi: uretim transpozisyonu OLCULEN GTI'ye karsi.

    zorla_egim verilirse tarama yapilmaz, o tek egim degerlendirilir -
    NEGATIF KONTROL bunun icindir (0 derece ile cagrildiginda kapi
    KIRMIZI yanmalidir).
    """
    m = (d["_sin_h"] > DKASC_KAPI_SIN_H) & (d[DKASC_GHI] > DKASC_KAPI_GHI) \
        & d[DKASC_GHI].notna() & d[DKASC_DHI].notna() \
        & d[DKASC_GTI].notna() & (d[DKASC_GTI] > 0) \
        & (d[DKASC_DHI] <= d[DKASC_GHI])
    alt = d[m]
    an_utc = pd.Series(alt.index + ORTA - ACST, index=alt.index)
    egimler = (np.array([zorla_egim]) if zorla_egim is not None
               else np.arange(*DKASC_EGIM_TARAMA))

    t = olculene_karsi(alt[DKASC_GHI].to_numpy(), alt[DKASC_DHI].to_numpy(),
                       alt[DKASC_GTI].to_numpy(), an_utc,
                       DKASC_LAT, DKASC_LON, egimler)
    en_iyi = t.loc[t["RMSE"].idxmin()]
    lo, hi = DKASC_KAPI_EGIM_ARALIK
    olcut = {
        "n": int(en_iyi["n"]),
        "egim": float(en_iyi["egim"]),
        "RMSE_yuzde": float(en_iyi["RMSE_yuzde"]),
        "MBE_yuzde": float(en_iyi["MBE_yuzde"]),
        "R2": float(en_iyi["R2"]),
        "rmse_ok": bool(en_iyi["RMSE_yuzde"] <= DKASC_KAPI_RMSE_YUZDE),
        "mbe_ok": bool(abs(en_iyi["MBE_yuzde"]) <= DKASC_KAPI_MBE_YUZDE),
        "egim_ok": bool(lo <= en_iyi["egim"] <= hi),
    }
    olcut["gecti"] = olcut["rmse_ok"] and olcut["mbe_ok"] and olcut["egim_ok"]
    return olcut["gecti"], olcut, t


def saatlige_topla(d: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Adim 6-8: 5 dk'da transpozisyon, sonra kural 10, sonra tam izgara."""
    say = {}
    # --- Adim 6: transpozisyon 5 DAKIKA cozunurlugunde (karar 4) ---
    an_utc = pd.Series(d.index + ORTA - ACST, index=d.index)
    bilesen = transpoze(d[DKASC_GHI].to_numpy(), d[DKASC_DHI].to_numpy(),
                        an_utc, DKASC_LAT, DKASC_LON, DKASC_EGIM)
    for k in ("Gb_i", "Gd_i", "Gr_i", "G_i"):
        d[k] = bilesen[k]

    # --- Adim 7: Kural 10 - yerel saat kovalari ---
    # Esik GIRDIDE gevser (>=9/12), HEDEF ve DEGERLENDIRMEDE siki kalir
    # (12/12). Gece satirlarini egitimde tutup gunduz filtresini yalnizca
    # degerlendirmede uygulamamizla ayni desen: filtre girdide degil ciktida.
    #
    # Tamlik G_i'yi URETEN kanallar ve hedefe gore olculur. RH tasinir ama
    # oznitelik degildir (PVGIS semasinda da yok), bu yuzden saati BAGLAMAZ;
    # baglasaydi kural 9'un RH kolu hicbir ozniteligi beslemeyen bir kanal
    # icin saat dusururdu.
    #
    # Yuva sayimi ORTAK maskeden gelir: bir yuva ancak DORT kanalin da dolu
    # oldugu yuvadir. Kanal basina ayri sayip minimum almak yanlistir, cunku
    # farkli kanallar farkli yuvalarda eksik olabilir. Daha onemlisi: saatlik
    # ortalamalar da bu ORTAK yuva kumesi uzerinden alinmalidir. Aksi halde
    # kural 6'nin yalnizca GHI'yi dusurdugu bir yuvada Gd_i durur, Gb_i/Gr_i/
    # G_i duser ve `.mean()` her sutunu FARKLI kumeden alir - G_i artik
    # bilesenlerin toplamina esit olmaz. Sema kapisi bunu yakaladi.
    tam5 = (d[DKASC_GHI].notna() & d[DKASC_DHI].notna()
            & d[DKASC_T].notna() & d[DKASC_HEDEF_DIZI].notna())
    # kanal bazinda tamlik, MASKELEMEDEN ONCE olculur - hangi kanalin
    # bagladigini gostermesi icin; maskelemeden sonra hepsi esitlenir
    for ad, c in (("GHI", DKASC_GHI), ("DHI", DKASC_DHI),
                  ("T2m", DKASC_T), ("P", DKASC_HEDEF_DIZI)):
        say[f"saat_tam_{ad}"] = int(
            (d[c].groupby(pd.Grouper(freq="h")).count() == DKASC_SAAT_YUVA).sum())

    ortalanacak = [DKASC_GHI, DKASC_DHI, DKASC_T, DKASC_RH, DKASC_HEDEF_DIZI,
                   "Gb_i", "Gd_i", "Gr_i", "G_i"]
    d.loc[~tam5, ortalanacak] = np.nan
    d["_tam"] = tam5

    kova = d.groupby(pd.Grouper(freq="h"))
    dolu = kova["_tam"].sum()
    gecerli = dolu >= DKASC_GIRDI_YUVA        # GIRDI icin
    kati = dolu == DKASC_SAAT_YUVA            # HEDEF ve DEGERLENDIRME icin

    say["saat_toplam"] = int(len(dolu))
    say["saat_kati_12_12"] = int(kati.sum())
    say["saat_girdi_gecerli"] = int(gecerli.sum())
    say["saat_kismi_girdi"] = int((gecerli & ~kati).sum())
    say["saat_bos"] = int((dolu == 0).sum())
    say["saat_esik_alti"] = int(((dolu > 0) & ~gecerli).sum())

    ort = kova[ortalanacak].mean()
    bayrak = kova[["rh_bayrak", "dhi_bayrak"]].max().astype(bool)
    s = pd.concat([ort, bayrak], axis=1)
    s = s.where(pd.Series(gecerli, index=s.index), other=np.nan)
    s.loc[~gecerli, ["rh_bayrak", "dhi_bayrak"]] = False
    # `kismi` bayragi: girdi esigini gecti ama 12/12 DEGIL. Bu satirlarin
    # hedefi ASLA kullanilmaz - asagida P'leri de eksige cevrilir.
    s["kismi"] = (gecerli & ~kati).reindex(s.index, fill_value=False)
    s["yuva"] = dolu.reindex(s.index)

    # Saatin on iki yuvasindaki EN YUKSEK gunes konumu. Saf geometridir,
    # gecerlilik maskesinden SONRA eklenir ki her satirda tanimli kalsin.
    # Sema kapisi buna dayanir: saat merkezi ufkun altinda olsa bile saatin
    # bir kismi gunduz olabilir (gunde tam olarak 1 saat boyledir).
    s["sin_h_maks"] = kova["_sin_h"].max()

    # --- Adim 8: tam saatlik izgaraya reindex ---
    # features.py konumsal shift(k) kullanir. Bosluklu bir seride shift(24)
    # 24 SAAT degil 24 SATIR oncesini alir ve G_i_lag24 yanlis damgadan gelir;
    # hicbir yerde hata firlamaz. Tam izgara bunu imkansiz kilar.
    saat_izgara = pd.date_range(f"{DKASC_BASLANGIC_YIL}-01-01",
                                f"{DKASC_BITIS_YIL}-12-31 23:00", freq="h")
    if len(s) != len(saat_izgara) or not s.index.equals(saat_izgara):
        s = s.reindex(saat_izgara)
    s.index.name = "time_local"
    say["saat_izgara"] = int(len(saat_izgara))
    return s, say


def semaya_donustur(s: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Adim 9-10: kural 7 (saatlik) + sema + birim donusumu."""
    say = {}
    s = s.reset_index()
    s["time_utc"] = s["time_local"] - ACST
    s["time_gozlem"] = s["time_utc"] + pd.Timedelta(hours=1) / 2

    sin_h = gunes_yuksekligi_sin(DKASC_LAT, DKASC_LON, s["time_gozlem"])
    s["H_sun"] = np.degrees(np.arcsin(np.clip(sin_h, -1.0, 1.0)))

    # --- Kural 7: gunduz sifir uretim; DEGERLENDIRMEDEN cikarilir, egitimden ASLA ---
    s["ariza"] = ((s[DKASC_GHI] > DKASC_ARIZA_GHI)
                  & (s[DKASC_HEDEF_DIZI] == 0.0)).fillna(False)
    say["k7_ariza_saat"] = int(s["ariza"].sum())

    # --- birim: DKASC kW -> sema W (PVGIS W kullaniyor). YON: x1000 ---
    s["P"] = s[DKASC_HEDEF_DIZI] * 1000.0

    s = s.rename(columns={DKASC_T: "T2m", DKASC_GHI: "GHI",
                          DKASC_DHI: "DHI", DKASC_RH: "RH"})
    s["konum"] = DKASC_KONUM
    s["lat"], s["lon"] = DKASC_LAT, DKASC_LON
    s["utc_ofset"] = DKASC_UTC_OFSET

    sira = ["konum", "time_utc", "time_local", "time_gozlem",
            "lat", "lon", "utc_ofset",
            "P", "G_i", "Gb_i", "Gd_i", "Gr_i", "H_sun", "T2m",
            "GHI", "DHI", "RH", "ariza", "kismi", "yuva",
            "rh_bayrak", "dhi_bayrak", "sin_h_maks"]
    s = s[sira].sort_values("time_utc").reset_index(drop=True)
    return s, say


def sema_kapisi(s: pd.DataFrame) -> None:
    """Cikti semasinin pv10/ katmaniyla uyumunu dogrular; uymazsa DURUR."""
    zorunlu = ["konum", "time_utc", "time_local", "time_gozlem", "lat", "lon",
               "utc_ofset", "P", "G_i", "H_sun", "T2m"]
    eksik = [c for c in zorunlu if c not in s.columns]
    if eksik:
        raise ValueError(f"cikti semasinda zorunlu sutunlar eksik: {eksik}")
    if "WS10m" in s.columns:
        raise ValueError("WS10m cikti semasinda - karar 1 geregi OLMAMALI. "
                         "Bos bir sutun uretilmis olabilir; sessizce birakmak "
                         "oznitelik setinin ne oldugunu belirsiz birakir.")

    bilesen = s[["Gb_i", "Gd_i", "Gr_i"]].sum(axis=1)
    fark = (s["G_i"] - bilesen).abs().max()
    if not (np.isnan(fark) or fark < 1e-9):
        raise ValueError(f"G_i bilesenlerin toplamina esit degil (maks fark "
                         f"{fark:.3e}). PVGIS kolunda bu ozdeslik saglaniyor.")

    if len(s[s["H_sun"] > 0]) == 0:
        raise ValueError("H_sun > 0 olan hic satir yok - gunduz maskesi bos.")

    # Kural 1 invaryanti. Dogru ifade "H_sun <= 0 iken G_i == 0" DEGILDIR:
    # H_sun saatin MERKEZINDE olculur, G_i ise on iki yuvanin ortalamasidir,
    # dolayisiyla merkez ufkun altindayken saatin bir kismi gunduz olabilir.
    # Alti yilda bu gunde TAM OLARAK 1 saat basina gelir (2.192 saat) ve
    # fizik geregi boyledir. Kuralin gercekten soyledigi sudur: on iki
    # yuvanin HEPSI ufkun altindaysa isinim sifir olmalidir.
    tam_gece = s[(s["sin_h_maks"] <= 0) & (s["G_i"] > 1e-9)]
    if len(tam_gece) > 0:
        raise ValueError(
            f"{len(tam_gece)} satirda saatin on iki yuvasinin hepsi ufkun "
            f"altinda oldugu halde G_i > 0 (maks {tam_gece['G_i'].max():.4f} "
            f"W/m2). Kural 1 uygulanmamis.")

    # Ters yon: merkez gece ama saatin bir kismi gunduz olan satirlar
    # DEGERLENDIRME maskesinin (H_sun > 0) disinda kalir. Bu PVGIS kolundaki
    # davranisin aynisidir (orada da H_sun ani bir degerdir), ama buyuklugu
    # burada gunde 1 saattir; sessiz kalmamasi icin sayilir.
    kenar = int(((s["H_sun"] <= 0) & (s["sin_h_maks"] > 0)
                 & s["G_i"].notna()).sum())
    print(f"  gecis saati (merkez gece, yuvalarin bir kismi gunduz): {kenar:,} "
          f"- gunduz maskesi bunlari DISLAR")

    # Kural 10 invaryanti: `kismi` bayrakli satirlarin verisi DOLU olmali
    # (gecikme kaynagi olarak yasarlar) ama 12/12 OLMAMALI. Bayragin bos
    # cikmasi esigin uygulanmadigi anlamina gelir; bayrakli bir satirin
    # 12/12 cikmasi bayragin yanlis hesaplandigi anlamina gelir.
    kismi = s[s["kismi"]]
    if len(kismi) == 0:
        raise ValueError(
            "hicbir satir `kismi` bayragi almadi. Girdi esigi "
            "uygulanmamis olabilir; olculen deger 1.145 saatti.")
    if kismi["G_i"].isna().any() or kismi["P"].isna().any():
        raise ValueError("`kismi` satirlarda G_i veya P eksik - bu satirlar "
                         "gecikme kaynagi olarak KULLANILACAK, dolu olmalilar.")
    if (kismi["yuva"] == 12).any():
        raise ValueError("12/12 olan bir satir `kismi` bayragi almis.")
    if (kismi["yuva"] < DKASC_GIRDI_YUVA).any():
        raise ValueError(f"`kismi` satirlarda yuva sayisi "
                         f"{DKASC_GIRDI_YUVA} esiginin altinda.")
    print(f"  kural 10: kati (12/12) {int((s['yuva'] == 12).sum()):,}  "
          f"kismi (>={DKASC_GIRDI_YUVA}/12) {len(kismi):,}  "
          f"-> kismi satirlar gecikme KAYNAGI, hedef ve degerlendirme DISI")


def duzenle(klasor: Path, cikti: Path) -> pd.DataFrame:
    print("\n[1-2] okuma ve 5 dk izgarasi")
    d = oku_birlestir(klasor)

    print("\n[3-5] kalite kurallari (5 dk cozunurluk)")
    d, say5 = kurallar_5dk(d)
    for k, v in say5.items():
        ref = DKASC_KESIF_SAYIM.get(k)
        if ref is None:
            print(f"  {k:26s} {v:>9,}")
        else:
            beklenen, not_ = ref
            im = "=" if v == beklenen else ("v" if v < beklenen else "^")
            print(f"  {k:26s} {v:>9,}   kesif {beklenen:>9,} {im}  {not_}")

    print("\n[kapi] transpozisyon, olculen GTI'ye karsi")
    gecti, olcut, tablo = transpozisyon_kapisi(d)
    print(f"  n={olcut['n']:,}  en iyi egim={olcut['egim']:.0f} deg  "
          f"RMSE=%{olcut['RMSE_yuzde']:.3f}  MBE=%{olcut['MBE_yuzde']:+.3f}  "
          f"R2={olcut['R2']:.5f}")
    print(f"  esikler: RMSE<=%{DKASC_KAPI_RMSE_YUZDE} [{olcut['rmse_ok']}]  "
          f"|MBE|<=%{DKASC_KAPI_MBE_YUZDE} [{olcut['mbe_ok']}]  "
          f"egim {DKASC_KAPI_EGIM_ARALIK} [{olcut['egim_ok']}]")
    if not gecti:
        raise SystemExit("[DUR] transpozisyon kapisi GECMEDI. Karar 4'un "
                         "dayandigi dogrulama uretimde tekrarlanmiyor.")

    # NEGATIF KONTROL - zorunlu. Kapi yanlisi yakalayamiyorsa islevsizdir.
    _, sifir, _ = transpozisyon_kapisi(d, zorla_egim=0.0)
    print(f"  negatif kontrol (egim 0 deg): RMSE=%{sifir['RMSE_yuzde']:.3f}  "
          f"MBE=%{sifir['MBE_yuzde']:+.3f}  gecti={sifir['gecti']}")
    if sifir["gecti"]:
        raise SystemExit("[DUR] NEGATIF KONTROL BASARISIZ: kapi 0 derecelik "
                         "duzlemi de kabul etti. Yanlisi yakalayamayan kapi "
                         "islevsizdir; esikler yeniden dusunulmeli.")

    print("\n[6-8] transpozisyon (5 dk) -> saatlige topla -> tam izgara")
    s, sayS = saatlige_topla(d)
    for k, v in sayS.items():
        print(f"  {k:26s} {v:>9,}")

    print("\n[9-10] kural 7 + sema")
    s, say7 = semaya_donustur(s)
    for k, v in say7.items():
        print(f"  {k:26s} {v:>9,}")

    print("\n[11] sema kapisi")
    sema_kapisi(s)
    dolu = int(s["P"].notna().sum())
    kati = int((s["yuva"] == 12).sum())
    print(f"  TAMAM. {len(s):,} saatlik satir, girdi-gecerli {dolu:,} "
          f"(%{100*dolu/len(s):.4f}), hedef-gecerli {kati:,} "
          f"(%{100*kati/len(s):.4f})")

    # yil sinirinda UTC kaymasi: time_utc yerel saatten 9,5 saat geridedir,
    # dolayisiyla yerel 1 Ocak'in ilk 10 saati UTC yilinda bir onceki yila
    # dusuyor. Bolme kodu time_utc kullandigi icin kayit altina aliniyor.
    kayan = int((s["time_local"].dt.year != s["time_utc"].dt.year).sum())
    print(f"  yil sinirinda UTC kaymasi: {kayan} satirin time_utc yili "
          f"time_local yilindan farkli (yil basina ~10 saat)")

    print("\n[12] dondurma")
    cikti.parent.mkdir(parents=True, exist_ok=True)
    s.to_parquet(cikti, index=False)
    h = hashlib.sha256(cikti.read_bytes()).hexdigest()[:16]
    kunye = "\n".join([
        f"dosya: {cikti.name}",
        f"sha256_16: {h}",
        f"satir: {len(s)}   girdi_gecerli: {dolu}   hedef_gecerli: {kati}",
        f"kural_10: girdi esigi >={DKASC_GIRDI_YUVA}/12 yuva, hedef ve "
        f"degerlendirme 12/12. `kismi` bayrakli satirlar gecikme KAYNAGIDIR; "
        f"egitim hedefi ve test gozlemi OLAMAZ - dislama bolme asamasinda "
        f"bayrakla yapilir (kural 7'nin `ariza` deseniyle ayni).",
        f"konum: {DKASC_KONUM}",
        f"aralik: {DKASC_BASLANGIC_YIL}-{DKASC_BITIS_YIL} (yerel ACST saat izgarasi)",
        f"kapasite_W: 5250.0",
        f"koordinat: {DKASC_LAT}, {DKASC_LON} - DIS KAYNAKLA DOGRULANDI",
        f"koordinat_kaynak: {DKASC_KOORDINAT_KAYNAK}",
        f"etiket_varsayimi: 5 dk etiketi aralik BASI; gozlem ani = etiket "
        f"+ {DKASC_ETIKET_ORTA_DK} dk (karar 5). Aralik SONU olcumle elendi; "
        f"BASI ile ANLIK ornek AYRILAMADI (belirsizlik 0,6 derece saat acisi).",
        f"geometri: time_gozlem = saatin merkezi (time_utc + 30 dk)",
        f"time_utc: yerel saat - {DKASC_UTC_OFSET} sa; dakikasi :30'dur "
        f"(izgara YEREL saatte kuruldu, karar 5)",
        f"transpozisyon: izotropik, egim {DKASC_EGIM} deg, albedo {DKASC_ALBEDO}, "
        f"Rb taban {DKASC_RB_TABAN}",
        f"kapi: n={olcut['n']} egim={olcut['egim']:.0f} "
        f"RMSE=%{olcut['RMSE_yuzde']:.4f} MBE=%{olcut['MBE_yuzde']:+.4f} "
        f"R2={olcut['R2']:.6f}",
        f"kapi_negatif_kontrol: egim 0 deg -> RMSE=%{sifir['RMSE_yuzde']:.4f} "
        f"MBE=%{sifir['MBE_yuzde']:+.4f} gecti={sifir['gecti']} (BEKLENEN False)",
        f"ruzgar: YOK (karar 1) - oznitelik seti config.DKASC_GECIKMELI",
        f"H_sun: PVGIS'ten degil, geometriden TURETILDI - gunduz maskesi "
        f"artik geometriden bagimsiz DEGIL (bolum 4, madde 8)",
        f"kurallar: dokumanlar/dkasc-kalite-kurallari.md",
    ])
    (cikti.parent / "dkasc_veri_surumu.txt").write_text(kunye + "\n",
                                                        encoding="utf-8")
    print(f"\n{'=' * 68}")
    print(f"Kaydedildi: {cikti.resolve()}")
    print(f"Veri surumu (sha256_16): {h}")
    if not DKASC_VERI_SHA16:
        print(f"config.DKASC_VERI_SHA16 = \"{h}\"  <- buraya yazin (henuz bos)")
    elif h == DKASC_VERI_SHA16:
        print(f"config.DKASC_VERI_SHA16 ile UYUYOR ({DKASC_VERI_SHA16})")
    else:
        print(f"  !! UYUSMUYOR: config {DKASC_VERI_SHA16}, uretilen {h}")
        print("  !! Veri veya kod degismis. Butun DKASC sonuclari bu surume "
              "bagliydi; devam etmeden once neyin degistigini bulun.")
    gunduz = s[(s["H_sun"] > 0) & s["P"].notna()]
    print(f"\nGunduz ortalama uretim: {gunduz['P'].mean():.2f} W "
          f"(kapasite 5250 W, kapasite faktoru "
          f"%{100*gunduz['P'].mean()/5250:.2f})")
    print(f"Yillik toplam (dolu saatler): "
          f"{s['P'].sum()/1000/(DKASC_BITIS_YIL-DKASC_BASLANGIC_YIL+1):.1f} "
          f"kWh/yil, {s['P'].sum()/1000/5.25/6:.1f} kWh/kWp/yil")
    return s


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("adim", choices=["dogrula", "duzenle"])
    ap.add_argument("klasor", nargs="?", default="ham/dkasc")
    ap.add_argument("--cikti", default=str(DKASC_VERI))
    a = ap.parse_args()

    klasor = Path(a.klasor)
    if not klasor.is_dir():
        sys.exit(f"{klasor} bulunamadi")

    if a.adim == "dogrula":
        sys.exit(0 if dogrula_klasor(klasor) else 1)
    duzenle(klasor, Path(a.cikti))


if __name__ == "__main__":
    main()
