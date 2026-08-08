# Faz 2 - sizinti ablasyonu  [GERIYE DONUK DERLENDI]

> **Bu not faz bittikten SONRA, koddan ve loglardan geriye donuk derlendi;
> ON-KAYIT IDDIASI TASIMAZ.**
>
> Faz 2 30 Temmuz 2026'da kosuldu ve o gun faz notu URETILMEDI. Bu dosya
> 8 Agustos 2026'da, yalnizca `git log`, commit iceriklerinde donmus kod,
> etiket mesajlari ve `sonuclar/ablasyon.csv` okunarak yazildi.
> `faz-notlari/faz-4.md` ve `faz-notlari/dkasc-replikasyon.md` fazlarin
> KENDI oturumlarinda yazildi ve on-kayit iddiasi tasir; **bu not tasimaz.**
> Ayrimin korunmasi sart: geriye donuk bir not on-kayitliymis gibi
> sunulursa diger notlarin degeri de duser.
>
> Asagida "ANLASILIYOR" diye isaretlenen her sey bir YENIDEN KURGUDUR:
> koddan cikarilmis makul bir aciklamadir, o gun alinmis kararin kaydi
> DEGILDIR. "KAYITLI" diye isaretlenenler o gunku commit'in icinde
> gercekten yaziliydi.

Sadece rapor. Yorum ve makale metni burada degil.

---

## Faz kunyesi

    faz             : 2 (sizinti ablasyonu). Faz 1 (veri hatti) AYNI
                      commit'te; repoda ayri bir Faz 1 milestone'u yok.
    commit          : 2119b44e453d0ebfe716a979bd1e9caf008ef43e
                      2026-07-30 01:58
                      "Leakage-aware PV forecasting: data pipeline and
                       ablation harness"
    etiket          : faz-2 -> 732e5ae (anotasyonlu), commit 2119b44
    not yazildi     : 2026-08-08, GERIYE DONUK
    veri surumu     : f722a717bac502c2  (525.888 satir, 6 konum, 2014-2023)
    push            : EDILDI

### En onemli yapisal gozlem

**Faz 1, Faz 2 ve Faz 3 toplam UC commit'tir ve ucu de 30 Temmuz 2026'da,
16 dakika icinde atilmistir** (01:58, 02:03, 02:14). Bunun iki sonucu var
ve ikisi de makalede savunulmasi gereken yerlerdir:

1. **Karar izi yok.** "Hangi karar ne zaman alindi" sorusu git'ten
   cevaplanamaz; her sey tek bir baslangic commit'inde belirmis.
2. **`sonuclar/ablasyon.csv`, onu ureten kodla AYNI commit'tedir.**
   Yani varyant kumesinin, model alt kumesinin ve test yili kumesinin
   sonuclar GORULMEDEN sabitlendigine dair **dosya duzeyinde kanit
   YOKTUR.** Faz 4'te `pv10/ozet.py`'nin izgaradan once yazildigi
   `git log -- pv10/ozet.py` ile gosterilebiliyor; Faz 2'de karsiligi
   gosterilemiyor.

Bu bosluk, DKASC kolunda kurallarin veri islenmeden once ayri commit'e
alinmasinin (`6da9109`) dogrudan sebebidir. Faz 2 icin geriye donuk olarak
kapatilamaz; **makalede boyle raporlanmalidir.**

---

## Uretilen cikti

### `sonuclar/ablasyon.csv` - 126 satir

Sema: `varyant, model, test_yil, egitim_n, MAE, RMSE, nRMSE_ortalama,
nRMSE_kapasite, R2, n, RMSE_persistence, skill, egitim_sn`

Izgara: **6 varyant x 3 model x 7 test yili (2017-2023) = 126 hucre.**
Hatali hucre yok.

---

## Kurulum - ne KAYITLI, ne YENIDEN KURGU

### Alti sizinti varyanti  [KAYITLI]

`pv10/config.py:SIZINTI_VARYANTLARI`, commit 2119b44 icinde yorumlariyla
birlikte:

    temiz          : makalenin tasarimi (referans)
    eszaman        : hedef saatteki meteoroloji de oznitelik olarak verilir
    rastgele_kfold : kronolojik bolme yerine karistirmali k-fold
    gece           : gece saatleri de degerlendirmeye dahil edilir
    olcekleyici    : standardizasyon/imputasyon tum veriye fit edilir
    enkotu         : eszaman + rastgele_kfold + gece + OLCEKLEYICI
                     (DORT mudahale - bkz. kusur 6)

