#!/usr/bin/env python3
"""Faz 4 - veri hacmi doygunlugu.

Kullanim:
    python run_doygunluk.py --dogrula      # dort invaryant kapisi (ONCE BU)
    python run_doygunluk.py --tahmin       # hucre maliyeti, kosmadan
    python run_doygunluk.py                # ana izgara

Ana izgaraya invaryant kapisi gecmeden gecilmez.
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# OpenMP thread sayisi numpy/sklearn IMPORT EDILMEDEN once sabitlenmeli;
# sonra atamak OpenMP calisma zamaninda etkisiz kalir. config.py yalnizca
# pathlib import ettigi icin bu asamada guvenle okunabilir.
# ---------------------------------------------------------------------------
from pv10.config import OMP_THREAD_SAYISI  # noqa: E402  (import sirasi kasitli)

# Ucu birden sabitlenir. Bu ortamda OMP_NUM_THREADS tek basina OpenBLAS
# havuzlarini da 8'e cekiyor (olculdu), ama bu numpy'nin derleme detayi ve
# surum degisiminde kayabilir. MLPRegressor matmul'lari OpenBLAS uzerinden
# gectigi icin thread sayisi degisince ciktisi BIT DUZEYINDE degisiyor
# (olculdu: 20 thread'de farkli hash, RMSE 10 ondalik ayni). Agac tabanlilar
# ve HGB bu duyarliligi gostermiyor.
THREAD_DEGISKENLERI = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
ONCEKI_THREAD = {ad: os.environ.get(ad) for ad in THREAD_DEGISKENLERI}
for _ad in THREAD_DEGISKENLERI:
    os.environ[_ad] = str(OMP_THREAD_SAYISI)

import argparse  # noqa: E402
import time  # noqa: E402

import pandas as pd  # noqa: E402

from pv10.config import VERI  # noqa: E402
from pv10.dogrulama import tum_invaryantlar  # noqa: E402


def thread_durumu() -> str:
    onceki = ", ".join(f"{k}={v if v is not None else 'ayarsiz'}"
                       for k, v in ONCEKI_THREAD.items())
    return (f"thread sabiti: {OMP_THREAD_SAYISI} "
            f"({', '.join(THREAD_DEGISKENLERI)})\n"
            f"  kosu oncesi ortam: {onceki}")


def dogrula(ham: pd.DataFrame) -> bool:
    print(f"{'=' * 78}")
    print("FAZ 4 INVARYANT KAPISI")
    print(f"{'=' * 78}")
    print(f"  {thread_durumu()}")
    print(f"  veri: {len(ham):,} satir, {ham.konum.nunique()} konum\n")

    t0 = time.time()
    d = tum_invaryantlar(ham)
    sure = time.time() - t0

    for ad in sorted(d.invaryant.unique()):
        alt = d[d.invaryant == ad]
        gecti = bool(alt.gecti.all())
        print(f"\n{'-' * 78}")
        print(f"{'GECTI' if gecti else 'KALDI'}  {ad}")
        print(f"{'-' * 78}")
        sutun = [c for c in alt.columns if c not in ("invaryant",)
                 and alt[c].notna().any()]
        print(alt[sutun].to_string(index=False))

    hepsi = bool(d.gecti.all())
    print(f"\n{'=' * 78}")
    print(f"{'HEPSI GECTI' if hepsi else 'BASARISIZ'} - "
          f"{int(d.gecti.sum())}/{len(d)} kontrol, {sure / 60:.1f} dakika")
    print(f"{'=' * 78}")
    if not hepsi:
        print("\nAna izgara KOSULMAZ. Kirilan invaryantlari duzeltmeden devam "
              "etmek Faz 4'un butun sayilarini supheli hale getirir.")
    return hepsi


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dogrula", action="store_true",
                    help="dort invaryant kapisini kos ve cik")
    a = ap.parse_args()

    ham = pd.read_parquet(VERI)

    if a.dogrula:
        raise SystemExit(0 if dogrula(ham) else 1)

    raise SystemExit("ana izgara henuz baglanmadi - once --dogrula")


if __name__ == "__main__":
    main()
