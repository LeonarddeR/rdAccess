# NVDA Remote Desktop Accessibility #

* Автори: [Леонард де Руйтер][1]
* Download [latest stable version][2]
* Сумісність з NVDA: 2023.2 і новіші версії

Додаток RDAccess (Remote Desktop Accessibility) додає підтримку доступу до
сеансів віддаленого робочого столу в NVDA за допомогою Microsoft Remote
Desktop, Citrix або VMware Horizon.  При встановленні в NVDA як на клієнті,
так і на сервері, мова і шрифт Брайля, згенеровані на сервері, будуть
відтворюватися на клієнтській машині.  Це дає користувачеві можливість
керувати віддаленою системою так само ефективно, як і локальною.

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

## Changelog

### Version 1.0

Initial stable release.

## Початок роботи

1. Встановіть RDAccess у клієнтську та серверну копії NVDA.
1. Віддалена система повинна автоматично почати розмовляти, використовуючи
   локальний синтезатор мовлення. Якщо ні, в копії NVDA на сервері виберіть
   віддалений синтезатор мовлення у діалозі вибору синтезатора NVDA.
1. Щоб використовувати шрифт Брайля, увімкніть автоматичне виявлення
   брайлівського дисплея в діалозі вибору брайлівського дисплея.

## Конфігурація

After installation, the RDAccess add-on can be configured using NVDA's settings dialog, which can be accessed from the NVDA Menu by choosing Preferences > Settings...
After that, choose the Remote Desktop category.

Цей діалог містить такі налаштування:

### Увімкнути доступність віддаленого робочого столу для

This list of check boxes controls the operating mode of the add-on. You can
choose between:

* Вхідні з'єднання (Сервер віддаленого робочого столу): Виберіть це
  налаштування, якщо поточний екземпляр NVDA запущено на сервері віддаленого
  робочого столу
* Вихідні з’єднання (клієнт віддаленого робочого столу): виберіть це
  налаштування, якщо поточний екземпляр NVDA запущено на клієнті віддаленого
  робочого столу, який підключається до одного або кількох серверів
* Secure Desktop pass through: : Choose this option if you want to use
  braille and speech from the user instance of NVDA when accessing the
  secure desktop. Note that for this to work, you need to make the RDAccess
  add-on available on the secure desktop copy of NVDA. For this, choose "Use
  currently saved settings during sign-in and on secure screens (requires
  administrator privileges)" in NVDA's general settings.

Щоб забезпечити плавний початок роботи додатка, усі налаштування початково
ввімкнено. Проте вам рекомендується вимкнути режим сервера або клієнта, якщо
це необхідно.

### Автоматичне відновлення віддаленого мовлення після втрати з’єднання

Це налаштування доступне лише в режимі сервера. Це гарантує, що підключення
буде автоматично відновлено, коли віддалений синтезатор мовлення активний і
з’єднання втрачено. Поведінка дуже схожа на автоматичне визначення дисплея
Брайля. Це також пояснює, чому існує лише такий варіант для
мовлення. Повторне підключення віддаленого брайлівського дисплея виконується
автоматично, якщо вибрати параметр «Автоматично» в діалозі вибору
брайлівського дисплея.

Це налаштування увімкнено початково. Наполегливо рекомендується залишити це
налаштування увімкненим, якщо сервер віддаленого робочого столу не має
аудіовиходу.

### Дозволити віддаленій системі керувати налаштуваннями драйвера

This client option, when enabled, allows you to control driver settings
(such as synthesizer voice and pitch) from the remote system.  This is
especially useful when you have difficulties accessing the local NVDA menu
when controlling a remote system.  Changes performed on the remote system
will automatically be reflected locally.

While enabling this option implies some performance degradation, you are yet
advised to enable it.  When this option is disabled, speech synthesizer
ppitch changes for capitals don't work.

### Постійна підтримка клієнта під час виходу з NVDA

Це клієнтське налаштування доступне лише у встановлених копіях NVDA.  Якщо
це налаштування увімкнено, воно гарантує, що клієнтська частина NVDA буде
завантажена у вашому клієнті віддаленого робочого столу, навіть якщо NVDA не
запущено.

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

### Увімкніть підтримку Microsoft Remote Desktop

Це налаштування увімкнено початково і гарантує, що клієнтська частина
RDAccess буде завантажена у клієнті Microsoft Remote Desktop (mstsc) під час
запуску NVDA.  Якщо не увімкнути підтримку постійного клієнта за допомогою
попереднього налаштування, ці зміни буде автоматично скасовано при виході з
NVDA.

### Увімкніть підтримку Citrix Workspace

Це налаштування увімкнено початково і гарантує, що клієнтська частина
RDAccess буде завантажена у програмі Citrix Workspace під час запуску NVDA.
Якщо не увімкнути підтримку постійного клієнта за допомогою попередньоо
налаштування, ці зміни буде автоматично скасовано при виході з NVDA.

Це налаштування доступне лише в таких випадках:

* Citrix Workspace встановлено. Зауважте, що версія програми з Windows Store
  не підтримується через обмеження самої програми
* Можна зареєструвати RDAccess у контексті поточного користувача. Щоб
  зробити це можливим, після встановлення програми потрібно один раз
  запустити віддалений сеанс

## Спеціальні інструкції Citrix

Під час використання RDAccess із програмою Citrix Workspace варто звернути
увагу на кілька важливих моментів.

### Вимоги на стороні клієнта

1. Варіант програми Windows Store *не* підтримується.
2. Після встановлення Citrix Workspace вам доведеться один раз запустити
   віддалений сеанс, щоб дозволити RDAccess зареєструватися. Причиною цього
   є те, що програма копіює конфігурацію системи в конфігурацію користувача,
   коли вона встановлює сеанс вперше. Після цього RDAccess може
   зареєструватися в контексті поточного користувача.

### Вимоги на стороні сервера

У Citrix Virtual Apps and Desktops 2109 компанія Citrix увімкнула так званий
список дозволених віртуальних каналів. Це означає, що віртуальні канали
сторонніх виробників, включаючи канал, необхідний для RDAccess, початково
заборонено. Для отримання додаткової інформації [див. цю статтю в блозі
Citrix](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/)

Явний дозвіл каналу RdPipe, необхідний для RDAccess, ще не
перевірено. Наразі, ймовірно, найкращим варіантом буде вимкнути список
дозволених каналів. Якщо ваш системний адміністратор незадоволений цим, не
соромтеся [написати рядок у спеціальному випуску][3].

## Проблеми та внесок

Якщо ви хочете повідомити про проблему або зробити свій внесок, перегляньте
[сторінку проблем на Github][3]

## Зовнішні компоненти

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
