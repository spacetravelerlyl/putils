# PUtils 跨平台打包更新说明

## 🎉 新增功能

本次更新为 PUtils 添加了完整的 **Linux 跨平台打包支持**，现在可以在 Windows 和 Linux 上构建便携式可执行文件。

---

## 📦 新增文件清单

### Linux 构建脚本（4个）

1. **`build_linux_interactive.sh`** - Linux 交互式主构建脚本（推荐使用）
   - 自动检查前置条件
   - 交互式选择构建类型
   - 生成 README 文档

2. **`build_linux.sh`** - Linux 目录版快速构建
   - 一键构建目录版本
   - 适合开发和测试

3. **`build_linux_single.sh`** - Linux 单文件版快速构建
   - 一键构建单文件版本
   - 适合分发

4. **`check_prerequisites_linux.sh`** - Linux 前置条件检查
   - 检查 Python3、pip、tkinter、sqlite3
   - 检查显示服务器（X11/Wayland）
   - 提供安装指导

### 文档（3个）

5. **`跨平台打包指南.md`** - 完整的跨平台打包教程
   - Windows 和 Linux 双平台支持
   - 详细的安装和配置说明
   - 故障排除指南
   - CI/CD 集成示例

6. **`跨平台快速参考.md`** - 跨平台快速参考卡片
   - 常用命令速查
   - 问题快速解决
   - 对比表格

7. **`README_LINUX.md`** - Linux 专用用户指南
   - 各发行版安装说明
   - 桌面集成方法
   - 故障排除

### 更新的文件

8. **`putils.spec`** - 更新为跨平台兼容
   - 自动检测操作系统
   - 使用正确的路径分隔符
   - 动态发现插件

9. **`requirements.txt`** - 跨平台依赖
   - 移除平台特定依赖
   - 仅保留核心库

10. **`.gitignore`** - 添加 Linux 构建产物
    - AppImage 文件
    - AppDir 目录

11. **`README.md`** - 主文档更新
    - 添加跨平台说明
    - 链接到所有文档
    - 系统要求说明

---

## 🚀 使用方法

### Windows 用户（无变化）

```batch
# 仍然使用原有命令
build.bat
```

### Linux 用户（新增）

#### 首次使用 - 安装依赖

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk
```

**Fedora:**
```bash
sudo dnf install python3 python3-pip python3-tkinter
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip tk
```

#### 构建应用

```bash
# 方法一：交互式构建（推荐）
chmod +x build_linux_interactive.sh
./build_linux_interactive.sh

# 方法二：快速构建
chmod +x build_linux.sh
./build_linux.sh              # 目录版

chmod +x build_linux_single.sh
./build_linux_single.sh       # 单文件版
```

#### 运行应用

```bash
cd dist/putils
chmod +x putils
./putils
```

---

## 🔑 关键特性

### 1. 跨平台数据目录

应用会根据操作系统自动选择正确的数据目录：

| 系统 | 数据目录 |
|------|---------|
| Windows | `%APPDATA%\PUtils` |
| Linux | `~/.local/share/putils` |

这符合各平台的规范：
- Windows: 使用 AppData/Roaming
- Linux: 遵循 XDG Base Directory Specification

### 2. 跨平台路径处理

[`putils.spec`](file://d:\Workspace\AiDev\putils\putils.spec) 现在会自动检测操作系统并使用正确的路径分隔符：
- Windows: `\` (反斜杠)
- Linux: `/` (正斜杠)

### 3. 统一的构建体验

Windows 和 Linux 都提供：
- ✅ 交互式构建脚本
- ✅ 快速构建脚本（目录版/单文件版）
- ✅ 前置条件检查
- ✅ 自动生成 README

---

## 📊 平台对比

| 特性 | Windows | Linux |
|------|---------|-------|
| **构建脚本** | `.bat` / `.ps1` | `.sh` |
| **可执行文件** | `.exe` | 无扩展名 |
| **数据目录** | `%APPDATA%` | `~/.local/share` |
| **GUI 依赖** | 内置 | tkinter 需单独安装 |
| **显示服务** | 内置 | X11/Wayland |
| **包格式** | ZIP | tar.gz / AppImage |
| **权限管理** | 无需特殊权限 | 需要 chmod +x |

---

## ⚠️ 重要注意事项

### 1. 不能交叉编译

PyInstaller **不支持交叉编译**，必须：
- 在 Windows 上构建 Windows 版本
- 在 Linux 上构建 Linux 版本

### 2. Linux 需要显示服务器

Linux GUI 应用需要 X11 或 Wayland：
```bash
# 检查是否有显示服务器
echo $DISPLAY        # X11
echo $WAYLAND_DISPLAY # Wayland
```

### 3. 文件权限

Linux 需要手动设置执行权限：
```bash
chmod +x putils
```

### 4. ffmpeg 不包含

两个平台都不包含 ffmpeg，用户需自行安装。

---

## 🧪 测试建议

### Windows 测试环境
- Windows 10 21H2+
- Windows 11 22H2+

### Linux 测试环境
- Ubuntu 20.04 LTS / 22.04 LTS
- Fedora 35+
- 确保测试 X11 和 Wayland

### 跨平台一致性测试
- [ ] 配置保存/加载一致
- [ ] 日志格式相同
- [ ] 插件加载机制一致
- [ ] UI 渲染正常
- [ ] 国际化工作正常

---

## 📤 分发包制作

### Windows
```powershell
Compress-Archive -Path dist\putils -DestinationPath putils-v0.1.0-windows.zip
```

### Linux
```bash
tar -czf putils-v0.1.0-linux.tar.gz -C dist putils
```

### 命名规范
```
putils-v{版本号}-{平台}.{格式}

