# Faz 4 - veri hacmi doygunlugu

Durum: TAMAM. Izgara kosuldu, genis kosu kosuldu, esli DM iki duzeyde
kosuldu, nondeterminizm olculdu.

Bu not `d469060`'daki ilk surumun yerine gecer. Eski surum altyapi
yazildiktan sonra, izgara kosulmadan once yazilmisti; "Uretilen deney sonucu:
YOK" diyordu ve o gunden bu yana refactor, ana izgara, genis kosu, iki DM
kosusu, pyarrow surum degisimi ve nondeterminizm olcumu gerceklesti.

Sadece rapor. Yorum ve makale metni burada degil.

## Faz kunyesi

    faz             : 4 (veri hacmi doygunlugu)
    HEAD (not yazilirken)
                    : 4be6a45a3bb783b57eaf152c035c0c215796c4e7
    agac            : bu not ve dogrulama kosulari commit edildikten sonra
                      temiz
    etiket          : faz-4, bu notu iceren commit'e baglanir (asagida)
    push            : YAPILMADI - Faz 2/3/4'un hicbir commit'i push edilmedi

Not kendi commit'inin hash'ini icermez; `faz-4` etiketi o commit'e baglandigi
icin `git show faz-4` ile bulunur.

Faz 4 commit'leri (19):

    13c6ee8  2026-07-31 06:05  Phase 4 scaffolding: window logic, subsampling,
                               invariant gate, summaries
    ae0f3c7  2026-07-31 06:24  Add Phase 4 grid runner and cost estimation
    2406774  2026-07-31 06:24  Add research context document and git/handover
                               conventions
    d469060  2026-07-31 06:25  Add Phase 4 handover note        [bu notun onceki surumu]
    b7e7a92  2026-08-02 00:44  Collapse the cell split into a single code path
    181d543  2026-08-02 00:51  Bind invariant 5 to the production path and give
                               it a negative control
    2de91c6  2026-08-02 00:56  Wire the summary tables into the runner and
                               correct the gate docstring
    a948ece  2026-08-02 01:06  Write the summary tables to sonuclar/ instead of
                               only printing them
    ccde501  2026-08-02 01:08  Bring CLAUDE.md up to the actual state of Phase 4
    0c8614b  2026-08-02 01:52  Add Phase 4 saturation grid results
    8b07d09  2026-08-02 01:56  Add two post-hoc summary tables in a separate
                               module
    482acf3  2026-08-02 03:50  Optionally persist each cell's prediction vector
    3d15cce  2026-08-02 03:51  Add paired Diebold-Mariano between the learning
                               curve's two ends
    8c84b11  2026-08-02 03:51  Add wide-run and paired-DM results
    566b111  2026-08-02 04:25  Test the 2022 winner change; it does not survive
                               a paired test
    74c3c62  2026-08-03 02:20  Pin pyarrow to 22.0.0 to work around Smart App
                               Control DLL block
    17681cd  2026-08-03 04:40  Test all five years; no winner beats its
                               runner-up significantly
    8bdf973  2026-08-03 04:40  Measure the RF/ET nondeterminism; close the open
                               item
    4be6a45  2026-08-03 04:49  Keep the DM and regression drivers in arac/
                               instead of scratchpad

## Degisen dosyalar

`d469060` (onceki faz notu) ile `HEAD` arasi, veri disi:

| dosya | satir | durum |
|---|---|---|
| `pv10/config.py` | +5 | `VERI_SHA16` eklendi |
| `pv10/doygunluk.py` | +64/-x | bolme tek kod yoluna toplandi, tahmin kaydi eklendi |
| `pv10/dogrulama.py` | +112/-x | invaryant 5 uretim yoluna baglandi, negatif kontrol |
| `pv10/ozet_sonrasi.py` | +430 | yeni - sonuclar goruldukten SONRA eklenen tablolar |
| `run_doygunluk.py` | +362 | ozet baglama, kunye, `--etiket`, `--tahmin-kaydet` |
| `arac/nondeterminizm.py` | +130 | yeni - teshis |
| `arac/nondeterminizm_karar.py` | +99 | yeni - teshis |
| `arac/dm_yil.py` | +145 | yeni - teshis surucusu |
| `arac/regresyon_kiyas.py` | +136 | yeni - teshis surucusu |
| `requirements.txt` | +5/-2 | pyarrow 22.0.0'a sabitlendi |
| `README.md` | +11/-2 | Reproducibility bolumu |
| `CLAUDE.md` | +167 | Durum, Kod, Calistirma bolumleri |

`pv10/ozet.py` DEGISMEDI - bkz. "On-kayit durumu".
`pv10/experiment.py`, `features.py`, `models.py`, `evaluate.py`, `ranking.py`
DEGISMEDI; Faz 2/3 kod yolu bu fazda hic ellenmedi.

`sonuclar/` altinda 25 CSV/TXT eklendi, toplam 3353 satir. Ayrinti asagida.

## Yeni ve degisen fonksiyon imzalari

    pv10/doygunluk.py
      pencere_basi(test_yil: int, pencere) -> int
      isinma_olc(ham_dilim: pd.DataFrame, o: pd.DataFrame) -> int
      class PencereOnbellegi:
          __init__(self, ham: pd.DataFrame)
          al(self, basla: int, test_yil: int)
          ham(self) -> pd.DataFrame
      egitim_test_bolme(onbellek: PencereOnbellegi, kol: str, pencere,
                        test_yil: int, tohum: int) -> tuple          [YENI]
      tahmin_dosyasi(dizin: Path, kol: str, pencere, test_yil: int,
                     model_ad: str, tohum: int) -> Path              [YENI]
      hucre_kos(onbellek: PencereOnbellegi, kol: str, pencere, test_yil: int,
                model_ad: str, tohum: int, bootstrap: bool = True,
                tahmin_dizin: Path | None = None) -> tuple[dict, list[dict]]
      izgara_hucreleri(kollar, pencereler, yillar, model_adlari, tohumlar)
      _tamamlananlar(log_yolu) -> set[tuple]
      izgara_kos(ham: pd.DataFrame, kollar, pencereler, yillar, model_adlari,
                 tohumlar, log_yolu, konum_log_yolu, bootstrap: bool = True,
                 ilerleme=print, tahmin_dizin: Path | None = None)
                 -> pd.DataFrame

    pv10/ozet_sonrasi.py                                            [YENI MODUL]
      DM_KUMELENME_BIRIMI = "time_utc (zaman damgasi); alti konum ayni damgada"
      _pencere_sirala(d: pd.DataFrame, sutun: str = "pencere") -> pd.DataFrame
      algoritma_span(d: pd.DataFrame, kol: str = "kaydirmali") -> pd.DataFrame
      ga_uclari(d: pd.DataFrame) -> pd.DataFrame
      _tahmin_oku(dizin: Path, kol: str, pencere, test_yil: int,
                  model_ad: str, tohum: int) -> pd.DataFrame
      uc_dm(tahmin_dizin, test_yillari, model_adlari, tohumlar,
            bootstrap: bool = True) -> pd.DataFrame
      yil_ici_dm(tahmin_dizin, test_yil: int, model_ciftleri,
                 kol: str = "kaydirmali", pencere="tum",
                 tohum: int = KAYDIRMALI_TOHUM,
                 bootstrap: bool = True) -> pd.DataFrame
      duzeltilmis_ana_tablo(dm: pd.DataFrame, genis: pd.DataFrame,
                            varyans: pd.DataFrame,
                            yil_dm: pd.DataFrame | None = None) -> pd.DataFrame

    run_doygunluk.py
      thread_durumu() -> str
      dogrula(ham: pd.DataFrame) -> bool
      tahmin_et(ham, kollar, pencereler, yillar, model_adlari, tohumlar) -> None
      _baslik(s: str) -> None                                        [YENI]
      veri_hash() -> str                                             [YENI]
      ozetle(kollar, pencereler, yillar, model_adlari, tohumlar) -> None  [YENI]
      _kunye_yaz(n_tamam, n_beklenen, eksik, hatali, e4, varyans_attrs,
                 yazilan, atlanan) -> None                           [YENI]
      main()

    arac/nondeterminizm.py       sha(a) -> str ; main() -> int
    arac/nondeterminizm_karar.py karar(a_farkli: bool, b_farkli: bool) -> str
                                 main() -> int
    arac/dm_yil.py               main() -> int
    arac/regresyon_kiyas.py      main() -> int

`pv10/ozet.py` imzalari `d469060`'daki gibi, degismedi.

