#!/usr/bin/env python3
"""Egri uclari arasinda esli Diebold-Mariano - 45 karsilastirma.

`sonuclar/doygunluk_ozet_dm.csv`'nin surucusudur. Makaledeki "hacim etkisi
HGB 15/15, PolyRidge 15/15, LR 5/15 anlamli" iddiasi bu tablodan okunur.
Hesap kendisi degil, pv10/ozet_sonrasi.py:uc_dm icindedir - burasi yalnizca
yillari, modelleri ve tohumlari verip tabloyu yazar.

Neden sonradan: tablo 3d15cce / 8c84b11'de bir oturum scratchpad'indeki
betikle uretildi ve o betik repoya alinmadi (4be6a45 yalnizca dm_yil.py ve
regresyon_kiyas.py'yi tasidi). Bu dosya o boslugu kapatir: ayni uretim
fonksiyonu, ayni tahminler, ayni parametreler.

Ne olcer:
  Her (test yili, model, tohum) icin altornekleme K=1 ucu ile paylasilan
  K=tum ucu (kaydirmali, tohum 0) arasinda esli kumelenmis DM ve esli
  gun-blogu bootstrap GA'si. Kumelenme birimi zaman damgasi - Faz 3 ile
  ayni (ranking.py:110). Pozitif DM, K=1'in K=tum'den DAHA KOTU oldugunu
  gosterir.

Determinizm:
  Model egitilmez; diskteki tahminler okunur. Bootstrap SEED ile tohumlu.
  Uc model (LR, PolyRidge, HGB) determinist; RF/ET bu tabloda YOK. Yani
  yeniden uretim bit duzeyinde ayni olmalidir.

Onkosul:
  `sonuclar/tahminler/doygunluk/dm/` altinda 75 tahmin dosyasi
  (`run_doygunluk.py ... --etiket dm --tahmin-kaydet`). Eksik dosya acik
  hata firlatir (_tahmin_oku), sessizce atlanmaz.

Kullanim (kok dizinden):
    python -m arac.uc_dm
    python -m arac.uc_dm --cikti sonuclar/doygunluk_ozet_dm_dogrulama.csv \\
        --referans sonuclar/doygunluk_ozet_dm.csv

Betik cikti dosyasinin UZERINE YAZAR. Mevcut tabloyu korumak icin
`--cikti <yol>` ver. `--referans` verilirse yeni tablo onunla
arac/csv_karsilastir.py uzerinden kiyaslanir (bayt + alan alan `==`,
round_trip okuma, her kosuda negatif kontrol); tek fark bile varsa 1 ile
doner. `--rapor` alan duzeyindeki kiyasi CSV olarak yazar.
"""
import argparse
import os
from pathlib import Path

from pv10.config import OMP_THREAD_SAYISI

# Thread sayisi numpy import edilmeden once sabitlenir; dm_yil.py ile ayni.
for _ad in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_ad] = str(OMP_THREAD_SAYISI)

import pandas as pd  # noqa: E402

from pv10.config import (DOYGUNLUK_TEST_YILLARI, ORNEKLEME_TOHUMLARI,  # noqa: E402
                         SONUC)
from pv10.ozet_sonrasi import uc_dm  # noqa: E402

from arac.csv_karsilastir import karsilastir  # noqa: E402

CIKTI = SONUC / "doygunluk_ozet_dm.csv"
TAHMIN_DIZIN = SONUC / "tahminler" / "doygunluk" / "dm"
DM_LOG = SONUC / "doygunluk_dm.csv"
BEKLENEN_SATIR = 45
ANAHTAR = ["test_yil", "model", "tohum"]


def model_sirasi() -> list[str]:
    """Modeller `dm` kosusunun logundaki sirayla (tablonun satir sirasi)."""
    g = pd.read_csv(DM_LOG)
    g = g[g["durum"] == "tamam"]
    if len(g) != 75:
        raise SystemExit(f"{DM_LOG.name}: {len(g)} tamam hucre, 75 beklenir")
    return list(dict.fromkeys(g["model"]))


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cikti", default=None,
                    help="cikti CSV yolu; varsayilan sonuclar/doygunluk_ozet_dm.csv. "
                         "Dosya UZERINE YAZILIR.")
    ap.add_argument("--referans", default=None,
                    help="yeni tabloyu bu CSV ile toleranssiz kiyasla")
    ap.add_argument("--rapor", default=None,
                    help="alan duzeyindeki kiyas raporunun CSV yolu (--referans ile)")
    a = ap.parse_args()
    cikti = Path(a.cikti) if a.cikti else CIKTI

    modeller = model_sirasi()
    print(f"tahmin dizini : {TAHMIN_DIZIN}")
    print(f"yillar        : {list(DOYGUNLUK_TEST_YILLARI)}")
    print(f"modeller      : {modeller}")
    print(f"tohumlar      : {list(ORNEKLEME_TOHUMLARI)}")

    d = uc_dm(TAHMIN_DIZIN, DOYGUNLUK_TEST_YILLARI, modeller, ORNEKLEME_TOHUMLARI)
    if len(d) != BEKLENEN_SATIR:
        raise SystemExit(f"{len(d)} satir uretildi, {BEKLENEN_SATIR} beklenir")

    print()
    print("model bazinda (p < 0.05):")
    for model, g in d.groupby("model", sort=False):
        print(f"  {model:24s} {int(g['anlamli'].sum())}/{len(g)}  "
              f"ortalama fark {g['RMSE_fark_W'].mean():.6f} W")
    print(f"  toplam                   {int(d['anlamli'].sum())}/{len(d)}")

    d.to_csv(cikti, index=False)
    print(f"\nyazildi -> {cikti}  ({len(d)} satir)")

    if a.referans:
        return karsilastir(cikti, Path(a.referans), ANAHTAR,
                           Path(a.rapor) if a.rapor else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
