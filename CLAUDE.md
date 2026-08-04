# CLAUDE.md

**Her oturumda once `dokumanlar/arastirma-baglami.md`'yi oku.** Makalenin
savunulabilir kalmasi gereken iddialari ve hakemin vuracagi yerler orada.

Bu dosyayı her oturum başında oku. Proje bağlamı ve uyulması zorunlu kurallar burada.

## Proje

On yıllık (2014-2023), altı konumlu PV güç tahmini çalışması. Amaç bir tahmin
modeli üretmek DEGIL; yaygın degerlendirme hatalarinin raporlanan basarimi ne
kadar sistirdigini olcmek ve tek yillik kiyaslama calismalarinin algoritma
siralamasi iddialarinin gecersizligini gostermek.

Hedef dergi: Solar Energy (APC yok) -> Energy Reports -> Energies.
Daha once ayni yazarlarin tek yillik, dort konumlu versiyonu GUFBD'ye gonderildi
ve halen degerlendirmede. Yeni makale ona atif verecek, ortusme %25'in altinda
tutulacak.

## Durum

- Faz 1 (veri) TAMAM. 525.888 satir, 6 konum, PVGIS-SARAH3.
- Faz 2 (sizinti ablasyonu) TAMAM. `sonuclar/ablasyon.csv`
- Faz 3 (siralama kararliligi) TAMAM. `sonuclar/siralama_*.csv`
- Faz 4 (veri hacmi doygunlugu) TAMAM.
  - K = 1/2/3/5/tum yillik egitim. 10 yillik pencere MUMKUN DEGIL: test yili
    disari cikinca en fazla 9 yil kalir.
  - Iki kol: `kaydirmali` (hacim + guncellik ic ice) ve `altornekleme`
    (gun blogu, konuma gore tabakali, 3 tohum - saf hacim etkisi).
    Makalenin ana orani ALTORNEKLEME kolundan gelir.
  - Invaryant kapisi: 5 invaryant / 18 kontrol, hepsi GECTI (~1,2 dk).
  - Ana izgara TAMAM: 255/255 hucre, 11,0 dk, hata yok. `sonuclar/doygunluk.csv`
  - Genis kosu TAMAM: 50/50 hucre, 81,2 dk, K=tum x 2019-2023 x 10 model
    (SVR haric). `sonuclar/doygunluk_genis.csv`
  - Esli kumelenmis DM (egri uclari) TAMAM: 45 karsilastirma, 35 anlamli.
    Kirilim model bagimli - LR 5/15, PolyRidge 15/15, HGB 15/15.
    `sonuclar/doygunluk_ozet_dm.csv`
  - 2022 dogrulama kosusu TAMAM: 10 hucre, 19,6 dk, tahmin kaydiyla.
    Genis kosuyla 99/100 alan birebir (tek istisna asagida).
  - 2022 dogrulama kosusu TAMAM: 10 hucre, 19,6 dk, tahmin kaydiyla.
  - Kalan dort yilin kosusu TAMAM: 40 hucre, 96,5 dk, tahmin kaydiyla,
    K=tum x 2019/2020/2021/2023 x 10 model. `sonuclar/doygunluk_dm_kalan.csv`
    Genis kosuyla 510/520 alan birebir; farkli cikan 10 alanin hepsi 1-2 ULP
    ve yalnizca Random Forest ile Extra Trees'te (asagiya bak).
  - **Yil ici DM (bes yil, ilk uc model) TAMAM. 15 karsilastirma, 1 anlamli.**
    KAZANAN-IKINCI FARKI HICBIR YILDA ANLAMLI DEGIL - 0/5:
    2019 p=0,155011 | 2020 p=0,742136 | 2021 p=0,432974 |
    2022 p=0,413134 | 2023 p=0,114696. Besinin de esli GA'si sifiri iceriyor.
    Yani on modelli, bes yillik kurulumda kazanan iki kez degisiyor
    (Polynomial Ridge x4, Neural Network x1) ama DEGISIMIN KENDISI GURULTU:
    hicbir yilda kazanani ikinciden ayirt edemiyoruz.
    Tek anlamli satir 2023 Polynomial Ridge vs Hist Gradient Boosting
    (p=0,038040) - birinci-UCUNCU cifti, kazanan-ikinci degil; ayrica 15
    testte 0,05 esiginde beklenen tesadufi anlamli sayisi 0,75 ve coklu
    karsilastirma duzeltmesi YAPILMADI. Bu tek satira iddia yaslanmaz.
    Sinirda bir tutarsizlik: 2021 Polynomial Ridge vs Extra Trees p=0,059786
    (anlamli degil) ama esli GA [-1,718271; -0,084734] sifiri DISLIYOR;
    DM'nin Newey-West standart hatasi ile blok bootstrap kuyrugu ayni yerde
    durmuyor. Kazanan-ikinci ciftlerinin hicbiri etkilenmiyor.
    `sonuclar/doygunluk_ozet_dm_yil.csv`
