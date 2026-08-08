# Faz 3 - siralama kararliligi  [GERIYE DONUK DERLENDI]

> **Bu not faz bittikten SONRA, koddan ve loglardan geriye donuk derlendi;
> ON-KAYIT IDDIASI TASIMAZ.**
>
> Faz 3 30 Temmuz 2026'da kosuldu ve o gun faz notu URETILMEDI. Bu dosya
> 8 Agustos 2026'da, yalnizca `git log`, commit iceriklerinde donmus kod,
> etiket mesaji ve `sonuclar/siralama_*.csv` okunarak yazildi.
> `faz-notlari/faz-4.md` ve `faz-notlari/dkasc-replikasyon.md` fazlarin
> KENDI oturumlarinda yazildi ve on-kayit iddiasi tasir; **bu not tasimaz.**
> Ayrimin korunmasi sart: geriye donuk bir not on-kayitliymis gibi
> sunulursa diger notlarin degeri de duser.
>
> "ANLASILIYOR" = koddan cikarilmis YENIDEN KURGU. "KAYITLI" = o gunku
> commit'in icinde gercekten yaziliydi.
>
> Ayrica: bu notta **YENIDEN HESAPLANMIS** bir sayi var (Kendall tau).
> Orijinal kosu onu ekrana basmis, hicbir dosyaya yazmamis; asagida
> `siralama_rmse.csv`'den yeniden uretildi ve oyle isaretlendi.

Sadece rapor. Yorum ve makale metni burada degil.

---

## Faz kunyesi

    faz             : 3 (siralama kararliligi)
    commit          : 9d8ff561242fa51d373f6ecc08d03dc6372b62d1
                      2026-07-30 02:14
                      "Add ranking stability analysis: clustered DM,
                       efect size, Kendall tau"
    etiket          : faz-3 -> c25ea0c (anotasyonlu), commit 9d8ff56
    not yazildi     : 2026-08-08, GERIYE DONUK
    veri surumu     : f722a717bac502c2  (DEGISMEDI)
    push            : EDILDI

Faz 2'den **16 dakika** sonra. Faz 1+2+3 toplam uc commit, hepsi ayni
gun. Karar izi git'ten cikarilamiyor; ayrintisi `faz-notlari/faz-2.md`,
"En onemli yapisal gozlem".

`sonuclar/siralama_rmse.csv` ve `sonuclar/siralama_karsilastirma.csv`,
onlari ureten kodla AYNI commit'tedir - Faz 2'deki ayni bosluk.

---

## Uretilen ciktilar

### `sonuclar/siralama_rmse.csv` - 7 satir

`test_yil` x 3 model, gunduz RMSE (W), uc ondalik.

### `sonuclar/siralama_karsilastirma.csv` - 21 satir

Sema: `test_yil, model_a, model_b, RMSE_a, RMSE_b, RMSE_fark_W,
RMSE_fark_kapasite_yuzde, RMSE_fark_bagil_yuzde, DM, p, anlamli,
fark_GA_alt, fark_GA_ust`

21 = 7 yil x 3 ikili (uc modelin ikili kombinasyonu).

### Uretilip KAYDEDILMEYEN

`pv10/ranking.py:kendall_tau_matrisi` ve `ozet` fonksiyonu
`kendall_tau_ortalama / _min` hesapliyor, `run_siralama.py:52` bunlari
EKRANA basiyor ama **hicbir CSV'ye yazmiyor.** O kosunun ciktisi kayip.
Asagida yeniden hesaplandi.

---

## Kurulum

### Kumelenme birimi  [KAYITLI - Faz 3'un en kritik tasarim karari]

`pv10/ranking.py:110` ve `pv10/evaluate.py:97-102`, ayni commit'te:

