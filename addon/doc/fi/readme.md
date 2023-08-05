# Etätyöpöydän saavutettavuus #

* Tekijä: [Leonard de Ruijter][1]
* Lataa [viimeisin beetaversio][2]
* Yhteensopivuus: NVDA 2023.2 ja uudemmat

Etätyöpöydän saavutettavuus -lisäosa lisää NVDA:han tuen
etätyöpöytäistunnoille Microsoft Etätyöpöytää, Citrixiä tai VMware Horizonia
käyttäen. Kun tämä lisäosa on asennettu NVDA:han sekä asiakas- että
palvelinkoneessa, palvelimella tuotettu puhe ja pistekirjoitus puhutaan ja
näytetään asiakaskoneessa. Tämä mahdollistaa käyttäjäkokemuksen, jossa
etäjärjestelmän hallinta tuntuu aivan paikallisen järjestelmän
käyttämiseltä.

## Ominaisuudet

* Tuki Microsoft Etätyöpöydälle, Citrixille ja VMware Horizonille
* Puheen ja pistekirjoituksen tuottaminen
* Automaattinen etäpistenäyttöjen tunnistus NVDA:n automaattista pistenäytön
  tunnistusta käyttäen
* Automaattinen etäpuhesyntetisaattoreiden tunnistus erityistä
  tunnistusprosessia käyttäen, joka voidaan poistaa käytöstä NVDA:n
  asetusvalintaikkunasta
* Tuki palvelimella käynnissä oleville NVDA:n massamuistiversioille
  (Citrixiä varten tarvitaan lisämäärityksiä)
* Täysi tuki asiakaskoneessa käynnissä oleville NVDA:n massamuistiversioille
  (lisäosan asentamiseen ei tarvita järjestelmänvalvojan lisäoikeuksia)
* Useita samanaikaisia aktiivisia asiakasistuntoja
* Etätyöpöytä käytettävissä heti NVDA:n käynnistyksen jälkeen
* Mahdollisuus säätää tiettyjä syntetisaattori- ja pistenäyttöasetuksia
  etäistunnosta poistumatta
* Mahdollisuus käyttää puhetta ja pistenäyttöä käyttäjäistunnosta suojatulla
  työpöydällä oltaessa

## Aloittaminen

1. Asenna Etätyöpöydän saavutettavuus NVDA:han sekä asiakas- että
   palvelinkoneella.
1. Etäjärjestelmän pitäisi alkaa puhua paikallista puhesyntetisaattoria
   käyttäen. Jos näin ei tapahdu, valitse etäpuhesyntetisaattori
   palvelimella käynnissä olevan NVDA:n Valitse syntetisaattori
   -valintaikkunasta.
1. Käytä pistenäyttöä ottamalla käyttöön automaattinen pistenäytön tunnistus
   NVDA:n Valitse pistenäyttö -valintaikkunasta.

## Asetusten määrittäminen

Etätyöpöydän saavutettavuus -lisäosan asennuksen jälkeen sen asetukset voidaan määrittää NVDA:n asetusvalintaikkunasta, Johon pääsee valitsemalla NVDA-valikosta Asetukset > Asetukset...
Valitse tämän jälkeen Etätyöpöytä-kategoria.

Tässä valintaikkunassa on seuraavat asetukset:

### Käytä etätyöpöydän saavutettavuutta

Tämän luettelon valintaruuduilla voit valita lisäosan
toimintatilan. Seuraavat vaihtoehdot ovat käytettävissä:

* Saapuville yhteyksille (etätyöpöytäpalvelin): Valitse tämä vaihtoehto, jos
  nykyinen NVDA-kopio on käynnissä etätyöpöytäpalvelimella.

* Lähteville yhteyksille (etätyöpöytäasiakas): Valitse tämä vaihtoehto, jos
  nykyinen NVDA-kopio on käynnissä etätyöpöytäasiakkaalla, joka muodostaa
  yhteyden yhteen tai useampaan palvelimeen.

