# DKASC kalite kontrol kurallari - ON-KAYIT

**Yazildigi tarih: 7 Agustos 2026.** Bu dosya, DKASC verisinin HICBIR
satiri islenmeden, hicbir oznitelik uretilmeden, hicbir model egitilmeden
once yazildi ve commit edildi. Amaci `pv10/ozet.py` ile ayni: kural
seciminin post-hoc olmadigini dosya duzeyinde `git log` ile
gosterebilmek.

Bu dosyaya sonradan eklenen her madde `[SONRADAN eklendi - <tarih>]`
diye isaretlenir ve gerekcesi yazilir. Isaretsiz madde, veri islenmeden
once sabitlenmistir.

Kurallarin dayandigi gozlemler bir KESIF turundan gelir (4-7 Agustos
2026). Kesif yalnizca okudu; hicbir kural uygulanmadi, hicbir deger
degistirilmedi, repoya veri girmedi.

---

## 0. Kapsam ve veri

| | |
|---|---|
| kaynak | dkasolarcentre.com.au, "All Individual Technologies (yearly data set with weather data)" |
| dosyalar | `ham/dkasc/Alice_Springs_{2017..2022}.csv` (6 dosya, ~1,2 GB) |
| indirme | 2022 -> 4 Agustos 2026; 2018, 2020 -> 4 Agustos 2026; 2017, 2019, 2021 -> 7 Agustos 2026 |
| cozunurluk | 5 dakika |
| bicim | genis; sutun adi `<id>_DKA_<dizi>_<kanal>` |
| sutun sayisi | 197, alti yilda da AYNI ad ve AYNI sira |
| sistem sayisi | 50 benzersiz id, alti yilda da ayni kume |
| zaman damgasi | yerel ACST (UTC+9:30) - olculdu, bkz. bolum 5 |
| birlesik satir | 621.933 (takvim yillarina kirpilmis, benzersiz damga) |
| tam izgara | 631.008 (2017-01-01 00:00 .. 2022-12-31 23:55) |
| eksik damga | 9.075 (%1,4382) |

**Dosyalar takvim yili DEGILDIR.** Her yillik dosya 1 Ocak 00:00'dan
ERTESI yilin 1 Ocak 23:55'ine kadar uzanir; sonda 288 satirlik fazladan
bir gun vardir. Birlestirme sirasinda bu fazlalik kirpilir, yoksa yil
sinirinda 288 satir cift sayilir.

### Kapsam karari: 2017-2022'nin TAMAMI kullanilir

Test yillari **2018-2022** (bes yil). 2017 yalnizca egitim penceresi
olarak girer; oznitelik isinmasi ve K=1 penceresi icin gereklidir.

**2022 anormal oldugu icin ELENMEZ.** 2022'de olculen sapmalar gercektir
(bolum 6), ama bir yili "anormal" diye disari atmak post-hoc secimdir ve
tam olarak bu makalenin elestirdigi uygulamadir. Duraganlik disi davranis
gercek dunyada vardir; raporlanir, ayiklanmaz. Aynisi 2019 (kurak yil,
54,0 mm) ve 2020-12 (dusuk isinim ayi) icin de gecerlidir.

---

## 1. Sekiz kural

Her kural icin: gozlem, esik, gerekce, etkilenen satir. Sayimlar
2017-2022'nin tamami uzerinden, 621.933 satirlik birlesik seride
olculmustur; yuzdeler bu paydaya goredir.

### Kural 1 - Piranometre gece ofseti

- **Gozlem:** gunes ufkun altindayken (`sin h < 0`) GHI sifir degil;
  medyan **2,2921** W/m2, ortalama 2,5560, p99 9,9649. GHI'nin tam
  sifir oldugu satir sayisi alti yilda 12.
- **Esik:** `sin h < 0` olan satirlarda GHI, DHI, GTI, DTI -> 0.
- **Gerekce:** ISO 9060 sinifinda ±5 W/m2 sifir ofseti beklenir; gece
  isinim tanim geregi sifirdir. Ofseti birakmak berrak-gokyuzu oranini
  ve gece/gunduz gecislerini kirletir.
