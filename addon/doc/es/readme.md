# NVDA Remote Desktop #

* Autores: [Leonard de Ruijter][1]
* Descargar [versión beta][2]
* Compatibilidad con NVDA: de 2023.1 en adelante

Este complemento añade soporte para que NVDA pueda acceder a sesiones de
escritorio remoto usando el escritorio remoto de Microsoft, Citrix o VMware
Horizon.  Al estar instalado tanto en el cliente como en el servidor, la voz
y el braille generados en el servidor se verbalizarán y mostrarán en braille
en el equipo del cliente. Esto permite una experiencia de usuario donde
gestionar un sistema remoto se siente igual de eficaz que al operar el
sistema local.

## Características

* Soporte para el escritorio remoto de Microsoft, Citrix y VMware Horizon
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

## Primeros pasos

1. Instala este complemento tanto en una copia cliente como servidor de
   NVDA.
1. El sistema remoto debería empezar a hablar automáticamente usando el
   sintetizador de voz local. Si no, en la instancia de NVDA del servidor,
   selecciona el sintetizador de voz remoto desde el diálogo de selección de
   sintetizador de NVDA.
1. Para usar braille, activa la detección automática de pantallas braille
   utilizando el diálogo de selección de pantallas braille.

## Incidencias y colaboración

Si quieres informar de una incidencia o colaborar, echa un vistazo a la
[página de incidencias en GitHub][3]

## Componentes externos

Este complemento se apoya en [RD Pipe][4], una biblioteca escrita en Rust
que respalda el soporte para clientes de escritorio remoto. RD Pipe se
redistribuye como parte de este complemento según los términos de la
[versión 3 de la licencia pública GNU Affero][5] tal y como la publicó la
Free Software Foundation.

[[!tag dev]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=nvdaRd-beta

[3]: https://github.com/leonardder/nvdaRd/issues

[4]: https://github.com/leonardder/rd_pipe-rs

[5]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
