# DKASC kalite kontrol kurallari - ON-KAYIT

**Yazildigi tarih: 7 Agustos 2026.** Bu dosya, DKASC verisinin HICBIR
satiri islenmeden, hicbir oznitelik uretilmeden, hicbir model egitilmeden
once yazildi ve commit edildi. Amaci `pv10/ozet.py` ile ayni: kural
seciminin post-hoc olmadigini dosya duzeyinde `git log` ile
gosterebilmek.

Bu dosyaya sonradan eklenen her madde `[SONRADAN eklendi - <tarih>]`
diye isaretlenir ve gerekcesi yazilir. Isaretsiz madde, veri islenmeden
once sabitlenmistir.

Kurallarin dayandigi gozlemler bir KESIF turundan gelir (4-8 Agustos
2026). Kesif yalnizca okudu; hicbir kural uygulanmadi, hicbir deger
degistirilmedi, repoya veri girmedi.

**8 Agustos 2026 eklemeleri de veri islenmeden oncedir.** Kural 9,
Kural 10, Karar 4, Karar 5 ve bolum 4'un guncellenen maddeleri
`dkasc_pipeline.py`'nin ILK SATIRI YAZILMADAN once, ayri bir commit'te
girdi. Dosya duzeyinde `git log dokumanlar/dkasc-kalite-kurallari.md`
bunu gosterir: bu commit ile pipeline commit'i ayridir ve bu once
gelir. Sebep `pv10/ozet.py` ile ayni - on-kayit disiplini
bulanmamalidir.

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

> `[SONRADAN eklendi - 8 Agustos 2026]` Bu bolume iki kural eklendi:
> **Kural 9** (sicaklik gecerli araligi) ve **Kural 10** (saatlik
> toplamada tam yuva sarti). Ikisi de asagida, kendi gerekceleri ve
> "neden sonradan" aciklamalariyla duruyor. Ikisi de DKASC verisinin
> hicbir satiri islenmeden, hicbir model egitilmeden once yazildi.
> Baslik "Sekiz kural" olarak birakildi; bolum 6 geregi eski hali
> silinmez.

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
- **Etkilenen:** 1.126 satir eksige cevrilir. (Uretimde 1.117; fark,
  kural 1'in once kosmasi ve gunes konumunun etiket + 2,5 dk'dan
  hesaplanmasindandir.)

#### Kural 6 TESHISI - kural DEGISTIRILMEDI  `[SONRADAN eklendi - 8 Agustos 2026]`

Kural 10'un cokusu arastirilirken kural 6'nin nerede atesledigi
olculdu. **Teshis amaclidir; kural degistirilmemistir.** Yorum kurali
olcumden ONCE yazildi: vuruslar alcak guneste yogunlasiyorsa uygulama
yazili niyetle (fiziksel tavan) uyusmuyor demektir; gun boyuna
yayilmissa kural gercek sensor sicramalarini yakaliyor demektir.

Olcum (1.117 vurulan yuva):

| | |
|---|---|
| sin h medyani | **0,00223** (yukseklik **0,128 derece**) |
| sin h < 0,05 orani | **%99,64** (1.113 yuva) |
| kiyas: butun gunduz yuvalarinda sin h < 0,10 orani | %7,35 |
| vurus aninda GHI medyani | **12,949 W/m2** (p95 21,746) |
| GHI < 20 W/m2 orani | %92,48 |
| gunes ogleninden \|sapma\| medyani | **355 dakika** |
| oglene 180 dk'dan yakin vurus | **0 (sifir)** |
| 300+ dk uzaktaki vurus | %99,64 |
| `sin h > 0,05` kisitiyla kalan vurus | **1.117'den 4'e** |
| yillik dagilim | 2017-2022: 192/184/189/180/179/193 |

