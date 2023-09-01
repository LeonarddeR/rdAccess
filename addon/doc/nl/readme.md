# Toegankelijkheid van extern bureaublad #

* Auteurs: [Leonard de Ruijter][1]
* Download [latest stable version][2]
* NVDA-compatibiliteit: 2023.2 en later

De RDAccess-add-on (Toegankelijkheid van extern bureaublad) voegt
ondersteuning toe voor toegang tot externe bureaubladsessies bij gebruik van
Microsoft Remote Desktop, Citrix of VMware Horizon. Wanneer geïnstalleerd in
NVDA op zowel de client als de server, worden spraak en braille die op de
server worden gegenereerd, uitgesproken en in braille weergegeven op de
clientcomputer. Dit maakt een gebruikerservaring mogelijk waarbij het beheer
van een systeem op afstand net zo vlot aanvoelt als het bedienen van het
lokale systeem.

## Functies

* Ondersteuning voor Microsoft Remote Desktop, Citrix en VMware Horizon
* Spraak- en braille-uitvoer
* Automatische detectie van extern braille met NVDA's automatische detectie
  van brailleleesregels
* Automatische detectie van externe spraak met behulp van een speciaal
  detectieproces dat kan worden uitgeschakeld in het
  instellingendialoogvenster van NVDA
* Ondersteuning voor draagbare kopieën van NVDA die op een server draaien
  (aanvullende configuratie vereist voor Fitrix)
* Volledige ondersteuning voor draagbare kopieën van NVDA die op een client
  draaien (geen extra administratieve rechten vereist om de add-on te
  installeren)
* Meerdere actieve cliëntsessies tegelijkertijd
* Extern bureaublad direct beschikbaar na het opstarten van NVDA
* Mogelijkheid om specifieke synthesizer- en brailleleesregelinstellingen te
  bedienen zonder de externe sessie te verlaten
* Mogelijkheid om de spraaksynthesizer en brailleleesregel van de ingelogde
  gebruiker te gebruiken op beveiligde bureaubladen

## Changelog

### Version 1.0

Initial stable release.

## Aan de slag

1. Installeer RDAccess in zowel een client- als een serverkopie van NVDA.
1. Het beheerde systeem zou automatisch moeten werken met behulp van de
   lokale spraaksynthesizer. Als dit niet het geval is, selecteer je in de
   NVDA-kopie op de server de optie Externe Spraak in het
   NVDA-dialoogvenster voor synthesizerselectie.
1. Om braille te gebruiken, schakel je automatische detectie van
   brailleleesregels in met behulp van het selectievenster voor
   brailleleesregels.

## Configuratie

After installation, the RDAccess add-on can be configured using NVDA's settings dialog, which can be accessed from the NVDA Menu by choosing Preferences > Settings...
After that, choose the Remote Desktop category.

Dit dialoogvenster bevat de volgende instellingen:

### Enable remote desktop accessibility for

This list of check boxes controls the operating mode of the add-on. You can
choose between:

* Inkomende verbindingen (Remote Desktop Server): Kies deze optie als het
  huidige exemplaar van NVDA draait op een remote desktop server
* Uitgaande verbindingen (Remote Desktop Client): Kies deze optie als het
  huidige exemplaar van NVDA draait op een remote desktop-client die
  verbinding maakt met een of meer servers
* Secure Desktop pass through: : Choose this option if you want to use
  braille and speech from the user instance of NVDA when accessing the
  secure desktop. Note that for this to work, you need to make the RDAccess
  add-on available on the secure desktop copy of NVDA. For this, choose "Use
  currently saved settings during sign-in and on secure screens (requires
  administrator privileges)" in NVDA's general settings.

Om een ​​vlotte start met de add-on te garanderen, zijn alle opties
standaard ingeschakeld. Je wordt echter aangemoedigd om de server- of
clientmodus uit te schakelen.

### Externe spraak automatisch herstellen na verbindingsverlies

Deze optie is alleen beschikbaar in de servermodus. Het zorgt ervoor dat de
verbinding automatisch wordt hersteld wanneer de Externe Spraak synthesizer
actief is en de verbinding wordt verbroken. Het gedrag lijkt sterk op dat
van automatische detectie van brailleleesregels. Dit verduidelijkt ook
waarom er alleen zo'n optie voor spraak is. Het opnieuw verbinden van de
Extern Braille wordt automatisch afgehandeld wanneer je de optie Automatisch
kiest in het dialoogvenster voor brailleleesregelselectie.

Deze optie is standaard ingeschakeld. Je wordt sterk aangeraden deze optie
ingeschakeld te laten als de Remote Desktop-server geen audio-uitvoer heeft.

### Extern systeem toestaan om instellingen van driver te bedienen

