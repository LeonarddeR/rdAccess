# NVDA Remote Desktop #

* Auteurs: [Leonard de Ruijter][1]
* Download [betaversie][2]
* NVDA-compatibiliteit: 2023.1 en later

Deze add-on voegt ondersteuning toe voor toegang tot externe
bureaubladsessies bij gebruik van Microsoft Remote Desktop, Citrix of VMware
Horizon. Wanneer geïnstalleerd in NVDA op zowel de client als de server,
worden spraak en braille die op de server worden gegenereerd, uitgesproken
en in braille weergegeven op de clientcomputer. Dit maakt een
gebruikerservaring mogelijk waarbij het beheer van een systeem op afstand
net zo vlot aanvoelt als het bedienen van het lokale systeem.

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

1. Installeer deze add-on in zowel een client- als een serverkopie van NVDA.
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

[2]: https://www.nvaccess.org/addonStore/legacy?file=nvdaRd-beta

[3]: https://github.com/leonardder/nvdaRd/issues

[4]: https://github.com/leonardder/rd_pipe-rs

[5]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
