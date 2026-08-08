# DKASC replikasyonu - gercek olcum verisiyle sizinti ablasyonu

Durum: TAMAM. Kalite kurallari on-kayda alindi, veri hatti kosuldu ve
donduruldu, ablasyon kosuldu, eslesmis kontrol kosusu kosuldu.

Sadece rapor. Yorum ve makale metni burada degil.

---

## MANSET

**Iki en onemli sizinti TERS YONLERE gidiyor.**

Ayni kod, ayni alti varyant, ayni uc model. Oran = varyantin RMSE'sinin
`temiz` referansa bolumu; etki = `1 - oran`.

| sizinti | PVGIS orani | DKASC orani | simulasyon ne yapiyor |
|---|---|---|---|
| `eszaman` (eszamanli meteoroloji) | 0,046492 | 0,208236 | etkiyi **~4,5 kat ABARTIYOR** |
| `rastgele_kfold` (kronolojik olmayan bolme) | 0,989057 | 0,917946 | etkiyi **~7,5 kat KUCUMSUYOR** |

- `eszaman`: oranlarin orani `0,208236 / 0,046492 = 4,4790`. Simule veride
  sizinti RMSE'yi temizin %4,65'ine indiriyor; gercek dizide ancak
  %20,82'sine.
- `rastgele_kfold`: etki olarak `1 - 0,917946 = 0,082054` (DKASC) ve
  `1 - 0,989057 = 0,010943` (PVGIS); orani **7,4983**. Simule veride
  rastgele bolme neredeyse hicbir sey kazandirmiyor; gercek veride
  kazandiriyor.

**Sonuc: simulasyonla sizinti buyuklugu KALIBRE EDILEMEZ.** Bir yon
abartiliyor, digeri kucumseniyor; ikisinin ayni yonde ve ayni carpanla
sapmadigi olculdu. Kucumsenen taraf - kronolojik olmayan bolme -
literaturdeki EN YAYGIN hatadir.

Iki sizinti dokunmadigi yerde uc kaynak arasinda 0,003 icinde ortusuyor
(asagida, bolum "Eslesmis kontrol"), yani yukaridaki iki fark kurulumun
gurultusu degil.

---

## Faz kunyesi

    faz             : DKASC replikasyonu (gercek olcum kolu, Faz 2'nin
                      esdegeri: sizinti ablasyonu)
    HEAD (not yazilirken)
                    : 2a0036f142768d9054e116ffb0bee92a74f01185
    agac            : bu not commit edildikten sonra temiz
    etiket          : dkasc-replikasyon (anotasyonlu), bu notu iceren
                      commit'e baglanir
    push            : EDILDI
    veri surumu     : f7f644df5e0d1618  (onceki: 24d7f7c2e6e00585)
    PVGIS surumu    : f722a717bac502c2  (DEGISMEDI)

Not kendi commit'inin hash'ini icermez; `dkasc-replikasyon` etiketi o
commit'e baglandigi icin `git show dkasc-replikasyon` ile bulunur.

**Bu notun ilk surumu (`c24f908`) iki seyi YANLIS yaziyordu:** "etiket: YOK -
repoda hic etiket yok" ve "push: YAPILMADI - Faz 2/3/4 ve bu fazin hicbir
commit'i push edilmedi". Ikisi de CLAUDE.md'deki eskimis bir maddeden
kopyalandi ve push oncesi dogrulanana kadar fark edilmedi. Gercek durum:
`faz-2`, `faz-3`, `faz-4` anotasyonlu etiketleri hem yerelde hem uzakta
MEVCUTTU, `origin/main` `bd3e120`'daydi ve Faz 2/3/4 push EDILMISTI.
Push edilmemis olan yalnizca bu fazin dokuz commit'iydi.

### Commit'ler (8)

    6da9109  2026-08-07 07:42  Pre-register the DKASC quality rules before
                               touching the data
    6412cd0  2026-08-08 01:34  Add rules 9-10 and decisions 4-5 before the
                               pipeline is written
    1cb311c  2026-08-08 01:47  Build the DKASC table from six raw years,
                               frozen at 24d7f7c2e6e00585
    604df85  2026-08-08 02:14  Declare the feature set instead of hard-coding
                               it, with two regression proofs
    42ffc05  2026-08-08 02:20  Drop rows whose target is missing, which PVGIS
                               never exposed
    5e90673  2026-08-08 02:31  Correct rule 10, record the rule 6 diagnostic,
                               leave rule 6 alone
    0a9d9e6  2026-08-08 02:32  Apply rule 10's input threshold, refreezing
                               DKASC at f7f644df5e0d1618
    2a0036f  2026-08-08 03:54  Run the DKASC ablation and its matched control,
                               splitting data from features

---

## Degisen dosyalar

    arac/oznitelik_regresyon.py             | 145 ++  YENI
    arac/regresyon_kiyas.py                 |  25 +-
    dkasc_pipeline.py                       | 576 ++  YENI
    dokumanlar/dkasc-kalite-kurallari.md    | 910 ++  YENI
    pv10/config.py                          | 118 +-
    pv10/evaluate.py                        |  18 +-
    pv10/experiment.py                      |  49 +-
    pv10/features.py                        |  62 +-
    pv10/transpozisyon.py                   | 121 ++  YENI
    run_ablasyon.py                         |  65 +-
    sonuclar/ablasyon_dkasc.csv             |  91 ++  YENI
    sonuclar/ablasyon_pvgis_indirgenmis.csv | 127 ++  YENI
    sonuclar/ablasyon_regresyon.csv         | 127 ++  YENI
    sonuclar/ablasyon_regresyon2.csv        | 127 ++  YENI
    14 dosya, 2.525 ekleme, 36 silme

`ham/dkasc/` (6 dosya, ~1,2 GB) ve `veri/dkasc_m6b.parquet` `.gitignore`
kapsamindadir; repoya girmedi.

---

## Yeni ve degisen fonksiyon imzalari

### `pv10/transpozisyon.py` (YENI)

    egik_bilesenler(ghi, dhi, sin_h, cos_theta, egim_derece,
                    albedo=DKASC_ALBEDO, rb_taban=DKASC_RB_TABAN)
        -> tuple[np.ndarray, np.ndarray, np.ndarray]

    transpoze(ghi, dhi, zaman_utc, lat, lon, egim_derece,
              albedo=DKASC_ALBEDO, rb_taban=DKASC_RB_TABAN)
        -> dict[str, np.ndarray]      # Gb_i, Gd_i, Gr_i, G_i, sin_h, cos_theta

    olculene_karsi(ghi, dhi, gti_olculen, zaman_utc, lat, lon, egimler,
                   albedo=DKASC_ALBEDO, rb_taban=DKASC_RB_TABAN)
        -> pd.DataFrame               # egim, n, MBE, MBE_yuzde, RMSE,
                                      # RMSE_yuzde, R2

`cos(theta)` KOPYALANMIS formulden gelmez. Ekvatora bakan (azimut 0) egik
duzlem icin `cos(theta) = gunes_yuksekligi_sin(lat + B, lon, t)` ozdesligi
kullanilir; Faz 2/3/4'un dondurulmus geometri koduna dokunulmadi.

### `dkasc_pipeline.py` (YENI)

    dogrula_klasor(klasor: Path) -> bool
    oku_birlestir(klasor: Path) -> pd.DataFrame
    kurallar_5dk(d: pd.DataFrame) -> tuple[pd.DataFrame, dict]
    transpozisyon_kapisi(d: pd.DataFrame, zorla_egim: float | None = None)
        -> tuple[bool, dict, pd.DataFrame]
    saatlige_topla(d: pd.DataFrame) -> tuple[pd.DataFrame, dict]
    semaya_donustur(s: pd.DataFrame) -> tuple[pd.DataFrame, dict]
    sema_kapisi(s: pd.DataFrame) -> None
    duzenle(klasor: Path, cikti: Path) -> pd.DataFrame

