# PUtils 跨平台打包完整指南

## 📋 概述

本指南详细说明如何将 PUtils 工具打包成独立的 **Windows** 和 **Linux** 可执行文件，实现真正的跨平台便携应用。

## 🎯 支持的操作系统

| 系统 | 最低版本 | 架构 | 状态 |
|------|---------|------|------|
| Windows | Windows 7 SP1 | x86_64 | ✅ 完全支持 |
| Linux | Ubuntu 18.04+ / Fedora 28+ | x86_64 | ✅ 完全支持 |
| macOS | macOS 10.14+ | x86_64/ARM64 | ⚠️ 实验性支持 |

## 📦 打包文件说明

### Windows 打包脚本
- **`build.bat`** - 交互式主构建脚本（推荐）
- **`build.ps1`** - PowerShell 版本
- **`build_portable.bat`** - 快速构建目录版
- **`build_single_file.bat`** - 快速构建单文件版
- **`check_prerequisites.bat`** - Windows 前置检查

### Linux 打包脚本
- **`build_linux_interactive.sh`** - 交互式主构建脚本（推荐）
- **`build_linux.sh`** - 快速构建目录版
- **`build_linux_single.sh`** - 快速构建单文件版
- **`check_prerequisites_linux.sh`** - Linux 前置检查

### 配置文件
- **`putils.spec`** - PyInstaller 跨平台配置
- **`requirements.txt`** - Python 依赖列表

---

## 🚀 Windows 打包

### 方法一：交互式构建（推荐）

```batch
build.bat
```

### 方法二：快速构建

```batch
# 目录版
build_portable.bat

# 单文件版
build_single_file.bat
```

### 输出位置
- **目录版**: `dist\putils\`
- **单文件版**: `dist\putils.exe` 或 `dist\package\putils.exe`

---

## 🐧 Linux 打包

### 准备工作

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk
```

#### Fedora
```bash
sudo dnf install python3 python3-pip python3-tkinter
```

#### Arch Linux
```bash
sudo pacman -S python python-pip tk
```

### 方法一：交互式构建（推荐）

```bash
# 赋予执行权限
chmod +x build_linux_interactive.sh

# 运行
./build_linux_interactive.sh
```

### 方法二：快速构建

```bash
# 目录版
chmod +x build_linux.sh
./build_linux.sh

# 单文件版
chmod +x build_linux_single.sh
./build_linux_single.sh
```

### 输出位置
- **目录版**: `dist/putils/`
- **单文件版**: `dist/package/putils`

### 运行打包后的应用

```bash
cd dist/putils
chmod +x putils
./putils
```

---

## 📊 两种打包方式对比

| 特性 | 目录版 | 单文件版 |
|------|--------|----------|
| **启动速度** | ⚡ 快 | 🐢 首次慢 |
| **文件大小** | 较小 | 较大 |
| **易于调试** | ✅ 是 | ❌ 否 |
| **便于分发** | 需压缩 | ✅ 单个文件 |
| **适用场景** | 开发测试 | 最终用户 |

---

## 🔧 跨平台注意事项

### 1. 数据目录差异

| 系统 | 默认数据目录 |
|------|------------|
| Windows | `%APPDATA%\PUtils` |
| Linux | `~/.local/share/putils` |
| macOS | `~/Library/Application Support/PUtils` |

应用会自动根据操作系统选择正确的路径。

### 2. 环境变量覆盖

所有平台都支持通过环境变量自定义数据目录：

```bash
# Windows (CMD)
set PUTILS_DATA_DIR=D:\MyData

# Windows (PowerShell)
$env:PUTILS_DATA_DIR="D:\MyData"

# Linux/macOS
export PUTILS_DATA_DIR=/home/user/mydata
```

### 3. ffmpeg 依赖

视频处理功能需要 ffmpeg，各平台安装方法：

**Windows:**
- 下载：https://ffmpeg.org/download.html
- 添加到 PATH 或放在应用目录

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**Fedora:**
```bash
sudo dnf install ffmpeg
```

**Arch:**
```bash
sudo pacman -S ffmpeg
```

### 4. 显示服务器（Linux）

Linux GUI 应用需要 X11 或 Wayland：

```bash
# 检查是否有显示服务器
echo $DISPLAY        # X11
echo $WAYLAND_DISPLAY # Wayland

# 如果没有，安装 X11
sudo apt install xorg
```

---

## 🧪 测试清单

### Windows 测试
- [ ] 在 Windows 10/11 上测试
- [ ] 验证无需 Python 即可运行
- [ ] 检查数据保存在 AppData
- [ ] 测试所有插件功能
- [ ] 验证国际化切换

### Linux 测试
- [ ] 在 Ubuntu 20.04+ 或 Fedora 30+ 上测试
- [ ] 验证 executable 权限正确设置
- [ ] 检查数据保存在 ~/.local/share
- [ ] 测试 X11 和 Wayland 兼容性
- [ ] 验证所有插件功能

