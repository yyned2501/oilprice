# oilprice — 今日油价

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/yyned2501/oilprice)](https://github.com/yyned2501/oilprice/releases)

Home Assistant 自定义组件，从 [qiyoujiage.com](https://www.qiyoujiage.com) 获取国内各省市实时油价数据，自动创建传感器实体。

## 功能

- 支持 31 个省/直辖市油价查询
- 自动创建各标号汽油/柴油价格传感器（89#、92#、95#、98#、0#柴油）
- 下次油价调整时间提醒
- 油价涨跌趋势预测提示
- 手动刷新按钮（可一键强制更新）
- `oilprice.refresh` 服务（可被自动化调用）
- HTTPS 优先，自动降级到 HTTP
- 每 6 小时自动刷新（无需干预）
- 简体中文界面

## 安装

### HACS 安装（推荐）

1. 打开 HACS → 集成 → 右上角菜单 → 自定义存储库
2. 添加 `https://github.com/yyned2501/oilprice`，类别选「集成」
3. 搜索 `oilprice` 并安装
4. 重启 Home Assistant

### 手动安装

1. 下载 `custom_components/oilprice/` 整个文件夹
2. 复制到 Home Assistant 配置目录下的 `custom_components/oilprice`
3. 重启 Home Assistant

## 配置

1. **设置 → 设备与服务 → 添加集成 → 搜索 `oilprice`**
2. 或直接点击：[![添加集成](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=oilprice)
3. 从下拉列表中选择省份
4. 完成

配置完成后，系统自动创建以下实体：

| 实体 | 含义 | 单位 |
|------|------|------|
| `sensor.oil_89` | 89#汽油 | 元/升 |
| `sensor.oil_92` | 92#汽油 | 元/升 |
| `sensor.oil_95` | 95#汽油 | 元/升 |
| `sensor.oil_98` | 98#汽油 | 元/升 |
| `sensor.oil_0` | 0#柴油 | 元/升 |
| `sensor.oil_next_change_date` | 下次调整时间 | — |
| `sensor.oil_tips` | 预测提示 | — |
| `button.oil_refresh` | 手动刷新 | — |

## 服务

### `oilprice.refresh`

强制刷新所有已配置区域的油价数据。无需参数。

可在自动化中调用：

```yaml
action:
  service: oilprice.refresh
```

## 数据源

- 主站：`https://www.qiyoujiage.com`（HTTPS 优先）
- 自动 fallback 到 `http://www.qiyoujiage.com`
- 数据缓存：6 小时（避免频繁抓取）
- 超时保护：15 秒全局超时

## 依赖

- `beautifulsoup4` — HTML 解析（自动安装）

## 开发者

详见 [ARCHITECTURE.md](ARCHITECTURE.md)