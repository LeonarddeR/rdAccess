# Remote Desktop Accessibility #

* Auteurs: [Leonard de Ruijter][1]
* Download [betaversie][2]
* NVDA compatibility: 2023.2 and later

The RDAccess add-on (Remote Desktop Accessibility) adds support to access
remote desktop sessions to NVDA using Microsoft Remote Desktop, Citrix or
VMware Horizon.  When installed in NVDA on both the client and the server,
speech and braille generated on the server will be spoken and brailled by
the client machine.  This enables a user experience where managing a remote
system feels just as performant as operating the local system.

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

## Aan de slag

1. Install RDAccess in both a client and server copy of NVDA.
1. Het beheerde systeem zou automatisch moeten werken met behulp van de
   lokale spraaksynthesizer. Als dit niet het geval is, selecteer je in de
   NVDA-kopie op de server de optie Externe Spraak in het
   NVDA-dialoogvenster voor synthesizerselectie.
1. Om braille te gebruiken, schakel je automatische detectie van
   brailleleesregels in met behulp van het selectievenster voor
   brailleleesregels.

## Problemen en bijdragen

Als je een probleem wilt melden of een bijdrage wilt leveren, kijk dan op
[de pagina met issues op Github][3] (Engelstalig). Als je de voorkeur geeft
aan Nederlands mag dat ook.

## Externe componenten

Deze add-on is afhankelijk van [RD Pipe][4], een library geschreven in Rust
die de basis vormt onder de ondersteuning voor remote desktop clients. RD
Pipe wordt aangeboden als onderdeel van deze add-on onder de voorwaarden van
[versie 3 van de GNU Affero General Public License][5] zoals gepubliceerd
door de Free Software Foundation.

[[!tag dev]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess-beta

[3]: https://github.com/leonardder/rdAccess/issues

[4]: https://github.com/leonardder/rd_pipe-rs

[5]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