**Neden bu alti?** `pv10/experiment.py`'nin modul docstring'i (ayni
commit'te, yani KAYITLI) tasarim ilkesini soyluyor: her varyant
**farkli bir mudahale noktasi**dir.

| varyant | mudahale noktasi |
|---|---|
| eszaman | OZNITELIKLERE (hedef saatteki meteoroloji eklenir) |
| rastgele_kfold | BOLMEYE (kronolojik yerine karistirmali) |
| gece | DEGERLENDIRME MASKESINE (gece saatleri dahil) |
| olcekleyici | ON-ISLEMEYE (imputasyon/olcekleme tum veriye fit) |
| enkotu | **DORDUNUN BIRLESIMI** (bkz. kusur 6) |

Dort mudahale noktasi + referans + birlesim = alti. Kume, "literaturde
sik gorulen hatalar" listesinden degil, **pipeline'in mudahale
edilebilecek dort katmanindan** turetilmis.

`ESZAMAN_DEGISKEN = ("G_i", "T2m", "WS10m")` ve ayrica `H_sun_eszaman`
- yani eszaman varyanti DORT kanal sizdirir.  [KAYITLI]

### Uc hizli model  [KAYITLI - gerekce kodda yaziyor]

`pv10/models.py:85-91`, ayni commit'te:

    # --- hesaplama gercekligi ---
    # 350 bin satir x 25 oznitelikte:
    #   Linear / Polynomial Ridge / Hist Gradient Boosting  -> saniyeler
    #   Random Forest, Extra Trees (400 agac), MLP          -> dakikalar, cok RAM
    #   SVR (O(n^2) kernel)                                 -> pratikte imkansiz
    # Ablasyon izgarasi 6 varyant x 8 yil x N model demek; agir modelleri
    # izgaranin her hucresinde kosmak haftalar surer.

    HIZLI_ALTKUME      = (Linear Regression, Polynomial Ridge,
                          Hist Gradient Boosting)
    ABLASYON_ALTKUMESI = HIZLI_ALTKUME + (Random Forest, Neural Network)

`run_ablasyon.py --modeller` varsayilani `hizli`, yani izgara UC modelle
kosuldu. `ablasyon` alt kumesi (bes model) tanimli ama KULLANILMADI -
`ablasyon.csv`'de yalnizca uc model var.

**Bu, `dokumanlar/arastirma-baglami.md`'de "hakemin vuracagi yer" olarak
listelenen soruya birebir denk geliyor:** "Test yili ve model alt kumesi
neye gore secildi? ... hesaplama maliyeti bir gerekcedir ama YAZILMASI
sarttir." Gerekce yazili ve kosuyla ayni commit'te; makalede
alintilanabilir.

Model havuzunun tamami 11 algoritma; hepsinin hiperparametreleri
`models.py`'de sabit ve `SEED = 42`. Hicbiri test setine gore
ayarlanmadi.  [KAYITLI]

### Yedi test yili (2017-2023)  [YENIDEN KURGU - gerekce KAYITLI DEGIL]

`run_ablasyon.py`'nin argparse varsayilani `2017,2018,...,2023` olarak
GOMULU; ne yorum, ne commit mesaji, ne de config sabiti bu secimi
aciklamiyor.

**ANLASILIYOR** (kanit degil): veri 2014'te basliyor ve kronolojik bolme
test yilindan onceki her seyi egitime aliyor. 2017 secilirse en az UC
yillik egitim penceresi garanti ediliyor (2014-2016); 2014-2016 test
yili olarak alinsaydi egitim penceresi sirasiyla 0, 1 ve 2 yil olurdu ve
2014 hic kosulamazdi.

Kiyas icin: Faz 4'te ayni tur secim **KAYITLI**dir -
`pv10/config.py:DOYGUNLUK_TEST_YILLARI` yaninda "K=5 seviyesinin var
olabilmesi icin test yili >= BASLANGIC_YIL + 5 olmali; test yili kumesi
bu yuzden 2019'da basliyor" yaziyor. Faz 2'de bunun karsiligi yok.

**Makalede test yili kumesinin gerekcesi yazilacaksa, kaynagi bu not
DEGIL, yeniden ifade edilmis bir tasarim gerekcesi olmalidir.**

### Bolme ve degerlendirme  [KAYITLI]

- Kronolojik: `yil < test_yil` egitim, `yil == test_yil` test.
- `rastgele_kfold`: ayni satir havuzu (`yil <= test_yil`) karistirilir ve
  **AYNI BOYUTTA** test ayrilir. Test boyutu esit tutuluyor ki fark
  bolmeden gelsin, veri miktarindan gelmesin. `rng = default_rng(SEED)`.
- Degerlendirme: gunduz (`H_sun > 0`); `gece` varyantinda maske kaldirilir.
- Isinma: 168 saatlik gecikme ve yuvarlanan pencereler icin gereken ilk
  gozlemler dusuruluyor (konum basina 191 satir), berrak-gokyuzu orani
  ZORUNLU listeye KONMUYOR - konsaydi butun gece satirlari silinirdi.

---

## Ham sonuclar

### Enflasyon tablosu - varyant duzeyinde (126 hucre, model ve yil uzerinde ortalama)

| varyant | RMSE (W) | R2 | RMSE orani | R2 artisi | fark (W) | fark (%) |
|---|---|---|---|---|---|---|
| temiz | 138,1468 | 0,7277 | 1,0000 | 0,0000 | - | - |
| enkotu | 4,6140 | 0,9995 | **0,0331** | +0,2719 | -133,5328 | -96,66 |
| eszaman | 6,4777 | 0,9992 | **0,0465** | +0,2715 | -131,6691 | -95,31 |
| gece | 98,1564 | 0,8528 | 0,7105 | +0,1251 | -39,9904 | -28,95 |
| rastgele_kfold | 136,6343 | 0,7348 | 0,9891 | +0,0071 | -1,5125 | -1,09 |
| olcekleyici | 138,2083 | 0,7274 | **1,0004** | -0,0002 | +0,0616 | +0,04 |

Uc gozlem, hicbiri yorum degil:

1. **Eszamanli oznitelik sizintisi RMSE'yi yirmi kata yakin dusuruyor**
   (138,1468 -> 6,4777) ve R2'yi 0,7277'den 0,9992'ye cikariyor.
2. **Gece satirlarinin degerlendirmeye karistirilmasi ucte bir dusuruyor**
   (-%28,95). Gece uretimi sifira yakin oldugu icin hata terimi kucuk;
   payda buyuyor, RMSE duser.
3. **Olcekleyicinin tum veride fit edilmesi bu kurulumda PRATIKTE
   ETKISIZ** (+%0,04) ve **rastgele bolme neredeyse etkisiz** (-%1,09).
   Literaturde en cok uyarilan iki hata, bu kurulumda en zararsizlari
   cikti.

Ucuncu madde DKASC kolunda TERSINE DONUYOR: `rastgele_kfold` orani orada
0,9179. Bkz. `faz-notlari/dkasc-replikasyon.md`, "MANSET".

### Model x varyant (RMSE ortalamasi, W)

| model | temiz | eszaman | rastgele_kfold | gece | olcekleyici | enkotu |
|---|---|---|---|---|---|---|
| Hist Gradient Boosting | 136,97 | 3,01 | 131,64 | 97,03 | 137,16 | 2,04 |
| Linear Regression | 140,98 | 11,89 | 142,07 | 100,34 | 140,97 | 8,74 |
| Polynomial Ridge | 136,49 | 4,54 | 136,19 | 97,10 | 136,49 | 3,06 |

Sizintinin buyuklugu MODEL BAGIMLI: `eszaman`'da esnek model (HGB, 3,01 W)
kati modelden (LR, 11,89 W) dort kat fazla yararlaniyor. `rastgele_kfold`
Linear Regression'da RMSE'yi ARTIRIYOR (140,98 -> 142,07).

### Yil bazinda `temiz` RMSE (W) - Faz 3'e kopru

| test_yil | Hist Gradient Boosting | Linear Regression | Polynomial Ridge |
|---|---|---|---|
| 2017 | 135,12 | 138,81 | 133,93 |
| 2018 | 139,00 | 142,61 | 139,43 |
| 2019 | 137,17 | 141,34 | 136,50 |
| 2020 | 136,80 | 140,90 | 136,38 |
| 2021 | 137,10 | 141,37 | 136,83 |
| 2022 | 140,22 | 143,95 | 139,76 |
| 2023 | 133,40 | 137,84 | 132,61 |

Bu tablo Faz 3'un girdisidir; `siralama_rmse.csv` ayni sayilari (uc
ondalikla) tasir.

