# Sizinti varyantlari ayni sekilde test EDILEMEZ - bir taksonomi

**Yazildigi tarih: 8 Agustos 2026, olcum yapildiktan SONRA.**
Yorum kurali olcumden ONCE ayri commit'tedir
(`dokumanlar/varyant-dm-yorum-kurali.md`, `397e362` ve `d9f2383`); bu
belge onun UYGULANMASINI ve sonuclarini tasir. Makalenin Yontem
bolumune alt baslik olarak buradan tasinacaktir.

---

## 0. Iddia

Bir sizinti ablasyonunda her varyant "referansa gore ne kadar sisirdi"
diye ayni bicimde raporlanir. Ama **varyantlar ayni istatistiksel
nesneyi degistirmez**, dolayisiyla hepsine ayni test uygulanamaz.
Neyi degistirdiklerine gore uc sinif vardir ve sinif, gecerli olcuyu
belirler. Ayrimi yapmamak iki hataya yol acar:

1. Dejenere bir teste anlam yuklemek (sinif B).
2. Kurulamayacak bir testi kurmus gibi yapmak ya da hic olcmemek
   (sinif C).

Bu, ablasyon yapan herkesin karsilastigi ama literaturde tartisilmayan
bir sorundur.

---

## 1. Uc sinif

| sinif | ne degisiyor | test satirlari | model | gecerli olcu |
|---|---|---|---|---|
| **A** | oznitelik / on-isleme -> MODEL | AYNI | farkli | esli kumelenmis DM |
| **B** | yalnizca DEGERLENDIRME MASKESI | alt kume | **AYNI** | **test YOK** - cebirsel ozdeslik |
| **C** | BOLME -> egitim VE test satirlari | FARKLI | farkli | kesisim DM + iki orneklemli bootstrap |

Bu calismadaki dagilim: A = `eszaman`, `olcekleyici`;
B = `gece`; C = `rastgele_kfold`, `enkotu`.

### Sinif A

Bolme degismedigi icin test kumesi referansla birebir aynidir; tek
degisen modeldir. Esli test standart bicimde kurulur. Eslestirme
konumsal indeksle degil `(konum, time_utc)` ile yapilir.

### Sinif B - esli DM burada DEJENEREDIR

`gece` varyantinda bayrak yalnizca degerlendirme maskesine giriyor;
oznitelik onbellegi, bolme, on-isleme dali ve model uydurma referansla
aynidir. Dolayisiyla **ortak satirlarda tahminler bit duzeyinde
ozdestir** ve kayip farki her gozlemde tam olarak sifirdir. DM
istatistigi tanimsizdir; sifir varyansli bir seriye test uygulamak
anlamsizdir.

Test edilecek bir "tahmin dogrulugu esittir" bos hipotezi yoktur.
Degisen sey metrigin hangi POPULASYON uzerinde hesaplandigidir.

Yerine kesin bir cebirsel ozdeslik raporlanir:

    RMSE^2(tumu) = [ n_gunduz * RMSE^2(gunduz) + n_gece * RMSE^2(gece) ] / n_toplam

**"Anlamlilik testi kurmadik" demekten cok daha gucludur: iliski
kesindir, hakem tartisamaz.**

### Sinif C - tam kumede esli test KURULAMAZ

Bolme degistigi icin test satirlari farklidir; eslesmeyen satirlar icin
kayip farki tanimsizdir. Iki olcu birlikte kullanilir, cunku **iki
farkli soru** vardir:

1. **Kesisim esli DM'si:** her iki kolun da tesadufen disarida tuttugu
   satirlarda. Degerlendirme populasyonu SABIT; tek degisken egitimde
   ne oldugu. Sizinti mekanizmasini izole eder.
2. **Iki orneklemli gun-blogu bootstrap'i:** tam test kumeleri
   uzerinde, gun bloklari her kumede bagimsiz yeniden orneklenerek.
   RAPORLANAN sayinin ne kadar sistigini olcer. Ortusme yok sayilir;
   pozitif korelasyonu atmak varyansi fazla tahmin eder, yani
   muhafazakar yondedir.

**Kesisim RMSE'si manset RMSE'si DEGILDIR.**

---

## 2. Sinif C'nin gizli tuzagi: POPULASYON MASKELEMESI

Manset orani iki FARKLI POPULASYON uzerinde hesaplanan RMSE'leri
kiyaslar. Kronolojik kol yalniz test yilinda olculur; rastgele kol
butun havuzdan cekilmis bir orneklemde. Eski yillar sistematik olarak
daha kolay ya da zorsa, populasyon farki gercek sizinti etkisini
maskeleyebilir - hatta ters yonde calisip isaretini cevirebilir.

