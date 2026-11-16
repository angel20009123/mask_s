# Mask Studio

中文 IPv4 掩码与 ACL 桌面计算器，使用 Python 标准库 Tkinter，无第三方依赖。

## 启动

推荐直接双击 `dist/MaskStudio.exe`，无需安装 Python。

运行源码：Windows 安装包含 Tkinter 的 Python 3.10 或更高版本后，双击 `启动客户端.bat`，或运行 `python app.py`。

## 功能

- 输入 IPv4 地址以及 CIDR 前缀、正掩码或反掩码 / ACL 通配符。
- 显示掩码互转、二进制表示、网络地址、广播地址、可用地址范围和数量。
- 支持非连续 ACL 通配符，显示实际匹配数量与最小、最大匹配地址。
- 将非连续通配符精确拆分为最少 CIDR 子网，在“子网层级与地址范围”页按地址层级展示；大量子网分页显示，每页 128 条。
- 蓝色固定匹配位、紫色非连续分支位、绿色连续地址位；子网列表按分组与子网分层配色。
- 检查指定 IPv4 地址是否符合 ACL，并复制全部计算结果。
- /31 按点对点网络处理，/32 按单主机处理。

反掩码与正掩码逐位取反。只有连续反掩码才对应单个 CIDR 网段。ACL 片段仅包含地址与通配符，实际规则还需按设备配置协议、动作与方向。

## 验证

运行 `python -m unittest -v`。

重新打包：`python -m PyInstaller --noconfirm --onefile --windowed --name MaskStudio --icon assets/mask-studio.ico --add-data "assets;assets" app.py`（需安装 PyInstaller）。

图标源文件生成脚本为 `create_assets.py`（重新生成需要 Pillow），PNG 与 Windows 多尺寸 ICO 位于 `assets/`。

例如 `192.168.0.0 0.0.5.255` 精确分解为 `192.168.0.0/23`、`192.168.4.0/23`，其间 `192.168.2.0/23` 不匹配。复制结果包含当前页子网，明确标注总数与页范围。
