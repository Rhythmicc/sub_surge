# Sub-Surge

<div align="center">
   <img src="https://raw.githubusercontent.com/Rhythmicc/sub-surge/main/sub-surge/web/logo.png" alt="Sub-Surge Logo" width="120" />
  <p><strong>Config-driven Surge Subscription Manager with Web UI</strong></p>
  <p>智能、高效的 Surge 订阅配置管理工具</p>
</div>

Sub-Surge 是一个功能强大的 Surge 订阅管理工具，提供现代化的 Web 界面，支持多机场管理、智能配置分析、订阅合并、健康检查以及自动更新。

## ✨ 主要功能

- **🖥 Web 管理界面**：直观的现代化 UI，轻松管理所有订阅。
- **🤖 AI 智能分析**：接入 Openrouter，分析订阅链接，识别节点特征，生成配置模板。
- **🔄 自动更新**：支持后台定时任务，自动更新并同步订阅配置。
- **🔗 订阅合并**：支持将多个机场订阅合并为一个 Surge 配置，实现负载均衡或故障转移。
- **🔄 Clash 配置生成**：支持将 Surge 订阅转换为 Clash 配置。
- **⚡️ 健康检查**：内置节点连通性检测，实时掌握节点状态。
- **📝 日志系统**：完整的操作日志记录，支持前端直接查看运行状态。
- **☁️ 腾讯云 COS 集成**：配置文件自动上传至对象存储，方便多端同步。
- **⚙️ 灵活部署**：支持 PM2 进程管理，支持自定义端口和配置路径。

## 📦 安装

```bash
pip3 install git+https://github.com/Rhythmicc/sub_surge.git -U [--break-system-packages]
```

## 🚀 快速开始

### 1. 启动服务

安装完成后，直接运行以下命令启动 Web 服务：

```bash
sub-surge serve
```

如果是首次运行，程序会引导你进行初始化配置：
- 选择配置存储目录（默认 `~/.sub-surge`）
- 设置 Web 服务默认端口（默认 `8000`）

### 2. 访问界面

打开浏览器访问：`http://localhost:8000`（或你设置的端口）

### 3. 开始使用

1. **添加订阅**：输入订阅链接，使用「智能分析」自动生成配置。
2. **管理节点**：在「机场列表」中查看、更新或删除订阅。
3. **合并配置**：勾选多个机场，点击「合并订阅」生成聚合配置。
4. **获取链接**：点击卡片上的复制按钮，获取 Surge 托管配置链接。

## 🛠 进阶配置与部署

### 环境变量

你可以通过环境变量自定义配置目录（适合 Docker 或特殊部署环境）：

```bash
export SUB_SURGE_CONFIG_DIR="/path/to/config"
sub-surge serve
```

### 使用 PM2 管理进程（推荐）

本项目内置了 PM2 支持，无需额外编写脚本即可实现后台运行和开机自启。

1. **安装 PM2**:
   ```bash
   npm install -g pm2
   ```

2. **启动服务**:
   ```bash
   # 在项目目录下
   pm2 start ecosystem.config.js
   ```

3. **常用命令**:
   ```bash
   pm2 logs sub-surge    # 查看日志
   pm2 stop sub-surge    # 停止服务
   pm2 restart sub-surge # 重启服务
   ```

详细 PM2 使用指南请参考 [PM2_GUIDE.md](PM2_GUIDE.md)。

## 📁 目录结构

默认情况下，程序会在用户根目录下创建 `.sub-surge` 文件夹：

```
~/.sub-surge/
├── config.json         # 机场与全局配置
├── user_config.json    # 用户偏好设置（如端口）
└── logs/               # 运行日志
    ├── sub-surge.log
    ├── pm2-out.log
    └── pm2-error.log
```

## 💻 命令行工具

除了 Web 界面，Sub-Surge 也提供了丰富的命令行工具：

```bash
# 启动 Web 服务
sub-surge serve [--host 0.0.0.0] [--port 8000]

# 添加机场
sub-surge add --name "MyAirport" --url "https://..." --key "my.conf"

# 更新订阅
sub-surge update "MyAirport"

# 合并订阅
sub-surge merge

# 列出所有机场
sub-surge list
```

## 📄 许可证

MIT License
