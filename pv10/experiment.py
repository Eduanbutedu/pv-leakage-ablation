"""Sizinti ablasyon izgarasi.

Her hucre bir (varyant, model, test_yili) uclusudur. Hucre sonuclari tek tek
diske yazilir; kosu kesilirse tamamlanmis hucreler atlanir. Amac su tabloyu
uretmek: yaygin degerlendirme hatalari raporlanan basarimi ne kadar sisiriyor?

Varyantlarin her biri farkli bir yere mudahale eder:
  eszaman        -> ozniteliklere (hedef saatteki meteoroloji eklenir)
  rastgele_kfold -> bolmeye (kronolojik yerine karistirmali)
  gece           -> degerlendirme maskesine (gece saatleri dahil)
  olcekleyici    -> on-islemeye (imputasyon/olcekleme tum veriye fit edilir)
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from .config import (DKASC_K8A_ORAN, DKASC_UTC_OFSET, ESZAMAN_DEGISKEN,
                     GECIKMELI_DEGISKEN, KAPASITE_W, SEED, SIZINTI_VARYANTLARI)
from .evaluate import gunduz_maskesi, metrikler
from .features import oznitelik_kolonlari, oznitelik_uret
from .models import modeller


# --------------------------------------------------------------------------- #
# oznitelik onbellegi - eszaman varyanti icin tablo iki kez uretilmeli
# --------------------------------------------------------------------------- #
class OznitelikOnbellegi:
    """Oznitelik tablosunu bir kez uretip saklar.

    `gecikmeli` / `eszaman_degisken` BEYAN EDILEN oznitelik setidir ve
    onbellege girer; varsayilanlari GUFBD cekirdek seti. DKASC kolunda
    `config.DKASC_GECIKMELI` / `config.DKASC_ESZAMAN` gecirilir (karar 1:
    ruzgar yok). Ayni tuple, PVGIS verisi uzerinde ESLESMIS KONTROL
    kosusunda da kullanilir - iki kolun sisme oranlari ancak ayni sayida
    sizinti kanaliyla kiyaslanabilir.
    """

    def __init__(self, ham: pd.DataFrame,
                 gecikmeli: tuple[str, ...] = GECIKMELI_DEGISKEN,
                 eszaman_degisken: tuple[str, ...] = ESZAMAN_DEGISKEN):
        self._ham = ham
        self.gecikmeli = tuple(gecikmeli)
        self.eszaman_degisken = tuple(eszaman_degisken)
        self._bellek: dict[bool, tuple[pd.DataFrame, list[str]]] = {}

    def al(self, eszaman: bool) -> tuple[pd.DataFrame, list[str]]:
        if eszaman not in self._bellek:
            o = oznitelik_uret(self._ham, eszaman=eszaman,
                               gecikmeli=self.gecikmeli,
                               eszaman_degisken=self.eszaman_degisken)
            self._bellek[eszaman] = (o, oznitelik_kolonlari(o))
        return self._bellek[eszaman]


# --------------------------------------------------------------------------- #
# bolme
# --------------------------------------------------------------------------- #
def bolme_indeksleri(o: pd.DataFrame, test_yil: int,
                     rastgele: bool) -> tuple[np.ndarray, np.ndarray]:
    """Egitim ve test indeksleri.

    Kronolojik: test_yil'dan onceki her sey egitim, test_yil test.
    Rastgele  : ayni satir havuzu, ama karistirilip ayni BOYUTTA test ayrilir.
                Test boyutu esit tutulur ki fark bolmeden gelsin, veri
                miktarindan gelmesin.
    """
    yil = o["time_utc"].dt.year.to_numpy()
    havuz = np.flatnonzero(yil <= test_yil)
    test_n = int(np.sum(yil == test_yil))

    if not rastgele:
        return np.flatnonzero(yil < test_yil), np.flatnonzero(yil == test_yil)

    rng = np.random.default_rng(SEED)
    karisik = rng.permutation(havuz)
    return karisik[test_n:], karisik[:test_n]


# --------------------------------------------------------------------------- #
# tek hucre
# --------------------------------------------------------------------------- #
def tahmin_dosyasi(dizin, varyant_ad: str, model_ad: str, test_yil: int):
    """Hucre basina tahmin dosyasinin yolu. Model adindaki bosluklar `_`."""
    return dizin / f"{varyant_ad}__{model_ad.replace(' ', '_')}__{test_yil}.parquet"


def k8a_bayragi(o: pd.DataFrame, tr: np.ndarray) -> np.ndarray:
    """Kural 8a - kismi ariza gunu bayragi, satir basina (o ile hizali).

    Esik = DKASC_K8A_ORAN x EGITIM bolmesinin gunduz medyani (`H_sun > 0`,
    `ariza` disi); yalnizca `tr` satirlarindan, hucre basina yeniden - bolme
    `rastgele_kfold` ise karistirilmis egitim bolmesi. Gunun medyani o yerel
    takvim gununun gunduz satirlarindan alinir; bir gunun medyani yalnizca
    o gunun kendi verisini kullanir. Medyani altinda kalan gunun BUTUN
    satirlari bayraklanir. Gunduz satiri olmayan gun bayraklanmaz.

    ON-KAYIT SONRASI duyarlilik analizi icindir; ana sonuclar 8a'SIZDIR.
    """
    if "ariza" not in o.columns:
        raise ValueError("kural 8a yalnizca DKASC tablosunda tanimli "
                         "(`ariza` sutunu yok)")
    gunduz = ((o["H_sun"] > 0) & ~o["ariza"]).to_numpy()
    egitim = np.zeros(len(o), dtype=bool)
    egitim[tr] = True
    esik = DKASC_K8A_ORAN * float(np.median(o["y"].to_numpy()[gunduz & egitim]))
    gun = (o["time_utc"] + pd.Timedelta(hours=DKASC_UTC_OFSET)).dt.normalize()
    medyan = o["y"][gunduz].groupby(gun[gunduz]).median()
    bayrakli = set(medyan.index[medyan < esik])
    return gun.isin(bayrakli).to_numpy()


def hucre_kos(onbellek: OznitelikOnbellegi, varyant_ad: str, model_ad: str,
              test_yil: int, kapasite_w: float = KAPASITE_W,
              tahmin_dizin=None, kural_8a: bool = False) -> dict:
    """Tek bir (varyant, model, yil) hucresini kosar ve metrikleri dondurur.

    kural_8a=True: kismi ariza gunleri (`k8a_bayragi`) DEGERLENDIRMEDEN
    cikarilir, egitimden ASLA. Varsayilan False; kapaliyken kod yolu
    degismez.
    """
    v = SIZINTI_VARYANTLARI[varyant_ad]
    o, X = onbellek.al(v["eszaman"])

    # Kural 10 (DKASC): `kismi` bayrakli satirlar gecikme KAYNAGIDIR ama
    # ornek DEGILDIR - ne egitim hedefi ne test gozlemi olurlar. Oznitelikleri
    # tam seri uzerinde zaten uretildi; burada yalnizca ornek havuzundan
    # cikarilirlar. Bolmeden ONCE cikarilir ki kronolojik ve rastgele kollar
    # AYNI havuzu bolsun. PVGIS tablosunda bu sutun yoktur, kod yolu girilmez.
    if "kismi" in o.columns:
        o = o[~o["kismi"].to_numpy()].reset_index(drop=True)

    tr, te = bolme_indeksleri(o, test_yil, v["rastgele_kfold"])
    Xtr, Xte = o.iloc[tr][X], o.iloc[te][X]
    ytr, yte = o.iloc[tr]["y"].to_numpy(), o.iloc[te]["y"].to_numpy()

    # --- on-isleme sizintisi ---
    if v["olcekleyici_tum"]:
        # KASITLI KOTU PRATIK: imputasyon ve olcekleme, test seti de dahil
        # tum veriye fit edilir. Boylece test setinin dagilim bilgisi
        # egitime sizar.
        tum = pd.concat([Xtr, Xte])
        imp = SimpleImputer(strategy="median").fit(tum)
        olc = StandardScaler().fit(imp.transform(tum))
        don = lambda A: olc.transform(imp.transform(A))
        Xtr, Xte = don(Xtr), don(Xte)
        hat = modeller(onisleme=False)[model_ad]
    else:
        hat = modeller(onisleme=True)[model_ad]

    t0 = time.time()
    hat.fit(Xtr, ytr)
    tahmin = hat.predict(Xte)
    sure = time.time() - t0

    # --- degerlendirme maskesi ---
    test_satirlari = o.iloc[te]
    maske = gunduz_maskesi(test_satirlari, gece_dahil=v["gece"])
    # Kural 7 (DKASC): ariza saatleri DEGERLENDIRMEDEN cikarilir, egitimden
    # ASLA. Gece satiri dersinin aynisi - filtre yalnizca ciktida.
    if "ariza" in test_satirlari.columns:
        maske = maske & ~test_satirlari["ariza"].to_numpy()
    if kural_8a:
        k8a = k8a_bayragi(o, tr)[te]
        maske = maske & ~k8a
    pers = test_satirlari["persistence"].to_numpy()

    m = metrikler(yte[maske], tahmin[maske], pers[maske], kapasite_w=kapasite_w)

    # --- tahmin vektoru (metrikler HESAPLANDIKTAN sonra, onlara dokunmadan) ---
    #
    # Faz 4'ten FARKLI olarak MASKESIZ yazilir ve `H_sun` tasinir. Iki sebep:
    #   1) `gece` varyantinin cebirsel ozdesligi gece satirlarini gerektiriyor
    #      (RMSE^2(tumu) = [n_g*RMSE^2(gunduz) + n_c*RMSE^2(gece)] / n).
    #   2) Maskeyi sonradan uygulamak, `enkotu` gibi maskesi farkli
    #      varyantlari ORTAK bir maskeyle kiyaslayabilmeyi mumkun kiliyor.
    # `(konum, time_utc)` de yaziliyor: `rastgele_kfold` kolunda test
    # satirlari FARKLI oldugu icin eslestirme konumsal indeksle YAPILAMAZ.
    if tahmin_dizin is not None:
        yol = tahmin_dosyasi(tahmin_dizin, varyant_ad, model_ad, test_yil)
        yol.parent.mkdir(parents=True, exist_ok=True)
        # `ariza` de yazilir: kural 7 geregi o satirlar DEGERLENDIRMEDEN
        # cikariliyor, dolayisiyla sonradan kurulan her olcu ayni
        # populasyonu kullanabilmek icin bayragi gormek zorunda. PVGIS
        # tablosunda sutun yoktur; orada False yazilir.
        ar = (test_satirlari["ariza"].to_numpy() if "ariza" in test_satirlari
              else np.zeros(len(test_satirlari), dtype=bool))
        kayit = pd.DataFrame({
            "konum": test_satirlari["konum"].to_numpy(),
            "time_utc": test_satirlari["time_utc"].to_numpy(),
            "H_sun": test_satirlari["H_sun"].to_numpy(),
            "ariza": ar,
            "y": yte,
            "persistence": pers,
            "tahmin": tahmin,
        })
        # 8a acikken bayrak da yazilir; `ablasyon_dm` sutun varsa dislar.
        # Kapaliyken sutun YOK - eski tahmin dosyalariyla ayni sema.
        if kural_8a:
            kayit["k8a"] = k8a
        kayit.to_parquet(yol, index=False)

    satir = dict(varyant=varyant_ad, model=model_ad, test_yil=test_yil,
                 egitim_n=len(tr), **m, egitim_sn=round(sure, 1))
    if kural_8a:
        satir["k8a_test_saat"] = int(k8a.sum())
    return satir


# --------------------------------------------------------------------------- #
# izgara
# --------------------------------------------------------------------------- #
def izgara_kos(ham: pd.DataFrame, varyantlar: list[str], model_adlari: list[str],
               yillar: list[int], log_yolu, ilerleme=print,
               gecikmeli: tuple[str, ...] = GECIKMELI_DEGISKEN,
               eszaman_degisken: tuple[str, ...] = ESZAMAN_DEGISKEN,
               kapasite_w: float = KAPASITE_W,
               tahmin_dizin=None, kural_8a: bool = False) -> pd.DataFrame:
    """Izgarayi kosar. Tamamlanmis hucreler log dosyasindan okunup atlanir."""
    onbellek = OznitelikOnbellegi(ham, gecikmeli, eszaman_degisken)

    tamam: set[tuple] = set()
    if log_yolu.exists():
        onceki = pd.read_csv(log_yolu)
        tamam = set(map(tuple, onceki[["varyant", "model", "test_yil"]].to_numpy()))
        ilerheme_mesaji = f"{len(tamam)} hucre daha once tamamlanmis, atlaniyor"
        ilerleme(ilerheme_mesaji)

    toplam = len(varyantlar) * len(model_adlari) * len(yillar)
    sayac = 0
    for varyant in varyantlar:
        for yil in yillar:
            for model_ad in model_adlari:
                sayac += 1
                anahtar = (varyant, model_ad, yil)
                if anahtar in tamam:
                    continue
                etiket = f"[{sayac}/{toplam}] {varyant} / {model_ad} / {yil}"
                try:
                    satir = hucre_kos(onbellek, varyant, model_ad, yil,
                                      kapasite_w=kapasite_w,
                                      tahmin_dizin=tahmin_dizin,
                                      kural_8a=kural_8a)
                except Exception as e:  # bir hucre patlarsa izgara devam etmeli
                    ilerleme(f"{etiket} -> HATA: {type(e).__name__}: {e}")
                    continue

                # her hucreyi ANINDA yaz: kosu kesilirse is kaybolmasin
                pd.DataFrame([satir]).to_csv(
                    log_yolu, mode="a", header=not log_yolu.exists(), index=False)
                ilerleme(f"{etiket} -> RMSE {satir['RMSE']:7.2f}  "
                         f"R2 {satir['R2']:.3f}  skill {satir['skill']:6.2f}%  "
                         f"({satir['egitim_sn']} sn)")

    return pd.read_csv(log_yolu)


def enflasyon_tablosu(sonuc: pd.DataFrame) -> pd.DataFrame:
    """Her varyantin 'temiz' referansa gore basarim sismesi.

    Makalenin ana tablosu bu olacak.
    """
    temiz = (sonuc[sonuc.varyant == "temiz"]
             .set_index(["model", "test_yil"])[["RMSE", "R2"]]
             .rename(columns={"RMSE": "RMSE_temiz", "R2": "R2_temiz"}))
    b = sonuc.join(temiz, on=["model", "test_yil"])
    b["RMSE_orani"] = b.RMSE / b.RMSE_temiz
    b["R2_artis"] = b.R2 - b.R2_temiz

    return (b.groupby("varyant")
            .agg(RMSE_ort=("RMSE", "mean"),
                 R2_ort=("R2", "mean"),
                 RMSE_orani=("RMSE_orani", "mean"),
                 R2_artis=("R2_artis", "mean"),
                 hucre=("RMSE", "size"))
            .sort_values("RMSE_ort"))