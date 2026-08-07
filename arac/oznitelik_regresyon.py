"""Teshis: `oznitelik_uret` parametrelesmesi uretilen tabloyu degistirdi mi?

`features.py`'ye `gecikmeli` / `eszaman_degisken` parametreleri eklendi ve
`evaluate.metrikler`/`etki_buyuklugu`'ne `kapasite_w` eklendi. Iddia:
VARSAYILANLARLA cagrildiklarinda davranis degismemistir.

Bu betik iddiayi ozet duzeyinde degil OZNITELIK MATRISI duzeyinde sinar.
Ablasyonun yeniden kosulmasi ~30 metrik kiyaslar; oznitelik matrisi
degisse bile ablasyonun duyarsiz oldugu bir sutunda degisirse ozet yine
tutardi. Burada 525.888 x ~30 degerin hepsi bit duzeyinde kiyaslanir.

Yontem: referans surum git'ten CIKARILIR ve HIC DEGISTIRILMEDEN gecici bir
pakete konur. `from .config import ...` satirinin calisabilmesi icin ayni
pakete bir `config.py` koyulur ve o da gercek `pv10.config`'i yeniden
ihrac eder - referans dosyanin kendisine tek bir karakter dokunulmaz.

Kosu (kok dizinden):
    python -m arac.oznitelik_regresyon
    python -m arac.oznitelik_regresyon --referans 1cb311c
"""

from __future__ import annotations

import argparse
import importlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK))

from pv10.config import VERI  # noqa: E402

VARSAYILAN_REFERANS = "1cb311c"   # oznitelik parametrelesmesinden ONCEKI commit
HEDEF = "pv10/features.py"


def referans_modul(commit: str, gecici: Path):
    """Referans features.py'yi git'ten cikarip ice aktarilabilir hale getirir."""
    ham = subprocess.run(["git", "show", f"{commit}:{HEDEF}"],
                         cwd=KOK, capture_output=True, check=True).stdout

    paket = gecici / "refpaket"
    paket.mkdir()
    (paket / "__init__.py").write_bytes(b"")
    # referans dosya BYTE DUZEYINDE aynen yazilir - tek karakter degismez
    (paket / "features.py").write_bytes(ham)
    # `from .config import ...` calissin diye ayni pakete koprü konur
    (paket / "config.py").write_text(
        "from pv10.config import *  # noqa: F401,F403\n", encoding="utf-8")

    sys.path.insert(0, str(gecici))
    modul = importlib.import_module("refpaket.features")
    return modul, len(ham)


def cerceve_kiyas(a: pd.DataFrame, b: pd.DataFrame, ad: str) -> list[str]:
    """Iki oznitelik tablosunu bit duzeyinde kiyaslar; farklari listeler."""
    sorun = []
    if list(a.columns) != list(b.columns):
        yalniz_a = [c for c in a.columns if c not in b.columns]
        yalniz_b = [c for c in b.columns if c not in a.columns]
        if yalniz_a or yalniz_b:
            sorun.append(f"{ad}: sutun KUMESI farkli - yalniz referansta "
                         f"{yalniz_a}, yalniz yenide {yalniz_b}")
        else:
            sorun.append(f"{ad}: sutun SIRASI farkli")
        return sorun
    if a.shape != b.shape:
        sorun.append(f"{ad}: sekil farkli - referans {a.shape}, yeni {b.shape}")
        return sorun

    for c in a.columns:
        x, y = a[c], b[c]
        if x.dtype != y.dtype:
            sorun.append(f"{ad}: {c} dtype farkli - {x.dtype} vs {y.dtype}")
            continue
        if pd.api.types.is_float_dtype(x):
            esit = np.array_equal(x.to_numpy(), y.to_numpy(), equal_nan=True)
        else:
            esit = x.equals(y)
        if not esit:
            fark = int((x.to_numpy() != y.to_numpy()).sum())
            sorun.append(f"{ad}: {c} DEGERLERI farkli ({fark} satir)")
    return sorun


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--referans", default=VARSAYILAN_REFERANS)
    ap.add_argument("--veri", default=str(VERI))
    a = ap.parse_args()

    print(f"referans commit : {a.referans}")
    print(f"veri            : {a.veri}")
    ham = pd.read_parquet(a.veri)
    print(f"                  {len(ham):,} satir, {ham.konum.nunique()} konum")

    gecici = Path(tempfile.mkdtemp(prefix="oznitelik_regresyon_"))
    try:
        ref, bayt = referans_modul(a.referans, gecici)
        import pv10.features as yeni
        print(f"referans dosya  : {bayt:,} bayt, git'ten degistirilmeden alindi")
        print(f"yeni dosya      : {Path(yeni.__file__).name}\n")

        sorunlar = []
        for etiket, kw in (("eszaman=False", {}), ("eszaman=True", {"eszaman": True})):
            r = ref.oznitelik_uret(ham, **kw)
            y = yeni.oznitelik_uret(ham, **kw)          # VARSAYILAN argumanlar
            s = cerceve_kiyas(r, y, etiket)
            sorunlar += s
            print(f"  {etiket:16s} referans {r.shape}  yeni {y.shape}  "
                  f"-> {'BIREBIR' if not s else 'FARK VAR'}")
            if not s:
                print(f"  {'':16s} {r.shape[0]*r.shape[1]:,} deger, "
                      f"{len(r.columns)} sutun, bit duzeyinde esit")
            # oznitelik_kolonlari da kiyaslanir - modele GIREN sutun kumesi
            rk, yk = ref.oznitelik_kolonlari(r), yeni.oznitelik_kolonlari(y)
            if rk != yk:
                sorunlar.append(f"{etiket}: oznitelik_kolonlari farkli")
            else:
                print(f"  {'':16s} oznitelik_kolonlari: {len(rk)} sutun, ayni")
    finally:
        sys.path.remove(str(gecici))
        shutil.rmtree(gecici, ignore_errors=True)

    print()
    if sorunlar:
        print("SONUC: REGRESYON VAR")
        for s in sorunlar:
            print(f"  -> {s}")
        return 1
    print("SONUC: REGRESYON YOK - varsayilan argumanlarla uretilen oznitelik "
          "tablosu referans surumle BIT DUZEYINDE ayni.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