**Sonuc: uygulama, kuralin yazili niyetiyle ALCAK GUNES bolgesinde
uyusmuyor.** Kuralin gerekcesi yuksek isinimda fiziksel bir tavandi
("bulut kenari yansimasi 1,4 kata cikabilir; 1,5 kat ustu fiziksel
degildir"); pratikte 0,13 derece yukseklikte, 13 W/m2'lik degerlerde
atesliyor. Mekanizma: `G0 = E0 x sin h` ufka yaklasirken sifira gider
(vurus aninda medyan G0 = 3,103 W/m2), oysa kural 1'in olctugu
piranometre ofseti ayni mertebededir (gece medyani 2,2921, p99
9,9649 W/m2). Ufkun hemen ustunde kural 1 artik sifirlama yapmaz ama
ofset durmaya devam eder; `1,5 x G0` cizgisi sensorun kendi
gurultusunun ICINE duser. Kuralin gercekten aradigi seyi - hakiki
sensor sicramalarini - yakaladigi da goruluyor ama nadiren: sin h >
0,15 olan yalnizca 2 vurus var, birinin GHI'si 2015,182 W/m2.

**KURAL DEGISTIRILMEDI.** Ateslenme oruntusu asagi akista sorun
yarattigi icin ON-KAYITLI bir esigi gevsetmek, tam olarak bu makalenin
elestirdigi post-hoc davranistir. Kayda gecirilmistir ve makalede
boyle raporlanacaktir. Etkisi kural 10'un yururlukteki haliyle zaten
notrlenmistir: bir saatte kural 6 tipik olarak TEK yuvayi dusurur,
geriye 11 yuva kalir ve saat girdi esigini (>=9) gecer - kural 6'nin
kendisine dokunmadan.

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

### Kural 9 - Sicaklik gecerli araligi  `[SONRADAN eklendi - 8 Agustos 2026]`

**Neden sonradan:** 7 Agustos'ta yazilan sekiz kural sicakligi hic ele
almiyordu; eksik bolum 4, madde 6'da acik kusur olarak kaydedilmisti
("sicaklik icin ayri bir sentinel kurali YAZILMADI ... pipeline'da
acikca ele alinacaktir"). Bu madde o acigi kapatir. Kural, DKASC'nin
hicbir satiri islenmeden ve hicbir model egitilmeden once yazilmistir;
gecikme kayittadir, gizlenmemistir.

- **Gozlem** (621.933 satir):

  | bant | satir | oran |
  |---|---|---|
  | `T <= -39` (analog ray, ~-39,9879) | 1.649 | %0,2651 |
  | `-39 < T <= -20` | 1.390 | %0,2235 |
  | `-20 < T <= -15` | 1 | %0,0002 |
  | `-15 < T <= -10` | 2 | %0,0003 |
  | `45,2 < T <= 50` | 29 | %0,0047 |
  | `T > 50` | 4 | %0,0006 |
  | `T` eksik (NaN) | 600 | %0,0965 |

  Ray degeri tam sabit degil (-39,987949 .. -39,987919), 56 kesintisiz
  blok, uc ayda kumelenmis: 2018-03 (105), 2020-02 (105), 2020-03
  (1.439). `T > 50` olan dort deger: 51,2617 · 51,4537 · 61,3712 ·
  61,9235. Gecerli sicaklik araligi min -38,99 maks 46,31 ort 21,381.
- **Esik:** `T < -10 °C` veya `T > 50 °C` -> **eksik**. Ayrica
  `T <= -39` olan satirlarda **RH de eksik** sayilir.
- **Gerekce:** Alice Springs rekor dusugu -7,5 °C, rekor yuksegi
  45,2 °C. Bracket kasten GENIS tutuldu (-10 .. +50): esik veriye
  bakilarak degil, sahanin iklim rekorlarina bakilarak secilmistir ve
  rekor kiran gercek bir degeri kendi elimizle kirpmamak icin
  rekorlarin disinda birakilmistir. `45,2 < T <= 50` bandindaki 29
  satir bu yuzden KORUNUR.
  RH'nin ayrica dusurulmesi olculdu: ray satirlarinin **hepsinde** RH
  0,0116 ile 0,9518 arasindadir (medyan 0,1498), yani RH de sifira
  raylanmistir. Ray disinda RH < %0,1 olan yalnizca 19 satir vardir,
  yani bu davranis raya OZGUdur. Kural RH esigine degil rayin kendisine
  baglanmistir; `RH < 0,1` esigi 1.649 ray satirinin yalnizca 646'sini
  yakalardi.
- **Etkilenen:** 3.046 satir (%0,4898) T bakimindan eksige cevrilir;
  bunlarin 1.649'unda RH de eksige cevrilir. Kural 10 (12/12) altinda
  **259 saat** duser (T bakimindan tam olan 51.737 saatten).

### Kural 10 - Saatlik toplamada tam yuva sarti  `[SONRADAN eklendi - 8 Agustos 2026]`

**Neden sonradan:** 5 dakikadan saatlige toplama 7 Agustos'ta uygulama
sirasinda (bolum 3, adim 6) bir islem olarak yaziliydi ama EKSIK YUVA
davranisi tanimlanmamisti. Tanimsiz birakmak sessiz basarisizliktir.

- **Gozlem:** 52.584 saatlik kovada GHI'nin dolu 5 dk yuvasi:
  **12/12 = 51.736 (%98,387)**, 0/12 = 787 (%1,497), kismi = **61
  (%0,116)**. DHI birebir ayni; M6_B 12/12 = 51.742. Kismi saatlerin
  yuva dagilimi: 11 yuva 23 saat, 10 yuva 9, 9 yuva 8, 8 yuva 3,
  7 yuva 4, 5 yuva 1, 4 yuva 2, 3 yuva 4, 2 yuva 1, 1 yuva 6.
- **Esik:** bir saat ancak **12/12 yuvasi da doluysa** gecerlidir;
  aksi halde o saat EKSIK'tir. Toplama islemi ortalamadir (isinim,
  sicaklik, nem ve guc icin ayni).
- **Gerekce:** uc yuvadan alinan ortalama ile on ikiden alinan ortalama
  ayni kestirici degildir; sematik olarak ayni gorunmeleri farki gizler.
  Esigi 12'den 1'e indirmenin kazanci **61 saat (%0,116)** olculdu -
  esigi gevsetmenin bedeli, gevsetmenin getirisinden buyuktur.
  Karsilastirma: >=12 -> 51.736 gecerli saat; >=9 -> 51.776;
  >=1 -> 51.797.
- ~~**Etkilenen:** 61 saat (%0,116) ek olarak duser; 787 saat zaten
  tamamen bostur.~~ **BU SAYI YANLIS - asagiya bakin.**
- **Not:** GTI'nin 12/12 orani yalnizca %87,502'dir (0/12 = 6.216).
  Bu kanal karar 2 geregi kullanilmadigi icin esigi baglamaz.

#### Kural 10 duzeltmesi  `[SONRADAN eklendi - 8 Agustos 2026, ikinci duzeltme]`

**Yukaridaki "61 saat" sayisi HAM veride olculmustu.** Uretimde kural 10,
uygulama sirasinin YEDINCI adimidir: kural 6 ve kural 9 ONDAN ONCE kosar
ve tek tek 5 dk yuvalarini eksige cevirir. Iki kural ayri ayri dogru
sayilmisti; ETKILESIMLERI hic hesaplanmamisti.

Uretimde olculen gercek bedel:

| kaynak | saat | oran |
|---|---|---|
| tamamen bos (0/12, hicbir kanalda olcum yok) | 787 | %35,63 |
| kismi gercek olcum (1-11 yuva) | 62 | %2,81 |
| **ham 12/12 TAMDI, kural dusurdu** | **1.360** | **%61,57** |
| - bunlardan kural 6 (GHI) | 1.115 | |
| - bunlardan kural 9 (T2m) | 257 | |
| **toplam gecersiz saat** | **2.209** | **%4,2009** |

Yani kural 10'un ek bedeli 61 degil **1.422 saattir** (62 kismi +
1.360 kural). Fark, kurallarin BIRBIRINE degil veriye bakilarak
sayilmasindan geliyor.

Bunun yikici sonucu asagi akista goruldu: `roll168` 168 ARDISIK gecerli
saat ister; kural 6'nin dusurdugu 1.115 saatin neredeyse hepsi tek
basina duran deliklerdir ve iclerinden gectikleri her 168 saatlik
pencereyi parcalar. Alti yilda yalnizca 22 adet >=168 saatlik kesintisiz
blok kalmisti ve **oznitelik tablosu 52.584 satirdan 1.344'e (%2,56)
dusuyordu** - 2022'de 57 satir. Bu haliyle DKASC ablasyonu kosulamazdi.

#### Kural 10'un YURURLUKTEKI hali  `[SONRADAN eklendi - 8 Agustos 2026]`

**Esik GIRDIDE gevser, HEDEF ve DEGERLENDIRMEDE siki kalir.**

- **Girdi (gecikme ve yuvarlanma ozniteliklerinin kaynagi):** bir saat,
  dort kanalin her birinde **en az 9/12 yuvasi doluysa** gecerlidir ve o
  saatin kismi ortalamasi kullanilir.
- **Hedef ve degerlendirme:** **12/12 SARTI AYNEN DURUR.** Girdi
  esigiyle gecen ama 12/12 olmayan saatler bayraklanir; ne egitim hedefi
  ne test gozlemi olurlar. Yalnizca baska satirlarin gecikme kaynagi
  olarak yasarlar.

**Bu desen bu projede YENI DEGILDIR.** Gece satirlarini egitimde tutup
gunduz filtresini yalnizca DEGERLENDIRMEDE uyguluyoruz (CLAUDE.md,
"gece satirlari" dersi; kural 1 ve kural 7'nin notlari da ayni sey).
Filtrenin girdide degil ciktida uygulanmasi, bu calismanin bastan beri
savundugu ayrimdir: egitim gercek isletme kosullarini gorur,
degerlendirme temiz kosulda olculur. Kural 10 artik ayni desende.

**Neden ARA DEGER DEGIL.** Once dogrusal ara deger dusunuldu (izole
tek saatler komsulardan doldurulur). Olculdu ve **daha kotu cikti**:
ara deger (K=1) 46.748 kullanilabilir satir verirken girdi esigi >=9
**46.857** veriyor - yani ara deger, uydurma sayi ekleyerek daha AZ
satir kurtariyor. Sebep, bu saatlerin bos olmamasidir: izole tek
saatlerin %97,43'unde ham veri 12/12 TAMDI ve kural onlari dusurmustu,
%2,57'sinde de kismi gercek olcum vardi; **hicbiri bos degildi (0/12
oran: %0,00).** Doldurulacak bir delik yoktu - kullanilmayan bir olcum
vardi. Bu yolla kullanilan her sayi GERCEK olcumun ortalamasidir.