Ayirt edici arac test degil CEBIRDIR. Manset farki kesin olarak uce
ayrilir:

    D  =  RMSE_v(tam) - RMSE_t(tam)
       =  [ RMSE_v(kes) - RMSE_t(kes) ]   <- A: MODEL etkisi, populasyon SABIT
        + [ RMSE_v(tam) - RMSE_v(kes) ]   <- B: varyantin populasyon terimi
        - [ RMSE_t(tam) - RMSE_t(kes) ]   <- C: referansin populasyon terimi

`A + B - C = D` sadelestirme ile dogrudan cikar. Uc kaynakta da
uretimde dogrulandi: **maks ayristirma hatasi 2,842e-14.**

---

## 3. Olcum sonuclari

Kurulum: alti varyant x uc model x yedi yil (DKASC'de bes yil),
`kume = time_utc`, Newey-West h=24, gun-blogu bootstrap 1000 tekrar,
tohum 42.

### 3.1 Sinif B - ozdeslik uc kaynakta da TAM

| kaynak | hucre | maks ozdeslik hatasi | maks kapi farki |
|---|---|---|---|
| PVGIS tam | 21 | 2,842e-14 | 1,421e-14 |
| PVGIS indirgenmis | 21 | 2,842e-14 | 1,421e-14 |
| DKASC | 15 | 1,137e-13 | 5,684e-14 |

Ornek satirlar (`temiz` modelinin tahminlerinden):

| kaynak | yil | model | n_gunduz | n_gece | RMSE gunduz | RMSE gece | RMSE tumu |
|---|---|---|---|---|---|---|---|
| PVGIS | 2019 | HGB | 25.776 | 26.784 | 137,168967 | **18,945015** | 97,005878 |
| PVGIS | 2020 | HGB | 25.887 | 26.817 | 136,804225 | **8,388790** | 96,064465 |
| DKASC | 2022 | HGB | 3.890 | 3.938 | 666,005614 | **7,729851** | 469,523022 |
| DKASC | 2018 | LR | 4.152 | 4.184 | 555,225215 | 80,645523 | 395,992619 |

**`gece` varyantinin -%28,95'i tamamen buradan gelir:** gece satirlari
sayica gunduzden fazladir (PVGIS'te 26.784 vs 25.776) ve kendi
RMSE'leri gunduzunkinin yedide biri ile onda biri arasindadir. Iki
ortalama havuzlaninca metrik mekanik olarak duser. Bu bir dogruluk
kazanci DEGILDIR.

### 3.2 Sinif A - `olcekleyici`: ANLAMLI ama ONEMSIZ

| kaynak | anlamli | \|etki\| medyan | \|etki\| maks | maks / kapasite |
|---|---|---|---|---|
| PVGIS tam | **7/21** | 0,000656 W | 0,347422 W | **%0,0347** |
| PVGIS indirgenmis | **8/21** | 0,000383 W | 0,237759 W | %0,0238 |
| DKASC | **4/15** | 0,036911 W | 6,506344 W | %0,1239 |

Ornek - PVGIS 2018 Linear Regression: fark **0,000660 W**, p =
**0,000431**. Kapasitenin on binde altisi kadar bir fark, p < 0,001
ile "anlamli".

**Yorum kurali "ANLAMLI cikarsa" dalina gore raporlanir:** onemli olan
p degeri degil etki buyuklugudur. On-kayitli pratik anlamlilik esigi
kapasitenin %0,5'iydi (Faz 3'un ilk-iki farklarinin mertebesi); uc
kaynagin maksimumu **%0,124** ile bu esigin dortte birinin altindadir.

Bu, `evaluate.etki_buyuklugu`'nun 30 Temmuz'da yazilan docstring'inin
birebir gerceklesmesidir: "yeterince buyuk bir orneklemde 0,8 W'lik bir
fark da anlamli cikar."

**Zorunlu niteleme (on-kayitli):** bu sonuc olcekleyici sizintisinin
genel olarak zararsiz oldugunun kaniti DEGILDIR. 29 oznitelikli,
gecikmeli degiskenlerin bilgi icerigine hakim oldugu bir kurulumda
etkisinin pratik olarak sifir oldugudur.

### 3.3 Sinif A - `eszaman`: saglik kontrolu GECTI

Uc kaynakta da 21/21, 21/21 ve 15/15 anlamli; DM istatistikleri 19-29
bandinda. On-kayitli ariza tuzagi tetiklenmedi.

### 3.4 Sinif C - POPULASYON MASKELEMESI OLCULDU

`rastgele_kfold`, model bazinda ortalama (W):

| kaynak | model | **A** (model, pop. sabit) | A / kapasite | (B−C) pop. | **D** (manset) | D / kapasite | A anlamli | isaret TERS |
|---|---|---|---|---|---|---|---|---|
| PVGIS tam | Linear Regression | **−0,050** | %−0,0050 | +1,148 | **+1,098** | %+0,1098 | 1/7 | **5/7** |
| PVGIS tam | Polynomial Ridge | −1,088 | %−0,1088 | +0,790 | −0,298 | %−0,0298 | 7/7 | 3/7 |
| PVGIS tam | Hist Gradient Boosting | −6,309 | %−0,6309 | +0,972 | −5,337 | %−0,5337 | 7/7 | 1/7 |
| PVGIS indirg | Linear Regression | −0,048 | %−0,0048 | +1,153 | +1,105 | %+0,1105 | 1/7 | 5/7 |
| PVGIS indirg | Polynomial Ridge | −0,800 | %−0,0800 | +0,901 | +0,101 | %+0,0101 | 7/7 | 3/7 |
| PVGIS indirg | Hist Gradient Boosting | −6,109 | %−0,6109 | +0,946 | −5,163 | %−0,5163 | 7/7 | 1/7 |
| DKASC | Linear Regression | −2,765 | %−0,0527 | −2,272 | −5,037 | %−0,0959 | 3/5 | 2/5 |
| DKASC | Polynomial Ridge | −32,120 | %−0,6118 | −1,466 | −33,586 | %−0,6397 | 5/5 | 1/5 |
| DKASC | Hist Gradient Boosting | **−126,640** | %−2,4122 | +0,390 | −126,250 | %−2,4048 | 5/5 | 0/5 |

**En temiz tekil ornek - PVGIS 2023, Hist Gradient Boosting:**

    A (model etkisi, ayni satirlarda)  = -4,354738 W   p = 4,5e-08
    (B - C) populasyon terimi          = +4,578994 W
    D (raporlanan manset farki)        = +0,224256 W

Rastgele bolme modeli **4,35 W iyilestiriyor** ve bu tartismasiz
anlamli; ama raporlanan sayi **0,22 W kotulesme** diyor. Populasyon
terimi etkiyi yutup isaretini ceviriyor.

Sayimlar:

| kaynak | A anlamli | A anlamli + bootstrap GA sifiri iceriyor | A anlamli + isaret TERS |
|---|---|---|---|
| PVGIS tam | 15/21 | **10** | **5** |
| PVGIS indirgenmis | 15/21 | **10** | **5** |
| DKASC | 13/15 | 4 | 2 |

**PVGIS'te 21 hucrenin 10'unda gosterilebilir bir sizinti etkisi manset
metriginde kayboluyor.** DKASC'de bu 15'te 4.

### 3.5 Manset farkinin aciklamasi

Faz 2 mansetinde `rastgele_kfold` PVGIS'te 0,9891, DKASC'de 0,9179 idi
ve bu fark "simule veri etkiyi ~7,5 kat kucumsuyor" diye okunuyordu.
Ayristirma nedenini gosteriyor:

- **PVGIS'te populasyon terimi (~+1 W) model etkisiyle (0,05-6,3 W)
  AYNI MERTEBEDE**, dolayisiyla mansette birbirlerini buyuk olcude
  goturuyorlar.
- **DKASC'de model etkisi (2,8-127 W) populasyon teriminden (0,4-2,3 W)
  bir-iki mertebe buyuk**, dolayisiyla mansete neredeyse tamamen
  yansiyor.

Yani simule veri etkiyi yalnizca kucultmuyor; **olculebilirligini de
bozuyor.** Sizintinin varligi degil, GORUNURLUGU sorunlu.

### 3.6 Ezberleme hipotezi - populasyon farkindan ARINMIS sinama

Yorum kurali 3.4'un istedigi sinama. `A` sutunu (kapasiteye gore %),
degerlendirme populasyonu sabitken:

| model | PVGIS tam | PVGIS indirgenmis | DKASC |
|---|---|---|---|
| Linear Regression | %−0,0050 | %−0,0048 | %−0,0527 |
| Polynomial Ridge | %−0,1088 | %−0,0800 | %−0,6118 |
| Hist Gradient Boosting | **%−0,6309** | **%−0,6109** | **%−2,4122** |

**Hipotez populasyon farkindan bagimsiz olarak DOGRULANDI.** Kazanc uc
kaynagin ucunde de model esnekligiyle monoton artiyor ve DKASC'nin HGB
etkisi PVGIS'inkinin **3,82 kati**. Tam kumedeki model kirilimi bir
populasyon kompozisyonu artefakti DEGILDIR.

---

## 4. On-kayittan iki SAPMA

Ikisi de saklanmadan raporlanir.

### 4.1 Test sayisi - varyant duzeyi yerine HUCRE duzeyi

Yorum kurali "4 varyant x 3 kaynak = 12 DM testi, beklenen tesadufi
0,60" diyordu; bu **varyant duzeyinde toplu test** varsayiyordu.
Uygulama **hucre duzeyinde** kostu - Faz 3 (21 ikili) ve Faz 4 (45 ve
15) ile ayni granulerlik:

| kaynak | test | beklenen tesadufi (0,05) |
|---|---|---|
| PVGIS tam | 84 | 4,20 |
| PVGIS indirgenmis | 84 | 4,20 |
| DKASC | 60 | 3,00 |
| **toplam** | **228** | **11,40** |

Coklu karsilastirma duzeltmesi YAPILMADI. `olcekleyici`'nin 19 anlamli
hucresi (7+8+4) bu beklentinin (11,40) uzerindedir ama ETKI
BUYUKLUKLERI yukarida; iddia anlamliliga degil buyukluge dayaniyor.

### 4.2 `C ~ 0` beklentisi YANLIS cikti

Yorum kurali 3.3b, kesisimin referansin test yilinin tekduze rastgele
alt kumesi oldugu icin `C` teriminin ornekleme gurultusu mertebesinde
kalmasini bekliyordu. Olculen (PVGIS tam):

    |C| ortalama = 1,738895 W      |B| ortalama = 1,201016 W

**|C| beklenenin aksine |B|'den BUYUK.** Yil icinde uc modelin C'si
ayni isaretli (ayni cekilis), yillar arasinda isaret degisiyor: bu bir
yanlilik degil, kesisim cekilisinin yil basina ornekleme kaymasidir.
Ama ihmal edilebilir degildir - ayristirmanin `C`'yi cikarmasi bu
yuzden zorunludur; "kesisim RMSE'si ~ tam RMSE" varsayimiyla
calisilsaydi sonuc bozulurdu.

---

## 5. Kapi bir HATA yakaladi - kayit

Sinif B kapisi (`gece`nin loglanan RMSE'si `temiz`in tahminlerinden
yeniden hesaplananla esit olmali) DKASC'de ILK kosuda **12/15 ile
DUSTU**, maks sapma 0,5787 W.

Ustu ortulmedi, once teshis edildi:

- Dusen hucreler **yalnizca 2018'in uc modeli**.
- `ariza` bayrakli alti saatin **besi 2017'de** (yalniz egitim yili,
  test kumesine hic girmiyor), **biri 2018'de** (2018-12-06 08:00).
