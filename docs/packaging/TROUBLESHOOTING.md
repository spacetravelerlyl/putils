# PyInstaller 打包错误排查指南

## ❌ 常见错误及解决方案

### 1. Module object for pyimod02_importers is NULL

**错误现象：**
```
Module object for pyimod02_importers is NULL
```

**原因：**
- PyInstaller bootloader 初始化失败
- 关键模块导入顺序错误
- PyInstaller 版本过旧或有 bug

**解决方案：**

#### 方案 A：升级 PyInstaller（推荐）
```batch
pip install --upgrade pyinstaller
```

确保使用最新版本（6.0+）。

#### 方案 B：使用修复后的构建脚本
```batch
build_single_file_fixed.bat
```

此脚本已优化：
- ✅ 添加了关键的 `encodings` 模块导入
- ✅ 禁用了 UPX 压缩（可能导致问题）
- ✅ 按正确顺序列出所有 hiddenimports

#### 方案 C：使用调试模式诊断
```batch
build_debug.bat
```

这会：
- 启用控制台窗口显示详细错误
- 显示完整的 traceback
- 帮助定位具体问题

#### 方案 D：尝试目录版而非单文件版
```batch
build_portable.bat
```

目录版通常更稳定，因为不需要解压过程。

---

### 2. ImportError: No module named 'xxx'

**错误现象：**
```
ImportError: No module named 'putils.plugins'
```

**解决方案：**

在 `putils.spec` 的 `hiddenimports` 中添加缺失的模块：

```python
hiddenimports=[
    'putils',
    'putils.app',
    'putils.plugins',
    'putils.plugins.video_saturation',
    # ... 其他模块
]
```

---

### 3. tkinter 相关错误

**错误现象：**
```
_tkinter.TclError: no display name and no $DISPLAY environment variable
```

**解决方案：**

确保包含完整的 tkinter：

```batch
--collect-all=tkinter
```

或在 spec 文件中：
```python
hiddenimports=['tkinter', 'tkinter.filedialog', 'tkinter.messagebox', 'tkinter.ttk']
```

---

### 4. 启动后立即崩溃（无错误信息）

**解决方案：**

1. **启用控制台模式** - 编辑 `putils.spec`：
   ```python
   console=True,  # 改为 True
   ```

2. **重新构建并运行**，查看错误信息

3. **或使用调试脚本**：
   ```batch
   build_debug.bat
   ```

---

### 5. 文件大小异常大

**解决方案：**

1. **启用 UPX 压缩**（如果之前禁用了）：
   ```batch
   --upx-dir=path/to/upx
   ```

2. **排除不必要的模块**：
   ```python
   excludes=[
       'test',
       'unittest',
       'email',
       'html',
       'http',
   ]
   ```

3. **使用目录版**而非单文件版

---

## 🔧 通用调试步骤

### 步骤 1：检查 Python 环境

```batch
python --version
pip list | findstr pyinstaller
```

确保：
- Python 3.8+ 
- PyInstaller 6.0+

### 步骤 2：清理构建缓存

```batch
rmdir /s /q build
rmdir /s /q dist
del *.spec.backup
```

### 步骤 3：使用 --clean 标志

```batch
pyinstaller --clean your_script.py
```

### 步骤 4：逐步添加模块

先构建最小版本，然后逐个添加模块：

```batch
# 最小版本
pyinstaller --onefile --windowed app.py

# 添加一个插件
pyinstaller --onefile --windowed --hidden-import=putils.plugins app.py

# 继续添加...
```

### 步骤 5：检查依赖树

```batch
pip install pipdeptree
pipdeptree
```

查看是否有循环依赖或冲突。

---

## 📋 构建前检查清单

- [ ] Python 版本 >= 3.8
- [ ] PyInstaller 版本 >= 6.0
- [ ] 已安装 tkinter: `python -c "import tkinter"`
- [ ] 已安装 sqlite3: `python -c "import sqlite3"`
- [ ] 清理了旧的 build/dist 目录
- [ ] 所有插件文件存在
- [ ] i18n.py 文件存在

运行检查脚本：
```batch
check_prerequisites.bat
```

---

## 🚀 推荐的构建流程

### 对于开发/测试

1. **使用目录版**（更快、更易调试）
   ```batch
   build_portable.bat
   ```

2. **测试功能**
   ```batch
   cd dist\putils
   putils.exe
   ```

3. **确认无误后构建单文件版**
   ```batch
   build_single_file_fixed.bat
   ```

### 对于发布

1. **先构建调试版**
   ```batch
   build_debug.bat
   ```

2. **从命令行运行，检查输出**
   ```batch
   cd dist
   putils-debug.exe
   ```

3. **如果没有错误，构建正式版**
   ```batch
   build_single_file_fixed.bat
   ```

4. **在干净环境中测试**
   - 复制到其他电脑
   - 或在新用户账户下测试

---

## 💡 最佳实践

### 1. 保持 PyInstaller 最新
```batch
pip install --upgrade pyinstaller
```

### 2. 使用虚拟环境
```batch
python -m venv build_env
build_env\Scripts\activate
pip install -r requirements.txt
```

### 3. 定期清理缓存
```batch
rmdir /s /q %LOCALAPPDATA%\pyinstaller
```

### 4. 记录成功配置
保存能正常工作的 spec 文件作为备份。

### 5. 分阶段构建
- 先构建最小可运行版本
- 逐步添加功能
- 每步都测试

---

## 🆘 仍然无法解决？

### 收集诊断信息

1. **Python 版本**
   ```batch
   python --version
   ```

2. **PyInstaller 版本**
   ```batch
   pyinstaller --version
   ```

3. **完整错误日志**
   使用 `build_debug.bat` 获取

4. **系统信息**
   ```batch
   systeminfo | findstr /C:"OS Name" /C:"OS Version"
   ```

### 寻求帮助

1. 查看 PyInstaller 官方文档：
   https://pyinstaller.org/en/stable/

2. 搜索 GitHub Issues：
   https://github.com/pyinstaller/pyinstaller/issues

3. 提供以下信息：
   - 完整错误消息
   - Python 和 PyInstaller 版本
   - 操作系统版本
   - 使用的构建命令
   - spec 文件内容

---

## 📚 相关文档

- [PyInstaller 官方文档](https://pyinstaller.org/)
- [常见问题 FAQ](https://pyinstaller.org/en/stable/FAQ.html)
- [已知问题](https://pyinstaller.org/en/stable/known-issues.html)
- [本项目构建脚本说明](BUILD_SCRIPTS.md)

---

**最后更新**: 2024年  
**适用版本**: PyInstaller 6.0+