**Neden 9, 1 degil.** Kural 10'un ilk gerekcesi hala gecerli: uc
yuvadan alinan ortalama ile on ikiden alinan ayni kestirici degildir.
9/12 saatin ucte dorduduur; 1/12 ise saatlik ortalama kiligina girmis
bir nokta ornegidir. Olculen kazanc bu gerekceyi bozmaya degmiyor:

| girdi esigi | oznitelik satiri | hedefi de dolu | oran |
|---|---|---|---|
| 12/12 (eski) | 1.344 | 1.321 | %2,51 |
| >= 11 yuva | 46.109 | 44.856 | %85,30 |
| **>= 9 yuva (SECILEN)** | **48.162** | **46.857** | **%89,11** |
| >= 1 yuva | 49.181 | 47.854 | %91,00 |
| *(kiyas) K=1 ara deger* | *48.044* | *46.748* | *%88,90* |

- **Etkilenen:** girdi olarak gecerli saat 50.375 -> 51.520; hedef ve
  degerlendirme icin gecerli saat **50.375 olarak DEGISMEZ.**

---

## 2. Uc karar

> `[SONRADAN eklendi - 8 Agustos 2026]` Bu bolume iki karar eklendi:
> **Karar 4** (transpozisyon modeli izotropik + dogrulama kapisi) ve
> **Karar 5** (geometri saat merkezinden, izgara yerel saatte). Baslik
> "Uc karar" olarak birakildi; bolum 6 geregi eski hali silinmez.

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

### Karar 4 - Transpozisyon modeli IZOTROPIK (Liu-Jordan)  `[SONRADAN eklendi - 8 Agustos 2026]`

**Neden sonradan:** karar 2 "GHI+DHI'den standart transpozisyon" diyor
ama HANGI transpozisyon modeli oldugunu soylemiyordu. Model secimi
uretilen `G_i` degerini degistirir; tanimsiz birakilamaz.

**Secim gelenege gore degil OLCUME gore yapildi.** Iki model, ayni
254.741 satirda (`sin h > 0,10`, `GHI > 20`, `DHI <= GHI`, GTI dolu),
egik piranometrenin OLCUMUNE karsi, egim taramasiyla:

| egim | izo MBE | izo RMSE | izo R2 | Hay-Davies MBE | HD RMSE | HD R2 |
|---|---|---|---|---|---|---|
| 0° | -37,5594 | 94,8296 (%15,13) | 0,92370 | -37,5594 | 94,8296 | 0,92370 |
| 11° | -6,5823 | 54,2796 (%8,66) | 0,97500 | -3,2986 | 52,2441 | 0,97680 |
| 14° | -1,3145 | 48,6780 (%7,77) | 0,97990 | +2,6894 | 47,7497 | 0,98070 |
| 16° | +1,4234 | 46,6126 (%7,44) | 0,98160 | +5,8635 | **46,9048** | 0,98134 |
| **18°** | +3,5389 | **45,9182 (%7,33)** | **0,98212** | +8,3797 | 47,6904 | 0,98070 |
| 20° | +5,0299 | 46,5254 (%7,42) | 0,98160 | +10,2354 | 49,8771 | 0,97890 |
| 30° | +3,1107 | 63,3162 (%10,10) | 0,96600 | +9,5924 | 72,8611 | 0,95500 |

- Izotropik en iyi egim **18°** (MBE-sifir 15°); Hay-Davies en iyi **16°**
  (MBE-sifir 13°). Ikisi de karar 2'nin 11-17° bracket'iyle ortusur.
- **Izotropik, Hay-Davies'ten IYIDIR** (45,9182 vs 46,9048 W/m2;
  R2 0,98212 vs 0,98134). Hay-Davies'in cevresel-gunes terimi bu sahanin
  yuksek berrak-gok oraninda `Rb` uzerinden fazla sisiriyor.
- **Sonuc model secimine dayaniklidir:** 20°/kuzey duzleminde iki modelin
  farki ortalama **+5,206 W/m2 (+%0,824)**, p99 31,901, maks 103,991.

**Karar:** izotropik. Bilesenler PVGIS'in `components=1` yapisini birebir
taklit eder, boylece `G_i`'nin bilesenlerden geri kurulmasi iki kolda
AYNI islemdir:

```
Gb_i = (GHI - DHI) * Rb
Gd_i = DHI * (1 + cos B) / 2
Gr_i = GHI * rho * (1 - cos B) / 2          rho = 0,20
G_i  = Gb_i + Gd_i + Gr_i
```

`cos(theta)` kopyalanmis bir formulden degil, URETIM fonksiyonundan
gelir: ekvatora bakan duzlem icin `cos(theta) = sin h(lat + B)`, yani
`gunes_yuksekligi_sin(lat + B, lon, t)`. `Rb` paydasi `max(sin h, 0,05)`
ile tabanlanir.

