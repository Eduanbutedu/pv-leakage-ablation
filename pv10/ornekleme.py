"""Faz 4 kontrol kolu - gun duzeyinde, konuma gore tabakali altornekleme.

Kaydirmali kol "son K yil"i alir; bu kol AYNI satir sayisini tum gecmisten
ceker. Ikisi arasindaki fark yalnizca yillarin dagilimi olmalidir, o yuzden
ornekleme granulaitesi ve konum payi kontrol altinda tutulur.

Iki tasarim karari:

1. GUN duzeyinde cekilir, saat duzeyinde DEGIL. Komsu saatler neredeyse
   kopyadir; esit satir sayisinda rastgele bir saat kumesi surekli bir
   pencereden cok daha fazla farkli gune yayilir ve yapay olarak bilgili
   cikar. Bu, kontrol kolunu gecersiz kilardi. Gun-blogu bootstrap zaten ayni
   otokorelasyonu kabul ediyor; ornekleme de ayni granulaitede.

2. KONUMA GORE TABAKALI. Havuzdan serbestce cekilirse alti konumun payi
   tohumdan tohuma oynar ve tohumlar arasi yayilim, olcmek istedigimiz
   ornekleme tesadufune konum dengesizligini de karistirir.

Cekim YERINE KOYMADAN yapilir - bu bir altorneklem, bootstrap degil. Havuz
hedefe esit oldugunda (2019'da K=5 boyle) cekim havuzun tamamini almali ve
sonuc kaydirmali kolla BIREBIR ayni cikmalidir; dogrulama.py'deki 4. invaryant
tam olarak bunu test eder.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def gun_blogu_altornekle(o_havuz: pd.DataFrame, hedef_konum: dict[str, int],
                         tohum: int) -> np.ndarray:
    """Havuzdan gun bloklari cekip konum basina hedef satir sayisini tutturur.

    o_havuz      : ornekleme havuzu (oznitelik tablosunun egitim dilimi)
    hedef_konum  : konum -> cekilecek satir sayisi
    tohum        : YALNIZCA gun secimini belirler

    Donen deger o_havuz'un KONUMSAL indeksleridir (iloc icin), artan sirali.

    Tam gun cekildigi icin hedefe genelde birkac satir kala durulur: bir sonraki
    gun hedefi asacaksa alinmaz. Gercek satir sayisi loga yazilir, hedefle
    karsilastirilabilir olsun diye.
    """
    rng = np.random.default_rng(tohum)
    gun = pd.to_datetime(o_havuz["time_utc"]).dt.floor("D").to_numpy()
    konum = o_havuz["konum"].to_numpy()

    eksik = set(hedef_konum) - set(np.unique(konum))
    if eksik:
        raise ValueError(
            f"Hedef verilen konumlar havuzda yok: {sorted(eksik)}. "
            "Sessizce atlamak kolu konum bazinda dengesiz birakir.")

    secilen: list[np.ndarray] = []
    for ad in sorted(hedef_konum):
        yerel = np.flatnonzero(konum == ad)
        hedef = hedef_konum[ad]

        # gun -> o konumdaki satirlarin konumsal indeksleri
        g_yerel = gun[yerel]
        sira = np.argsort(g_yerel, kind="stable")
        g_sirali, y_sirali = g_yerel[sira], yerel[sira]
        sinir = np.flatnonzero(np.r_[True, g_sirali[1:] != g_sirali[:-1]])
        bloklar = np.split(y_sirali, sinir[1:])

        toplam = sum(len(b) for b in bloklar)
        if toplam < hedef:
            raise ValueError(
                f"{ad}: havuzda {toplam} satir var, hedef {hedef}. "
                "Altornekleme havuzu hedeften kucuk olamaz.")

        # gunleri karistir, hedefi asmadan doldur
        alinan, birikim = [], 0
        for i in rng.permutation(len(bloklar)):
            b = bloklar[i]
            if birikim + len(b) > hedef:
                continue
            alinan.append(b)
            birikim += len(b)
            if birikim == hedef:
                break

        if not alinan:
            raise ValueError(f"{ad}: hicbir gun blogu secilemedi (hedef {hedef}).")
        secilen.append(np.concatenate(alinan))

    return np.sort(np.concatenate(secilen))


def hedef_satir_sayisi(ham: pd.DataFrame, basla: int, bitir: int,
                       isinma: int) -> dict[str, int]:
    """Kaydirmali kolun konum basina satir sayisi - altornekleme hedefi.

    [basla, bitir] yillarindaki ham satirlardan pencere basindaki isinma
    kaybi dusulur. Kaydirmali kol tam olarak bu kadar satir gorur; kontrol
    kolu da ayni sayiyi tutturmali ki tek degisken yil dagilimi kalsin.
    """
    yil = ham["time_utc"].dt.year
    dilim = ham[(yil >= basla) & (yil <= bitir)]
    sayi = dilim.groupby("konum").size()

    if sayi.nunique() != 1:
        raise ValueError(
            f"{basla}-{bitir} araliginda konumlarin satir sayisi esit degil: "
            f"{sayi.to_dict()}. Veri butunlugu bozuk.")

    return {ad: int(n) - isinma for ad, n in sayi.items()}
