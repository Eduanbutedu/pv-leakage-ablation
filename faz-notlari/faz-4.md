# Faz 4 - veri hacmi doygunlugu

Durum: ALTYAPI TAMAM, IZGARA KOSULMADI.
Uretilen deney sonucu: YOK.

Oturumun commit'leri:

    13c6ee8  Phase 4 scaffolding: window logic, subsampling, invariant gate,
             summaries
    ae0f3c7  Add Phase 4 grid runner and cost estimation
    2406774  Add research context document and git/handover conventions

Agac: bu not commit edildikten sonra temiz. Etiket atilmadi - faz bitmedi.

## Degisen dosyalar

| dosya | durum |
|---|---|
| `pv10/config.py` | Faz 4 sabitleri eklendi |
| `pv10/ornekleme.py` | yeni |
| `pv10/doygunluk.py` | yeni |
| `pv10/dogrulama.py` | yeni |
| `pv10/ozet.py` | yeni |
| `run_doygunluk.py` | yeni |
| `dokumanlar/arastirma-baglami.md` | yeni |
| `CLAUDE.md` | Git + Devir notu bolumleri, baslik yonlendirmesi |

`pv10/experiment.py`, `pv10/features.py`, `pv10/models.py`, `pv10/evaluate.py`,
`pv10/ranking.py` DEGISMEDI. Faz 2/3 kod yolu ellenmedi.

## Yeni fonksiyon imzalari

    pv10/doygunluk.py
      pencere_basi(test_yil: int, pencere) -> int
      isinma_olc(ham_dilim: pd.DataFrame, o: pd.DataFrame) -> int
      class PencereOnbellegi:
          __init__(self, ham: pd.DataFrame)
          al(self, basla: int, test_yil: int)
          ham(self) -> pd.DataFrame
      hucre_kos(onbellek, kol: str, pencere, test_yil: int, model_ad: str,
                tohum: int, bootstrap: bool = True) -> tuple[dict, list[dict]]
      izgara_hucreleri(kollar, pencereler, yillar, model_adlari, tohumlar)
      _tamamlananlar(log_yolu) -> set[tuple]
      izgara_kos(ham, kollar, pencereler, yillar, model_adlari, tohumlar,
                 log_yolu, konum_log_yolu, bootstrap=True, ilerleme=print)
                 -> pd.DataFrame

    pv10/ornekleme.py
      gun_blogu_altornekle(o_havuz: pd.DataFrame,
                           hedef_konum: dict[str, int], tohum: int) -> np.ndarray
      hedef_satir_sayisi(ham: pd.DataFrame, basla: int, bitir: int,
                         isinma: int) -> dict[str, int]

    pv10/dogrulama.py
      invaryant_1(onbellek, referans: dict) -> list[dict]
      invaryant_2(onbellek, referans: dict) -> list[dict]
      invaryant_3(onbellek) -> list[dict]
      invaryant_4(onbellek) -> list[dict]
      invaryant_5(onbellek, ham: pd.DataFrame) -> list[dict]
      referanslari_oku() -> dict
      tum_invaryantlar(ham: pd.DataFrame, ilerleme=print) -> pd.DataFrame

    pv10/ozet.py
      egri_tablosu(d) -> pd.DataFrame
      marjinal_kazanc(egri) -> pd.DataFrame
      hacim_orani(d) -> pd.DataFrame
      tohum_yayilimi(d) -> pd.DataFrame
      model_pencere_etkilesimi(d, kol="kaydirmali") -> dict
      varyans_ayristirmasi(d, kol="kaydirmali", deger="nRMSE_kapasite")
                           -> pd.DataFrame
      konum_tablosu(dk, kol="kaydirmali") -> pd.DataFrame

    run_doygunluk.py
      thread_durumu() -> str
      dogrula(ham) -> bool
      tahmin_et(ham, kollar, pencereler, yillar, model_adlari, tohumlar) -> None

