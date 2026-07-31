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
- Faz 4 (veri hacmi doygunlugu) YAPILACAK: 1/2/3/5/10 yillik egitimle ogrenme egrisi.
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
pv10/
  config.py features.py models.py evaluate.py experiment.py ranking.py
```

## Calistirma

Python komutlarini HER ZAMAN .venv\Scripts\python.exe ile calistir.
Sistem Python'unda pandas ve scikit-learn kurulu degil.

```
python pvgis_pipeline.py duzenle ham/
python run_smoke.py
python run_ablasyon.py --tahmin      # once maliyet
python run_ablasyon.py
python run_siralama.py
```

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
