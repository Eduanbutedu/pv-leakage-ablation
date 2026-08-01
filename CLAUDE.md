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
- Faz 4 (veri hacmi doygunlugu) ALTYAPI HAZIR, KOSU BEKLIYOR.
  - K = 1/2/3/5/tum yillik egitim. 10 yillik pencere MUMKUN DEGIL: test yili
    disari cikinca en fazla 9 yil kalir.
  - Iki kol: `kaydirmali` (hacim + guncellik ic ice) ve `altornekleme`
    (gun blogu, konuma gore tabakali, 3 tohum - saf hacim etkisi).
    Makalenin ana orani ALTORNEKLEME kolundan gelir.
  - Invaryant kapisi: 5 invaryant / 18 kontrol, hepsi GECTI (~1,2 dk).
  - Ozet fonksiyonlari sonuclar GORULMEDEN yazildi (`pv10/ozet.py`) ve
    runner'a baglandi; ciktilar `sonuclar/doygunluk_ozet_*.csv`.
  - Ana izgara: 255 hucre (~9 dk tahmin), HENUZ KOSULMADI.
  - Genis kosu: 50 hucre (K=tum, 2019-2023, SVR haric 10 model), OLCULMEDI.
- Opsiyonel: DKASC gercek olcum verisiyle replikasyon.
- Sonra: yazim.

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
```

Bolme mantigi TEK yerde: `pv10/doygunluk.py:egitim_test_bolme`. Hem
`hucre_kos` hem `dogrulama.py` oradan gecer - kopyalama yok.

## Calistirma

Python komutlarini HER ZAMAN .venv\Scripts\python.exe ile calistir.
Sistem Python'unda pandas ve scikit-learn kurulu degil.

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
