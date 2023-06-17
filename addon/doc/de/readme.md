# NVDA Remote Desktop #

* Autor: [Leonard de Ruijter][1]
* [Beta-Version herunterladen][2]
* NVDA-Kompatibilität: 2023.1 und neuer

Diese NVDA-Erweiterung bietet Unterstützung für den Zugriff auf
Remote-Desktop-Sitzungen mit NVDA über Microsoft Remote Desktop, Citrix oder
VMware Horizon.  Wenn NVDA sowohl auf dem Client als auch auf dem Server
installiert ist, wird die auf dem Server erzeugte Sprachausgabe und
Braille-Schrift auf dem Client mitgeteilt. Damit wird die Verwaltung eines
Remote-Systems genauso leistungsstark wie die Bedienung eines lokalen
Systems.

## Features

* Unterstützung für Microsoft Remote Desktop, Citrix und VMware Horizon
* Ausgabe via Sprachausgabe und Braille
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
* Mehrere aktive Client-Sitzungen zur gleichen Zeit
* Remote-Desktop sofort nach NVDA-Start verfügbar
* Möglichkeit, bestimmte Einstellungen der Sprachausgabe und der
  Braillezeile zu steuern, ohne die Remote-Sitzung zu verlassen
* Möglichkeit der Nutzung von Sprachausgabe und Braille aus der
  Benutzersitzung heraus beim Zugriff auf geschützte Desktops

## Einstieg

1. Installieren Sie diese NVDA-Erweiterung sowohl in einer Client- als auch
   in einer Server-Umgebung mit NVDA.
1. Das Remote-System sollte automatisch mit der lokalen Sprachausgabe
   beginnen zu sprechen. Wenn dies nicht der Fall ist, wählen Sie dort in
   der NVDA-Instanz auf dem Server die Sprachausgabe aus dem NVDA-Dialogfeld
   zur Auswahl der Sprachausgaben aus.
1. Um Braille zu verwenden, aktivieren Sie die automatische Erkennung der
   Braillezeile im Dialogfeld zur Auswahl der Braillezeilen.

## Probleme und Beiträge

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

[2]: https://www.nvaccess.org/addonStore/legacy?file=nvdaRd-beta

[3]: https://github.com/leonardder/nvdaRd/issues

[4]: https://github.com/leonardder/rd_pipe-rs

[5]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