* Suojatun työpöydän läpivienti: Valitse tämä vaihtoehto, jos haluat käyttää
  NVDA:n käyttäjäkopion pistenäyttöä ja puhetta etätyöpöytää
  käyttäessäsi. Huom: Jotta tätä toimintoa voisi käyttää, Etätyöpöydän
  saavutettavuus -lisäosa on kopioitava suojatulla työpöydällä käytettävään
  NVDA-versioon. Tämä tehdään valitsemalla NVDA:n yleisistä asetuksista
  "Käytä tallennettuja asetuksia sisäänkirjautumisen aikana ja suojatuissa
  ruuduissa (edellyttää järjestelmänvalvojan oikeuksia)".

Kaikki asetukset ovat oletusarvoisesti käytössä, jotta varmistetaan sujuva
lisäosan käytön aloitus. Sinua kuitenkin kannustetaan poistamaan käytöstä
tarpeen mukaan joko palvelin- tai asiakastila.

### Palauta etäpuhe automaattisesti yhteydenmenetyksen jälkeen

Tämä asetus on käytettävissä vain palvelintilassa. Se varmistaa, että yhteys
muodostetaan automaattisesti uudelleen, kun etäpuhesyntetisaattori on
käytössä yhteyden katketessa.  Tämä toiminnallisuus on hyvin samankaltainen
kuin pistenäytön automaattinen tunnistus.  Tämä selittää myös, miksi
tällainen asetus on käytettävissä vain puhetta varten.  Etäpistenäytön
uudelleenyhdistäminen hoidetaan automaattisesti valitsemalla
"Automaattinen"-vaihtoehto Valitse pistenäyttö -valintaikkunasta.

Tämä asetus on oletusarvoisesti käytössä. Tämän asetuksen käytössä pitäminen
on erittäin suositeltavaa, mikäli etätyöpöytäpalvelimella ei ole äänilähtöä.

### Anna etäjärjestelmän säätää ajurin asetuksia

Tämä asiakasasetus mahdollistaa käytössä ollessaan ajurin asetusten (kuten
syntetisaattorin äänen ja äänenkorkeuden) säätämisen etäjärjestelmästä.
Etäjärjestelmässä tehdyt muutokset toteutetaan automaattisesti paikallisessa
järjestelmässä.  Voit ottaa tämän asetuksen käyttöön, mikäli sinulla on
vaikeuksia NVDA-valikon avaamisessa etäjärjestelmää hallitessasi.  Muutoin
asetus kannattaa poistaa käytöstä, koska se saattaa aiheuttaa suorituskyvyn
heikentymistä.

### Säilytä asiakastuki NVDA:ta suljettaessa

Tämä asiakasasetus on käytettävissä vain NVDA:n asennetuissa versioissa.
Asetus varmistaa käytössä ollessaan, että NVDA:n asiakasosa ladataan
etätyöpöytäasiakkaaseesi, vaikka NVDA ei ole käynnissä.

Etätyöpöydän saavutettavuuden asiakasosan käyttöä varten Windowsin
rekisteriin on tehtävä useita muutoksia. Lisäosa varmistaa, että nämä
muutokset tehdään nykyiseen käyttäjäprofiiliin. Muutosten tekemiseen ei
tarvita järjestelmänvalvojan oikeuksia. Siksi NVDA voi käynnistettäessä
tehdä tarvittavat muutokset automaattisesti ja perua ne suljettaessa. Tämä
varmistaa, että lisäosa on täysin yhteensopiva NVDA:n massamuistiversioiden
kanssa. Tämän mahdollistamiseksi asetus on oletusarvoisesti poissa
käytöstä. Jos kuitenkin käytät NVDA:n asennettua versiota ja olet
järjestelmän ainoa käyttäjä, ota tämä asetus käyttöön varmistaaksesi sujuvan
toiminnan silloin, kun NVDA käynnistyy tai ei ole käynnissä muodostettaessa
yhteyttä etäjärjestelmään.