---

## Faz 2'de KURULMAMIS olan sey

Faz 2'nin cikti tablosunda **hicbir belirsizlik olcusu yoktur**: guven
araligi yok, Diebold-Mariano yok, gurultu tabani yok. `evaluate.py` ayni
commit'te `gun_blogu_bootstrap` ve `diebold_mariano` fonksiyonlarini
ICERIYOR ama `experiment.py` bunlari CAGIRMIYOR.

Yani "eszaman varyanti RMSE'yi %95,31 dusuruyor" ifadesi Faz 2'de
olculmus bir gurultu tabaniyla KIYASLANMAMISTIR. Bu bosluk Faz 3'te
(ikili DM) ve Faz 4'te (esli kumelenmis DM, bootstrap GA, nondeterminizm
olcumu) kapatilmistir, ama Faz 2'nin kendi tablosu icin gecerlidir.

Etki buyuklugu bu varyantlarda o kadar buyuk ki (-%95, -%29) gurultu
tabaninin bunlari degistirmesi beklenmez; **ama +%0,04'luk `olcekleyici`
ve -%1,09'luk `rastgele_kfold` icin durum boyle DEGILDIR.** Bu iki sayi
gurultu mertebesinde olabilir ve Faz 2 bunu olcmemistir.
`dokumanlar/arastirma-baglami.md`'nin 3 numarali iddiasi ("olculmus
gurultu tabani") Faz 2 tablosunun bu iki satiri icin KARSILANMAMISTIR.

