#!/usr/bin/env python3
"""
PVGIS veri hatti: indir -> dogrula -> duzenle
=============================================
Dun gonderdigim pvgis_indir.py'nin yerini alir. Uc isi tek dosyada yapar:

  1) indir    : PVGIS API'sinden her konum icin 2014-2023 saatlik veri
  2) dogrula  : yil araligi / satir sayisi / bosluk kontrolu (2005 hatasina karsi)
  3) duzenle  : hepsini tek bir temiz tabloya birlestirir, parquet olarak kaydeder

Konfigurasyon mevcut makalenizle birebir ayni:
  PVGIS-SARAH3, 1 kWp c-Si, 30 deg egim, 0 deg azimut (guney), %14 sistem kaybi

Kurulum:
    pip install requests pandas pyarrow

Kullanim:
    python pvgis_pipeline.py hepsi          # indir + dogrula + duzenle
    python pvgis_pipeline.py indir
    python pvgis_pipeline.py dogrula ham/
    python pvgis_pipeline.py duzenle ham/
"""

from __future__ import annotations

import argparse
import hashlib
import io
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

API = "https://re.jrc.ec.europa.eu/api/v5_3/seriescalc"
# PVGIS veri satiri: 20140101:0009,...
ZAMAN_SATIRI = re.compile(r"^\d{8}:\d{4},")
BASLANGIC_YIL, BITIS_YIL = 2014, 2023

# ad: (enlem, boylam, standart UTC ofseti saat)
# Ofset yaz saati UYGULANMADAN verilir - gunes calismalarinda dogru olan budur,
# cunku DST yapay bir 1 saatlik siçrama yaratip mevsimsel oruntuyu bozar.
KONUMLAR = {
    "adana":    (36.817794,  35.674212, +3),
    "konya":    (37.428100,  32.536400, +3),
    "braila":   (45.324110,  27.835540, +2),
    "portimao": (37.193283,  -8.508026,  0),
    # --- GENISLETME ---------------------------------------------------------
    # Kapsami 6-8 konuma cikarmak icin istediklerinizin basindaki # isaretini
    # kaldirin, sonra SADECE yenilerini indirin:
    #     python pvgis_pipeline.py indir --sadece leipzig,ouarzazate
    #
    # Onerilen ikili (iki eksik iklim ucunu kapatir):
    "leipzig":    (51.3397,  12.3731, +1),   # bulutlu kita ikliminde yuksek enlem
    "ouarzazate": (30.9335,  -6.9370, +1),   # yari col, cok yuksek isinim
    #
    # Sekize cikarmak isterseniz:
    # "athina":     (37.9838,  23.7275, +2),   # Adana/Portimao ile ayni enlemde kontrol
    # "stockholm":  (59.3293,  18.0686, +1),   # asiri mevsimsellik
    #
    # NOT: SARAH3 uydu kapsami ~65 derece enlemde biter ve yuksek enlemlerde
    # gorus acisi bozuldugu icin guvenilirlik duser. Kapsam disi bir konum
    # isterseniz PVGIS istegi hata dondurur - sessizce ERA5'e dusmez, yani
    # veritabani tutarliligi korunur.
}

SABIT_PARAM = {
    "raddatabase": "PVGIS-SARAH3",
    "pvcalculation": 1,
    "peakpower": 1.0,
    "loss": 14.0,
    "pvtechchoice": "crystSi",
    "mountingplace": "free",
    "angle": 30,      # egim
    "aspect": 0,      # 0 = guney
    "trackingtype": 0,
    "components": 1,
    "usehorizon": 1,
    "outputformat": "csv",
    "browser": 0,
}


# --------------------------------------------------------------------------- #
# yardimcilar
# --------------------------------------------------------------------------- #
def artik_mi(y: int) -> bool:
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def beklenen_satir(bas: int, bit: int) -> int:
    return sum(8784 if artik_mi(y) else 8760 for y in range(bas, bit + 1))


