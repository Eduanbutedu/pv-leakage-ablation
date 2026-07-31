# Arastirma baglami

Her oturumda, kod okumadan once bu dosya okunur.

## Bu repo nedir

Bir dergi makalesinin deney altyapisi. Kod urun degil, **kanit**. Buradaki
her sayi makaleye girecek ve bir hakem tarafindan sorgulanacak. "Calisiyor"
yeterli olcut degildir; "savunulabilir" olcuttur.

## Onceki calisma

4 konum, 11 algoritma, tek test yili (2023). GUFBD'ye **25 Haziran 2026**'da
gonderildi, halen degerlendirmede. Bu repo onun genisletilmis halini uretiyor:

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