- **Etkilenen:** 311.861 satir (%50,1438) sifirlanir; bunlarin 13.168'i
  (%2,1173) 5 W/m2'nin uzerindedir.
- **Not:** filtre DEGERLENDIRME degil DUZELTMEdir; gece satirlari
  egitimde kalir (Faz 2 dersi, bkz. CLAUDE.md).

### Kural 2 - Bagil nem ust siniri

- **Gozlem:** RH maksimumu **131,1584**; RH > 100 olan 5.054 satir
  (%0,8126), RH > 105 olan 5 satir (%0,0008, hepsi 2020-02/03).
- **Esik:** `clip(0, 100)`; RH > 105 ise satir ayrica bayraklanir.
- **Gerekce:** bagil nem tanim geregi <= %100. 100-105 araligi sensor
  kalibrasyon toleransidir, kirpilir; 105 ustu olcum hatasidir.
- **Etkilenen:** 5.054 kirpilir, 5'i bayraklanir.

### Kural 3 - Yayili bilesen globali asamaz

- **Gozlem:** `DHI > GHI` olan **6.146** satir (%0,9882); `DHI >
  1,05 x GHI` olan 5.134 satir (%0,8255).
- **Esik:** `DHI = min(DHI, GHI)`; oran > 1,05 ise satir bayraklanir.
- **Gerekce:** yayili isinim globalin bilesenidir, onu asamasi fiziksel
  olarak imkansizdir.
- **Etkilenen:** 6.146 duzeltilir, 5.134 bayraklanir.
- **Not:** bu sayim gece GHI ofsetiyle ters kilitlidir; gece tabani
  yuksek olan aylarda `DHI > GHI` neredeyse hic gorulmez
  (korelasyon **-0,6354**). Kural 1 uygulandiktan sonra bu sayimin
  dusmesi BEKLENIR; dustugu olculecek ve raporlanacaktir.

### Kural 4 - Ruzgar kanallari kullanilmaz

- **Gozlem:** `Wind_Speed` alti yilin 72 ayinin **72'sinde de tamamen
  bostur** - 621.933 satirda tek dolu deger yok. `Wind_Direction`
  %99,9038 dolu ama araligi pusula araligi degil: min **-6,9796**,
  maks **11.596,1650**, 604.426 benzersiz deger; aralik disi 3.421
  satir (%0,5501). Isaret/birim gelenegi zaman icinde iki kez
  degisiyor: `WD > 360` rejimi 2019-06'da kapaniyor, `WD < 0` rejimi
  2020-10'da acilip 2022-02'de kapaniyor.
- **Esik:** yok - **her iki kanal da oznitelik setinden CIKARILIR.**
- **Gerekce:** hiz yok, yon dogrulanamiyor. Birimi bilinmeyen bir
  kanali oznitelige koymak, olculmemis bir belirsizligi modele
  tasimaktir.
- **Etkilenen:** oznitelik seti; bkz. bolum 2, sapma 1.

### Kural 5 - Negatif guc

- **Gozlem:** M6_B'de `P < 0` olan **1.825** satir (%0,2934), minimum
  **-0,0188** kW. M2_C'de 1.711 satir (%0,2751), minimum -0,0035 kW.
  Iki dizide de `P < -0,05` kW olan satir **yok**.
- **Esik:** `|P| <= 0,05 kW` -> 0; `P < -0,05 kW` -> eksik say.
- **Gerekce:** gece invertor tuketimi ve olcum gurultusu kucuk negatif
  degerler uretir; buyuk negatif deger olcum hatasidir. Hedef dizilerin
  ikisinde de ikinci dal bos kalir - kural yine de yazilir, cunku esik
  veriye bakilarak degil fizige bakilarak secilmistir.
- **Etkilenen:** M6_B 1.825, M2_C 1.711 satir sifirlanir.

### Kural 6 - Isinim ust siniri

- **Gozlem:** `GHI > 1400` W/m2 olan **27** satir (%0,0043);
  `GHI > 1,5 x G0` (G0 = dunya-disi yatay isinim) olan 1.126 satir
  (%0,1810).