**Kapi (uretimde zorunlu):** kosuda transpozisyon olculen GTI'ye karsi
yeniden dogrulanir. Esikler burada, sonuc gorulmeden sabitlenmistir:
`RMSE <= %9` VE `|MBE| <= %2` VE `RMSE-optimal egim 11-20°` araliginda.
Gecmezse kosu DURUR. **Negatif kontrol:** kapi kasten `B = 0°` ile
cagrildiginda KIRMIZI yanmalidir (0°'da RMSE %15,13, MBE -%5,99 - yakalar).
Invaryant 5 dersi: kapi uretim fonksiyonunu cagirir ve yanlisi
yakalayamiyorsa islevsizdir.

### Karar 5 - Geometri SAAT MERKEZINDEN; izgara YEREL saatte  `[SONRADAN eklendi - 8 Agustos 2026]`

**Olcum:** alti dosyanin altisi da `01-01 00:00` ile baslar, `23:55` ile
biter; gunun ilk uc damgasi `00:00, 00:05, 00:10`. Bu, **aralik SONU**
etiketlemesini eler (o gelenek `00:05 .. 24:00` verirdi). Geriye aralik
BASI ile ANLIK ornek kalir; ikisi 2,5 dakika ayrisir.

Gunes ogleni 1.991 tam ve kesintisiz gunde olculdu (GHI>20 blogunun orta
noktasi): gozlenen eksi tahmin medyan **+4,498 dk**, ortalama +4,113,
sd 17,237. Bu artik BOYLAM hatasi olarak da ETIKET OFSETI olarak da
okunabilir - ikisi de saat acisinda sabit kaymadir ve isinimdan
**AYRILAMAZ**. Ustelik artik sabit degil, alti yilda suruklenir
(2017 +6,00 · 2018 +6,00 · 2019 +5,25 · 2020 +4,00 · 2021 +3,50 ·
2022 +4,00 dk; yillik standart hata ~0,95 dk), yani tamami tek bir
gelenek farkiyla aciklanamaz.

**Belirleyici olan bu 2,5 dakika degildir.** Saatlige toplandiginda
`HH:00`'dan `HH:55`'e on iki yuva `[HH:00, HH+1:00)` araligini kaplar;
temsil ettigi an **`HH:30`**'dur. Geometriyi `HH:00`'dan hesaplamak
**30 dakika = 7,5 derece** saat acisi hatasi verir - PVGIS'te yakalanan
`:09/:10` hatasinin (~1,5°) BES KATI. Cozulemeyen 2,5 dakikalik
belirsizlik ise 0,6°'dir.

**Karar:**
- Izgara **yerel ACST saatinde** kurulur; dosya zaten yerel gun
  sinirlarinda yatiyor.
- `time_local` = yerel `HH:00`; `time_utc` = `time_local - 9:30`
  (dakikasi `:30` olur); `time_gozlem` = `time_utc + 30 dk` = saatin
  merkezi. Butun gunes geometrisi `time_gozlem`'den hesaplanir.
- Sonuc: `h_sin`/`h_cos` PVGIS koluna gore sabit bir aci kadar DONER.
  Dogrusal modellerde bu (sin, cos) ciftinin tam bir dondurmesidir,
  yani birebir yeniden parametrizasyondur; agaclarda bolmeler
  degismez. Zararsizdir ama PVGIS ile kiyaslayan okuyucu `:00` bekler,
  bu yuzden kunyeye yazilir.

### Karar 6 - Ikinci olcum dizisi M15_A (sistem 23, Calyxo CdTe); yedek M3_A  `[SONRADAN eklendi - 22 Ekim 2026]`

**Bu secim M6_B'nin SONUCLARI GORULDUKTEN SONRA yapildi.** M6_B
ablasyonu (`2a0036f`), belirsizlik olcumu (`690f03a`) ve faz notu
(`c24f908`) bu karardan once yazildi ve okundu. Dolayisiyla bu karar
karar 1-5 ile ayni anlamda on-kayit DEGILDIR. Asagidaki ayrim
yapilir ve korunur:

- **Secim olcutu yalnizca VERI KALITESIDIR.** Hicbir aday dizide model
  egitilmedi, hicbir aday dizinin ablasyon veya tahmin sonucu
  uretilmedi ya da okunmadi. Secimin kaniti `arac/dizi_tarama.py` ->
  `sonuclar/dkasc_dizi_tarama.csv`; ham veri, kural uygulanmadan,
  karar 3 tablosunun olcutleriyle. Kontrol: M6_B satiri karar 3'u
  birebir verir (eksik %1,5318, gunduz medyan 2,6351 kW, maks
  5,5590, kural 8a gostergesi 70 gun; tek fark gun paydasi 2163'e
  karsi 2164).
- **Kurallar 1-10 ve karar 1-5 DEGISMEZ.** M15_A icin yeni kural
  yazilmaz, esik oynatilmaz. Kural 5, 7, 8a dizi bagimlidir; sayimlari
  yeniden olculur ve bu bolume `[SONRADAN eklendi]` diye eklenir,
  esikleri degil.
- **Ablasyon M6_B ile AYNI izgarayla kosulur**: ayni varyantlar, ayni
  uc model, ayni test yillari (2018-2022), ayni oznitelik seti
  (`DKASC_GECIKMELI`, `DKASC_ESZAMAN`).

**Soru:** Replikasyonun bulgusu (simulasyon `eszaman`'i abartiyor,
`rastgele_kfold`'u kucumsuyor) tek bir mono-Si diziye mi ozgu?
Bunu yalnizca farkli teknolojide ikinci bir olcum dizisi sinayabilir.

**Secim olcutu (sirayla uygulanir):**

1. Panel teknolojisi M6_B'den (mono-Si) FARKLI.
2. Ayni duzlem: sabit montaj, egim 20°, azimut 0° (kuzey). Boylece
   `G_i` (karar 2, 4) birebir ayni kalir ve iki dizi arasinda degisen
   TEK sey hedef `P` olur. GHI, DHI ve sicaklik zaten ortak hava
   istasyonundandir (`101_DKA_WeatherStation_*`), dizilere ait degil.
3. 2017-2022'nin alti yilinin HER BIRINDE calisir durumda: yillik
   gunduz medyani cokmemis (asagidaki tabloda "bozuk" diye isaretli
   yil yok), sistem sokulmemis, uretici/site "kiyas icin kullanmayin"
   notu yok.
4. Bunlari gecen adaylar arasinda en dusuk ariza imzasi (gunduz sifir
   orani, `GHI > 200` iken `P == 0`).

**Aday tablosu** (`sonuclar/dkasc_dizi_tarama.csv`, `yil == "tum"`;
teknoloji, kapasite ve duzlem sitenin detay sayfasindan, 22 Ekim 2026):

| metre (sistem) | teknoloji | kWp | eksik % | gunduz sifir % | negatif | GHI>200, P=0 | olcut 3 |
|---|---|---|---|---|---|---|---|
| M6_B (13) - mevcut | mono-Si | 5,25 | 1,5318 | 0,1969 | 1.825 | 108 | gecer |
| **M15_A (23) Calyxo CX-50** | **CdTe ince film** | **5,4** | 4,1738 | 0,7415 | 87 | 31 | **gecer** |
| M3_A (14) Kyocera KD135GX-LP | poli-Si | 5,4 | 1,5317 | 0,3777 | 5.872 | 110 | gecer |
| M5_C (11) BP 3165N | poli-Si | 4,95 | 1,5323 | 0,6098 | 7.107 | 108 | gecer |
| M20_B (29) CSUN 250-60P | poli-Si | 6,0 | 4,1732 | 0,1133 | 1.285 | 31 | gecer |
| M17_C (36) NovoPolymers | poli-Si, mikroinvertor | 5,2 | 4,1732 | 0,0402 | 0 | 31 | gecer |
| M4_A (8) Kaneka G-EA060 | a-Si ince film | 6,0 | 1,5322 | 1,3660 | 10.391 | 140 | KALMAZ: 2021 ve 2022 gunduz medyani 1,1693 / 0,9845 kW (diger yillar 2,80-3,08); invertor 29 Nisan 2022'de degisti |
| M4_B (17) Sanyo HIP-210NKHE5 | HIT | 6,3 | 1,5322 | 1,0196 | 1.260 | 254 | KALMAZ: 2019 gunduz medyani 1,6106 kW (diger yillar 3,19-3,47); site "Aralik 2018'den beri dusuk uretim", invertor Mayis 2019'da degisti |
| M16_B Hanergy/Solibro SL1-85 | CIGS ince film | 5,61 | 4,1740 | 5,3193 | 253 | 87 | KALMAZ: 2019-2022 maks 0,09-0,12 kW - dizi fiilen olu |
| M6_A (7) First Solar FS-272 | CdTe (prototip) | 6,96 | 1,5314 | 6,8937 | 268.955 | 15.995 | KALMAZ: site "prototip, kiyas icin kullanilmamali"; 2018 gunduz sifir %39,79 |
| M18_A (28) First Solar FS-387 | CdTe | 5,6 | 4,1736 | 4,1281 | 856 | 481 | KALMAZ: Mayis 2020'de sokuldu; 2021-2022 maks 0,06-0,10 kW |

M3_B ve M3_C (Kyocera poli-Si) olcut 3'te kalir (2021 gunduz medyani
0,0870 kW; 2019 1,2379 kW). M9_B / M9_A_C (Trina mono-Si, cift eksen
izleyici) olcut 1 ve 2'de, M11 (eco-Kinetics mono-Si) olcut 1'de,
M10 (SolFocus CPV, izleyici) olcut 2'de kalir. Sistem 9A (Solibro
SL2-130, CIGS, 5,2 kWp) 20 Ekim 2017'de kuruldu, 2017'yi kapsamaz;
olcut 3'te kalir (site metre eslemesini vermiyor).

