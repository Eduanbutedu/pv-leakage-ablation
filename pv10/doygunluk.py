"""Faz 4 - veri hacmi doygunlugu.

Faz 2 sizintinin basarimi ne kadar sistirdigini, Faz 3 siralamanin yildan yila
korunup korunmadigini olctu. Burada sorulan: raporlanan farkin ne kadari
algoritmadan, ne kadari elinizdeki veri miktarindan geliyor?

KRITIK TASARIM NOKTASI - oznitelikler pencere DILIMLENDIKTEN SONRA uretilir.

Faz 2/3'te oznitelik tablosu tum veri uzerinde bir kez uretilip yila gore
dilimleniyordu. Faz 4'te bu yanlis olurdu: "1 yil veriyle egitildi" dedigimiz
model, yuvarlanan istatistikleri onceki yillardan tasirdi. Isinma kaybi
(konum basina 191 satir = 24 shift + 168 roll168 - 1) veri kumesinin basinda
degil, PENCERENIN basinda tuketilmelidir. Aksi halde doygunluk egrisi yapay
olarak duzlesir ve sizinti uzerine yazilan bir makale tam da bu kusuru tasir.

Test tarafi bundan etkilenmez: test yilinin gecikmeli oznitelikleri gecmis
gozlemlerdir, mesru sekilde erisilebilir. Bu yuzden dilim [pencere_basi,
test_yili] araligini KAPSAR - egitim isinmayi kendi basinda yer, test yili
dokunulmadan kalir ve n butun K seviyelerinde sabit cikar.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

from .config import BASLANGIC_YIL, KAYDIRMALI_TOHUM, SEED
from .evaluate import gun_blogu_bootstrap, gunduz_maskesi, metrikler
from .features import oznitelik_kolonlari, oznitelik_uret
from .models import modeller
from .ornekleme import gun_blogu_altornekle, hedef_satir_sayisi


# --------------------------------------------------------------------------- #
# pencere aritmetigi
# --------------------------------------------------------------------------- #
def pencere_basi(test_yil: int, pencere) -> int:
    """Egitim penceresinin baslangic yili. 'tum' -> veri kumesinin basi."""
    if pencere == "tum":
        return BASLANGIC_YIL

    if not isinstance(pencere, (int, np.integer)) or pencere < 1:
        raise ValueError(f"gecersiz pencere: {pencere!r} (pozitif tamsayi veya 'tum')")

    basla = int(test_yil) - int(pencere)
    if basla < BASLANGIC_YIL:
        raise ValueError(
            f"{test_yil} icin {pencere} yillik pencere istendi ama veri "
            f"{BASLANGIC_YIL}'te basliyor (en fazla {test_yil - BASLANGIC_YIL} yil). "
            "Sessizce kisaltmak doygunluk egrisini yalan soyletir.")
    return basla


def isinma_olc(ham_dilim: pd.DataFrame, o: pd.DataFrame) -> int:
    """Pencere basinda kaybedilen satir sayisi (konum basina), OLCULEREK.

    features.py'deki dropna mantigini burada yeniden yazmak yerine gercek
    kaybi olcuyoruz; oznitelik tanimi degisirse bu sayi kendiliginden takip
    eder, dogrulama.py'deki literal 191 ise degisimi haber verir.
    """
    kayip = ham_dilim.groupby("konum").size() - o.groupby("konum").size()
    if kayip.nunique() != 1:
        raise ValueError(
            f"Isinma kaybi konumlara gore farkli: {kayip.to_dict()}. "
            "Konumlarin zaman ekseni ayni olmali.")
    return int(kayip.iloc[0])


# --------------------------------------------------------------------------- #
# pencere onbellegi
# --------------------------------------------------------------------------- #
class PencereOnbellegi:
    """(basla, test_yil) -> oznitelik tablosu.

    Faz 2/3'un OznitelikOnbellegi'nin aksine tabloyu pencere basina yeniden
    uretir - isinmanin pencere icinde tuketilmesi bunu zorunlu kiliyor.
    Izgara (test_yil, pencere) sirasinda dolasildigi icin tek hucrelik onbellek
    yeterli: her farkli dilim tam bir kez uretilir.
    """

    def __init__(self, ham: pd.DataFrame):
        self._ham = ham
        self._anahtar: tuple | None = None
        self._deger: tuple | None = None
        self.uretim_sayisi = 0

    def al(self, basla: int, test_yil: int):
        """(oznitelik tablosu, oznitelik sutunlari, isinma) dondurur."""
        anahtar = (basla, test_yil)
        if anahtar != self._anahtar:
            yil = self._ham["time_utc"].dt.year
            dilim = self._ham[(yil >= basla) & (yil <= test_yil)]
            if dilim.empty:
                raise ValueError(f"{basla}-{test_yil} dilimi bos")

            o = oznitelik_uret(dilim, eszaman=False)
            self._anahtar = anahtar
            self._deger = (o, oznitelik_kolonlari(o), isinma_olc(dilim, o))
            self.uretim_sayisi += 1
        return self._deger

    def ham(self) -> pd.DataFrame:
        return self._ham


# --------------------------------------------------------------------------- #
# tek hucre
# --------------------------------------------------------------------------- #
def hucre_kos(onbellek: PencereOnbellegi, kol: str, pencere, test_yil: int,
              model_ad: str, tohum: int, bootstrap: bool = True) -> tuple[dict, list[dict]]:
    """Tek bir hucreyi kosar.

    Donen: (ana satir, konum bazinda satirlar)
    """
    basla = pencere_basi(test_yil, pencere)

    if kol == "kaydirmali":
        # dilim = pencere + test yili; isinma pencerenin basinda tuketilir
        o, X, isinma = onbellek.al(basla, test_yil)
        yil = o["time_utc"].dt.year.to_numpy()
        tr = np.flatnonzero(yil < test_yil)

    elif kol == "altornekleme":
        # havuz TUM gecmis; ayni satir sayisi kadar gun-blogu cekilir
        o, X, isinma = onbellek.al(BASLANGIC_YIL, test_yil)
        yil = o["time_utc"].dt.year.to_numpy()
        havuz = np.flatnonzero(yil < test_yil)

        hedef = hedef_satir_sayisi(onbellek.ham(), basla, test_yil - 1, isinma)
        yerel = gun_blogu_altornekle(o.iloc[havuz], hedef, tohum)
        tr = havuz[yerel]

    else:
        raise ValueError(f"bilinmeyen kol: {kol!r}")

    te = np.flatnonzero(yil == test_yil)
    if len(tr) == 0 or len(te) == 0:
        raise ValueError(f"bos bolme: egitim {len(tr)}, test {len(te)}")

    Xtr, ytr = o.iloc[tr][X], o.iloc[tr]["y"].to_numpy()
    test_satirlari = o.iloc[te]

    hat = modeller(onisleme=True)[model_ad]
    t0 = time.time()
    hat.fit(Xtr, ytr)
    tahmin = hat.predict(test_satirlari[X])
    egitim_sn = time.time() - t0

    # --- gunduz degerlendirmesi (Faz 2/3 ile ayni protokol) ---
    maske = gunduz_maskesi(test_satirlari)
    yte = test_satirlari["y"].to_numpy()[maske]
    tah = tahmin[maske]
    pers = test_satirlari["persistence"].to_numpy()[maske]
    konum = test_satirlari["konum"].to_numpy()[maske]
    gunler = pd.to_datetime(test_satirlari["time_utc"]).dt.date.to_numpy()[maske]

    m = metrikler(yte, tah, pers)

    # --- gun-blogu bootstrap %95 GA (tohum SEED'de sabit) ---
    ga_alt = ga_ust = np.nan
    bootstrap_sn = 0.0
    if bootstrap:
        t1 = time.time()
        # tohum SEED'de sabit: uc ornekleme tohumunda ayni gun bloklari
        # cekilsin ki GA'lar dogrudan kiyaslanabilir olsun
        ga = gun_blogu_bootstrap(yte, tah, gunler, seed=SEED)
        ga_alt, ga_ust = ga["RMSE"]
        bootstrap_sn = time.time() - t1

    ana = dict(kol=kol, pencere=str(pencere), test_yil=test_yil, model=model_ad,
               tohum=tohum, egitim_basla=basla, egitim_n=len(tr), isinma=isinma,
               durum="tamam", hata="",
               **m, RMSE_GA_alt=ga_alt, RMSE_GA_ust=ga_ust,
               egitim_sn=round(egitim_sn, 1), bootstrap_sn=round(bootstrap_sn, 1))

    # --- konum bazinda: nRMSE_ortalama (mutlak W konumlar arasi kiyaslanamaz) ---
    konum_satirlari = []
    for ad in np.unique(konum):
        k = konum == ad
        km = metrikler(yte[k], tah[k])
        konum_satirlari.append(dict(
            kol=kol, pencere=str(pencere), test_yil=test_yil, model=model_ad,
            tohum=tohum, konum=ad, n=km["n"], MAE=km["MAE"], RMSE=km["RMSE"],
            nRMSE_ortalama=km["nRMSE_ortalama"], nRMSE_kapasite=km["nRMSE_kapasite"]))

    return ana, konum_satirlari
