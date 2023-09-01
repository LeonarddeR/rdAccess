# Zugänglichkeit für Remote Desktop #

* Autor: [Leonard de Ruijter][1]
* [Letzte stabile Version herunterladen][2]
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

## Änderungsprotokoll

### Version 1.0

Erste stabile Version.

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

## Konfiguration

Nach der Installation kann RDAccess über den Einstellungen in NVDA konfiguriert (NVDA-Menü > Optionen > Einstellungen...) und aufgerufen werden.
Wählen Sie dann die Kategorie "Remote-Desktop" aus.

Dieses Dialogfeld enthält die folgenden Einstellungen:

### Zugänglichkeit für Remote Desktop aktivieren für

Diese Liste von Kontrollkästchen steuert den Betriebsmodus der
NVDA-Erweiterung. Sie können auswählen zwischen:

* Eingehende Verbindungen (Remote-Desktop-Server): Wählen Sie diese Option
  aus, wenn die aktuelle Instanz von NVDA auf einem Remote-Desktop-Server
  ausgeführt wird
* Ausgehende Verbindungen (Remote-Desktop-Client): Wählen Sie diese Option
  aus, wenn die aktuelle Instanz von NVDA auf einem Remote-Desktop-Client
  ausgeführt wird, der eine Verbindung zu einem oder mehreren Servern
  herstellt
* Durchreichen des geschützten Desktops: Wählen Sie diese Option aus, wenn
  Sie Braillezeile und Sprachausgabe von der Benutzerinstanz von NVDA beim
  Zugriff auf den geschützten Desktop verwenden möchten. Beachten Sie, dass
  Sie RDAccess auf dem geschützten Desktop der NVDA-Version verfügbar machen
  müssen, damit dies funktioniert. Wählen Sie dazu in den allgemeinen
  Einstellungen von NVDA die Option "Aktuell gespeicherte Einstellungen bei
  der Anmeldung und auf sicheren Bildschirmen verwenden (Administratorrechte
  erforderlich)" aus.

Um einen reibungslosen Start mit der NVDA-Erweiterung zu gewährleisten, sind
alle Optionen standardmäßig aktiviert. Wir empfehlen Ihnen jedoch, den
Server- oder Client-Modus zu deaktivieren.

### Automatische Wiederherstellung der Sprachausgabe auf dem Remote-System bei Verbindungsabbrüchen

Diese Option ist nur im Server-Modus verfügbar. Sie sorgt dafür, dass die
Verbindung automatisch wiederhergestellt wird, wenn die Sprachausgabe auf
dem Remote-System aktiv ist und die Verbindung unterbrochen wird. Das
Verhalten ist dem der automatischen Erkennung der Braillezeile sehr
ähnlich.  Damit wird auch klar, warum es eine solche Option nur für die
Sprachausgabe gibt. Die Wiederherstellung der Verbindung mit der
Braillezeile auf dem Remote-System erfolgt automatisch, wenn Sie die Option
"Automatisch" im Dialogfeld Auswahl der Braillezeile auswählen.

Diese Option ist standardmäßig aktiviert. Es wird dringend empfohlen, diese
Option aktiviert zu lassen, wenn der Remote-Desktop-Server keine
Audio-Ausgabe hat.

### Steuerung der Treiber-einstellungen durch ein Remote-System zulassen

Wenn diese Client-Option aktiviert ist, können Sie die Treiber-Einstellungen
(z. B. Stimme und Tonhöhe der Sprachausgabe) über das Remote-System
steuern. Dies ist besonders nützlich, wenn Sie bei der Steuerung eines
Remote-Systems Schwierigkeiten haben, auf das NVDA-Menü vom eigenen Computer
zuzugreifen.  Änderungen, die auf dem Remote-System vorgenommen werden,
werden automatisch lokal übernommen.

Obwohl die Aktivierung dieser Option eine gewisse Leistungsverschlechterung
mit sich bringt, sollten Sie sie dennoch aktivieren.  Wenn diese Option
deaktiviert ist, funktionieren die Änderungen für die Tonhöhe der
Sprachausgabe bei Großbuchstaben nicht.

### Client-Unterstützung beim Beenden von NVDA beibehalten

Diese Client-Option ist nur bei installierten NVDA-Versionen verfügbar. Wenn
sie aktiviert ist, stellt es sicher, dass der Client von NVDA in Ihrem
Remote-Desktop-Client geladen wird, auch wenn NVDA nicht ausgeführt wird.

