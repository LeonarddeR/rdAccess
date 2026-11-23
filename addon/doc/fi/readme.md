# RDAccess: Etätyöpöydän saavutettavuus

* Tekijä: [Leonard de Ruijter][1]
* Lataa [viimeisin vakaa versio][2]
* Yhteensopivuus: NVDA 2026.1 tai uudempi

RDAccess-lisäosa (Remote Desktop Accessibility) lisää NVDA:han tuen etätyöpöytäistunnoille Microsoft-etätyöpöytää, Citrixiä, Parallels RASia ja VMware Horizonia käyttäen.
Kun tämä lisäosa on asennettu NVDA:han sekä asiakas- että palvelinkoneessa, palvelimella tuotettu puhe toistetaan ja pistekirjoitus näytetään asiakaskoneessa.
Tämä mahdollistaa käyttäjäkokemuksen, jossa etäjärjestelmän hallinta tuntuu aivan paikallisen järjestelmän käyttämiseltä.

## Ominaisuudet

* Microsoft Etätyöpöydän (sekä Azure Virtual Desktopin ja Microsoft Cloud PC:n), Citrixin, Parallels RASin ja VMware Horizonin tuki
* Puheen ja pistekirjoituksen tuottaminen
* Automaattinen etäpistenäyttöjen tunnistus NVDA:n automaattista pistenäytön tunnistusta käyttäen
* Automaattinen etäpuhesyntetisaattoreiden tunnistus erityistä tunnistusprosessia käyttäen, joka voidaan poistaa käytöstä NVDA:n asetusvalintaikkunasta
* Tuki palvelimella käynnissä oleville NVDA:n massamuistiversioille (Citrixiä varten tarvitaan lisämäärityksiä)
* Täysi tuki asiakaskoneessa käynnissä oleville NVDA:n massamuistiversioille (lisäosan asentamiseen ei tarvita järjestelmänvalvojan lisäoikeuksia)
* Useita samanaikaisia aktiivisia asiakasistuntoja
* Etätyöpöytä käytettävissä heti NVDA:n käynnistyksen jälkeen
* Mahdollisuus säätää tiettyjä syntetisaattori- ja pistenäyttöasetuksia etäistunnosta poistumatta

## Muutosloki

### Version 2.1

* Speech coming from the remote system now follows the speech mode of NVDA on the client. For example, when speech is off on the client, the remote system no longer speaks. In on-demand mode, remote speech is only spoken while the remote session has focus. With the new client option "Incoming speech follows local speech mode", you can make on-demand mode silent, or restore the previous behavior.
* Updated translations.

### Versio 2.0.5

* Korjattu NVDA 2027.1:n ongelma, jonka vuoksi suljettujen yhteyksien resursseja ei vapautettu asianmukaisesti. Tämä aiheutti muun muassa virheiden tallentumista lokiin, kun NVDA suljettiin etäjärjestelmässä.
* Käännöksiä päivitetty.

### Versio 2.0.4

* Yhteensopivuus NVDA 2027.1:ssä käyttöön otettujen Windows-rajapinnan muutosten kanssa.
* RD Pipe -riippuvuus päivitetty versioon 1.1.0.
* Käännöksiä päivitetty.

### Versio 2.0.3

* Asiakaskoneen Caps Lock -näppäimen tilan synkronointi perustuu nyt NVDA 2026.3:n toimintoihin, joiden avulla RDAccess pystyy erottamaan etätyöpöytäasiakasohjelman takaisin välittämät Caps Lockin painallukset todellisista näppäinpainalluksista. Tämän ansiosta synkronointi toimii myös silloin, kun etätyöpöytäistunto ei ole koko näytön tilassa mutta Windowsin näppäinyhdistelmät suoritetaan etätietokoneessa, sekä silloin, kun NVDA:n ”Käsittele muiden sovellusten näppäinpainallukset” -asetus on poistettu käytöstä. Asiakaskoneen synkronointi edellyttää nyt vähintään NVDA-versiota 2026.3. Palvelinkoneen synkronointi toimii kuitenkin edelleen kaikissa tuetuissa versioissa.