## Config sabitleri

    EGITIM_PENCERELERI      = (1, 2, 3, 5, "tum")
    DOYGUNLUK_TEST_YILLARI  = (2019, 2020, 2021, 2022, 2023)
    DOYGUNLUK_KOLLARI       = ("kaydirmali", "altornekleme")
    ORNEKLEME_TOHUMLARI     = (11, 22, 33)
    KAYDIRMALI_TOHUM        = 0
    GENIS_KOSU_HARIC        = ("Support Vector Regression",)
    OMP_THREAD_SAYISI       = 8
    INVARYANT_TOLERANS      = 1e-6

Degismeyen: SEED = 42, BASLANGIC_YIL = 2014, BITIS_YIL = 2023,
KAPASITE_W = 1000.0, UFUK = 24, GECIKMELER = (24, 48, 168).

## Uretilecek cikti dosyalari ve semalari

`sonuclar/doygunluk.csv` -- HENUZ URETILMEDI

    kol, pencere, test_yil, model, tohum, egitim_basla, egitim_n, isinma,
    durum, hata, MAE, RMSE, nRMSE_ortalama, nRMSE_kapasite, R2, n,
    RMSE_persistence, skill, RMSE_GA_alt, RMSE_GA_ust, egitim_sn, bootstrap_sn

    devam anahtari: (kol, pencere, test_yil, model, tohum)
    durum in {"tamam", "hata"}; yalnizca "tamam" tamamlanmis sayilir

`sonuclar/doygunluk_konum.csv` -- HENUZ URETILMEDI

    kol, pencere, test_yil, model, tohum, konum, n, MAE, RMSE,
    nRMSE_ortalama, nRMSE_kapasite

Izgara boyutu: 255 hucre.
  kaydirmali   {1,2,3,5,tum} x 5 yil x 3 model x 1 tohum =  75
  altornekleme {1,2,3,5}     x 5 yil x 3 model x 3 tohum = 180
Altornekleme K=tum URETILMEZ; kaydirmali K=tum hucresiyle ayni hucredir.

## Kapi sonuclari

Kosu: `python run_doygunluk.py --dogrula`. 18/18 kontrol gecti, 1.2 dakika.
Ortam: OMP/OPENBLAS/MKL_NUM_THREADS = 8 (kosu oncesi ucu de ayarsizdi).

### Invaryant 1 -- pencere esdegerligi (2019)

Beklenen: K=5 == K=tum == ablasyon.csv temiz/2019; egitim_n 261798.

| model | K=5 | K=tum | referans | bagil fark (ikili) | bagil fark (ref) |
|---|---|---|---|---|---|
| Linear Regression | 141.343658 | 141.343658 | 141.343658 | 0.0 | 0.0 |
| Polynomial Ridge | 136.502929 | 136.502929 | 136.502929 | 0.0 | 6.050675e-13 |
| Hist Gradient Boosting | 137.168967 | 137.168967 | 137.168967 | 0.0 | 0.0 |

egitim_n gozlenen 261798, beklenen 261798, fark 0.

### Invaryant 2 -- Faz 2 uyumlulugu (2023, K=tum)

Beklenen: ablasyon.csv temiz/2023; egitim_n 472182; test_n 25792.

| model | yeni | referans | bagil fark | mutlak fark |
|---|---|---|---|---|
| Linear Regression | 137.839921 | 137.839921 | 0.0 | 0.0 |
| Polynomial Ridge | 132.614714 | 132.614714 | 7.797529e-12 | 1.034067e-09 |
| Hist Gradient Boosting | 133.404201 | 133.404201 | 0.0 | 0.0 |

egitim_n 472182 == beklenen. test_n 25792 == beklenen.

### Invaryant 3 -- isinma siniri (2023)

| pencere | egitim_basla | egitim_n gozlenen | beklenen | fark | isinma | sinir_siziyor |
|---|---|---|---|---|---|---|
| 1 | 2022 | 51414 | 51414 | 0 | 191 | False |
| 2 | 2021 | 103974 | 103974 | 0 | 191 | False |

Sizinti hali olsaydi beklenen degerler 52560 ve 105120 olurdu.
test_n_ham 52560 (her iki pencerede).
191 = 24 (shift) + 168 (roll168) - 1; 6 konum x 191 = 1146.

### Invaryant 4 -- ornekleme kod yolu (2019, K=5, dejenere hucre)

