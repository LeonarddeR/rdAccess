# Remote Desktop Accessibility #

* Auteurs:  [Leonard de Ruijter][1]
* Télécharger [dernière version béta][2]
* Compatibilité NVDA : 2023.2 et plus

L'extension RDAccess (Remote Desktop Accessibility) ajoute une prise en
charge pour accéder aux sessions de bureau à distance à NVDA en utilisant
Microsoft Remote Desktop, Citrix ou VMware Horizon. Lorsqu'il est installé
dans NVDA sur le client et le serveur, la parole et le braille générées sur
le serveur seront verbalisées et braillées par la machine client. Cela
permet une expérience utilisateur où la gestion d'un système distant semble
tout aussi performante que le fonctionnement du système local.

## Caractéristiques

* Prise en charge de Microsoft Remote Desktop, Citrix et VMware Horizon
* Sortie de la parole et du braille
* Détection automatique du braille distant en utilisant la détection
  automatique de l'afficheur braille de NVDA
* Détection automatique de la parole distante en utilisant un processus de
  détection dédié qui peut être désactivé dans le dialogue des paramètres de
  NVDA
* Prise en charge des copies portables de NVDA fonctionnant sur un serveur
  (configuration supplémentaire requise pour Fitrix)
* Prise en charge complète pour les copies portables de NVDA fonctionnant
  sur un client (aucun privilège administratif supplémentaire requis pour
  installer l'extension)
* Plusieurs sessions de clients actives en même temps
* Remote desktop instantanément disponible après le démarrage de NVDA
* Possibilité à contrôler les paramètres du synthétiseur et l'afficheur
  braille spécifiques sans quitter la session distante
* Possibilité d'utiliser la parole et le braille de la session utilisateur
  lors de l'accès à des bureaux sécurisés

## Premiers pas

1. Installez RDAccess à la fois dans le client et serveur de la copie de
   NVDA.
1. Le système distant doit commencer automatiquement à parler en utilisant
   le synthétiseur de la parole local. Sinon, dans l'instance NVDA sur le
   serveur, sélectionnez le synthétiseur de la parole à distance dans le
   dialogue Sélection du synthétiseur de NVDA.
1. Pour utiliser le braille, activez la détection automatique de l'afficheur
   braille en utilisant le dialogue de sélection de l'afficheur braille.

## Configuration

Après l'installation, l'extension rdAccess peut être configurée à l'aide de la boîte de dialogue Paramètres de NVDA, accessible à partir du menu de NVDA en choisissant Préférences > Paramètres...
Après cela, choisissez la catégorie Bureau distant.

Cette boîte de dialogue contient les paramètres suivants :

### Activer remote desktop accessibility pour

Cette liste des boutons de cases à cocher contrôle le mode de fonctionnement
de l'extension. Vous pouvez choisir entre :

* Connexions entrantes (Remote Desktop Server) : Choisissez cette option si
  l'instance actuelle de NVDA s'exécute sur un serveur de bureau distant

* Connexions sortantes (Remote Desktop Client) : Choisissez cette option si
  l'instance actuelle de NVDA s'exécute sur un client de bureau distant qui
  se connecte à un ou plusieurs serveurs

* Passerelle Secure Desktop : Choisissez cette option si vous souhaitez
  utiliser le braille et la parole dans l'instance utilisateur de NVDA lors
  de l'accès au bureau distant. Notez que pour que cela fonctionne, vous
  devez rendre l'extension RDAccess disponible sur le bureau Sécurisé de la
  copie de NVDA. Pour cela, choisissez "Utiliser les paramètres NVDA
  actuellement sauvegardés pour l'écran de connexion et sur les écrans
  sécurisés (nécessite des privilèges administrateur)" dans les paramètres
  Général de NVDA.

Pour assurer un démarrage en douceur avec l'extension, toutes les options
sont activées par défaut. Vous êtes cependant encouragé à désactiver le
serveur ou le mode client, le cas échéant.

### Récupérer automatiquement la parole à distance après une perte de connexion

Cette option n'est disponible qu'en mode serveur. Il garantit que la
connexion sera automatiquement rétablie lorsque le synthétiseur de la parole
à distance  est actif et que la connexion est perdue. Le comportement est
très similaire à celui de la détection automatique de l'afficheur
braille. Cela clarifie également pourquoi il n'y a qu'une telle option de la
parole. La reconnexion de l'afficheur braille distant est automatiquement
gérée lors du choix de l'option automatique dans la boîte de dialogue de
l'afficheur braille.

Cette option est activée par défaut. Vous êtes fortement encouragé à laisser
cette option activée si le serveur de bureau distant n'a pas de sortie
audio.

### Autoriser le système distant à contrôler les paramètres du pilote

Cette option client, lorsqu'elle est activée, vous permet de contrôler les
paramètres du pilote (tels que la voix et la hauteur du synthétiseur) du
système distant. Les modifications effectuées sur le système distant seront
automatiquement reflétées localement. Si vous avez des difficultés à accéder
au menu de NVDA local lors du contrôle d'un système distant, vous pouvez
activer cette option. Sinon, il est conseillé de le désactiver, car cela
implique une certaine dégradation des performances.

### Conserver le support client lors de la sortie de NVDA

Cette option client n'est disponible que sur des copies installées de
NVDA. Lorsqu'il est activé, il garantit que la partie client de NVDA est
chargée dans votre client de bureau distant, même lorsque NVDA n'est pas en
cours d'exécution.

Pour utiliser la partie client de RDAccess, plusieurs modifications doivent
être faites dans le registre Windows. L'extension garantit que ces
modifications sont apportées dans le profil de l'utilisateur actuel. Ces
changements ne nécessitent pas de privilèges administrateur. Par conséquent,
NVDA peut appliquer automatiquement les modifications nécessaires lors du
chargement et annuler ces modifications lors de la sortie de NVDA. Cela
garantit que l'extension est entièrement compatible avec les versions
portables de NVDA. Pour permettre ce scénario, cette option est désactivée
par défaut. Cependant, si vous exécutez une copie installée et que vous êtes
le seul utilisateur du système, il est conseillé d'activer cette option pour
assurer un fonctionnement fluide au cas où NVDA a démarré ou n'est pas actif
lors de la connexion à un système distant.

### Activer le support de Microsoft Remote Desktop

Cette option est activée par défaut et garantit que la partie client de
RDAccess est chargée dans Microsoft Remote Desktop client (mstsc) lors du
démarrage de NVDA. À moins que conserver le support client ne soit activée
en activant l'option précédente, ces modifications seront automatiquement
annulées lors de la sortie de NVDA.

### Activer le support de Citrix Workspace

Cette option est activée par défaut et garantit que la partie client de
RDAccess est chargée dans l'application Citrix Workspace lors du démarrage
de NVDA. À moins que conserver le support client ne soit activée en activant
l'option précédente, ces modifications seront automatiquement annulées lors
de la sortie de NVDA.

Cette option n'est disponible que dans les cas suivants :

* Citrix Workspace est installé. Notez que la version Windows Store de
  l'application n'est pas prise en charge en raison des limites de cette
  application elle-même
* Il est possible d'enregistrer RDAccess dans le contexte actuel de
  l'utilisateur. Après avoir installé l'application, vous devez démarrer une
  session distante une fois pour rendre cela possible

## Instructions spécifiques de Citrix

Il y a quelques points de vigilance importants lors de l'utilisation de
RDAccess avec l'application Citrix Workspace.

### Exigences côté client

1. La variante Windows Store de l'application n'est *pas* prise en charge.

2. Après avoir installé Citrix Workspace, vous devez démarrer une session
   distante une fois pour permettre à RDAccess l'enregistrement de
   lui-même. La raison derrière cela est que l'application copie la
   configuration du système à la configuration de l'utilisateur lorsqu'il
   établit une session pour la première fois. Après cela, RDAccess peut
   s'enregistrer dans le contexte actuel de l'utilisateur.

### Exigence côté serveur

Dans Citrix Virtual Apps et Desktops 2109, Citrix a activé la liste
d'autorisation de la chaîne virtuelle dites. Cela signifie que les canaux
virtuels tiers, y compris le canal requis par RDAccess, ne sont pas
autorisés par défaut. Pour plus d'informations, [voir ce post sur le blog de
Citrix](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/)

Autoriser explicitement le canal RdPipe requis par RDAccess n'est pas encore
testé. Pour l'instant, probablement le mieux à faire c'est de désactiver
complètement la liste d'autorisation. Si votre administrateur système n'est
pas satisfait de cela, n'hésitez pas à [laisser tomber une ligne dans
l'incidence dédié][3]

## Problèmes et contribution

Si vous souhaitez signaler un problème ou contribuer, consultez [la page des
incidence (issues) sur GitHub][3]

## Composants externes

Cette extension s'appuie sur [RD Pipe][4], une bibliothèque écrite en Rust,
soutenant le support du client remote desktop.  RD Pipe est redistribué dans
le cadre de cette extension en vertu des termes de  la [version 3 de la GNU
Affero General Public License][5] publiée par la Free Software Foundation.

[[!tag dev beta]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess-beta

[3]: https://github.com/leonardder/rdAccess/issues

[4]: https://github.com/leonardder/rd_pipe-rs

[5]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