### `pv10/features.py` (DEGISTI)

    _konum_oznitelikleri(g, eszaman, gecikmeli, eszaman_degisken)
        -> pd.DataFrame                                    # imza degisti

    oznitelik_uret(ham, eszaman=False,
                   gecikmeli=GECIKMELI_DEGISKEN,
                   eszaman_degisken=ESZAMAN_DEGISKEN)      # iki yeni parametre
        -> pd.DataFrame

    oznitelik_kolonlari(o) -> list[str]                    # haric kumesi buyudu

Uc davranis degisikligi, ucu de PVGIS'te ISLEMSIZ (olculdu):

1. `zorunlu` dropna listesinin basina `"y"` eklendi.
2. `eszaman` dalindaki `if d in g` sessiz atlamasi KALDIRILDI; beyan edilen
   bir degisken yoksa `KeyError` firlar.
3. `kismi` ve `ariza` sutunlari VARSA `o`'ya tasinir; `oznitelik_kolonlari`
   ikisini de dislar, yani oznitelik OLMAZLAR.

### `pv10/evaluate.py` (DEGISTI)

    metrikler(y, tahmin, persistence=None, kapasite_w=KAPASITE_W)
    etki_buyuklugu(rmse_a, rmse_b, kapasite_w=KAPASITE_W)

### `pv10/experiment.py` (DEGISTI)

    OznitelikOnbellegi(ham, gecikmeli=GECIKMELI_DEGISKEN,
                       eszaman_degisken=ESZAMAN_DEGISKEN)
    hucre_kos(onbellek, varyant_ad, model_ad, test_yil,
              kapasite_w=KAPASITE_W) -> dict
    izgara_kos(ham, varyantlar, model_adlari, yillar, log_yolu,
               ilerleme=print, gecikmeli=GECIKMELI_DEGISKEN,
               eszaman_degisken=ESZAMAN_DEGISKEN,
               kapasite_w=KAPASITE_W) -> pd.DataFrame

`hucre_kos` icinde iki yeni, sutun varligina bagli dal:
- `kismi` bayrakli satirlar BOLMEDEN ONCE ornek havuzundan cikarilir
  (kronolojik ve rastgele kollar ayni havuzu bolsun diye).
- `ariza` bayrakli satirlar YALNIZCA degerlendirme maskesinden cikarilir.

### `arac/oznitelik_regresyon.py` (YENI)

    referans_modul(commit: str, gecici: Path) -> tuple[ModuleType, int]
    cerceve_kiyas(a: pd.DataFrame, b: pd.DataFrame, ad: str) -> list[str]
    main() -> int

### `arac/regresyon_kiyas.py` (DEGISTI)

`--anahtar` bayragi eklendi (varsayilan `kol,pencere,test_yil,model,tohum`).
`durum` ve `pencere` islemleri sutun varligina baglandi. Faz 4 cagrisi
DEGISMEDI.

### `run_ablasyon.py` (DEGISTI)

    log_yolu(etiket: str | None) -> Path
    OZNITELIK_SETLERI = {"gufbd": (...), "dkasc": (...)}

Yeni bayraklar: `--veri`, `--set {gufbd,dkasc}`, `--etiket`.
`--set` veya `--veri` varsayilan disi iken `--etiket` verilmezse kosu
BASLAMAZ.

---

## Config sabitleri ve degerleri

    DKASC_HAM               = <kok>/ham/dkasc
    DKASC_VERI              = <kok>/veri/dkasc_m6b.parquet
    DKASC_VERI_SHA16        = "f7f644df5e0d1618"
    DKASC_BASLANGIC_YIL     = 2017
    DKASC_BITIS_YIL         = 2022
    DKASC_TEST_YILLARI      = (2018, 2019, 2020, 2021, 2022)
    DKASC_KONUM             = "dkasc_m6b"
    DKASC_LAT               = -23.7621
    DKASC_LON               = 133.8744
    DKASC_UTC_OFSET         = 9.5
    DKASC_KAPASITE_W        = 5250.0
    DKASC_HEDEF_DIZI        = "92_DKA_M6_B_Phase_Active_Power"
    DKASC_YEDEK_DIZI        = "71_DKA_M2_C_Phase_Active_Power"
    DKASC_SUTUN_SAYISI      = 197
    DKASC_YUVA_DK           = 5
    DKASC_SAAT_YUVA         = 12          # hedef ve degerlendirme
    DKASC_GIRDI_YUVA        = 9           # girdi
    DKASC_ETIKET_ORTA_DK    = 2.5
    DKASC_RH_UST            = 100.0
    DKASC_RH_BAYRAK         = 105.0
    DKASC_DHI_ORAN_BAYRAK   = 1.05
    DKASC_GUC_OLU_BOLGE     = 0.05        # kW
    DKASC_G0_CARPAN         = 1.5
    DKASC_ARIZA_GHI         = 200.0
    DKASC_T_ALT             = -10.0
    DKASC_T_UST             = 50.0
    DKASC_T_RAY             = -39.0
    DKASC_GUNES_SABITI      = 1367.0
    DKASC_EGIM              = 20.0
    DKASC_ALBEDO            = 0.20
    DKASC_RB_TABAN          = 0.05
    DKASC_KAPI_RMSE_YUZDE   = 9.0
    DKASC_KAPI_MBE_YUZDE    = 2.0
    DKASC_KAPI_EGIM_ARALIK  = (11.0, 20.0)
    DKASC_KAPI_SIN_H        = 0.10
    DKASC_KAPI_GHI          = 20.0
    DKASC_EGIM_TARAMA       = (0.0, 36.0, 1.0)
    DKASC_GECIKMELI         = ("P", "G_i", "T2m")
    DKASC_ESZAMAN           = ("G_i", "T2m")
    DKASC_KESIF_SAYIM       = {8 kural: (beklenen, aciklama)}

`KAPASITE_W = 1000.0` DEGISMEDI.

---

## Uretilen cikti dosyalari ve semalari

### Dondurulmus veri - `veri/dkasc_m6b.parquet` (commit EDILMEZ)

52.584 satir x 23 sutun. Saatlik, yerel ACST izgarasi, 2017-01-01 00:00 ..
2022-12-31 23:00.

    konum         str      "dkasc_m6b"
    time_utc      dt64     time_local - 9:30  (dakikasi :30)
    time_local    dt64     yerel ACST saat etiketi, HH:00
    time_gozlem   dt64     time_utc + 30 dk = saatin MERKEZI; butun gunes
                           geometrisi bundan hesaplanir
    lat, lon      f64      -23.7621 / 133.8744
    utc_ofset     f64      9.5
    P             f64      W  (DKASC kW x 1000)
    G_i           f64      W/m2, 20 deg / kuzey duzlemi
    Gb_i, Gd_i, Gr_i f64   G_i'nin bilesenleri; G_i = Gb_i + Gd_i + Gr_i
    H_sun         f64      derece, time_gozlem'de; SADECE gunduz maskesi
    T2m           f64      C
    GHI, DHI      f64      W/m2, yatay (tasinir, oznitelik DEGIL)
    RH            f64      % (tasinir, oznitelik DEGIL)
    ariza         bool     kural 7 - degerlendirmeden cikar, egitimden ASLA
    kismi         bool     kural 10 - 9..11 yuva; gecikme KAYNAGI, ornek DEGIL
    yuva          f64      o saatteki dolu 5 dk yuvasi sayisi (0-12)
    rh_bayrak     bool     kural 2
    dhi_bayrak    bool     kural 3
    sin_h_maks    f64      saatin 12 yuvasindaki en yuksek sin(h)