def cikar_veri(ham_metin: str) -> pd.DataFrame:
    """PVGIS CSV'sinden metadata ve dipnot satirlarini ayiklar.

    Windows'ta dosya yazarken satir sonlari iki kez cevrilebildigi icin
    (\r\n -> \r\r\n) geri okundugunda araya bos satirlar girer. Bu yuzden
    once bos satirlar atilir, veri satirlari da zaman damgasi kalibiyla
    secilir - siraya/indekse guvenilmez.
    """
    satirlar = [s.strip() for s in ham_metin.splitlines()]
    satirlar = [s for s in satirlar if s]
    bas = next((i for i, s in enumerate(satirlar) if s.startswith("time,")), None)
    if bas is None:
        raise ValueError("'time,' basligi bulunamadi - dosya PVGIS ciktisi degil")

    veri = [s for s in satirlar[bas + 1:] if ZAMAN_SATIRI.match(s)]
    if not veri:
        raise ValueError("basliktan sonra veri satiri bulunamadi")

    df = pd.read_csv(io.StringIO(satirlar[bas] + "\n" + "\n".join(veri)))
    df["time"] = pd.to_datetime(df["time"], format="%Y%m%d:%H%M")
    return df


def ham_oku(yol: Path) -> str:
    """csv veya (tek sutuna yapistirilmis) xlsx okur."""
    if yol.suffix.lower() in (".xlsx", ".xls"):
        ham = pd.read_excel(yol, header=None)
        return "\n".join(str(v) for v in ham.iloc[:, 0].tolist())
    return yol.read_text(encoding="utf-8", errors="replace")


# --------------------------------------------------------------------------- #
# 1) indir
# --------------------------------------------------------------------------- #
def indir(ad, lat, lon, cikti_dir: Path, deneme=3) -> bool:
    param = dict(SABIT_PARAM, lat=lat, lon=lon,
                 startyear=BASLANGIC_YIL, endyear=BITIS_YIL)
    print(f"\n{ad} ({lat}, {lon}) indiriliyor...")
    for k in range(1, deneme + 1):
        try:
            r = requests.get(API, params=param, timeout=300)
            if r.status_code == 429:
                bekle = 10 * k
                print(f"  hiz siniri, {bekle} sn beklenip tekrar denenecek")
                time.sleep(bekle)
                continue
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"  deneme {k}/{deneme} basarisiz: {e}")
            time.sleep(5 * k)
            continue

        if "time," not in r.text:
            print(f"  [HATA] beklenmeyen yanit: {r.text[:200]}")
            return False

        yol = cikti_dir / f"{ad}_{BASLANGIC_YIL}_{BITIS_YIL}.csv"
        yol.write_text(r.text, encoding="utf-8", newline="")
        return dogrula_df(ad, cikar_veri(r.text))

    print(f"  [HATA] {ad}: {deneme} denemede de indirilemedi")
    return False


# --------------------------------------------------------------------------- #
# 2) dogrula
# --------------------------------------------------------------------------- #
def dogrula_df(ad: str, df: pd.DataFrame) -> bool:
    yillar = sorted(df["time"].dt.year.unique())
    beklenen = list(range(BASLANGIC_YIL, BITIS_YIL + 1))
    hedef_satir = beklenen_satir(BASLANGIC_YIL, BITIS_YIL)

    sorunlar = []
    if yillar != beklenen:
        sorunlar.append(
            f"YIL ARALIGI YANLIS: {yillar[0]}-{yillar[-1]} geldi, "
            f"{BASLANGIC_YIL}-{BITIS_YIL} bekleniyordu")
    if len(df) != hedef_satir:
        sorunlar.append(f"satir sayisi {len(df):,}, beklenen {hedef_satir:,}")
    if df["time"].duplicated().any():
        sorunlar.append(f"{df['time'].duplicated().sum()} tekrarli zaman damgasi")
    if df.isna().any().any():
        kolonlar = df.columns[df.isna().any()].tolist()
        sorunlar.append(f"eksik deger var: {kolonlar}")

    # saat surekliligi
    if len(yillar) > 1 or len(df) > 8000:
        fark = df["time"].diff().dropna().dt.total_seconds().div(3600)
        if not (fark == 1).all():
            sorunlar.append(f"{int((fark != 1).sum())} adet saat atlamasi/bosluk")

    int_orani = 100 * (df["Int"] > 0).mean() if "Int" in df else float("nan")
    yil_kwh = df["P"].sum() / 1000 / len(yillar) if "P" in df else float("nan")

    print(f"  [{'SORUNLU' if sorunlar else 'TAMAM'}] {ad}: {len(df):,} satir, "
          f"{yillar[0]}-{yillar[-1]}, Int={int_orani:.3f}%, "
          f"ort. yillik verim={yil_kwh:.1f} kWh/kWp")
    for s in sorunlar:
        print(f"          -> {s}")
    return not sorunlar


