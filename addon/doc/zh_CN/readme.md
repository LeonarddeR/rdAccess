# 远程桌面无障碍 #

* 作者： [Leonard de Ruijter][1]
* 下载： [latest stable version][2]
* NVDA 兼容性：2023.2 及更高版本

RDAccess 插件（Remote Desktop Accessibility，远程桌面无障碍）为 NVDA 添加了对 Microsoft
远程桌面、Citrix 或 VMware Horizon 远程会话的支持。
当在客户端和服务器上的 NVDA 中都安装此插件后，服务器上生成的语音和盲文将在客户端计算机上读出和（通过盲文点显器）显示。
这使得管理远程系统如同本地操作般的无缝体验。

## 功能特性

* 支持 Microsoft 远程桌面（包括 Azure 虚拟桌面和 Microsoft 云电脑）、Citrix 和 VMware Horizon
* 语音和盲文输出
* 使用 NVDA 的盲文点显器自动检测功能来自动检测远程盲文
* 使用专用的检测进程自动检测远程语音（可在 NVDA 设置对话框中禁用）
* 支持在服务器上运行的 NVDA 便携版（Citrix 需要额外配置）
* 完全支持在客户端上运行的 NVDA 便携版（安装插件无需额外的管理员权限）
* 同时支持多个活动的客户端会话
* NVDA 启动后远程桌面即时可用
* 能够在不离开远程会话的情况下控制特定的语音合成器和盲文点显器设置
* 能够在访问安全桌面时使用来自用户会话的语音和盲文

## 更新日志

### 1.0 版本

初始稳定版本。

## 开始使用

1. 在客户端和服务器上的 NVDA 中都安装 RDAccess。
1. 远程系统应自动使用本地语音合成器开始朗读。如果未能自动朗读，请在服务器上的 NVDA 实例中，从 NVDA
   的语音合成器选择对话框中选择远程语音合成器。
1. 要使用盲文，请使用盲文点显器选择对话框启用盲文点显器自动检测。

## 配置

安装后，可以通过 NVDA 的设置面板设置 RDAccess 插件，可以从 NVDA 菜单中选择“选项”>“设置...”找到 RDAccess 设置类别。

此面板包含以下设置：

### 为以下项启用远程桌面无障碍

此复选框列表控制插件的操作模式。请在以下选项中选择：

* 传入连接（远程桌面服务器）：如果当前 NVDA 实例运行在远程桌面服务器上，请选择此选项
* 传出连接（远程桌面客户端）：如果当前 NVDA 实例运行在连接到一个或多个服务器的远程桌面客户端上，请选择此选项
* 安全桌面直通：如果您想在访问安全桌面时使用来自用户 NVDA 实例的盲文和语音，请选择此选项。请注意，要使其工作，您需要让 RDAccess
  插件在安全桌面上的 NVDA 副本中可用。为此，请在 NVDA 的常规设置中选择“在登录和安全屏幕上使用当前保存的设置（需要管理员权限）”。

为确保顺利开始使用插件，默认情况下所有选项均已启用。但是，我们鼓励您根据实际情况禁用服务器或客户端模式。

### 连接丢失后自动恢复远程语音

此选项仅在服务器模式下可用。它确保当远程语音合成器处于活动状态且连接丢失时，连接将自动重新建立，类似于盲文点显器的自动检测。

此选项默认启用。如果远程桌面服务器没有音频输出，强烈建议保持此选项启用。

### 允许远程系统控制驱动程序设置

在客户端启用此选项后，您可以从远程系统控制驱动程序设置（例如语音合成器的语音和音高）。在远程系统上所做的更改将自动反映在本地。

While enabling this option implies some performance degradation, you are yet
advised to enable it.  When this option is disabled, speech synthesizer
ppitch changes for capitals don't work.

### 退出 NVDA 时保持客户端支持

This client option is only available on installed copies of NVDA.  When
enabled, it ensures that the client portion of NVDA is loaded in your remote
desktop client, even when NVDA is not running.

此客户端选项（在 NVDA 安装版上可用）确保即使 NVDA 未运行时，NVDA 的客户端部分也会加载到您的远程桌面客户端中。
要使用 RDAccess 的客户端部分，需要在 Windows 注册表中进行更改。
该插件确保这些更改在当前用户的配置文件下进行，无需管理员权限。
因此，NVDA 可以在加载时自动应用必要的更改，并在退出 NVDA 时撤销这些更改，从而确保与 NVDA 便携版兼容。

此选项默认禁用。但是，如果您运行的是安装版并且是系统的唯一用户，建议启用此选项，以便在 NVDA 启动后连接到远程系统时能顺利操作。

### 启用 Microsoft 远程桌面支持

此选项默认启用，确保在启动 NVDA 时，RDAccess 的客户端部分会加载到 Microsoft 远程桌面 客户端  (mstsc) 中。
除非启用了持久客户端支持，否则通过此选项所做的更改将在退出 NVDA 时自动撤销。

### 启用 Citrix Workspace 支持

此选项默认启用，确保在启动 NVDA 时，RDAccess 的客户端部分会加载到 Citrix Workspace 应用中。
除非启用了持久客户端支持，否则通过此选项所做的更改将在退出 NVDA 时自动撤销。

此选项仅在以下条件下可用：

* 已安装 Citrix Workspace。请注意，由于应用本身的限制，不支持该应用的 Windows 应用商店版本
* 可以在当前用户上下文中注册 RDAccess。安装该应用后，您必须启动一次远程会话才能启用此功能

## Citrix 特定说明

使用 RDAccess 与 Citrix Workspace 应用时，有一些重要的注意事项。

### 客户端要求

1. 不支持 Windows 应用商店版本的应用。
2. 安装 Citrix Workspace 后，您需要启动一次远程会话以让 RDAccess
   进行注册。这是因为该应用程序在初始会话设置期间会将系统设置复制到用户设置。在此之后，RDAccess 才能在当前用户上下文中自注册。

### 服务端要求

在 Citrix Virtual Apps and Desktops 2109 中，Citrix
启用了所谓的虚拟通道允许列表，默认情况下限制了第三方虚拟通道，包括 RDAccess 所需的通道。
有关更多信息，[请参阅此 Citrix
博客文章](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/)。

明确允许 RDAccess 所需的 RdPipe
通道尚未经过测试。目前，最好完全禁用该允许列表。如果您的系统管理员有疑虑，请随时[在此处提出问题][3]。

## 问题与贡献

要报告问题或做出贡献，请参阅 [Github 上的问题页面][3]。

## 外部组件

此插件依赖于[RD Pipe][4]，这是一个用 Rust 编写的库，为远程桌面客户端提供支持。
RD Pipe 作为此插件的一部分，根据[GNU Affero 通用公共许可证第 3 版][5]的条款进行再分发。

[[!tag stable dev beta]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess

[3]: https://github.com/leonardder/rdAccess/issues

[4]: https://github.com/leonardder/rd_pipe-rs

[5]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
