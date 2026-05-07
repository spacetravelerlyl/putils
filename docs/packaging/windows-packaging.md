# PUtils 打包成 Portable Windows 应用完整指南

## 📋 概述

本指南详细说明如何将 PUtils 工具打包成独立的 Windows 可执行文件，使其可以在任何 Windows 机器上运行，无需安装 Python 或依赖库。

## 🎯 打包方案特点

✅ **完全独立**：包含所有 Python 运行时和依赖库  
✅ **无需安装**：绿色便携，复制即可使用  
✅ **插件支持**：自动包含所有插件模块  
✅ **数据隔离**：用户数据存储在 AppData，与应用分离  
✅ **两种模式**：目录版（快速启动）和单文件版（易于分发）  

## 📦 打包文件说明

项目根目录已创建以下打包相关文件：

### 1. 配置文件
- **`requirements.txt`** - Python 依赖列表
- **`putils.spec`** - PyInstaller 打包配置文件
- **`.gitignore`** - Git 忽略规则

### 2. 构建脚本
- **`build.bat`** - 交互式批处理构建脚本（推荐）
- **`build.ps1`** - PowerShell 构建脚本（更友好）
- **`build_portable.bat`** - 快速构建目录版
- **`build_single_file.bat`** - 快速构建单文件版
- **`check_prerequisites.bat`** - 前置条件检查脚本

### 3. 文档
- **`PACKAGING.md`** - 详细打包技术文档（英文）
- **`README_PORTABLE.md`** - 用户使用说明（英文）

## 🚀 快速开始

### 方法一：使用交互式构建脚本（推荐）

```batch
# 双击运行或在命令行执行
build.bat
```

脚本会：
1. 自动检查所有前置条件
2. 询问你要构建的类型（目录版或单文件版）
3. 安装依赖
4. 执行打包
5. 生成 README 文件

### 方法二：使用 PowerShell 脚本

```powershell
# 构建目录版（默认）
.\build.ps1

# 构建单文件版
.\build.ps1 -BuildType single
```

### 方法三：直接构建

```batch
# 目录版
build_portable.bat

# 单文件版
build_single_file.bat
```

## 📂 构建输出

### 目录版输出
```
dist/
└── putils/
    ├── putils.exe          # 主程序
    ├── *.dll               # 依赖库
    ├── plugins/            # 插件目录
    └── README.txt          # 使用说明
```

**优点：**
- 启动速度快（无需解压）
- 便于调试和更新
- 文件结构清晰

**适用场景：** 开发测试、内部使用

### 单文件版输出
```
dist/
└── package/
    ├── putils.exe          # 单一可执行文件
    └── README.txt          # 使用说明
```

**优点：**
- 分发方便（单个文件）
- 简洁美观
- 不易误删文件

**缺点：**
- 首次启动较慢（需解压到临时目录）
- 文件体积较大

**适用场景：** 对外发布、最终用户分发

## 🔧 自定义配置

### 添加应用图标

1. 准备一个 `.ico` 格式图标文件（如 `putils.ico`）
2. 编辑 `putils.spec`，取消注释并修改：
```python
icon='putils.ico',
```

### 启用控制台输出（调试用）

编辑 `putils.spec`：
```python
console=True,  # 改为 True 显示控制台
```

### 减小文件体积

在 `putils.spec` 的 `excludes` 中添加不需要的模块：
```python
excludes=[
    'test',
    'unittest',
    'matplotlib',  # 如果没用到
    # ... 其他不需要的模块
],
```

### 添加额外文件

在 `putils.spec` 的 `datas` 中添加：
```python
datas=[
    ('source/path/file.txt', 'destination/path'),
],
```

## ⚙️ 工作原理

### 数据持久化

打包后的应用会将用户数据存储在：
```
C:\Users\[用户名]\AppData\Roaming\PUtils\
├── config.sqlite3    # 配置数据库
├── logs.sqlite3      # 日志数据库
└── cache.sqlite3     # 缓存数据库
```

这样做的好处：
- 应用程序可以随意移动/更新而不丢失数据
- 多用户环境下每个用户有独立配置
- 符合 Windows 应用规范

### 插件加载机制

PyInstaller 会将所有插件模块打包进去，运行时通过 `pkgutil.iter_modules` 动态发现和加载插件。`putils.spec` 中的 `hiddenimports` 确保所有插件都被正确包含。

### 路径处理

