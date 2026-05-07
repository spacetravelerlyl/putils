# PUtils 打包快速参考

## 🚀 一键打包

```batch
# 运行交互式构建脚本（推荐）
build.bat
```

## 📦 两种打包方式

| 方式 | 命令 | 输出 | 特点 |
|------|------|------|------|
| 目录版 | `build_portable.bat` | `dist\putils\` | 启动快，易调试 |
| 单文件版 | `build_single_file.bat` | `dist\putils.exe` | 易分发，简洁 |

## ✅ 前置检查

```batch
check_prerequisites.bat
```

## 🎯 使用 PowerShell

```powershell
# 目录版
.\build.ps1

# 单文件版
.\build.ps1 -BuildType single
```

## 📁 输出位置

- **目录版**: `dist\putils\`
- **单文件版**: `dist\package\putils.exe`

## 🔧 常用自定义

### 添加图标
编辑 `putils.spec`:
```python
icon='putils.ico',
```

### 显示控制台（调试）
编辑 `putils.spec`:
```python
console=True,
```

## ⚠️ 重要提示

1. **ffmpeg 不包含**：视频功能需要用户自行安装 ffmpeg
2. **数据位置**：`%APPDATA%\PUtils`
3. **首次启动**：单文件版首次启动较慢（需解压）
4. **测试**：务必在干净环境中测试

## 📋 分发前检查清单

- [ ] 在开发机器测试所有功能
- [ ] 在干净 Windows VM 测试
- [ ] 验证设置保存正常
- [ ] 确认插件加载正常
- [ ] 测试国际化切换
- [ ] 创建 ZIP 压缩包
- [ ] 编写版本更新说明

## 🐛 常见问题

**Q: 构建失败？**  
A: 运行 `check_prerequisites.bat` 检查环境

**Q: 插件未加载？**  
A: 检查 `putils.spec` 中的 `hiddenimports`

**Q: 启动闪退？**  
A: 设置 `console=True` 查看错误信息

**Q: 文件太大？**  
A: 移除不需要的插件和模块

## 📚 详细文档

- 中文指南：`打包指南.md`
- 英文文档：`PACKAGING.md`
- 用户说明：`README_PORTABLE.md`

---

**开始打包：** 双击 `build.bat` 🎉
