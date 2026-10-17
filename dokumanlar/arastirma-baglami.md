# Arastirma baglami

Her oturumda, kod okumadan once bu dosya okunur.

## Bu repo nedir

Bir dergi makalesinin deney altyapisi. Kod urun degil, **kanit**. Buradaki
her sayi makaleye girecek ve bir hakem tarafindan sorgulanacak. "Calisiyor"
yeterli olcut degildir; "savunulabilir" olcuttur.

## Onceki calisma

**Baslik:** "Veri Sizintisina Duyarli Gun Oncesi Fotovoltaik Guc Tahmini:
Cografi Olarak Farkli Dort Konumda On Bir Makine Ogrenmesi Algoritmasinin
Karsilastirmali Degerlendirmesi"

**Tasarim:** 4 konum, 11 algoritma, **tek test yili** - Aralik 2023
dokunulmamis test seti, genisleyen pencere dogrulama, 24 saat persistence
referansi, yalniz gunduz degerlendirme.

**Sonuc:** Polynomial Ridge secildi. Test RMSE **158,92 W**, R2 **0,553**,
persistence becerisi **%14,47**.

**Durum:** GUFBD'ye **25 Haziran 2026**'da gonderildi, **12 Ekim 2026**'da KABUL EDILDI, yayin sirasinda.

### Kritik baglanti - bu makalenin en somut ornegi

Faz 3'te yedi test yili (2017-2023) x 3 model kosuldu. Ilk-iki cifti
(Polynomial Ridge vs Hist Gradient Boosting) **yedi yilin yalnizca
2023'unde** anlamli fark veriyor (p = 0,038040); kalan alti yilda
p = 0,1138 / 0,3986 / 0,2127 / 0,3142 / 0,4330 / 0,2705.

**Onceki calismanin tek test yili da 2023'tur.**

Yani onceki calismanin algoritma secimi, yedi yil icinde farkin
anlamliliga ulastigi TEK yila denk gelmektedir. Kalan alti yilin herhangi
biri secilseydi ayni kurulum ilk iki algoritmayi ayirt EDEMEZDI.

**TON - degismez:** "onceki calismamiz yanlisti" DEGIL. Onceki calisma
kendi kurulumu icinde dogru raporlanmistir ve 12 Ekim 2026'da kabul edilmistir (yayin sirasinda).
Soylenecek olan sudur: **tek yillik bir kurulumda elde edilen algoritma
siralamasi o yilin bir yan urunu olabilir; bu makale tam olarak bunu
olcmektedir.** Ayni gozlem baskasinin makalesi uzerinden yapilsa saldirgan
olurdu; kendi onceki calismamiz uzerinden yapildiginda ikna edici olur.

Faz 4 ayni sonucu bagimsiz olarak dogruluyor: on model x bes yilda
kazanan-ikinci farki 0/5 anlamli (`sonuclar/doygunluk_ozet_dm_yil.csv`).

### Kapsam farki

Bu repo onceki calismanin genisletilmis halini uretiyor:

| | onceki | bu repo |
|---|---|---|
| konum | 4 | 6 |
| donem | tek yil | 2014-2023 |
| test yili | 2023 | 2017-2023 |

Veri kaynagi PVGIS-SARAH3, 1 kWp c-Si. Veri **dondurulmustur**: 525.888 satir,
sha256 `f722a717bac502c2`.

Hedef dergiler, sirayla: Solar Energy, Energy Reports, Energies.

## Arastirma sorusu

> Gun oncesi PV tahmininde raporlanan performans farklarinin ne kadari
> metodolojik tercihlerden -- sizinti, bolme stratejisi, test yili secimi,
> egitim verisi hacmi -- ne kadari algoritma seciminden geliyor?

Soru **yonsuzdur**. Hicbir fazin beklenen bir yonu yoktur. Sonucun hangi
tarafa ciktigi **bulgudur, hedef degildir**. Metodolojik etkinin buyuk
cikmasi da kucuk cikmasi da esit derecede raporlanabilir sonuclardir.

## Savunulabilir kalmasi gereken iddialar

Bunlar makalenin tasidigi yuktur. Bir tasarim karari bunlardan birini
zayiflatiyorsa, kosu baslamadan once soylenir.

1. **Zamansal ayrim.** Her hucrede egitim verisi test doneminden kesinlikle
   once bitiyor -- oznitelik hesabi dahil. Gecikmeli ve yuvarlanan
   ozniteliklerin isinmasi da bu sinira tabidir.

2. **Tek kod yolu.** Fazlar arasi sayilar ayni kod yolundan geliyor. Bir fazin
   sonucu digerinin kurulumuyla karsilastirilabilir olmali.

3. **Olculmus gurultu tabani.** Raporlanan her fark, olculmus bir gurultu
   tabaninin uzerinde. Fark ile gurultu ayni mertebedeyse bu acikca yazilir.

4. **Kayitli gerekce.** Her tasarim karari gerekcesiyle birlikte kayitli.
   Kosu sonrasi rasyonalizasyon degil.

5. **On-kayitli olcum.** Ozet ve metrik secimi sonuclar gorulmeden
   sabitlenmis.

## Hakemin vuracagi yerler

Bunlar tahmin degil, beklenti. Her biri icin cevabin kodda ve faz notlarinda
hazir olmasi gerekir.

- **Anlamlilik mi gurultu mu?** Yeterince buyuk orneklemde her fark "anlamli"
  cikar. p-degeri tek basina asla yeterli degil.
- **Test yili ve model alt kumesi neye gore secildi?** Secim olcut kosu
  oncesinde sabitlenmis olmali; hesaplama maliyeti bir gerekcedir ama
  yazilmasi sarttir.
- **Sizintiyi olcen kurulumun kendisine sizinti kacmadigini nasil biliyoruz?**
  En sert soru bu. Cevap invaryantlarda: kurulumun kendi dogrulugu, sonuca
  bakmadan, ayrica test edilmis olmali.
- **Tek sentetik kaynaga baglilik.** Butun veri PVGIS'ten. Gercek olcum
  verisiyle (DKASC) replikasyon opsiyonel ama sorulacak.
- **Tekrar uretilebilirlik.** Repo gonderimde acilacak ve Zenodo DOI alacak.
  Tohum, surum, thread sayisi, ortam -- hepsi kayitli olmali.

## Asistanin rolu

Bir tasarim karari yukaridaki iddialardan birini zayiflatiyorsa, **kosmadan
once** soyle. Sonucun beklentiye uyup uymamasi senin isin degil.
