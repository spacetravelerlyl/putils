# PUtils 跨平台打包快速参考

## 🚀 一键打包

### Windows
```batch
build.bat
```

### Linux
```bash
chmod +x build_linux_interactive.sh
./build_linux_interactive.sh
```

---

## 📦 两种打包方式

| 方式 | Windows 命令 | Linux 命令 | 输出 |
|------|-------------|------------|------|
| 目录版 | `build_portable.bat` | `./build_linux.sh` | `dist/putils/` |
| 单文件版 | `build_single_file.bat` | `./build_linux_single.sh` | `dist/putils.exe` 或 `dist/putils` |

---

## ✅ 前置检查

### Windows
```batch
check_prerequisites.bat
```

### Linux
```bash
chmod +x check_prerequisites_linux.sh
./check_prerequisites_linux.sh
```

---

## 🔧 使用 PowerShell (Windows)

```powershell
# 目录版
.\build.ps1

# 单文件版
.\build.ps1 -BuildType single
```

---

## 📁 输出位置

### Windows
- **目录版**: `dist\putils\`
- **单文件版**: `dist\package\putils.exe`

### Linux
- **目录版**: `dist/putils/`
- **单文件版**: `dist/package/putils`

---

## 🎯 运行打包后的应用

### Windows
```batch
cd dist\putils
putils.exe
```

### Linux
```bash
cd dist/putils
chmod +x putils
./putils
```

---

## 📤 分发包制作

### Windows
```powershell
# ZIP 压缩包
Compress-Archive -Path dist\putils -DestinationPath putils-v0.1.0-windows.zip
```

### Linux
```bash
# tar.gz 压缩包
tar -czf putils-v0.1.0-linux.tar.gz -C dist putils
```

---

## ⚙️ 数据目录

| 系统 | 默认位置 |
|------|---------|
| Windows | `%APPDATA%\PUtils` |
| Linux | `~/.local/share/putils` |

### 自定义数据目录

**Windows:**
```batch
set PUTILS_DATA_DIR=D:\MyData
```

**Linux:**
```bash
export PUTILS_DATA_DIR=/home/user/mydata
```

---

## 🔧 常用自定义

### 添加图标
编辑 `putils.spec`:
```python
icon='putils.ico',  # Windows
# icon='putils.png',  # Linux
```

### 显示控制台（调试）
编辑 `putils.spec`:
```python
console=True,
```

---

## ⚠️ 重要提示

### Windows
1. **ffmpeg 不包含**：视频功能需要用户自行安装
2. **数据位置**：`%APPDATA%\PUtils`
3. **首次启动**：单文件版首次启动较慢

### Linux
1. **赋予执行权限**：`chmod +x putils`
2. **需要显示服务器**：X11 或 Wayland
3. **安装 tkinter**：`sudo apt install python3-tk`
4. **ffmpeg 安装**：`sudo apt install ffmpeg`

---

## 🐛 常见问题

### Windows

**Q: 构建失败？**  
A: 运行 `check_prerequisites.bat` 检查环境

**Q: 启动闪退？**  
A: 设置 `console=True` 查看错误信息

**Q: 杀毒软件报毒？**  
A: PyInstaller 常见问题，使用目录版或提交白名单

### Linux

**Q: Permission denied？**  
A: `chmod +x putils`

**Q: 找不到 tkinter？**  
A: `sudo apt install python3-tk`

**Q: GUI 无法显示？**  
A: 确保有 X11 或 Wayland

**Q: 中文乱码？**  
A: `sudo apt install fonts-wqy-zenith`

---

## 📋 测试清单

### Windows
- [ ] 在 Windows 10/11 测试
- [ ] 验证无需 Python
- [ ] 检查 AppData 数据保存
- [ ] 测试所有插件

### Linux
- [ ] 在 Ubuntu/Fedora 测试
- [ ] 验证 executable 权限
- [ ] 检查 ~/.local/share 数据保存
- [ ] 测试 X11/Wayland 兼容性

---

## 📚 详细文档

- **跨平台指南**: [cross-platform-packaging.md](cross-platform-packaging.md)
- **Windows 指南**: [windows-packaging.md](windows-packaging.md)
- **技术文档**: [technical-details.md](technical-details.md)
- **Windows 用户说明**: [../user-guides/windows-user-guide.md](../user-guides/windows-user-guide.md)
- **Linux 用户说明**: [../user-guides/linux-user-guide.md](../user-guides/linux-user-guide.md)
- **文档索引**: [../README.md](../README.md)

---

**开始打包：**

- Windows: 双击 `build.bat` 🎉
- Linux: `./build_linux_interactive.sh` 🎉
