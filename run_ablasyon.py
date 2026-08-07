#!/usr/bin/env python3
"""Faz 2 - sizinti ablasyon izgarasi.

Kullanim:
    python run_ablasyon.py --tahmin              # once maliyeti gor, kosmadan
    python run_ablasyon.py                       # hizli modeller, tum varyantlar
    python run_ablasyon.py --modeller ablasyon   # Random Forest ve MLP dahil
    python run_ablasyon.py --yillar 2021,2022,2023
    python run_ablasyon.py --ozet                # sadece mevcut logu ozetle

DKASC kolu ve eslesmis kontrol kosusu:
    python run_ablasyon.py --set dkasc --veri veri/dkasc_m6b.parquet \\
        --yillar 2018,2019,2020,2021,2022 --etiket dkasc
    python run_ablasyon.py --set dkasc --etiket pvgis_indirgenmis

Ikinci komut ESLESMIS KONTROLDUR: ayni PVGIS verisi, ayni kod, yalnizca
DKASC'nin indirgenmis oznitelik seti. Iki kolun sisme oranlari ancak ayni
sayida sizinti kanaliyla kiyaslanabilir - DKASC'de ruzgar yok (karar 1) ve
H_sun geometriden turetildigi icin sizinti tasimiyor (bolum 4, madde 8).

--etiket VERILMEZSE kosu ana ablasyon.csv'ye yazar. Farkli oznitelik seti
veya farkli veri ile kosarken --etiket ZORUNLU sayilmali; aksi halde iki
farkli deneyin hucreleri ayni tabloda karisir ve ozet ortalamalari kirlenir.

Kosu kesilirse ayni komutu tekrar verin: tamamlanmis hucreler atlanir.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd

from pv10.config import (DKASC_ESZAMAN, DKASC_GECIKMELI, DKASC_KAPASITE_W,
                         ESZAMAN_DEGISKEN, GECIKMELI_DEGISKEN, KAPASITE_W,
                         SIZINTI_VARYANTLARI, SONUC, VERI)
from pv10.experiment import enflasyon_tablosu, izgara_kos
from pv10.models import ABLASYON_ALTKUMESI, HIZLI_ALTKUME, modeller

# Beyan edilen oznitelik setleri. Yeni bir set eklemek buraya bir satirdir;
# kod yoluna bayrak eklemek DEGILDIR.
OZNITELIK_SETLERI = {
    "gufbd": (GECIKMELI_DEGISKEN, ESZAMAN_DEGISKEN, KAPASITE_W),
    "dkasc": (DKASC_GECIKMELI, DKASC_ESZAMAN, DKASC_KAPASITE_W),
}


def log_yolu(etiket: str | None) -> Path:
    return SONUC / (f"ablasyon_{etiket}.csv" if etiket else "ablasyon.csv")


def ozetle(sonuc: pd.DataFrame) -> None:
    print(f"\n{'=' * 78}")
    print("ENFLASYON TABLOSU -- 'temiz' referansa gore")
    print(f"{'=' * 78}")
    t = enflasyon_tablosu(sonuc)
    print(f"{'varyant':<16}{'RMSE':>9}{'R2':>8}{'RMSE orani':>12}{'R2 artisi':>11}{'hucre':>7}")
    print("-" * 78)
    for ad, r in t.iterrows():
        print(f"{ad:<16}{r.RMSE_ort:>9.2f}{r.R2_ort:>8.3f}"
              f"{r.RMSE_orani:>12.3f}{r.R2_artis:>+11.3f}{int(r.hucre):>7}")

    print("\nModel bazinda ortalama RMSE (varyanta gore):")
    p = sonuc.pivot_table(index="model", columns="varyant", values="RMSE", aggfunc="mean")
    sutunlar = [c for c in ["temiz", "eszaman", "rastgele_kfold", "gece",
                            "olcekleyici", "enkotu"] if c in p.columns]
    print(p[sutunlar].round(2).to_string())

    print("\nYil bazinda 'temiz' RMSE (siralama kararliligi icin ilk isaret):")
    y = sonuc[sonuc.varyant == "temiz"].pivot_table(
        index="test_yil", columns="model", values="RMSE", aggfunc="mean")
    print(y.round(2).to_string())


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modeller", default="hizli",
                    choices=["hizli", "ablasyon", "tumu"])
    ap.add_argument("--varyantlar", default=None,
                    help="virgulle; varsayilan hepsi")
    ap.add_argument("--yillar", default="2017,2018,2019,2020,2021,2022,2023")
    ap.add_argument("--tahmin", action="store_true",
                    help="maliyeti tahmin et, kosma")
    ap.add_argument("--ozet", action="store_true", help="mevcut logu ozetle")
    ap.add_argument("--veri", default=str(VERI),
                    help="parquet yolu; varsayilan dondurulmus PVGIS seti")
    ap.add_argument("--set", dest="set_ad", default="gufbd",
                    choices=sorted(OZNITELIK_SETLERI),
                    help="beyan edilen oznitelik seti (varsayilan gufbd)")
    ap.add_argument("--etiket", default=None,
                    help="ayri log dosyasi: ablasyon_<etiket>.csv")
    a = ap.parse_args()

    LOG = log_yolu(a.etiket)
    gecikmeli, eszaman_degisken, kapasite_w = OZNITELIK_SETLERI[a.set_ad]

    if a.ozet:
        if not LOG.exists():
            raise SystemExit(f"{LOG} yok - once izgarayi kosun")
        ozetle(pd.read_csv(LOG))
        return

    # Varsayilan disi bir kosu ana logu kirletmemeli. Sessizce karismasi,
    # ozet ortalamalarini FARKLI deneylerin hucreleri uzerinden aldirir.
    if (a.set_ad != "gufbd" or Path(a.veri) != VERI) and not a.etiket:
        raise SystemExit(
            f"--set {a.set_ad} / --veri {a.veri} ile kosuyorsunuz ama --etiket "
            "verilmedi. Bu kosu ana ablasyon.csv'ye yazardi ve iki farkli "
            "deneyin hucreleri ayni tabloda karisirdi. --etiket verin.")

    varyantlar = (a.varyantlar.split(",") if a.varyantlar
                  else list(SIZINTI_VARYANTLARI))
    bilinmeyen = [v for v in varyantlar if v not in SIZINTI_VARYANTLARI]
    if bilinmeyen:
        raise SystemExit(f"bilinmeyen varyant: {bilinmeyen}")

    havuz = list(modeller())
    model_adlari = {"hizli": list(HIZLI_ALTKUME),
                    "ablasyon": list(ABLASYON_ALTKUMESI),
                    "tumu": havuz}[a.modeller]
    yillar = [int(y) for y in a.yillar.split(",")]

    hucre = len(varyantlar) * len(model_adlari) * len(yillar)
    print(f"Izgara: {len(varyantlar)} varyant x {len(model_adlari)} model "
          f"x {len(yillar)} yil = {hucre} hucre")
    print(f"  varyantlar: {', '.join(varyantlar)}")
    print(f"  modeller  : {', '.join(model_adlari)}")
    print(f"  yillar    : {yillar[0]}-{yillar[-1]}")
    print(f"  veri      : {a.veri}")
    print(f"  oznitelik : --set {a.set_ad}  gecikmeli={gecikmeli}  "
          f"eszaman={eszaman_degisken}  kapasite={kapasite_w:.0f} W")

    if a.tahmin:
        print("\nMaliyet tahmini icin tek hucre olculuyor...")
        ham = pd.read_parquet(a.veri)
        from pv10.experiment import OznitelikOnbellegi, hucre_kos
        ob = OznitelikOnbellegi(ham, gecikmeli, eszaman_degisken)
        t0 = time.time()
        hucre_kos(ob, "temiz", model_adlari[0], yillar[-1],
                  kapasite_w=kapasite_w)
        bir = time.time() - t0
        print(f"  '{model_adlari[0]}' / {yillar[-1]} -> {bir:.1f} sn")
        print(f"  KABA tahmin: {hucre} hucre x ~{bir:.0f} sn = "
              f"~{hucre * bir / 60:.0f} dakika")
        print("  (agir modeller ve erken yillar farkli surer; bu yalnizca "
              "buyukluk mertebesi)")
        return

    print(f"\nLog: {LOG}")
    ham = pd.read_parquet(a.veri)
    print(f"Veri: {len(ham):,} satir, {ham.konum.nunique()} konum\n")

    t0 = time.time()
    sonuc = izgara_kos(ham, varyantlar, model_adlari, yillar, LOG,
                       gecikmeli=gecikmeli,
                       eszaman_degisken=eszaman_degisken,
                       kapasite_w=kapasite_w)
    print(f"\nToplam sure: {(time.time() - t0) / 60:.1f} dakika")
    ozetle(sonuc)


if __name__ == "__main__":
    main()