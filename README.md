# \# GRZS Predikcija nesreč

# Glavni cilj tega projekta je izdelati klasifikacijski model, ki bo znal napovedati, ali se bo odprava v planine končala srečno ali z nesrečo. Poleg tega pa bomo odgovorili na druga vprasanja povezana s tem datasetom, kot npr.

# \- s

# \- 

# \- 

# \-

# 

# \# Pridobitev podatkov

# Vse podatke uporabljene v sledečih raziskavah lahko najdete v tem repositoriju pod /data. Jupiter notebook za čiščenje podatkov lahko najdete pod 

# 

# Originalen dataset smo pridobili s pomočjo prijazne Neže Bajzelj iz GRZS.

# Če ta dataset odpremo s pomočjo pandas lahko vidimo da dataset vsebuje 7439 vrstic in ima naslednje stolpce:

# \- PNID,

# \- Datum,

# \- Postaja,

# \- Št. ponesrečencev,

# \- HeliStCiklov,

# \- Dejavnost,

# \- PoskodbaVrstaNACA,

# \- Vzrok,

# \- Izkušenost,

# \- Okoliščine, 

# \- Poškodbe

# 

# Prvo lahko odstranimo stolpca PNID in HeliSTCiklov, saj nam ti podatke ne koristijo, poleg tega lahko odstranimo duplikirane vrednosti, saj so nekatere intervencije vpisane dvakrat. Zdaj lahko vidimo, da se je število instanc spremenilo na 6485, in imamo še samo 9 stolpcov.

# 

# Treba je tudi filtrirati dejavnosti in ločiti tiste, katere nas ne zanimajo(letenje z zmajem, promet, drugo(naravna ujma)...)

# 

# Prvo spremenimo stolpec dejavnost, da bo vsaka unikatna vrednost svoj stolpec - uporabimo one hot encoding s get\_dummies().

# Kar hitro vidimo da imamo zdaj 441 stolpcev, da bi šli vsakega posebej odstranjevat bi bilo nehumano, zato se bomo lotili problema na drug način.

# \- Preštejemo koliko vrednosti je posameznega stolpca

# \- Odstranimo tiste, ki se ne ponavljajo pogosto

# \- Odstranimo neprimerne

# Ko smo to opravili nam ostane 4825 vrstic in glavni stolpci za dejavnosti.

# 

# Za treniranje klasifikatorja bomo potrebovali več značilnic, kot so vremenske razmere tistega dni, prejšnih 2 dni - to lahko dobimo iz datuma.

# Potrebovali pa bomo tudi lokacijske informacije, kje se je nesreča zgodili, po kateri poti se je šlo, in tako dalje - to pa bomo probali dobiti iz novic.

# 

# \## Pridobivanje novic o reševalnih akcijah:

# 

# \- Pridobis vse novice posameznega gorsko reševalnega društva iz njihovega facebooka/spletne strani (posebej python scripte)

# \- za vsako intervencijo iz zbirke najdeš novice, ki so bile objavljene +-1dan od datuma intervencije

# \- za vsako izbrano novico preveris ce ustreza intervenciji preko opisa

# \- dodas nove stolpce z podatki kraja intervencije, poti itd.

# \- Uporabis informacije o datumu in kraju da dobiš vremenske podakte za tisti kraj na tisti datum in 1,2 dni prej.

# 

# Ko opravimo ta postopek, vidimo da nam je ostalo 357 vrstic. Več podatkov o tem lahko najdete v GRZS.ipynb