3 model x 3 tohum = 9 kontrol. Hepsinde:
bagil_fark 0.0, mutlak_fark 0.0, egitim_n 261798 (altornekleme == kaydirmali).

| model | tohum 11 | tohum 22 | tohum 33 | kaydirmali |
|---|---|---|---|---|
| Linear Regression | 141.343658 | 141.343658 | 141.343658 | 141.343658 |
| Polynomial Ridge | 136.502929 | 136.502929 | 136.502929 | 136.502929 |
| Hist Gradient Boosting | 137.168967 | 137.168967 | 137.168967 | 137.168967 |

### Invaryant 5 -- ornekleme hesap sirasi (2023, K=2, tohum 11)

Dejenere olmayan hucre.

    secilen_n              103974   (hedef_n 103974, fark 0)
    havuz_gun_konum          3280
    secilen_gun_konum         723
    gun_orani_konum        0.2204
    gun_kopuklugu_konum       560
    farkli_oznitelik            0   (29 oznitelik, hepsi birebir)
    ters_sira_farkli_oran     1.0
    ters_sira_maks_fark  168.053036 W

Son iki satir testin ayirt etme gucudur: ters sirada hesaplansaydi
P_roll168_mean_lag24 degerlerinin %100'u degisirdi.

## Kosu istatistikleri

`python run_doygunluk.py --tahmin`, 255 hucre, egitim 51414-472182 satir.

| sonda | pencere | yil | model | egitim_n | fit sn | bootstrap sn |
|---|---|---|---|---|---|---|
| kucuk | 1 | 2019 | Linear Regression | 51414 | 0.2 | 0.4 |
| kucuk | 1 | 2019 | Polynomial Ridge | 51414 | 0.6 | 0.4 |
| kucuk | 1 | 2019 | Hist Gradient Boosting | 51414 | 1.8 | 0.4 |
| buyuk | tum | 2023 | Linear Regression | 472182 | 1.6 | 0.3 |
| buyuk | tum | 2023 | Polynomial Ridge | 472182 | 4.8 | 0.4 |
| buyuk | tum | 2023 | Hist Gradient Boosting | 472182 | 7.4 | 0.4 |

Bootstrap ortalamasi 0.4 sn/hucre.
Lineer yayma: Hist Gradient Boosting 5 dk, Polynomial Ridge 3 dk,
Linear Regression 1 dk. Kaba toplam 9 dakika.

Karsilastirma: ablasyon.csv'de temiz/2023/Hist Gradient Boosting
egitim_sn = 22.0; ayni hucre bu oturumda 7.4 sn. RMSE birebir ayni
(invaryant 2). Fark thread sabitlemesine atfediliyor, dogrulanmadi.

## Thread duyarliligi olcumu

MLPRegressor(hidden_layer_sizes=(96,48), early_stopping=True, max_iter=500,
random_state=42), egitim 51414 satir x 29 oznitelik, test 2023.
n_iter_ = 141 dort kosuda da ayni.

| ortam | blas | openmp | tahmin SHA256 (ilk 32) | RMSE |
|---|---|---|---|---|
| hicbiri ayarsiz | 20 | 20 | 2f225d92439dd17d2fe4423d885693bb | 99.1842794987 |
| OMP=8 | 8 | 8 | 92eb860b64dc422d9544ad55d5f1e563 | 99.1842794987 |
| ucu de 8 | 8 | 8 | 92eb860b64dc422d9544ad55d5f1e563 | 99.1842794987 |
| ucu de 8 (tekrar) | 8 | 8 | 92eb860b64dc422d9544ad55d5f1e563 | 99.1842794987 |

Bu ortamda OMP_NUM_THREADS tek basina OpenBLAS havuzlarini da kontrol ediyor.
Thread sayisi degisince MLP ciktisi bit duzeyinde degisiyor; RMSE 10 ondalik
basamakta ayni. Agac tabanlilar ve HGB bu duyarliligi gostermedi.

Ortam: numpy 2.5.1, scikit-learn 1.9.0,
blas openblas (numpy: libscipy_openblas64_-b788215d9d47792bcba3a2e2a7114320.dll,
scipy: libscipy_openblas-197ee2fc9b4d071f7e048078cac74115.dll),
openmp vcomp140.dll (sklearn).