> KRITIK: birden fazla konum havuzlandiginda ayni zaman damgasi veri
> setinde birden fazla kez gecer. Newey-West yalnizca zaman icindeki
> otokorelasyonu duzeltir, konumlar arasi eszamanli korelasyonu DEGIL;
> duzeltilmezse varyans kucuk tahmin edilir ve p-degeri yapay olarak
> kuculur. Cozum: kayip farkini once zaman damgasi duzeyinde ortalayip
> testi o seri uzerinde kosmak.

Kumelenme birimi `time_utc`. Alti konum ayni damgayi paylastigi icin
damga duzeyinde kumelenmezse etkin n **alti kat** sisiyor ve her fark
"anlamli" cikiyor. Bu, `dokumanlar/arastirma-baglami.md`'nin "Anlamlilik
mi gurultu mu?" maddesine dogrudan cevaptir ve **koda kosudan once
yazilmistir**.

Faz 4 ayni birimi kullanir (`ozet_sonrasi.py:DM_KUMELENME_BIRIMI`).

### Diebold-Mariano  [KAYITLI]

Kare hata kayip fonksiyonu, Newey-West / Bartlett cekirdegi, `h = 24`
gecikmeye kadar. Pozitif DM, A'nin B'den DAHA KOTU oldugunu gosterir.
Iki tarafli p, normal yaklasimla.

### Etki buyuklugu  [KAYITLI]

`evaluate.etki_buyuklugu` uc olcek dondurur: mutlak W, kapasiteye gore %,
bagil %. Docstring'de gerekce yazili:

> Istatistiksel anlamlilik ile pratik anlamlilik ayni sey degildir:
> yeterince buyuk bir orneklemde 0.8 W'lik bir fark da "anlamli" cikar.
> Bu yuzden her karsilastirmada p-degerinin yaninda etki buyuklugu
> raporlanmalidir.

### Model kumesi ve yillar  [Faz 2 ile AYNI]

`run_siralama.py --modeller` varsayilani `hizli` (uc model),
`--yillar` varsayilani `2017,...,2023`. Gerekceler Faz 2 notundaki gibi:
model alt kumesi icin hesaplama maliyeti KAYITLI, test yili kumesi icin
gerekce KAYITLI DEGIL.

---

## Ham sonuclar

### 1. Yil x model RMSE (W)

| test_yil | Linear Regression | Polynomial Ridge | Hist Gradient Boosting |
|---|---|---|---|
| 2017 | 138,807 | **133,933** | 135,120 |
| 2018 | 142,612 | 139,429 | **138,996** |
| 2019 | 141,344 | **136,503** | 137,169 |
| 2020 | 140,903 | **136,379** | 136,804 |
| 2021 | 141,369 | **136,826** | 137,099 |
| 2022 | 143,950 | **139,756** | 140,223 |
| 2023 | 137,840 | **132,615** | 133,404 |

Kalin = o yilin kazanani. Yedi yilin altisinda Polynomial Ridge, 2018'de
Hist Gradient Boosting.

### 2. Ikili Diebold-Mariano - 21 karsilastirma

Kirilim:

| cift | anlamli (p < 0,05) |
|---|---|
| Linear Regression vs Polynomial Ridge | **7/7** |
| Linear Regression vs Hist Gradient Boosting | **7/7** |
| **Polynomial Ridge vs Hist Gradient Boosting** | **1/7** |