- **Esik:** `GHI > 1,5 x G0` -> eksik say.
- **Gerekce:** bulut kenari yansimasi gercek olarak 1,4 kat asirmaya
  yol acabilir; 1,5 kat ustu fiziksel degildir. Esik sabit bir W/m2
  degeri degil, gunes yuksekligine bagli G0 ile normalize edilir -
  boylece esik mevsimden ve saatten bagimsiz kalir.
- **Etkilenen:** 1.126 satir eksige cevrilir.

### Kural 7 - Gunduz sifir uretim

- **Gozlem:** `GHI > 200` W/m2 iken `P == 0` olan satir: M6_B **108**
  (%0,0174), M2_C **109** (%0,0175). `GHI > 200` olan toplam satir
  234.954.
- **Esik:** `GHI > 200 W/m2` ve `P == 0` -> ariza bayragi.
  **Egitimden CIKARILMAZ, yalnizca DEGERLENDIRMEDEN cikarilir.**
- **Gerekce:** Faz 2'deki gece satiri dersinin aynisi - filtre yalnizca
  degerlendirmede uygulanir. Ariza gunleri gercek isletme kosuludur;
  egitimden atmak modeli iyimser gosterir, degerlendirmede birakmak ise
  tahmin edilemez bir olayi tahminciye yikar.
- **Etkilenen:** M6_B 110, M2_C 110 satir (P <= 0 ile).

### Kural 8a - Kismi ariza gunu bayragi (SIZINTISIZ surum)

- **Gozlem:** dizilerde gun ortasi cokusu gorulen gunler var; sistem 12
  (M5_B) bu yuzden elendi (bolum 2, karar 3).
- **Esik:** gunun gunduz medyani, **yalnizca EGITIM bolmesinden**
  hesaplanan tek bir gunduz medyaninin **0,3** katindan kucukse gun
  bayraklanir.
- **Gerekce ve sizinti duzeltmesi:** kuralin ilk hali esigi "AYLIK
  gunduz medyani" olarak tanimliyordu ve bu medyan tum yil uzerinden,
  test donemi DAHIL hesaplaniyordu. Bu tam olarak Faz 2'nin
  `olcekleyici` varyantidir - on islemenin tum veri setine
  uydurulmasi. Sizinti makalesinin replikasyonunda kabul edilemez.
  Esik artik kat basina, yalnizca egitim bolmesinden yeniden
  hesaplanir; olcekleyicinin kendisiyle ayni yerde durur.
- **Takvim ayi referansi KULLANILMAZ.** Tek bir egitim-geneli gunduz
  medyani kullanilir. Sebep: aylik referans, egitim bolmesinde o ayin
  hic gorulmedigi durumda tanimsiz kalir; tek medyan bu bos-ay sorununu
  ortadan kaldirir ve kurali basitlestirir.
- **Gosterge sayim** (uretimde esik EGITIM bolmesinden gelecegi icin bu
  sayi ORNEKTIR, kuralin ciktisi degildir): alti yilin tamami referans
  alindiginda M6_B gunduz medyani 2,6351 kW, esik 0,7905, bayrakli gun
  **70/2164** (%3,235); M2_C icin 2,9371 / 0,8811 / 69/2164 (%3,189).

### Kural 8b - DEGERLENDIRILDI, SECILMEDI

- **Alternatif:** esik tamamen fiziksel olsun - `guc / GTI` oraninin
  berrak-gokyuzu beklentisine orani.
- **Neden secilmedi:** esik GTI'ye dayanir; GTI'nin dizinin duzlemiyle
  ayni olup olmadigi ise olculdu ve **ayni cikmadi** (bolum 2, karar 2).
  Bir belirsizligi baska bir belirsizlige yaslamak olurdu. 8a duzlemden
  bagimsizdir.
- Kayit icin yazilmistir; secilmedigi burada duruyor.

---

## 2. Uc karar

### Karar 1 - Ruzgar hizi ve yonu oznitelik setinden CIKARILDI

**Kural 4'ten sapma - GUFBD makalesiyle birebir aynilik burada BOZULUR.**

Cekirdek oznitelik seti `WS10m` ve onun gecikmelerini iceriyor
(`pv10/config.py:GECIKMELI_DEGISKEN`). DKASC'de bu degisken YOKTUR:
alti yilin 72 ayinin 72'sinde de `Wind_Speed` tamamen bostur.
`Wind_Direction` dolu ama birimi/isareti dogrulanamamaktadir.

