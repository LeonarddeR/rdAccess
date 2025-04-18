# Accesibilidad en Escritorio Remoto #

* Autores: [Leonard de Ruijter][1]
* Descargar [versión estable más reciente][2]
* Compatibilidad con NVDA: de 2024.1 en adelante

El complemento RD Access (Accesibilidad en Escritorio Remoto, en inglés
Remote Desktop Accessibility) añade soporte para que NVDA pueda acceder a
sesiones de escritorio remoto usando el escritorio remoto de Microsoft,
Citrix o VMware Horizon.  Al estar instalado tanto en el cliente como en el
servidor, la voz y el braille generados en el servidor se verbalizarán y
mostrarán en braille en el equipo del cliente. Esto permite una experiencia
de usuario donde gestionar un sistema remoto se siente igual de eficaz que
al operar el sistema local.

## Características

* Soporte para el escritorio remoto de Microsoft (Incluyendo el escritorio
  virtual de Azure y Microsoft Cloud PC), Citrix y VMware Horizon
* Salida hablada y por braille
* Detección automática de braille remoto usando la detección automática de
  pantallas braille de NVDA
* Detección automática de la voz remota usando un proceso dedicado de
  detección que se puede desactivar desde el diálogo de opciones de NVDA
* Soporte para copias portables de NVDA que se ejecutan en un servidor (es
  necesario hacer una configuración adicional en Fitrix)
* Soporte completo para copias portables de NVDA que se ejecutan en el
  cliente (no se requieren privilegios de administrador adicionales para
  instalar el complemento)
* Varias sesiones de cliente activas a la vez
* Escritorio remoto disponible al instante después de que arranque NVDA
* Capacidad de controlar opciones específicas de síntesis de voz y braille
  sin dejar la sesión remota
* Capacidad de usar voz y braille de la sesión del usuario al acceder a
  escritorios seguros

## Registro de cambios

### Versión 1.5

