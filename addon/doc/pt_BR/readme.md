# RDAccess: Remote Desktop Accessibility

* Autores: [Leonard de Ruijter][1]
* Faça o download da [última versão estável][2]
* NVDA compatibility: 2026.1 and later

The RDAccess add-on (Remote Desktop Accessibility) adds support for Microsoft Remote Desktop, Citrix, Parallels RAS, or VMware Horizon remote sessions to NVDA.
When installed on both the client and the server in NVDA, speech and braille generated on the server will be spoken and displayed in braille on the client machine.
This enables a user experience where managing a remote system feels as seamless as operating the local system.

## Recursos

* Support for Microsoft Remote Desktop (including Azure Virtual Desktop and Microsoft Cloud PC), Citrix, Parallels RAS, and VMware Horizon
* Saída de fala e braille
* Detecção automática de braile remoto usando a detecção automática de exibição em braile do NVDA
* Detecção automática de fala remota usando um processo de detecção dedicado que pode ser desativado na caixa de diálogo de configurações do NVDA
* Suporte para cópias portáteis do NVDA em execução em um servidor (configuração adicional necessária para Citrix)
* Suporte total para cópias portáteis do NVDA em execução em um cliente (não são necessários privilégios administrativos adicionais para instalar o complemento)
* Várias sessões de clientes ativas simultaneamente
* Área de trabalho remota disponível instantaneamente após a inicialização do NVDA
* Capacidade de controlar configurações específicas do sintetizador e da exibição em braile sem sair da sessão remota

## Registro de alterações

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
* Atualização da dependência RdPipe.
* Added the ability to configure RdPipe log level.
* Added a viewer for the RdPipe log, available from the settings panel.
* Improved uninstall behavior (no longer raise errors or remove Citrix support when Citrix is not available).

### Versão 1.5

