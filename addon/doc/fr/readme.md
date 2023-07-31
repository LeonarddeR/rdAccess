# Remote Desktop Accessibility #

* Auteurs:  [Leonard de Ruijter][1]
* Télécharger [version béta][2]
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

## Problèmes et contribution

Si vous souhaitez signaler un problème ou contribuer, consultez [la page des
incidence (issues) sur GitHub][3]

## Composants externes

Cette extension s'appuie sur [RD Pipe][4], une bibliothèque écrite en Rust,
soutenant le support du client remote desktop. RD Pipe est redistribué dans
le cadre de cette extension en vertu des termes de  la [version 3 de la GNU
Affero General Public License][5] publiée par la Free Software Foundation.

[[!tag dev]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess-beta

[3]: https://github.com/leonardder/rdAccess/issues

[4]: https://github.com/leonardder/rd_pipe-rs

[5]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
