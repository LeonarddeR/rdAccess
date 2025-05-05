# Etätyöpöydän saavutettavuus #

* Tekijä: [Leonard de Ruijter][1]
* Lataa [viimeisin vakaa versio][2]
* Yhteensopivuus: NVDA 2024.1 tai uudempi

RDAccess-lisäosa (Remote Desktop Accessibility) lisää NVDA:han tuen
etätyöpöytäistunnoille Microsoft Etätyöpöytää, Citrixiä tai VMware Horizonia
käyttäen. Kun tämä lisäosa on asennettu NVDA:han sekä asiakas- että
palvelinkoneessa, palvelimella tuotettu puhe ja pistekirjoitus puhutaan ja
näytetään asiakaskoneessa. Tämä mahdollistaa käyttäjäkokemuksen, jossa
etäjärjestelmän hallinta tuntuu aivan paikallisen järjestelmän
käyttämiseltä.

## Ominaisuudet

* Tuki Microsoft Etätyöpöydälle (Azure Virtual Desktop ja Microsoft Cloud PC
  mukaan lukien), Citrixille sekä VMware Horizonille
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

## Muutosloki

### Versio 1.5

* Lisätty mahdollisuus luoda virheenjäljityksen vianmääritysraportti
  painikkeen avulla RDAccessin asetuspaneelissa
  [#23](https://github.com/leonardder/rdAccess/pull/23).
* Tuki monirivisille pistenäytöille NVDA 2025.1:ssä ja sitä uudemmissa
  [#19](https://github.com/leonardder/rdAccess/pull/13).
* NVDA:n yhteensopiva vähimmäisversio on nyt 2024.1. Aiempien versioidenn
  tuki on poistettu.
* Lisätty asiakasyhteyden ilmoitukset
  [#25](https://github.com/leonardder/rdAccess/pull/25).
* RdPipe-riippuvuus päivitetty.
* Käännöksiä päivitetty.

### Versio 1.4

* Uusi vakaa versio.

### Versio 1.3

* Rikkoutuneet pistenäyttöjen näppäinkomennot korjattu.

### Versio 1.2

* Käytetään [Ruffia](https://github.com/astral-sh/ruff) koodin muotoilijana
  ja
  tarkistustyökaluna. [#13](https://github.com/leonardder/rdAccess/pull/13).
* Korjattu ongelma, joka aiheutti sen, että asiakas-NVDA tuotti virheen, kun
  puhe tauotettiin palvelimella.
* Korjattu `winAPI.secureDesktop.post_secureDesktopStateChange`:n tuki.
* Ajurin alustusta paranneltu palvelimella.

### Versio 1.1

* Added support for NVDA 2023.3 style device registration for automatic
  detection of braille
  displays. [#11](https://github.com/leonardder/rdAccess/pull/11).
* Lisätty tuki NVDA 2024.1 alfan
  `winAPI.secureDesktop.post_secureDesktopStateChange`laajennuspisteelle.
  [#12](https://github.com/leonardder/rdAccess/pull/12).

### Versio 1.0

Ensimmäinen vakaa versio.

## Aloittaminen

1. Asenna RDAccess NVDA:han sekä asiakas- että palvelinkoneella.
1. Etäjärjestelmän pitäisi alkaa puhua paikallista puhesyntetisaattoria
   käyttäen. Jos näin ei tapahdu, valitse etäpuhesyntetisaattori
   palvelimella käynnissä olevan NVDA:n Valitse syntetisaattori
   -valintaikkunasta.
1. Käytä pistenäyttöä ottamalla käyttöön automaattinen pistenäytön tunnistus
   NVDA:n Valitse pistenäyttö -valintaikkunasta.

## Asetusten määrittäminen

RDAccess-lisäosan asennuksen jälkeen sen asetukset voidaan määrittää NVDA:n asetusvalintaikkunasta, Johon pääsee valitsemalla NVDA-valikosta Mukautukset > Asetukset...
Valitse tämän jälkeen Etätyöpöytä-kategoria.

Tässä valintaikkunassa on seuraavat asetukset:

### Ota etätyöpöydän saavutettavuus käyttöön

Tämän luettelon valintaruuduilla voit valita lisäosan
toimintatilan. Seuraavat vaihtoehdot ovat käytettävissä:

* Saapuville yhteyksille (etätyöpöytäpalvelin): Valitse tämä vaihtoehto, jos
  nykyinen NVDA-kopio on käynnissä etätyöpöytäpalvelimella.
* Lähteville yhteyksille (etätyöpöytäasiakas): Valitse tämä vaihtoehto, jos
  nykyinen NVDA-kopio on käynnissä etätyöpöytäasiakkaalla, joka muodostaa
  yhteyden yhteen tai useampaan palvelimeen.
* Suojatun työpöydän läpivienti: Valitse tämä vaihtoehto, jos haluat käyttää
  NVDA:n käyttäjäkopion pistenäyttöä ja puhetta etätyöpöytää
  käyttäessäsi. Huom: Jotta tätä toimintoa voisi käyttää, RDAccess-lisäosa
  on kopioitava suojatulla työpöydällä käytettävään NVDA-versioon. Tämä
  tehdään valitsemalla NVDA:n yleisistä asetuksista "Käytä tallennettuja
  asetuksia sisäänkirjautumisen aikana ja suojatuissa ruuduissa (edellyttää
  järjestelmänvalvojan oikeuksia)".

Kaikki asetukset ovat oletusarvoisesti käytössä, jotta varmistetaan sujuva
lisäosan käytön aloitus. Sinua kuitenkin kannustetaan poistamaan käytöstä
tarpeen mukaan joko palvelin- tai asiakastila.

### Palauta etäpuhe automaattisesti yhteydenmenetyksen jälkeen

Tämä asetus on käytettävissä vain palvelintilassa. Se varmistaa, että yhteys
muodostetaan automaattisesti uudelleen, kun etäpuhesyntetisaattori on
käytössä yhteyden katketessa.  Tämä toiminnallisuus on samankaltainen kuin
pistenäytön automaattinen tunnistus.

Tämä asetus on oletusarvoisesti käytössä. Tämän asetuksen käytössä pitäminen
on erittäin suositeltavaa, mikäli etätyöpöytäpalvelimella ei ole äänilähtöä.

### Anna etäjärjestelmän säätää ajurin asetuksia

Tämä asiakasasetus mahdollistaa käytössä ollessaan ajurin asetusten (kuten
syntetisaattorin äänen ja äänenkorkeuden) säätämisen etäjärjestelmästä.
Etäjärjestelmässä tehdyt muutokset toteutetaan automaattisesti paikallisessa
järjestelmässä.

### Säilytä asiakastuki NVDA:ta suljettaessa

Tämä asiakasasetus on käytettävissä vain NVDA:n asennetuissa versioissa.
Asetus varmistaa käytössä ollessaan, että NVDA:n asiakasosa ladataan
etätyöpöytäasiakkaaseesi, vaikka NVDA ei olisi käynnissä.

Windowsin rekisteriin on tehtävä muutoksia RDAccessin asiakasosan käyttöä
varten. Lisäosa varmistaa, että nämä muutokset tehdään nykyiseen
käyttäjäprofiiliin. Muutosten tekemiseen ei tarvita järjestelmänvalvojan
oikeuksia. Siksi NVDA voi käynnistettäessä tehdä tarvittavat muutokset
automaattisesti ja perua ne suljettaessa. Tämä varmistaa, että lisäosa on
täysin yhteensopiva NVDA:n massamuistiversioiden kanssa.

Tämä asetus on oletusarvoisesti poissa käytöstä. Jos käytössäsi kuitenkin on
asennettu versio ja olet järjestelmän ainoa käyttäjä, suosittelemme tämän
asetuksen käyttöön ottamista. Tämä varmistaa sujuvan toiminnan
muodostettaessa yhteyttä etäjärjestelmään NVDA:n käynnistyksen jälkeen.

### Ota käyttöön Microsoft-etätyöpöydän tuki

Tämä asetus on oletusarvoisesti käytössä ja varmistaa, että  RDAccessin
asiakasosa ladataan Microsoft-etätyöpöytäasiakkaaseen NVDA:ta
käynnistettäessä.  Nämä muutokset perutaan automaattisesti NVDA:ta
suljettaessa, ellei asiakastuen säilyttämistä ole otettu käyttöön.

### Ota käyttöön Citrix Workspacen tuki

Tämä asetus on oletusarvoisesti käytössä ja varmistaa, että RDAccessin
asiakasosa ladataan Citrix Workspace -sovellukseen NVDA:ta
käynnistettäessä.  Nämä muutokset perutaan automaattisesti NVDA:ta
suljettaessa, ellei asiakastuen säilyttämistä ole otettu käyttöön.

Tämä asetus on käytettävissä vain seuraavissa tilanteissa:

* Citrix Workspace on asennettu. Huom: Sovelluksen Windows Store -versiota
  ei tueta sen rajoitusten vuoksi.
* RDAccess on mahdollista rekisteröidä nykyiselle käyttäjälle. Tämä tehdään
  aloittamalla etäistunto kerran sovelluksen asennuksen jälkeen.

### Ilmaise yhteyden muutokset

Tästä yhdistelmäruudusta voit hallita ilmoituksia, jotka vastaanotetaan, kun
etäjärjestelmä avaa tai sulkee etäpuhe- tai pistenäyttöyhteyden. Seuraavat
vaihtoehdot ovat käytettävissä:

* Ei käytössä (ei ilmoituksia)
* Ilmoituksilla (esim. "Etäpistenäyttö yhdistetty")
* Äänillä (NVDA 2025.1 ja uudemmat)
* Ilmoituksilla ja äänillä

Huomaa, että äänet eivät ole käytettävissä NVDA 2025.1:tä vanhemmissa
versioissa. Vanhemmissa versioissa käytetään äänimerkkejä.

### Avaa vianmääritysraportti

Tämä painike avaa erillisen ikkunan, joka sisältää JSON-muotoisen tulosteen
useista vianmäärityksistä, jotka voivat mahdollisesti auttaa
virheenjäljityksessä.  Kun [teet vikailmoituksen GitHubissa][4], sinua
saatetaan pyytää toimittamaan tämä raportti lisäosan tekijöille.

## Citrix-ohjeet

RDAccessin käytössä Citrix Workspace -sovelluksen kanssa on otettava
huomioon joitakin tärkeitä seikkoja.

### Asiakaspuolen vaatimukset

1. Sovelluksen Windows Store -versiota ei tueta.
1. Kun olet asentanut Citrix Workspace -sovelluksen, sinun on käynnistettävä
   etäistunto kerran, jotta RDAccess voi rekisteröidä itsensä. Syynä tähän
   on se, että sovellus kopioi järjestelmän asetukset käyttäjän asetuksiin
   luodessaan istunnon ensimmäistä kertaa. Tämän jälkeen RDAccess voi
   rekisteröidä itsensä nykyiselle käyttäjälle.

### Palvelinpuolen vaatimus

Citrix Virtual Apps and Desktopsin versiossa 2109 Citrix otti käyttöön niin
kutsutun virtuaalikanavan sallittujen luettelon. Tämä tarkoittaa, että
kolmannen osapuolen virtuaalikanavia, RDAccessin vaatima kanava mukaan
lukien, ei oletusarvoisesti sallita. Lisätietoja saat [tästä Citrixin
blogikirjoituksesta](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/).

RDAccessin vaatiman RdPipe-kanavan nimenomaista sallimista ei ole vielä
testattu. Tällä hetkellä todennäköisesti paras vaihtoehto on poistaa
sallittujen luettelo kokonaan käytöstä. Jos järjestelmäsi ylläpitäjä ei ole
tyytyväinen tähän ratkaisuun, voit vapaasti [ilmoittaa siitä asialle
omistetussa aiheessa][3].

## Ongelmat ja osallistuminen

Jos haluat ilmoittaa ongelmasta tai osallistua kehitykseen, tutustu
[GitHubin Issues-sivuun][4].

## Ulkoiset osat

Tämä lisäosa on riippuvainen [RD Pipestä][5], Rust-ohjelmointikielellä
kirjoitetusta kirjastosta, joka mahdollistaa etätyöpöytäasiakkaan tuen.  RD
Pipeä jaetaan tämän lisäosan mukana Free Software Foundationin julkaiseman
[GNU AGPL -lisenssin (versio 3)][6] ehtojen mukaisesti.

[[!tag stable dev beta]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess

[3]: https://github.com/leonardder/rdAccess/issues/1

[4]: https://github.com/leonardder/rdAccess/issues

[5]: https://github.com/leonardder/rd_pipe-rs

[6]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
