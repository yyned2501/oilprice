import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_REGION
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN
from .coordinator import MyCoordinator

_LOGGER = logging.getLogger(__name__)

# 定义传感器图标与默认单位，并映射为用户体验极佳的中文友好名称
ICON_GAS_STATION = "mdi:gas-station"

SENSOR_TYPES: Dict[str, Dict[str, Any]] = {
    "89": {"name": "89#汽油", "unit": "元/升", "icon": ICON_GAS_STATION},
    "92": {"name": "92#汽油", "unit": "元/升", "icon": ICON_GAS_STATION},
    "95": {"name": "95#汽油", "unit": "元/升", "icon": ICON_GAS_STATION},
    "98": {"name": "98#汽油", "unit": "元/升", "icon": ICON_GAS_STATION},
    "0": {"name": "0#柴油", "unit": "元/升", "icon": ICON_GAS_STATION},
    "next_change_date": {"name": "下次调整时间", "unit": None, "icon": "mdi:calendar-clock"},
    "tips": {"name": "预测提示", "unit": None, "icon": "mdi:alert-decagram-outline"},
    "update_time": {"name": "更新时间", "unit": None, "icon": "mdi:clock-outline"},
}


async def async_setup_entry(hass, config_entry, async_add_entities) -> None:
    """设置油价传感器实体平台，将各个解析到的数值项渲染为独立的 SensorEntity"""
    _LOGGER.info("正在加载今日油价传感器...")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    if coordinator.data:
        async_add_entities(
            [
                OilPriceSensor(
                    name=sensor_key,
                    region=config_entry.data[CONF_REGION],
                    coordinator=coordinator,
                )
                for sensor_key in coordinator.data
            ]
        )


class OilPriceSensor(CoordinatorEntity[MyCoordinator], SensorEntity):
    """基于 DataUpdateCoordinator 数据源的今日油价及变动提示实体类"""

    _attr_has_entity_name = True

    def __init__(self, name: str, region: str, coordinator: MyCoordinator) -> None:
        """初始化传感器并绑定到协调器上"""
        self.coordinator_name = f"{DOMAIN}_{region}"
        super().__init__(coordinator, context=self.coordinator_name)
        
        self._raw_key = name
        self._attr_unique_id = f"{region}_{name}"
        
        # 匹配元数据描述以美化 UI 展示
        meta = SENSOR_TYPES.get(name, {})
        self._attr_name = meta.get("name", name)
        self._attr_native_unit_of_measurement = meta.get("unit")
        self._attr_icon = meta.get("icon", ICON_GAS_STATION)

        # 为标号数字油价和柴油开启 measurement 指标统计模式，以便 HA 绘制历史曲线
        if name in ("89", "92", "95", "98", "0"):
            self._attr_state_class = "measurement"

    @property
    def native_value(self) -> Optional[Any]:
        """从协调器缓存数据中读取最新数值，实现单源更新，避免数据不一致"""
        if self.coordinator.data:
            return self.coordinator.data.get(self._raw_key)
        return None

    @property
    def device_info(self) -> DeviceInfo:
        """将同一地区的所有传感器聚合为一个独立的“今日油价”设备"""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator_name)},
            name=f"今日油价 - {self.coordinator_name}",
            manufacturer="@YY",
            model=DOMAIN,
            sw_version="1.0.3",
        )