### Versio 2.0.2

* Korjattu ongelma, jonka vuoksi Caps Lock -näppäimen tila ei pysynyt samana asiakas- ja palvelinkoneessa, kun molemmissa käytettiin Caps Lockia NVDA-näppäimenä. Koko näytön etätyöpöytäistunnossa Caps Lockin useat peräkkäiset painallukset eivät enää muuta sen tilaa asiakaskoneessa. Jos näppäimen tilaa muutetaan istunnossa, muutos välittyy asiakaskoneeseen heti kohdistuksen siirtyessä pois istunnosta. Synkronointia ohjaa uusi, oletusarvoisesti käytössä oleva ”Synkronoi Caps Lock -näppäimen tila asiakas- ja palvelinkoneen välillä” -asetus. Sen on oltava käytössä molemmissa koneissa. Caps Lockin tila voi kuitenkin edelleen jäädä synkronoimatta, jos asiakaskoneessa ei käytetä ”Käsittele muiden sovellusten näppäinpainallukset” -asetusta.

### Versio 2.0.1

* Automaattisesti käyttöön otettu etäpuhe pysyy nyt käytössä myös asetusprofiilin vaihtuessa. Aiemmin NVDA palautti käyttöön käyttäjän määrittämän puhesyntetisaattorin heti asetusprofiilin aktivoituessa, esimerkiksi siirryttäessä sovellukseen, jolle oli tehty oma asetusprofiili.
* Asetuksen ”Palauta etäpuhe automaattisesti yhteyden katkettua” nimeksi on muutettu ”Vaihda etäpuheeseen automaattisesti, kun se on käytettävissä”, mikä kuvaa paremmin asetuksen toimintaa.
* Korjattu etäjärjestelmässä usein esiintyneet virheet, joita ilmeni käytettäessä etäpuhesyntetisaattoria automaattisen kielen vaihtamisen ollessa käytössä. Ei-tuetuista kielistä ilmoitetaan nyt asiakaskoneen puhesyntetisaattorin kielituen perusteella.
* RDAccessia voidaan nyt käyttää myös ARM64-pohjaisissa Windows-versioissa x64-emuloinnilla toimivissa etätyöpöytäasiakasohjelmissa.
* Yhteensopivuus NVDA 2026.3:ssa käyttöön otettujen pistekirjoitussyötteen muutosten kanssa.

### Version 2.0

* Speech and braille coming from the remote system are now presented sooner, which makes working in a remote session feel more responsive.
* When starting a remote server instance of NVDA, braille is now shown as soon as a remote session connects, instead of only after the first keypress or focus change.
* Fixed a freeze when switching away from the remote synthesizer or braille display while a session was disconnecting.
* RDAccess now exchanges speech and braille using a new protocol modeled on the one used by NVDA's built-in Remote Access. It is more robust and no longer relies on the pickle format that a compromised remote system could abuse. The protocol version is chosen automatically, so a client and a server running different versions of RDAccess still work together.
* The minimum compatible NVDA version is now 2026.1. Removed support for earlier versions.
* Adapted to the braille changes introduced in NVDA 2026.3.
* Updated RD Pipe dependency to version 0.9.0.
* RDAccess is now licensed under the GNU General Public License version 2 or later.

### Version 1.7.1

* Hopefully fixed a bug in rd_pipe that caused the wrong virtual channel to be created.

### Version 1.7

* Removed secure desktop support.
* Added a client option "Incoming speech pitch change percentage" to shift the pitch of speech rendered from a remote NVDA, making remote and local speech audibly distinguishable.

### Version 1.6

* Documented and improved Parallels RAS support.
* The minimum compatible NVDA version is now 2025.1. Removed support for earlier versions.
* RdPipe-riippuvuus päivitetty.
* Added the ability to configure RdPipe log level.
* Added a viewer for the RdPipe log, available from the settings panel.
* Improved uninstall behavior (no longer raise errors or remove Citrix support when Citrix is not available).

