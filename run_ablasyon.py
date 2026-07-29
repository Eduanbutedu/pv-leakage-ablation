#!/usr/bin/env python3
"""Faz 2 - sizinti ablasyon izgarasi.

Kullanim:
    python run_ablasyon.py --tahmin              # once maliyeti gor, kosmadan
    python run_ablasyon.py                       # hizli modeller, tum varyantlar
    python run_ablasyon.py --modeller ablasyon   # Random Forest ve MLP dahil
    python run_ablasyon.py --yillar 2021,2022,2023
    python run_ablasyon.py --ozet                # sadece mevcut logu ozetle

Kosu kesilirse ayni komutu tekrar verin: tamamlanmis hucreler atlanir.
"""

from __future__ import annotations

import argparse
import time

import pandas as pd

from pv10.config import SIZINTI_VARYANTLARI, SONUC, VERI
from pv10.experiment import enflasyon_tablosu, izgara_kos
from pv10.models import ABLASYON_ALTKUMESI, HIZLI_ALTKUME, modeller

LOG = SONUC / "ablasyon.csv"


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
    a = ap.parse_args()

    if a.ozet:
        if not LOG.exists():
            raise SystemExit(f"{LOG} yok - once izgarayi kosun")
        ozetle(pd.read_csv(LOG))
        return

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

    if a.tahmin:
        print("\nMaliyet tahmini icin tek hucre olculuyor...")
        ham = pd.read_parquet(VERI)
        from pv10.experiment import OznitelikOnbellegi, hucre_kos
        ob = OznitelikOnbellegi(ham)
        t0 = time.time()
        hucre_kos(ob, "temiz", model_adlari[0], yillar[-1])
        bir = time.time() - t0
        print(f"  '{model_adlari[0]}' / {yillar[-1]} -> {bir:.1f} sn")
        print(f"  KABA tahmin: {hucre} hucre x ~{bir:.0f} sn = "
              f"~{hucre * bir / 60:.0f} dakika")
        print("  (agir modeller ve erken yillar farkli surer; bu yalnizca "
              "buyukluk mertebesi)")
        return

    print(f"\nLog: {LOG}")
    ham = pd.read_parquet(VERI)
    print(f"Veri: {len(ham):,} satir, {ham.konum.nunique()} konum\n")

    t0 = time.time()
    sonuc = izgara_kos(ham, varyantlar, model_adlari, yillar, LOG)
    print(f"\nToplam sure: {(time.time() - t0) / 60:.1f} dakika")
    ozetle(sonuc)


if __name__ == "__main__":
    main()