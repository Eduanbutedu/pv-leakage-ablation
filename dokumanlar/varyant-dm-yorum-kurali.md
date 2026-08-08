# Faz 2 belirsizlik olcumu - ON-KAYITLI YORUM KURALI

**Yazildigi tarih: 8 Agustos 2026.** Bu dosya, Faz 2 varyantlari icin
HICBIR belirsizlik olcumu yapilmadan once yazildi ve commit edildi.
Amaci `pv10/ozet.py` ve `dokumanlar/dkasc-kalite-kurallari.md` ile ayni:
hangi sonucun neye yorulacagini, sonuc gorulmeden sabitlemek.

Bu dosyaya sonradan eklenen her madde `[SONRADAN eklendi - <tarih>]`
diye isaretlenir.

---

## 0. Neden bu olcum yapiliyor

`sonuclar/ablasyon.csv` alti varyantin RMSE'sini veriyor ama **hicbir
belirsizlik olcusu icermiyor** (`faz-notlari/faz-2.md`, "Faz 2'de
KURULMAMIS olan sey"). Buyuk satirlar icin bu onemsiz: `eszaman` -%95,31
ve `gece` -%28,95 hicbir makul gurultu tabaninda kaybolmaz.

Iki satir icin onemli:

    olcekleyici     +%0,04   (138,2083 vs 138,1468 W)
    rastgele_kfold  -%1,09   (136,6343 vs 138,1468 W)

`rastgele_kfold` artik makalenin **mansetinin merkezinde**: PVGIS'te
0,9891, DKASC'de 0,9179 diyecegiz. 0,9891'in 1,0'dan ayirt edilebilir
olup olmadigi OLCULMEDI. Olcmemek tek kotu secenektir; iki sonuc da
iddiayi guclendirir:

- **anlamsiz** -> "simule veride hicbir etki gosterilemiyor, gercek
  veride net" (daha keskin bir ifade)
- **anlamli** -> "ikisi de gercek ama buyuklukler yedi kat farkli"

---

## 1. Varyant test taksonomisi - hangi varyant NASIL test edilir

Butun varyantlar ayni sekilde test EDILEMEZ. Neyi degistirdiklerine gore
uc sinifa ayrilirlar; sinif, gecerli olcuyu belirler.

### Sinif A - test satirlari AYNI, model FARKLI

| varyant | ne degisiyor |
|---|---|
| `eszaman` | oznitelik kumesi -> model |
| `olcekleyici` | on-isleme (imputer/scaler tum veride fit) -> model |

Bolme `rastgele_kfold=False` oldugu icin test kumesi ikisinde de
`yil == test_yil`; satirlar birebir ayni. **Standart esli kumelenmis
Diebold-Mariano gecerlidir.** Eslestirme `(konum, time_utc)` uzerinden,
`ozet_sonrasi.py` ile ayni desen.

### Sinif B - model AYNI, degerlendirme POPULASYONU farkli

| varyant | ne degisiyor |
|---|---|
| `gece` | yalnizca degerlendirme maskesi |

`experiment.py:hucre_kos` icinde `v["gece"]` YALNIZCA
`gunduz_maskesi(..., gece_dahil=...)` cagrisina giriyor. Oznitelik
onbellegi, bolme, on-isleme dali ve `hat.fit()` `temiz` ile ayni.
Dolayisiyla **ortak gunduz satirlarinda tahminler bit duzeyinde
ayni**dir ve kayip farki `d(i) = 0` cikar.

**Esli DM burada dejeneredir ve KURULMAYACAKTIR.** Test edilecek bir
"tahmin dogrulugu esittir" bos hipotezi yoktur; degisen sey metrigin
hangi populasyon uzerinde hesaplandigidir.

Yerine **cebirsel ozdeslik** raporlanir. Kesin bir iliskidir, test
gerektirmez:

    RMSE^2(tumu) = [ n_gunduz * RMSE^2(gunduz)
                   + n_gece   * RMSE^2(gece)   ] / n_toplam

Ozdeslik uc kaynagin her biri icin sayilarla doldurulacaktir
(`n_gunduz`, `n_gece`, `RMSE(gunduz)`, `RMSE(gece)`, `RMSE(tumu)`),
boylece -%28,95'in nereden geldigi CEBIRSEL olarak gosterilmis olur.

### Sinif C - test satirlari FARKLI, model FARKLI

| varyant | ne degisiyor |
|---|---|
| `rastgele_kfold` | bolme -> hem egitim hem test satirlari |
| `enkotu` | dort mudahale birden (asagiya bak) |

`bolme_indeksleri` rastgele kolda `yil <= test_yil` havuzunu permute
edip AYNI BOYUTTA ama FARKLI satirlardan test ayirir. Tam kumelerde
esli test **kurulamaz**: eslesmeyen satirlar icin `d(i)` tanimsizdir.

Kesisim boyutlari OLCUM ONCESI olculdu ve buraya yazildi (kesisimin
sonuclar gorulduKten sonra secilmedigi boylece kayitlidir):

| test yili | havuz | test_n | kesisim | % | kesisim+gunduz | kume |
|---|---|---|---|---|---|---|
| 2017 | 209.238 | 52.560 | 12.994 | 24,7 | 6.342 | 3.840 |
| 2018 | 261.798 | 52.560 | 10.502 | 20,0 | 5.195 | 3.433 |
| 2019 | 314.358 | 52.560 | 8.883 | 16,9 | 4.340 | 3.060 |
| 2020 | 367.062 | 52.704 | 7.383 | 14,0 | 3.726 | 2.778 |
| 2021 | 419.622 | 52.560 | 6.590 | 12,5 | 3.243 | 2.484 |
| 2022 | 472.182 | 52.560 | 5.946 | 11,3 | 2.912 | 2.269 |
| 2023 | 524.742 | 52.560 | 5.201 | 9,9 | 2.522 | 2.062 |

(kiyas: `temiz` kolun tam gunduz test kumesi 25.708-25.887 satir,
5.406-5.441 kume)

**IKI olcu birden raporlanir, cunku IKI FARKLI SORU vardir:**

1. **Kesisim esli DM'si** - "degerlendirme populasyonu SABITKEN model
   gercekten ne kadar iyilesti?" Her iki kolun da tesadufen disarida
   tuttugu satirlarda olculur; tek degisken egitimde ne oldugudur.
   Sizinti mekanizmasini izole eder.
2. **Iki orneklemli gun-blogu bootstrap'i** - "RAPORLANAN sayi ne kadar
   sisiyor?" Tam test kumeleri uzerinde, gun bloklari her iki kumede
   bagimsiz yeniden orneklenerek `RMSE_temiz - RMSE_varyant` icin %95
   GA. %10-25'lik ortusme yok sayilir; pozitif korelasyonu atmak
   varyansi FAZLA tahmin eder, yani GA genisler ve fark ilan etmek
   ZORLASIR - muhafazakar yon.

**Kesisim RMSE'si manset RMSE'si DEGILDIR ve oyle sunulmayacaktir.**

`enkotu` sinif C'dedir ama `gece=True` de tasir. Kesisim DM'sinde
**maske iki tarafta da gunduz sabitlenecektir**, yoksa sinif B ve sinif
C etkileri birbirine karisir.

---

## 2. Test parametreleri - sonuc gorulmeden sabit

    esik            : alfa = 0,05, iki tarafli
    kayip           : kare hata
    duzeltme        : Newey-West / Bartlett, h = 24
    kumelenme       : time_utc (zaman damgasi) - Faz 3 ve Faz 4 ile AYNI
    bootstrap       : gun blogu, 1000 tekrar, tohum = SEED (42)
    eslestirme      : (konum, time_utc) - konumsal indeks DEGIL
    coklu duzeltme  : YAPILMAYACAK

**Test sayisi ve tesadufi beklenti:** sinanan varyant sayisi 4'tur
(`eszaman`, `olcekleyici`, `rastgele_kfold`, `enkotu`); `temiz`
referanstir, `gece` dejeneredir. Uc kaynak (PVGIS tam, PVGIS
indirgenmis, DKASC) ile **4 x 3 = 12 DM testi**. 0,05 esiginde
**beklenen tesadufi anlamli sayisi 0,60**. Bu sayi tabloda yazacaktir
(Faz 4'te yapilanin aynisi).

Her satirda p-degerinin YANINDA etki buyuklugu raporlanir: mutlak W,
kapasiteye gore %, bagil %. `evaluate.etki_buyuklugu`'nun docstring'i
gerekceyi tasiyor: yeterince buyuk orneklemde 0,8 W'lik fark da
"anlamli" cikar.

---

## 3. YORUM KURALI - hangi sonuc neye yorulur

### 3.1 `olcekleyici` - BEKLENTIYI DOGRULAYAN OLCUM EN KOLAY YANLIS OKUNANDIR

Faz 2 tablosu +%0,04 diyor. **Beklenen sonuc: ANLAMSIZ.** Beklentiyi
dogrulayan bir olcumu "biliyorduk zaten" diye gecistirmek en kolay
hatadir; bu yuzden iki dal da ONCEDEN yazildi.

**ANLAMSIZ cikarsa** soyle raporlanacak:

> Bu kurulumda, on-islemenin tum veriye fit edilmesinin tahmin
> dogruluguna olculebilir bir etkisi GOSTERILEMEDI. Guven araligi
> [alt; ust] W'dir; bu genislikten buyuk bir etki dislanabilir,
> kucugu dislanamaz.

Ve MUTLAKA su nitelemeyle:

> Bu, olcekleyici sizintisinin genel olarak zararsiz oldugunun kaniti
> DEGILDIR. 29 oznitelikli, gecikmeli degiskenlerin bilgi icerigine
> hakim oldugu ve uc modelli bir kurulumda tespit edilemedigidir.
> Az oznitelikli, olceklemeye duyarli modeller iceren bir kurulumda
> sonuc farkli olabilir.

**ANLAMLI cikarsa:**

> Sizintinin en hafif bicimi bile bu orneklem buyuklugunde tespit
> edilebiliyor. Onemli olan p degeri degil etki buyuklugudur: X W,
> kapasitenin %Y'si - pratik olarak ihmal edilebilir / edilemez
> (esik: kapasitenin %0,5'i, Faz 3'un ilk-iki farklarinin mertebesi).

Her iki dalda da **GA genisligi yazilacaktir** ki okuyucu hangi
buyuklugun dislanabildigini gorsun.

### 3.2 `eszaman` - SAGLIK KONTROLU

**Beklenen: ANLAMLI, cok buyuk etkiyle** (RMSE 138,15 -> 6,48 W).

**ANLAMSIZ cikarsa bu bir BULGU DEGIL, ARIZA ISARETIDIR.** -%95'lik bir
fark esli testte reddedilemiyorsa eslestirme veya kumelenme bozuktur.
Bu durumda sonuc RAPORLANMAZ; once neden bozuldugu bulunur. Bu kural
buraya, sonuc gorulmeden yaziliyor ki "beklemedigimiz sonuc cikinca
testi sucladik" denemesin.

### 3.3 `rastgele_kfold` - MANSETIN MERKEZI

Iki olcu, dort olasi bilesim. Dordunun de nasil raporlanacagi:

| kesisim DM | bootstrap GA | okuma |
|---|---|---|
| anlamli | sifiri dislar | Iki soru da ayni yone: rastgele bolme hem raporlanan sayiyi degistiriyor hem ayni satirlarda modeli gercekten iyilestiriyor. |
| anlamli | sifiri icerir | Sabit satirlarda model gercekten iyilesiyor, ama raporlanan manset sayisindaki degisim ornekleme gurultusu icinde. **Etki var, olcek kucuk.** |
| anlamsiz | sifiri dislar | Raporlanan sayi degisiyor ama kiyaslanabilir satirlarda model iyilesmiyor: degisim degerlendirme POPULASYONUNUN kaymasindan geliyor. Bu en ilginc sonuc olurdu ve boyle raporlanir. |
| anlamsiz | sifiri icerir | Simule veride rastgele bolmenin etkisi HICBIR olcuyle gosterilemiyor. |

**Dordu de makale icin kullanilabilir.** Kritik nokta su ve simdiden
sabitleniyor:

> Makalenin iddiasi PVGIS'in MUTLAK sayisi degil, **PVGIS ile DKASC
> arasindaki KARSITLIK**tir. PVGIS'te hangi sonuc cikarsa ciksin,
> DKASC'nin 0,9179'u ile yan yana konacaktir. "PVGIS'te anlamsiz"
> cikmasi karsitligi ZAYIFLATMAZ, KESKINLESTIRIR.

### 3.4 `rastgele_kfold` kesisim etkisi - PVGIS vs DKASC yan yana

Kesisim olcusu ozellikle degerlidir cunku **degerlendirme populasyonu
sabittir**; iki kaynagin kesisim etkileri yan yana konuldugunda
ezberleme hipotezi populasyon farkindan ARINMIS halde sinanir.

`faz-notlari/dkasc-replikasyon.md`'deki on-kayitli hipotez: rastgele
bolmenin gercek veride ise yaramasinin sebebi dizi-ozgu gurultunun
EZBERLENMESIYSE, kazanc esnek modelde (HGB) kati modelden (LR) buyuk
olmali. Tam kumede DOGRULANDI (LR -0,0080/-0,0080/-0,0087;
HGB +0,0387/+0,0374/+0,2085).

**Kesisimde de ayni model siralamasi cikarsa** hipotez populasyon
farkindan bagimsiz olarak dogrulanmis olur. **Cikmazsa**, tam kumedeki
model kirilimi kismen populasyon kompozisyonundan geliyor demektir ve
bu ACIKCA yazilir; hipotez "kismen desteklendi" diye raporlanir,
sessizce birakilmaz.

### 3.5 `enkotu`

Bagimsiz bir iddia tasimaz; butunluk icin raporlanir. Dort mudahaleyi
birden tasidigi icin (asagiya bak) tek bir mekanizmaya atfedilemez.

---

## 4. Dogrulama kapilari - gecmezse DUR

### Kapi 1 - regresyon

`--tahmin-kaydet` uretim koduna dokunur. Yeniden kosulan hucrelerin
`RMSE`, `MAE`, `R2`, `egitim_n` degerleri mevcut loglarla **BIREBIR**
esit olmali (`==`, tolerans yok). Fark cikarsa DUR ve raporlama.

### Kapi 2 - sinif B ozdesligi

Sinif B iddiasi "`gece` ile `temiz` ayni modeli kurar" seklindedir.
Sinanabilir bicimi: **`gece` varyantinin loglanan RMSE'si, `temiz`
varyantinin KAYDEDILEN tahmin vektorunden TUM satirlar uzerinde
yeniden hesaplanan RMSE'ye esit olmali** (float toleransi icinde).

Esit CIKMAZSA sinif B siniflandirmasi YANLIStir; taksonomi duzeltilir,
ozdeslik raporlanmaz ve `gece` icin ayri bir olcu aranir.

### Kapi 3 - kesisim boyutu

Yukaridaki tabloda yazili kesisim boyutlari kosuda yeniden uretilmeli.
Sapma varsa `bolme_indeksleri` beklendigi gibi davranmiyordur.

---

## 5. Bu belge degistiginde

1. Degisiklik `[SONRADAN eklendi - <tarih>]` diye isaretlenir.
2. Gerekce yazilir: hangi gozlem degistirdi, sonuca bakildi mi.
3. Eski hali SILINMEZ, ustu cizilmez.

Bir yorum kuralinin sonuclar gorulduKten sonra degistirilmesi
MUMKUNDUR ama GIZLENEMEZ.