### Kunye - `veri/dkasc_veri_surumu.txt` (commit EDILMEZ)

Kosunun kendi sartlarini kaydeder: hash, satir sayilari, koordinat ve
"dis kaynakla dogrulandi" isareti + kaynak, etiket varsayimi, geometri
konvansiyonu, transpozisyon parametreleri, kapi olcumleri, negatif kontrol
sonucu, ruzgar yoklugu, H_sun'un turetilmis olmasi.

### Ablasyon loglari (commit EDILIR)

    sonuclar/ablasyon_dkasc.csv              90 hucre
    sonuclar/ablasyon_pvgis_indirgenmis.csv 126 hucre   [eslesmis kontrol]
    sonuclar/ablasyon_regresyon.csv         126 hucre   [regresyon kaniti 1]
    sonuclar/ablasyon_regresyon2.csv        126 hucre   [regresyon kaniti 2]

Sema `sonuclar/ablasyon.csv` ile AYNI: `varyant, model, test_yil, egitim_n,
MAE, RMSE, nRMSE_ortalama, nRMSE_kapasite, R2, n, RMSE_persistence, skill,
egitim_sn`.

### Belge

    dokumanlar/dkasc-kalite-kurallari.md    910 satir, ON-KAYIT

---

## Kapi / invaryant sonuclari

### Kapi 1 - transpozisyon, olculen GTI'ye karsi

Esikler kosudan ONCE `config.py`'ye yazildi.

| olcut | esik | gozlenen | sonuc |
|---|---|---|---|
| n | - | 254.740 | - |
| RMSE-optimal egim | 11-20 derece | **18** | GECTI |
| RMSE | <= %9,0 | **%7,288** | GECTI |
| \|MBE\| | <= %2,0 | **%+0,577** | GECTI |
| R2 | - | 0,98231 | - |

### Kapi 1N - NEGATIF KONTROL (zorunlu)

Kapi kasten `B = 0` derece ile cagrilir; KIRMIZI yanmasi BEKLENIR.

| olcut | beklenen | gozlenen | sonuc |
|---|---|---|---|
| RMSE | > %9 | **%15,113** | KIRMIZI (dogru) |
| MBE | \|.\| > %2 | **%-5,982** | KIRMIZI (dogru) |
| gecti | False | **False** | BEKLENEN |

Negatif kontrol GECERSE pipeline `SystemExit` ile durur. Invaryant 5 dersi:
yanlisi yakalayamayan kapi islevsizdir.

### Kapi 2 - sema

- zorunlu sutunlar mevcut: GECTI
- `WS10m` YOK: GECTI (karar 1)
- `G_i == Gb_i + Gd_i + Gr_i`: maks fark **0,0** (ilk kosuda 4,027e+00 ile
  KIRMIZI yandi, asagida)
- `H_sun > 0` olan satir var: GECTI
- 12 yuvanin HEPSI ufkun altindayken `G_i > 0` olan satir: **0** GECTI
- `kismi` bayrakli satir sayisi > 0: **1.145** GECTI
- `kismi` satirlarda G_i ve P dolu: GECTI
- 12/12 olup `kismi` bayrakli satir: **0** GECTI
- `kismi` satirlarda yuva >= 9: GECTI

### Kapi 3 - dondurma tekrarlanabilirligi

Ayni girdiyle iki AYRI surec sirayla kosuldu.

| kosu | sha256_16 |
|---|---|
| 1 | f7f644df5e0d1618 |
| 2 | f7f644df5e0d1618 |

Ilk dondurma (girdi esigi 12/12) da iki surecte `24d7f7c2e6e00585` verdi.

### Kapi 4 - on-kayitli kural sayimlariyla kiyas

Kosu her kural icin gozleneni kesif sayimiyla yan yana basar.

| kural | gozlenen | kesif | fark | beklenen miydi |
|---|---|---|---|---|
| k2_bayrak | 5 | 5 | 0 | EVET, birebir |
| k2_kirpilan | 5.054 | 5.054 | 0 | EVET, birebir |
| k3_bayrak | 5 | 5.134 | -5.129 | EVET, DUSMESI beklendi |
| k3_duzeltilen | 67 | 6.146 | -6.079 | EVET, DUSMESI beklendi |
| k6_eksige_cevrilen | 1.117 | 1.126 | -9 | EVET, yakin beklendi |
| k9_t_eksige_cevrilen | 3.046 | 3.046 | 0 | EVET, birebir |
| k9_rh_eksige_cevrilen | 1.649 | 1.649 | 0 | EVET, birebir |
| k5_negatif | 1.825 | 1.825 | 0 | EVET, birebir |

Sekizin altisi birebir. Ikisinin dusmesi belgede kosudan ONCE yazilmisti:
kural 1 gece GHI/DHI'yi sifirladigi icin `DHI > GHI` neredeyse kalmiyor.
Kural 6'daki 9 satirlik fark, kural 1'in once kosmasi ve gunes konumunun
etiket + 2,5 dk'dan hesaplanmasindan.

### Regresyon kanitlari (uretim kodu degistigi icin zorunlu)

**1. Oznitelik cercevesi - bit duzeyinde.** Referans `features.py` commit
`1cb311c`'ten BYTE DUZEYINDE cikarilip gecici bir pakete konur (tek karakter
degistirilmez; `from .config` calissin diye pakete kopru koyulur).

| varyant | referans sekil | yeni sekil | deger sayisi | sonuc |
|---|---|---|---|---|
| eszaman=False | (524742, 34) | (524742, 34) | 17.841.228 | BIREBIR |
| eszaman=True | (524742, 38) | (524742, 38) | 19.940.196 | BIREBIR |

`oznitelik_kolonlari` da ayni (29 ve 33 sutun). Bu kanit UC KEZ kosuldu:
tuple parametrelemesinden sonra, `y` dropna'sindan sonra, bayrak
tasimasindan sonra. Ucunde de birebir.

**2. Uctan uca ablasyon - toleranssiz.** Tum PVGIS ablasyonu yeniden
kosuldu ve `sonuclar/ablasyon.csv` ile alan alan `==` ile kiyaslandi.

| kosu | hucre | alan | karsilastirma | fark |
|---|---|---|---|---|
| `ablasyon_regresyon.csv` | 126 | 9 | 1.134 | **0** |
| `ablasyon_regresyon2.csv` | 126 | 9 | 1.134 | **0** |

Kiyaslanan alanlar: `egitim_n, n, RMSE, MAE, R2, nRMSE_kapasite,
nRMSE_ortalama, skill, RMSE_persistence`. Ilki oznitelik seti + kapasite
parametrelemesini, ikincisi bayrak dallarini kanitlar.

**3. Faz 4 invaryant kapisi.** `run_doygunluk.py --dogrula` -> **18/18
GECTI**, 1,8 dakika. Referans degerler degismedi: K=1 @ 2023 `egitim_n` =
51.414, isinma = 191, invaryant 4'te uc modelin ucunde de mutlak fark 0,0
(141,343658 / 136,502929 / 137,168967).

