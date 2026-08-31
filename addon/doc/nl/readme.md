# RDAccess: Toegankelijkheid van extern bureaublad

* Auteurs: [Leonard de Ruijter][1]
* Download de [nieuwste stabiele versie][2]
* NVDA-compatibiliteit: 2026.1 en nieuwer

De RDAccess-add-on (Toegankelijkheid van extern bureaublad) voegt ondersteuning toe aan NVDA voor externe sessies via Microsoft Remote Desktop, Citrix, Parallels RAS of VMware Horizon.
Wanneer de add-on in NVDA op zowel de client als de server is geïnstalleerd, worden spraak en braille die op de server worden gegenereerd, uitgesproken en in braille weergegeven op de clientcomputer.
Dit maakt een gebruikerservaring mogelijk waarbij het beheren van een systeem op afstand net zo vlot aanvoelt als het bedienen van het lokale systeem.

## Functies

* Ondersteuning voor Microsoft Remote Desktop (inclusief Azure Virtual Desktop en Microsoft Cloud PC), Citrix, Parallels RAS en VMware Horizon
* Spraak- en braille-uitvoer
* Automatische detectie van extern braille met NVDA's automatische detectie van brailleleesregels
* Automatische detectie van externe spraak met behulp van een speciaal detectieproces dat kan worden uitgeschakeld in het instellingendialoogvenster van NVDA
* Ondersteuning voor draagbare kopieën van NVDA die op een server draaien (aanvullende configuratie vereist voor Citrix)
* Volledige ondersteuning voor draagbare kopieën van NVDA die op een client draaien (geen extra administratieve rechten vereist om de add-on te installeren)
* Meerdere actieve clientsessies tegelijkertijd
* Extern bureaublad direct beschikbaar na het opstarten van NVDA
* Mogelijkheid om specifieke synthesizer- en brailleleesregelinstellingen te bedienen zonder de externe sessie te verlaten

## Wijzigingen

### Version 2.0.3

* Caps lock synchronization on the client now relies on NVDA 2026.3, which lets RDAccess tell caps lock presses fed back by the remote desktop client apart from real key presses. Synchronization therefore also works when the session is not full screen but Windows key combinations are applied on the remote computer, and when the NVDA setting "Handle keys from other applications" is disabled. The client side of the synchronization requires NVDA 2026.3 or later and is no longer available on older versions of NVDA; the server side keeps working on every supported version.

### Version 2.0.2

* Fixed caps lock going out of sync between the client and the server when both NVDA instances use caps lock as an NVDA modifier key. Quickly repeated caps lock presses in a full screen session no longer toggle caps lock on the client, and when caps lock is really toggled within the session, the client now follows as soon as the session loses focus. This behavior is controlled by the new setting "Synchronize the caps lock key between client and server", which is enabled by default and needs to be enabled on both the client and the server to work correctly. Note that with the setting "Handle keys from other applications" disabled on the client, caps lock can still get out of sync.

### Versie 2.0.1

* Wanneer externe spraak automatisch wordt ingeschakeld, blijft deze nu werken na het wisselen van configuratieprofiel. Voorheen viel NVDA, zodra een profiel werd geactiveerd, terug op de synthesizer die je hebt geconfigureerd. Dit gebeurde bijvoorbeeld wanneer je naar een toepassing met een eigen profiel ging.
* De optie "Externe spraak automatisch herstellen na verbindingsverlies" is hernoemd naar "Automatisch overschakelen naar externe spraak wanneer beschikbaar", wat beter beschrijft wat deze doet.
* Veelvuldige fouten op het externe systeem opgelost wanneer automatisch wisselen van taal was ingeschakeld bij gebruik van de externe synthesizer. Het melden van niet-ondersteunde talen is nu gebaseerd op de talen die de spraaksynthesizer op de client ondersteunt.
* Op ARM64-versies van Windows kunnen clients voor extern bureaublad die onder x64-emulatie draaien nu RDAccess gebruiken.
* Aangepast aan de wijzigingen in braille-invoer die in NVDA 2026.3 zijn geïntroduceerd.

### Versie 2.0