### 跨平台一致性测试
- [ ] 配置在不同平台间不冲突
- [ ] 日志格式一致
- [ ] 插件加载机制相同
- [ ] UI 渲染正常

---

## 📤 分发包制作

### Windows 分发

#### ZIP 压缩包
```batch
# 使用 PowerShell
Compress-Archive -Path dist\putils -DestinationPath putils-v0.1.0-windows.zip

# 或使用 7-Zip
7z a putils-v0.1.0-windows.zip dist\putils\*
```

### Linux 分发

#### tar.gz 压缩包
```bash
# 目录版
tar -czf putils-v0.1.0-linux.tar.gz -C dist putils

# 单文件版
tar -czf putils-v0.1.0-linux.tar.gz -C dist/package putils README.txt
```

#### AppImage（高级）
如需创建 AppImage，可使用 [linuxdeploy](https://github.com/linuxdeploy/linuxdeploy)：

```bash
# 安装 linuxdeploy
wget https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
chmod +x linuxdeploy-x86_64.AppImage

# 创建 AppImage
./linuxdeploy-x86_64.AppImage --appdir AppDir --executable dist/putils/putils --output appimage
```

---

## 🛠️ 自定义配置

### 添加应用图标

**Windows:**
编辑 `putils.spec`:
```python
icon='putils.ico',
```

**Linux:**
编辑 `putils.spec`:
```python
icon='putils.png',  # Linux 通常使用 PNG
```

### 启用控制台输出（调试）

编辑 `putils.spec`:
```python
console=True,  # 改为 True 显示控制台
```

### 减小文件体积

在 `putils.spec` 的 `excludes` 中添加不需要的模块：
```python
excludes=[
    'test',
    'unittest',
    'matplotlib',
],
```

---

## 🐛 故障排除

### Windows 问题

**Q: 构建失败，找不到模块？**  
A: 在 `putils.spec` 的 `hiddenimports` 中添加该模块

**Q: 启动后闪退？**  
A: 设置 `console=True` 重新构建，查看错误信息

**Q: 杀毒软件报毒？**  
A: 这是 PyInstaller 常见问题，可提交白名单或使用目录版

### Linux 问题

**Q: Permission denied？**  
A: 运行 `chmod +x putils` 赋予执行权限

**Q: 无法找到 tkinter？**  
A: 安装 python3-tk：`sudo apt install python3-tk`

**Q: GUI 无法显示？**  
A: 确保有 X11 或 Wayland 显示服务器

**Q: 中文乱码？**  
A: 安装中文字体：`sudo apt install fonts-wqy-zenith`

### 跨平台问题

**Q: 如何为不同平台构建？**  
A: 必须在目标平台上构建（Windows 上构建 Windows 版，Linux 上构建 Linux 版）

**Q: 能否交叉编译？**  
A: PyInstaller 不支持交叉编译，需要在目标系统上构建

---

## 📚 自动化构建（CI/CD）

### GitHub Actions 示例

```
name: Build PUtils

on: [push, pull_request]

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pyinstaller --clean putils.spec
      - uses: actions/upload-artifact@v3
        with:
          name: putils-windows
          path: dist/putils/

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: sudo apt install python3-tk
      - run: pip install -r requirements.txt
      - run: pyinstaller --clean putils.spec
      - uses: actions/upload-artifact@v3
        with:
          name: putils-linux
          path: dist/putils/
```

---

## 💡 最佳实践

1. **版本号管理**
   ```
   putils-v0.1.0-windows.zip
   putils-v0.1.0-linux.tar.gz
   ```

2. **在每个目标平台测试**
   - Windows 10/11
   - Ubuntu 20.04/22.04
   - Fedora 35+

3. **提供清晰的安装说明**
   - Windows: 解压即用
   - Linux: chmod +x 后运行

4. **文档多语言**
   - 提供中英文文档
   - 包含故障排除指南

5. **定期更新依赖**
   ```bash
   pip install --upgrade pyinstaller
   ```

---

## 🎉 完成！

现在你拥有了完整的跨平台打包方案：

### Windows 用户
```batch
build.bat
```

### Linux 用户
```bash
chmod +x build_linux_interactive.sh
./build_linux_interactive.sh
```

生成的应用可以在对应的系统上直接运行，无需安装 Python 或任何依赖！

查看详细文档：
- [Windows 打包指南](windows-packaging.md) - Windows 详细指南
- [技术文档](technical-details.md) - 深入的技术说明
- [Windows 用户指南](../user-guides/windows-user-guide.md) - 用户使用说明
- [Linux 用户指南](../user-guides/linux-user-guide.md) - Linux 使用说明
- [快速参考](quick-reference.md) - 常用命令速查
