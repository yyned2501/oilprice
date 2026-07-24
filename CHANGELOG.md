# Changelog

## 1.0.4 (2026-07-24)

### 改进

- **翻译框架**: 传感器名称改用 HA 国际化翻译系统，支持 `translations/zh-Hans.json`
- **配置流程**: 省份输入改为下拉选择框，支持 31 个省/直辖市
- **数据源**: HTTPS 优先，自动 fallback 到 HTTP
- **实体注册**: 移除 `if coordinator.data:` 守卫，首次刷新失败也能注册实体（显示 unavailable）
- **版本号**: 遵循 HA 规范，去 v 前缀（`v1.0.3` → `1.0.4`）
- **服务注册**: 新增 `services.yaml`，注册 `oilprice.refresh` 服务
- **移除冗余**: 删除 `update_time` 传感器，改用 `coordinator.last_update`

### 修复

- 修复首次刷新失败时实体永不注册的问题
- 修复 `asyncio.timeout` 兼容性问题

## v1.0.3 (2026-07-20)

### 改进

- 初始版本发布
- 支持按省份查询油价
- 自动创建 89#、92#、95#、98#、0#柴油传感器
- 下次油价调整时间提醒
- 手动刷新按钮