示例：
putils-v0.1.0-windows.zip
putils-v0.1.0-linux.tar.gz
```

---

## 🔄 持续集成（CI/CD）

可以配置 GitHub Actions 自动构建两个平台：

```yaml
jobs:
  build-windows:
    runs-on: windows-latest
    # ... Windows 构建步骤

  build-linux:
    runs-on: ubuntu-latest
    # ... Linux 构建步骤
```

详见 [`跨平台打包指南.md`](跨平台打包指南.md) 中的 CI/CD 章节。

---

## 🐛 已知限制

1. **macOS 支持**: 目前仅提供实验性支持，需要额外测试
2. **32位系统**: 未测试，建议使用 64 位系统
3. **Wayland 兼容性**: 某些 Linux 发行版可能需要额外配置
4. **中文字体**: Linux 可能需要手动安装中文字体

---

## 💡 最佳实践

1. **在每个目标平台测试**
   - 不要只在一个平台测试后就发布
   - 至少测试 Windows 10/11 和 Ubuntu 20.04/22.04

2. **提供清晰的文档**
   - Windows 和 Linux 用户习惯不同
   - 分别提供针对性的说明

3. **版本号同步**
   - Windows 和 Linux 版本使用相同版本号
   - 在文件名中明确标注平台

4. **自动化测试**
   - 使用 CI/CD 自动构建两个平台
   - 确保代码在两个平台都能正常工作

5. **用户反馈渠道**
   - 收集不同平台用户的问题
   - 及时修复平台特定的 bug

---

## 📚 相关文档

- 📘 [跨平台打包指南](跨平台打包指南.md) - **重点阅读**
- 📗 [跨平台快速参考](跨平台快速参考.md) - 常用命令
- 📕 [Windows 打包指南](打包指南.md) - Windows 专属
- 📙 [Linux 用户指南](README_LINUX.md) - Linux 专属
- 📔 [技术文档](technical-details.md) - 深入技术细节

---

## 🎯 下一步

1. **立即尝试 Linux 构建**
   ```bash
   chmod +x build_linux_interactive.sh
   ./build_linux_interactive.sh
   ```

2. **在 Linux 虚拟机中测试**
   - 下载 Ubuntu 22.04 ISO
   - 在 VirtualBox 中安装
   - 测试构建的应用

3. **准备发布**
   - 创建两个平台的分发包
   - 编写版本更新说明
   - 上传到 GitHub Releases

4. **收集反馈**
   - 邀请用户在两个平台测试
   - 记录并修复问题

---

## ✨ 总结

现在 PUtils 已经是一个**真正的跨平台便携应用**：

✅ **Windows 支持** - 完善的打包方案  
✅ **Linux 支持** - 完整的构建和使用指南  
✅ **统一体验** - 两个平台功能完全一致  
✅ **易于使用** - 简单的构建脚本  
✅ **专业标准** - 遵循平台规范  

开始跨平台打包之旅吧！🚀

相关文档：
- [文档索引](../README.md)
- [快速开始](quick-start.md)
- [跨平台打包指南](cross-platform-packaging.md)
