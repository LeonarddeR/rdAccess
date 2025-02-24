# RDAccess: 远程桌面辅助功能

* 作者：[Leonard de Ruijter][1]
* 下载[最新稳定版本][2]
* NVDA兼容性：2023.2及更高版本

RDAccess插件（远程桌面辅助功能）为NVDA添加了对Microsoft远程桌面、Citrix或VMware Horizon远程会话的支持。
当在服务器和客户端的NVDA中同时安装RDAccess时，服务器上生成的语音和盲文将在客户端机器上以盲文显示。
这使得管理远程系统的用户体验与操作本地系统一样无缝。

## 特点

* 支持Microsoft远程桌面、Citrix和VMware Horizon
* 语音和盲文输出
* 使用NVDA的自动盲文显示检测自动检测远程盲文
* 使用可在NVDA设置对话框中禁用的专用检测过程自动检测远程语音
* 支持在服务器上运行NVDA的便携式副本（Citrix需要额外配置）
* 完全支持在客户端上运行的NVDA的便携式副本（安装该插件不需要额外的管理权限）
* 多个活动客户端会话同时进行
* NVDA启动后远程桌面立即可用
* 能够在不离开远程会话的情况下控制特定的合成器和盲文显示设置
* 在访问安全桌面时，能够使用用户会话中的语音和盲文

## 更改日志

### 1.4版

- -新稳定版

### 1.3版

- 修复了损坏的盲文显示手势。

###  1.2版

- 使用 [Ruff](https://github.com/astral-sh/ruff) as a formatter and linter. [#13](https://github.com/leonardder/rdAccess/pull/13)
- 修复了客户端上的NVDA在暂停服务器上的语音时生成错误的问题。
- 修复了对“winAPI.secureDesktop.post_secureTesktopStateChange”的支持。
- 改进了服务器上的驱动程序初始化。

### 1.1版

- 添加了对NVDA 2023.3风格设备注册的支持，用于自动检测盲文显示器。[#11](https://github.com/leonardder/rdAccess/pull/11)
- 添加了对NVDA 2024.1 Alpha“winAPI.secureDesktop.post_secureDestopStateChange”扩展点的支持。[#12](https://github.com/leonardder/rdAccess/pull/12)

### 1.0版

初始稳定释放。

## 入门指南

1. 在NVDA的客户端和服务器副本上安装RDAccess。
1. 远程系统应使用本地语音合成器自动开始讲话。如果没有，在服务器上的NVDA实例中，从NVDA的合成器选择对话框中选择远程语音合成器。
1. 要使用盲文，请使用盲文显示选择对话框启用自动盲文显示检测。

## 配置

安装后，可以使用NVDA的设置对话框配置RDAccess插件，该对话框可通过选择首选项>设置…从NVDA菜单访问。。。
然后，选择“远程桌面”类别。

此对话框包含以下设置：

### 为远程桌面启用辅助功能

此复选框列表控制插件的操作模式。在以下选项之间进行选择：

* 传入连接（远程桌面服务器）：如果NVDA的当前实例正在远程桌面服务器上运行，请选择此选项。
* 传出连接（远程桌面客户端）：如果NVDA的当前实例正在连接到一个或多个服务器的远程桌面客户端上运行，请选择此选项。
* 安全桌面直通：如果您想在访问安全桌面时使用NVDA用户实例中的盲文和语音，请选择此选项。请注意，要使此功能正常工作，您需要在NVDA的安全桌面副本上提供RDAccess插件。为此，请在NVDA的常规设置中选择“在登录期间和安全屏幕上使用当前保存的设置（需要管理员权限）”。

为了确保插件的顺利启动，默认情况下启用了所有选项。但是，建议您根据需要禁用服务器或客户端模式。

### 连接丢失后自动恢复远程语音

此选项仅在服务器模式下可用。它确保了当远程语音合成器处于活动状态并且连接丢失时，连接将自动重新建立，类似于盲文显示自动检测。

默认情况下启用此选项。如果远程桌面服务器没有音频输出，强烈建议启用此选项。

### 允许远程系统控制驱动设置

在客户端启用此选项后，您可以从远程系统控制驱动程序设置（如合成器语音和音调）。在远程系统上所做的更改将自动反映在本地。

### 退出NVDA时保持客户端支持

此客户端选项在已安装的NVDA副本上可用，可确保即使NVDA未运行，NVDA的客户端部分也会加载到远程桌面客户端中。

要使用RDAccess的客户端部分，需要在Windows注册表中进行更改。
该插件确保这些更改是在当前用户的配置文件下进行的，不需要任何管理权限。
因此，NVDA可以在加载时自动应用必要的更改，并在退出NVDA时撤消这些更改，确保与NVDA的便携版本兼容。

默认情况下，此选项处于禁用状态。但是，如果您正在运行已安装的副本，并且您是系统的唯一用户，建议启用此选项，以便在NVDA启动后连接到远程系统时平稳运行。

### 启用Microsoft远程桌面支持

此选项默认启用，可确保在启动NVDA时将RDAccess的客户端部分加载到Microsoft远程桌面客户端（mstsc）中。
退出NVDA时，通过此选项所做的更改将自动撤消，除非启用了持久客户端支持。

### 启用Citrix工作区支持

此选项默认启用，可确保在启动NVDA时将RDAccess的客户端部分加载到Citrix Workspace应用程序中。
退出NVDA时，通过此选项所做的更改将自动撤消，除非启用了持久客户端支持。

此选项仅在以下条件下可用：

* Citrix Workspace已安装。请注意，由于应用程序本身的限制，不支持该应用程序的Windows应用商店版本。
* 可以在当前用户上下文下注册RDAccess。安装应用程序后，您必须启动一次远程会话才能启用此功能。

## Citrix特定说明

在Citrix Workspace应用程序中使用RDAccess时，有几点需要注意：

### 客户端要求

1. 不支持该应用程序的Windows应用商店变体。
1. 	

### 服务器端要求

在Citrix Virtual Apps and Desktop 2109中，Citrix启用了所谓的虚拟通道允许列表，默认情况下限制第三方虚拟通道，包括RDAccess所需的通道。
有关更多信息，[请参阅Citrix博客文章](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/).

RDAccess要求明确允许RdPipe通道尚未经过测试。目前，最好完全禁用允许列表。如果您的系统管理员有任何疑问，请随时[在此处解决问题][3]。

## 问题和贡献

要报告问题或做出贡献，请参阅[Github上的问题页面][4]

## 外部组件

这个插件依赖于[RD Pipe][5]，这是一个用Rust编写的库，支持远程桌面客户端支持。
RD Pipe作为此附加组件的一部分，根据[GNU Affero通用公共许可证版本3][6]的条款重新分发。

标记开发测试版]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess

[3]: https://github.com/leonardder/rdAccess/issues/1

[4]: https://github.com/leonardder/rdAccess/issues

[5]: https://github.com/leonardder/rd_pipe-rs

[6]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
