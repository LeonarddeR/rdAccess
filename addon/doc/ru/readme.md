# Доступность Удалённого Рабочего Стола #

* Авторы: [Leonard de Ruijter][1]
* Загрузить [последнюю стабильную версию][2]
* Совместимость с NVDA: 2023.2 и выше

Дополнение RDAccess (Remote Desktop Accessibility, Доступность удаленного
рабочего стола) добавляет поддержку доступа к сеансам удалённого рабочего
стола в NVDA с помощью Удалённого Рабочего Стола Microsoft, Citrix или
VMware Horizon.  При установке в NVDA как на клиенте, так и на сервере, речь
и брайль, сгенерированные на сервере, будут воспроизводиться на клиентском
компьютере.  Это позволяет пользователю управлять удаленной системой так же
эффективно, как и локальной системой.

## Возможности

* Поддержка Microsoft Remote Desktop, Citrix и VMware Horizon
* Вывод речи и брайля
* Автоматическое распознавание удалённого Брайля с помощью функции
  автоматического распознавания брайлевского дисплея NVDA
* Автоматическое распознавание удалённой речи с помощью специального
  процесса обнаружения, который можно отключить в диалоге настроек NVDA
* Поддержка переносных копий NVDA, запущенных на сервере (для Fitrix
  требуется дополнительная настройка)
* Полная поддержка переносных копий NVDA, запущенных на клиенте (для
  установки дополнения не требуются дополнительные административные
  привилегии)
* Несколько активных клиентских сеансов одновременно
* Удалённый рабочий стол доступен мгновенно после запуска NVDA
* Возможность управлять определёнными настройками синтезатора и брайлевского
  дисплея, не выходя из удалённого сеанса
* Возможность использования речи и брайля в пользовательском сеансе при
  доступе к защищённым рабочим столам

## Журнал изменений

### Версия 1.0

Первоначальный стабильный выпуск.

## Приступая к работе

1. Установите RDAccess как в клиентской, так и в серверной копии NVDA.
1. Удалённая система должна автоматически начать говорить, используя
   локальный синтезатор речи. Если нет, то в экземпляре NVDA на сервере
   выберите удалённый синтезатор речи в диалоге выбора синтезатора NVDA.
1. Чтобы использовать брайль, включите автоматическое определение
   брайлевского дисплея в диалоге выбора брайлевского дисплея.

## Конфигурация

После установки дополнение RDAccess можно настроить с помощью диалога настроек NVDA, доступ к которому можно получить из меню NVDA, выбрав "Параметры" > "Настройки..."
После этого выберите категорию "Доступность удалённого рабочего стола".

Этот диалог содержит следующие настройки:

### Включить доступ к удалённому рабочему столу для

Этот список флажков определяет режим работы дополнения. Вы можете выбирать
между:

* Incoming connections (Remote Desktop Server): Choose this option if the
  current instance of NVDA is running on a remote desktop server
* Outgoing connections (Remote Desktop Client): Choose this option if the
  current instance of NVDA is running on a remote desktop client that
  connects to one or more servers
* Secure Desktop pass through: : Choose this option if you want to use
  braille and speech from the user instance of NVDA when accessing the
  secure desktop. Note that for this to work, you need to make the RDAccess
  add-on available on the secure desktop copy of NVDA. For this, choose "Use
  currently saved settings during sign-in and on secure screens (requires
  administrator privileges)" in NVDA's general settings.

To ensure a smooth start with the add-on, all options are enabled by
default. You are however encouraged to disable server or client mode as
appropriate.

### Automatically recover remote speech after connection loss

This option is only available in server mode. It ensures that the connection
will automatically be re-established when the Remote Speech synthesizer is
active and the connection is lost.  The behavior is very similar to that of
braille display auto detection.  This also clarifies why there is only such
an option for speech.  The reconnection of the Remote Braille display is
automatically handled when choosing the Automatic option from the Braille
Display Selection dialog.

This option is enabled by defalt. You are strongly encouraged to leave this
option enabled if the Remote Desktop server has no audio output.

### Allow remote system to control driver settings

This client option, when enabled, allows you to control driver settings
(such as synthesizer voice and pitch) from the remote system.  This is
especially useful when you have difficulties accessing the local NVDA menu
when controlling a remote system.  Changes performed on the remote system
will automatically be reflected locally.

While enabling this option implies some performance degradation, you are yet
advised to enable it.  When this option is disabled, speech synthesizer
ppitch changes for capitals don't work.

### Persist client support when exiting NVDA

This client option is only available on installed copies of NVDA.  When
enabled, it ensures that the client portion of NVDA is loaded in your remote
desktop client, even when NVDA is not running.

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

### Enable Microsoft Remote Desktop support

This option is enabled by default and ensures that the client portion of
RDAccess is loaded in the Microsoft Remote Desktop client (mstsc) when
starting NVDA.  Unless persistent client support is enabled by enabling the
previous option, these changes will be automatically undone when exiting
NVDA.

### Enable Citrix Workspace support

This option is enabled by default and ensures that the client portion of
RDAccess is loaded in the Citrix Workspace app when starting NVDA.  Unless
persistent client support is enabled by enabling the previous option, these
changes will be automatically undone when exiting NVDA.

This option is only available in the following cases:

* Citrix Workspace is installed. Note that the Windows Store version of the
  app is not supported due to limitations in that app itself
* It is possible to register RDAccess under the current user context. After
  installing the app, you have to start a remote session once to make this
  possible

## Citrix specific instructions

There are some important points of attention when using RDAccess with the
Citrix Workspace app.

### Client side requirements

1. The Windows Store variant of the app is *not* supported.
2. After installing Citrix Workspace, you have to start a remote session
   once to allow RDAccess registering itself. The reason behind this is that
   the application copies the system configuration to the user configuration
   when it establishes a session for the first time. After that, RDAccess
   can register itself under the current user context.

### Server side requirement

In Citrix Virtual Apps and Desktops 2109, Citrix enabled the so called
virtual channel allow list. This means that third party virtual channels,
including the channel required by RDAccess, is not allowed by default. For
more information, [see this Citrix blog
post](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/)

Explicitly allowing the RdPipe channel required by RDAccess is not yet
tested. For now, it is probably your best bet to disable the allow list
altogether. If your system administrator is unhappy with this, feel free to
[drop a line in the devoted issue][3]

## Проблемы и вклад в их решение

Если вы хотите сообщить о проблеме или внести свой вклад, загляните на
[страницу проблем на Github][3].

## Внешние компоненты

Это дополнение основано на [RD Pipe][4], библиотеке, написанной на Rust и
поддерживающей клиентскую поддержку удаленных рабочих столов.  RD Pipe
распространяется как часть этого дополнения в соответствии с условиями
[версии 3 GNU Affero General Public License][5], опубликованными Фондом
свободного программного обеспечения (Free Software Foundation).

[[!tag stable dev beta]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess

[3]: https://github.com/leonardder/rdAccess/issues

[4]: https://github.com/leonardder/rd_pipe-rs

[5]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
