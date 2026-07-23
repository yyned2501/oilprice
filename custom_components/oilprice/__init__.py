import logging
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry

from .coordinator import MyCoordinator

DOMAIN = "oilprice"
DEVICES = ["sensor", "button"]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the config entry, initialize the coordinator, and load platforms."""
    _LOGGER.info("正在初始化今日油价集成...")

    # Initialize global data store
    hass.data.setdefault(DOMAIN, {})

    # Instantiate the data update coordinator
    coordinator = MyCoordinator(hass, entry)

    # Execute first async data fetch before registering platform entities,
    # so entities have initial state immediately upon loading
    await coordinator.async_config_entry_first_refresh()

    # Store runtime data
    hass_data = {
        "coordinator": coordinator,
        "unsub_options_update_listener": entry.add_update_listener(options_update_listener),
    }
    hass.data[DOMAIN][entry.entry_id] = hass_data

    # Register the refresh service
    async def handle_refresh(call: ServiceCall) -> None:
        """Handle oilprice.refresh service call — trigger coordinator refresh."""
        _LOGGER.info("收到 oilprice.refresh 服务调用，正在刷新油价数据...")
        await coordinator.async_refresh()

    hass.services.async_register(DOMAIN, "refresh", handle_refresh)

    # Load sensor and button platforms in parallel using the modern API
    await hass.config_entries.async_forward_entry_setups(entry, DEVICES)
    return True


async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Options update listener — reload the integration when the user modifies config."""
    _LOGGER.info("检测到配置选项更新，正在重新加载集成...")
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the config entry — clean up and release resources."""
    _LOGGER.info("正在卸载今日油价集成...")

    # Remove the refresh service
    hass.services.async_remove(DOMAIN, "refresh")

    # Unload platforms using the standard API
    unload_ok = await hass.config_entries.async_unload_platforms(entry, DEVICES)

    if unload_ok:
        # Unregister the update listener and clean cached data
        hass.data[DOMAIN][entry.entry_id]["unsub_options_update_listener"]()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
