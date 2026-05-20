import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.const import CONF_REGION
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN
from .coordinator import MyCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities) -> None:
    """在设备控制台注册手动刷新按钮"""
    _LOGGER.info("正在加载今日油价刷新按钮...")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    async_add_entities(
        [
            RefreshButton(
                name="refresh",
                region=config_entry.data[CONF_REGION],
                coordinator=coordinator,
            )
        ]
    )


class RefreshButton(CoordinatorEntity[MyCoordinator], ButtonEntity):
    """一键触发数据更新协调器强制拉取的按钮实体"""

    _attr_has_entity_name = True

    def __init__(self, name: str, region: str, coordinator: MyCoordinator) -> None:
        """初始化按钮实体并关联设备组"""
        self.coordinator_name = f"{DOMAIN}_{region}"
        super().__init__(coordinator, context=self.coordinator_name)
        
        self._attr_unique_id = f"{region}_{name}"
        self._attr_name = "手动刷新"
        self._attr_icon = "mdi:refresh"

    @property
    def device_info(self) -> DeviceInfo:
        """保持与传感器实体完全一致的 DeviceInfo，实现设备级完美聚合"""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator_name)},
            name=f"今日油价 - {self.coordinator_name}",
            manufacturer="@YY",
            model=DOMAIN,
            sw_version="1.0.3",
        )

    async def async_press(self) -> None:
        """点击按钮，由协调器向远端服务器发起最新一轮的数据请求"""
        _LOGGER.info("触发手动刷新按钮：正在向 qiyoujiage.com 请求最新油价...")
        await self.coordinator.async_refresh()
