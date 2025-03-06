# Remote Desktop Accessibility #

* Autores: [Leonard de Ruijter][1]
* Faça o download da [última versão estável][2]
* Compatibilidade com NVDA: 2023.2 e posteriorCompatibilidade com NVDA:
  2023.2 e posterior

O complemento RDAccess (Remote Desktop Accessibility) adiciona suporte para
acessar sessões de área de trabalho remota ao NVDA usando o Microsoft Remote
Desktop, Citrix ou VMware Horizon.  Quando instalado no NVDA, tanto no
cliente quanto no servidor, a fala e o braile gerados no servidor serão
falados e braileados pela máquina cliente.  Isso permite uma experiência de
usuário em que o gerenciamento de um sistema remoto é tão eficiente quanto a
operação do sistema local.

## Recursos

* Suporte para Microsoft Remote Desktop, Citrix e VMware Horizon
* Saída de fala e braille
* Detecção automática de braile remoto usando a detecção automática de
  exibição em braile do NVDA
* Detecção automática de fala remota usando um processo de detecção dedicado
  que pode ser desativado na caixa de diálogo de configurações do NVDA
* Suporte para cópias portáteis do NVDA em execução em um servidor
  (configuração adicional necessária para o Fitrix)
* Suporte total para cópias portáteis do NVDA em execução em um cliente (não
  são necessários privilégios administrativos adicionais para instalar o
  complemento)
* Várias sessões de cliente ativas ao mesmo tempo
* Área de trabalho remota disponível instantaneamente após a inicialização
  do NVDA
* Capacidade de controlar configurações específicas do sintetizador e da
  exibição em braile sem sair da sessão remota
* Capacidade de usar fala e braile na sessão do usuário ao acessar desktops
  seguros

## Registro de alterações

### Versão 1.0

Versão estável inicial.

## Primeiros passos

1. Instale o RDAccess em uma cópia do cliente e do servidor do NVDA.
1. O sistema remoto deve começar a falar automaticamente usando o
   sintetizador de fala local. Caso contrário, na instância do NVDA no
   servidor, selecione o sintetizador de fala remoto na caixa de diálogo de
   seleção de sintetizador do NVDA.
1. Para usar o braile, ative a detecção automática de exibição em braile
   usando a caixa de diálogo de seleção de exibição em braile.

## Configuração

Após a instalação, o complemento RDAccess pode ser configurado usando a caixa de diálogo de configurações do NVDA, que pode ser acessada no menu NVDA, escolhendo Preferências > Configurações...
Depois disso, escolha a categoria Remote Desktop. Após a instalação, o complemento RDAccess pode ser configurado usando a caixa de diálogo de configurações do NVDA, que pode ser acessada no menu NVDA, escolhendo Preferências > Configurações...
Depois disso, escolha a categoria Remote Desktop.

Essa caixa de diálogo contém as seguintes configurações:

### Habilite a acessibilidade da área de trabalho remota para

Essa lista de caixas de seleção controla o modo de operação do
complemento. Você pode escolher entre:

* Conexões de entrada (servidor de área de trabalho remota): Escolha essa
  opção se a instância atual do NVDA estiver sendo executada em um servidor
  de área de trabalho remota
* Conexões de saída (cliente de área de trabalho remota): Escolha essa opção
  se a instância atual do NVDA estiver sendo executada em um cliente de área
  de trabalho remota que se conecta a um ou mais servidores