**4. Gecikme zaman-dogrulugu (DKASC'ye ozgu).** Oznitelik tablosundaki her
gecikme sutunu, ham tablodan `time_utc - k saat` ile cekilen degerle
karsilastirildi.

| sutun | zaman-dogru | uyusmayan |
|---|---|---|
| P_lag24 / P_lag48 / P_lag168 | True | 0 / 0 / 0 |
| G_i_lag24 / G_i_lag48 / G_i_lag168 | True | 0 / 0 / 0 |
| T2m_lag24 / T2m_lag48 / T2m_lag168 | True | 0 / 0 / 0 |

Bu, tam saatlik izgaraya reindex adiminin sinandigi yerdir. Reindex
olmadan `shift(24)` 24 SAAT degil 24 SATIR oncesini alirdi ve hicbir yerde
hata firlamazdi.

---

## Kosu istatistikleri

### Veri hatti

    dogrula   : 6/6 dosya TAMAM, 197 sutun, alti yilda ayni sema
    duzenle   : ~4 dakika (okuma agirlikli), tek surec

    okunan damga                621.933   (takvim disi 6 x 288 = 1.728 kirpildi)
    tam 5 dk izgarasi           631.008
    hic olmayan damga             9.075   (%1,4382)
    var olan ama tamamen bos        473   (okunan 8 sutunun hicbirinde deger yok)

    kural 1  gece izgara satiri 316.111
             sifirlanan deger 1.176.730
    kural 2  bayrak                    5   kirpilan          5.054
    kural 3  bayrak                    5   duzeltilen           67
    kural 6  eksige cevrilen       1.117
    kural 9  T eksige cevrilen     3.046   RH eksige cevrilen 1.649
    kural 5  negatif               1.825   eksige cevrilen       0   sifirlanan 331.226
    kural 7  ariza saat                6

    saat toplam                  52.584
    kati (12/12)                 50.375   (%95,7991)  -> hedef ve degerlendirme
    girdi-gecerli (>=9/12)       51.520   (%97,9766)  -> gecikme ve yuvarlanma
    kismi (9..11)                 1.145
    tamamen bos                   1.036
    esik alti (1..8)                 28

    kanal bazinda 12/12 saat (ortak maskeden ONCE):
      GHI 50.621   DHI 51.736   T2m 51.478   P 51.742

    gecis saati (merkez gece, yuvalarin bir kismi gunduz)   2.142
    yil sinirinda UTC kaymasi                                  60

    gunduz ortalama uretim   2.197,58 W  (kapasite 5.250 W)
    yillik toplam            9.361,7 kWh/yil = 1.783,2 kWh/kWp/yil

### Oznitelik katmani (DKASC)

    oznitelik satiri                47.928
      `kismi` bayrakli               1.071   -> ornek DEGIL
      hedef olarak kullanilabilir   46.857
      `ariza` bayrakli                   6   -> degerlendirme disi
      y NaN                              0
    gunduz + hedef gecerli          23.271

    yil basina hedef-gecerli / gunduz:
      2017  7.986 / 3.985      2018  8.337 / 4.153
      2019  7.691 / 3.812      2020  7.705 / 3.801
      2021  7.310 / 3.630      2022  7.828 / 3.890

Kiyas: eski girdi esigiyle (12/12) oznitelik tablosu **1.344** satirdi,
hedef-gecerli **1.321**, 2022'de 57 satir.

### Ablasyon izgaralari

| kosu | hucre | duvar saati | egitim_sn toplami |
|---|---|---|---|
| DKASC | 90 | 0,7 dk | 39,7 |
| PVGIS indirgenmis (eslesmis kontrol) | 126 | ~11 dk | 331,0 |
| PVGIS regresyon 2 | 126 | ~13 dk | 398,6 |

Hepsi hatasiz; `durum="hata"` satiri yok.

---

## Ham ozet tablolar

### 1. Enflasyon - uc kosu yan yana

Oran = varyant RMSE / `temiz` RMSE, yillar ve modeller uzerinde ortalama.

| varyant | PVGIS tam RMSE | PVGIS tam oran | PVGIS indirg. RMSE | PVGIS indirg. oran | DKASC oran |
|---|---|---|---|---|---|
| temiz | 138,1468 | 1,0000 | 138,2064 | 1,0000 | 1,0000 |
| eszaman | 6,4777 | 0,0465 | 9,5959 | 0,0692 | 0,2082 |
| rastgele_kfold | 136,6343 | 0,9891 | 136,8875 | 0,9906 | 0,9179 |
| gece | 98,1564 | 0,7105 | 98,1167 | 0,7099 | 0,7078 |
| olcekleyici | 138,2083 | 1,0004 | 138,2062 | 1,0000 | 1,0016 |
| enkotu | 4,6140 | 0,0331 | 6,7653 | 0,0488 | 0,2170 |

### 2. Eslesmis kontrolun AYRIMI

`oznitelik etkisi = PVGIS indirgenmis - PVGIS tam` (ayni veri, az oznitelik)
`veri etkisi = DKASC - PVGIS indirgenmis` (ayni oznitelik, farkli veri)

| varyant | oznitelik etkisi | veri etkisi | toplam fark |
|---|---|---|---|
| eszaman | **+0,0227** | **+0,1390** | +0,1617 |
| rastgele_kfold | +0,0014 | -0,0726 | -0,0712 |
| gece | -0,0006 | -0,0022 | -0,0028 |
| olcekleyici | -0,0004 | +0,0016 | +0,0011 |
| enkotu | +0,0157 | +0,1682 | +0,1839 |

`eszaman`'daki 0,1617'lik farkin **0,0227'si** (yaklasik yedide biri)
indirgenmis oznitelik setinden, **0,1390'i** verinin kendisinden geliyor.

Ayrimin okunabilir olmasinin sebebi: oznitelik setine dokunmayan uc varyant
uc kaynakta 0,003 icinde ortusuyor ve oznitelik etkileri en fazla 0,0014.
Indirgenmis set, sizintinin kaldirilan kanallardan gectigi yer disinda
hicbir seyi oynatmiyor.

### 3. MODEL KIRILIMI [hipotez ONCEDEN yazildi]

**ON-KAYITLI HIPOTEZ:** rastgele bolmenin gercek veride daha cok ise
yaramasinin sebebi dizi-ozgu gurultunun EZBERLENMESIYSE, kazanc esnek
modelde (HGB) kati modelden (LR) buyuk olmali.

Oran = varyant RMSE / `temiz` RMSE, yillar uzerinde ortalama.
`rk` = `rastgele_kfold`, `es` = `eszaman`.

| model | rk PVGIS tam | rk PVGIS indirg. | rk DKASC | es PVGIS tam | es PVGIS indirg. | es DKASC |
|---|---|---|---|---|---|---|
| Linear Regression | 1,0080 | 1,0080 | 1,0087 | 0,0843 | 0,0907 | 0,2218 |
| Polynomial Ridge | 0,9981 | 1,0010 | 0,9536 | 0,0333 | 0,0589 | 0,1975 |
| Hist Gradient Boosting | 0,9613 | 0,9626 | **0,7915** | 0,0220 | 0,0581 | 0,2054 |

`rastgele_kfold` KAZANCI (`1 - oran`; pozitif = rastgele bolme ISE YARADI):

| model | PVGIS tam | PVGIS indirgenmis | DKASC |
|---|---|---|---|
| Linear Regression | -0,0080 | -0,0080 | -0,0087 |
| Polynomial Ridge | +0,0019 | -0,0010 | +0,0464 |
| Hist Gradient Boosting | **+0,0387** | **+0,0374** | **+0,2085** |

**HIPOTEZ DOGRULANDI.** Kazanc uc kosunun UCUNDE de model esnekligiyle
monoton artiyor. Linear Regression hicbir kaynakta kazanmiyor (-0,0080 /
-0,0080 / -0,0087 - uc sayi da birbirinin ayni). HGB'nin DKASC'deki kazanci
PVGIS'inkinin **5,39 kati** (0,2085 / 0,0387).

Manset farkinin kaynagi da budur: toplam `rastgele_kfold` orani DKASC'de
0,9179, PVGIS'te 0,9891 - fark neredeyse tamamen HGB'den geliyor
(0,7915 vs 0,9613), LR'de fark yok (1,0087 vs 1,0080).

DKASC HGB icin yil bazinda `rastgele_kfold` orani - kirilim tutarli, tek
bir kotu yildan gelmiyor:

| test_yil | HGB | LR | PolyRidge |
|---|---|---|---|
| 2018 | 0,7810 | 1,0367 | 0,9745 |
| 2019 | 0,9633 | 1,2565 | 1,1699 |
| 2020 | 0,7853 | 0,9706 | 0,9244 |
| 2021 | 0,7379 | 0,9150 | 0,8740 |
| 2022 | 0,6902 | 0,8646 | 0,8249 |

HGB 5/5 yilda 1'in altinda; LR 5 yilin 3'unde 1'in ustunde.

`eszaman` icin ayni kirilim (HGB - LR farki): PVGIS tam **-0,0623**,
PVGIS indirgenmis **-0,0327**, DKASC **-0,0163**. Model yayilimi gercek
veride DARALIYOR; eszamanli meteoroloji orada her modele asagi yukari ayni
olcude yariyor.

### 4. DKASC `temiz` referansi - tam kunye

| test_yil | model | egitim_n | n | MAE | RMSE | R2 | nRMSE_ort | nRMSE_kap | skill | RMSE_pers |
|---|---|---|---|---|---|---|---|---|---|---|
| 2018 | Linear Regression | 7.986 | 4.152 | 333,055630 | 555,225215 | 0,852045 | 24,822553 | 10,575718 | 16,977115 | 668,761652 |
| 2018 | Polynomial Ridge | 7.986 | 4.152 | 328,417145 | 544,489757 | 0,857712 | 24,342601 | 10,371233 | 18,582389 | 668,761652 |
| 2018 | Hist Gradient Boosting | 7.986 | 4.152 | 383,868055 | 618,127176 | 0,816623 | 27,634722 | 11,773851 | 7,571379 | 668,761652 |
| 2019 | Linear Regression | 16.323 | 3.812 | 236,838245 | 413,051528 | 0,917444 | 17,371171 | 7,867648 | 14,303202 | 481,991785 |
| 2019 | Polynomial Ridge | 16.323 | 3.812 | 241,106728 | 414,013545 | 0,917059 | 17,411630 | 7,885972 | 14,103610 | 481,991785 |
| 2019 | Hist Gradient Boosting | 16.323 | 3.812 | 268,513091 | 459,488579 | 0,897838 | 19,324114 | 8,752163 | 4,668795 | 481,991785 |
| 2020 | Linear Regression | 24.014 | 3.801 | 310,995277 | 537,446457 | 0,856914 | 23,835161 | 10,237075 | 13,818372 | 623,620686 |
| 2020 | Polynomial Ridge | 24.014 | 3.801 | 302,244297 | 529,661214 | 0,861029 | 23,489894 | 10,088785 | 15,066766 | 623,620686 |
| 2020 | Hist Gradient Boosting | 24.014 | 3.801 | 302,811065 | 543,906912 | 0,853453 | 24,121675 | 10,360132 | 12,782413 | 623,620686 |
| 2021 | Linear Regression | 31.719 | 3.630 | 329,209361 | 580,424205 | 0,834068 | 25,798146 | 11,055699 | 17,302313 | 701,862683 |
| 2021 | Polynomial Ridge | 31.719 | 3.630 | 321,533466 | 579,314811 | 0,834701 | 25,748837 | 11,034568 | 17,460377 | 701,862683 |
| 2021 | Hist Gradient Boosting | 31.719 | 3.630 | 331,891158 | 594,827929 | 0,825730 | 26,438349 | 11,330056 | 15,250099 | 701,862683 |
| 2022 | Linear Regression | 39.029 | 3.890 | 389,245522 | 637,767509 | 0,793450 | 29,869331 | 12,147953 | 15,588153 | 755,542657 |
| 2022 | Polynomial Ridge | 39.029 | 3.890 | 370,724002 | 636,324925 | 0,794383 | 29,801768 | 12,120475 | 15,779087 | 755,542657 |
| 2022 | Hist Gradient Boosting | 39.029 | 3.890 | 378,727983 | 666,005614 | 0,774755 | 31,191840 | 12,685821 | 11,850693 | 755,542657 |

### 5. Kural 6 teshisi [kural DEGISTIRILMEDI]

Yorum kurali olcumden ONCE yazildi: vuruslar alcak guneste yogunlasiyorsa
uygulama yazili niyetle uyusmuyor; gun boyuna yayilmissa kural gercek
sensor sicramalarini yakaliyor.

| olcut | deger |
|---|---|
| vurulan yuva | 1.117 |
| sin h medyani | 0,00223 (yukseklik 0,128 derece) |
| sin h p05 / p95 | 0,00022 / 0,00768 |
| sin h < 0,05 orani | %99,64 (1.113 yuva) |
| KIYAS: butun gunduz yuvalarinda sin h < 0,10 | %7,35 |
| GHI medyani (vurus aninda) | 12,949 W/m2 |
| GHI p05 / p95 / maks | 4,128 / 21,746 / 2015,182 |
| GHI < 20 W/m2 orani | %92,48 |
| G0 medyani (vurus aninda) | 3,103 W/m2 |
| GHI/G0 medyani | 3,071 |
| gunes ogleninden \|sapma\| medyani | 355 dakika |
| oglene 180 dk'dan yakin vurus | **0** |
| 300+ dk uzaktaki vurus | %99,64 |
| sabah / ikindi | 330 / 787 |
| `sin h > 0,05` kisitiyla kalan vurus | **4** (1.117'den) |
| yillik dagilim | 192 / 184 / 189 / 180 / 179 / 193 |
| aylik: sifir olan ay | 0 / 72 |

**SONUC: uygulama, kuralin yazili niyetiyle ALCAK GUNES bolgesinde
uyusmuyor.** Kural yuksek isinimda fiziksel bir tavan olarak yazilmisti;
pratikte 0,128 derece yukseklikte, 12,9 W/m2'lik degerlerde atesliyor.
Mekanizma: `G0 = E0 x sin h` ufka yaklasirken cokuyor, oysa kural 1'in
olctugu piranometre ofseti ayni mertebede (gece medyani 2,2921, p99
9,9649 W/m2) ve ufkun hemen ustunde artik sifirlanmiyor - `1,5 x G0`
cizgisi sensorun kendi gurultusunun ICINE dusuyor. Kural aradigini da
yakaliyor ama nadiren: `sin h > 0,15` olan 2 vurus var, birinin GHI'si
2015,182 W/m2.

**KURAL DEGISTIRILMEDI.**

### 6. Kural 10 - duzeltme oncesi ve sonrasi

Belgede yazili "Etkilenen: 61 saat (%0,116)" HAM veride olculmustu.
Uretimde kural 10 YEDINCI adimdir; kural 6 ve 9 ondan once kosar.

| kaynak | saat | oran |
|---|---|---|
| tamamen bos (0/12) | 787 | %35,63 |
| kismi gercek olcum (1-11 yuva) | 62 | %2,81 |
| ham 12/12 TAMDI, kural dusurdu | 1.360 | %61,57 |
| - kural 6 (GHI) | 1.115 | |
| - kural 9 (T2m) | 257 | |
| toplam gecersiz | 2.209 | %4,2009 |

IZOLE tek saatlerin (1.128 adet) kaynagi:

| kaynak | sayi | oran |
|---|---|---|
| tamamen bos | **0** | %0,00 |
| kismi gercek olcum | 29 | %2,57 |
| ham TAM, kural dusurdu (HEPSI kural 6) | **1.099** | %97,43 |

Girdi esigi secenekleri (olculdu, secim yapilmadan once):

| girdi esigi | oznitelik satiri | hedef olarak kullanilabilir | oran |
|---|---|---|---|
| 12/12 (eski) | 1.344 | 1.321 | %2,51 |
| >= 11 yuva | 46.109 | 44.856 | %85,30 |
| **>= 9 yuva (SECILEN)** | **48.162** | **46.857** | **%89,11** |
| >= 6 yuva | 48.557 | 47.244 | %89,84 |
| >= 3 yuva | 49.007 | 47.686 | %90,69 |
| >= 1 yuva | 49.181 | 47.854 | %91,00 |
| *(kiyas) K=1 dogrusal ara deger* | *48.044* | *46.748* | *%88,90* |

Ara deger, uydurma sayi ekleyerek DAHA AZ satir kurtariyor (46.748 <
46.857). Sebep, bu saatlerin bos olmamasi.

### 7. Transpozisyon modeli secimi (kosudan onceki olcum)

254.741 satirda, olculen egik piranometreye karsi:

| egim | izo MBE | izo RMSE | izo R2 | Hay-Davies MBE | HD RMSE | HD R2 |
|---|---|---|---|---|---|---|
| 0 | -37,5594 | 94,8296 | 0,92370 | -37,5594 | 94,8296 | 0,92370 |
| 11 | -6,5823 | 54,2796 | 0,97500 | -3,2986 | 52,2441 | 0,97680 |
| 14 | -1,3145 | 48,6780 | 0,97990 | +2,6894 | 47,7497 | 0,98070 |
| 16 | +1,4234 | 46,6126 | 0,98160 | +5,8635 | 46,9048 | 0,98134 |
| **18** | +3,5389 | **45,9182** | **0,98212** | +8,3797 | 47,6904 | 0,98070 |
| 20 | +5,0299 | 46,5254 | 0,98160 | +10,2354 | 49,8771 | 0,97890 |
| 30 | +3,1107 | 63,3162 | 0,96600 | +9,5924 | 72,8611 | 0,95500 |

Izotropik, Hay-Davies'ten iyi. 20 derecelik duzlemde iki modelin farki
ortalama +5,206 W/m2 (+%0,824), p99 31,901, maks 103,991.

---

## TEMEL RMSE'LER KIYASLANAMAZ

**554,0050 W (DKASC) ile 138,1468 W (PVGIS) YAN YANA KONULMAZ.** Uc ayri
sebep, hicbiri metodolojik degil:

1. **Kapasite farkli.** DKASC hedef dizisi M6_B 5.250 W anma gucunde;
   PVGIS kurulumu 1.000 W (1 kWp). Mutlak W cinsinden RMSE dogrudan
   kapasiteyle olceklenir.
2. **Konum kumesi farkli.** DKASC TEK saha (Alice Springs, yari col, cok
   berrak, alti yil yagis ortalamasi 230,7 mm). PVGIS ALTI saha havuzlanmis
   ve iclerinde Leipzig gibi bulutlu kita ikliminde yuksek enlem noktalari
   var. Havuzlanmis alti konumun hata dagilimi tek sahaninkiyle ayni sey
   degildir.
3. **Yil kumesi farkli.** DKASC 2018-2022 (bes test yili), PVGIS
   2017-2023 (yedi).

Kapasiteye gore normalize edilse bile kiyas duzelmez, yalnizca yaklasir:
`nRMSE_kapasite` DKASC `temiz` icin %10,55 (554,0050 / 5.250), PVGIS icin
%13,81 (138,1468 / 1.000). Aradaki fark iklim ve havuzlama farkidir,
yontem farki degil.

**KIYASLANABILIR OLAN ORANLARDIR.** Her oran kendi kosusunun kendi `temiz`
referansina bolunur; kapasite, iklim ve konum sayisi paydada ve payda ayni
sekilde bulundugu icin sadelesir. Makalede iki temel sayi yan yana
KONMAYACAK; kiyas yalnizca oran duzeyinde yapilacak.

---

## ON-KAYIT ZINCIRI

Iddia: kural secimi post-hoc DEGILDIR. Dayanak dosya duzeyinde `git log`.

    git log --follow dokumanlar/dkasc-kalite-kurallari.md
    git log --follow dkasc_pipeline.py

| ne | commit | zaman | veri islendi mi |
|---|---|---|---|
| Kural 1-8a, Karar 1-3 | `6da9109` | 2026-08-07 07:42 | HAYIR |
| Kural 9, Kural 10, Karar 4, Karar 5, uygulama sirasi | `6412cd0` | 2026-08-08 01:34 | HAYIR |
| `dkasc_pipeline.py`'nin ILK SATIRI | `1cb311c` | 2026-08-08 01:47 | - |
| Kural 10 duzeltmesi + kural 6 teshisi | `5e90673` | 2026-08-08 02:31 | pipeline kosuldu, ABLASYON KOSULMADI |
| Kural 10'un uygulanmasi, yeniden dondurma | `0a9d9e6` | 2026-08-08 02:32 | ayni |
| DKASC ablasyonu | `2a0036f` | 2026-08-08 03:54 | EVET |

Isaretsiz kural = veri islenmeden once sabitlendi. `[SONRADAN eklendi]`
isaretli olanlar:

- **Kural 9** (sicaklik) - 8 Agustos. Neden sonradan: 7 Agustos'ta yazilan
  sekiz kural sicakligi ele almiyordu; eksiklik bolum 4 madde 6'da ACIK
  KUSUR olarak kayitliydi.
- **Kural 10** (saatlik toplama) - 8 Agustos. Neden sonradan: toplama bir
  islem olarak yaziliydi ama eksik yuva davranisi tanimsizdi.
- **Kural 10 duzeltmesi** (girdi esigi) - 8 Agustos, ikinci duzeltme.
  Eski "61 saat" sayisi USTU CIZILEREK birakildi, silinmedi.
- **Karar 4** (izotropik transpozisyon + kapi) - 8 Agustos. Karar 2
  "standart transpozisyon" diyordu ama modeli soylemiyordu.
- **Karar 5** (geometri saat merkezinden) - 8 Agustos.
- **Kural 6 teshisi** - 8 Agustos. Kural DEGISTIRILMEDI; yalnizca olculdu.
- **Bolum 4'un 1, 6, 12, 13, 14. maddeleri** - 8 Agustos.

Zayif nokta, acikca: `5e90673` ve `0a9d9e6` commit'lerinin ICERIGI pipeline
yeniden kosulmadan once yazildi ama COMMIT'ler kosudan sonra atildi (madde
13 sonuc hash'ini tasimak zorunda oldugu icin). Git bunu kanitlayamaz.
Kanitlayabildigi sey, ablasyonun `2a0036f`'te, kural metinlerinden 83 dakika
SONRA kosuldugudur - yani kurallar ablasyon sonuclarina bakilarak
yazilmamistir.

`pv10/ozet.py` ile ayni disiplin: sonradan eklenen AYRI dosyaya/AYRI
commit'e gider ve isaretlenir.

---

## Alinan kararlar ve gerekceleri

### 1. Oznitelik seti BEYAN EDILEN TUPLE, bayrak DEGIL

DKASC'de `Wind_Speed` alti yilin 72 ayinin 72'sinde de bos. Uc secenek
degerlendirildi:

- (a) `oznitelik_uret`'e parametre - SECILDI
- (b) `pv10/dkasc_features.py` kopyasi - REDDEDILDI
- (c) baska - onerilmedi

(b) reddedildi cunku kural 4 ("oznitelik tanimlari GUFBD ile birebir ayni
kalmali") kopya ile DOGRULANAMAZ hale gelir: `features.py`'de bir satir
degisirse kopya sessizce eski tanimi tasir, iki kol farkli oznitelik
uretirken makale "ayni oznitelikler" der. Invaryant 5 dersi.

`ruzgar: bool` yerine tuple secildi: bayrak sapmayi uretim koduna gomer ve
her veri setinde bir bayrak daha birikir; beyan edilen tuple oznitelik
setini kod yolunun yan etkisi olmaktan cikarip RAPORLANABILIR bir degere
cevirir - makalede raporlanacak sey de zaten budur.

### 2. Regresyon kaniti CERCEVE duzeyinde, ozet duzeyinde DEGIL

Ablasyonun yeniden kosulmasi ~30 metrik kiyaslar; oznitelik matrisi
ablasyonun duyarsiz oldugu bir sutunda degisse ozet yine tutardi. Bu yuzden
cerceve-birebir testi EKLENDI (37,8 milyon deger). Ama tek basina da
yetmez - `kapasite_w` `evaluate.py`'ye dokunuyor ve orasi Faz 2/3/4'un
hepsinde kullaniliyor - bu yuzden UCTAN UCA ablasyon da yeniden kosuldu.
Ikisi birlikte.

### 3. Kural 6 DEGISTIRILMEDI

Ateslenme oruntusu asagi akista sorun yarattigi icin ON-KAYITLI bir esigi
gevsetmek, tam olarak bu makalenin elestirdigi post-hoc davranistir.
Olculdu, kayitta, degistirilmedi. Etkisi kural 10'un yeni haliyle zaten
notrleniyor: kural 6 saatte tipik olarak TEK yuva dusurur, 11 kalir, saat
girdi esigini gecer.

### 4. Kural 10: esik GIRDIDE gevser, HEDEF/DEGERLENDIRMEDE siki kalir

Ayni desen projede zaten var: gece satirlari egitimde kalir, gunduz
filtresi yalnizca degerlendirmede uygulanir; kural 7'nin `ariza` bayragi da
yalnizca degerlendirmeden cikarir. Filtre girdide degil ciktida.

Ara deger REDDEDILDI, cunku olculdu ve daha kotu cikti (46.748 < 46.857) -
uydurma sayi ekleyerek daha az satir kurtariyor. `min_periods` gevsetmesi
GUNDEME ALINMADI: 168 saatlik ortalama ile "son 168 saatin en az 120'sinin
ortalamasi" farkli kestiricilerdir, kural 4'u dogrudan ihlal eder.

Esik 9 secildi, 1 degil: kural 10'un ilk gerekcesi hala gecerli - uc
yuvadan alinan ortalama ile on ikiden alinan ayni kestirici degildir. 9/12
saatin ucte dordu; 1/12 saatlik ortalama kiligina girmis nokta ornegi.
1'in kazanci 997 satir (%1,9), bedeli kendi gerekcemizi bosa cikarmak.

### 5. `kismi` satirlarin P'si SILINMEDI

Silinseydi `P_lag24` de duserdi ve kapatilmaya calisilan bosluk sorunu geri
gelirdi. Dislama bolme asamasinda bayrakla yapilir. Kural 7'nin `ariza`
bayragiyla ayni mekanizma, farkli kapsam: `kismi` hem egitim hedefinden hem
degerlendirmeden cikar, `ariza` yalnizca degerlendirmeden.

### 6. Kapsam 2017-2022, 2022 ELENMEDI

Anormal oldugu icin yil cikarmak post-hoc secimdir. 2022 alti yilin en
yagislisi (445,6 mm); duraganlik disi davranis gercek dunyada vardir,
raporlanir. Iki dis teyit: (i) sahaya 2023'te batarya kuruldu, yani 2023 ve
sonrasi ayni fiziksel kurulum degil - kapsamin 2022'de bitmesi bagimsiz
olarak dogru; (ii) "Class A" hava verisi ayri bir projeye (NTSR) ait,
yillik dosyalara hic girmiyor - Nisan 2019 kiriginin neden cikmadigini
aciklar.

### 7. Saatlik ortalama ORTAK yuva maskesinden

Girdi esigi gevsedikten sonra her sutunu kendi dolu yuvalari uzerinden
ortalamak `G_i = Gb_i + Gd_i + Gr_i` ozdesligini bozdu (maks fark
4,027 W/m2, sema kapisi yakaladi): kural 6 yalniz GHI'yi dusurdugunde o
yuvada `Gd_i` durur ama `Gb_i`, `Gr_i`, `G_i` duser. Bir yuva ancak DORT
kanalin da dolu oldugu yuvadir.

### 8. Sema kapisi ilk halinde YANLISTI, duzeltildi

Ilk hali "H_sun <= 0 ise G_i == 0" diyordu ve 1.230 satirda kirmizi yandi.
Olculdu: 2.192 gunun HER BIRINDE tam olarak bir saat, merkez ufkun
altindayken yuvalarin bir kismi ustunde. Satirlar dogru, iddia yanlisti -
`H_sun` saatin merkezinde ANI bir deger, `G_i` ise saat boyunca ORTALAMA.
Kapi artik kuralin gercekten soyledigini sinar: on iki yuvanin HEPSI ufkun
altindaysa isinim sifir olmali.

### 9. `--etiket` verilmeden farkli set/veri kosulmaz

`--set` veya `--veri` varsayilan disi iken `--etiket` yoksa kosu
`SystemExit` ile durur. Faz 4'teki ayni dersin Faz 2'ye tasinmasi: iki
farkli deneyin hucreleri ayni tabloda karisirsa ozet ortalamalari kirlenir.

---

## Bilinen kusurlar ve varsayimla gecilen her sey

1. **Kural 6'nin alcak gunes uyusmazligi.** Olculdu (bolum "Ham ozet
   tablolar", 5), DEGISTIRILMEDI. 1.117 vurusun %99,64'u sin h < 0,05'te,
   GHI medyani 12,949 W/m2, gunes ogleninden medyan 355 dakika uzakta.
   Kuralin yazili niyeti (yuksek isinimda fiziksel tavan) ile uygulamasi
   alcak gunes bolgesinde uyusmuyor. Makalede boyle raporlanacak.

2. **Ruzgar kanallari YOK - kural 4'ten sapma.** `WS10m` ve gecikmeleri
   cekirdek sette; DKASC'de `Wind_Speed` 621.933 satirda tek dolu deger
   icermiyor, `Wind_Direction` %99,9038 dolu ama araligi pusula araligi
   degil (min -6,9796, maks 11.596,1650) ve isaret/birim gelenegi zaman
   icinde iki kez degisiyor. Replikasyon, PVGIS kurulumunun birebir kopyasi
   DEGIL, ruzgarsiz bir varyantidir. Eslesmis kontrol kosusu bu sapmanin
   buyuklugunu OLCTU (oznitelik etkisi sutunu), ama PVGIS tarafinda
   ruzgarin permutasyon onemi HALA olculmedi.

3. **`H_sun` geometriden TURETILDI, sizinti kanali eksildi.** PVGIS'te
   `H_sun` PVGIS'in KENDI sutunudur ve bizim Spencer hesabimizdan
   BAGIMSIZDIR; DKASC'de ayni rutinden turetiliyor. Iki sonucu var:
   (i) gunduz maskesi artik geometriden bagimsiz degil - geometride bir
   hata olursa hem maskeyi hem ozniteligi TUTARLI bicimde kaydirir ve
   kendini gizler; (ii) `eszaman` varyantinda `H_sun_eszaman` artik
   `elev_sin`'in deterministik fonksiyonu, yani DKASC kolunda hic sizinti
   TASIMIYOR. Ruzgarla birlikte DKASC'nin `eszaman` varyantinda PVGIS'e
   gore IKI sizinti kanali eksik.

4. **TEK SAHA.** Alti konumlu PVGIS koluna karsi tek dizi (M6_B, sistem 13).
   `konum` tek-sicak kodlamasi tek sabit sutuna (`loc_dkasc_m6b` = 1,0)
   dusuyor - agaclar yok sayar, Ridge merkezleme sonrasi sifirlar, zararsiz
   ama kayitta. DM/bootstrap kumelenmesi de tek konumlu; Faz 3'teki
   "alti konum ayni damgayi paylasir" duzeltmesi burada gecerli degil.

5. **Koordinat DIS KAYNAKLA dogrulandi, iceriden DOGRULANAMADI.**
   Kullanilan -23,7621 / 133,8744. Hakemli kaynak (Theoret. Appl. Climatol.
   2022, doi:10.1007/s00704-022-04166-6) 23 46' G / 133 52' D / 558 m
   veriyor; fark enlemde 0,005, boylamda 0,007 derece. Veriden ic dogrulama
   YETERSIZ cikti: gun uzunlugundan enlem -23,060 derece, ama enlemi 1
   derece oynatinca artik RMS yalnizca 23,35 -> 23,53 dakika degisiyor.

6. **Etiket geleneginde 2,5 dakikalik belirsizlik COZULMEDI.** Aralik SONU
   olcumle elendi (dosyalar 00:00 baslayip 23:55 bitiyor); aralik BASI ile
   ANLIK ornek AYRILAMADI, cunku 2,5 dakikalik etiket ofseti ile boylam
   hatasi ayni imzayi tasiyor. Gozlenen gunes ogleni artigi medyan
   +4,498 dk, sd 17,237, n 1.991; alti yilda 6,00'dan 3,50'ye surukleniyor,
   yani tamami tek bir gelenek farkiyla da aciklanmiyor. Buyuklugu 0,6
   derece saat acisi. Karar 5'in kapattigi 7,5 derecelik hatanin yaninda
   kucuk ama sifir degil.

7. **Transpozisyon ALCAK GUNESTE dogrulanmadi.** Kapi `sin h > 0,10`
   (yukseklik > 5,74 derece) ile sinirli. Uretimde `Rb` paydasi
   `max(sin h, 0,05)` ile tabanlanir; bu taban DOGRULANMAMIS bir secimdir.

8. **Albedo varsayim.** `rho = 0,20`, sahada olculmedi. 20 derecelik
   duzlemde yer terimi GHI'nin %0,60'i; rho'yu 0,10-0,30 araliginda
   oynatmak `G_i`'yi ~±%0,3 kaydirir.

9. **Azimut olculmedi.** Kullanilan ozdeslik (`cos(theta) = sin h(lat+B)`)
   yalnizca azimut = 0 icin gecerli. Diziler belgelenmis olarak Tilt 20 /
   Azi 0 (Solar North); istasyonun egik piranometresinin azimutu bilinmiyor
   ve kapinin artiginin bir kismi buradan geliyor olabilir.

10. **`ranking.py` ve `doygunluk.py` HALA `KAPASITE_W = 1000` kullaniyor.**
    `kapasite_w` parametresi `evaluate.metrikler` ve `evaluate.etki_buyuklugu`'ne
    eklendi ve `experiment.py` (Faz 2) uzerinden gecirildi. Faz 3 (`ranking.py`)
    ve Faz 4 (`doygunluk.py`) modul varsayilanini kullanmaya devam ediyor.
    DKASC Faz 2'de kaldigi surece sorun yok; **Faz 3 veya Faz 4 DKASC'ye
    tasinirsa `kapasite_w` oraya da gecirilmeli**, yoksa `nRMSE_kapasite` ve
    `RMSE_fark_kapasite_yuzde` 5,25 kat kucuk cikar ve hicbir yerde hata
    firlamaz. Bu, bu notun en somut acik isidir.

11. **Yil sinirinda UTC kaymasi.** `time_utc` yerel saatten 9,5 saat geride
    oldugu icin yerel 1 Ocak'in ilk 10 saati bir onceki UTC yilina dusuyor;
    `bolme_indeksleri` `time_utc.dt.year` kullaniyor. Etkilenen: **60
    satir**, bes yil siniri x ~10 saat, oznitelik tablosunun %0,13'u.
    PVGIS kolunda ayni artefakt var ama daha kucuk (Avrupa konumlari icin
    1-3 saat). Duzeltilmedi.

12. **Guc birimi VARSAYIM.** DKASC guc kanallari kW kabul edildi (M6_B maks
    5,5590, anma 5,25 kWp ile tutarli) ve x1000 ile W'ye cevrildi. Sitede
    birim etiketi ayrica dogrulanmadi.

13. **DKASC ablasyonu YALNIZCA uc hizli modelle kosuldu.** Linear
    Regression, Polynomial Ridge, Hist Gradient Boosting. Random Forest,
    Extra Trees ve MLP kosulmadi; Faz 4'te olculen RF/ET nondeterminizmi bu
    kolda hic devreye girmedi.

14. **Faz 3'un esdegeri (siralama kararliligi) DKASC'de KOSULMADI.** Bu not
    yalnizca Faz 2'nin (sizinti ablasyonu) replikasyonunu kapsar.

15. ~~**Etiket yok.**~~ Bu madde YANLISTI, bkz. faz kunyesi. `faz-2`,
    `faz-3` ve `faz-4` anotasyonlu etiketleri zaten mevcuttu ve uzakta da
    vardi; bu faz `dkasc-replikasyon` etiketiyle kapandi. Madde silinmedi,
    duzeltilerek birakildi.

16. **Ortam:** kesif kosularinda `pandas._libs.parsers` DLL'i bir kez
    "Uygulama Denetimi ilkesi bu dosyayi engelledi" hatasiyla yuklenemedi,
    ikinci denemede acildi. pyarrow'da yasananla ayni sinif (Windows Smart
    App Control). SAC ayarina DOKUNULMADI. pyarrow 22.0.0 kullaniliyor.

---

## Calistirma

    python dkasc_pipeline.py dogrula ham/dkasc
    python dkasc_pipeline.py duzenle ham/dkasc

    python run_ablasyon.py --set dkasc --veri veri/dkasc_m6b.parquet \
        --yillar 2018,2019,2020,2021,2022 --etiket dkasc

    python run_ablasyon.py --set dkasc --etiket pvgis_indirgenmis \
        --yillar 2017,2018,2019,2020,2021,2022,2023

    python -m arac.oznitelik_regresyon
    python -m arac.regresyon_kiyas --referans sonuclar/ablasyon.csv \
        --yeni sonuclar/ablasyon_regresyon2.csv \
        --anahtar varyant,model,test_yil --nondet ""

Python komutlari HER ZAMAN `.venv\Scripts\python.exe` ile.
