import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .coordinator import MyCoordinator

DOMAIN = "oilprice"
DEVICES = ["sensor", "button"]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """设置配置条目，初始化协调器并加载平台"""
    _LOGGER.info("正在初始化今日油价集成...")
    
    # 初始化全局数据存储
    hass.data.setdefault(DOMAIN, {})
    
    # 实例化数据更新协调器
    coordinator = MyCoordinator(hass, entry)
    
    # 在注册平台实体前，先执行首次异步数据拉取，确保实体加载时能立即获得初始状态
    await coordinator.async_config_entry_first_refresh()
    
    # 存储集成运行时所需的数据
    hass_data = {
        "coordinator": coordinator,
        "unsub_options_update_listener": entry.add_update_listener(options_update_listener)
    }
    hass.data[DOMAIN][entry.entry_id] = hass_data

    # 采用现代且推荐的 API 一键并行加载传感器和按钮平台
    await hass.config_entries.async_forward_entry_setups(entry, DEVICES)
    return True


async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """选项更新监听器，当用户在 UI 中修改配置时触发重载"""
    _LOGGER.info("检测到配置选项更新，正在重新加载集成...")
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载配置条目，清理并释放资源"""
    _LOGGER.info("正在卸载今日油价集成...")
    
    # 采用标准的一键卸载平台 API
    unload_ok = await hass.config_entries.async_unload_platforms(entry, DEVICES)
    
    if unload_ok:
        # 注销更新监听器并清理缓存数据
        hass.data[DOMAIN][entry.entry_id]["unsub_options_update_listener"]()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