**Tablonun kapsami:** ince film ve HIT adaylarinin HEPSI tabloda. Diger
c-Si dizileri (BP, Q CELLS, REC, Winaico, Tindo, Elkem, Canadian Solar,
TDG, Sungrid, Solco ...) teknoloji acisindan tek tek incelenmedi;
hepsi c-Si ailesindedir ve olcut 1 icin M15_A'dan zayif adaydir.
Tabloya alinan dort poli-Si dizi yedek secimi icin ornek alindi,
c-Si'nin tam taramasi DEGILDIR.

**Secilen:** `61_DKA_M15_A_Phase_Active_Power` = sistem 23, Calyxo
CX-50, **CdTe ince film, 5,4 kWp, sabit, egim 20° / azimut 0°**,
kurulum 1 Mart 2010. Olcut 1-3'u gecen TEK c-Si disi aday; tabloda
olcutleri gecen diger dort aday poli-Si, yani c-Si ailesinde kalir.

**Yedek:** `90_DKA_M3_A_Phase_Active_Power` = sistem 14, Kyocera
KD135GX-LP, poli-Si, 5,4 kWp, sabit, 20° / 0°. Tabloda olcut 2-3'u
gecen poli-Si adaylari icinde eksik orani en dusuk olan. Yalnizca M15_A
asagidaki durma esiklerinden birine takilir VE kullaniciya
sorulduktan sonra devreye girer.

**Bilinen zayiflik:** M15_A'nin eksik orani M6_B'nin 2,7 kati (%4,1738;
2018'de %8,4209). Sebep 23-38 numarali sistemlerin ortak kesintileri
(site notlari: Aralik 2016, Aralik 2017 - Ocak 2018, Temmuz 2018,
Agustos 2021 sayac arizasi). Kural 10'un 12/12 sartiyla etkilesimi
(bolum 4, madde 12) bu tabloda OLCULMEDI; uretimde olculecek.

**Durma esikleri - pipeline kosmadan ONCE sabitlendi.** Asagidakilerden
biri gerceklesirse ablasyon KOSULMAZ, kullaniciya sorulur:

- M15_A'nin hedef-gecerli saat sayisi M6_B'ninkinin (46.857) %90'inin
  altinda (< 42.171), ya da herhangi bir test yilinda M6_B'nin ayni
  yilinin %85'inin altinda.
- Kural 5, 7 veya 8a'nin uretimdeki sayimi M6_B'nin ayni sayiminin 3
  katini asiyor.
- Sema kapisi, transpozisyon kapisi ya da herhangi bir invaryant
  kirmizi.
- Dizi kanalinda M6_B'de gorulmeyen yeni bir hata sinifi (ornegin
  sabit deger platosu, birim degisimi) gorunuyor.

**Kapasite:** `kapasite_w = 5400`. `nRMSE_kapasite` ve
`fark_kapasite_yuzde` bu paydayla hesaplanir.

#### Karar 6 - uretim sayimlari ve durma esikleri  `[SONRADAN eklendi - 22 Ekim 2026]`

Pipeline `--dizi m15a` ile kosuldu, veri donduruldu:
**`be6dd9e1a15dcc61`** (`veri/dkasc_m15a.parquet`, 52.584 saat). Model
EGITILMEDI. Kurallar ve esikler degistirilmedi.

**Kapilar:** transpozisyon kapisi GECTI (n 254.740, en iyi egim 18°,
RMSE %7,288, MBE +%0,577, R2 0,98231); negatif kontrol (0°) KIRMIZI
yandi (RMSE %15,113, MBE -%5,982) - beklenen. Sema kapisi GECTI. Hava
kanallarinin butun sayimlari (k1, k2, k3, k6, k9, transpozisyon kapisi,
`saat_tam_GHI/DHI/T2m`) M6_B kosusuyla BIREBIR ayni; farkli cikan yalnizca
guc kanalina bagli satirlar. Ortak istasyon icin beklenen budur.

**Dizi bagimli kural sayimlari:**

| sayim | M6_B | M15_A | M15_A / M6_B |
|---|---|---|---|
| k5_negatif (kesif ile) | 1.825 (= 1.825) | 87 (= 87) | 0,048 |
| k5_eksige_cevrilen | 0 | 0 | - |
| k5_sifirlanan | 331.226 | 328.987 | 0,993 |
| k7_ariza_saat | 6 | **0** | 0 |
| saat_tam_P | 51.742 | 50.307 | 0,972 |
| saat_kati_12_12 | 50.375 | 48.946 | 0,972 |
| saat_kismi_girdi | 1.145 | 1.148 | 1,003 |
| saat_bos | 1.036 | 2.419 | 2,335 |

Kural 8a, kat basina, esik = 0,3 x EGITIM bolmesinin gunduz medyani;
populasyon degerlendirme populasyonu (`kismi` disi, `H_sun > 0`, `ariza`
disi), gun yerel takvim gunu:

| test yili | M6_B esik W | bayrakli egitim / test gunu | M15_A esik W | bayrakli egitim / test gunu |
|---|---|---|---|---|
| 2018 | 728,51 | 9/343 · 11/357 | 842,66 | 7/313 · 8/262 |
| 2019 | 745,60 | 20/699 · 3/332 | 851,11 | 15/575 · 3/312 |
| 2020 | 768,41 | 24/1030 · 8/331 | 864,30 | 18/886 · 13/298 |
| 2021 | 764,77 | 32/1360 · 12/315 | 853,81 | 31/1183 · 17/304 |
| 2022 | 762,58 | 43/1674 · 15/336 | 845,85 | 47/1486 · 19/314 |

**Kural 8a UYGULANMIYOR - M6_B dahil.** Bu olcum sirasinda goruldu:
bolum 3'teki yururlukteki sira kural 8a'yi adim 13'e ("bolme yapilir,
bundan SONRA") koyuyor, ek S3 de onu uygulanmis gibi anlatiyor; ama
`dkasc_pipeline.py`, `pv10/experiment.py:hucre_kos` ve `pv10/`'un
hicbir yerinde kural 8a kodu YOK. M6_B'nin butun DKASC sonuclari kural
8a OLMADAN uretildi. Bu bir on-kayit sapmasidir ve M15_A'dan bagimsizdir;
karari kullaniciya birakildi.

**Oznitelik duzeyinde hedef-gecerli satir** (`oznitelik_uret`, DKASC
seti, `kismi` disi; yil `time_utc`):