### Versio 1.5

* Lisätty mahdollisuus luoda virheenjäljityksen vianmääritysraportti painikkeen avulla RDAccessin asetuspaneelissa [#23](https://github.com/leonardder/rdAccess/pull/23).
* Tuki monirivisille pistenäytöille NVDA 2025.1:ssä ja sitä uudemmissa [#19](https://github.com/leonardder/rdAccess/pull/13).
* NVDA:n yhteensopiva vähimmäisversio on nyt 2024.1. Aiempien versioidenn tuki on poistettu.
* Lisätty asiakasyhteyden ilmoitukset [#25](https://github.com/leonardder/rdAccess/pull/25).
* RdPipe-riippuvuus päivitetty.
* Käännöksiä päivitetty.

### Versio 1.4

* Uusi vakaa versio.

### Versio 1.3

* Rikkoutuneet pistenäyttöjen näppäinkomennot korjattu.

### Versio 1.2

* Käytetään [Ruffia](https://github.com/astral-sh/ruff) koodin muotoilijana ja tarkistustyökaluna. [#13](https://github.com/leonardder/rdAccess/pull/13).
* Korjattu ongelma, joka aiheutti sen, että asiakas-NVDA tuotti virheen, kun puhe tauotettiin palvelimella.
* Korjattu `winAPI.secureDesktop.post_secureDesktopStateChange`:n tuki.
* Ajurin alustusta paranneltu palvelimella.

### Versio 1.1

* Added support for NVDA 2023.3 style device registration for automatic detection of braille displays. [#11](https://github.com/leonardder/rdAccess/pull/11).
* Lisätty tuki NVDA 2024.1 alfan `winAPI.secureDesktop.post_secureDesktopStateChange`laajennuspisteelle. [#12](https://github.com/leonardder/rdAccess/pull/12).

### Versio 1.0

Ensimmäinen vakaa versio.

## Aloittaminen

1. Asenna RDAccess NVDA:han sekä asiakas- että palvelinkoneella.
1. Etäjärjestelmän pitäisi alkaa puhua paikallista puhesyntetisaattoria käyttäen.
      Jos näin ei tapahdu, valitse etäpuhesyntetisaattori palvelimella käynnissä olevan NVDA:n Valitse syntetisaattori -valintaikkunasta.
1. Käytä pistenäyttöä ottamalla käyttöön automaattinen pistenäytön tunnistus NVDA:n Valitse pistenäyttö -valintaikkunasta.

## Asetusten määrittäminen

RDAccess-lisäosan asennuksen jälkeen sen asetukset voidaan määrittää NVDA:n asetusvalintaikkunasta, Johon pääsee valitsemalla NVDA-valikosta Mukautukset > Asetukset...
Valitse tämän jälkeen Etätyöpöytä-kategoria.

Tässä valintaikkunassa on seuraavat asetukset:

### Ota etätyöpöydän saavutettavuus käyttöön

Tämän luettelon valintaruuduilla voit valita lisäosan toimintatilan.
Seuraavat vaihtoehdot ovat käytettävissä:

* Saapuville yhteyksille (etätyöpöytäpalvelin): Valitse tämä vaihtoehto, jos nykyinen NVDA-kopio on käynnissä etätyöpöytäpalvelimella.
* Lähteville yhteyksille (etätyöpöytäasiakas): Valitse tämä vaihtoehto, jos nykyinen NVDA-kopio on käynnissä etätyöpöytäasiakkaalla, joka muodostaa yhteyden yhteen tai useampaan palvelimeen.

Kaikki asetukset ovat oletusarvoisesti käytössä, jotta varmistetaan sujuva lisäosan käytön aloitus.
Sinua kuitenkin kannustetaan poistamaan käytöstä tarpeen mukaan joko palvelin- tai asiakastila.

### Synchronize the Caps Lock Key between Client and Server

When both the client and the server run NVDA with caps lock as an NVDA modifier key, the caps lock state can get out of sync, since the remote desktop client feeds caps lock presses back into the client system whenever it captures the keyboard, for example in a full screen session.
When this option is enabled on the client, these fed back caps lock presses no longer toggle caps lock on the client.
When it is enabled on the server, the server reports its caps lock state to the client, which applies it as soon as the remote session loses focus.
For correct behavior, this option needs to be enabled on both the client and the server; it is enabled by default on both.
On the client, this option requires NVDA 2026.3 or later; the server side works with every NVDA version supported by the add-on.

Note that while a remote desktop session window has focus, caps lock presses sent by other software, such as NVDA Remote Access, are suppressed on the client as well.

### Automatically Switch to Remote Speech when Available

This option is only available in server mode.
It ensures that Remote Speech is activated as soon as a remote desktop client offers it, similar to braille display auto-detection, and that the connection is automatically re-established when it is lost.
While Remote Speech is active this way, your configured synthesizer is left untouched, and switching configuration profiles no longer falls back to it.

Tämä asetus on oletusarvoisesti käytössä.
Tämän asetuksen käytössä pitäminen on erittäin suositeltavaa, mikäli etätyöpöytäpalvelimella ei ole äänilähtöä.

### Anna etäjärjestelmän säätää ajurin asetuksia

Tämä asiakasasetus mahdollistaa käytössä ollessaan ajurin asetusten (kuten syntetisaattorin äänen ja äänenkorkeuden) säätämisen etäjärjestelmästä.
Etäjärjestelmässä tehdyt muutokset toteutetaan automaattisesti paikallisessa järjestelmässä.

### Säilytä asiakastuki NVDA:ta suljettaessa

Tämä asiakasasetus on käytettävissä vain NVDA:n asennetuissa versioissa. Asetus varmistaa käytössä ollessaan, että NVDA:n asiakasosa ladataan etätyöpöytäasiakkaaseesi, vaikka NVDA ei olisi käynnissä.

To use the client portion of RDAccess, changes need to be made in the Windows Registry.
The add-on ensures that these changes are made under the profile of the current user, requiring no administrative privileges.
Therefore, NVDA can automatically apply the necessary changes when loaded and undo these changes when exiting NVDA, ensuring compatibility with portable versions of NVDA.

This option is disabled by default.
However, if you are running an installed copy and you are the only user of the system, it is advised to enable this option for smooth operation when connecting to a remote system after NVDA starts.

### Enable Default Remote Desktop Support

This option, enabled by default, ensures that the client portion of RDAccess is loaded in the Microsoft Remote Desktop client (mstsc) when starting NVDA.
This is also required for VMware Horizon, Parallels RAS, Azure Virtual Desktop. etc.
Changes made through this option will be automatically undone when exiting NVDA unless persistent client support is enabled.

### Ota käyttöön Citrix Workspacen tuki

Tämä asetus on oletusarvoisesti käytössä ja varmistaa, että RDAccessin asiakasosa ladataan Citrix Workspace -sovellukseen NVDA:ta käynnistettäessä.
Nämä muutokset perutaan automaattisesti NVDA:ta suljettaessa, ellei asiakastuen säilyttämistä ole otettu käyttöön.

Tämä asetus on käytettävissä vain seuraavissa tilanteissa:

* Citrix Workspace on asennettu.
    Huom: Sovelluksen Windows Store -versiota ei tueta sen rajoitusten vuoksi.
* RDAccess on mahdollista rekisteröidä nykyiselle käyttäjälle.
    Tämä tehdään aloittamalla etäistunto kerran sovelluksen asennuksen jälkeen.

### Ilmaise yhteyden muutokset

Tästä yhdistelmäruudusta voit hallita ilmoituksia, jotka vastaanotetaan, kun etäjärjestelmä avaa tai sulkee etäpuhe- tai pistenäyttöyhteyden.
Seuraavat vaihtoehdot ovat käytettävissä:

* Ei käytössä (ei ilmoituksia)
* Ilmoituksilla (esim. "Etäpistenäyttö yhdistetty")
* Sounds
* Ilmoituksilla ja äänillä

### Incoming Speech Pitch Change Percentage

This client option shifts the pitch of speech rendered locally when it originates from a remote NVDA, making remote and local speech audibly distinguishable.

The value is a percentage between -100 and 100.
Positive values raise pitch, negative values lower it.
A value of 0 disables the shift.
The default is 10.

The shift is applied only when the local synthesizer supports pitch commands; synthesizers without pitch support are unaffected.

### Incoming Speech Follows Local Speech Mode

This client option controls whether speech coming from the remote system follows the speech mode of NVDA on the client.
You can choose between:

* No: remote speech is spoken in every speech mode on the client.
* Yes, on-demand speaks while remote session has focus (default)
* Yes, on-demand is silent

When remote speech follows the speech mode on the client, the speech modes work as follows:

* Talk: remote speech is spoken.
* On-demand: depending on the chosen option, remote speech is only spoken while the remote session has focus, or not at all.
* Beeps: NVDA beeps instead of speaking remote speech.
* Off: remote speech is not spoken.

Tones and sounds from the remote system play in every speech mode.

The speech mode of NVDA on the server applies as well.
Remote speech is only spoken when both speech modes allow it.
For example, when speech is set to on-demand on the server and to talk on the client, the remote system only speaks on demand.

### Avaa vianmääritysraportti

Tämä painike avaa erillisen ikkunan, joka sisältää JSON-muotoisen tulosteen useista vianmäärityksistä, jotka voivat mahdollisesti auttaa virheenjäljityksessä.
Kun [teet vikailmoituksen GitHubissa][4], sinua saatetaan pyytää toimittamaan tämä raportti lisäosan tekijöille.

## Citrix-ohjeet

RDAccessin käytössä Citrix Workspace -sovelluksen kanssa on otettava huomioon joitakin tärkeitä seikkoja.

### Asiakaspuolen vaatimukset

1. Sovelluksen Windows Store -versiota ei tueta.
1. Kun olet asentanut Citrix Workspace -sovelluksen, sinun on käynnistettävä etäistunto kerran, jotta RDAccess voi rekisteröidä itsensä.
      Syynä tähän on se, että sovellus kopioi järjestelmän asetukset käyttäjän asetuksiin luodessaan istunnon ensimmäistä kertaa.
      Tämän jälkeen RDAccess voi rekisteröidä itsensä nykyiselle käyttäjälle.

### Palvelinpuolen vaatimus

In Citrix Virtual Apps and Desktops 2109, Citrix enabled the so-called virtual channel allow list, restricting third-party virtual channels, including the channel required by RDAccess, by default.
For more information, [see this Citrix blog post](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/).

RDAccessin vaatiman RdPipe-kanavan nimenomaista sallimista ei ole vielä testattu.
Tällä hetkellä todennäköisesti paras vaihtoehto on poistaa sallittujen luettelo kokonaan käytöstä.
Jos järjestelmäsi ylläpitäjä ei ole tyytyväinen tähän ratkaisuun, voit vapaasti [ilmoittaa siitä asialle omistetussa aiheessa][3].

## Ongelmat ja osallistuminen

Jos haluat ilmoittaa ongelmasta tai osallistua kehitykseen, tutustu [GitHubin Issues-sivuun][4].

## Ulkoiset osat

Tämä lisäosa on riippuvainen [RD Pipestä][5], Rust-ohjelmointikielellä kirjoitetusta kirjastosta, joka mahdollistaa etätyöpöytäasiakkaan tuen.
RD Pipeä jaetaan tämän lisäosan mukana Free Software Foundationin julkaiseman [GNU AGPL -lisenssin (versio 3)][6] ehtojen mukaisesti.

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess

[3]: https://github.com/leonardder/rdAccess/issues/1

[4]: https://github.com/leonardder/rdAccess/issues

[5]: https://github.com/leonardder/rd_pipe-rs

[6]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
