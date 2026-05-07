# PUtils v0.1.0 发布说明

## 🎉 新版本特性

### 新增功能
- [在此列出新功能]

### 改进优化
- [在此列出改进内容]

### Bug 修复
- [在此列出修复的问题]

## 📥 下载安装

### 系统要求
- Windows 7 SP1 或更高版本
- 推荐 Windows 10/11 64位
- 无需安装 Python

### 下载选项

#### 选项 1：目录版（推荐）
- 文件：`putils-v0.1.0-windows.zip`
- 大小：约 XX MB
- 特点：启动速度快，适合常用用户

**安装步骤：**
1. 下载并解压 ZIP 文件
2. 将 `putils` 文件夹复制到任意位置（如 `C:\Programs\putils`）
3. 双击 `putils.exe` 运行

#### 选项 2：单文件版
- 文件：`putils-v0.1.0-windows.exe`
- 大小：约 XX MB
- 特点：单个文件，便于携带

**使用步骤：**
1. 下载 `putils.exe`
2. 双击运行
3. 首次启动可能需要几秒解压时间

## 🔧 可选依赖

### ffmpeg（视频处理功能）

如需使用视频饱和度调整功能，需要安装 ffmpeg：

**Windows 安装方法：**

1. **下载 ffmpeg**
   - 官方下载：https://ffmpeg.org/download.html
   - 推荐构建：https://github.com/BtbN/FFmpeg-Builds/releases
   - 下载 `ffmpeg-master-latest-win64-gpl.zip`

2. **安装步骤**
   - 解压 ZIP 文件
   - 将 `bin` 文件夹路径添加到系统 PATH
   - 或者将 `ffmpeg.exe`、`ffprobe.exe`、`ffplay.exe` 复制到 putils 文件夹

3. **验证安装**
   ```batch
   ffmpeg -version
   ```

## 📖 使用说明

### 首次使用
1. 启动应用后，建议在设置中配置：
   - 语言偏好
   - 时区设置
   - 数据目录位置（可选）

2. 查看日志标签页了解应用状态

### 数据存储
- 默认位置：`C:\Users\[用户名]\AppData\Roaming\PUtils`
- 包含：配置文件、日志、缓存
- 可在设置中更改数据目录

### 插件使用
- 应用启动时自动加载所有插件
- 在"依赖"标签页查看插件状态
- 某些插件可能需要额外依赖（如 ffmpeg）

## 🐛 已知问题

- [在此列出已知问题和限制]

## 💡 常见问题

### Q: 应用无法启动？
A: 
- 确认系统是 Windows 7 或更高版本
- 尝试以管理员身份运行
- 检查杀毒软件是否阻止

### Q: 设置无法保存？
A: 
- 确认对 AppData 文件夹有写入权限
- 尝试以管理员身份运行一次

### Q: 视频功能不可用？
A: 
- 确认已安装 ffmpeg
- 在命令行运行 `ffmpeg -version` 验证
- 检查 ffmpeg 是否在 PATH 中

### Q: 如何更新到新版本？
A: 
- **目录版**：删除旧文件夹，解压新版本
- **单文件版**：替换 exe 文件
- 用户数据会自动保留

## 📝 变更日志

### v0.1.0 (2024-XX-XX)
- 初始版本发布
- 支持插件系统
- 包含视频饱和度调整插件
- 多语言支持
- 日志管理功能

## 📞 支持与反馈

- **问题反馈**：[GitHub Issues 链接]
- **功能建议**：[GitHub Discussions 链接]
- **邮箱**：[联系邮箱]

## 📄 许可证

本项目采用 [许可证名称] 许可证。
详见 LICENSE 文件。

## 🙏 致谢

感谢以下开源项目：
- PyInstaller - Python 打包工具
- tkinter - Python GUI 框架
- ffmpeg - 视频处理工具
- [其他依赖...]

---

**下载地址**：[下载链接]  
**项目主页**：[GitHub 仓库链接]