- **Random Forest / Extra Trees nondeterminizmi - OLCULDU, KAPANDI.**
  Sapma yalnizca Extra Trees'te degil, Random Forest'ta da var. Olcum:
  ayni hucre (kaydirmali K=tum 2020) uc modelde iki duzeyde tekrarlandi -
  A: ayni surecte pes pese iki kosu, B: ayri iki surecte. **A duzeyi kesti,
  B'ye gerek kalmadi:** RF ve ET'de dort kosunun dordu de FARKLI tahmin
  hash'i verdi. Sebep surec ici paralel hesap (agac toplama sirasi),
  pyarrow DEGIL. Kontrol tanigi: Neural Network dort kosuda da AYNI hash
  (`52016056fdc69ba8...`) - duzenek yapay fark uretmiyor, farkli hash'ler
  gercek. `y` ve `persistence` on iki satirin hepsinde tek deger, yani fark
  modelde, veride degil.
  Sapma tahmin vektorunde HER ZAMAN var, metrige ancak BAZEN yansiyor:
  dort RF kosusunun RMSE'si de 138,71018130192496 ciktigi halde ayni
  hucrenin izgaradaki degeri 1 ULP asagidaydi. 40 hucrede yalnizca 10 alanin
  oynamasinin sebebi bu - hucre sayisi degil, yuvarlamanin nereye dustugu.
  Etkilenen alanlar 1-2 ULP (bagil ~2e-16); `egitim_n`, `n`, `isinma`,
  `egitim_basla`, `RMSE_persistence` her hucrede TAM ESIT.
  Raporlanan hicbir sayi etkilenmiyor. Yalniz 2021'in ucuncu modeli Extra
  Trees oldugu icin o DM satirinin son basamagi baska kosuda birebir
  tekrarlanmayabilir; kazanan-ikinci ciftleri etkilenmiyor.
  **Dogrulama kosusu TAMAM (4 Agustos 2026):** olcum betigi REPODAKI haliyle
  iki surec sirayla kosuldu, cikti ayri dosyaya
  (`sonuclar/nondeterminizm_olcum_dogrulama.csv`). Karar birebir tekrarlandi -
  RF ve ET'de A duzeyi kesti, NN dort kosuda tek hash. Hash'ler tekrarlanmadi
  (RF/ET'de iki olcumun 8 kosusu 8 farkli hash, ortak sifir) - olculen sey
  zaten bu. Kontrol tanigi NN ayni hash'i (`52016056fdc69ba8...`) iki olcumda,
  ayri gunlerde, dort surecte verdi.
- Faz 4 notu TAMAM: `faz-notlari/faz-4.md` bastan yazildi (eski surum izgara
  kosulmadan onceydi ve "uretilen deney sonucu YOK" diyordu).
- Kalan:
  1. `faz-2` / `faz-3` / `faz-4` anotasyonlu etiketler (repoda hic etiket yok).
  2. Push (bugune kadarki commit'lerin hicbiri push EDILMEDI).
  3. `arac/dm_yil.py` repodaki haliyle hic kosulmadi - tek acik
     kalicilastirma boslugu; ~20-25 dk. Faz notunda kusur 2 olarak yazili.
  Sonra DKASC (opsiyonel) veya dogrudan yazim.

## Degismez kurallar

1. **Veri dondurulmustur.** sha256 = `f722a717bac502c2`. Veriyi yeniden
   indirme, konum ekleme veya cikarma - butun deney sonuclari bu surume
   bagli. Degistirmek gerekiyorsa once bana sor.

2. **Hiperparametreleri ASLA test setine gore ayarlama.** Onceden sabitlenmis
   olmalari kasitli bir metodolojik tercih. "Sonuclari iyilestirdim" diye
   ayarlarsan makalenin butun iddiasi coker.

3. **Veri commit edilmez.** `ham/`, `veri/`, `sonuclar/tahminler/` .gitignore'da.
   `sonuclar/*.csv` commit EDILIR.

4. **Oznitelik tanimlari GUFBD makalesiyle birebir ayni kalmali.** Cekirdek set
   sabit; yeni oznitelik eklenirse ayri bir ek deney olarak raporlanir, ana
   analize karistirilmaz.

5. **Sessiz basarisizlik yasak.** Eksik sutun, eksik degisken, beklenmeyen
   satir sayisi -> acik hata firlat. Bu projede uc hata tam olarak sessiz
   atlama yuzunden gunlerce fark edilmedi (asagiya bak).

## Daha once yakalanan hatalar - tekrar uretme

- **Gunes geometrisi:** PVGIS zaman damgasi uydu gozlem dakikasini tasir
  (`:09`, `:10`). Saat basina yuvarlanmis damgayla hesap yapmak ~1.5 derece
  sistematik sapma verir. Geometri `time_gozlem` sutunundan hesaplanir.

- **Gece satirlari:** berrak-gokyuzu orani gece tanim geregi eksiktir. Onu
  zorunlu dropna listesine koymak butun gece gozlemlerini siler. Egitim gece
  saatlerini ICERIR; gunduz filtresi yalnizca DEGERLENDIRMEDE uygulanir.

- **`G_i` kaybi:** PVGIS `components=1` ile toplam `G(i)` yerine bilesenleri
  dondurur. Pipeline `Gb_i + Gd_i + Gr_i` toplamindan `G_i`'yi geri kurar.
  `G_i_lag24` permutasyon oneminde en guclu oznitelik - kaybolursa fark et.

- **Pencere sinirinda oznitelik isinmasi:** oznitelikler once tum veride
  uretilip sonra yila gore dilimlenirse, "1 yil veriyle egitildi" denen model
  onceki yillarin yuvarlanan istatistiklerini tasir. Isinma (konum basina 191
  satir = 24 shift + 168 roll168 - 1) veri kumesinin basinda degil PENCERENIN
  basinda tuketilmeli. Kontrol: K=1 @ 2023 icin `egitim_n` = **51.414**
  dogrudur; **52.560** cikiyorsa sinir siziyor. Invaryant 3 bunu olcer.

- **Yanlis turden kiyas:** `hacim_orani` tablosu hacim SPAN'ini (K=1 -> K=tum)
  Faz 3'un algoritma MEDYAN IKILI farkina (0,4669 W) bolup "4,72 kat" uretiyordu.
  Ikisi ayni turden istatistik degil - biri bir aralik, digeri ikili farklarin
  medyani. Span span ile, medyan medyan ile kiyaslanir. Ayni turden bakildiginda
  algoritma span'i 3,65-4,67 W, hacim span'i 0,25-6,74 W: ayni mertebede.
  Tablo kayit icin yerinde birakildi, ana iddia
  `sonuclar/doygunluk_ozet_duzeltilmis.csv`'den okunur.

- **Havuzlanmis ortalama etkiyi gizler:** saf hacim etkisinin 2,204968 W'lik
  ortalamasi, Linear Regression'in 0,209944 W'siyle Hist Gradient Boosting'in
  4,493244 W'sini ayni potaya koyuyor. LR'de etki 15 karsilastirmanin yalnizca
  5'inde anlamli, IKI hucrede isaret ters (2019 tohum 11 ve 33, ikisi de
  anlamsiz) ve 10 hucrede esli GA sifiri iceriyor; HGB'de 15/15 anlamli.
  Etki MODEL BAGIMLI, tek sayiya indirgenmez.

- **Marjinal GA cakismasi "fark yok" demek DEGILDIR:** egrinin iki ucu AYNI test
  setinde degerlendirildigi icin hatalar korelasyonlu; esli olmayan kiyas
  muhafazakardir. Marjinal GA'larda 45/45 cakisiyordu, esli kumelenmis DM'de
  35/45 anlamli cikti. Cakismama farki ispatlar, cakisma farksizligi ispatlamaz.
  Kumelenme birimi `time_utc` - Faz 3 ile ayni (`ranking.py:110`).

- **Invaryantin uretim yerine kendi kopyasini dogrulamasi:** bolme mantigi
  invaryanta kopyalanirsa test tautolojiye doner - kopya dogru oldugu surece
  uretim yanlis olsa bile kapi yesil yanar. Faz 4'te invaryant 5 tam bunu
  yapiyordu; karsilastirmanin iki tarafi da ayni cagriydi ve `farkli_oznitelik
  = 0` sonucu determinizmden geliyordu, olcumden degil. Kural: invaryant
  URETIM fonksiyonunu cagirir (`egitim_test_bolme`, `hucre_kos`) ve kasten
  yanlis bir referansla NEGATIF KONTROLU olur; yanlisi yakalayamiyorsa
  invaryant islevsizdir ve kapi kirmizi yanmalidir.

## Hesaplama gercekligi

350-525 bin satir x 29 oznitelikte:
- Linear / Polynomial Ridge / Hist Gradient Boosting -> saniyeler, varsayilan bunlar
- Random Forest, Extra Trees (400 agac), MLP -> dakikalar, cok RAM
- SVR -> O(n^2) kernel, pratikte imkansiz, calistirmayi deneme

Uzun izgaralar kaldigi yerden devam edebilir olmali; her hucre aninda diske
yazilir.

## Kod

Turkce degisken ve fonksiyon adlari, Turkce yorumlar. Modul basina tek
sorumluluk. Sabitler `pv10/config.py` disinda tanimlanmaz.

```
pvgis_pipeline.py    veri indirme, dogrulama, birlestirme
run_smoke.py         tek bolmeli akil saglig testi
run_ablasyon.py      sizinti ablasyon izgarasi
run_siralama.py      siralama kararliligi
run_doygunluk.py     veri hacmi doygunlugu (Faz 4) + invaryant kapisi + ozet
pv10/
  config.py features.py models.py evaluate.py experiment.py ranking.py
  doygunluk.py       pencere aritmetigi, oznitelik onbellegi, hucre, izgara
  ornekleme.py       gun blogu, konuma gore tabakali altornekleme
  dogrulama.py       deney invaryantlari (5 adet) - VERI degil KURGU dogrular
  ozet.py            Faz 4 ozet tablolari; sonuclar gorulmeden yazildi
  ozet_sonrasi.py    sonuclar GORULDUKTEN sonra eklenen tablolar
arac/
  nondeterminizm.py        teshis: ayni hucre x tekrar x surec, tahmin sha256
  nondeterminizm_karar.py  yorum kurali (sonuc gorulmeden) + karar tablosu
```

`arac/` DENEY DEGIL TESHIS icindir; makalenin hicbir sayisini uretmez ve
ana akistan cagrilmaz. `pv10/` ile `run_*.py` yalnizca deney kodu kalsin
diye ayri tutuldu - faz notunda hangi dosyanin makale sayisi urettigi
bulanmasin.

`ozet.py` ile `ozet_sonrasi.py` ayri tutulur; sebep kayit duzenidir. `ozet.py`
izgara kosulmadan once yazildi ve o gunden beri dokunulmadi - bunu
`git log -- pv10/ozet.py` dosya duzeyinde gosteriyor. Metrik seciminin post-hoc
olmadigi iddiasi buna dayaniyor. Sonradan eklenen tablo AYRI dosyaya gider,
kunyede `[sonradan eklendi]` diye isaretlenir.

Bolme mantigi TEK yerde: `pv10/doygunluk.py:egitim_test_bolme`. Hem
`hucre_kos` hem `dogrulama.py` oradan gecer - kopyalama yok.

## Calistirma

Python komutlarini HER ZAMAN .venv\Scripts\python.exe ile calistir.
Sistem Python'unda pandas ve scikit-learn kurulu degil.

**pyarrow 22.0.0 kullaniliyor (25.0.0 DEGIL).** 3 Agustos 2026 02:06'da Windows
Smart App Control 25.0.0'in `arrow.dll`'ini bloklamaya basladi (CodeIntegrity
3077/3033, `VerifiedAndReputablePolicyState=1`); parquet okunamadigi icin hicbir
kosu baslamiyordu. 22.0.0'a indirildi, `--only-binary=:all:` ile, kaynaktan
derleme yok. SAC ayarina DOKUNULMADI - kapatmak geri alinamaz bir islem.
Veri hash'i degismedi (`f722a717bac502c2`), invaryant kapisi 22.0.0 ile 18/18
gecti ve invaryant 1-2'nin ablasyon referanslari son basamagina kadar ayni
cikti (6,050675e-13 ve 7,797529e-12 bagil fark, ikisi de surum oncesiyle
birebir). Ana izgara, genis kosu ve 2022 kosusu 25.0.0 ile uretildi; sonraki
kosular 22.0.0 ile.

```
python pvgis_pipeline.py duzenle ham/
python run_smoke.py
python run_ablasyon.py --tahmin      # once maliyet
python run_ablasyon.py
python run_siralama.py

python run_doygunluk.py --dogrula    # 5 invaryant / 18 kontrol - ONCE BU
python run_doygunluk.py --tahmin     # hucre maliyeti, kosmadan
python run_doygunluk.py              # ana izgara, sonunda ozet otomatik
python run_doygunluk.py --ozet       # mevcut CSV'lerden ozet, izgara kosmadan
```

Ana izgara disinda kosu yaparken uc bayrak:

```
--pencere tum        # pencere listesini kisitla; varsayilan HEPSI (1,2,3,5,tum)
--etiket genis       # ayri log dosyasi (doygunluk_<etiket>.csv); ozet uretilmez
--tahmin-kaydet      # her hucrenin gunduz tahmin vektorunu diske yaz
```

`--etiket` VERILMEZSE kosu ana izgara loguna yazar ve ozet tablolari kirlenir -
egri, ana oran, tohum yayilimi ve model x pencere tablolari mevcut modeller
uzerinde ortalama aliyor. Farkli model kumesi veya tek pencere kosarken
`--etiket` ZORUNLU sayilmali.

Teshis (deney degil, kok dizinden `-m` ile; iki surec SIRAYLA kosulur):

```
python -m arac.nondeterminizm --surec p1
python -m arac.nondeterminizm --surec p2
python -m arac.nondeterminizm_karar     # sonuclar/nondeterminizm_olcum.csv

python -m arac.dm_yil                   # yil ici DM, bes yil
python -m arac.regresyon_kiyas          # iki izgara logu, toleranssiz kiyas
```

`nondeterminizm.py` CSV'ye EKLER, uzerine yazmaz - B duzeyi ancak boyle
olusur. Onceki bir olcumu korumak icin `--cikti <yol>` ver; karar tarafinda
karsiligi `--olcum <yol>`.

`--tahmin-kaydet` olmadan esli DM SONRADAN kosulamaz; tahmin vektoru
uretilir ama diske yazilmaz. Tahminler `sonuclar/tahminler/doygunluk/<etiket>/`
altina parquet olarak gider, `.gitignore` kapsamindadir.

Invaryant kapisi gecmeden ana izgara kosulmaz. Izgara kaldigi yerden devam
eder; basarisiz hucre `durum="hata"` ile diske yazilir, sessizce atlanmaz.

## Git

- Her mantiksal birim bittiginde commit at; oturum sonunda toplu degil.
- **`git add .` yok.** Acik dosya yolu ver, oncesinde `git status --short`
  goster.
- Veri repoya girmez. Commit oncesi `.gitignore` kapsamini ve 1 MB ustu dosya
  olmadigini dogrula.
- `sonuclar/` altindaki CSV'ler ve `faz-notlari/` REPOYA GIRER.
- Commit mesaji: 72 karakterlik ozet, bos satir, sonra **ne + neden**. Kosu
  commit'lerinde hucre sayisi, duvar saati ve kapi sonuclari yazilir.
- Faz bitince anotasyonlu etiket (`faz-4`), mesajinda temel sayilar.
- **Gecmisi yeniden yazma:** force push, rebase, amend yok.
- Anahtar, token, yerel mutlak yol commit etme.
- **Push'u ben soylemeden yapma.**

## Devir notu

Oturum sonunda `faz-notlari/<faz>.md` uret. Sadece rapor, yorum yok. Sayilar
tam hassasiyette, kod govdesi yok, yalniz imza. Icerik:

- faz + commit hash + agac durumu
- degisen dosyalar
- yeni fonksiyon imzalari
- config sabitleri ve degerleri
- uretilen cikti dosyalari ve semalari
- kapi/invaryant sonuclari: beklenen, gozlenen, fark
- kosu istatistikleri
- ham ozet tablolar
- alinan kararlar ve gerekceleri
- bilinen kusurlar ve varsayimla gecilen her sey

## Beklentim

Kod yazmadan once ne yapacagini soyle ve onay bekle. Bir sey olcmeden
"iyilestirdim" deme - once kosur, sayilari goster. Emin olmadigin yerde
tahmin yurutme, sor.
