# RDAccess: Remote Desktop Accessibility

* Autores: [Leonard de Ruijter][1]
* Descargar [versión estable más reciente][2]
* NVDA compatibility: 2026.1 and later

The RDAccess add-on (Remote Desktop Accessibility) adds support for Microsoft Remote Desktop, Citrix, Parallels RAS, or VMware Horizon remote sessions to NVDA.
When installed on both the client and the server in NVDA, speech and braille generated on the server will be spoken and displayed in braille on the client machine.
This enables a user experience where managing a remote system feels as seamless as operating the local system.

## Características

* Support for Microsoft Remote Desktop (including Azure Virtual Desktop and Microsoft Cloud PC), Citrix, Parallels RAS, and VMware Horizon
* Salida hablada y por braille
* Detección automática de braille remoto usando la detección automática de pantallas braille de NVDA
* Detección automática de la voz remota usando un proceso dedicado de detección que se puede desactivar desde el diálogo de opciones de NVDA
* Support for portable copies of NVDA running on a server (additional configuration required for Citrix)
* Soporte completo para copias portables de NVDA que se ejecutan en el cliente (no se requieren privilegios de administrador adicionales para instalar el complemento)
* Varias sesiones de cliente activas a la vez
* Escritorio remoto disponible al instante después de que arranque NVDA
* Capacidad de controlar opciones específicas de síntesis de voz y braille sin dejar la sesión remota

## Registro de cambios

### Version 2.0.1

* When remote speech is switched on automatically, it now keeps speaking after a configuration profile switch. Previously, NVDA fell back to the synthesizer you have configured as soon as a profile was activated, for example when you moved to an application with its own profile.
* Renamed the option "Automatically recover remote speech after connection loss" to "Automatically switch to remote speech when available", which better describes what it does.
* Fixed frequent errors on the remote system when automatic language switching was enabled while using the remote synthesizer. Reporting of unsupported languages now reflects the languages supported by the speech synthesizer on the client.
* On ARM64 versions of Windows, remote desktop clients that run under x64 emulation can now use RDAccess.
* Adapted to the braille input changes introduced in NVDA 2026.3.

### Version 2.0

* Speech and braille coming from the remote system are now presented sooner, which makes working in a remote session feel more responsive.
* When starting a remote server instance of NVDA, braille is now shown as soon as a remote session connects, instead of only after the first keypress or focus change.
* Fixed a freeze when switching away from the remote synthesizer or braille display while a session was disconnecting.
* RDAccess now exchanges speech and braille using a new protocol modeled on the one used by NVDA's built-in Remote Access. It is more robust and no longer relies on the pickle format that a compromised remote system could abuse. The protocol version is chosen automatically, so a client and a server running different versions of RDAccess still work together.
* The minimum compatible NVDA version is now 2026.1. Removed support for earlier versions.
* Adapted to the braille changes introduced in NVDA 2026.3.
* Updated RD Pipe dependency to version 0.9.0.
* RDAccess is now licensed under the GNU General Public License version 2 or later.

### Version 1.7.1

* Hopefully fixed a bug in rd_pipe that caused the wrong virtual channel to be created.

### Version 1.7

* Removed secure desktop support.
* Added a client option "Incoming speech pitch change percentage" to shift the pitch of speech rendered from a remote NVDA, making remote and local speech audibly distinguishable.

### Version 1.6

* Documented and improved Parallels RAS support.
* The minimum compatible NVDA version is now 2025.1. Removed support for earlier versions.
* Se actualiza la dependencia RdPipe.
* Added the ability to configure RdPipe log level.
* Added a viewer for the RdPipe log, available from the settings panel.
* Improved uninstall behavior (no longer raise errors or remove Citrix support when Citrix is not available).

### Versión 1.5