### Ota käyttöön Microsoft-etätyöpöydän tuki

Tämä asetus on oletusarvoisesti käytössä ja varmistaa, että  Etätyöpöydän
saavutettavuuden asiakasosa ladataan Microsoft-etätyöpöytäasiakkaaseen
NVDA:ta käynnistettäessä.  Ellei asiakastuen säilyttämistä ole otettu
käyttöön, nämä muutokset perutaan automaattisesti NVDA:ta suljettaessa.

### Ota käyttöön Citrix Workspacen tuki

Tämä asetus on oletusarvoisesti käytössä ja varmistaa, että Etätyöpöydän
saavutettavuuden asiakasosa ladataan Citrix Workspace -sovellukseen NVDA:ta
käynnistettäessä.  Ellei asiakastuen säilyttämistä ole otettu käyttöön, nämä
muutokset perutaan automaattisesti NVDA:ta suljettaessa.

Tämä asetus on käytettävissä vain seuraavissa tilanteissa:

* Citrix Workspace on asennettu. Huom: Sovelluksen Windows Store -versiota
  ei tueta sen rajoitusten vuoksi.
* Etätyöpöydän saavutettavuus on mahdollista rekisteröidä nykyiselle
  käyttäjälle. Tämä mahdollistetaan aloittamalla etäistunto kerran
  sovelluksen asennuksen jälkeen.

## Citrixin erityisohjeet.

Etätyöpöydän saavutettavuuden käytössä Citrix Workspace -sovelluksen kanssa
on otettava huomioon joitakin tärkeitä seikkoja.

### Asiakaspuolen vaatimukset

1. Sovelluksen Windows Store -versiota ei tueta.

2. Kun olet asentanut Citrix Workspace -sovelluksen, sinun on käynnistettävä
   etäistunto kerran, jotta Etätyöpöydän saavutettavuus -lisäosa voi
   rekisteröidä itsensä. Syynä tähän on se, että sovellus kopioi
   järjestelmän asetukset käyttäjän asetuksiin luodessaan istunnon
   ensimmäistä kertaa. Tämän jälkeen Etätyöpöydän saavutettavuus voi
   rekisteröidä itsensä nykyiselle käyttäjälle.

### Palvelinpuolen vaatimus

Citrix Virtual Apps and Desktopsin versiossa 2109 Citrix otti käyttöön niin
kutsutun virtuaalikanavan sallittujen luettelon. Tämä tarkoittaa, että
kolmannen osapuolen virtuaalikanavia, Etätyöpöydän saavutettavuus -lisäosan
vaatima kanava mukaan lukien, ei oletusarvoisesti sallita. Lisätietoja saat
[tästä Citrixin
blogikirjoituksesta](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/).

Etätyöpöydän saavutettavuus -lisäosan vaatiman RdPipe-kanavan nimenomaista
sallimista ei ole vielä testattu. Tällä hetkellä todennäköisesti paras
vaihtoehto on poistaa sallittujen luettelo kokonaan käytöstä. Jos
järjestelmäsi ylläpitäjä ei ole tyytyväinen tähän ratkaisuun, voit vapaasti
[ilmoittaa siitä asialle omistetussa aiheessa][3].

## Ongelmat ja osallistuminen

Jos haluat ilmoittaa ongelmasta tai osallistua kehitykseen, tutustu
[GitHubin Issues-sivuun][3].

## Ulkoiset osat

Tämä lisäosa on riippuvainen [RD Pipestä][4], Rust-ohjelmointikielellä
kirjoitetusta kirjastosta, joka mahdollistaa etätyöpöytäasiakkaan tuen.  RD
Pipeä jaetaan tämän lisäosan mukana Free Software Foundationin julkaiseman
[GNU AGPL -lisenssin (versio 3)][5] ehtojen mukaisesti.

[[!tag dev beta]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess-beta

[3]: https://github.com/leonardder/rdAccess/issues

[4]: https://github.com/leonardder/rd_pipe-rs

[5]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