Um den Client von RDAccess zu nutzen, müssen einige Änderungen in der
Windows-Registrierung vorgenommen werden. Die NVDA-Erweiterung sorgt dafür,
dass diese Änderungen unter dem Profil des aktuellen Benutzers vorgenommen
werden.  Für diese Änderungen sind keine administrativen Berechtigungen
erforderlich. Daher kann NVDA die erforderlichen Änderungen beim Laden
automatisch vornehmen und beim Beenden von NVDA rückgängig machen.  Dadurch
wird sichergestellt, dass die NVDA-Erweiterung vollständig mit portablen
NVDA-Versionen kompatibel ist.

Diese Option ist standardmäßig deaktiviert. Wenn Sie jedoch eine
installierte Version ausführen und der alleinige Benutzer an diesem Computer
sind, wird empfohlen, diese Option zu aktivieren. Dies gewährleistet einen
reibungslosen Betrieb, falls NVDA bei der Verbindung mit einem Remote-System
nicht aktiv ist und erst danach gestartet wird.

### Unterstützung für Microsoft Remote Desktop aktivieren

Diese Option ist standardmäßig aktiviert und stellt sicher, dass der Client
von RDAccess beim Starten von NVDA in den Microsoft Remote Desktop Client
(mstsc) geladen wird.  Diese Änderungen werden beim Beenden von NVDA
automatisch rückgängig gemacht, es sei denn, die persistente
Client-Unterstützung ist durch Aktivierung der vorherigen Option aktiviert.

### Unterstützung für Citrix Workspace aktivieren

Diese Option ist standardmäßig aktiviert und stellt sicher, dass der Client
von RDAccess beim Starten von NVDA in der App Citrix Workspace geladen
wird.  Diese Änderungen werden beim Beenden von NVDA automatisch rückgängig
gemacht, es sei denn, die persistente Client-Unterstützung ist durch
Aktivierung der vorherigen Option aktiviert.

Diese Option ist nur in den folgenden Fällen verfügbar:

* Citrix Workspace ist installiert. Beachten Sie, dass die Windows
  Store-Version der App aufgrund von Einschränkungen in dieser App selbst
  nicht unterstützt wird
* Es ist möglich, RDAccess unter dem aktuellen Benutzer zu
  registrieren. Nach der Installation der App müssen Sie einmalig eine
  Remote-Sitzung starten, damit dies möglich ist

## Citrix-spezifische Anweisungen

Bei der Verwendung von RDAccess mit der Citrix Workspace-App gibt es einige
wichtige Punkte zu beachten.

### Client-seitige Anforderungen

1. Die Variante aus dem Microsoft Store der App wird *nicht* unterstützt.
2. Nach der Installation von Citrix Workspace müssen Sie einmalig eine
   Remote-Sitzung starten, damit sich RDAccess selbst registrieren kann. Der
   Grund dafür ist, dass die Anwendung die Systemkonfiguration in die
   Benutzerkonfiguration kopiert, wenn sie zum ersten Mal eine Sitzung
   aufbaut. Danach kann sich RDAccess unter dem aktuellen Benutzerkontext
   registrieren.

### Server-seitige Anforderungen

In Citrix Virtual Apps und Desktops 2109 hat Citrix die so genannte "Virtual
Channel allow list" aktiviert. Dies bedeutet, dass virtuelle Kanäle von
Drittanbietern, einschließlich des von RDAccess benötigten Kanals,
standardmäßig nicht zugelassen sind. Weitere Informationen finden Sie [in
diesem
Citrix-Blogbeitrag](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/)

Das explizite Zulassen des Kanals von Rd Pipe, der für RDAccess erforderlich
ist, wurde noch nicht getestet. Im Moment ist es wahrscheinlich am besten,
die Zulassen-Liste ganz zu deaktivieren. Wenn Ihr Systemadministrator damit
nicht zufrieden sein sollte, können Sie [eine Nachricht in der
entsprechenden Ausgabe][3] hinterlassen.

## Themen und Beiträge

Wenn Sie ein Problem melden oder einen Beitrag leisten möchten, schauen Sie
sich [die Themen-Seite auf GitHub][3] an.

## Externe Komponenten

Diese NVDA-Erweiterung basiert auf [RD Pipe][4], eine in Rust geschriebene
Bibliothek, die den Remote-Desktop-Client unterstützt. RD Pipe wird als Teil
dieser NVDA-Erweiterung unter den Bedingungen der [Version 3 der GNU Affero
General Public License][5], wie sie von der Free Software Foundation
veröffentlicht wurde, weiterverteilt.

[[!tag stable dev beta]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess

[3]: https://github.com/leonardder/rdAccess/issues

[4]: https://github.com/leonardder/rd_pipe-rs

[5]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