* Spraak en braille die van het externe systeem komen, worden nu sneller gepresenteerd, waardoor werken in een externe sessie vlotter aanvoelt.
* Bij het starten van NVDA op een externe server wordt braille nu weergegeven zodra een externe sessie verbinding maakt, in plaats van pas na de eerste toetsaanslag of focuswijziging.
* Een vastloper opgelost bij het wegschakelen van de externe synthesizer of brailleleesregel terwijl de verbinding van een sessie werd verbroken.
* RDAccess wisselt spraak en braille nu uit via een nieuw protocol dat is gebaseerd op het protocol van NVDA's ingebouwde externe toegang. Het is robuuster en is niet langer afhankelijk van het pickle-formaat, dat door een gecompromitteerd extern systeem misbruikt zou kunnen worden. De protocolversie wordt automatisch gekozen, zodat een client en een server met verschillende versies van RDAccess nog steeds samenwerken.
* De minimaal compatibele NVDA-versie is nu 2026.1. Ondersteuning voor eerdere versies is verwijderd.
* Aangepast aan de braillewijzigingen die in NVDA 2026.3 zijn geïntroduceerd.
* De RD Pipe-afhankelijkheid is bijgewerkt naar versie 0.9.0.
* RDAccess valt nu onder de GNU General Public License versie 2 of later.

### Versie 1.7.1

* Hopelijk een fout in rd_pipe opgelost waardoor het verkeerde virtuele kanaal werd aangemaakt.

### Versie 1.7

* Ondersteuning voor beveiligd bureaublad verwijderd.
* Een clientoptie "Percentage toonhoogteverandering voor binnenkomende spraak" toegevoegd om de toonhoogte van spraak afkomstig van een externe NVDA te veranderen, zodat externe en lokale spraak hoorbaar van elkaar te onderscheiden zijn.

### Versie 1.6

* Ondersteuning voor Parallels RAS gedocumenteerd en verbeterd.
* De minimaal compatibele NVDA-versie is nu 2025.1. Ondersteuning voor eerdere versies is verwijderd.
* De RdPipe-afhankelijkheid is bijgewerkt.
* De mogelijkheid toegevoegd om het RdPipe-logniveau in te stellen.
* Een lezer voor het RdPipe-logboek toegevoegd, beschikbaar vanuit het instellingenpaneel.
* Verbeterd gedrag bij het verwijderen van de add-on (er worden geen fouten meer weergegeven en de Citrix-ondersteuning wordt niet meer verwijderd wanneer Citrix niet beschikbaar is).

### Versie 1.5