| yil | M6_B | M15_A | oran |
|---|---|---|---|
| 2017 | 7.986 | 7.244 | 0,9071 |
| **2018** | 8.337 | **5.998** | **0,7194** |
| 2019 | 7.691 | 7.167 | 0,9319 |
| 2020 | 7.705 | 6.834 | 0,8870 |
| 2021 | 7.310 | 7.049 | 0,9643 |
| 2022 | 7.828 | 7.279 | 0,9299 |
| **toplam** | 46.857 | **41.571** | **0,8872** |

**Durma esikleri - SONUC: IKI ESIK TUTTU, ABLASYON KOSULMADI.**

| esik | olculen | sonuc |
|---|---|---|
| toplam hedef-gecerli >= 42.171 (M6_B'nin %90'i) | 41.571 (%88,72) | **TUTTU** |
| her test yili >= M6_B'nin %85'i | 2018: %71,94; digerleri %88,70-%96,43 | **TUTTU (2018)** |
| kural 5/7/8a sayimi <= M6_B x 3 | k5 0,048x; k7 0; 8a en fazla 1,63x (2020 test 13/8) | gecmedi |
| kapi kirmizi | hepsi yesil | gecmedi |

**Kayip nereden** (M15_A 2018): `P` dolu 7.998 saat -> 12/12 sonrasi
7.810 (-188) -> oznitelik tablosu 5.998 (-1.812). Kaybin ~%90'i 12/12
sartindan DEGIL, oznitelik katmanindan geliyor: `lag168` ve
`roll168_*` tam bir 168 saatlik gecmis ister ve Ocak 2018 kesintisi
(yerel Ocak'ta 545 eksik saat; 23-38 numarali sistemlerin ortak
kesintisi, site notu "Aralik 2017 - Ocak 2018") her boslugun ardindan
bir hafta daha siler. Bolum 4, madde 12'deki kural etkilesiminin aynisi.
`ariza` saati sifir: M15_A'da `GHI > 200` iken saatlik `P == 0` hic yok
(5 dk duzeyinde 31 yuva vardi, hicbiri tam saati sifirlamiyor).

#### Karar 6 - kullanici kararlari  `[SONRADAN eklendi - 22 Ekim 2026]`

Durma esikleri tuttuktan ve kural 8a'nin uygulanmadigi bulunduktan SONRA,
herhangi bir M15_A/M3_A model sonucu uretilmeden once alindi:

1. **M15_A kosulur, esik sapmasi kayda gecer.** Yukaridaki iki esik
   (toplam %88,72; 2018 %71,94) tuttugu halde ablasyon kosulur. Kayip
   dizinin kendisinden degil, 23-38 numarali sistemlerin ortak
   kesintisinden ve `lag168`/`roll168` genislemesinden gelir. 2018 test
   yilinda istatistiksel guc daha dusuktur; bu raporlanir.
2. **M3_A ucuncu kol olarak eklenir** (yedek olarak degil, M15_A'nin
   YANINA): Kyocera poli-Si, 5,4 kWp, 20°/0°, `kapasite_w = 5400`.
   Gerekce: M6_B'nin bosluk profilini (eksik %1,53) tasiyan bir c-Si
   kontrolu. M6_B ile M3_A arasindaki fark "ayni teknoloji ailesinde
   baska dizi", M15_A ile M3_A arasindaki fark teknoloji + bosluk
   profili olur. Ablasyondan once M3_A icin de pipeline kosulur ve ayni
   durma esikleri olculur; biri tutarsa yine durulur ve sorulur.
3. **Kural 8a icin:** sapma olarak kaydedilir. Butun diziler M6_B gibi
   8a'siz kosulur; Tablo 6-7 degismez. Ek S3'e ve DKASC faz notuna
   sapma notu eklendi.

#### Karar 6 - M3_A uretim sayimlari ve durma esikleri  `[SONRADAN eklendi - 22 Ekim 2026]`

`--dizi m3a`, dondurulan surum **`9c1c08bf08a9b84b`** (52.584 saat; ikinci
kosu ayni hash). Model EGITILMEDI. Kapilar M15_A ile birebir (transpozisyon
kapisi diziden bagimsizdir); hava sayimlari M6_B ile birebir.

| sayim | M6_B | M3_A | M3_A / M6_B |
|---|---|---|---|
| k5_negatif (kesif ile) | 1.825 (= 1.825) | **5.872** (= 5.872) | **3,22** |
| k5_eksige_cevrilen | 0 | 0 | - |
| k5_sifirlanan | 331.226 | 333.618 | 1,007 |
| k7_ariza_saat | 6 | 3 | 0,50 |
| saat_kati_12_12 | 50.375 | 50.375 | 1,000 |
| oznitelik hedef-gecerli | 46.857 | 46.857 | 1,000 (her yil 1,000) |

Kural 8a kat basina (egitim / test bayrakli gun): 2018 8/343 · 12/357;
2019 20/699 · 3/332; 2020 25/1030 · 11/331; 2021 36/1360 · 16/315;
2022 51/1674 · 19/336. M6_B'ye oran en fazla 1,375 (2020 test 11/8).

**Durma esigi - SONUC: BIR ESIK HARFIYEN TUTTU, M3_A ABLASYONU KOSULMADI.**
Satir sayisi esiklerinin ikisi de gecer (%100). Ama `k5_negatif` M6_B'nin
3,22 kati ve esik "kural 5, 7 veya 8a'nin uretimdeki sayimi M6_B'nin 3
katini asiyor" diyor. Icerikte zararsiz gorunuyor: negatiflerin hepsi
+-0,05 kW olu bolgesinde (sifirlanir), eksige cevrilen 0 - kuralin
ETKISI (`k5_sifirlanan`) M6_B'nin 1,007 kati. Esik sayimi mi etkiyi mi
kastettigi on-kayitta yazmiyor; harfiyen okundu ve kullaniciya soruldu.

**Kullanici karari (22 Ekim 2026, M3_A model sonucu uretilmeden once):**
M3_A kosulur. Esigin ham sayimi mi kuralin etkisini mi kastettigi on-kayitta
belirsizdi; harfiyen okundugunda tuttu, kullanici kosturmaya karar verdi.
Sonraki esikler icin ders: esik "sayim" degil "etkilenen satir" olarak
yazilmaliydi.

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

### Yururlukteki sira  `[SONRADAN eklendi - 8 Agustos 2026]`

Yukaridaki dokuz adimlik liste 7 Agustos'ta yazildi ve **yerinde
birakilmistir**. Asagidaki liste onun yerine gecer; iki degisiklik ve
uc ekleme vardir, hepsinin gerekcesi yazilidir.

1. Alti yillik dosyayi oku, takvim disi 288 satiri kirp, birlestir
   (621.933 satir).
2. Tam 5 dakikalik izgaraya oturt; olmayan damgalar EKSIK'tir.
3. Kural 1 (gece ofseti) - isinim kanallarini sifirla.
4. Kural 2 (nem), Kural 3 (DHI<=GHI), Kural 6 (isinim ust siniri),
   **Kural 9 (sicaklik araligi - YENI)**.
5. Kural 5 (negatif guc).
6. **Transpozisyon 5 DAKIKA cozunurlugunde yapilir** (karar 2 + karar 4).
   **DEGISIKLIK:** eski listede toplama (adim 6) transpozisyondan
   (adim 7) onceydi. **Gerekce:** `Rb` saat icinde nonlineerdir ve
   alcak gunes acilarinda patlar; saatlik ortalamadan hesaplanan `Rb`
   ile saat ici degerlerin ortalamasindan gelen `Rb` ayni sey degildir
   ve fark sistematiktir. Karar 4'un dogrulamasi da 5 dakikada
   yapilmistir - uretim, dogrulanan yolla ayni olmalidir.