## Config sabitleri

    EGITIM_PENCERELERI      = (1, 2, 3, 5, "tum")
    DOYGUNLUK_TEST_YILLARI  = (2019, 2020, 2021, 2022, 2023)
    DOYGUNLUK_KOLLARI       = ("kaydirmali", "altornekleme")
    ORNEKLEME_TOHUMLARI     = (11, 22, 33)
    KAYDIRMALI_TOHUM        = 0
    GENIS_KOSU_HARIC        = ("Support Vector Regression",)
    OMP_THREAD_SAYISI       = 8
    INVARYANT_TOLERANS      = 1e-6
    VERI_SHA16              = "f722a717bac502c2"          [Faz 4'te eklendi]

Degismeyen: SEED = 42, BASLANGIC_YIL = 2014, BITIS_YIL = 2023,
KAPASITE_W = 1000.0, UFUK = 24, GECIKMELER = (24, 48, 168).

## run_doygunluk.py bayraklari

    --dogrula          invaryant kapisi (5 invaryant / 18 kontrol)
    --tahmin           hucre maliyeti, izgara kosmadan
    --ozet             mevcut CSV'lerden ozet, izgara kosmadan
    --modeller         hizli | tumu   (varsayilan hizli = 3 model)
    --pencere          pencere listesini kisitla (varsayilan hepsi)
    --etiket           ayri log dosyasi -> doygunluk_<etiket>.csv; ozet URETILMEZ
    --yillar           varsayilan DOYGUNLUK_TEST_YILLARI
    --kol              varsayilan iki kol
    --hizli-bootstrap  bootstrap tekrar sayisini dusurur
    --tahmin-kaydet    her hucrenin gunduz tahmin vektorunu diske yaz

## Uretilen cikti dosyalari ve semalari

### Izgara loglari

`sonuclar/doygunluk.csv` -- ana izgara, 255 satir

    kol, pencere, test_yil, model, tohum, egitim_basla, egitim_n, isinma,
    durum, hata, MAE, RMSE, nRMSE_ortalama, nRMSE_kapasite, R2, n,
    RMSE_persistence, skill, RMSE_GA_alt, RMSE_GA_ust, egitim_sn, bootstrap_sn

    devam anahtari: (kol, pencere, test_yil, model, tohum)
    durum in {"tamam", "hata"}; yalnizca "tamam" tamamlanmis sayilir

`sonuclar/doygunluk_konum.csv` -- konum kirilimi, 1530 satir

    kol, pencere, test_yil, model, tohum, konum, n, MAE, RMSE,
    nRMSE_ortalama, nRMSE_kapasite

Ayni sema ile uretilen etiketli loglar:

| dosya | hucre | icerik |
|---|---|---|
| `doygunluk_genis.csv` | 50 | K=tum x 5 yil x 10 model, kaydirmali |
| `doygunluk_dm2022.csv` | 10 | K=tum x 2022 x 10 model, tahmin kaydiyla |
| `doygunluk_dm_kalan.csv` | 40 | K=tum x 2019/2020/2021/2023 x 10 model, tahmin kaydiyla |
| `doygunluk_genis_konum.csv` | 300 | konum kirilimi |
| `doygunluk_dm2022_konum.csv` | 60 | konum kirilimi |
| `doygunluk_dm_kalan_konum.csv` | 240 | konum kirilimi |

### Ozet tablolari

| dosya | satir | kaynak modul | kayit |
|---|---|---|---|
| `doygunluk_ozet_egri.csv` | 10 | `ozet.py` | ON-KAYITLI |
| `doygunluk_ozet_marjinal.csv` | 8 | `ozet.py` | ON-KAYITLI |
| `doygunluk_ozet_hacim_orani.csv` | 3 | `ozet.py` | ON-KAYITLI (YANLIS, bkz. karar 1) |
| `doygunluk_ozet_tohum_yayilimi.csv` | 60 | `ozet.py` | ON-KAYITLI |
| `doygunluk_ozet_model_pencere.csv` | 5 | `ozet.py` | ON-KAYITLI |
| `doygunluk_ozet_model_pencere_yil.csv` | 25 | `ozet.py` | ON-KAYITLI |
| `doygunluk_ozet_varyans.csv` | 7 | `ozet.py` | ON-KAYITLI |
| `doygunluk_ozet_konum.csv` | 6 | `ozet.py` | ON-KAYITLI |
| `doygunluk_ozet_algoritma_span.csv` | 10 | `ozet_sonrasi.py` | SONRADAN |
| `doygunluk_ozet_ga.csv` | 46 | `ozet_sonrasi.py` | SONRADAN |
| `doygunluk_ozet_duzeltilmis.csv` | 17 | `ozet_sonrasi.py` | SONRADAN |
| `doygunluk_ozet_dm.csv` | 45 | `ozet_sonrasi.py` | SONRADAN |
| `doygunluk_ozet_dm_yil.csv` | 15 | `ozet_sonrasi.py` | SONRADAN |
| `doygunluk_ozet_kunye.txt` | - | `run_doygunluk.py` | - |
| `nondeterminizm_olcum.csv` | 12 | `arac/nondeterminizm.py` | teshis |
| `nondeterminizm_olcum_dogrulama.csv` | 12 | `arac/nondeterminizm.py` | teshis, dogrulama |
| `doygunluk_ozet_dm_yil_dogrulama.csv` | 15 | `arac/dm_yil.py` | teshis, dogrulama |

Dogrulama CSV'leri ASLA ana tablolarin yerine gecmez; kiyas icin duruyorlar.
Ana tablo her zaman `_dogrulama` soneki OLMAYAN dosyadir.

DM tablolarinin semasi:

    test_yil, model[_a/_b], tohum, RMSE_*, RMSE_fark_W,
    RMSE_fark_kapasite_yuzde, RMSE_fark_bagil_yuzde, DM, p, anlamli,
    n_ham, n_kume, kumelenme, fark_GA_alt, fark_GA_ust, GA_sifiri_iceriyor

`doygunluk_ozet_dm_yil.csv` ek olarak: `kaynak_dizin`, `en_iyi`, `ikinci`,
`kazanan_ikinci_cifti`, `dipnot`.

### Diske yazilan ama commit EDILMEYEN

`sonuclar/tahminler/doygunluk/<etiket>/` altinda hucre basina bir parquet
(`y`, `tahmin`, `persistence`, `konum`, `time_utc`). `.gitignore` kapsaminda.
`--tahmin-kaydet` olmadan uretilir ama yazilmaz; o durumda esli DM SONRADAN
hesaplanamaz.

## Kapi / invaryant sonuclari

Kosu: `python run_doygunluk.py --dogrula`. **18/18 kontrol GECTI**, ~1,2 dakika.
Ortam: OMP/OPENBLAS/MKL_NUM_THREADS = 8.

Kapi iki kez kosuldu: pyarrow 25.0.0 ile (izgara oncesi) ve 22.0.0 ile
(surum degisiminden sonra). Iki kosuda da 18/18 ve invaryant 1-2'nin bagil
farklari son basamagina kadar AYNI.

### Invaryant 1 -- pencere esdegerligi (2019)

Beklenen: K=5 == K=tum == `ablasyon.csv` temiz/2019; `egitim_n` 261798.

| model | K=5 | K=tum | referans | bagil fark (ikili) | bagil fark (ref) |
|---|---|---|---|---|---|
| Linear Regression | 141.343658 | 141.343658 | 141.343658 | 0.0 | 0.0 |
| Polynomial Ridge | 136.502929 | 136.502929 | 136.502929 | 0.0 | 6.050675e-13 |
| Hist Gradient Boosting | 137.168967 | 137.168967 | 137.168967 | 0.0 | 0.0 |

`egitim_n` gozlenen 261798, beklenen 261798, fark 0.

### Invaryant 2 -- Faz 2 uyumlulugu (2023, K=tum)

| model | yeni | referans | bagil fark | mutlak fark |
|---|---|---|---|---|
| Linear Regression | 137.839921 | 137.839921 | 0.0 | 0.0 |
| Polynomial Ridge | 132.614714 | 132.614714 | 7.797529e-12 | 1.034067e-09 |
| Hist Gradient Boosting | 133.404201 | 133.404201 | 0.0 | 0.0 |

`egitim_n` 472182 == beklenen. `test_n` 25792 == beklenen.
Tolerans 1e-6 bagil; gozlenen en buyuk sapma 7.797529e-12.

### Invaryant 3 -- isinma siniri (2023)

| pencere | egitim_basla | egitim_n gozlenen | beklenen | fark | isinma | sinir_siziyor |
|---|---|---|---|---|---|---|
| 1 | 2022 | 51414 | 51414 | 0 | 191 | False |
| 2 | 2021 | 103974 | 103974 | 0 | 191 | False |

Sizinti hali olsaydi 52560 ve 105120 beklenirdi. `test_n_ham` 52560.
191 = 24 (shift) + 168 (roll168) - 1; 6 konum x 191 = 1146.

### Invaryant 4 -- ornekleme kod yolu (2019, K=5, dejenere hucre)

3 model x 3 tohum = 9 kontrol; hepsinde bagil_fark 0.0, mutlak_fark 0.0,
`egitim_n` 261798 (altornekleme == kaydirmali).

| model | tohum 11 | tohum 22 | tohum 33 | kaydirmali |
|---|---|---|---|---|
| Linear Regression | 141.343658 | 141.343658 | 141.343658 | 141.343658 |
| Polynomial Ridge | 136.502929 | 136.502929 | 136.502929 | 136.502929 |
| Hist Gradient Boosting | 137.168967 | 137.168967 | 137.168967 | 137.168967 |

### Invaryant 5 -- ornekleme hesap sirasi (2023, K=2, tohum 11)

Dejenere OLMAYAN hucre. `181d543` ile uretim yoluna baglandi.

    secilen_n              103974   (hedef_n 103974, fark 0)
    havuz_gun_konum          3280
    secilen_gun_konum         723
    gun_orani_konum        0.2204
    gun_kopuklugu_konum       560
    farkli_oznitelik            0   (29 oznitelik, hepsi birebir)
    ters_sira_farkli_oran     1.0
    ters_sira_maks_fark  168.053036 W

Son iki satir NEGATIF KONTROLDUR ve testin ayirt etme gucudur: oznitelikler
ters sirada (once altornekleme, sonra oznitelik) hesaplansaydi
`P_roll168_mean_lag24` degerlerinin %100'u degisir, en buyuk fark 168,053036 W
olurdu. Bu satirlar olmadan invaryant tautolojiydi - bkz. karar 8.

## Kosu istatistikleri

| kosu | hucre | durum | duvar saati (egitim+bootstrap) | pyarrow |
|---|---|---|---|---|
| ana izgara | 255/255 | 255 tamam, 0 hata | 9,5 dk (log toplami) / 11,0 dk (duvar) | 25.0.0 |
| genis kosu | 50/50 | 50 tamam, 0 hata | 81,0 dk (log) / 81,2 dk (duvar) | 25.0.0 |
| 2022 dogrulama | 10/10 | 10 tamam, 0 hata | 19,6 dk | 25.0.0 |
| kalan dort yil | 40/40 | 40 tamam, 0 hata | 96,3 dk (log) / 96,5 dk (duvar) | 22.0.0 |
| invaryant kapisi | 18/18 kontrol | hepsi gecti | 1,2 dk | 25.0.0 ve 22.0.0 |

Ana izgara boyutu 255 hucre:

    kaydirmali   {1,2,3,5,tum} x 5 yil x 3 model x 1 tohum =  75
    altornekleme {1,2,3,5}     x 5 yil x 3 model x 3 tohum = 180

Altornekleme K=tum URETILMEZ; kaydirmali K=tum hucresiyle ayni hucredir
(`doygunluk_ozet_egri.csv`'de `paylasilan=True`).

`egitim_n` araligi 51414 - 472182. Test seti buyuklukleri (gunduz filtresi
sonrasi): 2019 25776, 2020 25887, 2021 25798, 2022 25774, 2023 25792.

### Ana izgara, model basina

| model | hucre | egitim sn | bootstrap sn | toplam dk |
|---|---|---|---|---|
| Hist Gradient Boosting | 85 | 290,7 | 35,0 | 5,428333 |
| Polynomial Ridge | 85 | 136,2 | 34,4 | 2,843333 |
| Linear Regression | 85 | 42,3 | 34,3 | 1,276667 |

### Genis kosu (K=tum x 5 yil), model basina

| model | hucre | egitim sn | bootstrap sn | toplam dk |
|---|---|---|---|---|
| Gradient Boosting | 5 | 2323,2 | 2,0 | 38,753333 |
| Random Forest | 5 | 1357,9 | 2,3 | 22,670000 |
| Extra Trees | 5 | 478,0 | 2,0 | 8,000000 |
| Neural Network | 5 | 461,3 | 2,0 | 7,721667 |
| K-Nearest Neighbours | 5 | 105,6 | 2,1 | 1,795000 |
| Decision Tree | 5 | 39,4 | 2,0 | 0,690000 |
| Hist Gradient Boosting | 5 | 33,5 | 2,2 | 0,595000 |
| Polynomial Ridge | 5 | 18,4 | 2,1 | 0,341667 |
| SGD Regression | 5 | 15,7 | 2,0 | 0,295000 |
| Linear Regression | 5 | 5,9 | 2,0 | 0,131667 |

Gradient Boosting ve Random Forest butun kosunun %76'sini yiyor. SVR
`GENIS_KOSU_HARIC` ile disarida - O(n^2) kernel, denenmedi.

### Kalan dort yil kosusu (40 hucre), model basina

| model | hucre | egitim sn | bootstrap sn | toplam dk |
|---|---|---|---|---|
| Gradient Boosting | 4 | 2370,1 | 2,0 | 39,535000 |
| Random Forest | 4 | 1575,3 | 2,8 | 26,301667 |
| Neural Network | 4 | 971,8 | 2,2 | 16,233333 |
| Extra Trees | 4 | 590,0 | 2,3 | 9,871667 |
| K-Nearest Neighbours | 4 | 113,5 | 2,7 | 1,936667 |
| Decision Tree | 4 | 48,2 | 2,7 | 0,848333 |
| Hist Gradient Boosting | 4 | 31,5 | 2,2 | 0,561667 |
| Polynomial Ridge | 4 | 22,3 | 2,9 | 0,420000 |
| SGD Regression | 4 | 20,5 | 2,9 | 0,390000 |
| Linear Regression | 4 | 7,9 | 2,9 | 0,180000 |

## Regresyon kanitlanmasi: kalan dort yil vs genis kosu

`python -m arac.regresyon_kiyas` (varsayilanlar: referans
`doygunluk_genis.csv`, yeni `doygunluk_dm_kalan.csv`).

Ayni 40 hucre iki kez kosuldu: bir kez genis kosuda (pyarrow 25.0.0, tahmin
kaydi yok), bir kez `dm_kalan` etiketiyle (pyarrow 22.0.0, `--tahmin-kaydet`).
Kiyas TOLERANSSIZ - `==`, "yaklasik esit" degil.

    hucre       : 40
    kiyaslanan  : 13 alan -> 520 karsilastirma
    birebir     : 510
    farkli      : 10   (beklenen nondet 10, BEKLENMEYEN 0)

Kiyaslanan alanlar: `egitim_n`, `n`, `RMSE`, `MAE`, `R2`, `nRMSE_kapasite`,
`nRMSE_ortalama`, `skill`, `isinma`, `egitim_basla`, `RMSE_persistence`,
`RMSE_GA_alt`, `RMSE_GA_ust`.

Farkli cikan 10 alanin tamami:

| alan | yil | model | referans | yeni | fark | bagil |
|---|---|---|---|---|---|---|
| RMSE | 2020 | Random Forest | 138.71018130192496 | 138.71018130192493 | -2.842171e-14 | -2.049e-16 |
| MAE | 2020 | Extra Trees | 91.154269072233802 | 91.154269072233816 | 1.421085e-14 | 1.559e-16 |
| MAE | 2021 | Extra Trees | 91.076574059051737 | 91.076574059051723 | -1.421085e-14 | -1.560e-16 |
| R2 | 2019 | Extra Trees | 0.72683760267952213 | 0.72683760267952202 | -1.110223e-16 | -1.527e-16 |
| nRMSE_kapasite | 2020 | Random Forest | 13.871018130192496 | 13.871018130192493 | -3.552714e-15 | -2.561e-16 |
| nRMSE_ortalama | 2020 | Random Forest | 38.966968883756692 | 38.966968883756685 | -7.105427e-15 | -1.823e-16 |
| skill | 2020 | Random Forest | 19.932346077995252 | 19.932346077995280 | 2.842171e-14 | 1.426e-15 |
| RMSE_GA_alt | 2020 | Extra Trees | 134.08554705430734 | 134.08554705430737 | 2.842171e-14 | 2.120e-16 |
| RMSE_GA_alt | 2023 | Random Forest | 130.27692554521454 | 130.27692554521451 | -2.842171e-14 | -2.182e-16 |
| RMSE_GA_ust | 2019 | Random Forest | 143.43089346302574 | 143.43089346302571 | -2.842171e-14 | -1.982e-16 |

Hepsi 1-2 ULP, hepsi yalnizca Random Forest ve Extra Trees'te. Sekiz model
(Decision Tree, Gradient Boosting, Hist Gradient Boosting, K-Nearest
Neighbours, Linear Regression, Neural Network, Polynomial Ridge, SGD
Regression) 13 alanin 13'unde de TAM ESIT. `egitim_n`, `n`, `isinma`,
`egitim_basla`, `RMSE_persistence` her hucrede tam esit.

`[sonradan eklendi - 17 Ekim 2026]` "Hepsi 1-2 ULP" eksik: bagil fark 1,5e-15'in altinda: dogrudan hesaplanan metriklerde 1-2 ULP, turetilmis `skill` alaninda 8 ULP'ye kadar (Random Forest 2020: 19.932346077995252 -> 19.932346077995280, bagil 1,43e-15). Tablodaki `skill` satirinin farki (2.842171e-14) o degerde 8 ULP'dir; `nRMSE_kapasite` 2 ULP, kalan sekiz alan 1 ULP.

Bu, pyarrow surum degisiminin metrikleri kimildatmadiginin kanitidir: surum
degisseydi butun modeller etkilenirdi, sekiz model bit duzeyinde ayni cikmazdi.

### 2022 dogrulama kosusu vs genis kosu `[sonradan eklendi - 17 Ekim 2026]`

Bu oturumda kaydi tutulan "99/100 alan birebir" sayisi 10 alan uzerindendi
(yukaridaki listeden `RMSE_persistence`, `RMSE_GA_alt`, `RMSE_GA_ust`
haric; kaydedilmemis bir oturum betigiyle). 13 alanla 127/130 (2 fark
Extra Trees guven araligi sinirlarinda, ~1 ULP, bilinen nondeterminizm).
Yeniden kiyas: `arac/regresyon_kiyas.py`, round_trip okuma, negatif kontrol
gecti; kayit `sonuclar/regresyon_kiyas_dogrulama.csv`.

| alan | yil | model | referans | yeni | fark | bagil |
|---|---|---|---|---|---|---|
| R2 | 2022 | Extra Trees | 0.71267991754062854 | 0.71267991754062843 | -1.110223e-16 | -1.558e-16 |
| RMSE_GA_alt | 2022 | Extra Trees | 136.34379624860702 | 136.34379624860705 | 2.842171e-14 | 2.085e-16 |
| RMSE_GA_ust | 2022 | Extra Trees | 145.38181363957437 | 145.3818136395744 | 2.842171e-14 | 1.955e-16 |

Beklenmeyen fark 0; dokuz model 13 alanin 13'unde tam esit.

## Nondeterminizm olcumu

Sorun: yukaridaki 10 alan. Iki aday - surec ici paralel hesap, ya da pyarrow
surum degisimi.

**Yorum kurali sonuc GORULMEDEN sabitlendi** (`arac/nondeterminizm_karar.py`
docstring'i ve `karar()` fonksiyonu):

    A'da fark VAR          -> surec ICI nondeterminizm; acik madde kapanir,
                              sebep paralel hesap
    A ayni, B'de fark VAR  -> SUREC duzeyi (thread/havuz atamasi); kapanir,
                              pyarrow degil
    A ve B ayni            -> supheyi pyarrow'a KAYDIRAMAYIZ, cunku 25.0.0'a
                              donulemiyor (SAC blogu). ACIK MADDE kalir ve
                              "olculemedi" diye yazilir - tahmin yurutulmez

Duzenek: ayni hucre (kaydirmali, K=tum, 2020, tohum 0), uc model, iki duzey.
A = ayni surecte pes pese iki tekrar; B = ayri iki surec (`--surec p1/p2`).
Hash'lenen sey METRIK DEGIL TAHMIN VEKTORU - metrik yuvarlamasi farki
yutabiliyor.

Neural Network KONTROL TANIGI olarak eklendi: duzenegin fark yakalayabildigini
degil, YAPAY fark URETMEDIGINI gostermek icin.

### Ilk olcum - `sonuclar/nondeterminizm_olcum.csv` (12 satir)

| model | surec | tekrar | tahmin_sha (ilk 16) | RMSE |
|---|---|---|---|---|
| Random Forest | p1 | 1 | 6d6bd8070e24a55a | 138.71018130192496 |
| Random Forest | p1 | 2 | c22fd98ec2f04474 | 138.71018130192496 |
| Random Forest | p2 | 1 | 363eb6e9d1b1c45f | 138.71018130192496 |
| Random Forest | p2 | 2 | de5b90e619be3957 | 138.71018130192496 |
| Extra Trees | p1 | 1 | 6e227f4f7212a9c7 | 138.27351833010343 |
| Extra Trees | p1 | 2 | 9c6d7defecc70540 | 138.27351833010343 |
| Extra Trees | p2 | 1 | c646d9e1571bf25c | 138.27351833010343 |
| Extra Trees | p2 | 2 | 08ca728dd6fde409 | 138.27351833010343 |
| Neural Network | p1 | 1 | 52016056fdc69ba8 | 136.52628249309137 |
| Neural Network | p1 | 2 | 52016056fdc69ba8 | 136.52628249309137 |
| Neural Network | p2 | 1 | 52016056fdc69ba8 | 136.52628249309137 |
| Neural Network | p2 | 2 | 52016056fdc69ba8 | 136.52628249309137 |

`y_sha` on iki satirin hepsinde `a45d9203377d0c82...`, `pers_sha` hepsinde
`cdb1d84a9c94032b...` - tek deger. Fark modelde, veride DEGIL.
`egitim_n` on iki satirda da 314358.

**Karar: A duzeyi kesti, B'ye gerek kalmadi.** RF ve ET'de dort kosunun dordu
de FARKLI tahmin hash'i verdi -> surec ICI nondeterminizm, sebep paralel
hesap (agac toplama sirasi), pyarrow DEGIL. Kontrol tanigi Neural Network
dort kosuda da AYNI hash'i verdi; duzenek yapay fark uretmiyor.

Sapma TAHMIN VEKTORUNDE her zaman var, METRIGE ancak bazen yansiyor: dort RF
kosusunun RMSE'si de 138.71018130192496 ciktigi halde ayni hucrenin genis
izgaradaki degeri 1 ULP asagidaydi (138.71018130192493). 40 hucrede yalnizca
10 alanin oynamasinin sebebi budur - hucre sayisi degil, yuvarlamanin nereye
dustugu.

### Dogrulama kosusu - `sonuclar/nondeterminizm_olcum_dogrulama.csv`

Ilk olcum scratchpad'deki tek kullanimlik betikle yapilmisti; `arac/` altindaki
surum olcumden SONRA yazilip mevcut CSV'ye baglanmisti. Bu bosluk bu kosuyla
kapatildi: betik REPODAKI haliyle, iki surec sirayla kosuldu.

    python -m arac.nondeterminizm --surec d1 --cikti sonuclar/nondeterminizm_olcum_dogrulama.csv
    python -m arac.nondeterminizm --surec d2 --cikti sonuclar/nondeterminizm_olcum_dogrulama.csv
    python -m arac.nondeterminizm_karar --olcum sonuclar/nondeterminizm_olcum_dogrulama.csv

Tarih 4 Agustos 2026, pyarrow 22.0.0, OMP_NUM_THREADS=8, pid 15216 / 13076.
Cikti AYRI dosyaya yazildi; ilk olcumun CSV'si EZILMEDI. `--cikti` bayragi bu
kosu icin eklendi (varsayilan yol degismedi, olcum mantigina dokunulmadi) -
betik CSV'ye EKLEDIGI icin ayni dosyaya yazsaydi ilk olcumun kaydi kirlenirdi.

| model | surec | tekrar | sure (sn) | tahmin_sha (ilk 16) | RMSE |
|---|---|---|---|---|---|
| Random Forest | d1 | 1 | 243.7 | ffbffedb253d4dc5 | 138.71018130192496 |
| Random Forest | d1 | 2 | 240.5 | 1c0c76f3591d1c9a | 138.71018130192496 |
| Random Forest | d2 | 1 | 229.7 | eb7cd1e0ab3cfc31 | 138.71018130192496 |
| Random Forest | d2 | 2 | 237.2 | 81ab752b1282b789 | 138.71018130192496 |
| Extra Trees | d1 | 1 | 82.9 | 32631a18886df683 | 138.27351833010343 |
| Extra Trees | d1 | 2 | 84.7 | 79907a3959c1b7d4 | 138.27351833010343 |
| Extra Trees | d2 | 1 | 82.3 | 8d210ba6b39fdd1e | 138.27351833010343 |
| Extra Trees | d2 | 2 | 81.8 | 8d661076037b4f66 | 138.27351833010343 |
| Neural Network | d1 | 1 | 91.5 | 52016056fdc69ba8 | 136.52628249309137 |
| Neural Network | d1 | 2 | 78.9 | 52016056fdc69ba8 | 136.52628249309137 |
| Neural Network | d2 | 1 | 80.5 | 52016056fdc69ba8 | 136.52628249309137 |
| Neural Network | d2 | 2 | 77.2 | 52016056fdc69ba8 | 136.52628249309137 |

Karar duzeyi kiyas - **ucu de tuttu**:

| model | kosu | A farkli | B farkli | farkli sha |
|---|---|---|---|---|
| Random Forest | ilk | True | True | 4/4 |
| Random Forest | dogrulama | True | True | 4/4 |
| Extra Trees | ilk | True | True | 4/4 |
| Extra Trees | dogrulama | True | True | 4/4 |
| Neural Network | ilk | False | False | 1/4 |
| Neural Network | dogrulama | False | False | 1/4 |

Karar metni iki kosuda kelimesi kelimesine ayni cikti: "A'da fark VAR ->
surec ICI nondeterminizm. Acik madde KAPANIR; sebep paralel hesap, pyarrow
degil." Kontrol tanigi iki kosuda da gecti; cikis kodu 0.

Kiyas HASH duzeyinde degil KARAR duzeyinde yapildi - beklenen buydu.
Hash'lerin tekrarlanmamasi olcumun konusunun kendisi:

    Random Forest    ilk 4 hash, dogrulama 4 hash, ORTAK 0  -> 8 kosu 8 farkli hash
    Extra Trees      ilk 4 hash, dogrulama 4 hash, ORTAK 0  -> 8 kosu 8 farkli hash
    Neural Network   ilk 1 hash, dogrulama 1 hash, ORTAK 1  -> 8 kosu TEK hash

Kontrol taniginin gucu tam burada: Neural Network'un hash'i
(`52016056fdc69ba8bf4f6d826f58ae5bb82faccf05e7ac498097987851ba902f`) iki
olcum arasinda, ayri gunlerde, dort ayri surecte ve sekiz kosuda AYNI cikti.
Yani duzenek surecten surece, gunden gune fark uretmiyor; RF/ET'nin 8/8
farkli hash'i gercek.

Metrik duzeyinde ise ucu de sekiz kosuda AYNI RMSE'yi verdi
(RF 138.71018130192496, ET 138.27351833010343, NN 136.52628249309137) -
sapmanin metrige ancak bazen yansimasi burada da gorunuyor.

Yirmi dort satirin hepsinde `y_sha` ve `pers_sha` tek deger, `egitim_n`
314358. Fark modelde, veride degil.

## Ham ozet tablolar

### 1. Ogrenme egrisi -- `doygunluk_ozet_egri.csv` [ON-KAYITLI]

Tohumlar uzerinde ortalanmis, 15 hucre/satir.

| kol | pencere | RMSE (W) | nRMSE_kapasite (%) | egitim_n | paylasilan |
|---|---|---|---|---|---|
| altornekleme | 1 | 140.350649166 | 14.0350649166 | 51442.8 | False |
| altornekleme | 2 | 139.274949064 | 13.9274949064 | 104031.6 | False |
| altornekleme | 3 | 138.712225682 | 13.8712225682 | 156649.2 | False |
| altornekleme | 5 | 138.358034799 | 13.8358034799 | 261826.8 | False |
| altornekleme | tum | 138.14568071 | 13.814568071 | 367004.4 | True |
| kaydirmali | 1 | 141.472199115 | 14.1472199115 | 51442.8 | False |
| kaydirmali | 2 | 139.668547086 | 13.9668547086 | 104031.6 | False |
| kaydirmali | 3 | 138.877082879 | 13.8877082879 | 156649.2 | False |
| kaydirmali | 5 | 138.376483047 | 13.8376483047 | 261826.8 | False |
| kaydirmali | tum | 138.14568071 | 13.814568071 | 367004.4 | False |

### 2. Marjinal kazanc -- `doygunluk_ozet_marjinal.csv` [ON-KAYITLI]

| kol | gecis | RMSE kazanc (W) | kumulatif (W) |
|---|---|---|---|
| altornekleme | 1 -> 2 | 1.07570010243 | 1.07570010243 |
| altornekleme | 2 -> 3 | 0.562723381705 | 1.63842348414 |
| altornekleme | 3 -> 5 | 0.354190883278 | 1.99261436742 |
| altornekleme | 5 -> tum | 0.212354089006 | 2.20496845642 |
| kaydirmali | 1 -> 2 | 1.80365202908 | 1.80365202908 |
| kaydirmali | 2 -> 3 | 0.79146420668 | 2.59511623576 |
| kaydirmali | 3 -> 5 | 0.500599832096 | 3.09571606786 |
| kaydirmali | 5 -> tum | 0.230802337438 | 3.3265184053 |

Egri doyuyor: her adimda kazanc bir onceki adimin yaklasik yarisi.

### 3. Hacim orani -- `doygunluk_ozet_hacim_orani.csv` [ON-KAYITLI, YANLIS]

Tablo kayit icin yerinde birakildi; `oran_algoritma_farkina` sutunu
KULLANILMAZ. Gerekce karar 1'de.

| etki | RMSE_fark_W | makaleye_giren | Faz3_medyan_W | oran (KULLANILMAZ) |
|---|---|---|---|---|
| saf hacim (altornekleme, K=1 -> tum) | 2.20496845642 | True | 0.4669 | 4.72257112106 |
| uygulamali hacim (kaydirmali, K=1 -> tum) | 3.3265184053 | False | 0.4669 | 7.12469137995 |
| guncellik / yil cesitliligi (fark) | 1.12154994888 | False | 0.4669 | 2.40212025889 |

### 4. Varyans ayristirmasi -- `doygunluk_ozet_varyans.csv` [ON-KAYITLI]

Uc faktorlu kare toplami, kaydirmali kol, 3 hizli model, deger
`nRMSE_kapasite`.

| kaynak | kare toplami | varyans payi (%) |
|---|---|---|
| test_yil (yil) | 3.43747047784 | 48.4868371067 |
| model (algoritma) | 1.78775995708 | 25.2170386286 |
| pencere (veri hacmi) | 1.08272273123 | 15.2722186385 |
| pencere x model | 0.688924589358 | 9.7175450839 |
| artik (uclu etkilesim) | 0.0373067877828 | 0.526226524376 |
| model x test_yil | 0.0353894563419 | 0.499181830362 |
| pencere x test_yil | 0.0199180830928 | 0.280952187553 |

### 5. Model x pencere -- `doygunluk_ozet_model_pencere.csv` [ON-KAYITLI]

3 hizli model, kaydirmali kol. Kazanan pencere degisince DEGISMIYOR.

| pencere | kazanan | ikinci | kazanan RMSE | ikinci RMSE | ilk-iki fark (W) |
|---|---|---|---|---|---|
| 1 | Polynomial Ridge | Linear Regression | 139.410945077 | 141.327885941 | 1.91694086401 |
| 2 | Polynomial Ridge | Hist Gradient Boosting | 137.52431025 | 140.309870834 | 2.78556058441 |
| 3 | Polynomial Ridge | Hist Gradient Boosting | 136.945876004 | 138.585914977 | 1.64003897354 |
| 5 | Polynomial Ridge | Hist Gradient Boosting | 136.560665924 | 137.49981682 | 0.939150896054 |
| tum | Polynomial Ridge | Hist Gradient Boosting | 136.415915435 | 136.939917088 | 0.52400165356 |

25 (pencere x yil) hucrenin 25'inde de kazanan Polynomial Ridge
(`doygunluk_ozet_model_pencere_yil.csv`). Ilk-iki farki 0.272656091192 W ile
3.33035639968 W arasinda.

### 6. Konum kirilimi -- `doygunluk_ozet_konum.csv` [ON-KAYITLI]

nRMSE_ortalama (%), kaydirmali kol, tohum/model ortalamasi.

| konum | K=1 | K=2 | K=3 | K=5 | K=tum |
|---|---|---|---|---|---|
| adana | 38.3314537801 | 37.8497881489 | 37.674693908 | 37.5484759764 | 37.4967664778 |
| braila | 51.486608219 | 50.9022130375 | 50.5945727372 | 50.4554396954 | 50.4208749526 |
| konya | 41.1875550355 | 40.7575660282 | 40.5029148329 | 40.3685535422 | 40.2876058724 |
| leipzig | 63.8539991198 | 62.9069958815 | 62.499341069 | 62.3183851198 | 62.1846921594 |
| ouarzazate | 24.9057102365 | 24.4672704993 | 24.3179797209 | 24.2160075243 | 24.1792010607 |
| portimao | 32.2299744792 | 31.8509992888 | 31.7240096235 | 31.5198444502 | 31.4417247846 |

Siralama hicbir pencerede degismiyor; hacim artisi alti konumun hepsinde
ayni yonde.

### 7. Tohum yayilimi -- `doygunluk_ozet_tohum_yayilimi.csv` [ON-KAYITLI]

Altornekleme kolu, 60 satir (4 pencere x 5 yil x 3 model). Pencere basina
`RMSE_std` ozeti:

| pencere | ortalama std | min | maks | havuz orani (K/tum) |
|---|---|---|---|---|
| 1 | 0.379061 | 0.057337 | 1.180309 | 0.1089 - 0.1964 |
| 2 | 0.274058 | 0.020665 | 0.721008 | 0.2202 - 0.3972 |
| 3 | 0.184447 | 0.010260 | 0.522730 | 0.3318 - 0.5985 |
| 5 | 0.144936 | 0.000000 | 0.482358 | 0.5544 - 1.0000 |

Ornekleme tesadufu hacim buyudukce kuculuyor - beklenen davranis.
K=5 minimumu 0.0 tam uc hucrede: 2019 x {LR, PolyRidge, HGB}. Orada
`havuz_orani = 1.0`, yani altornekleme DEJENERE (havuz = hedef, `egitim_n`
= `havuz_n` = 261798) ve uc tohum ayni kumeyi seciyor. Invaryant 4 tam bu
hucreyi olcer.

### 8. Algoritma span'i vs hacim span'i -- `doygunluk_ozet_algoritma_span.csv` [SONRADAN]

Ayni turden kiyas: iki span. Kaydirmali kol, 3 hizli model.

Pencere basina algoritma span'i (K sabit, model degisiyor):

| pencere | HGB | LR | PolyRidge | en iyi | en kotu | span (W) |
|---|---|---|---|---|---|---|
| 1 | 143.677766327 | 141.327885941 | 139.410945077 | Polynomial Ridge | Hist Gradient Boosting | 4.26682125007 |
| 2 | 140.309870834 | 141.171460174 | 137.52431025 | Polynomial Ridge | Linear Regression | 3.64714992451 |
| 3 | 138.585914977 | 141.099457656 | 136.945876004 | Polynomial Ridge | Linear Regression | 4.15358165236 |
| 5 | 137.49981682 | 141.068966396 | 136.560665924 | Polynomial Ridge | Linear Regression | 4.5083004718 |
| tum | 136.939917088 | 141.081209606 | 136.415915435 | Polynomial Ridge | Linear Regression | 4.66529417096 |

Model basina hacim span'i (model sabit, K degisiyor, K=1 -> K=tum):

| model | span (W) |
|---|---|
| Hist Gradient Boosting | 6.73784923862 |
| Polynomial Ridge | 2.99502964211 |
| Linear Regression | 0.246676335157 |

Kiyas satiri:

    algoritma_span (K sabit)   : min 3.64714992451  ort 4.24822949394  maks 4.66529417096  n=5
    hacim_span (model sabit)   : min 0.246676335157 ort 3.3265184053   maks 6.73784923862  n=3

**Ikisi ayni mertebede.** Ayrinti karar 1'de.

### 9. Marjinal guven araliklari -- `doygunluk_ozet_ga.csv` [SONRADAN]

45 karsilastirma (5 yil x 3 model x 3 tohum) + 1 TOPLAM satiri.
K=1 ile K=tum'un marjinal (esli OLMAYAN) bootstrap GA'lari.

    cakisan_n / toplam_n     : 45 / 45   (%100)
    ortalama K=1 GA genisligi: 8.808804 W
    ortalama K=tum GA genisl.: 8.696402 W
    ortalama fark            : 2.204968 W

**45/45 cakisiyor.** Bu "fark yok" DEMEK DEGILDIR - karar 4.

### 10. Esli kumelenmis DM, egri uclari -- `doygunluk_ozet_dm.csv` [SONRADAN]

Ayni 45 karsilastirma, bu kez ESLI ve `time_utc` duzeyinde kumelenmis.
Pozitif fark = K=tum daha iyi.

| model | n | anlamli (p<0.05) | GA sifir icerir | ters isaret | fark min (W) | fark maks (W) |
|---|---|---|---|---|---|---|
| Hist Gradient Boosting | 15 | 15 | 0 | 0 | 3.393074 | 5.745608 |
| Polynomial Ridge | 15 | 15 | 0 | 0 | 1.133145 | 2.677570 |
| Linear Regression | 15 | 5 | 10 | 2 | -0.057593 | 0.775491 |

**TOPLAM 35/45 anlamli.** p araligi 2.5199839453432825e-17 - 0.970016151097306.

Isaret ters cikan iki hucre (ikisi de anlamsiz):

| yil | model | tohum | fark (W) | p |
|---|---|---|---|---|
| 2019 | Linear Regression | 11 | -0.026204 | 0.834425 |
| 2019 | Linear Regression | 33 | -0.057593 | 0.632986 |

Marjinal GA'da 45/45 cakisma vardi; esli DM'de 35/45 anlamli. Karar 4.

### 11. Genis kosu -- yil x model RMSE (W), K=tum, kaydirmali

| model | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|
| Polynomial Ridge | 136.502928678 | 136.379318934 | 136.826471496 | 139.75614397 | 132.614714096 |
| Neural Network | 137.097065058 | 136.526282493 | 138.345229802 | 139.4447665 | 133.347520301 |
| Hist Gradient Boosting | 137.16896737 | 136.804224601 | 137.099127587 | 140.223065162 | 133.404200722 |
| Gradient Boosting | 137.580440885 | 137.313986772 | 137.858040558 | 140.918305563 | 133.721206097 |
| Extra Trees | 138.63735257 | 138.27351833 | 137.685551875 | 140.894605533 | 134.086934127 |
| Random Forest | 139.060715398 | 138.710181302 | 137.839834696 | 141.649572025 | 134.315329832 |
| Linear Regression | 141.343657513 | 140.903245067 | 141.368869735 | 143.950354777 | 137.839920936 |
| SGD Regression | 141.221749012 | 141.24072396 | 141.432446949 | 143.96688268 | 138.127991789 |
| K-Nearest Neighbours | 145.431349599 | 143.69724034 | 145.227498738 | 146.47440499 | 140.215151093 |
| Decision Tree | 176.562645318 | 172.834835679 | 169.438634572 | 177.292103155 | 165.652734774 |

Yil ortalamasi uzerinden havuz span'i:

    tam kume (10 model)         : 35.9402752648831 W
    Decision Tree haric (9)     :  7.793213517227656 W

Yil basina ilk uc:

| yil | 1. | 2. | 3. | ilk-iki fark (W) |
|---|---|---|---|---|
| 2019 | Polynomial Ridge 136.50292867804177 | Neural Network 137.0970650575597 | Hist Gradient Boosting 137.16896736972845 | 0.59413637951792 |
| 2020 | Polynomial Ridge 136.3793189338747 | Neural Network 136.52628249309137 | Hist Gradient Boosting 136.80422460091566 | 0.14696355921665827 |
| 2021 | Polynomial Ridge 136.82647149596892 | Hist Gradient Boosting 137.0991275871606 | Extra Trees 137.68555187464014 | 0.272656091191692 |
| 2022 | Neural Network 139.44476650011856 | Polynomial Ridge 139.75614396966736 | Hist Gradient Boosting 140.2230651615558 | 0.31137746954880186 |
| 2023 | Polynomial Ridge 132.61471409623294 | Neural Network 133.34752030125907 | Hist Gradient Boosting 133.4042007222262 | 0.7328062050261224 |

**Ilk okuma:** on modelli, bes yillik kurulumda kazanan DEGISIYOR - Polynomial
Ridge x4, Neural Network x1 (2022). Bu okuma asagidaki tablo ile GERI ALINDI.

### 12. Yil ici esli DM -- `doygunluk_ozet_dm_yil.csv` [SONRADAN]

Her yilin ILK UC modelinin butun ikilileri; kumelenme `time_utc`, Faz 3 ile
ayni birim. Pozitif DM = `model_a`, `model_b`'den daha KOTU.

| yil | model_a | model_b | fark (W) | DM | p | anlamli | GA alt | GA ust | GA sifir | kazanan-ikinci |
|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | Polynomial Ridge | Neural Network | -0.594136379518 | -1.42205256707 | 0.155010991184 | False | -1.24770852125 | 0.0973248923628 | True | **EVET** |
| 2019 | Polynomial Ridge | Hist Gradient Boosting | -0.666038691687 | -1.24614646564 | 0.2127106287 | False | -1.4350653877 | 0.143360131675 | True | hayir |
| 2019 | Neural Network | Hist Gradient Boosting | -0.0719023121688 | -0.138822282332 | 0.889590585719 | False | -0.973751591223 | 0.789064196339 | True | hayir |
| 2020 | Polynomial Ridge | Neural Network | -0.146963559217 | -0.329026012081 | 0.742136026877 | False | -1.00175696513 | 0.677435362716 | True | **EVET** |
| 2020 | Polynomial Ridge | Hist Gradient Boosting | -0.424905667041 | -1.00642460799 | 0.314211361176 | False | -1.21824099762 | 0.349952207648 | True | hayir |
| 2020 | Neural Network | Hist Gradient Boosting | -0.277942107824 | -0.558495216342 | 0.576506270153 | False | -1.20492487375 | 0.721502362598 | True | hayir |
| 2021 | Polynomial Ridge | Hist Gradient Boosting | -0.272656091192 | -0.784111842816 | 0.432974486978 | False | -1.01783144393 | 0.422913439425 | True | **EVET** |
| 2021 | Polynomial Ridge | Extra Trees | -0.859080378671 | -1.8823696373 | 0.0597858454445 | False | -1.71827108985 | -0.0847340449261 | **False** | hayir |
| 2021 | Hist Gradient Boosting | Extra Trees | -0.58642428748 | -1.33339265376 | 0.182402981926 | False | -1.24607865116 | 0.12023771794 | True | hayir |
| 2022 | Neural Network | Polynomial Ridge | -0.311377469549 | -0.818390392662 | 0.413134305825 | False | -1.05564100478 | 0.412986633518 | True | **EVET** |
| 2022 | Neural Network | Hist Gradient Boosting | -0.778298661437 | -1.5369274027 | 0.12431108819 | False | -1.70351676245 | 0.155894068023 | True | hayir |
| 2022 | Polynomial Ridge | Hist Gradient Boosting | -0.466921191888 | -1.10189728499 | 0.270506329076 | False | -1.20143190366 | 0.217290167653 | True | hayir |
| 2023 | Polynomial Ridge | Neural Network | -0.732806205026 | -1.57743441497 | 0.114695601884 | False | -1.70812911661 | 0.167348027916 | True | **EVET** |
| 2023 | Polynomial Ridge | Hist Gradient Boosting | -0.789486625993 | -2.07441857594 | **0.0380404536005** | **True** | -1.5055220934 | -0.0973899636411 | False | hayir |
| 2023 | Neural Network | Hist Gradient Boosting | -0.0566804209671 | -0.00725484129532 | 0.994211524917 | False | -0.939207395428 | 0.773562903555 | True | hayir |

    karsilastirma          : 15   (5 yil x 3 cift)
    p < 0.05               : 1/15
    esli GA sifir icerir   : 13/15
    KAZANAN-IKINCI ANLAMLI : 0/5
    p min / maks           : 0.0380405 / 0.994212
    kumelenme birimi       : time_utc; n_ham 25774-25887, n_kume 5418-5441
    dipnotlu satir         : 2  (2021 - Extra Trees iceren iki satir)

**Kazanan-ikinci farki HICBIR YILDA ANLAMLI DEGIL:**
2019 p=0.155010991184 | 2020 p=0.742136026877 | 2021 p=0.432974486978 |
2022 p=0.413134305825 | 2023 p=0.114695601884. Besinin de esli GA'si sifiri
iceriyor.

### 13. Duzeltilmis ana tablo -- `doygunluk_ozet_duzeltilmis.csv` [SONRADAN]

Makalenin ana iddialari BU tablodan okunur, `hacim_orani`'ndan degil.

| soru | olcu | deger (W) | ek | kayit |
|---|---|---|---|---|
| S1 veri hacmi | saf hacim span'i, Hist Gradient Boosting | 4.49324429128 | 15/15 esli DM p<0.05 | SONRADAN |
| S1 veri hacmi | saf hacim span'i, Polynomial Ridge | 1.91171668237 | 15/15 esli DM p<0.05 | SONRADAN |
| S1 veri hacmi | saf hacim span'i, Linear Regression | 0.209944395617 | 5/15 esli DM p<0.05 | SONRADAN |
| S2 algoritma | ilk-iki farki | 0.52400165356 | Polynomial Ridge vs Hist Gradient Boosting | SONRADAN |
| S2 algoritma | havuz span'i (Decision Tree haric) | 7.79321351723 | 9 model | SONRADAN |
| S2 algoritma | havuz span'i (tam kume) | 35.9402752649 | 10 model, Decision Tree dahil | SONRADAN |
| S3 test yili | kazanan degisimi (10 model) | - | 2 farkli kazanan: Polynomial Ridge 4, Neural Network 1 | SONRADAN |
| S3 kapsam | 2019 ilk-iki farki | 0.594136379518 | p=0.155011, anlamli DEGIL | SONRADAN |
| S3 kapsam | 2020 ilk-iki farki | 0.146963559217 | p=0.742136, anlamli DEGIL | SONRADAN |
| S3 kapsam | 2021 ilk-iki farki | 0.272656091192 | p=0.432974, anlamli DEGIL | SONRADAN |
| S3 kapsam | 2022 ilk-iki farki | 0.311377469549 | p=0.413134, anlamli DEGIL | SONRADAN |
| S3 kapsam | 2023 ilk-iki farki | 0.732806205026 | p=0.114696, anlamli DEGIL | SONRADAN |
| S3 kapsam | kazanan degisimi iddiasinin dayanagi | - | sinanan: [2019,2020,2021,2022,2023] \| sinanmayan: [] | SONRADAN |
| S3 test yili | varyans payi: test yili | - | %48.486837 | ON-KAYITLI |
| S3 test yili | varyans payi: algoritma | - | %25.217039 | ON-KAYITLI |
| S3 test yili | varyans payi: veri hacmi | - | %15.272219 | ON-KAYITLI |
| S3 test yili | varyans payi: hacim x algoritma | - | %9.717545 | ON-KAYITLI |

`sinanmayan` listesi BOS - bes test yilinin hepsi esli DM ile sinandi.

### 14. Faz 3 ile capraz teyit -- 2023 PolyRidge vs HGB ayni satiri veriyor

Faz 3'te (`sonuclar/siralama_karsilastirma.csv`) yedi yilin ilk-iki cifti
yalnizca 2023'te anlamli cikmisti: Polynomial Ridge vs Hist Gradient Boosting,
p=0,0380. Faz 4'un yil ici DM'sinde AYNI cift, AYNI yilda, ayni sayilari
veriyor.

Bu beklenen bir sonuctur - K=tum @ 2023 hucresi Faz 3'un 2023 bolmesiyle ayni
egitim/test bolmesidir (invaryant 2 tam bunu pinliyor). Beklenen olmasi
onemsiz oldugu anlamina gelmez: iki sayi IKI AYRI KOD YOLUNDAN cikiyor.

| alan | Faz 3 (`siralama_karsilastirma.csv`) | Faz 4 (`doygunluk_ozet_dm_yil.csv`) | Faz 4, Faz 3 hassasiyetine yuvarlanmis |
|---|---|---|---|
| RMSE_a | 132.61 | 132.61471409623294 | 132.61 |
| RMSE_b | 133.4 | 133.4042007222262 | 133.40 |
| RMSE_fark_W | -0.7895 | -0.7894866259932485 | -0.7895 |
| RMSE_fark_kapasite_yuzde | -0.0789 | -0.07894866259932484 | -0.0789 |
| RMSE_fark_bagil_yuzde | -0.5918 | -0.5918004243637838 | -0.5918 |
| DM | -2.074 | -2.0744185759403537 | -2.074 |
| p | 0.038 | 0.03804045360045688 | 0.0380 |
| fark_GA_alt | -1.51 | -1.5055220933988522 | -1.51 |
| fark_GA_ust | -0.1 | -0.09738996364109556 | -0.10 |

**Dokuz alanin dokuzu da tutuyor.** Faz 3'un CSV'si yuvarlanmis
saklandigi icin kiyas o hassasiyette; bit duzeyi kiyas degil.

Ayrisan kod yollari:

    bolme     : Faz 3 pv10/experiment.py:bolme_indeksleri
                Faz 4 pv10/doygunluk.py:egitim_test_bolme
    DM hesabi : Faz 3 pv10/ranking.py
                Faz 4 pv10/ozet_sonrasi.py:yil_ici_dm

Ortak olan: `features.py`, `models.py`, `evaluate.py` ve dondurulmus veri.
Yani teyit edilen sey oznitelik uretimi degil, BOLME ve DM zinciri - Faz 4'te
bilincli olarak yeniden yazilmis olan iki parca (karar: `bolme_indeksleri`
degistirilmedi, ayri kod yolu acildi).

Invaryant 2 bir NOKTA metrigi karsilastirir (RMSE, `ablasyon.csv`'ye karsi).
Bu satir ondan fazlasini yapiyor: farkli GA'sini, DM istatistigini, p
degerini ve bootstrap araligini da ayni yere dusuruyor. **Invaryant 2'nin
bagimsiz bir teyididir** ve invaryantin kapsamadigi zinciri (kumelenme,
Newey-West, blok bootstrap) de kapsar.

Not: bu satir kazanan-ikinci cifti DEGIL, birinci-ucuncu ciftidir (karar 6);
capraz teyit degeri, iddia degeri ile karistirilmamalidir.

### 15. `dm_yil.py` dogrulama kosusu -- `doygunluk_ozet_dm_yil_dogrulama.csv`

Betik REPODAKI haliyle kosuldu (4 Agustos 2026):

    python -m arac.dm_yil --cikti sonuclar/doygunluk_ozet_dm_yil_dogrulama.csv

`--cikti` bayragi bu kosu icin eklendi; betik cikti dosyasinin UZERINE
yazdigi icin bayrak olmadan mevcut tablo ezilirdi. Varsayilan yol degismedi,
hesap mantigina dokunulmadi.

Kiyas: 15 satir x 19 alan = **285 karsilastirma, TOLERANSSIZ (`==`),
sifir fark.** Anahtar `(test_yil, model_a, model_b)`; iki tabloda da 15 satir,
eslesme tam. Sayisal alanlar kadar `anlamli`, `kumelenme`, `kaynak_dizin`,
`en_iyi`, `ikinci`, `kazanan_ikinci_cifti`, `dipnot` gibi metin/mantik
alanlari da kiyaslandi.

**Beklenen tek sapma GERCEKLESMEDI ve sebebi ogreticidir.** 2021'in Extra
Trees iceren iki satirinin son basamaginin oynayabilecegi dusunulmustu; hicbir
alan oynamadi. Sebep: `dm_yil.py` MODEL EGITMEZ - diskteki tahmin
parquet'lerini okur. RF/ET nondeterminizmi model FIT edildiginde dogar; ayni
tahmin vektoru iki kez okundugunda ayni sayilari verir.

Dolayisiyla `dipnot` sutununun kapsami daraltilmali: o satirlar "bu betik
tekrar kosulursa degisebilir" demiyor - **"IZGARA yeniden kosulur ve tahminler
yeniden uretilirse degisebilir"** diyor. Betik duzeyinde tekrarlanabilirlik
tam; belirsizlik yukarida, tahminleri ureten katmanda.

Bu ayni zamanda kusur 1'in siniridir: nondeterminizm `hucre_kos` cagrisinda
dogar, ondan sonraki her sey (tahmin -> DM -> ozet) determinist.

## Alinan kararlar ve gerekceleri

Karar 1-14 arasi `d469060`'daki kararlarin devamidir; numaralar orada
birakildigi yerden degil, bu notta bastan verilmistir. Onceki nottaki
tasarim kararlari (10 yillik pencere yok, test yillari 2019-2023,
oznitelikler dilimden SONRA, `bolme_indeksleri` degistirilmedi, gun duzeyi
tabakali altornekleme, tohum yalnizca gun secimini oynatir, bootstrap tohumu
SEED, kaydirmali tohum 0, ana oran altornekleme kolundan, nRMSE secimi,
varyans ayristirmasi 3 modelde, tolerans 1e-6, hatali hucre diske yazilir)
GECERLIDIR ve degismemistir.

### 1. "4,72 kat" orani DUSURULDU -- yanlis turden kiyas

`doygunluk_ozet_hacim_orani.csv` saf hacim etkisini (2,204968 W) Faz 3'un
algoritma MEDYAN IKILI farkina (0,4669 W) bolup **4,72257112106** uretiyordu.

Sorun: pay bir SPAN (K=1'den K=tum'e aralik), payda ise IKILI FARKLARIN
MEDYANI. Ikisi ayni turden istatistik degil; birinin digerine bolumu bir
"kat" ifade etmiyor. Span span ile, medyan medyan ile kiyaslanir.

Ayni turden bakildiginda (tablo 8):

    algoritma span'i (K sabit, model degisiyor)  : 3.64714992451 - 4.66529417096 W
    hacim span'i     (model sabit, K degisiyor)  : 0.246676335157 - 6.73784923862 W

**Ayni mertebede.** "Veri hacmi algoritma seciminden 4,72 kat onemli"
iddiasi kurulamaz.

Tablo SILINMEDI, kayit icin yerinde birakildi; kunye dosyasina UYARI blogu
yazildi. Makalenin ana iddiasi `doygunluk_ozet_duzeltilmis.csv`'den okunur.

### 2. On-kayitli tablo ile sonradan eklenen tablo AYRI MODULDE

`pv10/ozet.py` izgara kosulmadan ONCE yazildi ve o gunden beri dokunulmadi.
Dosya duzeyinde kanit:

    git log -- pv10/ozet.py
    -> 13c6ee8  2026-07-31  (tek commit)

    izgara kosu tarihi: 2026-08-03 04:32:09  (doygunluk_ozet_kunye.txt)

Yani `ozet.py` izgaradan uc gun once yazilmis, sonra hic degismemis. Hangi
metrigin raporlanacagi sayilar gorulmeden sabitlendi; metrik secimi post-hoc
DEGILDIR. Bu iddia tam olarak bu dosya gecmisine dayanir.

`pv10/ozet_sonrasi.py` sonuclar GORULDUKTEN sonra yazildi:

    git log -- pv10/ozet_sonrasi.py
    -> 8b07d09  2026-08-02
       3d15cce  2026-08-02
       566b111  2026-08-02

Bu modulden cikan her tablo kunyede `[sonradan eklendi]` diye isaretlenir ve
`doygunluk_ozet_duzeltilmis.csv`'nin `kayit` sutununda `SONRADAN` gorunur.
Ayrimin sebebi kayit duzenidir: hakem "bu metrigi sonuclari gorunce mi
sectiniz" diye sordugunda cevap dosya gecmisinden okunur.

ON-KAYITLI: egri, marjinal, hacim_orani, tohum_yayilimi, model_pencere,
model_pencere_yil, varyans, konum.
SONRADAN: algoritma_span, ga, duzeltilmis, dm, dm_yil.

### 3. Hacim etkisi MODEL BAGIMLI -- havuzlanmis ortalama verilmiyor

Saf hacim etkisinin havuzlanmis ortalamasi 2,204968 W. Bu tek sayi
yaniltici, cunku uc modeli ayni potaya koyuyor:

| model | saf hacim span'i (W) | esli DM anlamli |
|---|---|---|
| Hist Gradient Boosting | 4.49324429128 | 15/15 |
| Polynomial Ridge | 1.91171668237 | 15/15 |
| Linear Regression | 0.209944395617 | 5/15 |

Linear Regression'da etki 15 karsilastirmanin yalnizca 5'inde anlamli, iki
hucrede isaret TERS (2019 tohum 11: -0,026204 W; 2019 tohum 33: -0,057593 W;
ikisi de anlamsiz) ve 10 hucrede esli GA sifiri iceriyor. Hist Gradient
Boosting'de 15/15 anlamli, hicbirinde GA sifiri icermiyor.

Yani "daha fazla veri daha iyi model" ifadesi modelden bagimsiz DOGRU DEGIL:
dogrusal modelde 51 bin satirla 472 bin satir arasinda pratikte fark yok.
Bu yuzden `duzeltilmis` tablosu S1'i tek satir yerine UC MODEL SATIRI olarak
raporlar; havuzlanmis 2,204968 W makaleye ana sayi olarak GIRMEZ.

Ayni sey varyans ayristirmasinda `pencere x model` teriminin %9,72 ile
`pencere` ana etkisinin (%15,27) ucte ikisi kadar olmasinda da gorunuyor.

### 4. Marjinal GA cakismasindan ESLI KUMELENMIS DM'ye gecildi

`doygunluk_ozet_ga.csv`: 45 karsilastirmanin 45'inde K=1 ve K=tum'un
bootstrap guven araliklari CAKISIYOR (%100).

Bu "fark yok" DEMEK DEGILDIR. Egrinin iki ucu AYNI test setinde
degerlendiriliyor; hatalar korelasyonlu. Esli olmayan (marjinal) kiyas bu
durumda muhafazakardir - ortak varyansi iki kez sayar.

Esli, `time_utc` duzeyinde kumelenmis DM ile ayni 45 karsilastirma:
**35/45 anlamli**. Yani marjinal GA'ya bakip "hacimin etkisi yok" denseydi
35 gercek etkiden 35'i kacirilacakti.

Kural: **cakismama farki ispatlar, cakisma farksizligi ispatlamaz.**
Kumelenme birimi `time_utc` - Faz 3 ile ayni (`ranking.py:110`); alti konum
ayni zaman damgasinda oldugu icin damga duzeyinde kumelenmezse bagimsizlik
varsayimi alti kat sisirilmis n verir. `n_ham` 25774-25887, `n_kume`
5418-5441.

Marjinal GA tablosu SILINMEDI; iki tablonun yan yana durmasi gecisin
gerekcesinin kendisidir.

### 5. Genis kosunun "kazanan degisiyor" okumasi GERI ALINDI

Genis kosu (tablo 11) ilk bakista tam beklenen sonucu veriyordu: ayni
kurulumda yalnizca test yili degisince kazanan degisiyor - dort yil
Polynomial Ridge, 2022'de Neural Network. Makalenin en cok ise yarayacak
bulgusu buydu.

Yil ici esli DM (tablo 12) bunu GERI ALDI:

    kazanan-ikinci farki, 5 yilin 5'inde de ANLAMSIZ
    2019 p=0.155010991184   2020 p=0.742136026877   2021 p=0.432974486978
    2022 p=0.413134305825   2023 p=0.114695601884
    besinin de esli GA'si sifiri iceriyor

Yani kazanan gercekten iki kez degisiyor, ama **DEGISIMIN KENDISI GURULTU**:
hicbir yilda kazanani ikinciden ayirt edemiyoruz. 2022'de Neural Network'un
Polynomial Ridge'i gectigi soylenemez; siralamanin o yil bas asagi donmesi
0,311377 W'lik ve p=0,413134 olan bir farka dayaniyor.

Iddia bu yuzden "kazanan yila gore degisir" degil, **"tek yillik bir kiyasin
urettigi siralama, kazanani ikinciden ayirt edecek guce sahip degildir"**
seklinde kurulur. Ikincisi daha zayif gorunuyor ama savunulabilir olan bu.

Ilk okuma NOTTAN SILINMEDI; geri alinmis olmasi kaydin parcasi.

### 6. 15 testin 1'i anlamli - ama o satir iddiaya dayanak DEGIL

Tek anlamli satir 2023 Polynomial Ridge vs Hist Gradient Boosting,
p=0.0380404536005. Uc gerekceyle iddiaya yaslanmiyor:

1. **Birinci-UCUNCU cifti**, kazanan-ikinci degil. 2023'te ikinci Neural
   Network (p=0.114695601884, anlamsiz).
2. **Coklu karsilastirma duzeltmesi YAPILMADI.** 15 testte 0,05 esiginde
   beklenen tesadufi anlamli sayisi 15 x 0,05 = **0,75**. Gozlenen 1.
   Bonferroni esigi 0,05/15 = 0,00333; p=0,038 bunu gecmiyor.
3. Duzeltme yapilmamasi bilincli: her yil ayri bir soru olarak kurulmustu.
   Ama bu, tek bir anlamli satiri "bulgu" saymaya izin vermez.

### 7. 2021 PolyRidge vs Extra Trees -- DM ile esli GA SINIRDA AYRISIYOR

Tek ic tutarsizlik. `doygunluk_ozet_dm_yil.csv`, 8. satir:

    2021  Polynomial Ridge vs Extra Trees
    fark      = -0.859080378671 W
    DM        = -1.8823696373
    p         =  0.0597858454445        -> ANLAMLI DEGIL (p > 0.05)
    esli GA   = [-1.71827108985 ; -0.0847340449261]
    GA_sifiri_iceriyor = False          -> GA SIFIRI DISLIYOR

Iki test ayni yerde durmuyor: DM'nin Newey-West standart hatasi p>0,05
verirken blok bootstrap kuyrugu sifiri disliyor. Ikisi farkli varsayimlar
altinda calisiyor (biri asimptotik ve otokorelasyon duzeltmeli, digeri
yeniden orneklemeli ve gun blogu bagimliligini tasiyor); sinirda ayrismalari
beklenmedik degil ama SESSIZ GECILMEZ.

Etkisi: YOK. Bu satir kazanan-ikinci cifti DEGIL (2021'in ikincisi Hist
Gradient Boosting). Kazanan-ikinci ciftlerinin besinde de iki test ayni
yonde: hem p>0,05 hem GA sifiri iceriyor. Ayrica bu satir Extra Trees
icerdigi icin `dipnot` sutunuyla ayrica isaretli - son basamagi baska kosuda
birebir tekrarlanmayabilir.

Raporlanacak sekli: makalede bu satir verilirse HER IKI sonuc birlikte
verilir; yalnizca birini yazmak seciciliktir.

### 8. Invaryant 5 uretim yolunu dogrular hale getirildi (`181d543`)

Ilk halinde invaryant 5, bolme mantiginin invaryanta KOPYALANMIS surumunu
dogruluyordu; karsilastirmanin iki tarafi da ayni cagriydi ve
`farkli_oznitelik = 0` sonucu DETERMINIZMDEN geliyordu, olcumden degil.
Kopya dogru oldugu surece uretim yanlis olsa bile kapi yesil yanardi.

Duzeltme iki parcali:
1. Invaryant artik URETIM fonksiyonunu cagiriyor (`egitim_test_bolme`,
   `hucre_kos`). Bolme mantigi TEK yerde: `pv10/doygunluk.py:egitim_test_bolme`
   (`b7e7a92`); hem `hucre_kos` hem `dogrulama.py` oradan geciyor.
2. Kasten YANLIS bir referans uretiliyor (oznitelikler ters sirada
   hesaplaniyor) ve invaryantin bunu YAKALADIGI olculuyor:
   `ters_sira_farkli_oran = 1.0`, `ters_sira_maks_fark = 168.053036 W`.

Negatif kontrol olmadan bir invaryant islevsizdir - yanlisi yakalayamiyorsa
kapinin yesil yanmasi bilgi tasimaz.

### 9. pyarrow 22.0.0'a indirildi (`74c3c62`)

3 Agustos 2026 02:06'da Windows Smart App Control pyarrow 25.0.0'in
`arrow.dll`'ini bloklamaya basladi (CodeIntegrity 3077/3033,
`VerifiedAndReputablePolicyState=1`). Parquet okunamadigi icin hicbir kosu
baslamiyordu.

Secenekler ve secim:
- SAC'i kapatmak: **YAPILMADI.** Geri alinamaz bir islem (yeniden acmak
  Windows'un yeniden kurulmasini gerektiriyor). Ayarina DOKUNULMADI.
- pyarrow'u kaynaktan derlemek: yapilmadi, `--only-binary=:all:` kullanildi.
- 22.0.0'a inmek: SECILDI.

Surum degisiminden sonra veri ve kapi yeniden dogrulandi:

    veri sha256_16     : f722a717bac502c2   (DEGISMEDI)
    satir              : 525.888            (DEGISMEDI)
    konum              : 6                  (DEGISMEDI)
    invaryant kapisi   : 18/18 GECTI
    invaryant 1 bagil  : 6.050675e-13       (surum oncesiyle BIREBIR)
    invaryant 2 bagil  : 7.797529e-12       (surum oncesiyle BIREBIR)

Ana izgara, genis kosu ve 2022 kosusu 25.0.0 ile uretildi; kalan dort yilin
kosusu ve nondeterminizm olcumu 22.0.0 ile. Iki surum arasinda metriklerin
kimildamadiginin kaniti yukaridaki 510/520 regresyon kiyasidir - surum
etkili olsaydi sekiz model bit duzeyinde ayni cikmazdi.

### 10. Teshis kodu deney kodundan AYRI DIZINDE (`arac/`)

`arac/` DENEY DEGIL TESHIS icindir: makalenin hicbir sayisini uretmez ve ana
akistan cagrilmaz. `pv10/` ile `run_*.py` icinde yalnizca deney kodu kalsin
diye ayri tutuldu - faz notunda hangi dosyanin makale sayisi urettigi
bulanmasin.

    arac/nondeterminizm.py        teshis: ayni hucre x tekrar x surec
    arac/nondeterminizm_karar.py  yorum kurali (sonuc gorulmeden) + karar
    arac/dm_yil.py                yil ici DM surucusu
    arac/regresyon_kiyas.py       iki izgara logunun toleranssiz kiyasi

`dm_yil.py` ve `regresyon_kiyas.py` once scratchpad'de tek kullanimlik
betiklerdi; commit edilmis CSV'lerin nasil uretildigini repoda hicbir sey
anlatmadigi icin `4be6a45` ile kalicilastirildilar. Govdeleri, CSV'leri
ureten betiklerle birebir ayni; degisen yalniz docstring, argparse ve cikti
yollari.

### 11. `--etiket` verilmeden farkli model kumesi kosulmaz

`--etiket` VERILMEZSE kosu ana izgara loguna yazar ve ozet tablolari
kirlenir: egri, ana oran, tohum yayilimi ve model x pencere tablolari mevcut
modeller uzerinde ortalama aliyor. Farkli model kumesi veya tek pencere
kosarken `--etiket` ZORUNLU sayilir. Bu yuzden genis kosu, 2022 kosusu ve
kalan dort yilin kosusu ayri log dosyalarina yazildi.

### 12. Kunye dosyasi kosunun kendi sartlarini kaydediyor

`doygunluk_ozet_kunye.txt` her ozet uretiminde yeniden yazilir ve sunlari
tasir: kosu tarihi, izgara tamam mi, hucre sayisi, eksik/basarisiz hucre,
veri dosyasi adi, veri sha256_16, BEKLENEN sha256_16, thread sabiti,
on-kayit durumu, hacim_orani uyarisi, model x pencere kazanan dagilimi,
varyans ayristirmasi parametreleri, yazilan tablolarin listesi ve satir
sayilari (`[sonradan eklendi]` isaretiyle).

`VERI_SHA16` config'e bu yuzden eklendi: kunye, calisilan dosyanin hash'ini
sabite karsi kontrol eder. Veri sessizce degisirse ozet bunu yazar.

## Bilinen kusurlar ve varsayimla gecilen her sey

1. **Random Forest ve Extra Trees surec ici nondeterminist.** Olculdu ve
   kapatildi (yukariya bak). Sapma 1-2 ULP (bagil ~2e-16) ve raporlanan
   hicbir sayiyi etkilemiyor.
   `[sonradan eklendi - 17 Ekim 2026]` "1-2 ULP (bagil ~2e-16)" eksik: bagil fark 1,5e-15'in altinda: dogrudan hesaplanan metriklerde 1-2 ULP, turetilmis `skill` alaninda 8 ULP'ye kadar (Random Forest 2020: 19.932346077995252 -> 19.932346077995280, bagil 1,43e-15).

   Belirsizligin siniri OLCULDU: nondeterminizm `hucre_kos` icinde, model FIT
   edilirken doguyor. Ondan sonraki zincir (kaydedilmis tahmin -> DM -> ozet)
   determinist - `dm_yil.py` dogrulama kosusu 285/285 alani birebir uretti.
   Yani `doygunluk_ozet_dm_yil.csv`'nin Extra Trees iceren iki satiri betik
   tekrar kosuldugunda DEGISMEZ; degisebilecegi durum IZGARANIN yeniden
   kosulup tahminlerin yeniden uretilmesidir. `dipnot` sutunu bu ikinci
   durumu isaretler. Kazanan-ikinci ciftlerinin hicbiri etkilenmiyor.

2. ~~`arac/dm_yil.py` repodaki haliyle hic kosulmadi.~~ **KAPANDI.**
   Kalicilastirma boslugu kalmadi; dort teshis betiginin dordu de repodaki
   haliyle kosuldu:
   - `arac/dm_yil.py` -> `doygunluk_ozet_dm_yil_dogrulama.csv`, 285/285 alan
     birebir (asagida).
   - `arac/regresyon_kiyas.py` -> 510/520, cikis kodu 0.
   - `arac/nondeterminizm.py` + `nondeterminizm_karar.py` -> karar iki
     olcumde de ayni.

3. **`hacim_orani` tablosu yanlis ama repoda duruyor.** Silinmedi; kunyede
   UYARI blogu var, bu notta karar 1 var, `duzeltilmis` tablosu yerine
   geciyor. Yine de dosyayi baglamsiz okuyan biri 4,72257112106 sayisini
   gorur. Makale metnine giderken bu sayinin HICBIR YERDE kullanilmadigi
   ayrica kontrol edilmeli.

4. **Coklu karsilastirma duzeltmesi hicbir DM tablosunda yapilmadi.**
   Ne 45 karsilastirmalik egri-ucu tablosunda ne 15 karsilastirmalik yil ici
   tabloda. Egri-ucu tablosunda etki buyuk (35/45, p'ler 1e-17'ye kadar
   iniyor) ve duzeltme sonucu degistirmez; yil ici tabloda tek anlamli satir
   duzeltmeyi gecmez (karar 6). Makalede bu acikca yazilmali.

5. **Altornekleme hedefi tam tutturamayabilir.** Gun bloklari tam alindigi
   icin bir sonraki gun hedefi asacaksa alinmaz; konum basina 24 satira kadar
   eksik kalabilir. Invaryant 5'in olctugu hucrede tam isabet (103974 ==
   103974). Butun hucrelerde dogrulanmadi; gercek deger her satirda
   `egitim_n` olarak loglaniyor.

6. **`hedef_satir_sayisi` konumlarin satir sayisinin esit olmasini varsayar**,
   degilse ValueError firlatir. Dondurulmus veride esit.

7. **`.gitignore` `sonuclar/tahminler/` dizinini YOL olarak dislamiyor;**
   icindeki dosyalar yalnizca global `*.parquet` kuraliyla disarida kaliyor.
   O dizine parquet olmayan bir cikti yazilirsa commit'e girer. CLAUDE.md
   kural 3 dizini yol olarak dislanmis gibi anlatiyor. **ACIK - duzeltilmedi.**

8. **Invaryant 2'nin referansi `ablasyon.csv`**, o dosya thread sabitlemesi
   olmadan uretildi. 1e-6 bagil tolerans bu farki soguruyor; gozlenen en
   buyuk sapma 7.797529e-12.

9. **HGB'nin Faz 2'ye gore 22,0 -> 7,4 sn hizlanmasi aciklanmadi.** RMSE
   birebir ayni (invaryant 2). Thread sabitlemesine atfedildi, olculerek
   dogrulanmadi. **ACIK.**

10. **Yil ici DM yalnizca ILK UC modeli kapsiyor.** Dorduncu ve sonrasi
    sinanmadi. Gerekce: soru "kazanan ikinciden ayirt edilebilir mi";
    10 modelin butun ikilileri 45 x 5 = 225 test olurdu ve coklu
    karsilastirma sorunu buyurdu. Ama bu, "ilk uc disinda bir modelin
    kazanandan anlamli farki yok" DEMEK DEGILDIR - olculmedi.

11. **SVR hic kosulmadi.** `GENIS_KOSU_HARIC` ile disarida; O(n^2) kernel,
    350-472 bin satirda pratikte imkansiz. "10 model" ifadesi her yerde
    SVR haric anlamina gelir.

12. **Genis kosu yalnizca K=tum'de.** Model x pencere etkilesimi 10 model
    icin olculmedi; `doygunluk_ozet_model_pencere.csv` ve varyans
    ayristirmasi 3 hizli modelin alt kumesine dayanir. Varyans paylari
    (%48,5 yil / %25,2 algoritma / %15,3 hacim) bu alt kumeye ozgudur ve
    10 modele genellenemez.

13. **Ana izgara duvar saati ile log toplami arasinda fark var** (11,0 dk vs
    9,5 dk). Aradaki ~1,5 dk oznitelik onbellegi kurulumu, parquet okuma ve
    disk yazimi; hucre basina degil kosu basina masraf. Olculmedi, ayristirma
    yapilmadi.

14. **`egitim_n` degerleri kolda ayni gorunuyor ama tam ayni degil.**
    `doygunluk_ozet_egri.csv`'de iki kol ayni `egitim_n` ortalamasini
    tasiyor (51442.8, 104031.6, ...) cunku altornekleme hedefi kaydirmali
    pencerenin satir sayisidir. Hucre duzeyinde sapma olabilir (kusur 5).