## Faz 3 payda hesabi

En iyi ile ikinci arasindaki mutlak RMSE farki, sonuclar/siralama_*.csv'den.
Cift her yil {Polynomial Ridge, Hist Gradient Boosting}; 2018'de yon ters.

| yil | fark W | p | anlamli |
|---|---|---|---|
| 2017 | 1.1878 | 0.1138 | hayir |
| 2018 | 0.4330 | 0.3986 | hayir |
| 2019 | 0.6660 | 0.2127 | hayir |
| 2020 | 0.4249 | 0.3142 | hayir |
| 2021 | 0.2727 | 0.4330 | hayir |
| 2022 | 0.4669 | 0.2705 | hayir |
| 2023 | 0.7895 | 0.0380 | EVET |

Medyan 7 yil (2017-2023): 0.4669
Medyan 5 yil (2019-2023): 0.4669
Dusen degerler: 2017 -> 1.1878, 2018 -> 0.4330 (biri medyanin ustunde,
biri altinda; medyan degismiyor).
Anlamli yil sayisi: 7 yilda 1, 5 yilda 1.

## Ham ozet tablolar

YOK. Izgara kosulmadi. Ozet fonksiyonlari yalnizca sentetik veriyle
(RMSE = 150 - 8*log1p(K) + N(0, 0.6)) sekil dogrulamasi gordu; o kosunun
sayilari deney sonucu DEGILDIR ve hicbir yere alinmamistir.

## Alinan kararlar ve gerekceleri

1. **10 yillik pencere uygulanmadi.** Test yili ayrildiginda geriye en fazla
   9 yil kalir. Seviyeler {1,2,3,5,"tum"}; "tum" test yiline gore 5-9 yil.

2. **Test yillari 2019-2023.** K=5 seviyesinin var olabilmesi icin test yili
   >= BASLANGIC_YIL + 5 olmali.

3. **Oznitelikler pencere DILIMLENDIKTEN SONRA uretiliyor.** Faz 2/3'te tablo
   tum veri uzerinde bir kez uretilip yila gore dilimleniyordu. Faz 4'te bu
   yanlis olurdu: isinma veri kumesinin basinda tuketilirse "1 yil veriyle
   egitildi" denen model onceki yillarin yuvarlanan istatistiklerini tasir ve
   doygunluk egrisi yapay olarak duzlesir. Dilim [pencere_basi, test_yili]
   araligini kapsar; test yili isinmadan etkilenmez, gecikmeleri gecmis
   gozlemdir. Invaryant 3 bunu pinliyor.

4. **`bolme_indeksleri` degistirilmedi.** Parametre eklemek yerine ayri kod
   yolu; Faz 2/3 sonuclarini korumanin en guvenli hali. Invaryant 2 bekcisi.

5. **Altornekleme gun duzeyinde ve konuma gore tabakali, yerine koymadan.**
   Saat duzeyinde cekim komsu saatleri neredeyse kopya yapar; esit N'de
   rastgele saat kumesi surekli pencereden yapay olarak bilgili cikardi.
   Konum tabakalamasi olmadan alti konumun payi tohumdan tohuma oynardi.

6. **Tohum yalnizca gun secimini degistirir.** Model random_state'leri SEED'de
   sabit. Ikisi birlikte oynatilirsa olculen sey ornekleme tesadufu ile model
   baslatma tesadufunun karisimi olurdu.

7. **Bootstrap tohumu butun hucrelerde SEED.** Uc ornekleme tohumunda ayni gun
   bloklari cekilir; guven araliklari dogrudan kiyaslanabilir olur.

8. **Kaydirmali kol tohum sutununa 0 yazar.** NaN yazilsaydi devam anahtarinda
   NaN != NaN yuzunden tamamlanmis hucre asla eslesmez, izgara kendini
   sonsuza kadar tekrarlardi.

9. **Ana oran altornekleme kolundan gelecek.** Kaydirmali kolda hacim ile
   guncellik ic ice: pencere buyudukce eklenen yillar hep daha eski. Saf hacim
   etkisi yalnizca yil kompozisyonunun sabit oldugu kolda olculur.

