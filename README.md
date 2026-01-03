# GRZS Predikcija nesreč
Glavni cilj tega projekta je izdelati klasifikacijski model, ki na podlagi značilnic (dejavnost, lokacija, vreme, …) oceni, ali se bo aktivnost v gorah končala uspešno ali pa z nesrečo (aproksimirano z NACA lestvico). Poleg tega projekt vključuje še analize in vizualizacije, ki pomagajo razumeti vzorce intervencij GRZS.

V okviru projekta odgovarjamo tudi na vprašanja, kot so:
- Kako se intervencije porazdelijo geografsko in ali se pojavljajo smiselne gruče lokacij.
- Kako se število intervencij spreminja skozi čas (sezone/meseci).
- Kateri tipi dejavnosti so povezani z višjo povprečno resnostjo nesreče (NACA).
- Ali je mogoče opaziti povezavo med vremenom (temperatura, dež, sneg) in resnostjo poškodb.
- Predikcija, ali bo posamezna gorska reševalna postaja potrebovala helikoptersko pomoč naslednji dan...

## Struktura repozitorija

- `Data/`  
  Podatki različnih datasetov

- `ScrapingHelpers/`  
  Python programi, ki so bili uporabljeni za pridobitev podatkov

- `webapp/`  
  Preprost spletni vmesnik + API strežnik, ki uporablja shranjen model za napoved, ali se bo zgodila nesreča glede na okoliščine.


# Pridobitev podatkov

Vse podatke, uporabljene v raziskavi, najdete v tem repozitoriju pod `Data/`.  
Glavni jupyter notebook za čiščenje podatkov in gradnjo modelov je GRZS.ipynb

Originalen dataset smo pridobili s pomočjo prijazne Neže Bajzelj iz GRZS.

Če dataset odpremo s pandas, vidimo približno 7439 vrstic in naslednje stolpce:
- `PNID`
- `Datum`
- `Postaja`
- `Št. ponesrečencev`
- `HeliStCiklov`
- `Dejavnost`
- `PoskodbaVrstaNACA`
- `Vzrok`
- `Izkušenost`
- `Okoliščine`
- `Poškodbe`

## Osnovno čiščenje

1. Odstranimo stolpca `PNID` in (v prvi fazi) `HeliStCiklov`, ker:
   - `PNID` je identifikator,
   - `HeliStCiklov` v začetnem delu čiščenja ni ključen (kasneje ga po potrebi dodamo nazaj).

2. Odstranimo **duplikate**, ker so nekatere intervencije vpisane dvakrat.  
   Po tem koraku ostane približno **6485** instanc.

## Filtriranje dejavnosti

Ker so v stolpcu `Dejavnost` tudi kategorije, ki niso predmet analize (npr. promet, zmaj/padalo, vodne aktivnosti, delo, …), jih filtriramo.

Postopek:
- `Dejavnost` pretvorimo v one-hot stolpce (`get_dummies()`).
- Ker dobimo veliko stolpcev, uporabimo **prag pojavitev**:
  - preštejemo pojavitev vsake kategorije,
  - odstranimo redke kategorije (npr. manj kot 25 pojavitev),
  - ročno odstranimo še očitno neprimerne kategorije.
- Obdržimo samo vrstice, kjer je po filtriranju še vedno prisotna vsaj ena “veljavna” dejavnost.

Po tem koraku ostane približno **4825** vrstic.

---

# Nadgradnja značilnic: novice, lokacija, vreme

Za boljše modele potrebujemo več konteksta, predvsem:
- **lokacijo** (kje se je nesreča zgodila),
- **vreme** na dan nesreče in nekaj dni prej.

## Pridobivanje novic o reševalnih akcijah

Ker originalni dataset ne vsebuje natančne lokacije poti/dogodka, jo poskusimo pridobiti iz javnih objav društev (Facebook/spletne strani).

Postopek:
- pridobimo objave posameznih društev (ločene skripte),
- za vsako intervencijo poiščemo objave
- preverimo ujemanje (opis/datum),
- dodamo nove stolpce (npr. lokacija/pot),
- nato glede na datum in lokacijo pridobimo vremenske podatke za:
  - tisti dan,
  - prejšnji dan,
  - pred-prejšnji dan.

Po tem postopku je število popolno obogatenih vrstic manjše (približno **357**), ker:
- niso vse intervencije opisane v javnih objavah,
- objave niso vedno dovolj strukturirane za zanesljivo ujemanje,
- manjkajo lokacije ali so dvoumne.

## Geokodiranje (lat/lon)

Za lažjo vizualizacijo in uporabo lokacije v modelih lokacije geokodiramo v:
- `latitude`
- `longitude`

Za geokodiranje uporabljamo https://www.geoapify.com/geocoding-api/

## Končni dataset

Po združevanju podatkov, čiščenju in one-hot kodiranju kategorij (npr. `Postaja`, `Vzrok`, `Izkušenost`) se izdela končni CSV, uporabljen za analize in modele:
- `KončniDataset.csv`
- `CelotenDatasetWithLatLon.csv` (razširjena verzija, kjer se manjkajoče lokacije dopolnijo z regresijo in nato ponovno dodajo vremenski podatki)

Več lahko najdete v GRZS.ipynb.

## Kako zagnati web app

- v /backend poženite naslednje ukaze:
```powershell
npm install
python -m pip install -r requirements.txt
npm start
```
- odprite frontend/index.html



