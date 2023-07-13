import asyncio
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .coordinator import MyCoordinator

DOMAIN = "oilprice"
DEVICES = ["sensor", "button"]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("async_setup_entry in init")
    # 全局注册一个set，用来共享数据
    hass.data.setdefault(DOMAIN, {})
    hass_data = dict(entry.data)
    unsub_options_update_listener = entry.add_update_listener(options_update_listener)
    hass_data["unsub_options_update_listener"] = unsub_options_update_listener
    hass_data["coordinator"] = MyCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = hass_data

    # 添加设备
    for sd in DEVICES:
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, sd))
    return True


async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = all(
        await asyncio.gather(
            *[hass.config_entries.async_forward_entry_unload(entry, sd) for sd in DEVICES]
        )
    )
    # 删除设备时不用重启
    hass.data[DOMAIN][entry.entry_id]["unsub_options_update_listener"]()
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
