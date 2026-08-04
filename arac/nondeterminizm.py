#!/usr/bin/env python3
"""Model nondeterminizmi olcumu - iki duzey.

TESHIS betigidir, deney degil: makalenin hicbir sayisini uretmez. Ana
izgara bunu cagirmaz. Burada durmasinin sebebi, faz notundaki "olculdu"
ifadesinin dayanagi olmasi.

Sorun: ayni hucre iki kez kosuldugunda Random Forest ve Extra Trees
metrikleri 1-2 ULP oynuyordu (bkz. CLAUDE.md). Iki aday vardi - surec ici
paralel hesap, ya da pyarrow surum degisimi (25.0.0 -> 22.0.0).

Duzenek ayni hucreyi iki duzeyde tekrarlar:
  A duzeyi : AYNI surecte pes pese iki tekrar
  B duzeyi : AYRI iki surecte, ayni komut (--surec p1 / p2)
B'ye gerek duyulmasinin sebebi: thread havuzu surec basina bir kez kurulur,
A ayni cikarsa surecler arasi atama hala farkli olabilir.

Her tekrarda gunduz tahmin vektoru diske yazilir ve sha256'lanir. Metrik
degil TAHMIN VEKTORU hash'lenir; metrik yuvarlamasi farki yutabiliyor
(olculdu: dort RF kosusunun RMSE'si ayni cikti, tahmin vektorleri farkliydi).

Neural Network KONTROL olarak var: thread duyarliligi bilinen model ve
olcum izgarasinda birebir cikmisti. Duzenegin fark yakalayabildigini degil,
YAPAY fark URETMEDIGINI gostermesi icin - hepsi farkli cikarsa olcum
degersizdir.

Yorum kurali sonuc GORULMEDEN sabitlendi, bkz. nondeterminizm_karar.py.

Kullanim (kok dizinden, -m ile; iki surec SIRAYLA - ayni anda kosulmaz,
CPU cakisir ve thread atamasi olcumun konusu):
    python -m arac.nondeterminizm --surec p1
    python -m arac.nondeterminizm --surec p2
    python -m arac.nondeterminizm_karar

Betik CSV'ye EKLER, uzerine yazmaz - B duzeyi ancak boyle olusur. Onceki bir
olcumu korumak icin `--cikti` ile ayri yol verilir; karar tarafinda karsiligi
`--olcum`.

Ilk kosu: 3 Agustos 2026, pyarrow 22.0.0, OMP_NUM_THREADS=8.
Sonuc: A duzeyi kesti - RF ve ET'de dort kosunun dordu farkli hash;
NN dordunde de ayni. Sebep surec ici paralel hesap, pyarrow degil.

Dogrulama kosusu: 4 Agustos 2026, betigin REPODAKI suruyle, --surec d1/d2,
--cikti sonuclar/nondeterminizm_olcum_dogrulama.csv. Hash'lerin ilk olcumle
AYNI cikmasi beklenmez (olculen sey zaten tekrarlanmamalari); beklenen sey
KARARIN ayni cikmasi.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
from pathlib import Path

from pv10.config import OMP_THREAD_SAYISI

# Thread sayisi numpy/sklearn IMPORT EDILMEDEN once sabitlenir; sonra
# atamak OpenMP calisma zamaninda etkisiz kalir. run_doygunluk.py ile ayni
# gerekce, ayni sira.
for _ad in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_ad] = str(OMP_THREAD_SAYISI)

import pandas as pd  # noqa: E402
import pyarrow  # noqa: E402

from pv10.config import SONUC, VERI  # noqa: E402
from pv10.doygunluk import (PencereOnbellegi, hucre_kos,  # noqa: E402
                            tahmin_dosyasi)

KOL, PENCERE, TEST_YIL, TOHUM = "kaydirmali", "tum", 2020, 0
MODELLER = ("Random Forest", "Extra Trees", "Neural Network")
TEKRAR = (1, 2)
CIKTI = SONUC / "nondeterminizm_olcum.csv"
# Tahmin parquet'leri: sonuclar/tahminler/ .gitignore kapsaminda.
TAHMIN_KOK = SONUC / "tahminler" / "nondeterminizm"


def sha(a) -> str:
    return hashlib.sha256(a.tobytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--surec", required=True,
                    help="surec etiketi (or. p1 / p2); B duzeyi bununla ayrisir")
    ap.add_argument("--cikti", default=None,
                    help="olcum CSV yolu; varsayilan sonuclar/nondeterminizm_"
                         "olcum.csv. Dosya varsa satirlar EKLENIR, uzerine "
                         "yazilmaz - onceki bir olcumu korumak icin ayri yol ver.")
    a = ap.parse_args()
    cikti = Path(a.cikti) if a.cikti else CIKTI

    print(f"surec       : {a.surec}   pid {os.getpid()}")
    print(f"pyarrow     : {pyarrow.__version__}")
    print(f"thread      : {OMP_THREAD_SAYISI}")
    print(f"hucre       : {KOL} K={PENCERE} {TEST_YIL} tohum={TOHUM}")
    print(f"modeller    : {list(MODELLER)}  (Neural Network = kontrol)")
    print(f"cikti       : {cikti}")
    print()

    ham = pd.read_parquet(VERI)
    onbellek = PencereOnbellegi(ham)

    satir = []
    for model_ad in MODELLER:
        for t in TEKRAR:
            dizin = TAHMIN_KOK / f"{a.surec}_t{t}"
            t0 = time.time()
            ana, _ = hucre_kos(onbellek, KOL, PENCERE, TEST_YIL, model_ad,
                               TOHUM, bootstrap=False, tahmin_dizin=dizin)
            sure = time.time() - t0
            yol = tahmin_dosyasi(dizin, KOL, PENCERE, TEST_YIL, model_ad, TOHUM)
            d = pd.read_parquet(yol)
            h = sha(d["tahmin"].to_numpy())
            satir.append(dict(
                surec=a.surec, tekrar=t, model=model_ad, pid=os.getpid(),
                pyarrow=pyarrow.__version__, thread=OMP_THREAD_SAYISI,
                n=len(d), tahmin_sha=h,
                # y ve persistence modelden BAGIMSIZ; oynarlarsa sorun modelde
                # degil test setinde demektir - kararda acikca kontrol edilir
                y_sha=sha(d["y"].to_numpy()),
                pers_sha=sha(d["persistence"].to_numpy()),
                # repr: tam hassasiyet, yuvarlama yok
                RMSE=repr(ana["RMSE"]), MAE=repr(ana["MAE"]),
                R2=repr(ana["R2"]), egitim_n=ana["egitim_n"],
                sure_sn=round(sure, 1)))
            print(f"  {model_ad:16} tekrar {t}  {sure:6.1f} sn  "
                  f"RMSE={ana['RMSE']!r}  sha={h[:16]}")

    yeni = pd.DataFrame(satir)
    # Ayri surecler ayri kosuda yazar; onceki satirlar KORUNUR, yoksa B
    # duzeyi hic olusmaz.
    if cikti.exists():
        yeni = pd.concat([pd.read_csv(cikti), yeni], ignore_index=True)
    cikti.parent.mkdir(parents=True, exist_ok=True)
    yeni.to_csv(cikti, index=False)
    print(f"\nyazildi -> {cikti}  ({len(yeni)} satir)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