This client option, when enabled, allows you to control driver settings
(such as synthesizer voice and pitch) from the remote system.  This is
especially useful when you have difficulties accessing the local NVDA menu
when controlling a remote system.  Changes performed on the remote system
will automatically be reflected locally.

While enabling this option implies some performance degradation, you are yet
advised to enable it.  When this option is disabled, speech synthesizer
ppitch changes for capitals don't work.

### Client-ondersteuning behouden bij afsluiten NVDA

Deze clientoptie is alleen beschikbaar op geïnstalleerde exemplaren van
NVDA. Indien ingeschakeld, zorgt het ervoor dat het clientgedeelte van NVDA
wordt geladen in je remote desktop-client, zelfs wanneer NVDA niet actief
is.

To use the client portion of RDAccess, several changes have to be maede in
the Windows Registry.  The add-on ensures that these changes are made under
the profile of the current user.  These changes don't require administrative
privileges.  Therefore, NVDA can automatically apply the necessary changes
when loaded, and undo these changes when exiting NVDA.  This ensures that
the add-on is fully compatible with portable versions of NVDA.

This option is disabled by default.  However, if you are running an
installed copy and you are the only user of the system, you are advised to
enable this option.  This ensures smooth operation in case NVDA is not
active when connecting to a remote system and is then started afterwards.

### Ondersteuning voor Microsoft Remote Desktop inschakelen

Deze optie is standaard ingeschakeld en zorgt ervoor dat het clientgedeelte
van RDAccess wordt geladen in de Microsoft Remote Desktop-client (mstsc) bij
het starten van NVDA. Tenzij clientondersteuning behouden is ingeschakeld
door de vorige optie in te schakelen, worden deze wijzigingen automatisch
ongedaan gemaakt bij het afsluiten van NVDA.

### Ondersteuning voor Citrix Workspace inschakelen

Deze optie is standaard ingeschakeld en zorgt ervoor dat het clientgedeelte
van RDAccess wordt geladen in de Citrix Workspace-app bij het opstarten van
NVDA. Tenzij clientondersteuning behouden is ingeschakeld door de vorige
optie in te schakelen, worden deze wijzigingen automatisch ongedaan gemaakt
bij het afsluiten van NVDA.

Deze optie is alleen beschikbaar in de volgende gevallen:

* Citrix Workspace is geïnstalleerd. Merk op dat de Windows Store-versie van
  de app niet wordt ondersteund vanwege beperkingen in die app zelf
* Het is mogelijk om RDAccess te registreren onder de huidige
  gebruikerscontext. Na installatie van de app moet je eenmalig een externe
  sessie starten om dit mogelijk te maken

## Citrix-specifieke instructies

Er zijn enkele belangrijke aandachtspunten bij het gebruik van RDAccess met
de Citrix Workspace app.

### Vereisten aan de client-zijde

1. De Windows Store-variant van de app wordt *niet* ondersteund.
2. Na installatie van Citrix Workspace moet je eenmalig een externe sessie
   starten om RDAccess zichzelf te laten registreren. De reden hierachter is
   dat de applicatie de systeemconfiguratie naar de gebruikersconfiguratie
   kopieert wanneer deze voor de eerste keer een sessie tot stand
   brengt. Daarna kan RDAccess zichzelf registreren onder de huidige
   gebruikerscontext.

### Vereisten aan de serverzijde

In Citrix Virtual Apps and Desktops 2109 heeft Citrix de zogenaamde virtual
channel allow list ingeschakeld. Dit betekent dat virtuele kanalen (virtual
channels) van derden, inclusief het door RDAccess vereiste kanaal, standaard
niet zijn toegestaan. Voor meer informatie, [zie dit
Citrix-blogbericht](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/)

Het expliciet toestaan ​​van het door RDAccess vereiste RdPipe-kanaal is nog
niet getest. Voor nu is het waarschijnlijk de beste keuze om de
acceptatielijst helemaal uit te schakelen. Als uw systeembeheerder hier niet
blij mee is, [geef dan een seintje in het daarvoor bestemde issue][3]

## Problemen en bijdragen

Als je een probleem wilt melden of een bijdrage wilt leveren, kijk dan op
[de pagina met issues op Github][3] (Engelstalig). Als je de voorkeur geeft
aan Nederlands mag dat ook.

## Externe componenten

This add-on relies on [RD Pipe][4], a library written in Rust backing the
remote desktop client support.  RD Pipe is redistributed as part of this
add-on under the terms of [version 3 of the GNU Affero General Public
License][5] as published by the Free Software Foundation.

[[!tag stable dev beta]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess

[3]: https://github.com/leonardder/rdAccess/issues

[4]: https://github.com/leonardder/rd_pipe-rs

[5]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