10. **Ozet fonksiyonlari izgara kosulmadan once yazildi.** Hangi tablonun
    uretilecegi sayilar gelmeden sabitlendi; aksi halde metrik secimi post-hoc
    olurdu.

11. **Yillar arasi kiyas nRMSE_kapasite, konumlar arasi nRMSE_ortalama.**
    nRMSE_ortalama'nin paydasi yila gore degisir.

12. **Varyans ayristirmasi yalnizca 3 hizli modelin alt kumesinde.** 10
    seviyeli bir faktorun araligi 5 seviyeliden yapisal olarak buyuk cikar ve
    algoritma payini sisirirdi.

13. **Invaryant toleransi 1e-6 bagil, bit duzeyi degil.** MLP thread sayisina
    bit duzeyinde duyarli (olculdu). ablasyon.csv thread sabitlemesi olmadan
    uretilmis.

14. **Basarisiz hucre diske yazilir** (durum="hata"), devam kosusunda yeniden
    denenir, ozet DISLAR. Faz 2'nin izgarasinda patlayan hucre CSV'ye hic
    yazilmiyordu; kosu "bitti" der ama eksik hucreyi soyleyen hicbir sey
    olmuyordu.

## Bilinen kusurlar ve varsayimla gecilenler

1. **Izgara kosulmadi.** Faz 4'un uretilmis tek bir deney sayisi yok.

2. **Geniş kosu (K=tum x 2019-2023 x 10 model, SVR haric) ne olculdu ne
   kosuldu.** 9 dakikalik tahmin yalnizca 3 hizli modeli kapsar. Gradient
   Boosting (tek cekirdek, tam bolme arama), K-Nearest Neighbours (29 boyutta
   KD-tree cokuyor, pratikte kaba kuvvet: ~25.8 bin test x 472 bin egitim),
   Extra Trees ve Random Forest (400 agac, min_samples_leaf=2, bellek
   baskisi), MLP olculmedi. CLAUDE.md'nin hesaplama gercekligi bolumunde
   Gradient Boosting ve KNN icin uyari YOK.

3. **Ozet fonksiyonlari gercek ciktiyla hic calismadi.** Sentetik veride
   varyans paylari toplami %100.0 cikti ve alti tablo da uretildi; gercek
   veride dengesiz tasarim veya eksik hucre farkli davranabilir.
   `varyans_ayristirmasi` dengesiz tasarimda ValueError firlatir.

4. **Altornekleme hedefi tam tutturamayabilir.** Gun bloklari tam alindigi
   icin bir sonraki gun hedefi asacaksa alinmaz; konum basina 24 satira kadar
   eksik kalabilir. Olculen iki hucrede (2019/K=5, 2023/K=2) tam isabet oldu
   (103974 == 103974). Butun hucrelerde dogrulanmadi. Gercek deger her satirda
   `egitim_n` olarak loglanir.

5. **`hedef_satir_sayisi` konumlarin satir sayisinin esit olmasini varsayar**,
   degilse ValueError firlatir. Dondurulmus veride esit (her yil her konumda
   8760/8784, yinelenen kayit yok - dogrulandi).

6. **`.gitignore` `sonuclar/tahminler/` dizinini YOL olarak dislamiyor**;
   icindeki dosyalar yalnizca global `*.parquet` kuraliyla disarida kaliyor.
   O dizine parquet olmayan bir cikti yazilirsa commit'e girer. CLAUDE.md
   kural 3 dizini yol olarak dislanmis gibi anlatiyor.

7. **CLAUDE.md'de iki bolum bayat.** `## Durum` Faz 4'u "YAPILACAK" gosteriyor;
   `## Kod` modul listesinde bes yeni dosya yok.

8. **Invaryant 2'nin referansi ablasyon.csv**, o dosya thread sabitlemesi
   olmadan uretildi. 1e-6 bagil tolerans bu farki sogurur; gozlenen en buyuk
   sapma 7.797529e-12.

9. **HGB'nin 22.0 -> 7.4 sn hizlanmasi aciklanmadi.** RMSE birebir ayni.
   Thread sabitlemesine atfedildi, olculerek dogrulanmadi.
