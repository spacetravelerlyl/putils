# 构建脚本说明

本文档说明 PUtils 项目中的所有构建脚本。

## 📦 Windows 构建脚本

### 主要脚本

#### `build.bat` - 交互式主构建脚本 ⭐ 推荐
- **功能**: 完整的交互式构建流程
- **特点**: 
  - 自动检查前置条件
  - 交互式选择构建类型（目录版/单文件版）
  - 自动生成 README
- **使用**: 
  ```batch
  build.bat
  ```

#### `build.ps1` - PowerShell 版本
- **功能**: 与 build.bat 相同，但使用 PowerShell
- **特点**: 彩色输出，更好的错误处理
- **使用**:
  ```powershell
  # 目录版（默认）
  .\build.ps1
  
  # 单文件版
  .\build.ps1 -BuildType single
  ```

### 快速构建脚本

#### `build_portable.bat` - 目录版快速构建
- **功能**: 直接构建目录版本
- **输出**: `dist\putils\`
- **使用**:
  ```batch
  build_portable.bat
  ```

#### `build_single_file.bat` - 单文件版快速构建
- **功能**: 直接构建单文件版本
- **输出**: `dist\putils.exe`
- **使用**:
  ```batch
  build_single_file.bat
  ```

### 辅助脚本

#### `check_prerequisites.bat` - 前置条件检查
- **功能**: 检查 Python、pip、tkinter、sqlite3 等
- **使用**:
  ```batch
  check_prerequisites.bat
  ```

---

## 🐧 Linux 构建脚本

### 主要脚本

#### `build_linux_interactive.sh` - 交互式主构建脚本 ⭐ 推荐
- **功能**: 完整的交互式构建流程
- **特点**: 
  - 自动检查前置条件
  - 交互式选择构建类型
  - 自动生成 README
- **使用**:
  ```bash
  chmod +x build_linux_interactive.sh
  ./build_linux_interactive.sh
  ```

### 快速构建脚本

#### `build_linux.sh` - 目录版快速构建
- **功能**: 直接构建目录版本
- **输出**: `dist/putils/`
- **使用**:
  ```bash
  chmod +x build_linux.sh
  ./build_linux.sh
  ```

#### `build_linux_single.sh` - 单文件版快速构建
- **功能**: 直接构建单文件版本
- **输出**: `dist/package/putils`
- **使用**:
  ```bash
  chmod +x build_linux_single.sh
  ./build_linux_single.sh
  ```

### 辅助脚本

#### `check_prerequisites_linux.sh` - 前置条件检查
- **功能**: 检查 Python3、pip、tkinter、显示服务器等
- **使用**:
  ```bash
  chmod +x check_prerequisites_linux.sh
  ./check_prerequisites_linux.sh
  ```

---

## 🎯 如何选择

### 新手用户
- **Windows**: 使用 `build.bat`（交互式，有提示）
- **Linux**: 使用 `build_linux_interactive.sh`（交互式，有提示）

### 开发/测试
- **Windows**: 使用 `build_portable.bat`（快速，便于调试）
- **Linux**: 使用 `build_linux.sh`（快速，便于调试）

### 发布分发
- **Windows**: 使用 `build_single_file.bat`（单个文件，易于分发）
- **Linux**: 使用 `build_linux_single.sh`（单个文件，易于分发）

---

## 📋 构建前准备

### Windows
确保已安装：
- Python 3.8+
- pip
- tkinter（通常随 Python 一起安装）

运行检查：
```batch
check_prerequisites.bat
```

### Linux
确保已安装：
```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip python3-tk

# Fedora
sudo dnf install python3 python3-pip python3-tkinter

# Arch
sudo pacman -S python python-pip tk
```

运行检查：
```bash
chmod +x check_prerequisites_linux.sh
./check_prerequisites_linux.sh
```

---

## 🔧 配置文件

### `putils.spec` - PyInstaller 配置
- **用途**: 定义打包选项
- **特点**: 跨平台兼容，自动检测操作系统
- **编辑**: 如需自定义打包行为

### `requirements.txt` - Python 依赖
- **用途**: 列出所有 Python 依赖
- **内容**: pyinstaller（其他依赖都是标准库）

---

## 📤 构建输出

### Windows
```
dist/
├── putils/              (目录版)
│   ├── putils.exe
│   ├── *.dll
│   └── plugins/
└── package/             (单文件版)
    └── putils.exe
```

### Linux
```
dist/
├── putils/              (目录版)
│   ├── putils
│   ├── *.so
│   └── plugins/
└── package/             (单文件版)
    └── putils
```

---

## 🐛 常见问题

### Q: 构建失败怎么办？
A: 先运行对应的 check_prerequisites 脚本检查环境

### Q: 如何清理构建产物？
A: 删除 `dist/` 和 `build/` 目录

### Q: 可以交叉编译吗？
A: 不可以，必须在目标平台上构建

### Q: 如何选择构建类型？
A: 
- 开发测试用目录版（启动快）
- 最终分发用单文件版（方便）

---

## 📚 相关文档

- [快速开始](packaging/quick-start.md)
- [跨平台打包指南](packaging/cross-platform-packaging.md)
- [技术细节](packaging/technical-details.md)
- [文档索引](../README.md)