- Yani dusen hucre kumesi, test kumesinde ariza satiri BULUNAN yilla
  birebir ortusuyor.

**Sebep taksonomi degil, teshis aracinin populasyon tanimiydi:**
`hucre_kos` kural 7 geregi ariza satirlarini degerlendirmeden cikariyor,
ozdeslik hesabi cikarmiyordu. Tahmin dosyalarina `ariza` sutunu
eklendi, tum olculer ayni populasyonu kullanacak sekilde duzeltildi,
DKASC izgarasi yeniden kosuldu; kapi **15/15, sapma 5,684e-14** ile
gecti ve regresyon kapisi 810 karsilastirmada sifir fark verdi.

Genel ders, makaleye girecek: **bir sizinti calismasinda "ayni
populasyon" varsayimi her olcude ayrica dogrulanmalidir.** Kapi bu
hatayi yakalamasaydi, DKASC'nin sinif B ozdesligi %0,1 hatali
raporlanacakti.

---

## 6. Makaleye ne gider

Ana metin (Yontem, alt baslik):
- Bolum 1'in tablosu (uc sinif, gecerli olcu)
- Sinif B'nin dejenere oldugu ve yerine ozdeslik kondugu - iki cumle
- Bolum 2'nin ayristirmasi (`A + B - C = D`) - bir denklem

Ana metin (Sonuclar):
- 3.4'un tablosu ya da 3.5'in iki maddesi
- 3.6'nin uc satirlik tablosu

Ek dosya:
- 3.1, 3.2, 3.3'un tam tablolari
- Bolum 4'un iki sapmasi
- Bolum 5'in kapi kaydi