* Passagem da área de trabalho segura: : Escolha esta opção se quiser usar
  braile e fala da instância do usuário do NVDA ao acessar a área de
  trabalho segura. Observe que, para que isso funcione, você precisa
  disponibilizar o complemento RDAccess na cópia da área de trabalho segura
  do NVDA. Para isso, escolha “Usar as configurações salvas atuais nas
  credenciais do Windows e outras telas seguras (requer privilégios
  administrativos” nas configurações gerais do NVDA.

Para garantir um início tranquilo com o complemento, todas as opções estão
ativadas por padrão. No entanto, recomendamos que você desative o modo
servidor ou cliente, conforme apropriado.

### Recupere automaticamente a fala remota após a perda de conexão

Essa opção está disponível somente no modo de servidor. Ela garante que a
conexão será restabelecida automaticamente quando o sintetizador de fala
remoto estiver ativo e a conexão for perdida.  O comportamento é muito
semelhante ao da detecção automática da tela braile.  Isso também esclarece
por que só existe essa opção para fala.  A reconexão do monitor Braille
remoto é tratada automaticamente quando se escolhe a opção Automático na
caixa de diálogo Seleção de monitor Braille.

Essa opção é ativada por padrão. É altamente recomendável que você deixe
essa opção ativada se o servidor da Área de Trabalho Remota não tiver saída
de áudio.

### Permitir que o sistema remoto controle as configurações do driver

Essa opção de cliente, quando ativada, permite controlar as configurações do
driver (como a voz e o tom do sintetizador) a partir do sistema remoto.
Isso é especialmente útil quando você tem dificuldades para acessar o menu
local do NVDA ao controlar um sistema remoto.  As alterações realizadas no
sistema remoto serão automaticamente refletidas localmente.

Embora a ativação dessa opção implique alguma degradação do desempenho,
recomendamos que você a ative.  Quando essa opção está desativada, as
alterações de tom do sintetizador de fala para letras maiúsculas não
funcionam.

### Suporte ao cliente persistente ao sair do NVDA

Essa opção de cliente está disponível somente em cópias instaladas do NVDA.
Quando ativada, ela garante que a parte do cliente do NVDA seja carregada no
seu cliente de área de trabalho remota, mesmo quando o NVDA não estiver em
execução.

Para usar a parte do cliente do RDAccess, várias alterações precisam ser
feitas no Registro do Windows.  O complemento garante que essas alterações
sejam feitas no perfil do usuário atual.  Essas alterações não requerem
privilégios administrativos.  Portanto, o NVDA pode aplicar automaticamente
as alterações necessárias quando carregado e desfazer essas alterações ao
sair do NVDA.  Isso garante que o complemento seja totalmente compatível com
as versões portáteis do NVDA.

Essa opção está desativada por padrão.  No entanto, se você estiver
executando uma cópia instalada e for o único usuário do sistema,
recomendamos que ative essa opção.  Isso garante uma operação tranquila caso
o NVDA não esteja ativo ao se conectar a um sistema remoto e seja iniciado
posteriormente.

### Habilitar o suporte à Área de Trabalho Remota da Microsoft

Essa opção é ativada por padrão e garante que a parte do cliente do RDAccess
seja carregada no cliente Microsoft Remote Desktop (mstsc) ao iniciar o
NVDA.  A menos que o suporte persistente ao cliente seja ativado por meio da
ativação da opção anterior, essas alterações serão automaticamente desfeitas
ao sair do NVDA.

### Habilitar o suporte ao Citrix Workspace

Essa opção é ativada por padrão e garante que a parte do cliente do RDAccess
seja carregada no aplicativo Citrix Workspace ao iniciar o NVDA.  A menos
que o suporte persistente ao cliente seja ativado pela opção anterior, essas
alterações serão automaticamente desfeitas ao sair do NVDA.

Essa opção só está disponível nos seguintes casos:

* O Citrix Workspace está instalado. Observe que a versão do aplicativo para
  Windows Store não é compatível devido a limitações do próprio aplicativo
* É possível registrar o RDAccess no contexto do usuário atual. Depois de
  instalar o aplicativo, é necessário iniciar uma sessão remota uma vez para
  que isso seja possível

## Instruções específicas do Citrix

Há alguns pontos de atenção importantes ao usar o RDAccess com o aplicativo
Citrix Workspace.

### Requisitos do lado do cliente

1. A variante do aplicativo na Windows Store não é *suportada*.
2. Depois de instalar o Citrix Workspace, é necessário iniciar uma sessão
   remota uma vez para permitir que o RDAccess se registre. A razão por trás
   disso é que o aplicativo copia a configuração do sistema para a
   configuração do usuário quando estabelece uma sessão pela primeira
   vez. Depois disso, o RDAccess pode se registrar no contexto do usuário
   atual.

### Requisito do lado do servidor

No Citrix Virtual Apps and Desktops 2109, o Citrix ativou a chamada lista de
permissão de canais virtuais. Isso significa que os canais virtuais de
terceiros, incluindo o canal exigido pelo RDAccess, não são permitidos por
padrão. Para obter mais informações, [consulte esta postagem no blog da
Citrix]
(https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/)

A permissão explícita do canal RdPipe exigida pelo RDAccess ainda não foi
testada. Por enquanto, sua melhor opção é desativar completamente a lista de
permissões. Se o administrador do sistema não estiver satisfeito com isso,
sinta-se à vontade para [escrever uma linha na edição dedicada][3]

## Problemas e contribuições

Se quiser relatar um problema ou contribuir, dê uma olhada na [página de
problemas no Github][3]

## Componentes externos

Esse complemento depende do [RD Pipe][4], uma biblioteca escrita em Rust que
oferece suporte ao cliente de área de trabalho remota.  O RD Pipe é
redistribuído como parte desse complemento sob os termos da [versão 3 da GNU
Affero General Public License][5], conforme publicado pela Free Software
Foundation.

[[!tag stable dev beta]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess

[3]: https://github.com/leonardder/rdAccess/issues

[4]: https://github.com/leonardder/rd_pipe-rs

[5]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