* Se añade la posibilidad de crear un informe de diagnóstico de depuración
  mediante un botón en el panel de opciones de RDAccess
  [#23](https://github.com/leonardder/rdAccess/pull/23).
* Soporte para pantallas braille multilínea en NVDA 2025.1 y posterior
  [#19](https://github.com/leonardder/rdAccess/pull/13).
* La versión mínima compatible de NVDA es ahora la 2024.1. Se elimina el
  soporte para versiones anteriores.
* Se añaden notificaciones de conexión del cliente
  [#25](https://github.com/leonardder/rdAccess/pull/25).
* Se actualiza la dependencia RdPipe.
* Traducciones actualizadas.

### Versión 1.4

* Nueva versión estable.

### Versión 1.3

* Se corrigen gestos de pantallas braille que no funcionaban.

### Versión 1.2

* Se usa [Ruff](https://github.com/astral-sh/ruff) como formateador y
  corrector. [#13](https://github.com/leonardder/rdAccess/pull/13).
* Se corrige un problema por el que NVDA en el cliente genera un error al
  pausar la voz en el servidor.
* Se corrige el soporte de
  `winAPI.secureDesktop.post_secureDesktopStateChange`.
* Se mejora la inicialización del controlador en el servidor.

### Versión 1.1

* Se añade soporte para el estilo de registro de dispositivos de NVDA 2023.3
  para detectar automáticamente pantallas
  braille. [#11](https://github.com/leonardder/rdAccess/pull/11).
* Se añade soporte para el punto de extensión
  `winAPI.secureDesktop.post_secureDesktopStateChange` de NVDA 2024.1
  alfa. [#12](https://github.com/leonardder/rdAccess/pull/12).

### Versión 1.0

Primera versión estable.

## Primeros pasos

1. Instala RD Access tanto en una copia cliente como servidor de NVDA.
1. El sistema remoto debería empezar a hablar automáticamente usando el
   sintetizador de voz local. Si no, en la instancia de NVDA del servidor,
   selecciona el sintetizador de voz remoto desde el diálogo de selección de
   sintetizador de NVDA.
1. Para usar braille, activa la detección automática de pantallas braille
   utilizando el diálogo de selección de pantallas braille.

## Configuración

Tras la instalación, se puede configurar el complemento RD Access desde el diálogo de opciones de NVDA, al que se puede acceder desde el menú NVDA eligiendo Preferencias > Opciones...
Tras esto, elige la categoría Escritorio remoto.

Este diálogo contiene las siguientes opciones:

### Activar accesibilidad en escritorio remoto para

Esta lista de casillas de verificación controla el modo de operación del
complemento. Se puede elegir entre:

* Conexiones entrantes (servidor de escritorio remoto): elige esta opción si
  la copia actual de NVDA se ejecuta en un servidor de escritorio remoto.
* Conexiones salientes (cliente de escritorio remoto): elige esta opción si
  la copia actual de NVDA se ejecuta en un cliente de escritorio remoto que
  se conecta a uno o más servidores.
* Dejar pasar el escritorio seguro: elige esta opción si quieres usar
  braille y voz de la instancia de usuario de NVDA al acceder al escritorio
  remoto. Ten en cuenta que para que esto funcione, debes hacer que el
  complemento RD Access esté disponible en la copia de NVDA del escritorio
  seguro. Para ello, elige "Utilizar opciones actualmente guardadas durante
  el inicio de sesión y en pantallas seguras (requiere privilegios de
  administrador)" en las opciones generales de NVDA.

Para garantizar un inicio suave con el complemento, todas las opciones
vienen activadas por defecto. Sin embargo, se aconseja desactivar el modo
cliente o servidor según corresponda.

### Recuperar automáticamente voz remota tras una pérdida de conexión

Esta opción sólo está disponible en modo servidor. Garantiza que se volverá
a establecer la conexión automáticamente cuando el sintetizador de voz
remoto esté activo y la conexión se pierda. El comportamiento es similar al
de detección automática de pantallas braille.

Esta opción viene activada por defecto. Se aconseja encarecidamente dejarla
activada si el servidor de escritorio remoto no tiene salida de audio.

### Permitir que el sistema remoto modifique ajustes del controlador

Cuando esta opción del cliente está activada, permite modificar ajustes del
controlador (como voz del sintetizador y tono) desde el sistema remoto. Los
cambios realizados en el sistema remoto se reflejarán automáticamente en el
local.

### Mantener soporte de cliente al salir de NVDA

Esta opción de cliente, disponible sólo en copias instaladas de NVDA,
garantiza que la parte cliente de NVDA se carga en tu cliente de escritorio
remoto, incluso cuando NVDA no está en ejecución.

Para usar la parte cliente de RDAccess, se deben realizar varios cambios en
el registro de Windows. El complemento se asegura de hacer estos cambios en
el perfil del usuario actual. Estos cambios no necesitan privilegios de
administrador. Por lo tanto, NVDA puede aplicar automáticamente los cambios
necesarios al cargarse, y deshacer estos cambios al salir. Esto asegura que
el complemento es completamente compatible con versiones portables de NVDA.

Esta opción se desactiva por defecto. Sin embargo, si ejecutas una copia
instalada de NVDA y eres el único usuario del sistema, se aconseja activar
esta opción para garantizar una operación más suave en caso de que NVDA no
esté activo al conectar a un sistema remoto y se inicie posteriormente.

### Habilitar soporte para Escritorio Remoto de Microsoft

Esta opción, activada por defecto, garantiza que la parte cliente de RD
Access se carga en el cliente de escritorio remoto de Microsoft (mstsc) al
arrancar NVDA. A menos que se habilite el soporte persistente de cliente
activando la opción anterior, estos cambios se desharán automáticamente al
salir de NVDA.

### Habilitar soporte para Citrix Workspace

Esta opción, activada por defecto, garantiza que la parte cliente de RD
Access se carga en la aplicación Citrix Workspace al arrancar NVDA. A menos
que se habilite el soporte persistente de cliente activando la opción
anterior, estos cambios se desharán automáticamente al salir de NVDA.

Esta opción sólo está disponible bajo las siguientes condiciones:

* Citrix Workspace está instalado. Ten en cuenta que la versión de esta
  aplicación para la tienda de Windows no está soportada debido a
  limitaciones en la propia aplicación.
* Es posible registrar RDAccess bajo el contexto del usuario actual. Después
  de instalar la aplicación, se debe iniciar una sesión remota una vez para
  activarlo.

### Notificar cambios de conexión con

Este cuadro combinado permite controlar notificaciones recibidas cuando un
sistema remoto abre o cierra la voz remota o la conexión braille. Puedes
elegir entre:

* Desactivado (sin notificaciones)
* Mensajes (por ejemplo, braille remoto conectado)
* Sonidos (NVDA 2025.1+)
* Tanto mensajes como sonidos

Ten en cuenta que los sonidos no están disponibles en versiones de NVDA
anteriores a la 2025.1. Se usarán pitidos en versiones anteriores.

### Abrir informe de diagnóstico

Este botón abre un mensaje explorable con una salida JSON que contiene
varios diagnósticos que posiblemente puedan ayudar en la depuración. Si
[abres una incidencia en GitHub][4], se te puede pedir que proporciones este
informe.

## Instrucciones específicas para Citrix

Se deben tener en cuenta algunas consideraciones importantes al usar RD
Access con la aplicación Citrix Workspace:

### Requisitos del lado cliente

1. La variante de esta aplicación para la tienda de Windows *no* está
   soportada.
1. Tras instalar Citrix Workspace, tienes que iniciar una sesión remota una
   vez para permitir que RD Access se registre. La razón detrás de esto es
   que la aplicación copia la configuración del sistema a la configuración
   del usuario al establecer una sesión por primera vez. Tras esto, RD
   Access se puede registrar por sí mismo bajo el contexto del usuario
   actual.

### Requisitos del lado servidor

En Citrix Virtual Apps and Desktops 2109, Citrix habilitó algo llamado Lista
de canales virtuales permitidos, restringiendo canales virtuales de
terceros, incluido el canal que necesita RDAccess, por defecto. Para más
información, [consulta esta entrada de blog de
Citrix](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/)

Permitir explícitamente el canal de RDPipe que necesita RDAccess es algo que
no se ha probado todavía. Por ahora, lo mejor que se puede hacer es
desactivar por completo la lista de permitidos. Si el administrador de tu
sistema no está contento con esto, siéntete libre de [mencionarlo en la
incidencia relacionada][3].

## Incidencias y colaboración

Si quieres informar de una incidencia o colaborar, echa un vistazo a la
[página de incidencias en GitHub][4].

## Componentes externos

Este complemento se apoya en [RD Pipe][5], una biblioteca escrita en Rust
que respalda el soporte para clientes de escritorio remoto. RD Pipe se
redistribuye como parte de este complemento según los términos de la
[versión 3 de la licencia pública GNU Affero][6] tal y como la publicó la
Free Software Foundation.

[[!tag stable dev beta]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess

[3]: https://github.com/leonardder/rdAccess/issues/1

[4]: https://github.com/leonardder/rdAccess/issues

[5]: https://github.com/leonardder/rd_pipe-rs

[6]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
