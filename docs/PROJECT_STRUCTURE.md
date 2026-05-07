# PUtils 项目文件组织结构

## 📁 目录结构

```
putils/
│
├── 📄 README.md                          # 项目主文档（入口）
├── 📄 requirements.txt                   # Python 依赖列表
├── 📄 putils.spec                        # PyInstaller 配置文件
├── 📄 .gitignore                         # Git 忽略规则
│
├── 🔧 构建脚本 (Build Scripts)
│   ├── build.bat                         # Windows 交互式构建 ⭐
│   ├── build.ps1                         # Windows PowerShell 构建
│   ├── build_portable.bat                # Windows 目录版快速构建
│   ├── build_single_file.bat             # Windows 单文件版快速构建
│   ├── check_prerequisites.bat           # Windows 前置检查
│   │
│   ├── build_linux_interactive.sh        # Linux 交互式构建 ⭐
│   ├── build_linux.sh                    # Linux 目录版快速构建
│   ├── build_linux_single.sh             # Linux 单文件版快速构建
│   └── check_prerequisites_linux.sh      # Linux 前置检查
│
├── 📚 文档 (docs/)
│   ├── README.md                         # 文档索引 ⭐
│   │
│   ├── 👥 用户指南 (user-guides/)
│   │   ├── windows-user-guide.md         # Windows 用户使用说明
│   │   └── linux-user-guide.md           # Linux 用户使用说明
│   │
│   ├── 📦 打包文档 (packaging/)
│   │   ├── BUILD_SCRIPTS.md              # 构建脚本详细说明 ⭐ 新增
│   │   ├── quick-start.md                # 快速开始指南
│   │   ├── quick-reference.md            # 快速参考卡片
│   │   ├── cross-platform-packaging.md   # 跨平台打包完整教程 ⭐
│   │   ├── windows-packaging.md          # Windows 打包专属教程
│   │   ├── technical-details.md          # 技术细节和配置
│   │   ├── cross-platform-update.md      # 更新说明
│   │   └── release-template.md           # 发布模板
│   │
│   ├── 💻 开发文档
│   │   ├── development.md                # 插件开发指南
│   │   └── user-guide.md                 # 通用用户指南
│   │
├── 🐍 应用代码 (putils/)
    ├── app.py                            # 主应用程序
    ├── plugins/                          # 插件目录
    │   ├── __init__.py
    │   └── video_saturation.py
    ├── database.py                       # 数据库管理
    ├── i18n.py                          # 国际化
    ├── paths.py                         # 路径工具
    ├── plugin_api.py                    # 插件 API
    ├── plugin_loader.py                 # 插件加载器
    └── tk_utils.py                      # Tkinter 工具
```

## 🎯 文件分类说明

### 根目录文件
- **README.md**: 项目介绍和快速开始，所有文档的入口
- **requirements.txt**: Python 依赖（仅 pyinstaller）
- **putils.spec**: PyInstaller 打包配置（跨平台兼容）
- **.gitignore**: Git 版本控制忽略规则

### 构建脚本 (7个)
全部位于根目录，方便访问：
- **Windows**: 5个脚本 (.bat, .ps1)
- **Linux**: 3个脚本 (.sh)

### 文档 (14个)
全部在 `docs/` 目录下，分类清晰：
- **用户指南** (2个): 面向最终用户
- **打包文档** (8个): 面向开发者
- **开发文档** (2个): 面向插件开发者
- **文档索引** (1个): 导航中心
- **通用指南** (1个): 功能介绍

## 🔗 文档导航流程

```
用户访问
  ↓
README.md (项目主页)
  ↓
docs/README.md (文档索引)
  ↓
根据需求选择:
  ├─ 我是用户 → user-guides/
  ├─ 我要打包 → packaging/
  └─ 我要开发 → development.md
```

## ✅ 组织原则

1. **文档集中管理**: 所有 `.md` 文档都在 `docs/` 目录
2. **分类清晰**: 
   - `user-guides/` - 用户使用
   - `packaging/` - 打包发布
   - 根级别 - 开发相关
3. **构建脚本外露**: 构建脚本在根目录，方便执行
4. **代码独立**: 应用代码在 `putils/` 包中
5. **配置集中**: 配置文件在根目录

## 📊 统计信息

- **总文档数**: 14 个 Markdown 文件
- **构建脚本**: 8 个可执行脚本
- **代码文件**: 8 个 Python 模块
- **配置文件**: 3 个配置文件

## 🎨 图标说明

- 📄 文档文件
- 🔧 构建脚本
- 📚 文档目录
- 👥 用户相关
- 📦 打包相关
- 💻 开发相关
- 🐍 Python 代码
- ⭐ 重点推荐

---

**最后更新**: 2024年  
**维护者**: PUtils Team