7. **Kural 10 (YENI):** yerel saat kovalarina topla. Girdi icin
   **>=9/12** yuva sarti; hedef ve degerlendirme icin **12/12** sarti.
   12/12 olmayan ama >=9 olan saatler `kismi` bayragini alir.
   `[8 Agustos 2026'da guncellendi - eski hali "12/12 yuva sarti" idi;
   gerekce kural 10'un duzeltmesinde]`
8. **Tam saatlik izgaraya reindex (YENI - kritik).** `pv10/features.py`
   konumsal `shift(k)` kullanir. PVGIS boslusuzdu; DKASC'de 787+ eksik
   saat vardir. Boslukli bir seride `shift(24)` **24 saat oncesini
   degil 24 SATIR oncesini** alir; makalenin en guclu ozniteligi
   `G_i_lag24` yanlis satirdan gelir ve **hicbir yerde hata firlamaz**.
   Tam izgaraya reindex edilince bosluklar NaN kalir ve zorunlu-sutun
   `dropna`'si onlari dusurur. Bu bir tercih degil, "sessiz basarisizlik
   yasak" maddesidir (CLAUDE.md, kural 5).
9. **Kural 7 (gunduz sifir bayragi) SAATLIK duzeyde** hesaplanir;
   degerlendirmede dislanir, egitimde ASLA.
10. Semaya donustur: `P` kW -> W (**x1000**), `konum = "dkasc_m6b"`,
    `utc_ofset = +9,5`, `H_sun` geometriden turetilir (bolum 4,
    madde 8).
11. Transpozisyon kapisi (karar 4) + sema kapisi. Gecmezse DUR.
12. Dondur: parquet + `sha256_16` + veri surumu kunyesi.
13. **Bolme yapilir. Bundan SONRA** Kural 8a: esik egitim bolmesinden,
    kat basina yeniden.
14. Oznitelikler uretilir. Ruzgar YOK (karar 1).

---

## 4. Bilinen kusurlar ve varsayimla gecilen her sey

1. ~~**Konum koordinati varsayimdir.**~~ Gunes geometrisi hesaplarinda
   `lat = -23,7621`, `lon = 133,8744` kullanildi. Siteden teyit
   EDILMEDI. Damga geleneginin ACST cikmasi ve GHI korelasyonunun
   +0,82..+0,84 olmasi koordinatin dogru mertebede oldugunu gosterir
   ama tam degerini dogrulamaz.

   **`[SONRADAN eklendi - 8 Agustos 2026]` KUSUR KAPANDI - koordinat
   DIS KAYNAKLA DOGRULANDI.** Hakemli bir yayin DKASC'nin konumunu
   **23° 46' G, 133° 52' D, 558 m** olarak veriyor (Theoretical and
   Applied Climatology, 2022, doi:10.1007/s00704-022-04166-6). Ondalik
   karsiligi -23,7667 / 133,8667; kullandigimiz varsayimla fark
   **enlemde 0,005°, boylamda 0,007°** - gunes geometrisinde ihmal
   edilebilir. Kunyeye "koordinat: dis kaynakla dogrulandi" diye
   islenir, kaynak da yazilir. Kullanilan deger DEGISTIRILMEZ
   (-23,7621 / 133,8744); fark, olcum belirsizliginin cok altindadir
   ve degistirmek dondurulmus kesif sayilarini kaydirirdi.

   Veriden ic dogrulama denendi ve **yetersiz cikti** - bu yontemin
   kaydi: gun uzunlugundan (saat geleneginden BAGIMSIZ) ortak EKK ile
   enlem -23,060°, esik yuksekligi `sin h0 = 0,060`, artik RMS
   23,35 dk. Enlemi ±1° oynatinca artik RMS yalnizca 23,35 -> 23,53 dk
   degisiyor: bulut kaynakli kenar kirpilmasi sinyali boguyor ve
   enlem ile `s0` birbiriyle takas ediliyor. Yani veri koordinatla
   CELISMIYOR ama koordinati DOGRULAMIYOR; dogrulama disaridan geldi.
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
6. ~~**Sentinel degerler alti yilda uc ayda kumelenmis:**~~ `T <= -39`
   yalniz 2018-03 (105), 2020-02 (105), 2020-03 (1439); `T > 50`
   yalniz ayni uc ay. Bu aylar icin sicaklik kanali guvenilmezdir.
   Sicaklik icin ayri bir sentinel kurali YAZILMADI - sicaklik
   `T2m` olarak oznitelik setinde oldugu icin bu bir aciktir ve
   pipeline'da acikca ele alinacaktir.

   **`[SONRADAN eklendi - 8 Agustos 2026]` ACIK KAPANDI: Kural 9.**
   Ayrica bu maddedeki iki ifade olcumle DUZELTILMISTIR: (i) bozukluk
   yalnizca raydan ibaret degil - `-39 < T <= -20` bandinda 1.390
   satir daha var, `T < -10` toplami 3.046'dir; (ii) `T > 50` olan
   dort satirin ucuncusu ve dorduncusu (61,37 / 61,92) 2020-03'te
   degil, dagilmis haldedir. Ray satirlarinda RH de sifira raylanmistir
   (hepsi 0,0116-0,9518 arasi, medyan 0,1498), bu yuzden kural 9 RH'yi
   de dusurur.

7. **RH sifira yakin 19 satir kural disidir.** `RH < %0,1` olan 665
   satirin 646'si sicaklik rayindadir ve kural 9 ile temizlenir; kalan
   19 satir hicbir kurala takilmaz. Kural yazilmadi: 19 satir
   621.933'te %0,003'tur ve fiziksel olarak imkansiz olduklari
   gosterilemez (col ikliminde cok dusuk RH gercektir). Kayit icin
   burada duruyor.  `[SONRADAN eklendi - 8 Agustos 2026]`

8. **`H_sun` DKASC'de YOKTUR, geometriden TURETILIR - ve bu maskeyi
   ozniteliktEN bagimsiz olmaktan cikarir.**  `[SONRADAN eklendi - 8 Agustos 2026]`
   `pv10/features.py:74` `H_sun` sutununu zorunlu kilar ve
   `pv10/evaluate.py:21` gunduz maskesini `H_sun > 0` ile tanimlar.
   PVGIS'te `H_sun` PVGIS'in KENDI sutunudur; bizim Spencer
   hesabimizdan BAGIMSIZDIR, dolayisiyla geometrimizde bir hata olsa
   maske onu yakalardi. DKASC'de `H_sun` ayni Spencer rutininden
   turetilecegi icin **bu bagimsizlik kaybolur: geometride bir hata
   olursa hem maskeyi hem ozniteligi TUTARLI bicimde kaydirir ve
   kendini gizler.** Faz notunda da kusur olarak yer alir.

   Ikinci sonuc: `eszaman` sizinti varyantinda `H_sun_eszaman` artik
   `elev_sin`'in deterministik fonksiyonudur, yani **DKASC kolunda hic
   sizinti tasimaz**. Ruzgarin da olmamasiyla birlikte DKASC'nin
   `eszaman` varyantinda PVGIS'e gore IKI sizinti kanali eksiktir.
   Iki kolun sisme oranlari bu haliyle dogrudan kiyaslanamaz; kiyas
   icin PVGIS ablasyonu DKASC'nin indirgenmis oznitelik setiyle ayrica
   kosulacaktir (eslesmis kontrol kosusu, ayri log dosyasina).