def dogrula_klasor(klasor: Path) -> bool:
    dosyalar = sorted([p for p in klasor.iterdir()
                       if p.suffix.lower() in (".csv", ".xlsx", ".xls")])
    if not dosyalar:
        sys.exit(f"{klasor} icinde csv/xlsx bulunamadi")
    print(f"{klasor} kontrol ediliyor:\n")
    tumu = True
    for f in dosyalar:
        try:
            tumu &= dogrula_df(f.stem, cikar_veri(ham_oku(f)))
        except ValueError as e:
            print(f"  [SORUNLU] {f.stem}: {e}")
            tumu = False
    return tumu


# --------------------------------------------------------------------------- #
# 3) duzenle
# --------------------------------------------------------------------------- #
def duzenle(klasor: Path, cikti: Path) -> pd.DataFrame:
    """Tum konumlari tek bir temiz tabloda birlestirir."""
    parcalar = []
    for ad, (lat, lon, ofset) in KONUMLAR.items():
        eslesen = [p for p in klasor.iterdir()
                   if p.stem.lower().startswith(ad)
                   and p.suffix.lower() in (".csv", ".xlsx", ".xls")]
        if not eslesen:
            print(f"  [ATLANDI] {ad}: dosya bulunamadi")
            continue

        df = cikar_veri(ham_oku(eslesen[0]))

        # PVGIS zaman damgasi uydu gozlem dakikasini tasir (:09, :10 gibi).
        # Konumdan konuma degistigi icin saat basina indiriyoruz.
        df["time_utc"] = df["time"].dt.floor("h")
        df["time_local"] = df["time_utc"] + pd.Timedelta(hours=ofset)
        # Orijinal damgayi SAKLIYORUZ: gunes geometrisini saat basina
        # yuvarlanmis damgayla hesaplamak ~1.5 derece sistematik hata verir.
        df["time_gozlem"] = df["time"]
        df = df.drop(columns=["time"])

        df.insert(0, "konum", ad)
        df["lat"], df["lon"], df["utc_ofset"] = lat, lon, ofset
        parcalar.append(df)
        print(f"  {ad}: {len(df):,} satir eklendi")

    if not parcalar:
        sys.exit("hicbir konum yuklenemedi")

    tum = pd.concat(parcalar, ignore_index=True)
    tum = tum.rename(columns={"G(i)": "G_i", "Gb(i)": "Gb_i",
                              "Gd(i)": "Gd_i", "Gr(i)": "Gr_i"})

    # components=1 kullanildiginda PVGIS toplam G(i) yerine bilesenleri
    # dondurur. Toplam isinim bilesenlerin toplamidir; geri kuruyoruz.
    if "G_i" not in tum.columns:
        bilesen = [c for c in ("Gb_i", "Gd_i", "Gr_i") if c in tum.columns]
        if len(bilesen) < 2:
            sys.exit(f"G(i) yok ve bilesenlerden kurulamiyor. Bulunan: {bilesen}")
        tum["G_i"] = tum[bilesen].sum(axis=1)
        print(f"  G_i, bilesenlerden kuruldu: {' + '.join(bilesen)}")
    tum = tum.sort_values(["konum", "time_utc"]).reset_index(drop=True)

    # Once bilinen sutunlari sirala, ARDINDAN geri kalan her seyi ekle.
    # Beyaz liste kullanmak tanimadigimiz sutunlari sessizce siliyordu.
    kolon_sira = ["konum", "time_utc", "time_local", "time_gozlem",
                  "lat", "lon", "utc_ofset",
                  "P", "G_i", "Gb_i", "Gd_i", "Gr_i",
                  "H_sun", "T2m", "WS10m", "Int"]
    onde = [c for c in kolon_sira if c in tum.columns]
    tum = tum[onde + [c for c in tum.columns if c not in onde]]

    zorunlu_sutun = ["P", "G_i", "H_sun", "T2m", "WS10m"]
    eksik = [c for c in zorunlu_sutun if c not in tum.columns]
    if eksik:
        sys.exit(f"Zorunlu sutunlar eksik: {eksik}")

    cikti.parent.mkdir(parents=True, exist_ok=True)
    try:
        tum.to_parquet(cikti, index=False)
        yazilan = cikti
    except (ImportError, ValueError):
        yazilan = cikti.with_suffix(".csv")
        tum.to_csv(yazilan, index=False)
        print("  (pyarrow yok -> csv olarak kaydedildi)")

    # Veri setini DONDUR: deneyler aylar surecek, veri sessizce degisirse
    # sonuclar kayar. Bu hash'i makalede ve kod deposunda saklayin.
    h = hashlib.sha256(yazilan.read_bytes()).hexdigest()[:16]
    (yazilan.parent / "veri_surumu.txt").write_text(
        f"dosya: {yazilan.name}\nsha256_16: {h}\nsatir: {len(tum)}\n"
        f"konum: {', '.join(sorted(tum.konum.unique()))}\n"
        f"aralik: {BASLANGIC_YIL}-{BITIS_YIL}\n", encoding="utf-8")

    print(f"\n{'=' * 62}")
    print(f"Kaydedildi: {yazilan.resolve()}")
    print(f"Toplam {len(tum):,} satir, {tum.konum.nunique()} konum")
    print(f"Veri surumu (sha256): {h}")
    print(f"\nKonum bazinda ortalama yillik verim (kWh/kWp):")
    ozet = (tum.groupby("konum")["P"].sum() / 1000 /
            (BITIS_YIL - BASLANGIC_YIL + 1)).round(1)
    for k, v in ozet.items():
        print(f"  {k:<12} {v:>8.1f}")
    return tum


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("adim", choices=["indir", "dogrula", "duzenle", "hepsi"])
    ap.add_argument("klasor", nargs="?", default="ham",
                    help="ham veri klasoru (varsayilan: ham)")
    ap.add_argument("--cikti", default="veri/pvgis_10yil.parquet")
    ap.add_argument("--sadece", default=None,
                    help="yalnizca bu konumlari indir, virgulle: leipzig,ouarzazate")
    a = ap.parse_args()

    klasor = Path(a.klasor)

    if a.adim in ("indir", "hepsi"):
        klasor.mkdir(parents=True, exist_ok=True)
        istenen = ([s.strip() for s in a.sadece.split(",")] if a.sadece
                   else list(KONUMLAR))
        bilinmeyen = [s for s in istenen if s not in KONUMLAR]
        if bilinmeyen:
            sys.exit(f"KONUMLAR icinde yok: {bilinmeyen}")
        sonuc = {}
        for ad in istenen:
            lat, lon, _ = KONUMLAR[ad]
            sonuc[ad] = indir(ad, lat, lon, klasor)
            time.sleep(2)  # PVGIS'e nazik davran
        basarili = sum(sonuc.values())
        print(f"\nOZET: {basarili}/{len(sonuc)} konum sorunsuz")
        for ad, ok in sonuc.items():
            if not ok:
                print(f"  tekrar denenmeli: {ad}")
        if basarili != len(sonuc) and a.adim == "hepsi":
            sys.exit("Eksik konum var, duzenleme adimina gecilmiyor.")

    if a.adim == "dogrula":
        sys.exit(0 if dogrula_klasor(klasor) else 1)

    if a.adim in ("duzenle", "hepsi"):
        print("\nBirlestiriliyor...")
        duzenle(klasor, Path(a.cikti))


if __name__ == "__main__":
    main()