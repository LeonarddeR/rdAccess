# Remote Desktop Accessibility #

* Автори: [Леонард де Руйтер][1]
* Завантажити [бета-версію][2]
* NVDA compatibility: 2023.2 and later

The RDAccess add-on (Remote Desktop Accessibility) adds support to access
remote desktop sessions to NVDA using Microsoft Remote Desktop, Citrix or
VMware Horizon.  When installed in NVDA on both the client and the server,
speech and braille generated on the server will be spoken and brailled by
the client machine.  This enables a user experience where managing a remote
system feels just as performant as operating the local system.

## Особливості

* Підтримка Microsoft Remote Desktop, Citrix і VMware Horizon
* Виведення мовлення та шрифту Брайля
* Автоматичне виявлення віддаленого шрифту Брайля за допомогою автоматичного
  виявлення брайлівського дисплея в NVDA
* Автоматичне виявлення віддаленого мовлення за допомогою спеціального
  процесу виявлення, який можна вимкнути в діалозі налаштувань NVDA
* Підтримка переносних копій NVDA, запущених на сервері (потрібна додаткова
  конфігурація для Citrix)
* Повна підтримка переносних копій NVDA, запущених на клієнті (не потрібні
  додаткові адміністративні права для встановлення додатка)
* Кілька активних клієнтських сеансів одночасно
* Віддалений робочий стіл стає миттєво доступним після запуску NVDA
* Можливість керувати певними налаштуваннями синтезатора та брайлівського
  дисплея, не виходячи з віддаленого сеансу
* Можливість використання мовлення та шрифту Брайля в сеансі користувача під
  час доступу до захищених робочих столів

## Початок роботи

1. Install RDAccess in both a client and server copy of NVDA.
1. Віддалена система повинна автоматично почати розмовляти, використовуючи
   локальний синтезатор мовлення. Якщо ні, в копії NVDA на сервері виберіть
   віддалений синтезатор мовлення у діалозі вибору синтезатора NVDA.
1. Щоб використовувати шрифт Брайля, увімкніть автоматичне виявлення
   брайлівського дисплея в діалозі вибору брайлівського дисплея.

## Проблеми та внесок

Якщо ви хочете повідомити про проблему або зробити свій внесок, перегляньте
[сторінку проблем на Github][3]

## Зовнішні компоненти

Цей додаток використовує [RD Pipe][4], бібліотеку, написану на Rust, яка
підтримує клієнтську підтримку віддаленого робочого столу. RD Pipe
розповсюджується як частина цього додатка згідно з умовами [версії 3 GNU
Affero General Public License][5], опублікованої Фондом вільного програмного
забезпечення.

[[!tag dev]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess-beta

[3]: https://github.com/leonardder/rdAccess/issues

[4]: https://github.com/leonardder/rd_pipe-rs

[5]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
