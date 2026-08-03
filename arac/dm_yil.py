#!/usr/bin/env python3
"""Yil ici esli Diebold-Mariano - bes test yilinin hepsi.

Faz notundaki "bes yilin hepsi sinandi, kazanan-ikinci farki 0/5 anlamli"
ifadesinin dayanagi bu betiktir. Hesap kendisi degil,
pv10/ozet_sonrasi.py:yil_ici_dm icindedir - burasi yalnizca hangi yilda
hangi modellerin kiyaslanacagini secip tabloyu birlestirir.

Ne olcer:
  Her test yilinda, o yilin RMSE siralamasindaki ILK UC modelin butun
  ikilileri arasinda esli kumelenmis DM. Kumelenme birimi zaman damgasi -
  Faz 3 ile ayni (ranking.py:110). Pozitif DM, model_a'nin model_b'den
  DAHA KOTU oldugunu gosterir.

  Ilk uc model her yil AYRI hesaplanir; siralama yila gore degistigi icin
  sabit bir model listesi kullanmak sorunun kendisini kacirirdi.
  `kazanan_ikinci_cifti` sutunu, makalenin iddiasinin dayandigi satiri
  isaretler: o yilin birincisi ile ikincisi.

Neden iki dizin:
  2022 tahminleri dm2022/ altinda (pyarrow 25.0.0 doneminde kosuldu),
  2019/2020/2021/2023 dm_kalan/ altinda (22.0.0). Yil -> dizin eslemesi
  KAYNAK sozlugunde acikca duruyor; tahmin dosyasi bulunamazsa
  _tahmin_oku hata firlatir, sessizce atlanmaz.

Dipnot sutunu:
  Random Forest ve Extra Trees surec ici nondeterminist (bkz.
  arac/nondeterminizm.py). Bu iki modelden birini iceren satirin son
  basamagi baska kosuda birebir tekrarlanmayabilir; sutun bunu satir
  duzeyinde isaretler. 3 Agustos 2026 kosusunda yalnizca 2021'in iki
  satiri dipnotlu, kazanan-ikinci ciftlerinin hicbiri degil.

Onkosul:
  Tahmin vektorleri diskte olmali - izgara --tahmin-kaydet ile kosulmus
  olacak. Yoksa esli DM SONRADAN hesaplanamaz.

Kullanim (kok dizinden):
    python -m arac.dm_yil

Ilk kosu: 3 Agustos 2026. 15 karsilastirma, 1 anlamli
(2023 Polynomial Ridge vs Hist Gradient Boosting, p=0,038040 - birinci
UCUNCU cifti). Kazanan-ikinci: 0/5 anlamli, p = 0,155011 / 0,742136 /
0,432974 / 0,413134 / 0,114696, besinin de esli GA'si sifiri iceriyor.
"""
import os
from itertools import combinations

from pv10.config import OMP_THREAD_SAYISI

# Thread sayisi numpy import edilmeden once sabitlenir; run_doygunluk.py
# ile ayni gerekce, ayni sira.
for _ad in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_ad] = str(OMP_THREAD_SAYISI)

import pandas as pd  # noqa: E402

from pv10.config import SONUC  # noqa: E402
from pv10.ozet_sonrasi import DM_KUMELENME_BIRIMI, yil_ici_dm  # noqa: E402

CIKTI = SONUC / "doygunluk_ozet_dm_yil.csv"
ILK_N = 3  # yil basina kiyaslanan model sayisi
# yil -> (log dosyasi, tahmin dizini)
KAYNAK = {
    2019: ("doygunluk_dm_kalan.csv", "dm_kalan"),
    2020: ("doygunluk_dm_kalan.csv", "dm_kalan"),
    2021: ("doygunluk_dm_kalan.csv", "dm_kalan"),
    2022: ("doygunluk_dm2022.csv", "dm2022"),
    2023: ("doygunluk_dm_kalan.csv", "dm_kalan"),
}
# Surec ici nondeterminist modeller - olculdu, bkz. arac/nondeterminizm.py
NONDET = {"Extra Trees", "Random Forest"}


def main() -> int:
    pd.set_option("display.width", 260, "display.max_columns", 60,
                  "display.max_rows", None)

    print("=" * 100)
    print("YIL ICI ESLI DIEBOLD-MARIANO - bes test yili, K=tum, kaydirmali")
    print("=" * 100)
    print("  pozitif DM -> model_a, model_b'den DAHA KOTU")
    print(f"  kumelenme birimi: {DM_KUMELENME_BIRIMI}")
    print("  Faz 3 ile ayni birim (ranking.py:110, kume=damga)")
    print()

    parca = []
    for yil, (log_ad, dizin_ad) in sorted(KAYNAK.items()):
        g = pd.read_csv(SONUC / log_ad)
        g = g[(g.durum == "tamam") & (g.test_yil == yil)]
        if g.empty:
            raise SystemExit(f"{yil}: {log_ad} icinde tamamlanmis hucre yok")
        sira = g.set_index("model")["RMSE"].sort_values()
        ilk_uc = list(sira.index[:ILK_N])
        ciftler = list(combinations(ilk_uc, 2))

        d = yil_ici_dm(SONUC / "tahminler" / "doygunluk" / dizin_ad, yil, ciftler)
        d["kaynak_dizin"] = dizin_ad
        d["en_iyi"], d["ikinci"] = sira.index[0], sira.index[1]
        d["kazanan_ikinci_cifti"] = [
            {r.model_a, r.model_b} == {sira.index[0], sira.index[1]}
            for r in d.itertuples()]
        d["dipnot"] = [
            ("son basamagi baska kosuda birebir tekrarlanmayabilir: "
             + ", ".join(sorted(NONDET & {r.model_a, r.model_b})))
            if NONDET & {r.model_a, r.model_b} else ""
            for r in d.itertuples()]
        parca.append(d)
        print(f"{yil}  ilk uc: {ilk_uc}   ({dizin_ad})")

    d = pd.concat(parca, ignore_index=True)

    goster = ["test_yil", "model_a", "model_b", "RMSE_a", "RMSE_b",
              "RMSE_fark_W", "DM", "p", "anlamli", "n_ham", "n_kume",
              "fark_GA_alt", "fark_GA_ust", "GA_sifiri_iceriyor",
              "kazanan_ikinci_cifti"]
    print()
    print(d[goster].to_string(index=False))

    print()
    print("-" * 100)
    print("KAZANAN-IKINCI CIFTLERI (makalenin iddiasinin dayandigi satirlar)")
    print("-" * 100)
    k = d[d.kazanan_ikinci_cifti]
    print(k[goster + ["dipnot"]].to_string(index=False))

    print()
    print("-" * 100)
    print("OZET")
    print("-" * 100)
    print(f"  karsilastirma         : {len(d)}  ({d.test_yil.nunique()} yil)")
    print(f"  p < 0.05              : {int(d.anlamli.sum())}/{len(d)}")
    print(f"  esli GA sifir icerir  : {int(d.GA_sifiri_iceriyor.sum())}/{len(d)}")
    print(f"  kazanan-ikinci anlamli: {int(k.anlamli.sum())}/{len(k)}")
    print(f"  p min / maks          : {d.p.min():.6g} / {d.p.max():.6g}")
    dip = d[d.dipnot != ""]
    print(f"  dipnotlu satir        : {len(dip)}"
          + (f"  -> {sorted(set(dip.test_yil))}" if len(dip) else ""))

    d.to_csv(CIKTI, index=False)
    print(f"\nyazildi -> {CIKTI}  ({len(d)} satir)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
