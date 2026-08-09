"""Teshis: Faz 2 varyantlarinin belirsizlik olcumu.

YORUM KURALI OLCUMDEN ONCE YAZILDI: dokumanlar/varyant-dm-yorum-kurali.md
(commit 397e362). Bu betik o kurali UYGULAR; kural burada yeniden
tartisilmaz.

Uc sinif, uc ayri olcu:

  SINIF A  eszaman, olcekleyici     -> tam kumede esli kumelenmis DM
           (test satirlari AYNI, model farkli)

  SINIF B  gece                     -> DM YOK, cebirsel ozdeslik
           (model AYNI, populasyon farkli); ozdeslik:
             RMSE^2(tumu) = [n_g*RMSE^2(gunduz) + n_c*RMSE^2(gece)] / n

  SINIF C  rastgele_kfold, enkotu   -> kesisimde esli DM + iki orneklemli
           (test satirlari FARKLI)      gun-blogu bootstrap'i

Eslestirme HER ZAMAN (konum, time_utc) uzerinden; konumsal indeksle
degil - sinif C'de satir kumeleri farklidir.

Kosu (kok dizinden):
    python -m arac.ablasyon_dm --etiket ana --log sonuclar/ablasyon.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK))

from pv10.config import SEED, SONUC  # noqa: E402
from pv10.evaluate import diebold_mariano, metrikler  # noqa: E402

SINIF = {
    "eszaman": "A", "olcekleyici": "A",
    "gece": "B",
    "rastgele_kfold": "C", "enkotu": "C",
}

# Degerlendirme MASKESINI degistiren varyantlar (gece=True). Esli DM maskeyi
# iki tarafta da GUNDUZDE sabitledigi icin bunlarin `D_manset`'i loglanan
# manset farki DEGILDIR; aradaki fark sinif B bilesenidir. Etiket ciktiya
# yazilir - okuyanin iki sayiyi karistirmamasi icin.
MASKE_DEGISTIREN = {"gece", "enkotu"}
BOOTSTRAP_TEKRAR = 1000
ALFA = 0.05


def oku(dizin: Path, varyant: str, model: str, yil: int) -> pd.DataFrame:
    yol = dizin / f"{varyant}__{model.replace(' ', '_')}__{yil}.parquet"
    if not yol.exists():
        raise FileNotFoundError(
            f"{yol} yok. Izgara --tahmin-kaydet ile kosulmali; tahmin "
            "vektoru olmadan esli DM SONRADAN kurulamaz.")
    return pd.read_parquet(yol)


def _arizasiz(d: pd.DataFrame) -> pd.DataFrame:
    """Kural 7: ariza satirlari DEGERLENDIRMEDEN cikarilir (egitimden ASLA).

    `hucre_kos` bunu yaptigi icin buradaki her olcu ayni populasyonu
    kullanmak ZORUNDA. Sinif B kapisi ilk kosuda tam bunu yakaladi:
    ozdeslik ariza satirlarini iceriyordu, loglanan RMSE icermiyordu ve
    DKASC 2018'in uc hucresi (o yilin tek ariza saati) dustu.
    PVGIS tablosunda bu sutun yoktur; orada filtre islemsizdir.
    """
    return d[~d["ariza"].to_numpy()] if "ariza" in d.columns else d


def gunduz(d: pd.DataFrame) -> pd.DataFrame:
    d = _arizasiz(d)
    return d[d["H_sun"] > 0]


# --------------------------------------------------------------------------- #
# SINIF A ve C - esli DM
# --------------------------------------------------------------------------- #
def esli_dm(temiz: pd.DataFrame, varyant: pd.DataFrame, kapasite_w: float
            ) -> dict:
    """Iki tahmin dosyasini (konum, time_utc) ile esler ve DM kosar.

    Sinif A'da birlestirme TAM ortusur; sinif C'de KESISIM verir. Ikisinde
    de maske GUNDUZ sabitlenir - `enkotu` gibi maskesi farkli varyantlarin
    sinif B etkisini icine karistirmamak icin.
    """
    a, b = gunduz(temiz), gunduz(varyant)
    m = a.merge(b, on=["konum", "time_utc"], suffixes=("_t", "_v"))
    if len(m) == 0:
        raise ValueError("kesisim BOS - eslestirme anahtari yanlis olabilir")

    if not np.allclose(m["y_t"].to_numpy(), m["y_v"].to_numpy(), equal_nan=True):
        raise ValueError(
            "ayni (konum, time_utc) icin hedef degerler farkli. Eslestirme "
            "bozuk; sessizce devam etmek anlamsiz bir DM uretir.")

    y = m["y_t"].to_numpy()
    ta, tb = m["tahmin_t"].to_numpy(), m["tahmin_v"].to_numpy()
    dm = diebold_mariano(y, ta, tb, kume=m["time_utc"].to_numpy())

    rmse_t = float(np.sqrt(np.mean((ta - y) ** 2)))
    rmse_v = float(np.sqrt(np.mean((tb - y) ** 2)))
    fark = rmse_v - rmse_t

    # --- POPULASYON MASKELEMESI AYRISTIRMASI (yorum kurali 3.3b) ---
    # Manset farki KESIN olarak uce ayrilir; test degil, cebir:
    #   D = [Rv(kes) - Rt(kes)] + [Rv(tam) - Rv(kes)] - [Rt(tam) - Rt(kes)]
    #     =        A            +         B           -         C
    # A: model etkisi, populasyon SABIT.  B, C: her kolun populasyon terimi.
    # Beklenti: kesisim `temiz`in test yilinin tekduze rastgele alt kumesi
    # oldugu icin C ~ 0; populasyon etkisi B'de yasamali.
    rt_tam = float(np.sqrt(np.mean((a["tahmin"] - a["y"]) ** 2)))
    rv_tam = float(np.sqrt(np.mean((b["tahmin"] - b["y"]) ** 2)))
    A = rmse_v - rmse_t
    B = rv_tam - rmse_v
    C = rt_tam - rmse_t
    D = rv_tam - rt_tam

    return {
        "maske": "gunduz",
        "n_kesisim": len(m),
        "n_kume": int(pd.unique(m["time_utc"]).size),
        "kesisim_orani": len(m) / len(a),
        "RMSE_temiz_kesisim": rmse_t,
        "RMSE_varyant_kesisim": rmse_v,
        "RMSE_temiz_tam": rt_tam,
        "RMSE_varyant_tam": rv_tam,
        "fark_W": fark,
        "fark_kapasite_yuzde": 100.0 * fark / kapasite_w,
        "fark_bagil_yuzde": 100.0 * fark / rmse_t,
        "DM": dm["DM"], "p": dm["p"], "anlamli": bool(dm["p"] < ALFA),
        "A_model": A, "B_pop_varyant": B, "C_pop_temiz": C, "D_manset": D,
        "ayristirma_hatasi": abs((A + B - C) - D),
        "pop_terimi": B - C,
    }


# --------------------------------------------------------------------------- #
# SINIF C - iki orneklemli gun-blogu bootstrap'i
# --------------------------------------------------------------------------- #
def iki_ornekli_bootstrap(temiz: pd.DataFrame, varyant: pd.DataFrame,
                          tekrar: int = BOOTSTRAP_TEKRAR, seed: int = SEED
                          ) -> dict:
    """TAM test kumeleri uzerinde RMSE farki icin %95 GA.

    Iki kume FARKLI satirlardan olusur; gun bloklari her kumede BAGIMSIZ
    yeniden orneklenir. %10-25'lik ortusme yok sayilir: pozitif
    korelasyonu atmak varyansi FAZLA tahmin eder, yani GA genisler ve
    fark ilan etmek ZORLASIR (muhafazakar yon).
    """
    rng = np.random.default_rng(seed)

    def hazirla(d):
        g = gunduz(d)
        gun = pd.to_datetime(g["time_utc"]).dt.date.to_numpy()
        hata2 = (g["tahmin"].to_numpy() - g["y"].to_numpy()) ** 2
        ix = {k: np.flatnonzero(gun == k) for k in np.unique(gun)}
        return hata2, np.array(list(ix.keys())), ix

    # NOT: maske IKI tarafta da GUNDUZ. `rastgele_kfold` icin raporlanan
    # sayi zaten gunduzdur, yani bu bootstrap manset buyuklugunu olcer.
    # `enkotu` icin raporlanan sayi TUM satirlardir (gece=True); burada
    # gunduzde sabitlemek sinif C bilesenini sinif B'den AYIRIR, yani
    # `enkotu` icin bu GA manset sayisinin GA'si DEGILDIR. Ayrimin sebebi
    # yorum kuralinda yazili: iki sinifin etkisi birbirine karistirilmaz.
    ha, ka, ia = hazirla(temiz)
    hb, kb, ib = hazirla(varyant)

    dagilim = np.empty(tekrar)
    for i in range(tekrar):
        sa = np.concatenate([ia[k] for k in rng.choice(ka, len(ka), replace=True)])
        sb = np.concatenate([ib[k] for k in rng.choice(kb, len(kb), replace=True)])
        dagilim[i] = np.sqrt(hb[sb].mean()) - np.sqrt(ha[sa].mean())

    alt, ust = np.percentile(dagilim, [2.5, 97.5])
    return {
        "bootstrap_fark_W": float(np.sqrt(hb.mean()) - np.sqrt(ha.mean())),
        "bootstrap_GA_alt": float(alt), "bootstrap_GA_ust": float(ust),
        "bootstrap_sifiri_iceriyor": bool(alt <= 0.0 <= ust),
        "n_gun_temiz": len(ka), "n_gun_varyant": len(kb),
    }


# --------------------------------------------------------------------------- #
# SINIF B - cebirsel ozdeslik + KAPI
# --------------------------------------------------------------------------- #
def gece_ozdesligi(temiz: pd.DataFrame, gece_log_rmse: float) -> dict:
    """`gece` varyantinin -%28,95'i nereden geliyor? Test degil, CEBIR.

        RMSE^2(tumu) = [n_g*RMSE^2(gunduz) + n_c*RMSE^2(gece)] / n_toplam

    KAPI: `gece` varyantinin LOGLANAN RMSE'si, `temiz`in kaydedilen
    tahminlerinden TUM satirlar uzerinde yeniden hesaplanan RMSE'ye esit
    olmali. Esit degilse "gece ile temiz ayni modeli kurar" iddiasi
    YANLIStir ve ozdeslik raporlanmaz.
    """
    temiz = _arizasiz(temiz)          # kural 7 - loglanan RMSE ile ayni populasyon
    g, c = temiz[temiz["H_sun"] > 0], temiz[temiz["H_sun"] <= 0]
    r_g = float(np.sqrt(np.mean((g["tahmin"] - g["y"]) ** 2)))
    r_c = float(np.sqrt(np.mean((c["tahmin"] - c["y"]) ** 2)))
    n_g, n_c = len(g), len(c)
    n = n_g + n_c

    ozdeslik = float(np.sqrt((n_g * r_g ** 2 + n_c * r_c ** 2) / n))
    dogrudan = float(np.sqrt(np.mean((temiz["tahmin"] - temiz["y"]) ** 2)))

    return {
        "n_gunduz": n_g, "n_gece": n_c, "n_toplam": n,
        "RMSE_gunduz": r_g, "RMSE_gece": r_c,
        "RMSE_tumu_ozdeslikten": ozdeslik,
        "RMSE_tumu_dogrudan": dogrudan,
        "ozdeslik_hatasi": abs(ozdeslik - dogrudan),
        "RMSE_gece_varyanti_loglanan": gece_log_rmse,
        "kapi_farki": abs(dogrudan - gece_log_rmse),
        "kapi_gecti": bool(abs(dogrudan - gece_log_rmse) < 1e-9),
    }


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--etiket", required=True, help="tahmin dizini adi")
    ap.add_argument("--log", required=True, help="izgara logu (csv)")
    ap.add_argument("--kapasite", type=float, default=1000.0)
    ap.add_argument("--cikti-onek", default=None,
                    help="varsayilan: --etiket degeri")
    a = ap.parse_args()

    dizin = SONUC / "tahminler" / "ablasyon" / a.etiket
    log = pd.read_csv(a.log)
    onek = a.cikti_onek or a.etiket
    modeller = sorted(log["model"].unique())
    yillar = sorted(log["test_yil"].unique())
    pd.set_option("display.width", 250, "display.max_columns", 40)

    dm_satir, boot_satir, ozd_satir = [], [], []
    for yil in yillar:
        for model in modeller:
            temiz = oku(dizin, "temiz", model, yil)

            # --- SINIF B kapisi + ozdeslik ---
            g_log = float(log[(log.varyant == "gece") & (log.model == model)
                              & (log.test_yil == yil)]["RMSE"].iloc[0])
            ozd = gece_ozdesligi(temiz, g_log)
            ozd_satir.append(dict(test_yil=yil, model=model, **ozd))

            def log_rmse(varyant: str) -> float:
                s = log[(log.varyant == varyant) & (log.model == model)
                        & (log.test_yil == yil)]["RMSE"]
                if len(s) != 1:
                    raise ValueError(
                        f"{varyant}/{model}/{yil} icin {len(s)} log satiri "
                        "var, 1 bekleniyordu")
                return float(s.iloc[0])

            for varyant, sinif in SINIF.items():
                if sinif == "B":
                    continue
                v = oku(dizin, varyant, model, yil)
                r = esli_dm(temiz, v, a.kapasite)

                # Loglanan manset ile ayristirmanin D'si ayni sey mi?
                # `enkotu` gece=True tasidigi icin loglanan RMSE'si TUM
                # satirlar uzerindedir; `D_manset` ise gunduzde. Fark sinif B
                # bilesenidir ve populasyon maskelemesiyle KARISTIRILMAZ.
                rt_log, rv_log = log_rmse("temiz"), log_rmse(varyant)
                d_log = rv_log - rt_log
                esdeger = varyant not in MASKE_DEGISTIREN
                dm_satir.append(dict(
                    test_yil=yil, model=model, varyant=varyant, sinif=sinif,
                    **r,
                    manset_esdeger=esdeger,
                    RMSE_temiz_log=rt_log, RMSE_varyant_log=rv_log,
                    D_log_tumsatir=d_log,
                    sinifB_payi=d_log - r["D_manset"]))
                if sinif == "C":
                    b = iki_ornekli_bootstrap(temiz, v)
                    boot_satir.append(dict(test_yil=yil, model=model,
                                           varyant=varyant, **b))

    dm = pd.DataFrame(dm_satir)
    boot = pd.DataFrame(boot_satir)
    ozd = pd.DataFrame(ozd_satir)

    # --- KAPI 2: sinif B ozdesligi ---
    print("=" * 100)
    print("KAPI - SINIF B: `gece` ile `temiz` ayni modeli mi kuruyor?")
    print("=" * 100)
    kotu = ozd[~ozd["kapi_gecti"]]
    print(f"  hucre {len(ozd)}   gecen {int(ozd['kapi_gecti'].sum())}   "
          f"maks kapi farki {ozd['kapi_farki'].max():.3e}   "
          f"maks ozdeslik hatasi {ozd['ozdeslik_hatasi'].max():.3e}")
    if len(kotu):
        print(kotu.to_string(index=False))
        print("\n[DUR] Sinif B siniflandirmasi YANLIS - ozdeslik raporlanmaz.")
        return 1
    print("  GECTI - `gece`nin loglanan RMSE'si `temiz`in tahminlerinden "
          "tum satirlarda yeniden hesaplananla ayni.")

    print()
    print("=" * 100)
    print("SINIF B - CEBIRSEL OZDESLIK (test DEGIL)")
    print("=" * 100)
    print(ozd[["test_yil", "model", "n_gunduz", "n_gece", "RMSE_gunduz",
               "RMSE_gece", "RMSE_tumu_ozdeslikten", "RMSE_tumu_dogrudan"]]
          .to_string(index=False, float_format=lambda v: f"{v:.6f}"))

    print()
    print("=" * 100)
    print("SINIF A ve C - ESLI KUMELENMIS DIEBOLD-MARIANO")
    print("=" * 100)
    print(dm.to_string(index=False, float_format=lambda v: f"{v:.6f}"))

    print()
    print("=" * 100)
    print("SINIF C - IKI ORNEKLEMLI GUN-BLOGU BOOTSTRAP'I (tam test kumeleri)")
    print("=" * 100)
    print("Maske iki tarafta da GUNDUZ. `rastgele_kfold` icin bu MANSET")
    print("buyuklugudur; `enkotu` icin DEGILDIR (onun manset sayisi tum")
    print("satirlardan gelir) - burada sinif C bileseni sinif B'den ayrilmistir.")
    print()
    print(boot.to_string(index=False, float_format=lambda v: f"{v:.6f}"))

    print()
    print("=" * 100)
    print("SINIF C - POPULASYON MASKELEMESI AYRISTIRMASI (yorum kurali 3.3b)")
    print("=" * 100)
    print("D = A + B - C   (A: model etkisi populasyon SABIT; B, C: populasyon)")
    print("Beklenti: C ~ 0 (kesisim, test yilinin tekduze rastgele alt kumesi)")
    print()
    c = dm[dm.sinif == "C"]
    print(c[["test_yil", "model", "varyant", "maske", "A_model",
             "B_pop_varyant", "C_pop_temiz", "pop_terimi", "D_manset",
             "ayristirma_hatasi", "manset_esdeger", "D_log_tumsatir",
             "sinifB_payi"]]
          .to_string(index=False, float_format=lambda v: f"{v:.6f}"))
    print(f"\n  maks ayristirma hatasi = {c['ayristirma_hatasi'].max():.3e} "
          f"(cebirsel ozdeslik; 0 olmali)")
    print(f"  |C| ortalama = {c['C_pop_temiz'].abs().mean():.6f} W   "
          f"|B| ortalama = {c['B_pop_varyant'].abs().mean():.6f} W")

    # KAPI: maskesi degismeyen varyantta `D_manset` loglanan farkin TA KENDISI
    # olmali. Bu ayni zamanda maske etiketinin negatif kontroludur - `enkotu`
    # icin sifirdan UZAK cikmasi beklenir, cikmazsa etiket anlamsizdir.
    esd = c[c.manset_esdeger]
    print(f"\n  KAPI (maske esdeger varyantlar): maks |sinifB_payi| = "
          f"{esd['sinifB_payi'].abs().max():.3e}  "
          f"({'GECTI' if esd['sinifB_payi'].abs().max() < 1e-9 else 'DUSTU'})")

    for v in sorted(c["varyant"].unique()):
        s = c[c.varyant == v]
        oran = (s.pop_terimi.abs() / s.A_model.abs())
        print(f"  {v:16s} A ort={s.A_model.mean():+12.6f}  "
              f"(B-C) ort={s.pop_terimi.mean():+11.6f}  "
              f"D(gunduz) ort={s.D_manset.mean():+12.6f}  "
              f"D(log) ort={s.D_log_tumsatir.mean():+12.6f}  "
              f"sinifB ort={s.sinifB_payi.mean():+10.6f}")
        print(f"  {'':16s} anlamli={int(s.anlamli.sum())}/{len(s)}  "
              f"(B-C) ters isaret={int((np.sign(s.A_model) != np.sign(s.pop_terimi)).sum())}/{len(s)}  "
              f"A ile D_manset TERS (maskeleme)="
              f"{int((np.sign(s.A_model) != np.sign(s.D_manset)).sum())}/{len(s)}  "
              f"|B-C|/|A| medyan={oran.median():.4f} maks={oran.max():.4f}")

    print()
    print("=" * 100)
    print("VARYANT OZETI")
    print("=" * 100)
    ozet = dm.groupby(["varyant", "sinif"]).agg(
        hucre=("p", "size"), anlamli=("anlamli", "sum"),
        fark_ort_W=("fark_W", "mean"), p_medyan=("p", "median"),
        kesisim_orani=("kesisim_orani", "mean")).reset_index()
    print(ozet.to_string(index=False, float_format=lambda v: f"{v:.6f}"))
    print(f"\n  test sayisi = {len(dm)}   0,05 esiginde beklenen tesadufi "
          f"anlamli = {len(dm) * ALFA:.2f}   coklu duzeltme YAPILMADI")

    for ad, t in (("dm", dm), ("bootstrap", boot), ("gece_ozdeslik", ozd)):
        yol = SONUC / f"ablasyon_belirsizlik_{onek}_{ad}.csv"
        t.to_csv(yol, index=False)
        print(f"  yazildi: {yol.name}  ({len(t)} satir)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