[`paths.py`](file://d:\Workspace\AiDev\putils\putils\paths.py) 已经处理了打包后的路径问题：
- 使用 `sys.frozen` 检测是否在打包环境
- 资源文件通过 PyInstaller 的数据文件机制访问
- 用户数据始终指向 AppData 目录

## 🧪 测试清单

打包完成后，请按以下步骤测试：

### 基础测试
- [ ] 在开发机器上运行，确认所有功能正常
- [ ] 检查设置能否保存
- [ ] 验证国际化切换是否正常
- [ ] 测试所有插件功能

### 清洁环境测试
- [ ] 在干净的 Windows VM 或另一台电脑上测试
- [ ] 确认无需安装 Python 即可运行
- [ ] 验证首次启动时间可接受
- [ ] 检查数据目录是否正确创建

### 功能测试
- [ ] 视频饱和度调整（需要安装 ffmpeg）
- [ ] 依赖检查功能
- [ ] 日志查看和过滤
- [ ] 数据目录迁移功能

### 边界测试
- [ ] 以管理员身份运行
- [ ] 在受限用户账户下运行
- [ ] 数据目录设置为不同位置
- [ ] 长时间运行稳定性

## 📤 分发包制作

### ZIP 压缩包（推荐）

```batch
# 使用 7-Zip 或 WinRAR 压缩 dist\putils 文件夹
# 命名为：putils-v0.1.0-windows.zip

# 或使用 PowerShell
Compress-Archive -Path dist\putils -DestinationPath putils-v0.1.0-windows.zip
```

### 安装包制作（可选）

可以使用以下工具创建安装程序：
- **NSIS** - 免费开源
- **Inno Setup** - 免费，易用
- **Advanced Installer** - 商业软件

### 分发内容建议

```
putils-v0.1.0-windows/
├── putils/              # 应用程序文件夹
│   ├── putils.exe
│   └── ...
├── INSTALLATION.txt     # 安装说明
├── CHANGELOG.md         # 版本更新日志
└── LICENSE              # 许可证文件
```

## ⚠️ 注意事项

### ffmpeg 依赖

视频处理功能需要 ffmpeg：
- **不包含在打包中**（体积太大且有许可问题）
- 用户需要自行安装 ffmpeg
- 建议在分发文档中说明

提供 ffmpeg 下载链接：
```
https://ffmpeg.org/download.html
https://github.com/BtbN/FFmpeg-Builds/releases
```

### 杀毒软件误报

单文件可执行程序可能被某些杀毒软件标记为可疑：
- 这是 PyInstaller 打包的常见问题
- 可以向杀毒软件厂商提交白名单
- 使用代码签名证书可以减少误报
- 目录版通常不会被误报

### 首次启动慢

单文件版首次启动需要解压到临时目录：
- 可能需要 5-15 秒
- 后续启动会快很多
- 可以在 README 中提醒用户

### 系统兼容性

- 最低支持：Windows 7 SP1
- 推荐：Windows 10/11 64位
- 在 32 位系统上需要单独构建

## 🐛 故障排除

### 构建失败：找不到模块

**问题：** `ModuleNotFoundError: No module named 'xxx'`

**解决：**
1. 在 `putils.spec` 的 `hiddenimports` 中添加该模块
2. 重新运行构建

### 插件未加载

**问题：** 启动后没有显示插件

**解决：**
1. 检查 `putils.spec` 中是否包含插件文件
2. 确认插件模块名在 `hiddenimports` 中
3. 使用目录版测试，查看是否有导入错误

### 启动后立即崩溃

**问题：** 双击 exe 后闪退

**解决：**
1. 在 `putils.spec` 中设置 `console=True`
2. 重新构建，从控制台查看错误信息
3. 根据错误修复问题

### 文件体积过大

**问题：** exe 文件超过 100MB

**解决：**
1. 移除不需要的插件
2. 在 `excludes` 中添加不必要的模块
3. 考虑使用目录版而非单文件版

## 📚 相关资源

- [PyInstaller 官方文档](https://pyinstaller.org/en/stable/)
- [ffmpeg 下载](https://ffmpeg.org/download.html)
- [Inno Setup](https://jrsoftware.org/isdl.php)
- [NSIS](https://nsis.sourceforge.io/Download)

## 💡 最佳实践

1. **版本号管理**：在文件名中包含版本号
2. **更新机制**：考虑添加自动更新功能
3. **用户反馈**：提供 bug 报告渠道
4. **文档完善**：提供详细的用户手册
5. **测试充分**：在多个 Windows 版本上测试
6. **备份策略**：定期备份构建配置

## 🎉 完成！

现在你已经拥有了完整的打包方案。只需运行 `build.bat`，就能生成可在任何 Windows 机器上运行的便携式应用！

如有问题，请查看 [技术文档](technical-details.md) 获取更详细的技术说明。

相关文档：
- [跨平台打包指南](cross-platform-packaging.md) - Windows + Linux 完整教程
- [快速参考](quick-reference.md) - 常用命令速查
- [Windows 用户指南](../user-guides/windows-user-guide.md) - 用户使用说明