* Adicionar a capacidade de criar um relatório de diagnóstico de depuração por meio de um botão no painel de configurações do RDAccess [#23](https://github.com/leonardder/rdAccess/pull/23).
* Suporte para visores braille multilinha no NVDA 2025.1 e versões mais recentes [#19](https://github.com/leonardder/rdAccess/pull/13).
* A versão mínima compatível do NVDA agora é a 2024.1. O suporte para versões anteriores foi removido.
* Adicionadas notificações de conexão do cliente [#25](https://github.com/leonardder/rdAccess/pull/25).
* Atualização da dependência RdPipe.
* Traduções atualizadas.

### Versão 1.4

* Nova versão estável.

### Versão 1.3

* Corrigidos gestos defeituosos no visor Braille.

### Versão 1.2

* Use [Ruff](https://github.com/astral-sh/ruff) as a formatter and linter. [#13](https://github.com/leonardder/rdAccess/pull/13).
* Corrigido um problema em que o NVDA no cliente gerava um erro ao pausar a fala no servidor.
* Suporte corrigido para `winAPI.secureDesktop.post_secureDesktopStateChange`.
* Inicialização do driver aprimorada no servidor.

### Versão 1.1

* Adicionado suporte para registro de dispositivos no estilo NVDA 2023.3 para detecção automática de visores braille. [#11](https://github.com/leonardder/rdAccess/pull/11).
* Adicionado suporte para o ponto de extensão NVDA 2024.1 Alpha `winAPI.secureDesktop.post_secureDesktopStateChange`. [#12](https://github.com/leonardder/rdAccess/pull/12).

### Versão 1.0

Versão estável inicial.

## Introdução

1. Instale o RDAccess tanto na cópia cliente quanto na cópia servidor do NVDA.
1. O sistema remoto deve começar a falar automaticamente usando o sintetizador de voz local.
      Caso contrário, na instância do NVDA no servidor, selecione o sintetizador de voz remoto na caixa de diálogo de seleção do sintetizador do NVDA.
1. Para usar o braile, ative a detecção automática de exibição em braile usando a caixa de diálogo de seleção de exibição em braile.

## Configuração

Após a instalação, o complemento RDAccess pode ser configurado usando a caixa de diálogo de configurações do NVDA, acessível no menu NVDA, selecionando Preferências > Configurações...
Em seguida, selecione a categoria Área de Trabalho Remota.

Essa caixa de diálogo contém as seguintes configurações:

### Habilite a acessibilidade da área de trabalho remota para

Esta lista de caixas de seleção controla o modo de operação do complemento.
Escolha entre:

* Conexões de entrada (Servidor de Área de Trabalho Remota): Escolha esta opção se a instância atual do NVDA estiver sendo executada em um servidor de área de trabalho remota.
* Conexões de saída (Cliente de Área de Trabalho Remota): Escolha esta opção se a instância atual do NVDA estiver sendo executada em um cliente de área de trabalho remota que se conecta a um ou mais servidores.

Para garantir um início tranquilo com o complemento, todas as opções estão ativadas por padrão.
No entanto, recomendamos que você desative o modo servidor ou cliente, conforme apropriado.

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

Esta opção está habilitada por padrão.
É altamente recomendável deixar esta opção ativada se o servidor Remote Desktop não tiver saída de áudio.

### Permitir que o sistema remoto controle as configurações do driver

Quando habilitada no cliente, esta opção permite controlar as configurações do driver (como voz e tom do sintetizador) a partir do sistema remoto.
As alterações feitas no sistema remoto serão automaticamente refletidas localmente.

### Manter o suporte ao cliente ao sair do NVDA

Esta opção do cliente, disponível nas cópias instaladas do NVDA, garante que a parte do cliente do NVDA seja carregada no seu cliente de desktop remoto, mesmo quando o NVDA não estiver em execução.

Para usar a parte cliente do RDAccess, é necessário fazer alterações no Registro do Windows.
O complemento garante que essas alterações sejam feitas no perfil do usuário atual, sem a necessidade de privilégios administrativos.
Portanto, o NVDA pode aplicar automaticamente as alterações necessárias ao ser carregado e desfazer essas alterações ao sair do NVDA, garantindo a compatibilidade com versões portáteis do NVDA.

Esta opção está desativada por padrão.
No entanto, se você estiver executando uma cópia instalada e for o único usuário do sistema, é recomendável habilitar esta opção para um funcionamento suave ao se conectar a um sistema remoto após o NVDA iniciar.

### Enable Default Remote Desktop Support

This option, enabled by default, ensures that the client portion of RDAccess is loaded in the Microsoft Remote Desktop client (mstsc) when starting NVDA.
This is also required for VMware Horizon, Parallels RAS, Azure Virtual Desktop. etc.
Changes made through this option will be automatically undone when exiting NVDA unless persistent client support is enabled.

### Habilitar suporte ao Citrix Workspace

Esta opção, habilitada por padrão, garante que a parte do cliente do RDAccess seja carregada no aplicativo Citrix Workspace ao iniciar o NVDA.
As alterações feitas por meio desta opção serão automaticamente desfeitas ao sair do NVDA, a menos que o suporte persistente ao cliente esteja ativado.

Esta opção está disponível apenas nas seguintes condições:

* O Citrix Workspace está instalado.
    Observe que a versão da aplicação da Windows Store não é suportada devido a limitações na própria aplicação.
* É possível registrar o RDAccess no contexto do usuário atual.
    Após instalar o aplicativo, é necessário iniciar uma sessão remota uma vez para habilitar essa função.

### Notificar alterações de conexão com

Esta caixa combinada permite controlar as notificações recebidas quando um sistema remoto abre ou fecha a conexão remota de voz ou braille.
Você pode escolher entre:

* Desabilitado (sem notificações)
* Mensagens (por exemplo, “Braille remoto conectado”)
* Sons (NVDA 2025.1+)
* Mensagens e sons

Observe que os sons não estão disponíveis nas versões do NVDA anteriores à 2025.1.
Nas versões mais antigas, serão utilizados sinais sonoros.

### Incoming Speech Pitch Change Percentage

This client option shifts the pitch of speech rendered locally when it originates from a remote NVDA, making remote and local speech audibly distinguishable.

The value is a percentage between -100 and 100.
Positive values raise pitch, negative values lower it.
A value of 0 disables the shift.
The default is 10.

The shift is applied only when the local synthesizer supports pitch commands; synthesizers without pitch support are unaffected.

### Abrir relatório de diagnóstico

Este botão abre uma mensagem navegável com saída JSON contendo vários diagnósticos que podem ajudar na depuração.
Ao [registrar um problema no GitHub][4], pode ser solicitado que você forneça este relatório.

## Instruções específicas da Citrix

Há pontos importantes a serem observados ao usar o RDAccess com o aplicativo Citrix Workspace:

### Requisitos do lado do cliente

1. A variante do aplicativo na Windows Store não é *suportada*.
1. Após instalar o Citrix Workspace, é necessário iniciar uma sessão remota uma vez para permitir que o RDAccess se registre.
      Isso ocorre porque o aplicativo copia as configurações do sistema para as configurações do usuário durante a configuração inicial da sessão.
      Em seguida, o RDAccess pode se registrar no contexto do usuário atual.

### Requisito do lado do servidor

No Citrix Virtual Apps and Desktops 2109, o Citrix habilitou a chamada lista de permissões de canais virtuais, restringindo canais virtuais de terceiros, incluindo o canal exigido pelo RDAccess, por padrão.
Para obter mais informações, [consulte esta publicação no blog da Citrix](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/).

A permissão explícita do canal RdPipe exigido pelo RDAccess ainda não foi testada.
Por enquanto, é melhor desabilitar completamente a lista de permissões.
Se o administrador do seu sistema tiver alguma dúvida, sinta-se à vontade para [abordar a questão aqui][3].

## Questões e contribuições

Para relatar um problema ou contribuir, consulte [a página de problemas no Github][4].

## Componentes externos

Este complemento depende do [RD Pipe][5], uma biblioteca escrita em Rust que dá suporte ao cliente de desktop remoto.
O RD Pipe é redistribuído como parte deste complemento sob os termos da [versão 3 da GNU Affero General Public License][6].

[[!tag stable dev beta]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess

[3]: https://github.com/leonardder/rdAccess/issues/1

[4]: https://github.com/leonardder/rdAccess/issues

[5]: https://github.com/leonardder/rd_pipe-rs

[6]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