Bu **ayri bir sapma olarak raporlanacaktir**. Replikasyon, PVGIS
kurulumunun birebir kopyasi degil, ruzgarsiz bir varyantidir; PVGIS
tarafinda ruzgarin permutasyon onemi ayrica olculup makaleye konacak ki
sapmanin buyuklugu okurun gorebildigi bir sey olsun.

Baska yil indirilerek kanalin herhangi bir yilda dolu olup olmadigina
bakildi: 2017, 2018, 2019, 2020, 2021, 2022 - hicbirinde yok.

### Karar 2 - GTI/DTI KULLANILMAYACAK; GHI+DHI'den transpozisyon

Diziler belgelenmis olarak **Tilt 20 / Azi 0 (Solar North)** duzlemindedir
(sistem 12, 13 ve 18'in detay sayfalarinda ayni deger). Hava
istasyonunun egik piranometresinin duzlemi ise BELGELENMEMISTIR ve
olculdugunde 20 derece CIKMAMISTIR:

| yontem | secim olcutu | n | kestirim |
|---|---|---|---|
| kapali gok DTI/DHI | `DHI/GHI > 0,90`, `sin h > 0,4`, `GHI > 100` | 4.757 | 11,24° (albedo 0) ... 13,44° (albedo 0,30) |
| berrak gok transpozisyon | `sin h > 0,4`, `GHI > 300`, `DHI/GHI < 0,15` | 20.488 | 16,0° (RMSE-optimal); MBE sifiri ~11,0° |

Aylik uydurma kararsiz (11,5° - 28,5°) ve gun ici artikta monoton
sabah-ikindi egimi var (sabah medyan model/olcum 1,0363; ikindi 0,9987).
20 derece hicbir yontemde optimal cikmadi; berrak gok uydurmasinda
20°'nin RMSE'si optimumdan ~%15 yuksek, MBE +23,3 W/m2. Azimut
OLCULMEDI - kullanilan ozdeslik yalnizca azimut = 0 icin gecerlidir ve
azimut kestirmek yeni geometri kodu gerektirirdi.

**Karar:** GTI ve DTI kanallari kullanilmaz. Istenen duzleme (20°/kuzey)
donusum GHI + DHI'den standart transpozisyonla yapilir. Boylece
istasyon duzlemini BILMEK gerekmez; belirsizlik zincire hic girmez.

Ikinci gerekce kullanilabilirlik: egik kanallar en zayif kanallardir.

| kanal | eksik (izgaraya gore) |
|---|---|
| GHI | 9.676 (%1,533) |
| DHI | 9.676 (%1,533) |
| **GTI** | **76.181 (%12,073)** |
| **DTI** | **76.181 (%12,073)** |

Kesinti dagilimi da kotudur: 2019-07'de GTI %100 eksik, 2019-05..10
araliginda %62,8-%100, 2018-01'de %72,1, 2020-04'te %40,9. GHI/DHI ayni
aylarda kesintisizdir.

### Karar 3 - Hedef dizi M6_B_Phase (sistem 13); yedek M2_C (sistem 18)

**Secilen:** `92_DKA_M6_B_Phase_Active_Power` = sistem 13, Trina,
**5,25 kWp mono-Si, SABIT montaj, Tilt 20 / Azi 0.**

Gerekce: PVGIS kurulumuna (1 kWp c-Si, sabit) en yakin teknoloji ve
montaj; sabit egim/azimut belgelenmis; alti yilda da kalitesi duzgun.

**Yedek:** `71_DKA_M2_C_Phase_Active_Power` = sistem 18, SunPower
5,236 kWp mono-Si, sabit.

Alti yillik kalite (gunduz = `sin h > 0,1`; eksik oran tam izgaraya
gore):

| yil | eksik% | negatif | gunduz sifir% | gunduz medyan (kW) | maks (kW) | p99 |
|---|---|---|---|---|---|---|
| 2017 | 0,5774 | 639 | 0,4242 | 2,5813 | 5,5590 | 4,3333 |
| 2018 | 0,0000 | 226 | 0,1996 | 2,6877 | 4,9254 | 4,2411 |
| 2019 | 2,1071 | 226 | 0,0464 | 2,8718 | 4,9959 | 4,2633 |
| 2020 | 0,0275 | 270 | 0,1293 | 2,5957 | 5,2186 | 4,2319 |
| 2021 | 4,3617 | 253 | 0,2049 | 2,6496 | 5,1914 | 4,2603 |
| 2022 | 2,1214 | 211 | 0,2230 | 2,4241 | 4,9988 | 4,2016 |

Alti yil toplu: M6_B eksik %1,5318, gunduz medyan 2,6351 kW, maks
5,5590; M2_C eksik %1,5322, gunduz medyan 2,9371 kW, maks 5,9518.

**Elenen:** sistem 12 (M5_B). Gun ortasi cokusu - invertor termal
sinirlamasi veya MPPT arizasi imzasi. Hedef degiskende fizikle celisen
sistematik yanlilik; kullanilmaz.

**Sistem -> metre eslemesi** sitenin detay sayfasi URL slug'indan gelir,
dosyadan cikarilamaz: sistem 12 -> `dka-m5-b-phase`, sistem 13 ->
`dka-m6-b-phase`, sistem 18 -> `dka-m2-c-phase`.

---

## 3. Uygulama sirasi

Kurallar bu sirayla uygulanir; sira degistirilirse sonuc degisir.

1. Yillik dosyalari oku, takvim disi 288 satiri kirp, birlestir.
2. Tam 5 dakikalik izgaraya oturt; olmayan damgalar EKSIK'tir,
   sessizce atlanmaz.
3. Kural 1 (gece ofseti) - isinim kanallarini sifirla.
4. Kural 2 (nem), Kural 3 (DHI<=GHI), Kural 6 (isinim ust siniri).
5. Kural 5 (negatif guc), Kural 7 (gunduz sifir bayragi).
6. Saatlige topla.
7. Transpozisyon: GHI + DHI -> 20°/kuzey duzlemi (karar 2).
8. Bolme yapilir. **Bundan SONRA** Kural 8a: esik egitim bolmesinden
   hesaplanir, kat basina yeniden.
9. Oznitelikler uretilir. Ruzgar YOK (karar 1).

Kural 8a'nin bolmeden SONRA gelmesi kuralin kendisi kadar onemlidir;
oncesine alinirsa sizinti geri gelir.

---

## 4. Bilinen kusurlar ve varsayimla gecilen her sey

1. **Konum koordinati varsayimdir.** Gunes geometrisi hesaplarinda
   `lat = -23,7621`, `lon = 133,8744` kullanildi. Siteden teyit
   EDILMEDI. Damga geleneginin ACST cikmasi ve GHI korelasyonunun
   +0,82..+0,84 olmasi koordinatin dogru mertebede oldugunu gosterir
   ama tam degerini dogrulamaz.
2. **Istasyon egimi bilinmiyor.** Olculdu, 11-17 derece araliginda
   bracket edildi, 20 cikmadi; belirsizlik kestirimin kendisinden
   buyuk. Karar 2 bu belirsizligi zincirin disina attigi icin sonuc
   etkilenmez.
3. **Azimut olculmedi.** Mevcut `gunes_yuksekligi_sin` yalnizca
   yukseklik sinusu dondurur; azimut icin tam gelis acisi formulu
   gerekir, o da Faz 2/3'un dondurulmus kod yoluna dokunurdu.
4. **Isaretlerin birimi.** Guc kanallari kW varsayildi (M6_B maks
   5,5590 ile 5,25 kWp anma gucu tutarli). Sitede birim etiketi
   ayrica dogrulanmalidir.
5. **`Weather_Daily_Rainfall` gunluk birikimlidir**, ani deger degil;
   gun icinde monoton artar ve gece yarisi sifirlanir. Aylik toplam,
   gunluk maksimumlarin toplamidir. Gunun maksimumu ile son degeri
   gunlerin %99,95'inde ayni.
6. **Sentinel degerler alti yilda uc ayda kumelenmis:** `T <= -39`
   yalniz 2018-03 (105), 2020-02 (105), 2020-03 (1439); `T > 50`
   yalniz ayni uc ay. Bu aylar icin sicaklik kanali guvenilmezdir.
   Sicaklik icin ayri bir sentinel kurali YAZILMADI - sicaklik
   `T2m` olarak oznitelik setinde oldugu icin bu bir aciktir ve
   pipeline'da acikca ele alinacaktir.
7. **Ortam:** 4-7 Agustos 2026 kesif kosularinda `pandas._libs.parsers`
   DLL'i bir kez "Uygulama Denetimi ilkesi bu dosyayi engelledi"
   hatasiyla yuklenemedi, ikinci denemede acildi. pyarrow'da yasananla
   ayni sinif (Windows Smart App Control). SAC ayarina DOKUNULMADI.

---

## 5. Kurallarin dayandigi kesif bulgulari

Bu bolum kayit icindir; kural uretmez.

### 5.1 Zaman damgasi yerel ACST (UTC+9:30)

| yil | gunluk GHI tepe medyani | corr(sin h, GHI) ACST | UTC | GHI>50 gunduz orani ACST | UTC |
|---|---|---|---|---|---|
| 2018 | 12:35 | +0,8407 | -0,6276 | %100,00 | %16,73 |
| 2020 | 12:25 | +0,8241 | -0,6177 | %100,00 | %17,28 |
| 2022 | 12:30 | +0,8256 | -0,6154 | %100,00 | %17,52 |

### 5.2 Meteoroloji serilerinde ADIM vs SURUKLENME

Karar kurali sonuclar gorulmeden sabitlendi. Mevsimsellikten arindir
(ay-of-yil ortalamasi cikar); `D(k) = |ort(sonra) - ort(once)| / sd`,
her yanda >=6 ay; `D_maks >= 2,0` -> ADIM; degilse EKK egimi
`|t| >= 3,0` -> SURUKLENME; ikisi de degilse DURAGAN. Ikinci tarama:
ozyinelemeli ikili bolme, kabul esigi `D >= 1,5`.

| seri | karar | D_maks | eğim/yil | t | kabul edilen kirilma |
|---|---|---|---|---|---|
| DHI_ort | SURUKLENME | 1,5804 | +1,9453 W/m2 | +3,466 | 2022-05 (+14,0099) |
| DHI/GHI | DURAGAN | 1,3847 | +0,0124 | +2,449 | 2022-05 (+0,1051) |
| gece_GHI_ort | DURAGAN | 1,0699 | -0,0762 | -1,614 | yok |
| gece_GHI_med | DURAGAN | 1,4411 | -0,0787 | -2,136 | 2018-05, 2022-05 |
| nem_ort | SURUKLENME | 1,2567 | +1,4691 % | +3,102 | yok |
| sic_ort | DURAGAN | 0,9255 | -0,2656 C | -2,292 | yok |
| GHI_ort | DURAGAN | 1,0464 | -1,0388 W/m2 | -0,747 | yok |
| M6B_gunduz_med | DURAGAN | 1,4537 | -0,0344 kW | -2,050 | 2022-05 (-0,3668) |

**Hicbir seri D_maks >= 2,0 esigini gecmiyor.** 72 ayda en buyuk tek
bolme istatistigi 1,7524.

Gece GHI'de tek adim veya duzgun surukleme yoktur; **tekrarlayan rejim**
vardir - en az alti gecis, yuksek rejim ~2,8-3,3 W/m2, dusuk rejim
~1,4-2,1 W/m2:

| blok | aylar | ortalama |
|---|---|---|
| yuksek | 2017-01 .. 2018-04 | 2,7948 |
| dusuk | 2018-05 .. 2019-05 | 1,8032 |
| yuksek | 2019-06 .. 2019-09 | 3,0547 |
| dusuk | 2019-10 .. 2020-02 | 1,7141 |
| yuksek | 2020-03 .. 2020-06 | 3,7598 |
| dusuk | 2020-07 .. 2022-04 | 1,7660 |
| yuksek | 2022-05 .. 2022-12 | 3,0095 |

### 5.3 "Historical" / "Class A" ayrimi dosyalara YANSIMAMIS

Sitede meteoroloji 2008-Nisan 2019 "Historical", sonrasi "Class A" diye
ayriliyor. Nisan 2019'a zorlanan bolmenin istatistigi her seride kendi
maksimumunun cok altinda: DHI_ort 0,574 · DHI/GHI 0,385 · gece_GHI_ort
0,256 · gece_GHI_med 0,471 · nem 0,401 · sicaklik 0,458 · GHI **0,030** ·
GTI/GHI 0,926. Gunluk cozunurlukte de kesinti yok (Mart-Mayis 2019 gece
GHI gunluk ortalamasi 1,23-2,04 bandinda duz).

O tarihe yakin tek gercek olay egik kanal KESINTISIDIR (kullanilabilirlik,
kalibrasyon degil): GTI aylik NaN orani 2019-05 %68,3 · 2019-06 %87,3 ·
**2019-07 %100,0** · 2019-08 %87,8 · 2019-09 %62,8 · 2019-10 %87,6.
GHI/DHI ayni aylarda kesintisiz.

**Sonuc: bu ayrim yillik dosyalara yansimamistir; kaynak degisimi icin
ayri bir kural veya kukla degisken GEREKMEZ.**

### 5.4 2022-05 olayi HAVA'dir, alet degil

Kirilmanin dordu de (DHI_ort, DHI/GHI, gece_GHI_med, M6B_gunduz_med)
ayni aya, 2022-05'e dusuyor. Yorum kurali sonuclar gorulmeden yazildi:
HAVA ise yagis artar, berrak oran duser, GHI duser, DHI artar - dordu
de ayni yonde. ALET ise DHI artar ama yagis ve bulutlanma degismez.

2022-05..12 ile 2017-2021'in AYNI takvim aylari (5 yil x 8 ay = 40 ay):

| seri | 2022-05..12 | 2017-2021 ayni aylar | fark | fark% | z |
|---|---|---|---|---|---|
| yagis (mm/ay) | 23,7250 | 15,4500 | +8,2750 | +53,56 | +0,26 |
| yagisli gun | 4,6250 | 3,1250 | +1,5000 | +48,00 | +0,39 |
| berrak satir orani | 0,4931 | 0,6348 | -0,1417 | -22,32 | -0,90 |
| berrak gun orani | 0,3266 | 0,5159 | -0,1893 | -36,69 | -0,74 |
| bulutlu satir orani | 0,2714 | 0,1333 | +0,1381 | +103,54 | +1,45 |
| GHI (W/m2) | 242,0586 | 264,7850 | -22,7264 | -8,58 | -0,43 |
| DHI (W/m2) | 62,7057 | 47,7618 | +14,9439 | +31,29 | +0,77 |
| DHI/GHI medyan | 0,2263 | 0,1323 | +0,0940 | +71,07 | +1,84 |
| M6_B gunduz medyan (kW) | 2,3111 | 2,7023 | -0,3912 | -14,48 | -1,07 |

**Dort isaretin dordu de HAVA yonunde (4/4).** Yillik yagis toplami bunu
tek basina tasiyor: 2017 238,4 · 2018 242,8 · 2019 54,0 · 2020 191,2 ·
2021 212,0 · **2022 445,6 mm** - alti yilin en yaglisi, ikincisinin
%84 uzerinde ve uzun donem ortalamasinin (~280 mm) 1,6 kati.
Ay bazinda 2022, DHI'de bes ayda (05, 08, 10, 11, 12) alti yilin
REKORUNU kiriyor; ayni aylarda berrak oran alti yilin en dusugu.

**Tek cumleyle: 2022-05 kirilmasi alet degil HAVA'dir - alti yilin en
yagisli yilinda atmosfer bulaniklasmis, yayili oran artmis, huzme
azalmis, iki PV dizisi birden ayni yonde dusmustur.**

---

## 6. Bu belge degistiginde

Kural degisirse:
1. Degisiklik `[SONRADAN eklendi - <tarih>]` diye isaretlenir.
2. Gerekce yazilir: hangi gozlem degistirdi, sonuca bakildi mi.
3. Eski hali SILINMEZ, ustu cizilmez - yerinde birakilir.

Bir kuralin sonuclar gorulduKten sonra degistirilmesi MUMKUNDUR ama
GIZLENEMEZ. `ozet.py` / `ozet_sonrasi.py` ayrimindaki ile ayni disiplin.