9. **Etiket geleneginde 2,5 dakikalik belirsizlik COZULMEDI.**
   `[SONRADAN eklendi - 8 Agustos 2026]` Aralik SONU elendi (olculdu,
   karar 5) ama aralik BASI ile ANLIK ornek ayrilamadi; ayrilamamasinin
   sebebi boylam hatasiyla tam olarak ayni imzayi tasimalaridir.
   Buyuklugu 0,6 derece saat acisidir. Karar 5'in kapattigi 7,5
   derecelik hatanin yaninda kucuktur ama sifir degildir.

10. **Transpozisyon dogrulamasi ALCAK GUNESTE yapilmamistir.**
    `[SONRADAN eklendi - 8 Agustos 2026]` Karar 4'un 254.741 satirlik
    dogrulamasi `sin h > 0,10` (yukseklik > 5,74°) ile sinirlidir;
    `Rb`'nin en kararsiz oldugu bolge olculmemistir. Uretimde payda
    `max(sin h, 0,05)` ile tabanlanir - bu taban DOGRULANMAMIS bir
    secimdir. Alcak gunes satirlarinin gunduz enerjisine katkisi
    kucuktur, ama kayit icin buradadir.

11. **Albedo varsayimdir.** `rho = 0,20` alindi; sahada olculmedi.
    20°'lik duzlemde yer terimi GHI'nin %0,60'idir, yani rho'yu
    0,10-0,30 araliginda oynatmak `G_i`'yi ~±%0,3 kaydirir.
12. **Kurallar tek tek dogru, ETKILESIMLERI sayilmamisti.**
    `[SONRADAN eklendi - 8 Agustos 2026]` Kural 6, kural 9 ve kural
    10'un her birinin "etkilenen satir" sayisi HAM veride olculmustu.
    Uretimde kurallar SIRAYLA kosar; kural 6 ve 9'un actigi tek yuvalik
    delikler, kural 10'un 12/12 sartiyla carpisip 1.360 saat dusurdu ve
    `roll168` uzerinden oznitelik tablosunu %2,56'ya indirdi. Hicbir
    kural yanlis degildi; eksik olan, kurallarin BIRBIRINE bakilarak
    sayilmamasiydi. Bundan sonra eklenen her kural icin etkilenen satir
    sayisi, ondan ONCE gelen kurallar uygulanmis veri uzerinde de
    olculecektir.

13. **Dondurulmus surum gecmisi.** `[SONRADAN eklendi - 8 Agustos 2026]`

    | surum | sha256_16 | satir | girdi-gecerli | hedef-gecerli |
    |---|---|---|---|---|
    | ilk (girdi esigi 12/12) | `24d7f7c2e6e00585` | 52.584 | 50.375 | 50.375 |
    | **yururlukteki (girdi esigi >=9)** | **`f7f644df5e0d1618`** | 52.584 | 51.520 | 50.375 |

    Eski hash kayit icin burada birakildi. **O surumle uretilmis HICBIR
    deney sonucu yoktur** - kural 10'un cokusu ablasyon kosulmadan once
    yakalandi, dolayisiyla geri alinacak bir sayi da yok.

    Yururlukteki surumun oznitelik katmanindaki karsiligi: **47.928
    oznitelik satiri**, bunlarin **46.857'si hedef olarak kullanilabilir**
    (1.071'i `kismi` bayrakli, yalnizca gecikme kaynagi), 23.271'i gunduz.
    Yil basina hedef-gecerli: 2017/7.986 · 2018/8.337 · 2019/7.691 ·
    2020/7.705 · 2021/7.310 · 2022/7.828.

14. **Saatlik ortalama ORTAK yuva maskesinden alinir.**
    `[SONRADAN eklendi - 8 Agustos 2026]` Girdi esigi gevsedikten sonra
    bir saatte bazi kanallar dolu bazilari eksik olabiliyor. Her sutunu
    kendi dolu yuvalari uzerinden ortalamak `G_i = Gb_i + Gd_i + Gr_i`
    ozdesligini bozar: kural 6 yalnizca GHI'yi dusurdugunde o yuvada
    `Gd_i` durur ama `Gb_i`, `Gr_i` ve `G_i` duser, ortalamalar FARKLI
    kumelerden alinir. Sema kapisi bunu ilk kosuda yakaladi (maks fark
    4,027 W/m2). Bir yuva ancak DORT kanalin da dolu oldugu yuvadir;
    hem sayim hem ortalama bu ortak maskeden gecer.

15. **Ortam:** 4-7 Agustos 2026 kesif kosularinda `pandas._libs.parsers`
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

### 5.5 Dis teyitler  `[SONRADAN eklendi - 8 Agustos 2026]`

Kesifte veriden CIKARILAN iki sonucu, veri disi kaynaklar bagimsiz
olarak destekliyor:

1. **Nisan 2019 kiriginin neden cikmadigi acikandi.** "Class A" hava
   verisi DKASC'nin yillik dosyalariyla ayni akista degildir; **ayri bir
   projeye (NTSR) aittir** ve yillik dosyalara hic girmez. Bolum 5.3'te
   olculen sey - Nisan 2019'a zorlanan bolmenin her seride kendi
   maksimumunun cok altinda kalmasi (GHI'de 0,030) - bu yuzden
   beklenen sonuctur. Olcum ile belge ayni yeri gosteriyor.

   **Faz 2 acisindan sonuc:** `rastgele_kfold` varyantinin olctugu sisme
   sensor/yontem degisiminden GELMIYOR. Bu, oturumun basindaki risk
   sorusunun cevabidir.

2. **Kapsamin 2022'de bitmesi dogru karardir.** Sahaya **2023'te batarya
   kuruldu.** Batarya, olculen dizi gucu ile isinim arasindaki iliskiyi
   degistirir; 2023 ve sonrasi, oncesiyle ayni fiziksel kurulum
   degildir. Kapsam karari (bolum 0) veri indirilirken bagimsiz
   gerekcelerle verilmisti; bu teyit onu guclendirir. **2022'nin
   anormalligi hala kapsam disi birakma gerekcesi DEGILDIR** - orada
   degisen hava, kurulum degil.

---

## 6. Bu belge degistiginde

Kural degisirse:
1. Degisiklik `[SONRADAN eklendi - <tarih>]` diye isaretlenir.
2. Gerekce yazilir: hangi gozlem degistirdi, sonuca bakildi mi.
3. Eski hali SILINMEZ, ustu cizilmez - yerinde birakilir.

Bir kuralin sonuclar gorulduKten sonra degistirilmesi MUMKUNDUR ama
GIZLENEMEZ. `ozet.py` / `ozet_sonrasi.py` ayrimindaki ile ayni disiplin.