* Se añade la posibilidad de crear un informe de diagnóstico de depuración mediante un botón en el panel de opciones de RDAccess [#23](https://github.com/leonardder/rdAccess/pull/23).
* Soporte para pantallas braille multilínea en NVDA 2025.1 y posterior [#19](https://github.com/leonardder/rdAccess/pull/13).
* La versión mínima compatible de NVDA es ahora la 2024.1. Se elimina el soporte para versiones anteriores.
* Se añaden notificaciones de conexión del cliente [#25](https://github.com/leonardder/rdAccess/pull/25).
* Se actualiza la dependencia RdPipe.
* Traducciones actualizadas.

### Versión 1.4

* Nueva versión estable.

### Versión 1.3

* Se corrigen gestos de pantallas braille que no funcionaban.

### Versión 1.2

* Se usa [Ruff](https://github.com/astral-sh/ruff) como formateador y corrector. [#13](https://github.com/leonardder/rdAccess/pull/13).
* Se corrige un problema por el que NVDA en el cliente genera un error al pausar la voz en el servidor.
* Se corrige el soporte de `winAPI.secureDesktop.post_secureDesktopStateChange`.
* Se mejora la inicialización del controlador en el servidor.

### Versión 1.1

* Se añade soporte para el estilo de registro de dispositivos de NVDA 2023.3 para detectar automáticamente pantallas braille. [#11](https://github.com/leonardder/rdAccess/pull/11).
* Se añade soporte para el punto de extensión `winAPI.secureDesktop.post_secureDesktopStateChange` de NVDA 2024.1 alfa. [#12](https://github.com/leonardder/rdAccess/pull/12).

### Versión 1.0

Primera versión estable.

## Primeros pasos

1. Instala RD Access tanto en una copia cliente como servidor de NVDA.
1. El sistema remoto debería empezar a hablar automáticamente usando el sintetizador de voz local.
      Si no, en la instancia de NVDA del servidor, selecciona el sintetizador de voz remoto desde el diálogo de selección de sintetizador de NVDA.
1. Para usar braille, activa la detección automática de pantallas braille utilizando el diálogo de selección de pantallas braille.

## Configuración

Tras la instalación, se puede configurar el complemento RD Access desde el diálogo de opciones de NVDA, al que se puede acceder desde el menú NVDA eligiendo Preferencias > Opciones...
Tras esto, elige la categoría Escritorio remoto.

Este diálogo contiene las siguientes opciones:

### Activar accesibilidad en escritorio remoto para

Esta lista de casillas de verificación controla el modo de operación del complemento.
Se puede elegir entre:

* Conexiones entrantes (servidor de escritorio remoto): elige esta opción si la copia actual de NVDA se ejecuta en un servidor de escritorio remoto.
* Conexiones salientes (cliente de escritorio remoto): elige esta opción si la copia actual de NVDA se ejecuta en un cliente de escritorio remoto que se conecta a uno o más servidores.

Para garantizar un inicio suave con el complemento, todas las opciones vienen activadas por defecto.
Sin embargo, se aconseja desactivar el modo cliente o servidor según corresponda.

### Synchronize the Caps Lock Key between Client and Server

When both the client and the server run NVDA with caps lock as an NVDA modifier key, the caps lock state can get out of sync, since the remote desktop client feeds caps lock presses back into the client system when the session is full screen.
When this option is enabled on the client, caps lock presses aimed at a full screen remote session no longer toggle caps lock on the client.
When it is enabled on the server, the server reports its caps lock state to the client, which applies it as soon as the remote session loses focus.
For correct behavior, this option needs to be enabled on both the client and the server; it is enabled by default on both.

Note that with the NVDA setting "Handle keys from other applications" disabled on the client, caps lock can still get out of sync.

### Automatically Switch to Remote Speech when Available

This option is only available in server mode.
It ensures that Remote Speech is activated as soon as a remote desktop client offers it, similar to braille display auto-detection, and that the connection is automatically re-established when it is lost.
While Remote Speech is active this way, your configured synthesizer is left untouched, and switching configuration profiles no longer falls back to it.

Esta opción viene activada por defecto.
Se aconseja encarecidamente dejarla activada si el servidor de escritorio remoto no tiene salida de audio.

### Permitir que el sistema remoto modifique ajustes del controlador

Cuando esta opción del cliente está activada, permite modificar ajustes del controlador (como voz del sintetizador y tono) desde el sistema remoto.
Los cambios realizados en el sistema remoto se reflejarán automáticamente en el local.

### Mantener soporte de cliente al salir de NVDA

Esta opción de cliente, disponible sólo en copias instaladas de NVDA, garantiza que la parte cliente de NVDA se carga en tu cliente de escritorio remoto, incluso cuando NVDA no está en ejecución.

To use the client portion of RDAccess, changes need to be made in the Windows Registry.
The add-on ensures that these changes are made under the profile of the current user, requiring no administrative privileges.
Therefore, NVDA can automatically apply the necessary changes when loaded and undo these changes when exiting NVDA, ensuring compatibility with portable versions of NVDA.

Esta opción se desactiva por defecto.
Sin embargo, si ejecutas una copia instalada de NVDA y eres el único usuario del sistema, se aconseja activar esta opción para garantizar una operación más suave en caso de que NVDA no esté activo al conectar a un sistema remoto y se inicie posteriormente.

### Enable Default Remote Desktop Support

This option, enabled by default, ensures that the client portion of RDAccess is loaded in the Microsoft Remote Desktop client (mstsc) when starting NVDA.
This is also required for VMware Horizon, Parallels RAS, Azure Virtual Desktop. etc.
Changes made through this option will be automatically undone when exiting NVDA unless persistent client support is enabled.

### Habilitar soporte para Citrix Workspace

Esta opción, activada por defecto, garantiza que la parte cliente de RD Access se carga en la aplicación Citrix Workspace al arrancar NVDA.
A menos que se habilite el soporte persistente de cliente activando la opción anterior, estos cambios se desharán automáticamente al salir de NVDA.

Esta opción sólo está disponible bajo las siguientes condiciones:

* Citrix Workspace está instalado.
    Ten en cuenta que la versión de esta aplicación para la tienda de Windows no está soportada debido a limitaciones en la propia aplicación.
* Es posible registrar RDAccess bajo el contexto del usuario actual.
    Después de instalar la aplicación, se debe iniciar una sesión remota una vez para activarlo.

### Notificar cambios de conexión con

Este cuadro combinado permite controlar notificaciones recibidas cuando un sistema remoto abre o cierra la voz remota o la conexión braille.
Puedes elegir entre:

* Desactivado (sin notificaciones)
* Mensajes (por ejemplo, braille remoto conectado)
* Sonidos (NVDA 2025.1+)
* Tanto mensajes como sonidos

Ten en cuenta que los sonidos no están disponibles en versiones de NVDA anteriores a la 2025.1.
Se usarán pitidos en versiones anteriores.

### Incoming Speech Pitch Change Percentage

This client option shifts the pitch of speech rendered locally when it originates from a remote NVDA, making remote and local speech audibly distinguishable.

The value is a percentage between -100 and 100.
Positive values raise pitch, negative values lower it.
A value of 0 disables the shift.
The default is 10.

The shift is applied only when the local synthesizer supports pitch commands; synthesizers without pitch support are unaffected.

### Abrir informe de diagnóstico

Este botón abre un mensaje explorable con una salida JSON que contiene varios diagnósticos que posiblemente puedan ayudar en la depuración.
Si [abres una incidencia en GitHub][4], se te puede pedir que proporciones este informe.

## Instrucciones específicas para Citrix

Se deben tener en cuenta algunas consideraciones importantes al usar RD Access con la aplicación Citrix Workspace:

### Requisitos del lado cliente

1. La variante de esta aplicación para la tienda de Windows *no* está soportada.
1. Tras instalar Citrix Workspace, tienes que iniciar una sesión remota una vez para permitir que RD Access se registre.
      La razón detrás de esto es que la aplicación copia la configuración del sistema a la configuración del usuario al establecer una sesión por primera vez.
      Tras esto, RD Access se puede registrar por sí mismo bajo el contexto del usuario actual.

### Requisitos del lado servidor

En Citrix Virtual Apps and Desktops 2109, Citrix habilitó algo llamado Lista de canales virtuales permitidos, restringiendo canales virtuales de terceros, incluido el canal que necesita RDAccess, por defecto.
Para más información, [consulta esta entrada de blog de Citrix](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/)

Permitir explícitamente el canal de RDPipe que necesita RDAccess es algo que no se ha probado todavía.
Por ahora, lo mejor que se puede hacer es desactivar por completo la lista de permitidos.
Si el administrador de tu sistema no está contento con esto, siéntete libre de [mencionarlo en la incidencia relacionada][3].

## Incidencias y colaboración

Si quieres informar de una incidencia o colaborar, echa un vistazo a la [página de incidencias en GitHub][4].

## Componentes externos

Este complemento se apoya en [RD Pipe][5], una biblioteca escrita en Rust que respalda el soporte para clientes de escritorio remoto.
RD Pipe se redistribuye como parte de este complemento según los términos de la [versión 3 de la licencia pública GNU Affero][6] tal y como la publicó la Free Software Foundation.

[[!tag stable dev beta]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess

[3]: https://github.com/leonardder/rdAccess/issues/1

[4]: https://github.com/leonardder/rdAccess/issues

[5]: https://github.com/leonardder/rd_pipe-rs

[6]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