* De mogelijkheid toegevoegd om een diagnostisch rapport voor foutopsporing te maken via een knop in het RDAccess-instellingenpaneel [#23](https://github.com/leonardder/rdAccess/pull/23).
* Ondersteuning voor brailleleesregels met meerdere regels in NVDA 2025.1 en nieuwer [#19](https://github.com/leonardder/rdAccess/pull/13).
* De minimaal compatibele NVDA-versie is nu 2024.1. Ondersteuning voor eerdere versies is verwijderd.
* Notificaties voor clientverbindingen toegevoegd [#25](https://github.com/leonardder/rdAccess/pull/25).
* De RdPipe-afhankelijkheid is bijgewerkt.
* Vertalingen bijgewerkt.

### Versie 1.4

* Nieuwe stabiele versie.

### Versie 1.3

* Niet-werkende invoerhandelingen van brailleleesregels opgelost.

### Versie 1.2

* [Ruff](https://github.com/astral-sh/ruff) wordt gebruikt als formatter en linter. [#13](https://github.com/leonardder/rdAccess/pull/13).
* Een probleem opgelost waarbij NVDA op de client een fout gaf bij het pauzeren van spraak op de server.
* Ondersteuning voor `winAPI.secureDesktop.post_secureDesktopStateChange` gerepareerd.
* Verbeterde initialisatie van drivers op de server.

### Versie 1.1

* Ondersteuning toegevoegd voor registratie voor automatische detectie van brailleleesregels in de stijl van NVDA 2023.3. [#11](https://github.com/leonardder/rdAccess/pull/11).
* Ondersteuning toegevoegd voor het extension point `winAPI.secureDesktop.post_secureDesktopStateChange` van NVDA 2024.1 Alpha. [#12](https://github.com/leonardder/rdAccess/pull/12).

### Versie 1.0

Eerste stabiele versie.

## Aan de slag

1. Installeer RDAccess in zowel een client- als een serverkopie van NVDA.
1. Het externe systeem zou automatisch moeten beginnen te spreken via de lokale spraaksynthesizer.
      Als dit niet het geval is, selecteer je in het NVDA-exemplaar op de server de synthesizer Externe spraak in het NVDA-dialoogvenster voor synthesizerselectie.
1. Om braille te gebruiken, schakel je automatische detectie van brailleleesregels in met behulp van het selectievenster voor brailleleesregels.

## Configuratie

Na installatie kan de RDAccess-add-on worden geconfigureerd via het instellingendialoogvenster van NVDA, dat je opent vanuit het NVDA-menu via Opties > Instellingen...
Kies vervolgens de categorie Extern bureaublad.

Dit dialoogvenster bevat de volgende instellingen:

### Toegankelijkheid van extern bureaublad inschakelen voor

Deze lijst met selectievakjes bepaalt de werkingsmodus van de add-on.
Kies uit:

* Inkomende verbindingen (Remote Desktop Server): Kies deze optie als het huidige exemplaar van NVDA draait op een server voor extern bureaublad.
* Uitgaande verbindingen (Remote Desktop Client): Kies deze optie als het huidige exemplaar van NVDA draait op een client voor extern bureaublad die verbinding maakt met een of meer servers.

Om een vlotte start met de add-on te garanderen, zijn alle opties standaard ingeschakeld.
Je wordt echter aangemoedigd om de server- of clientmodus uit te schakelen waar dat van toepassing is.

### Synchroniseer de Caps Lock-toets tussen client en server

When both the client and the server run NVDA with caps lock as an NVDA modifier key, the caps lock state can get out of sync, since the remote desktop client feeds caps lock presses back into the client system whenever it captures the keyboard, for example in a full screen session.
When this option is enabled on the client, these fed back caps lock presses no longer toggle caps lock on the client.
Wanneer deze optie op de server is ingeschakeld, meldt de server zijn Caps Lock-status aan de client, die deze toepast zodra de externe sessie de focus verliest.
Voor een correcte werking moet deze optie op zowel de client als de server zijn ingeschakeld; standaard is dat op beide het geval.
On the client, this option requires NVDA 2026.3 or later; the server side works with every NVDA version supported by the add-on.

Note that while a remote desktop session window has focus, caps lock presses sent by other software, such as NVDA Remote Access, are suppressed on the client as well.

### Automatisch overschakelen naar externe spraak wanneer beschikbaar

Deze optie is alleen beschikbaar in de servermodus.
Deze zorgt ervoor dat Externe spraak wordt geactiveerd zodra een client voor extern bureaublad deze aanbiedt, vergelijkbaar met de automatische detectie van brailleleesregels, en dat de verbinding automatisch wordt hersteld wanneer deze wordt verbroken.
Zolang Externe spraak op deze manier actief is, blijft je geconfigureerde synthesizer onaangeroerd en valt NVDA er bij het wisselen van configuratieprofiel niet langer op terug.

Deze optie is standaard ingeschakeld.
Je wordt sterk aangeraden deze optie ingeschakeld te laten als de server voor extern bureaublad geen audio-uitvoer heeft.

### Extern systeem toestaan om instellingen van driver te bedienen

Wanneer deze optie op de client is ingeschakeld, kun je driverinstellingen (zoals de stem en toonhoogte van de synthesizer) bedienen vanaf het externe systeem.
Wijzigingen die op het externe systeem worden gemaakt, worden automatisch lokaal doorgevoerd.

### Client-ondersteuning behouden bij afsluiten NVDA

Deze clientoptie, beschikbaar op geïnstalleerde exemplaren van NVDA, zorgt ervoor dat het clientgedeelte van NVDA wordt geladen in je client voor extern bureaublad, zelfs wanneer NVDA niet actief is.

Om het clientgedeelte van RDAccess te gebruiken, moeten er wijzigingen worden aangebracht in het Windows-register.
De add-on zorgt ervoor dat deze wijzigingen worden aangebracht onder het profiel van de huidige gebruiker, waarvoor geen administratieve rechten nodig zijn.
Daardoor kan NVDA de benodigde wijzigingen automatisch toepassen bij het laden en ze weer ongedaan maken bij het afsluiten van NVDA, wat compatibiliteit met draagbare versies van NVDA garandeert.

Deze optie is standaard uitgeschakeld.
Als je echter een geïnstalleerde kopie gebruikt en de enige gebruiker van het systeem bent, wordt aangeraden deze optie in te schakelen voor een vlotte werking bij het verbinden met een extern systeem nadat NVDA is gestart.

### Standaardondersteuning voor extern bureaublad inschakelen

Deze optie, standaard ingeschakeld, zorgt ervoor dat het clientgedeelte van RDAccess wordt geladen in de Microsoft Remote Desktop-client (mstsc) bij het starten van NVDA.
Dit is ook vereist voor VMware Horizon, Parallels RAS, Azure Virtual Desktop, enz.
Wijzigingen die via deze optie worden gemaakt, worden bij het afsluiten van NVDA automatisch ongedaan gemaakt, tenzij het behouden van clientondersteuning is ingeschakeld.

### Ondersteuning voor Citrix Workspace inschakelen

Deze optie, standaard ingeschakeld, zorgt ervoor dat het clientgedeelte van RDAccess wordt geladen in de Citrix Workspace-app bij het starten van NVDA.
Wijzigingen die via deze optie worden gemaakt, worden bij het afsluiten van NVDA automatisch ongedaan gemaakt, tenzij het behouden van clientondersteuning is ingeschakeld.

Deze optie is alleen beschikbaar onder de volgende voorwaarden:

* Citrix Workspace is geïnstalleerd.
    Merk op dat de Windows Store-versie van de app niet wordt ondersteund vanwege beperkingen in de app zelf.
* Het is mogelijk om RDAccess te registreren onder de huidige gebruikerscontext.
    Na installatie van de app moet je eenmalig een externe sessie starten om dit mogelijk te maken.

### Verbindingswijzigingen melden met

Met deze vervolgkeuzelijst bepaal je welke meldingen je ontvangt wanneer een extern systeem de verbinding voor externe spraak of braille opent of sluit.
Je kunt kiezen uit:

* Uit (geen meldingen)
* Berichten (bijv. "Extern braille verbonden")
* Sounds
* Zowel berichten als geluiden

### Percentage toonhoogteverandering voor binnenkomende spraak

Deze clientoptie verandert de toonhoogte van spraak die lokaal wordt weergegeven wanneer deze afkomstig is van een externe NVDA, zodat externe en lokale spraak hoorbaar van elkaar te onderscheiden zijn.

De waarde is een percentage tussen -100 en 100.
Positieve waarden verhogen de toonhoogte, negatieve waarden verlagen deze.
Een waarde van 0 schakelt de verandering uit.
De standaardwaarde is 10.

De verandering wordt alleen toegepast wanneer de lokale synthesizer toonhoogte-opdrachten ondersteunt; synthesizers zonder ondersteuning voor toonhoogte worden niet beïnvloed.

### Diagnostisch rapport openen

Deze knop opent een scherm in bladermodus met JSON-uitvoer die verschillende diagnostische gegevens bevat die mogelijk kunnen helpen bij het opsporen van fouten.
Bij het [melden van een probleem op GitHub][4] kan je worden gevraagd dit rapport aan te leveren.

## Citrix-specifieke instructies

Er zijn enkele belangrijke aandachtspunten bij het gebruik van RDAccess met de Citrix Workspace-app:

### Vereisten aan de clientzijde

1. De Windows Store-variant van de app wordt *niet* ondersteund.
1. Na installatie van Citrix Workspace moet je eenmalig een externe sessie starten om RDAccess zichzelf te laten registreren.
      Dit komt doordat de applicatie de systeeminstellingen naar de gebruikersinstellingen kopieert bij het opzetten van de eerste sessie.
      Daarna kan RDAccess zichzelf registreren onder de huidige gebruikerscontext.

### Vereiste aan de serverzijde

In Citrix Virtual Apps and Desktops 2109 heeft Citrix de zogenaamde virtual channel allow list ingeschakeld, waardoor virtuele kanalen van derden, inclusief het door RDAccess vereiste kanaal, standaard worden geblokkeerd.
Voor meer informatie, [zie dit Citrix-blogbericht](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/).

Het expliciet toestaan van het door RDAccess vereiste RdPipe-kanaal is nog niet getest.
Voor nu is het het beste om de acceptatielijst helemaal uit te schakelen.
Als je systeembeheerder hier bezwaren tegen heeft, [kaart het dan hier aan][3].

## Problemen en bijdragen

Om een probleem te melden of een bijdrage te leveren, kijk je op [de pagina met issues op Github][4].

## Externe componenten

Deze add-on maakt gebruik van [RD Pipe][5], een in Rust geschreven bibliotheek die de ondersteuning voor clients voor extern bureaublad mogelijk maakt.
RD Pipe wordt als onderdeel van deze add-on verspreid onder de voorwaarden van [versie 3 van de GNU Affero General Public License][6].

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess

[3]: https://github.com/leonardder/rdAccess/issues/1

[4]: https://github.com/leonardder/rdAccess/issues

[5]: https://github.com/leonardder/rd_pipe-rs

[6]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
