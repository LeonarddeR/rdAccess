# Zugänglichkeit von Remote Desktop #

* Autor: [Leonard de Ruijter][1]
* [Beta-Version herunterladen][2]
* NVDA-Kompatibilität: 2023.2 und neuer

Die NVDA-Erweiterung RDAccess (Remote Desktop Accessibility) bietet
Unterstützung für den Zugriff auf Remote-Desktop-Sitzungen mit NVDA über
Microsoft Remote Desktop, Citrix oder VMware Horizon. Wenn es in NVDA sowohl
auf dem Client als auch auf dem Server installiert ist, wird  auf dem Server
die Sprachausgabe und Braille-Schrift auf dem Client-Rechner ausgegeben und
mit der Braille-Schrift versehen. Dies ermöglicht eine Benutzererfahrung,
bei der die Verwaltung eines entfernten Systems genauso leistungsfähig ist
wie die Bedienung des lokalen Systems.

## Features

* Unterstützung für Microsoft Remote Desktop, Citrix und VMware Horizon
* Ausgabe via Sprachausgabe und Braille-Schrift
* Automatische Erkennung auf dem Remote-System von Braillezeilen mit Hilfe
  der automatischen Erkennung von Braillezeilen durch NVDA
* Automatische Erkennung der Sprachausgabe auf dem Remote-System mit Hilfe
  eines speziellen Erkennungsprozesses, der in den NVDA-Einstellungen
  deaktiviert werden kann
* Unterstützung für portable NVDA-Versionen auf einem Server (zusätzliche
  Konfiguration für Fitrix erforderlich)
* Vollständige Unterstützung für portable NVDA-Versionen auf einem Client
  (keine zusätzlichen administrativen Berechtigungen für die Installation
  der NVDA-Erweiterung erforderlich)
* Mehrere parallellaufende aktive Client-Sitzungen
* Remote Desktop sofort nach NVDA-Start verfügbar
* Möglichkeit, bestimmte Einstellungen der Sprachausgabe und der
  Braillezeile zu steuern, ohne die Remote-Sitzung zu verlassen
* Möglichkeit der Nutzung von Sprachausgabe und Braille-Schrift aus der
  Benutzersitzung heraus beim Zugriff auf geschützte Desktops

## Erste Schritte

1. Installieren Sie RDAccess in einer NVDA-Version sowohl in einer Client-
   als auch in einer Server-Umgebung.
1. Das Remote-System sollte automatisch mit der lokalen Sprachausgabe
   beginnen zu sprechen. Wenn dies nicht der Fall ist, wählen Sie dort in
   der NVDA-Instanz auf dem Server die Sprachausgabe aus dem Dialogfeld zur
   Auswahl der Sprachausgaben in NVDA aus.
1. Um die Braille-Unterstützung zu verwenden, aktivieren Sie die
   automatische Erkennung der Braillezeile im Dialogfeld zur Auswahl der
   Braillezeilen.

## Themen und Beiträge

Wenn Sie ein Problem melden oder einen Beitrag leisten möchten, schauen Sie
sich [die Themen-Seite auf GitHub][3] an.

## Externe Komponenten

Diese NVDA-Erweiterung stützt sich auf [RD Pipe][4], eine in Rust
geschriebene Bibliothek, die den Remote-Desktop-Client unterstützt. RD Pipe
wird als Teil dieser NVDA-Erweiterung unter den Bedingungen der [Version 3
der GNU Affero General Public License][5], wie sie von der Free Software
Foundation veröffentlicht wurde, weiterverteilt.

[[!tag dev]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess-beta

[3]: https://github.com/leonardder/rdAccess/issues

[4]: https://github.com/leonardder/rd_pipe-rs

[5]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