---

## Bilinen kusurlar ve varsayimla gecilen her sey

1. **Bu not geriye donuktur.** On-kayit iddiasi tasimaz.
2. **`ablasyon.csv` kodla ayni commit'te.** Varyant/model/yil kumesinin
   sonuclar gorulmeden sabitlendigine dair dosya duzeyinde kanit yok.
3. **Test yili kumesinin (2017-2023) gerekcesi hicbir yerde kayitli
   degil.** Yukaridaki aciklama yeniden kurgudur.
4. **Belirsizlik olcusu yok** (yukariya bak). `olcekleyici` ve
   `rastgele_kfold` satirlari gurultu mertebesinde olabilir.
5. **Uc model, on bir modelin uctu.** Gerekce (hesaplama maliyeti)
   kayitli ama secimin sonuca duyarli olup olmadigi Faz 2'de test
   edilmedi. Faz 4'un genis kosusu on modele cikip ayni yone isaret
   etti.
6. **`enkotu` varyanti DORT mudahaleyi birden tasir:** `eszaman` +
   `rastgele_kfold` + `gece` + **`olcekleyici`**. `SIZINTI_VARYANTLARI`
   tanimi `eszaman=True, rastgele_kfold=True, gece=True,
   olcekleyici_tum=True` icerir.
   `[8 Agustos 2026'da DUZELTILDI]` `config.py`'deki yorum satiri
   o tarihe kadar yalnizca uc mudahale sayiyordu; **kod her zaman
   dogruydu, YORUM eksikti** ve yorum duzeltildi. Makaleye girecek her
   yerde bu varyant **DORT mudahale** olarak tanimlanacaktir. Yanlis
   tanimlanmis bir varyanti raporlamak sizinti makalesinde affedilmez;
   `enkotu`'nun -%96,66'lik degeri tek bir mekanizmaya atfedilemez.
7. **`egitim_sn` ile olculen sure tek makineye ozgudur**; toplam 937,8
   saniye (15,6 dakika) yalnizca egitim, oznitelik uretimi haric.
8. Ortam: pyarrow o gun 25.0.0'di (3 Agustos'ta 22.0.0'a indirildi).
   Faz 2 tablosu 25.0.0 ile uretildi. Surum degisimi sonrasi invaryant
   1-2'nin ablasyon referanslari son basamagina kadar ayni cikti
   (bagil fark 6,050675e-13 ve 7,797529e-12).

---

## Calistirma

    python run_ablasyon.py --tahmin      # once maliyet
    python run_ablasyon.py               # hizli modeller, tum varyantlar
    python run_ablasyon.py --ozet        # mevcut logu ozetle

`--veri`, `--set` ve `--etiket` bayraklari SONRADAN (8 Agustos, `604df85`)
eklendi; Faz 2 kosusunda yoktular.
