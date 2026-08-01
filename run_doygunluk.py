#!/usr/bin/env python3
"""Faz 4 - veri hacmi doygunlugu.

Kullanim:
    python run_doygunluk.py --dogrula      # bes invaryant kapisi, 18 kontrol (ONCE BU)
    python run_doygunluk.py --tahmin       # hucre maliyeti, kosmadan
    python run_doygunluk.py                # ana izgara, sonunda ozet
    python run_doygunluk.py --ozet         # mevcut CSV'lerden ozet, izgara kosmadan

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
import hashlib  # noqa: E402
import time  # noqa: E402
from datetime import datetime  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from pv10.config import (DOYGUNLUK_KOLLARI, DOYGUNLUK_TEST_YILLARI,  # noqa: E402
                         EGITIM_PENCERELERI, GENIS_KOSU_HARIC,
                         ORNEKLEME_TOHUMLARI, SONUC, VERI, VERI_SHA16)
from pv10 import ozet  # noqa: E402
from pv10.dogrulama import tum_invaryantlar  # noqa: E402
# _tamamlananlar ozel ad ama kasitli olarak yeniden yazilmiyor: "tamamlanmis
# hucre" tanimi (durum == 'tamam') tek yerde kalmali, yoksa devam mantigi ile
# ozetin eksik hucre sayimi birbirinden kayar.
from pv10.doygunluk import (PencereOnbellegi, _tamamlananlar,  # noqa: E402
                            hucre_kos, izgara_hucreleri, izgara_kos,
                            pencere_basi)
from pv10.models import ABLASYON_ALTKUMESI, HIZLI_ALTKUME, modeller  # noqa: E402

LOG = SONUC / "doygunluk.csv"
KONUM_LOG = SONUC / "doygunluk_konum.csv"


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


def tahmin_et(ham: pd.DataFrame, kollar, pencereler, yillar, model_adlari,
              tohumlar) -> None:
    """Iki uctan olcup izgaranin tamamina yayar.

    Egitim suresi satir sayisiyla kabaca lineer; bootstrap ise egitim
    boyutundan BAGIMSIZ (test seti her yil ~25.8 bin gunduz satiri), o yuzden
    ayri olculup her hucreye sabit eklenir.
    """
    onbellek = PencereOnbellegi(ham)
    hucreler = list(izgara_hucreleri(kollar, pencereler, yillar, model_adlari,
                                     tohumlar))

    # --- her hucrenin egitim_n'i: yalnizca (pencere, test_yil)'e bagli ---
    yil_s = ham["time_utc"].dt.year
    konum_s = ham.konum.nunique()
    isinma_toplam = None

    def egitim_n(pencere, test_yil):
        nonlocal isinma_toplam
        basla = pencere_basi(test_yil, pencere)
        ham_n = int(((yil_s >= basla) & (yil_s <= test_yil - 1)).sum())
        if isinma_toplam is None:
            _, _, isinma = onbellek.al(basla, test_yil)
            isinma_toplam = isinma * konum_s
        return ham_n - isinma_toplam

    # anahtar ORIJINAL pencere degeri (int veya 'tum'); izgara_hucreleri de
    # ayni tipi uretiyor, stringe cevirmek pencere_basi'ni kirar
    boyut = {(p, y): egitim_n(p, y) for p in pencereler for y in yillar}

    print(f"\nIzgara: {len(hucreler)} hucre")
    print(f"  egitim boyutu araligi: {min(boyut.values()):,} - "
          f"{max(boyut.values()):,} satir\n")

    # --- iki uctan olc ---
    kucuk = min(boyut, key=boyut.get)
    buyuk = max(boyut, key=boyut.get)
    print(f"Sonda hucreleri olculuyor (bootstrap DAHIL):")
    olcum = {}
    for etiket, (pen, yil) in (("kucuk", kucuk), ("buyuk", buyuk)):
        for model_ad in model_adlari:
            t0 = time.time()
            ana, _ = hucre_kos(onbellek, "kaydirmali", pen, yil, model_ad, 0,
                               bootstrap=True)
            sure = time.time() - t0
            olcum[(etiket, model_ad)] = (ana["egitim_n"], ana["egitim_sn"],
                                         ana["bootstrap_sn"], sure)
            print(f"  {etiket:6} K={str(pen):4} {yil} {model_ad:24} "
                  f"n={ana['egitim_n']:>7,}  fit {ana['egitim_sn']:>6.1f} sn  "
                  f"boot {ana['bootstrap_sn']:>5.1f} sn")

    # --- lineer yayma: fit ~ a + b*n, bootstrap sabit ---
    boot_ort = float(np.mean([v[2] for v in olcum.values()]))
    toplam = 0.0
    model_toplam = {}
    for model_ad in model_adlari:
        n1, f1, _, _ = olcum[("kucuk", model_ad)]
        n2, f2, _, _ = olcum[("buyuk", model_ad)]
        b = (f2 - f1) / (n2 - n1) if n2 != n1 else 0.0
        a = f1 - b * n1
        s = sum(max(a + b * boyut[(p, y)], 0.0) + boot_ort
                for (kol, p, y, m, t) in hucreler if m == model_ad)
        model_toplam[model_ad] = s
        toplam += s

    print(f"\n  bootstrap ortalamasi: {boot_ort:.1f} sn/hucre "
          f"x {len(hucreler)} = {boot_ort * len(hucreler) / 60:.0f} dakika")
    print(f"\nMODEL BAZINDA TAHMIN:")
    for model_ad, s in sorted(model_toplam.items(), key=lambda x: -x[1]):
        print(f"  {model_ad:24} {s / 60:>7.0f} dakika")
    print(f"\n  KABA TOPLAM: {toplam / 60:.0f} dakika ({toplam / 3600:.1f} saat)")
    print("  (lineer yayma; agir modeller ve bellek baskisi bu tahmini asabilir)")


def _baslik(s: str) -> None:
    print(f"\n{'-' * 78}\n{s}\n{'-' * 78}")


# Ozet CSV'leri. Bir tablo uretilemezse dosyasi YAZILMAZ - yarim veya bos
# dosya birakmak, sonraki oturumda gecerli sonucla karistirilir.
OZET_DOSYA = {
    "egri": "doygunluk_ozet_egri.csv",
    "marjinal": "doygunluk_ozet_marjinal.csv",
    "hacim_orani": "doygunluk_ozet_hacim_orani.csv",
    "tohum_yayilimi": "doygunluk_ozet_tohum_yayilimi.csv",
    "model_pencere": "doygunluk_ozet_model_pencere.csv",
    "model_pencere_yil": "doygunluk_ozet_model_pencere_yil.csv",
    "varyans": "doygunluk_ozet_varyans.csv",
    "konum": "doygunluk_ozet_konum.csv",
}
KUNYE = SONUC / "doygunluk_ozet_kunye.txt"


def veri_hash() -> str:
    """Calisilan parquet'in sha256'si, pvgis_pipeline.py ile ayni yontem."""
    return hashlib.sha256(VERI.read_bytes()).hexdigest()[:16]


def ozetle(kollar, pencereler, yillar, model_adlari, tohumlar) -> None:
    """Faz 4 ozet tablolari: ekrana basar ve sonuclar/ altina CSV yazar.

    ozet.py sonuclar gorulmeden yazildi; burada yalnizca CAGRILIR. Tablo
    tanimlari, metrik secimleri ve esikler bu dosyadan degistirilmez.

    Diske YUVARLANMAMIS deger gider: makalenin sayilari bu CSV'lerden
    okunacak, terminal ciktisindan degil.

    Eksiklik tespiti tahminle degil, izgara_hucreleri'nin urettigi beklenen
    kume ile logdaki tamamlanmis kumenin farkindan gelir.
    """
    if not LOG.exists():
        raise SystemExit(f"{LOG} yok - once izgarayi kosun.")

    ham_log = pd.read_csv(LOG)
    tamam = _tamamlananlar(LOG)
    beklenen = {(kol, str(p), y, m, t) for kol, p, y, m, t
                in izgara_hucreleri(kollar, pencereler, yillar, model_adlari,
                                    tohumlar)}
    eksik = sorted(beklenen - tamam)
    hatali = ham_log[ham_log.durum == "hata"]

    print(f"\n{'=' * 78}")
    print(f"FAZ 4 OZET - {len(tamam)}/{len(beklenen)} beklenen hucre tamam")
    print(f"{'=' * 78}")

    # Kural 5: eksik ve basarisiz hucreler ACIKCA listelenir, kirpilmadan.
    if len(hatali):
        _baslik(f"BASARISIZ HUCRELER ({len(hatali)})")
        with pd.option_context("display.max_rows", None, "display.width", 200):
            print(hatali[["kol", "pencere", "test_yil", "model", "tohum",
                          "hata"]].to_string(index=False))

    if eksik:
        _baslik(f"EKSIK HUCRELER ({len(eksik)})")
        e = pd.DataFrame(eksik, columns=["kol", "pencere", "test_yil", "model",
                                         "tohum"])
        with pd.option_context("display.max_rows", None, "display.width", 200):
            print(e.to_string(index=False))
        print("\nUYARI: izgara EKSIK. Asagidaki tablolar yalnizca tamamlanan "
              "hucrelerden hesaplandi.")

    d = ham_log[ham_log.durum == "tamam"]
    if d.empty:
        raise SystemExit("tamamlanmis hucre yok - ozet uretilemez.")
    dk = pd.read_csv(KONUM_LOG) if KONUM_LOG.exists() else pd.DataFrame()

    yazilan: dict[str, str] = {}
    atlanan: dict[str, str] = {}

    def yaz(t: pd.DataFrame, anahtar: str, indeks: bool = False) -> None:
        """Tabloyu tam hassasiyette diske yazar. Bos tablo YAZILMAZ."""
        if t is None or t.empty:
            atlanan[anahtar] = "tablo bos"
            return
        yol = SONUC / OZET_DOSYA[anahtar]
        t.to_csv(yol, index=indeks)  # float_format YOK -> tam hassasiyet
        yazilan[anahtar] = f"{yol.name} ({len(t)} satir)"

    def atla(anahtar: str, neden: str) -> None:
        atlanan[anahtar] = neden

    egri = ozet.egri_tablosu(d)
    _baslik("1) OGRENME EGRISI - iki kol")
    print(egri.to_string(index=False))
    yaz(egri, "egri")

    marjinal = ozet.marjinal_kazanc(egri)
    _baslik("1b) MARJINAL KAZANC - doygunluk nerede?")
    print(marjinal.to_string(index=False))
    yaz(marjinal, "marjinal")

    hacim = ozet.hacim_orani(d)
    _baslik("2) ANA ORAN - saf hacim vs uygulamali hacim")
    print(hacim.to_string(index=False))
    yaz(hacim, "hacim_orani")

    _baslik("3) TOHUM YAYILIMI - (K, yil, model) bazinda")
    t3 = ozet.tohum_yayilimi(d)
    if t3.empty:
        print("altornekleme hucresi yok")
        atla("tohum_yayilimi", "altornekleme hucresi yok")
    else:
        print(t3.to_string(index=False))
        yaz(t3, "tohum_yayilimi")

    _baslik("4) MODEL x PENCERE ETKILESIMI")
    e4 = ozet.model_pencere_etkilesimi(d)
    if not e4:
        print("kaydirmali hucre yok")
        atla("model_pencere", "kaydirmali hucre yok")
        atla("model_pencere_yil", "kaydirmali hucre yok")
    else:
        print(f"kazanan degisiyor mu: {e4['kazanan_degisiyor_mu']}  "
              f"({e4['farkli_kazanan_sayisi']} farkli kazanan, "
              f"{e4['kazanan_dagilimi']})\n")
        print(e4["pencere_bazinda"].to_string(index=False))
        print()
        print(e4["pencere_yil_bazinda"].to_string(index=False))
        yaz(e4["pencere_bazinda"], "model_pencere")
        yaz(e4["pencere_yil_bazinda"], "model_pencere_yil")

    _baslik("5) VARYANS AYRISTIRMASI")
    varyans_attrs = {}
    try:
        v = ozet.varyans_ayristirmasi(d)
        if v.empty:
            print("hizli altkume bos")
            atla("varyans", "hizli altkume bos")
        else:
            print(v.to_string(index=False))
            varyans_attrs = dict(v.attrs)
            yaz(v, "varyans")
    except ValueError as e:
        # Eksik izgarada dengesiz tasarim BEKLENEN durumdur. Izgara TAMSA ayni
        # hata gercek bir kusurdur ve yutulmaz.
        if not eksik:
            raise
        print(f"ATLANDI - izgara {len(eksik)} hucre eksik, tasarim dengeli "
              f"degil.\n  {e}")
        atla("varyans", f"tasarim dengesiz ({len(eksik)} hucre eksik)")

    _baslik("6) KONUM BAZINDA - nRMSE_ortalama")
    if dk.empty:
        print(f"{KONUM_LOG} yok")
        atla("konum", f"{KONUM_LOG.name} yok")
    else:
        t6 = ozet.konum_tablosu(dk)
        if t6.empty:
            print("kaydirmali konum satiri yok")
            atla("konum", "kaydirmali konum satiri yok")
        else:
            print(t6.to_string())
            yaz(t6, "konum", indeks=True)

    _kunye_yaz(len(tamam), len(beklenen), eksik, hatali, e4, varyans_attrs,
               yazilan, atlanan)


def _kunye_yaz(n_tamam, n_beklenen, eksik, hatali, e4, varyans_attrs,
               yazilan, atlanan) -> None:
    """Ozet CSV'lerinin kunyesi: hangi izgaradan, hangi veriden uretildiler."""
    h = veri_hash()
    s = [
        "FAZ 4 OZET KUNYESI",
        "=" * 60,
        "",
        f"kosu tarihi         : {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"izgara tamam        : {'evet' if not eksik else 'HAYIR'}",
        f"hucre               : {n_tamam}/{n_beklenen}",
        f"eksik hucre         : {len(eksik)}",
        f"basarisiz hucre     : {len(hatali)}",
        f"veri dosyasi        : {VERI.name}",
        f"veri sha256_16      : {h}",
        f"beklenen sha256_16  : {VERI_SHA16}"
        f"{'' if h == VERI_SHA16 else '   <-- UYUSMUYOR, VERI DEGISMIS'}",
        f"thread sabiti       : {OMP_THREAD_SAYISI}",
    ]

    if e4:
        s += ["", "model x pencere:",
              f"  kazanan degisiyor mu : {e4['kazanan_degisiyor_mu']}",
              f"  farkli kazanan       : {e4['farkli_kazanan_sayisi']}",
              f"  kazanan dagilimi     : {e4['kazanan_dagilimi']}"]
    if varyans_attrs:
        s += ["", "varyans ayristirmasi:",
              f"  deger                : {varyans_attrs.get('deger')}",
              f"  kol                  : {varyans_attrs.get('kol')}",
              f"  model sayisi         : {varyans_attrs.get('model_sayisi')}"]

    s += ["", f"yazilan tablolar ({len(yazilan)}):"]
    s += [f"  {k:20} {v}" for k, v in yazilan.items()] or ["  (yok)"]
    if atlanan:
        # Kural 5: atlanan tablo sessizce kaybolmaz. Onceki kosudan kalmis
        # ayni adli dosya varsa BAYAT'tir; silmiyoruz, isaret ediyoruz.
        s += ["", f"YAZILMAYAN tablolar ({len(atlanan)}):"]
        for k, v in atlanan.items():
            bayat = (SONUC / OZET_DOSYA[k]).exists()
            s.append(f"  {k:20} {v}"
                     + ("   <-- ESKI DOSYA DURUYOR, BAYAT" if bayat else ""))

    KUNYE.write_text("\n".join(s) + "\n", encoding="utf-8")
    print(f"\n{'=' * 78}")
    print(f"{len(yazilan)} ozet CSV yazildi -> {SONUC}")
    if atlanan:
        print(f"{len(atlanan)} tablo uretilemedi, kunyeye islendi: "
              f"{', '.join(atlanan)}")
    print(f"kunye: {KUNYE.name}")
    print(f"{'=' * 78}")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dogrula", action="store_true",
                    help="bes invaryant kapisini (18 kontrol) kos ve cik")
    ap.add_argument("--tahmin", action="store_true",
                    help="maliyeti tahmin et, izgarayi kosma")
    ap.add_argument("--ozet", action="store_true",
                    help="mevcut CSV'lerden ozet tablolari bas, izgarayi kosma")
    ap.add_argument("--modeller", default="hizli",
                    choices=["hizli", "ablasyon", "tumu"])
    ap.add_argument("--yillar", default=",".join(str(y) for y in DOYGUNLUK_TEST_YILLARI))
    ap.add_argument("--kol", default=",".join(DOYGUNLUK_KOLLARI))
    ap.add_argument("--hizli-bootstrap", action="store_true",
                    help="gun-blogu bootstrap GA'sini atla")
    a = ap.parse_args()

    ham = pd.read_parquet(VERI)

    if a.dogrula:
        raise SystemExit(0 if dogrula(ham) else 1)

    kollar = a.kol.split(",")
    bilinmeyen = [k for k in kollar if k not in DOYGUNLUK_KOLLARI]
    if bilinmeyen:
        raise SystemExit(f"bilinmeyen kol: {bilinmeyen}")
    yillar = [int(y) for y in a.yillar.split(",")]
    havuz = list(modeller())
    model_adlari = {"hizli": list(HIZLI_ALTKUME),
                    "ablasyon": list(ABLASYON_ALTKUMESI),
                    "tumu": [m for m in havuz if m not in GENIS_KOSU_HARIC]}[a.modeller]

    if a.ozet:
        ozetle(kollar, EGITIM_PENCERELERI, yillar, model_adlari,
               ORNEKLEME_TOHUMLARI)
        return

    if a.tahmin:
        tahmin_et(ham, kollar, EGITIM_PENCERELERI, yillar, model_adlari,
                  ORNEKLEME_TOHUMLARI)
        return

    print(f"  {thread_durumu()}")
    print(f"  veri: {len(ham):,} satir, {ham.konum.nunique()} konum")
    print(f"  log : {LOG}\n")
    t0 = time.time()
    izgara_kos(ham, kollar, EGITIM_PENCERELERI, yillar, model_adlari,
               ORNEKLEME_TOHUMLARI, LOG, KONUM_LOG,
               bootstrap=not a.hizli_bootstrap)
    print(f"\nToplam sure: {(time.time() - t0) / 60:.1f} dakika")

    ozetle(kollar, EGITIM_PENCERELERI, yillar, model_adlari,
           ORNEKLEME_TOHUMLARI)


if __name__ == "__main__":
    main()