Zayif modelle guclu model arasindaki fark HER YIL tespit ediliyor
(14/14, p'lerin hepsi <= 0,0059); iki guclu model arasindaki fark
**yalnizca bir yil** tespit ediliyor.

Ilk-iki cifti (`{Polynomial Ridge, Hist Gradient Boosting}`) her yil ayni:

| test_yil | fark (W) | DM | p | anlamli | fark %95 GA |
|---|---|---|---|---|---|
| 2017 | -1,1878 | -1,581 | 0,1138 | Hayir | [-2,32; -0,07] |
| 2018 | +0,4330 | +0,844 | 0,3986 | Hayir | [-0,84; 2,06] |
| 2019 | -0,6660 | -1,246 | 0,2127 | Hayir | [-1,44; 0,14] |
| 2020 | -0,4249 | -1,006 | 0,3142 | Hayir | [-1,22; 0,35] |
| 2021 | -0,2727 | -0,784 | 0,4330 | Hayir | [-1,02; 0,42] |
| 2022 | -0,4669 | -1,102 | 0,2705 | Hayir | [-1,20; 0,22] |
| **2023** | **-0,7895** | **-2,074** | **0,038040** | **EVET** | [-1,51; -0,10] |

Ilk-iki farkinin medyani **0,4669 W** = kapasitenin **%0,0467**'si.

**Sinirda bir tutarsizlik:** 2017'de p = 0,1138 (anlamli DEGIL) ama
bootstrap GA'si [-2,32; -0,07] sifiri DISLIYOR. DM'nin Newey-West
standart hatasi ile gun-blogu bootstrap kuyrugu ayni yerde durmuyor.
Ayni tur tutarsizlik Faz 4'te 2021 Polynomial Ridge vs Extra Trees'te
de gorulmustu (p = 0,059786, GA [-1,718271; -0,084734]).

### 3. Kendall tau  [YENIDEN HESAPLANDI - orijinal kosu kaydetmedi]

`siralama_rmse.csv`'den `pv10/ranking.py:kendall_tau_matrisi` ile:

    tau ortalama = 0,8095   min = 0,3333   maks = 1,0000   (21 yil cifti)

Alti yil birbiriyle tau = 1,0000 (ayni siralama: PolyRidge > HGB > LR);
2018 digerlerinin hepsiyle tau = 0,3333 (ilk iki yer degismis).

Yani siralama **yuksek ama tam olmayan** bir kararlilik gosteriyor - ve
tek bozan yil, farkin zaten anlamsiz oldugu yerde bozuyor: 2018'de
HGB-PolyRidge farki 0,4330 W, p = 0,3986.

### 4. Coklu karsilastirma duzeltmesi YAPILMADI

21 testte 0,05 esiginde beklenen tesadufi anlamli sayisi **1,05**.
Gozlenen anlamli sayisi 15'tir, yani toplam icin duzeltme sonucu
degistirmez. Ama **ilk-iki cifti icin gozlenen 1, beklenen 0,35**tir;
o tek satir coklu karsilastirma duzeltmesi olmadan raporlanmaktadir ve
tek basina bir iddiaya dayanak DEGILDIR.

---

## GUFBD baglantisi - onceki calisma tam bu yila dayaniyor

Bu bolum 8 Agustos 2026'da eklendi ve **olcumun bir parcasi degil, onun
yorumlanacagi baglamdir**; makalenin "Related work" ve "Discussion"
bolumlerine girecek.

Onceki calisma (`dokumanlar/arastirma-baglami.md`):

    Baslik : "Veri Sizintisina Duyarli Gun Oncesi Fotovoltaik Guc
             Tahmini: Cografi Olarak Farkli Dort Konumda On Bir Makine
             Ogrenmesi Algoritmasinin Karsilastirmali Degerlendirmesi"
    Tasarim: 4 konum, TEK test yili (Aralik 2023 dokunulmamis test
             seti), genisleyen pencere dogrulama, 24 saat persistence
             referansi, yalniz gunduz degerlendirme
    Sonuc  : Polynomial Ridge secildi; test RMSE 158,92 W, R2 0,553,
             persistence becerisi %14,47
    Durum  : GUFBD'ye 25 Haziran 2026'da gonderildi, HALEN
             DEGERLENDIRMEDE

**Gozlem:** Faz 3'te yedi test yilinin **yalnizca 2023'unde** ilk-iki
farki anlamli cikiyor (p = 0,038040). GUFBD calismasinin tek test yili
da **2023**'tur.

Yani onceki calismanin algoritma secimi, yedi yil icinde farkin
anlamliliga ulastigi TEK yila denk gelmektedir. Kalan alti yilin
herhangi biri tek test yili olarak secilseydi, ayni kurulum ilk iki
algoritmayi birbirinden AYIRT EDEMEYECEKTI (p = 0,1138 ... 0,4330).

**TON - makalede boyle yazilacak:** onceki calismanin sonucu YANLIS
degildir; kendi kurulumu icinde dogru olarak raporlanmistir ve halen
hakem degerlendirmesindedir. Gozlem sudur: **tek yillik bir kurulumda
elde edilen algoritma siralamasi, o yilin bir yan urunu olabilir; bu
makale tam olarak bunu olcmektedir.** Ayni gozlem baskasinin makalesi
uzerinden yapilsaydi saldirgan olurdu; kendi onceki calismamiz uzerinden
yapildiginda ikna edici olur ve makalenin ana tezinin en somut ornegidir.

Faz 4 ayni sonucu bagimsiz olarak dogruluyor: on model x bes yilda
kazanan-ikinci farki **0/5** yilda anlamli
(`sonuclar/doygunluk_ozet_dm_yil.csv`).

Not: Faz 3'un 2023 satiri ile Faz 4'un 2023 satiri **AYRI kod
yollarindan** gecerek ayni sayilari veriyor (p = 0,038040, DM = -2,074,
GA [-1,51; -0,10]) - dokuz alanin dokuzu. Ayrinti `faz-notlari/faz-4.md`,
"Faz 3 ile capraz teyit".

---

## Bilinen kusurlar ve varsayimla gecilen her sey

1. **Bu not geriye donuktur.** On-kayit iddiasi tasimaz.
2. **`siralama_*.csv` kodla ayni commit'te.** Metrik ve test seciminin
   sonuclar gorulmeden sabitlendigine dair dosya duzeyinde kanit yok.
3. **Kendall tau kaybolmus.** Orijinal kosu ekrana basip diske
   yazmamis; buradaki deger yeniden hesaplandi. Yeniden hesap ayni
   girdi ve ayni fonksiyonla yapildigi icin orijinaliyle ayni olmasi
   beklenir, ama ORIJINAL CIKTIYLA KARSILASTIRILAMAZ.
4. **Test yili kumesinin (2017-2023) gerekcesi kayitli degil.**
5. **Uc model.** Faz 4'un genis kosusu on modele cikip ayni yone isaret
   etti, ama Faz 3'un kendi tablosu uc modelliktir; "ilk iki ayirt
   edilemiyor" ifadesi bu uc modelin ilk ikisi icindir.
6. **Coklu karsilastirma duzeltmesi yok** (yukariya bak).
7. **DM ile bootstrap GA 2017'de ayrisiyor** (p = 0,1138 ama GA sifiri
   disliyor). Iki yontem farkli varsayimlar altinda calisiyor; hangisinin
   dogru oldugu Faz 3'te KARARLASTIRILMADI. Faz 4'te ayni durum
   yeniden goruldu ve orada da karara baglanmadi - her iki sayi da
   raporlaniyor.
8. **`anlamli` sutunu 0,05 esigine gomulu**; esik `ranking.py` icinde
   sabit ve config'de degil.
9. Ortam: pyarrow 25.0.0 (Faz 2 ile ayni gun).

---

## Calistirma

    python run_siralama.py
    python run_siralama.py --yillar 2021,2022,2023
    python run_siralama.py --ozet

Kendall tau'yu yeniden uretmek icin (CSV'ye yazilmiyor):

    python -c "import pandas as pd,sys; sys.path.insert(0,'.'); \
      from pv10.ranking import kendall_tau_matrisi; \
      r=pd.read_csv('sonuclar/siralama_rmse.csv').set_index('test_yil'); \
      print(kendall_tau_matrisi(r.rank(axis=1)))"
