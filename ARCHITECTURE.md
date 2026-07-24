# Oil Price Home Assistant Custom Component Architecture (油价插件架构文档)

## 1. 概述
本项目是一个基于 Home Assistant 自定义组件（Custom Component）架构开发的国内今日油价和油价调整趋势的数据集成插件。它通过异步爬取和解析 `qiyoujiage.com` 的实时页面，为 Home Assistant 自动注册各标号汽柴油价格及变动预测的传感器实体。

## 2. 核心架构与核心设计原则
- **数据共享协同（DataUpdateCoordinator）**: 整个插件共享单一的数据更新协调器 `MyCoordinator`。所有传感器不单独发起 HTTP 请求，而是绑定到同一个协调器。协调器每 6 小时触发一次数据请求，保证数据一致性的同时极大地减少了对目标网站的访问压力。
- **高鲁棒性解析器 (Robust Parser)**: 网页爬虫解析逻辑采用高阶容错设计，在部分 DOM 节点排版改变时会降级提示，而绝对不让整个数据抓取或同步链路中断抛错。
- **共享连接池**: 使用 Home Assistant 全局共享的高性能 HTTP 客户端会话连接池（`aiohttp_client.async_get_clientsession`），避免频繁创建和关闭 Socket 连接。
- **HTTPS 优先**: 自动尝试 HTTPS 连接，失败后降级到 HTTP，提高数据传输安全性。
- **零编译安装（树莓派友好）**: 解析引擎采用 Python 原生、免编译的 `html.parser` 驱动，完全兼容并适配树莓派（ARM 架构）等轻量级智能家居网关设备。

## 3. 目录与职责划分
```text
/home/hermes/projects/oilprice/
├── custom_components/oilprice/
│   ├── __init__.py           # 插件配置项入口，管理集成（ConfigEntry）生命周期、注册平台与服务
│   ├── manifest.json         # 插件配置清单，定义元数据、版本及 beautifulsoup4 依赖项
│   ├── config_flow.py        # 用户 UI 配置流管理，提供省份下拉选择框
│   ├── coordinator.py        # 核心数据同步协调器，执行异步抓取、DOM 解析与全局异常退避
│   ├── sensor.py             # 动态生成并挂载各型油价、下次调整时间、跌涨提示等传感器实体
│   ├── button.py             # 注册"手动刷新（Refresh）"按钮，触发协调器刷新
│   ├── services.yaml         # 定义 oilprice.refresh 服务，可被自动化调用
│   └── translations/
│       └── zh-Hans.json      # 中文界面翻译描述配置文件（含实体名称）
├── CHANGELOG.md              # 版本变更日志
├── README.md                 # 项目说明与安装指南
└── ARCHITECTURE.md           # 本系统架构说明文档
```

## 4. 核心工作与更新数据流 (Data Flow)

```mermaid
graph TD
    Timer([6小时定时器]) --> Coord[MyCoordinator.async_refresh]
    Btn[手动刷新按钮 Press] --> Coord
    Service[oilprice.refresh 服务] --> Coord
    Coord --> Fetch[coordinator.fetch_data]
    Fetch --> HttpClient[HA 共享 aiohttp 客户端]
    HttpClient -- HTTPS优先/HTTP降级 --> Parser[BeautifulSoup 解析器]
    Parser -- html.parser 提取 --> Mapping[数据格式清洗映射]
    Mapping --> Dispatch[通知所有绑定 Sensor]
    Dispatch --> State[Ha Sensor 状态更新]
```

## 5. 连接恢复与异常退让机制
- **协议降级**: 先尝试 HTTPS 连接，失败后自动降级到 HTTP，适配不同网络环境。
- **超时保护**: 网页抓取限制最长 15 秒超时（`asyncio.timeout(15)`），单次请求限制 10 秒。
- **UpdateFailed 状态传导**: 凡遇网络波动、请求失败或超时，协调器统一向上级抛出 `UpdateFailed` 异常。此时 Home Assistant 框架会自动将实体设为"不可用（Unavailable）"，并启动框架内置的指数退让重试机制，免去了循环请求爆破的隐患。

## 6. 实体与服务
- **传感器实体**: 7 个传感器（89#、92#、95#、98#、0#柴油、下次调整时间、预测提示），名称通过 `_attr_translation_key` + 翻译文件实现国际化。
- **按钮实体**: 1 个手动刷新按钮，点击触发 `coordinator.async_refresh()`。
- **服务**: `oilprice.refresh` — 无需参数，可在自动化中调用，触发所有配置区域的刷新。

## 7. 版本管理
- 版本号遵循 HA 规范，纯数字格式（如 `1.0.4`）。
- 版本记录在 `manifest.json` 中，由 GitHub 自动创建 tag 和 release。