# NVDA Remote Desktop #

* Tekijä: [Leonard de Ruijter][1]
* Lataa [beetaversio][2]
* Yhteensopivuus: NVDA 2023.1 ja uudemmat

Tämä lisäosa lisää NVDA:han tuen etätyöpöytäistunnoille Microsoft
Etätyöpöytää, Citrixiä tai VMware Horizonia käyttäen. Kun tämä lisäosa on
asennettu NVDA:han sekä asiakas- että palvelinkoneessa, palvelimella
tuotettu puhe ja pistekirjoitus puhutaan ja näytetään asiakaskoneessa. Tämä
mahdollistaa käyttäjäkokemuksen, jossa etäjärjestelmän hallitseminen tuntuu
aivan paikallisen järjestelmän käyttämiseltä.

## Ominaisuudet

* Tuki Microsoft Etätyöpöydälle, Citrixille ja VMware Horizonille
* Puheen ja pistekirjoituksen tulostus
* Automaattinen etäpistenäyttöjen tunnistus NVDA:n automaattista pistenäytön
  tunnistusta käyttäen
* Automaattinen etäpuhesyntetisaattoreiden tunnistus erityistä
  tunnistusprosessia käyttäen, joka voidaan poistaa käytöstä NVDA:n
  asetusvalintaikkunasta
* Tuki palvelimella käynnissä oleville NVDA:n massamuistiversioille
  (Citrixiä varten tarvitaan lisämäärityksiä)
* Täysi tuki asiakaskoneessa käynnissä oleville NVDA:n massamuistiversioille
  (lisäosan asentamiseen ei tarvita järjestelmänvalvojan lisäoikeuksia)
* Useita aktiivisia asiakasistuntoja samanaikaisesti
* Etätyöpöytä käytettävissä heti NVDA:n käynnistyksen jälkeen
* Mahdollisuus säätää tiettyjä syntetisaattori- ja pistenäyttöasetuksia
  etäistunnosta poistumatta
* Mahdollisuus käyttää puhetta ja pistenäyttöä käyttäjäistunnosta suojatulla
  työpöydällä oltaessa

## Aloittaminen

1. Asenna tämä lisäosa sekä asiakas- että palvelinkoneelle.
1. Etäjärjestelmän pitäisi alkaa puhua paikallista puhesyntetisaattoria
   käyttäen. Jos näin ei tapahdu, valitse etäpuhesyntetisaattori
   palvelimella käynnissä olevan NVDA:n Valitse syntetisaattori
   -valintaikkunasta.
1. Käytä pistenäyttöä ottamalla käyttöön automaattinen pistenäytön tunnistus
   NVDA:n Valitse pistenäyttö -valintaikkunasta.

## Ongelmat ja osallistuminen

Jos haluat ilmoittaa ongelmasta tai osallistua kehitykseen, tutustu
[GitHubin Issues-sivuun][3].

## Ulkoiset osat

Tämä lisäosa on riippuvainen [RD Pipestä][4], Rust-ohjelmointikielellä
kirjoitetusta kirjastosta, joka mahdollistaa etätyöpöytäasiakkaan tuen. RD
Pipeä jaetaan tämän lisäosan mukana Free Software Foundationin julkaiseman
[GNU AGPL -lisenssin (versio 3)][5] ehtojen mukaisesti.

[[!tag dev]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=nvdaRd-beta

[3]: https://github.com/leonardder/nvdaRd/issues

[4]: https://github.com/leonardder/rd_pipe-rs

[5]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
